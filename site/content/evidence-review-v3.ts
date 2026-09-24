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

export const approvalOverviewTakeaway = `Approval is not accuracy: approving more patches can mean accepting more good work, more faulty work, or both. These follow-up rates use all usable responses, with different denominators. The main findings instead compare matched tasks. [Metric definitions](#appendix-c).`;

export const reviewSections: ReviewSection[] = [
  { id: "introduction", title: "Why this research?", body: `An AI proposes a software fix. Before accepting it, you ask another AI to review the change. What evidence should that reviewer receive—and would another model make the same decision?

We wanted to understand whether test results help AI reviewers make better acceptance decisions, whether a concise summary is enough, and whether calling the same evidence “independent” changes its influence.

A reviewer that rejects everything can avoid faulty approvals while blocking useful work. We therefore examined both sides: acceptance of patches that passed the benchmark and approval of patches that failed it. This is a study of how reviewers interpret available evidence, not whether they can discover defects independently.` },
  { id: "experiment-setup", title: "How we tested AI reviewers", body: `We used 60 public software tasks, each with one AI-generated **patch**: a proposed code change intended to fix the reported problem. Three reviewers—GPT-5.6 Terra, Claude Sonnet 5 and Gemini 3.8 Flash—received the same issue and patch under five evidence scenarios:

1. **No report:** issue and proposed fix only.
2. **Factual summary:** a short account of recorded test results.
3. **Full report:** the complete log, with no source label.
4. **Patch-producing source:** the full log attributed to the system that proposed the fix.
5. **Separate evaluator:** the identical log attributed to an evaluator that did not propose it.

The summary retained failures and warnings. The last three scenarios used identical report bodies; their source labels were explicitly hypothetical. [Evidence and selection details](#appendix-a).

Each reviewer was asked twice in fresh sessions, without tools, to approve, hold or abstain. Hold meant requesting more work; it did not necessarily mean the patch was wrong. The 20-task initial batch and 40-task follow-up produced 1,692 usable reviews. Repeats are not independent tasks. [Settings and missing responses](#appendix-b).

The reports came from the same benchmark evaluation used to label patches as passing or failing. “Passing” therefore means passing those tests—not independently proven correctness.` },
  { id: "findings-at-a-glance", title: "Three findings at a glance", body: "" },
  { id: "finding-1", title: "1. Test evidence reduced faulty approvals", body: `### Did a summary help—and did a full report help more?

Without a test report, reviewers sometimes approved patches that failed the benchmark. With either a faithful summary or the full report, those approvals disappeared on the matched failing tasks.

![Faulty approvals across the same 15 tasks and three evidence scenarios.](/research-assets/evidence-review/v2/finding-2-evidence-content.svg)

The full report showed no further reduction on this measure. That makes a concise summary worth testing in a review workflow, but it does not establish that the two formats are interchangeable: they may differ in accepting passing patches or on new tasks.

**Practical takeaway:** give the reviewer concrete test evidence, including failures and warnings. Test whether a faithful summary supports the decisions you need before assuming a longer log is better. [Worked example](#appendix-f) · [Missing-response check](#appendix-d).` },
  { id: "finding-2", title: "2. The same evidence led to different acceptance decisions", body: `### Did reviewers agree on which passing patches to accept?

No. Given the same full report, Claude accepted more benchmark-passing fixes than Terra or Gemini. None approved a benchmark-failing patch on this matched task set.

![Acceptance of passing patches under the same full report.](/research-assets/evidence-review/v2/finding-1-same-evidence.svg)

A withheld approval is not automatically an error. In one passing example, Gemini acknowledged the fix but requested a committed regression test and removal of a reproduction script. We did not measure whether those requests were necessary or what following them would cost. [The example and its selection rule](#appendix-f).

**Practical takeaway:** evaluate what your reviewer leaves waiting as well as what it accepts. A low faulty-approval rate alone does not tell you how much useful work it blocks.

These are configured reviewers, not a universal ranking. Sonnet used a native structured-output constraint in the follow-up; the [configuration details](#appendix-b) matter when interpreting the comparison.` },
  { id: "finding-3", title: "3. An “independent” label had no consistent follow-up benefit", body: `### Did changing the stated source change approval?

The early pattern did not hold consistently. Calling an identical report the work of a separate evaluator initially increased approval on average. In the larger follow-up, the average was near zero and the individual reviewers moved in different directions.

![Source-label approval differences, shown separately for the initial batch and follow-up.](/research-assets/evidence-review/v2/finding-3-source-attribution.svg)

The two phases used different tasks, and Sonnet's response constraint changed before the follow-up. We keep the phases separate rather than interpreting their difference as the effect of one change. [Paired comparisons and uncertainty](#appendix-d).

Related research shows that [surface cues can bias code judges](https://aclanthology.org/2026.findings-eacl.70/) and [authorship labels can change judgments of unchanged material](https://arxiv.org/html/2608.18091). Our finding is narrower: the claimed source of a test report did not consistently increase approval in this follow-up.

**Practical takeaway:** don't rely on the word “independent” to improve review decisions. This experiment changed a label, not the tests; it does not tell us whether genuinely independent testing would help.` },
  { id: "application", title: "How to use these findings", body: `For an AI-assisted review workflow:

1. Give reviewers actual test outcomes, preserving failures, warnings and relevant context.
2. Compare concise summaries with full reports on the same work. Measure both faulty approvals and acceptance of passing fixes.
3. Inspect withheld approvals: is the requested follow-up useful, or is it unnecessary friction? Our study identifies that question; it did not measure the answer.
4. Test the reviewer configuration on your own tasks before using it as an acceptance gate.

Keep the test harness and human judgment in the workflow. A second model is another source of evidence, not a substitute for verifying a fix.` },
  { id: "limitations", title: "What this study does—and doesn’t—tell us", body: `Use this study to design reviewer evaluations and decide what evidence to test in your workflow. It does not establish a universal model ranking or prove that an AI reviewer can certify software correctness. We selected public tasks, some reviews were missing, and model training exposure is unknown. The supplied reports came from the same evaluation used to label the patches. The benchmark comparisons were added after collection, and Sonnet's formatting constraint changed between phases.

Tests can [miss defects](https://arxiv.org/abs/2503.15223) or [reject acceptable implementations](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/). Validate these patterns on your own work; do not treat zero observed faulty approvals as zero risk. [Full limitations](#appendix-g).` },
  { id: "conclusion", title: "The bottom line", body: `Test evidence helped these reviewers avoid faulty approvals, but it did not make their acceptance decisions interchangeable. Evaluate both the bad fixes a reviewer accepts and the good work it leaves waiting—and judge evidence by its contents, not just its stated source.` },
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
