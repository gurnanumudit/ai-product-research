"""Offline transport guards, with synthetic inputs only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import runner


class TransportGuards(unittest.TestCase):
    def rows(self):
        return [{"id": str(i), "question": "What is two plus two?", "locations": {"T1": "2"}}
                for i in range(50)]

    def load(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "inputs.json"
            path.write_text(json.dumps(rows))
            return runner.load_inputs(path)

    def test_exact_fifty(self):
        self.assertEqual(len(self.load(self.rows())), 50)

    def test_wrong_count(self):
        with self.assertRaises(ValueError):
            self.load(self.rows()[:49])

    def test_duplicate_rejected(self):
        rows = self.rows()
        rows[-1] = rows[0]
        with self.assertRaises(ValueError):
            self.load(rows)

    def test_gold_field_rejected(self):
        rows = self.rows()
        rows[0]['answer'] = 4
        with self.assertRaises(ValueError):
            self.load(rows)

    def test_locations_map_required(self):
        rows = self.rows()
        rows[0]['locations'] = []
        with self.assertRaises(ValueError):
            self.load(rows)

    def test_exclusive_write(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            runner.save_json(path, {'x': 1})
            with self.assertRaises(FileExistsError):
                runner.save_json(path, {'x': 2})

    def test_budget_forecast(self):
        forecast = 1397 * (runner.MAX_ESTIMATED_INPUT * runner.INPUT_PRICE +
                           runner.MAX_OUTPUT * runner.OUTPUT_PRICE)
        self.assertLess(forecast, 40)
        self.assertLess(50 * ((runner.MAX_REQUEST_BYTES + 4096) * runner.INPUT_PRICE +
                             runner.MAX_OUTPUT * runner.OUTPUT_PRICE), 5)

    def test_endpoint_fixed(self):
        self.assertEqual(runner.ENDPOINT, 'https://ai-gateway.vercel.sh/v1/chat/completions')

    def body(self, model='gpt-5.4-mini-2026-03-17'):
        return {'model': model, 'usage': {'prompt_tokens': 100, 'completion_tokens': 50},
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': '{}'}}]}

    def test_first_model_wrong_family_rejected(self):
        record, stop, model = runner.assess_body(self.body('gpt-4o'), .02, None)
        self.assertEqual(stop, 'returned_model_unexpected_missing_or_changed')
        self.assertIsNone(model)

    def test_expected_first_model_and_stability(self):
        record, stop, model = runner.assess_body(self.body(), .02, None)
        self.assertIsNone(stop)
        self.assertEqual(model, 'gpt-5.4-mini-2026-03-17')
        self.assertIsNotNone(runner.assess_body(self.body('gpt-5.4-mini'), .02, model)[1])

    def test_missing_usage_reserved_and_stops(self):
        body = self.body()
        del body['usage']
        record, stop, _ = runner.assess_body(body, .02, None)
        self.assertEqual(stop, 'usage_missing_or_invalid')
        self.assertEqual(record['accounted_usd'], .02)

    def test_boolean_usage_rejected(self):
        body = self.body()
        body['usage']['prompt_tokens'] = True
        self.assertEqual(runner.assess_body(body, .02, None)[1], 'usage_missing_or_invalid')

    def test_usage_over_bound_stops(self):
        body = self.body()
        body['usage']['completion_tokens'] = runner.MAX_OUTPUT + 1
        self.assertEqual(runner.assess_body(body, .02, None)[1], 'observed_usage_exceeds_bound')

    def test_nonobject_body(self):
        self.assertEqual(runner.assess_body([], .02, None)[1], 'invalid_response_body')

    def test_refusal_incomplete_missing_not_answer(self):
        body = self.body()
        body['choices'][0]['message']['refusal'] = 'No'
        self.assertEqual(runner.response_content(body)[1], 'refusal')
        del body['choices'][0]['message']['refusal']
        body['choices'][0]['finish_reason'] = 'length'
        self.assertEqual(runner.response_content(body)[1], 'incomplete_or_unexpected_finish')
        body['choices'] = []
        self.assertIsNone(runner.response_content(body)[0])

    def test_complete_mandatory_approval_fields(self):
        expected = {'files': {name: 'sha' for name in runner.REQUIRED_FILES}, 'model': runner.MODEL,
                    'ids': [str(i) for i in range(50)], 'adjudication_sha256': 'frozen'}
        approval = {**expected, 'approved': True, 'hq_decision': 'reviewed-hq-gate'}
        runner.validate_approval(approval, expected)
        with self.assertRaises(ValueError):
            runner.validate_approval({**approval, 'files': {}}, expected)
        with self.assertRaises(ValueError):
            runner.validate_approval({**approval, 'ids': expected['ids'][::-1]}, expected)
        with self.assertRaises(ValueError):
            runner.validate_approval({**approval, 'approved': False}, expected)
        with self.assertRaises(ValueError):
            runner.validate_approval({**approval, 'adjudication_sha256': 'changed'}, expected)

    def test_required_set_covers_every_local_module(self):
        names = {str(p.relative_to(runner.BASE)) for p in (runner.BASE / 'package').glob('*.py')}
        self.assertTrue(names.issubset(runner.REQUIRED_FILES))
        self.assertIn('summarize_pilot.py', runner.REQUIRED_FILES)

    def test_consumed_approval_cannot_restart_new_directory(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(runner, 'BASE', Path(folder) / 'implementation'):
            approval = Path(folder) / 'approval.json'
            runner.save_json(approval, {'approved': True, 'budget_sha256': '0' * 64})
            runner.consume_approval(approval, Path(folder) / 'run1')
            with self.assertRaises(FileExistsError):
                runner.consume_approval(approval, Path(folder) / 'run2')

    def test_intent_durable_before_network_and_http_no_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            def post(*args, **kwargs):
                self.assertTrue((out / '01-request.json').is_file())
                intent = json.loads((out / '01-request.json').read_text())
                self.assertTrue(intent['may_have_been_sent'])
                self.assertFalse(kwargs['allow_redirects'])
                return Mock(status_code=500)
            session = Mock()
            session.post.side_effect = post
            resources = runner.run_calls(self.rows(), [{}] * 50, [.02] * 50, out, session, 'synthetic')
            self.assertEqual(session.post.call_count, 1)
            self.assertEqual(resources['unattempted'], 49)
            self.assertEqual(resources['list_price_plus_unresolved_reserves_usd'], .02)

    def test_transport_exception_no_retry_and_reserved(self):
        import requests
        with tempfile.TemporaryDirectory() as folder:
            session = Mock()
            session.post.side_effect = requests.Timeout('synthetic')
            resources = runner.run_calls(self.rows(), [{}] * 50, [.02] * 50, Path(folder), session, 'synthetic')
            self.assertEqual(session.post.call_count, 1)
            self.assertEqual(resources['list_price_plus_unresolved_reserves_usd'], .02)

    def test_fifty_success_maximum(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Mock()
            response = Mock(status_code=200)
            response.json.return_value = self.body()
            session.post.return_value = response
            with patch('builtins.print'):
                resources = runner.run_calls(self.rows(), [{}] * 50, [.02] * 50, Path(folder), session, 'synthetic')
            self.assertEqual(session.post.call_count, 50)
            self.assertEqual(resources['stop_reason'], 'completed')

    def test_crash_retains_intent_without_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            session = Mock()
            session.post.side_effect = KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):
                runner.run_calls(self.rows(), [{}] * 50, [.02] * 50, Path(folder), session, 'synthetic')
            self.assertTrue((Path(folder) / '01-request.json').exists())
            self.assertFalse((Path(folder) / '01-response.json').exists())


if __name__ == '__main__':
    unittest.main()

