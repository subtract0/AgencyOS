# Multi-Machine Topology

## Recommended topology

Use one strategic governor and multiple worker machines.

- Hermes / GPT-5.5: strategic fleet governor
- s1 / Qwen3.6-27B class model: implementation, harness, validation, benchmark execution
- s2 / Qwopus-27B class model: planning, architecture, synthesis, critique
- mbp1 / Gemma-class model: independent critique, diversity solving, adversarial review

## Important rule

Do not run three independent strategic governors against the same state without coordination. That creates policy conflicts.

Better:

- one primary governor owns `CURRENT_OPERATING_POLICY.md`
- local worker agents own execution of claimed tasks
- dispatcher enforces claim uniqueness
- watchdog handles restarts and stale work

## If running three Hermes-like agents

Use them as role-specific governors, not equal kings:

1. Primary Hermes: final policy and prioritization authority.
2. Reliability Hermes: audits state, validators, watchdog, dispatcher, logs.
3. Product Hermes: audits Completion Bench, artifact quality, final reports.

Only the primary governor may change the global operating policy. Other governors propose patches through review tasks.

## Shared state

All machines should write to a shared repo-backed or append-only state directory:

- `ops/fleet/kanban.jsonl`
- `ops/fleet/task_claims.jsonl`
- `ops/fleet/heartbeat.jsonl`
- `ops/fleet/artifact_index.jsonl`
- `ops/evals/gap_matrix.jsonl`
- `ops/reports/latest_fleet_report.md`

## Claim safety

Task claiming must be atomic. If atomic file locking is unavailable, use one dispatcher as the sole writer of claims.
