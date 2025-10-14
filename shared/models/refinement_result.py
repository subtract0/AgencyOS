"""
VectorStore Rule Refinement Models.

Pydantic models for RuleRefiner output (spec Section 8).

Models:
- RefinementEntry: Single refinement iteration record
- RefinementHistory: Track refinement iterations per task
- ThresholdAdjustment: Record of threshold tuning
- RefinementResult: Result of VectorStore refinement operation
- VectorStoreSnapshot: Snapshot of VectorStore state for rollback

Constitutional Compliance:
- Article II: Strict typing (no Dict[Any, Any])
- Article V: Follows spec-004-quality-feedback-loop.md Section 8

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 8
"""

from pydantic import BaseModel, ConfigDict, Field


class RefinementEntry(BaseModel):
    """
    Single refinement iteration record.

    Tracks one refinement operation with original/corrected tier and confidence.

    Attributes:
        timestamp: ISO 8601 timestamp of refinement
        original_tier: Tier before refinement (simple/moderate/complex)
        corrected_tier: Tier after refinement (simple/moderate/complex)
        confidence: Confidence score after refinement (0.0-1.0)
        reason: Human-readable reason for refinement

    Example:
        >>> entry = RefinementEntry(
        ...     timestamp="2025-10-10T15:23:45Z",
        ...     original_tier="simple",
        ...     corrected_tier="complex",
        ...     confidence=0.95,
        ...     reason="Test failure rate 33% (CRITICAL)"
        ... )
        >>> entry.corrected_tier
        'complex'
    """

    timestamp: str = Field(..., description="ISO 8601 timestamp of refinement operation (UTC)")

    original_tier: str = Field(
        ...,
        description="Tier before refinement (simple/moderate/complex)",
        pattern="^(simple|moderate|complex)$",
    )

    corrected_tier: str = Field(
        ...,
        description="Tier after refinement (simple/moderate/complex)",
        pattern="^(simple|moderate|complex)$",
    )

    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score after refinement (0.0-1.0)"
    )

    reason: str = Field(
        ..., description="Human-readable reason for refinement (e.g., 'Test failure detected')"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "timestamp": "2025-10-10T15:23:45Z",
                "original_tier": "simple",
                "corrected_tier": "complex",
                "confidence": 0.95,
                "reason": "Test failure rate 33% (CRITICAL)",
            }
        },
    )


class RefinementHistory(BaseModel):
    """
    Track refinement iterations per task.

    Enforces max 3 iterations per task to prevent oscillation (spec Section 8.6).

    Attributes:
        task_id: Unique task identifier
        iteration_count: Number of refinement iterations (0-3)
        refinement_history: List of refinement entries (chronological)

    Example:
        >>> history = RefinementHistory(
        ...     task_id="refactor_async_handler_42",
        ...     iteration_count=1,
        ...     refinement_history=[
        ...         RefinementEntry(
        ...             timestamp="2025-10-10T15:23:45Z",
        ...             original_tier="simple",
        ...             corrected_tier="complex",
        ...             confidence=0.95,
        ...             reason="Test failures detected"
        ...         )
        ...     ]
        ... )
        >>> history.iteration_count
        1
    """

    task_id: str = Field(
        ..., description="Unique task identifier (same as MisclassificationReport.task_id)"
    )

    iteration_count: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Number of refinement iterations (max 3 per spec Section 8.6)",
    )

    refinement_history: list[RefinementEntry] = Field(
        default_factory=list, description="List of refinement entries in chronological order"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "task_id": "refactor_async_handler_42",
                "iteration_count": 1,
                "refinement_history": [
                    {
                        "timestamp": "2025-10-10T15:23:45Z",
                        "original_tier": "simple",
                        "corrected_tier": "complex",
                        "confidence": 0.95,
                        "reason": "Test failures detected",
                    }
                ],
            }
        },
    )


class ThresholdAdjustment(BaseModel):
    """
    Record of threshold tuning.

    Tracks threshold adjustments made during refinement (spec Section 8.3).

    Attributes:
        signal_name: Signal name (test_failure_rate, code_churn_lines, etc.)
        old_threshold: Threshold value before adjustment
        new_threshold: Threshold value after adjustment
        adjustment_count: Number of CRITICAL detections triggering adjustment
        adjusted_at: ISO 8601 timestamp of adjustment

    Example:
        >>> adjustment = ThresholdAdjustment(
        ...     signal_name="test_failure_rate",
        ...     old_threshold=0.1,
        ...     new_threshold=0.09,
        ...     adjustment_count=3,
        ...     adjusted_at="2025-10-10T15:23:45Z"
        ... )
        >>> adjustment.new_threshold
        0.09
    """

    signal_name: str = Field(
        ..., description="Signal name (test_failure_rate, code_churn_lines, execution_time_ratio)"
    )

    old_threshold: float = Field(..., description="Threshold value before adjustment")

    new_threshold: float = Field(
        ..., description="Threshold value after adjustment (10% reduction per spec Section 8.3)"
    )

    adjustment_count: int = Field(
        ..., ge=0, description="Number of CRITICAL detections triggering this adjustment"
    )

    adjusted_at: str = Field(..., description="ISO 8601 timestamp of adjustment (UTC)")

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "signal_name": "test_failure_rate",
                "old_threshold": 0.1,
                "new_threshold": 0.09,
                "adjustment_count": 3,
                "adjusted_at": "2025-10-10T15:23:45Z",
            }
        },
    )


class RefinementResult(BaseModel):
    """
    Result of VectorStore refinement operation.

    Output from RuleRefiner.refine() with all refinement metadata.

    Attributes:
        task_id: Task identifier
        patterns_updated: Number of VectorStore patterns modified
        confidence_before: Confidence before refinement (None if new pattern)
        confidence_after: Confidence after refinement
        threshold_adjustments: List of threshold adjustments made
        iteration_count: Total refinement iterations for this task (1-3)
        convergence_achieved: True if accuracy >98% (spec Section 8.5)
        accuracy_estimate: Estimated routing accuracy (None until Phase 5)
        refined_at: ISO 8601 timestamp of refinement

    Example:
        >>> result = RefinementResult(
        ...     task_id="refactor_async_handler_42",
        ...     patterns_updated=1,
        ...     confidence_before=0.70,
        ...     confidence_after=0.715,
        ...     threshold_adjustments=[],
        ...     iteration_count=1,
        ...     convergence_achieved=False,
        ...     accuracy_estimate=None,
        ...     refined_at="2025-10-10T15:23:45Z"
        ... )
        >>> result.confidence_after
        0.715
    """

    task_id: str = Field(
        ..., description="Task identifier (same as MisclassificationReport.task_id)"
    )

    patterns_updated: int = Field(
        ..., ge=0, description="Number of VectorStore patterns modified (0 if no update needed)"
    )

    confidence_before: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score before refinement (None if new pattern)"
    )

    confidence_after: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score after refinement (formula: old * 0.95 + 0.05)",
    )

    threshold_adjustments: list[ThresholdAdjustment] = Field(
        default_factory=list, description="List of threshold adjustments made during refinement"
    )

    iteration_count: int = Field(
        ...,
        ge=0,
        le=3,
        description="Total refinement iterations for this task (max 3 per spec Section 8.6)",
    )

    convergence_achieved: bool = Field(
        default=False,
        description="True if routing accuracy >98% on validation set (spec Section 8.5)",
    )

    accuracy_estimate: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated routing accuracy after refinement (computed in Phase 5)",
    )

    refined_at: str = Field(..., description="ISO 8601 timestamp of refinement operation (UTC)")

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "task_id": "refactor_async_handler_42",
                "patterns_updated": 1,
                "confidence_before": 0.70,
                "confidence_after": 0.715,
                "threshold_adjustments": [],
                "iteration_count": 1,
                "convergence_achieved": False,
                "accuracy_estimate": None,
                "refined_at": "2025-10-10T15:23:45Z",
            }
        },
    )


class VectorStoreSnapshot(BaseModel):
    """
    Snapshot of VectorStore state for rollback.

    Enables rollback if accuracy degrades >5% (spec Section 8.7).

    Attributes:
        snapshot_id: Unique snapshot identifier
        created_at: ISO 8601 timestamp of snapshot creation
        patterns: List of all misclassification patterns in VectorStore
        thresholds: Detection thresholds at snapshot time
        accuracy_baseline: Routing accuracy baseline (for degradation detection)

    Example:
        >>> snapshot = VectorStoreSnapshot(
        ...     snapshot_id="snapshot_1728567825",
        ...     created_at="2025-10-10T15:23:45Z",
        ...     patterns=[{"task_id": "task_1", "confidence": 0.95}],
        ...     thresholds={"test_failure_rate": 0.1, "code_churn_lines": 100},
        ...     accuracy_baseline=0.92
        ... )
        >>> snapshot.accuracy_baseline
        0.92
    """

    snapshot_id: str = Field(
        ..., description="Unique snapshot identifier (e.g., 'snapshot_1728567825')"
    )

    created_at: str = Field(..., description="ISO 8601 timestamp of snapshot creation (UTC)")

    patterns: list[dict] = Field(
        ..., description="List of all misclassification patterns in VectorStore at snapshot time"
    )

    thresholds: dict[str, float] = Field(
        ...,
        description="Detection thresholds at snapshot time (test_failure_rate, code_churn_lines, etc.)",
    )

    accuracy_baseline: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Routing accuracy baseline (for degradation detection, >5% drop triggers rollback)",
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "snapshot_id": "snapshot_1728567825",
                "created_at": "2025-10-10T15:23:45Z",
                "patterns": [
                    {
                        "task_id": "task_1",
                        "original_tier": "simple",
                        "corrected_tier": "complex",
                        "confidence": 0.95,
                    }
                ],
                "thresholds": {
                    "test_failure_rate": 0.1,
                    "code_churn_lines": 100,
                    "execution_time_ratio": 3.0,
                },
                "accuracy_baseline": 0.92,
            }
        },
    )
