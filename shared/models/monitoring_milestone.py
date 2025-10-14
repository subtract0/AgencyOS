"""
Monitoring Milestone Model for Quality Feedback Loop.

Tracks progress through first 100 tasks with milestone reports at 25/50/75/100.
Provides snapshot data for learning and performance analysis.

Constitutional Compliance:
- Article I: Complete context (all task data before milestone generation)
- Article II: 100% verification (strict Pydantic validation)
- Article IV: Milestone data stored for learning
- Article V: Spec-004 traceability

Reference: specs/spec-004-quality-feedback-loop.md Section 9 (Monitoring)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MilestoneMetrics(BaseModel):
    """
    Aggregated metrics at milestone threshold.

    Captures cumulative and interval-specific performance data
    for quality feedback loop analysis.
    """

    # Task counts
    total_tasks: int = Field(..., ge=0, description="Total tasks processed since monitoring start")
    tasks_since_last_milestone: int = Field(
        ..., ge=0, description="Tasks processed since previous milestone (or start)"
    )

    # Accuracy metrics
    overall_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Cumulative routing accuracy (correct / total)"
    )
    interval_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy since last milestone (improvement tracking)"
    )

    # Detection metrics
    misclassifications_detected: int = Field(
        0, ge=0, description="Total misclassifications detected (CRITICAL/WARNING)"
    )
    detection_rate: float = Field(
        0.0, ge=0.0, le=1.0, description="Ratio of misclassifications to total tasks"
    )

    # Refinement metrics
    refinements_applied: int = Field(0, ge=0, description="Total VectorStore refinements applied")
    refinement_effectiveness: float = Field(
        0.0, ge=0.0, le=1.0, description="% of refinements that improved accuracy"
    )
    avg_refinement_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Average confidence of applied refinements"
    )

    # Per-tier breakdown
    p1_accuracy: float | None = Field(
        None, ge=0.0, le=1.0, description="Accuracy for P1 (complex) tasks"
    )
    p2_accuracy: float | None = Field(
        None, ge=0.0, le=1.0, description="Accuracy for P2 (moderate) tasks"
    )
    p3_accuracy: float | None = Field(
        None, ge=0.0, le=1.0, description="Accuracy for P3 (simple) tasks"
    )

    # Quality signal statistics
    avg_test_failure_rate: float | None = Field(
        None, ge=0.0, le=1.0, description="Average test failure rate across tasks"
    )
    avg_code_churn: float | None = Field(
        None, ge=0.0, description="Average code churn (lines changed)"
    )
    avg_execution_time_ratio: float | None = Field(
        None, ge=0.0, description="Average execution time ratio (actual/estimated)"
    )


class MonitoringMilestone(BaseModel):
    """
    Milestone report for Quality Feedback Loop monitoring.

    Generated at 25/50/75/100 task intervals during first 100 tasks.
    Captures comprehensive metrics and dashboard snapshot for analysis.

    Example:
        >>> milestone = MonitoringMilestone(
        ...     milestone_number=1,
        ...     task_threshold=25,
        ...     tasks_processed=25,
        ...     metrics=MilestoneMetrics(
        ...         total_tasks=25,
        ...         tasks_since_last_milestone=25,
        ...         overall_accuracy=0.88,
        ...         interval_accuracy=0.88
        ...     )
        ... )
        >>> milestone.is_improving
        True
    """

    # Milestone identification
    milestone_number: int = Field(
        ..., ge=1, le=4, description="Milestone number (1=25 tasks, 2=50, 3=75, 4=100)"
    )
    task_threshold: int = Field(
        ..., description="Task count threshold for this milestone (25/50/75/100)"
    )

    # Timing metadata
    reached_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when milestone was reached"
    )
    time_since_start: float | None = Field(
        None, ge=0.0, description="Seconds since monitoring started"
    )

    # Task counts
    tasks_processed: int = Field(
        ..., ge=0, description="Actual tasks processed (may exceed threshold)"
    )

    # Metrics snapshot
    metrics: MilestoneMetrics = Field(..., description="Aggregated metrics at milestone")

    # Health indicators
    is_improving: bool = Field(
        default=True, description="Accuracy trending upward compared to previous milestone"
    )
    accuracy_delta: float | None = Field(
        None, description="Accuracy change since last milestone (+/- percentage points)"
    )

    # Dashboard snapshot reference
    dashboard_snapshot_path: str | None = Field(
        None, description="Path to saved dashboard HTML snapshot"
    )

    # Learning insights
    top_misclassification_patterns: list[str] = Field(
        default_factory=list, description="Most common misclassification patterns detected"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Suggested actions to improve accuracy"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "milestone_number": 2,
                "task_threshold": 50,
                "reached_at": "2025-10-10T16:30:00Z",
                "time_since_start": 3600.0,
                "tasks_processed": 50,
                "metrics": {
                    "total_tasks": 50,
                    "tasks_since_last_milestone": 25,
                    "overall_accuracy": 0.92,
                    "interval_accuracy": 0.96,
                    "misclassifications_detected": 4,
                    "detection_rate": 0.08,
                    "refinements_applied": 3,
                    "refinement_effectiveness": 0.85,
                    "avg_refinement_confidence": 0.88,
                },
                "is_improving": True,
                "accuracy_delta": 0.04,
                "dashboard_snapshot_path": "logs/monitoring/milestones/milestone_50.html",
                "top_misclassification_patterns": [
                    "simple → complex (test failures)",
                    "moderate → complex (high churn)",
                ],
                "recommended_actions": [
                    "Lower test_failure_rate threshold to 0.09",
                    "Continue VectorStore refinement",
                ],
            }
        }
    )


class MilestoneHistory(BaseModel):
    """
    Complete milestone tracking history.

    Maintains all milestones and provides progression analysis.
    """

    monitoring_session_id: str = Field(
        ..., description="Unique session identifier for monitoring run"
    )
    started_at: datetime = Field(
        default_factory=datetime.now, description="When monitoring started"
    )

    milestones: list[MonitoringMilestone] = Field(
        default_factory=list, description="Ordered list of reached milestones"
    )

    is_complete: bool = Field(
        default=False, description="True when all 4 milestones reached (100 tasks)"
    )
    final_accuracy: float | None = Field(
        None, ge=0.0, le=1.0, description="Final accuracy at 100-task milestone"
    )
    accuracy_improvement: float | None = Field(
        None, description="Total accuracy improvement from start to 100 tasks"
    )

    def get_latest_milestone(self) -> MonitoringMilestone | None:
        """Get most recent milestone."""
        return self.milestones[-1] if self.milestones else None

    def get_milestone_by_number(self, number: int) -> MonitoringMilestone | None:
        """Get specific milestone by number (1-4)."""
        for milestone in self.milestones:
            if milestone.milestone_number == number:
                return milestone
        return None

    def calculate_progression_rate(self) -> float | None:
        """
        Calculate average accuracy improvement per milestone.

        Returns:
            Average percentage point improvement per milestone, or None if <2 milestones
        """
        if len(self.milestones) < 2:
            return None

        first_accuracy = self.milestones[0].metrics.overall_accuracy
        last_accuracy = self.milestones[-1].metrics.overall_accuracy
        num_milestones = len(self.milestones)

        return (last_accuracy - first_accuracy) / (num_milestones - 1)
