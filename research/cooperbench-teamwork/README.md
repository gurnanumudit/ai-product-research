# When does an AI team beat one agent?

Research code and offline numerical reproduction for Mudit Gurnani's CooperBench teamwork comparison.

[Read the article](https://research.muditgurnani.com/research/when-does-an-ai-team-beat-one-agent) · [Published research website](https://research.muditgurnani.com/)

Published November 21, 2026. The source for the article is in [site/components/teamwork](../../site/components/teamwork/).

## What was tested

One agent, simple two-agent teamwork and structured two-agent teamwork received the same maximum **32 model calls per team**. The selected sample has **37 feature pairs, 24 underlying tasks and 11 repositories**. Three repetitions per pair and workflow gave **333 assignments**. There are **327 observed results and six permanently missing interrupted runs**.

| Workflow | Both features pass / observed | Features / team | Features / agent | Known API cost / observed success |
|---|---:|---:|---:|---:|
| Solo | 59 / 110 | 1.4182 | 1.4182 | $0.033651 |
| Simple team | 36 / 108 | 0.7593 | 0.3796 | $0.045710 |
| Structured team | 53 / 109 | 1.3303 | 0.6651 | $0.030551 |

These raw rates are descriptive. The primary comparison gives each underlying task equal weight after averaging pairs and repetitions. The selected-sample missing-outcome bounds preserve the ordering: solo, structured team, simple team. They are **not confidence intervals** and do not establish a population effect. This compares whole workflows, not isolated planning or general team scaling.

## Run offline

Python 3.10+ standard library; no installation, credentials, network, model calls, Docker or grading:

```sh
python3 -B research/cooperbench-teamwork/reproduce.py
cd research/cooperbench-teamwork
python3 -B -m unittest -v test_reproduce.py
```

The command verifies release hashes, the assignment/outcome/missing partition, exact cost conservation in nano-USD, all fields of the saved analysis, and independent rational-arithmetic success bounds. It writes no results and does not overwrite anything. `analysis.py` contains the reviewed pure analysis functions extracted verbatim from the original reporter; the launch/report entrypoint is excluded.

## Included

- `data/schedule.json`: all 333 assignments, in original order, including roles and integrators.
- `data/outcomes.json`: 327 derived score, cost, usage, phase and timing records.
- `data/missing-keys.json`: six missing outcomes, never imputed as observed failures.
- `data/interrupted-costs.json`: settled interrupted-call costs and the separate unknown reserve.
- `reference/analysis.json`: exact accepted aggregate output, used as a comparison target.
- `analysis.py`, `reproduce.py`, `test_reproduce.py`: analysis and offline checks.
- `source-excerpts/`: exact original prompt/phase and run-team function excerpts for inspection; not stand-alone launchers.
- `METHODS.md`, `DATA_DICTIONARY.md`, `PROVENANCE.md`: definitions and release boundaries.

This package reproduces numerical summaries from released derived outcomes. It does **not** independently verify the scores, rerun agents, execute hidden tests, reproduce private evidence custody or validate provider invoices. Source excerpts show the original workflow but do not constitute an end-to-end runnable benchmark harness.

Known study API charges total **$5.250162005**, including failed and interrupted settled calls. One same-study request remains unresolved, with a $0.05 reserve, not a known charge. Infrastructure, electricity, human time and Codex usage were unmetered. See the methods for allowance sensitivities and operational amendments.

Original software is MIT-licensed under [LICENSE](LICENSE). Benchmark code, tests, references, model responses and third-party solutions are not redistributed or relicensed here.
