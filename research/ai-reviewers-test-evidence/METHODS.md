# Methods and data dictionary

## Materials and conditions

There are 60 disjoint task cases, one selected patch per task: 20 in phase 1 and 40 in phase 2. Each patch has three configured reviewers, five conditions and two repeats, giving 1,800 planned reviews. Selection used public repository, candidate and input-length metadata with fixed hash rankings and quotas, not benchmark success labels. It is a selected roster, not a representative sample.

A supplies issue and patch only. B adds a factual diagnostic summary. C adds the complete execution report with source unspecified. D attributes that complete report to the patch-producing system; E attributes the identical report to a separate evaluator. Source labels are hypothetical experimental assignments. B differs from C in content and length, not only presentation.

Reviewers are the recorded routes `openai/gpt-5.6-terra`, `anthropic/claude-sonnet-5` and `google/gemini-3.8-flash`. Reviews were separate sessions without tools or code execution. Sonnet received a native JSON-schema output constraint in phase 2; its phase change is not assumed behaviorally inert. The two task rosters also differ. There is no pooled cross-phase effect estimate.

## Records

`data/reviews.json` contains two arrays:

- `labels`: `phase` (1 or 2), public `task_id`, Boolean `resolved`, normalized `patch_sha256`, downloaded `patch_file_sha256`, public `patch_url`, `report_url` and `report_sha256`. Order preserves each original roster for exact bootstrap reproduction. Labels are the official report's resolved flag; 10/10 passing/failing tasks in phase 1 and 20/20 in phase 2.
- `cells`: `phase`, `task_id`, configured `model`, `condition` (A–E), `repeat` (1 or 2), Boolean `valid` and `resolved`. A valid cell additionally has `decision`: APPROVE, HOLD or ABSTAIN. Invalid cells have no decision. There is one record per attempted planned cell; there were no retries.

APPROVE means accepting without additional correctness work. HOLD requests more correctness work or evidence. ABSTAIN means no meaningful assessment can be made. HOLD is not a claim that a patch is wrong.

No response prose, reasoning, probabilities, raw request/response payloads, API identifiers, personal paths, contact information, credentials, usage or billing data are included. This allowlist is intentional.

## Statistics

Approval is APPROVE divided by usable reviews. Passing-patch acceptance and failing-patch approval condition on the benchmark label. Approval precision is passing-patch approvals divided by all approvals. Binary policy agreement counts passing-patch approvals plus failing-patch nonapprovals, divided by usable reviews; HOLD and ABSTAIN are combined only for that binary policy metric.

Matched model comparisons require all three reviewers to have both usable repeats within a condition. Matched scenario comparisons require both repeats of both relevant conditions within a reviewer. Class-stratified paired bootstraps resample whole tasks, preserving both repeats and the observed passing/failing mix, for 10,000 draws using the original fixed seeds. These supplementary comparisons and benchmark scoring are post-hoc.

The figure's conservative task-level intervals average exact binomial bounds for the indicators "any approval" and "both approvals," with a union bound. They deliberately avoid treating two reviews as independent trials. The sensitivity assumption concerns exchangeable tasks and is not a sampling guarantee for software work. Zero observed failing approvals does not imply zero risk.

The original E−D approval contrast averages repeats within each task, then tasks within each reviewer. The three-model mean uses tasks complete for all reviewers in D and E. Its 10,000-draw whole-task bootstrap is not class-stratified. Each phase uses its original seed and roster order. Full-roster missing-answer bounds assign every unavailable approval its extreme value; these are not confidence intervals.

## Limits of this reproduction

The package reproduces all numerical objects in the saved supplementary article statistics and all three audited figure datasets. It does not reconstruct the original selection population, full condition packets, provider-side serialization, parser decisions from raw prose, or qualitative rationale examples. Direct archive checks support the exported classifications, but a public user cannot redo those private checks from this package. No model outputs were recollected or repaired.
