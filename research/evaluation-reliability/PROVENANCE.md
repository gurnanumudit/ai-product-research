# Provenance and public packaging

## Origin

The scientific protocol and core implementation were frozen on September 27, 2026, before the reported simulation. The study used 15 declared worlds, 2,000 cohorts per world and seeds 2709271800–2709271814. There are no private benchmark answers, real customer records or model-generated outcomes in this package.

The six files named by [SOURCE-FREEZE.json](SOURCE-FREEZE.json) are published byte-for-byte unchanged. The original protocol SHA-256 is:

`24aa3bd8f1dbcae428dd22ab6b65c9be44b34d8d5d074d46759323a561774fef`

The unchanged protocol includes its historical initial-phase restriction on publication; the author subsequently authorized publication. [AUTHORIZATION.md](AUTHORIZATION.md) is a new public scope note, not a copy of the original internal authorization.

The simulation, tests, summarizer, independent prefix implementation, saved-result auditor, table renderer, analysis, rendered tables, compressed ledger, compressed decisions and count summary are unchanged from the completed study. `reproduce.py`, the public documentation, publication manifest and article-table export are publication additions. No scientific scenario, sample size, decision rule or observed result was changed for publication.

## Explicit metadata redactions

Only public copies were edited. The original private evidence remains preserved.

| Public file | Change | Original SHA-256 | Public SHA-256 |
|---|---|---|---|
| `run1/manifest.json` | Replace the author's absolute local `protocol_path` with `PROTOCOL.md` | `79685e805cd5b3bbb6f581a09cbf6dd871bfc4057000a7ebed582af89ade4837` | `cec3ee3e470995e4d7e92ce0682e8ae39b968fec6fa26706023ac2e79ee7f1d7` |
| `run1/execution.json` | Update `files.manifest.json` to the public manifest hash | `2c88e926f2bf926ac0d8fa34809259aa440043ef76ad92baac77d9e55c6fcac8` | `e3b79e372d48436e0679bcfbe55f14ca83e9d78dfa9978ca1925af2d819e5b39` |

Scientific metadata values, counts, execution measurements and all other bytes are unchanged. The published execution receipt is an explicitly transformed historical receipt, not the byte-identical original.

The three primary scientific streams retain their original hashes:

| File | SHA-256 |
|---|---|
| `run1/ledger.jsonl.gz` | `ea7ebf95c5ffa9069df5c748c200a37dfe8fffec4792c55ff4eea92d7b768752` |
| `run1/decisions.jsonl.gz` | `ed1ebb7e0da974936eec5cc1fde5c8c547cae8412ab86fd1994c93d7a7ddaad0` |
| `run1/summary.json` | `4bfcd97042621a175f526c578fbb0cdbd3b52740075344e9bc6b5db57ce13531` |

## Verification scope

`reproduce.py` verifies the public package manifest and frozen-source hashes, executes deterministic tests, recalculates the saved aggregate analysis and complete rate table, audits saved outputs, and checks the article's 90 rows against the full-precision source. The auditor checks 30,000 cohort identities, 210,000 method/recoding records, 225 paired contrasts and 600 independently calculated intervals from 30 prescribed prefix cohorts.

The optional `--rerun` reproduces the same fixed seeds. It compares decompressed scientific JSON streams, count output and aggregate analysis. It does not require byte equality for the new run's manifest or execution receipt: machine paths, Python version, runtime, memory measurements and compression implementation can differ. It writes to a new temporary directory and never rewrites this package.

The original run and its historical full same-seed replay matched all four deterministic output files in their original environment. That historical check is distinct from the default public audit, which does not execute a full simulation. A full replay is not additional scientific evidence.

`PUBLICATION-MANIFEST.json` records SHA-256 values for the published files, excluding itself. A hash verifies content consistency against this package; it does not independently establish the historical freeze date or external validity of the design.
