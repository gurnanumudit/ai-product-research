import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

const source = readFileSync(new URL('../content/financial-review-data.ts', import.meta.url), 'utf8');
const { followupRows, reviewMetrics } = await import(`data:text/javascript;base64,${Buffer.from(stripTypeScriptTypes(source)).toString('base64')}`);

test('financial review figures preserve the published counts and calculations', () => {
  assert.deepEqual(followupRows, [
    { capacity: 5, slots: 56, confidence: 31, verification: 35, random: 17 },
    { capacity: 10, slots: 112, confidence: 59, verification: 88, random: 35 },
    { capacity: 20, slots: 225, confidence: 103, verification: 143, random: 67 },
    { capacity: 50, slots: 563, confidence: 204, verification: 211, random: 185 },
  ]);
  for (const row of followupRows) for (const policy of ['confidence', 'verification', 'random']) {
    const actual = reviewMetrics(row, policy);
    assert.equal(actual.selected + actual.missed, 347);
    assert.equal(actual.unreviewed, 1127 - row.slots);
    const publishedAccuracy = (765 - row.slots + row[policy] + 15) / (1127 - row.slots) * 100;
    const publishedPrecision = row[policy] / row.slots * 100;
    assert.ok(Math.abs(actual.accuracy - publishedAccuracy) < 1e-10);
    assert.ok(Math.abs(actual.precision - publishedPrecision) < 1e-10);
  }
  assert.deepEqual(followupRows.map(r => [Math.round(100*r.confidence/347), Math.round(100*r.verification/347)]), [[9,10],[17,25],[30,41],[59,61]]);
});
