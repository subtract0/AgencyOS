"""
Data models for Night Shift scheduler (Mission 5).

Constitutional Compliance:
- Article II: Strict typing (Pydantic models, no Dict[Any, Any])
- Article V: Spec-driven development (spec-mission-5-night-shift-auto-recovery.md)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NightShiftConfig(BaseModel):
    """Configuration for Night Shift scheduler."""

    schedule: str = Field(
        default="0 */4 * * *",
        description="Cron-like schedule (default: every 4 hours)",
    )
    max_tasks_per_execution: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max tasks to execute per cycle",
    )
    min_interval_minutes: int = Field(
        default=15,
        ge=5,
        description="Minimum interval between executions",
    )
    max_task_duration_minutes: int = Field(
        default=60,
        ge=10,
        description="Maximum duration per task (timeout)",
    )
    dry_run: bool = Field(
        default=False,
        description="Dry run mode (log intent without execution)",
    )
    enable_notifications: bool = Field(
        default=False,
        description="Enable email/notification escalations",
    )
    notification_email: Optional[str] = Field(
        default=None,
        description="Email for escalation notifications",
    )


class NightShiftState(BaseModel):
    """Persistent state for Night Shift scheduler."""

    last_execution_time: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of last execution",
    )
    current_task_id: Optional[str] = Field(
        default=None,
        description="Currently executing task ID (for resume on restart)",
    )
    tasks_completed_this_cycle: int = Field(
        default=0,
        description="Tasks completed in current cycle",
    )
    total_tasks_completed: int = Field(
        default=0,
        description="Total tasks completed across all cycles",
    )
    total_failures: int = Field(
        default=0,
        description="Total failures across all cycles",
    )
    total_escalations: int = Field(
        default=0,
        description="Total escalations to user",
    )
    health_status: dict[str, bool] = Field(
        default_factory=dict,
        description="Latest health check results",
    )
