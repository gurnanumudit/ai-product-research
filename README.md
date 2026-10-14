# AI Product Research

Independent research by [Mudit Gurnani](https://www.linkedin.com/in/muditgurnani), exploring how AI works, where it falls short, and what makes it useful in everyday work.

[Read the website](https://research.muditgurnani.chatgpt.site/)

## Published articles

Coming from an article? Its study folder is the starting point for the methods, evidence and reproduction instructions.

### How to avoid false confidence in AI evaluations

A higher evaluation score is not always a reason to switch. We used simulations to examine how related questions, repeated checks and missing outcomes affect that decision.

[Read the article](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations) · [Code, frozen results and reproduction](research/evaluation-reliability/README.md)

This is a known-truth simulation of established statistical methods, not a comparison of real AI models. The package includes 15 scenarios, 2,000 simulated evaluations per scenario, six approaches and offline verification.

### When is more reasoning worth it?

We compared three models at three reasoning settings on 134 analytical questions.
The [study code, derived results and methods](research/reasoning-costs/README.md)
reproduce the accuracy tables, cost comparisons and sensitivity checks offline.
Read the [published article](https://research.muditgurnani.chatgpt.site/research/when-is-more-reasoning-worth-it).

### How AI reviewers use test evidence

We gave three AI reviewers the same proposed software fixes under five evidence scenarios. Test reports reduced faulty approvals on matched tasks, while reviewers differed in which benchmark-passing fixes they accepted. Changing a report's stated source did not produce a consistent follow-up increase in approval.

[Read the article](https://research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence) · [Study code, data and methods](research/ai-reviewers-test-evidence/README.md)

The study contains 60 tasks and 1,692 usable reviews. Its offline supplement reproduces the numerical results from saved classifications, not the original model experiment or independent software verification.

## Repository

| Folder | Contents |
| --- | --- |
| [site/](site/README.md) | Website source, all three articles, and web assets |
| [research/evaluation-reliability/](research/evaluation-reliability/README.md) | Evaluation decision simulation: code, tests, frozen outcomes and reproducibility |
| [research/reasoning-costs/](research/reasoning-costs/README.md) | Analytical reasoning study: question-level outcomes, costs and offline reproduction |
| [research/ai-reviewers-test-evidence/](research/ai-reviewers-test-evidence/README.md) | Reviewer study: methods, derived observations, analysis, and figures |
| [research/archive/](research/archive/README.md) | Historical exploratory work — not evidence for the current published articles |

Each new study gets its own folder. Private execution logs, credentials, cached repositories and unfinished experiments are not part of this repository. Earlier website versions remain recoverable in Git history.

## Reproduce the published numbers

Clone the repository and run these commands from its root. All three use the Python standard library, with no model calls, API keys or paid services:

```sh
python3 research/ai-reviewers-test-evidence/reproduce.py
python3 research/reasoning-costs/reproduce.py
python3 -B research/evaluation-reliability/reproduce.py
```

The reviewer and reasoning packages require Python 3.10 or later. The evaluation-reliability package was run with Python 3.14.3 and requires macOS, Linux or WSL; see its [environment and verification notes](research/evaluation-reliability/README.md#reproduce-the-published-results). Do not run verification with Python's `-O` option, which disables assertions.

**What these commands establish:** the saved records reproduce the published numerical results. For the two model studies, they do not rerun the original models or independently regrade raw answers. The simulation package also verifies its implementation and offers a separate full replay. Each study documents what is included and what cannot be reproduced from the public release.

Generated output is kept separate from frozen evidence. Start with the [research index](research/README.md) for the file guide and reproduction boundaries of each study.

For website setup, see [site/README.md](site/README.md).

## Questions, corrections and reuse

Please [open an issue](https://github.com/gurnanumudit/ai-product-research/issues) with the article or study name, the claim or file in question, and any steps needed to reproduce the issue. Include your Python version and command output for a failed check; remove credentials and private information first.

When referencing this work, link to the relevant article and credit Mudit Gurnani. For a reproducible analysis, also record the repository commit you used. Corrections should preserve the original evidence and explain any change to published numbers; do not silently overwrite frozen results.

## License and attribution

Original software is covered by the [MIT license](LICENSE). Third-party materials retain their own rights and attribution. See the provenance notes for [evaluation reliability](research/evaluation-reliability/PROVENANCE.md), [reasoning costs](research/reasoning-costs/PROVENANCE.md), and [AI reviewers](research/ai-reviewers-test-evidence/PROVENANCE.md) before reusing study materials.
