"""Independent read-only scientific checks; writes only a new review receipt.

Does not import the sensitivity runner or frozen generator/evaluator. Audits all
saved threshold trajectories and all compact records; independently regenerates
the first two prescribed cohorts in every cell using the stated probability law.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT.parent / "evaluation-reliability"
METHODS = ("row_fixed", "row_peek", "context_fixed", "context_peek",
           "context_adjusted", "integrity_adjusted")
MAPPING = dict(zip(METHODS, ("row", "row", "context", "context",
                            "context_adjusted", "integrity_adjusted")))
LOOKS = (40, 80, 120, 160, 200)


def records(path):
    with gzip.open(path, "rt") as source:
        for line in source:
            yield json.loads(line)


def close(actual, expected, tolerance=1e-12):
    assert math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance), (actual, expected)


def wilson(k, n):
    z = statistics.NormalDist().inv_cdf(.975)
    p = k/n
    center = (p + z*z/(2*n))/(1+z*z/n)
    radius = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0., center-radius), min(1., center+radius)]


def event(action, delta, tau):
    if action == "inconclusive":
        return action
    return ("correct_" if (action == "ship") == (delta > tau) else "false_") + action


def first_crossings(looks, tau):
    output = []
    for method, kind in MAPPING.items():
        decision, consumed = "inconclusive", 200
        for look in looks:
            t = look["intended_contexts"]
            if method.endswith("_fixed") and t != 200:
                continue
            interval = look["intervals"][kind]
            if interval["reason"] is not None:
                continue
            if interval["lower"] > tau:
                decision, consumed = "ship", t
                break
            if interval["upper"] < tau:
                decision, consumed = "hold", t
                break
        output.append([decision, consumed])
    return output


def independent_ledger(cell, rng):
    delta, h = Fraction(str(cell["delta"])), Fraction(str(cell["h"]))
    a, b = [], []
    for _ in range(200):
        c = -1 if rng.random() < .5 else 1
        z = int(rng.random() < .5)
        minus = float((Fraction(1, 2)-delta-h*c)/2)
        zero_end = float((Fraction(1, 2)-delta-h*c)/2+Fraction(1, 2))
        for _ in range(5):
            u = rng.random()
            av, bv = (1, 0) if u < minus else (z, z) if u < zero_end else (0, 1)
            a.append(av)
            b.append(bv)
    failures = cell.get("failed_grade_loss", .4 if cell["world_id"] == "w09_clustered_mnar" else 0.)
    successes = cell.get("successful_grade_loss", .05 if cell["world_id"] == "w09_clustered_mnar" else 0.)
    observed = [rng.random() >= (failures if value == 0 else successes) for value in b]
    return a, b, observed


def interval(values, adjusted=False):
    if len(values) < 2 or len(set(values)) < 2:
        return {"reason": "unavailable"}
    mean = statistics.fmean(values)
    se = statistics.stdev(values)/math.sqrt(len(values))
    z = statistics.NormalDist().inv_cdf(.995 if adjusted else .975)
    return {"reason": None, "lower": mean-z*se, "upper": mean+z*se}


def independent_decisions(a, b, observed, tau):
    looks = []
    for t in LOOKS:
        grouped = defaultdict(list)
        for i in range(t*5):
            if observed[i]:
                grouped[i//5].append(b[i]-a[i])
        rows = [d for values in grouped.values() for d in values]
        contexts = [statistics.fmean(values) for values in grouped.values()]
        intervals = {"row": interval(rows), "context": interval(contexts),
                     "context_adjusted": interval(contexts, True),
                     "integrity_adjusted": interval(contexts, True) if all(observed[:t*5]) else {"reason": "missing"}}
        looks.append({"intended_contexts": t, "intervals": intervals})
    return first_crossings(looks, tau)


def main():
    assert __debug__, "Do not disable assertions"
    result = json.loads((ROOT / "results/analysis.json").read_text())
    cells = {r["cell"]["id"]: r for r in result["cells"]}
    assert len(cells) == 23
    compact = {name: {} for name in cells}
    for record in records(ROOT / "results/cohort-outcomes.jsonl.gz"):
        destination = compact[record["cell"]]
        assert record["cohort"] not in destination
        destination[record["cohort"]] = record
    assert all(set(rows) == set(range(2000)) for rows in compact.values())
    checks = Counter()
    for name, result_cell in cells.items():
        cell = result_cell["cell"]
        for j, method in enumerate(METHODS):
            counts, use = Counter(), Counter()
            for record in compact[name].values():
                action, consumed = record["methods"][j]
                assert action in ("ship", "hold", "inconclusive") and consumed in LOOKS
                counts[event(action, cell["delta"], cell["tau"])] += 1
                use[consumed] += 1
            counts["correct_decision"] = counts["correct_ship"]+counts["correct_hold"]
            counts["false_decision"] = counts["false_ship"]+counts["false_hold"]
            actual = result_cell["methods"][method]
            for key in ("false_ship", "false_hold", "correct_ship", "correct_hold", "inconclusive", "false_decision", "correct_decision"):
                assert actual["counts"][key] == counts[key]
                close(actual["rates"][key]["estimate"], counts[key]/2000)
                for left, right in zip(actual["rates"][key]["wilson95"], wilson(counts[key], 2000)):
                    close(left, right)
                checks["aggregate_event_rates_and_intervals"] += 1
            assert actual["first_decision_or_horizon_distribution"] == {str(k): v for k, v in use.items()}
            close(actual["mean_intended_contexts"], sum(k*v for k, v in use.items())/2000)
        close(result_cell["approach1_final_look"]["mean_estimate"], statistics.fmean(r["row_final_mean"] for r in compact[name].values()))
        close(result_cell["missing_pair_fraction"], sum(r["missing_pairs"] for r in compact[name].values())/2000000)
        rng = random.Random(cell["seed"])
        for index in range(2):
            a, b, observed = independent_ledger(cell, rng)
            expected = independent_decisions(a, b, observed, cell["tau"])
            actual = compact[name][index]
            assert actual["methods"] == expected, (name, index, actual["methods"], expected)
            assert actual["missing_pairs"] == observed.count(False)
            close(actual["row_final_mean"], statistics.fmean(bv-av for av, bv, seen in zip(a, b, observed) if seen))
            checks["independent_prefix_cell_cohorts"] += 1
    threshold_cells = [r["cell"] for r in cells.values() if r["cell"]["family"] == "threshold"]
    for saved in records(FROZEN / "data/run1/decisions.jsonl.gz"):
        for cell in threshold_cells:
            if saved["world_id"] == cell["world_id"]:
                expected = first_crossings(saved["looks"], cell["tau"])
                assert compact[cell["id"]][saved["cohort_index"]]["methods"] == expected
                checks["saved_threshold_cell_trajectories"] += 1
    assert checks["independent_prefix_cell_cohorts"] == 46
    assert checks["saved_threshold_cell_trajectories"] == 18000
    comparisons = json.loads((ROOT / "results/paired-contrasts.json").read_text())["contrasts"]
    for comparison in comparisons:
        left, right = comparison["cell"], comparison["reference_cell"]
        a, b = cells[left]["cell"], cells[right]["cell"]
        j = METHODS.index(comparison["method"])
        assert comparison["truth_class_can_differ"] == ((a["delta"] > a["tau"]) != (b["delta"] > b["tau"]))
        for key, expected in comparison["events"].items():
            differences = []
            for i in range(2000):
                events = [event(compact[name][i]["methods"][j][0], c["delta"], c["tau"])
                          for name, c in ((left, a), (right, b))]
                def indicator(value):
                    if key in ("correct_decision", "false_decision"):
                        return int(value.startswith(key.split("_")[0]+"_"))
                    return int(value == key)
                differences.append(indicator(events[0])-indicator(events[1]))
            mean = statistics.fmean(differences)
            variance = statistics.variance(differences)
            half = statistics.NormalDist().inv_cdf(.975)*math.sqrt(variance/2000) if variance > 0 else math.sqrt(2*math.log(40)/2000)
            close(expected["difference"], mean)
            for actual, target in zip(expected["interval95"], (max(-1., mean-half), min(1., mean+half))):
                close(actual, target)
            checks["independent_paired_contrast_events"] += 1
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    for family, base in (("local", ROOT), ("frozen_inputs", FROZEN)):
        for name, digest in freeze["files"][family].items():
            assert hashlib.sha256((base/name).read_bytes()).hexdigest() == digest, name
            checks["unchanged_frozen_inputs_and_runner_files"] += 1
    analytic = []
    for failed in (0., .05, .1, .2, .3, .4):
        for successful in ((0.,) if failed == 0 else (.05, .1)):
            numerator = .23*(1-successful)-.27*(1-failed)
            denominator = .48*(1-successful)+.52*(1-failed)
            mean = numerator/denominator
            if failed == successful:
                close(mean, -.04)
            analytic.append({"failure_loss": failed, "success_loss": successful,
                             "pooled_observed_population_mean": mean,
                             "bias_vs_true_delta": mean+.04})
    for r in cells.values():
        if r["cell"]["family"] == "relatedness":
            close(r["cell"]["paired_difference_icc"], r["cell"]["h"]**2/(.5-.02**2))
    receipt = {"status": "passed", "checks": dict(checks),
               "review_scope": "All compact counts/rates/intervals and paired contrast events; all threshold decisions from frozen saved intervals; first two cell-cohorts independently generated and evaluated. Not an independent full regeneration of all missingness/dependence cohorts.",
               "analytic_missingness": analytic,
               "analytic_caveat": "Population ratio for pooled observed paired differences, not the exact expectation of finite-sample ratio estimates or equal-context estimator; no empirical production calibration.",
               "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), ROOT/"analyze.py", ROOT/"config.json", ROOT/"results/analysis.json", ROOT/"results/cohort-outcomes.jsonl.gz")}}
    with (ROOT / "independent-review.json").open("x") as target:
        json.dump(receipt, target, indent=2)
        target.write("\n")
    print(json.dumps({"status": "passed", "checks": dict(checks)}, indent=2))


if __name__ == "__main__":
    main()
