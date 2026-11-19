# Methods and frozen protocol

## Population and endpoint

The evaluation bank contains 200 families: 100 TACO-derived coding tasks labeled VERY_HARD, 50 authored graph-coloring tasks and 50 authored Sokoban tasks. Each has A, S and R endpoints. All 600 are resolved; invalid or truncated endpoints count as failures. Missing validity metadata does not mean a missing grade. There is no outcome-dependent exclusion, refill, prompt selection, best-of-S/R choice or calibration-headroom gate for the workflow claim.

Coding selection used source-only qualification and finite family/exposure exclusions. The selected bank comprises 95 older-cohort tasks and five recent reserves, spanning 55 TRAIN and 45 TEST tasks, with 14,802 stored cases. Planning pooled eligible unused records with a complete fixed 20,000-slot generation schedule; 84 selected tasks were newly generated and 16 were saved eligible tasks. These selection statements are archived provenance, not reverified from raw benchmark data by this release.

## Exact prompt construction and settings

`protocol/PROMPTS.json` is copied byte for byte from the prompt artifact frozen by the study. Its embedded draft status describes the older file's creation, not whether the study later fixed its bytes. Mathematics fields are retained to preserve the hash but were not used in this coding/planning study. No development prompt search was run for this experiment.

The historical route was `openai/gpt-6-luna`, reasoning effort `medium`, with `max_output_tokens: 16384`, including reasoning output. These are archived settings, not a claim about a currently available model or current prices. The frozen semantic request assembly explicitly supplies the model, input messages, reasoning effort and output cap; it sets no temperature or top-p parameter. This package does not reconstruct gateway defaults or the complete transport environment.

Let `T` denote the exact original task text including its unchanged format contract. Task text is not redistributed. The following expressions specify concatenation, including the two newline characters:

```text
A.input = [
  {role: "system", content: PROMPTS.shared_system},
  {role: "user", content: PROMPTS.baseline_instruction + "\n\n" + T}
]
S.input = [
  {role: "system", content: PROMPTS.shared_system},
  {role: "user", content: PROMPTS.structured_checklists[domain] + "\n\n" + T}
]
R.input = S.input + [
  {role: "assistant", content: EXACT_SAVED_VISIBLE_S},
  {role: "user", content: PROMPTS.revision_instruction}
]
```

R is always requested, even after an empty or malformed S. It receives no correctness feedback, hidden tests, expected answers, witnesses or references. S is generated once and is not told about the future revision. All 600 answers were frozen before grading. The original scheduling order was bank order, with A/S/R consecutive for each task, not randomized service-time allocation. Release-local IDs preserve bootstrap order but do not encode collection order or original task identities.

The owner-authorized continuation adopted 279 saved answers, replaced one ambiguous original A request using the same wire body, and completed 320 untouched slots. Lookup remained incomplete and recovery was not exhausted. Original remote completion and charge remain unknown. This amendment changes operational completion and accounting, not the four contrasts, bank or outcome denominator. It is not original no-retry completion.

## Four comparisons

The primary family consists of coding S−A, coding R−S, planning S−A and planning R−S. For each, gains are fail→pass and regressions are pass→fail. The net change is `(gains - regressions)/100`. Both-pass and both-fail counts are retained.

With `n = gains + regressions` and `m = min(gains, regressions)`, the two-sided exact paired McNemar p-value is `min(1, 2 * sum(comb(n,k), k=0..m) / 2**n)`. If n is zero, p is one. Integer arithmetic and exact rational fractions are retained. Holm correction covers all four tests, in increasing exact p order; ties use the frozen primary-comparison order. A formal improvement requires adjusted p ≤ 0.05 and a positive change. R−A is not one of the confirmatory comparisons.

## Paired bootstrap

Use 20,000 draws and `random.Random(20261111)` in Python 3.14.3. Each replicate samples 100 coding families with replacement, then 50 graph-coloring families, then 50 Sokoban families. Keep all A/S/R endpoints together, using the same family draws for both contrasts. Planning retains its fixed 50:50 composition. Within each stratum the original engine sorts canonical family IDs; the public IDs retain precisely that ordering.

For every sampled index, append its unsigned four-byte big-endian representation to a running SHA256. The expected stream digest is `28922f32c580f3627f13c1864c15311c8615a291063704246f38a6f9ae02cc24`. This checks the random index stream, not just the final interval endpoints. Percentiles use linear interpolation at position `(N-1)*p` (type 7), at p=0.025 and 0.975. Intervals are pointwise, not simultaneous; independence across families and bootstrap approximation remain assumptions.

## Costs, tokens and durations

Charges are integer nano-USD; divide by 1,000,000,000 for USD. Current usable rows have settled charges. Add the original unresolved physical-only row to obtain current campaign accounting; its cost, full durations and usage are null. It has no scientific grade. Recorded reserve is not charge. Earlier totals are separate frozen aggregates and are added once, not represented as additional scientific observations.

Standalone A uses A; standalone S uses S; standalone R uses S+R. Costs, tokens and request durations add constituent calls, propagating missing values. Grading duration for standalone R is R's final grading duration, not S+R grading. Overlapping standalone totals must not be summed as campaign spending. Full operational A cost is unknown because of the extra original attempt.

Output includes reasoning tokens; cached/cache-write counts are input subsets. Detail columns are not added again to total usage. `known_sum` sums measured values only, `missing` counts nulls, and `complete_sum` is null if any component is missing. Request-duration sums are not pure inference time, wall time or time to a correct answer. Generation and whole-campaign wall times are unknown; guarded grading wall time is 11,044,133 ms. The original observed transport segment is diagnostic and is never substituted for a full request duration.

## What numerical reproduction establishes

The public engine extracts unchanged pure functions from the frozen computation core; the new wrapper validates the smaller public schema and recomputes derived statistics. Agreement establishes numerical consistency with the released outcomes, not independent correctness of grading, model execution, receipts or source qualification. A separate historical source-study audit is hash-committed in provenance; it is not a substitute for independent review of this public export.
