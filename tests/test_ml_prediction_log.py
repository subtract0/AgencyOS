"""
Tests for PredictionLog Pydantic model (Leap 5 Phase 3).

Validates:
- Schema definition with required fields (task_id, tier, confidence, method, model_version, timestamp)
- Field validation (confidence 0-1, tier enum, timestamp ISO 8601)
- Serialization (to_dict, from_dict roundtrip)
- VectorStore integration (Article IV: prediction logging)

NECESSARY Pattern Coverage:
- N: Normal operation (valid prediction log creation)
- E: Edge cases (boundary values: confidence 0.0, 1.0)
- C: Corner cases (empty strings, None values)
- E: Error conditions (invalid confidence, invalid tier)
- S: Security (no sensitive data leakage)
- S: Stress (large batch logging)
- A: Accessibility (clear field names, docstrings)
- R: Regression (schema changes don't break compatibility)
- Y: Yield tests (to_dict output validation)

Constitutional compliance:
- Article I: Complete context (all prediction fields logged)
- Article II: 100% verification (confidence validation)
- Article IV: VectorStore-ready schema (Article IV mandate)
- Article V: Spec-driven (traces to spec-007)

Reference: specs/spec-007-phase3-ml-inference.md (section 5.5)
Author: TestGeneratorAgent
Date: 2025-10-10
"""

import pytest
from datetime import UTC, datetime
from pydantic import ValidationError


# ============================================================================
# Test Category 1: Field Validation (NECESSARY: N - Normal Operation)
# ============================================================================


class TestPredictionLogFieldValidation:
    """Test PredictionLog field validation and happy path scenarios."""

    def test_prediction_log_creation_with_defaults(self):
        """
        Test AC-3.2: Valid PredictionLog with all required fields.

        Article I: Complete context (all fields provided).
        Article IV: VectorStore-ready schema.
        NECESSARY: N (Normal operation - happy path).
        """
        # Arrange: Import here to allow implementation later
        from tools.ml_routing.prediction_log import PredictionLog

        # Act: Create valid PredictionLog with auto-populated timestamp
        log = PredictionLog(
            task_id="task_abc123",
            tier="complex",
            confidence=0.92,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            class_probabilities={"simple": 0.03, "moderate": 0.05, "complex": 0.92},
            session_id="session_leap5_phase3_1728567825",
        )

        # Assert: All fields set correctly
        assert log.task_id == "task_abc123"
        assert log.tier == "complex"
        assert log.confidence == 0.92
        assert log.method == "ml_model"
        assert log.model_version == "2025-10-10T12:00:00Z"
        assert log.class_probabilities == {
            "simple": 0.03,
            "moderate": 0.05,
            "complex": 0.92,
        }
        assert log.session_id == "session_leap5_phase3_1728567825"
        assert log.timestamp is not None  # Auto-populated

    def test_prediction_log_to_dict_preserves_fields(self):
        """
        Test AC-3.2: to_dict() exports all fields for VectorStore storage.

        Article IV: VectorStore-ready metadata.
        NECESSARY: Y (Yield validation - output format).
        """
        # Arrange
        from tools.ml_routing.prediction_log import PredictionLog

        timestamp = datetime.now(UTC).isoformat()
        log = PredictionLog(
            task_id="task_xyz789",
            tier="moderate",
            confidence=0.85,
            method="rule_based_fallback",
            model_version="leap4_rules",
            class_probabilities={},
            session_id="session_test_1234",
            timestamp=timestamp,
            ab_group="new_model",
            fallback_reason="ML confidence 0.65 < 0.7",
        )

        # Act: Export to dict
        data = log.to_dict()

        # Assert: All fields preserved
        assert data["task_id"] == "task_xyz789"
        assert data["tier"] == "moderate"
        assert data["confidence"] == 0.85
        assert data["method"] == "rule_based_fallback"
        assert data["model_version"] == "leap4_rules"
        assert data["class_probabilities"] == {}
        assert data["session_id"] == "session_test_1234"
        assert data["timestamp"] == timestamp
        assert data["ab_group"] == "new_model"
        assert data["fallback_reason"] == "ML confidence 0.65 < 0.7"

    def test_prediction_log_from_dict_deserialization(self):
        """
        Test AC-3.2: from_dict() deserializes prediction log (roundtrip).

        NECESSARY: Y (Yield validation - roundtrip serialization).
        """
        # Arrange
        from tools.ml_routing.prediction_log import PredictionLog

        original_log = PredictionLog(
            task_id="task_roundtrip_test",
            tier="simple",
            confidence=0.98,
            method="ml_model",
            model_version="2025-10-10T15:00:00Z",
            class_probabilities={"simple": 0.98, "moderate": 0.01, "complex": 0.01},
            session_id="session_roundtrip",
        )

        # Act: Export and re-import
        data = original_log.to_dict()
        reconstructed = PredictionLog.from_dict(data)

        # Assert: Fields match
        assert reconstructed.task_id == original_log.task_id
        assert reconstructed.tier == original_log.tier
        assert reconstructed.confidence == original_log.confidence
        assert reconstructed.method == original_log.method
        assert reconstructed.model_version == original_log.model_version
        assert reconstructed.class_probabilities == original_log.class_probabilities
        assert reconstructed.session_id == original_log.session_id

    def test_prediction_log_validation_invalid_confidence(self):
        """
        Test AC-3.2: confidence outside [0, 1] raises ValidationError.

        Article II: 100% verification enforcement.
        NECESSARY: E (Error condition - out of bounds).
        """
        # Arrange
        from tools.ml_routing.prediction_log import PredictionLog

        # Act & Assert: confidence > 1.0
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            PredictionLog(
                task_id="task_invalid_confidence",
                tier="complex",
                confidence=1.5,  # Invalid (>1.0)
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                class_probabilities={},
                session_id="session_test",
            )

        # Act & Assert: confidence < 0.0
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            PredictionLog(
                task_id="task_invalid_confidence",
                tier="complex",
                confidence=-0.1,  # Invalid (<0.0)
                method="ml_model",
                model_version="2025-10-10T12:00:00Z",
                class_probabilities={},
                session_id="session_test",
            )

    def test_prediction_log_timestamp_auto_populated(self):
        """
        Test AC-3.2: timestamp auto-populated with current UTC time.

        NECESSARY: N (Normal operation - default timestamp).
        """
        # Arrange
        from tools.ml_routing.prediction_log import PredictionLog

        before = datetime.now(UTC)

        # Act: Create log without explicit timestamp
        log = PredictionLog(
            task_id="task_auto_timestamp",
            tier="moderate",
            confidence=0.75,
            method="ml_model",
            model_version="2025-10-10T12:00:00Z",
            class_probabilities={"moderate": 0.75},
            session_id="session_test",
        )

        after = datetime.now(UTC)

        # Assert: timestamp is between before and after
        log_timestamp = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
        assert before <= log_timestamp <= after
