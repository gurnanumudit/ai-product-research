# Which financial AI answers should we review?

This is the offline analysis supplement for the article. It compares **confidence** (review lower-confidence answers first) with **verification** (review calculation warnings first, then citation warnings, then unused-input warnings), at the same review capacity. A fixed-seed random queue provides a descriptive baseline.

The earlier [version 2 package](../v2/README.md) is preserved. Its original source-judgment evaluation is **not** the scoring used for this article. This supplement evaluates the saved model answers against FinQA's original numerical answer key, with the numerical allowance below. The comparison and four-budget analysis were performed **after the original study**, not preregistered as its primary outcome.

## Results and what can be reproduced

[`aggregate-results.json`](aggregate-results.json) contains only aggregate counts and metric fractions—no questions, report extracts, model responses or row-level judgments. For 1,127 saved responses, 765 matched the key, 347 were numerical mismatches, and 15 were abstentions. The common mandatory-review rule uses 35 slots, including the 15 abstentions; these are included in, not added to, each budget.

| Review share | Slots | Confidence: mismatches caught | Verification: mismatches caught |
| --- | ---: | ---: | ---: |
| 5% | 56 | 31 | 19 |
| 10% | 112 | 59 | 42 |
| 20% | 225 | 103 | 95 |
| 50% | 563 | 204 | 204 |

**Publicly runnable:** the synthetic tests and inspection of the algorithms and aggregate results. **Not fully reproducible from the public repository alone:** the empirical study needs the exact archived inputs, original-reference annotations and 1,127 saved model responses, which are not distributed here. FinQA's public dataset alone does not recreate the model's historical responses. The archive has been replayed locally and checked against the frozen labels, all 12 ordered review/released queues and every published aggregate metric. This is an author-side replay, not independent public data reproduction.

## Run the offline tests

Python 3.11 or newer; standard library only. From this directory:

```sh
python3 -m unittest -v test_analyze
```

The fixtures are synthetic. No API key, network call, download, paid execution or installation is used. Tests cover arithmetic allowance boundaries, percentage adaptation, abstentions, malformed input, equal-budget partitions, nested queues, independence of selection from answer-key labels and safe output handling.

## Replay the archived study

Supply an existing local archive in this layout:

```text
local-archive/
  data/test-v1/inputs.json
  data/test-v1/annotations.json
  runs/test-01/*-response.json
```

`inputs.json` is a list of `{id, question, locations}` records. `annotations.json` has a `records` list; each record needs an `id` and `original_reference` containing numeric `exe_ans` and string `program`. Other historical annotation fields are ignored. Each saved response file has `{id, response}`; `response` contains exactly one completed, non-refused assistant choice in the historical Chat Completions envelope. Its content follows the preserved [response schema](../v2/implementation/package/schema.py).

```sh
python3 analyze.py --archive ./local-archive --out ./new-replay
```

The output directory must not exist, must not be symlinked and must be outside the supplied archive. The command verifies the exact historical input and response-collection checksums before analysis. It rejects missing, changed or incomplete archives rather than silently substituting data. It recomputes the checker from the saved input and answer, then calls the unchanged version 2 queue implementation. It writes only `aggregate-results.json` and a provenance receipt into the fresh destination. It does not regenerate answers or change the input archive.

[`provenance.json`](provenance.json) records the original input digests, implementation digests and historical script/result identities. The response-collection digest is SHA-256 of a JSON object mapping each response filename to its SHA-256, with sorted keys, compact separators and one trailing newline. Hashes establish artifact identity, not permission, answer-key correctness or independent access.

## Exact scoring and selection

- The answer key is the archived FinQA `exe_ans`. This is **adapted final-answer agreement**, not FinQA's official program-execution accuracy: the AI returns a final answer and a restricted derivation, not a FinQA reasoning program.
- Percentage answers are divided by 100 unless the reference program's final operation explicitly multiplies by `100` or `const_100`. That rule uses program structure, not whichever conversion would produce a match. Ratios use an absolute allowance of `0.00005`; a divided percentage therefore gets an allowance equivalent to `0.005` percentage points. Other answers, including explicit percentage-point answers, use `0.005` in displayed units. Other unit/scale disagreements are not repaired. Comparisons are inclusive at the boundary and use rational arithmetic.
- A null answer is an abstention, not a numerical mismatch. Every policy first includes all unusable checker responses; these consume review slots. Confidence ranks usable answers by increasing reported confidence. Verification ranks calculation, evidence and unused-input warning flags in that priority order. Both retain the historical hash-based tie ordering and `finqa-v2-primary-20261012` seed. The answer key never enters the queue selection.
- Budgets are `floor(N/20)`, `floor(N/10)`, `floor(N/5)` and `floor(N/2)`. More mandatory cases than slots makes a budget infeasible and stops this analysis. No favorable tie seed or subset is selected.
- **Review precision** is numerical mismatches selected / all review slots. **Recall** is numerical mismatches selected / all numerical mismatches. **Released accuracy** is answer-key matches / responses outside review. Abstentions consume slots but are not counted as numerical mismatches; the alternative numeric-answer-only precision is also provided explicitly.

## Important limitations

The article's comparison allows small numerical differences. That choice changes the ranking: at 20% review under a stricter five-decimal comparison, verification catches 177 numerical mismatches and confidence catches 113; with the article allowance, the figures are 95 and 103. The aggregate file retains this sensitivity. The practical-precision interpretation must not be presented as a scoring-independent or universal confidence win.

The original checker flags calculation differences greater than `0.00001` in displayed units, much tighter than the article's scoring allowance for many percentage answers. It verifies arithmetic and source-number presence, not whether the correct company, period or financial measure was chosen. An inconsistency can therefore trigger a warning without counting as an answer-key mismatch. A fixed queue difference is not proof that changing a single warning threshold would reverse the result; such an improved policy remains untested.

Results are descriptive for one saved response per question from one model/settings combination. The key can be imperfect; numerical disagreement does not measure financial harm. No human correction time, corrected-answer quality, production savings or statistically general advantage is established. Questions from the same company or report can be correlated. The single random queue is not an expectation over random rankings. Review does not automatically correct an answer.

`analyze.py` is a portable, safety-adapted combination of two historical offline analyses, with a fresh checker replay; it is not byte-identical to their original executables. It reuses unchanged schema/checker/policy code in `v2`. The full v2 runner exists for historical transparency but is not imported or executed by this supplement. No approvals, credentials, source passages or response payloads are included here. Code is covered by the repository's [MIT license](../../../LICENSE); FinQA and financial-report rights remain separate.
