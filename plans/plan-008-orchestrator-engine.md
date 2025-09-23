# Plan: OrchestratorEngine (Agent Orchestration Intelligence)

## Overview
Deliver an additive orchestration library and CLI enabling intelligent parallel execution and DAG-aware scheduling across agents, with telemetry and quality-gate integrations. Keep scope minimal, compatible, and reversible.

## Milestones
- M0: Scaffold module + CLI skeleton
- M1: Parallel executor (execute_parallel) with policies, retries, timeouts
- M2: DAG executor (execute_graph) with topological scheduling + backpressure
- M3: Telemetry integration + metrics (speedup, cost)
- M4: Tests green (unit + integration), docs, examples

## Work Breakdown
- Phase 0: Scaffolding
  - tools/orchestrator/{__init__.py, api.py, scheduler.py, graph.py, cli.py}
  - Define TaskSpec, OrchestrationPolicy, OrchestrationResult dataclasses
  - CLI: python -m tools.orchestrator run --tasks '[...]' --max-concurrency 4 --timeout 300
- Phase 1: Parallel execution
  - asyncio-based scheduler with bounded semaphore (max_concurrency)
  - Retry policy: fixed/exp backoff with optional jitter; deterministic in tests
  - Timeout per task and global timeout
  - Cancellation policy: cascading|isolated
- Phase 2: DAG execution
  - TaskGraph structure; cycle detection on build
  - Topological scheduling; ready-queue; backpressure
  - Failure isolation (downstream skip vs continue policy)
- Phase 3: Observability + quality
  - Emit Telemetry events: lifecycle, task start/finish, errors
  - Compute metrics: wall_time, speedup_vs_serial, attempts, cost_estimate (via Telemetry adapters)
  - Optional callbacks to AuditorAgent/MergerAgent before finalize
- Phase 4: Tests + docs
  - Unit: scheduler policies, retry/backoff, timeouts, DAG ordering
  - Integration: stub agents simulating work; assert speedup; verify dependency order
  - Deterministic tests; no external deps; CI green
  - README with examples

## Deliverables
- Module: tools/orchestrator/*
- Tests: tests/tools/test_orchestrator/*
- Docs: README in module (follow-up) and spec/plan in repo

## Acceptance Criteria
- AC1: Parallel speedup vs serial on sample workload (2–5x at concurrency 4–8)
- AC2: Correct DAG execution; no deadlocks; backpressure works
- AC3: Deterministic retries/backoff and timeouts in tests; failure isolation
- AC4: Telemetry events emitted and consumable by Agency CLI
- AC5: All tests green; no weakening of existing tests

## Risks & Mitigations
- Deadlock/graph errors: cycle detection, timeouts, rich logging
- Nondeterminism: seeded backoff, fixed clocks in tests
- Overhead: minimal I/O in hot paths; batched telemetry

## Timeline (target)
- M0–M1: 1 day
- M2: 0.5–1 day
- M3–M4: 0.5–1 day

## Rollback Plan
Fully additive; disable by not importing or invoking. CLI optional.
