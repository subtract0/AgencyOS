# Spec: OrchestratorEngine (Agent Orchestration Intelligence)

## Problem
Manual, linear handoffs limit throughput and increase latency. We need intelligent parallelism and DAG-aware scheduling that remains fully compatible with our spec-driven, quality-gated workflow.

## Goals
- Execute multiple agent tasks in parallel with dynamic load balancing
- Support dependency graphs (DAGs) with backpressure and correctness
- Provide retries/backoff, timeouts, and failure isolation
- Integrate with Telemetry for observability and with Auditor/Merger quality gates
- Remain additive, low-churn, and reversible

## Non-Goals
- Distributed cluster orchestration (MVP)
- External brokers/queues
- Long-running daemons (MVP is library + CLI)

## Requirements
- Python API
  - from tools.orchestrator import execute_parallel, execute_graph
  - execute_parallel(tasks: list[TaskSpec], policy: OrchestrationPolicy) -> OrchestrationResult
  - execute_graph(graph: TaskGraph, policy: OrchestrationPolicy) -> OrchestrationResult
- TaskSpec: {agent_factory: Callable[[AgentContext], Agent], prompt: str, params?: dict, id?: str}
- OrchestrationPolicy: {max_concurrency, retry: {max_attempts, backoff: exp|fixed, jitter}, timeout_s, cost_budget, fairness: round_robin|shortest_first, cancellation: cascading|isolated}
- OrchestrationResult: {tasks: [{id, agent, status, started_at, finished_at, attempts, artifacts, errors}], metrics: {wall_time, speedup_vs_serial, cost_estimate}, merged: {summary, conflicts?}}
- Features
  - Dynamic load balancing; work stealing
  - DAG execution with topological scheduling and backpressure
  - Failure handling with retries/backoff and circuit breaker
  - Cancellation/timeout policies per task and global
  - Telemetry events (lifecycle, task, heartbeat) and cost awareness
  - Optional quality-gate hooks to AuditorAgent/MergerAgent
- Security
  - No secret leakage; rely on Telemetry scrubbers
  - Do not embed credentials in prompts or logs
- Compatibility
  - Use existing create_*_agent factories and shared AgentContext
  - No breaking changes; purely additive

## Architecture
- Module: tools/orchestrator/{__init__.py, api.py, scheduler.py, graph.py, cli.py}
- Concurrency: asyncio with bounded semaphore; thread pool for blocking calls as needed
- Scheduler: encapsulates policy (fairness, retries/backoff, timeouts, cost guard)
- Graph: TaskGraph representation, topological order, backpressure
- Integrations: Telemetry for events; optional QualityGate callbacks

## Risks & Mitigations
- Deadlocks in DAG: comprehensive unit tests; timeouts; detection of cycles at build time
- Nondeterministic retries: deterministic backoff in tests; seed control
- Overhead: keep <1–2% CPU by simple asyncio primitives and minimal logging
- Secret leakage: central scrubber; redact env keys

## Testing Strategy
- Unit: scheduler policies, retry/backoff, timeouts, DAG scheduling
- Integration: stub agents that simulate work; measure speedup vs serial; verify dependency ordering and isolation
- Telemetry assertions: events emitted and parsable by Agency CLI

## Rollout
- Land module and tests; no default behavioral changes
- Optional CLI: python -m tools.orchestrator run --tasks '[...]' --max-concurrency 4 --timeout 300
- Documentation: usage examples in module README (follow-up)

## Acceptance Criteria
- AC1: execute_parallel achieves measured speedup vs serial on sample workload
- AC2: execute_graph honors dependencies and backpressure; no deadlocks
- AC3: Retries/timeouts deterministic in tests; failures isolated
- AC4: Telemetry events emitted and visible via CLI
- AC5: All tests green; no weakening existing tests

## Success Metrics
- 2–5x speedup on synthetic parallel tasks at concurrency 4–8
- Zero flaky tests introduced; CI stability maintained
- Telemetry shows correct task lifecycle coverage (>95%)
