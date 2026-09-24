import base from "@/components/article/page.module.css";
import styles from "./page.module.css";

const components = [
  ["M", "Method judgment", "From direct arithmetic to choosing and justifying a non-routine method."],
  ["D", "Dependent reasoning", "From one result to interacting stages, iteration and conditional planning."],
  ["I", "Data integration", "From one table to linked transformations, sources and conflicting data structures."],
  ["V", "Validation", "From returning a number to checking robustness, assumptions and sensitivity."],
];
const examples = [
  {band:"Easy", range:"0–2", title:"Weight the tax rate", task:"Day-weight the tax rates within February 2022.", score:[0,1,1,0], id:"25/q32", why:"One intermediate calculation and a routine transformation."},
  {band:"Medium", range:"3–5", title:"Calculate the tax charge", task:"Combine monthly profits with day-weighted tax-rate changes.", score:[0,2,2,0], id:"25/q33", why:"Dependent stages and interacting transformations."},
  {band:"Hard", range:"6–8", title:"Forecast cash tax paid", task:"Track expiring loss pools, use losses oldest-first, and apply payment lags.", score:[1,3,2,0], id:"25/q41", why:"A conventional method plus an interacting, conditional chain."},
];
const anchors = [
  ["M · Method", "Direct arithmetic, counting, filtering or a descriptive aggregate", "One named standard method or conventional transformation", "Combine methods or make a bounded consequential method choice", "Design and justify a non-routine method or competing assumptions"],
  ["D · Dependence", "One result, or independent parallel results", "One meaningful intermediate feeds the result", "Two or more dependent stages, or branch-dependent analysis", "Interacting stages requiring iteration, reconciliation or conditional planning"],
  ["I · Integration", "Named columns in one table", "Routine missing values, encoding, a derived variable or grouping", "Interacting transformations, time alignment, cross-grain grouping or a join", "Nontrivial multi-source or entity integration with conflicting units or grains"],
  ["V · Validation", "Return the requested numbers or labels", "Apply a threshold, report model error or interpret a standard diagnostic", "Compare robustness or validate assumptions with analytical consequences", "Independently test reliability, uncertainty or sensitivity across plausible choices"],
];
export function DifficultyMethod() {
  return <div id="difficulty-definition" className="prose">
    <p>Easy means mostly direct calculations; medium means several linked steps; hard means more complex, interacting steps, often with conditions to track. We assigned these labels from the work required, not the models’ scores.</p>
    <p>Imagine the same shop, with increasingly complex questions (illustrative examples):</p>
    <ul>
      <li><strong>Easy:</strong> How much did we sell this month?</li>
      <li><strong>Medium:</strong> How much profit remains after discounts, product costs and expenses?</li>
      <li><strong>Hard:</strong> Will we have enough cash for the next three months if customers pay late and a loan repayment is due?</li>
    </ul>
    <p><a href="#difficulty-rubric">Full rubric and benchmark examples</a>.</p>
  </div>;
}

export function DifficultyRubricAppendix() {
  return <section id="difficulty-rubric" className={base.appendixSection}><h3>B. The difficulty rubric</h3>
    <div className="prose"><p>The rubric was frozen on September 14 and rates the work required, not model performance. Four scores from 0 to 3 determine the difficulty band.</p></div>
    <div className={styles.rubricComponents}>{components.map(([code,title,description]) => <div key={code}><span>{code}</span><h3>{title}<small>0–3 points</small></h3><p>{description}</p></div>)}</div>
    <div className={styles.rubricEquation}>M + D + I + V <span>→</span> difficulty score <small>0–12 points total</small></div>
    <details className={styles.chartDetails}><summary>The full 0–3 scoring anchors</summary><div className={styles.resultsTable}><table><caption>Content rubric frozen September 14, 2026. Multiple independent outputs do not count as a dependent reasoning chain.</caption><thead><tr><th scope="col">Component</th>{[0,1,2,3].map(n=><th key={n} scope="col">{n} points</th>)}</tr></thead><tbody>{anchors.map(([name,...levels])=><tr key={name}><th scope="row">{name}</th>{levels.map(level=><td key={level}>{level}</td>)}</tr>)}</tbody></table></div></details>
    <h3 className={styles.methodSubhead}>Same workbook. Different analytical demands.</h3>
    <div className={styles.difficultyCards}>{examples.map(example => <section key={example.band}><div className={styles.bandBadge}>{example.band}<span>{example.range} points</span></div><h4>{example.title}</h4><p>{example.task}</p><div className={styles.scoreRecipe}>{example.score.map((value,i) => <span key={i}><small>{components[i][0]}</small>{value}</span>)}<strong>= {example.score.reduce((a,b)=>a+b,0)}</strong></div><p className={styles.exampleWhy}>{example.why}</p><small>DSBench {example.id} · high rating confidence</small></section>)}</div>
    <div className="prose"><p>Thresholds are fixed: easy 0–2, medium 3–5, hard 6–8 and very hard 9–12. No very-hard questions were included, and no questions were relabelled to fill a quota. Formatting burden and operational failures do not add difficulty points.</p><p>These are single-reviewer judgments, not publisher labels or a validated scale. The reviewer was not blind to all prior familiarity, but prior model scores were not used to assign difficulty.</p></div>
    <p className={styles.appendixReturn}><a href="#difficulty-definition">Back to the simple difficulty examples ↑</a></p>
  </section>;
}
