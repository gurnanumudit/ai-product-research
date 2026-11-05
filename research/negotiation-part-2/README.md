# How AI negotiates, Part 2

Published November 4, 2026. [Read the article](https://research.muditgurnani.chatgpt.site/research/how-ai-negotiates-part-2).

Does the buyer’s apparent advantage survive when the economic opportunities change sides? We tested neutral AI on both sides of 80 fresh scenario families. Each family has an original economy and its exact mirror, both starting roles, and three repetitions: 960 assigned negotiations. The model was `openai/gpt-6.1-sol`, medium reasoning.

## Reproduce the numbers

Python 3.10+ and NumPy 2.3.5 are required. From the repository root:

```sh
python3 -m venv .venv-negotiation-part2
.venv-negotiation-part2/bin/python -m pip install -r research/negotiation-part-2/requirements.txt
.venv-negotiation-part2/bin/python -B research/negotiation-part-2/reproduce.py
```

Verified with Python 3.14.3 / NumPy 2.3.5 and Python 3.11.15 / NumPy 2.4.6.

The verifier makes no network or model calls and writes no files. It checks the package hashes, all scenario mirrors and legal contract gains, all 960 assignments, scores from saved executed contract IDs, primary missing-outcome bounds, descriptive results, four exploratory confidence intervals and all six outcome distributions. Do not use Python’s `-O` option: assertions are part of verification.

This reproduces calculations from released synthetic scenarios and derived saved outcomes. It does not rerun the agents, validate every conversation/action against the private execution archive, recover missing outcomes, or independently audit provider billing. No API key is needed.

## Files

| File | Purpose |
| --- | --- |
| `code/game.py` | Unmodified deterministic engine used by the study; scoring, legal contracts and game rules |
| `code/mirror.py` | Exact mirror function extracted from frozen preparation code |
| `code/analysis_contract.py` | Unmodified frozen family-level primary analysis and legal missing-outcome bounds |
| `code/subgroup_uncertainty.py` | Exact reviewed whole-family bootstrap helper extracted from the exploratory analysis |
| `reproduce.py` | Portable public verifier joining the exported inputs and checking saved results |
| `data/scenarios.json` | 160 synthetic original/mirrored economies |
| `data/schedule.json` | All 960 assignments in original order |
| `data/outcomes.json` | All assignments, saved gains, executed contract IDs, legal gap bounds and explicit unknown outcomes |
| `data/methods.json` | Model configuration, seeds and exact system prompt components |
| `reference/` | Frozen primary, secondary, uncertainty and distribution targets |
| `PROVENANCE.json`, `MANIFEST.json` | Source lineage, extraction boundaries and public package hashes |

[Article presentation code](../../site/components/negotiation-part2/) contains the interactive charts. Historical metadata in `reference/chart-data.json` still says “unpublished preview”; the file is retained byte-for-byte as the article’s chart input, not as the current publication status.

## What is mirrored?

A possible contract’s price `p` becomes `260 - p`, and its three binary package terms are complemented. The private values, costs and outside options are transformed so each corresponding contract exchanges the two sides’ gains exactly. The verifier checks every contract in every family. This reverses available opportunities; it does not force the agents to choose mirrored deals.

The base engine retains its original generation-distribution constant. The Part 2 interface supplies the amended mirrored public prior shown in `data/methods.json`; that is the prompt used for this follow-up.

## Interpretation and limitations

There are 951 completed negotiations and nine failed outcomes that remain unknown. Missing outcomes are never replaced with zero. The frozen feasible-family primary point estimate and ordinary confidence interval remain suppressed. Sample legal bounds run from approximately −2.24 to +1.00 buyer-minus-seller points; the approximate population bound interval spans −3.69 to +2.42. Neither a general buyer advantage nor equality is established.

The four subgroup intervals are a separate, post-hoc exploratory analysis requested after results were observed. They use 20,000 whole-family percentile bootstrap draws with PCG64 seed 2026110401, sharing draws across starters within each category. They describe completed-outcome means, exclude unknown outcomes and are pointwise rather than simultaneous. They do not directly test the effect of changing who starts. Individual spread is shown separately; earning less than the other party does not mean losing value relative to walking away.

Collection was interrupted after 250 completed and five failed assignments. The owner requested continuation after seeing partial outcomes and restoring connectivity. Only the 705 untouched original assignments continued, yielding 701 completed and four failed outcomes. The public-prior amendment and outage/sleep-guard changes are disclosed in the [article’s continuation appendix](https://research.muditgurnani.chatgpt.site/research/how-ai-negotiates-part-2#continuation). The offline package does not authorize or implement another collection run.

The main practical takeaway: **Before deciding an AI is better at one role, test it on both sides of the opportunity and with both starting roles.**

## Release boundaries

This package includes original synthetic scenarios and derived research records under the repository’s MIT license. It excludes credentials, provider identities and receipts, full model transcripts, operational logs and launch controls. Original model-service terms still govern that service. Source hashes identify the frozen inputs but are not substitutes for the private execution archive. The original scenario generator’s earlier-sample exclusion archive is not included; the realized scenario set and fixed schedule are included in full.
