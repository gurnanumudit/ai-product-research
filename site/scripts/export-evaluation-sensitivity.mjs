// Derive article presentation data from saved, independently reviewed results.
// No simulations, network calls or changes to research evidence.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const sourceUrl = new URL('../../research/evaluation-reliability-sensitivity/results/analysis.json', import.meta.url);
const freezeUrl = new URL('../../research/evaluation-reliability-sensitivity/FREEZE.json', import.meta.url);
const reviewUrl = new URL('../../research/evaluation-reliability-sensitivity/independent-review.json', import.meta.url);
const targetUrl = new URL('../content/evaluation-sensitivity-results.json', import.meta.url);
const downloadUrl = new URL('../public/research-assets/evaluation-reliability/sensitivity-results.json', import.meta.url);
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const sourceBytes = readFileSync(sourceUrl);
const source = JSON.parse(sourceBytes);
const freezeSha256 = digest(readFileSync(freezeUrl));
const review = JSON.parse(readFileSync(reviewUrl));
const methods = ['row_fixed', 'row_peek', 'context_fixed', 'context_peek', 'context_adjusted', 'integrity_adjusted'];
assert.deepEqual(source.methods_order, methods);
assert.equal(source.freeze_sha256, freezeSha256);
assert.equal(review.status, 'passed');
assert.equal(review.files['results/analysis.json'], digest(sourceBytes));
assert.equal(source.cells.length, 23);
assert.equal(new Set(source.cells.map(row => row.cell.id)).size, 23);
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-12, `${actual} != ${expected}`);
function wilson(count, n) {
  const p = count / n, z = 1.959963984540054, z2 = z * z;
  const center = (p + z2 / (2 * n)) / (1 + z2 / n);
  const half = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n);
  return [count === 0 ? 0 : Math.max(0, center - half), count === n ? 1 : Math.min(1, center + half)];
}
let metricsChecked = 0;
const cells = source.cells.map(result => {
  const n = result.cohorts;
  assert.equal(n, 2000);
  const worthwhile = result.cell.delta > result.cell.tau;
  assert.equal(result.truth_class, worthwhile ? 'switch_worthy' : 'hold_worthy');
  const rows = methods.map((method, index) => {
    const value = result.methods[method];
    assert.equal(['false_ship', 'false_hold', 'correct_ship', 'correct_hold', 'inconclusive']
      .reduce((sum, key) => sum + value.counts[key], 0), n);
    const metric = key => {
      const count = value.counts[key], rate = value.rates[key];
      assert.ok(Number.isInteger(count) && count >= 0 && count <= n);
      near(rate.estimate, count / n);
      const expected = wilson(count, n);
      rate.wilson95.forEach((number, i) => near(number, expected[i]));
      metricsChecked++;
      return { count, estimate: rate.estimate, wilson95: rate.wilson95 };
    };
    assert.equal(value.counts[worthwhile ? 'false_ship' : 'correct_ship'], 0);
    const distribution = Object.entries(value.first_decision_or_horizon_distribution);
    assert.equal(distribution.reduce((sum, [, count]) => sum + count, 0), n);
    near(value.mean_intended_contexts, distribution.reduce((sum, [groups, count]) => sum + Number(groups) * count, 0) / n);
    return { method, number: index + 1, switch: metric(worthwhile ? 'correct_ship' : 'false_ship'),
      correctHold: metric('correct_hold'), falseHold: metric('false_hold'), inconclusive: metric('inconclusive'),
      meanContexts: value.mean_intended_contexts };
  });
  return { ...result.cell, cohorts: n, switchKind: worthwhile ? 'correct' : 'incorrect',
    missingFraction: result.missing_pair_fraction, finalMean: result.approach1_final_look.mean_estimate,
    bias: result.approach1_final_look.bias_vs_known_delta, rows };
});
assert.equal(cells.filter(row => row.family === 'missingness').length, 11);
assert.equal(cells.filter(row => row.family === 'threshold').length, 9);
assert.equal(cells.filter(row => row.family === 'relatedness').length, 3);
assert.equal(metricsChecked, 552);
const output = { schema: 'evaluation-sensitivity-article-v1', provenance: {
  source: 'research/evaluation-reliability-sensitivity/results/analysis.json',
  sourceSha256: digest(sourceBytes), freezeSha256,
  reviewSha256: digest(readFileSync(reviewUrl)), cellsVerified: cells.length, methodRowsVerified: cells.length * methods.length,
  metricCountsRatesAndIntervalsVerified: metricsChecked,
}, cells };
const serialized = JSON.stringify(output, null, 2) + '\n';
if (process.argv.includes('--check')) {
  assert.equal(readFileSync(targetUrl, 'utf8'), serialized, 'Article data is stale; regenerate it from the reviewed evidence.');
  assert.equal(readFileSync(downloadUrl, 'utf8'), serialized, 'Download data must match article data.');
} else {
  writeFileSync(targetUrl, serialized);
  writeFileSync(downloadUrl, serialized);
}
console.log(`${process.argv.includes('--check') ? 'Verified' : 'Exported'} 23 settings, 138 method rows and 552 count/rate/interval metrics: ${fileURLToPath(targetUrl)}`);
