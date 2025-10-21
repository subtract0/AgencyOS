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

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from shared.models.prediction_log import PredictionLog


class TestPredictionLogModel:
    """Test PredictionLog Pydantic model."""

    def test_creates_prediction_log_with_all_fields(self):
        """Test creating PredictionLog with all fields."""
        # Arrange
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Act
        log = PredictionLog(
            task_id="task-123",
            tier="complex",
            confidence=0.85,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
            timestamp=timestamp,
            class_probabilities={"complex": 0.85, "moderate": 0.10, "simple": 0.05},
        )

        # Assert
        assert log.task_id == "task-123"
        assert log.tier == "complex"
        assert log.confidence == 0.85
        assert log.timestamp == timestamp
        assert log.method == "ml_model"
        assert log.model_version == "2025-10-10T12:00:00Z"
        assert log.session_id == "session_test"

    def test_creates_prediction_log_with_minimal_fields(self):
        """Test creating PredictionLog with minimal required fields."""
        # Act
        log = PredictionLog(
            task_id="task-456",
            tier="moderate",
            confidence=0.72,
            method="rule_based_fallback",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
        )

        # Assert
        assert log.task_id == "task-456"
        assert log.tier == "moderate"
        assert log.confidence == 0.72
        assert log.method == "rule_based_fallback"
        assert log.model_version == "2025-10-10T12:00:00Z"
        assert log.session_id == "session_test"
        assert isinstance(log.timestamp, str)

    def test_creates_prediction_log_with_default_timestamp(self):
        """Test PredictionLog creates default timestamp."""
        # Act
        from datetime import timezone

        before = datetime.now(UTC)
        log = PredictionLog(
            task_id="task-789",
            tier="simple",
            confidence=0.95,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
        )
        after = datetime.now(UTC)

        # Assert
        assert isinstance(log.timestamp, str)
        # Timestamp should be ISO 8601 format
        log_time = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
        assert before <= log_time <= after

    def test_rejects_invalid_tier(self):
        """Test validation rejects invalid tier values."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-999",
                tier="P4",  # Invalid tier
                confidence=0.8,
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )

        # Assert error message
        assert "tier" in str(exc_info.value)

    def test_rejects_invalid_confidence_below_zero(self):
        """Test validation rejects confidence < 0.0."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-neg",
                tier="complex",
                confidence=-0.1,  # Invalid
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )

        # Assert error message
        assert "confidence" in str(exc_info.value)

    def test_rejects_invalid_confidence_above_one(self):
        """Test validation rejects confidence > 1.0."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-high",
                tier="moderate",
                confidence=1.5,  # Invalid
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )

        # Assert error message
        assert "confidence" in str(exc_info.value)

    def test_rejects_invalid_method(self):
        """Test validation rejects invalid method values."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PredictionLog(
                task_id="task-bad",
                tier="complex",
                confidence=0.8,
                method="unknown",  # Invalid method
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )

        # Assert error message
        assert "method" in str(exc_info.value)

    def test_to_dict_exports_all_fields(self):
        """Test to_dict() exports all fields correctly."""
        # Arrange
        timestamp = "2025-10-10T12:30:00Z"
        log = PredictionLog(
            task_id="task-export",
            tier="moderate",
            confidence=0.78,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
            timestamp=timestamp,
            class_probabilities={"moderate": 0.78, "simple": 0.12, "complex": 0.10},
        )

        # Act
        data = log.to_dict()

        # Assert
        assert data["task_id"] == "task-export"
        assert data["tier"] == "moderate"
        assert data["confidence"] == 0.78
        assert data["timestamp"] == timestamp
        assert data["method"] == "ml_model"
        assert data["model_version"] == "2025-10-10T12:00:00Z"
        assert data["session_id"] == "session_test"
        assert data["class_probabilities"] == {"moderate": 0.78, "simple": 0.12, "complex": 0.10}

    def test_to_dict_handles_optional_fields(self):
        """Test to_dict() handles optional fields correctly."""
        # Arrange
        log = PredictionLog(
            task_id="task-optional",
            tier="simple",
            confidence=0.9,
            method="rule_based_fallback",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
            ab_group="new_model",
            fallback_reason="ML confidence below threshold",
        )

        # Act
        data = log.to_dict()

        # Assert
        assert data["ab_group"] == "new_model"
        assert data["fallback_reason"] == "ML confidence below threshold"

    def test_from_dict_deserializes_correctly(self):
        """Test from_dict() deserializes data correctly."""
        # Arrange
        data = {
            "task_id": "task-deser",
            "tier": "complex",
            "confidence": 0.82,
            "method": "ml_model",
            "model_version": "2025-10-10T12:00:00Z",
            "session_id": "session_test",
            "timestamp": "2025-10-10T15:45:00Z",
            "class_probabilities": {"complex": 0.82, "moderate": 0.13, "simple": 0.05},
        }

        # Act
        log = PredictionLog.from_dict(data)

        # Assert
        assert log.task_id == "task-deser"
        assert log.tier == "complex"
        assert log.confidence == 0.82
        assert log.timestamp == "2025-10-10T15:45:00Z"
        assert log.method == "ml_model"
        assert log.model_version == "2025-10-10T12:00:00Z"
        assert log.session_id == "session_test"

    def test_from_dict_handles_optional_fields(self):
        """Test from_dict() handles optional fields correctly."""
        # Arrange
        data = {
            "task_id": "task-deser-optional",
            "tier": "simple",
            "confidence": 0.95,
            "method": "rule_based_fallback",
            "model_version": "2025-10-10T12:00:00Z",
            "session_id": "session_test",
            "timestamp": "2025-10-10T16:00:00Z",
            "ab_group": "control",
            "fallback_reason": "Testing fallback",
        }

        # Act
        log = PredictionLog.from_dict(data)

        # Assert
        assert log.ab_group == "control"
        assert log.fallback_reason == "Testing fallback"

    def test_from_dict_rejects_missing_required_fields(self):
        """Test from_dict() rejects data with missing required fields."""
        # Arrange
        data = {
            "task_id": "task-incomplete",
            "tier": "complex",
            # Missing confidence, method, model_version, session_id
        }

        # Act & Assert
        with pytest.raises(ValidationError):
            PredictionLog.from_dict(data)

    def test_supports_all_tier_values(self):
        """Test PredictionLog supports all valid tier values."""
        # Act & Assert
        for tier in ["simple", "moderate", "complex"]:
            log = PredictionLog(
                task_id=f"task-{tier}",
                tier=tier,
                confidence=0.9,
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )
            assert log.tier == tier

    def test_supports_both_method_values(self):
        """Test PredictionLog supports both valid method values."""
        # Act & Assert
        for method in ["ml_model", "rule_based_fallback"]:
            log = PredictionLog(
                task_id=f"task-{method}",
                tier="moderate",
                confidence=0.8,
                method=method,
                model_version="2025-10-10T12:00:00Z",
                session_id="session_test",
            )
            assert log.method == method

    def test_legacy_field_support(self):
        """Test legacy predicted_tier/actual_tier fields are excluded from serialization."""
        # Arrange - Create log with legacy fields (should be ignored)
        log = PredictionLog(
            task_id="task-legacy",
            tier="complex",
            confidence=0.85,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            session_id="session_test",
            predicted_tier="P1",  # Legacy field - should be excluded
            actual_tier="P2",  # Legacy field - should be excluded
        )

        # Act
        data = log.to_dict()

        # Assert - Legacy fields excluded from dict
        assert "predicted_tier" not in data
        assert "actual_tier" not in data
        assert data["tier"] == "complex"  # New field present
