# Reproducing the confirmatory analysis without paid calls

These commands rebuild the final analysis and figure from the preserved, already graded evidence.
They do not call model APIs or create Vercel Sandboxes.

From the repository root:

```bash
uv sync --extra dev --extra empirical

uv run analyze-verification-confirmatory \
  --result data/empirical/verification_confirmatory_test_bundle_20260820/confirmatory_test_result.json \
  --model-state data/empirical/verification_confirmatory_test_batch_08_20260820/next_model_budget_state.json \
  --platform-state data/empirical/verification_confirmatory_test_bundle_20260820/next_platform_budget_state_after_grading.json \
  --output reports/confirmatory/confirmatory-analysis-reproduced.json

uv run create-verification-confirmatory-figures \
  --analysis reports/confirmatory/confirmatory-analysis.json \
  --output reports/figures/verification-confirmatory-reproduced.png

uv run audit-verification-confirmatory \
  --repo-root . \
  --output reports/confirmatory/robustness-audit-reproduced.json

uv run ruff check .
uv run pytest
```

## Authoritative artifacts

- Frozen design: `data/empirical/verification_confirmatory_frozen_v0_2/`
- Validation lock: `data/empirical/verification_confirmatory_validation_bundle_20260820/confirmatory_validation_result.json`
- Held-out pre-outcome receipt: `data/empirical/verification_confirmatory_test_bundle_20260820/preoutcome_bundle_receipt.json`
- Held-out result: `data/empirical/verification_confirmatory_test_bundle_20260820/confirmatory_test_result.json`
- Final analysis: `reports/confirmatory/confirmatory-analysis.json`
- Robustness audit: `reports/confirmatory/robustness-audit.json`
- Robustness report: `docs/verification-confirmatory-robustness-report.md`
- Final figure: `reports/figures/verification-confirmatory.png`
- Final platform state: `data/empirical/verification_confirmatory_test_bundle_20260820/next_platform_budget_state_after_grading.json`

## Integrity checks

The held-out bundle contains exactly 140 unique task-system-repetition identities. Its frozen
pre-outcome table explicitly records `official_outcomes_joined: false` and contains no official
outcome fields. All four official aggregates report zero evaluator errors and zero incomplete
instances. The final Vercel check found no active study Sandbox.

Rerunning generation or official grading is not necessary for analysis reproduction and would
incur new external cost. Do not run paid stages without new authorization.
