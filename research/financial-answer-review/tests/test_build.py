"""Synthetic mechanics only; no FinQA payloads or provider calls."""

import inspect
import json
import unittest
from fractions import Fraction

from package.checker import CheckReport, check_response, evaluate
from package.numbers import number, source_number, numeric_tokens
from package.policies import matched_policies, strict_withholding
from package.prompt import build_messages
from package.schema import parse_response, RESPONSE_SCHEMA
from package.scorer import score_final


def item(identity="case"):
    return {"id": identity, "question": "What was the change?",
            "locations": {"r1": "Prior 100. Current 125. Year 2020.", "r2": "Loss (1,200). Margin 25%."}}


def response():
    return {"answer": "25", "unit": "number", "scale": "1", "confidence": 0.8,
            "operands": [{"id": "o1", "location_id": "r1", "quote": "125", "value": "125"},
                         {"id": "o2", "location_id": "r1", "quote": "100", "value": "100"}],
            "constants": [], "expression": "o1-o2"}


def reference(value="25", unit="number", scale="1"):
    return {"value": value, "unit": unit, "scale": scale, "provenance": "synthetic fixture",
            "tolerance": "0.000005", "tolerance_provenance": "synthetic 5-decimal fixture", "qualified": True}


class NumberTests(unittest.TestCase):
    def test_signed_parentheses_currency_percent(self):
        for token, expected in (("(1,200)", -1200), ("−3.5", Fraction(-7, 2)),
                                ("$ 1,200.50", Fraction(2401, 2)), ("25%", 25), ("0", 0)):
            self.assertEqual(source_number(token), expected)

    def test_reject_nonfinite_bool_scientific_and_oversize(self):
        for invalid in (True, float("nan"), "NaN", "Infinity", "1e3", "9" * 100, "1,200"):
            with self.assertRaises(ValueError):
                number(invalid)

    def test_ambiguous_source_syntax(self):
        for invalid in ("(25", "25)", "(-25)", "12,34", "25 and 26", "1e3"):
            with self.assertRaises(ValueError):
                source_number(invalid)

    def test_exact_tokens_not_substrings(self):
        self.assertEqual(numeric_tokens("Year 2020, cost (1,200), margin 25%."), ["2020", "(1,200)", "25%"])

    def test_punctuation_and_malformed_grouping(self):
        self.assertEqual(numeric_tokens("100. 125. 25%. 1,234.50; 12,34."), ["100", "125", "25%", "1,234.50", "12,34"])


class SchemaTests(unittest.TestCase):
    def test_valid_roundtrip(self):
        self.assertEqual(parse_response(json.dumps(response())), response())
        self.assertFalse(RESPONSE_SCHEMA["additionalProperties"])

    def test_additional_missing_and_duplicate_json_keys(self):
        bad = response(); bad["gold"] = 25
        for payload in (bad, {}, '{"answer":"1","answer":"2"}'):
            self.assertFalse(check_response(item(), payload).usable)

    def test_reject_confidence_limits(self):
        for confidence in (True, -0.01, 1.01, float("nan"), "0.8"):
            bad = response(); bad["confidence"] = confidence
            self.assertTrue(check_response(item(), bad).mandatory_abstain)

    def test_duplicate_and_bad_ids(self):
        for bad_id in ("o1", "__class__", "x1"):
            bad = response(); bad["operands"][1]["id"] = bad_id
            self.assertFalse(check_response(item(), bad).usable)

    def test_unknown_or_data_constant(self):
        bad = response(); bad["constants"] = [{"id": "c1", "value": "2020"}]
        self.assertFalse(check_response(item(), bad).usable)

    def test_explicit_abstention(self):
        null = {"answer": None, "unit": "", "scale": "1", "confidence": 0,
                "operands": [], "constants": [], "expression": ""}
        report = check_response(item(), null)
        self.assertTrue(report.mandatory_abstain)
        self.assertEqual(report.mandatory_reasons, ("explicit_abstention",))
        null["expression"] = "o1"
        self.assertIn("unusable_response", check_response(item(), null).mandatory_reasons[0])


class CheckerTests(unittest.TestCase):
    def test_clean_response(self):
        report = check_response(item(), response())
        self.assertTrue(report.usable)
        self.assertEqual(report.warnings, ())

    def test_wrong_location_and_value_are_warnings(self):
        bad = response(); bad["operands"][0]["location_id"] = "absent"
        bad["operands"][1]["value"] = "101"
        report = check_response(item(), bad)
        self.assertTrue(report.usable)
        self.assertEqual(len(report.warnings), 3)

    def test_partial_number_and_dropped_sign_rejected(self):
        for quote, location in (("20", "r1"), ("1,200", "r2")):
            bad = response(); bad["operands"][0].update(quote=quote, location_id=location)
            self.assertTrue(any("source_number_not_exact" in x for x in check_response(item(), bad).warnings))

    def test_percent_display_arithmetic(self):
        answer = response(); answer.update(unit="percent", expression="(o1-o2)/o2*c1")
        answer["constants"] = [{"id": "c1", "value": "100"}]
        self.assertEqual(check_response(item(), answer).warnings, ())

    def test_unsafe_arithmetic_mandatory(self):
        for expression in ("__import__('os').system('echo unsafe')", "o1**o2", "o1[0]",
                           "o1.real", "sum([o1])", "o1+5", "unknown", "o1/(o2-o2)"):
            bad = response(); bad["expression"] = expression
            self.assertFalse(check_response(item(), bad).usable, expression)

    def test_bounds_depth_and_large_products(self):
        with self.assertRaises(ValueError):
            evaluate("o1" + "+o1" * 80, {"o1": Fraction(1)})
        with self.assertRaises(ValueError):
            evaluate("o1*o1", {"o1": Fraction(10**20)})

    def test_unused_declarations(self):
        bad = response(); bad.update(answer="125", expression="o1")
        self.assertIn("unused_declared_inputs", check_response(item(), bad).warnings)

    def test_checker_does_not_claim_semantic_correctness(self):
        wrong_metric = item(); wrong_metric["question"] = "What was the 2019 margin?"
        self.assertEqual(check_response(wrong_metric, response()).warnings, ())

    def test_allowed_constant_cannot_prove_semantic_use(self):
        answer = response()
        answer.update(answer="1", expression="c1*o1+c2", operands=[answer["operands"][0]])
        answer["constants"] = [{"id": "c1", "value": "0"}, {"id": "c2", "value": "1"}]
        self.assertEqual(check_response(item(), answer).warnings, ())

    def test_gold_input_fields_rejected(self):
        leaking = item(); leaking["answer"] = "25"
        with self.assertRaises(ValueError):
            check_response(leaking, response())
        with self.assertRaises(ValueError):
            build_messages(leaking)


class ScorerTests(unittest.TestCase):
    def test_exact_and_negative(self):
        self.assertTrue(score_final(response(), reference()).correct)
        self.assertFalse(score_final(response(), reference("-25")).correct)

    def test_percent_ratio_equivalence(self):
        pred = response(); pred.update(answer="-52.485", unit="percent")
        self.assertTrue(score_final(pred, reference("-0.52485", "ratio")).correct)
        self.assertFalse(score_final(pred, reference("0.52485", "ratio")).correct)

    def test_no_implicit_percent_rescue(self):
        pred = response(); pred.update(answer="25", unit="ratio")
        self.assertFalse(score_final(pred, reference("0.25", "ratio")).correct)

    def test_explicit_scale_only(self):
        pred = response(); pred.update(answer="2", unit="USD", scale="1000000")
        self.assertTrue(score_final(pred, reference("2000", "USD", "1000")).correct)
        pred["scale"] = "1"
        self.assertFalse(score_final(pred, reference("2000", "USD", "1000")).correct)

    def test_contradictory_unit_wrong(self):
        pred = response(); pred["unit"] = "USD"
        self.assertEqual(score_final(pred, reference()).reason, "unit_mismatch")

    def test_missing_ambiguous_invalid_reference_unscorable(self):
        for gold in ({}, {"exe_ans": 25}, {**reference(), "ambiguous": True},
                     {**reference(), "unit": ""}, {**reference(), "value": "NaN"}):
            score = score_final(response(), gold)
            self.assertFalse(score.scorable)
            self.assertIsNone(score.correct)

    def test_prefilled_but_pending_reference_is_unscorable(self):
        for qualification in (None, False, 1, "true"):
            gold = reference(); gold["qualified"] = qualification
            self.assertFalse(score_final(response(), gold).scorable)

    def test_zero_and_explicit_reference_tolerance(self):
        pred = response(); pred["answer"] = "0.000005"
        self.assertTrue(score_final(pred, reference("0")).correct)
        pred["answer"] = "0.000006"
        self.assertFalse(score_final(pred, reference("0")).correct)

    def test_reference_specific_precision_and_missing_precision(self):
        pred = response(); pred["answer"] = "1.26923"
        gold = reference("1.27"); gold.update(tolerance="0.005", tolerance_provenance="synthetic rounded two-decimal answer")
        self.assertTrue(score_final(pred, gold).correct)
        del gold["tolerance_provenance"]
        self.assertFalse(score_final(pred, gold).scorable)
        gold = reference("0.33333", "ratio")
        pred.update(answer="33.33333333", unit="percent")
        self.assertTrue(score_final(pred, gold).correct)
        gold["tolerance"] = "-0.1"
        self.assertFalse(score_final(pred, gold).scorable)

    def test_invalid_prediction_is_not_reference_ambiguity(self):
        pred = response(); pred["answer"] = "NaN"
        score = score_final(pred, reference())
        self.assertTrue(score.scorable)
        self.assertFalse(score.correct)

    def test_percent_scale_contradiction(self):
        pred = response(); pred.update(unit="percent", scale="1000")
        self.assertFalse(score_final(pred, reference("0.25", "ratio")).correct)


class PolicyTests(unittest.TestCase):
    def reports(self):
        return [CheckReport(str(i), True, i / 49, ("warning",) if i % 3 == 0 else ()) for i in range(50)]

    def test_equal_budget_and_common_abstentions(self):
        reports = self.reports(); reports[0] = CheckReport("0", False, None)
        for decision in matched_policies(reports).values():
            self.assertTrue(decision.feasible)
            self.assertEqual(len(decision.review_ids), 10)
            self.assertEqual(len(decision.accepted_ids), 40)
            self.assertIn("0", decision.review_ids)

    def test_infeasible_not_silent_overbudget(self):
        reports = self.reports()
        reports[:11] = [CheckReport(str(i), False, None) for i in range(11)]
        for decision in matched_policies(reports).values():
            self.assertFalse(decision.feasible)
            self.assertEqual(len(decision.mandatory_ids), 11)
            self.assertEqual(decision.review_ids, ())
            self.assertEqual(decision.accepted_ids, ())

    def test_order_invariant_and_deterministic(self):
        reports = self.reports()
        self.assertEqual(matched_policies(reports), matched_policies(reversed(reports)))

    def test_confidence_and_verification_rank_differently(self):
        policies = matched_policies(self.reports())
        self.assertEqual(set(policies["confidence"].review_ids), {str(i) for i in range(10)})
        self.assertTrue(all(int(i) % 3 == 0 for i in policies["verification"].review_ids))

    def test_strict_withholding_is_not_budget_capped(self):
        strict = strict_withholding(self.reports())
        self.assertGreater(strict["required_review_slots"], 10)

    def test_invalid_budget_duplicate_and_bad_confidence(self):
        for budget in (-1, 51, True, 2.5):
            with self.assertRaises(ValueError):
                matched_policies(self.reports(), budget)
        with self.assertRaises(ValueError):
            matched_policies([CheckReport("x", True, 0.5)] * 2, budget=1)
        with self.assertRaises(ValueError):
            matched_policies([CheckReport("x", True, None)], budget=1)

    def test_gold_free_module_boundaries(self):
        import package.checker as checker
        import package.policies as policies
        import package.prompt as prompt
        for module in (checker, policies, prompt):
            self.assertNotIn("import scorer", inspect.getsource(module))
            self.assertNotIn("open(", inspect.getsource(module))
        messages = build_messages(item())
        self.assertEqual(json.loads(messages[1]["content"]), item())


if __name__ == "__main__":
    unittest.main()
