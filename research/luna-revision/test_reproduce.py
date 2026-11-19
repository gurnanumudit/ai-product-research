"""Small hand-computed and negative fixtures; the full saved-data replay is separate."""
import copy
from fractions import Fraction
import json
import unittest

import computation as c
import reproduce as r


class NumericalTests(unittest.TestCase):
    def test_zero_discordant(self):
        self.assertEqual(c.exact_mcnemar(0, 0)['two_sided_p'], 1)

    def test_all_wins_and_losses(self):
        for gains, losses in [(10, 0), (0, 10)]:
            p = c.exact_mcnemar(gains, losses)
            self.assertEqual(Fraction(int(p['p_numerator']), int(p['p_denominator'])), Fraction(1, 512))

    def test_balanced_and_single(self):
        self.assertEqual(c.exact_mcnemar(1, 1)['two_sided_p'], 1)
        self.assertEqual(c.exact_mcnemar(1, 0)['two_sided_p'], 1)

    def test_holm_four(self):
        tests = {k: c.exact_mcnemar(0, 0) for k in c.PRIMARY}
        tests['coding:R-S'] = c.exact_mcnemar(10, 0)
        adjusted = c.holm(tests)
        self.assertEqual(adjusted['coding:R-S']['holm_adjusted_p'], 1/128)
        self.assertEqual(adjusted['planning:S-A']['holm_adjusted_p'], 1)

    def test_quantile_type7(self):
        self.assertEqual(c.quantile([0, 10], .25), 2.5)

    def test_null_not_zero(self):
        self.assertEqual(c.metric([1, None, 2]), dict(known_sum=3, missing=1, complete_sum=None, n=3))

    def test_bootstrap_preserves_triplets_seed_and_order(self):
        fs = []
        for domain, stratum in [('coding', 'VERY_HARD'), ('planning', 'graph_color'), ('planning', 'sokoban')]:
            for i in range(2):
                fs.append(dict(domain=domain, stratum=stratum, canonical_family_id=str(i),
                               endpoints={w: {'passed': bool(i)} for w in c.WORKFLOWS}))
        a = c.paired_bootstrap(fs, draws=31)
        self.assertEqual(a, c.paired_bootstrap(list(reversed(fs)), draws=31))
        self.assertTrue(all(x == {'low': 0.0, 'high': 0.0} for x in a['intervals'].values()))
        self.assertNotEqual(a['resample_index_stream_sha256'],
                            c.paired_bootstrap(fs, draws=31, seed=20261112)['resample_index_stream_sha256'])

    def test_negative_counts(self):
        with self.assertRaises(ValueError): c.exact_mcnemar(-1, 0)

    def test_comparison_not_tolerant_of_stats_or_null_change(self):
        with self.assertRaises(ValueError): r.compare(.1 + 1e-12, .1, 'primary.difference')
        with self.assertRaises(ValueError): r.compare(0, None, 'times_ms.complete_sum')


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(x) for x in (r.ROOT/'data/outcomes.jsonl').read_text().splitlines()]

    def test_complete(self):
        self.assertEqual(len(r.validate(self.rows)), 200)

    def test_missing(self):
        with self.assertRaises(ValueError): r.validate(self.rows[:-1])

    def test_duplicate(self):
        with self.assertRaises(ValueError): r.validate(self.rows[:-1] + [self.rows[0]])

    def test_invalid_cannot_pass(self):
        rows = copy.deepcopy(self.rows)
        rows[0].update(passed=True, valid=False)
        with self.assertRaises(ValueError): r.validate(rows)

    def test_no_pending(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['cost_nano_usd'] = None
        with self.assertRaises(ValueError): r.validate(rows)

    def test_null_logical_duration_retained(self):
        self.assertEqual(sum(x['times_ms']['logical_elapsed'] is None for x in self.rows), 1)
        self.assertTrue(all(x['times_ms']['physical_elapsed'] is not None for x in self.rows))


if __name__ == '__main__':
    unittest.main()
