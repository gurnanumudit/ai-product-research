import fs from 'node:fs';
import { savedMetrics } from './figure-metrics.js';
const {rows}=JSON.parse(fs.readFileSync(new URL('./study-tables.json',import.meta.url),'utf8'));
const percent=(n,d)=>Number((100*n/d).toFixed(1));
const combined=rows.slice(0,4).map((r,i)=>{
  const other=rows[i+4],total=r.total+other.total;
  return {model:r.model,total_mismatches:total,confidence_caught:r.c+other.c,verification_caught:r.v+other.v,
    confidence_recall:percent(r.c+other.c,total),verification_recall:percent(r.v+other.v,total),
    budgets:savedMetrics[i].budgets.map((m,j)=>{
      const b=savedMetrics[i+4].budgets[j],c=r.budgets[j][0]+other.budgets[j][0],v=r.budgets[j][1]+other.budgets[j][1];
      return {capacity:m.capacity,slots:m.slots+b.slots,confidence_recall:percent(c,total),verification_recall:percent(v,total),
        confidence_remaining_accuracy:percent(m.cMatches+b.cMatches,m.released+b.released),verification_remaining_accuracy:percent(m.vMatches+b.vMatches,m.released+b.released)};
    })};
});
console.log(JSON.stringify(combined,null,2));
