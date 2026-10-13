"""Synthetic reporting tests: no dataset, reference audit, network or model calls."""
import copy
import unittest
from summarize_pilot import summarize


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'id': str(i), 'question': 'What is the value?', 'locations': {'T1': '2'}} for i in range(50)]
        reference = {'qualified': True, 'value': '2', 'unit': 'USD', 'scale': '1',
                     'provenance': 'synthetic', 'tolerance': '0', 'tolerance_provenance': 'exact synthetic'}
        self.annotations = {'records': [{'id': str(i), 'qualified': True, 'status': 'qualified',
                                        'scoring': copy.deepcopy(reference)} for i in range(50)]}
        self.responses = [self.record(str(i)) for i in range(50)]

    def record(self, identity, answer='2', unit='USD'):
        import json
        response = {'answer': answer, 'unit': unit, 'scale': '1', 'confidence': .8,
                    'operands': [{'id': 'o1', 'location_id': 'T1', 'quote': '2', 'value': '2'}],
                    'constants': [], 'expression': 'o1'}
        return {'id': identity, 'status': 'received', 'response': {'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(response)}}]}}

    def test_all_fifty_and_matched_ten(self):
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(result['N_planned'], 50)
        self.assertEqual(result['M_numerically_comparable'], 50)
        self.assertEqual(result['C_known_correct'], 50)
        for policy in result['policies'].values():
            self.assertEqual(len(policy['review_ids']), 10)
            self.assertEqual(len(policy['accepted_ids']), 40)

    def test_missing_outputs_are_not_known_numeric_errors(self):
        result = summarize(self.rows, self.annotations, self.responses[:40])
        self.assertEqual(len(result['rows']), 50)
        self.assertEqual(result['operational_failures_or_abstentions'], 10)
        self.assertEqual(result['W_known_numeric_errors'], 0)
        self.assertEqual(result['M_numerically_comparable'], 40)
        for policy in result['policies'].values():
            self.assertTrue(policy['feasible'])
            self.assertEqual(set(policy['review_ids']), {str(i) for i in range(40, 50)})

    def test_eleven_missing_infeasible_not_zero_error_claim(self):
        result = summarize(self.rows, self.annotations, self.responses[:39])
        for policy in result['policies'].values():
            self.assertFalse(policy['feasible'])
            self.assertIsNone(policy['escaped_error_accounting_envelope'])

    def test_unqualified_references_do_not_enter_policies(self):
        before = summarize(self.rows, self.annotations, self.responses)
        self.annotations['records'][0].update(qualified=False, status='unqualified', scoring=None)
        after = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(after['Q_qualified_references'], 49)
        self.assertEqual(after['rows'][0]['numerical_status'], 'unknown_reference')
        for policy in before['policies']:
            self.assertEqual(before['policies'][policy]['review_ids'], after['policies'][policy]['review_ids'])

    def test_unit_contract_mismatch_not_known_error(self):
        self.responses[0] = self.record('0', unit='USD/year')
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(result['W_known_numeric_errors'], 0)
        self.assertEqual(result['unit_contract_mismatch_ids'], ['0'])
        self.assertEqual(result['M_numerically_comparable'], 49)

    def test_known_wrong_and_unknown_accounting_envelope(self):
        self.responses = [self.record(str(i), answer='3') for i in range(50)]
        for record in self.annotations['records'][:15]:
            record.update(qualified=False, scoring=None, status='unqualified')
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(result['W_known_numeric_errors'], 35)
        for policy in result['policies'].values():
            interval = policy['escaped_error_accounting_envelope']
            self.assertEqual(interval['upper_numerator'], 40)
            self.assertEqual(interval['denominator'], 50)
            self.assertEqual(interval['lower_numerator'], policy['accepted_known_numeric_errors'])

    def test_unknown_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            summarize(self.rows, self.annotations, self.responses + [self.responses[0]])
        with self.assertRaises(ValueError):
            summarize(self.rows, self.annotations, [self.record('not-planned')])

    def test_missing_annotation_retained_unknown(self):
        self.annotations['records'].pop()
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(len(result['rows']), 50)
        self.assertEqual(result['rows'][-1]['annotation_status'], 'missing_annotation')

    def test_malformed_and_refusal_are_common_mandatory(self):
        self.responses[0]['response']['choices'][0]['message']['content'] = 'not json'
        self.responses[1]['response']['choices'][0]['message']['refusal'] = 'synthetic'
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(result['operational_failures_or_abstentions'], 2)
        self.assertEqual(result['W_known_numeric_errors'], 0)
        for policy in result['policies'].values():
            self.assertTrue({'0', '1'}.issubset(policy['mandatory_ids']))

    def test_crashed_request_is_explicit(self):
        result = summarize(self.rows, self.annotations, self.responses[1:], [{'id': '0'}])
        self.assertEqual(result['rows'][0]['operational_status'], 'attempt_without_response')

    def test_invalid_derivation_does_not_change_numeric_correctness(self):
        import json
        message = self.responses[0]['response']['choices'][0]['message']
        prediction = json.loads(message['content'])
        prediction['expression'] = 'o1 ** o1'
        message['content'] = json.dumps(prediction)
        result = summarize(self.rows, self.annotations, self.responses)
        self.assertEqual(result['rows'][0]['numerical_status'], 'known_correct')
        self.assertFalse(result['rows'][0]['checker']['usable'])


if __name__ == '__main__':
    unittest.main()
