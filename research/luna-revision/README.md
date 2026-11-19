# When does asking AI to revise help?

Offline research code and derived results for the Luna A/S/R workflow comparison. Intended repository location: `research/luna-revision`. Article route: `/research/when-does-asking-ai-to-revise-help`. The article publication date is **Monday, November 16, 2026**; this package does not publish the article or assert that it is live.

One neutral revision increased coding success from **59/100 to 69/100**, fixing 10 answers with no regressions. The change was +10 percentage points, with a pointwise 95% bootstrap interval of +5 to +16 points and a Holm-adjusted exact paired p-value of 0.0078125. It was the only one of four planned comparisons meeting the formal improvement rule.

| Domain | A: simple prompt | S: structured checklist | R: one revision of S |
|---|---:|---:|---:|
| Coding | 60/100 | 59/100 | 69/100 |
| Planning | 60/100 | 66/100 | 74/100 |

| Comparison | Gains / regressions | Change | Pointwise 95% interval | Holm-adjusted p |
|---|---:|---:|---:|---:|
| Coding S−A | 10 / 11 | −1 pp | −10 to +8 pp | 1 |
| Coding R−S | 10 / 0 | +10 pp | +5 to +16 pp | 0.0078125 |
| Planning S−A | 21 / 15 | +6 pp | −6 to +18 pp | 0.8100644922815263 |
| Planning R−S | 18 / 10 | +8 pp | −2 to +18 pp | 0.5548000261187553 |

These are fixed-bank results for one configuration. They do not establish superiority to an equal-compute alternative, broad model ability, equivalence for nonsignificant comparisons, or a universally best workflow.

## Reproduce offline

From this directory, with Python 3.14.3 (the validated reference runtime):

```sh
python3 -E -s -S -B -m unittest -v test_reproduce.py
python3 -E -s -S -B reproduce.py
```

No dependencies, network, credentials, source programs, grading, or model requests are needed. Importing either module does no analysis. `--help` describes the interface. `--write` additionally creates `output/reproduced.json` and refuses to replace an existing result. Generated output is ignored by Git. Other Python versions are not certified here; exact bootstrap results and the draw-stream hash are checked on every run.

The second command verifies the release hashes, all 600 resolved endpoints, four paired tables, exact two-sided McNemar tests with Holm correction, and 20,000 family bootstrap draws. It also checks domain and diagnostic subtype counts, current-run cost/token/time tables, S+R standalone accounting, and arithmetic consistency with the saved historical aggregates. Statistics and integer counts must match exactly. Only floating-point sums of durations permit 0.000001 millisecond roundoff from summation order; nulls must match exactly.

## Inputs and verification boundary

- [data/outcomes.jsonl](data/outcomes.jsonl): 600 derived endpoint records, with 200 complete A/S/R triples, measured charges, usage and nullable durations.
- [data/original-unresolved-attempt.json](data/original-unresolved-attempt.json): one separate physical-only attempt with unknown charge and full duration. It is never scored as an extra endpoint.
- [reference/summary.json](reference/summary.json): exact JSON values of selected frozen aggregate fields, including historical totals and their missing values. This is a public projection, not the private canonical summary file.
- [reference/pairs.json](reference/pairs.json): the 200 paired outcome triples, with release-local family IDs.
- [protocol/PROMPTS.json](protocol/PROMPTS.json): byte-exact generic prompts used by the study; [protocol/STUDY.json](protocol/STUDY.json) and [METHODS.md](METHODS.md) explain settings, assembly and the continuation amendment.

The release lets readers recompute numerical conclusions from saved derived outcomes. It does **not** independently establish that those grades are correct, reproduce the original model responses, verify provider invoices, or reconstruct private custody. Questions, tests, references, model answers, receipts and live launchers are omitted. Historical totals are preserved and checked arithmetically, not regenerated from the 397 earlier receipt records.

## Cost and interruption disclosure

The 600 usable responses have recorded API charges of **$1.466287055** and 3,214,764 total tokens. The campaign also includes an original request whose completion and charge remain unknown, for **601 physical requests**. Its $0.591016800 reserve is not an actual charge.

An interrupted run preserved 279 answers. The owner then directed one same-body replacement before recovery lookup was complete, plus completion of 320 untouched slots. This is amended completion, not compliance with the original no-retry protocol. Replacement logical elapsed time is null; its physical duration is separately measured. The interruption adds time and provider variation to fixed A/S/R ordering.

Earlier history adds $2.302121250 in known charges and an $11.820336 reserve with unknown actual charge. Lifetime known API charges are $3.768408305 across 998 physical requests and 996 logical endpoints. The $10 infrastructure commitment is not spend; its invoice is unknown. Full API and all-in costs remain unknown. Standalone R costs S+R, while the actual experiment generated S only once: do not sum overlapping standalone rows as spend.

## Limitations and source rights

The bank has 100 coding families and 50 each of graph coloring and Sokoban. Public coding tasks may have appeared in training. Finite family/history exclusions do not prove uncontamination. Stored tests and planning certificates provide finite checks, not universal correctness. Model and domain choices followed calibration. There is one stochastic trajectory per family, fixed order, unequal workflow compute, limited precision and possible provider alias/time drift. Planning subtype results are diagnostic only; the intervals have no simultaneous coverage guarantee.

See [METHODS.md](METHODS.md), [DATA_DICTIONARY.md](DATA_DICTIONARY.md) and [PROVENANCE.md](PROVENANCE.md) for exact definitions, omissions and source commitments. Original software is MIT-licensed under [LICENSE](LICENSE). No license for benchmark questions, tests or third-party solutions is granted by this package.
