import { articleV2 } from "./evidence-review-v2";
import { methods, tables } from "./evidence-review-draft";

export type ReviewSection = { id: string; title: string; body: string };

// Editorial version only. Reuse the audited result prose and figures without
// changing their estimates, cohorts, uncertainty, or source records.
function withoutEmDash(text: string) {
  return text.replace(/—/g, ", ").replace(/,\s+,/g, ",");
}
function originalFinding(number: number) {
  const start = articleV2.indexOf(`## ${number}. `);
  const end = articleV2.indexOf("\n## ", start + 1);
  return withoutEmDash(articleV2.slice(start, end < 0 ? undefined : end).split("\n").slice(1).join("\n").trim());
}
function methodSection(title: string) {
  const start = methods.indexOf(`## ${title}\n`);
  const end = methods.indexOf("\n## ", start + 1);
  return withoutEmDash(methods.slice(start, end < 0 ? undefined : end).split("\n").slice(1).join("\n").trim());
}

// Move illustrative cases and missing-response sensitivity out of the main
// narrative, retaining their audited wording and selection disclosures.
const firstFinding = originalFinding(1);
const secondFinding = originalFinding(2);
const passingCaseStart = firstFinding.indexOf("A colorbar fix makes the distinction concrete.");
const passingCaseEnd = firstFinding.indexOf("The comparison concerns these configured systems");
const failingCaseStart = secondFinding.indexOf("Matplotlib 20676, the first task");
const missingBoundsStart = secondFinding.indexOf("Missing responses do not erase");
if ([passingCaseStart, passingCaseEnd, failingCaseStart, missingBoundsStart].some(index => index < 0)) {
  throw new Error("Expected audited finding boundaries are missing");
}
const passingCase = firstFinding.slice(passingCaseStart, passingCaseEnd).trim();
const missingResponseBounds = secondFinding.slice(missingBoundsStart).trim();

export const approvalOverviewTakeaway = `### What stands out?

Claude approved the largest share of patches in every scenario, Terra was in the middle, and Gemini approved the smallest share. Across the five scenarios, approval ranged from 39.5% to 48.0% for Claude, 32.9% to 39.5% for Terra, and 15.8% to 27.6% for Gemini. The ordering across reviewers stayed the same even as the evidence changed.

There was no uniform rise in approval as more evidence was supplied. Compared with no report, the full, source-unspecified report had a lower approval rate for Terra and higher rates for Claude and Gemini. These descriptive differences do not establish statistical significance, or prove that the scenarios had no effect.

But the overall rate leaves an important question unanswered: which patches were being approved? Similar approval rates can conceal different decisions about passing and failing patches. We therefore break the results into three findings below: the first answers our questions about supplying evidence and adding detail, the second compares reviewers, and the third examines the source label.`;

export const reviewSections: ReviewSection[] = [
  { id: "introduction", title: "Introduction", body: `An AI has proposed a software fix. Before accepting it, you ask another AI to review the change. It sounds like a sensible second opinion. But what evidence does that reviewer need, and would another model make the same decision?

A reviewer that rejects every fix can avoid approving a faulty one, but it also prevents useful work from moving forward. To understand review quality, we need to look at both sides: which fixes a system accepts and which it leaves behind.

We studied how three AI reviewers responded to five evidence scenarios. We gave them the same software issues and proposed fixes, then varied the amount of test evidence and its stated source. This let us examine what changed when evidence was supplied, whether a full report added value beyond a summary, how reviewers differed, and whether a source label affected approval.

We measured approval decisions across the scenarios and also compared them with official benchmark outcomes. The aim was to understand how AI reviewers use evidence already available to them, not whether they can discover software defects independently.` },
  { id: "experiment-setup", title: "Experiment setup", body: `### What is a patch?

A **patch** is a proposed change to software intended to fix a problem. For example, a plotting tool might draw a selection handle in the wrong place. A patch changes the code responsible for positioning it. The question for a reviewer is whether to accept that change.

A **test** checks a particular behavior, such as whether the handle appears at the expected position. A **test report** records what ran, what passed, and what failed. Passing those tests is useful evidence, but it does not prove that every possible behavior is correct.

In this study, the patches were previously generated AI fixes for public software tasks. We did not ask the reviewers to create patches or run new tests. We supplied the issue description, the proposed code change, and one of five evidence scenarios. [Appendix A](#appendix-a) explains how the patches and reports were selected.

### Questions we investigated

1. Does providing test evidence change approval decisions? We compared no report with a factual summary or full report.
2. Does a full report add value beyond a factual summary? We compared the two evidence packages.
3. Do different reviewers make similar decisions with the same evidence? We compared the three models under the same scenarios.
4. Does the stated source matter when the evidence stays identical? We changed only the source label on the full report.

### One patch, five evidence scenarios

| Scenario | What the reviewer received | Why we included it |
|---|---|---|
| A. No report | Issue description and patch only | Establish decisions without test evidence |
| B. Factual summary | The same issue and patch, plus a short account of recorded test results | Test whether a concise summary helps |
| C. Full report | The same issue and patch, plus the complete log with no source label | Test whether more detail adds value |
| D. Patch-producing source | The full log attributed to the system that proposed the patch | Measure decisions when evidence is described as coming from the producer |
| E. Separate evaluator | The identical full log attributed to an evaluator that did not propose the patch | Isolate the effect of claimed independent provenance |

The report bodies in C, D, and E were identical. The source labels were explicitly **hypothetical experimental assignments**, not claims about who actually collected the evidence. The summary retained failures, warnings, and diagnostic context; it was not a favorable rewrite. Comparing the summary with the full log therefore changes both information and length.

### Three reviewers, the same decision

We used **GPT-5.6 Terra, Claude Sonnet 5, and Gemini 3.8 Flash**. Each was asked to review each patch twice in each scenario, in fresh sessions, without tools or code execution. The repeats let us observe whether a decision was consistent; they do not turn one software task into two independent tasks.

Each reviewer chose one of three responses:

- **Approve:** accept the patch without further correctness work.
- **Hold:** request more work or evidence before accepting it.
- **Abstain:** the supplied material does not permit a meaningful assessment.

A hold is not necessarily a claim that the patch is wrong. A model might acknowledge the fix but still request a committed regression test or another change. [Appendix C](#appendix-c) defines the decisions and metrics, and [Appendix F](#appendix-f) shows all five scenarios for one actual patch.

### What we compared

The study began with **20 tasks**, followed by **40 different tasks**. With three reviewers, five scenarios, and two repeats, that gave 1,800 planned reviews. We retained 1,692 usable responses from 1,736 attempts. [Appendix B](#appendix-b) records the model settings and accounts for invalid and unattempted reviews.

Overall approval rates describe how willing a reviewer was to accept a patch. Comparing those decisions with benchmark outcomes lets us distinguish approval of a passing patch from approval of a failing one. We report both, rather than treating a higher approval rate as automatically better. The analysis history is recorded in [Appendix D](#appendix-d).

The reports came from the same official evaluation that supplied those benchmark outcomes. Here, “benchmark-passing” means the candidate passed that evaluation, not that its correctness was independently established. This is a study of evidence interpretation.

The findings below use matched subsets when comparing reviewers or scenarios, so their exact task counts differ. We show those counts with each result rather than treating all 1,692 responses as independent observations.` },
  { id: "approval-overview", title: "Approval across the five scenarios", body: `The overview below shows all usable reviews in the 40-task follow-up, with two planned reviews per task, scenario, and model. Each percentage is the share of usable reviews that approved a patch, whether it passed or failed the benchmark.

These are descriptive rates with different response counts, not matched estimates of scenario effects. A higher bar is not necessarily a better result. The findings that follow separate faulty approvals from acceptance of passing patches and use matched tasks for comparisons.` },
  { id: "findings-at-a-glance", title: "Three findings at a glance", body: `1. [Test evidence reduced faulty approvals](#finding-1). A summary and full report both reduced observed faulty approvals to zero on matched failing tasks; the full report showed no further reduction.
2. [Reviewers differed in accepting passing patches](#finding-2). The same full report led to different acceptance rates for benchmark-passing patches.
3. [Changing the stated source did not consistently increase approval](#finding-3). The initial increase weakened in the larger follow-up.` },
  { id: "finding-1", title: "1. Test evidence reduced faulty approvals", body: `### Does providing test evidence change approval decisions?

Yes, on the matched benchmark-failing tasks. Some reviews approved these patches without a report; none approved them with either the factual summary or full report.

### Does a full report add value beyond a factual summary?

We observed no further reduction in faulty approvals: both formats reached zero on this matched sample. That answers this particular metric, not whether full reports offer other benefits or whether the formats are equivalent.

` + secondFinding.slice(0, failingCaseStart).trim().replace(/^[\s\S]*?\n\n/, "") + `

### What this means

The reviewers sometimes accepted a failing patch when they only saw the issue and code. Once they received a faithful summary of the test results, those approvals disappeared on the matched tasks. Giving them the full log did not reduce faulty approvals further in this sample.

That makes a concise summary worth testing in a review workflow. It does not prove that summaries always work as well as full reports, or that either format prevents every mistake. The patch example is in [Appendix F](#appendix-f), and the check on missing responses is in [Appendix D](#appendix-d).` },
  { id: "finding-2", title: "2. Reviewers differed in accepting passing patches", body: `### Do different reviewers make similar decisions with the same evidence?

Not consistently. They differed in how often they accepted benchmark-passing patches, even when the report and tasks were the same.

` + firstFinding.slice(0, passingCaseStart).trim() + `

### What this means

With the full, source-unspecified test report, none of the three reviewers approved a benchmark-failing patch on these matched tasks. But they did not agree on which benchmark-passing patches were ready to accept. Avoiding faulty approvals is only one part of useful review; we also need to ask how much passing work a reviewer leaves waiting.

Withholding approval does not necessarily mean the reviewer thinks a fix is wrong. It can mean asking for another test or code change. Acting on those requests could take more time and, if an AI does the follow-up work, more tokens. We did not measure that additional work or determine whether it was necessary. A concrete example appears in [Appendix F](#appendix-f).

These results describe the configured reviewers on this task sample, not a universal model ranking. Sonnet also used a native structured-output constraint in the follow-up. The configuration is described in [Appendix B](#appendix-b); matched samples and uncertainty are explained in [Appendix D](#appendix-d).` },
  { id: "finding-3", title: "3. Changing the stated source did not consistently increase approval", body: `### Does the stated source matter when the evidence stays identical?

The result was mixed. Attributing the report to a separate evaluator initially increased approval on average, but that increase did not hold consistently in the larger follow-up. This is not evidence that source labels can never matter.

` + originalFinding(3).replace("The original primary comparison changed only", "To isolate the source-label comparison, we changed only") + `

### What this means

Changing who supposedly supplied an identical report did not reliably increase approval in the larger follow-up. The encouraging early pattern did not hold consistently across reviewers on the new tasks.

We should not assume that calling a report “independent” makes reviewers trust it more. This experiment changed a label, not the quality or actual independence of the tests. It therefore says nothing about whether genuinely independent testing is useful. See [Appendix D](#appendix-d) for the paired comparison and [Appendix F](#appendix-f) for the exact source-label wording.` },
  { id: "conclusion", title: "What this means for AI-assisted review", body: `The central lesson is not simply that more evidence makes AI reviewers better. These reviewers used test evidence to avoid some approvals of benchmark-failing patches, but they differed substantially in their willingness to accept benchmark-passing fixes. Calling an identical report independently sourced did not produce a consistent follow-up benefit.

For someone building an AI-assisted review workflow, this suggests evaluating **both acceptance and withholding**. A low faulty-approval rate is valuable, but it does not tell you how many useful fixes the system leaves waiting. Approval rate alone cannot distinguish those outcomes either.

It also suggests testing the usefulness of a concise, faithful summary before assuming that a longer report is always necessary. Our result supports that question, not a universal recommendation to discard detail. The study did not measure the cost or necessity of the additional work reviewers requested.

Calling a report “independent” did not consistently increase approval in our follow-up. We changed only the report's stated source, not its contents. This result does not tell us whether genuinely independent testing would improve review quality.

### What we cannot conclude

This is not a universal ranking of Claude, Terra, and Gemini. We tested particular configured systems on a selected set of public tasks. Sonnet used a native structured-output constraint in the follow-up, public tasks may have appeared in training, and missing reviews limit what we can infer.

Nor does a benchmark outcome certify software correctness. [Tests can miss defects](https://arxiv.org/abs/2503.15223) or [reject acceptable implementations](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/). Because the reviewers saw evidence from the evaluation used to assess their decisions, this experiment does not show that an LLM can replace a test harness or human reviewer.

The next useful question is whether these patterns hold with genuinely independent evidence and a broader task sample. That remains future work, not a result of this study.

The appendix below provides the supporting detail: [selection and evidence](#appendix-a), [model settings and missing reviews](#appendix-b), [metric definitions](#appendix-c), [uncertainty](#appendix-d), [full results](#full-tables), [worked examples](#appendix-f), and [interpretation limits](#appendix-g).` },
];

export const appendixSections: ReviewSection[] = [
  { id: "appendix-a", title: "A. Task selection and evidence", body: methodSection("Materials and selection") },
  { id: "appendix-b", title: "B. Models, prompts, and collection", body: methodSection("Reviewers and collection") },
  { id: "appendix-c", title: "C. Decision definitions and metrics", body: methodSection("Definitions") },
  { id: "appendix-d", title: "D. Statistical methods and uncertainty", body: "### Source-label comparison\n\n" + methodSection("Original paired estimates and uncertainty") + "\n\n### Supplementary matched comparisons\n\n" + methodSection("Article-specific matched comparisons").replaceAll("Figure 2", "The supplementary matched analysis") },
  { id: "full-tables", title: "E. Complete results and missing responses", body: withoutEmDash(tables.replace(/^# [^\n]+\n/, "")).replaceAll("Figure 2", "the main findings") },
  { id: "appendix-f", title: "F. Five-scenario walkthrough and patch examples", body: methodSection("Reproducibility").replace("[Exact public revision, report hashes, all 30 decisions and original Gemini C1/C2 rationales](#two-cases-behind-the-aggregate-rates) remain available.", "Exact public revisions, report hashes, all 30 decisions and original Gemini C1/C2 rationales are preserved in the local research archive. The case illustrates [Finding 2](#finding-2).") },
  { id: "appendix-g", title: "G. Limitations and interpretation", body: `The earlier analysis plan prioritized the source-label comparison. Benchmark-label scoring and the article-specific matched comparisons were added after collection. These later analyses are supplementary, not retrospectively prespecified hypotheses.

The study retained 568 APPROVE, 1,114 HOLD, and 10 ABSTAIN decisions. Forty-four attempts were technically invalid and 64 planned reviews were unattempted. Missing responses were not scored as wrong, and repeats were not treated as independent tasks.

The quota-selected tasks are not a representative sample of software work. Matched complete-case subsets may differ from the full roster. Bootstrap intervals describe stability under the stated resampling procedure; missing-answer bounds answer a different question and are not confidence intervals.

The supplied reports came from the evaluation defining the outcome labels. Source attributions were hypothetical. No new tests were generated or executed in this experiment, and the causal claims in reviewer rationales were not independently established. Public-task training exposure is unknown.

Sonnet's structured-output constraint changed before the follow-up. That change and the different task mix prevent attributing cross-stage differences to one cause. Results concern these configurations, not model families in general.

Original study artifacts remain unchanged. The [public analysis supplement](https://github.com/gurnanumudit/ai-product-research/tree/main/research/ai-reviewers-test-evidence) reproduces the numerical results from derived decision records; it does not rerun the original model experiment.` },
];

// Keep the full audited detail available without requiring every reader to
// traverse derivations, hashes and archival paths in the main appendix.
export const technicalAppendix = appendixSections.filter(s => ["appendix-a", "appendix-b", "appendix-d", "appendix-f"].includes(s.id));
export const resultTableSections = appendixSections.find(s => s.id === "full-tables")!.body
  .split(/^## /m).slice(1).map((part, index) => ({
    id: index === 0 ? "phase-2-results" : "phase-1-results",
    title: part.slice(0, part.indexOf("\n")).replace("all-usable descriptive metrics", "complete descriptive results"),
    body: part.slice(part.indexOf("\n") + 1).trim(),
  }));
export const conciseAppendixSections: ReviewSection[] = appendixSections.map(section => {
  const summaries: Record<string, string> = {
    "appendix-c": `The main findings distinguish willingness to approve from agreement with benchmark outcomes. These definitions explain the chart labels and the complete tables in [Appendix E](#full-tables).

- Approval rate: the share of usable reviews that approved a patch, whether it passed or failed the benchmark.
- Passing-patch approval: approvals divided by usable reviews of benchmark-passing patches. This measures how often passing fixes were accepted.
- Failing-patch approval: approvals divided by usable reviews of benchmark-failing patches. This measures faulty approvals relative to the benchmark.
- Approval precision: among approved patches, the share that passed the benchmark. It is undefined if nothing was approved.

Hold means additional work or evidence was requested. Abstain means the reviewer could not meaningfully assess the patch. Neither is automatically a declaration that a patch is wrong, and an invalid or unattempted response is neither of these decisions.

The expanded tables also retain binary policy agreement: the share of usable reviews that either approved a passing patch or withheld a failing patch. Only for this metric are hold and abstain grouped together. It does not establish that every withheld patch needed more work.

Reviewers also supplied a probability that the patch satisfied the issue without relevant regressions. We do not use those estimates to claim calibrated confidence or to support the three main findings.`,
    "full-tables": `These tables support the [approval overview](#approval-overview) and let readers inspect passing-patch approvals, faulty approvals, and withheld decisions for every model and scenario. They include all usable responses, so their denominators differ from the matched subsets used in [Finding 1](#finding-1) and [Finding 2](#finding-2). They should not be subtracted as if every row contained the same tasks.

Open either phase below. A means no report; B, factual summary; C, full report with source unspecified; D, the same report attributed to the patch-producing system; E, the identical report attributed to a separate evaluator. Metric definitions are in [Appendix C](#appendix-c), and missing-review counts are in [Appendix B](#appendix-b).`,
    "appendix-g": `These limits apply to the three findings, rather than adding a separate research claim.

### What the benchmark can establish

The reviewers saw reports from the same evaluation used to label patches as passing or failing. This tests interpretation of available benchmark evidence, not independent verification of software correctness. Tests can miss defects or reject acceptable implementations.

### Where the results may not generalize

The sample was selected using repository and report-length quotas, not drawn to represent all software work. Public tasks may have appeared in model training. Missing responses also affect which tasks enter the matched comparisons. Results describe the selected tasks and configured reviewers.

### Why the phases are not interchangeable

The follow-up used different tasks and repository proportions, and Sonnet gained a structured-output constraint. We cannot attribute a change between phases to only one of those differences. [Appendix B](#appendix-b) records the configuration change; [Appendix D](#appendix-d) explains how the phases were analyzed.

### What was not measured

The source labels were hypothetical; no independently generated tests were compared. Reviewer explanations were not verified as accounts of their internal reasoning. We did not measure the necessity, time, or token cost of the additional work requested when approval was withheld.`,
    "appendix-a": `We audited 260 historical patches across 122 software tasks. Exact-patch public execution logs were available for 216 patches across 78 tasks. We selected one candidate per task, first for 20 tasks and then for 40 different tasks, using fixed repository and report-length quotas. Selection did not use correctness labels or reviewer outcomes.

The combined sample covered six repositories and happened to contain 30 benchmark-passing and 30 benchmark-failing patches. This was not a correctness quota or a representative sample of all software work.

The factual summary retained adverse diagnostics; the full-report scenarios used identical log bodies. No new tests were generated or run. The reports came from the evaluation defining the official outcome, although its final resolved flag was not supplied as a direct answer key.`,
    "appendix-b": `The reviewers were GPT-5.6 Terra, Claude Sonnet 5, and Gemini 3.8 Flash. Each task had two planned fresh reviews per model and scenario, with low reasoning effort, a 4,096-token output limit, and no tools. Each response supplied a decision, probability estimate, and short rationale.

Before the follow-up, Sonnet gained a native JSON output constraint to improve response formatting. The visible review instructions stayed fixed, but we cannot assume that the constraint had no behavioral effect. No study response was rerun or repaired.

| Stage | Tasks | Planned | Attempted | Usable | Invalid | Unattempted |
|---|---:|---:|---:|---:|---:|---:|
| Phase 1 | 20 | 600 | 600 | 563 | 37 | 0 |
| Phase 2 | 40 | 1200 | 1136 | 1129 | 7 | 64 |
| Total | 60 | 1800 | 1736 | 1692 | 44 | 64 |

“Usable” means a response could be interpreted in the required format, not that its decision was correct. Budget protection left 64 follow-up reviews unattempted. Invalid and unattempted responses remain missing, not rejections or wrong answers.`,
    "appendix-d": `### Analysis history\n\nThe study examined all five scenarios. The earlier analysis plan prioritized the paired source-label comparison, E versus D. Comparing decisions with benchmark outcomes and the additional matched comparisons were added after response collection. We preserve that history without treating it as a ranking of the questions\u0027 importance.\n\n### Comparisons and uncertainty\n\nFor the source-label comparison, we compared the separate-evaluator and patch-producing-source scenarios within the same task and model, averaging the two repeats first. A task entered that comparison only when all four responses were usable. Pooled estimates required all three models and gave each model equal weight.

We resampled whole tasks 10,000 times to obtain the reported 95% bootstrap intervals. This preserves the relationship between repeated reviews of the same task. The intervals describe stability on our selected roster, not representativeness of all software tasks.

The supplementary model and evidence comparisons also use matched tasks. Finding 2 includes 35 follow-up tasks, of which 18 passed the benchmark and 17 failed. Finding 1 includes 15 benchmark-failing tasks with both repeats available across all three reviewers and scenarios A, B, and C. Missingness need not be random, and these cohorts are not interchangeable.

The charts retain conservative task-level uncertainty intervals, including nonzero upper bounds where no faulty approvals were observed. Full constructions and sensitivity results remain in the technical details below.

### Could missing responses change Finding 1?

${missingResponseBounds}

In plain English, even assigning the missing decisions in the least favorable way would still leave fewer faulty approvals with the full report than without one on this planned task roster. That does not guarantee the same result on new tasks.`,
    "appendix-f": `### A contrasting case: a passing fix that one reviewer withheld

${passingCase}

This illustrates the distinction in [Finding 2](#finding-2): passing the benchmark and satisfying a reviewer's acceptance requirements are not necessarily the same thing. We did not measure the necessity or cost of the extra work requested.

### Reproducibility

Neither example substitutes for the aggregate analysis. The walkthrough above uses the first task in the frozen follow-up dispatch order, selected before benchmark scoring. The contrasting passing-patch example was selected after outcomes by the rule stated above. Exact patches, source reports, original responses, selection rules, and analysis code remain preserved in the research archive. Long identifiers and archival paths are retained in the expandable technical details. The [public analysis supplement](https://github.com/gurnanumudit/ai-product-research/tree/main/research/ai-reviewers-test-evidence) includes derived decisions, benchmark metadata, and code to reproduce the numbers. It excludes raw responses and source logs.`,
  };
  return summaries[section.id] ? { ...section, body: summaries[section.id] } : section;
});

export const findingSummaries = [
  { id: "finding-1", title: "Test evidence reduced faulty approvals", summary: "Both the factual summary and full report reduced observed faulty approvals to zero on matched benchmark-failing tasks. The full report showed no further reduction, but that does not establish that the formats are equivalent." },
  { id: "finding-2", title: "Reviewers differed in accepting passing patches", summary: "With the same full report, Claude accepted more benchmark-passing fixes than Terra or Gemini. None approved a benchmark-failing fix on that matched task set." },
  { id: "finding-3", title: "The source label had no consistent follow-up benefit", summary: "Changing the identical report's stated source to a separate evaluator did not consistently increase approval in the larger follow-up. The initial positive pattern weakened." },
];
