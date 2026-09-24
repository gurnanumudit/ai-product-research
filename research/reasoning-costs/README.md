# When is more reasoning worth it?

Offline analysis supplement for a study of analytical work beyond coding:
134 DSBench questions (29 easy, 55 medium, 50 hard), three models and three
reasoning settings. The article remains an unpublished review draft; this
release publishes its numerical analysis materials, not the website.

## Reproduce the numbers

Python 3.10 or later, no dependencies, credentials, network access or model calls:

```sh
python3 research/reasoning-costs/reproduce.py
```

The script checks the exported records against frozen article results and writes
`output/analysis.json` and `output/results.md`. It reproduces all 27
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

The recommendation comparisons are illustrative, not a validated routing policy.
They use Luna low for easy/medium and Luna high for hard as lower-cost options,
compared with the most accurate setting (cheapest when tied). Cost per correct
answer alone instead favors Luna low in each band.
