#!/usr/bin/env python3
"""Recompute published numerical results offline. Python 3.10+, standard library."""
import collections
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
MODELS = ["openai/gpt-5.6-terra", "anthropic/claude-sonnet-5", "google/gemini-3.8-flash"]


def read(path):
    return json.loads(path.read_text())


def compare(actual, expected, at="root"):
    """Strict topology/count checks; tolerate only floating-point roundoff."""
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (at, set(actual) ^ set(expected))
        for k in expected:
            compare(actual[k], expected[k], at + "." + k)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), (at, len(actual), len(expected))
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare(a, e, at + "[" + str(i) + "]")
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, abs_tol=1e-12, rel_tol=1e-12), (at, actual, expected)
    else:
        assert actual == expected, (at, actual, expected)


def quantile(values, p):
    values = sorted(values)
    x = (len(values)-1)*p
    lo, hi = math.floor(x), math.ceil(x)
    return values[lo] + (values[hi]-values[lo])*(x-lo)


def source_effect(doc):
    cells = {(r["phase"], r["task_id"], r["model"], r["condition"], r["repeat"]): r for r in doc["cells"]}
    rows = []
    def predictions(phase, task, model, condition):
        return [cells.get((phase, task, model, condition, repeat)) for repeat in (1, 2)]
    def bounds(records):
        valid = [r for r in records if r and r["valid"]]
        n = sum(r["decision"] == "APPROVE" for r in valid)
        return n / 2, (n + 2 - len(valid)) / 2
    for phase in (1, 2):
        # Preserve original roster order because seeded bootstrap draws depend on it.
        tasks = [r["task_id"] for r in doc["labels"] if r["phase"] == phase]
        complete, model_bounds = {}, {}
        for model in MODELS:
            diffs, all_bounds = {}, []
            for task in tasks:
                left, right = predictions(phase, task, model, "E"), predictions(phase, task, model, "D")
                ll, lu = bounds(left)
                rl, ru = bounds(right)
                all_bounds.append((ll-ru, lu-rl))
                if all(r and r["valid"] for r in left+right):
                    diffs[task] = ll-rl
            complete[model], model_bounds[model] = diffs, all_bounds
        common = [t for t in tasks if all(t in complete[m] for m in MODELS)]
        complete["pooled"] = {t: statistics.fmean(complete[m][t] for m in MODELS) for t in common}
        model_bounds["pooled"] = [b for m in MODELS for b in model_bounds[m]]
        for model in MODELS + ["pooled"]:
            values = list(complete[model].values())
            salt = "evidence-attribution-batch" + str(phase) + "-task-bootstrap-v1" + "E-Dapproval" + model
            rng = random.Random(int(hashlib.sha256(salt.encode()).hexdigest(), 16))
            draws = [statistics.fmean(rng.choices(values, k=len(values))) for _ in range(10000)]
            rows.append(dict(phase=phase, model=model, n_tasks=len(values), mean=statistics.fmean(values),
                             bootstrap_95_interval=[quantile(draws, .025), quantile(draws, .975)],
                             full_roster_missingness_bounds=[statistics.fmean(b[i] for b in model_bounds[model]) for i in (0, 1)]))
    # Match the published figure-data order: model rows first, pooled rows last.
    return sorted(rows, key=lambda r: (r["model"] == "pooled", r["phase"], (MODELS+["pooled"]).index(r["model"])))


def main():
    doc = read(ROOT / "data/reviews.json")
    assert set(doc) == {"labels", "cells"}
    for r in doc["labels"]:
        assert set(r) == {"phase", "task_id", "resolved", "patch_sha256", "report_url", "report_sha256", "patch_url", "patch_file_sha256"}
        for field in ("report_url", "patch_url"):
            url = urlparse(r[field])
            assert url.scheme == "https" and url.hostname in ("huggingface.co", "swe-bench-submissions.s3.amazonaws.com")
            assert not url.username and not url.password and not url.query and not url.fragment
        for field in ("patch_sha256", "report_sha256", "patch_file_sha256"):
            assert len(r[field]) == 64 and all(c in "0123456789abcdef" for c in r[field])
    label_index = {(r["phase"], r["task_id"]): r["resolved"] for r in doc["labels"]}
    keys = [(r["phase"], r["task_id"], r["model"], r["condition"], r["repeat"]) for r in doc["cells"]]
    assert len(label_index) == 60 and len(set(keys)) == len(keys) == 1736
    assert not ({t for p, t in label_index if p == 1} & {t for p, t in label_index if p == 2})
    for r in doc["cells"]:
        assert r["resolved"] == label_index[r["phase"], r["task_id"]]
        assert r["model"] in MODELS and r["condition"] in "ABCDE" and r["repeat"] in (1, 2)
        assert set(r) == ({"phase", "task_id", "model", "condition", "repeat", "valid", "resolved", "decision"} if r["valid"] else
                          {"phase", "task_id", "model", "condition", "repeat", "valid", "resolved"})
        if r["valid"]:
            assert r["decision"] in ("APPROVE", "HOLD", "ABSTAIN")
    counts = []
    for phase, planned, attempted, usable in ((1, 600, 600, 563), (2, 1200, 1136, 1129)):
        rows = [r for r in doc["cells"] if r["phase"] == phase]
        assert len(rows) == attempted and sum(r["valid"] for r in rows) == usable
        assert sum(v for (p, t), v in label_index.items() if p == phase) == (10 if phase == 1 else 20)
        counts.append(dict(phase=phase, planned=planned, attempted=attempted, usable=usable,
                           invalid=attempted-usable, unattempted=planned-attempted))
    decisions = dict(collections.Counter(r["decision"] for r in doc["cells"] if r["valid"]))
    assert decisions == {"APPROVE": 568, "HOLD": 1114, "ABSTAIN": 10}
    result = json.loads(subprocess.check_output([sys.executable, str(ROOT / "analysis/supplementary.py")], text=True))
    numeric = {k: v for k, v in result.items() if k not in ("source_sha256", "analysis_status", "tests")}
    compare(numeric, read(ROOT / "reference/article-statistics.json"))
    approval = []
    for row in result["raw"]:
        phase, model, condition = row["phase"], row["model"], row["condition"]
        item = {k: row[k] for k in ("phase", "model", "condition", "planned", "attempted", "usable", "invalid",
                                   "unattempted", "correct_approvals", "incorrect_approvals", "approvals", "hold", "abstain")}
        item.update(benchmark_correct_responses=row["correct_reviews"], benchmark_incorrect_responses=row["incorrect_reviews"],
                    policy_agreement_numerator=row["policy_agreements"], **row["estimate"])
        item["distinct_usable_tasks"] = len({r["task_id"] for r in doc["cells"] if r["phase"] == phase and
                                            r["model"] == model and r["condition"] == condition and r["valid"]})
        approval.append(item)
    approval.sort(key=lambda r: (r["phase"], MODELS.index(r["model"]), r["condition"]))
    figure_data = dict(approval=approval, benchmark_approval=result["figure2"], source_effect=source_effect(doc))
    compare(figure_data, read(ROOT / "reference/figure-data.json"))
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    for name, value in (("article-statistics.json", result), ("figure-data.json", figure_data),
                        ("verification.json", dict(status="PASS", phase_counts=counts, decisions=decisions,
                        checks=["All 30 raw cells", "All 30 matched-condition cells", "All 30 matched-model contrasts",
                                "All 24 matched-scenario contrasts", "All 60 benchmark chart points",
                                "All 8 original source-effect estimates and bootstrap intervals"],
                        scope="Offline numerical reproduction from derived records; not an end-to-end experiment rerun"))):
        (out / name).write_text(json.dumps(value, indent=2) + "\n")
    subprocess.run([sys.executable, str(ROOT / "analysis/render_figures.py")], check=True)
    print("PASS: 1,800 planned; 1,736 attempted; 1,692 usable (563 + 1,129).")
    print("PASS: published raw, matched and source-label results; three SVG figures regenerated.")
    print("This reproduces analysis of derived records, not the original model experiment.")


if __name__ == "__main__":
    main()
