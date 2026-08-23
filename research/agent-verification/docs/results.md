# Confirmatory result: executive brief

## Decision

Do not use the tested independent challenge agent to auto-approve coding-agent patches.

Validation forced the `reject_all` policy before held-out labels were opened. The primary
confirmatory claim therefore failed: 0 of 140 held-out attempts were auto-approved, providing no
automation coverage.

## Evidence

- 43 fresh SWE-rebench repositories: 8 validation and 35 held out.
- Two generator systems, two repetitions each: 172 total attempts.
- 140 held-out attempts produced 28 resolutions, 54 failed submitted patches, and 58 no-patch
  outcomes.
- Exploratory held-out diagnostic: 38 challenge passes contained 15 resolutions and 23 failures.
- Challenge-pass escaped-failure rate: 60.5% (95% Wilson interval 44.7%–74.4%).
- Challenge plus observed tests approved three patches; all three failed.
- Efficient system: 18/70 resolved for $2.59 generation cost.
- Strong system: 10/70 resolved for $8.95 generation cost.
- Efficient-first escalation on no patch added two resolutions for $3.02 incremental generation
  cost.

## Recommended product policy

1. Use the efficient generator first.
2. Retry or escalate only when no deliverable patch exists.
3. Use independent challenge generation to suggest additional tests, never as approval authority.
4. Fully test every submitted patch with an outcome-equivalent executable suite.
5. Escalate failed patches to repair or human review.

## Spend

- Model usage: $23.82 of the $75 approved ceiling.
- Sandbox conservative upper bound: $4.56 of the $10 ceiling.
- All-in audited upper amount: $28.38 of $85.
- Auto-reload remained disabled; no additional spending was authorized or used.

## Interpretation

This is a meaningful negative result. It rules out a tempting low-cost approval shortcut under the
frozen design, while identifying two deployable signals that remain useful: no-deliverable for
routing and comprehensive executable tests for acceptance.
