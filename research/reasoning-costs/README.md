# When is more reasoning worth it?

[Read the published article](https://research.muditgurnani.chatgpt.site/research/when-is-more-reasoning-worth-it) · [All studies](../README.md)

**Question:** When does extra reasoning improve analytical answers enough to justify its additional model cost?

We compared three models at three reasoning settings on the same 134 DSBench data-analysis questions. This package contains the derived outcomes, recorded costs and offline analysis behind the article.

## Study at a glance

- **Tasks:** 134 questions from 24 source contexts, including Excel workbooks: 29 easy, 55 medium and 50 hard.
- **Configurations:** Luna, Terra and Sol, each with none, low and high reasoning. These are historical recorded model routes, not a claim of current availability; exact identifiers are in [Methods](METHODS.md).
- **Comparison:** correct final answers and recorded model-cost exposure across the nine configurations, using the same questions and tools.
- **Design:** a descriptive comparison, not a randomized experiment or a validated model-routing policy. Difficulty labels were assigned by the study.

## Reproduce the numbers

From the repository root, with Python 3.10 or later. No dependencies, credentials, network access or model calls:

```sh
python3 research/reasoning-costs/reproduce.py
```

The script checks the exported records against frozen article results and writes
`research/reasoning-costs/output/analysis.json` and `research/reasoning-costs/output/results.md` (ignored by Git). It reproduces all 27
model × reasoning × difficulty result/cost cells, overall and cohort results,
paired changes, equal-context averages, failure-filtered checks, the hard-question
cost frontier and the illustrative dollar-impact comparisons.

This is **numerical reproduction from derived outcome records**, not a rerun
of the experiment or independent regrading of answers. The original model-serving
environment, workbook inputs, prompts and raw responses are not included.

## Package

| File | Purpose |
|---|---|
| [reproduce.py](reproduce.py) | Portable offline analysis and verification |
| [data/results.jsonl](data/results.jsonl) | 1,251 assigned question × model × reasoning cells; 1,206 included in the matched analysis |
| [data/costs.jsonl](data/costs.jsonl) | 1,212 physical cost records for the retained questions, including six retry pairs |
| [reference/expected.json](reference/expected.json) | Frozen numerical targets, independently checked against exported records |
| [reference/provenance.json](reference/provenance.json) | Source version and integrity hashes |
| [METHODS.md](METHODS.md) | Scoring, exclusions, cost accounting and interpretation |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Fields and join keys for further analysis |
| [PROVENANCE.md](PROVENANCE.md) | Attribution, release scope and reproduction boundaries |

The records preserve question identity, source context, difficulty, configuration,
collection cohort and failure classification for regrouping or post-hoc analysis.
Do not treat configurations or questions sharing a workbook as independent
samples. No statistical significance or universal configuration ranking is claimed.

## Headline interpretation

Low reasoning improved success over none for each tested model and difficulty
group. High reasoning's benefit varied by model and workload. Lower model cost
and highest observed accuracy are different objectives; the cost of a wrong
answer is not measured here.

Cost exposure includes recorded charges and pending reservations, not settled invoices or the full cost of deployment. Selected tasks, shared source contexts and changes in execution conditions limit generalization. See [Methods](METHODS.md) for exclusions, retries and sensitivity checks.

The recommendation comparisons are illustrative, not a validated routing policy.
They use Luna low for easy/medium and Luna high for hard as lower-cost options,
compared with the most accurate setting (cheapest when tied). Cost per correct
answer alone instead favors Luna low in each band.
