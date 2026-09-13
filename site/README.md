# Research website

Source for [Mudit Gurnani's research website](https://mudit-gurnani-research.muditgurnani.chatgpt.site/). A short introduction and one current research article.

## Run locally

Node.js 22.13 or later is required. Node.js 24 is recommended.

```sh
cd site
npm ci
npm run dev
```

Open the local URL printed by the server. Validate the production build and both routes with `npm test`.

## Where to edit

- `components/research-home.tsx`: homepage introduction and study listing.
- `content/publication.ts`: article URL, GitHub and LinkedIn links.
- `content/evidence-review-v3.ts`: current article and appendix.
- `components/article/`: layout, index and data exhibits.
- `public/research-assets/`: charts and illustration.

Supporting article modules preserve material used in the current appendix. They are not additional published article routes.

## Hosting

The live website is managed through OpenAI Sites. `.openai/hosting.json` identifies the existing project; it contains no credential and does not grant deployment permission. Contributors must not publish to that project without the owner's authorization.

GitHub is the maintained source repository. Pushing here does **not** automatically deploy the website. The owner builds, saves and deploys reviewed source through Sites. Public deployment is distinct from local preview.

Displaying the articles needs no model API key, database or paid research run. Generated build output and local credentials are excluded from Git.
