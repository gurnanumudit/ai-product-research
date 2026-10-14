# How to avoid false confidence in AI evaluations

Code and evidence for the article: [How to avoid false confidence in AI evaluations](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations) by Mudit Gurnani.

This study simulates paired correct/incorrect outcomes with a known performance difference. It tests how six approaches to analyzing the same evidence respond to related questions, repeated checking, missing grades and duplicated successes. It does not benchmark actual AI models or estimate how common these problems are in production.

## Reproduce the published results

From this directory:

```sh
python3 -B reproduce.py
```

This verifies package hashes, runs 32 deterministic tests, checks the first two frozen cohorts in every scenario with a separate implementation, recomputes the saved analysis, audits all 30,000 cohort records, and checks all 90 article-table rows. It writes only to a fresh temporary directory and prints its location; published evidence is never overwritten. No API calls or credentials are needed.

To additionally replay the complete simulation using the original seeds:

```sh
python3 -B reproduce.py --rerun
```

The original full simulation pass took about 5.5 minutes and produced about 39 MB of compressed evidence. Runtime varies by computer. Each run enforces the original 20-minute, 1 GiB resident-memory and 2 GiB output limits; failures preserve partial output. A replay is a reproducibility check, not a new independent sample.

**Environment:** Python standard library only; no package installation. The original run used Python 3.14.3 on macOS. The simulation imports Unix `resource`, so use macOS, Linux or WSL. Do not use Python `-O`, which disables assertions used by the frozen checks. Other Python versions are not certified for exact numerical reproduction.

## Study at a glance

- **Known gains:** −4, +2 and +10 percentage points for B relative to A.
- **Data conditions:** independent paired differences, related paired differences, randomly missing B grades, selectively missing B grades, and duplicated B successes.
- **Size:** 15 combinations × 2,000 simulated tests; each test has 200 independent contexts with five paired questions each.
- **Decision hurdle:** B must improve success probability by strictly more than two points. Switch when the confidence interval is entirely above that hurdle; conclude it does not clear the hurdle when the interval is entirely below it; otherwise remain inconclusive.
- **Five-check schedule:** after 40, 80, 120, 160 and 200 contexts (200–1,000 intended paired questions).

| Article label | Code identifier | Evidence and checking rule |
|---|---|---|
| Approach 1 | `row_fixed` | Treat question-level paired differences as independent; one final check |
| Approach 2 | `row_peek` | Same calculation; five unadjusted checks |
| Approach 3 | `context_fixed` | Account for related questions; one final check |
| Approach 4 | `context_peek` | Account for related questions; five unadjusted checks |
| Approach 5 | `context_adjusted` | Account for related questions; five Bonferroni-adjusted checks |
| Approach 6 | `integrity_adjusted` | Approach 5 plus identical-record deduplication and withholding decisions on incomplete/invalid evidence |

The extra `forced_row_fixed` entry in full outputs is a separately labeled operational recoding, not a seventh approach. It converts Approach 1's inconclusive outcome into an operational hold.

## Folder guide

```text
evaluation-reliability/
├── README.md                  # Start here
├── reproduce.py               # One-command verification
├── PROVENANCE.md              # Publication history and evidence limits
├── PUBLICATION-MANIFEST.json  # Hashes of the current package
├── study/                    # Frozen code, tests, protocol and source hashes
├── data/run1/                # Recorded simulation outcomes and run metadata
└── results/                  # Analysis, readable tables and article values
```

The frozen code, tests and protocol stay together so their original paths and hashes remain valid. The article’s package and provenance links are unchanged.

## Files

- [PROTOCOL.md](study/PROTOCOL.md): unchanged pre-run scientific specification.
- [simulation.py](study/simulation.py): generator, observed-evidence interfaces, six decision approaches and bounded runner.
- [test_simulation.py](study/test_simulation.py), [test_review.py](study/test_review.py): 21 implementation tests and 11 independently written checks.
- [independent_reproduce.py](study/independent_reproduce.py): separate generator/interval checks for the prescribed first two cohorts per scenario.
- [data/run1/](data/run1/): synthetic truth/observation ledger, per-look decisions, counts, execution receipt and public manifest.
- [summarize.py](study/summarize.py), [audit_saved.py](study/audit_saved.py): analysis and independent saved-result audit.
- [analysis.json](results/analysis.json): all outcome rates, Monte Carlo intervals, paired contrasts and diagnostics.
- [ALL-RATES.md](results/ALL-RATES.md): readable complete result tables, generated by [render_tables.py](study/render_tables.py).
- [article-results.json](results/article-results.json): the 90 rounded result rows used in the article, verified against the full analysis.
- [PROVENANCE.md](PROVENANCE.md), [SOURCE-FREEZE.json](study/SOURCE-FREEZE.json), [PUBLICATION-MANIFEST.json](PUBLICATION-MANIFEST.json): provenance and integrity checks.

## How to interpret the results

The study demonstrates behavior under specified synthetic assumptions, not the frequency of real-world evaluation failures. The intervals used to make decisions are normal approximations. Wilson intervals in the result tables describe Monte Carlo precision, not uncertainty about real deployment outcomes. Accounting for repeated checks does not repair biased missing data. Approach 6's refusal to decide is not evidence that it selected the correct product.

There is no demonstrated overall winner: the preferred tradeoff depends on mistaken-switch costs, delayed benefits, testing costs and the real distribution of situations. At the true +2-point boundary, B does not exceed the stated switching hurdle; inconclusive results are expected, not proof of equivalence.

The independent audit recomputes all saved decisions/counts and the prescribed prefix intervals; it does not independently regenerate every raw cohort's interval. See the protocol for the precise validation scope. Original execution metadata and public redactions are distinguished in [PROVENANCE.md](PROVENANCE.md).
