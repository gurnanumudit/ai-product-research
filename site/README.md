# Research website

Source for [Mudit Gurnani's research website](https://research.muditgurnani.com/). Research data, methods and offline reproduction live separately in [research/](../research/README.md).

## Run and check locally

Node.js 22.13 or later is required; Node.js 24 is recommended. From the repository root:

```sh
cd site
npm ci
npm run dev
```

Open the local URL printed by the server. All subsequent commands in this README run from `site/`.

```sh
npm test
```

`npm test` checks TypeScript, builds the production site, and runs every `tests/*.test.mjs` file. This covers rendered pages, article navigation, anchors, release metadata, and numerical comparisons with the published research supplements. Clone the full repository: some evidence checks require the sibling `research/` directory. No test runs AI models or collects research data. GitHub Actions runs the same command with Node.js 24 for pull requests and pushes to `main`.

For a quick type check, run `npm run typecheck`. The Python exhibit-preservation script and its baseline are historical snapshots from before the approved interactive-chart redesign, not the current release gate. Do not regenerate that baseline to conceal numerical or prose changes.

## Article-to-source map

| Published article | Main presentation source | Research evidence |
| --- | --- | --- |
| [How AI negotiates Part 2](https://research.muditgurnani.com/research/how-ai-negotiates-part-2) | [components/negotiation-part2/](components/negotiation-part2/) | [negotiation Part 2 package](../research/negotiation-part-2/README.md) |
| [When a test report is wrong, is a warning enough?](https://research.muditgurnani.com/research/when-a-test-report-is-wrong) | [components/tool-error/](components/tool-error/) | [tool-error source archive](../research/tool-error-recovery/README.md) |
| [How AI negotiates](https://research.muditgurnani.com/research/how-ai-negotiates) | [components/negotiation/](components/negotiation/) | [negotiation package](../research/negotiation/README.md) |
| [Which financial AI answers should we review? Part 2](https://research.muditgurnani.com/research/which-financial-ai-answers-should-we-review-part-2) | [components/financial-answer-review-part-2/](components/financial-answer-review-part-2/) | [saved-results code package](../research/financial-answer-review-part-2/README.md); not a full empirical replay |
| [Which financial AI answers should we review?](https://research.muditgurnani.com/research/which-financial-ai-answers-should-we-review) | [components/financial-answer-review/](components/financial-answer-review/) and [content/financial-answer-review-draft.ts](content/financial-answer-review-draft.ts) | [checker sensitivity analysis](../research/financial-answer-review/checker-sensitivity/README.md) |
| [How to avoid false confidence in AI evaluations](https://research.muditgurnani.com/research/how-to-avoid-false-confidence-in-ai-evaluations) | [components/evaluation-reliability/](components/evaluation-reliability/) | [evaluation-reliability](../research/evaluation-reliability/README.md) |
| [When is more reasoning worth it?](https://research.muditgurnani.com/research/when-is-more-reasoning-worth-it) | [app/preview/reasoning-costs/](app/preview/reasoning-costs/) | [reasoning-costs](../research/reasoning-costs/README.md) |
| [How AI reviewers use test evidence](https://research.muditgurnani.com/research/how-ai-reviewers-use-test-evidence) | [content/evidence-review-v3.ts](content/evidence-review-v3.ts) and [components/article/](components/article/) | [ai-reviewers-test-evidence](../research/ai-reviewers-test-evidence/README.md) |

The permanent routes and sharing metadata are under [app/research/](app/research/). The reasoning article reuses the implementation in `app/preview/reasoning-costs/`; that older URL remains available for compatibility. It is not an additional article. Earlier reviewer content modules are still imported by the current article and are not unused drafts.

Other editing points:

- [components/research-home.tsx](components/research-home.tsx): homepage introduction and flagship summary.
- [content/research-catalog.ts](content/research-catalog.ts): article summaries, dates and newest-first ordering.
- [components/theme-toggle.tsx](components/theme-toggle.tsx) and [app/layout.tsx](app/layout.tsx): light-mode default and saved theme preference.
- [components/financial-answer-review/review-explorer.tsx](components/financial-answer-review/review-explorer.tsx): interactive charts and separate review table; data comes from [content/financial-review-data.ts](content/financial-review-data.ts).
- [lib/research-release.ts](lib/research-release.ts): publication state and canonical public origin.
- [content/publication.ts](content/publication.ts): reviewer article's publication links.
- [content/evaluation-reliability-results.json](content/evaluation-reliability-results.json), [content/reasoning-expanded.json](content/reasoning-expanded.json) and [content/evidence-figure-data.json](content/evidence-figure-data.json): article chart and table inputs. Changes must be checked against the corresponding research package, not edited to change a finding independently.
- [public/research-assets/](public/research-assets/): article illustrations and chart assets.

## Optional local review build

For a bundled preview without development-only imports:

```sh
npm run build:review
TEST_REVIEW=1 node --test tests/rendered-html.test.mjs
npm run start -- --hostname 127.0.0.1 --port 5173
```

This is a local-only review build with **noindex** metadata. Do not publish its output. An ordinary `npm run build` restores production output; run `npm test` before a release. To review on a phone on a trusted local network, use `--hostname 0.0.0.0` instead, which exposes the preview to that network.

## Hosting and release boundaries

The live website is managed through OpenAI Sites. [.openai/hosting.json](.openai/hosting.json) identifies the existing project; it contains no credential and does not grant deployment permission.

**A GitHub push does not deploy the website.** Publishing requires owner approval, a fresh production build, and the separate Sites save/deploy workflow. After deployment, check the homepage, every published article route, research links and sharing metadata on the public origin.

The custom domain is the public address; the `chatgpt.site` hostname is an alias for the same hosted project, not a second website to maintain. Use the custom domain for new public links.

### Keep GitHub and production in sync

1. Start from the latest saved Sites source and inspect GitHub for concurrent changes before editing.
2. Keep website changes under `site/`. Preserve frozen research inputs and results under `research/`.
3. Run `npm test` from the full repository, review the diff, and commit the source changes to GitHub.
4. When publishing is authorized, deploy that reviewed source through Sites and verify the public routes. Record the Sites version and source commit in the release or pull-request notes.
5. If another publishing agent updates Sites directly, reconcile its latest source back into GitHub before the next edit. Never publish a stale checkout over newer work.

The November 9, 2026 synchronization imported Sites version 48, source commit `d6c73b3ba16fa5f97da932d12e53d99ceff6bc1e`. Subsequent repository maintenance adds portable tests, CI and documentation without changing the published research evidence.

Displaying the articles needs no model API key, database or paid research run. Build output, installed dependencies and local credentials are excluded from Git. Historical publication and implementation changes remain available in Git history.

## Known dependency maintenance

The November 9, 2026 audit applied compatible transitive dependency updates without changing the pinned hosting framework. `npm audit` still reports 23 affected packages (10 high, 13 moderate). These are dependency advisories, not 23 confirmed exploitable website defects, but they are not a clean security bill either.

Remaining groups include Vinext/image tooling, React Server Components, Vite, Cloudflare/Wrangler tooling, TypeScript ESLint, and Drizzle tooling. Resolve these in a separately tested framework/dependency upgrade, then validate the Sites Worker build and staging behavior before deploying. Do not use `npm audit fix --force` indiscriminately: its proposed changes include downgrades and versions outside the pinned ranges. Re-run `npm audit` for current details; counts change as advisories and dependencies evolve.
