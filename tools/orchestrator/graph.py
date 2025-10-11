from __future__ import annotations

import dataclasses
import time
from collections import defaultdict, deque

from shared.agent_context import AgentContext  # type: ignore
from shared.models.orchestrator import ExecutionMetrics
from shared.type_definitions.json import JSONValue

from .scheduler import OrchestrationPolicy, OrchestrationResult, TaskResult, TaskSpec
from .scheduler import _telemetry_emit, run_parallel as _run_parallel
from .slop_guardian import SlopDetected, SlopGuardian, enforce_slop_immunity


@dataclasses.dataclass
class TaskGraph:
    nodes: dict[str, TaskSpec]
    edges: list[tuple[str, str]]  # (upstream, downstream)

    def topo_order(self) -> list[str]:
        indeg: dict[str, int] = defaultdict(int)
        for u, v in self.edges:
            indeg[v] += 1
            indeg.setdefault(u, 0)
        q = deque([n for n in self.nodes if indeg.get(n, 0) == 0])
        order: list[str] = []
        while q:
            u = q.popleft()
            order.append(u)
            for a, b in self.edges:
                if a == u:
                    indeg[b] -= 1
                    if indeg[b] == 0:
                        q.append(b)
        if len(order) != len(self.nodes):
            raise ValueError("Cycle detected in TaskGraph")
        return order


def _create_deterministic_batches(task_ids: list[str], max_workers: int) -> list[list[str]]:
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
        >>> _create_deterministic_batches(["task_3", "task_1", "task_2"], 2)
        [["task_1", "task_2"], ["task_3"]]

        >>> _create_deterministic_batches(["task_a", "task_b", "task_c", "task_d"], 4)
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
        batch = sorted_tasks[i : i + max_workers]
        batches.append(batch)

    return batches


async def run_graph(
    ctx: AgentContext, graph: TaskGraph, policy: OrchestrationPolicy
) -> OrchestrationResult:
    """
    Execute task graph with full layer batching and deterministic execution order.

    This implementation ensures:
    - ALL tasks in each layer are executed (Article I: Complete Context)
    - Deterministic execution order via stable sort (reproducibility)
    - Telemetry for all state transitions (observability)
    - Layer completion verification (constitutional compliance)
    - Slop immunity pre-flight check (Article III: Quality gate)

    Args:
        ctx: Agent context for execution
        graph: Task graph with nodes and edges
        policy: Orchestration policy with max_concurrency

    Returns:
        OrchestrationResult with all task results and metrics

    Raises:
        SlopDetected: If any task description fails quality threshold (score <3.5)
    """
    # PRE-FLIGHT CHECK: Slop immunity validation (Article III, Clause 3.2)
    # Evaluate all task descriptions for quality before execution
    guardian = SlopGuardian()

    for task_id, task_spec in graph.nodes.items():
        # Extract description from task spec
        task_description = task_spec.prompt if hasattr(task_spec, 'prompt') else str(task_spec)

        result = enforce_slop_immunity(
            task_description,
            guardian,
            stage="graph_validation"
        )

        if result.is_err():
            # Slop detected - raise exception to halt execution
            slop_error = result.unwrap_err()
            _telemetry_emit({
                "type": "slop_detected",
                "task_id": task_id,
                "score": slop_error.verdict.score,
                "status": slop_error.verdict.status,
                "reasons": slop_error.verdict.reasons,
            })
            raise slop_error

    _telemetry_emit({
        "type": "slop_check_passed",
        "tasks_validated": len(graph.nodes),
    })

    # Level-by-level execution based on indegree (simple backpressure)
    levels: list[list[str]] = _levels(graph)
    all_results: dict[str, TaskResult] = {}
    graph_started = time.time()

    for layer_idx, level in enumerate(levels):
        layer_started = time.time()

        # Sort tasks deterministically by ID for reproducibility
        sorted_tasks = sorted(level)

        # Split into batches respecting max_workers
        batches = _create_deterministic_batches(sorted_tasks, policy.max_concurrency)

        _telemetry_emit(
            {
                "type": "layer_started",
                "layer_id": layer_idx,
                "tasks": len(level),
                "batches": len(batches),
                "started_at": layer_started,
            }
        )

        # Execute ALL batches in layer (not just first batch)
        layer_results: list[TaskResult] = []
        for batch_idx, batch in enumerate(batches):
            batch_started = time.time()

            # Get task specs for this batch
            specs = [graph.nodes[task_id] for task_id in batch]

            _telemetry_emit(
                {
                    "type": "batch_started",
                    "layer_id": layer_idx,
                    "batch_id": batch_idx,
                    "tasks": batch,
                    "concurrency": len(batch),
                    "started_at": batch_started,
                }
            )

            # Execute batch with concurrency limit
            res = await _run_parallel(ctx, specs, policy)

            batch_finished = time.time()

            # Store results
            for r in res.tasks:
                all_results[r.id] = r
                layer_results.append(r)

            _telemetry_emit(
                {
                    "type": "batch_finished",
                    "layer_id": layer_idx,
                    "batch_id": batch_idx,
                    "completed": len(res.tasks),
                    "duration_s": max(0.0, batch_finished - batch_started),
                    "finished_at": batch_finished,
                }
            )

        # Verify layer completion (Article I: Complete Context Before Action)
        completed_in_layer = [r for r in all_results.values() if r.id in level]
        assert len(completed_in_layer) == len(
            level
        ), f"Layer {layer_idx} incomplete: expected {len(level)} tasks, got {len(completed_in_layer)}"

        layer_finished = time.time()
        tasks_succeeded = sum(1 for r in layer_results if r.status == "success")
        tasks_failed = sum(1 for r in layer_results if r.status in ["failed", "timeout"])

        _telemetry_emit(
            {
                "type": "layer_completed",
                "layer_id": layer_idx,
                "tasks": len(level),
                "batches": len(batches),
                "tasks_succeeded": tasks_succeeded,
                "tasks_failed": tasks_failed,
                "duration_s": max(0.0, layer_finished - layer_started),
                "finished_at": layer_finished,
            }
        )

        # Basic failure isolation: if any upstream failed, downstream can be skipped later
        # (MVP does not auto-skip; policy can extend this)

    graph_finished = time.time()

    # Aggregate metrics
    merged: dict[str, JSONValue] = {"summary": "dag_executed", "levels": len(levels)}
    metrics = ExecutionMetrics(
        wall_time=max(0.0, graph_finished - graph_started),
        tasks=len(all_results),
        additional={},
    )
    return OrchestrationResult(tasks=list(all_results.values()), metrics=metrics, merged=merged)


def _levels(graph: TaskGraph) -> list[list[str]]:
    indeg: dict[str, int] = defaultdict(int)
    adj: dict[str, list[str]] = defaultdict(list)
    for u, v in graph.edges:
        adj[u].append(v)
        indeg[v] += 1
        indeg.setdefault(u, 0)
    level0 = [n for n in graph.nodes if indeg.get(n, 0) == 0]
    levels: list[list[str]] = []
    frontier = level0
    seen: set[str] = set()
    while frontier:
        levels.append(frontier)
        seen.update(frontier)
        next_frontier: list[str] = []
        for u in frontier:
            for v in adj.get(u, []):
                indeg[v] -= 1
                if indeg[v] == 0:
                    next_frontier.append(v)
        frontier = next_frontier
    if len(seen) != len(graph.nodes):
        raise ValueError("Cycle detected in TaskGraph")
    return levels
