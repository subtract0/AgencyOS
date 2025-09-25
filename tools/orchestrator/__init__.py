"""
Orchestrator System - Advanced Agent Task Coordination

This module provides sophisticated orchestration capabilities extracted from
the enterprise infrastructure branch. Key features:

- Parallel task execution with concurrency control
- Exponential backoff retry policies with jitter
- Real-time heartbeat monitoring
- Comprehensive telemetry integration
- Graceful error handling and recovery
- Cost accounting and resource utilization tracking

Usage:
    from tools.orchestrator.scheduler import run_parallel, OrchestrationPolicy, TaskSpec

    policy = OrchestrationPolicy(
        max_concurrency=4,
        retry=RetryPolicy(max_attempts=3, backoff="exp")
    )

    result = await run_parallel(context, task_specs, policy)
"""

from .scheduler import (
    run_parallel,
    OrchestrationPolicy,
    OrchestrationResult,
    RetryPolicy,
    TaskSpec,
    TaskResult,
    BackoffType,
    FairnessType,
    CancellationType,
)

__all__ = [
    "run_parallel",
    "OrchestrationPolicy",
    "OrchestrationResult",
    "RetryPolicy",
    "TaskSpec",
    "TaskResult",
    "BackoffType",
    "FairnessType",
    "CancellationType",
]