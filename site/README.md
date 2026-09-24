# Research website

Source for [Mudit Gurnani's research website](https://mudit-gurnani-research.muditgurnani.chatgpt.site/). The local homepage features the new reasoning-cost study above the earlier test-evidence article.

## Run locally

Node.js 22.13 or later is required. Node.js 24 is recommended.

```sh
cd site
npm ci
npm run dev
```

Open the local URL printed by the server. Validate the production build, published article and draft protection with `npm test`.

## Review draft, not deployed

The development homepage shows both studies. The new article is available locally
at `/research/when-is-more-reasoning-worth-it`; the existing
`/preview/reasoning-costs` address remains available.

The article is intentionally blocked in production, and the production homepage
does not list it yet. Publication requires owner approval, removal of the article's
production guard, updating the homepage visibility rule and draft labels, and a
separate Sites deployment. A GitHub push does not publish the live website.

## Where to edit

- `components/research-home.tsx`: homepage introduction and study listing.
- `content/publication.ts`: article URL, GitHub and LinkedIn links.
- `content/evidence-review-v3.ts`: current article and appendix.
- `components/article/`: layout, index and data exhibits.
- `app/preview/reasoning-costs/`: shared reasoning article, figures and difficulty methods.
- `app/research/when-is-more-reasoning-worth-it/page.tsx`: planned permanent address, sharing the same article.
- `content/reasoning-expanded.json`: frozen chart/table inputs, paired with the [offline research supplement](../research/reasoning-costs/README.md).
- `public/research-assets/`: charts and illustration.

Supporting article modules preserve material used in the appendices. Draft routes are not additional published articles.

## Hosting

The live website is managed through OpenAI Sites. `.openai/hosting.json` identifies the existing project; it contains no credential and does not grant deployment permission. Contributors must not publish to that project without the owner's authorization.

GitHub is the maintained source repository. Pushing here does **not** automatically deploy the website. The owner builds, saves and deploys reviewed source through Sites. Public deployment is distinct from local preview.

Displaying the articles needs no model API key, database or paid research run. Generated build output and local credentials are excluded from Git.
