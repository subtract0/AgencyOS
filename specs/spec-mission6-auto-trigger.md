# Mission 6 Spec: Auto-Trigger System

**Owner**: CodingAgent / QualityEnforcerAgent  
**Last Updated**: 2025-11-15  
**Status**: Draft (ready for implementation)

## Goal
Automatically map incoming witness signals to concrete remediation actions (run self-healing, rebalance costs, collect logs) without manual approval for safe operations.

## Success Criteria
1. Library `trinity_protocol/auto_trigger.py` exposes `AutoTriggerEngine` with `route(event: dict) -> TriggerResult`.
2. Supports at least these routes:
   - `event.source == "night_shift" and event.type == "failure"` → invoke SelfHealingAgent with failing test context.
   - `event.source == "cmp" and event.severity == "high"` → enqueue backlog task to refactor problematic clade.
   - `event.source == "cost" and event.metric == "daily_spend"` → call `tools/cost_optimizer.py` (if exists) or log escalation.
   - `event.source == "git" and event.kind == "high_value_commit"` → capture learning memory.
3. Each trigger logs actions to `~/.agency/logs/auto_trigger/<date>.log` and records metrics (total actions, per-route counts).
4. Provides dry-run flag for validation.
5. Covered by unit tests mocking downstream agents.

## Functional Requirements
- **Input contract**: expects witness-style dict with `event_id`, `source`, `type`, `summary`, `payload`.
- **Routing table**: YAML or Python dict specifying predicate + action function.
- **Actions** (v1):
  - `self_heal_failure(event)` → call `SelfHealingAgent().heal_one_failure(...)`.
  - `enqueue_backlog(event)` → instantiate `Task` + store via `BacklogStorage`.
  - `optimize_costs(event)` → stub calling `python tools/cost_optimizer.py --auto` (log if script missing).
  - `record_learning(event)` → store memory via `EnhancedMemoryStore`.
- **Safety**: if action raises, record Err result and optionally add backlog escalation task.
- **CLI**:
  ```bash
  python trinity_protocol/auto_trigger.py --event-file witness_event.json
  ```

## Implementation Outline
- Define `TriggerResult` dataclass (success bool, action_name, metadata).
- Build `ROUTES` table with predicate lambdas referencing event fields.
- Provide `AutoTriggerEngine.route(event)` to iterate routes until first match (or allow multi-match for future).
- Integrate with witness loop by importing engine and calling on each event (optional initial integration).

## Testing
- `tests/test_auto_trigger.py` covering:
  - Each route executes expected action (use mocks for SelfHealingAgent, BacklogStorage).
  - Dry-run mode logs intent but skips action.
  - Unknown event returns graceful "no_route" result.

## Logging & Metrics
- Append structured JSON lines to `~/.agency/logs/auto_trigger/<date>.log` (fields: timestamp, event_id, action, success, latency).
- Update Night Shift CMP metadata if auto-trigger created backlog entries (tag `auto_trigger`).

## Dependencies / Risks
- Depends on Witness events for input (but can be invoked standalone for now).
- Need guardrails to avoid infinite loops (e.g., auto-trigger creating backlog tasks that regenerate same event).
- Cost optimizer may not exist; log actionable TODO when missing.
