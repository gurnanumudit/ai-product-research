"""Offline transport guards, with synthetic inputs only."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
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


if __name__ == '__main__':
    unittest.main()
