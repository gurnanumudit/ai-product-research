# Tool-error article and homepage: release preparation

Status: local preview prepared for owner review. Nothing deployed or pushed by this change.

## Proposed homepage

Keep “Understanding AI through evidence.” Describe the work as experiments, simulations and data analysis spanning AI evaluation, agent behavior and economic tradeoffs.

Use Latest research, Featured research and All research. Featured selections are “How AI negotiates” (October 29) and “How to avoid false confidence in AI evaluations” (September 30). These selections remain visible when a newer article appears. Use “Research code” consistently for the repository link.

## Article package

Route: `/research/when-a-test-report-is-wrong`.

The article is a site derivative of reviewed draft v7. The numerical chart data are unchanged. It preserves the 720 outcomes, all 15 comparisons, amended-completion provenance, partial-cost accounting and scientific limitations. Small precision edits clarify net additional successes, aggregate token costs and the limits of the stale-report condition.

Only these article assets are prepared for public delivery:

- `research-assets/tool-error/chart-data-v2.json`: unchanged aggregate chart values.
- `research-assets/tool-error/chart-data-v2.csv`: all 15 comparisons.
- `research-assets/tool-error/review-summary.json`: review scope and source hashes.
- `research-assets/tool-error/cover.svg` and `cover.png`: original conceptual cover, not an observed study example.

The full operational archive, per-task records, requests, receipts and private benchmark inputs are excluded. Internal evidence links were removed. The historical research-code link remains pinned to commit `ba47d5b22b1dbae6476ca0e25166adb30b20ab76`.

## Preview and release checks

Use Node >=22.13. `npm run build:review` prepares a noindex local preview. `npm run start -- --port 8769` serves it. `TEST_REVIEW=1 node --test tests/rendered-html.test.mjs` checks the preview and existing published routes.

A normal production build deliberately returns 404 for the unpublished article and does not list it as latest. The homepage redesign is still only a local proposal, not a deployed change. Normal-build rendered tests also passed.

Before a future owner-approved release:

1. Reconfirm the current live site version and upstream branch to avoid overwriting another publication. At preparation, live version was 20 and GitHub main was `fb5bd83a3cc3fa9663f8a52c95e19b1a06d8d559`.
2. Apply the owner’s homepage feedback. Confirm both the article and homepage are approved to publish.
3. Set the actual publication date; remove article preview labels; replace the local-review gate with the approved publication state. Update indexing and homepage latest/archive state. Preserve draft history and source evidence.
4. Repeat the normal-build route, link, metadata and asset checks. Prepare the GitHub publication commit/PR and Sites source artifact using the official source/build workflow. Do not deploy the review build.
5. Deploy only after approval, then check the public homepage, article, interactive figures, downloads and social card. Record the deployed version and final GitHub identity.

No new experimental execution is needed or authorized by this preparation.
