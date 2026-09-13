# AI Product Research

Independent research by [Mudit Gurnani](https://www.linkedin.com/in/muditgurnani), exploring how AI works, where it falls short, and what makes it useful in everyday work.

[Read the website](https://mudit-gurnani-research.muditgurnani.chatgpt.site/)

## Current research

### How AI reviewers use test evidence

We gave three AI reviewers the same proposed software fixes under five evidence scenarios. Test reports reduced faulty approvals on matched tasks, while reviewers differed in which benchmark-passing fixes they accepted. Changing a report's stated source did not produce a consistent follow-up increase in approval.

[Read the article](https://mudit-gurnani-research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence) · [Study code, data and methods](research/ai-reviewers-test-evidence/README.md)

The study contains 60 tasks and 1,692 usable reviews. Its offline supplement reproduces the numerical results from saved classifications, not the original model experiment or independent software verification.

## Repository

| Folder | Contents |
| --- | --- |
| [site/](site/README.md) | Website source, article, and web assets |
| [research/ai-reviewers-test-evidence/](research/ai-reviewers-test-evidence/README.md) | Current study: methods, derived observations, analysis, and figures |
| [research/agent-verification/](research/agent-verification/README.md) | Preserved earlier exploratory study, separate from the current article |

Each new study gets its own folder. Private execution logs, credentials, cached repositories and unfinished experiments are not part of this repository. Earlier website versions remain recoverable in Git history.

## Reproduce the current results

Python 3.10 or later, no dependencies or model calls:

```sh
python3 research/ai-reviewers-test-evidence/reproduce.py
```

For website setup, see [site/README.md](site/README.md).

## License and attribution

Original software is covered by the existing [MIT license](LICENSE). Third-party materials retain their own rights and attribution; see the study's [provenance and release scope](research/ai-reviewers-test-evidence/PROVENANCE.md). Numerical reproduction is deliberately distinguished from end-to-end experimental reproduction.
