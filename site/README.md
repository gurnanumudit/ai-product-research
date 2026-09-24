# Research website

Source for [Mudit Gurnani's research website](https://mudit-gurnani-research.muditgurnani.chatgpt.site/). The local homepage features the new reasoning-cost study above the earlier test-evidence article.

## Run locally

Node.js 22.13 or later is required. Node.js 24 is recommended.

```sh
cd site
npm ci
npm run dev
```

Open the local URL printed by the server. Validate the production build, published article and draft protection with `npm test`. Figure-preservation checks run with `node --test tests/evidence-figures.test.mjs`.

## Review draft, not deployed

The development homepage shows both studies. The new article is available locally
at `/research/when-is-more-reasoning-worth-it`; the existing
`/preview/reasoning-costs` address remains available.

The article is intentionally blocked in the ordinary production build, and that
homepage does not list it yet. `lib/research-release.ts` owns the publication gate.
A GitHub push does not publish the live website.

For phone review without development/HMR module imports:

```sh
npm run build:review
TEST_REVIEW=1 node --test tests/rendered-html.test.mjs
npm run start -- --hostname 0.0.0.0 --port 5173
```

This is a **local-only review build**, with both articles and noindex metadata.
Keep it on the review machine; do not upload its output to Sites. A later ordinary
`npm run build` resets the output to the protected production state.
The browser review exposed a link-prefetch setup error; article navigation now uses
ordinary anchors rather than client-router prefetching. The reported phone import
failure could not be reproduced in the desktop browser;
the bundled preview removes development-only imports but still needs a check on
the user's phone.

After explicit owner approval: set `reasoningPublished` to true, confirm the actual
publication date and draft-label removal, adjust the draft-protection tests for
the approved release, and run a fresh ordinary production build. Then use a
separate Sites deployment and verify the public homepage and both article URLs.
The prior authoring checkout is no longer the phone-review source; this maintained
GitHub checkout supplies the bundled preview.

## Where to edit

- `components/research-home.tsx`: homepage introduction and study listing.
- `content/publication.ts`: article URL, GitHub and LinkedIn links.
- `content/evidence-review-v3.ts`: current article and appendix.
- `components/article/`: layout, index and data exhibits.
- `content/evidence-figure-data.json`: presentation data for the responsive figures.
  Estimates and intervals are checked against the published supplement and
  original SVG figures; the research records are unchanged.
- `app/preview/reasoning-costs/`: shared reasoning article, figures and difficulty methods.
- `app/research/when-is-more-reasoning-worth-it/page.tsx`: planned permanent address, sharing the same article.
- `content/reasoning-expanded.json`: frozen chart/table inputs, paired with the [offline research supplement](../research/reasoning-costs/README.md).
- `public/research-assets/`: charts and illustration.

Supporting article modules preserve material used in the appendices. Draft routes are not additional published articles.

## Hosting

The live website is managed through OpenAI Sites. `.openai/hosting.json` identifies the existing project; it contains no credential and does not grant deployment permission. Contributors must not publish to that project without the owner's authorization.

GitHub is the maintained source repository. Pushing here does **not** automatically deploy the website. The owner builds, saves and deploys reviewed source through Sites. Public deployment is distinct from local preview.

Displaying the articles needs no model API key, database or paid research run. Generated build output and local credentials are excluded from Git.
