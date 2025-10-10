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
    1. Before execution: Create log with predicted_tier, actual_tier=None
    2. After execution: Update log with actual_tier
    3. Learning analysis: Compare predicted_tier vs actual_tier

    Fields:
        task_id: Unique task identifier
        predicted_tier: Predicted tier (P1/P2/P3)
        actual_tier: Actual tier after execution (None until complete)
        confidence: Model confidence score (0.0-1.0)
        timestamp: Prediction timestamp (UTC)
        method: Classification method ("ml" or "rules")

    Example:
        >>> # Before execution
        >>> log = PredictionLog(
        ...     task_id="task-123",
        ...     predicted_tier="P2",
        ...     actual_tier=None,
        ...     confidence=0.82,
        ...     method="ml"
        ... )
        >>>
        >>> # After execution (update actual_tier)
        >>> log.actual_tier = "P1"  # Task was more complex than predicted
        >>> assert log.is_mispredicted()  # True - P2 != P1
    """

    task_id: str = Field(
        ...,
        description="Unique task identifier for tracking",
    )

    predicted_tier: str = Field(
        ...,
        description="Predicted tier (P1=complex, P2=moderate, P3=simple)",
    )

    actual_tier: str | None = Field(
        None,
        description="Actual tier after execution (None until complete)",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0.0-1.0)",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Prediction timestamp (UTC)",
    )

    method: str = Field(
        ...,
        description="Classification method (ml or rules)",
    )

    @field_validator("predicted_tier")
    @classmethod
    def validate_predicted_tier(cls, v: str) -> str:
        """
        Validate predicted_tier is P1, P2, or P3.

        Article II compliance: Strict validation before storage.

        Args:
            v: Predicted tier to validate

        Returns:
            Validated tier string

        Raises:
            ValueError: If tier is invalid
        """
        valid_tiers = {"P1", "P2", "P3"}
        if v not in valid_tiers:
            raise ValueError(
                f"predicted_tier must be one of {valid_tiers}, got '{v}'. "
                "Article II violation: Invalid tier value."
            )
        return v

    @field_validator("actual_tier")
    @classmethod
    def validate_actual_tier(cls, v: str | None) -> str | None:
        """
        Validate actual_tier is None or P1/P2/P3.

        Article II compliance: Strict validation before storage.

        Args:
            v: Actual tier to validate

        Returns:
            Validated tier string or None

        Raises:
            ValueError: If tier is invalid
        """
        if v is None:
            return None

        valid_tiers = {"P1", "P2", "P3"}
        if v not in valid_tiers:
            raise ValueError(
                f"actual_tier must be one of {valid_tiers}, got '{v}'. "
                "Article II violation: Invalid tier value."
            )
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """
        Validate method is "ml" or "rules".

        Article II compliance: Strict validation before storage.

        Args:
            v: Method to validate

        Returns:
            Validated method string

        Raises:
            ValueError: If method is invalid
        """
        valid_methods = {"ml", "rules"}
        if v not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got '{v}'. "
                "Article II violation: Invalid method value."
            )
        return v

    def to_dict(self) -> dict:
        """
        Export prediction log to dictionary for storage.

        Used for:
        - JSON serialization (VectorStore storage)
        - Database persistence (prediction history)
        - Learning analysis (misclassification detection)

        Returns:
            Dictionary with all fields

        Example:
            >>> log = PredictionLog(...)
            >>> data = log.to_dict()
            >>> data.keys()
            dict_keys(['task_id', 'predicted_tier', 'actual_tier', 'confidence', 'timestamp', 'method'])
        """
        return {
            "task_id": self.task_id,
            "predicted_tier": self.predicted_tier,
            "actual_tier": self.actual_tier,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PredictionLog":
        """
        Deserialize prediction log from dictionary.

        Used for:
        - JSON deserialization (VectorStore retrieval)
        - Database loading (prediction history)

        Args:
            data: Dictionary with prediction log fields

        Returns:
            PredictionLog instance

        Raises:
            ValidationError: If required fields missing or invalid

        Example:
            >>> data = {
            ...     "task_id": "task-123",
            ...     "predicted_tier": "P2",
            ...     "actual_tier": "P1",
            ...     "confidence": 0.82,
            ...     "timestamp": "2025-10-10T12:30:00",
            ...     "method": "ml"
            ... }
            >>> log = PredictionLog.from_dict(data)
        """
        # Parse ISO 8601 timestamp
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        return cls(**data)

    def is_mispredicted(self) -> bool:
        """
        Check if prediction was incorrect.

        Compares predicted_tier vs actual_tier. Returns False if actual_tier
        is None (task not yet executed).

        Returns:
            True if predicted_tier != actual_tier, False otherwise

        Example:
            >>> log = PredictionLog(predicted_tier="P2", actual_tier="P1", ...)
            >>> log.is_mispredicted()
            True  # Predicted P2 but actual P1
            >>>
            >>> log = PredictionLog(predicted_tier="P2", actual_tier=None, ...)
            >>> log.is_mispredicted()
            False  # No actual tier yet
        """
        if self.actual_tier is None:
            return False
        return self.predicted_tier != self.actual_tier
