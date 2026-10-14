"""Audit the published study without modifying frozen evidence or calling APIs."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
PROTOCOL_SHA256 = "24aa3bd8f1dbcae428dd22ab6b65c9be44b34d8d5d074d46759323a561774fef"


def sha(path, compressed=False):
    digest = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_package():
    manifest = json.loads((ROOT / "PUBLICATION-MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid manifest path")
        if sha(ROOT / relative) != expected:
            raise ValueError("Published file hash mismatch: " + name)
    return len(manifest["files"])


def verify_article(analysis):
    article = json.loads((ROOT / "article-results.json").read_text())
    worlds = {world["world_id"]: world for world in analysis["worlds"]}
    methods = ("row_fixed", "row_peek", "context_fixed", "context_peek",
               "context_adjusted", "integrity_adjusted")
    if len(article["worlds"]) != 15 or {w["id"] for w in article["worlds"]} != set(worlds):
        raise ValueError("Article scenario coverage mismatch")
    checked = 0
    for world in article["worlds"]:
        source = worlds[world["id"]]
        assert world["trueGain"] == round(100 * source["spec"]["delta"])
        assert tuple(row["method"] for row in world["rows"]) == methods
        for row in world["rows"]:
            values = source["methods"][row["method"]]
            rates = values["rates"]
            expected = {
                "falseShip": rates["false_ship"]["estimate"] * 100,
                "falseHold": rates["false_hold"]["estimate"] * 100,
                "correct": rates["correct_decision"]["estimate"] * 100,
                "inconclusive": rates["inconclusive"]["estimate"] * 100,
                "meanContexts": values["mean_contexts_consumed"],
                "falseShipLow": rates["false_ship"]["wilson95"][0] * 100,
                "falseShipHigh": rates["false_ship"]["wilson95"][1] * 100,
                "correctLow": rates["correct_decision"]["wilson95"][0] * 100,
                "correctHigh": rates["correct_decision"]["wilson95"][1] * 100,
            }
            for name, number in expected.items():
                assert abs(row[name] - round(number, 2)) < 1e-9, (world["id"], row["method"], name)
            checked += 1
    assert checked == 90
    return checked


def command(*args):
    subprocess.run([sys.executable, "-B", *map(str, args)], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rerun", action="store_true", help="Also reproduce all frozen seeds into a fresh temporary directory (no new scenarios).")
    args = parser.parse_args()
    if sys.flags.optimize:
        raise SystemExit("Do not use Python -O: the frozen audit uses assertions.")
    verified = verify_package()
    output = Path(tempfile.mkdtemp(prefix="evaluation-reliability-"))
    print("Verification output (retained):", output, flush=True)
    command("-m", "unittest", "-v", "test_simulation", "test_review")
    command("independent_reproduce.py")
    command("summarize.py", ROOT / "run1", output / "analysis.json")
    assert sha(output / "analysis.json") == sha(ROOT / "analysis.json"), "Saved analysis differs"
    command("audit_saved.py", ROOT / "run1", output / "analysis.json")
    command("render_tables.py", output / "analysis.json", output / "ALL-RATES.md")
    assert sha(output / "ALL-RATES.md") == sha(ROOT / "ALL-RATES.md"), "Rendered rates differ"
    rows = verify_article(json.loads((output / "analysis.json").read_text()))
    if args.rerun:
        run = output / "rerun"
        command("-c", "import simulation, sys; simulation.execute_study(sys.argv[1], sys.argv[2], sys.argv[3])",
                run, ROOT / "PROTOCOL.md", PROTOCOL_SHA256)
        # Paths, Python version, runtime and gzip implementations can vary by host.
        # Compare the scientific JSON streams separately from those metadata.
        for name in ("ledger.jsonl.gz", "decisions.jsonl.gz"):
            assert sha(run / name, compressed=True) == sha(ROOT / "run1" / name, compressed=True), name
        assert sha(run / "summary.json") == sha(ROOT / "run1" / "summary.json"), "Rerun counts differ"
        command("summarize.py", run, output / "rerun-analysis.json")
        assert sha(output / "rerun-analysis.json") == sha(ROOT / "analysis.json"), "Rerun analysis differs"
        command("audit_saved.py", run, output / "rerun-analysis.json")
    print(json.dumps({"status": "passed", "package_files_verified": verified,
                      "article_rows_verified": rows, "full_frozen_seed_rerun": args.rerun,
                      "output_directory": str(output)}, indent=2))


if __name__ == "__main__":
    main()
