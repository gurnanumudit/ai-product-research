import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

const repo = new URL('../../', import.meta.url);
const read = path => readFileSync(new URL(path, repo));
const json = path => JSON.parse(read(path));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const study = 'research/evaluation-reliability-sensitivity/';
const article = json('site/content/evaluation-sensitivity-results.json');
const source = json(study + 'results/analysis.json');
const sourceById = new Map(source.cells.map(row => [row.cell.id, row]));
const methods = ['row_fixed', 'row_peek', 'context_fixed', 'context_peek', 'context_adjusted', 'integrity_adjusted'];
const finalOutcomes = ['correct_ship', 'false_ship', 'correct_hold', 'false_hold', 'inconclusive'];
const near = (actual, expected, message) => {
  assert.ok(Number.isFinite(actual) && Number.isFinite(expected), message);
  assert.ok(Math.abs(actual - expected) <= 1e-12, `${message}: ${actual} != ${expected}`);
};

function wilson(count, n) {
  const p = count / n, z = 1.959963984540054, z2 = z * z;
  const denominator = 1 + z2 / n;
  const center = (p + z2 / (2 * n)) / denominator;
  const half = z * Math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominator;
  return [count === 0 ? 0 : Math.max(0, center - half), count === n ? 1 : Math.min(1, center + half)];
}

test('article export identifies the exact audited source, freeze and review', () => {
  assert.equal(article.schema, 'evaluation-sensitivity-article-v1');
  const review = json(study + 'independent-review.json');
  assert.equal(review.status, 'passed');
  assert.equal(article.provenance.source, study + 'results/analysis.json');
  assert.equal(article.provenance.sourceSha256, digest(read(study + 'results/analysis.json')));
  assert.equal(review.files['results/analysis.json'], article.provenance.sourceSha256);
  assert.equal(article.provenance.freezeSha256, digest(read(study + 'FREEZE.json')));
  assert.equal(source.freeze_sha256, article.provenance.freezeSha256);
  assert.equal(article.provenance.reviewSha256, digest(read(study + 'independent-review.json')));
  assert.equal(article.provenance.cellsVerified, 23);
  assert.equal(article.provenance.methodRowsVerified, 138);
  assert.equal(article.provenance.metricCountsRatesAndIntervalsVerified, 552);
  assert.equal(read('site/public/research-assets/evaluation-reliability/sensitivity-results.json').toString(),
    read('site/content/evaluation-sensitivity-results.json').toString(), 'Download and bundled article data must match');
});

test('all 23 settings and 138 method rows map exactly to reviewed results', () => {
  assert.deepEqual(source.methods_order, methods);
  assert.equal(article.cells.length, 23);
  assert.equal(new Set(article.cells.map(cell => cell.id)).size, 23);
  assert.deepEqual(article.cells.map(cell => cell.id), source.cells.map(result => result.cell.id));
  const families = Object.fromEntries(['missingness', 'threshold', 'relatedness'].map(family => [family, article.cells.filter(cell => cell.family === family).length]));
  assert.deepEqual(families, { missingness: 11, threshold: 9, relatedness: 3 });
  let rowsVerified = 0, metricsVerified = 0;
  for (const cell of article.cells) {
    const original = sourceById.get(cell.id);
    assert.ok(original, `Unknown setting: ${cell.id}`);
    for (const [key, value] of Object.entries(original.cell)) assert.deepEqual(cell[key], value, `${cell.id}.${key}`);
    assert.equal(cell.cohorts, 2000);
    assert.equal(original.cohorts, 2000);
    const worthwhile = cell.delta > cell.tau;
    assert.equal(cell.switchKind, worthwhile ? 'correct' : 'incorrect');
    assert.equal(original.truth_class, worthwhile ? 'switch_worthy' : 'hold_worthy');
    assert.equal(cell.finalMean, original.approach1_final_look.mean_estimate);
    assert.equal(cell.bias, original.approach1_final_look.bias_vs_known_delta);
    assert.equal(original.approach1_final_look.stopping_conditioned, false);
    assert.equal(original.approach1_final_look.cohorts_in_mean, cell.cohorts);
    assert.equal(cell.missingFraction, original.missing_pair_fraction);
    assert.ok(cell.missingFraction >= 0 && cell.missingFraction <= 1);
    near(cell.finalMean - cell.delta, cell.bias, `${cell.id}: final-look bias`);
    assert.deepEqual(cell.rows.map(row => row.method), methods);
    assert.deepEqual(cell.rows.map(row => row.number), [1, 2, 3, 4, 5, 6]);
    for (const row of cell.rows) {
      const expected = original.methods[row.method];
      assert.equal(finalOutcomes.reduce((sum, key) => sum + expected.counts[key], 0), cell.cohorts);
      const metricNames = { switch: worthwhile ? 'correct_ship' : 'false_ship', correctHold: 'correct_hold', falseHold: 'false_hold', inconclusive: 'inconclusive' };
      assert.equal(Object.keys(metricNames).reduce((sum, key) => sum + row[key].count, 0), cell.cohorts);
      for (const [displayKey, event] of Object.entries(metricNames)) {
        const metric = row[displayKey];
        assert.deepEqual(Object.keys(metric).sort(), ['count', 'estimate', 'wilson95']);
        assert.ok(Number.isInteger(metric.count) && metric.count >= 0 && metric.count <= cell.cohorts);
        assert.equal(metric.count, expected.counts[event], `${cell.id}:${row.method}:${event} count`);
        assert.equal(metric.estimate, expected.rates[event].estimate, `${cell.id}:${row.method}:${event} rate`);
        assert.deepEqual(metric.wilson95, expected.rates[event].wilson95, `${cell.id}:${row.method}:${event} interval`);
        near(metric.estimate, metric.count / cell.cohorts, 'Count-derived rate');
        assert.equal(metric.wilson95.length, 2);
        const interval = wilson(metric.count, cell.cohorts);
        metric.wilson95.forEach((value, i) => near(value, interval[i], 'Independent Wilson interval'));
        assert.ok(metric.wilson95[0] >= 0 && metric.wilson95[1] <= 1 && metric.wilson95[0] <= metric.estimate && metric.estimate <= metric.wilson95[1]);
        metricsVerified++;
      }
      assert.equal(row.meanContexts, expected.mean_intended_contexts);
      const distribution = Object.entries(expected.first_decision_or_horizon_distribution);
      assert.equal(distribution.reduce((sum, [, count]) => sum + count, 0), cell.cohorts);
      assert.ok(distribution.every(([look, count]) => [40, 80, 120, 160, 200].includes(Number(look)) && Number.isInteger(count) && count > 0));
      near(row.meanContexts, distribution.reduce((sum, [look, count]) => sum + Number(look) * count, 0) / cell.cohorts, 'Unconditional mean groups');
      rowsVerified++;
    }
  }
  assert.equal(rowsVerified, 138);
  assert.equal(metricsVerified, 552);
});

test('all five original anchors retain frozen published counts and correct labels', () => {
  const original = json('research/evaluation-reliability/results/analysis.json');
  const worlds = new Map(original.worlds.map(world => [world.world_id, world]));
  const anchors = ['missing_f40_s05', 'related_h30', 'threshold_w04_t02', 'threshold_w09_t02', 'threshold_w05_t02'];
  for (const id of anchors) {
    const cell = article.cells.find(row => row.id === id);
    const reference = worlds.get(cell.world_id);
    for (const row of cell.rows) {
      const expected = reference.methods[row.method];
      const switchEvent = cell.switchKind === 'correct' ? 'correct_ship' : 'false_ship';
      assert.equal(row.switch.count, expected.counts[switchEvent] || 0);
      assert.equal(row.correctHold.count, expected.counts.correct_hold || 0);
      assert.equal(row.falseHold.count, expected.counts.false_hold || 0);
      assert.equal(row.inconclusive.count, expected.counts.inconclusive || 0);
      assert.equal(row.meanContexts, expected.mean_contexts_consumed);
    }
  }
  const byId = new Map(article.cells.map(cell => [cell.id, cell]));
  assert.match(byId.get('missing_f00_s00').condition, /w09.*not w03/);
  assert.match(byId.get('missing_f05_s10').condition, /reversed-selection negative control/);
  for (const id of ['missing_f05_s05', 'missing_f10_s10']) assert.equal(byId.get(id).condition, 'equal-loss MCAR control');
  assert.equal(byId.get('threshold_w04_t01').switchKind, 'correct');
  assert.equal(byId.get('threshold_w04_t02').switchKind, 'incorrect');
  assert.equal(byId.get('threshold_w04_t05').switchKind, 'incorrect');
  for (const cell of article.cells.filter(row => row.family === 'relatedness')) near(cell.paired_difference_icc, cell.h ** 2 / (0.5 - cell.delta ** 2), 'Relatedness is correlation, not h');
});

const reviewUrl = process.env.SENSITIVITY_REVIEW_URL;
test('local rendered draft has complete stable anchors and exact displayed values', { skip: !reviewUrl }, async () => {
  const url = new URL(reviewUrl);
  assert.equal(url.protocol, 'http:', 'This check is local-only; do not point it at production');
  assert.ok(['localhost', '127.0.0.1', '[::1]'].includes(url.hostname), 'This check is local-only');
  const response = await fetch(url);
  assert.equal(response.status, 200);
  const html = (await response.text()).replace(/<!--[\s\S]*?-->/g, '');
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'Duplicate HTML ids');
  const idSet = new Set(ids);
  for (const [, id] of html.matchAll(/href="#([^"]+)"/g)) assert.ok(idSet.has(id), `Broken anchor: ${id}`);
  assert.ok(idSet.has('sensitivity-details'), 'Main appendix wrapper is required');
  assert.ok(html.includes('href="#sensitivity-details"'), 'Sensitivity appendix must be linked from article');
  for (const family of ['missingness', 'threshold', 'relatedness']) assert.ok(idSet.has(`sensitivity-${family}`));
  const extracted = [...html.matchAll(/<tr\b[^>]*data-sensitivity-row="([^"]+)"[^>]*>([\s\S]*?)<\/tr>/g)];
  assert.equal(extracted.length, 138);
  const renderedRows = new Map(extracted.map(([, key, row]) => [key, row]));
  assert.equal(renderedRows.size, 138, 'Duplicate rendered method rows');
  for (const cell of article.cells) {
    assert.ok(idSet.has(`sensitivity-${cell.id}`), `Missing setting: ${cell.id}`);
    assert.ok(html.includes(`<details id="sensitivity-${cell.id}"`), 'Setting should remain collapsible');
    for (const row of cell.rows) {
      const rendered = renderedRows.get(`${cell.id}:${row.method}`);
      assert.ok(rendered, `Missing row: ${cell.id}:${row.method}`);
      assert.ok(!rendered.includes('NaN') && !rendered.includes('undefined'), 'No malformed row values');
      assert.ok(rendered.includes(`Approach ${row.number}:`));
      const columns = [...rendered.matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(match => match[1]);
      assert.equal(columns.length, 5);
      for (const [i, key] of ['switch', 'correctHold', 'falseHold', 'inconclusive'].entries()) {
        const metric = row[key];
        assert.ok(columns[i].startsWith(`${(100 * metric.estimate).toFixed(2)}%`), `${cell.id}:${row.method}:${key} percentage`);
        assert.ok(columns[i].includes(`[${(100 * metric.wilson95[0]).toFixed(2)}%, ${(100 * metric.wilson95[1]).toFixed(2)}%]`), 'Displayed interval');
        assert.ok(!columns[i].includes('/ 2,000'), 'Raw counts stay in downloadable data, not the displayed table');
      }
      assert.equal(columns[4], row.meanContexts.toFixed(2));
    }
  }
  const compact = [...html.matchAll(/data-missingness-value="([^"]+)"[^>]*>([\s\S]*?)<\/td>/g)];
  assert.equal(compact.length, 12);
  assert.equal(new Set(compact.map(([, key]) => key)).size, 12);
  for (const [, key, rendered] of compact) {
    const [cellId, method] = key.split(':');
    const cell = article.cells.find(row => row.id === cellId);
    assert.equal(cell.switchKind, 'incorrect');
    const row = cell.rows.find(item => item.method === method);
    assert.ok(rendered.includes(`${(100 * row.switch.estimate).toFixed(2)}%`));
  }
  assert.equal((html.match(/data-switch-value=/g) || []).length, 18, 'Original three figures remain intact');
  const directions = [...html.matchAll(/data-rate-direction="([^"]+)" aria-labelledby="figure-(\d+)"/g)].map(([, direction, figure]) => [figure, direction]);
  assert.deepEqual(directions, [['01', 'lower-better'], ['02', 'lower-better'], ['03', 'higher-better']], 'Chart colors follow the meaning of the rate');
  for (const [, value, cell] of html.matchAll(/data-switch-value="([^"]+)"[^>]*>([\s\S]*?)<\/td>/g)) {
    assert.ok(Number(value) >= 0 && Number(value) <= 100, 'Bar uses a percentage scale');
    assert.ok(cell.includes(`style="width:${value}%"`), 'Bar length equals the displayed rate, including zero');
    assert.ok(!cell.includes('style="left:'), 'Bars replace the old dot markers');
  }
  assert.equal((html.match(/<details id="results-/g) || []).length, 15, 'Original complete results remain intact');
});
