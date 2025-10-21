"""
Tests for EmergencyRetrainingTrigger alert system.

Tests cover:
- N: Normal operation (drift detected, retraining triggered)
- E: Edge cases (no drift, insufficient samples, threshold boundaries)
- S: Scaling (multiple drift alerts, alert deduplication)
- S: Security (safe configuration, validation gates)
- A: Audit (VectorStore logging, constitutional compliance)
- R: Reliability (graceful degradation, rollback safety)
- Y: Year 2038 (timestamp handling)

Constitutional compliance:
- Article I: Complete context (validate drift before action)
- Article II: 100% verification (Result pattern, validation gates)
- Article III: Automated enforcement (zero manual intervention)
- Article IV: VectorStore storage (emergency events logged)
- Law #1: TDD (tests written first)
- Law #2: Strict typing (Pydantic models)
- Law #5: Result pattern for error handling

Reference: specs/spec-009-misclassification-detection.md Section 5.3
Author: AgencyOSAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok
from tools.ml_routing.emergency_retraining_trigger import (
    EmergencyRetrainingResult,
    EmergencyRetrainingTrigger,
    TriggerConfig,
    TriggerError,
)


class TestTriggerConfigModel:
    """Test TriggerConfig Pydantic model (Law #2: Strict typing)."""

    def test_trigger_config_default_values(self):
        """Test default configuration values."""
        config = TriggerConfig()

        assert config.check_interval_minutes == 60  # Hourly checks
        assert config.drift_threshold_pct == 5.0  # 5% accuracy drop
        assert config.baseline_accuracy == 0.982  # Phase 3 baseline
        assert config.min_samples_for_retraining == 300
        assert config.skip_ab_rollout is True  # Emergency = immediate deployment
        assert config.alert_deduplication_hours == 24

    def test_trigger_config_validation(self):
        """Test Pydantic validation constraints."""
        # Valid config
        config = TriggerConfig(
            check_interval_minutes=30,
            drift_threshold_pct=3.0,
            baseline_accuracy=0.95,
            min_samples_for_retraining=100,
        )
        assert config.check_interval_minutes == 30
        assert config.drift_threshold_pct == 3.0

        # Invalid: check_interval < 1
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            TriggerConfig(check_interval_minutes=0)

        # Invalid: drift_threshold negative
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            TriggerConfig(drift_threshold_pct=-1.0)

        # Invalid: baseline_accuracy > 1
        with pytest.raises(ValueError, match="less than or equal to 1"):
            TriggerConfig(baseline_accuracy=1.5)

    def test_trigger_config_to_dict(self):
        """Test serialization to dict."""
        config = TriggerConfig(check_interval_minutes=120, drift_threshold_pct=4.0)
        data = config.model_dump()

        assert data["check_interval_minutes"] == 120
        assert data["drift_threshold_pct"] == 4.0
        assert data["baseline_accuracy"] == 0.982


class TestEmergencyRetrainingResultModel:
    """Test EmergencyRetrainingResult Pydantic model."""

    def test_result_model_fields(self):
        """Test result model contains required fields."""
        result = EmergencyRetrainingResult(
            triggered=True,
            drift_detected=True,
            drift_alert_timestamp="2025-10-10T12:00:00Z",
            current_accuracy=0.925,
            accuracy_drop_pct=5.7,
            retraining_initiated=True,
            new_model_version="v1.5",
            new_model_accuracy=0.986,
            samples_used=450,
            deployment_status="success",
        )

        assert result.triggered is True
        assert result.drift_detected is True
        assert result.current_accuracy == 0.925
        assert result.accuracy_drop_pct == 5.7
        assert result.new_model_version == "v1.5"
        assert result.deployment_status == "success"

    def test_result_model_no_retraining(self):
        """Test result when no drift detected."""
        result = EmergencyRetrainingResult(
            triggered=False,
            drift_detected=False,
            drift_alert_timestamp=None,
            current_accuracy=0.983,
            accuracy_drop_pct=0.1,
            retraining_initiated=False,
            new_model_version=None,
            new_model_accuracy=None,
            samples_used=0,
            deployment_status="no_action",
        )

        assert result.triggered is False
        assert result.drift_detected is False
        assert result.retraining_initiated is False
        assert result.new_model_version is None


class TestEmergencyRetrainingTrigger:
    """Test EmergencyRetrainingTrigger class (main functionality)."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext."""
        context = Mock(spec=AgentContext)
        context.store_memory = Mock()
        return context

    @pytest.fixture
    def trigger_config(self):
        """Create test TriggerConfig."""
        return TriggerConfig(
            check_interval_minutes=60,
            drift_threshold_pct=5.0,
            baseline_accuracy=0.982,
            min_samples_for_retraining=300,
        )

    @pytest.fixture
    def trigger(self, mock_context, trigger_config):
        """Create EmergencyRetrainingTrigger instance."""
        return EmergencyRetrainingTrigger(
            context=mock_context,
            config=trigger_config,
        )

    # N: Normal operation
    def test_check_and_trigger_with_drift_detected(self, trigger, mock_context):
        """Test normal flow: drift detected → retraining triggered."""
        # Mock drift detector
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.925,
            "accuracy_drop": 0.057,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        # Mock scheduler with successful retraining
        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.5"
        mock_retraining_report.new_accuracy = 0.986
        mock_retraining_report.samples_added = 450

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Ok(mock_retraining_report)

            result = trigger.check_and_trigger()

            assert result.is_ok()
            report = result.unwrap()

            assert report.triggered is True
            assert report.drift_detected is True
            assert report.current_accuracy == 0.925
            assert report.retraining_initiated is True
            assert report.new_model_version == "v1.5"
            assert report.new_model_accuracy == 0.986
            assert report.deployment_status == "success"

            # Verify VectorStore logging (Article IV)
            assert mock_context.store_memory.called

    def test_check_and_trigger_no_drift(self, trigger, mock_context):
        """Test normal flow: no drift detected → no action."""
        mock_drift_report = {
            "drift_detected": False,
            "current_accuracy": 0.983,
            "accuracy_drop": 0.001,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        with patch.object(trigger, "_check_drift") as mock_check:
            mock_check.return_value = Ok(mock_drift_report)

            result = trigger.check_and_trigger()

            assert result.is_ok()
            report = result.unwrap()

            assert report.triggered is False
            assert report.drift_detected is False
            assert report.retraining_initiated is False
            assert report.deployment_status == "no_action"

    # E: Edge cases
    def test_check_and_trigger_insufficient_samples(self, trigger, mock_context):
        """Test edge case: drift detected but insufficient samples."""
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.920,
            "accuracy_drop": 0.062,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Err("Insufficient samples: 250 < 300")

            result = trigger.check_and_trigger()

            # Should return error result (Article I: complete context required)
            assert result.is_err()
            assert "Insufficient samples" in result.unwrap_err()

    def test_check_and_trigger_drift_check_failure(self, trigger):
        """Test edge case: drift check fails (VectorStore unavailable)."""
        with patch.object(trigger, "_check_drift") as mock_check:
            mock_check.return_value = Err("VectorStore unavailable")

            result = trigger.check_and_trigger()

            # Should propagate error (Article I: complete context required)
            assert result.is_err()
            assert "VectorStore unavailable" in result.unwrap_err()

    def test_check_and_trigger_threshold_boundary(self, trigger, mock_context):
        """Test edge case: accuracy drop exactly at threshold (5%)."""
        mock_drift_report = {
            "drift_detected": True,  # Exactly at threshold
            "current_accuracy": 0.932,  # 0.982 - 0.05 = 0.932
            "accuracy_drop": 0.050,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.4"
        mock_retraining_report.new_accuracy = 0.984
        mock_retraining_report.samples_added = 320

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Ok(mock_retraining_report)

            result = trigger.check_and_trigger()

            assert result.is_ok()
            report = result.unwrap()

            assert report.drift_detected is True
            assert report.accuracy_drop_pct == 5.0
            assert report.retraining_initiated is True

    # S: Scaling
    def test_alert_deduplication(self, trigger, mock_context):
        """Test alert deduplication (only 1 alert per 24 hours)."""
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.925,
            "accuracy_drop": 0.057,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.5"
        mock_retraining_report.new_accuracy = 0.986
        mock_retraining_report.samples_added = 450

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Ok(mock_retraining_report)

            # First alert (should trigger)
            result1 = trigger.check_and_trigger()
            assert result1.is_ok()
            assert result1.unwrap().triggered is True

            # Second alert within 24 hours (should be deduplicated)
            result2 = trigger.check_and_trigger()
            assert result2.is_ok()
            report2 = result2.unwrap()

            # Should not trigger again (deduplication)
            assert report2.triggered is False
            assert report2.deployment_status == "deduplicated"

    # S: Security
    def test_validation_gates(self, trigger):
        """Test validation gates prevent unsafe deployments."""
        # Test: New model accuracy < 98% should fail deployment
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.920,
            "accuracy_drop": 0.062,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.5"
        mock_retraining_report.new_accuracy = 0.975  # <98% validation threshold
        mock_retraining_report.samples_added = 450

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Err(
                "Validation failed: new model accuracy 0.975 < 0.98 threshold"
            )

            result = trigger.check_and_trigger()

            # Should return error (Article II: 100% verification)
            assert result.is_err()
            assert "Validation failed" in result.unwrap_err()

    # A: Audit
    def test_vectorstore_logging(self, trigger, mock_context):
        """Test VectorStore logging (Article IV compliance)."""
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.925,
            "accuracy_drop": 0.057,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.5"
        mock_retraining_report.new_accuracy = 0.986
        mock_retraining_report.samples_added = 450

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Ok(mock_retraining_report)

            result = trigger.check_and_trigger()
            assert result.is_ok()

            # Verify store_memory called with correct tags (Article IV)
            assert mock_context.store_memory.called
            call_args = mock_context.store_memory.call_args
            assert "emergency" in call_args.kwargs["tags"]
            assert "retraining" in call_args.kwargs["tags"]
            assert "drift_recovery" in call_args.kwargs["tags"]

    # R: Reliability
    def test_graceful_degradation_vectorstore_unavailable(self, trigger):
        """Test graceful degradation when VectorStore unavailable."""
        with patch.object(trigger, "_check_drift") as mock_check:
            mock_check.return_value = Err("VectorStore connection timeout")

            result = trigger.check_and_trigger()

            # Should log error and return Err (Article I: retry next hour)
            assert result.is_err()
            assert "VectorStore" in result.unwrap_err()

    def test_rollback_safety(self, trigger, mock_context):
        """Test old model preserved for rollback."""
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.920,
            "accuracy_drop": 0.062,
            "detection_timestamp": "2025-10-10T12:00:00Z",
        }

        # Mock retraining failure after model training
        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Err("Deployment failed: old model preserved")

            result = trigger.check_and_trigger()

            # Should fail safely (Article II: 100% verification)
            assert result.is_err()
            assert "old model preserved" in result.unwrap_err()

    # Y: Year 2038
    def test_timestamp_handling(self, trigger):
        """Test timestamp handling for future dates (Y2038 safety)."""
        # Test with timestamp beyond 2038 (Unix timestamp overflow)
        future_timestamp = "2040-01-01T00:00:00Z"
        mock_drift_report = {
            "drift_detected": False,
            "current_accuracy": 0.985,
            "accuracy_drop": 0.001,
            "detection_timestamp": future_timestamp,
        }

        with patch.object(trigger, "_check_drift") as mock_check:
            mock_check.return_value = Ok(mock_drift_report)

            result = trigger.check_and_trigger()

            assert result.is_ok()
            report = result.unwrap()
            assert report.drift_alert_timestamp == future_timestamp


class TestEmergencyRetrainingTriggerIntegration:
    """Integration tests for EmergencyRetrainingTrigger (end-to-end)."""

    @pytest.fixture
    def mock_context_with_memory(self):
        """Create mock AgentContext with proper memory store."""
        context = Mock(spec=AgentContext)
        context.store_memory = Mock()
        context.search_memories = Mock(return_value=[{"content": "test"}])
        return context

    def test_end_to_end_drift_recovery(self, mock_context_with_memory):
        """
        Test end-to-end drift detection → retraining → deployment.

        Workflow:
        1. Drift detected (accuracy < 93.2%)
        2. Emergency retraining triggered
        3. Model trained with 300+ samples
        4. Model deployed with skip_ab_rollout=True
        5. VectorStore event logged
        """
        config = TriggerConfig(
            drift_threshold_pct=5.0,
            baseline_accuracy=0.982,
            min_samples_for_retraining=300,
            skip_ab_rollout=True,
        )

        trigger = EmergencyRetrainingTrigger(context=mock_context_with_memory, config=config)

        # Mock drift detector and scheduler (integration test, not full e2e)
        mock_drift_report = {
            "drift_detected": True,
            "current_accuracy": 0.920,
            "accuracy_drop": 0.062,
            "detection_timestamp": datetime.now(UTC).isoformat(),
        }

        mock_retraining_report = Mock()
        mock_retraining_report.version = "v1.6"
        mock_retraining_report.new_accuracy = 0.987
        mock_retraining_report.samples_added = 480

        with (
            patch.object(trigger, "_check_drift") as mock_check,
            patch.object(trigger, "_trigger_retraining") as mock_retrain,
        ):
            mock_check.return_value = Ok(mock_drift_report)
            mock_retrain.return_value = Ok(mock_retraining_report)

            result = trigger.check_and_trigger()

            assert result.is_ok()
            report = result.unwrap()

            # Verify complete workflow
            assert report.triggered is True
            assert report.drift_detected is True
            assert report.retraining_initiated is True
            assert report.new_model_version == "v1.6"
            assert report.new_model_accuracy == 0.987
            assert report.deployment_status == "success"

            # Verify VectorStore logging (Article IV)
            assert mock_context_with_memory.store_memory.called
            call_args = mock_context_with_memory.store_memory.call_args
            assert "emergency" in call_args.kwargs["tags"]
            assert "retraining" in call_args.kwargs["tags"]
