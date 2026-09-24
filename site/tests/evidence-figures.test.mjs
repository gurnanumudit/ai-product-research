import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const data = JSON.parse(await readFile(new URL('../content/evidence-figure-data.json', import.meta.url)));
const original = JSON.parse(await readFile(new URL('../../research/ai-reviewers-test-evidence/reference/figure-data.json', import.meta.url)));
const svg = await readFile(new URL('../public/research-assets/evidence-review/v2/finding-2-evidence-content.svg',import.meta.url),'utf8');

test('responsive figures preserve the published source and passing comparisons exactly', () => {
  assert.deepEqual(data.source, original.source_effect);
  for (const r of data.passing) {
    const ref=original.benchmark_approval.find(x=>x.phase===2&&x.model===r.model&&x.condition==='C'&&x.label==='correct');
    for(const key of Object.keys(r)) assert.deepEqual(r[key],ref[key],key);
  }
});

test('shared failing cohort retains all nine original estimates and uncertainty intervals', () => {
  const models=['anthropic/claude-sonnet-5','openai/gpt-5.6-terra','google/gemini-3.8-flash'];
  const points=[...svg.matchAll(/<circle cx="([^"]+)" cy="([^"]+)" r="7"/g)];
  const whiskers=[...svg.matchAll(/<line x1="([^"]+)" y1="([^"]+)" x2="([^"]+)" y2="([^"]+)" stroke="#(?:A64B2A|006D77|6654A3)" stroke-width="3"/g)];
  assert.equal(data.failing.length,9);
  models.forEach((model,j)=>['A','B','C'].forEach((condition,k)=>{
    const r=data.failing.find(x=>x.model===model&&x.condition===condition);
    assert.equal(r.n_tasks,15);assert.equal(r.n_reviews,30);
    const origin=218+j*466, i=j*3+k;
    assert.ok(Math.abs((Number(points[i][1])-origin)/336-r.estimate)<1e-12);
    assert.ok(Math.abs((Number(whiskers[i][1])-origin)/336-r.interval95[0])<1e-12);
    assert.ok(Math.abs((Number(whiskers[i][3])-origin)/336-r.interval95[1])<1e-12);
  }));
});
