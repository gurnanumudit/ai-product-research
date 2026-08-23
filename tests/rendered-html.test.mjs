import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render(pathname = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${pathname}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${pathname}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the research portfolio home", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Mudit Gurnani — Research &amp; Writing<\/title>/i);
  assert.match(html, /Research notes on how AI systems behave in the real world/);
  assert.match(html, /The Test Passed\. The Patch Was Still Wrong\./);
  assert.match(html, /June 2026/);
  assert.match(html, /23 of 38/);
  assert.match(html, /Read the research note/);
  assert.match(html, /href="https:\/\/www\.linkedin\.com\/in\/muditgurnani"/);
  assert.match(html, /href="https:\/\/github\.com\/gurnanumudit\/ai-product-research"/);
  assert.doesNotMatch(html, /\$28\.38|Four product decisions|How the work is done|Research status/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape|react-loading-skeleton/);
});

test("server-renders the complete Article 1 route", async () => {
  const response = await render("/research/agent-verification");
  assert.equal(response.status, 200);

  const html = await response.text();
  assert.match(html, /<title>The Test Passed\. The Patch Was Still Wrong\. — Mudit Gurnani<\/title>/i);
  assert.match(html, /An AI coding agent says it fixed a bug/);
  assert.match(html, /June 2026/);
  assert.doesNotMatch(html, /August 2026/);
  assert.match(html, /only 15 of those 38 patches/);
  assert.match(html, /23 were still wrong/);
  assert.match(html, /Useful approval/);
  assert.match(html, /Unsafe approval/);
  assert.match(html, /Correct patch missed/);
  assert.match(html, /Wrong patch not approved/);
  assert.match(html, /mostly means the verifier did[\s\S]*not return a usable result/);
  assert.match(html, /A test pass is a clue—not clearance/);
  assert.match(html, /GPT-5\.4 Mini/);
  assert.match(html, /Claude Opus 4\.6/);
  assert.match(html, /How did we know whether a patch was really correct/);
  assert.match(html, /href="https:\/\/swe-rebench\.com\/about"/);
  assert.match(html, /Mini, then GPT-5\.4 when no patch appeared/);
  assert.match(html, /Read the Anthropic study/);
  assert.match(html, /Read the UTBoost paper/);
  assert.match(html, /Read the Otter paper/);
  assert.match(html, /Escalation recovered two additional fixes for \$3\.02/);
  assert.match(html, /href="https:\/\/www\.linkedin\.com\/in\/muditgurnani"/);
  assert.match(html, /Code and study materials/);
  assert.match(
    html,
    /href="https:\/\/github\.com\/gurnanumudit\/ai-product-research\/tree\/main\/research\/agent-verification"/,
  );
  assert.doesNotMatch(html, /0 \/ 140|This was not a synthetic-data exercise|escaped-failure rate|targeted challenge package/);
});

test("removes starter artifacts and keeps publication assets", async () => {
  const [page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.doesNotMatch(page, /SkeletonPreview|codex-preview/);
  assert.doesNotMatch(layout, /Starter Project|codex-preview/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await access(new URL("../public/og.png", import.meta.url));
  await access(new URL("../public/og-research-note.png", import.meta.url));
  await access(new URL("../public/verification-confirmatory.png", import.meta.url));
  await assert.rejects(access(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)));
});
