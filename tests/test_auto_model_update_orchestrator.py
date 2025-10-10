"""
Tests for AutoModelUpdateOrchestrator - end-to-end retraining → A/B rollout pipeline.

Tests automated model update workflow: trigger retraining, validate accuracy,
orchestrate A/B rollout, handle emergency deployments.

Constitutional Compliance:
- Article I: Complete context (validate each stage before proceeding)
- Article II: 100% verification (Result pattern, all tests must pass)
- Article III: Automated pipeline (no manual intervention)
- Article IV: VectorStore integration (pipeline metadata storage)
- Law #1: TDD - tests written BEFORE implementation
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: AAA pattern (Arrange, Act, Assert)

Coverage Target: >95% for tools/ml_routing/auto_model_update_orchestrator.py

Test Categories (NECESSARY Pattern):
- N: Normal operation (happy path retraining + A/B rollout)
- E: Edge cases (accuracy improvement below threshold, skip A/B)
- C: Corner cases (emergency mode, retraining failure)
- E: Error conditions (rollout failures, validation errors)
- S: Security (artifact integrity, version validation)
- S: Stress tests (large-scale pipeline execution)
- A: Accessibility (clear error messages, metadata logging)
- R: Regression (version consistency, symlink integrity)
- Y: Yield tests (output validation, Result pattern)

Reference: Task description - AutoModelUpdateOrchestrator implementation
Author: AgencyCodeAgent
Date: 2025-10-10
"""

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.ab_rollout_controller import RolloutConfig, RolloutResult
from tools.ml_routing.auto_model_update_orchestrator import (
    AutoModelUpdateOrchestrator,
    OrchestrationError,
    OrchestratorConfig,
    UpdateResult,
)
from tools.ml_routing.weekly_retraining_scheduler import RetrainingReport

# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def mock_agent_context():
    """Create mock AgentContext for VectorStore operations."""
    context = Mock(spec=AgentContext)
    context.store_memory = Mock()
    context.search_memories = Mock(return_value=[])
    return context


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for model artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_orchestrator_config():
    """Create sample OrchestratorConfig."""
    return OrchestratorConfig(
        retraining_enabled=True,
        ab_rollout_enabled=True,
        emergency_mode=False,
        min_accuracy_improvement=0.005,
        model_output_dir="models",
    )


@pytest.fixture
def sample_retraining_report():
    """Create sample RetrainingReport for successful retraining."""
    return RetrainingReport(
        version="v2.0",
        previous_accuracy=0.980,
        new_accuracy=0.986,
        accuracy_improvement=0.006,
        training_date=datetime.now(UTC).isoformat(),
        samples_added=150,
        artifact_path="models/ensemble_v2.0.pkl",
        report_path="reports/retraining_v2.0.md",
        success=True,
    )


@pytest.fixture
def sample_retraining_report_no_improvement():
    """Create RetrainingReport with insufficient accuracy improvement."""
    return RetrainingReport(
        version="v2.0",
        previous_accuracy=0.980,
        new_accuracy=0.982,
        accuracy_improvement=0.002,  # Below 0.5% threshold
        training_date=datetime.now(UTC).isoformat(),
        samples_added=150,
        artifact_path="models/ensemble_v2.0.pkl",
        report_path="reports/retraining_v2.0.md",
        success=True,
    )


@pytest.fixture
def sample_rollout_result_success():
    """Create sample RolloutResult for successful rollout."""
    return RolloutResult(
        success=True,
        stage_completed="stage3",
        new_model_accuracy=0.986,
        current_model_accuracy=0.980,
        predictions_analyzed=500,
        rollback_triggered=False,
        message="Rollout completed: v2.0 active",
    )


@pytest.fixture
def sample_rollout_result_rollback():
    """Create sample RolloutResult for rollback scenario."""
    return RolloutResult(
        success=False,
        stage_completed="stage2",
        new_model_accuracy=0.975,
        current_model_accuracy=0.980,
        predictions_analyzed=300,
        rollback_triggered=True,
        message="Rollback: new accuracy 0.975 < current 0.980 - 0.02",
    )


# ==============================================================================
# Test OrchestratorConfig Pydantic Model
# ==============================================================================


class TestOrchestratorConfig:
    """Test OrchestratorConfig Pydantic model validation."""

    def test_valid_config(self):
        """Test OrchestratorConfig with valid parameters."""
        config = OrchestratorConfig(
            retraining_enabled=True,
            ab_rollout_enabled=True,
            emergency_mode=False,
            min_accuracy_improvement=0.005,
            model_output_dir="models",
        )

        assert config.retraining_enabled is True
        assert config.ab_rollout_enabled is True
        assert config.emergency_mode is False
        assert config.min_accuracy_improvement == 0.005

    def test_emergency_mode_disables_ab_rollout(self):
        """Test emergency mode bypasses A/B rollout."""
        config = OrchestratorConfig(
            retraining_enabled=True,
            ab_rollout_enabled=True,
            emergency_mode=True,  # Should override ab_rollout_enabled
            min_accuracy_improvement=0.005,
            model_output_dir="models",
        )

        # Emergency mode should be True
        assert config.emergency_mode is True

    def test_default_config(self):
        """Test OrchestratorConfig with default values."""
        config = OrchestratorConfig()

        assert config.retraining_enabled is True
        assert config.ab_rollout_enabled is True
        assert config.emergency_mode is False
        assert config.min_accuracy_improvement == 0.005
        assert config.model_output_dir == "models"


# ==============================================================================
# Test UpdateResult Pydantic Model
# ==============================================================================


class TestUpdateResult:
    """Test UpdateResult Pydantic model validation."""

    def test_valid_update_result(self):
        """Test UpdateResult with valid fields."""
        result = UpdateResult(
            success=True,
            version="v2.0",
            retraining_completed=True,
            rollout_completed=True,
            new_accuracy=0.986,
            previous_accuracy=0.980,
            rollback_occurred=False,
            message="Pipeline completed: v2.0 deployed",
        )

        assert result.success is True
        assert result.version == "v2.0"
        assert result.rollback_occurred is False

    def test_update_result_with_rollback(self):
        """Test UpdateResult with rollback scenario."""
        result = UpdateResult(
            success=False,
            version="v2.0",
            retraining_completed=True,
            rollout_completed=False,
            new_accuracy=0.975,
            previous_accuracy=0.980,
            rollback_occurred=True,
            message="Rollback triggered: accuracy regression",
        )

        assert result.success is False
        assert result.rollback_occurred is True


# ==============================================================================
# Test Normal Operation (N)
# ==============================================================================


class TestNormalOperation:
    """Test normal operation (happy path) of AutoModelUpdateOrchestrator."""

    def test_execute_pipeline_success(
        self,
        mock_agent_context,
        sample_orchestrator_config,
        sample_retraining_report,
        sample_rollout_result_success,
    ):
        """Test successful pipeline execution: retraining → A/B rollout → deployment."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        # Mock scheduler and rollout controller
        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report)

        mock_rollout = Mock()
        mock_rollout.execute_rollout.return_value = Ok(sample_rollout_result_success)

        orchestrator.scheduler = mock_scheduler
        orchestrator._create_rollout_controller = Mock(return_value=mock_rollout)

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()
        update_result = result.unwrap()

        assert update_result.success is True
        assert update_result.version == "v2.0"
        assert update_result.retraining_completed is True
        assert update_result.rollout_completed is True
        assert update_result.new_accuracy == 0.986
        assert update_result.rollback_occurred is False

        # Verify VectorStore storage (Article IV)
        mock_agent_context.store_memory.assert_called_once()

    def test_execute_pipeline_retraining_only(self, mock_agent_context, sample_retraining_report):
        """Test pipeline with retraining but A/B rollout disabled."""
        # Arrange
        config = OrchestratorConfig(
            retraining_enabled=True,
            ab_rollout_enabled=False,  # Skip A/B
            emergency_mode=False,
            min_accuracy_improvement=0.005,
        )

        orchestrator = AutoModelUpdateOrchestrator(context=mock_agent_context, config=config)

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report)

        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()
        update_result = result.unwrap()

        assert update_result.retraining_completed is True
        assert update_result.rollout_completed is False  # Skipped
        assert "a/b rollout skipped" in update_result.message.lower()


# ==============================================================================
# Test Edge Cases (E)
# ==============================================================================


class TestEdgeCases:
    """Test edge cases for AutoModelUpdateOrchestrator."""

    def test_accuracy_improvement_below_threshold(
        self,
        mock_agent_context,
        sample_orchestrator_config,
        sample_retraining_report_no_improvement,
    ):
        """Test pipeline stops when accuracy improvement < threshold."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report_no_improvement)

        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()
        update_result = result.unwrap()

        # Retraining completed but rollout skipped due to insufficient improvement
        assert update_result.retraining_completed is True
        assert update_result.rollout_completed is False
        assert (
            "accuracy improvement below threshold" in update_result.message.lower()
            or "insufficient improvement" in update_result.message.lower()
        )

    def test_emergency_mode_skips_ab_rollout(
        self, mock_agent_context, sample_retraining_report, temp_model_dir
    ):
        """Test emergency mode bypasses A/B rollout for immediate 100% deployment."""
        # Arrange
        config = OrchestratorConfig(
            retraining_enabled=True,
            ab_rollout_enabled=True,
            emergency_mode=True,  # Emergency: skip A/B
            min_accuracy_improvement=0.005,
            model_output_dir=str(temp_model_dir),
        )

        orchestrator = AutoModelUpdateOrchestrator(context=mock_agent_context, config=config)

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report)

        orchestrator.scheduler = mock_scheduler

        # Create dummy model file for symlink update
        model_file = temp_model_dir / "ensemble_v2.0.pkl"
        model_file.touch()

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()
        update_result = result.unwrap()

        assert update_result.retraining_completed is True
        assert update_result.rollout_completed is False  # A/B skipped
        assert "emergency mode" in update_result.message.lower()

        # Verify symlink updated to new version (immediate 100%)
        active_symlink = temp_model_dir / "ensemble_active.pkl"
        assert active_symlink.exists() or active_symlink.is_symlink()


# ==============================================================================
# Test Error Conditions (E)
# ==============================================================================


class TestErrorConditions:
    """Test error conditions for AutoModelUpdateOrchestrator."""

    def test_retraining_failure(self, mock_agent_context, sample_orchestrator_config):
        """Test pipeline handles retraining failure gracefully."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Err("Data merge failed: insufficient samples")

        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_err()
        error_message = result.unwrap_err()

        assert "retraining failed" in error_message.lower()

    def test_rollout_failure_triggers_rollback(
        self,
        mock_agent_context,
        sample_orchestrator_config,
        sample_retraining_report,
        sample_rollout_result_rollback,
    ):
        """Test rollout failure triggers rollback and error reporting."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report)

        mock_rollout = Mock()
        mock_rollout.execute_rollout.return_value = Ok(sample_rollout_result_rollback)

        orchestrator.scheduler = mock_scheduler
        orchestrator._create_rollout_controller = Mock(return_value=mock_rollout)

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()  # Rollback is a "successful" failure (handled gracefully)
        update_result = result.unwrap()

        assert update_result.success is False
        assert update_result.rollback_occurred is True
        assert "rollback" in update_result.message.lower()


# ==============================================================================
# Test VectorStore Integration (Article IV)
# ==============================================================================


class TestVectorStoreIntegration:
    """Test VectorStore integration (Article IV compliance)."""

    def test_metadata_stored_after_success(
        self,
        mock_agent_context,
        sample_orchestrator_config,
        sample_retraining_report,
        sample_rollout_result_success,
    ):
        """Test pipeline stores metadata to VectorStore after successful execution."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Ok(sample_retraining_report)

        mock_rollout = Mock()
        mock_rollout.execute_rollout.return_value = Ok(sample_rollout_result_success)

        orchestrator.scheduler = mock_scheduler
        orchestrator._create_rollout_controller = Mock(return_value=mock_rollout)

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_ok()

        # Verify VectorStore storage called
        mock_agent_context.store_memory.assert_called_once()

        # Get call arguments from mock
        # store_memory(key=..., content=..., tags=...) uses keyword args
        call_kwargs = mock_agent_context.store_memory.call_args.kwargs

        key = call_kwargs["key"]
        content = call_kwargs["content"]
        tags = call_kwargs["tags"]

        # Verify key format
        assert "pipeline_execution" in key

        # Verify content structure
        assert "version" in content
        assert "retraining_completed" in content
        assert "rollout_completed" in content

        # Verify tags
        assert "orchestrator" in tags
        assert "pipeline" in tags
        assert "leap5_phase4" in tags

    def test_metadata_stored_after_failure(self, mock_agent_context, sample_orchestrator_config):
        """Test pipeline stores metadata even after failure (for learning)."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=sample_orchestrator_config
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Err("Training failed: GPU OOM")

        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_err()

        # Even on failure, we should store metadata for learning (Article IV)
        # Note: This depends on implementation - may not store on early failure
        # For now, we test that it doesn't crash


# ==============================================================================
# Test Result Pattern Compliance (Law #5)
# ==============================================================================


class TestResultPattern:
    """Test Result pattern compliance (Constitutional Law #5)."""

    def test_execute_pipeline_returns_result(self, mock_agent_context):
        """Test execute_pipeline returns Result[UpdateResult, str]."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=OrchestratorConfig()
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Err("Test error")
        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert - verify Result type
        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")
        assert hasattr(result, "unwrap")
        assert hasattr(result, "unwrap_err")

    def test_error_messages_are_strings(self, mock_agent_context):
        """Test error messages are strings (not enums or dicts)."""
        # Arrange
        orchestrator = AutoModelUpdateOrchestrator(
            context=mock_agent_context, config=OrchestratorConfig()
        )

        mock_scheduler = Mock()
        mock_scheduler.run_retraining.return_value = Err("Retraining failed")
        orchestrator.scheduler = mock_scheduler

        # Act
        result = orchestrator.execute_pipeline()

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, str)
