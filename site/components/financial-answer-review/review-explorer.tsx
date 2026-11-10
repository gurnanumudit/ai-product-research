"use client";

import { useId, useRef, useState } from 'react';
import { followupRows, reviewMetrics, type ReviewPolicy } from '@/content/financial-review-data';
import styles from './review-explorer.module.css';

const policies: { key: ReviewPolicy; label: string; color: string }[] = [
  { key: 'confidence', label: 'Confidence', color: '#ad512e' },
  { key: 'verification', label: 'Verification', color: '#176b63' },
  { key: 'random', label: 'Random baseline', color: '#77766e' },
];

function CapacityToggle({ capacity, select }: { capacity: number; select: (value: number) => void }) {
  return <fieldset className={styles.budget}><legend>Share of answers you can review</legend><div>{followupRows.map(r => <button key={r.capacity} type="button" aria-pressed={capacity === r.capacity} onClick={() => select(r.capacity)}>{r.capacity}%</button>)}</div></fieldset>;
}

export function ReviewComparison() {
  return <div id="review-budget-explorer">
    <table className={styles.comparisonTable}>
      <caption>Mismatches with FinQA’s answer key selected for review.<br /><span>Each cell shows the count and the percentage of all 347 mismatches caught (recall), not the percentage of review slots.</span></caption>
      <thead><tr><th rowSpan={2} scope="col">Review capacity</th><th rowSpan={2} scope="col">Responses reviewed</th><th colSpan={2} scope="colgroup" style={{textAlign:'center'}}>Mismatches caught</th></tr><tr><th scope="col">Confidence</th><th scope="col">Verification</th></tr></thead>
      <tbody>{followupRows.map(row => <tr key={row.capacity}>
        <th scope="row">{row.capacity}%</th><td>{row.slots}</td>
        <td>{row.confidence} <span className={styles.cellPercent}>({Math.round(100*row.confidence/347)}%)</span></td>
        <td><strong>{row.verification}</strong> <span className={styles.cellPercent}>({Math.round(100*row.verification/347)}%)</span></td>
      </tr>)}</tbody>
    </table>
  </div>;
}

export function ReviewExplorer({ metric = 'accuracy' }: { metric?: 'accuracy' | 'precision' }) {
  const [capacity, select] = useState(20);
  const row = followupRows.find(r => r.capacity === capacity)!;
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const expandedButton = useRef<HTMLButtonElement>(null);
  const accuracy = metric === 'accuracy';
  const min = accuracy ? 60 : 0;
  const x = (n: number) => 55 + (n - 5) / 45 * 605;
  const y = (n: number) => 225 - (n - min) / (100 - min) * 190;
  const title = accuracy ? 'How often did unreviewed answers match the answer key?' : 'How often did a review slot select a mismatch?';
  const chart = () => <svg viewBox="0 0 710 285" role="group" aria-label={`${title} Three strategies at four tested review capacities. Exact values follow the chart.`}>
    {(accuracy ? [60,70,80,90,100] : [0,20,40,60,80,100]).map(t => <g key={t}><line x1="55" x2="660" y1={y(t)} y2={y(t)} stroke="#deded5" /><text x="43" y={y(t)+4} textAnchor="end">{t}%</text></g>)}
    <line x1={x(capacity)} x2={x(capacity)} y1="25" y2="225" stroke="#176b63" strokeDasharray="3 5" opacity=".6" />
    {policies.map(p => <g key={p.key}><polyline fill="none" stroke={p.color} strokeWidth="2.5" strokeDasharray={p.key === 'random' ? '5 4' : undefined} points={followupRows.map(r => `${x(r.capacity)},${y(reviewMetrics(r,p.key)[metric])}`).join(' ')} />{followupRows.map(r => <circle key={r.capacity} cx={x(r.capacity)} cy={y(reviewMetrics(r,p.key)[metric])} r={r.capacity === capacity ? 6 : 3.5} fill={p.color} stroke="#fffefa" strokeWidth="1.5" />)}</g>)}
    {followupRows.map(r => <g key={r.capacity} role="button" tabIndex={0} aria-label={`Compare all strategies at ${r.capacity}% review capacity`} aria-pressed={capacity === r.capacity} onClick={() => select(r.capacity)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(r.capacity); } }} className={styles.chartTarget}>
      <rect x={x(r.capacity)-20} y="24" width="40" height="235" fill="transparent" />
      <text x={x(r.capacity)} y="250" textAnchor="middle" fontWeight={capacity === r.capacity ? 750 : 400}>{r.capacity}%</text>
    </g>)}
    <text x="355" y="278" textAnchor="middle">Share of answers sent for review</text>
  </svg>;

  return <div className={styles.explorer} data-interactive-exhibit="" id={accuracy ? 'review-accuracy-chart' : 'review-precision-chart'}>
    <figure className={styles.figure}>
      <div className={styles.chartHeading}><h4 id={`${id}-title`}>{title}</h4><button ref={expandedButton} type="button" onClick={() => dialog.current?.showModal()}>Expand ↗</button></div>
      <CapacityToggle capacity={capacity} select={select} />
      <div className={styles.legend}>{policies.map(p => <span key={p.key}><i style={{ borderColor: p.color, borderTopStyle: p.key === 'random' ? 'dashed' : 'solid' }} />{p.label}</span>)}</div>
      {chart()}
      <div className={styles.values} aria-live="polite">{policies.map(p => <div key={p.key}><span>{p.label}</span><strong>{reviewMetrics(row,p.key)[metric].toFixed(1)}%</strong></div>)}</div>
      <figcaption>At {capacity}% capacity: {accuracy ? 'answer-key agreement among answers left unreviewed, not accuracy after correction. Vertical axis: 60% to 100%.' : 'mismatches selected per 100 review slots, not the share of all mismatches caught. Vertical axis: 0% to 100%.'} Tap a capacity on the chart or use the buttons above.</figcaption>
    </figure>
    <details className={styles.exact}><summary>Exact values at all four tested capacities</summary><div className={styles.tableScroll} tabIndex={0} role="region" aria-label="Exact results"><table><caption>{accuracy ? 'Unreviewed answer-key agreement' : 'Mismatches per review slot'} (%)</caption><thead><tr><th>Capacity</th>{policies.map(p => <th key={p.key}>{p.label}</th>)}</tr></thead><tbody>{followupRows.map(r => <tr key={r.capacity}><th>{r.capacity}%</th>{policies.map(p => <td key={p.key}>{reviewMetrics(r,p.key)[metric].toFixed(2)}%</td>)}</tr>)}</tbody></table></div></details>
    <div className={styles.note}>Only four capacities were tested. Connecting lines are visual guides. Random baseline is one fixed ranking, not an average. These exploratory results measure selection, not human correction or time saved. <a href="#method-metrics">Methods and definitions</a>.</div>
    <dialog ref={dialog} className={styles.dialog} aria-label={title} onClose={() => expandedButton.current?.focus()}>
      <div className={styles.chartHeading}><h4>{title}</h4><button type="button" autoFocus onClick={() => dialog.current?.close()}>Close ×</button></div>
      <CapacityToggle capacity={capacity} select={select} />
      <div className={styles.legend}>{policies.map(p => <span key={p.key}><i style={{ borderColor:p.color, borderTopStyle:p.key === 'random' ? 'dashed' : 'solid' }} />{p.label}</span>)}</div>
      {chart()}
      <div className={styles.values}>{policies.map(p => <div key={p.key}><span>{p.label}</span><strong>{reviewMetrics(row,p.key)[metric].toFixed(1)}%</strong></div>)}</div>
      <div className={styles.note}>Selected review capacity: {capacity}%. {accuracy ? 'Agreement among unreviewed answers. Vertical axis starts at 60%.' : 'Mismatches per review slot. Vertical axis starts at zero.'}</div>
    </dialog>
  </div>;
}
