# Mudit Gurnani — AI Product Research

Source for Mudit Gurnani's research portfolio website and the public materials behind each
published study.

## Included pages

- `/` — the public research index
- `/research/agent-verification` — the complete Article 1 public narrative

The reproducibility materials for Article 1 live in
[`research/agent-verification`](research/agent-verification/README.md).

Only work ready for a public audience appears on the website. Unfinished studies, credentials,
private runtime state, and raw working directories are intentionally excluded from this repository.

## Local use

Requires Node.js `>=22.13.0`.

```bash
npm install
npm run dev
npm test
```

Set `NEXT_PUBLIC_SITE_URL` to the final public origin before deployment so Open Graph and X image
URLs use the correct host. `.env.example` shows the local value.

## Evidence-linked assets

- `public/verification-confirmatory.png` is copied from the reproducible Article 1 figure.
- `public/og.png` is the generated social-preview image.
- `public/og-prompt.txt` preserves the exact generation prompt.

## Publication boundary

This repository contains publication-ready source and public study materials. Website deployment
and a custom domain remain separate steps.
