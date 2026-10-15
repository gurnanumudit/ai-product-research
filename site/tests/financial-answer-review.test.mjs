import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const results = JSON.parse(await readFile(new URL('../content/financial-answer-review-results.json', import.meta.url)));
for (const [file,key,min,max] of [
 ['review-budget-accuracy-detail.svg','released_accuracy',68,76],
 ['review-budget-precision-detail.svg','review_precision_per_slot',20,60],
]) {
 test(file + ' preserves all twelve points on a clearly labeled zoomed scale', async () => {
  const svg = await readFile(new URL('../public/research-assets/financial-answer-review/' + file,import.meta.url),'utf8');
  assert.ok(svg.includes(min + '–' + max + '%'));
  const series = [...svg.matchAll(/<polyline data-policy="([^"]+)" points="([^"]+)"/g)];
  assert.equal(series.length,3);
  for (const [,policy,coords] of series) {
   const points = coords.split(' ').map(p=>p.split(',').map(Number));
   assert.equal(points.length,4);
   points.forEach(([x,y],i)=>{
    assert.ok(y>=105 && y<=345, 'no point hidden by zoom');
    assert.equal(x,70+(results.results[i].review_percent-5)*14);
    const value = min+(345-y)*(max-min)/240;
    assert.ok(Math.abs(value-results.results[i].policies[policy][key].percent)<.001);
   });
  }
 });
}
test('published aggregates retain answer-key counts and scoring sensitivity',()=>{
 assert.equal(results.N,1127);
 assert.equal(results.matches,765);
 assert.equal(results.numeric_mismatches,347);
 assert.equal(results.abstentions,15);
 assert.deepEqual(results.results.map(r=>r.policies.confidence.reviewed_mismatches),[31,59,103,204]);
 assert.deepEqual(results.results.map(r=>r.policies.verification_priority.reviewed_mismatches),[19,42,95,204]);
 assert.equal(results.strict5_sensitivity_at_20_percent.policies.confidence.reviewed_mismatches,113);
 assert.equal(results.strict5_sensitivity_at_20_percent.policies.verification_priority.reviewed_mismatches,177);
});
