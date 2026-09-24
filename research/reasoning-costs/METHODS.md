# Methods and interpretation

## Design and sample

The matched panel contains 134 selected DSBench data-analysis questions from
24 source contexts: 29 easy, 55 medium and 50 hard. Three recorded model routes
(`openai/gpt-5.6-luna`, `openai/gpt-5.6-terra`, `openai/gpt-5.6-sol`)
each used none, low and high reasoning on the same questions and tools.
These are the recorded route identifiers, not a claim of current API availability.

The historical cohort has 50 questions (10/10/30); the extension has 84 complete
questions (19/45/20). Five additional medium questions were excluded across
all nine settings because testing was incomplete: 19 cells never started and
26 completed. Coverage, not correctness, determined inclusion. Their derived
outcome records remain in the export; excluded-question costs are outside this
matched-cost release, not assumed zero.

Difficulty was assigned by the work required, not observed model accuracy.
Four dimensions—method judgment, dependent reasoning, data integration and
validation—were scored 0–3 each. Totals 0–2 were easy, 3–5 medium, 6–8 hard
and 9–12 very hard; there are no very-hard questions in the analysis.
This was a single-reviewer classification, not fully blind to prior task familiarity.
Individual rubric component scores are not included in this numerical supplement.

## Outcomes and retries

One selected result per question/configuration. Final answers were compared to
the frozen public reference using a deterministic option/numeric comparator.
Correct final deliveries score one; attempted wrong, invalid or missing answers
score zero. Never-started cells have null correctness in this release and are
outside the matched panel. The reference attachments were checked; all reference
answers were not independently rederived.

Six budget-interrupted extension runs received approved retries. Their fixed
retry outcomes were used regardless of success, never best-of-two selection.
Cost accounting includes both attempts. The outcome table is not a two-repeat
experiment. Runtime scheduling, concurrency and operational handling changed
during collection, including after interim review; comparisons are descriptive,
not randomized. The prompts, scoring and per-task limits stayed fixed across
the extension. This release does not reconstruct the original execution harness.

## Costs and recommended comparisons

All accuracy and dollar comparisons use the same 134 questions.
The 1,212 cost records comprise 450 historical attempts and 762 extension attempts.
Model-cost exposure = recorded model charges + pending reservations.
Runtime is an additional estimate, not included in the main model-cost plots.
These are historical recorded amounts, not settled invoices, a single current
tariff or the complete cost of deployment. No monetary value of errors was assigned.

Extra cost per 100 = 100 × (target total cost / question count − baseline total
cost / question count). Extra correct per 100 uses the difference in success
rates. Calculations use unrounded inputs. Normalizing to 100 creates neither
new observations nor a prediction of future performance.

The lower-cost choices are editorial trade-offs: Luna low on easy/medium and
Luna high on hard. The accuracy choices maximize observed correct answers,
breaking ties by model cost. These choices are not an optimized or externally
validated routing policy. The hard frontier contains nondominated configurations;
lines between them do not represent tested intermediate settings.

## Sensitivity and dependence

The primary outcome retains attempted operational failures. Removing whole
questions affected by provider/infrastructure/deadline failures leaves 97
questions. Restricting to ordinary completed answers at all settings leaves 92.
Neither check selectively removes just an unsuccessful configuration.

Equal-context averages give every source context the same weight. For hard
questions, Sol low and high both score 42/50: 38 correct at both settings,
four only at low, four only at high, four at neither. Equal totals do not mean
equivalence; changing context weights changes the comparison.

Use the study to shortlist settings and examine cost/accuracy trade-offs, then
test on fresh examples from your own workload. Purposeful sampling, shared
contexts, one selected result per setting, public-data training contamination
uncertainty and evolving execution conditions limit generalization.
