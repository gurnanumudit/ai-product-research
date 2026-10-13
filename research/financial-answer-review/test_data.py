"""Offline training-intake isolation tests; never downloads or calls a model."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import prepare_data as intake

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

class IntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((DATA/'source/train.json').read_text())
        cls.inputs = json.loads((DATA/'inputs.json').read_text())
        cls.gold = json.loads((DATA/'gold.json').read_text())
        cls.selection = json.loads((DATA/'selection.json').read_text())
        cls.by_id = {r['id']: r for r in cls.source}

    def test_source_pin(self):
        self.assertEqual(len(self.source), 6251)
        self.assertEqual(hashlib.sha256((DATA/'source/train.json').read_bytes()).hexdigest(), intake.TRAIN_SHA)

    def test_numeric_safety(self):
        for value in [True, False, None, [], 'nan', 'Infinity', float('inf')]:
            self.assertIsNone(intake.numeric(value))
        self.assertEqual(intake.numeric('-0.02597'), '-0.02597')

    def test_selection_order_independence(self):
        selected, _, _ = intake.select(self.source)
        reversed_selected, _, _ = intake.select(list(reversed(self.source)))
        self.assertEqual([r['id'] for r in selected], [r['id'] for r in reversed_selected])
        self.assertEqual([r['id'] for r in selected], [r['id'] for r in self.inputs])

    def test_frozen_quotas(self):
        self.assertEqual(len(self.inputs), 50)
        self.assertEqual(len({r['id'] for r in self.inputs}), 50)
        counts = collections.Counter(intake.stratum(self.by_id[r['id']])[0] for r in self.inputs)
        self.assertEqual(dict(counts), intake.QUOTAS)

    def test_exact_neutral_context(self):
        for item in self.inputs:
            self.assertEqual(set(item), {'id', 'question', 'locations'})
            source = self.by_id[item['id']]
            self.assertEqual(item['question'], source['qa']['question'])
            self.assertEqual(item['locations'], intake.locations(source))
            self.assertEqual(len(item['locations']), len(source['pre_text'])+len(source['post_text'])+len(source['table']))
            if source['table']:
                self.assertEqual(item['locations']['table:row:0'], ' | '.join(source['table'][0]))

    def test_context_independent_of_gold(self):
        for item in self.inputs:
            source = copy.deepcopy(self.by_id[item['id']])
            original = intake.locations(source)
            source['qa'] = {'program': 'MALICIOUS', 'gold_inds': {'table_0':'HIGHLIGHT'}, 'exe_ans': 999}
            self.assertEqual(intake.locations(source), original)
            del source['qa']
            self.assertEqual(intake.locations(source), original)

    def test_original_references_preserved_separately(self):
        self.assertEqual([r['id'] for r in self.gold], [r['id'] for r in self.inputs])
        for gold in self.gold:
            qa = self.by_id[gold['id']]['qa']
            for field in ['exe_ans', 'answer', 'program', 'program_re', 'gold_inds']:
                self.assertEqual(gold[field], qa.get(field))

    def test_bad_schema_rejected(self):
        source = copy.deepcopy(self.source[0]); source['table'] = ['not a row']
        with self.assertRaises(ValueError): intake.locations(source)

    def test_existing_destination_refused_before_acquisition(self):
        result = subprocess.run([sys.executable, str(ROOT/'prepare_data.py'), '--out', str(DATA)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Refuse existing destination', result.stderr)

    def test_qualification_preserves_denominator(self):
        path = DATA/'reference-qualification.json'
        if not path.exists(): self.skipTest('Qualification artifact not yet saved')
        audit = json.loads(path.read_text())
        self.assertEqual([r['id'] for r in audit['records']], [r['id'] for r in self.gold])
        for audited, original in zip(audit['records'], self.gold):
            self.assertEqual(audited['original_reference'], original)
            if 'scoring' in audited:
                self.assertEqual(audited['status'], 'manual_consistent')
                self.assertTrue({'value','unit','scale','provenance','tolerance','tolerance_provenance'} <= set(audited['scoring']))

if __name__ == '__main__': unittest.main(verbosity=2)
