"""
TaskMetadata Pydantic model for ML feature extraction metadata.

Constitutional compliance:
- Article II: Strict typing (Law #2) - replaces dict[str, Any]
- Article IV: Structured metadata for feature engineering

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.3
Author: QualityEnforcer
Date: 2025-10-10
"""

from pydantic import BaseModel, Field


class TaskMetadata(BaseModel):
    """
    Task metadata for ML feature extraction.

    Used by FeatureExtractor to generate metadata features (8-dim).

    Fields:
        estimated_time_seconds: User-estimated task duration
        historical_tier_mode: Most common historical tier (0=unknown, 1-3=tier)

    Constitutional Compliance:
        Article II: Strict typing (replaces dict[str, Any])
        Article IV: Structured metadata for learning

    Example:
        >>> metadata = TaskMetadata(
        ...     estimated_time_seconds=1800.0,
        ...     historical_tier_mode=2
        ... )
        >>> features = extractor.extract_features(
        ...     task_description="Implement feature X",
        ...     task_metadata=metadata
        ... )
    """

    estimated_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated task duration in seconds (default: 0.0)",
    )

    historical_tier_mode: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Most common historical tier (0=unknown, 1=simple, 2=moderate, 3=complex)",
    )

    def to_dict(self) -> dict[str, float | int]:
        """
        Export to dictionary for feature extraction.

        Returns:
            Dictionary with estimated_time_seconds and historical_tier_mode
        """
        return {
            "estimated_time_seconds": self.estimated_time_seconds,
            "historical_tier_mode": self.historical_tier_mode,
        }
