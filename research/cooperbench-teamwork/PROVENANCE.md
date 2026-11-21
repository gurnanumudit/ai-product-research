# Provenance and release boundary

Study: CooperBench broader comparison, final recovery-v4; completed and internally accepted November 19, 2026. Owner requested GitHub code publication and article linkage November 20. Article remains a separate private review draft.

Public inputs are an explicit field allowlist projected from the accepted actual-audit metadata. Hidden tests, reference patches, feature-description bodies, model responses, commands, raw logs, receipts, encrypted state, credentials, local paths and container/image identifiers are excluded. A merge record is projected to `status` only. Phase objects retain only numeric counters and durations. The expected aggregate analysis is copied unchanged.

`reference/source-provenance.json` records SHA-256 commitments to the original audit, report source, analysis, collector and contract sources without exposing private paths. All released pure function bodies in `analysis.py` are exact excerpts of the accepted reporter. Only the module header/imports/constants and the local `require` helper are supplied independently; there is no original report entrypoint, claim creation or execution gate. The safe offline driver is new publication code.

`source-excerpts/prompts-and-phases.mjs.txt` is the exact phaseSpec/instruction source range; `run-team.mjs.txt` is the exact runTeam source range. They are inspection-only excerpts with unresolved original dependencies, not launchers. They do not include benchmark feature descriptions or private reference material. No claim is made that these excerpts recreate the entire original environment.

`SHA256SUMS.json` commits to package files except itself. Numerical equality does not independently authenticate grading, provider bills or raw custody. The internal actual review accepted the full private evidence package with no material objections; this was a separate agent review, not academic peer review. The public replay independently checks rational missing-outcome arithmetic in addition to reusing the reviewed pure analysis.

Benchmark attribution: CooperBench; repository/base labels and feature IDs are retained for traceability. No upstream test, task-description or solution bodies are redistributed. Third-party materials retain their own rights. Original analysis and publication software use this repository's MIT license.
