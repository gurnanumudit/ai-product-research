# The Test Passed. The Patch Was Still Wrong.

Public study materials for Mudit Gurnani's research note on whether one AI coding agent can safely
verify another agent's patch.

## The experiment

- **Tasks:** 35 recent software issues from [SWE-rebench](https://swe-rebench.com/about)
- **Patch generators:** GPT-5.4 Mini and GPT-5.4, two attempts per task
- **Independent verifier:** Claude Opus 4.6
- **Ground truth:** SWE-rebench's separate executable evaluation

The verifier inspected each issue, repository, and proposed patch without seeing the benchmark's
final evaluation. It returned one pass-or-no-approval verdict for each submitted patch.

## Headline finding

The generators submitted 82 patches. The verifier passed 38 of them. Only 15 of those 38 were
actually correct; 23 were still wrong.

| AI check | Actually correct | Actually wrong | Total |
| --- | ---: | ---: | ---: |
| Passed | 15 | 23 | 38 |
| No approval | 13 | 31 | 44 |
| Total | 28 | 54 | 82 |

The practical conclusion is deliberately narrow: this verifier's pass was useful evidence, but it
was not safe as an automatic release gate.

## What is included

- [`data/confirmatory-analysis.json`](data/confirmatory-analysis.json) — frozen aggregate analysis
- [`data/preregistration.json`](data/preregistration.json) — frozen study rules
- [`docs/methodology.md`](docs/methodology.md) — offline reproduction notes
- [`docs/results.md`](docs/results.md) — technical result brief
- [`figures/verification-confirmatory.png`](figures/verification-confirmatory.png) — final study figure
- [`reproduce.py`](reproduce.py) — zero-dependency check of the article's headline numbers

Run the public check with Python 3.11 or newer:

```bash
python3 research/agent-verification/reproduce.py
```

This public package contains processed results and analysis materials. It does not contain API
credentials, private runtime databases, cached repositories, raw provider traces, or unfinished
studies.
