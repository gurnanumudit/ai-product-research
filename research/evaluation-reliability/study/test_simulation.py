"""Author deterministic tests only. No reporting run or extra random seed."""

from dataclasses import asdict
from fractions import Fraction as F
import gzip
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import simulation as s


class FixedRandom:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = 0

    def random(self):
        self.calls += 1
        return next(self.values)


def row(pair_id, a, b, m=5, context=None):
    return s.ObservedRow(pair_id,a,b,pair_id//m if context is None else context)


class LawAndLedgerTests(unittest.TestCase):
    def test_frozen_manifest_order_and_exact_law(self):
        specs = s.worlds()
        self.assertEqual(len(specs),15)
        for i,world in enumerate(specs):
            self.assertEqual(world.index,i)
            self.assertEqual(world.seed,2709271800+i)
            self.assertEqual(world.mechanism,s.MECHANISMS[i//3])
            self.assertEqual(world.delta,s.EFFECTS[i%3])
            self.assertEqual((world.m,world.horizon),(5,200))
            exact = s.law(world.q,world.delta,world.h,world.m)
            self.assertEqual(exact['mean_D'],F(str(world.delta)))
            for sign,probs in exact['probabilities'].items():
                self.assertEqual(sum(probs),1)
                self.assertTrue(all(0 <= p <= 1 for p in probs))
                self.assertEqual(probs[2]-probs[0],F(str(world.delta))+F(str(world.h))*sign)
        self.assertEqual(s.law(.5,.1,.3)['variance_D'],F(17,100))
        self.assertEqual(s.law(.5,0,0)['covariance_d'],0)

    def test_constraints_and_boundaries(self):
        for args in ((0,0,0,5),(1,1,0,1),(1,-1,0,5),(1,0,1,5),(.3,.1,.2,5)):
            self.assertEqual(sum(s.law(*args)['probabilities'][1]),1)
        for position in range(3):
            for value in (float('nan'),float('inf'),-float('inf'),True,None,'0'):
                values = [.5,0,.3,5]; values[position] = value
                with self.assertRaises(ValueError): s.law(*values)
        for args in ((-.1,0,0,5),(1.1,0,0,5),(.5,0,-.1,5),(.5,.4,.3,5),(.5,0,0,0),(.5,0,0,True)):
            with self.assertRaises(ValueError): s.law(*args)

    def fixture(self, mechanism, observation_uniforms):
        world = s.World(0,mechanism,.1,.3,2709271800,horizon=1)
        # Literal truth: A=11100, B=01111; then five mask uniforms.
        rng = FixedRandom([.1,.2,0,.35,.849,.85,.999]+observation_uniforms)
        ledger = s.simulate_cohort(world,0,rng)
        self.assertEqual(rng.calls,12)
        self.assertEqual((ledger.a_bits,ledger.b_bits),('11100','01111'))
        return ledger

    def test_truth_then_mask_fixed_draw_order(self):
        ledger = self.fixture('clustered_mcar',[0,.2,.3,.99,.1])
        self.assertEqual(ledger.b_observed,'01110')
        self.assertEqual(ledger.b_multiplicity,'01110')
        self.assertEqual([r.pair_id for r in s.observed_rows(ledger)],[1,2,3])
        self.assertEqual([r.b-r.a for r in s.observed_rows(ledger)],[0,0,1])

    def test_mnar_uses_truth_only_in_fault_generation(self):
        ledger = self.fixture('clustered_mnar',[.399,.049,.05,.8,.9])
        self.assertEqual(ledger.b_observed,'00111')
        exposed = s.observed_rows(ledger)
        self.assertEqual(len(exposed),3)
        self.assertTrue(all(r.pair_id not in (0,1) for r in exposed))
        self.assertEqual(s.evaluate_prefix(exposed,1)['diagnostics']['missing_pairs'],2)

    def test_duplicates_join_same_a_and_preserve_identity(self):
        ledger = self.fixture('clustered_duplicate',[0,0,0,0,0])
        self.assertEqual(ledger.b_observed,'11111')
        self.assertEqual(ledger.b_multiplicity,'12222')
        exposed = s.observed_rows(ledger)
        self.assertEqual(len(exposed),9)
        unique,diag = s.deduplicate(exposed,5,5)
        self.assertEqual(len(unique),5)
        self.assertEqual(diag['duplicate_extra_rows'],4)
        self.assertIsNone(diag['integrity_reason'])
        self.assertEqual(exposed[1],exposed[2])

    def test_clean_still_consumes_all_mask_uniforms(self):
        ledger = self.fixture('clustered_complete',[0,0,0,0,0])
        self.assertEqual(ledger.b_observed,'11111')
        self.assertEqual(ledger.b_multiplicity,'11111')

    def test_ledger_roundtrip_and_mask_validation(self):
        ledger = self.fixture('clustered_mcar',[0,.2,.3,.99,.1])
        self.assertEqual(s.Ledger(**json.loads(s._json(asdict(ledger)))),ledger)
        bad = asdict(ledger); bad['b_multiplicity'] = '11111'
        with self.assertRaises(ValueError): s.Ledger(**bad)
        bad = asdict(ledger); bad['a_bits'] = '11102'
        with self.assertRaises(ValueError): s.Ledger(**bad)

    def test_gzip_is_deterministic_and_reconstructs_fixture(self):
        ledger = self.fixture('clustered_duplicate',[.1]*5)
        text = s._json(asdict(ledger))+'\n'
        with tempfile.TemporaryDirectory(prefix='phase1-gzip-fixture-') as directory:
            paths = [Path(directory)/name for name in ('a.gz','b.gz')]
            for path in paths:
                with s._gzip_text(path) as handle: handle.write(text)
            self.assertEqual(paths[0].read_bytes(),paths[1].read_bytes())
            with gzip.open(paths[0],'rt') as handle:
                self.assertEqual(s.Ledger(**json.load(handle)),ledger)


class DecisionTests(unittest.TestCase):
    def test_quantiles_and_hand_interval(self):
        values = [-1,0,1]
        for k,z in ((1,1.959963984540054),(5,2.5758293035489004)):
            result = s.normal_interval(values,looks_adjustment=k)
            self.assertEqual(result['mean'],0)
            self.assertEqual(result['sd'],1)
            self.assertAlmostEqual(result['lower'],-z/math.sqrt(3),places=14)
            self.assertAlmostEqual(result['upper'],z/math.sqrt(3),places=14)

    def test_degenerate_and_nonfinite_values(self):
        for values,reason in (([],'insufficient_n'),([1],'insufficient_n'),([.2]*200,'zero_sd'),([1]*200,'zero_sd')):
            interval = s.normal_interval(values)
            self.assertEqual(interval['reason'],reason)
            self.assertEqual(s.interval_decision(interval),'inconclusive')
        for values in ([float('nan'),0],[float('inf'),1],[2,0]):
            with self.assertRaises(ValueError): s.normal_interval(values)

    def test_strict_boundaries_and_truth_equality(self):
        for lower,upper,expected in ((.02,.1,'inconclusive'),(-.1,.02,'inconclusive'),(.021,.1,'ship'),(-.1,.019,'hold')):
            self.assertEqual(s.interval_decision({'reason':None,'lower':lower,'upper':upper}),expected)
        self.assertEqual(s.classify('ship',.02),'false_ship')
        self.assertEqual(s.classify('hold',.02),'correct_hold')
        self.assertEqual(s.classify('hold',.1),'false_hold')

    def test_zero_outcome_is_observed_not_missing(self):
        rows = [row(i,i%2,0) for i in range(10)]
        full = s.evaluate_prefix(rows,2)
        self.assertEqual(full['diagnostics']['missing_pairs'],0)
        self.assertIsNone(full['diagnostics']['integrity_reason'])
        lost = s.evaluate_prefix(rows[1:],2)
        self.assertEqual(lost['diagnostics']['missing_pairs'],1)
        self.assertEqual(lost['intervals']['integrity_adjusted']['reason'],'integrity_missing_pairs')

    def test_equal_context_weighting_and_duplicate_repair(self):
        rows = [row(0,0,1),row(1,0,0),row(5,1,0)]
        result = s.evaluate_prefix(rows,2)
        self.assertAlmostEqual(result['intervals']['row']['mean'],0)
        self.assertAlmostEqual(result['intervals']['context']['mean'],-.25)
        full = [row(i,0,1 if i%3 else 0) for i in range(10)]
        dup = full+[full[1],full[1]]
        repaired = s.evaluate_prefix(dup,2)
        base = s.evaluate_prefix(full,2)
        self.assertEqual(repaired['intervals']['integrity_adjusted'],base['intervals']['integrity_adjusted'])
        self.assertEqual(repaired['diagnostics']['duplicate_extra_rows'],2)

    def test_empty_context_count_and_look_not_replaced(self):
        result = s.evaluate_prefix([row(0,0,1),row(1,1,0)],3)
        self.assertEqual(result['intended_contexts'],3)
        self.assertEqual(result['diagnostics']['available_contexts'],1)
        self.assertEqual(result['diagnostics']['zero_observation_contexts'],2)
        self.assertEqual(result['intervals']['context']['reason'],'insufficient_n')

    def test_conflicting_and_unknown_current_ids_reach_guard(self):
        rows = [row(i,0,i%2) for i in range(10)]
        conflict = s.evaluate_prefix(rows+[row(0,0,1)],2)
        self.assertEqual(conflict['intervals']['integrity_adjusted']['reason'],'integrity_conflicting_duplicate')
        bad = s.evaluate_prefix(rows+[row(999,0,1,context=1)],2)
        self.assertEqual(bad['intervals']['integrity_adjusted']['reason'],'integrity_invalid_observed_row')
        self.assertEqual(bad['decisions']['integrity_adjusted'],'inconclusive')

    def test_first_decision_survives_later_reversal_and_missingness(self):
        rows = [row(i,0,i%2,m=1) for i in range(40)]
        rows += [row(i,1,0,m=1) for i in range(40,200) if i != 190]
        result = s.evaluate_cohort(rows,m=1)
        self.assertEqual([v['intended_contexts'] for v in result['looks']],[40,80,120,160,200])
        for method in ('row_peek','context_peek','context_adjusted','integrity_adjusted'):
            self.assertEqual(result['methods'][method]['decision'],'ship')
            self.assertEqual(result['methods'][method]['decision_contexts'],40)
        self.assertEqual(result['methods']['row_fixed']['decision'],'hold')
        self.assertEqual(result['looks'][-1]['intervals']['integrity_adjusted']['reason'],'integrity_missing_pairs')

    def test_later_unknown_id_cannot_veto_earlier_decision(self):
        rows = [row(i,0,i%2,m=1) for i in range(200)]
        rows.append(row(9999,0,1,m=1,context=190))
        result = s.evaluate_cohort(rows,m=1)
        self.assertEqual(result['methods']['integrity_adjusted']['decision'],'ship')
        self.assertEqual(result['methods']['integrity_adjusted']['decision_contexts'],40)
        self.assertEqual(result['looks'][-1]['intervals']['integrity_adjusted']['reason'],'integrity_invalid_observed_row')

    def test_inconclusive_consumes_horizon_and_forced_hold_is_separate(self):
        rows = [row(i,0,0,m=1) for i in range(200)]
        result = s.evaluate_cohort(rows,m=1)
        self.assertEqual(result['forced_row_fixed'],'hold')
        for value in result['methods'].values():
            self.assertEqual(value['decision'],'inconclusive')
            self.assertEqual(value['decision_contexts'],200)
            self.assertEqual(value['reason'],'zero_sd')

    def test_reporting_entrypoint_rejects_unfrozen_sizes_without_running(self):
        with self.assertRaises(ValueError):
            s.execute_study('not-created','not-read','not-hashed',cohorts_per_world=1)
        with self.assertRaises(ValueError):
            s.execute_study('not-created','not-read','not-hashed',seed_base=1)

    def test_interruption_preserved_before_any_stochastic_draw(self):
        protocol = Path(__file__).with_name('PROTOCOL.md')
        with tempfile.TemporaryDirectory(prefix='phase1-interrupt-fixture-') as directory:
            with patch.object(s,'_enforce_limits',side_effect=KeyboardInterrupt('fixture')):
                with patch.object(s,'simulate_cohort',side_effect=AssertionError('must not generate')) as generate:
                    with self.assertRaises(KeyboardInterrupt):
                        s.execute_study(directory,protocol,s._file_sha256(protocol))
                    generate.assert_not_called()
            error = json.loads((Path(directory)/'error.json').read_text())
            self.assertEqual(error['completed_cohorts'],0)
            self.assertEqual(error['error_type'],'KeyboardInterrupt')
            self.assertEqual(error['planned_cohorts'],30000)

    def test_resource_limits_raise_without_sampling(self):
        import time
        with tempfile.TemporaryDirectory(prefix='phase1-limit-fixture-') as directory:
            with self.assertRaises(RuntimeError):
                s._enforce_limits(time.perf_counter()-1201,Path(directory))
            with patch.object(s,'_resources',return_value={'cpu_seconds':0,'peak_rss_bytes':1024**3+1}):
                with self.assertRaises(RuntimeError):
                    s._enforce_limits(time.perf_counter(),Path(directory))


if __name__ == '__main__':
    unittest.main()
