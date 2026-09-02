# AI Product Research

The public source for Mudit Gurnani's research website. It is intentionally small: the site, the
assets it serves, and the evidence package behind the published research note.

## Published work

- `/` — research index
- `/research/agent-verification` — *The Test Passed. The Patch Was Still Wrong.*
- [`research/agent-verification`](research/agent-verification/README.md) — frozen aggregate,
  study rules, technical note, and a zero-dependency consistency check

## Repository map

| Path | Purpose |
| --- | --- |
| `app/` | Website pages and styles |
| `public/` | Images served by the website |
| `research/agent-verification/` | Public evidence for the published study |
| `tests/` | Rendered-page and publication-boundary checks |

## Run locally

Requires Node.js `>=22.13.0` and Python 3.11 or newer.

```bash
npm install
npm run dev
npm test
python3 research/agent-verification/reproduce.py
```

Set `NEXT_PUBLIC_SITE_URL` to the public origin before deployment. `.env.example` contains the
local default.

## Publication boundary

This is a reader-facing repository, not a research workspace or artifact archive. It excludes
credentials, provider traces, cached repositories, private runtime state, unfinished studies, and
internal operating records. The included Python check validates the published numbers against the
frozen public aggregate; it does not recreate the model runs or official benchmark grading.
