from __future__ import annotations

import asyncio
from typing import List

from shared.agent_context import AgentContext  # type: ignore

from .scheduler import OrchestrationPolicy, OrchestrationResult, TaskSpec, run_parallel
from .graph import TaskGraph, run_graph


async def execute_parallel(ctx: AgentContext, tasks: List[TaskSpec], policy: OrchestrationPolicy) -> OrchestrationResult:
    """Execute tasks concurrently using the provided policy.

    Returns an OrchestrationResult with task-level results and aggregate metrics.
    """
    return await run_parallel(ctx, tasks, policy)


async def execute_graph(ctx: AgentContext, graph: TaskGraph, policy: OrchestrationPolicy) -> OrchestrationResult:
    """Execute a DAG of tasks honoring dependencies and backpressure."""
    return await run_graph(ctx, graph, policy)