import test from 'node:test';
import assert from 'node:assert/strict';
import { followupRows, financialAnswerReviewSections as sections } from '../content/financial-answer-review-draft.ts';

test('draft uses reviewed revised counts and intact confidence comparator', () => {
  assert.deepEqual(followupRows.map(r=>r.verification),[35,88,143,211]);
  assert.deepEqual(followupRows.map(r=>r.confidence),[31,59,103,204]);
  assert.deepEqual(followupRows.map(r=>r.slots),[56,112,225,563]);
  assert.equal(347-143,204);
  assert.equal(347-211,136);
});
test('all 24 plotted coordinates reproduce the reviewed metrics', () => {
  for (const [id,accuracy] of [['capacity',true],['precision',false]]) {
    const html=sections.find(s=>s.id===id).html;
    const series=[...html.matchAll(/<polyline data-policy="([^"]+)" points="([^"]+)"/g)];
    assert.equal(series.length,3);
    for (const [,policy,coords] of series) {
      const points=coords.split(' ').map(p=>p.split(',').map(Number));
      assert.equal(points.length,4);
      points.forEach(([x,y],i)=>{
        const r=followupRows[i], min=accuracy?60:0;
        const expected=accuracy?(765-r.slots+r[policy]+15)/(1127-r.slots)*100:r[policy]/r.slots*100;
        assert.equal(x,70+(r.capacity-5)*14);
        assert.ok(y>=105 && y<=345);
        assert.ok(Math.abs(min+(345-y)*(100-min)/240-expected)<1e-9);
      });
    }
  }
});
test('learning replaces update callout; appendix preserves methodological history', () => {
  const setup=sections.find(s=>s.id==='setup').html;
  assert.ok(!setup.includes('A note on this update'));
  assert.ok(!setup.includes('revision-note'));
  const all=sections.map(s=>s.html).join('');
  assert.ok(all.includes('checker-sensitivity'));
  assert.ok(!all.includes('Draft note:'));
  assert.ok(all.includes('Exact empirical replay requires the original saved responses'));
  assert.ok(all.includes('After examining the initial results'));
  assert.ok(all.includes('same saved responses, without changing the answers or grading rule'));
  assert.ok(all.includes('exploratory, not independent validation'));
  assert.ok(all.includes('Do not automatically give priority'));
  assert.ok(!all.includes('Adjusted verification'));
  assert.ok(!all.includes('177 versus 113'));
  assert.ok(!all.includes('263'));
});
test('index IDs and every appendix anchor are unique and resolve', () => {
  const all=sections.map(s=>`<section id="${s.id}">${s.html}</section>`).join('');
  const ids=[...all.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  assert.equal(new Set(ids).size,ids.length);
  for(const [,id] of all.matchAll(/href="#([^"]+)"/g)) assert.ok(ids.includes(id),id);
});
