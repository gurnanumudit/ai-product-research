# How AI negotiates

Published October 29, 2026. [Read the article](https://research.muditgurnani.chatgpt.site/research/how-ai-negotiates).

We tested four buyer strategies against three seller strategies across 180 synthetic scenarios: 2,160 assigned negotiations. The AI used one model configuration, `openai/gpt-6.1-sol` with medium reasoning. Two sellers and one buyer followed deterministic policies. Points measure gain above each side’s outside option, not dollars or a human judge’s rating.

## Reproduce the article’s numerical results

Python 3.10+ and NumPy 2.3.5 are required. The reference environment used Python 3.14.3. From the repository root:

```sh
python3 -m venv .venv-negotiation
.venv-negotiation/bin/python -m pip install -r research/negotiation/requirements.txt
.venv-negotiation/bin/python -B research/negotiation/reproduce.py
```

The verifier checks file hashes, all 2,160 derived outcomes, 180 contract menus, 12 matchup averages, five original contrasts, 17 subgroup reports, the 107-case distribution, and both post-hoc bootstrap analyses with all failure sensitivities. It recomputes the fixed 10,000-resample intervals, makes no network or model calls, and writes no results over frozen data. Do not use Python’s `-O` option, which disables assertions.

This reproduces calculations from saved outcomes. It does not rerun the model experiment, recover missing responses, independently validate provider billing, or measure repeated-run model variability. No API key is needed.

## Files

| File | Contents |
| --- | --- |
| `reproduce.py` | Portable offline numerical verifier |
| `code/game.py` | Unmodified frozen deterministic game, scoring and programmed policies |
| `code/analysis_math.py` | Unmodified numerical-helper prefix extracted from the original frozen analyzer |
| `data/episodes.json` | 2,160 derived episode records: assignments, contracts, scores and failure flags |
| `data/methods-and-scenarios.json` | Exact AI instruction text, interface rules, 180 synthetic scenario definitions and source hashes |
| `reference/article-results.json` | Frozen chart inputs, comparison intervals, subgroup results, paired outcomes, selected nine-turn transcript and accounting totals |
| `PROVENANCE.json` | Source segment hashes, extraction scope and omitted materials |
| `MANIFEST.json` | SHA-256 pins for this public package |

[Website presentation source](../../site/components/negotiation/) contains the interactive article and charts. The illustration is labeled AI-generated artwork; it is not experimental evidence.

## How to interpret the results

All combined results are permanently post-interim amended and exploratory. Collection proceeded across five immutable segments with prospectively amended error-handling rules. Complete assignment coverage is not successful operational feasibility: 14 cases ended in infrastructure failure. Their recorded zero scores are not observed walkaways or ties. Both unfavorable and favorable legal-outcome bounds remain in the analysis.

Firm instructions averaged almost the same buyer score as neutral instructions; collaborative instructions averaged 0.63 points more. The largest of the five original differences was 3.01 points, below the predefined five-point practical margin. This does not establish equivalence or a universal best strategy. Six descriptive subgroup comparisons reverse direction relative to their pooled result.

The role follow-up selected 107 scenarios with a mutually acceptable contract and equal separate attainable maxima. Equal maxima do not imply symmetric opportunities or equal winning probabilities. In the neutral-AI pairing, the buyer’s recorded lead was 1.78 points; balancing starting roles within scenario type gave 1.90 points, with a 95% exploratory interval from −0.04 to +3.85. The result motivates another test, rather than establishing a general buyer advantage. The 60 no-zone scenarios remain reported separately; technical failures are not imputed as known strategic behavior.

## Reproduction boundaries and license

These are original synthetic scenarios and derived research records. Repository code is covered by the root MIT license. Original model-service terms still govern use of that service; this package grants no access to it. The release excludes credentials, account state, provider identifiers, private operational logs, launch controls, and the full model-response archive. Only the article’s selected public transcript is included. Source hashes document lineage but do not substitute for the unreleased operational archive.

The numerical helpers include a historical threshold helper; the public verifier uses their arithmetic and resampling only. It does not call the original gated analysis entry point or use historical decision flags to make confirmatory declarations. API cost totals in the reference file are reported accounting summaries, not independently re-audited by this public verifier. Original five-comparison, role-gap and first-mover seeds are 20261025043, 2026102901 and 2026102902 respectively; scenario pairs and failure bounds are kept together in resampling.
