# Research website

Source for [Mudit Gurnani's research website](https://research.muditgurnani.chatgpt.site/). The homepage links to three published articles. Research data, methods and offline reproduction live separately in [research/](../research/README.md).

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
node --test tests/evidence-figures.test.mjs
node --test tests/evaluation-sensitivity.test.mjs
node scripts/export-evaluation-sensitivity.mjs --check
```

`npm test` builds the production site and checks rendered pages, article navigation, anchors and release metadata. The separate figure check compares the reviewer article's presentation data with the published research supplement. Neither command runs AI models or collects research data.

The sensitivity test and export check verify all 23 assumption-check settings against the [audited research package](../research/evaluation-reliability-sensitivity/README.md). To include rendered-page checks, set `SENSITIVITY_REVIEW_URL` to the evaluation article's URL on a running local server. Confidence intervals remain in the appendix; the three main charts use the same 0–100% scale, with red for mistaken switches and green for correct switches.

## Article-to-source map

| Published article | Main presentation source | Research evidence |
| --- | --- | --- |
| [How to avoid false confidence in AI evaluations](https://research.muditgurnani.chatgpt.site/research/how-to-avoid-false-confidence-in-ai-evaluations) | [components/evaluation-reliability/](components/evaluation-reliability/) | [Baseline](../research/evaluation-reliability/README.md) and [assumption checks](../research/evaluation-reliability-sensitivity/README.md) |
| [When is more reasoning worth it?](https://research.muditgurnani.chatgpt.site/research/when-is-more-reasoning-worth-it) | [app/preview/reasoning-costs/](app/preview/reasoning-costs/) | [reasoning-costs](../research/reasoning-costs/README.md) |
| [How AI reviewers use test evidence](https://research.muditgurnani.chatgpt.site/research/how-ai-reviewers-use-test-evidence) | [content/evidence-review-v3.ts](content/evidence-review-v3.ts) and [components/article/](components/article/) | [ai-reviewers-test-evidence](../research/ai-reviewers-test-evidence/README.md) |

The permanent routes and sharing metadata are under [app/research/](app/research/). The reasoning article reuses the implementation in `app/preview/reasoning-costs/`; that older URL remains available for compatibility. It is not a fourth article. Earlier reviewer content modules are still imported by the current article and are not unused drafts.

Other editing points:

- [components/research-home.tsx](components/research-home.tsx): homepage introduction and article listing.
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

**A GitHub push does not deploy the website.** Publishing requires owner approval, a fresh production build, and the separate Sites save/deploy workflow. After deployment, check the homepage, all three article routes, research links and sharing metadata on the public origin.

Displaying the articles needs no model API key, database or paid research run. Build output, installed dependencies and local credentials are excluded from Git. Historical publication and implementation changes remain available in Git history.
