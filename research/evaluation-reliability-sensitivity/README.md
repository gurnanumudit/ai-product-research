# Sensitivity checks for AI evaluation decisions

Local research extension to [How to avoid false confidence in AI evaluations](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations), specified October 17, 2026. The original [study and published evidence](../evaluation-reliability/README.md) remain unchanged. This extension is for review before deciding whether to update the article or write a follow-up.

## What we are checking

- **Missing grades:** How does mistaken switching change when successful and unsuccessful answers have different probabilities of losing their grades?
- **Switching requirements:** What changes when the required improvement is greater than one or five points instead of two?
- **Related questions:** How sensitive are the results to stronger or weaker dependence between questions?

The [design](DESIGN.md) fixes eleven missingness settings, nine threshold settings and three relatedness settings, with 2,000 evaluations per setting. Settings share outcomes or random draws; 46,000 setting-level evaluations are not 46,000 independent new experiments. All six original approaches are retained, without method tuning or a new AI model experiment.

This is a post-publication exploratory extension, not a claim that these checks were part of the original preregistration. The configuration and code were frozen before executing the extension. No website update or public release is included in this work.

## What we found

**Recommendation: make a bounded update to the existing article.** These checks preserve its practical advice, but make clear that the reported error rates depend strongly on the assumptions. They do not establish a new method or a separate empirical finding about production AI systems.

### Selective missingness changes the size of the problem

B is truly four points worse in this comparison. With successful-grade loss fixed at 5%, the risk of an incorrect switch rises sharply as more failed grades disappear:

| Failed grades missing | Approach 1 incorrect switches | Approach 3 incorrect switches | Approach 5 incorrect switches |
| --- | --- | --- | --- |
| 20% | 1.65% [1.18, 2.31] | 0.45% [0.24, 0.85] | 0.55% [0.31, 0.98] |
| 30% | 15.10% [13.60, 16.74] | 2.80% [2.16, 3.62] | 2.10% [1.56, 2.83] |
| 40% | 55.05% [52.86, 57.22] | 17.90% [16.28, 19.64] | 11.65% [10.32, 13.13] |

Brackets are pointwise 95% Monte Carlo intervals, in percent. Approach 1 treats questions as independent and checks once; Approach 3 accounts for groups and checks once; Approach 5 accounts for groups and adjusts five checks. The full results retain all six approaches and every planned missingness setting.

Approach 1's average estimated gain changes from +0.27 to +3.59 to +7.34 points across these three settings, despite a true −4-point difference. With equal 5% loss for successes and failures, its estimated difference is −4.00 points and there are zero observed false switches; that does not guarantee zero risk.

The first tested setting above a 10% false-switch rate is 30% failure loss when success loss is 5%, but 40% failure loss when success loss is 10%. The neighboring tested settings are respectively 20%/5% (1.65%) and 30%/10% (6.95%). This brackets a crossing in this grid; it is not a universal missingness tolerance. Both absolute loss probabilities, the true gain, threshold, sample size and dependence matter. See [all crossing summaries](results/crossings.json) for the 10%, 25% and 50% descriptive rate hurdles.

### Accounting for relatedness remains useful

When the true gain equals the two-point switching hurdle, incorrect switching changes as follows:

| Within-group correlation of paired differences | Approach 1 | Approach 2 | Approach 3 | Approach 5 |
| --- | ---: | ---: | ---: | ---: |
| 4.5% | 3.35% | 8.30% | 2.40% | 1.45% |
| 18.0% | 6.15% | 17.05% | 2.55% | 1.75% |
| 40.5% | 10.80% | 25.50% | 2.25% | 1.95% |

Ignoring relatedness becomes more consequential as dependence increases. Approaches 3 and 5 remain comparatively stable in these settings; small fluctuations in their rates are not evidence of meaningful differences. Full intervals and paired comparisons are linked below. The new sweep does not include independence.

### The switching requirement changes the decision

For a genuine ten-point gain, Approach 5 recommends switching in 74.60%, 63.00% and 26.30% of evaluations when the requirement is greater than one, two and five points, respectively. A higher requirement is harder to establish with the same evidence; it does not demonstrate a better or worse statistical method.

The true +2-point case changes category altogether: worthwhile at a one-point requirement, at the boundary at two, and below the requirement at five. We recomputed all decision opportunities and truth classifications rather than relabeling the original final outcomes.

### The complete-record rule remains too strict as a general policy

Approach 6 leaves every evaluation unresolved in all ten nonzero-missingness settings, even when successful and failed grades are equally likely to disappear at 5%. Its zero incorrect switches therefore do not demonstrate successful discrimination. This is an observed result in the tested settings, not a claim that the rule can never decide before later records go missing.

## Suggested article update

Keep the original headline results and add a short, dated robustness section. Explain that selective loss matters more than the mere presence of missing results; quantify how relatedness changes the risk; and clarify that changing the minimum worthwhile improvement changes the decision being tested. Link a compact appendix to all settings and their uncertainty. Do not frame 55.05% as a typical production failure rate or advertise a universal safe missingness gap.

These checks deepen the existing story rather than justify a separate article. A follow-up would be more useful if it introduced production evidence, compared practical ways to recover missing outcomes, or answered another distinct decision question. No such follow-up has been run here.

## Results and verification

- [Local review with charts and all six approaches](results/REVIEW.html)
- [Full results](results/analysis.json) and [table data](results/table-source.json)
- [Paired comparisons](results/paired-contrasts.json) and [compact cohort-level outcomes](results/cohort-outcomes.jsonl.gz)
- [Missingness chart](results/missingness.svg), [switching-threshold chart](results/threshold.svg) and [relatedness chart](results/relatedness.svg)
- [Execution receipt](results/execution.json) and [independent review](independent-review.json)

All five original-result anchors matched, including regenerated original ledgers. The independent audit checked 966 aggregate rates and intervals, all 18,000 threshold trajectories, 46 independently generated prefix evaluations, and 1,176 paired event comparisons. It is not an independent full regeneration of every missingness and relatedness evaluation.

The main run took 173.84 seconds, used about 41.55 MB peak resident memory, and made no model calls. The original published package's verifier and nine extension tests passed. Frozen study inputs and the extension runner remained unchanged. The local HTML review was generated from the audited data; browser visual inspection was unavailable because the browser blocks local-file URLs.

## Reproduce and inspect

Use Python 3.14.3 on macOS, Linux or WSL for the tested environment. The package uses only the standard library; no model API calls, credentials, network access or paid services are required. Run from the repository root:

```sh
python3 -B research/evaluation-reliability-sensitivity/reproduce.py
```

The default verifies input and output hashes, deterministic tests and an independent audit of the saved results, in a fresh temporary copy. It never overwrites original or extension evidence. Do not use Python `-O`, which disables assertions used in verification.

To replay all 23 settings into a fresh temporary copy:

```sh
python3 -B research/evaluation-reliability-sensitivity/reproduce.py --rerun
```

The replay has a 20-minute, 1 GiB memory and 1 GiB output cap. Temporary outputs are retained and their location is printed. Exact numerical/compressed-file reproduction on other Python or compression-library versions is not certified. A same-seed replay checks reproducibility; it is not additional independent evidence.

Regenerate the local review and three figures from the saved results:

```sh
python3 -B research/evaluation-reliability-sensitivity/render.py
```

## Files

| File | Purpose |
| --- | --- |
| [DESIGN.md](DESIGN.md) | Questions, settings, interpretation and reporting boundaries |
| [config.json](config.json) | Fixed grid, seeds, sample size and resource limits |
| [FREEZE.json](FREEZE.json) | Pre-execution configuration and source/input hashes |
| [analyze.py](analyze.py) | Reuses the original generator and evaluator; writes only new extension results |
| [test_sensitivity.py](test_sensitivity.py) | Deterministic checks of pairing, masks, thresholds and reporting |
| [independent_review.py](independent_review.py) | Separate saved-result audit and prescribed-prefix regeneration; imports neither generator nor runner |
| [reproduce.py](reproduce.py) | Non-destructive verification and optional replay |
| [render.py](render.py) | Creates charts and the local review from saved numerical results |

The original model-free simulation assumptions still apply. These sensitivities do not estimate how frequently missing grades or dependence occur in production, measure deployment value, or identify a universally best approach. Original software follows the repository's [MIT license](../../LICENSE).
