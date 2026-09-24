import data from "@/content/evidence-figure-data.json";
import styles from "./evidence-figures.module.css";

const models = [
  { id: "anthropic/claude-sonnet-5", name: "Claude Sonnet 5", color: "#a64b2a" },
  { id: "openai/gpt-5.6-terra", name: "GPT-5.6 Terra", color: "#006d77" },
  { id: "google/gemini-3.8-flash", name: "Gemini 3.8 Flash", color: "#6654a3" },
];
const pct = (n: number) => `${(n * 100).toFixed(1)}%`;
const pp = (n: number) => `${n > 0 ? "+" : ""}${(n * 100).toFixed(1)} pp`;

// Only geometry is SVG. Labels remain normal-size HTML at every viewport.
function Interval({ value, interval, color, source = false, followup = false }: {
  value: number; interval: number[]; color: string; source?: boolean; followup?: boolean;
}) {
  const lo = source ? -.2 : 0, hi = source ? .35 : 1;
  const x = (v: number) => `${(8 + 284 * (v - lo) / (hi - lo)) / 3}%`;
  return <svg aria-hidden="true" className={styles.interval}>
    <line x1={x(lo)} x2={x(hi)} y1="12" y2="12" stroke="#dedfd6" />
    {source && <line x1={x(0)} x2={x(0)} y1="0" y2="24" stroke="#666b62" strokeDasharray="2 3" />}
    <line x1={x(interval[0])} x2={x(interval[1])} y1="12" y2="12" stroke={color} strokeWidth="2" />
    {interval.map((v,i) => <line key={i} x1={x(v)} x2={x(v)} y1="7" y2="17" stroke={color} strokeWidth="2" />)}
    {source && followup ? <rect x={x(value)} transform="translate(-4 0)" y="8" width="8" height="8" fill={color} /> :
      <circle cx={x(value)} cy="12" r="4" stroke={color} strokeWidth="2" fill={source ? "#faf9f5" : color} />}
  </svg>;
}
function Axis({ source = false }: {source?: boolean}) {
  return <div className={styles.axis} aria-hidden="true">{(source ? ["−20", "0", "+35 pp"] : ["0%", "50%", "100%"]).map((v,i) =>
    <span key={v} style={source && i === 1 ? {left: "36.36%"} : undefined}>{v}</span>)}</div>;
}
function Uncertainty({ source = false }: {source?: boolean}) {
  return <figcaption>{source ? "Whiskers retain the original 95% task-bootstrap stability intervals; phases are not pooled." :
    "Whiskers retain the conservative 95% task-level sensitivity intervals. Repeated reviews are not independent tasks; zero observed faulty approvals does not mean zero risk."}
    {" "}<a href="#appendix-d">How to read the uncertainty</a>.</figcaption>;
}
export function EvidenceFigure({ src }: {src:string}) {
  if (src.endsWith("finding-2-evidence-content.svg")) return <figure className={styles.figure} data-evidence-figure="failing">
    <h3>Faulty approvals fell with test evidence</h3>
    <p className={styles.subtitle}>The same 15 benchmark-failing tasks · 30 reviews per setting</p>
    <div className={styles.threePanels}>{models.map(m => <section key={m.id}>
      <h4 style={{color:m.color}}>{m.name}</h4>
      {data.failing.filter(r=>r.model===m.id).map(r=><div className={styles.row} key={r.condition} data-estimate={r.estimate}>
        <div className={styles.rowLabel}><span>{{A:"No report",B:"Factual summary",C:"Full report"}[r.condition]}</span><strong>{pct(r.estimate)}<small>{r.approvals}/{r.n_reviews} reviews</small></strong></div>
        <Interval value={r.estimate} interval={r.interval95} color={m.color}/>
        <span className={styles.srOnly}>95% interval: {pct(r.interval95[0])} to {pct(r.interval95[1])}.</span>
      </div>)}
      <Axis/>
    </section>)}</div>
    <Uncertainty/>
  </figure>;
  if (src.endsWith("finding-1-same-evidence.svg")) return <figure className={styles.figure} data-evidence-figure="passing">
    <h3>Passing fixes were not accepted equally</h3>
    <p className={styles.subtitle}>Same full report · 18 passing tasks · 36 reviews per model</p>
    {models.map(m=>{const r=data.passing.find(r=>r.model===m.id)!;return <div key={m.id} className={styles.row} data-estimate={r.estimate}>
      <div className={styles.rowLabel}><span style={{color:m.color}}>{m.name}</span><strong>{pct(r.estimate)}<small>{r.approvals}/{r.n_reviews} reviews</small></strong></div>
      <Interval value={r.estimate} interval={r.interval95} color={m.color}/>
      <span className={styles.srOnly}>95% interval: {pct(r.interval95[0])} to {pct(r.interval95[1])}.</span>
    </div>;})}
    <Axis/>
    <p className={styles.note}>On the same matched set’s 17 failing tasks, every reviewer approved 0 of 34 reviews.</p>
    <Uncertainty/>
  </figure>;
  if (src.endsWith("finding-3-source-attribution.svg")) return <figure className={styles.figure} data-evidence-figure="source">
    <h3>The early source-label pattern weakened</h3>
    <p className={styles.subtitle}>Approval change from “patch producer” to “separate evaluator.” Positive means more approvals—not necessarily better decisions.</p>
    <div className={styles.twoPanels}>{[...models,{id:"pooled",name:"Three-model mean",color:"#373d36"}].map(m=><section key={m.id}>
      <h4 style={{color:m.color}}>{m.name}</h4>
      {data.source.filter(r=>r.model===m.id).map(r=><div className={styles.row} key={r.phase} data-estimate={r.mean}>
        <div className={styles.rowLabel}><span>{r.phase===1 ? "○ Initial batch" : "■ Follow-up"}</span><strong>{pp(r.mean)}<small>{r.n_tasks} matched tasks</small></strong></div>
        <Interval source followup={r.phase===2} value={r.mean} interval={r.bootstrap_95_interval} color={m.color}/>
        <span className={styles.srOnly}>95% interval: {pp(r.bootstrap_95_interval[0])} to {pp(r.bootstrap_95_interval[1])}.</span>
      </div>)}
      <Axis source/>
    </section>)}</div>
    <p className={styles.note}>Initial batch: 20 tasks; follow-up: 40 different tasks. Each comparison uses complete paired tasks. The mean requires all three models on the same tasks.</p>
    <Uncertainty source/>
  </figure>;
  return null;
}
