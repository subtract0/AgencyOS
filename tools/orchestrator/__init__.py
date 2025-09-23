"""OrchestratorEngine public API.

Additive orchestration engine providing parallel execution and DAG-aware scheduling.
"""
from .api import execute_parallel, execute_graph
from .scheduler import TaskSpec, OrchestrationPolicy, OrchestrationResult

__all__ = [
    "execute_parallel",
    "execute_graph",
    "TaskSpec",
    "OrchestrationPolicy",
    "OrchestrationResult",
]
