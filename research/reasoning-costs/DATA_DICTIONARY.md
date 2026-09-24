# Data dictionary

UTF-8 JSON Lines, one JSON object per line. Currency is USD. No raw questions,
answers, credentials or private execution identifiers are included.

## results.jsonl

- `cell_id`: study identifier for one assigned question/model/reasoning cell.
- `question_id`: public DSBench question identifier.
- `source_context`: shared source/workbook context identifier.
- `difficulty`: easy, medium or hard, assigned by the study.
- `model`: recorded provider/model route.
- `reasoning`: none, low or high.
- `cohort`: historical50 or extension84. The latter label describes the
  retained cohort; five excluded questions also belong to the extension.
- `included`: whether all nine configurations for this question completed
  evaluation and the question enters the matched panel.
- `terminal_class`: ordinary_answer, provider_failure, infrastructure_failure,
  model_limit, fallback_failed or other preserved terminal category; not_started
  denotes an unevaluated cell.
- `correct`: 1 for a correct selected final answer, 0 for an attempted
  unsuccessful delivery, null for an unevaluated/open cell. A zero in a failed
  attempted cell is not necessarily a substantive wrong answer.

Do not average all 1,251 rows as the primary result: first select `included=true`.
Group by question identity when comparing configurations.

## costs.jsonl

- `physical_id`: unique physical-attempt study identifier.
- `cell_id`: join to the outcome table; six cells have two physical rows.
- `selected_for_outcome`: whether this attempt supplied the canonical outcome.
  Include both true and false rows when summing matched costs.
- `model_charges_usd`: recorded model charges.
- `pending_usd`: unresolved model reservations, not confirmed billed charges.
- `runtime_estimate_usd`: separate estimated sandbox exposure.

There is exactly one selected physical record for each of the 1,206 included
cells. Cost records contain only retained questions. Unknown costs must never
be converted to zero; exported retained-question amounts are all known numbers.
