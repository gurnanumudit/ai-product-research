# Released fields

All JSON is UTF-8. Times are seconds; charges are USD. No raw private test output is included.

- `key`: original logical assignment identifier; `ti`: sparse original pair index; `rep`: zero-based repetition; `block_id`: pair/repetition block.
- `repo`, `task_id`: benchmark repository label and base task identifier; a base is their pair.
- `features`: selected two feature indices; `role_features`: ordered worker assignments; `integrator`: designated structured logical worker index, otherwise null.
- `previously_run_base`: whether this underlying task appeared in prior local experimental work, not a training-contamination label.
- `arm`: SOLO / SIMPLE / STRUCTURED. `agents`: 1 / 2 / 2.
- `both`: binary native complete-success score; `features_credit`: native feature-credit count 0–2. `both == (features_credit == 2)`.
- `merge`: null or status-only projection. Other original merge fields omitted. `integration_setup`: saved staging status, not an outcome score.
- `api_usd`, `calls`: completed-run settled API cost and call count. Interrupted settlements are separate.
- `input_tokens`, `output_tokens`, `cached_tokens`, `reasoning_tokens`: saved usage metadata; do not assume these categories are disjoint or add them blindly.
- `wall_seconds`: inclusive team elapsed time; `grade_seconds`: recorded evaluation time, not a causal speed comparison.
- `messages`, `messages_delivered`: saved and delivered messages; `phases` maps named phases to calls, API USD, inclusive wall seconds, shell action count, and messages.
- Interrupted costs: integer `settled_nano_usd` (one-billionth USD), `settled_calls`, `unknown_requests` and `unknown_reserve_nano_usd`. Unknown is not zero charge.
- Expected aggregate fields match the accepted analysis. Per-agent feature credit divides by the number of logical agents; it is not individual causal contribution.

Outcomes retain original schedule order. A missing key has no outcome record. No historical scientific outcomes from another study are included.
