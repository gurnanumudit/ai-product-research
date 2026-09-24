# Provenance and release scope

Prepared September 24, 2026, from the frozen complete134 analysis and subsequent
full-cohort cost reconciliation. The earlier 84-question-only cost restriction
was superseded after historical costs were reconciled. This package uses 134
questions for both accuracy and cost.

## Upstream attribution

Questions originate from [DSBench](https://github.com/LiqiangJing/DSBench),
specifically selected ModelOff-derived business-analysis cases in its
[data-analysis track at the pinned source revision](https://github.com/LiqiangJing/DSBench/tree/ba786096137a5108af11c016ad3f09cdb97beefd/data_analysis).
See Jing et al., [DSBench: How Far Are Data Science Agents from Becoming Data
Science Experts?](https://arxiv.org/abs/2409.07703), ICLR 2025.

The public export contains derived study classifications, numerical costs and
public question identifiers. It does not redistribute upstream workbooks,
question text, reference answers, model response text or third-party code.
Original analysis software follows the repository's MIT license. Third-party
materials retain their own rights; publication does not relicense them or imply
provider or benchmark-author endorsement.

## Integrity and boundaries

`reference/provenance.json` records SHA-256 hashes for exported data and the frozen
source artifacts from which they were projected. Only relative source labels
are retained. The original archive is not distributed; its hashes document
provenance but do not let a reader audit private collection logs.

The export uses explicit field allowlists, omitting local paths, account/project
identifiers, errors with free-form provider content, timestamps, raw responses,
credentials and execution workspaces. The six nonselected original attempts
are retained in the matched cost table, not as extra outcome observations.

The runnable program recalculates numerical claims from these derived records.
It cannot independently verify original prompts, model versions behind routes,
scoring from raw answers, source references or paid resource metering. No new
model calls, regrading, outcome selection or changes to frozen source data were
made for this release.
