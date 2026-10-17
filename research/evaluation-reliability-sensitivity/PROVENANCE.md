# Provenance and article mapping

This package supplies the assumption checks in [How to avoid false confidence in AI evaluations](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations).

## Research chronology

The baseline study was specified and executed separately. Its code, protocol and results remain in [evaluation-reliability](../evaluation-reliability/README.md), unchanged by this release.

The sensitivity grid was selected after the baseline findings were known. Its configuration, runner and inputs were frozen on October 17, 2026, before execution; [FREEZE.json](FREEZE.json) records the timestamp and hashes. These are exploratory checks, not part of the baseline preregistration. Historical release plans in the frozen [design](DESIGN.md) describe the plan at that time, not the current publication status.

The website retains the article's original September 30 date and integrates the findings into one narrative. That display date is not the execution date of this sensitivity analysis. Git history and the frozen research records preserve the chronology.

## Article-to-evidence map

| Article section | Evidence |
| --- | --- |
| Finding 1: relatedness | Three `relatedness` settings in `results/analysis.json` |
| Finding 2: missing grades | Eleven `missingness` settings in `results/analysis.json` |
| Finding 3: required improvement | Nine `threshold` settings in `results/analysis.json` |
| All settings and uncertainty | [Full analysis](results/analysis.json), [paired contrasts](results/paired-contrasts.json) and [independent review](independent-review.json) |

Each setting contains 2,000 evaluations. Settings reuse outcomes or random draws, so the 46,000 setting-level evaluations are not independent new experiments. There were no model calls or measurements of production outcomes.

## Verification and presentation

The package verifier checks frozen input/output hashes, nine deterministic tests and a separate saved-result audit. The audit covers 966 aggregate rates/intervals, 18,000 threshold trajectories, 46 independently regenerated prefix evaluations and 1,176 paired comparisons. It does not independently regenerate every missingness or relatedness evaluation.

The [site exporter](../../site/scripts/export-evaluation-sensitivity.mjs) maps the audited results to 23 settings, 138 approach rows and 552 displayed metrics. [Presentation tests](../../site/tests/evaluation-sensitivity.test.mjs) check those values, source hashes, baseline anchors, article links and the original figures. Presentation edits do not change frozen evidence.

Original software follows the repository's [MIT license](../../LICENSE). The analysis reuses the original study's synthetic data and implementation; see its [provenance](../evaluation-reliability/PROVENANCE.md) for the source history.
