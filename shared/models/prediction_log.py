"""
PredictionLog model for tracking ML predictions and actual outcomes.

Used for online learning and model monitoring. Stores predictions before
execution and actual tiers after completion for misclassification detection.

Constitutional compliance:
- Article I: Complete context (all prediction metadata captured)
- Article II: 100% verification (strict typing, Pydantic validation)
- Article IV: VectorStore integration (logs stored for learning)
- Article V: Spec-driven (follows spec-007-phase3-ml-inference.md)

Reference: specs/spec-007-phase3-ml-inference.md Section 3.1
Author: CodeAgent
Date: 2025-10-10
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PredictionLog(BaseModel):
    """
    Prediction log for online learning and monitoring.

    Workflow:
    1. Before execution: Create log with tier prediction
    2. Log to VectorStore with class probabilities
    3. Learning analysis: Compare predictions vs outcomes

    Fields:
        task_id: Unique task identifier
        tier: Predicted tier ("simple", "moderate", or "complex")
        confidence: Model confidence score (0.0-1.0)
        method: Classification method ("ml_model" or "rule_based_fallback")
        model_version: Model version timestamp (ISO 8601)
        class_probabilities: Dict mapping tier names to probabilities
        session_id: Session identifier for tracking
        timestamp: Prediction timestamp (ISO 8601 string, auto-populated)
        ab_group: Optional A/B test group ("control" or "new_model")
        fallback_reason: Optional reason for fallback to rules

    Example:
        >>> log = PredictionLog(
        ...     task_id="task-123",
        ...     tier="complex",
        ...     confidence=0.92,
        ...     method="ml_model",
        ...     model_version="2025-10-10T12:00:00Z",
        ...     class_probabilities={"simple": 0.03, "moderate": 0.05, "complex": 0.92},
        ...     session_id="session_leap5_phase3_1728567825"
        ... )
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier for tracking",
    )

    tier: str = Field(
        ...,
        description="Predicted tier (simple, moderate, or complex)",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0.0-1.0)",
    )

    method: str = Field(
        ...,
        description="Classification method (ml_model or rule_based_fallback)",
    )

    model_version: str = Field(
        ...,
        description="Model version timestamp (ISO 8601)",
    )

    class_probabilities: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of tier names to class probabilities",
    )

    session_id: str = Field(
        ...,
        description="Session identifier for tracking",
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Prediction timestamp (ISO 8601 UTC string)",
    )

    ab_group: str | None = Field(
        None,
        description="Optional A/B test group (control or new_model)",
    )

    fallback_reason: str | None = Field(
        None,
        description="Optional reason for fallback to rule-based classification",
    )

    # Legacy field support for backward compatibility
    predicted_tier: str | None = Field(None, exclude=True)
    actual_tier: str | None = Field(None, exclude=True)

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """
        Validate tier is "simple", "moderate", or "complex".

        Article II compliance: Strict validation before storage.

        Args:
            v: Tier to validate

        Returns:
            Validated tier string

        Raises:
            ValueError: If tier is invalid
        """
        valid_tiers = {"simple", "moderate", "complex"}
        if v not in valid_tiers:
            raise ValueError(
                f"tier must be one of {valid_tiers}, got '{v}'. "
                "Article II violation: Invalid tier value."
            )
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """
        Validate method is "ml_model" or "rule_based_fallback".

        Article II compliance: Strict validation before storage.

        Args:
            v: Method to validate

        Returns:
            Validated method string

        Raises:
            ValueError: If method is invalid
        """
        valid_methods = {"ml_model", "rule_based_fallback"}
        if v not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got '{v}'. "
                "Article II violation: Invalid method value."
            )
        return v

    def to_dict(self) -> dict:
        """
        Export prediction log to dictionary for VectorStore storage.

        Used for:
        - JSON serialization (VectorStore storage)
        - Learning analysis (Article IV compliance)

        Returns:
            Dictionary with all fields

        Example:
            >>> log = PredictionLog(...)
            >>> data = log.to_dict()
            >>> data.keys()
            dict_keys(['task_id', 'tier', 'confidence', 'method', 'model_version', ...]
        """
        result = {
            "task_id": self.task_id,
            "tier": self.tier,
            "confidence": self.confidence,
            "method": self.method,
            "model_version": self.model_version,
            "class_probabilities": self.class_probabilities,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        }

        # Add optional fields if present
        if self.ab_group is not None:
            result["ab_group"] = self.ab_group
        if self.fallback_reason is not None:
            result["fallback_reason"] = self.fallback_reason

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "PredictionLog":
        """
        Deserialize prediction log from dictionary.

        Used for:
        - JSON deserialization (VectorStore retrieval)
        - Article IV learning integration

        Args:
            data: Dictionary with prediction log fields

        Returns:
            PredictionLog instance

        Raises:
            ValidationError: If required fields missing or invalid

        Example:
            >>> data = {
            ...     "task_id": "task-123",
            ...     "tier": "complex",
            ...     "confidence": 0.92,
            ...     "method": "ml_model",
            ...     "model_version": "2025-10-10T12:00:00Z",
            ...     "class_probabilities": {"complex": 0.92},
            ...     "session_id": "session_test",
            ...     "timestamp": "2025-10-10T12:30:00Z"
            ... }
            >>> log = PredictionLog.from_dict(data)
        """
        return cls(**data)
