# Mission 6 Spec: Autonomous Witness Loop

**Owner**: CodingAgent / Night Shift Scheduler  
**Last Updated**: 2025-11-15  
**Status**: Draft (ready for implementation)

## Goal
Continuously monitor high-signal data sources (git history, Night Shift logs, CMP events, cost dashboards, failing tests) and emit structured "opportunity" events without human prompting. This is the intake valve for fully autonomous Meta Productivity 2.0 operation.

## Success Criteria
1. Runs as a long-lived daemon (invoked by Night Shift or `python trinity_protocol/run_autonomous_witness.py --continuous`).
2. Polls all target feeds at configurable cadences (default 60s) and debounces duplicate detections.
3. Emits JSON events to both:
   - `~/.agency/logs/autonomous_witness/<date>.log` (append-only)
   - MessageBus shim (`agency_memory/enhanced_memory_store.py`) with tag `witness_event`
4. Detects at least these triggers out of the box:
   - **Git commit**: new commit in working tree or upstream containing keywords (`fix`, `perf`, `cost`, `spec`)
   - **Night Shift failure**: state shows `total_failures` incremented
   - **CMP anomaly**: >3 rejected events for same clade in last hour
   - **Cost spike**: `logs/costs/latest.json` daily spend exceeds configurable budget
   - **Test failure artifact**: `test-results/latest.json` exists with failures
5. Each event contains `event_id`, `source`, `severity`, `summary`, `recommended_task`.
6. Covered by unit tests for event builders + integration smoke test with fake feeds.

## Functional Requirements
1. **Configuration** (`config/autonomous_witness.yaml` optional)
   - Poll intervals per source (default 60s)
   - Budget thresholds
   - Keywords for git detection
2. **Source adapters**
   - Git: uses `git log --since`
   - Night Shift: reads `~/.agency/state/night_shift_state.json`
   - CMP: tails `data/cmp_events.jsonl`
   - Cost: reads JSON exports under `logs/costs/`
   - Tests: watches `test-results/` directory
3. **Event deduplication**: maintain in-memory cache of last N events per source (persisted to `~/.agency/state/autonomous_witness_cache.json`).
4. **Output**: call new helper `trinity_protocol/message_bus.publish(event)` (stub OK if bus not yet implemented) + log.
5. **CLI**
   ```bash
   python trinity_protocol/run_autonomous_witness.py --continuous
   python trinity_protocol/run_autonomous_witness.py --once --sources git,night_shift
   ```

## Implementation Outline
- Create `trinity_protocol/run_autonomous_witness.py` with:
  - `WitnessConfig` (Pydantic) and `WitnessEvent`
  - Source-specific detector classes (GitDetector, NightShiftDetector, etc.)
  - `WitnessLoop` orchestrator with async or threaded polling (simple sequential loop is fine for v1)
  - Logging + graceful shutdown via signals
- Add helper `trinity_protocol/message_bus.py` (thin wrapper around EnhancedMemoryStore) if not present.

## Testing
- Unit tests for each detector under `tests/test_autonomous_witness.py`
- Integration test that fakes inputs and asserts events logged + stored.

## Telemetry / Logging
- Log file per day under `~/.agency/logs/autonomous_witness/`
- Include `event_id`, `source`, `severity`, `summary`, `recommended_task`
- Surface metrics: total events, per-source counts, dedupe hits

## Dependencies / Risks
- Requires git availability and stable working tree
- Should run in same environment as Night Shift; resource usage must stay low (<5% CPU).
- Budget data path must exist; if not, warn but keep running.
