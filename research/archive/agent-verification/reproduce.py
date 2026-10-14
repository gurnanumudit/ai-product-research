"""Reproduce the public headline numbers from the frozen Article 1 analysis."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parent
ANALYSIS = ROOT / "data" / "confirmatory-analysis.json"


def main() -> None:
    analysis = json.loads(ANALYSIS.read_text())
    overall = analysis["overall"]
    challenge = analysis["verification_signals_exploratory"][
        "challenge_pass_submitted_patches"
    ]
    systems = {row["role"]: row for row in analysis["systems"]}
    route = analysis["deployable_routing"]["efficient_then_strong_on_no_deliverable"]

    matrix = {
        "passed_correct": challenge["safely_accepted"],
        "passed_wrong": challenge["escaped_failures"],
        "not_approved_correct": challenge["rejected_successes"],
        "not_approved_wrong": challenge["rejected_failures"],
    }

    assert overall["submitted_patches"] == 82
    assert matrix == {
        "passed_correct": 15,
        "passed_wrong": 23,
        "not_approved_correct": 13,
        "not_approved_wrong": 31,
    }
    assert systems["efficient"]["resolved"] == 18
    assert systems["strong"]["resolved"] == 10
    assert route["eventual_resolved"] == 20

    print("Article 1 public result check: PASS")
    print("Submitted patches: 82")
    print("AI check passed: 38 (15 correct, 23 wrong)")
    print("AI check gave no approval: 44 (13 correct, 31 wrong)")
    print("Correct solutions: GPT-5.4 Mini 18; GPT-5.4 10; routed system 20")


if __name__ == "__main__":
    main()
