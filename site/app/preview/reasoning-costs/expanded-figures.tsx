import styles from "./expanded.module.css";

export type Point = { band: string; modelName: string; effort: string; correct: number; n: number; complete?: boolean; model: number | null; pending: number | null; runtime: number | null };
const models = ["Luna", "Terra", "Sol"];
const efforts = ["None", "Low", "High"];
const bands = ["easy", "medium", "hard"];
const colors: Record<string, string> = { Luna: "#256b63", Terra: "#ad6029", Sol: "#59678e" };
export const percent = (correct: number, n: number) => n > 0 ? `${(100 * correct / n).toFixed(1)}%` : "—";
const title = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const cost = (p: Point) => p.model !== null && p.pending !== null && p.n > 0 ? (p.model + p.pending) / p.n : NaN;
const rate = (p: Point) => 100 * p.correct / p.n;
const signed = (x: number) => `${x > 0 ? "+" : ""}${x.toFixed(1)}`;
const dollars = (x: number | null) => x === null ? "Unresolved" : `$${x.toFixed(4)}`;
const ready = (points: Point[]) => points.length === 27 && points.every(p => p.complete !== false && p.n > 0 && Number.isFinite(cost(p)) && cost(p) > 0);
export function ExactResults({ points }: { points: Point[] }) {
  return <div className={styles.tableWrap}><table className={styles.results}><caption>Exact counts behind the main results. Each denominator is a question count for one configuration.</caption><thead><tr><th>Model</th><th>Reasoning</th>{bands.map(b => <th key={b}>{title(b)}</th>)}</tr></thead><tbody>{models.flatMap(m => efforts.map(e => <tr key={`${m}-${e}`}><th scope="row">{m}</th><td>{e}</td>{bands.map(b => { const p = points.find(p => p.band === b && p.modelName === m && p.effort === e)!; return <td key={b}>{p.correct} / {p.n}</td>; })}</tr>))}</tbody></table></div>;
}
export function ExactCosts({ points }: { points: Point[] }) {
  return <div className={styles.tableWrap}><table className={styles.results}><caption>All 134 matched questions. Dollar totals include every physical attempt assigned to these questions, including original budget failures and authorized retries. Model reservations remain unresolved; runtime is an upper estimate.</caption><thead><tr><th>Configuration</th><th>Difficulty</th><th>Correct / assigned</th><th>Model charges</th><th>Pending model</th><th>Runtime estimate</th></tr></thead><tbody>{points.map(p => <tr key={`${p.band}-${p.modelName}-${p.effort}`}><th scope="row">{p.modelName} · {p.effort}</th><td>{title(p.band)}</td><td>{p.complete === false ? "Incomplete" : `${p.correct} / ${p.n}`}</td><td>{dollars(p.model)}</td><td>{dollars(p.pending)}</td><td>{dollars(p.runtime)}</td></tr>)}</tbody></table></div>;
}
export function ResultsOverview({ points }: { points: Point[] }) {
  return <div className={styles.tableWrap}><table className={`${styles.results} ${styles.overview}`}><caption>Correct-answer delivery · 134 matched questions, including unsuccessful attempts</caption><thead><tr><th>Model</th><th>Reasoning</th>{bands.map(b => <th key={b}>{title(b)}<small>{points.find(p => p.band === b)!.n} questions</small></th>)}</tr></thead>{models.map(model => <tbody key={model}>{efforts.map((effort, i) => <tr key={effort}>{i === 0 && <th rowSpan={3} scope="rowgroup" className={styles.model} style={{ color: colors[model] }}>{model}</th>}<th scope="row">{effort}</th>{bands.map(b => { const p = points.find(p => p.modelName === model && p.effort === effort && p.band === b)!; return <td key={b} title={`${p.correct} correct of ${p.n} assigned`}>{Math.round(rate(p))}%</td>; })}</tr>)}</tbody>)}</table></div>;
}
function Mark({ p, x, y }: { p: Point; x: number; y: number }) {
  const color = colors[p.modelName];
  return p.effort === "High" ? <path d={`M${x},${y - 6}l6,6 -6,6 -6,-6Z`} fill={color} stroke="#fcfbf7" strokeWidth="1.5" /> : <circle cx={x} cy={y} r="5" fill={p.effort === "None" ? "#fcfbf7" : color} stroke={color} strokeWidth="2" />;
}
export function CostSmallMultiples({ points }: { points: Point[] }) {
  if (!ready(points)) return <p id="resource-frontiers">The cost comparison is awaiting complete collection and accounting; missing results are not plotted as zero.</p>;
  const positive = points.map(cost);
  const lo = 10 ** Math.floor(Math.log10(Math.min(...positive)));
  const largest = Math.max(...positive);
  const magnitude = 10 ** Math.floor(Math.log10(largest));
  const hi = [1, 2, 5, 10, 20].map(n => n * magnitude).find(n => n >= largest * 1.08)!;
  const ticks = [lo];
  for (let tick = lo * 10; tick < hi * .999; tick *= 10) ticks.push(tick);
  ticks.push(hi);
  const x = (v: number) => 60 + Math.log10(v / lo) / Math.log10(hi / lo) * 306;
  const y = (v: number) => 220 - v * 1.8;
  const tickLabel = (v: number) => `$${v < .01 ? v.toFixed(3) : v < 1 ? v.toFixed(2) : v.toFixed(0)}`;
  return <figure id="resource-frontiers" className={styles.figure}><header><p className={styles.kicker}>The cost–quality trade-off</p><h3>Cost and success, by difficulty.</h3><p>{bands.reduce((sum, b) => sum + points.find(p => p.band === b)!.n, 0)} matched questions · Higher success, lower cost is better.</p></header><div className={styles.legend}>{models.map(m => <span key={m} style={{ color: colors[m] }}><i style={{ background: colors[m] }} />{m}</span>)}<span className={styles.shapes}>○ None &nbsp; ● Low &nbsp; ◆ High</span></div><div className={styles.panels}>{bands.map(b => {
    const data = points.filter(p => p.band === b);
    const frontier = data.filter(p => !data.some(q => cost(q) <= cost(p) && rate(q) >= rate(p) && (cost(q) < cost(p) || rate(q) > rate(p)))).sort((a, z) => cost(a) - cost(z));
    return <section key={b} className={b === "hard" ? styles.hard : ""}><h4>{title(b)}<small>{data[0].n} questions</small></h4><svg viewBox="0 0 400 266" role="img" aria-labelledby={`${b}-expanded-title ${b}-expanded-desc`}><title id={`${b}-expanded-title`}>{`${title(b)} questions: correct delivery against average model-cost exposure`}</title><desc id={`${b}-expanded-desc`}>{data.map(p => `${p.modelName} ${p.effort}: ${percent(p.correct, p.n)}, $${cost(p).toFixed(4)} per assigned question`).join("; ")}</desc><text x="60" y="17" className={styles.plotLabel}>Correct answers</text>{[0, 25, 50, 75, 100].map(v => <g key={v}><line x1="60" x2="366" y1={y(v)} y2={y(v)} className={styles.grid} /><text x="49" y={y(v) + 5} textAnchor="end">{v}%</text></g>)}{ticks.map(v => <g key={v}><line x1={x(v)} x2={x(v)} y1="40" y2="220" className={styles.vertical} /><text x={x(v)} y="247" textAnchor="middle">{tickLabel(v)}</text></g>)}{models.map(m => <polyline key={m} points={efforts.map(e => data.find(p => p.modelName === m && p.effort === e)!).map(p => `${x(cost(p))},${y(rate(p))}`).join(" ")} stroke={colors[m]} strokeOpacity=".25" fill="none" strokeWidth="1.5" />)}{b === "hard" && <polyline points={frontier.map(p => `${x(cost(p))},${y(rate(p))}`).join(" ")} fill="none" stroke="#373d36" strokeWidth="1.5" strokeDasharray="4 5" />}{data.map(p => <g key={`${p.modelName}-${p.effort}`} data-model={p.modelName} data-effort={p.effort} data-band={p.band} data-correct={p.correct} data-n={p.n} data-cost={cost(p)}><title>{`${p.modelName} · ${p.effort}: ${percent(p.correct, p.n)}; $${cost(p).toFixed(4)} per question`}</title><Mark p={p} x={x(cost(p))} y={y(rate(p))} /></g>)}</svg></section>;
  })}</div><p className={styles.axis}>Average model-cost exposure per question · USD, log scale</p><figcaption>Model cost includes pending reservations and retry costs; it excludes runtime estimates. Dashed line: observed frontier on {points.find(p => p.band === "hard")!.n} hard questions. Shared axes; matched questions. <a href="#appendix-d">Exact values and cost sensitivity</a>.</figcaption></figure>;
}
export function IncrementalValue({ points }: { points: Point[] }) {
  if (!ready(points)) return null;
  return <figure className={styles.figure}><header><p className={styles.kicker}>Low → high</p><h3>What extra reasoning bought</h3></header><div className={styles.tableWrap}><table className={styles.increment}><caption>{bands.reduce((sum, b) => sum + points.find(p => p.band === b)!.n, 0)} matched questions · Success change in percentage points (pp), alongside model-cost exposure change (%).</caption><thead><tr><th>Model</th>{bands.map(b => <th key={b}>{title(b)}</th>)}</tr></thead><tbody>{models.map(m => <tr key={m}><th scope="row" style={{ color: colors[m] }}>{m}</th>{bands.map(b => { const l = points.find(p => p.band === b && p.modelName === m && p.effort === "Low")!, h = points.find(p => p.band === b && p.modelName === m && p.effort === "High")!; const change = rate(h) - rate(l), delta = 100 * (cost(h) / cost(l) - 1); return <td key={b}><strong>{signed(change)} pp</strong><small>{signed(delta)}% cost</small></td>; })}</tr>)}</tbody></table></div><figcaption>A percentage-point gain is not a financial return. “No gain” means no net increase in this sample, not proof that the settings are equivalent.</figcaption></figure>;
}
// Editorial comparison, not an optimized routing rule: trade less spend for lower accuracy.
const lowerCostChoice = (points: Point[], band: string) => points.find(p => p.band === band && p.modelName === "Luna" && p.effort === (band === "hard" ? "High" : "Low"))!;
export function Recommendations({ points }: { points: Point[] }) {
  if (!ready(points)) return null;
  const hardLow = points.find(p => p.band === "hard" && p.modelName === "Luna" && p.effort === "Low")!;
  return <div className={styles.recommendation}><table><caption>Compare cost with accuracy</caption><thead><tr><th scope="col">Question</th><th scope="col">Lower-cost option</th><th scope="col">Highest observed accuracy</th></tr></thead><tbody>{bands.map(band => {
    const group = points.filter(p => p.band === band);
    const lower = lowerCostChoice(points, band);
    const bestCorrect = Math.max(...group.map(p => p.correct));
    const leaders = group.filter(p => p.correct === bestCorrect);
    const target = leaders.reduce((a,b) => cost(a) <= cost(b) ? a : b);
    return <tr key={band}><th scope="row">{title(band)}</th><td><strong>{lower.modelName} · {lower.effort}</strong><span>{Math.round(rate(lower))}% correct</span></td><td><strong>{target.modelName} · {target.effort}</strong><span>{Math.round(rate(target))}% correct{leaders.length > 1 ? " · high tied" : ""}</span></td></tr>;
  })}</tbody></table><p>On hard questions, Luna low was cheaper still, but answered only {Math.round(rate(hardLow))}% correctly. We show Luna high as a compromise between that lower price and Sol low’s higher accuracy.</p><p>Small leads are not dependable rankings: Sol high’s medium-question lead over Terra high was just one correct answer.</p></div>;
}
export function DollarImpact({ points }: { points: Point[] }) {
  if (!ready(points)) return null;
  return <figure className={styles.figure} id="dollar-impact"><header><p className={styles.kicker}>From lower cost to higher accuracy</p><h3>What does the upgrade buy?</h3><p>Three cost–accuracy trade-offs: extra model cost and extra correct answers per 100 questions.</p></header><div className={styles.impactRows}>{bands.map(band => {
    const group = points.filter(p => p.band === band);
    const baseline = lowerCostChoice(points, band);
    const bestCorrect = Math.max(...group.map(p => p.correct));
    const target = group.filter(p => p.correct === bestCorrect).reduce((a,b) => cost(a) <= cost(b) ? a : b);
    const delta = 100*(cost(target)-cost(baseline));
    const gain = rate(target)-rate(baseline);
    return <div key={band} className={styles.impactRow} data-impact-band={band} data-extra-cost-per-100={delta} data-extra-correct-per-100={gain}>
      <div className={styles.impactChoice}><h4>{title(band)}</h4><p>{baseline.modelName} {baseline.effort.toLowerCase()} <span aria-hidden="true">→</span> {target.modelName} {target.effort.toLowerCase()}</p></div>
      <div className={styles.impactNumber}><strong>{`+$${delta.toFixed(2)}`}</strong><span>extra model cost</span><small>${(cost(baseline)*100).toFixed(2)} to ${(cost(target)*100).toFixed(2)}</small></div>
      <div className={styles.impactNumber}><strong>+{Math.round(gain)}</strong><span>correct answers</span><small>per 100 questions</small></div>
    </div>;
  })}</div><figcaption>Rounded comparisons scaled from the same 29 easy, 55 medium and 50 hard questions—not 100 new trials or a forecast. Costs include recorded model charges and pending reservations, but not runtime. <a href="#appendix-d">Calculation and costs</a>.</figcaption></figure>;
}
