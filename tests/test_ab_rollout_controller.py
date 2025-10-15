"""
Tests for ABRolloutController - gradual ML model rollout with A/B testing.

Tests cover:
- Rollout stage progression (10% → 50% → 100%)
- Accuracy comparison (new vs current model)
- Rollback logic (new accuracy < current - 2%)
- Symlink management (active model updates)
- Result pattern compliance

Constitutional compliance:
- Article I: Complete context (≥100 predictions per stage)
- Article II: 100% verification (all tests must pass)
- Article III: Automated rollout (no manual intervention)
- Law #1: TDD (tests written first)
- Law #2: Strict typing (Pydantic models)
- Law #5: Result pattern

Reference: specs/spec-007-phase3-ml-inference.md Section 3.2
Author: AgencyCodeAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from shared.agent_context import create_agent_context
from shared.models.ab_test_config import ABTestConfig
from shared.models.prediction_log import PredictionLog
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.ab_rollout_controller import (
    ABRolloutController,
    RolloutConfig,
    RolloutError,
    RolloutResult,
    RolloutStage,
)


class TestRolloutConfig:
    """Test RolloutConfig Pydantic model validation."""

    def test_valid_config(self):
        """Test RolloutConfig with valid stages."""
        config = RolloutConfig(
            stages=[
                RolloutStage(name="stage1", percentage=10, duration_hours=16),
                RolloutStage(name="stage2", percentage=50, duration_hours=16),
                RolloutStage(name="stage3", percentage=100, duration_hours=16),
            ],
            accuracy_threshold=0.02,
            min_predictions=100,
        )

        assert len(config.stages) == 3
        assert config.accuracy_threshold == 0.02
        assert config.min_predictions == 100

    def test_invalid_percentage(self):
        """Test RolloutConfig rejects invalid percentage."""
        with pytest.raises(ValidationError, match="less than or equal to 100"):
            RolloutConfig(
                stages=[RolloutStage(name="bad", percentage=150, duration_hours=16)],
                accuracy_threshold=0.02,
                min_predictions=100,
            )

    def test_invalid_duration(self):
        """Test RolloutConfig rejects invalid duration."""
        with pytest.raises(ValidationError, match="greater than 0"):
            RolloutConfig(
                stages=[RolloutStage(name="bad", percentage=10, duration_hours=0)],
                accuracy_threshold=0.02,
                min_predictions=100,
            )

    def test_invalid_threshold(self):
        """Test RolloutConfig rejects invalid accuracy threshold."""
        with pytest.raises(ValidationError, match="greater than 0"):
            RolloutConfig(
                stages=[RolloutStage(name="s1", percentage=10, duration_hours=16)],
                accuracy_threshold=-0.01,
                min_predictions=100,
            )

    def test_default_config(self):
        """Test RolloutConfig with default values."""
        config = RolloutConfig()

        assert len(config.stages) == 3
        assert config.stages[0].percentage == 10
        assert config.stages[1].percentage == 50
        assert config.stages[2].percentage == 100
        assert config.accuracy_threshold == 0.02
        assert config.min_predictions == 100


class TestRolloutStage:
    """Test RolloutStage Pydantic model."""

    def test_valid_stage(self):
        """Test RolloutStage with valid values."""
        stage = RolloutStage(name="stage1", percentage=10, duration_hours=16)

        assert stage.name == "stage1"
        assert stage.percentage == 10
        assert stage.duration_hours == 16

    def test_stage_equality(self):
        """Test RolloutStage equality comparison."""
        stage1 = RolloutStage(name="s1", percentage=10, duration_hours=16)
        stage2 = RolloutStage(name="s1", percentage=10, duration_hours=16)
        stage3 = RolloutStage(name="s2", percentage=50, duration_hours=16)

        assert stage1 == stage2
        assert stage1 != stage3


class TestRolloutResult:
    """Test RolloutResult Pydantic model."""

    def test_success_result(self):
        """Test RolloutResult for successful rollout."""
        result = RolloutResult(
            success=True,
            stage_completed="stage3",
            new_model_accuracy=0.985,
            current_model_accuracy=0.982,
            predictions_analyzed=150,
            rollback_triggered=False,
            message="Rollout completed successfully",
        )

        assert result.success is True
        assert result.stage_completed == "stage3"
        assert result.new_model_accuracy == 0.985
        assert result.rollback_triggered is False

    def test_rollback_result(self):
        """Test RolloutResult for rollback scenario."""
        result = RolloutResult(
            success=False,
            stage_completed="stage1",
            new_model_accuracy=0.960,
            current_model_accuracy=0.982,
            predictions_analyzed=120,
            rollback_triggered=True,
            message="Rollback: new accuracy 0.960 < current 0.982 - 0.02",
        )

        assert result.success is False
        assert result.rollback_triggered is True
        assert result.new_model_accuracy < result.current_model_accuracy


class TestABRolloutController:
    """Test ABRolloutController gradual rollout orchestration."""

    @pytest.fixture
    def context(self):
        """Create test AgentContext."""
        return create_agent_context(session_id="test_rollout")

    @pytest.fixture
    def default_config(self):
        """Create default RolloutConfig."""
        return RolloutConfig(
            stages=[
                RolloutStage(name="stage1", percentage=10, duration_hours=16),
                RolloutStage(name="stage2", percentage=50, duration_hours=16),
                RolloutStage(name="stage3", percentage=100, duration_hours=16),
            ],
            accuracy_threshold=0.02,
            min_predictions=100,
        )

    @pytest.fixture
    def models_dir(self, tmp_path):
        """Create temporary models directory."""
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        return models_dir

    def test_init(self, context, default_config, models_dir):
        """Test ABRolloutController initialization."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        assert controller.config == default_config
        assert controller.new_model_version == "v2.0"
        assert controller.current_model_version == "v1.0"
        assert controller.models_dir == models_dir

    def test_execute_rollout_success(self, context, default_config, models_dir):
        """Test successful rollout through all stages."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        # Mock stage execution to always succeed
        with patch.object(controller, "_execute_stage", return_value=Ok((0.985, 0.982, 150))):
            with patch.object(controller, "_update_active_symlink", return_value=Ok(None)):
                result = controller.execute_rollout()

        assert result.is_ok()
        rollout_result = result.unwrap()
        assert rollout_result.success is True
        assert rollout_result.stage_completed == "stage3"
        assert rollout_result.rollback_triggered is False

    def test_execute_rollout_with_rollback(self, context, default_config, models_dir):
        """Test rollout with accuracy regression triggering rollback."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        # Mock stage execution to fail accuracy threshold (0.960 < 0.982 - 0.02)
        with patch.object(controller, "_execute_stage", return_value=Ok((0.960, 0.982, 150))):
            with patch.object(controller, "_rollback_symlink", return_value=Ok(None)):
                result = controller.execute_rollout()

        assert result.is_ok()
        rollout_result = result.unwrap()
        assert rollout_result.success is False
        assert rollout_result.rollback_triggered is True
        assert "Rollback" in rollout_result.message

    def test_execute_stage_with_ab_config(self, context, default_config, models_dir):
        """Test _execute_stage configures A/B test correctly."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        stage = RolloutStage(name="stage1", percentage=10, duration_hours=16)

        # Mock prediction retrieval with sufficient samples
        timestamp_str = (datetime.now(UTC) - timedelta(hours=8)).isoformat().replace(
            "+00:00", ""
        ) + "Z"
        mock_predictions = [
            PredictionLog(
                task_id=f"task-{i}",
                tier="moderate",
                confidence=0.85,
                method="ml_model",
                model_version="v2.0",
                session_id="test_session",
                timestamp=timestamp_str,
            )
            for i in range(150)
        ]

        with patch.object(
            controller, "_get_predictions_for_stage", return_value=Ok(mock_predictions)
        ):
            with patch.object(controller, "_wait_for_stage", return_value=Ok(None)):
                result = controller._execute_stage(stage)

        assert result.is_ok()
        new_acc, current_acc, count = result.unwrap()
        assert 0.0 <= new_acc <= 1.0
        assert 0.0 <= current_acc <= 1.0
        assert count == 150

    def test_execute_stage_insufficient_predictions(self, context, default_config, models_dir):
        """Test _execute_stage fails with insufficient predictions."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        stage = RolloutStage(name="stage1", percentage=10, duration_hours=16)

        # Mock insufficient predictions (< min_predictions=100)
        timestamp_str = datetime.now(UTC).isoformat().replace("+00:00", "") + "Z"
        mock_predictions = [
            PredictionLog(
                task_id=f"task-{i}",
                tier="moderate",
                confidence=0.85,
                method="ml_model",
                model_version="v2.0",
                session_id="test_session",
                timestamp=timestamp_str,
            )
            for i in range(50)  # Only 50 predictions
        ]

        with patch.object(
            controller, "_get_predictions_for_stage", return_value=Ok(mock_predictions)
        ):
            with patch.object(controller, "_wait_for_stage", return_value=Ok(None)):
                result = controller._execute_stage(stage)

        assert result.is_err()
        assert "Insufficient predictions" in result.unwrap_err()

    def test_calculate_accuracy(self, context, default_config, models_dir):
        """Test _calculate_accuracy computes correct accuracy."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        timestamp_str = datetime.now(UTC).isoformat().replace("+00:00", "") + "Z"
        predictions = [
            PredictionLog(
                task_id=f"task-{i}",
                tier="moderate",
                confidence=0.85,
                method="ml_model",
                model_version="v2.0",
                session_id="test_session",
                timestamp=timestamp_str,
                predicted_tier="P2",  # Legacy field for accuracy calculation
                actual_tier="P2" if i < 98 else "P1",  # 98% accuracy
            )
            for i in range(100)
        ]

        accuracy = controller._calculate_accuracy(predictions)
        assert accuracy == 0.98

    def test_calculate_accuracy_empty(self, context, default_config, models_dir):
        """Test _calculate_accuracy handles empty predictions."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        accuracy = controller._calculate_accuracy([])
        assert accuracy == 0.0

    def test_update_active_symlink(self, context, default_config, models_dir):
        """Test _update_active_symlink creates symlink correctly."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        # Create mock model file
        new_model_path = models_dir / "routing_classifier_v2.0.pkl"
        new_model_path.write_text("mock_model")

        result = controller._update_active_symlink()

        assert result.is_ok()
        symlink = models_dir / "routing_classifier_latest.pkl"
        assert symlink.is_symlink()
        assert symlink.resolve() == new_model_path

    def test_rollback_symlink(self, context, default_config, models_dir):
        """Test _rollback_symlink reverts to current model."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        # Create mock model files
        current_model_path = models_dir / "routing_classifier_v1.0.pkl"
        current_model_path.write_text("current_model")
        new_model_path = models_dir / "routing_classifier_v2.0.pkl"
        new_model_path.write_text("new_model")

        # Create symlink pointing to new model
        symlink = models_dir / "routing_classifier_latest.pkl"
        symlink.symlink_to(new_model_path.name)

        # Rollback to current model
        result = controller._rollback_symlink()

        assert result.is_ok()
        assert symlink.is_symlink()
        assert symlink.resolve() == current_model_path

    def test_rollback_error_model_not_found(self, context, default_config, models_dir):
        """Test _rollback_symlink fails if current model not found."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        # No model files created
        result = controller._rollback_symlink()

        assert result.is_err()
        assert "Current model not found" in result.unwrap_err()

    def test_get_predictions_for_stage(self, context, default_config, models_dir):
        """Test _get_predictions_for_stage retrieves VectorStore predictions."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        stage = RolloutStage(name="stage1", percentage=10, duration_hours=16)

        # Store mock predictions in VectorStore
        timestamp_base = datetime.now(UTC) - timedelta(hours=8)
        for i in range(150):
            # Format timestamp properly: replace +00:00 with Z
            timestamp_str = timestamp_base.isoformat().replace("+00:00", "") + "Z"
            prediction = PredictionLog(
                task_id=f"task-{i}",
                tier="moderate",
                confidence=0.85,
                method="ml_model",
                model_version="v2.0",
                session_id="test_session",
                timestamp=timestamp_str,
                predicted_tier="P2",  # Legacy field for accuracy calculation
                actual_tier="P2",  # Legacy field for accuracy calculation
            )
            context.store_memory(
                key=f"prediction_task-{i}_{prediction.timestamp}",
                content=prediction.to_dict(),
                tags=["prediction", "P2", "ml_model"],
            )

        result = controller._get_predictions_for_stage(stage)

        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) >= 100  # At least min_predictions

    def test_wait_for_stage(self, context, default_config, models_dir):
        """Test _wait_for_stage (no-op in tests, tested via integration)."""
        controller = ABRolloutController(
            context=context,
            config=default_config,
            new_model_version="v2.0",
            current_model_version="v1.0",
            models_dir=models_dir,
        )

        stage = RolloutStage(name="stage1", percentage=10, duration_hours=16)

        # In production, this would wait duration_hours
        # In tests, we mock or skip
        result = controller._wait_for_stage(stage)
        assert result.is_ok()


class TestRolloutError:
    """Test RolloutError enum."""

    def test_error_values(self):
        """Test RolloutError enum values."""
        assert RolloutError.INSUFFICIENT_PREDICTIONS == "insufficient_predictions"
        assert RolloutError.ACCURACY_REGRESSION == "accuracy_regression"
        assert RolloutError.MODEL_NOT_FOUND == "model_not_found"
        assert RolloutError.SYMLINK_UPDATE_FAILED == "symlink_update_failed"
        assert RolloutError.STAGE_EXECUTION_FAILED == "stage_execution_failed"
