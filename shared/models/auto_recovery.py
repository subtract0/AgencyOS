"""
Data models for Auto-Recovery system (Mission 5).

Constitutional Compliance:
- Article II: Strict typing (Pydantic models, no Dict[Any, Any])
- Article V: Spec-driven development (spec-mission-5-night-shift-auto-recovery.md)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AutoRecoveryConfig(BaseModel):
    """Configuration for Auto-Recovery system."""

    max_retries: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum retry attempts",
    )
    retry_delays_seconds: list[int] = Field(
        default=[0, 30, 120],
        description="Retry delays (exponential backoff)",
    )
    enable_rollback: bool = Field(
        default=True,
        description="Enable automatic rollback on failure",
    )
    enable_escalation: bool = Field(
        default=True,
        description="Enable escalation to user on failure",
    )
    retryable_errors: list[str] = Field(
        default=["network_timeout", "file_lock", "resource_contention"],
        description="Error types that trigger retry",
    )


class RecoveryAttempt(BaseModel):
    """Metadata for a single recovery attempt."""

    task_id: str = Field(..., description="Task ID being recovered")
    attempt_number: int = Field(..., ge=1, description="Attempt number (1-indexed)")
    failure_type: str = Field(..., description="Type of failure detected")
    error_message: str = Field(..., description="Error message from failure")
    stack_trace: str = Field(default="", description="Stack trace if available")
    recovery_action: str = Field(
        ...,
        description="Recovery action taken: 'retry', 'rollback', 'escalate'",
    )
    outcome: str = Field(..., description="Outcome: 'success' or 'failure'")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of recovery attempt",
    )


class EscalationRecord(BaseModel):
    """Record of escalation to user."""

    task_id: str = Field(..., description="Task ID that failed")
    failure_reason: str = Field(..., description="Reason for failure")
    recovery_attempts: list[RecoveryAttempt] = Field(
        default_factory=list,
        description="All recovery attempts made",
    )
    stack_trace: str = Field(default="", description="Stack trace from failure")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of escalation",
    )
    resolved: bool = Field(default=False, description="Whether escalation was resolved")
    resolution_notes: Optional[str] = Field(
        default=None,
        description="Notes on how escalation was resolved",
    )
