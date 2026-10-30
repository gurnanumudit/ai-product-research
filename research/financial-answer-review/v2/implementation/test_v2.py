"""Version2 prospective mechanics, synthetic fixtures only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import runner
from package.numbers import display_quote, citation_matches
from package.checker import CheckReport, check_response
from package.policies import matched_policies, PRIMARY_SEED, TIE_SEEDS
from summarize_pilot import paired_accounting, coefficient_bounds, cluster_uncertainty, summarize
import test_summary as fixtures


class CitationTests(unittest.TestCase):
    def test_display_suffix_no_implicit_scale(self):
        self.assertEqual(display_quote('$ 1.76 billion')[0], display_quote('1.760')[0])
        self.assertTrue(citation_matches('Revenue was $1.76 billion.', '$ 1.76 billion'))
        self.assertFalse(citation_matches('Revenue was $1.76 million.', '$1.76 billion'))

    def test_commas_currency_whitespace_and_leading_decimal(self):
        self.assertTrue(citation_matches('Total | 9,271', '$ 9271'))
        self.assertTrue(citation_matches('value .3 billion', '0.30 billion'))
        self.assertFalse(citation_matches('2020', '20'))

    def test_sign_and_percent_not_erased(self):
        self.assertFalse(citation_matches('(1,200)', '1200'))
        self.assertTrue(citation_matches('(1,200)', '-1200'))
        self.assertFalse(citation_matches('25%', '25'))
        self.assertFalse(citation_matches('25', '25%'))

    def test_multi_numeric_quote_rejected(self):
        with self.assertRaises(ValueError):
            display_quote('12% (12 %)')
        with self.assertRaises(ValueError):
            display_quote('20 million in 2008')

    def test_one_citation_detail_and_one_evidence_category(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        pred = json.loads(fixture.responses[0]['response']['choices'][0]['message']['content'])
        pred['operands'][0].update(quote='2 nonsense', value='3', location_id='unknown')
        result = check_response(fixture.rows[0], pred)
        self.assertEqual(result.warnings, ('arithmetic', 'evidence'))
        self.assertEqual(sum(':o1' in s for s in result.details), 1)

    def test_expanded_value_not_silently_accepted(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        pred = json.loads(fixture.responses[0]['response']['choices'][0]['message']['content'])
        pred.update(answer='2000000', expression='o1')
        pred['operands'][0].update(quote='2 million', value='2000000')
        fixture.rows[0]['locations']['T1'] = '2 million'
        result = check_response(fixture.rows[0], pred)
        self.assertEqual(result.warnings, ('evidence',))


class PhaseTests(unittest.TestCase):
    def test_full_synthetic_dev_dry_preflight(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            inputs, annotations, groups = root / 'inputs.json', root / 'annotations.json', root / 'groups.json'
            budget, protocol, out = root / 'budget.json', root / 'protocol.json', root / 'out'
            runner.save_json(inputs, [{'id': str(i), 'question': 'What is two?', 'locations': {'T1': '2'}} for i in range(200)])
            runner.save_json(annotations, {'records': []})
            runner.save_json(groups, {'selected': []})
            runner.save_json(budget, self.budget())
            runner.save_json(protocol, {'scope': 'synthetic only'})
            args = ['runner.py', '--inputs', str(inputs), '--adjudication', str(annotations),
                    '--groups', str(groups), '--budget', str(budget), '--protocol', str(protocol),
                    '--phase', 'dev', '--expected-count', '200', '--verification', 'both', '--out', str(out)]
            with patch('sys.argv', args), patch('builtins.print'):
                runner.main()
            template = json.loads((out / 'approval-template.json').read_text())
            self.assertFalse(template['approved'])
            self.assertEqual(template['planned'], 200)
            self.assertEqual(len(template['request_sha256']), 200)
            self.assertEqual(set(template['files']), set(runner.REQUIRED_FILES))
            self.assertEqual(json.loads((out / 'preflight.json').read_text())['calls'], 0)

    def test_wire_byte_cap_not_only_decoded_unicode_bytes(self):
        from unittest.mock import Mock
        row = {'id': 'synthetic', 'question': 'q', 'locations': {'T1': '\u2603' * 20000}}
        with patch('tiktoken.get_encoding', return_value=Mock(encode=lambda *a, **k: [])):
            with self.assertRaises(ValueError): runner.inspect_requests([row])

    def budget(self):
        return {'schema_version': 1, 'total_cap_usd': '40', 'prior_spend_usd': '0.140064',
                'phases': {'dev': {'max_attempts': 200, 'reserve_usd': '6'},
                           'test': {'max_attempts': 1147, 'reserve_usd': '33.859936'}}}

    def load_budget(self, value):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'budget.json'
            runner.save_json(path, value)
            return runner.load_budget(path)

    def test_inclusive_budget(self):
        self.assertEqual(self.load_budget(self.budget())['prior_spend_usd'], '0.140064')
        bad = self.budget(); bad['phases']['test']['reserve_usd'] = '34'
        with self.assertRaises(ValueError): self.load_budget(bad)
        bad = self.budget(); bad['prior_spend_usd'] = '0'
        with self.assertRaises(ValueError): self.load_budget(bad)

    def test_phase_counts_and_candidate_gate(self):
        budget = self.budget()
        runner.phase_check('dev', 200, 'both', [.02] * 200, budget)
        runner.phase_check('test', 1147, 'count', [.02] * 1147, budget)
        for phase, n, candidate in [('dev', 199, 'both'), ('dev', 200, 'count'), ('test', 1148, 'count'), ('test', 1147, 'both')]:
            with self.assertRaises(ValueError): runner.phase_check(phase, n, candidate, [.02] * n, budget)
        with self.assertRaises(ValueError): runner.phase_check('dev', 200, 'both', [.04] * 200, budget)

    def test_phase_markers_and_budget_lock(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'BASE', Path(folder) / 'implementation'):
            path = Path(folder) / 'approval.json'
            runner.save_json(path, {'budget_sha256': 'a' * 64})
            runner.consume_approval(path, Path(folder) / 'dev', 'dev')
            runner.consume_approval(path, Path(folder) / 'test', 'test')
            with self.assertRaises(FileExistsError): runner.consume_approval(path, Path(folder) / 'another', 'dev')
            other = Path(folder) / 'other.json'
            runner.save_json(other, {'budget_sha256': 'b' * 64})
            with self.assertRaises(ValueError): runner.consume_approval(other, Path(folder) / 'another', 'test')

    def test_general_counts(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'inputs.json'
            rows = [dict(fixture.rows[0], id=str(i)) for i in range(200)]
            runner.save_json(path, rows)
            self.assertEqual(len(runner.load_inputs(path, 200)), 200)
            with self.assertRaises(ValueError): runner.load_inputs(path, 199)


class PairedInferenceTests(unittest.TestCase):
    def test_same_unknown_cancels(self):
        p = {'feasible': True, 'accepted_ids': ['u']}
        result = paired_accounting(p, p, {'u': {'numerical_status': 'unknown_reference'}}, 1)
        self.assertEqual(result['accounting_envelope']['lower'], 0)
        self.assertEqual(result['accounting_envelope']['upper'], 0)

    def test_duplicated_unknown_opposite_coefficients_cancel(self):
        self.assertEqual(coefficient_bounds(['u0'], ['u1'], {'u0': 'u', 'u1': 'u'},
                                           {'u': 'unknown_reference'}, 2), (0, 0))

    def test_known_paired_sign_and_unknown_directions(self):
        bounds = coefficient_bounds([], ['w'], {'w': 'w'}, {'w': 'known_numeric_error'}, 10)
        self.assertEqual(bounds, (-.1, -.1))
        bounds = coefficient_bounds(['u'], [], {'u': 'u'}, {'u': 'unknown_reference'}, 10)
        self.assertEqual(bounds, (0, .1))

    def test_two_rules_and_frozen_seeds(self):
        reports = [CheckReport(str(i), True, .9, ('evidence', 'unused') if i < 5 else ('arithmetic',)) for i in range(10)]
        decisions = matched_policies(reports, 2)
        self.assertTrue(all(int(i) < 5 for i in decisions['verification_count'].review_ids))
        self.assertTrue(all(int(i) >= 5 for i in decisions['verification_priority'].review_ids))
        self.assertEqual(PRIMARY_SEED, 'finqa-v2-primary-20261012')
        self.assertEqual(len(TIE_SEEDS), 100)

    def test_cluster_retention_rerank_budget_and_repeatability(self):
        reports = [CheckReport(str(i), True, .5, ('arithmetic',) if i % 2 else ()) for i in range(10)]
        output = [{'id': r.id, 'numerical_status': 'known_numeric_error' if int(r.id) % 2 else 'known_correct'} for r in reports]
        groups = {r.id: 'small' if int(r.id) < 2 else 'large' for r in reports}
        a = cluster_uncertainty(reports, output, groups, 'count', replicates=30)
        b = cluster_uncertainty(reports, output, groups, 'count', replicates=30)
        self.assertEqual(a, b)
        records = a['comparisons']['verification_count']['replicate_records']
        self.assertTrue(all(r['N'] in (4, 10, 16) and r['K'] == r['N'] // 5 for r in records))
        self.assertEqual(len(records), 30)

    def test_infeasible_replicates_retained(self):
        reports = [CheckReport(str(i), i >= 2, .9 if i >= 2 else None) for i in range(10)]
        output = [{'id': r.id, 'numerical_status': 'unknown_reference'} for r in reports]
        groups = {r.id: 'fail' if int(r.id) < 2 else 'good' for r in reports}
        result = cluster_uncertainty(reports, output, groups, 'count', replicates=30)
        self.assertGreater(result['infeasible_replicates'], 0)
        records = result['comparisons']['verification_count']['replicate_records']
        self.assertEqual(len(records), 30)
        self.assertTrue(all((r['lower'], r['upper']) == (-1, 1) for r in records if r['status'].startswith('infeasible')))

    def test_missing_and_single_group_inference_unavailable(self):
        reports = [CheckReport(str(i), True, .9) for i in range(5)]
        output = [{'id': r.id, 'numerical_status': 'known_correct'} for r in reports]
        self.assertEqual(cluster_uncertainty(reports, output, {}, 'count')['status'], 'unavailable')
        self.assertEqual(cluster_uncertainty(reports, output, {r.id: 'one' for r in reports}, 'count')['status'], 'unavailable')

    def test_default_thousand_replicates(self):
        reports = [CheckReport(str(i), True, .9) for i in range(10)]
        output = [{'id': r.id, 'numerical_status': 'known_correct'} for r in reports]
        result = cluster_uncertainty(reports, output, {r.id: r.id for r in reports}, 'count')
        self.assertEqual(result['replicates'], 1000)
        self.assertEqual(result['comparisons']['verification_count']['approximate_95pct_uncertainty_envelope'], [0, 0])

    def test_dev_selection_exact_tie_defaults_count(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        result = summarize(fixture.rows, fixture.annotations, fixture.responses, verification='both', tie_sensitivity=False)
        self.assertEqual(result['development_selection']['selected'], 'count')

    def test_seed_objectives_exact_ties_retain_primary_choice(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        result = summarize(fixture.rows, fixture.annotations, fixture.responses)
        self.assertEqual(result['development_selection']['selected'], 'count')
        self.assertEqual([r['seed'] for r in result['tie_sensitivity']], list(TIE_SEEDS))
        for seed in result['tie_sensitivity']:
            self.assertEqual(seed['development_selection']['selected'], 'count')
            self.assertEqual(set(seed['candidate_objectives']), {'count', 'priority'})
            for objective in seed['candidate_objectives'].values():
                self.assertEqual(objective, {'feasible': True, 'accepted_known_numeric_errors': 0,
                    'accepted_unresolved': 0, 'objective_numerator': 0, 'denominator': 50})

    def test_seed_choice_instability_reports_existing_objectives(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        rows = fixture.rows[:10]
        annotations = {'records': fixture.annotations['records'][:10]}
        annotations['records'][1].update(qualified=False, scoring=None, status='unqualified')
        responses = [fixture.record(str(i), answer='3' if i in (0, 5) else '2') for i in range(10)]
        reports = {str(i): CheckReport(str(i), True, .9,
                   ('evidence', 'unused') if i < 5 else ('arithmetic',)) for i in range(10)}
        with patch('summarize_pilot.check_response', side_effect=lambda item, content: reports[item['id']]):
            result = summarize(rows, annotations, responses)
        choices = set()
        for sensitivity in result['tie_sensitivity']:
            decisions = matched_policies(list(reports.values()), 2, seed=sensitivity['seed'])
            objectives = sensitivity['candidate_objectives']
            for candidate in ('count', 'priority'):
                accepted = set(decisions['verification_' + candidate].accepted_ids)
                errors, unresolved = len(accepted & {'0', '5'}), int('1' in accepted)
                self.assertEqual(objectives[candidate], {'feasible': True,
                    'accepted_known_numeric_errors': errors, 'accepted_unresolved': unresolved,
                    'objective_numerator': errors + unresolved, 'denominator': 10})
            expected = min(('count', 'priority'), key=lambda c: (
                objectives[c]['objective_numerator'], c != 'count'))
            self.assertEqual(sensitivity['development_selection']['selected'], expected)
            choices.add(expected)
        self.assertEqual(choices, {'count', 'priority'})

    def test_seed_infeasible_objectives_are_null_not_zero(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        result = summarize(fixture.rows, fixture.annotations, fixture.responses[:39])
        for seed in result['tie_sensitivity']:
            self.assertIsNone(seed['development_selection']['selected'])
            for objective in seed['candidate_objectives'].values():
                self.assertEqual(objective, {'feasible': False, 'accepted_known_numeric_errors': None,
                    'accepted_unresolved': None, 'objective_numerator': None, 'denominator': 50})

    def test_final_candidate_sensitivity_does_not_reselect(self):
        fixture = fixtures.SummaryTests(); fixture.setUp()
        result = summarize(fixture.rows, fixture.annotations, fixture.responses, verification='count')
        self.assertNotIn('development_selection', result)
        for seed in result['tie_sensitivity']:
            self.assertEqual(set(seed['candidate_objectives']), {'count'})
            self.assertNotIn('development_selection', seed)


if __name__ == '__main__': unittest.main()
