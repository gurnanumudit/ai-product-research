"""Offline numerical reproduction from derived study records; Python 3.10+.

No dependencies, network, model calls, grading, or writes to source data.
Run from any working directory. Outputs go to this study's ignored output/.
"""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = {"openai/gpt-5.6-luna": "Luna", "openai/gpt-5.6-terra": "Terra", "openai/gpt-5.6-sol": "Sol"}
BANDS = ("easy", "medium", "hard")
EFFORTS = ("none", "low", "high")
OPEN = {"not_started", "unreported", "running", "in_progress"}
OPERATIONAL = {"provider_failure", "infrastructure_failure", "study_deadline_stop"}


def read(name):
    return json.loads((HERE / name).read_text())


def rows(name):
    return [json.loads(line) for line in (HERE / name).read_text().splitlines()]


def near(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), (actual, expected)


def groups(values):
    result = defaultdict(list)
    for row in values:
        result[row["question_id"]].append(row)
    return result


def matches(row, point):
    return MODELS[row["model"]] == point["modelName"] and row["reasoning"] == point["effort"] and (
        "band" not in point or row["difficulty"] == point["band"])


def check_points(values, expected):
    for point in expected:
        subset = [r for r in values if matches(r, point)]
        assert len(subset) == point["n"]
        assert sum(r["correct"] for r in subset) == point["correct"]
        contexts = defaultdict(list)
        for row in subset:
            contexts[row["source_context"]].append(row["correct"])
        near(sum(map(sum, contexts.values())) / len(subset), point["successRate"])
        near(sum(sum(c) / len(c) for c in contexts.values()) / len(contexts), point["equalContextSuccessRate"])
        if "terminalCounts" in point:
            assert dict(Counter(r["terminal_class"] for r in subset)) == point["terminalCounts"]


def check_changes(values, expected):
    for point in expected:
        subset = [r for r in values if MODELS[r["model"]] == point["modelName"]
                  and (point["band"] == "all" or r["difficulty"] == point["band"])]
        before = {r["question_id"]: r["correct"] for r in subset if r["reasoning"] == point["before"]}
        after = {r["question_id"]: r["correct"] for r in subset if r["reasoning"] == point["after"]}
        assert before.keys() == after.keys()
        assert len(before) == point["n"]
        wins = sum(after[q] == 1 and before[q] == 0 for q in before)
        losses = sum(before[q] == 1 and after[q] == 0 for q in before)
        assert (wins, losses, wins - losses) == (point["gained"], point["lost"], point["net"])
        near(100 * (wins - losses) / len(before), point["percentagePoints"])


def main():
    if not __debug__:
        raise RuntimeError("Run without -O: verification checks must remain enabled.")
    manifest = read("reference/provenance.json")
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    assigned = rows("data/results.jsonl")
    costs = rows("data/costs.jsonl")
    expected = read("reference/expected.json")
    assert len(assigned) == 1251
    assert len({r["cell_id"] for r in assigned}) == 1251
    question_groups = groups(assigned)
    combinations = {(model, effort) for model in MODELS for effort in EFFORTS}
    for subset in question_groups.values():
        assert len(subset) == 9
        assert {(r["model"], r["reasoning"]) for r in subset} == combinations
        for field in ("difficulty", "source_context", "cohort", "included"):
            assert len({r[field] for r in subset}) == 1
        complete = all(r["terminal_class"] not in OPEN for r in subset)
        assert all(r["included"] == complete for r in subset)
        for row in subset:
            if row["terminal_class"] in OPEN:
                assert row["correct"] is None
            else:
                assert row["correct"] in (0, 1)
    primary = [r for r in assigned if r["included"]]
    excluded = [r for r in assigned if not r["included"]]
    assert len(primary) == 1206 and len(groups(primary)) == expected["questions"] == 134
    assert len(excluded) == 45 and sum(r["terminal_class"] in OPEN for r in excluded) == 19
    assert sorted(groups(excluded)) == expected["excludedQuestions"]
    assert all(r["difficulty"] == "medium" for r in excluded)
    assert dict(Counter(g[0]["difficulty"] for g in groups(primary).values())) == expected["bands"]
    assert len({r["source_context"] for r in primary}) == expected["sourceContexts"] == 24
    assert sum(r["correct"] for r in primary) == 899
    check_points(primary, expected["points"])
    check_points(primary, expected["overall"])
    check_changes(primary, expected["pairedChanges"])
    for cohort, n, key in [("historical50", 450, "historicalOverall"), ("extension84", 756, "extensionOverall")]:
        subset = [r for r in primary if r["cohort"] == cohort]
        assert len(subset) == n
        check_points(subset, expected[key])
    for key, predicate in [
        ("noInfrastructureFailure", lambda r: r["terminal_class"] not in OPERATIONAL),
        ("ordinaryTerminalsOnly", lambda r: r["terminal_class"] == "ordinary_answer"),
    ]:
        keep = {q for q, group in groups(primary).items() if all(predicate(r) for r in group)}
        subset = [r for r in primary if r["question_id"] in keep]
        reference = expected["sensitivities"][key]
        assert len(keep) == reference["questions"]
        check_points(subset, reference["points"])
        check_points(subset, reference["overall"])
        check_changes(subset, reference["changes"])
    by_id = {r["cell_id"]: r for r in primary}
    assert len(costs) == len({r["physical_id"] for r in costs}) == 1212
    assert {c["cell_id"] for c in costs} == by_id.keys()
    selected = Counter(c["cell_id"] for c in costs if c["selected_for_outcome"])
    assert selected == Counter({key: 1 for key in by_id})
    multiplicities = Counter(c["cell_id"] for c in costs)
    assert Counter(multiplicities.values()) == {1: 1200, 2: 6}
    resources = {"model": "model_charges_usd", "pending": "pending_usd", "runtime": "runtime_estimate_usd"}
    for cost in costs:
        assert type(cost["selected_for_outcome"]) is bool
        for field in resources.values():
            assert type(cost[field]) in (int, float) and math.isfinite(cost[field]) and cost[field] >= 0
    economic = []
    for point in expected["economicFullPoints"]:
        subset = [r for r in primary if matches(r, point)]
        resource_rows = [c for c in costs if matches(by_id[c["cell_id"]], point)]
        result = {k: point[k] for k in ("band", "modelName", "effort")}
        result.update(n=len(subset), correct=sum(r["correct"] for r in subset))
        assert result["n"] == point["n"] and result["correct"] == point["correct"]
        assert len(resource_rows) == point["physicalRecords"]
        for key, field in resources.items():
            result[key] = sum(c[field] for c in resource_rows)
            near(result[key], point[key])
        result["successRate"] = result["correct"] / result["n"]
        result["costPerQuestion"] = (result["model"] + result["pending"]) / result["n"]
        near(result["costPerQuestion"], point["costPerQuestion"])
        economic.append(result)
    for key, field in resources.items():
        near(sum(c[field] for c in costs), expected["costTotals"][key])
    hard = [p for p in economic if p["band"] == "hard"]
    frontier = [p for p in hard if not any(
        q["costPerQuestion"] <= p["costPerQuestion"] and q["successRate"] >= p["successRate"] and (
            q["costPerQuestion"] < p["costPerQuestion"] or q["successRate"] > p["successRate"])
        for q in hard)]
    assert {(p["modelName"], p["effort"]) for p in frontier} == {
        ("Luna", "none"), ("Luna", "low"), ("Luna", "high"), ("Sol", "low")}
    upgrades = []
    for band in BANDS:
        candidates = [p for p in economic if p["band"] == band]
        baseline = next(p for p in candidates if p["modelName"] == "Luna"
                        and p["effort"] == ("high" if band == "hard" else "low"))
        top = max(p["correct"] for p in candidates)
        target = min((p for p in candidates if p["correct"] == top), key=lambda p: p["costPerQuestion"])
        upgrades.append({"band": band, "from": [baseline["modelName"], baseline["effort"]],
                         "to": [target["modelName"], target["effort"]],
                         "extraCostPer100": 100 * (target["costPerQuestion"] - baseline["costPerQuestion"]),
                         "extraCorrectPer100": 100 * (target["successRate"] - baseline["successRate"])})
    output = HERE / "output"
    output.mkdir(exist_ok=True)
    (output / "analysis.json").write_text(json.dumps({
        "verified": True, "questions": 134, "outcomes": 1206, "physicalCosts": 1212,
        "points": economic, "hardFrontier": frontier, "illustrativeUpgrades": upgrades,
    }, indent=2) + "\n")
    lines = ["# Reproduced results", "", "| Model | Reasoning | Easy | Medium | Hard |",
             "|---|---|---:|---:|---:|"]
    for name in MODELS.values():
        for effort in EFFORTS:
            cells = [next(p for p in economic if p["modelName"] == name and p["effort"] == effort and p["band"] == band) for band in BANDS]
            lines.append("| " + " | ".join([name, effort, *[
                f'{p["correct"]}/{p["n"]} ({100*p["successRate"]:.1f}%)' for p in cells]]) + " |")
    (output / "results.md").write_text("\n".join(lines) + "\n")
    print("PASS: 134 questions; 1,206 outcomes; 1,212 cost records; all 27 result/cost cells.")
    print("PASS: exclusions, both sensitivity checks, cohorts, paired changes, shared contexts and hard frontier.")
    print("Wrote output/analysis.json and output/results.md. No network or paid calls.")


if __name__ == "__main__":
    main()
