from __future__ import annotations

"""
Orchestrator models for typed scheduling, execution, and results.

These models provide a concrete replacement for Dict[str, Any] artifacts,
metrics, and merged outputs used by the scheduler.
"""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field, ConfigDict

from shared.type_definitions.json import JSONValue


BackoffType = Literal["fixed", "exp"]
FairnessType = Literal["round_robin", "shortest_first"]
CancellationType = Literal["cascading", "isolated"]


class ExecutionMetrics(BaseModel):
    """Wall-clock and task metrics for a single orchestration run."""
    model_config = ConfigDict(extra="forbid")

    wall_time: float = Field(..., ge=0.0, description="Total wall-clock time in seconds")
    tasks: int = Field(..., ge=0, description="Total number of tasks executed")
    additional: Dict[str, JSONValue] = Field(default_factory=dict, description="Extra metrics keyed by name")


class TaskArtifacts(BaseModel):
    """Container for optional task artifacts produced during execution."""
    model_config = ConfigDict(extra="forbid")

    # Note: When artifacts are truly heterogeneous, use JSONValue while
    # progressively introducing specific models for common shapes.
    data: JSONValue | None = Field(default=None, description="Artifact payload as JSONValue")


class TaskResultModel(BaseModel):
    """Result of a single task execution under the orchestrator."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Task identifier")
    agent: str = Field(..., description="Agent name that executed the task")
    status: Literal["success", "failed", "canceled", "timeout"] = Field(..., description="Final task status")
    started_at: float = Field(..., description="Start time (epoch seconds)")
    finished_at: float = Field(..., description="Finish time (epoch seconds)")
    attempts: int = Field(..., ge=1, description="Number of attempts performed")
    artifacts: JSONValue | None = Field(default=None, description="Optional artifacts produced by the task")
    errors: List[str] | None = Field(default=None, description="Error messages if any")


class OrchestrationResultModel(BaseModel):
    """Aggregate result for an orchestration run, including per-task results and overall metrics."""
    model_config = ConfigDict(extra="forbid")

    tasks: List[TaskResultModel] = Field(..., description="Results for each task in the run")
    metrics: ExecutionMetrics = Field(..., description="Top-level execution metrics")
    merged: Dict[str, JSONValue] = Field(default_factory=dict, description="Optional merged outputs keyed by name")


__all__ = [
    "ExecutionMetrics",
    "TaskArtifacts",
    "TaskResultModel",
    "OrchestrationResultModel",
    "BackoffType",
    "FairnessType",
    "CancellationType",
]
