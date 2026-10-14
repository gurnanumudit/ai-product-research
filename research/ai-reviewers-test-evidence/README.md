# How AI reviewers use test evidence

[Read the published article](https://research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence) · [All studies](../README.md)

**Question:** How does showing a test report—and changing its stated source—affect an AI reviewer's decision to approve a proposed software fix?

We gave three reviewers one selected patch for each of 60 SWE-bench Verified tasks under five evidence conditions. This package reproduces the published numerical tables and three charts from derived decision records. It does **not** rerun the model experiment or independently establish patch correctness.

## Study at a glance

- **Reviewers:** recorded routes `openai/gpt-5.6-terra`, `anthropic/claude-sonnet-5` and `google/gemini-3.8-flash`, each reviewing in a separate session without tools or code execution. These identify the study configurations, not current API availability. Phase differences are in [Methods](METHODS.md).
- **Conditions:** A: issue and patch only; B: add a diagnostic summary; C: add a full report without a stated source; D: attribute that report to the patch-producing system; E: attribute the identical report to a separate evaluator.
- **Outcomes:** APPROVE, HOLD or ABSTAIN, compared with benchmark labels and with the same reviewer's decisions under other conditions. HOLD is not a claim that a patch is wrong.
- **Design:** two disjoint task batches (20 and 40), with two planned reviews per task, reviewer and condition. Source labels were hypothetical assignments; the reports were not new independent tests.

Test reports reduced faulty approvals on matched tasks. Changing the report's stated source did not produce a consistent follow-up increase in approval. These results describe the selected tasks and conditions, not a general ranking of reviewers.

## Reproduce

Requires Python 3.10 or later; standard library only. No installation, account, API key, model call or network access is needed.

```sh
python3 research/ai-reviewers-test-evidence/reproduce.py
```

Run the command from the repository root. It checks the observations, recomputes the raw and matched results, compares them with the frozen published numbers (floating-point tolerance 1e-12), and writes JSON results plus three SVG charts to `research/ai-reviewers-test-evidence/output/` (ignored by Git). SVG fonts may vary by viewer; this does not change the numerical values.

## Coverage

| Phase | Tasks | Planned | Attempted | Usable | Invalid | Unattempted |
|---|---:|---:|---:|---:|---:|---:|
| Initial main batch | 20 | 600 | 600 | 563 | 37 | 0 |
| Follow-up | 40 | 1,200 | 1,136 | 1,129 | 7 | 64 |
| Total | 60 | 1,800 | 1,736 | 1,692 | 44 | 64 |

The separate development pilot is excluded. Usable decisions total 568 APPROVE, 1,114 HOLD and 10 ABSTAIN. Missing responses are never scored as incorrect.

## Contents

- [data/reviews.json](data/reviews.json): all 1,736 attempted cells, including 44 invalid flags, and 60 benchmark labels with public source URLs and content hashes. The 64 unattempted cells are the absent members of the complete task × model × five conditions × two repeats grid.
- [analysis/supplementary.py](analysis/supplementary.py): raw rates; common-task model comparisons; within-model scenario comparisons; conservative task-level intervals; seeded paired bootstrap and missingness bounds.
- [reproduce.py](reproduce.py): validation, original E−D source-label contrast and full numerical comparison.
- [analysis/render_figures.py](analysis/render_figures.py): portable SVG renderings using the original chart coordinates.
- [reference/](reference/): frozen published numerical targets, kept separate from the observations.
- [figures/](figures/): checked-in versions of the three reproduced charts. Fresh runs write charts and verification results to the Git-ignored `output/` folder.
- [data/archive-audit.json](data/archive-audit.json): aggregate receipt of direct checks against the preserved private research archive.
- [METHODS.md](METHODS.md) and [PROVENANCE.md](PROVENANCE.md): definitions, attribution, omissions and release limitations.

## Read the results correctly

The all-usable overview has varying denominators. Matched comparisons require both repeats on the relevant common task set; they must not be substituted for the overview. The original E−D contrast is phase-specific; its three-model mean uses common complete tasks, not every usable review. The benchmark-label comparisons were added after collection.

Reports B–E came from the evaluation that also supplied the benchmark labels. These results concern evidence interpretation, not independent testing. Repeated reviews are clustered within tasks. Selected tasks and complete-case subsets do not establish population-level model rankings.

Original analysis code and documentation use the repository's MIT license. The numerical data retain upstream attribution and do not relicense third-party source materials. See [PROVENANCE.md](PROVENANCE.md) for release scope and the limits of numerical-only reproduction.
