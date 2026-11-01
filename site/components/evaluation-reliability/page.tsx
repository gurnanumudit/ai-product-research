import { ArticleIndex } from "@/components/article/article-index";
import results from "@/content/evaluation-reliability-results.json";
import base from "@/components/article/page.module.css";
import styles from "./page.module.css";
import { MissingnessComparison, SensitivityResults } from "./sensitivity-results";


const entries = [
  { id: "introduction", title: "More correct answers. Should we switch?" },
  { id: "pitfalls", title: "Three reasons to look closer" },
  { id: "experiment-setup", title: "Study design: simulate a known difference" },
  { id: "worked-example", title: "What counted as a reason to switch?" },
  { id: "findings-at-a-glance", title: "The three scenarios we examine" },
  { id: "finding-1", title: "1. Grouping and repeated checking need separate safeguards" },
  { id: "finding-2", title: "2. Missing failures can reverse the conclusion" },
  { id: "finding-3", title: "3. Stronger safeguards can delay genuine improvements" },
  { id: "application", title: "Which approach should you use?" },
  { id: "limitations", title: "Scope and limitations" },
  { id: "conclusion", title: "The bottom line" },
  { id: "appendix", title: "Appendix" },
  { id: "references", title: "References" },
];
const world = (id: string) => results.worlds.find(w => w.id.startsWith(`${id}_`))!;
const pct = (n: number) => `${n.toFixed(2)}%`;

const displayMethods = [
  { id: "row_fixed", number: 1, name: "One check", detail: "Treat questions as independent", explanation: "Treat every question as independent evidence. Compare A and B once, after all 1,000 questions." },
  { id: "row_peek", number: 2, name: "Five checks", detail: "Treat questions as independent; no adjustment", explanation: "Use the same calculation as Approach 1, but check after 200, 400, 600, 800 and 1,000 questions. Make no adjustment for these extra opportunities to decide." },
  { id: "context_fixed", number: 3, name: "Related questions, one check", detail: "Account for groups; decide at the end", explanation: "Compare A and B once at the end, as in Approach 1, but account for questions that share a policy, document or other context when calculating uncertainty." },
  { id: "context_peek", number: 4, name: "Related questions, five checks", detail: "Account for groups; no repeated-check adjustment", explanation: "Account for related questions, as in Approach 3, and check at the same five points as Approach 2. Do not adjust for repeated checking." },
  { id: "context_adjusted", number: 5, name: "Related questions, five adjusted checks", detail: "Account for groups; stronger evidence at each check", explanation: "Start with Approach 4, but require stronger evidence at each check to account for the five opportunities to decide." },
  { id: "integrity_adjusted", number: 6, name: "Adjusted checks plus record checks", detail: "Also check for duplicate, missing or invalid records", explanation: "Start with Approach 5, remove identical duplicate records, and withhold a decision at any checkpoint with missing or invalid records." },
];
const labels = Object.fromEntries(displayMethods.map(method => [method.id, `Approach ${method.number}: ${method.name}`]));

function DecisionFigure({ id, number, title, note }: { id: string; number: string; title: string; note: string }) {
  const scenario = world(id);
  const highlights: Record<string, { label: string; tone: string }> = id === "w04" ? {
    row_peek: { label: "Most unjustified switches", tone: styles.rankRisk },
    context_adjusted: { label: "Fewest unjustified switches · tied", tone: styles.rankFavorable },
    integrity_adjusted: { label: "Fewest unjustified switches · tied", tone: styles.rankFavorable },
  } : id === "w09" ? {
    row_peek: { label: "Most unjustified switches", tone: styles.rankRisk },
    context_adjusted: { label: "Fewest false switches among Approaches 1–5", tone: styles.rankNeutral },
    integrity_adjusted: { label: "Zero switches · all tests unresolved", tone: styles.rankNeutral },
  } : {
    row_peek: { label: "Most genuine improvements detected", tone: styles.rankFavorable },
    context_adjusted: { label: "Fewest genuine improvements detected · tied", tone: styles.rankRisk },
    integrity_adjusted: { label: "Fewest genuine improvements detected · tied", tone: styles.rankRisk },
  };
  return <figure className={`${styles.comparisonFigure} ${scenario.trueGain > 2 ? styles.higherBetter : styles.lowerBetter}`} data-rate-direction={scenario.trueGain > 2 ? "higher-better" : "lower-better"} aria-labelledby={`figure-${number}`}>
    <div className={styles.figureKicker}>Figure {number} <span>Tests recommending a switch · %</span></div>
    <h3 id={`figure-${number}`}>{title}</h3>
    <p className={styles.figureNote}>{note}</p>
    <div className={styles.comparisonScroll} role="region" aria-label={`Figure ${number}: switch recommendations`} tabIndex={0}>
      <table className={`${styles.comparisonTable} ${styles.switchTable}`}>
        <thead><tr><th scope="col">Approach</th><th scope="col">Tests recommending a switch<div className={styles.miniAxis} aria-hidden="true"><span>0</span><span>25</span><span>50</span><span>75</span><span>100%</span></div></th></tr></thead>
        <tbody>{displayMethods.map(method => {
          const row = scenario.rows.find(r => r.method === method.id)!;
          const value = scenario.trueGain > 2 ? row.correct : row.falseShip;
          const highlight = highlights[method.id];
          return <tr key={method.id}><th scope="row"><strong>Approach {method.number}: {method.name}</strong><small>{method.detail}</small></th>
            <td className={styles.decision0} data-switch-value={value}><span className={styles.cellValue}>{pct(value)}</span><div className={styles.barTrack} aria-hidden="true"><span className={styles.barFill} style={{width: `${value}%`}} /></div>{highlight && <span className={`${styles.rankLabel} ${highlight.tone}`}>{highlight.label}</span>}</td>
          </tr>;
        })}</tbody>
      </table>
    </div>
    {id === "w09" && <p className={styles.figureWarning}>Approach 6 leaves all 2,000 tests unresolved. It does not identify which version is better.</p>}
    <figcaption>Each row analyzes the same 2,000 simulated tests. Percentages describe switch recommendations, not AI answer accuracy. Labels identify the highest and lowest observed rates here, not an overall winner or a statistically established ranking. Figures 01–03 use the same six approaches and 0–100% scale. <a href={`#results-${scenario.id}`}>Other decisions and uncertainty estimates for this scenario →</a></figcaption>
  </figure>;
}

function FullResults() {
  return <div>{results.worlds.map(w => <details id={`results-${w.id}`} className={styles.details} key={w.id}>
    <summary>{w.name} · true gain {w.trueGain > 0 ? "+" : ""}{w.trueGain} points</summary>
    <div className={styles.tableWrap} role="region" aria-label={`Results for ${w.name}, true gain ${w.trueGain} points`} tabIndex={0}><table>
      <caption>2,000 simulations per row. Brackets are pointwise 95% Monte Carlo intervals.</caption>
      <thead><tr><th scope="col">Approach</th><th scope="col">False switch</th><th scope="col">False evidence-hold</th><th scope="col">Correct decision</th><th scope="col">Inconclusive</th><th scope="col">Mean groups used</th></tr></thead>
      <tbody>{w.rows.map(r => <tr key={r.method}><th scope="row">{labels[r.method]}</th><td>{pct(r.falseShip)}<small>[{r.falseShipLow.toFixed(2)}, {r.falseShipHigh.toFixed(2)}]</small></td><td>{pct(r.falseHold)}</td><td>{pct(r.correct)}<small>[{r.correctLow.toFixed(2)}, {r.correctHigh.toFixed(2)}]</small></td><td>{pct(r.inconclusive)}</td><td>{r.meanContexts.toFixed(2)}</td></tr>)}</tbody>
    </table></div>
  </details>)}</div>;
}

export function EvaluationReliabilityArticle() {
  return <div className={`${base.page} ${styles.page}`}>
    <a className={base.skip} href="#introduction">Skip to article</a>
    <header className={base.siteHeader}><a className={base.wordmark} href="/">Mudit Gurnani</a><nav aria-label="Site navigation"><a href="/">Research</a><a href="#appendix">Methods & results</a></nav></header>
    <main>
      <header className={base.hero}>
        <p className={base.eyebrow}>AI evaluation · Simulation study</p>
        <h1>How to avoid false confidence<br className={styles.titleBreak} /> in AI evaluations</h1>
        <p className={base.subtitle}>The new AI answers more test questions correctly. Is that enough reason to switch? We used simulations to measure how often different evaluation approaches make the right decision.</p>
        <p className={base.byline}>Mudit Gurnani <span>·</span> <time dateTime="2026-09-30">September 30, 2026</time></p>
        <p className={base.resourceLine}><a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/evaluation-reliability" target="_blank" rel="noreferrer">Research code ↗</a><span> · </span><a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/evaluation-reliability-sensitivity" target="_blank" rel="noreferrer">Assumption checks ↗</a><span> · </span><a href="#appendix">Methods and complete results ↓</a></p>
      </header>
      <figure className={base.cover}>
        <img src="/research-assets/evaluation-reliability/evaluation-confidence-cover.png" width="1774" height="887" alt="A magnifying glass reveals gaps among grouped pairs of marks on textured evaluation sheets." fetchPriority="high" />
        <figcaption>Looking beyond the score to examine the evidence behind it. AI-generated editorial illustration, not experimental data.</figcaption>
      </figure>
      <div className={base.layout}><ArticleIndex entries={entries} /><article className={base.article}>
        <section id="introduction" className={base.section}><h2>More correct answers. Should we switch?</h2><div className="prose">
          <p>Imagine your team uses an AI assistant to answer customer questions. You change its instructions and test both versions on the same 100 questions.</p>
          <p>The current version answers 70 correctly; the new version answers 75. That is a five-percentage-point improvement on this test. Is it enough evidence to switch?</p>
          <p>The new version could be better, or its lead could be due to chance. We need enough evidence to avoid an unnecessary switch without delaying a useful improvement.</p>
          <p>Our research asks: <strong>when does an apparent improvement provide enough evidence to switch?</strong> We examined both the mistakes a decision rule can make and the useful improvements it can leave unconfirmed.</p>
        </div></section>

        <section id="pitfalls" className={base.section}><h2>Three reasons to look closer</h2><div className="prose">
          <ul className={styles.crispList}>
            <li><strong>Related questions:</strong> Five questions about one refund policy may share the same failure mode. Treating them as independent evidence can overstate certainty.</li>
            <li><strong>Repeated checking:</strong> Inspecting results after every batch and stopping at the first apparent win creates more opportunities to act on chance.</li>
            <li><strong>Missing results:</strong> If the new version’s unsuccessful outcomes are more likely to lose their recorded grades, its remaining results look better than they should.</li>
          </ul>
        </div></section>

        <section id="experiment-setup" className={base.section}><h2>Study design: simulate a known difference</h2><div className="prose">
          <p>We simulated evaluation results with a known underlying performance difference. This let us measure whether an analysis reached the right conclusion, rather than infer which version was truly better from the same test we were evaluating.</p>
          <p>A represented the current version and B the new version. We defined three performance scenarios:</p>
          <ul className={styles.crispList}>
            <li><strong>B is worse:</strong> its success rate is 4 percentage points lower than A’s.</li>
            <li><strong>B has a small advantage:</strong> its success rate is 2 points higher.</li>
            <li><strong>B has a substantial advantage:</strong> its success rate is 10 points higher.</li>
          </ul>
          <p>Each simulated test contained correct or incorrect outcomes for A and B on 1,000 questions, arranged in 200 groups of five. We also varied the available records, including whether all grades were present or some were missing.</p>
          <p>Each comparison used <strong>2,000 simulated tests</strong>. Within a setting, the underlying performance difference stayed fixed while the recorded results varied by chance. To isolate the effect of a changed assumption, comparisons across settings reused outcomes or random draws where possible.</p>
          <p>We analyzed <strong>every test six ways</strong>. All six approaches received the same recorded results; only the way they used that evidence to make a decision changed. We then counted how often each approach recommended switching.</p>
          <ul className={styles.crispList}>{displayMethods.map(method => <li key={method.id} id={`analysis-approach-${method.number}`}><strong>Approach {method.number}: {method.name}.</strong> {method.explanation}</li>)}</ul>
          <p>We also checked how the findings changed when grades went missing less often, questions were more or less related, and the improvement required to switch was smaller or larger. This let us see how much each result depended on our assumptions.</p>
          <p className={styles.readingNote}>Technical details: <a href="#simulation-details">simulation design and data conditions</a> · <a href="#duplicate-details">duplicate-record stress test</a> · <a href="#reproducibility-details">reproducibility checks</a>.</p>
        </div></section>

        <section id="worked-example" className={base.section}><h2>What counted as a reason to switch?</h2><div className="prose">
          <p>Our main comparisons use an illustrative requirement: B must improve success by <strong>more than 2 percentage points</strong>. Each analysis estimates the improvement and a confidence interval, a range expressing uncertainty around that estimate. Each simulated test gets its own interval; the 2,000 repetitions measure how often the resulting decision is right or wrong.</p>
          <ul className={styles.crispList}>
            <li><strong>Switch:</strong> the entire interval is above +2 points.</li>
            <li><strong>Gain below the requirement:</strong> the entire interval is below +2 points.</li>
            <li><strong>Not enough evidence:</strong> the interval includes or touches +2 points.</li>
          </ul>
          <p className={styles.readingNote}>See <a href="#ci-example">how one test’s confidence interval is calculated</a> and the <a href="#interval-details">formal interval and decision rules</a>.</p>
          <p>A single-check approach waited for all 1,000 questions. A five-check approach examined cumulative results after 200, 400, 600, 800 and 1,000 questions, retaining the first conclusive decision. Each check includes more questions. These checks do not generate new attempts at previous questions.</p>
          <p><strong>Adjusted checks</strong> required stronger evidence to account for the five decision opportunities. <strong>Unadjusted checks</strong> reused the single-check standard each time. The <a href="#adjustment-details">adjustment method</a> is explained in the appendix. A separate <strong>record check</strong> required an outcome for both versions on every question expected at that checkpoint; a missing grade is not a recorded failure.</p>
        </div></section>

        <section id="findings-at-a-glance" className={base.section}><h2>The three scenarios we examine</h2>
          <div className={styles.scenarioBrief}>
            <div><span>01</span><p><strong>A small gain, complete results</strong>B is +2 points better; switching requires more than +2. Can the analysis avoid an unjustified switch?</p></div>
            <div><span>02</span><p><strong>A worse version, missing grades</strong>B’s true gain is −4 points; its unsuccessful outcomes are more likely to disappear. Can the analysis resist the misleading results?</p></div>
            <div><span>03</span><p><strong>A large gain, complete results</strong>B is +10 points better. Can the analysis confirm a worthwhile improvement?</p></div>
          </div>
          <p className={styles.readingNote}>All three include related questions. The figures show how often each approach recommends switching across 2,000 simulated tests per scenario. They do not show answer accuracy.</p>
        </section>

        <section id="finding-1" className={base.section}><h2>1. Grouping and repeated checking need separate safeguards</h2><div className="prose">
          <p>B’s true advantage is exactly +2 points, so it does not exceed our switching requirement. Records are complete.</p>
          <ul className={styles.crispList}>
            <li><strong>Approach 1 → Approach 3:</strong> accounting for related questions, while keeping one final check, reduced mistaken switches from 6.15% to 2.55% of the 2,000 tests.</li>
            <li><strong>Approach 3 → Approach 4:</strong> checking five times without an adjustment raised mistaken switches to 7.20%, despite accounting for related questions.</li>
            <li><strong>Approach 4 → Approach 5:</strong> adjusting those five checks reduced mistaken switches from 7.20% to 1.75%.</li>
          </ul>
        </div><DecisionFigure id="w04" number="01" title="Two safeguards, two sources of false confidence" note="True gain: +2 points · Complete records · Lower is better: switching is not justified under the greater-than-2 rule." />
          <p className={styles.findingTakeaway}>Approach 2 had the most unjustified switches (17.05%); Approaches 5 and 6 tied for the fewest (1.75%). When checking repeatedly, accounting for related questions alone was not enough; the extra decision opportunities also needed an adjustment. <a href="#contrast-details">Uncertainty in these comparisons →</a></p>
          <div className="prose">
            <p><strong>How much does relatedness matter?</strong> Across our weaker-to-stronger relatedness settings, Approach 2’s mistaken-switch rate rose from <strong>8.30% to 25.50%</strong>. Approach 3 stayed around 2–3%, and Approach 5 around 1–2%. The small fluctuations in those latter rates do not establish meaningful differences.</p>
            <p>In these tests, treating related questions as independent produced more mistaken switches as their results became more related. Accounting for groups remained useful across the range we tested. <a href="#sensitivity-relatedness">Relatedness settings and all six approaches →</a></p>
          </div>
        </section>

        <section id="finding-2" className={base.section}><h2>2. Missing failures can reverse the conclusion</h2><div className="prose">
          <p>Now B is truly four points worse. The question is whether missing grades can make it look better.</p>
          <p>When successful and unsuccessful answers each had a 5% chance of losing their grades, Approach 1 still estimated an average <strong>four-point disadvantage</strong> for B. It made no mistaken switches in these 2,000 tests. Missing data reduced the evidence available, but this random-loss example did not systematically favor B.</p>
          <p>We then made failed answers more likely to lose their grades, keeping the loss rate for successful answers at 5%. The table shows how often each approach recommended switching to the worse version.</p>
        </div><MissingnessComparison />
          <div className="prose">
            <p>At the severe 40%/5% setting, Approach 1 estimated an average <strong>+7.34-point advantage</strong> for B, reversing the true −4-point difference. Approach 5 still made mistaken switches in <strong>11.65%</strong> of tests. Stronger evidence requirements reduced the number of switches; they did not restore the missing information.</p>
            <p>These probabilities are stress-test assumptions, not measured product failure rates. With 10% of successful grades missing instead of 5%, the rates changed again. There is no universal “safe” missingness percentage in these results. <a href="#sensitivity-missingness">All missingness settings and uncertainty →</a></p>
          </div>
          <DecisionFigure id="w09" number="02" title="How the six approaches handle the severe missing-data case" note="True gain: −4 points · Failed grades missing: 40%; successful grades missing: 5% · Every switch is incorrect." />
          <div className="prose"><p>Approach 6 left every test unresolved in all the settings with missing grades, including the equal 5%/5% case. It avoided mistaken switches by withholding every decision. That does not make its complete-record rule suitable for every incomplete evaluation.</p></div>
          <p className={styles.findingTakeaway}>Investigate why results are missing, not just how many. Selective loss can make a worse version look better, and a more cautious calculation cannot repair that evidence.</p>
        </section>

        <section id="finding-3" className={base.section}><h2>3. Stronger safeguards can delay genuine improvements</h2><div className="prose">
          <p>With complete records and a true +10-point gain, we want the analysis to recognize that B clears the switching requirement.</p>
          <p><strong>Approach 2 detected this large improvement most often:</strong> it recommended switching in 93.45% of the 2,000 tests. But in the earlier +2-point scenario, where the gain did not exceed our requirement, it also recommended switching in 17.05% of tests. A high detection rate alone does not establish a better decision method.</p>
          <p>Approaches 4 and 5 both account for related questions. Adding the repeated-check adjustment in Approach 5 reduced confirmed switches from <strong>83.65% to 63.00%</strong>. Unresolved tests increased from <strong>16.25% to 36.95%</strong>.</p>
          <p>The adjustment reduced mistaken switches in the first scenario, but confirmed fewer real improvements here at the same maximum test size. Neither result alone is enough to choose an approach.</p>
        </div><DecisionFigure id="w05" number="03" title="Greater caution leaves more improvements unconfirmed" note="True gain: +10 points · Complete records · Higher is better: switching is justified if the test establishes the gain." />
          <p className={styles.findingTakeaway}>Approach 2 detected the most genuine improvements (93.45%); Approaches 5 and 6 tied for the fewest (63.00%). This reverses their ranking in the first scenario. Choosing an approach requires considering both mistaken switches and missed improvements. <a href="#contrast-details">Additional estimates →</a></p>
          <div className="prose">
            <p>We also varied the improvement required to switch. With the same genuine ten-point gain and the same test results, Approach 5 confirmed a switch in <strong>74.60%</strong> of tests when the requirement was more than one point, <strong>63.00%</strong> at more than two, and <strong>26.30%</strong> at more than five.</p>
            <p>Requiring stronger statistical evidence and requiring a larger business improvement are different choices. Raising the improvement requirement asks the test to establish more; it does not make the statistical method better.</p>
            <p>A genuine two-point gain makes this distinction clear: it is worthwhile under a one-point requirement, exactly at the boundary under two, and below the requirement under five. Set that requirement before interpreting which decisions count as correct. <a href="#sensitivity-threshold">All three switching requirements →</a></p>
          </div>
        </section>

        <section id="application" className={base.section}><h2>Which approach should you use?</h2><div className="prose">
          <p>In a real evaluation, you do not know the true improvement. Choose the approach before seeing the results, based on how the test is designed and what a mistaken or delayed switch would cost.</p>
          <ul className={styles.crispList}>
            <li><strong>Can you wait until the test ends?</strong> For related questions like those studied here, Approach 3 is a reasonable starting point: account for the groups and make one planned decision.</li>
            <li><strong>Do you need early decisions?</strong> Use an approach designed for repeated checking. Approach 5 is our tested example, not a proven best option; we did not compare it with other sequential methods.</li>
            <li><strong>Are the records trustworthy?</strong> Reconcile the intended questions with the recorded grades. Investigate missing results and duplicates before comparing scores. Check whether failures could disappear more often than successes; the overall missing percentage alone cannot answer that question. Approach 6’s strict refusal rule is not a substitute for investigating the cause.</li>
            <li><strong>What would a wrong decision or a delay cost?</strong> Choose a common time horizon, such as the next month. Estimate the loss from an unjustified switch and the value forgone by delaying a useful update. Set the minimum worthwhile improvement, any non-negotiable risk limits and the testing budget upfront. If the evidence is still insufficient when that budget is exhausted, report the uncertainty. Do not extend the test just to obtain a favorable result.</li>
          </ul>
          <p>You may accept more decision risk for a cheap, reversible switch than for a costly deployment. The analysis should still account for related questions and report uncertainty accurately.</p>
          <p><strong>We have not established an overall winner.</strong> That would require the costs of mistaken switches, delayed improvements and further testing, plus how often different situations occur. Our simulation did not estimate those inputs.</p>
          <p className={styles.readingNote}><a href="#decision-cost-example">Worked example: how different decision costs change the choice between Approaches 3 and 5 →</a></p>
        </div></section>

        <section id="limitations" className={base.section}><h2>Scope and limitations</h2><div className="prose">
          <ul className={styles.crispList}>
            <li><strong>Conditional results:</strong> Relatedness, missing grades and duplicates were simulated, not calibrated to production evaluations. Varying the assumptions shows where the conclusions are sensitive; it does not establish real-world error rates or deployment value.</li>
            <li><strong>Safeguards have limits:</strong> Intervals are approximate; the complete-record rule is deliberately strict. No approach met our error-and-decision targets across every applicable baseline setting. See the <a href="#complete-results">baseline results</a> and <a href="#sensitivity-details">assumption checks</a>.</li>
            <li><strong>Applied demonstration, not a new method:</strong> We stress-tested established statistics, not AI products. Related reading: <a href="https://arxiv.org/html/2411.00640v1">Adding Error Bars to Evals</a>.</li>
          </ul>
        </div></section>

        <section id="conclusion" className={base.section}><h2>The bottom line</h2><div className="prose">
          <p>The assistant that answered 75 questions correctly instead of 70 may be better. To decide whether to switch, we need to know how those questions were selected, whether the records are complete, and whether the estimated gain is large enough to matter.</p>
          <p>Choose the approach before looking at the results. Account for related questions, plan when decisions can be made, and investigate missing records. Consider both mistaken switches and useful improvements left unconfirmed. If the test cannot resolve the choice within the agreed budget, report “not enough evidence yet.”</p>
        </div></section>

        <section id="appendix" className={base.appendix}><p className={base.eyebrow}>Methods and supporting material</p><h2>Appendix</h2><p className={base.appendixIntro}>The methods and tables retain all six approaches: the 15 baseline scenarios, plus the comparisons that vary missingness, relatedness and the switching requirement. Expand only the detail you need.</p>
          <details id="sensitivity-details" className={styles.details}><summary>How the findings change with the assumptions</summary><div className="prose">
            <p>Each setting contains 2,000 evaluations. Missingness comparisons reuse the same underlying outcomes and logging-loss draws; threshold comparisons reuse saved baseline outcomes; relatedness comparisons reuse the same random draws under different dependence settings. These are paired comparisons, not 46,000 independent new experiments.</p>
            <ul>
              <li><strong>Missingness:</strong> failed-grade loss of 5%, 10%, 20%, 30% or 40%, crossed with successful-grade loss of 5% or 10%, plus a complete-record reference. B is truly four points worse. The equal-loss cases are controls; 5% failure loss with 10% success loss reverses the selection direction.</li>
              <li><strong>Switching requirement:</strong> greater than one, two or five points in the three scenarios discussed above. We recomputed the first conclusive decision across every eligible check, then classified it against the new requirement.</li>
              <li><strong>Relatedness:</strong> h = 0.15, 0.30 or 0.45 with a true +2-point gain and complete records. Within-group correlation of paired differences is h² / (0.5 − Δ²): approximately 4.5%, 18.0% and 40.5%. This sweep does not include independence.</li>
            </ul>
            <p>For Approach 1, the first tested failed-grade loss above a 10% mistaken-switch rate was 30% when successful-grade loss was 5%, but 40% when it was 10%. The preceding tested settings had rates of 1.65% and 6.95%, respectively. This brackets crossings on the tested grid; it does not identify a precise or universal safe cutoff.</p>
            <p>Intervals below describe simulation precision, not production risk, and are pointwise rather than simultaneous. “Correct evidence-hold” at the exact +2-point boundary retains the baseline operational convention; it does not prove the effect is strictly below the requirement. The strict record check can decide on a clean earlier prefix, although all tested nonzero-missingness settings here remained unresolved.</p>
            <p><a href="/research-assets/evaluation-reliability/sensitivity-results.json" download>Download the complete sensitivity table data</a> · <a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/evaluation-reliability-sensitivity">Code and reproduction instructions</a> · <a href="#reproducibility-details">Design and verification scope</a></p>
          </div><SensitivityResults /><p className={styles.tableNote}><a href="#finding-1">Return to Finding 1</a> · <a href="#finding-2">Finding 2</a> · <a href="#finding-3">Finding 3 ↑</a></p></details>
          <details id="decision-cost-example" className={styles.details}><summary>Worked example: choosing an approach when mistakes and delays have different costs</summary><div className="prose">
            <p>Suppose a team is choosing between Approach 3 (one final check) and Approach 5 (five adjusted checks). Both account for related questions. This example combines our simulated decision rates with <strong>invented business assumptions</strong>; it is not a measured financial result or a comparison of every approach.</p>
            <h3>1. Define the decision and the costs</h3>
            <p>Use a one-month horizon. Keep the current version whenever the test does not recommend switching. Assume half of proposed updates have a true +2-point gain and half have a +10-point gain, with complete records. We chose this 50/50 mix for the example; the study did not estimate it.</p>
            <ul>
              <li><strong>Unjustified switch: $10,000.</strong> Assume switching when the gain does not clear the more-than-2-point requirement incurs this net loss. A +2-point gain is not a quality regression; the penalty represents a rollout that fails the team’s worthwhile-improvement rule.</li>
              <li><strong>Delayed useful update: $1,000.</strong> Assume keeping the current version for the month when the true gain is +10 points forgoes this much net value.</li>
            </ul>
            <p>In practice, estimate these amounts from rollout and rollback effort, user exposure and the value of improved answers over the same period. Use ranges where evidence is weak. Set safety or contractual limits separately; a low average cost does not override them.</p>
            <h3>2. Combine those assumptions with the decision rates</h3>
            <p>In our complete-record simulations, Approach 3 recommended an unjustified switch in <strong>2.55%</strong> of +2-point tests; Approach 5 did so in <strong>1.75%</strong>. At a true +10-point gain, they failed to recommend switching in <strong>21.70%</strong> and <strong>37.00%</strong>, respectively. The latter includes both unresolved tests and conclusions below the requirement, so it differs from the 36.95% unresolved share.</p>
            <p><strong>Expected loss per proposed update</strong> = chance of an update that does not clear the requirement × false-switch rate × switch loss + chance of a worthwhile update × no-switch rate × delay loss.</p>
            <ul>
              <li><strong>Approach 3:</strong> 0.50 × 0.0255 × $10,000 + 0.50 × 0.2170 × $1,000 = <strong>$236.00</strong>.</li>
              <li><strong>Approach 5:</strong> 0.50 × 0.0175 × $10,000 + 0.50 × 0.3700 × $1,000 = <strong>$272.50</strong>.</li>
            </ul>
            <p><strong>Under these assumptions, Approach 3 has the lower expected loss.</strong> It allows more unjustified switches, but misses fewer useful updates. These are averages across hypothetical future updates, not the cost of one particular decision.</p>
            <h3>3. Check the choice at a higher cost</h3>
            <p>Now raise the assumed loss from an unjustified switch to <strong>$100,000</strong>, leaving everything else unchanged. Expected loss becomes <strong>$1,383.50 for Approach 3</strong> and <strong>$1,060.00 for Approach 5</strong>. Approach 5 is now preferable between these two: preventing an unjustified switch matters more.</p>
            <p>Before choosing in practice, vary both the costs and the assumed frequency of worthwhile updates. Use comparable historical evaluations where available; otherwise examine a range of plausible mixes. If small changes in these assumptions change the preferred approach, the simulation does not support a firm recommendation.</p>
            <h3>4. Account for what this example leaves out</h3>
            <p>This simplified example omits evaluation costs, the value of earlier decisions within the month, other effect sizes and missing-record problems. It uses estimated simulation rates without propagating their uncertainty. A deployment analysis should include those factors and estimate the rates under conditions relevant to the product.</p>
            <p>This example also does not calculate whether more testing is worth the cost. That requires estimating how additional evidence would change decisions and comparing the expected reduction in loss with testing and delay costs. Our study did not estimate that value.</p>
            <p>An approach with fewer mistaken switches can still have a higher expected cost if it delays enough useful updates. The choice in this example depends on the assumed costs and frequency of each kind of update.</p>
            <p><a href="#application">Return to the article’s recommendation ↑</a></p>
          </div></details>
          <details id="ci-example" className={styles.details}><summary>Worked example: one test’s confidence interval</summary><div className="prose">
            <p>This is an illustrative calculation, not a selected simulation result. Suppose one test contains 1,000 questions in 200 independent groups of five. A gets 700 correct and B gets 750 correct: an estimated improvement of 5 percentage points.</p>
            <ol>
              <li><strong>Calculate the difference within each group.</strong> If A gets 3 of 5 correct and B gets 4 of 5, B’s advantage in that group is 20 percentage points. Average the differences across all 200 groups.</li>
              <li><strong>Measure how much those differences vary.</strong> Suppose their sample standard deviation is 20 percentage points. This must come from the group-level results; the totals of 700 and 750 cannot determine it.</li>
              <li><strong>Calculate the standard error.</strong> 20 ÷ √200 ≈ 1.414 percentage points. We use 200 independent groups, not 1,000 independent questions.</li>
              <li><strong>Calculate the approximate 95% interval.</strong> 5 ± 1.96 × 1.414 gives approximately +2.23 to +7.77 points. Its lower end exceeds +2, so the unadjusted analysis recommends switching.</li>
              <li><strong>Adjust for five planned checks.</strong> 5 ± 2.576 × 1.414 gives approximately +1.36 to +8.64 points. This wider interval includes gains below +2, so the adjusted analysis remains inconclusive.</li>
            </ol>
            <p>The outcomes and estimated gain are unchanged. The evidence requirement changes because there are five opportunities to decide. Each simulated test gets its own intervals; the 2,000 repetitions are used to evaluate decision frequencies, not to calculate this interval.</p>
            <p><a href="#worked-example">Return to the decision rule ↑</a></p>
          </div></details>
          <details id="adjustment-details" className={styles.details}><summary>Which method handles repeated checking?</summary><div className="prose"><p>For five planned checks, we used a <strong>Bonferroni adjustment</strong>: a 99% confidence interval at each check rather than 95%. The <a href="https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm">Bonferroni principle</a> divides the nominal error allowance across those decision opportunities, requiring stronger evidence each time.</p><p>This simple adjustment is not necessarily the most efficient. Our intervals remain approximations; adjustment does not repair missing records or account for related questions by itself. For continuous monitoring, <a href="https://doi.org/10.1287/opre.2021.2135">always-valid confidence intervals</a> are another option when their assumptions fit. We did not compare them here.</p><p><a href="#worked-example">Return to the main article ↑</a></p></div></details>
          <details id="simulation-details" className={styles.details}><summary>A. Outcome generation and data conditions</summary><div className="prose"><p>Independent groups contain five paired binary outcomes. Let Δ be the population mean of B − A and d a paired difference. Each group draws C uniformly from −1 and +1 and a common Bernoulli(0.5) value Z. With q = 0.5, the probabilities of d = −1, 0, +1 are (q − Δ − hC)/2, 1 − q, and (q + Δ + hC)/2.</p><p>Differences −1 and +1 map to (A,B) = (1,0) and (0,1); a zero difference maps to (Z,Z). The mean difference is Δ and within-group difference covariance is h². The baseline grid uses h = 0 for independent paired differences and h = 0.30 for grouped scenarios. The relatedness comparison varies h as specified in the assumption-check tables. Even in the independent-difference condition, raw A/B outcomes can share difficulty; independence concerns the paired differences being analyzed.</p><ul><li>Complete logs: one B record per intended question.</li><li>Random loss: each B grade is missing with probability 20%.</li><li>Selective loss: B failures lose grades with probability 40%; B successes, 5%.</li><li>Duplication: every B success produces two identical records with the same question identity.</li></ul><p>All A outcomes and intended identifiers remain available. Naive analyses use observed joined pairs, including duplicate rows. The integrity workflow collapses identical duplicates and declines a decision at a look if that prefix is incomplete or invalid. A later defect does not overturn an earlier valid decision. No workflow sees hidden grades or the population truth.</p><p><a href="#experiment-setup">Return to the main article ↑</a></p></div></details>
          <details id="interval-details" className={styles.details}><summary>B. Decision intervals, monitoring and uncertainty</summary><div className="prose"><p>Question-level methods analyze observed paired differences. Group-level methods analyze the mean observed difference within each nonempty group, giving groups equal weight. Under selective loss, these available-data means need not estimate the intended complete-data target.</p><p>Intervals take the form mean ± z × sample standard deviation / √n. Final-look and unadjusted five-look workflows use z ≈ 1.96. The five-look adjustment uses z ≈ 2.576, allocating a total nominal two-sided error of 0.05 across five planned looks. These remain normal approximations, not finite-sample guarantees.</p><p>Looks occur after 40, 80, 120, 160 and 200 intended groups. The first conclusive decision is final. The result is inconclusive if there are fewer than two usable observations or the estimated variance is zero. We do not treat zero estimated variance as certainty.</p><p>At the exact +2-point truth, switching violates the strict greater-than-2 requirement. An evidence-hold is categorized as a correct operational direction in the archived table because B does not exceed the switching requirement. It does not prove that the true effect is strictly below it: the boundary case is used to assess false switches, not power to establish inferiority.</p><p>Across 2,000 evaluations per scenario, rates have pointwise 95% Wilson Monte Carlo intervals. Paired contrasts use evaluation-level indicator differences and an approximate interval; a conservative Hoeffding fallback is used for zero-variance contrasts. These intervals quantify simulation precision, not external validity, and are not simultaneous guarantees across the complete table.</p><p>The descriptive nonboundary screen required no more than 5% false decisions and at least 70% correct decisions at the available horizon. Meeting either point-estimate threshold is not proof of its population value. No single workflow met both screens in every nonboundary scenario.</p><p><a href="#worked-example">Return to the main article ↑</a></p></div></details>
          <details id="duplicate-details" className={styles.details}><summary>C. Duplicate records and other scenarios</summary><div className="prose"><p>In the deliberately extreme duplicate-success scenario with a true −4-point difference, adding identity-based repair and integrity checks to the adjusted workflow reduced false switches from 26.55% to 0.10%. But only 38.30% of decisions were correct and 61.60% remained inconclusive. This repair uses retained identity information; it does not show that lost outcomes can be recovered or that arbitrary duplication is harmless.</p><p>With complete records, independent question-level differences and a true +10-point gain, adjusted monitoring correctly recommended switching in 86.45% of evaluations. It therefore confirmed more improvements in this setting than in the related-question setting. Conversely, a biased analysis can appear successful when its upward bias happens to favor a genuinely positive effect. Results across all scenarios are needed to interpret a method.</p><p>Separately recoding the final question-level method’s inconclusive outcomes as an operational hold misses 10.05% of worthwhile changes in the complete grouped +10-point scenario. That is a choice to defer, not a false statistical claim that the improvement is absent. This secondary recoding is not included among the six primary workflows below.</p><p><a href="#experiment-setup">Return to the main article ↑</a></p></div></details>
          <details id="reproducibility-details" className={styles.details}><summary>D. Reproducibility and evidence limits</summary><div className="prose"><p>The baseline protocol specified 15 scenarios before their results were observed, with 2,000 evaluations in each. The reporting run was followed by an exact same-seed replay; four scientific output files matched byte for byte. The replay checks reproducibility, not another independent sample.</p><p>Verification included 32 deterministic checks, separate calculations for the first two evaluations in each scenario, and an audit of saved outputs. It was not a second independent implementation of all 30,000 evaluations. The <a href="https://github.com/gurnanumudit/ai-product-research/tree/main/research/evaluation-reliability">public reproduction package</a> includes the simulation code, tests, frozen outcomes, seeds and instructions for checking these results. The <a href="https://github.com/gurnanumudit/ai-product-research/blob/main/research/evaluation-reliability/PROVENANCE.md">provenance notes</a> distinguish the original study from publication checks.</p><p>The 23 assumption-check settings are exploratory: their grid was chosen after the baseline findings were known, then frozen before execution. They reuse outcomes or random draws and do not constitute an additional independent sample. All five baseline anchors matched exactly. Verification included nine deterministic tests, checks of every threshold trajectory, separate regeneration of the first two evaluations per setting, and audits of saved counts, intervals and paired comparisons. It was not an independent regeneration of every missingness and relatedness evaluation. The <a href="#sensitivity-details">assumption-check tables and downloadable data</a> retain every setting rather than only those highlighted in the article.</p><p>No model or provider calls were made by the simulation. We did not measure researcher time, the cost of agent assistance, user impact or the prevalence of logging faults. The absence of model calls in the simulation does not mean the research had no cost.</p><p><a href="#experiment-setup">Return to the main article ↑</a></p></div></details>
          <details id="contrast-details" className={styles.details}><summary>Additional estimates behind the main findings</summary><div className="prose"><p>In the complete grouped +2-point scenario, adjusting the five checks reduced false switches by 5.45 percentage points, with a paired 95% Monte Carlo interval of 4.45 to 6.45 points. In the independent-difference +2-point scenario, unadjusted repeated checking raised false switches from 2.05% to 7.60%.</p><p>In the complete grouped +10-point scenario, the adjustment reduced correct switches by 20.65 percentage points, with a paired 95% Monte Carlo interval of 18.88 to 22.42 points. Mean groups used increased from 116.18 to 150.98, including unresolved tests at the full horizon. These are evidence counts, not measured token or dollar costs. The strict missingness check left all tests unresolved in all six baseline missing-grade scenarios, and in every nonzero-missingness setting in the assumption checks.</p><p><a href="#finding-1">Return to the main article ↑</a></p></div></details>
          <details id="complete-results" className={styles.details}><summary>Complete baseline results: all 15 scenarios</summary><p className={styles.tableNote}>“Correct decision” combines correct switches and correct evidence-holds under the specified threshold rule. At a true +2-point gain, read the <a href="#interval-details">boundary caveat</a>. Expand a scenario; wide tables scroll horizontally.</p><FullResults /><p className={styles.tableNote}><a href="#finding-1">Return to Finding 1</a> · <a href="#finding-2">Finding 2</a> · <a href="#finding-3">Finding 3 ↑</a></p></details>
        </section>
        <section id="references" className={base.references}><h2>References</h2><ol>
          <li>Miller, E. (2024). <a href="https://arxiv.org/html/2411.00640v1">Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations</a>. Pairing, shared contexts and evaluation uncertainty.</li>
          <li>Johari, R., Koomen, P., Pekelis, L., and Walsh, D. (2021). <a href="https://doi.org/10.1287/opre.2021.2135">Always Valid Inference: Continuous Monitoring of A/B Tests</a>. Background on monitoring; our finite-look adjustment is not their always-valid procedure.</li>
          <li>Fabijan, A., et al. (2019). <a href="https://www.microsoft.com/en-us/research/publication/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments-a-taxonomy-and-rules-of-thumb-for-practitioners/">Diagnosing Sample Ratio Mismatch in Online Controlled Experiments</a>. Motivation for investigating measurement pipelines, not evidence for our assumed loss rates.</li>
          <li>NIST/SEMATECH. <a href="https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm">Bonferroni’s method</a>. The principle behind allocating error across a fixed set of checks.</li>
        </ol></section>
      </article></div>
    </main><footer className={base.footer}><span>Independent research by Mudit Gurnani</span><a href="#introduction">Back to introduction ↑</a></footer>
    <script src="/research-assets/evaluation-reliability/appendix-navigation.js" defer />
  </div>;
}
