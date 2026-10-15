"""Evaluator-only reference scorer. Never imported by checker, prompt or policy."""

from dataclasses import dataclass
from .numbers import canonical, number


@dataclass(frozen=True)
class Score:
    scorable: bool
    correct: bool | None
    reason: str


def score_final(response, reference):
    """Qualified reference includes value/unit/scale/provenance and precision fields.

    Preserve sign. Percent/100 and explicit scale are the only conversions.
    No tolerance search, unit inference, absolute-value matching or program execution.
    This is the Stage A scorer convention, not a claim of official-evaluator identity.
    """
    try:
        if not isinstance(reference, dict) or not isinstance(reference.get("provenance"), str) or not reference["provenance"].strip():
            raise ValueError("reference normalization provenance missing")
        if reference.get("qualified") is not True:
            raise ValueError("reference has not been explicitly qualified")
        if reference.get("ambiguous", False):
            raise ValueError("reference interpretation ambiguous")
        if not isinstance(reference.get("tolerance_provenance"), str) or not reference["tolerance_provenance"].strip():
            raise ValueError("reference precision provenance missing")
        tolerance = number(reference["tolerance"])
        if tolerance < 0:
            raise ValueError("reference tolerance must be nonnegative")
        gold_unit, gold_value, gold_factor = canonical(reference["value"], reference["unit"], reference["scale"])
    except (KeyError, TypeError, ValueError) as exc:
        return Score(False, None, "unscorable_reference:" + str(exc))
    try:
        if response is None or response.get("answer") is None:
            return Score(True, False, "no_numeric_answer")
        pred_unit, pred_value, _ = canonical(response["answer"], response["unit"], response["scale"])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return Score(True, False, "invalid_prediction:" + str(exc))
    if pred_unit != gold_unit:
        return Score(True, False, "unit_mismatch")
    correct = abs(pred_value - gold_value) <= tolerance * abs(gold_factor)
    return Score(True, correct, "numeric_match" if correct else "numeric_mismatch")


