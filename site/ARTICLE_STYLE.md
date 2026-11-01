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
