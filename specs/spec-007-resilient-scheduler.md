# Specification: Resilient Scheduler with Deterministic Batching

**Spec ID**: `spec-007-resilient-scheduler`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-11
**Last Updated**: 2025-10-11
**Related Plan**: `plan-007-resilient-scheduler.md` (to be created after approval)
**Related ADR**: `ADR-023: Agent Orchestration Framework`
**Leap**: Leap 6 - The Bulletproof Orchestrator

---

## Executive Summary

Design a production-grade resilient scheduler for the orchestrator system that executes ALL tasks in a dependency layer (not just first batch), implements deterministic execution order for reproducibility, defines strict task result contracts using Pydantic models, and establishes comprehensive failure policies with retries, exponential backoff, and idempotency guarantees.

This specification transforms the MVP orchestrator into a bulletproof production system capable of handling complex task graphs with full observability, reproducibility, and constitutional compliance (Articles I, II, IV).

---

## Goals

### Primary Goals

- [ ] **Goal 1**: Execute ALL tasks in each dependency layer respecting `max_workers` concurrency limits (address current TODO at graph.py:46-50)
- [ ] **Goal 2**: Implement deterministic batching algorithm ensuring same task graph produces identical execution order across runs
- [ ] **Goal 3**: Define strict task result contracts using Pydantic models with typed success/failure states (replace `Dict[Any, Any]` artifacts)
- [ ] **Goal 4**: Establish comprehensive failure policies with retry limits, exponential backoff, and idempotency key tracking
- [ ] **Goal 5**: Achieve production-grade observability with full telemetry integration and execution replay capability

### Success Metrics

- **Execution Completeness**: 100% of tasks in layer executed (no premature termination after first batch)
- **Determinism**: 100% reproducibility - same graph produces identical task order across 1,000 runs
- **Type Safety**: Zero `Dict[Any, Any]` usage - all task results use strict Pydantic models
- **Failure Recovery**: >95% success rate for transient failures with retry policy (3 attempts, exponential backoff)
- **Observability**: 100% of task state transitions logged to telemetry with <10ms p99 overhead

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time task re-scheduling based on runtime performance (fixed DAG execution only)
- **Non-Goal 2**: Dynamic dependency graph modification mid-execution (graph is immutable after submission)
- **Non-Goal 3**: Cross-graph task sharing or resource pooling (each graph execution is isolated)
- **Non-Goal 4**: Distributed execution across multiple machines (single-machine parallelism only)

### Future Considerations

- **Future Enhancement 1**: Adaptive concurrency tuning based on system resource availability
- **Future Enhancement 2**: Task priority levels within dependency layers (weighted scheduling)
- **Future Enhancement 3**: Checkpoint/resume for long-running task graphs (hours to days)
- **Future Enhancement 4**: Distributed execution with Celery or Ray backend

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Orchestrator System (Autonomous Agent)
- **Description**: Core scheduling engine executing task graphs with dependency management
- **Goals**: Execute all tasks correctly, handle failures gracefully, maintain deterministic order
- **Pain Points**: Current MVP only executes first batch per layer, non-deterministic execution order
- **Technical Proficiency**: Production-grade system requiring 100% correctness (Article II)

#### Persona 2: PrimeCCC Agent (Task Graph Builder)
- **Description**: Autonomous orchestration agent constructing task graphs from strategic intent
- **Goals**: Reliable execution of complex multi-agent workflows, full task completion guarantees
- **Pain Points**: Incomplete layer execution causes downstream dependency failures
- **Technical Proficiency**: Requires deterministic behavior for reproducibility and debugging

#### Persona 3: Development Team
- **Description**: Engineers debugging task graph execution failures and optimizing workflows
- **Goals**: Understand execution order, replay failures, trace task dependencies
- **Pain Points**: Non-deterministic execution makes debugging impossible, lack of typed result contracts
- **Technical Proficiency**: Senior engineers requiring full observability and reproducibility

### User Journeys

#### Journey 1: Full Layer Execution (Primary Use Case)
```
1. User starts with: Task graph with 10 tasks in layer 0, max_workers=4
2. Current MVP behavior:
   - Executes first 4 tasks (batch 1)
   - Moves to layer 1 WITHOUT executing remaining 6 tasks
   - Downstream tasks fail due to missing dependencies
3. Desired behavior:
   - Batch 1: Execute tasks 0-3 (4 workers)
   - Batch 2: Execute tasks 4-7 (4 workers)
   - Batch 3: Execute tasks 8-9 (2 workers)
   - ALL 10 tasks complete before moving to layer 1
4. User achieves: 100% layer completion, zero orphaned tasks
```

#### Journey 2: Deterministic Execution Order (Debugging Use Case)
```
1. User starts with: Task graph execution failure requiring debugging
2. User needs to: Reproduce exact execution order to isolate failure
3. System performs:
   - Load task graph from definition
   - Apply deterministic sort (stable sort by task ID within layer)
   - Execute in IDENTICAL order as original run
   - Compare telemetry logs (task_started events match timestamps)
4. User achieves: Reproducible execution, root cause identified
```

#### Journey 3: Typed Result Contracts (Type Safety Use Case)
```
1. User starts with: Agent producing task results with heterogeneous structure
2. Current MVP: Results stored as `JSONValue` (effectively `Dict[Any, Any]`)
3. Desired behavior:
   - Define TaskResultContract Pydantic model
   - Validate agent output against contract on completion
   - Typed access: result.data.output (not result["artifacts"]["data"]["output"])
   - Type errors caught at runtime with clear validation messages
4. User achieves: Type-safe result access, schema validation, mypy compliance
```

#### Journey 4: Failure Recovery (Resilience Use Case)
```
1. User starts with: Task graph execution encountering transient network failure
2. System responds:
   - Task attempt 1: Network timeout after 30s
   - Retry policy triggered: Wait 1s (base_delay_s)
   - Task attempt 2: Network timeout after 30s
   - Exponential backoff: Wait 2s (2^1 * base_delay_s)
   - Task attempt 3: Success
3. System logs: 3 attempts, 2 failures, 1 success, total retry time 3s
4. User achieves: Transient failure recovery, no manual intervention
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Full Layer Execution

- [ ] **AC-1.1**: Execute ALL tasks in dependency layer before advancing to next layer (no premature layer transitions)
- [ ] **AC-1.2**: Respect `max_workers` concurrency limit via semaphore-based batching
- [ ] **AC-1.3**: Batching algorithm splits layer tasks into ceil(layer_size / max_workers) batches
- [ ] **AC-1.4**: Each batch executes concurrently, waits for completion before next batch starts
- [ ] **AC-1.5**: Layer completion verified: `len(completed_tasks) == len(layer_tasks)` assertion

#### Feature Component 2: Deterministic Batching

- [ ] **AC-2.1**: Task execution order is deterministic (same graph → same order across runs)
- [ ] **AC-2.2**: Batching algorithm uses stable sort by task ID within each layer
- [ ] **AC-2.3**: Batch assignment is deterministic: `batch_id = sorted_index // max_workers`
- [ ] **AC-2.4**: Execution order reproducible: telemetry logs show identical `task_started` sequence
- [ ] **AC-2.5**: Determinism verified: 1,000 runs of same graph produce identical execution traces

#### Feature Component 3: Task Result Contracts

- [ ] **AC-3.1**: Define `TaskResultContract` Pydantic model replacing `JSONValue` artifacts
- [ ] **AC-3.2**: All task results validate against contract schema on completion
- [ ] **AC-3.3**: Success state includes: `status="success"`, `data: TaskOutputData`, `errors=None`
- [ ] **AC-3.4**: Failure state includes: `status="failed"`, `data=None`, `errors: list[str]`
- [ ] **AC-3.5**: Type-safe access: `result.data.field_name` (not dict access)

#### Feature Component 4: Failure Policies

- [ ] **AC-4.1**: Retry policy with configurable `max_attempts` (default: 3)
- [ ] **AC-4.2**: Exponential backoff: `delay = base_delay_s * (2 ** (attempt - 1))`
- [ ] **AC-4.3**: Idempotency key tracking: same task ID + retry attempt = unique execution
- [ ] **AC-4.4**: Timeout policy: task-level timeout with configurable `timeout_s` (default: 300s)
- [ ] **AC-4.5**: Failure isolation: failed task does not cancel other tasks in same batch

#### Feature Component 5: Observability

- [ ] **AC-5.1**: Telemetry events for ALL state transitions: `batch_started`, `batch_finished`, `layer_completed`
- [ ] **AC-5.2**: Execution trace includes: task_id, batch_id, layer_id, attempt, start_time, end_time
- [ ] **AC-5.3**: Replay capability: reconstruct execution order from telemetry logs
- [ ] **AC-5.4**: Metrics tracking: tasks_per_layer, batches_per_layer, retry_rate, failure_rate
- [ ] **AC-5.5**: Telemetry overhead <10ms p99 (non-blocking async writes)

### Non-Functional Requirements

#### Performance

- [ ] **AC-P.1**: Batching algorithm completes in O(n log n) time where n = layer size (sort + split)
- [ ] **AC-P.2**: Deterministic sort overhead <50ms for 10,000 tasks
- [ ] **AC-P.3**: Full layer execution adds <5% overhead vs current first-batch-only approach
- [ ] **AC-P.4**: Memory usage O(layer_size) for batch tracking (no full graph in memory per layer)

#### Quality

- [ ] **AC-Q.1**: 100% test coverage for batching algorithm (unit tests for all edge cases)
- [ ] **AC-Q.2**: Zero `Dict[Any, Any]` usage in result types (strict Pydantic models only)
- [ ] **AC-Q.3**: Mypy passes with `--strict` flag (no type: ignore comments)
- [ ] **AC-Q.4**: Retry policy tested with simulated failures (transient vs permanent)

#### Reliability

- [ ] **AC-R.1**: Transient failure recovery >95% success rate (with 3 retries + exponential backoff)
- [ ] **AC-R.2**: Permanent failure detection: 3 consecutive failures → task marked `failed` (no infinite retries)
- [ ] **AC-R.3**: Idempotency guarantee: same task + same inputs → same result (no side effects on retry)
- [ ] **AC-R.4**: Graceful degradation: telemetry write failures logged but don't crash execution

### Constitutional Compliance

#### Article I: Complete Context Before Action

- [ ] **AC-CI.1**: ALL tasks in layer execute to completion (no partial layer execution)
- [ ] **AC-CI.2**: Timeout handling with retry (2x, 3x up to 10x per Article I requirements)
- [ ] **AC-CI.3**: Layer completion assertion: verify 100% task count before advancing

#### Article II: 100% Verification and Stability

- [ ] **AC-CII.1**: 100% test coverage for batching, retry, and failure handling logic
- [ ] **AC-CII.2**: All edge cases tested: empty layers, single task, max_workers > layer_size
- [ ] **AC-CII.3**: Failure scenarios validated: timeout, exception, validation error

#### Article III: Automated Merge Enforcement

- [ ] **AC-CIII.1**: No manual overrides for failure policies (retry limits are enforced)
- [ ] **AC-CIII.2**: Constitutional compliance validated in CI pipeline

#### Article IV: Continuous Learning and Improvement

- [ ] **AC-CIV.1**: Execution patterns stored in VectorStore (task success rates, retry patterns)
- [ ] **AC-CIV.2**: Failure analysis auto-stored: task_id, failure_reason, retry_count, resolution
- [ ] **AC-CIV.3**: Learning queries before execution: check historical failure patterns for tasks

#### Article V: Spec-Driven Development

- [ ] **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- [ ] **AC-CV.2**: All technical decisions traced to spec requirements

---

## Technical Design

### 5.1 Full Layer Execution Architecture

**Current MVP Behavior** (graph.py:39-56):
```python
async def run_graph(ctx, graph, policy):
    levels = _levels(graph)
    all_results = {}
    for level in levels:
        specs = [graph.nodes[n] for n in level]
        res = await _run_parallel(ctx, specs, policy)  # ❌ Only executes first batch
        for r in res.tasks:
            all_results[r.id] = r
```

**Desired Behavior** (Full Layer Execution):
```python
async def run_graph(ctx, graph, policy):
    levels = _levels(graph)
    all_results = {}

    for layer_idx, level in enumerate(levels):
        # Sort tasks deterministically by ID
        sorted_tasks = sorted(level, key=lambda task_id: task_id)

        # Split into batches respecting max_workers
        batches = create_deterministic_batches(
            sorted_tasks,
            max_workers=policy.max_concurrency
        )

        # Execute ALL batches in layer
        for batch_idx, batch in enumerate(batches):
            specs = [graph.nodes[task_id] for task_id in batch]

            _telemetry_emit({
                "type": "batch_started",
                "layer": layer_idx,
                "batch": batch_idx,
                "tasks": len(batch)
            })

            res = await _run_parallel(ctx, specs, policy)

            for r in res.tasks:
                all_results[r.id] = r

            _telemetry_emit({
                "type": "batch_finished",
                "layer": layer_idx,
                "batch": batch_idx,
                "completed": len(res.tasks)
            })

        # Verify layer completion (Article I)
        assert len([r for r in all_results.values() if r.id in level]) == len(level), \
            f"Layer {layer_idx} incomplete: expected {len(level)} tasks"

        _telemetry_emit({
            "type": "layer_completed",
            "layer": layer_idx,
            "tasks": len(level),
            "batches": len(batches)
        })
```

### 5.2 Deterministic Batching Algorithm

**Algorithm Requirements**:
1. **Stable Sort**: Tasks within layer sorted by task ID (lexicographic order)
2. **Deterministic Assignment**: Batch assignment based on sorted index
3. **Reproducibility**: Same graph → same batch structure across runs

**Implementation**:
```python
def create_deterministic_batches(
    task_ids: list[str],
    max_workers: int
) -> list[list[str]]:
    """
    Create deterministic batches from task IDs.

    Algorithm:
    1. Sort tasks by ID (stable sort for reproducibility)
    2. Split into ceil(len(tasks) / max_workers) batches
    3. Each batch has at most max_workers tasks

    Args:
        task_ids: Unsorted task IDs in layer
        max_workers: Maximum concurrent tasks per batch

    Returns:
        List of batches, each containing at most max_workers task IDs

    Examples:
        >>> create_deterministic_batches(["task_3", "task_1", "task_2"], max_workers=2)
        [["task_1", "task_2"], ["task_3"]]

        >>> create_deterministic_batches(["task_a", "task_b", "task_c", "task_d"], max_workers=4)
        [["task_a", "task_b", "task_c", "task_d"]]

    Determinism:
        - Same task_ids (regardless of input order) → same output batches
        - Batch assignment: batch_id = sorted_index // max_workers
        - Reproducible across 1,000+ runs (validated in tests)
    """
    # Stable sort by task ID (lexicographic order)
    sorted_tasks = sorted(task_ids)

    # Split into batches
    batches: list[list[str]] = []
    for i in range(0, len(sorted_tasks), max_workers):
        batch = sorted_tasks[i:i + max_workers]
        batches.append(batch)

    return batches
```

**Complexity Analysis**:
- **Time**: O(n log n) for sort + O(n) for split = O(n log n)
- **Space**: O(n) for sorted list + O(batches) for output = O(n)
- **Determinism**: 100% (sort is stable, split is index-based)

### 5.3 Task Result Contracts (Pydantic Models)

**Problem**: Current MVP uses `JSONValue` for task artifacts, leading to:
- No type safety (runtime errors from dict access)
- No schema validation (malformed results pass silently)
- No mypy support (all dict access is `Any`)

**Solution**: Strict Pydantic models for all result types.

#### Base Result Contract
```python
from typing import Literal, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T', bound=BaseModel)
E = TypeVar('E', bound=BaseModel)

class TaskOutputData(BaseModel):
    """Base model for task output data (agent-specific subclasses)."""

    model_config = ConfigDict(extra="forbid")

    # Subclasses define specific fields
    # Example: class CodeGenerationOutput(TaskOutputData):
    #     code: str
    #     file_path: str
    #     lines_written: int

class TaskError(BaseModel):
    """Structured error information for failed tasks."""

    model_config = ConfigDict(extra="forbid")

    error_type: str = Field(..., description="Error class name (e.g., 'TimeoutError', 'ValidationError')")
    message: str = Field(..., description="Human-readable error message")
    traceback: str | None = Field(None, description="Full traceback if available")
    retry_attempt: int = Field(..., ge=1, description="Which retry attempt failed")

class TaskResultContract(BaseModel, Generic[T]):
    """
    Typed task result contract replacing Dict[Any, Any] artifacts.

    Success state: status="success", data populated, errors=None
    Failure state: status="failed", data=None, errors populated

    Type safety: Use Generic[T] to specify output data type per task.
    """

    model_config = ConfigDict(extra="forbid")

    # Task metadata
    task_id: str = Field(..., description="Unique task identifier")
    agent_name: str = Field(..., description="Agent that executed task")

    # Execution status
    status: Literal["success", "failed", "timeout", "canceled"] = Field(
        ..., description="Final task execution status"
    )

    # Typed output data (Generic[T])
    data: T | None = Field(None, description="Typed output data (None if failed)")

    # Error information
    errors: list[TaskError] | None = Field(
        None, description="Structured errors (None if success)"
    )

    # Timing metadata
    started_at: float = Field(..., description="Start time (epoch seconds)")
    finished_at: float = Field(..., description="Finish time (epoch seconds)")
    attempts: int = Field(..., ge=1, description="Number of attempts before completion")

    # Idempotency tracking
    idempotency_key: str = Field(
        ..., description="Unique key: {task_id}:{attempt}:{timestamp}"
    )

    @property
    def duration_s(self) -> float:
        """Computed duration in seconds."""
        return self.finished_at - self.started_at

    def is_success(self) -> bool:
        """Type guard for success state."""
        return self.status == "success" and self.data is not None

    def is_failure(self) -> bool:
        """Type guard for failure state."""
        return self.status in ["failed", "timeout"] and self.errors is not None
```

**Usage Example**:
```python
# Define agent-specific output type
class CodeGenerationOutput(TaskOutputData):
    code: str
    file_path: str
    lines_written: int

# Task result with typed data
result = TaskResultContract[CodeGenerationOutput](
    task_id="generate_api_handler",
    agent_name="AgencyCodeAgent",
    status="success",
    data=CodeGenerationOutput(
        code="def handler(): ...",
        file_path="/Users/am/Code/Agency/api/handler.py",
        lines_written=42
    ),
    errors=None,
    started_at=1728567825.0,
    finished_at=1728567830.5,
    attempts=1,
    idempotency_key="generate_api_handler:1:1728567825000"
)

# Type-safe access
if result.is_success():
    print(f"Generated {result.data.lines_written} lines at {result.data.file_path}")
    # mypy knows result.data is CodeGenerationOutput (not None)
```

### 5.4 Failure Policies

#### Retry Policy (Enhanced)
```python
from pydantic import BaseModel, Field

class RetryPolicy(BaseModel):
    """Enhanced retry policy with idempotency tracking."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(3, ge=1, description="Maximum retry attempts")
    backoff_type: Literal["fixed", "exponential"] = Field(
        "exponential", description="Backoff strategy"
    )
    base_delay_s: float = Field(1.0, ge=0.0, description="Base delay in seconds")
    max_delay_s: float = Field(60.0, ge=0.0, description="Maximum delay cap")
    jitter: float = Field(0.1, ge=0.0, le=1.0, description="Jitter factor (0.0-1.0)")

    def compute_delay(self, attempt: int) -> float:
        """
        Compute retry delay for given attempt.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds before next retry

        Examples:
            >>> policy = RetryPolicy(backoff_type="exponential", base_delay_s=1.0)
            >>> policy.compute_delay(1)  # First retry
            1.0
            >>> policy.compute_delay(2)  # Second retry
            2.0
            >>> policy.compute_delay(3)  # Third retry
            4.0
        """
        if self.backoff_type == "fixed":
            delay = self.base_delay_s
        else:  # exponential
            delay = self.base_delay_s * (2 ** (attempt - 1))

        # Apply max delay cap
        delay = min(delay, self.max_delay_s)

        # Add jitter to prevent thundering herd
        if self.jitter > 0:
            import random
            jitter_amount = delay * self.jitter * random.random()
            delay += jitter_amount

        return delay
```

#### Timeout Policy
```python
class TimeoutPolicy(BaseModel):
    """Task-level timeout configuration."""

    model_config = ConfigDict(extra="forbid")

    timeout_s: float | None = Field(
        300.0, ge=0.0, description="Task timeout in seconds (None = no timeout)"
    )

    timeout_action: Literal["cancel", "continue"] = Field(
        "cancel", description="Action on timeout: cancel task or continue execution"
    )

    timeout_grace_period_s: float = Field(
        5.0, ge=0.0, description="Grace period for cleanup before forced termination"
    )
```

#### Idempotency Key Generation
```python
import time
from typing import Protocol

class IdempotencyKeyGenerator(Protocol):
    """Protocol for generating idempotency keys."""

    def generate(self, task_id: str, attempt: int) -> str:
        """Generate unique idempotency key."""
        ...

class DefaultIdempotencyKeyGenerator:
    """Default implementation using task_id + attempt + timestamp."""

    def generate(self, task_id: str, attempt: int) -> str:
        """
        Generate idempotency key: {task_id}:{attempt}:{timestamp_ms}

        Examples:
            >>> gen = DefaultIdempotencyKeyGenerator()
            >>> gen.generate("task_42", 1)
            "task_42:1:1728567825123"
        """
        timestamp_ms = int(time.time() * 1000)
        return f"{task_id}:{attempt}:{timestamp_ms}"
```

### 5.5 Observability & Telemetry

#### Enhanced Telemetry Events
```python
# Layer-level events
_telemetry_emit({
    "type": "layer_started",
    "layer_id": layer_idx,
    "tasks": len(layer),
    "batches": len(batches),
    "started_at": time.time()
})

_telemetry_emit({
    "type": "layer_completed",
    "layer_id": layer_idx,
    "tasks_completed": len([r for r in results if r.status == "success"]),
    "tasks_failed": len([r for r in results if r.status == "failed"]),
    "duration_s": time.time() - layer_start_time
})

# Batch-level events
_telemetry_emit({
    "type": "batch_started",
    "layer_id": layer_idx,
    "batch_id": batch_idx,
    "tasks": [task_id for task_id in batch],
    "concurrency": len(batch)
})

_telemetry_emit({
    "type": "batch_finished",
    "layer_id": layer_idx,
    "batch_id": batch_idx,
    "completed": len(results),
    "duration_s": batch_duration
})

# Retry events
_telemetry_emit({
    "type": "task_retry",
    "task_id": task_id,
    "attempt": attempt,
    "reason": str(error),
    "next_retry_in_s": delay
})
```

#### Execution Replay Capability
```python
from tools.telemetry.aggregator import list_events

def replay_execution_order(graph_id: str) -> list[str]:
    """
    Reconstruct execution order from telemetry logs.

    Args:
        graph_id: Unique graph execution identifier

    Returns:
        Ordered list of task IDs as executed

    Example:
        >>> replay_execution_order("graph_abc123")
        ["task_1", "task_2", "task_3", ...]  # Exact execution order
    """
    # Query telemetry for task_started events
    events = list_events(
        event_type="task_started",
        filters={"graph_id": graph_id},
        since="7d"
    )

    # Sort by timestamp (preserves execution order)
    sorted_events = sorted(events, key=lambda e: e["started_at"])

    # Extract task IDs
    return [event["task_id"] for event in sorted_events]
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `tools/orchestrator/scheduler.py` - Core scheduler with retry logic
- **Dependency 2**: `tools/orchestrator/graph.py` - Task graph and layer computation
- **Dependency 3**: `shared/models/orchestrator.py` - Pydantic models for types
- **Dependency 4**: `tools/telemetry/telemetry_log.py` - Telemetry event logging

### External Dependencies

- **External Dep 1**: `asyncio` (Python ≥3.11) - Async/await support for batching
- **External Dep 2**: `pydantic` (≥2.0) - Data validation and typing

### Technical Constraints

- **Constraint 1**: Single-machine execution only (no distributed scheduler)
- **Constraint 2**: Graph must be acyclic (DAG) - cycles detected and rejected
- **Constraint 3**: Task IDs must be unique within graph (enforced by TaskGraph validation)
- **Constraint 4**: Telemetry overhead must be <10ms p99 (async writes required)

### Business Constraints

- **Constraint 1**: Determinism required for debugging and reproducibility
- **Constraint 2**: Full layer execution mandatory (Article I compliance)
- **Constraint 3**: Type safety enforced (zero `Dict[Any, Any]` usage per constitutional mandate)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Full layer execution performance overhead** - *Mitigation*: Benchmark with 1,000-task layers, optimize batch scheduling, async telemetry writes
- **Risk 2**: **Deterministic sort breaks existing workflows** - *Mitigation*: Feature flag for opt-in determinism, compatibility layer for legacy code

### Medium Risk Items

- **Risk 3**: **Retry policy infinite loops** - *Mitigation*: Hard cap at `max_attempts`, exponential backoff with max_delay cap
- **Risk 4**: **Pydantic validation overhead** - *Mitigation*: Lazy validation, cache validation results, use `model_validate_json` for speed

### Constitutional Risks

- **Constitutional Risk 1**: **Article I violation (incomplete layer execution)** - *Mitigation*: Assertion checks, telemetry verification, integration tests
- **Constitutional Risk 2**: **Article II violation (test failures from edge cases)** - *Mitigation*: Comprehensive test suite (empty layers, single task, max_workers > layer_size)

---

## Integration Points

### Agent Integration

- **PrimeCCC**: Primary consumer - constructs task graphs, relies on full layer execution
- **AgencyCodeAgent**: Task executor - produces results validated against contracts
- **QualityEnforcer**: Constitutional compliance validation
- **LearningAgent**: Extracts execution patterns (retry rates, failure modes)

### System Integration

- **Orchestrator**: Core system enhanced with full layer execution
- **Telemetry System**: Event logging for observability
- **VectorStore**: Learning storage for failure patterns (Article IV)

---

## Testing Strategy

### Test Categories

- **Unit Tests** (15+ tests required):
  1. Deterministic batching algorithm (5 tests: empty, single, multiple batches, edge cases)
  2. Retry policy delay computation (3 tests: fixed, exponential, max delay cap)
  3. Idempotency key generation (2 tests: uniqueness, format validation)
  4. Task result contract validation (5 tests: success state, failure state, type guards)

- **Integration Tests** (10+ tests required):
  1. Full layer execution (3 tests: small layer, large layer, max_workers > layer_size)
  2. Determinism validation (1 test: 1,000 runs produce identical order)
  3. Retry policy end-to-end (3 tests: transient failure recovery, permanent failure, timeout)
  4. Telemetry integration (3 tests: event logging, replay capability, overhead measurement)

- **Performance Tests** (3+ tests required):
  1. Batching algorithm performance (1 test: 10,000 tasks in <50ms)
  2. Full layer execution overhead (1 test: <5% overhead vs first-batch-only)
  3. Telemetry overhead (1 test: <10ms p99 for event writes)

### Test Data Requirements

- **Test Data 1**: Sample task graphs (10 tasks, 100 tasks, 1,000 tasks)
- **Test Data 2**: Simulated failure scenarios (network timeout, validation error, exception)
- **Test Data 3**: Telemetry event logs for replay testing

### Test Environment Requirements

- **Environment 1**: Python ≥3.11 with asyncio support
- **Environment 2**: Telemetry directory with write permissions
- **Environment 3**: VectorStore for learning integration tests

---

## Implementation Phases

### Phase 1: Deterministic Batching (Week 1, Day 1-2)

- **Scope**: Implement `create_deterministic_batches()` algorithm
- **Deliverables**:
  - Batching function with stable sort
  - Unit tests for determinism (1,000 runs validation)
  - Performance benchmarks (<50ms for 10,000 tasks)
- **Success Criteria**: 100% determinism, O(n log n) complexity verified

### Phase 2: Full Layer Execution (Week 1, Day 3-4)

- **Scope**: Modify `run_graph()` to execute ALL batches per layer
- **Deliverables**:
  - Enhanced graph executor with batch loop
  - Layer completion assertions (Article I)
  - Integration tests (small/large layers)
- **Success Criteria**: 100% layer completion, zero orphaned tasks

### Phase 3: Task Result Contracts (Week 1, Day 5)

- **Scope**: Pydantic models for typed task results
- **Deliverables**:
  - `TaskResultContract`, `TaskOutputData`, `TaskError` models
  - Validation logic integrated into scheduler
  - Type guards and property methods
- **Success Criteria**: Zero `Dict[Any, Any]`, mypy passes with `--strict`

### Phase 4: Enhanced Failure Policies (Week 2, Day 1-2)

- **Scope**: Retry policy with exponential backoff and idempotency
- **Deliverables**:
  - Enhanced `RetryPolicy` with jitter
  - `TimeoutPolicy` for task-level timeouts
  - Idempotency key generation
- **Success Criteria**: >95% transient failure recovery, no infinite retries

### Phase 5: Observability & Telemetry (Week 2, Day 3-4)

- **Scope**: Enhanced telemetry events and replay capability
- **Deliverables**:
  - Layer/batch telemetry events
  - Execution replay function
  - Performance overhead validation (<10ms p99)
- **Success Criteria**: Full execution trace, replay matches original order

### Phase 6: VectorStore Learning Integration (Week 2, Day 5)

- **Scope**: Store failure patterns for continuous improvement (Article IV)
- **Deliverables**:
  - Failure pattern storage (task_id, failure_reason, retry_count)
  - Learning queries before execution
  - Cross-session pattern recognition
- **Success Criteria**: Historical failure patterns inform retry strategy

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: PrimeCCC Agent, Orchestrator System
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), QualityEnforcer (type safety)

### Review Criteria

- [ ] **Completeness**: All acceptance criteria defined with clear verification
- [ ] **Clarity**: Technical design is implementable without ambiguity
- [ ] **Feasibility**: Implementation realistic within existing architecture
- [ ] **Constitutional Compliance**: Articles I, II, IV, V fully addressed
- [ ] **Quality Standards**: Determinism, type safety, observability requirements met

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Constitutional Compliance**: Pending QualityEnforcer validation
- [ ] **Final Approval**: Pending after Phase 1 implementation

---

## Appendices

### Appendix A: Glossary

- **Dependency Layer**: Set of tasks with same topological depth in DAG
- **Deterministic Batching**: Algorithm producing identical batch assignments for same input
- **Idempotency Key**: Unique identifier ensuring task execution is idempotent across retries
- **Task Result Contract**: Pydantic model defining typed success/failure states
- **Full Layer Execution**: Execution of ALL tasks in dependency layer before advancing

### Appendix B: References

- **ADR-023**: Agent Orchestration Framework
- **ADR-001**: Complete Context Before Action (Article I)
- **ADR-002**: 100% Verification and Stability (Article II)
- **ADR-004**: Continuous Learning and Improvement (Article IV)
- **Leap 6**: The Bulletproof Orchestrator - Production Hardening

### Appendix C: Related Documents

- **Current Implementation**: `tools/orchestrator/graph.py:39-56` (MVP with first-batch-only execution)
- **Scheduler**: `tools/orchestrator/scheduler.py` (retry logic, telemetry)
- **Models**: `shared/models/orchestrator.py` (ExecutionMetrics, TaskResult)
- **Tests**: `tests/test_orchestrator_system.py` (existing test suite)

---

## Revision History

| Version | Date       | Author       | Changes                                                |
|---------|------------|--------------|--------------------------------------------------------|
| 1.0     | 2025-10-11 | PlannerAgent | Initial specification for resilient scheduler (Leap 6) |

---

*"Resilience is not the absence of failure, but the deterministic recovery from it."* - Bulletproof Orchestrator Principle
