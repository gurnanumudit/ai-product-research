import data from "@/content/evaluation-sensitivity-results.json";
import styles from "./page.module.css";
import local from "./sensitivity-results.module.css";

type Cell = (typeof data.cells)[number];
type Metric = Cell["rows"][number]["switch"];
const percent = (value: number) => `${(100 * value).toFixed(2)}%`;
const points = (value: number) => `${value > 0 ? "+" : ""}${Number((100 * value).toFixed(2))}`;
const methodNames = ["One check", "Five checks", "Related questions, one check", "Related questions, five checks", "Related questions, five adjusted checks", "Adjusted checks plus record checks"];

function settingTitle(cell: Cell) {
  if (cell.family === "missingness") {
    return `Missing grades: ${100 * (cell.failed_grade_loss ?? 0)}% of failures · ${100 * (cell.successful_grade_loss ?? 0)}% of successes`;
  }
  if (cell.family === "threshold") {
    return `Require more than ${100 * cell.tau} points · true gain ${points(cell.delta)} points${cell.world_id === "w09_clustered_mnar" ? " · missing grades" : " · complete records"}`;
  }
  return `Related questions: ${((cell.paired_difference_icc ?? 0) * 100).toFixed(1)}% within-group correlation · h = ${cell.h}`;
}

function RateCell({ metric }: { metric: Metric }) {
  return <td>{percent(metric.estimate)}<small>[{percent(metric.wilson95[0])}, {percent(metric.wilson95[1])}]</small></td>;
}

export function SensitivityResults() {
  const families = [
    { id: "missingness", title: "Missing grades: 11 settings", note: "The new version is truly four points worse. Failure-grade loss varies from 5% to 40%, and success-grade loss from 5% to 10%. The 0%/0% setting is a paired complete-record reference; equal-loss and reversed-selection controls are retained." },
    { id: "threshold", title: "Switching requirement: 9 settings", note: "The same three scenarios are evaluated at requirements greater than 1, 2 and 5 points. Every check and first conclusive decision is recalculated. A switch can change from correct to incorrect when the requirement changes." },
    { id: "relatedness", title: "Related questions: 3 settings", note: "The true gain and switching requirement remain +2 points, with complete records. The three settings vary the correlation of paired outcome differences within a group; h is a generator parameter, not the correlation itself." },
  ];
  return <div data-sensitivity-results="all-23-settings">
    {families.map(family => <details id={`sensitivity-${family.id}`} className={styles.details} key={family.id}>
      <summary>{family.title}</summary>
      <p className={styles.tableNote}>{family.note}</p>
      {data.cells.filter(cell => cell.family === family.id).map(cell => <details id={`sensitivity-${cell.id}`} className={styles.details} key={cell.id}>
        <summary>{settingTitle(cell)}</summary>
        <p className={styles.tableNote}>True gain: {points(cell.delta)} points. Switching requires more than {100 * cell.tau} points, so a switch is {cell.switchKind} here. Approach 1’s average final estimate: {points(cell.finalMean)} points; bias: {points(cell.bias)} points.</p>
        <div className={styles.tableWrap} role="region" aria-label={`Complete results: ${settingTitle(cell)}`} tabIndex={0}>
          <table>
            <caption>2,000 evaluations per approach. Brackets show pointwise 95% Monte Carlo intervals. They describe simulation precision, not production risk.</caption>
            <thead><tr><th scope="col">Approach</th><th scope="col">{cell.switchKind === "correct" ? "Correct switch" : "Incorrect switch"}</th><th scope="col">Correct evidence-hold</th><th scope="col">Incorrect evidence-hold</th><th scope="col">Inconclusive</th><th scope="col">Mean groups used</th></tr></thead>
            <tbody>{cell.rows.map(row => <tr key={row.method} data-sensitivity-row={`${cell.id}:${row.method}`}>
              <th scope="row">Approach {row.number}: {methodNames[row.number - 1]}</th>
              <RateCell metric={row.switch} /><RateCell metric={row.correctHold} /><RateCell metric={row.falseHold} /><RateCell metric={row.inconclusive} /><td>{row.meanContexts.toFixed(2)}</td>
            </tr>)}</tbody>
          </table>
        </div>
      </details>)}
    </details>)}
    <p className={styles.tableNote}>Settings reuse outcomes or random draws and are not independent replications. At the +2-point boundary, “correct evidence-hold” follows the stated operational classification; it does not establish that the true gain is strictly below the requirement. Refusing to decide is not counted as a correct conclusion.</p>
  </div>;
}

export function MissingnessComparison() {
  const selected = ["missing_f05_s05", "missing_f20_s05", "missing_f30_s05", "missing_f40_s05"];
  const methods = ["row_fixed", "context_fixed", "context_adjusted"];
  return <figure className={styles.comparisonFigure} aria-labelledby="missingness-comparison-title">
    <div className={styles.figureKicker}>Missing grades <span>Incorrect switches · % of tests</span></div>
    <h3 id="missingness-comparison-title">The risk changes with which grades go missing</h3>
    <p className={styles.figureNote}>B is truly four points worse. Successful grades have a 5% chance of going missing; the rows vary that probability for failures. Switching requires more than a two-point gain.</p>
    <div className={styles.comparisonScroll} role="region" aria-label="Incorrect switches as failure grades increasingly go missing" tabIndex={0}>
      <table className={`${styles.comparisonTable} ${local.compactTable}`}>
        <thead><tr><th scope="col">Failure grades missing</th><th scope="col">Approach 1<small>One check; ignore groups</small></th><th scope="col">Approach 3<small>One check; account for groups</small></th><th scope="col">Approach 5<small>Groups; five adjusted checks</small></th></tr></thead>
        <tbody>{selected.map(id => {
          const cell = data.cells.find(item => item.id === id)!;
          return <tr key={id}><th scope="row"><strong>{100 * (cell.failed_grade_loss ?? 0)}%</strong>{cell.failed_grade_loss === cell.successful_grade_loss && <small>Equal loss for failures and successes</small>}</th>{methods.map(method => {
            const row = cell.rows.find(item => item.method === method)!;
            return <td key={method} data-missingness-value={`${id}:${method}`}><span className={local.value}>{percent(row.switch.estimate)}</span></td>;
          })}</tr>;
        })}</tbody>
      </table>
    </div>
    <figcaption>The same 2,000 underlying tests are evaluated under each missingness setting. These are selected settings, not a universal safe cutoff; the full comparison also varies missing successful grades. <a href="#sensitivity-details">All settings, all six approaches and uncertainty intervals →</a></figcaption>
  </figure>;
}
