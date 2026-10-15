import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import analyze as a
from package.policies import PolicyDecision


def payload(answer='10', confidence=0.5):
    if answer is None:
        return {'answer': None, 'unit': '', 'scale': '1', 'confidence': confidence,
                'operands': [], 'constants': [], 'expression': ''}
    return {'answer': answer, 'unit': 'USD', 'scale': '1', 'confidence': confidence,
            'operands': [{'id': 'o1', 'value': '10', 'location_id': 'table', 'quote': '10'}],
            'constants': [], 'expression': 'o1'}


def envelope(value):
    return {'choices': [{'finish_reason': 'stop', 'message': {
        'role': 'assistant', 'content': json.dumps(value)}}]}


def fixture():
    inputs, annotations, responses = [], [], []
    for i in range(40):
        identity = 'synthetic-' + str(i)
        value = payload(None if i == 0 else ('11' if i % 3 == 0 else '10'), i / 40)
        inputs.append({'id': identity, 'question': 'What is the value?', 'locations': {'table': 'Value: 10'}})
        annotations.append({'id': identity, 'original_reference': {'exe_ans': 10, 'program': 'add(5, 5)'}})
        responses.append({'id': identity, 'response': envelope(value)})
    return inputs, annotations, responses


class ScoringTests(unittest.TestCase):
    def test_fractional_percent(self):
        self.assertEqual(a.score({'answer': '12.5', 'unit': 'percent'}, {'exe_ans': .125, 'program': 'divide(1, 8)'}), 'match')

    def test_explicit_percent_points(self):
        self.assertEqual(a.score({'answer': '12.5', 'unit': 'percent'}, {'exe_ans': 12.5, 'program': 'divide(1,8), multiply(#0, const_100)'}), 'match')

    def test_only_final_multiply(self):
        self.assertFalse(a.final_times100('multiply(2, const_100), divide(#0, 3)'))
        self.assertTrue(a.final_times100('multiply(100, #0)'))

    def test_no_closeness_chosen_conversion(self):
        self.assertEqual(a.score({'answer': '12.5', 'unit': 'percent'}, {'exe_ans': 12.5, 'program': 'divide(1,8)'}), 'numeric_nonmatch')

    def test_displayed_money_not_scale_repaired(self):
        self.assertEqual(a.score({'answer': '51', 'unit': 'USD', 'scale': '1000000'}, {'exe_ans': 51, 'program': 'subtract(65.7,14.7)'}), 'match')

    def test_tolerance_boundary(self):
        ref = {'exe_ans': 1, 'program': 'add(1,0)'}
        self.assertEqual(a.score({'answer': '1.005', 'unit': 'USD'}, ref), 'match')
        self.assertEqual(a.score({'answer': '1.005001', 'unit': 'USD'}, ref), 'numeric_nonmatch')

    def test_strict_sensitive(self):
        ref = {'exe_ans': .13924, 'program': 'divide(1,2)'}
        response = {'answer': '13.925', 'unit': 'percent'}
        self.assertEqual(a.score(response, ref), 'match')
        self.assertEqual(a.score(response, ref, strict=True), 'numeric_nonmatch')

    def test_null_separate(self):
        self.assertEqual(a.score({'answer': None}, {'exe_ans': 0, 'program': ''}), 'abstention')

    def test_non_numeric_gold_rejected(self):
        for value in (True, float('inf'), '10'):
            with self.assertRaises(ValueError):
                a.score({'answer': '10', 'unit': 'USD'}, {'exe_ans': value, 'program': ''})


class PipelineTests(unittest.TestCase):
    def test_complete_synthetic_pipeline_and_nested_queues(self):
        result, labels, decisions = a.analyze(*fixture())
        self.assertEqual((result['N'], result['matches'], result['numeric_mismatches'], result['abstentions']), (40, 26, 13, 1))
        self.assertEqual([row['policies']['confidence']['reviewed'] for row in result['results']], [2, 4, 8, 20])
        for name in decisions[5]:
            for low, high in ((5, 10), (10, 20), (20, 50)):
                self.assertLessEqual(set(decisions[low][name].review_ids), set(decisions[high][name].review_ids))

    def test_answer_key_does_not_affect_selection(self):
        inputs, annotations, responses = fixture()
        _, _, original = a.analyze(inputs, annotations, responses)
        changed = copy.deepcopy(annotations)
        for row in changed:
            row['original_reference']['exe_ans'] = 999
        _, _, rerun = a.analyze(inputs, changed, responses)
        self.assertEqual(original, rerun)

    def test_duplicate_and_missing_ids_rejected(self):
        inputs, refs, responses = fixture()
        with self.assertRaises(ValueError):
            a.analyze(inputs + [inputs[0]], refs, responses)
        with self.assertRaises(ValueError):
            a.analyze(inputs, refs, responses[:-1])

    def test_incomplete_response_rejected(self):
        body = envelope(payload())
        body['choices'][0]['finish_reason'] = 'length'
        with self.assertRaises(ValueError):
            a.response_text(body)

    def test_metrics_keep_abstention_in_slot_denominator(self):
        labels = {'a': 'match', 'b': 'numeric_nonmatch', 'c': 'abstention', 'd': 'match'}
        d = PolicyDecision('x', True, 2, ('c',), ('b', 'c'), ('a', 'd'), 'ok')
        m = a.metrics(labels, d)
        self.assertEqual(m['review_precision_per_slot']['percent'], 50)
        self.assertEqual(m['numeric_answer_precision']['percent'], 100)
        self.assertEqual(m['error_capture']['percent'], 100)
        self.assertEqual(m['released_accuracy']['percent'], 100)

    def test_invalid_partition_and_infeasible(self):
        for d in (PolicyDecision('x', True, 1, (), ('a',), ('a',), 'bad'),
                  PolicyDecision('x', False, 0, ('a',), (), (), 'bad')):
            with self.assertRaises(ValueError):
                a.metrics({'a': 'match'}, d)

    def test_fraction_empty(self):
        self.assertIsNone(a.fraction(0, 0)['percent'])
        self.assertAlmostEqual(a.fraction(103, 225)['percent'], 45.7777777778)


class OutputSafetyTests(unittest.TestCase):
    def test_existing_output_refused_before_input_access(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(a, 'digest', side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):
                a.reproduce(Path(tmp) / 'missing-archive', Path(tmp))

    def test_archive_descendant_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                a.fresh_destination(Path(tmp) / 'output', Path(tmp))

    def test_symlink_parent_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'real').mkdir()
            (base / 'link').symlink_to(base / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                a.fresh_destination(base / 'link' / 'out', base / 'archive')


if __name__ == '__main__':
    unittest.main()
