# Methods and interpretation

## Design

37 technically eligible feature pairs from 24 underlying tasks in 11 repositories; three workflows and three repetitions, 111 assignments per workflow. Luna (`openai/gpt-6-luna`) with medium reasoning, native Responses shell/finish interface, network-isolated workers and a maximum of 32 calls per team. A call includes a finish action. Unused phase allowance does not transfer.

- SOLO: one worker, up to 32 calls for both requested features.
- SIMPLE: two workers, up to 16 calls each, separate workspaces and messages.
- STRUCTURED: two planning calls per worker (4 total), ten build calls per worker (20 total), then eight integration calls by the designated logical agent. Build retains its workspace but starts a fresh context. Integration uses a new isolated workspace seeded with the designated patch, both saved build patches and recorded messages.

Prompts and workflow excerpts preserve the exact inspected source. Calls are equal ceilings, not equal tokens, cost or wall time. Feature descriptions and private evidence are not included.

## Selection, exposure and interruptions

The technical screen evaluated 92 feature suites: 74 positive, four negative, 14 ambiguous. Only pairs with both suites positive were eligible; 71 distinct positive features serve these 37 pairs. This describes the pinned technical setup, not representative software work or agent performance on excluded tasks.

10 previously unrun underlying tasks supply 19 pairs (57 slots per arm); 14 reused tasks supply 18 pairs (54 slots per arm). This refers to local experimental history, not freedom from model training exposure. Public benchmark exposure remains possible. No outcomes from the earlier 12-job study are pooled.

Five collection epochs contribute 27 + 3 + 26 + 192 + 79 = 327 completed outcomes. Six interrupted assignments remain missing; continuations admitted only never-started assignments. Source staging used a 60-second ceiling in the first four epochs and 300 seconds in the last. The model workflow and grading limits remained unchanged. Four diagnostic trials did not prove that the larger staging ceiling was necessary or sufficient. Raw timing spans both preparation ceilings.

## Grading and delivery

All 435 final patches and 218 build patches were frozen before native final hidden evaluation. Native inner limits were unchanged; outer grading limit 360 seconds. Solo and integrated submissions deliver one final patch. SIMPLE uses the benchmark merge/fallback policy: clean merges are authoritative; conflicts/missing input can still earn both credits through the designated lead-alone both-suite fallback. Thus feature credits depend on delivery policy. The release contains only derived scores, not tests, patches or test output.

SIMPLE has 50 clean deliveries (31 both pass), 52 conflicts (5 both pass), and six missing-input deliveries (0 both pass). These associations do not identify what would happen if conflicts were repaired.

## Estimands and missing bounds

Primary: STRUCTURED minus SOLO. Secondary: STRUCTURED minus SIMPLE. For each arm, average the three repetitions within each pair, then pairs within a base task, then the 24 base tasks equally. Low/high endpoints substitute zero/one success for each missing outcome. Feature bounds substitute zero/two credits. Contrasts use the worst/best combination of the two arms' endpoints.

| Arm | Equal-task success bounds |
|---|---:|
| SOLO | 52.7778–53.4722% |
| SIMPLE | 31.2500–34.0278% |
| STRUCTURED | 47.9167–49.3056% |

STRUCTURED−SOLO: −5.5556 to −3.4722 percentage points. STRUCTURED−SIMPLE: +13.8889 to +18.0556 points. Bounds address missing outcomes only; no complete-data bootstrap, confidence interval or population claim. `resampling` is null. The historical pure analysis includes a dormant complete-case resampling helper, but the actual analysis explicitly sets `complete=False` and rejects more than 327 outcomes. It is not used by this replay.

## Accounting and coordination

All-assigned known arm charges include completed and interrupted settled calls. SOLO $1.985411395, SIMPLE $1.645559865, STRUCTURED $1.619190745. 47 interrupted settled calls cost $0.017578630 (23 SIMPLE / $0.007795810; 24 STRUCTURED / $0.009782820). SIMPLE has one additional unknown request; its $0.05 reserve is not spend. Same-study total: 9,784 dispatches, 9,783 settlements, $5.250162005 known API.

Cost per success divides known all-assigned API charges by observed both-pass count, including costs of failures. Zero-success ratios are undefined. Adding a reserve is explicitly a sensitivity, not an invoice. The existing $5 allowance is allocated once, either equally by assigned arm or proportional to observed counts. Equal assignment gives $0.061899628, $0.092006293, $0.061997310 per success; observed-share allocation gives $0.062158790, $0.091581556, $0.061997310. This changes the tiny solo/structured ordering. Human, hardware, electricity and Codex costs are unmetered, not zero.

Phase aggregates are completed-only. Calls/messages/API/time are preserved separately; messages to finished peers are saved but not delivered. Phase and team times are inclusive, may overlap, and do not establish speedup. STRUCTURED plan + integrate used 1,304 / 3,462 completed calls. These are whole-workflow differences, not causal estimates for planning, integration or general team size.
