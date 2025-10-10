"""
Prediction Log Model for ML Routing System.

Stores prediction metadata for retraining and drift detection.

Constitutional Compliance:
- Article IV: VectorStore integration (predictions logged for learning)
- Article V: Spec-driven (per spec-008, spec-009, spec-010)

Author: QualityEnforcer
Date: 2025-10-10
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionLog(BaseModel):
    """
    Prediction log entry for ML routing system.

    Stores prediction metadata for retraining, drift detection, and learning.
    Logged to VectorStore for institutional memory (Article IV).

    Attributes:
        task_id: Unique task identifier
        predicted_tier: ML model prediction (P1, P2, P3)
        actual_tier: Ground truth tier (post-execution validation)
        confidence: Model confidence score (0.0-1.0)
        method: Prediction method ("ml", "heuristic", "fallback")
        timestamp: Prediction timestamp (UTC)
    """

    task_id: str = Field(..., description="Unique task identifier")
    predicted_tier: str = Field(..., description="ML model prediction (P1, P2, P3)")
    actual_tier: str = Field(..., description="Ground truth tier (post-execution)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    method: str = Field(..., description="Prediction method (ml, heuristic, fallback)")
    timestamp: datetime = Field(..., description="Prediction timestamp (UTC)")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
