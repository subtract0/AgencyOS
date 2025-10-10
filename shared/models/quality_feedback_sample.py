"""
QualityFeedbackSample Pydantic model for VectorStore quality feedback records.

Constitutional compliance:
- Article II: Strict typing (Law #2) - replaces dict[str, Any]
- Article IV: VectorStore integration (structured learning data)

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.4
Author: QualityEnforcer
Date: 2025-10-10
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QualityFeedbackSample(BaseModel):
    """
    Quality feedback sample from VectorStore misclassification records.

    Used for training data preparation. Contains task description,
    corrected tier label, and quality metrics.

    Fields:
        task_description: Original task description text
        corrected_tier: Human-corrected tier (1=simple, 2=moderate, 3=complex)
        confidence: Correction confidence score (0.0-1.0)
        tier_change_count: Number of tier changes (oscillation detection)
        estimated_time_seconds: Estimated task duration
        historical_tier_mode: Most common historical tier
        task_id: Unique task identifier
        timestamp: Feedback timestamp (ISO 8601)
        tags: VectorStore tags (for filtering)

    Constitutional Compliance:
        Article II: Strict typing (replaces dict[str, Any])
        Article IV: Structured VectorStore data

    Example:
        >>> sample = QualityFeedbackSample(
        ...     task_description="Refactor authentication module",
        ...     corrected_tier=3,
        ...     confidence=0.85,
        ...     tier_change_count=1,
        ...     estimated_time_seconds=3600.0,
        ...     historical_tier_mode=2,
        ...     task_id="task_123",
        ...     timestamp="2025-10-10T12:00:00Z",
        ...     tags=["quality_feedback", "misclassification"]
        ... )
    """

    task_description: str = Field(
        ...,
        min_length=1,
        description="Task description text (non-empty)",
    )

    corrected_tier: int = Field(
        ...,
        ge=1,
        le=3,
        description="Corrected tier label (1=simple, 2=moderate, 3=complex)",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Correction confidence score (0.0-1.0)",
    )

    tier_change_count: int = Field(
        default=0,
        ge=0,
        description="Number of tier changes (oscillation detection)",
    )

    estimated_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated task duration in seconds",
    )

    historical_tier_mode: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Most common historical tier (0=unknown, 1-3=tier)",
    )

    task_id: str = Field(
        default="unknown",
        description="Unique task identifier",
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Feedback timestamp (ISO 8601 format)",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="VectorStore tags for filtering",
    )

    @classmethod
    def from_vectorstore_content(cls, content: dict) -> Optional["QualityFeedbackSample"]:
        """
        Create QualityFeedbackSample from raw VectorStore content.

        Safely handles missing fields with defaults.

        Args:
            content: Raw VectorStore content dictionary

        Returns:
            QualityFeedbackSample instance or None if invalid
        """
        try:
            return cls(
                task_description=content.get("task_description", ""),
                corrected_tier=content.get("corrected_tier", 1),
                confidence=content.get("confidence", 0.0),
                tier_change_count=content.get("tier_change_count", 0),
                estimated_time_seconds=content.get("estimated_time_seconds", 0.0),
                historical_tier_mode=content.get("historical_tier_mode", 0),
                task_id=content.get("task_id", "unknown"),
                timestamp=content.get("timestamp", datetime.now().isoformat()),
                tags=content.get("tags", []),
            )
        except Exception:
            return None
