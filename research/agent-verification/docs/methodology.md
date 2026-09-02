# Public verification note

This repository publishes a compact evidence package, not the private execution workspace. The
public check verifies that the article's headline numbers agree with the frozen processed result.
It makes no network calls and does not regenerate patches or rerun official grading.

From the repository root:

```bash
python3 research/agent-verification/reproduce.py
```

The script reads `data/confirmatory-analysis.json` and checks the reported sample size, verifier
decisions, outcome counts, error counts, and rates. A passing check means the article and the
published aggregate are internally consistent. It does not independently prove that the source
model traces or benchmark labels are correct.

## Frozen design

- **Question:** Was a pass from the tested independent verifier safe enough to approve an
  AI-generated patch automatically?
- **Tasks:** 35 recent SWE-rebench software issues.
- **Patch generators:** GPT-5.4 Mini and GPT-5.4, with two attempts per task.
- **Verifier:** Claude Opus 4.6, shown the issue, repository, and proposed patch but not the final
  benchmark outcome.
- **Outcome label:** SWE-rebench's separate executable evaluation.
- **Decision rule:** The verifier had to return a usable approval for a patch to count as passed.

The preregistered rules are preserved in `data/preregistration.json`. The processed result used by
the article is preserved in `data/confirmatory-analysis.json`.

## Evidence boundary

The private execution record included model responses, benchmark grading outputs, runtime state,
and integrity receipts. Those materials are not included here because they contain provider traces,
large cached repositories, or internal operating records. Consequently, this public snapshot
supports inspection of the frozen design and reported aggregate, plus a deterministic consistency
check. A full raw-data reanalysis would require a separately reviewed release package.

No paid stage should be rerun merely to use this public repository.
