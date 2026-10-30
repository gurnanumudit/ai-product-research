Which financial AI answers should we review? Part 2
Mudit Gurnani. Published October 21, 2026. Pilot began October 17.

Reproduce the saved-answer warning diagnostic (Python 3, standard library only):
  python3 diagnose.py --output diagnostic-reproduced.json
Choose a fresh output filename. The script verifies the bundled input checksum.
The eight cells must equal diagnostic.json; input_sha256 is additional provenance.

Reproduce the combined article summaries and plotted values (Node.js 22+):
  node reproduce.mjs

Files:
- study-tables.json: eight dataset/configuration rows, counts and rounded intervals.
- saved-estimates.json: original saved estimates, intervals and tie sensitivity.
- combined-plot-data.json: saved inputs for the article's combined presentation.
- figure-metrics.js: exact matches outside review and conditional-random expectations.
- diagnostic-input.json: de-identified grade, usability, warning and selected-row fields.
- diagnostic.json: independently reviewed diagnostic output.
- diagnose.py and reproduce.mjs: runnable reproduction code.

Scope and limitations:
This package reproduces the diagnostic and displayed summaries from saved results.
It does not generate model answers or rerun the original paired bootstrap analysis.
No prompts, source reports, raw model responses, provider IDs or credentials are included.
Intervals are separate pointwise 95% intervals per dataset; no combined interval is claimed.
Queues were formed separately for FinQA and TAT-QA before summing displayed counts.
Mini used low reasoning; Sol, Sonnet and Gemini used medium. Configurations are not
an experiment isolating model intelligence or reasoning effort. Warning diagnostics
are descriptive, post-study analysis; frozen primary outcomes and rules are unchanged.

Original saved-summary SHA256:
a15fa1d7d746ecb32ebfb122a54c4bbcbb878a7e8b2f76b7199d19f9b920d0be
