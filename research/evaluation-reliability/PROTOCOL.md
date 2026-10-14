# Phase 1 protocol: AI experiment decision reliability

Version 1, September 27, 2026. **Frozen after independent design challenge, before randomized study results; lead records SHA-256 in the coordination ledger.** Owner EVAL. Authority and exclusions: [AUTHORIZATION.md](AUTHORIZATION.md). No production model, user or private benchmark outcomes are used.

## Question, target and truth

Study the decisions from one fixed paired A/B comparison, not candidate search. Primary estimand is the **equal-context mean difference in qualified-completion probability**, `Delta = E_g[mean_i(Y_Bgi - Y_Agi)]`, in a specified synthetic population with five paired questions per context. Contexts are independent by construction. Outcome 0 is an observed unsuccessful qualified completion; a lost log is missing measurement, not an observed zero. This is neither human productivity nor measured economic value.

A product would require improvement greater than `tau=.02` (two percentage points) to merit a change. This hurdle is a declared illustrative preference, not estimated willingness-to-pay, an actual deployment authorization or a universal minimum effect. **Truth:** ship-worthy iff `Delta > tau`; otherwise hold-worthy, including equality. The tested values `Delta=-.04,.02,.10` represent below, at and above this hurdle.

Statistical actions are distinct: **ship** if the lower confidence limit is strictly above tau; **evidence-hold** if the upper limit is strictly below tau; otherwise **inconclusive**. “Hold” here means evidence against clearing the hurdle, not simply delaying release while evidence is inconclusive. First crossing wins; later observations do not reverse the recorded decision. At equality the truth class is hold-worthy, but many well-behaved tests will be inconclusive rather than demonstrate a negative contrast.

For each cohort/method, exactly one exclusive outcome is recorded: false ship (ship on hold-worthy truth), false hold (evidence-hold on ship-worthy truth), correct decision, or inconclusive. Report correct-ship and correct-hold separately too. A secondary, explicitly labeled **forced binary** interpretation recodes only the final row-IID method's inconclusives as operational hold. This shows the consequence of treating “not significant” as “not worth shipping”; it is not a seventh estimator or evidence that a rational delay is necessarily a business mistake.

## Known-truth generator

Independent contexts have `C_g` uniformly -1/+1 and independent common-success `Z_g ~ Bernoulli(.5)`. Conditional on C, five independent paired differences d have probabilities

`P(d=-1)=(q-Delta-h*C)/2`, `P(d=0)=1-q`, `P(d=1)=(q+Delta+h*C)/2`, with `q=.5`.

Map -1 to `(A,B)=(1,0)`, +1 to `(0,1)`, zero to `(Z,Z)`. Thus `E[D]=Delta`, `Cov(d_i,d_j)=h^2`, and `Var(D)=(q-Delta^2)/5+4*h^2/5`. Probabilities require `abs(Delta +/- h)<=q`. At h=0 raw outcomes may share difficulty but paired differences are independent; the design does not force clustering to harm every method.

This is a **mechanism-based stress test**, not an empirically calibrated distribution of AI product traffic. Heterogeneity, missingness and duplication rates were chosen for transparent failure mechanisms before results. Do not estimate their prevalence or transfer the resulting decision rates to a real product.

## Frozen-sized scenario set

Five telemetry/dependence mechanisms crossed with the three effects above: **15 worlds**, no further scenario expansion. Every cohort contains **H=200 intended contexts**, five pairs each. The first two mechanisms isolate paired-difference dependence; later mechanisms each add one fault to the clustered law.

| Mechanism/order | h | Observed B outcome log |
|---|---:|---|
| 0 clean_iid | 0 | Complete, one record per intended pair |
| 1 clustered_complete | .30 | Complete, one record per intended pair |
| 2 clustered_mcar | .30 | Independently missing with probability .20 |
| 3 clustered_mnar | .30 | Missing with probability .40 when true B=0 and .05 when true B=1 |
| 4 clustered_duplicate | .30 | Complete; B=1 creates two identical same-ID records, B=0 creates one |

All A outcomes and the intended `(context_id, question_id)` ledger remain available. Duplication creates duplicate joined A/B pairs when naive analyses join B events to A; it does not create additional assignments. Missing B removes that complete pair from naive analyses. The fault generator may use hidden B to construct MNAR, but the analysis receives only intended IDs, A and observable B records. It cannot see lost grades, mechanism labels, Delta or oracle truth.

Draw order, frozen for reproducibility: one `random.Random(seed)` continuous stream per world, cohort then context order. First generate all H truth contexts: for each draw C (`u<.5 => -1`), Z (`u<.5 => 1`), then five categorical differences using cumulative probabilities and strict `<`. Next draw one logging-loss uniform per original question pair in context-major order, consumed in **every** mechanism even if no record can be lost. Thus each cohort consumes exactly 2,400 uniforms. Duplication uses no extra random draws. Seed `2709271800 + world_index`; world index is `3*mechanism_index + effect_index` for effects in order `(-.04,.02,.10)`. **2,000 cohorts/world: 30,000 distinct cohorts, 6,000,000 contexts, 30,000,000 paired questions and 60,000,000 binary outcomes.** Complete streams are generated regardless of early decision.

These are the only reporting worlds/seeds. Deterministic boundary/analytic fixtures and fixed prefixes/replays of these seeds are allowed for code checks. No extra random seed search, result-based change in replication count, or method tuning. Preserve errors and document repairs. Exact same-seed replay is reproducibility, not additional independent evidence.

## Six methods, same cohort and intended target

At intended look t, only assigned contexts 1..t are visible; missing/empty contexts do not advance or replace a look. For each vector x, use sample mean, sample variance with denominator n-1, and `mean +/- z*SD/sqrt(n)`. Fewer than two observations or zero/nonpositive estimated variance produces inconclusive, not a zero-width certificate. All intervals are **normal approximations**, not finite-sample guarantees.

| Method | Input vector | Looks / critical value |
|---|---|---|
| row_fixed | All observed joined paired differences, including duplicate rows | t=200; z=Phi^-1(.975) |
| row_peek | Same | t=40,80,120,160,200; same z each time |
| context_fixed | Mean observed joined difference within each nonempty context, then equal context weights | t=200; z=Phi^-1(.975) |
| context_peek | Same | Five looks; same z each time |
| context_adjusted | Same | Five looks; z=Phi^-1(1-.05/(2*5)) |
| integrity_adjusted | Verify intended-ID coverage, collapse only identical duplicate events, then complete context means | Five looks; same adjusted z, provided integrity checks pass |

`integrity_adjusted` returns integrity-inconclusive at a look with missing B outcomes, unexpected IDs or conflicting duplicates. It does not fill missing outcomes or recover truth. Identical duplicates can be deduplicated because the observed ledger carries stable identity. Lost outcomes persist at all later looks. A valid earlier decision is not retrospectively vetoed by later logging corruption. It checks only the current prefix, not future data. Preserve every look's eligible row/context counts, integrity flags and decision evidence so this is auditable.

Complete-case context means under MNAR need not estimate the original target; narrower intervals cannot repair that bias. Even MCAR can reduce effective information. Bonferroni allocates alpha across the five two-sided looks; it does **not** make an inaccurate normal interval exact or fix biased/missing data. Fixed-time nominal two-sided error is .05; at the equality boundary a single normal ship tail is .025 under the reference approximation, not a separate .05 one-sided test.

## Analysis and practical success criteria

Report every world's method rates: false ship, false hold, correct ship/hold/total, inconclusive; integrity versus statistical inconclusives; first decision look and intended contexts consumed (H for all inconclusives). Do not average evidence use only over successful decisions or equate simulation counts with dollar savings. Report observed paired-row and context coverage, duplicate rows and missing grades to explain mechanisms.

Each rate gets a 95% Wilson Monte Carlo interval. Report prespecified **paired** method contrasts for false decisions, correct decisions and inconclusives; uncertainty uses cohort-level paired indicator differences x in {-1,0,1}, not independent-binomial errors. For nonzero sample variance, use the approximate interval `mean(x) +/- 1.959963984540054 * sampleSD(x)/sqrt(2000)`, clipped to [-1,1]. When sample variance is zero, use the conservative bounded-difference interval `mean(x) +/- sqrt(2*log(2/.05)/2000)`, clipped to [-1,1], explicitly labelled Hoeffding fallback rather than a zero-width certificate. Contrasts: context_fixed-row_fixed (clustering); row_peek-row_fixed and context_peek-context_fixed (peeking); context_adjusted-context_peek (look adjustment); integrity_adjusted-context_adjusted (data integrity). These are descriptive comparisons across all declared worlds, not selected-significance discoveries; no claim of simultaneous confidence across the table.

Define a **material change** descriptively as at least five percentage points in an outcome rate, with its paired uncertainty and countervailing inconclusive/correct-decision change shown. A universal winning method is not required. “Useful operating characteristics” in a nonboundary world require false-decision rate <=.05 and correct-decision rate >=.70 at the chosen horizon; report point estimates and Monte Carlo uncertainty, do not call a point estimate below a threshold proof of meeting it. The equality boundary diagnoses false ship and inconclusiveness, not power. Do not average across worlds to conceal a failure.

At 2,000 cohorts/world, approximate Monte Carlo 95% half-width is about .96 percentage points near a .05 rate, and 2.2 points at .5. These describe simulation precision only. More cohorts do not establish that the world is representative, the outcome valid, or the product safe. Report a negative result if no tested method meets the declared criteria; do not widen the study after seeing it.

## Validation, artifacts and stop

Before reporting runs: independent prefreeze design challenge; exact generator moment/probability checks; deterministic observed-zero versus missing fixtures; strict boundary/degenerate-vector checks; correct look counts and full intended horizon; immutable ID/dedup/conflict checks; analysis interface excluding hidden truth; critical values independently checked. Freeze this protocol hash, scenario manifest and source before outcomes.

Retain a compact per-cohort truth/observed-log representation, seed/index manifest, decisions and per-look diagnostics; avoid a generalized data platform. Root checks all cohort counts/identities and replay outputs. EVAL-REVIEW independently inspects code and regenerates a prespecified subset: first two cohorts in each world and the deterministic fixtures, plus aggregate count/hash/recomputation checks. Root performs one full exact-seed replay if resource use is reasonable; do not change scientific sample size for resource convenience after results.

Local run budget: no external spend, no network calls from simulation; stop and preserve partial evidence if a run exceeds 20 minutes wall time or 1 GiB resident memory, if generated outputs threaten 2 GiB storage, or if validation/authority fails. Do not silently substitute methods or drop worlds. These limits cover an execution pass, not permission to keep retrying to obtain desired findings. A code repair that does not change the scientific design must preserve incident evidence and reproduce unchanged frozen seeds.

Deliver one integrated internal RESULTS/guide, minimum reproducible code/tests/data/source manifests, independent review, actual resources and limitations registered in the shared inventory. **Stop at this Phase 1 evidence gate. No publication, paid follow-up, empirical panel analysis or new scenario study.**
