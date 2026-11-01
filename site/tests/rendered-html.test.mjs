import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

test('production homepage and article render with direct study links', async () => {
  const reviewBuild = process.env.TEST_REVIEW === '1';
  const port = process.env.TEST_PORT || '3197';
  const server = spawn(process.execPath, ['node_modules/vinext/dist/cli.js', 'start', '--port', port], {
    cwd: process.cwd(), detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe'], env: process.env,
  });
  let log = '';
  server.stdout.on('data', chunk => { log += chunk; });
  server.stderr.on('data', chunk => { log += chunk; });
  try {
    let ready = false;
    for (let i = 0; i < 100; i++) {
      if (server.exitCode !== null) throw new Error(log);
      if (log.includes('Production server running')) { ready = true; break; }
      await delay(100);
    }
    assert.ok(ready, `Server did not start: ${log}`);
    const articlePath = '/research/how-ai-reviewers-use-test-evidence';
    const home = await fetch(`http://localhost:${port}/`);
    assert.equal(home.status, 200);
    const homeHtml = await home.text();
    checkAnchors(homeHtml);
    const negotiationPath = '/research/how-ai-negotiates';
    assert.ok(homeHtml.includes(negotiationPath));
    assert.ok(homeHtml.includes('Oct 29, 2026'));
    const negotiation = await fetch(`http://localhost:${port}${negotiationPath}`);
    assert.equal(negotiation.status, 200);
    const negotiationHtml = await negotiation.text();
    checkAnchors(negotiationHtml);
    for (const text of ['October 29, 2026', 'research/negotiation', '2,160', '1.90', 'Appendix', '2026-10-29']) assert.ok(negotiationHtml.includes(text), `Missing negotiation content: ${text}`);
    for (const text of ['Not yet published', 'Unpublished review draft', 'has not yet been published there', 'Research draft · October']) assert.ok(!negotiationHtml.includes(text), `Stale negotiation copy: ${text}`);
    assert.ok(negotiationHtml.includes('https://research.muditgurnani.chatgpt.site/research/how-ai-negotiates'));
    const negotiationData = await fetch(`http://localhost:${port}/research-assets/negotiation/chart-data.json`);
    assert.equal(negotiationData.status, 200);
    const nd = await negotiationData.json();
    assert.equal(nd.main.episodes,2160);assert.equal(nd.roleGap.rows.length,107);

    assert.ok(homeHtml.includes('<h1 id="research-title">Evidence for better decisions about AI.</h1>'));
    assert.ok(!homeHtml.includes('<h1 id="research-title">Research</h1>'));
    assert.ok(homeHtml.includes('I study what AI can do, what it costs and how it behaves.'));
    for (const text of ['Three questions guide the work', 'Cost and quality', 'Trust and review', 'Agent decisions', 'All 7 published studies', 'Flagship research', 'Latest article', 'My background is in finance and data science', 'The goal: help people choose AI systems']) assert.ok(homeHtml.includes(text), `Missing homepage content: ${text}`);
    for (const removed of ['Show article covers', 'Coming next', 'Prompt vs harness', 'Forthcoming conclusion']) assert.ok(!homeHtml.includes(removed), `Unwanted homepage content: ${removed}`);
    const toolErrorPath = '/research/when-a-test-report-is-wrong';
    const toolErrorResponse = await fetch(`http://localhost:${port}${toolErrorPath}`);
    assert.equal(toolErrorResponse.status, 200);
    assert.equal(homeHtml.includes(toolErrorPath), true);
    {
      const article = await toolErrorResponse.text();
      checkAnchors(article);
      await checkSocialPreview(port, toolErrorPath, '/research-assets/tool-error/cover.png');
      for (const phrase of [reviewBuild ? 'noindex, nofollow' : 'index, follow', '720', '27 net additional successes', 'Related research', 'Research code', 'amended completion']) assert.ok(article.includes(phrase), phrase);
      for (const bad of ['../econ-tool-error', '/Users/', '127.0.0.1', 'localhost', '—']) assert.ok(!article.includes(bad), bad);
      for (const asset of ['chart-data-v2.json','chart-data-v2.csv','review-summary.json']) assert.equal((await fetch(`http://localhost:${port}/research-assets/tool-error/${asset}`)).status,200,asset);
      const data = await (await fetch(`http://localhost:${port}/research-assets/tool-error/chart-data-v2.json`)).json();
      assert.deepEqual(Object.values(data.strata.overall.arms).map(a=>a.successes), [185,187,212]);
      assert.equal(Object.values(data.strata).flatMap(s=>s.contrasts).length,15);
    }
    for (const slug of ['how-ai-reviewers-use-test-evidence','when-is-more-reasoning-worth-it','how-to-avoid-false-confidence-in-ai-evaluations','which-financial-ai-answers-should-we-review','which-financial-ai-answers-should-we-review-part-2','how-ai-negotiates','when-a-test-report-is-wrong']) {
      const page = await fetch(`http://localhost:${port}/research/${slug}`);
      assert.equal(page.status, 200, slug);
      const text = await page.text();
      checkAnchors(text);
      for (const role of ['research-article','article-header','article-hero','article-cover','article-dek','article-byline','article-resources','article-layout','article-body','article-index']) assert.ok(text.includes(`data-${role}=""`), `Missing standard ${role}: ${slug}`);
      assert.ok(text.includes('Data and methods ↓'), `Missing appendix link: ${slug}`);
      assert.match(text, /<a[^>]+href="https:\/\/github\.com\/gurnanumudit\/ai-product-research\/tree\/[^" ]+"[^>]*>Research code(?: ↗)?<\/a>/, `Missing consistent research-code link: ${slug}`);
    }
    const financialPath = '/research/which-financial-ai-answers-should-we-review';
    assert.equal((homeHtml.match(new RegExp(`<a href="${financialPath}"`, 'g')) || []).length >= 1, true);
    const financial = await fetch(`http://localhost:${port}${financialPath}`);
    assert.equal(financial.status, 200);
    const financialHtml = await financial.text();
    checkAnchors(financialHtml);
    assert.ok(financialHtml.includes('October 10, 2026'));
    assert.ok(financialHtml.includes('article-analysis'));
    assert.ok(financialHtml.includes('rule-based checks to recalculate the answer'));
    assert.ok(financialHtml.includes('same automatic-review rules'));
    assert.ok(financialHtml.includes('Mismatches caught'));
    assert.ok(financialHtml.includes('347 answers did not match.'));
    assert.ok(financialHtml.includes('60–100%') && financialHtml.includes('0–100%'));
    assert.ok(financialHtml.includes('After examining the initial results'));
    assert.ok(financialHtml.includes('exploratory, not independent validation'));
    assert.ok(financialHtml.includes('We tested only one model: GPT-5.4 mini.'));
    assert.ok(financialHtml.includes('143 mismatches in 225 slots'));
    assert.ok(financialHtml.includes('In this article'));
    assert.ok(financialHtml.includes('checker-sensitivity'));
    assert.ok(financialHtml.includes('Updated') && financialHtml.includes('October 21, 2026'));
    for (const stale of ['Draft 4', 'Draft note:', 'Local draft', 'Draft revision', 'not yet been added', 'saved locally', 'Local reading preview', '127.0.0.1']) assert.ok(!financialHtml.includes(stale), `Stale text: ${stale}`);
    assert.ok(financialHtml.includes(reviewBuild ? 'noindex, nofollow' : 'index, follow'));
    for (const asset of ['review-budget-accuracy-detail.svg', 'review-budget-precision-detail.svg', 'appendix-navigation.js']) {
      const response = await fetch(`http://localhost:${port}/research-assets/financial-answer-review/${asset}`);
      assert.equal(response.status, 200);
    }
    await checkSocialPreview(port, financialPath, '/research-assets/financial-answer-review/cover-v3.png');
    const partTwoPath = financialPath + '-part-2';
    assert.equal((homeHtml.match(new RegExp(`<a href="${partTwoPath}"`, 'g')) || []).length >= 1,true);
    assert.ok(financialHtml.includes(`href="${partTwoPath}"`));
    const partTwoResponse = await fetch(`http://localhost:${port}${partTwoPath}`);
    assert.equal(partTwoResponse.status,200);
    const partTwoHtml = await partTwoResponse.text();checkAnchors(partTwoHtml);
    for(const stale of ['Draft for review','Draft preparation:','/Users/','192.168.','localhost','public repository link and an export review are still needed']) assert.ok(!partTwoHtml.includes(stale),stale);
    assert.ok(partTwoHtml.includes('October 21, 2026'));assert.ok(partTwoHtml.includes('October 17, 2026'));
    assert.ok(partTwoHtml.includes('Better strategy'));assert.ok(partTwoHtml.includes('No clear winner'));
    assert.ok(partTwoHtml.includes(reviewBuild ? 'noindex, nofollow' : 'index, follow'));
    await checkSocialPreview(port,partTwoPath,'/research-assets/financial-answer-review-part-2/cover-v1.png');
    for(const [,path] of partTwoHtml.matchAll(/href="(\/research-assets\/[^"#]+)"/g))assert.equal((await fetch(`http://localhost:${port}${path}`)).status,200,path);
    const reliabilityPath = '/research/how-to-avoid-false-confidence-in-ai-evaluations';
    assert.equal((homeHtml.match(new RegExp(`<a href="${reliabilityPath}"`, 'g')) || []).length >= 1, true);
    await checkSocialPreview(port, reliabilityPath, '/research-assets/evaluation-reliability/evaluation-confidence-cover.png');
    const reliability = await fetch(`http://localhost:${port}${reliabilityPath}`);
    assert.equal(reliability.status, 200);
    const reliabilityHtml = await reliability.text();
    assert.ok(reliabilityHtml.includes('September 30, 2026'));
    assert.ok(reliabilityHtml.includes('https://github.com/gurnanumudit/ai-product-research/tree/main/research/evaluation-reliability'));
    assert.ok(!reliabilityHtml.includes('Unpublished') && !reliabilityHtml.includes('release is not yet'));
    assert.ok(reliabilityHtml.includes(reviewBuild ? 'noindex, nofollow' : 'index, follow'));
    assert.equal((reliabilityHtml.match(/data-switch-value=/g) || []).length, 18);
    assert.equal((reliabilityHtml.match(/<details id="results-/g) || []).length, 15);
    checkAnchors(reliabilityHtml);
    const navigation = await fetch(`http://localhost:${port}/research-assets/evaluation-reliability/appendix-navigation.js`);
    assert.equal(navigation.status, 200);
    await checkSocialPreview(port, '/', '/og-research-journey-v1.png');
    await checkSocialPreview(port, articlePath, '/research-assets/evidence-review/v3/three-lenses.png');
    await checkSocialPreview(port, '/research/when-is-more-reasoning-worth-it', '/research-assets/reasoning-costs/reasoning-selector-cover-v2.png');
    assert.ok(homeHtml.includes('href="/research/when-is-more-reasoning-worth-it"'), 'published study is listed');
    for (const draftPath of ['/research/when-is-more-reasoning-worth-it', '/preview/reasoning-costs']) {
      const draft = await fetch(`http://localhost:${port}${draftPath}`);
      assert.equal(draft.status, 200, 'both canonical and legacy article addresses remain available');
      {
        const draftHtml = await draft.text();
        assert.ok(draftHtml.includes(reviewBuild ? 'noindex, nofollow' : 'index, follow'));
        assert.ok(!draftHtml.includes('Review draft') && !draftHtml.includes('Unpublished'));
        assert.ok(draftHtml.includes('https://research.muditgurnani.chatgpt.site/research/when-is-more-reasoning-worth-it'));
        assert.ok(draftHtml.includes('three OpenAI GPT-5.6 models'));
        checkAnchors(draftHtml);
        assert.ok(!draftHtml.includes('/chunks/link-'), 'static articles do not load client-router link prefetching');
        assert.ok(!draftHtml.includes('/@vite/client') && !draftHtml.includes('virtual:vite-rsc/entry-browser'), 'review uses bundled modules, not development imports');
      }
    }
    assert.equal((homeHtml.match(new RegExp(`<a href="${articlePath}"`, 'g')) || []).length >= 1, true);
    const article = await fetch(`http://localhost:${port}${articlePath}`);
    assert.equal(article.status, 200);
    const html = await article.text();
    for (const id of ['introduction', 'experiment-setup', 'finding-1', 'finding-2', 'finding-3', 'application', 'limitations', 'conclusion', 'appendix', 'references']) {
      assert.ok(html.includes(`id="${id}"`), `Missing ${id}`);
    }
    assert.ok(html.includes('https://github.com/gurnanumudit/ai-product-research/tree/main/research/ai-reviewers-test-evidence'));
    assert.ok(!html.includes('Study-specific code and data release pending'));
    assert.ok(!html.includes('A public reproduction package is not yet published'));
    for (const name of ['failing', 'passing', 'source']) assert.ok(html.includes(`data-evidence-figure="${name}"`));
    assert.ok(html.includes(reviewBuild ? 'noindex, nofollow' : 'index, follow'));
    checkAnchors(html);
    assert.ok(!html.includes('/chunks/link-'), 'static articles do not load client-router link prefetching');
    for (const image of ['/research-assets/evidence-review/v3/three-lenses.webp', '/research-assets/reasoning-costs/reasoning-selector-cover-v2.webp']) {
      const asset = await fetch(`http://localhost:${port}${image}`);
      assert.equal(asset.status, 200);
      assert.match(asset.headers.get('content-type'), /image\/webp/);
      assert.ok((await asset.arrayBuffer()).byteLength < 350000);
    }
  } finally {
    if (server.pid) {
      try { process.platform === 'win32' ? server.kill() : process.kill(-server.pid, 'SIGTERM'); } catch {}
    }
  }
});

function checkAnchors(html) {
  const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
  for (const [,id] of html.matchAll(/href="#([^"]+)"/g)) assert.ok(ids.has(id), `Missing anchor: ${id}`);
}

async function checkSocialPreview(port, path, imagePath) {
  const response = await fetch('http://localhost:' + port + path, {
    headers: { 'User-Agent': 'LinkedInBot/1.0' },
  });
  assert.equal(response.status, 200);
  const html = await response.text();
  const head = html.slice(0, html.indexOf('</head>'));
  const tags = new Map([...head.matchAll(/<meta\s+(?:property|name)="([^"]+)"\s+content="([^"]*)"[^>]*>/g)].map(m => [m[1],m[2]]));
  for (const key of ['og:title','og:description','og:url','og:type','og:image','og:image:width','og:image:height','twitter:image']) {
    assert.ok(tags.get(key), path + ': missing server-rendered ' + key);
  }
  assert.equal(new URL(tags.get('og:url')).href, new URL(path, 'https://research.muditgurnani.chatgpt.site').href);
  assert.equal(tags.get('og:image'), 'https://research.muditgurnani.chatgpt.site' + imagePath);
  assert.equal(tags.get('twitter:image'), tags.get('og:image'));
  if (path === '/') {
    assert.ok(tags.get('og:description').length >= 100, 'homepage sharing description is at least 100 characters');
    assert.ok(tags.get('og:description').includes('Evidence for better decisions about AI.'));
    assert.ok(!tags.get('og:image').includes('og-v2.png'), 'new card has a fresh cache key');
  }
  assert.ok(Number(tags.get('og:image:width')) >= 1200);
  assert.ok(Number(tags.get('og:image:height')) >= 627);
  const image = await fetch('http://localhost:' + port + imagePath, {headers: {'User-Agent': 'LinkedInBot/1.0'}});
  assert.equal(image.status, 200);
  assert.match(image.headers.get('content-type'), /image\/png/);
  const bytes = new Uint8Array(await image.arrayBuffer());
  assert.ok(bytes.length < 5 * 1024 * 1024);
  assert.deepEqual([...bytes.slice(0,8)], [137,80,78,71,13,10,26,10]);
}
