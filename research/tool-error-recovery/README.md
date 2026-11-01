# Tool-error recovery: research source code

Code for the study accompanying **When an AI’s test report is wrong**. The article remains an unpublished draft. This branch archives the research implementation; it does not publish the article or deploy the website.

## What is included

The `source/` folders preserve the original pilot, main collection, first continuation and final completion source files byte-for-byte. Keeping the original sibling folder names preserves cross-phase source references.

| Phase | Folder | Purpose |
| --- | --- | --- |
| Pilot | `econ-tool-error-recovery-20261027` | Sampling, interaction, grading, billing checks and analysis |
| Main | `econ-tool-error-recovery-20261027-main-v1` | Main collector, grading worker, analysis and audit |
| First continuation | `econ-tool-error-recovery-20261029-continuation-v1` | Bounded continuation, resource management and combined reporting |
| Final completion | `econ-tool-error-recovery-20261029-completion-v2` | Saved-response recovery, bounded receipt/read handling and final reporting |

Tests are included as historical implementation evidence. `SOURCE-MANIFEST.json` records the SHA-256 of every archived file and its original relative source path. Run `python3 research/tool-error-recovery/verify_archive.py` from the repository root to check the archive without importing or executing study code.

## Reading the implementation

Start with main `interaction.mjs` for the three workflows and report handling, `worker.py` for the grading wrapper, and `analyze.py` for the statistical calculations. The final completion `continuation.mjs`, `transport.mjs`, `model-client.mjs` and `report_completion.py` show the operational recovery and audit changes. The historical sources remain separate so later repairs cannot be mistaken for the implementation used in earlier phases.

## Scope and reproducibility

This is a **source archive, not a self-contained experiment or offline results-reproduction package**. Original entry points depend on private manifests, schedules, saved evidence, benchmark inputs, local runtime paths and infrastructure adapters that are not included. Some historical tests also require those files. Syntax validation is not a claim that the whole test suite runs from this archive.

The protocol compared baseline, a fixed warning, and automatic first verification using the same model configuration and task assignments. Only first-report feedback was altered; final all-hidden-test success was the outcome. The completed analysis is a post-interruption amended completion; the original incomplete report remains historical primary. Public benchmarking, one model configuration and unadjusted descriptive paired intervals limit interpretation.

No credentials, private runtime database, raw provider traces, task candidates, hidden-test source, resource identifiers, consumed claims, financial receipts or internal review records are distributed here. The operator-specific one-off host cleanup utility is excluded. Model/service prices and paths embedded in the historical code reflect the experiment, not current guidance.

**Do not use these archived entry points to restart the completed study.** No collector, model request, grader or actual reporter was rerun to create this archive. The original evidence remains unchanged.

Original code is covered by the repository MIT license. Referenced third-party software and benchmark materials retain their own licenses; they are not bundled here.
