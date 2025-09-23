# Plan: Real-Time Performance Dashboard (Pulse)

## Overview
Extend Agency CLI with a live dashboard powered by Telemetry JSONL events. Provide real-time visibility into throughput, bottlenecks, costs, and compliance—feeding back into OrchestratorEngine policies.

## Milestones
- D0: Aggregation utilities in tools/telemetry/aggregator.py
- D1: CLI dashboard view (text) with 1–5s refresh
- D2: Snapshots export; filters; tests green

## Work Breakdown
- Phase 0: Aggregation
  - Implement rolling windows, rates, percentiles
  - Compute metrics: success/failure rate, MTTR, retries, CPU/RSS, costs
  - Bottleneck heuristics
- Phase 1: CLI view
  - agency dashboard [--since 1h] [--refresh 2s] [--format text|json]
  - Render overview/resources/costs/compliance/learning sections
  - Export snapshots to logs/telemetry/summaries/
- Phase 2: Tests
  - Unit tests for aggregator correctness (fixtures)
  - Integration tests with synthetic event streams; golden outputs

## Deliverables
- tools/telemetry/aggregator.py
- tools/agency_cli/dashboard.py (+ CLI wiring)
- tests/tools/test_telemetry/* and tests/tools/test_agency_cli/*

## Acceptance Criteria
- AC1: Dashboard refresh ≤5s and highlights bottlenecks
- AC2: Correct aggregation for costs and success rates
- AC3: Stable under rotation; non-blocking I/O
- AC4: All tests green; no weakening existing tests

## Risks & Mitigations
- Performance: windowed reads; caching; avoid full-file scans
- Data quality: fixtures and golden tests

## Timeline (target)
- D0–D1: 1 day
- D2: 0.5 day

## Rollback Plan
Feature-gated via CLI; safe to disable by not invoking.
