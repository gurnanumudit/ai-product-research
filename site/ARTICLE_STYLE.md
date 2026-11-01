# Shared research article format

All published articles use the negotiation article as the reading template. The shared rules live in `components/article/standard.css`, imported once in the root layout and scoped to `data-research-article`. Do not create competing article typography rules.

## Page structure

Use the shared data attributes for header, hero, eyebrow, cover, caption, dek, byline, resources, layout, body, index and footer. Place the cover before the title. Use a left-aligned title, serif introduction, compact byline and resource links. Keep the homepage outside this scope.

Use `ArticleIndex` for a sticky desktop index and a compact index above the text on phones. Use `ArticleNavigation` for fragment links: it opens enclosing appendix disclosures before scrolling, including repeated clicks and direct deep links.

## Typography and figures

Use the shared sans-serif headings and serif reading text, common reading width, spacing and captions. At 760px and below, switch to one column. Preserve chart scales, colors, controls, data and scientific wording. Wide tables and charts must scroll inside their own containers rather than widen the page.

## Resource links

Use “Research code” for the existing study-specific GitHub directory. Use “Data and methods” for the local appendix containing methods, data and reproducibility details. These are distinct destinations. Keep series links where useful. Never label an internal anchor as an external link.

## Before publishing

Build and run the rendered-page checks. Verify all seven pages, their internal anchors, appendix opening, interactive figures and mobile overflow. Presentation changes must preserve research text, figures, data and conclusions. Synchronize the published source with the GitHub site directory.

## Interactive exhibits

The five earlier articles opt into `ExhibitEnhancements`. `exhibits.css` provides shared figure frames, table typography, sticky table headers, mobile scrolling and full-screen panels. Controls progressively enhance the original published DOM; with JavaScript unavailable, the underlying figures and tables remain readable.

Use `data-exhibit-panel` on whole chart panels, labeled with the existing model or difficulty name. Inspection uses an existing SVG point title or `data-exhibit-value`, derived from the same data and formatting already used by the figure. Never regenerate results, change axis limits, pool intervals or silently recalculate a chart when switching panels. All panels are visible initially. Original captions and caveats stay with the figure, including in expanded view.

Table search hides matching rows only and always displays the visible/total row count plus Reset. Tables with merged body cells are not filtered, to preserve group context. Expansion keeps the original controls, traps keyboard focus, supports Escape and returns focus on closing.

For presentation-only changes, run `python3 tests/check-exhibit-preservation.py --origin http://localhost:8772` against a production preview. It compares research text, table cells, SVG geometry and encoded values with the pre-formatting baseline. Update this baseline only for an explicitly approved information change, never to make a failed presentation check pass.

## Appendix navigation

Each appendix topic uses native `details` with a meaningful `summary` and a stable fragment ID. Omit `open`: topics are collapsed in the initial HTML and expand only when readers choose them. Link methods, definitions, exact results and limitations from the relevant main-text passage, including links to nested topics. Shared ArticleNavigation opens only the target and its enclosing disclosures before scrolling, including direct URLs, browser back/forward and repeated clicks. Keep existing return links to the main text. Do not hide supporting evidence behind JavaScript-only controls or change its contents. Use the shared appendix styles for headings and disclosure indicators.
