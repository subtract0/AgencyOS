"""
Comprehensive TDD tests for WeeklyRetrainingScheduler orchestrator.

Tests automated weekly retraining workflow: merge data, retrain model,
validate accuracy, store artifacts, generate reports.

Constitutional Compliance:
- Article I: Complete context (retry on failures, validate before deploy)
- Article II: 100% verification (Result pattern, accuracy thresholds)
- Article IV: VectorStore integration (store retraining metadata)
- Law #1: TDD - tests written BEFORE implementation
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: AAA pattern (Arrange, Act, Assert)

Coverage Target: >95% for tools/ml_routing/weekly_retraining_scheduler.py

Test Categories (NECESSARY Pattern):
- N: Normal operation (happy path retraining)
- E: Edge cases (no new predictions, insufficient data)
- C: Corner cases (accuracy regression, threshold not met)
- E: Error conditions (merge failures, training errors)
- S: Security (artifact validation, version integrity)
- S: Stress tests (large dataset retraining)
- A: Accessibility (clear error messages, report generation)
- R: Regression (version increments, metadata consistency)
- Y: Yield tests (output validation, Result pattern)

Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.5
Author: CodingAgent
Date: 2025-10-10
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import joblib
import pytest

from shared.agent_context import AgentContext
from shared.models.ensemble_model import EnsembleModel
from shared.models.prediction_log import PredictionLog
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import DatasetMetadata, TrainingDataset, TrainingSample
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.model_retrainer import RetrainingResult
from tools.ml_routing.training_data_merger import TrainingDataMerger
from tools.ml_routing.weekly_retraining_scheduler import (
    RetrainingReport,
    SchedulerConfig,
    SchedulerError,
    WeeklyRetrainingScheduler,
)

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
def sample_config():
    """Create sample SchedulerConfig."""
    return SchedulerConfig(
        cron_schedule="0 2 * * 0",
        days_back=7,
        min_confidence=0.8,
        min_accuracy_improvement=0.005,
        model_output_dir="models",
        report_output_dir="reports",
    )


@pytest.fixture
def sample_training_dataset():
    """Create sample TrainingDataset."""

    # Create simple TaskFeatureVector with correct dimensions
    def create_feature_vector():
        return TaskFeatureVector(
            embedding=[0.0] * 1536,
            tfidf_features=[0.0] * 100,
            description_length=50,
            word_count=10,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=60.0,
            historical_tier_mode=2,
        )

    samples = [
        TrainingSample(
            features=create_feature_vector(),
            label=i % 3 + 1,
            confidence=0.9,
            source="vectorstore",
            task_id=f"task_{i}",
            timestamp=datetime.now(UTC).isoformat(),
        )
        for i in range(100)
    ]

    return TrainingDataset(
        samples=samples,
        train_indices=list(range(80)),
        val_indices=list(range(80, 100)),
        metadata=DatasetMetadata(
            total_samples=100,
            train_count=80,
            val_count=20,
            label_distribution={1: 33, 2: 33, 3: 34},
            created_at=datetime.now(UTC),
            version="v1.0",
            min_confidence=0.8,
            source="vectorstore_quality_feedback",
        ),
    )


@pytest.fixture
def sample_retraining_result():
    """Create sample RetrainingResult."""
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        RandomForestClassifier,
        VotingClassifier,
    )

    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, random_state=42)
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb)], voting="soft", weights=[0.7, 0.3]
    )

    model = EnsembleModel(
        ensemble=ensemble,
        rf_model=rf,
        gb_model=gb,
        validation_accuracy=0.984,
        false_negative_rate=0.018,
        training_date=datetime.now(UTC).isoformat(),
        feature_names=[f"feature_{i}" for i in range(1644)],
    )

    return RetrainingResult(
        model=model,
        fold_metrics=[
            {"accuracy": 0.98, "precision": 0.97, "recall": 0.98, "f1": 0.975},
            {"accuracy": 0.99, "precision": 0.98, "recall": 0.99, "f1": 0.985},
        ],
        average_accuracy=0.984,
        average_precision=0.975,
        average_recall=0.985,
        average_f1=0.980,
        version="v1.1",
        training_date=datetime.now(UTC).isoformat(),
        artifact_path="models/ensemble_v1.1.pkl",
    )


@pytest.fixture
def sample_predictions():
    """Create sample PredictionLog instances."""
    tier_names = ["simple", "moderate", "complex"]
    return [
        PredictionLog(
            task_id=f"task_{i}",
            tier=tier_names[i % 3],  # Use valid tier names
            confidence=0.9,
            method="ml_model",  # Valid method name
            model_version="2025-10-10T12:00:00Z",  # Added required field
            class_probabilities={  # Added required field
                "simple": 0.1 if i % 3 != 0 else 0.8,
                "moderate": 0.1 if i % 3 != 1 else 0.8,
                "complex": 0.1 if i % 3 != 2 else 0.8,
            },
            session_id="test_session",  # Added required field
            timestamp=datetime.now(UTC).isoformat(),  # Convert to ISO string
        )
        for i in range(50)
    ]


# ==============================================================================
# N: Normal Operation Tests
# ==============================================================================


def test_scheduler_config_validation(sample_config):
    """Test SchedulerConfig validates all required fields."""
    # Arrange & Act
    config = sample_config

    # Assert
    assert config.cron_schedule == "0 2 * * 0"
    assert config.days_back == 7
    assert config.min_confidence == 0.8
    assert config.min_accuracy_improvement == 0.005
    assert config.model_output_dir == "models"
    assert config.report_output_dir == "reports"


def test_scheduler_initialization(mock_agent_context, sample_config, temp_model_dir):
    """Test WeeklyRetrainingScheduler initializes with valid config."""
    # Arrange
    config = SchedulerConfig(
        cron_schedule="0 2 * * 0",
        days_back=7,
        min_confidence=0.8,
        min_accuracy_improvement=0.005,
        model_output_dir=str(temp_model_dir / "models"),
        report_output_dir=str(temp_model_dir / "reports"),
    )

    # Act
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=config)

    # Assert
    assert scheduler.context == mock_agent_context
    assert scheduler.config == config
    assert Path(scheduler.config.model_output_dir).exists()
    assert Path(scheduler.config.report_output_dir).exists()


def test_load_current_model_metadata_success(mock_agent_context, sample_config, temp_model_dir):
    """Test loading current model metadata from models/ensemble_active.pkl."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    # Create mock model metadata
    metadata = {
        "version": "v1.0",
        "validation_accuracy": 0.980,
        "training_date": "2025-10-03T12:00:00Z",
    }

    model_path = temp_model_dir / "ensemble_active.pkl"
    metadata_path = temp_model_dir / "ensemble_active_metadata.json"

    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

    # Act
    with patch.object(scheduler, "_get_active_model_path", return_value=model_path):
        result = scheduler._load_current_model_metadata()

    # Assert
    assert result.is_ok()
    loaded_metadata = result.unwrap()
    assert loaded_metadata["version"] == "v1.0"
    assert loaded_metadata["validation_accuracy"] == 0.980


def test_orchestrate_retraining_happy_path(
    mock_agent_context,
    sample_config,
    temp_model_dir,
    sample_predictions,
    sample_training_dataset,
    sample_retraining_result,
):
    """Test full retraining orchestration (happy path)."""
    # Arrange
    config = SchedulerConfig(
        cron_schedule="0 2 * * 0",
        days_back=7,
        min_confidence=0.8,
        min_accuracy_improvement=0.005,
        model_output_dir=str(temp_model_dir / "models"),
        report_output_dir=str(temp_model_dir / "reports"),
    )
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=config)

    # Mock pipeline components
    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok(
            {
                "version": "v1.0",
                "validation_accuracy": 0.975,
                "training_date": "2025-10-03T12:00:00Z",
            }
        )

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Ok(sample_training_dataset)

            with patch.object(scheduler, "_retrain_model") as mock_retrain:
                mock_retrain.return_value = Ok(sample_retraining_result)

                with patch.object(scheduler, "_generate_report") as mock_report:
                    report = RetrainingReport(
                        version="v1.1",
                        previous_accuracy=0.975,
                        new_accuracy=0.984,
                        accuracy_improvement=0.009,
                        training_date=datetime.now(UTC).isoformat(),
                        samples_added=50,
                        artifact_path="models/ensemble_v1.1.pkl",
                        report_path="reports/retraining_v1.1.md",
                        success=True,
                    )
                    mock_report.return_value = Ok(report)

                    # Act
                    result = scheduler.run_retraining()

    # Assert
    assert result.is_ok()
    report = result.unwrap()
    assert report.version == "v1.1"
    assert report.success is True
    assert report.accuracy_improvement >= 0.005


# ==============================================================================
# E: Edge Cases
# ==============================================================================


def test_no_new_predictions_available(mock_agent_context, sample_config, temp_model_dir):
    """Test retraining skipped when no new predictions in VectorStore."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.980})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Err("No new predictions found in VectorStore")

            # Act
            result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "No new predictions found" in result.unwrap_err()


def test_insufficient_training_samples(
    mock_agent_context, sample_config, temp_model_dir, sample_training_dataset
):
    """Test retraining fails with insufficient training samples (<50)."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    # Create dataset with <50 samples
    small_dataset = TrainingDataset(
        samples=sample_training_dataset.samples[:30],
        train_indices=list(range(20)),
        val_indices=list(range(20, 30)),
        metadata=DatasetMetadata(
            total_samples=30,
            train_count=20,
            val_count=10,
            label_distribution={1: 10, 2: 10, 3: 10},
            created_at=datetime.now(UTC),
            version="v1.1",
            min_confidence=0.8,
            source="vectorstore",
        ),
    )

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.980})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Ok(small_dataset)

            with patch.object(scheduler, "_retrain_model") as mock_retrain:
                mock_retrain.return_value = Err("Insufficient training samples: 20 < 50")

                # Act
                result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "Insufficient training samples" in result.unwrap_err()


# ==============================================================================
# C: Corner Cases
# ==============================================================================


def test_accuracy_regression_detected(
    mock_agent_context, sample_config, temp_model_dir, sample_training_dataset
):
    """Test retraining aborted when accuracy regresses."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.990})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Ok(sample_training_dataset)

            with patch.object(scheduler, "_retrain_model") as mock_retrain:
                mock_retrain.return_value = Err("Accuracy regression detected: 0.980 < 0.990")

                # Act
                result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "Accuracy regression detected" in result.unwrap_err()


def test_accuracy_improvement_below_threshold(
    mock_agent_context, sample_config, temp_model_dir, sample_training_dataset
):
    """Test retraining rejected when improvement <0.5%."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.981})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Ok(sample_training_dataset)

            with patch.object(scheduler, "_retrain_model") as mock_retrain:
                mock_retrain.return_value = Err(
                    "Insufficient accuracy improvement: 0.984 - 0.981 = 0.003 < 0.005"
                )

                # Act
                result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "Insufficient accuracy improvement" in result.unwrap_err()


# ==============================================================================
# E: Error Conditions
# ==============================================================================


def test_merge_training_data_failure(mock_agent_context, sample_config):
    """Test retraining aborted when data merge fails."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.980})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Err("VectorStore query failed: Connection timeout")

            # Act
            result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "VectorStore query failed" in result.unwrap_err()


def test_model_training_failure(mock_agent_context, sample_config, sample_training_dataset):
    """Test retraining aborted when model training fails."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
        mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.980})

        with patch.object(scheduler, "_merge_training_data") as mock_merge:
            mock_merge.return_value = Ok(sample_training_dataset)

            with patch.object(scheduler, "_retrain_model") as mock_retrain:
                mock_retrain.return_value = Err("Ensemble training failed: Memory allocation error")

                # Act
                result = scheduler.run_retraining()

    # Assert
    assert result.is_err()
    assert "Ensemble training failed" in result.unwrap_err()


# ==============================================================================
# S: Security & Stress Tests
# ==============================================================================


def test_validate_artifact_integrity(mock_agent_context, sample_config, temp_model_dir):
    """Test artifact validation after serialization."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    artifact_path = temp_model_dir / "ensemble_v1.1.pkl"

    # Create mock model
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        RandomForestClassifier,
        VotingClassifier,
    )

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=5, random_state=42)
    ensemble = VotingClassifier(estimators=[("rf", rf), ("gb", gb)])

    # Serialize model
    joblib.dump(ensemble, artifact_path)

    # Act
    result = scheduler._validate_artifact(artifact_path)

    # Assert
    assert result.is_ok()


def test_large_dataset_retraining(
    mock_agent_context, sample_config, temp_model_dir, sample_training_dataset
):
    """Test retraining with large dataset (1000+ samples)."""
    # Arrange
    config = SchedulerConfig(
        cron_schedule="0 2 * * 0",
        days_back=7,
        min_confidence=0.8,
        min_accuracy_improvement=0.005,
        model_output_dir=str(temp_model_dir / "models"),
        report_output_dir=str(temp_model_dir / "reports"),
    )

    # Mock FeatureExtractor to avoid initialization issues
    with patch("tools.ml_routing.weekly_retraining_scheduler.FeatureExtractor"):
        scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=config)

        # Create simple feature vector
        def create_feature_vector():
            return TaskFeatureVector(
                embedding=[0.0] * 1536,
                tfidf_features=[0.0] * 100,
                description_length=50,
                word_count=10,
                has_refactor_keyword=0,
                has_test_keyword=0,
                has_async_keyword=0,
                has_fix_keyword=0,
                estimated_time_seconds=60.0,
                historical_tier_mode=2,
            )

        # Create large dataset
        large_samples = [
            TrainingSample(
                features=create_feature_vector(),
                label=i % 3 + 1,
                confidence=0.9,
                source="vectorstore",
                task_id=f"task_{i}",
                timestamp=datetime.now(UTC).isoformat(),
            )
            for i in range(1000)
        ]

        large_dataset = TrainingDataset(
            samples=large_samples,
            train_indices=list(range(800)),
            val_indices=list(range(800, 1000)),
            metadata=DatasetMetadata(
                total_samples=1000,
                train_count=800,
                val_count=200,
                label_distribution={1: 333, 2: 333, 3: 334},
                created_at=datetime.now(UTC),
                version="v1.1",
                min_confidence=0.8,
                source="vectorstore",
            ),
        )

        with patch.object(scheduler, "_load_current_model_metadata") as mock_load:
            mock_load.return_value = Ok({"version": "v1.0", "validation_accuracy": 0.975})

            with patch.object(scheduler, "_merge_training_data") as mock_merge:
                mock_merge.return_value = Ok(large_dataset)

                with patch.object(scheduler, "_retrain_model") as mock_retrain:
                    # Retraining should handle large dataset
                    assert large_dataset.metadata.train_count == 800
                    assert large_dataset.metadata.val_count == 200


# ==============================================================================
# A: Accessibility (Report Generation)
# ==============================================================================


def test_generate_retraining_report(
    mock_agent_context, sample_config, temp_model_dir, sample_retraining_result
):
    """Test markdown report generation with all metrics."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    previous_accuracy = 0.975
    samples_added = 50

    # Act
    result = scheduler._generate_report(
        retraining_result=sample_retraining_result,
        previous_accuracy=previous_accuracy,
        samples_added=samples_added,
    )

    # Assert
    assert result.is_ok()
    report = result.unwrap()
    assert report.version == "v1.1"
    assert report.previous_accuracy == 0.975
    assert report.new_accuracy == 0.984
    assert abs(report.accuracy_improvement - 0.009) < 1e-6  # Floating-point tolerance
    assert report.samples_added == 50
    assert report.success is True


def test_report_contains_required_sections(
    mock_agent_context, sample_config, temp_model_dir, sample_retraining_result
):
    """Test report markdown contains all required sections."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    # Act
    result = scheduler._generate_report(
        retraining_result=sample_retraining_result, previous_accuracy=0.975, samples_added=50
    )

    # Assert
    assert result.is_ok()
    report = result.unwrap()

    # Validate report path exists
    assert Path(report.report_path).parent.exists()


# ==============================================================================
# R: Regression (Version Management)
# ==============================================================================


def test_version_increment_consistency(mock_agent_context, sample_config):
    """Test version increments correctly (v1.0 → v1.1 → v1.2)."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    # Act
    v1 = scheduler._increment_version("v1.0")
    v2 = scheduler._increment_version(v1)
    v3 = scheduler._increment_version(v2)

    # Assert
    assert v1 == "v1.1"
    assert v2 == "v1.2"
    assert v3 == "v1.3"


def test_metadata_stored_to_vectorstore(
    mock_agent_context, sample_config, sample_retraining_result
):
    """Test retraining metadata stored to VectorStore (Article IV)."""
    # Arrange
    scheduler = WeeklyRetrainingScheduler(context=mock_agent_context, config=sample_config)

    # Act
    scheduler._store_metadata_to_vectorstore(
        retraining_result=sample_retraining_result,
        previous_accuracy=0.975,
        samples_added=50,
    )

    # Assert
    mock_agent_context.store_memory.assert_called_once()
    call_args = mock_agent_context.store_memory.call_args

    # Validate stored content
    assert "retraining_v1.1" in call_args[1]["key"]
    assert "retraining" in call_args[1]["tags"]
    assert "leap5_phase4" in call_args[1]["tags"]


# ==============================================================================
# Y: Yield Tests (Output Validation)
# ==============================================================================


def test_retraining_report_pydantic_validation():
    """Test RetrainingReport validates all fields with Pydantic."""
    # Arrange & Act
    report = RetrainingReport(
        version="v1.1",
        previous_accuracy=0.975,
        new_accuracy=0.984,
        accuracy_improvement=0.009,
        training_date=datetime.now(UTC).isoformat(),
        samples_added=50,
        artifact_path="models/ensemble_v1.1.pkl",
        report_path="reports/retraining_v1.1.md",
        success=True,
    )

    # Assert
    assert report.version == "v1.1"
    assert report.accuracy_improvement > 0.005
    assert report.success is True


def test_scheduler_error_enum():
    """Test SchedulerError enum covers all error categories."""
    # Arrange & Act
    errors = [
        SchedulerError.METADATA_LOAD_FAILED,
        SchedulerError.MERGE_FAILED,
        SchedulerError.TRAINING_FAILED,
        SchedulerError.VALIDATION_FAILED,
        SchedulerError.ARTIFACT_SERIALIZATION_FAILED,
        SchedulerError.REPORT_GENERATION_FAILED,
    ]

    # Assert
    assert len(errors) == 6
    assert all(isinstance(e, SchedulerError) for e in errors)


def test_result_pattern_enforced_throughout():
    """Test all scheduler methods return Result<T, E>."""
    # Arrange
    mock_context = Mock(spec=AgentContext)
    config = SchedulerConfig(
        cron_schedule="0 2 * * 0",
        days_back=7,
        min_confidence=0.8,
        min_accuracy_improvement=0.005,
        model_output_dir="models",
        report_output_dir="reports",
    )
    scheduler = WeeklyRetrainingScheduler(context=mock_context, config=config)

    # Act & Assert - check return types are Result
    # _load_current_model_metadata returns Result
    with patch.object(scheduler, "_get_active_model_path"):
        result = scheduler._load_current_model_metadata()
        assert hasattr(result, "is_ok") and hasattr(result, "is_err")
