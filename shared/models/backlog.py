"""
Backlog Agent Data Models (Mission 4).

Defines Task, TaskPriority, TaskStatus, TaskType, and BacklogMetrics models
for intelligent task prioritization and tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels (P1 > P2 > P3)."""

    P1 = "P1"  # Critical (always first)
    P2 = "P2"  # High
    P3 = "P3"  # Normal


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"  # Not started
    IN_PROGRESS = "in_progress"  # Currently being worked on
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Attempted but failed


class TaskType(str, Enum):
    """Type of work the task represents."""

    TEST_FAILURE = "test_failure"  # Failing test to fix
    FEATURE_REQUEST = "feature_request"  # New functionality
    TECH_DEBT = "tech_debt"  # Code quality improvement
    BUG_FIX = "bug_fix"  # Bug to fix


class Task(BaseModel):
    """
    Represents a single backlog task with prioritization metadata.

    Attributes:
        id: Unique task identifier (UUID)
        title: Short task description (1 sentence)
        description: Detailed task description
        task_type: Type of task (test_failure, feature_request, etc.)
        priority: Business priority (P1/P2/P3)
        status: Current execution status
        created_at: Task creation timestamp
        updated_at: Last modification timestamp
        estimated_complexity: Complexity estimate (1=simple, 10=complex)
        business_value: Business value (1=low, 10=high)
        cmp_related_clade_ids: Related clade IDs for CMP scoring
        metadata: Additional task-specific data
    """

    id: str = Field(..., description="Unique task ID (UUID)")
    title: str = Field(..., description="Short task description")
    description: str = Field(..., description="Detailed task description")
    task_type: TaskType = Field(..., description="Type of task")
    priority: TaskPriority = Field(default=TaskPriority.P2)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    estimated_complexity: int = Field(
        ..., ge=1, le=10, description="1=simple, 10=complex"
    )
    business_value: int = Field(default=5, ge=1, le=10, description="1=low, 10=high")
    cmp_related_clade_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BacklogMetrics(BaseModel):
    """
    Aggregate metrics for backlog health monitoring.

    Attributes:
        total_tasks: Total number of tasks
        pending_tasks: Tasks not yet started
        in_progress_tasks: Tasks currently being worked on
        completed_tasks: Successfully finished tasks
        failed_tasks: Tasks that failed execution
        avg_completion_time_hours: Average time to complete tasks
        p1_count: Number of P1 (critical) tasks
        p2_count: Number of P2 (high) tasks
        p3_count: Number of P3 (normal) tasks
        oldest_pending_task_age_days: Age of oldest pending task in days
    """

    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    failed_tasks: int
    avg_completion_time_hours: float
    p1_count: int
    p2_count: int
    p3_count: int
    oldest_pending_task_age_days: float
