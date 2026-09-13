# Provenance, attribution and release limits

## What was transformed

The package is an allowlisted numerical extract of the preserved study archive: 60 public benchmark label records and 1,736 attempted response classifications. Source report URLs and hashes bind each label to a specific public evaluation; patch URLs and original/normalized SHA-256 values bind that evaluation to the selected patch. Reports, patches, issue text, trajectories and reviewer prose are not redistributed here.

The publication's `article-statistics.json` and audited `figure-data.json` supply the frozen comparison targets. Their source hashes, plus the source analysis and figure-script hashes, are in `data/archive-audit.json`. Paths identifying a local user have been removed. The supplementary statistical functions and seeds were retained, with a portable input loader and private-path checks removed. The SVG renderer retains the chart geometry while removing the Pillow/macOS-font dependency. The original E−D calculation was implemented directly from the same task-level rules and seeds and verified against all eight saved chart rows.

Direct local audit checked all 1,736 original terminal hashes; the validity flag and canonical decision for every attempted response; all 60 label-report hashes and resolved flags; and every selected patch hash against its original roster. This is an audit receipt, not a substitute for providing the original records.

## Public upstream materials

1. **Alejandro Cuadron and coauthors, O1 native-tool-calling results.** [Dataset](https://huggingface.co/datasets/AlexCuadron/SWE-Bench-Verified-O1-native-tool-calling-reasoning-high-results), pinned revision `1467c51c3b4f506d212509489704a1f2934843a1`. Its archived dataset card declares [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This package extracts task identifiers, patch fingerprints and resolved flags rather than redistributing source text. The native card's embedded citation names the reasoning dataset; the actual pinned native URL above and per-record URLs are authoritative for this package's provenance.
2. **Alejandro Cuadron and coauthors, O1 reasoning-high results.** [Dataset](https://huggingface.co/datasets/AlexCuadron/SWE-Bench-Verified-O1-reasoning-high-results), pinned revision `a57cfefbb319d0119bb92b3c81d150653747d12e`. Its archived card also declares CC BY 4.0. The card credits Alejandro Cuadron, Dacheng Li, Xingyao Wang, Siyuan Zhuang, Yichuan Wang, Luis G. Schroeder, Tian Xia, Aditya Desai, Ion Stoica, Graham Neubig and Joseph E. Gonzalez.
3. **Live-SWE-agent Gemini submission.** Public evaluation receipts are under the SWE-bench submission `verified/20251120_livesweagent_gemini-3-pro-preview`; exact per-task URLs and content hashes are included. The related [trajectory dataset](https://huggingface.co/datasets/livesweagent/gemini_3_pro_swebench_verified_traj) at revision `607040a2d2a5fb8e857cb4990213362d84c111f6` has an archived card declaring MIT. That card is not treated as conclusive licensing of separately hosted S3 evaluation artifacts. S3 URLs are not revision-pinned; hashes identify the bytes used in the study.
4. **SWE-bench Verified and original repositories.** The task benchmark is [SWE-bench Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified). Selected tasks refer to Matplotlib, scikit-learn, pylint, requests, seaborn and Flask. The package does not assume a benchmark or dataset license overrides rights in upstream issue text, source code or logs.

License declarations above describe archived source cards inspected during package preparation; they are not a comprehensive rights opinion or a current-service-terms audit. No fresh network retrieval was needed to reproduce the numbers.

## Release scope

Original analysis code and documentation are covered by the repository's MIT license, copyright 2026 Mudit Gurnani. Data files contain study-derived categorical decisions and numerical summaries, together with attributed public benchmark outcome metadata. Publication does not relicense upstream datasets, issue text, patches, execution logs, provider models or other third-party material; applicable third-party rights and notices remain in force.

Raw prompts, response prose, patches and execution logs are excluded, as are credentials, contact details and usage/billing metadata. The separately hosted Live-SWE-agent source files are linked and fingerprinted, not redistributed or asserted to be MIT-licensed. Extending the package to include those original files requires a source-specific review.

This package reproduces published numerical results from preserved classifications. It does not rerun the model experiment, reconstruct the original selection population and collection requests, or independently establish software correctness. No provider endorsement is implied.
