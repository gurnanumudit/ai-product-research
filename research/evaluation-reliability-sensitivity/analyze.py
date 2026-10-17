"""Bounded exploratory sensitivities. Frozen study imports are read-only.

Freeze code/config with `python3 -B analyze.py freeze`; run only after review GO
with `python3 -B analyze.py run`. Neither import nor freeze executes cohorts.
"""
from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import resource
import sys
import time

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT.parent / "evaluation-reliability"
sys.path.insert(0, str(FROZEN / "study"))
import simulation as frozen
import summarize as reporting

N = 2000
EVENTS = ("false_ship", "false_hold", "correct_ship", "correct_hold",
          "correct_decision", "false_decision", "inconclusive")
METHODS = frozen.METHODS


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write_new(path, value):
    with Path(path).open("xb") as target:
        target.write(json_bytes(value))


def config():
    value = json.loads((ROOT / "config.json").read_text())
    assert value["cohorts_per_cell"] == N
    assert tuple(value["methods"]) == METHODS and tuple(value["looks"]) == frozen.LOOKS
    for family, index in (("missingness", 9), ("relatedness", 4)):
        world = frozen.worlds()[index]
        spec = value[family]
        assert (spec["world_index"], spec["seed"], spec["delta"], spec["tau"]) == (index, world.seed, world.delta, .02)
    assert value["missingness"]["h"] == frozen.worlds()[9].h
    assert value["missingness"]["include_clean_anchor"] is True
    assert value["missingness"]["original_anchor"] == [.4, .05]
    assert value["relatedness"]["original_anchor"] == .3
    assert value["thresholds"]["world_indices"] == [4, 9, 5]
    assert value["thresholds"]["tau"] == [.01, .02, .05]
    return value


def file_contract():
    local = ("config.json", "analyze.py", "test_sensitivity.py", "DESIGN.md")
    inputs = ("study/simulation.py", "study/summarize.py", "study/PROTOCOL.md",
              "study/SOURCE-FREEZE.json", "data/run1/ledger.jsonl.gz",
              "data/run1/decisions.jsonl.gz", "data/run1/summary.json",
              "data/run1/manifest.json", "results/analysis.json")
    return {"local": {name: sha(ROOT / name) for name in local},
            "frozen_inputs": {name: sha(FROZEN / name) for name in inputs}}


def freeze():
    settings = config()
    write_new(ROOT / "FREEZE.json", {"schema": "sensitivity-freeze-v1",
              "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "files": file_contract(),
              "config": settings, "cells": cells(settings),
              "execution_authorization": "Independent code review and lead GO required before run."})


def verify_freeze():
    record = json.loads((ROOT / "FREEZE.json").read_text())
    assert record["files"] == file_contract(), "Frozen inputs/code/config changed"
    assert record["config"] == config()
    assert record["cells"] == cells(config())
    return record


def missing_label(failed, successful):
    if failed == successful == 0:
        return "clean anchor using w09 truth/seed; not w03"
    if failed == successful:
        return "equal-loss MCAR control"
    if failed < successful:
        return "reversed-selection negative control"
    return "failure-selective missingness"


def cells(settings):
    output = []
    miss = settings["missingness"]
    for failed, successful in [(0., 0.)] + [(f, s) for f in miss["failed_grade_loss"] for s in miss["successful_grade_loss"]]:
        output.append({"id": f"missing_f{round(100*failed):02d}_s{round(100*successful):02d}",
                       "family": "missingness", "world_id": frozen.worlds()[9].world_id,
                       "seed": miss["seed"], "delta": miss["delta"], "h": miss["h"],
                       "tau": miss["tau"], "failed_grade_loss": failed,
                       "successful_grade_loss": successful, "condition": missing_label(failed, successful)})
    for index in settings["thresholds"]["world_indices"]:
        world = frozen.worlds()[index]
        for tau in settings["thresholds"]["tau"]:
            output.append({"id": f"threshold_w{index:02d}_t{round(100*tau):02d}", "family": "threshold",
                           "world_id": world.world_id, "seed": world.seed, "delta": world.delta,
                           "h": world.h, "tau": tau})
    related = settings["relatedness"]
    for h in related["h"]:
        output.append({"id": f"related_h{round(100*h):02d}", "family": "relatedness",
                       "world_id": frozen.worlds()[4].world_id, "seed": related["seed"],
                       "delta": related["delta"], "h": h, "tau": related["tau"],
                       "paired_difference_icc": h*h/(.5-related["delta"]**2)})
    assert len(output) == 23 and len({x["id"] for x in output}) == 23
    return output


class CapturedRandom:
    """Delegate draws without changing the frozen generator's RNG contract."""
    def __init__(self, generator):
        self.generator = generator
        self.values = []

    def random(self):
        value = self.generator.random()
        self.values.append(value)
        return value

    def clear(self):
        self.values.clear()


def capture_cohort(world, index, generator):
    generator.clear()
    ledger = frozen.simulate_cohort(world, index, generator)
    truth_draws = world.horizon * (world.m + 2)
    assert len(generator.values) == truth_draws + world.horizon * world.m == 2400
    return ledger, tuple(generator.values[truth_draws:])


def remask(ledger, uniforms, failed, successful):
    assert 0 <= failed <= 1 and 0 <= successful <= 1
    assert len(uniforms) == len(ledger.b_bits)
    seen = "".join(str(int(u >= (failed if b == "0" else successful))) for b, u in zip(ledger.b_bits, uniforms))
    return replace(ledger, b_observed=seen, b_multiplicity=seen)


def saved_ledgers(wanted):
    counts = Counter()
    with gzip.open(FROZEN / "data/run1/ledger.jsonl.gz", "rt") as source:
        for line in source:
            value = json.loads(line)
            if value["world_id"] in wanted:
                assert value["cohort_index"] == counts[value["world_id"]]
                counts[value["world_id"]] += 1
                yield frozen.Ledger(**value)
    assert dict(counts) == {name: N for name in wanted}


def evaluate(ledger, tau):
    # Recompute every look and first crossing at the new tau, not old final actions.
    return frozen.evaluate_cohort(frozen.observed_rows(ledger), tau=tau)


class Accumulator:
    def __init__(self, cell):
        self.cell = cell
        self.n = 0
        self.counts = {method: Counter() for method in METHODS}
        self.looks = {method: Counter() for method in METHODS}
        self.final_means = []
        self.missing = 0
        self.coverage = Counter()
        self.actions = {method: bytearray() for method in METHODS}
        self.ledger_hash = hashlib.sha256()

    def add(self, ledger, result, stream):
        assert ledger.cohort_index == self.n
        self.n += 1
        self.ledger_hash.update(json_bytes(asdict(ledger)))
        self.missing += ledger.b_observed.count("0")
        diagnostic = result["looks"][-1]["diagnostics"]
        for name in ("observed_joined_rows", "unique_observed_pairs", "available_contexts", "zero_observation_contexts"):
            self.coverage[name] += diagnostic[name]
        mean = result["looks"][-1]["intervals"]["row"]["mean"]
        assert mean is not None
        self.final_means.append(mean)
        compact = []
        for method in METHODS:
            item = result["methods"][method]
            action, used = item["decision"], item["decision_contexts"]
            self.actions[method].append({"inconclusive": 0, "ship": 1, "hold": 2}[action])
            count = self.counts[method]
            count.update(reporting.event_vector(action, self.cell["delta"] > self.cell["tau"]))
            count["contexts_consumed"] += used
            self.looks[method][used] += 1
            if action == "inconclusive":
                count["integrity_inconclusive" if item["reason"].startswith("integrity_") else "statistical_inconclusive"] += 1
                assert used == 200
            compact.append([action, used])
        stream.write(json_bytes({"cell": self.cell["id"], "cohort": ledger.cohort_index,
                                 "methods": compact, "row_final_mean": mean,
                                 "missing_pairs": ledger.b_observed.count("0")}))

    def finish(self):
        assert self.n == N
        output = {}
        for method in METHODS:
            count = self.counts[method]
            assert sum(count[x] for x in ("false_ship", "false_hold", "correct_ship", "correct_hold", "inconclusive")) == N
            metrics = EVENTS + ("integrity_inconclusive", "statistical_inconclusive")
            output[method] = {"counts": {k: count[k] for k in metrics},
                              "rates": {k: {"estimate": count[k]/N, "wilson95": reporting.wilson(count[k], N)} for k in metrics},
                              "mean_intended_contexts": count["contexts_consumed"]/N,
                              "first_decision_or_horizon_distribution": dict(sorted(self.looks[method].items()))}
        mean = math.fsum(self.final_means)/N
        return {"cell": self.cell, "cohorts": N,
                "truth_class": "switch_worthy" if self.cell["delta"] > self.cell["tau"] else "hold_worthy",
                "ledger_uncompressed_sha256": self.ledger_hash.hexdigest(),
                "missing_pair_fraction": self.missing/(N*1000),
                "final_look_mean_coverage": {name: count/N for name, count in self.coverage.items()},
                "approach1_final_look": {"mean_estimate": mean, "bias_vs_known_delta": mean-self.cell["delta"],
                                          "cohorts_in_mean": N, "stopping_conditioned": False},
                "methods": output}


def paired_contrasts(accumulators):
    """Cohort-matched rate contrasts; pointwise uncertainty, not a winner test."""
    pairs = set()
    for key, accumulator in accumulators.items():
        cell = accumulator.cell
        if cell["family"] == "missingness":
            baselines = ("missing_f00_s00", "missing_f40_s05")
        elif cell["family"] == "threshold":
            baselines = (f"threshold_w{int(cell['world_id'][1:3]):02d}_t02",)
        else:
            baselines = ("related_h30",)
        for baseline in baselines:
            if key != baseline:
                pairs.add((key, baseline))
    output = []
    for key, baseline in sorted(pairs):
        current, reference = accumulators[key], accumulators[baseline]
        assert current.n == reference.n == N
        for method in METHODS:
            sums = {event: [0, 0] for event in EVENTS}
            for left, right in zip(current.actions[method], reference.actions[method]):
                labels = ("inconclusive", "ship", "hold")
                a = reporting.event_vector(labels[left], current.cell["delta"] > current.cell["tau"])
                b = reporting.event_vector(labels[right], reference.cell["delta"] > reference.cell["tau"])
                for event in EVENTS:
                    difference = a[event]-b[event]
                    sums[event][0] += difference
                    sums[event][1] += difference*difference
            output.append({"cell": key, "reference_cell": baseline, "method": method,
                           "paired_cohorts": N, "direction": "cell minus reference_cell",
                           "truth_class_can_differ": (current.cell["delta"] > current.cell["tau"]) != (reference.cell["delta"] > reference.cell["tau"]),
                           "events": {event: reporting.paired_interval(total, squares, N) for event, (total, squares) in sums.items()}})
    return output


class Budget:
    def __init__(self, output, limits):
        self.output, self.limits = output, limits
        self.start = time.monotonic()
        self.cpu = time.process_time()

    def check(self):
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        value = {"wall_seconds": time.monotonic()-self.start, "cpu_seconds": time.process_time()-self.cpu,
                 "resident_memory_bytes": rss,
                 "output_bytes": sum(p.stat().st_size for p in self.output.rglob("*") if p.is_file())}
        for key, limit in self.limits.items():
            if value[key] > limit:
                raise RuntimeError("Resource limit exceeded: " + key)
        return value


def check_original_anchor(result, reference):
    for method in METHODS:
        actual = result["methods"][method]
        expected = reference["methods"][method]
        for event in EVENTS + ("integrity_inconclusive", "statistical_inconclusive"):
            assert actual["counts"][event] == expected["counts"].get(event, 0), (result["cell"]["id"], method, event)
        assert actual["mean_intended_contexts"] == expected["mean_contexts_consumed"]
        assert {str(k): v for k, v in actual["first_decision_or_horizon_distribution"].items()} == expected["context_consumption_distribution"]
    expected_mean = reference["terminal_data_diagnostics"]["row_fixed_mean_estimate"]
    assert math.isclose(result["approach1_final_look"]["mean_estimate"], expected_mean, abs_tol=1e-12, rel_tol=0)


def run():
    if not __debug__:
        raise RuntimeError("Run without -O")
    freeze_record = verify_freeze()
    settings = config()
    output = ROOT / "results"
    output.mkdir(exist_ok=False)
    budget = Budget(output, settings["limits"])
    accumulators = {cell["id"]: Accumulator(cell) for cell in cells(settings)}
    checks = Counter()
    write_new(output / "execution-start.json", {"freeze_sha256": sha(ROOT / "FREEZE.json"),
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
              "cells": 23, "cohorts_per_cell": N, "external_spend_usd": 0})
    try:
        with (output / "cohort-outcomes.jsonl.gz").open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                # Missingness: same truth and same 1,000 loss uniforms in all 11 cells.
                world = frozen.worlds()[9]
                generator = CapturedRandom(random.Random(world.seed))
                group = [a for a in accumulators.values() if a.cell["family"] == "missingness"]
                for saved in saved_ledgers({world.world_id}):
                    budget.check()
                    generated, uniforms = capture_cohort(world, saved.cohort_index, generator)
                    assert generated == saved, "Original w09 full-ledger mismatch"
                    checks["missingness_original_full_ledgers"] += 1
                    for accumulator in group:
                        cell = accumulator.cell
                        ledger = remask(generated, uniforms, cell["failed_grade_loss"], cell["successful_grade_loss"])
                        if (cell["failed_grade_loss"], cell["successful_grade_loss"]) == (.4, .05):
                            assert ledger == saved
                            checks["missingness_remasked_anchor_full_ledgers"] += 1
                        accumulator.add(ledger, evaluate(ledger, cell["tau"]), stream)
                    checks["missingness_paired_truth_and_mask_streams"] += 1
                print("Missingness family complete: 11 cells", flush=True)
                # Threshold: same saved data, with every decision look recomputed.
                group = [a for a in accumulators.values() if a.cell["family"] == "threshold"]
                for ledger in saved_ledgers({a.cell["world_id"] for a in group}):
                    budget.check()
                    for accumulator in group:
                        if accumulator.cell["world_id"] == ledger.world_id:
                            accumulator.add(ledger, evaluate(ledger, accumulator.cell["tau"]), stream)
                    checks["threshold_saved_ledgers_reused_at_all_three_thresholds"] += 1
                print("Threshold family complete: 9 cells", flush=True)
                # Relatedness: same uniforms across h; h changes the truth law itself.
                group = [a for a in accumulators.values() if a.cell["family"] == "relatedness"]
                generators = {a.cell["id"]: CapturedRandom(random.Random(a.cell["seed"])) for a in group}
                worlds = {a.cell["id"]: replace(frozen.worlds()[4], h=a.cell["h"]) for a in group}
                for saved in saved_ledgers({frozen.worlds()[4].world_id}):
                    budget.check()
                    baseline_draws = None
                    for accumulator in group:
                        cell = accumulator.cell
                        generator = generators[cell["id"]]
                        ledger, _ = capture_cohort(worlds[cell["id"]], saved.cohort_index, generator)
                        if baseline_draws is None:
                            baseline_draws = tuple(generator.values)
                        else:
                            assert tuple(generator.values) == baseline_draws
                        if cell["h"] == .3:
                            assert ledger == saved, "Original h=.30 full-ledger mismatch"
                            checks["relatedness_original_full_ledgers"] += 1
                        accumulator.add(ledger, evaluate(ledger, cell["tau"]), stream)
                    checks["relatedness_identical_full_uniform_streams"] += 1
                print("Relatedness family complete: 3 cells", flush=True)
        results = [a.finish() for a in accumulators.values()]
        reference = {x["world_id"]: x for x in json.loads((FROZEN / "results/analysis.json").read_text())["worlds"]}
        for result in results:
            cell = result["cell"]
            anchor = cell["id"] in ("missing_f40_s05", "related_h30") or (cell["family"] == "threshold" and cell["tau"] == .02)
            if anchor:
                check_original_anchor(result, reference[cell["world_id"]])
                checks["original_aggregate_anchor_cells"] += 1
        assert checks["original_aggregate_anchor_cells"] == 5
        record = {"schema": "sensitivity-results-v1", "status": "exploratory",
                  "freeze_sha256": sha(ROOT / "FREEZE.json"), "methods_order": METHODS,
                  "checks": dict(checks), "cells": results,
                  "interpretation": ["Pointwise Monte Carlo intervals, no multiplicity-adjusted cross-cell claims.",
                                     "Cells share random streams/data and are not independent experiments.",
                                     "Sensitivity assumptions were chosen after original results, not prespecified before that study.",
                                     "Final-look mean uses all 2000 cohorts, not a stopping-conditioned subset.",
                                     "A strict integrity guard's inconclusive outcome is not a correct product choice."]}
        write_new(output / "analysis.json", record)
        write_new(output / "paired-contrasts.json", {"schema": "sensitivity-paired-contrasts-v1",
                  "scope": "Pointwise paired Monte Carlo intervals; no simultaneous coverage or independent-cell assumption. Threshold changes can change the truth class.",
                  "contrasts": paired_contrasts(accumulators)})
        table = [{"cell_id": r["cell"]["id"], "family": r["cell"]["family"], "method": m,
                  "parameters": r["cell"], "truth_class": r["truth_class"],
                  "counts": r["methods"][m]["counts"], "rates": r["methods"][m]["rates"],
                  "mean_intended_contexts": r["methods"][m]["mean_intended_contexts"],
                  "final_look_mean": r["approach1_final_look"]["mean_estimate"],
                  "final_look_bias": r["approach1_final_look"]["bias_vs_known_delta"]} for r in results for m in METHODS]
        assert len(table) == 138
        write_new(output / "table-source.json", {"schema": "sensitivity-table-v1", "rows": table})
        assert freeze_record["files"] == file_contract(), "Source inputs changed during run"
        resources = budget.check()
        write_new(output / "execution.json", {"status": "passed", "cells": 23, "cohort_cell_evaluations": 46000,
                  "resources": resources, "external_spend_usd": 0, "checks": dict(checks),
                  "files": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}})
        print(json.dumps({"status": "passed", "checks": dict(checks), "resources": resources}, indent=2))
    except BaseException as error:
        write_new(output / "error.json", {"error_type": type(error).__name__, "message": str(error),
                  "completed_cell_cohorts": {name: value.n for name, value in accumulators.items()},
                  "checks": dict(checks), "elapsed_seconds": time.monotonic()-budget.start})
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("freeze", "run"):
        raise SystemExit("Usage: python3 -B analyze.py freeze|run")
    (freeze if sys.argv[1] == "freeze" else run)()
