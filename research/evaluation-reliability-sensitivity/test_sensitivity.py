"""Deterministic interfaces and prescribed original-prefix checks; no sweep."""
from dataclasses import replace
import io
import json
import random
import unittest
from unittest.mock import patch

import analyze as s


class SensitivityTests(unittest.TestCase):
    def test_config_size_and_controls(self):
        cells = s.cells(s.config())
        self.assertEqual(len(cells), 23)
        self.assertEqual(sum(c["family"] == "missingness" for c in cells), 11)
        self.assertEqual(sum(c["family"] == "threshold" for c in cells), 9)
        self.assertEqual(sum(c["family"] == "relatedness" for c in cells), 3)
        labels = {c["id"]: c.get("condition") for c in cells}
        self.assertEqual(labels["missing_f05_s10"], "reversed-selection negative control")
        self.assertEqual(labels["missing_f05_s05"], "equal-loss MCAR control")
        self.assertEqual(labels["missing_f10_s10"], "equal-loss MCAR control")

    def test_capture_original_anchor_and_rng_state(self):
        world = s.frozen.worlds()[9]
        reference = random.Random(world.seed)
        captured = s.CapturedRandom(random.Random(world.seed))
        for i in range(2):
            expected = s.frozen.simulate_cohort(world, i, reference)
            actual, masks = s.capture_cohort(world, i, captured)
            self.assertEqual(actual, expected)
            self.assertEqual(s.remask(actual, masks, .4, .05), expected)
            self.assertEqual(reference.getstate(), captured.generator.getstate())
            self.assertEqual(len(masks), 1000)

    def test_remasking_never_changes_truth_or_consumes_rng(self):
        world = s.frozen.worlds()[9]
        rng = s.CapturedRandom(random.Random(world.seed))
        ledger, masks = s.capture_cohort(world, 0, rng)
        before = rng.generator.getstate()
        clean = s.remask(ledger, masks, 0, 0)
        lost = s.remask(ledger, masks, 1, 1)
        self.assertEqual(clean.b_observed, "1"*1000)
        self.assertEqual(lost.b_observed, "0"*1000)
        self.assertEqual(clean.a_bits, ledger.a_bits)
        self.assertEqual(clean.b_bits, ledger.b_bits)
        self.assertEqual(before, rng.generator.getstate())
        for rate in (.05, .1):
            equal = s.remask(ledger, masks, rate, rate)
            self.assertEqual(equal.b_observed, "".join(str(int(u >= rate)) for u in masks))

    def test_pairing_across_relatedness(self):
        generators = [s.CapturedRandom(random.Random(2709271804)) for _ in range(3)]
        for i in range(2):
            for h, rng in zip((.15, .3, .45), generators):
                s.capture_cohort(replace(s.frozen.worlds()[4], h=h), i, rng)
            self.assertEqual(generators[0].values, generators[1].values)
            self.assertEqual(generators[1].values, generators[2].values)
        cell = next(x for x in s.cells(s.config()) if x["id"] == "related_h30")
        self.assertAlmostEqual(cell["paired_difference_icc"], .09/(.5-.02**2))

    def test_threshold_truth_changes_and_equality(self):
        self.assertEqual(s.frozen.classify("ship", .02, .01), "correct_ship")
        self.assertEqual(s.frozen.classify("ship", .02, .02), "false_ship")
        self.assertEqual(s.frozen.classify("ship", .02, .05), "false_ship")
        interval = {"reason": None, "lower": .02, "upper": .03}
        self.assertEqual(s.frozen.interval_decision(interval, .02), "inconclusive")

    def test_recompute_first_crossing_not_final_relabel(self):
        ledger = s.frozen.simulate_cohort(s.frozen.worlds()[4], 0, random.Random(2709271804))
        for tau in (.01, .02, .05):
            calls = []
            original = s.frozen.evaluate_prefix
            def observed(*args, **kwargs):
                calls.append((args[1], kwargs["tau"]))
                return original(*args, **kwargs)
            with patch.object(s.frozen, "evaluate_prefix", side_effect=observed):
                result = s.evaluate(ledger, tau)
            self.assertEqual(calls, [(t, tau) for t in s.frozen.LOOKS])
            for method, interval_name in {"row_peek": "row", "context_peek": "context", "context_adjusted": "context_adjusted", "integrity_adjusted": "integrity_adjusted"}.items():
                eligible = [(x["intended_contexts"], s.frozen.interval_decision(x["intervals"][interval_name], tau)) for x in result["looks"]]
                chosen = next(((t, a) for t, a in eligible if a != "inconclusive"), (200, "inconclusive"))
                item = result["methods"][method]
                self.assertEqual((item["decision_contexts"], item["decision"]), chosen)

    def test_accumulator_uses_final_not_stopping_mean(self):
        cell = s.cells(s.config())[0]
        accumulator = s.Accumulator(cell)
        ledger = s.frozen.simulate_cohort(s.frozen.worlds()[9], 0, random.Random(2709271809))
        result = s.evaluate(ledger, .02)
        result["looks"][-1]["intervals"]["row"]["mean"] = .123
        accumulator.add(ledger, result, io.BytesIO())
        self.assertEqual(accumulator.final_means, [.123])
        for method in s.METHODS:
            count = accumulator.counts[method]
            self.assertEqual(sum(count[k] for k in ("correct_ship", "correct_hold", "false_ship", "false_hold", "inconclusive")), 1)

    def test_wilson_endpoints(self):
        self.assertEqual(s.reporting.wilson(0, 2000)[0], 0)
        self.assertGreater(s.reporting.wilson(0, 2000)[1], 0)
        self.assertEqual(s.reporting.wilson(2000, 2000)[1], 1)

    def test_pairing_contrasts_use_matched_actions_and_changed_truth(self):
        cells = {x["id"]: x for x in s.cells(s.config())}
        keys = ("threshold_w04_t01", "threshold_w04_t02")
        accumulators = {key: s.Accumulator(cells[key]) for key in keys}
        for accumulator in accumulators.values():
            accumulator.n = 2000
            accumulator.actions = {m: bytearray([1]*1000+[0]*1000) for m in s.METHODS}
        contrasts = s.paired_contrasts(accumulators)
        self.assertEqual(len(contrasts), 6)
        for contrast in contrasts:
            self.assertTrue(contrast["truth_class_can_differ"])
            self.assertEqual(contrast["events"]["correct_ship"]["difference"], .5)
            self.assertEqual(contrast["events"]["false_ship"]["difference"], -.5)
            self.assertEqual(contrast["events"]["inconclusive"]["difference"], 0)
            self.assertEqual(contrast["events"]["inconclusive"]["interval_method"], "conservative_Hoeffding_degenerate_fallback")


if __name__ == "__main__":
    unittest.main()
