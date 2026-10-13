# Financial answer review — version 2

Code-only reproduction package for a financial-answer review study. It compares mechanical verification with model confidence at equal review capacity. It does not assume that every warning is an error, that a reviewed answer is corrected, or that verification wins.

The earlier Stage A package one directory above is preserved. This directory contains no dataset, manual annotations, model outputs or effectiveness estimates. Scientific results and source-level interpretation require separately reviewed evidence; software tests alone do not establish effectiveness.

## Exact code and portable helpers

`implementation/` contains 14 byte-identical Python files from the reviewed version2 freeze: the schema/prompt/checker/scorer/policies, guarded runner, all-planned summary, historical training diagnostic and their tests. `SOURCE-MANIFEST.json` distinguishes exact copies from adaptations and records source and destination hashes. The historical `implementation/training_check.py` assumes the original sibling archive layout; use the separate portable helper below instead of editing that historical file.

`reproduce/prepare_dev.py` is an unchanged development-data preparation script. It verifies the pinned source and requires a fresh destination. `reproduce/training_check.py` and `reproduce/assemble_annotations.py` are explicitly adapted local-file helpers: their inputs are provided as command-line paths and their outputs go into fresh, non-symlinked directories outside the input archive. The assembler also rejects truncated or duplicate input collections. Neither adaptation changes the arithmetic, scoring tolerances, prompt, warning categories, ranking candidates or selection rule. They are not byte-identical historical executables.

The helpers do not create manual source judgments. The annotation assembler consumes a separately reviewed source-first decision file, revisions and reconciliation records; it is not an automatic gold-label repair tool. The original reconciliation script embeds case-specific reference answers and adjudication notes and is deliberately omitted. Archive-dependent tests are also omitted, rather than claiming they run without their private local inputs.

## Offline tests

From this `v2` directory, with Python3.11 or newer:

```sh
cd implementation
python3 -m unittest discover -s tests -v
python3 -m unittest test_runner test_summary test_v2 -v
cd ..
python3 -m unittest discover -s reproduce -v
```

There are39 package tests,58 transport/report/version2 tests and37 portable-helper tests:134 total. The latter include29 final-test preparation/assembly checks. Fixtures are synthetic, provider calls are mocked, and no credentials or dataset are needed. Cost messages printed by mocked transport tests are fixtures, not external spending. The optional packages for transport/preflight tests are pinned in `requirements-runner.txt`; install them in an isolated environment if needed. The tokenizer must already have its local `o200k_base` cache for the synthetic preflight test. Cache misses fail instead of downloading during preflight. No dependencies are installed by this repository's tests.

The portable tests cover existing-output refusal before input reading, symlink refusal, keeping outputs outside input archives, unchanged rational arithmetic/precision, source-hash mismatch, truncated input rejection, a synthetic50-answer training replay, and preparation refusal before any network request when its destination already exists.

## Data and local reproduction boundaries

The source pin is [FinQA commit0f16e2867befa6840783e58be38c9efb9229d742](https://github.com/czyssrs/FinQA/tree/0f16e2867befa6840783e58be38c9efb9229d742). No source acquisition is part of the offline tests. The optional preparation script can acquire only the pinned public development split after a separately reviewed selection protocol is supplied:

```sh
python3 reproduce/prepare_dev.py --protocol /absolute/path/to/reviewed-selection-protocol.json --out /absolute/path/to/new-dev-archive
```

The protocol must satisfy the script's explicit source hash and pre-acquisition review checks. It supplies stratum quotas, deterministic seed and prospective prior-exposure exclusions; no internal protocol or approval is distributed here. Downloading does not qualify references or authorize generation. FinQA and underlying financial reports retain their own rights.

Two local-file operations require existing archives and create new output directories; neither downloads data or calls a model:

```sh
python3 reproduce/training_check.py --stage /absolute/path/to/existing-stage-a-archive --out /absolute/path/to/new-training-diagnostics
python3 reproduce/assemble_annotations.py --data-dir /absolute/path/to/existing-reviewed-dev-archive --source-first-sha256 REVIEWED_64_HEX_DIGEST --out /absolute/path/to/new-annotation-output
```

The training archive must contain the original50 answering inputs, saved summary and ordered response files in the historical `data/` and `runs/pilot-01/` layout. The development archive must contain200 aligned inputs, original references, selection metadata, source-first decisions, reference reconciliation and pinned source file; optional revisions remain evaluator-only. The helpers produce `training-diagnostics.json` and `annotations.json`, respectively. Existing destinations and symlink paths are refused; a failed run may leave a fresh empty directory that must not be reused automatically. Assembly leaves review status pending and does not certify its caller-supplied decisions.

### Offline final-test preparation

`reproduce/prepare_test.py` is a separate offline adaptation of the historical final-frame preparer. It reads an already acquired local source, supplied protocol and supplied exposure snapshot. It adds no download, credential or provider path. Its natural-frame census, eligibility, deterministic order, report/page/company flags and fixed stratified audit selection retain the historical logic; they do not impose development's equal-stratum quotas. Exact previously exposed IDs are excluded, while other questions in the same report remain eligible and flagged.

```sh
python3 reproduce/prepare_test.py --source /absolute/archive/source/test.json --protocol /absolute/archive/test-protocol.json --exposure /absolute/archive/test-exposure.json --bindings /absolute/archive/intake-bindings.json --out /absolute/new-test-preparation
```

The binding file must be a JSON object with exactly `source`, `protocol` and `exposure`, each mapped to its independently recorded lowercase SHA256. The source must also match the protocol's `source_sha256`, `source_expected_bytes` and `source_expected_n`. The protocol supplies `seed`, `strata`, `maximum_selected_n` and `independent_audit` (`seed`, `n_per_stratum`). The exposure object supplies `protocol_sha256`, `groups` of prior `ids`/`reports`/`pages`/`companies`, the sorted `excluded_exact_ids` union, its `excluded_exact_id_count` and `union_ids_sha256`. The union hash is SHA256 of compact JSON for the sorted union plus a newline. Group metadata and the union are checked against the supplied IDs. Paths mentioned inside a protocol or exposure record are not automatically opened.

The four generated files separate neutral answering inputs from original evaluator-only QA, selection metadata and independent audit IDs. The source is not recopied. Output must be fresh, non-symlinked, and outside the parent directories of all supplied files. Put the supplied files in a dedicated archive, with a separate output directory. Local hash bindings verify identity, not permission, scientific approval, source completeness or reference quality.

### Offline final source-first assembly

```sh
python3 reproduce/assemble_test_annotations.py --archive /absolute/existing-reviewed-test-archive --bindings /absolute/existing-reviewed-test-archive/assembly-bindings.json --expected-n 1127 --out /absolute/new-test-annotations
```

The required binding keys are the exact relative filenames `source/test.json`, `source-first-decisions.jsonl`, `SOURCE-FIRST-FREEZE.json`, `inputs.json`, `gold.json`, `selection.json`, `source-review-revisions.json` and `reference-review-notes.json`. Every value is an independently recorded SHA256. These files are supplied locally, not distributed here. An empty review-note or revision list must be explicit, not silently invented. `SOURCE-FIRST-FREEZE.json` must bind the first-pass digest. Every planned row must remain aligned; duplicate IDs, duplicate/out-of-range revision or note indices, mismatched order, altered inputs and incomplete collections are rejected.

The first-pass JSONL contains ordered `i` indices and source-review decisions (`formula`, `unit`, `scale`, `reason`, `evidence` location IDs, with optional `exact_count`). Revisions are separate records `{i, decision: {...}}`, applied without altering that first pass; review notes contain `i` and `category` plus their supplied interpretation. These are independent source judgments, not outputs this code can reconstruct from released answers. The adapter preserves unresolved rows, original QA, evidence, revisions and source-review notes. It emits evaluator-only `annotations.json`, diagnostic `reference-reconciliation.json` and a local reproduction manifest into the new directory. Scoring remains separate from reference diagnostics, which never infer percent conversion by numerical closeness. Review status remains pending; no caller-supplied judgment is certified.

Rational targets retain the original restricted arithmetic and precision conventions. The historical fractional-power exception remains limited to the original three reviewed row indices and exact positive five-year CAGR expression form, evaluated at80 and100 digits with agreement better than `1e-70` and rendered at60 digits. Assembly additionally requires the original first-pass/input/gold digests for these cases. The row guards contain no source values and are not a general license to apply CAGR to other records; they do not modify the operational answer checker. Synthetic tests exercise the numeric helper and rejection of unauthorized new-archive powers, not the undistributed empirical annotations.

Both final helpers are explicit safe-output adaptations, not the historical executables and not new scientific policies. Their manifests record source-script and supplied-input identities; output metadata will differ from historical internal receipts. The original `freeze_test_data.py` is omitted because it embeds review/resource receipt statements, not a needed numerical algorithm. The historical `test_test_data.py` requires the undistributed archive and embeds audit counts; it is omitted rather than advertised as independently runnable. The new synthetic suite covers reusable safeguards and arithmetic, not a replay of those private archive tests. No real archive replay was used to validate this delivery, and no published efficacy claim follows from passing software tests.

## Study contract encoded in the implementation

Verification has three distinct concern categories: evidence, arithmetic and unused inputs. A counts categories; B prioritizes arithmetic, then evidence, then unused. Operand-level details do not multiply the evidence risk category. Normalized source-number matching preserves sign and percent meaning; unit-bearing quotations retain the displayed operand value, with conversions explicit in the derivation. Mechanical checks do not prove that the correct metric, year or denominator was chosen.

At primary20% review, common mandatory abstentions consume `floor(.20*N)` slots. More mandatory cases than slots makes the operating point infeasible. Ten and30% are secondary. Development selects the feasible verification candidate with the smaller accepted-known-mismatch plus accepted-unresolved count; ties choose A. The100 fixed tie seeds report sensitivity, not favorable-seed selection. Final evaluation requires a single separately frozen candidate.

The scorer uses explicitly qualified reference values, units, scales and precision provenance; raw benchmark execution answers are not automatic truth. It separates numerical mismatches from unresolved references, unit-contract mismatches and operational failures. Even a frozen-contract mismatch can be sensitive to source rounding or financial-sign conventions; it is not necessarily an unambiguous financial reasoning error.

The summary keeps every planned question. Paired unresolved-label ranges cancel shared unknown decisions, rather than subtracting two loose marginal ranges. The1000-replicate report/company resampling reranks whole batches, keeps duplicated-original unknown truth shared, and retains infeasible replicates explicitly. These are approximate benchmark-resampling and unresolved-label accounting analyses, not causal or production-generalization confidence claims. One response per question does not measure repeated-generation variation.

## Request and summary safety

The preserved runner is dry-run by default. It requires explicit inputs, annotations, group metadata, phase, count, candidate, protocol, budget and a new output directory. Execution needs a separately reviewed exact approval binding code, runtime, ordered requests and data hashes. No such approval, budget, execution marker or credential is included. The historical model/pricing constants are provenance, not current recommendations or permission to call a provider.

There is no automatic retry or crash resume. Phase-specific one-use markers and the fixed budget lock are written one directory above `implementation/`. Do not delete them to bypass a stopped run, and never execute from an evidence archive or an unreviewed copied approval. A separately gated final phase is not automatically authorized by successful development.

For a saved run, create a fresh local output folder before invoking the unchanged summarizer; the summary file itself must not exist:

```sh
mkdir /absolute/path/to/new-summary-folder
python3 implementation/summarize_pilot.py --inputs /absolute/path/to/inputs.json --adjudication /absolute/path/to/annotations.json --groups /absolute/path/to/selection.json --run /absolute/path/to/saved-run --out /absolute/path/to/new-summary-folder/summary.json
```

Code is covered by the repository's [MIT license](../../../LICENSE). Data rights are separate. Raw reports, selected financial passages, annotation decisions, request/response traces, empirical diagnostics, approvals, budgets, credentials and internal coordination records are excluded. This package does not modify or publish a website article.
