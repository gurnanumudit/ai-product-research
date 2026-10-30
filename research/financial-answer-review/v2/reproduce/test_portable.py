"""Synthetic-only checks for portability and non-overwriting output behavior."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from safe_output import fresh_output
import assemble_annotations as assemble
import prepare_dev

spec = importlib.util.spec_from_file_location('portable_training', HERE / 'training_check.py')
training = importlib.util.module_from_spec(spec)
spec.loader.exec_module(training)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class PortableTests(unittest.TestCase):
    def source_archive(self, root):
        root.mkdir()
        rows = [{'id': str(i), 'question': 'Synthetic question', 'locations': {'T1': '0.1 and 0.2'}} for i in range(200)]
        decisions = [{'i': i, 'formula': '0.1+0.2', 'unit': 'USD', 'scale': '1',
                      'evidence': ['T1'], 'reason': 'Synthetic decision only'} for i in range(200)]
        first = root / 'source-first-decisions.jsonl'
        first.write_text(''.join(json.dumps(row) + '\n' for row in decisions))
        save(root / 'inputs.json', rows)
        save(root / 'gold.json', [{'id': r['id'], 'original_qa': {'answer': 'synthetic'}} for r in rows])
        save(root / 'selection.json', {'selected': [{'id': r['id']} for r in rows]})
        save(root / 'reference-reconciliation.json', [])
        save(root / 'source/dev.json', [])
        return hashlib.sha256(first.read_bytes()).hexdigest()

    def assemble_args(self, root, out, digest):
        return ['assemble_annotations.py', '--data-dir', str(root),
                '--source-first-sha256', digest, '--out', str(out)]

    def test_existing_output_rejected_before_input_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); output = root / 'out'; output.mkdir()
            with patch('sys.argv', ['training_check.py', '--stage', str(root / 'absent'), '--out', str(output)]), patch.object(training, 'load_inputs') as loader:
                with self.assertRaises(ValueError): training.main()
                loader.assert_not_called()
            with patch('sys.argv', self.assemble_args(root / 'absent', output, '0' * 64)), patch.object(assemble, 'sha') as reader:
                with self.assertRaises(ValueError): assemble.main()
                reader.assert_not_called()

    def test_symlink_targets_and_ancestors_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); actual = root / 'actual'; actual.mkdir()
            alias = root / 'alias'; alias.symlink_to(actual, target_is_directory=True)
            for output in (alias, alias / 'fresh'):
                with self.assertRaises(ValueError): fresh_output(output)
            self.assertEqual(list(actual.iterdir()), [])

    def test_outputs_cannot_be_inside_input_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with self.assertRaises(ValueError): fresh_output(root / 'new', root)
            self.assertFalse((root / 'new').exists())

    def test_annotation_arithmetic_and_originals_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'inputs'; digest = self.source_archive(root)
            out = root.parent / 'fresh'; original = (root / 'inputs.json').read_bytes()
            with patch('sys.argv', self.assemble_args(root, out, digest)), patch('builtins.print'):
                assemble.main()
            result = json.loads((out / 'annotations.json').read_text())
            self.assertEqual(len(result['records']), 200)
            self.assertEqual(result['records'][0]['exact_rational'], {'numerator': '3', 'denominator': '10'})
            self.assertEqual(result['records'][0]['scoring']['value'], '0.3')
            self.assertEqual(result['records'][0]['scoring']['tolerance'], '0.005')
            self.assertEqual(result['review_state'], 'METHODS_REVIEW_PENDING')
            self.assertEqual((root / 'inputs.json').read_bytes(), original)
            self.assertFalse((root / 'annotations.json').exists())
            with patch('sys.argv', self.assemble_args(root, out, digest)):
                with self.assertRaises(ValueError): assemble.main()

    def test_hash_mismatch_produces_no_annotations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'inputs'; self.source_archive(root); out = root.parent / 'fresh'
            with patch('sys.argv', self.assemble_args(root, out, '0' * 64)):
                with self.assertRaises(ValueError): assemble.main()
            self.assertFalse((out / 'annotations.json').exists())

    def test_truncated_parallel_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'inputs'; digest = self.source_archive(root); out = root.parent / 'fresh'
            rows = json.loads((root / 'gold.json').read_text()); save(root / 'gold.json', rows[:-1])
            with patch('sys.argv', self.assemble_args(root, out, digest)):
                with self.assertRaises(ValueError): assemble.main()
            self.assertFalse((out / 'annotations.json').exists())

    def test_explicit_stage_training_replay_is_non_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve() / 'stage'; out = root.parent / 'fresh'
            rows = [{'id': str(i), 'question': 'What is two?', 'locations': {'T1': '2'}} for i in range(50)]
            save(root / 'data/inputs.json', rows)
            save(root / 'runs/pilot-01/summary.json', {'rows': [{'id': r['id'], 'checker': {'usable': True, 'warnings': []}} for r in rows]})
            answer = {'answer': '2', 'unit': 'USD', 'scale': '1', 'confidence': .9,
                      'operands': [{'id': 'o1', 'location_id': 'T1', 'quote': '2', 'value': '2'}],
                      'constants': [], 'expression': 'o1'}
            for i, row in enumerate(rows, 1):
                save(root / f'runs/pilot-01/{i:02d}-response.json', {'id': row['id'], 'response': {'choices': [{'message': {'content': json.dumps(answer)}}]}})
            args = ['training_check.py', '--stage', str(root), '--out', str(out)]
            with patch('sys.argv', args): training.main()
            result = json.loads((out / 'training-diagnostics.json').read_text())
            self.assertEqual((result['planned'], result['v1_any_concern'], result['v2_any_concern']), (50, 0, 0))
            with patch('sys.argv', args):
                with self.assertRaises(ValueError): training.main()

    def test_prepare_existing_destination_stops_before_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); protocol = root / 'protocol.json'; save(protocol, {})
            with patch('sys.argv', ['prepare_dev.py', '--protocol', str(protocol), '--out', str(root)]), patch.object(prepare_dev.subprocess, 'run') as network:
                with self.assertRaises(SystemExit): prepare_dev.main()
                network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
