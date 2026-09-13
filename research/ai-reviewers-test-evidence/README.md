# How AI reviewers use test evidence

Offline analysis supplement for the 60-task, three-reviewer study. This package reproduces the published numerical tables and three charts from derived decision records. It does **not** rerun the model experiment or independently establish patch correctness.

[Read the article](https://mudit-gurnani-research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence)

## Reproduce

Requires Python 3.10 or later; standard library only. No installation, account, API key, model call or network access is needed.

```sh
python3 reproduce.py
```

The command checks the observations, recomputes the raw and matched results, compares them with the frozen published numbers (floating-point tolerance 1e-12), and writes JSON results plus three SVG charts to `output/`. Run it from any working directory by giving the script's path. SVG fonts may vary by viewer; this does not change the numerical values.

| Phase | Tasks | Planned | Attempted | Usable | Invalid | Unattempted |
|---|---:|---:|---:|---:|---:|---:|
| Initial main batch | 20 | 600 | 600 | 563 | 37 | 0 |
| Follow-up | 40 | 1,200 | 1,136 | 1,129 | 7 | 64 |
| Total | 60 | 1,800 | 1,736 | 1,692 | 44 | 64 |

The separate development pilot is excluded. Usable decisions total 568 APPROVE, 1,114 HOLD and 10 ABSTAIN. Missing responses are never scored as incorrect.

## Contents

- `data/reviews.json`: all 1,736 attempted cells, including 44 invalid flags, and 60 benchmark labels with public source URLs and content hashes. The 64 unattempted cells are the absent members of the complete task × model × five conditions × two repeats grid.
- `analysis/supplementary.py`: raw rates; common-task model comparisons; within-model scenario comparisons; conservative task-level intervals; seeded paired bootstrap and missingness bounds.
- `reproduce.py`: validation, original E−D source-label contrast and full numerical comparison.
- `analysis/render_figures.py`: portable SVG renderings using the original chart coordinates.
- `reference/`: frozen published numerical targets, kept separate from the observations.
- `figures/`: checked-in versions of the three reproduced charts. Fresh runs write charts and verification results to the Git-ignored `output/` folder.
- `data/archive-audit.json`: aggregate receipt of direct checks against the preserved private research archive.
- `METHODS.md` and `PROVENANCE.md`: definitions, attribution, omissions and release limitations.

## Read the results correctly

The all-usable overview has varying denominators. Matched comparisons require both repeats on the relevant common task set; they must not be substituted for the overview. The original E−D contrast is phase-specific; its three-model mean uses common complete tasks, not every usable review. The benchmark-label comparisons were added after collection.

Reports B–E came from the evaluation that also supplied the benchmark labels. These results concern evidence interpretation, not independent testing. Repeated reviews are clustered within tasks. Selected tasks and complete-case subsets do not establish population-level model rankings.

Original analysis code and documentation use the repository's MIT license. The numerical data retain upstream attribution and do not relicense third-party source materials. See `PROVENANCE.md` for release scope and the limits of numerical-only reproduction.
