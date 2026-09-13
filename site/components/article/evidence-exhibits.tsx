import { scenarioExample as example } from "@/content/evidence-review-example";
import styles from "./page.module.css";

const models = [
  { id: "openai/gpt-5.6-terra", name: "GPT-5.6 Terra", color: "#087b82" },
  { id: "anthropic/claude-sonnet-5", name: "Claude Sonnet 5", color: "#ac5030" },
  { id: "google/gemini-3.8-flash", name: "Gemini 3.8 Flash", color: "#7059a5" },
];
const scenarios = [
  { id: "A", name: "No report" },
  { id: "B", name: "Factual summary" },
  { id: "C", name: "Full report · source unspecified" },
  { id: "D", name: "Full report · patch-producing system" },
  { id: "E", name: "Full report · separate evaluator" },
];

export function ApprovalOverview() {
  return <figure className={styles.overview}>
    <div className={styles.exhibitTable} role="region" aria-label="Overall approval rates" tabIndex={0}>
      <table>
        <caption>Follow-up approval rates · all usable reviews</caption>
        <thead><tr><th scope="col">Evidence scenario</th>{models.map(m => <th scope="col" key={m.id}>{m.name}</th>)}</tr></thead>
        <tbody>{scenarios.map(s => <tr key={s.id}>
          <th scope="row">{s.name}</th>
          {models.map(m => {
            const count = example.counts.find(c => c.scenario === s.id && c.model === m.id)!;
            const rate = 100 * count.approvals / count.usable;
            return <td key={m.id}>
              <span className={styles.rate}>{rate.toFixed(1)}%</span>
              <span className={styles.rateBar} aria-hidden="true"><span style={{ width: `${rate}%`, background: m.color }} /></span>
              <span className={styles.denominator}>{count.approvals}/{count.usable} reviews</span>
            </td>;
          })}
        </tr>)}</tbody>
      </table>
    </div>
    <figcaption>Bars share a 0–100% scale. Approval is not accuracy. Counts differ because some reviews were missing or unusable; these are not matched scenario-effect estimates. Exact phase 1 and phase 2 counts are in <a href="#full-tables">Appendix E</a>.</figcaption>
  </figure>;
}

function ExactText({ title, text }: { title: string; text: string }) {
  return <details className={styles.exactText}><summary>{title}</summary><pre>{text}</pre></details>;
}

export function ScenarioWalkthrough() {
  return <div className={styles.walkthrough}>
    <h4>One patch, five review scenarios</h4>
    <p>Matplotlib 20676 concerns a plotting tool: turning on an interactive selection unexpectedly expanded the plot to include zero. The proposed patch changed how the selection handles were added so they would not change the plot limits. This was the first task in the frozen follow-up order, selected for illustration before benchmark scoring.</p>
    <p>Every scenario used the same issue, candidate patch, review instructions, and final question: “Would you accept this patch as the solution to the supplied issue? Return the specified JSON object.” Reviewers could approve, hold, or abstain. They could not run tests or browse.</p>
    <ExactText title="Read the original issue description" text={example.issue} />
    <ExactText title="Read the candidate patch supplied in all five scenarios" text={example.patch} />

    <h4>A. Issue and patch only</h4>
    <p>The reviewer received the issue and patch above, without a test report or report-source label. This shows what it decided from the proposed fix alone.</p>

    <h4>B. Add a factual summary</h4>
    <p>The reviewer also received the actual summary below, with the label “{example.conditions[1].sourceLabel}” It retained the recorded failures, warnings, and diagnostic context. It reported three failures, 32 passes, and one skip. It was shorter than the full log, not a one-line verdict.</p>
    <ExactText title="Read the exact factual summary supplied in scenario B" text={example.summary} />

    <h4>C. Supply the full report</h4>
    <p>The summary was replaced by the complete execution report, with the same label “{example.conditions[2].sourceLabel}” This adds detail, including routine setup and individual passing-test names.</p>
    <ExactText title="Read the full report shared by scenarios C, D, and E" text={example.report} />

    <h4>D and E. Change only the stated source</h4>
    <p>The issue, patch, and full report remained identical. Only the source line changed:</p>
    <div className={styles.sourceLabels}>
      <p>D. “{example.conditions[3].sourceLabel}”</p>
      <p>E. “{example.conditions[4].sourceLabel}”</p>
    </div>
    <p>These were hypothetical assignments, explicitly described as such in the review instructions. We did not obtain a second independent test report. C, D, and E used the same report text, verified against the saved evidence hashes.</p>

    <h4>What each reviewer decided</h4>
    <p>Each cell shows repeat 1 / repeat 2. All 30 reviews for this example were usable. Hold means further work was requested, not necessarily that the reviewer declared the patch incorrect.</p>
    <div className={styles.exhibitTable} role="region" aria-label="Recorded decisions for the example patch" tabIndex={0}>
      <table><thead><tr><th scope="col">Scenario</th>{models.map(m => <th scope="col" key={m.id}>{m.name}</th>)}</tr></thead>
        <tbody>{scenarios.map(s => <tr key={s.id}><th scope="row">{s.id}. {s.name}</th>{models.map(m => <td key={m.id}>{[1, 2].map(repeat => {
          const review = example.reviews.find(r => r.scenario === s.id && r.model === m.id && r.repeat === repeat)!;
          return review.decision.charAt(0) + review.decision.slice(1).toLowerCase();
        }).join(" / ")}</td>)}</tr>)}</tbody>
      </table>
    </div>
    <p>Without a report, Terra and Gemini approved both times; Sonnet held both times. With any report, all three held in both repeats. The report showed handle-position checks returning zero instead of the expected bounds, and the reviewers cited those failures. The candidate failed its official benchmark evaluation.</p>
    <p>This example illustrates a change after supplying evidence, not an effect of the source label: D and E produced the same approval decisions here. We did not rerun the patch or independently establish the causal explanations in the reviewers’ rationales. The aggregate findings, not this single case, support the article’s conclusions.</p>
  </div>;
}
