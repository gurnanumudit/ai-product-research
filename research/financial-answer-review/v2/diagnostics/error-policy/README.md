# Frozen error-taxonomy × review-policy diagnostic

Code-only follow-up to the financial-answer review study. This module joins a previously frozen, policy-blind error taxonomy to two already selected review sets. It reports the four paired membership cells, separates common mandatory withholding from discretionary selection, and describes existing answer-versus-own-expression differences in their stated units.

This is a descriptive diagnostic, not a new experiment, policy calibration, target adjudication or financial-materiality model. It does not modify the original labels, select alternative policies, rerank cases, introduce severity thresholds, estimate human correction, or establish overall policy superiority. No results, source excerpts, audit decisions or model traces are distributed here.

## Offline synthetic tests

From the containing `v2` directory, with Python 3.11 or later:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s diagnostics/error-policy -p test_diagnose.py -v
```

All 14 tests use synthetic fixtures. No credentials, network, dataset or actual model outputs are required. The tests import only the existing frozen parsing/evaluation helpers from `v2/implementation`. They cover taxonomy partitions, fixed review-set membership, mandatory overlap, sample/identity failures, exact percentage-point arithmetic and medians, aggregate-replication failure, bounded trace identity checks and fresh-output protection.

## Supplied local records required for an actual reproduction

The script is intentionally bound to the original reviewed input hashes and historical selection rules; it is not a generic interface for silently changing the research sample. A reproducer must separately supply the original `TEST-ERROR-AUDIT.md`, `analysis/test-summary.json`, `analysis/test-audit-neutral.json`, the permitted arithmetic-roster responses in `runs/test-01/`, and the unchanged implementation helpers. These records are not generated, downloaded, licensed or certified by this code. The audit's original sections and exact response/ID mapping are required; parsing fails closed if categories or identities differ.

From `v2`, use explicit local paths and a new output directory outside every input archive:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 diagnostics/error-policy/diagnose.py --audit /absolute/archive/TEST-ERROR-AUDIT.md --summary /absolute/archive/analysis/test-summary.json --neutral /absolute/archive/analysis/test-audit-neutral.json --implementation /absolute/path/to/v2/implementation --run-dir /absolute/archive/runs/test-01 --out /absolute/new-diagnostic-output
```

The frozen neutral packet contains absolute response-file paths. Its recorded run directory must be present at the original absolute location; `--run-dir` does not remap those paths. Do not edit the hash-pinned packet to relocate it. The example paths are placeholders for the recorded locations, not a relocation facility.

The script reads only the response roster authorized by the frozen audit, not other response bodies, source contexts or reference targets. It verifies original file identities, sample order, the complete review partitions and common mandatory membership. Exact answer-minus-own-expression calculations use the existing safe evaluator. The pre-existing percent-case aggregate must replicate before magnitudes are split by membership. These differences are percentage points—not relative-percent error, target validity, financial importance or realized loss. No mixed-unit monetary summary is created.

Outputs are `results.json`, `provenance.json` and `resources.json`; a failed invocation records `failure.json`. They are local artifacts, not an authorization to publish their contents. Existing or symlinked output destinations are refused, and files are created exclusively. A failed run may leave its new directory; preserve it and investigate rather than silently retrying or changing definitions. The script never calls a provider or downloads inputs.

## Copy provenance and limits

The historical scientific script SHA256 is `b50efbe26297ad7d3e45d506c9e1ca8f47bd8d8d2f7311354a90e6a139795990`; the historical tests are `44c51910e1ac1e3e382163c12e383c9b1e9cfd94aa6d09c8f060d4fbf2c97b63`. Both remain unchanged in the original research archive.

Only two portability changes were made in these copies: provenance stores the historical plan/review hashes instead of trying to read adjacent private documents, and the synthetic test's helper lookup points to the already delivered `v2/implementation`. No input hash, fixture, arithmetic, sample rule, policy choice or result definition changed. Thus generated provenance metadata is not byte-identical to the original execution receipt. The original plan/review content and all empirical artifacts remain outside this code package. Code licensing follows the repository license; data and report rights are separate.
