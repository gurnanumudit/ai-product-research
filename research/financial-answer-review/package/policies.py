"""Matched batch review policies using checker output, never evaluator labels."""

import hashlib
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PolicyDecision:
    policy: str
    feasible: bool
    budget: int
    mandatory_ids: tuple[str, ...]
    review_ids: tuple[str, ...]
    accepted_ids: tuple[str, ...]
    reason: str


def _hash(identity, seed):
    return hashlib.sha256((seed + "\0" + identity).encode()).hexdigest()


def matched_policies(reports, budget=10, seed="finqa-stage-a-v1"):
    reports = list(reports)
    if isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= len(reports):
        raise ValueError("budget must be integer in [0,batch size]")
    ids = [r.id for r in reports]
    if len(ids) != len(set(ids)) or not all(isinstance(x, str) and x for x in ids):
        raise ValueError("unique nonempty IDs required")
    for r in reports:
        if r.usable and (isinstance(r.confidence, bool) or not isinstance(r.confidence, (int, float))
                         or not math.isfinite(r.confidence) or not 0 <= r.confidence <= 1):
            raise ValueError("usable report has invalid confidence")
    tie = lambda r: (_hash(r.id, seed + ":tie"), r.id)
    mandatory = tuple(r.id for r in sorted(reports, key=tie) if not r.usable)
    candidates = [r for r in reports if r.usable]
    orders = {
        "confidence": sorted(candidates, key=lambda r: (r.confidence, *tie(r))),
        "verification": sorted(candidates, key=lambda r: (-len(r.warnings), *tie(r))),
        "random": sorted(candidates, key=lambda r: (_hash(r.id, seed + ":random"), r.id)),
    }
    result = {}
    for policy, ordered in orders.items():
        if len(mandatory) > budget:
            result[policy] = PolicyDecision(policy, False, budget, mandatory, (), (),
                                            "mandatory_abstentions_exceed_budget; batch withheld")
            continue
        reviewed = mandatory + tuple(r.id for r in ordered[:budget - len(mandatory)])
        result[policy] = PolicyDecision(policy, True, budget, mandatory, reviewed,
                                        tuple(sorted(set(ids) - set(reviewed))), "matched_budget")
    return result


def strict_withholding(reports):
    """Separate diagnostic, deliberately not a matched-budget operating point."""
    reports = list(reports)
    if len({r.id for r in reports}) != len(reports):
        raise ValueError("duplicate IDs")
    withheld = tuple(sorted(r.id for r in reports if not r.usable or r.warnings))
    return {"withheld_ids": withheld,
            "accepted_ids": tuple(sorted(r.id for r in reports if r.usable and not r.warnings)),
            "required_review_slots": len(withheld)}
