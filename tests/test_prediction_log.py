"""
Tests for PredictionLog model.

Constitutional compliance:
- Article II: TDD - tests written FIRST before implementation
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling

Reference: specs/spec-007-phase3-ml-inference.md
Author: CodeAgent
Date: 2025-10-10
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from shared.models.prediction_log import PredictionLog


class TestPredictionLogModel:
    """Test PredictionLog Pydantic model."""

    def test_creates_prediction_log_with_all_fields(self):
        """Test creating PredictionLog with all fields."""
        # Arrange
        timestamp = datetime.utcnow()

        # Act
        log = PredictionLog(
            task_id="task-123",
            predicted_tier="P1",
            actual_tier="P1",
            confidence=0.85,
            timestamp=timestamp,
            method="ml",
        )

        # Assert
        assert log.task_id == "task-123"
        assert log.predicted_tier == "P1"
        assert log.actual_tier == "P1"
        assert log.confidence == 0.85
        assert log.timestamp == timestamp
        assert log.method == "ml"

    def test_creates_prediction_log_with_none_actual_tier(self):
        """Test creating PredictionLog with None actual_tier (before execution)."""
        # Act
        log = PredictionLog(
            task_id="task-456",
            predicted_tier="P2",
            actual_tier=None,
            confidence=0.72,
            method="rules",
        )

        # Assert
        assert log.task_id == "task-456"
        assert log.predicted_tier == "P2"
        assert log.actual_tier is None
        assert log.confidence == 0.72
        assert log.method == "rules"
        assert isinstance(log.timestamp, datetime)

    def test_creates_prediction_log_with_default_timestamp(self):
        """Test PredictionLog creates default timestamp."""
        # Act
        log = PredictionLog(
            task_id="task-789",
            predicted_tier="P3",
            actual_tier=None,
            confidence=0.95,
            method="ml",
        )

        # Assert
        assert isinstance(log.timestamp, datetime)
        # Timestamp should be recent (within last second)
        time_diff = datetime.utcnow() - log.timestamp
        assert time_diff.total_seconds() < 1.0

    def test_rejects_invalid_predicted_tier(self):
        """Test validation rejects invalid tier values."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-999",
                predicted_tier="P4",  # Invalid tier
                actual_tier=None,
                confidence=0.8,
                method="ml",
            )

        # Assert error message
        assert "predicted_tier" in str(exc_info.value)

    def test_rejects_invalid_confidence_below_zero(self):
        """Test validation rejects confidence < 0.0."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-neg",
                predicted_tier="P1",
                actual_tier=None,
                confidence=-0.1,  # Invalid
                method="ml",
            )

        # Assert error message
        assert "confidence" in str(exc_info.value)

    def test_rejects_invalid_confidence_above_one(self):
        """Test validation rejects confidence > 1.0."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-high",
                predicted_tier="P2",
                actual_tier=None,
                confidence=1.5,  # Invalid
                method="ml",
            )

        # Assert error message
        assert "confidence" in str(exc_info.value)

    def test_rejects_invalid_method(self):
        """Test validation rejects invalid method values."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-bad",
                predicted_tier="P1",
                actual_tier=None,
                confidence=0.8,
                method="unknown",  # Invalid method
            )

        # Assert error message
        assert "method" in str(exc_info.value)

    def test_to_dict_exports_all_fields(self):
        """Test to_dict() exports all fields correctly."""
        # Arrange
        timestamp = datetime(2025, 10, 10, 12, 30, 0)
        log = PredictionLog(
            task_id="task-export",
            predicted_tier="P2",
            actual_tier="P1",
            confidence=0.78,
            timestamp=timestamp,
            method="ml",
        )

        # Act
        data = log.to_dict()

        # Assert
        assert data["task_id"] == "task-export"
        assert data["predicted_tier"] == "P2"
        assert data["actual_tier"] == "P1"
        assert data["confidence"] == 0.78
        assert data["timestamp"] == "2025-10-10T12:30:00"
        assert data["method"] == "ml"

    def test_to_dict_handles_none_actual_tier(self):
        """Test to_dict() handles None actual_tier."""
        # Arrange
        log = PredictionLog(
            task_id="task-none",
            predicted_tier="P3",
            actual_tier=None,
            confidence=0.9,
            method="rules",
        )

        # Act
        data = log.to_dict()

        # Assert
        assert data["actual_tier"] is None

    def test_from_dict_deserializes_correctly(self):
        """Test from_dict() deserializes data correctly."""
        # Arrange
        data = {
            "task_id": "task-deser",
            "predicted_tier": "P1",
            "actual_tier": "P2",
            "confidence": 0.82,
            "timestamp": "2025-10-10T15:45:00",
            "method": "ml",
        }

        # Act
        log = PredictionLog.from_dict(data)

        # Assert
        assert log.task_id == "task-deser"
        assert log.predicted_tier == "P1"
        assert log.actual_tier == "P2"
        assert log.confidence == 0.82
        assert log.timestamp == datetime(2025, 10, 10, 15, 45, 0)
        assert log.method == "ml"

    def test_from_dict_handles_none_actual_tier(self):
        """Test from_dict() handles None actual_tier."""
        # Arrange
        data = {
            "task_id": "task-deser-none",
            "predicted_tier": "P3",
            "actual_tier": None,
            "confidence": 0.95,
            "timestamp": "2025-10-10T16:00:00",
            "method": "rules",
        }

        # Act
        log = PredictionLog.from_dict(data)

        # Assert
        assert log.actual_tier is None

    def test_from_dict_rejects_missing_required_fields(self):
        """Test from_dict() rejects data with missing required fields."""
        # Arrange
        data = {
            "task_id": "task-incomplete",
            "predicted_tier": "P1",
            # Missing confidence, method
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            PredictionLog.from_dict(data)

    def test_supports_all_tier_values(self):
        """Test PredictionLog supports all valid tier values."""
        # Act & Assert
        for tier in ["P1", "P2", "P3"]:
            log = PredictionLog(
                task_id=f"task-{tier}",
                predicted_tier=tier,
                actual_tier=tier,
                confidence=0.9,
                method="ml",
            )
            assert log.predicted_tier == tier
            assert log.actual_tier == tier

    def test_supports_both_method_values(self):
        """Test PredictionLog supports both valid method values."""
        # Act & Assert
        for method in ["ml", "rules"]:
            log = PredictionLog(
                task_id=f"task-{method}",
                predicted_tier="P2",
                actual_tier=None,
                confidence=0.8,
                method=method,
            )
            assert log.method == method

    def test_is_mispredicted_returns_false_when_no_actual_tier(self):
        """Test is_mispredicted() returns False when actual_tier is None."""
        # Arrange
        log = PredictionLog(
            task_id="task-pending",
            predicted_tier="P1",
            actual_tier=None,
            confidence=0.85,
            method="ml",
        )

        # Act & Assert
        assert log.is_mispredicted() is False

    def test_is_mispredicted_returns_false_when_tiers_match(self):
        """Test is_mispredicted() returns False when tiers match."""
        # Arrange
        log = PredictionLog(
            task_id="task-correct",
            predicted_tier="P2",
            actual_tier="P2",
            confidence=0.9,
            method="ml",
        )

        # Act & Assert
        assert log.is_mispredicted() is False

    def test_is_mispredicted_returns_true_when_tiers_differ(self):
        """Test is_mispredicted() returns True when tiers differ."""
        # Arrange
        log = PredictionLog(
            task_id="task-wrong",
            predicted_tier="P3",
            actual_tier="P1",
            confidence=0.75,
            method="ml",
        )

        # Act & Assert
        assert log.is_mispredicted() is True
