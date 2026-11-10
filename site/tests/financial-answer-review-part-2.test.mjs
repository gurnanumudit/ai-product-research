import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {rows,sections,partOneUrl,randomExpected,combined} from '../content/financial-answer-review-part-2.ts';
import {savedMetrics} from '../content/financial-answer-review-part-2-metrics.js';
// Published frozen estimates, not a private workstream on the author's machine.
const summary=JSON.parse(readFileSync(new URL('../public/research-assets/financial-answer-review-part-2/saved-estimates.json',import.meta.url),'utf8'));
const diagnostic=JSON.parse(readFileSync(new URL('../public/research-assets/financial-answer-review-part-2/diagnostic.json',import.meta.url),'utf8'));
const names={'GPT-5.4 mini':'openai/gpt-5.4-mini','GPT-6.1 Sol':'openai/gpt-6.1-sol','Claude Sonnet 5.5':'anthropic/claude-sonnet-5.5','Gemini 4 Argon':'google/gemini-4-argon'};
test('all primary and secondary counts match reviewed frozen results',()=>{
  assert.equal(rows.length,8);
  for(const r of rows){
    const d=r.dataset==='FinQA'?'finqa':'tatqa';
    const cell=summary.cells.find(c=>c.dataset===d&&c.model===names[r.model]);
    assert.equal(r.n,cell.N);const p=cell.point_estimates['20'];
    assert.equal(r.slots,p.budget);assert.equal(r.total,p.total_status_counts.numerical_mismatch);
    assert.equal(r.c,p.policies.confidence.numerical_mismatches_caught);
    assert.equal(r.v,p.policies.verification.numerical_mismatches_caught);
    const interval=cell.bootstrap['20'].metrics.verification_minus_confidence.additional_mismatches_per_100_review_slots;
    assert.deepEqual(r.range,[Number(interval.lower_2_5pct.toFixed(1)),Number(interval.upper_97_5pct.toFixed(1))]);
    [5,10,20,50].forEach((b,i)=>assert.deepEqual(r.budgets[i],[cell.point_estimates[b].policies.confidence.numerical_mismatches_caught,cell.point_estimates[b].policies.verification.numerical_mismatches_caught]));
    const diag=diagnostic.cells.find(c=>c.dataset===d&&c.model===names[r.model]);
    assert.equal(r.warned,diag.warned.mismatches);assert.equal(r.flagged,diag.warned.total);assert.equal(r.selectedWarned,diag.warned.selected_mismatches);
  }
});
test('article index, appendix and chart anchors resolve uniquely',()=>{
  const html=sections.map(s=>`<section id="${s.id}">${s.html}</section>`).join('');
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(ids.length,new Set(ids).size);
  for(const [,id] of html.matchAll(/href="#([^"]+)"/g))assert.ok(ids.includes(id),id);
  assert.ok(html.includes(partOneUrl));assert.ok(!html.includes('/Users/'));assert.ok(!html.includes('http://localhost'));
  assert.ok(html.includes('post-study'));assert.ok(html.includes('low reasoning'));assert.ok(html.includes('medium'));
});
test('matched random baselines reproduce saved expectations and Sonnet is not bolded',()=>{
  rows.forEach((r,i)=>{
    const cell=summary.cells.find(c=>c.dataset===(r.dataset==='FinQA'?'finqa':'tatqa')&&c.model===names[r.model]);
    assert.equal(randomExpected[i],cell.point_estimates['20'].conditional_random_expectation.numerical_mismatches_caught.value);
  });
  const results=sections.find(s=>s.id==='appendix').html;
  const sonnetRows=[...results.matchAll(/<tr><th scope="row">Claude Sonnet 5\.5<\/th>(.*?)<\/tr>/g)];
  assert.equal(sonnetRows.length,2);
  sonnetRows.forEach(m=>assert.ok(!m[1].includes('<strong>')));
  assert.match(results,/automatic-review cases/);
  assert.ok(!sections.find(s=>s.id==='setup').html.includes('automatic-review cases'));
});
test('combined cards and charts add original queues without reranking',()=>{
  assert.deepEqual(combined.map(r=>[r.total,r.c,r.v]),[[215,63,110],[115,58,20],[183,87,103],[103,60,23]]);
  savedMetrics.forEach(m=>{
    const cell=summary.cells.find(c=>c.dataset===m.dataset&&c.model===m.model);
    m.budgets.forEach(b=>{
      const p=cell.point_estimates[b.capacity];
      assert.equal(b.slots,p.budget);assert.equal(b.released,cell.N-p.budget);
      assert.ok(Math.abs(b.cMatches/b.released-p.policies.confidence.released_answer_key_agreement)<1e-12);
      assert.ok(Math.abs(b.vMatches/b.released-p.policies.verification.released_answer_key_agreement)<1e-12);
      assert.equal(b.randomCaught,p.conditional_random_expectation.numerical_mismatches_caught.value);
    });
  });
  combined.forEach((r,i)=>r.metrics.forEach((m,j)=>{
    assert.equal(m.slots,[46,93,188,470][j]);assert.equal(m.released,942-m.slots);
    assert.equal(m.cMatches,savedMetrics[i].budgets[j].cMatches+savedMetrics[i+4].budgets[j].cMatches);
    assert.equal(m.vMatches,savedMetrics[i].budgets[j].vMatches+savedMetrics[i+4].budgets[j].vMatches);
  }));
  const main=sections.filter(s=>s.id!=='appendix').map(s=>s.html).join('');
  assert.match(main,/Sonnet’s higher verification count was not a clear lead/);assert.match(main,/not a test that isolates/);
  assert.ok(!main.includes('result-card'));assert.match(main,/Verification − confidence \(95% CI\)/);
  assert.match(main,/No combined confidence interval is reported/);
  assert.match(main,/<td>29\.3%<small>63 of 215<\/small><\/td>/);
  assert.match(main,/<td>51\.2%<small>110 of 215<\/small><\/td>/);
  assert.match(main,/Better strategy/);
  const leads=[...main.matchAll(/class="strategy-result [^"]+">([^<]+)<\/td>/g)].map(m=>m[1]);
  assert.deepEqual(leads,['Verification','Confidence','No clear winner','Confidence']);
  assert.equal((main.match(/<svg /g)||[]).length,8);
});
test('export matches table data and preview stays separate from publication',()=>{
  const exported=JSON.parse(readFileSync(new URL('../public/research-assets/financial-answer-review-part-2/study-tables.json',import.meta.url),'utf8'));
  assert.deepEqual(exported.rows,rows);
  const page=readFileSync(new URL('../app/preview/financial-answer-review-part-2/page.tsx',import.meta.url),'utf8');
  assert.match(page,/index:false,follow:false/);assert.match(page,/Part 2/);assert.match(page,/<PartTwo draft/);
  const published=readFileSync(new URL('../app/research/which-financial-ai-answers-should-we-review-part-2/page.tsx',import.meta.url),'utf8');
  assert.match(published,/canonical:url/);assert.match(published,/index:!localReview/);
});
