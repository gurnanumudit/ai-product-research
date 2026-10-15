"""Synthetic-only final preparation/assembly tests; no archive or network."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import assemble_test_annotations as assembly
import final_io
import prepare_test as intake


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + '\n')


def source_row(identifier='A/2000/page_1.pdf-1', number='1', text=False, multi=False):
    return {'id': identifier, 'pre_text': ['neutral 1'], 'post_text': ['neutral 2'],
            'table': [['label', 'value'], ['x', '1']],
            'qa': {'question': 'What is x?', 'exe_ans': number, 'answer': 'SYNTHETIC GOLD',
                   'program': 'add(1, 0), divide(#0, 1)' if multi else 'add(1, 0)',
                   'gold_inds': {'text_0' if text else 'table_1': 'SYNTHETIC SUPPORT'}}}


def protocol(n):
    return {'seed': 'synthetic-order', 'source_expected_n': n, 'maximum_selected_n': 1147,
            'strata': ['table_only|single', 'table_only|multi', 'text_involved|single', 'text_involved|multi'],
            'independent_audit': {'seed': 'synthetic-audit', 'n_per_stratum': 20}}


def exposure(ids=None):
    ids = sorted(ids or [])
    return {'groups': {'prior': {'ids': ids,
             'reports': sorted({'/'.join(i.split('/')[:2]) for i in ids}),
             'pages': sorted({i.rsplit('-', 1)[0] for i in ids}),
             'companies': sorted({i.split('/')[0] for i in ids})}},
            'excluded_exact_ids': ids, 'excluded_exact_id_count': len(ids),
            'union_ids_sha256': hashlib.sha256((json.dumps(ids, separators=(',', ':')) + '\n').encode()).hexdigest()}


class FinalIOTests(unittest.TestCase):
    def test_existing_output_refused_before_inputs(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(final_io, 'bindings') as load:
            out = Path(tmp).resolve() / 'existing'; out.mkdir()
            with self.assertRaises(ValueError):
                intake.prepare('/missing/a/source', '/missing/b/protocol', '/missing/c/exposure', '/missing/d/bindings', out)
            with self.assertRaises(ValueError):
                assembly.assemble('/missing/archive', '/missing/bindings', out, 2)
            load.assert_not_called()

    def test_inside_input_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp).resolve() / 'archive'; archive.mkdir()
            with self.assertRaises(ValueError): final_io.destination(archive/'new', [archive])
            self.assertFalse((archive/'new').exists())

    def test_symlink_and_dangling_output_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); (root/'real').mkdir()
            (root/'alias').symlink_to(root/'real', target_is_directory=True)
            (root/'dangling').symlink_to(root/'missing')
            for out in (root/'alias'/'new', root/'dangling'):
                with self.subTest(out=out), self.assertRaises(ValueError):
                    final_io.destination(out, [])

    def test_bindings_exact_nonempty_keys_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'bindings.json'
            for value in ({}, {'source': 'bad'}, {'source': '0'*64, 'other': '0'*64}):
                write(p, value)
                with self.subTest(value=value), self.assertRaises(ValueError): final_io.bindings(p, ['source'])

    def test_bound_read_and_exclusive_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'file'; p.write_bytes(b'12345')
            self.assertEqual(final_io.read_bound(p, final_io.digest(p), 5), b'12345')
            with self.assertRaises(ValueError): final_io.read_bound(p, final_io.digest(p), 4)
            with self.assertRaises(ValueError): final_io.read_bound(p, '0'*64)
            with self.assertRaises(FileExistsError): final_io.save(p, {})
            self.assertEqual(p.read_bytes(), b'12345')


class CensusTests(unittest.TestCase):
    def choose(self, rows, prior=None):
        return intake.census(rows, protocol(len(rows)), exposure(prior), expected_n=len(rows))

    def test_natural_census_without_quota(self):
        rows = [source_row(f'A/2000/page_{i}.pdf-1') for i in range(25)]
        chosen, selected, excluded, audit = self.choose(rows)
        self.assertEqual((len(chosen), len(selected), len(excluded), len(audit)), (25, 25, 0, 20))

    def test_permutation_invariant(self):
        rows = [source_row(f'A/2000/page_{i}.pdf-1') for i in range(8)]
        self.assertEqual(self.choose(rows)[1:], self.choose(rows[::-1])[1:])

    def test_exclude_exact_id_only_and_flag_report(self):
        a, b = source_row(), source_row('A/2000/page_1.pdf-2')
        _, selected, excluded, _ = self.choose([a, b], [a['id']])
        self.assertEqual([r['id'] for r in selected], [b['id']])
        self.assertTrue(selected[0]['exposure_flags']['prior']['report'])
        self.assertEqual(excluded[0]['reason'], 'documented_prior_manual_exposure')

    def test_invalid_metadata_excluded(self):
        rows = [source_row(), source_row('B/2000/page_1.pdf-1', 'NaN'),
                source_row('C/2000/page_1.pdf-1', True), source_row('D/2000/page_1.pdf-1', 'yes')]
        self.assertEqual(len(self.choose(rows)[2]), 3)
        for edit in ('program', 'gold_inds', 'context'):
            bad = source_row('B/2000/page_1.pdf-1')
            if edit == 'context': bad['table'] = [3]
            else: bad['qa'][edit] = '' if edit == 'program' else {}
            self.assertEqual(len(self.choose([source_row(), bad])[2]), 1)

    def test_corrupt_empty_or_oversized_frame_stops(self):
        with self.assertRaises(ValueError): self.choose([source_row(), source_row()])
        with self.assertRaises(ValueError): self.choose([source_row(number='no')])
        p = protocol(1); p['maximum_selected_n'] = 0
        with self.assertRaises(ValueError): intake.census([source_row()], p, exposure(), 1)
        with self.assertRaises(ValueError): intake.census([source_row()], protocol(2), exposure(), 2)

    def test_exposure_union_group_and_binding_consistency(self):
        e = exposure(['A/2000/page_1.pdf-1']); e['protocol_sha256'] = 'a'*64
        intake.validate_exposure(e, 'a'*64)
        for key, value in [('excluded_exact_ids', []), ('excluded_exact_id_count', 0), ('union_ids_sha256', '0'*64)]:
            bad = deepcopy(e); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): intake.validate_exposure(bad, 'a'*64)
        bad = deepcopy(e); bad['groups']['prior']['reports'] = []
        with self.assertRaises(ValueError): intake.validate_exposure(bad, 'a'*64)
        with self.assertRaises(ValueError): intake.validate_exposure(e, 'b'*64)

    def test_offline_file_transform_and_no_gold_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); archive = root/'inputs'; archive.mkdir()
            source = archive/'source.json'; write(source, [source_row()])
            p = protocol(1); p.update(source_sha256=final_io.digest(source), source_expected_bytes=source.stat().st_size)
            pp = archive/'protocol.json'; write(pp, p)
            e = exposure(); e['protocol_sha256'] = final_io.digest(pp)
            ep = archive/'exposure.json'; write(ep, e)
            bp = archive/'bindings.json'; write(bp, {'source': final_io.digest(source), 'protocol': final_io.digest(pp), 'exposure': final_io.digest(ep)})
            before = {x.name: x.read_bytes() for x in archive.iterdir()}
            out = root/'new-output'
            result = intake.prepare(source, pp, ep, bp, out)
            self.assertEqual(result['selected_n'], 1)
            answer_input = json.loads((out/'inputs.json').read_text())
            self.assertEqual(set(answer_input[0]), {'id', 'question', 'locations'})
            self.assertNotIn('SYNTHETIC', json.dumps(answer_input))
            self.assertEqual(before, {x.name: x.read_bytes() for x in archive.iterdir()})
            self.assertEqual(json.loads((out/'reproduction-manifest.json').read_text())['network_requests'], 0)
            self.assertFalse(hasattr(intake, 'acquire'))


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve(); self.archive = self.root/'archive'; self.archive.mkdir()
        self.bp = self.archive/'bindings.json'
        self.rows = [{'id': f'A/2000/page_{i}.pdf-1', 'question': 'Synthetic question', 'locations': {'pre:0': 'Synthetic neutral 1 and 2'}} for i in range(2)]
        self.first = [{'i': 0, 'formula': '1/3', 'unit': 'ratio', 'scale': '1', 'reason': 'Synthetic source decision', 'evidence': ['pre:0']},
                      {'i': 1, 'formula': None, 'unit': None, 'scale': None, 'reason': 'Synthetic ambiguity', 'evidence': ['pre:0']}]
        write(self.archive/'source/test.json', [])
        write(self.archive/'inputs.json', self.rows)
        write(self.archive/'gold.json', [{'id': r['id'], 'original_qa': {'answer': '50%', 'exe_ans': 50, 'program': 'multiply(0.5, const_100)'}} for r in self.rows])
        write(self.archive/'selection.json', {'selected': [{'id': r['id']} for r in self.rows]})
        (self.archive/'source-first-decisions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.first))
        write(self.archive/'SOURCE-FIRST-FREEZE.json', {'source_first_sha256': final_io.digest(self.archive/'source-first-decisions.jsonl')})
        write(self.archive/'source-review-revisions.json', [{'i': 0, 'decision': {'formula': '1/2', 'reason': 'Synthetic reviewed revision'}}])
        write(self.archive/'reference-review-notes.json', [{'i': 0, 'category': 'synthetic_reviewed_category'}])
        self.bind()

    def bind(self):
        write(self.bp, {name: final_io.digest(self.archive/name) for name in assembly.REQUIRED})

    def run_assembly(self, n=2):
        return assembly.assemble(self.archive, self.bp, self.root/'out', n)

    def test_source_first_revision_unknown_and_input_preservation(self):
        before = {name: (self.archive/name).read_bytes() for name in assembly.REQUIRED}
        result = self.run_assembly()
        a, b = result['records']
        self.assertEqual(a['source_first']['formula'], '1/3')
        self.assertEqual(a['adjudication']['formula'], '1/2')
        self.assertEqual((a['scoring']['value'], a['scoring']['tolerance']), ('0.5', '0.00005'))
        self.assertEqual(a['reference_reconciliation']['category'], 'synthetic_reviewed_category')
        self.assertIsNone(b['scoring']); self.assertFalse(b['qualified'])
        self.assertEqual(before, {name: (self.archive/name).read_bytes() for name in assembly.REQUIRED})
        self.assertEqual(result['review_state'], 'METHODS_REVIEW_PENDING')
        self.assertTrue((self.root/'out'/'reproduction-manifest.json').exists())

    def test_exact_count_tolerance(self):
        write(self.archive/'source-review-revisions.json', [{'i': 0, 'decision': {'formula': '2', 'unit': 'count', 'exact_count': True}}]); self.bind()
        self.assertEqual(self.run_assembly()['records'][0]['scoring']['tolerance'], '0')

    def test_named_unit_tolerance(self):
        write(self.archive/'source-review-revisions.json', [{'i': 0, 'decision': {'unit': 'USD'}}]); self.bind()
        self.assertEqual(self.run_assembly()['records'][0]['scoring']['tolerance'], '0.005')

    def test_source_tamper_rejected(self):
        write(self.archive/'inputs.json', [])
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): self.run_assembly()

    def test_first_freeze_rejected(self):
        write(self.archive/'SOURCE-FIRST-FREEZE.json', {'source_first_sha256': '0'*64}); self.bind()
        with self.assertRaisesRegex(ValueError, 'freeze mismatch'): self.run_assembly()

    def test_truncated_or_wrong_expected_frame_rejected(self):
        with self.assertRaisesRegex(ValueError, 'complete expected frame'): self.run_assembly(3)

    def test_duplicate_id_rejected(self):
        self.rows[1]['id'] = self.rows[0]['id']; write(self.archive/'inputs.json', self.rows); self.bind()
        with self.assertRaisesRegex(ValueError, 'Unique'): self.run_assembly()

    def test_reordered_selection_rejected(self):
        write(self.archive/'selection.json', {'selected': [{'id': r['id']} for r in self.rows[::-1]]}); self.bind()
        with self.assertRaisesRegex(ValueError, 'order mismatch'): self.run_assembly()

    def test_duplicate_revision_rejected(self):
        write(self.archive/'source-review-revisions.json', [{'i': 0, 'decision': {}}, {'i': 0, 'decision': {}}]); self.bind()
        with self.assertRaisesRegex(ValueError, 'Duplicate revision'): self.run_assembly()

    def test_out_of_range_revision_rejected(self):
        write(self.archive/'source-review-revisions.json', [{'i': 2, 'decision': {}}]); self.bind()
        with self.assertRaisesRegex(ValueError, 'Invalid revision'): self.run_assembly()

    def test_duplicate_review_note_rejected(self):
        write(self.archive/'reference-review-notes.json', [{'i': 0}, {'i': 0}]); self.bind()
        with self.assertRaisesRegex(ValueError, 'Duplicate review note'): self.run_assembly()

    def test_fractional_power_not_enabled_for_new_archive(self):
        write(self.archive/'source-review-revisions.json', [{'i': 0, 'decision': {'formula': '(3200/100)**(1/5)-1'}}]); self.bind()
        with self.assertRaisesRegex(ValueError, 'original reviewed'): self.run_assembly()


class FinalNumericTests(unittest.TestCase):
    def test_signed_decimal_rational_and_rendering(self):
        self.assertEqual(assembly.rational('(-1.2 + 0.2) / 3'), Fraction(-1, 3))
        value, method = assembly.target(0, '1/8')
        self.assertEqual(value, '0.125'); self.assertEqual(method['denominator'], '8')

    def test_non_arithmetic_nodes_and_zero_division_rejected(self):
        for expression in ('abs(-1)', 'x+1', 'True', '[1][0]', '2**3'):
            with self.subTest(expression=expression), self.assertRaises(ValueError): assembly.rational(expression)
        with self.assertRaises(ZeroDivisionError): assembly.rational('1/0')

    def test_restricted_cagr_numeric_agreement(self):
        value, method = assembly.target(685, '(3200/100)**(1/5)-1')
        self.assertLess(abs(Decimal(value)-Decimal(1)), Decimal('1e-59'))
        self.assertEqual(method['evaluation_precision_digits'], [80, 100])
        self.assertEqual(method['agreement_absolute_bound'], '1e-70')

    def test_cagr_index_and_form_guards(self):
        with self.assertRaises(ValueError): assembly.target(0, '(3200/100)**(1/5)-1')
        for expression in ('(-3200/100)**(1/5)-1', '(3200/100)**(1/4)-1', '2**3', '(32/1)**(1/5)-1'):
            with self.subTest(expression=expression), self.assertRaises(ValueError): assembly.target(685, expression)

    def test_reference_diagnostic_never_guesses_percent_by_closeness(self):
        scoring = {'unit': 'ratio', 'value': '0.5', 'tolerance': '0.00005'}
        original = {'exe_ans': 50, 'program': 'add(50, 0)'}
        result = assembly.comparison(0, {'id': 'synthetic'}, original, scoring)
        self.assertEqual(result['comparison_factor'], '1')
        original['program'] = 'multiply(0.5, const_100)'
        result = assembly.comparison(0, {'id': 'synthetic'}, original, scoring)
        self.assertEqual(result['comparison_factor'], '0.01')
        self.assertTrue(result['comparison_not_used_for_model_scoring'])
        self.assertEqual(scoring, {'unit': 'ratio', 'value': '0.5', 'tolerance': '0.00005'})


if __name__ == '__main__':
    unittest.main()
