# Interactive article components

Source for the unpublished article preview, revision 7. This directory adds presentation code only; it does not deploy or publish the article. The manuscript and chart dataset are supplied separately and are not bundled here.

- `article.js`: four-condition grouped success bars, a condition/workflow walkthrough, paired-interval and dollars/testing-minutes selectors, and expandable figures.
- `article.css`: article layout and compact/mobile chart styles. The draft explains the design as a sequential narrative, without dimension panels or a sample-size matrix.
- `reference-style.css`: existing research-site visual styles reused by the preview.
- `build_preview.py`: assembles supplied HTML/data with these assets. It has no model, grading or statistical-analysis functionality.

The chart reads recorded counts and frozen intervals from data. It does not estimate new intervals. Gray-green always denotes baseline, terracotta warning and teal verification. The walkthrough is explicitly an invented explanation, not an experimental transcript.

The local template must include the expected figure mounts and one each of `/* STYLE */`, `/* DATA */`, `/* SCRIPT */`. The JSON supplies `strata` and `resources` as consumed by the renderer. Dataset and manuscript release are separate from this code delivery.

```sh
python3 research/tool-error-recovery/article-ui/build_preview.py --template /path/to/article-template.html --data /path/to/chart-data.json --output /path/to/new-preview.html
```

Open the resulting preview through a local server. Relative evidence/download links still need the corresponding separately supplied files. This is not a complete public article package.

Shared writing and link conventions: [Research article style](../../ARTICLE-STYLE.md).
