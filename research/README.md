# Research behind the articles

Each published article has a self-contained study folder. Start with its README for the research question, setup, findings, limitations and reproduction command.

| Published article | Study package | What you can verify offline |
| --- | --- | --- |
| [Which financial AI answers should we review?](https://research.muditgurnani.chatgpt.site/research/which-financial-ai-answers-should-we-review) | [financial-answer-review/article-analysis](financial-answer-review/article-analysis/README.md) | Synthetic tests and aggregate results; empirical replay needs unreleased historical inputs and model responses |
| [How to avoid false confidence in AI evaluations](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations) | [evaluation-reliability](evaluation-reliability/README.md) | Known-truth simulation, saved decisions, analysis and article tables; optional full simulation replay |
| [When is more reasoning worth it?](https://research.muditgurnani.chatgpt.site/research/when-is-more-reasoning-worth-it) | [reasoning-costs](reasoning-costs/README.md) | Accuracy and cost comparisons from derived question-level outcomes and recorded costs |
| [How AI reviewers use test evidence](https://research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence) | [ai-reviewers-test-evidence](ai-reviewers-test-evidence/README.md) | Numerical comparisons and figures from exported reviewer decisions and benchmark labels |

## Reading a study

1. **Understand the setup:** the README explains what was tested and what the findings can support.
2. **Inspect the methods:** `METHODS.md`, or the simulation's `study/PROTOCOL.md`, defines outcomes, comparisons and assumptions.
3. **Inspect the evidence:** `data/` contains the released records; `reference/` or `results/` holds frozen comparison targets and results.
4. **Check the numbers:** run the study's `reproduce.py` using its documented environment. No model calls or API keys are needed.
5. **Check the boundaries:** `PROVENANCE.md` explains sources, attribution, omitted material and what the public release cannot reproduce.

The reviewer and reasoning studies release derived records, not the full original model-execution environment. The financial-answer study releases code and aggregates, not the historical response archive; its README documents the additional replay inputs. Numerical agreement does not independently validate raw answers, benchmark labels or production impact. The simulation tests specified assumptions, not real AI assistants.

## Historical work

[archive/](archive/README.md) preserves a separate exploratory study. It is not used by the current articles and should not be combined with their samples or findings.

Website presentation code lives in [site/](../site/README.md). Return to the [repository overview](../README.md) for correction, citation and license guidance.
