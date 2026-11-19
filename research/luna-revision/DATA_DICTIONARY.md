# Public data dictionary

## data/outcomes.jsonl

One JSON object per logical scientific endpoint, exactly 600 rows.

| Field | Meaning |
|---|---|
| `family_id` | Release-local rank: coding-001..100, graph-001..050, sokoban-001..050. Ranks preserve original canonical-family ordering within stratum, not collection order. |
| `domain`, `stratum` | coding / VERY_HARD, or planning / graph_color or sokoban. Labels are metadata, not text supplied to the model. |
| `workflow` | A simple prompt; S checklist; R neutral revision of saved S. |
| `model` | Historical route alias, openai/gpt-6-luna. |
| `resolved` | True for every scientific endpoint. |
| `passed` | Saved finite-check binary outcome; all invalid or truncated endpoints fail. |
| `valid` | True, false or null. Null is absent validity metadata, not an unresolved grade. |
| `truncated` | Saved output-truncation indicator; nullable schema, none missing in this study. |
| `output_status` | Saved compact status label; no answer text or freeform grading reason. |
| `cost_nano_usd` | Settled endpoint API charge, integer nano-USD. |
| `pending_reserve_nano_usd` | Zero for every usable endpoint. |
| `tokens` | Input, output, total, cached, cache_write and reasoning counts. Details overlap the input/output totals. |
| `times_ms` | Nullable measured logical_elapsed, physical_elapsed, receipt_wait, receipt_elapsed and grading_elapsed durations, milliseconds. |

The single replacement has unknown logical elapsed duration and a separately recorded physical duration. Family identifiers do not reveal task text or identify a source problem. They are stable within this release, not a guarantee that outcomes could never be linked using other information.

## data/original-unresolved-attempt.json

The extra original coding A attempt is a physical accounting record, with `logical_answer: false`, null actual charge/tokens/full durations, and a 591,016,800 nano-USD reserve. `transport_segment_elapsed_ms` records only the observed transport segment. It is not added to duration totals. There is no pass/fail field and no source/provider identifier.

## reference files

`summary.json` is an allowlisted projection preserving exact original JSON values. It contains four primary comparisons, bootstrap metadata, cells, current and historical aggregate accounting, measured phase times and original limitations. It is not a byte copy of the private canonical file. `publication_authorized: false` is preserved historical metadata from the reporting stage, not a statement about later owner publication decisions.

`pairs.json` contains the 200 public family IDs and their A/S/R booleans, plus the S−A and R−S differences. `PROVENANCE.json` supplies source hashes, the exact list of projected fields, the ID transformation, extracted function names, and omitted material.

For primary tests, rational p-value numerator/denominator strings retain exact arithmetic; floating-point values are conveniences. `bootstrap_pointwise95` is in proportions, so 0.10 is ten percentage points. `formal_improvement` is positive direction plus Holm rejection, not a claim of general superiority.

Each accounting metric records `known_sum`, `missing`, `complete_sum` and `n`. A null complete sum is unknown, not zero. Current physical accounting has 601 rows, while usable-response accounting has 600. Historical accounting has 397 physical rows and 396 logical endpoints. Historical and lifetime tables are frozen aggregates; only current-run tables are rebuilt from released row-level measurements. Cost arithmetic against the historical aggregates is checked separately.

## Code and output

`computation.py` contains twelve unchanged pure functions extracted from the frozen internal engine. `reproduce.py` is the new public-data wrapper. Neither imports historical launchers or canonical reporting code. `test_reproduce.py` contains small mathematical fixtures and schema rejection tests. `HANDOFF.json` hashes every distributed file except itself; it records validation and pending independent export review. Optional `output/reproduced.json` is derived scratch output, not a frozen reference.
