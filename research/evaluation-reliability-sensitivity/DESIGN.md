# Evaluation decision sensitivity checks

Specified October 17, 2026, after review of the published evaluation-reliability article. This is a separately authorized exploratory extension, not part of the original frozen protocol. Its purpose is to decide whether the article needs a bounded robustness update or a substantive follow-up. No publication or paid model runs are authorized by this analysis.

## Question

Do the article's practical conclusions change when the probability of missing results, the minimum worthwhile improvement, or the dependence between questions changes?

Keep the original six approaches and their approximate normal intervals. Use 2,000 simulated evaluations per setting, 200 independent contexts of five paired questions, and the original five decision opportunities. Preserve the original study folder without modification. Write all new code, run receipts and results in this sibling folder.

## Planned comparisons

### Missing grades

Use the original selectively missing scenario with true gain −4 points and seed 2709271809. Cross failure-grade loss probabilities 5%, 10%, 20%, 30%, 40% with success-grade loss probabilities 5%, 10%. Include a complete-record 0%/0% reference using this same seed. This gives eleven settings.

Reuse identical underlying outcomes and logging-loss uniform draws across settings. The 5%/5% and 10%/10% settings are random-missing controls. The 5%/10% setting reverses the direction of selection and must remain in the report. The 0%/0% reference is paired with this sweep; it is not a replay of the separately seeded original clean-data scenario.

For all approaches report correct switches, incorrect switches, correct evidence-holds, incorrect evidence-holds, inconclusive results and mean intended contexts consumed. Show pointwise 95% Wilson Monte Carlo intervals for outcome rates. Report final-look observed coverage and Approach 1's mean estimated advantage and bias relative to the true −4 points. Do not average estimates selected by early stopping and call that general estimation bias.

For Approach 1, describe where observed false-switch rates first exceed 10%, 25% and 50% along each fixed success-loss slice, if they do. Give the neighboring tested settings and their uncertainty; do not interpolate a precise break point or claim a universal safe missingness gap. Do not expand the grid after seeing the crossing. Highlight Approaches 1, 3 and 5 in the concise comparison; preserve results for all six.

### Minimum worthwhile improvement

Reuse saved ledgers for the three headline scenarios: grouped complete data with a true +2-point gain (w04), selective missingness with a true −4-point gain (w09), and grouped complete data with a true +10-point gain (w05). Re-evaluate at thresholds strictly greater than 1, 2 and 5 points. This gives nine settings without new underlying simulations.

Recompute decisions from all five eligible looks. The first conclusive crossing remains final; do not merely relabel the original terminal decision. Reclassify truth relative to each new threshold. A true +2-point gain is worthwhile at the 1-point threshold, at the boundary at 2 points, and below the 5-point threshold. Report the distance between true gain and threshold alongside outcomes. Keep the original economic illustration out of these extrapolations.

At the +2-point equality boundary, the archived classification treats an evidence-hold as the correct operational direction; it does not establish that the effect is strictly below the hurdle. Preserve that caveat in the extension's interpretation.

### Related questions

Use the original grouped-complete +2-point scenario and seed 2709271804 with h = 0.15, 0.30 and 0.45. This gives three settings. Keep the switching threshold at +2 points and the same uniforms across the three settings.

The parameter h controls covariance; it is not a correlation. Within-context correlation of paired differences is h² / (0.5 − delta²), approximately 4.5%, 18.0% and 40.5% here. All three settings satisfy the generator's probability constraints. These are not empirically estimated levels of relatedness in production evaluations.

## Verification and reporting

Before the full extension, reproduce the original saved results with its published verifier. Test the extension and review its implementation independently. Record the execution configuration and source/input hashes before running the full grid.

The original missingness setting, all three threshold-2 settings and h = 0.30 must reproduce their original decision counts exactly. Regenerated anchor ledgers must equal the frozen scientific records. The missingness anchor must recover 55.05% false switches for Approach 1, 11.65% for Approach 5 and 100% inconclusive for Approach 6; its mean estimated gain rounds to +7.34 points.

Results across settings share underlying draws and are not new independent samples. Use paired evaluation-level contrasts when reporting changes between paired settings. Monte Carlo intervals describe finite simulation precision, not production risk, and are pointwise rather than simultaneous. Report every planned setting, including null and reversed results. Do not select a universal winner from whichever scenario favors it.

Approach 6 checks completeness at each eligible prefix. Missing data often prevent it from deciding, but it can decide before later loss. Distinguish refusal from a correct conclusion and show its decision coverage.

Cap one execution pass at 20 minutes, 1 GiB resident memory and 1 GiB generated output. Preserve partial results and error receipts if a cap or validation fails; do not silently reduce the sample or omit cells. No network, model API calls or package installation are required for the analysis.

## Article decision after results

Recommend a concise article update if the checks mainly qualify the size of effects while preserving the practical advice. Recommend a follow-up if they introduce a distinct useful question or materially change the workflow recommendation. A contradiction requiring correction must be surfaced in the original article, not hidden in a follow-up. Make this recommendation only after reviewing the results; do not edit or publish the article during this analysis.
