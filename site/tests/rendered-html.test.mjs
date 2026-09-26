import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

test('production homepage and article render with direct study links', async () => {
  const reviewBuild = process.env.TEST_REVIEW === '1';
  const port = process.env.TEST_PORT || '3197';
  const server = spawn('npm', ['run', 'start', '--', '--port', port], {
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
    assert.equal((homeHtml.match(new RegExp(`<a href="${articlePath}"`, 'g')) || []).length, 3);
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
    assert.ok(tags.get('og:description').includes('research journey'));
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
