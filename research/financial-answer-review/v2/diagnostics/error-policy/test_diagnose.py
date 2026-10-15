"""Synthetic tests only. No actual audit/policy join or saved response reads."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

import diagnose as d


class ParserTests(unittest.TestCase):
    def audit(self):
        return '''### Known mismatch sample
| Exact ID | Saved response number |
| --- | ---: |
| A/2000/page_1.pdf-1 | 1 |
| A/2000/page_2.pdf-1 | 2 |
| A/2000/page_3.pdf-1 | 3 |
| A/2000/page_4.pdf-1 | 4 |
### Mandatory sample
Not parsed.
### Arithmetic trace roster
`1`.
### Metric and component differences
| Response | Finding |
| ---: | --- |
| 2 | synthetic |
### Precision sign and interpretation differences
| Response | Finding |
| ---: | --- |
| 3 | synthetic |
### Unit and scale differences
Response 4 has a synthetic unit issue.
## Other section
Response 999 is outside scope.
'''

    def test_exact_four_rosters(self):
        rows = d.parse_taxonomy(self.audit(), dict.fromkeys(d.CATEGORIES, 1))
        self.assertEqual([r['category'] for r in rows], list(d.CATEGORIES))
        self.assertEqual([r['response_number'] for r in rows], [1, 2, 3, 4])

    def test_duplicate_missing_and_extra_assignments_fail(self):
        for body in (self.audit().replace('`1`', '`2`'), self.audit().replace('Response 4', 'Response 5'),
                     self.audit().replace('`1`', '`1, 5`'), self.audit().replace('### Arithmetic trace roster', '### Other')):
            with self.subTest(body=body), self.assertRaises(ValueError):
                d.parse_taxonomy(body, dict.fromkeys(d.CATEGORIES, 1))


class MembershipTests(unittest.TestCase):
    def setUp(self):
        self.ids = [f'A/2000/page_{i}.pdf-1' for i in range(4)]
        self.ids.sort(key=lambda i: (d.digest((d.AUDIT_SEED+'\0'+i).encode()), i))
        self.sample = [{'id': i, 'response_number': n+1, 'category': d.CATEGORIES[n]} for n, i in enumerate(self.ids)]
        rows = [{'id': i, 'numerical_status': 'known_numeric_error', 'operational_status': 'complete',
                 'checker': {'usable': n != 0}} for n, i in enumerate(self.ids)]
        self.neutral = {'summary_sha256': d.INPUT_HASHES['summary'],
                        'rows': [{'id': i, 'numerical_status': 'known_numeric_error', 'operational_status': 'complete', 'mandatory': n == 0}
                                 for n, i in enumerate(self.ids)]}
        def policy(review):
            return {'feasible': True, 'budget': 2, 'review_ids': review,
                    'accepted_ids': [i for i in self.ids if i not in review], 'mandatory_ids': [self.ids[0]]}
        self.summary = {'rows': rows, 'N_planned': 4, 'matched_budget': 2, 'verification_candidate': 'priority',
                        'policies': {'verification_priority': policy(self.ids[:2]), 'confidence': policy([self.ids[0], self.ids[2]])}}

    def validate(self):
        return d.validate_sets(self.summary, self.neutral, self.sample, n=4, budget=2, mismatch_n=4, mandatory_n=1)

    def test_membership_and_mandatory_not_double_counted(self):
        _, b, c, m = self.validate()
        rows, table, _, cells = d.join(self.sample, b, c, m, {self.ids[0]: Fraction(1, 100), self.ids[1]: Fraction(1, 20)})
        self.assertEqual([r['membership'] for r in rows], list(d.CELLS))
        total = table[-1]
        self.assertEqual([total[k] for k in d.CELLS], [1, 1, 1, 1])
        self.assertEqual((total['mandatory_within_both'], total['discretionary_both']), (1, 0))
        self.assertEqual((total['reviewed_B'], total['reviewed_confidence']), (2, 2))
        self.assertEqual(cells['neither']['n'], 0)

    def test_duplicate_status_sample_and_candidate_fail(self):
        original = deepcopy(self.summary)
        self.summary['rows'].append(self.summary['rows'][0])
        with self.assertRaises(ValueError): self.validate()
        self.summary = deepcopy(original); self.summary['verification_candidate'] = 'count'
        with self.assertRaises(ValueError): self.validate()
        self.summary = deepcopy(original); self.summary['rows'][0]['numerical_status'] = 'known_correct'
        with self.assertRaises(ValueError): self.validate()
        self.summary = original; self.sample.reverse()
        with self.assertRaises(ValueError): self.validate()

    def test_bad_policy_partition_budget_or_mandatory_fail(self):
        original = deepcopy(self.summary)
        for key, value in [('feasible', False), ('budget', 3), ('review_ids', [self.ids[0], self.ids[0]]),
                           ('accepted_ids', self.ids[:2]), ('mandatory_ids', [])]:
            self.summary = deepcopy(original); self.summary['policies']['confidence'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.validate()


class MagnitudeTests(unittest.TestCase):
    def test_median_even_odd_empty_singleton_and_exact_rounding(self):
        self.assertIsNone(d.stats([])['median'])
        self.assertEqual(d.stats([Fraction(2)])['min'], d.stats([Fraction(2)])['max'])
        self.assertEqual(d.stats([Fraction(1), Fraction(3)])['median']['numerator'], '2')
        self.assertEqual(d.stats([Fraction(5), Fraction(1), Fraction(3)])['median']['numerator'], '3')
        self.assertEqual(d.rounded(Fraction('0.000005'), 5), '0.00001')

    def test_original_aggregate_check_and_failure(self):
        values = [Fraction('0.00510')] + [Fraction('0.00999')]*56 + [Fraction('0.31494')]
        self.assertEqual(d.replicate(values)['n'], 58)
        with self.assertRaises(ValueError): d.replicate(values[:-1])
        values[-1] = Fraction('0.4')
        with self.assertRaisesRegex(ValueError, 'replication failed'): d.replicate(values)


class TraceAndSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]/'implementation'
        cls.helpers = d.load_helpers(root)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve(); self.run = self.root/'run'; self.run.mkdir()
        self.sample, self.neutral, self.hashes = [], {}, {}
        deltas = ['0.00510'] + ['0.00999']*56 + ['0.31494']
        for n in range(1, 71):
            identity = f'SYNTHETIC/2000/page_{n}.pdf-1'; path = self.run/f'{n:02d}-response.json'
            response = {'answer': deltas[n-1] if n <= 58 else '0', 'unit': 'percent' if n <= 58 else 'ratio',
                        'scale': '1', 'confidence': 0.5, 'operands': [{'id': 'o1', 'location_id': 'pre:0', 'quote': '0', 'value': '0'}],
                        'constants': [], 'expression': 'o1'}
            record = {'id': identity, 'attempt': n, 'status': 'received',
                      'response': {'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(response)}}]}}
            path.write_text(json.dumps(record))
            self.hashes[path.name] = d.digest(path.read_bytes())
            self.sample.append({'id': identity, 'response_number': n, 'category': 'arithmetic'})
            self.neutral[identity] = {'response_file': str(path)}
        self.summary = {'provenance': {'response_files': self.hashes}}

    def read(self, log=None):
        return d.read_arithmetic(self.sample, self.neutral, self.summary, self.run, self.helpers, [] if log is None else log)

    def test_exact_70_reads_58_percent_points_not_ratio_error(self):
        log = []; magnitudes, aggregate, units = self.read(log)
        self.assertEqual((len(log), len(magnitudes), aggregate['n']), (70, 58, 58))
        self.assertEqual(units, {'percent': 58, 'ratio': 12})
        self.assertEqual(magnitudes[self.sample[0]['id']], Fraction('0.00510'))

    def test_other_categories_not_read(self):
        fake = {'id': 'SYNTHETIC/2000/page_71.pdf-1', 'response_number': 71, 'category': 'unit_scale'}
        self.sample.append(fake); self.neutral[fake['id']] = {'response_file': str(self.run/'71-response.json')}
        self.assertFalse((self.run/'71-response.json').exists())
        log = []; self.read(log); self.assertEqual(len(log), 70)

    def test_hash_mismatch_stops(self):
        self.hashes['01-response.json'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'hash/size'): self.read()

    def test_embedded_identity_mismatch_stops(self):
        p = self.run/'01-response.json'; record = json.loads(p.read_text()); record['id'] = 'OTHER'
        p.write_text(json.dumps(record)); self.hashes[p.name] = d.digest(p.read_bytes())
        with self.assertRaisesRegex(ValueError, 'embedded identity'): self.read()

    def test_path_escape_and_number_mismatch_stop(self):
        identity = self.sample[0]['id']; self.neutral[identity]['response_file'] = str(self.root/'01-response.json')
        with self.assertRaisesRegex(ValueError, 'path differs'): self.read()
        self.neutral[identity]['response_file'] = str(self.run/'02-response.json')
        with self.assertRaisesRegex(ValueError, 'path differs'): self.read()

    def test_percent_scale_mismatch_stops(self):
        p = self.run/'01-response.json'; record = json.loads(p.read_text())
        response = json.loads(record['response']['choices'][0]['message']['content']); response['scale'] = '1000'
        record['response']['choices'][0]['message']['content'] = json.dumps(response)
        p.write_text(json.dumps(record)); self.hashes[p.name] = d.digest(p.read_bytes())
        with self.assertRaisesRegex(ValueError, 'scale'): self.read()

    def test_existing_symlink_and_nested_output_refused(self):
        with self.assertRaises(ValueError): d.fresh(self.run, [])
        with self.assertRaises(ValueError): d.fresh(self.run/'output', [self.run])
        alias = self.root/'alias'; alias.symlink_to(self.run, target_is_directory=True)
        with self.assertRaises(ValueError): d.fresh(alias/'output', [])
        good = d.fresh(self.root/'fresh', [self.run]); self.assertTrue(good.is_dir())


if __name__ == '__main__':
    unittest.main()
