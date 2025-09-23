# Spec: Real-Time Performance Dashboard (Pulse)

## Problem
We lack real-time visibility into agent throughput, bottlenecks, cost usage, and quality compliance—hindering orchestration efficiency and auto-healing.

## Goals
- Live dashboard (CLI-first) summarizing agent activity, performance, costs, and bottlenecks
- Build on Telemetry JSONL events; no agent API changes required
- Deterministic tests; minimal deps; local-first

## Non-Goals (MVP)
- Web UI
- External data stores/services

## Requirements
- Extend Agency CLI with: agency dashboard
- Views
  - Overview: active agents, backlog, wall-time per task, success/failure rates
  - Resources: CPU/RSS per agent (from heartbeats), concurrency utilization
  - Costs: per-agent/model token usage and USD estimates
  - Compliance: AuditorAgent pass rate; MTTR; flake detection rate (from TestDebugger when available)
  - Learning: latest LearningAgent entries; effectiveness heuristic
- Features
  - Refresh interval: 1–5s
  - Bottleneck heuristics: long-running tasks, high retry rates, saturation, error spikes
  - Export: snapshots to logs/telemetry/summaries/{status.json, dashboard.md}
  - Filters: agent=, since=, type=
- Compatibility
  - Use Telemetry events; no changes to agent interfaces
- Security & Performance
  - Secret scrub; bounded file reads; handle rotation; non-blocking I/O

## Architecture
- Module: tools/agency_cli/{dashboard.py}
- Aggregation: tools/telemetry/aggregator.py provides rollups (rates, histograms, percentiles)
- CLI: python -m tools.agency_cli dashboard [--since 1h] [--refresh 2s] [--format text|json]

## Risks & Mitigations
- Large log files: windowed reads; index by offsets; rotate daily
- Race conditions: read-only operations; tolerate partial lines
- Incorrect metrics: unit tests with synthetic fixtures; golden files

## Testing Strategy
- Unit: aggregation correctness, window rates, bottleneck flags
- Integration: simulate Telemetry events; validate dashboard output

## Acceptance Criteria
- AC1: Updates within 5s and highlights top bottlenecks on synthetic streams
- AC2: Correct cost and success-rate aggregation
- AC3: Stable under log rotation; non-blocking I/O
- AC4: Tests green; no weakening existing tests

## Success Metrics
- Accurate top-k bottlenecks; <200ms refresh compute on typical logs
- Zero flakes in CI
