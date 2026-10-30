# Financial-answer review: calculation-warning sensitivity

This is the offline code and aggregate-results supplement for the article's revised verification rule. It preserves the [original article analysis](../article-analysis/README.md) unchanged.

## What changed

The original checker gave calculation discrepancies priority even when they were smaller than the allowance used to grade final answers. The follow-up changes only the arithmetic-warning threshold to **0.005 in displayed units**, or **0.00005 for a ratio**. A discrepancy exactly at the threshold is accepted. The checker compares the model's stated answer with its own calculation; it never reads FinQA's answer key.

Source-number checks, unused-input checks, unusable-response handling, confidence scores, the answer-key scoring rule, hash-based tie order and queue seed remain unchanged. This is one fixed modification, not a search across checker thresholds.

## Results

There are 1,127 saved responses: 765 answer-key matches, 347 numerical mismatches and 15 abstentions. Both methods share the same 35 mandatory-review responses, which consume slots within each budget.

| Review share | Slots | Confidence: mismatches caught | Original verification | Revised verification |
| --- | ---: | ---: | ---: | ---: |
| 5% | 56 | 31 | 19 | 35 |
| 10% | 112 | 59 | 42 | 88 |
| 20% | 225 | 103 | 95 | 143 |
| 50% | 563 | 204 | 204 | 211 |

At 20% review, revised verification has precision 143/225 (63.6%), recall 143/347 (41.2%), and answer-key agreement among unreviewed responses 698/902 (77.4%). Review does not automatically correct an answer.

The adjustment removes 213 arithmetic warnings, leaving 114. Of those removed warnings, 183 answers match the key and 30 do not. Small internal discrepancies are not proof that an answer is correct.

[`aggregate-results.json`](aggregate-results.json) includes the four-budget comparison, original-queue scoring sensitivity at allowances 0, .001, .005 and .01, unit counts, warning counts, and historical five-decimal comparison. There are no questions, report extracts, answer IDs, model responses or queue memberships in this public package.

## Interpretation

This is an **exploratory same-batch follow-up**. The modification was fixed before the follow-up outcomes, but it was motivated by examples already examined in the original results. Recomputing on the same saved answers is not fresh independent validation. These results describe one model/settings combination and one dataset. They do not establish universal verification superiority, financial materiality, human correction time or production safety.

The scoring allowance is unit-dependent, not one financial-materiality threshold. The scoring adapter is final-answer agreement against FinQA's archived answer key, not official FinQA program-execution accuracy. Exact rational equality and the historical five-decimal criterion are different analyses.

## Run public tests

Python 3.11 or newer, standard library only. From this directory:

```sh
python3 -m unittest -v test_analyze
```

Fixtures are synthetic; tests make no model calls or network requests. The adjacent article-analysis and v2 implementation must remain in their repository layout. This supplement imports only the archived checker, schema, numbers and policy code, not the paid runner.

## Replay with the private historical archive

The empirical results cannot be fully reproduced from this public repository alone. The exact 1,127 saved responses, extracted inputs and reference annotations are not redistributed. FinQA alone does not reproduce historical model responses. Supply the same locally held, appropriately authorized archive described in the [original supplement](../article-analysis/README.md#replay-the-archived-study):

```text
local-archive/
  data/test-v1/inputs.json
  data/test-v1/annotations.json
  runs/test-01/*-response.json
```

```sh
python3 analyze.py --archive ./local-archive --out ./new-replay
```

The command checks the original frozen input, implementation and response-collection hashes, reproduces the historical public aggregates, recomputes this follow-up, and requires exact agreement with the published aggregate object. It rechecks input hashes before writing. A missing or altered archive stops rather than substituting data.

The output directory must be fresh, outside the archive, and non-symlinked. Only aggregate results and a hash receipt are written; private answer-level diagnostics are never exported. No input acquisition, API keys, paid execution or modification of the archive occurs.

## Provenance and reproduction limits

[`provenance.json`](provenance.json) identifies the accepted generating script, tests, plan and result by SHA-256. The public analyzer is a portable adaptation with the same scoring, threshold, warning and queue algorithms; its archive replay gate uses published aggregates rather than private historical row-level audit files.

The original local result was independently reconstructed against all 1,127 saved responses, 24 original/revised queues and 48 scoring-grid policy cells before this publication package. This packaging step passed 14 follow-up synthetic tests, 19 original-supplement tests, and an exact archived-input replay against both public aggregate files. This is author-side release verification, not new model execution, fresh validation data or independent revalidation of every source citation.

Source passages, raw responses, private audits, row-level queues, local paths, credentials and approval records are excluded. No new empirical outcomes or external spend were incurred during packaging. Repository code is MIT licensed; FinQA and financial-report rights remain separate.
