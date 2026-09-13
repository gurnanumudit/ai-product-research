import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { setTimeout as delay } from 'node:timers/promises';

test('production homepage and article render with direct study links', async () => {
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
    assert.equal((homeHtml.match(new RegExp(`<a href="${articlePath}"`, 'g')) || []).length, 3);
    const article = await fetch(`http://localhost:${port}${articlePath}`);
    assert.equal(article.status, 200);
    const html = await article.text();
    for (const id of ['introduction', 'experiment-setup', 'finding-1', 'finding-2', 'finding-3', 'appendix']) {
      assert.ok(html.includes(`id="${id}"`), `Missing ${id}`);
    }
    assert.ok(html.includes('https://github.com/gurnanumudit/ai-product-research/tree/main/research/ai-reviewers-test-evidence'));
    assert.ok(!html.includes('Study-specific code and data release pending'));
  } finally {
    if (server.pid) {
      try { process.platform === 'win32' ? server.kill() : process.kill(-server.pid, 'SIGTERM'); } catch {}
    }
  }
});
