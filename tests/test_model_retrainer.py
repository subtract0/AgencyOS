"""
Comprehensive unit tests for ModelRetrainer.

Tests the model retraining orchestrator with 20+ tests validating:
- 5-fold cross-validation execution
- Ensemble model training (RandomForest + GradientBoosting)
- Per-fold metrics computation (accuracy, precision, recall, F1)
- Validation accuracy improvement threshold (≥current + 0.5%)
- Versioned artifact serialization (models/ensemble_v{version}.pkl)
- VectorStore metrics storage (Article IV compliance)

Constitutional Compliance:
- Article I: Complete context (retry on training failures, validate metrics)
- Article II: 100% verification (Result pattern, all tests pass)
- Article IV: Store metrics to VectorStore (cross-session learning)
- Article V: Trace to Spec-008 acceptance criteria

Test Framework: pytest with NECESSARY pattern
Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.4

Author: AgencyCodeAgent
Date: 2025-10-10
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import joblib
import numpy as np
import pytest
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier

from shared.agent_context import AgentContext
from shared.models.ensemble_model import EnsembleModel
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import DatasetMetadata, TrainingDataset, TrainingSample
from shared.type_definitions.result import Err, Ok, Result


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
def mock_training_dataset():
    """
    Generate mock TrainingDataset with 100 samples (80 train, 20 val).

    Stratified across 3 tiers for cross-validation testing.
    """
    samples = []

    # Generate 100 samples (stratified: 33+33+34 = 100)
    for tier in [1, 2, 3]:
        count = 33 if tier < 3 else 34  # Tier 3 has 34 to reach 100 total
        for i in range(count):
            features = Mock(spec=TaskFeatureVector)
            features.to_flat_array = Mock(return_value=np.random.rand(1644))

            sample = TrainingSample(
                features=features,
                label=tier,
                confidence=0.8 + (i % 3) * 0.05,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    # Stratified train/val split (80 train = 26+27+27, 20 val = 7+6+7)
    # Tier 1: 0-32 (33 total) → train: 0-25 (26), val: 26-32 (7)
    # Tier 2: 33-65 (33 total) → train: 33-59 (27), val: 60-65 (6)
    # Tier 3: 66-99 (34 total) → train: 66-92 (27), val: 93-99 (7)
    train_indices = list(range(0, 26)) + list(range(33, 60)) + list(range(66, 93))
    val_indices = list(range(26, 33)) + list(range(60, 66)) + list(range(93, 100))

    metadata = DatasetMetadata(
        total_samples=100,
        train_count=80,
        val_count=20,
        label_distribution={1: 33, 2: 33, 3: 34},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    return TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )


@pytest.fixture
def mock_current_model():
    """Create mock current EnsembleModel with 98.0% accuracy."""
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, random_state=42)
    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb)], voting="soft", weights=[0.7, 0.3]
    )

    # Mock fit state
    rf.classes_ = np.array([1, 2, 3])
    gb.classes_ = np.array([1, 2, 3])
    ensemble.estimators_ = [("rf", rf), ("gb", gb)]

    return EnsembleModel(
        ensemble=ensemble,
        rf_model=rf,
        gb_model=gb,
        validation_accuracy=0.980,  # Current baseline: 98.0%
        false_negative_rate=0.015,
        training_date="2025-10-01T12:00:00Z",
        feature_names=[f"feature_{i}" for i in range(1644)],
    )


@pytest.fixture
def temp_model_dir():
    """Create temporary directory for model artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ==============================================================================
# Test Category 1: 5-Fold Cross-Validation (5 tests)
# ==============================================================================


def test_run_5_fold_cross_validation_success(mock_training_dataset, mock_agent_context):
    """
    Test 5-fold cross-validation executes successfully.

    NECESSARY: Normal operation test (happy path)
    AC-1.1: Validate 5-fold CV with stratified sampling

    AAA Pattern:
    - Arrange: Mock dataset with 100 samples
    - Act: Run 5-fold CV retraining
    - Assert: 5 folds executed, per-fold metrics computed
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    # Patch where cross_val_score is USED, not where it's defined
    with patch("tools.ml_routing.model_retrainer.cross_val_score") as mock_cv_score:
        mock_cv_score.return_value = np.array([0.985, 0.988, 0.987, 0.986, 0.989])

        with patch("tools.ml_routing.model_retrainer.confusion_matrix") as mock_cm:
            mock_cm.return_value = np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]])

            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), f"Retraining should succeed, got {result}"
    retraining_result = result.unwrap()

    assert hasattr(retraining_result, "fold_metrics"), "Result must have fold_metrics"
    assert len(retraining_result.fold_metrics) == 5, "Must have 5 fold metrics"


def test_stratified_k_fold_preserves_class_balance(mock_training_dataset, mock_agent_context):
    """
    Test StratifiedKFold preserves class distribution across folds.

    NECESSARY: Normal operation test
    AC-1.1: Validate stratified sampling (balanced tier distribution per fold)

    AAA Pattern:
    - Arrange: Mock dataset, patch StratifiedKFold
    - Act: Run retraining
    - Assert: StratifiedKFold used (not KFold)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.StratifiedKFold") as mock_skf:
        mock_skf_instance = Mock()
        mock_skf_instance.split = Mock(
            return_value=[
                (np.array([0, 1, 2]), np.array([3, 4, 5])),
                (np.array([6, 7, 8]), np.array([9, 10, 11])),
                (np.array([12, 13, 14]), np.array([15, 16, 17])),
                (np.array([18, 19, 20]), np.array([21, 22, 23])),
                (np.array([24, 25, 26]), np.array([27, 28, 29])),
            ]
        )
        mock_skf.return_value = mock_skf_instance

        with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
            with patch(
                "tools.ml_routing.model_retrainer.confusion_matrix",
                return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
            ):
                # Act
                result = retrainer.retrain_ensemble(
                    dataset=mock_training_dataset,
                    current_accuracy=0.980,
                    random_state=42,
                )

        # Assert
        assert result.is_ok(), "Retraining should succeed with StratifiedKFold"
        assert mock_skf.called, "StratifiedKFold should be instantiated"


def test_per_fold_metrics_computed(mock_training_dataset, mock_agent_context):
    """
    Test per-fold metrics (accuracy, precision, recall, F1) are computed.

    NECESSARY: Normal operation test
    AC-1.2: Validate comprehensive metrics per fold

    AAA Pattern:
    - Arrange: Mock dataset, mock sklearn metrics
    - Act: Run retraining
    - Assert: Per-fold metrics contain all 4 metrics
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score") as mock_cv_score:
        # Return different scores per metric type
        def mock_cv_scores(model, X, y, cv, scoring, n_jobs=-1):
            if scoring == "accuracy":
                return np.array([0.985, 0.988, 0.987, 0.986, 0.989])
            elif scoring == "precision_weighted":
                return np.array([0.980, 0.982, 0.981, 0.983, 0.984])
            elif scoring == "recall_weighted":
                return np.array([0.975, 0.978, 0.976, 0.977, 0.979])
            elif scoring == "f1_weighted":
                return np.array([0.977, 0.980, 0.978, 0.979, 0.981])

        mock_cv_score.side_effect = mock_cv_scores

        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    retraining_result = result.unwrap()

    # Check per-fold metrics structure
    for fold_idx, fold_metric in enumerate(retraining_result.fold_metrics):
        assert "accuracy" in fold_metric, f"Fold {fold_idx} must have accuracy"
        assert "precision" in fold_metric, f"Fold {fold_idx} must have precision"
        assert "recall" in fold_metric, f"Fold {fold_idx} must have recall"
        assert "f1" in fold_metric, f"Fold {fold_idx} must have F1 score"


def test_average_metrics_across_folds(mock_training_dataset, mock_agent_context):
    """
    Test average metrics are computed across all folds.

    NECESSARY: Normal operation test
    AC-1.2: Validate averaged metrics (mean of 5 folds)

    AAA Pattern:
    - Arrange: Mock dataset, mock CV scores
    - Act: Run retraining
    - Assert: Average accuracy = mean([0.985, 0.988, 0.987, 0.986, 0.989]) = 0.987
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score") as mock_cv_score:
        mock_cv_score.return_value = np.array([0.985, 0.988, 0.987, 0.986, 0.989])

        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    retraining_result = result.unwrap()

    # Validate average accuracy
    expected_avg = np.mean([0.985, 0.988, 0.987, 0.986, 0.989])
    assert hasattr(retraining_result, "average_accuracy"), "Result must have average_accuracy"
    assert (
        abs(retraining_result.average_accuracy - expected_avg) < 0.001
    ), f"Average accuracy should be {expected_avg:.3f}, got {retraining_result.average_accuracy:.3f}"


def test_cv_folds_configurable(mock_training_dataset, mock_agent_context):
    """
    Test cv_folds parameter is configurable (3, 5, 10 folds).

    NECESSARY: Edge case test
    AC-1.1: Validate configurable fold count

    AAA Pattern:
    - Arrange: Mock dataset, cv_folds=10
    - Act: Run retraining with 10 folds
    - Assert: 10 fold metrics returned
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=10)

    with patch("tools.ml_routing.model_retrainer.cross_val_score") as mock_cv_score:
        mock_cv_score.return_value = np.array([0.986] * 10)  # Must exceed 0.980 + 0.005

        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed with 10 folds"
    retraining_result = result.unwrap()
    assert len(retraining_result.fold_metrics) == 10, "Must have 10 fold metrics"


# ==============================================================================
# Test Category 2: Ensemble Model Training (4 tests)
# ==============================================================================


def test_train_ensemble_model_after_cv(mock_training_dataset, mock_agent_context):
    """
    Test ensemble model is trained after CV validation.

    NECESSARY: Normal operation test
    AC-1.3: Validate ensemble training (RandomForest + GradientBoosting)

    AAA Pattern:
    - Arrange: Mock dataset, mock CV success
    - Act: Run retraining
    - Assert: EnsembleModel returned with VotingClassifier
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    retraining_result = result.unwrap()

    assert hasattr(retraining_result, "model"), "Result must have model field"
    assert isinstance(
        retraining_result.model, EnsembleModel
    ), "Model must be EnsembleModel instance"


def test_ensemble_voting_classifier_configuration(mock_training_dataset, mock_agent_context):
    """
    Test VotingClassifier has soft voting and weights [0.7, 0.3].

    NECESSARY: Normal operation test
    AC-1.3: Validate VotingClassifier configuration

    AAA Pattern:
    - Arrange: Mock dataset
    - Act: Run retraining
    - Assert: Ensemble has soft voting, weights [0.7, 0.3]
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    model = result.unwrap().model

    assert model.ensemble.voting == "soft", f"Voting must be soft, got {model.ensemble.voting}"
    assert model.ensemble.weights == [
        0.7,
        0.3,
    ], f"Weights must be [0.7, 0.3], got {model.ensemble.weights}"


def test_rf_and_gb_models_configured(mock_training_dataset, mock_agent_context):
    """
    Test RandomForest and GradientBoosting models are configured correctly.

    NECESSARY: Normal operation test
    AC-1.3: Validate RF (100 trees) and GB (50 estimators) configurations

    AAA Pattern:
    - Arrange: Mock dataset
    - Act: Run retraining
    - Assert: RF has 100 estimators, GB has 50 estimators
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    model = result.unwrap().model

    # Validate RandomForest
    assert isinstance(
        model.rf_model, RandomForestClassifier
    ), "rf_model must be RandomForestClassifier"
    assert model.rf_model.n_estimators == 100, f"RF must have 100 trees, got {model.rf_model.n_estimators}"

    # Validate GradientBoosting
    assert isinstance(
        model.gb_model, GradientBoostingClassifier
    ), "gb_model must be GradientBoostingClassifier"
    assert (
        model.gb_model.n_estimators == 50
    ), f"GB must have 50 estimators, got {model.gb_model.n_estimators}"


def test_model_trained_on_full_train_set(mock_training_dataset, mock_agent_context):
    """
    Test final model is trained on full training set (not just folds).

    NECESSARY: Normal operation test
    AC-1.3: Validate final model uses all training data (80 samples)

    AAA Pattern:
    - Arrange: Mock dataset with 80 train samples
    - Act: Run retraining, check model fit
    - Assert: Model trained on 80 samples (full train set)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            with patch.object(VotingClassifier, "fit") as mock_fit:
                # Act
                result = retrainer.retrain_ensemble(
                    dataset=mock_training_dataset,
                    current_accuracy=0.980,
                    random_state=42,
                )

                # Assert
                assert mock_fit.called, "VotingClassifier.fit should be called"
                call_args = mock_fit.call_args[0]
                X_train, y_train = call_args[0], call_args[1]

                assert len(X_train) == 80, f"Model should train on 80 samples, got {len(X_train)}"


# ==============================================================================
# Test Category 3: Validation Accuracy Threshold (4 tests)
# ==============================================================================


def test_validation_accuracy_improvement_check(mock_training_dataset, mock_agent_context):
    """
    Test validation accuracy must be ≥current + 0.5%.

    NECESSARY: Normal operation test
    AC-1.4: Validate accuracy improvement threshold (≥current + 0.5%)

    AAA Pattern:
    - Arrange: Current accuracy 98.0%, new accuracy 98.6%
    - Act: Run retraining
    - Assert: Returns Ok (improvement: 98.6% - 98.0% = 0.6% ≥ 0.5%)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.986] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,  # Current: 98.0%
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed with 0.6% improvement"
    retraining_result = result.unwrap()
    assert retraining_result.average_accuracy >= 0.985, "New accuracy should be ≥98.5%"


def test_insufficient_improvement_returns_err(mock_training_dataset, mock_agent_context):
    """
    Test accuracy improvement <0.5% returns Err.

    NECESSARY: Error condition test
    AC-1.4: Enforce minimum 0.5% accuracy improvement

    AAA Pattern:
    - Arrange: Current accuracy 98.0%, new accuracy 98.3%
    - Act: Run retraining
    - Assert: Returns Err (improvement: 98.3% - 98.0% = 0.3% < 0.5%)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.983] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,  # Current: 98.0%
                random_state=42,
            )

    # Assert
    assert result.is_err(), "Retraining should fail with insufficient improvement"
    error_msg = result.unwrap_err()
    assert "improvement" in error_msg.lower(), f"Error should mention improvement, got: {error_msg}"


def test_accuracy_at_threshold_succeeds(mock_training_dataset, mock_agent_context):
    """
    Test accuracy at exactly current + 0.5% succeeds (boundary test).

    NECESSARY: Edge case test
    AC-1.4: Validate accuracy ≥current + 0.5% (inclusive)

    AAA Pattern:
    - Arrange: Current accuracy 98.0%, new accuracy 98.5%
    - Act: Run retraining
    - Assert: Returns Ok (improvement: 98.5% - 98.0% = 0.5%, exact threshold)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,  # Current: 98.0%
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed with exact 0.5% improvement"


def test_accuracy_decrease_returns_err(mock_training_dataset, mock_agent_context):
    """
    Test accuracy decrease returns Err (regression detection).

    NECESSARY: Error condition test
    AC-1.4: Detect accuracy regression (new < current)

    AAA Pattern:
    - Arrange: Current accuracy 98.0%, new accuracy 97.8%
    - Act: Run retraining
    - Assert: Returns Err (regression: 97.8% < 98.0%)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.978] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,  # Current: 98.0%
                random_state=42,
            )

    # Assert
    assert result.is_err(), "Retraining should fail with accuracy regression"
    error_msg = result.unwrap_err()
    assert (
        "regression" in error_msg.lower() or "decrease" in error_msg.lower()
    ), f"Error should mention regression, got: {error_msg}"


# ==============================================================================
# Test Category 4: Versioned Artifact Serialization (4 tests)
# ==============================================================================


def test_serialize_model_to_versioned_artifact(
    mock_training_dataset, mock_agent_context, temp_model_dir
):
    """
    Test model is serialized to models/ensemble_v{version}.pkl.

    NECESSARY: Normal operation test
    AC-1.5: Validate versioned artifact generation

    AAA Pattern:
    - Arrange: Mock dataset, temp model dir
    - Act: Run retraining with version=v1.1
    - Assert: File models/ensemble_v1.1.pkl created
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(
        context=mock_agent_context, cv_folds=5, model_output_dir=temp_model_dir
    )

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
                version="v1.1",
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    model_path = Path(temp_model_dir) / "ensemble_v1.1.pkl"
    assert model_path.exists(), f"Model artifact should exist at {model_path}"


def test_serialized_model_loadable(mock_training_dataset, mock_agent_context, temp_model_dir):
    """
    Test serialized model can be loaded with joblib.

    NECESSARY: Normal operation test
    AC-1.5: Validate model artifact is loadable

    AAA Pattern:
    - Arrange: Mock dataset, save model
    - Act: Run retraining, load saved model
    - Assert: Loaded model has same accuracy as saved model
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(
        context=mock_agent_context, cv_folds=5, model_output_dir=temp_model_dir
    )

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
                version="v1.2",
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    saved_model = result.unwrap().model

    # Load model from disk
    model_path = Path(temp_model_dir) / "ensemble_v1.2.pkl"
    loaded_model = joblib.load(model_path)

    assert isinstance(loaded_model, EnsembleModel), "Loaded model must be EnsembleModel"
    assert (
        loaded_model.validation_accuracy == saved_model.validation_accuracy
    ), "Loaded accuracy should match saved accuracy"


def test_version_defaults_to_incremented(mock_training_dataset, mock_agent_context, temp_model_dir):
    """
    Test version auto-increments if not provided (v1.0 → v1.1).

    NECESSARY: Normal operation test
    AC-1.5: Validate auto-versioning

    AAA Pattern:
    - Arrange: Mock dataset, no version parameter
    - Act: Run retraining
    - Assert: Version auto-incremented from dataset version
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(
        context=mock_agent_context, cv_folds=5, model_output_dir=temp_model_dir
    )

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act (no version parameter)
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    retraining_result = result.unwrap()

    # Check version was auto-incremented (v1.0 → v1.1)
    assert hasattr(retraining_result, "version"), "Result must have version field"
    assert retraining_result.version == "v1.1", f"Version should be v1.1, got {retraining_result.version}"


def test_artifact_metadata_stored(mock_training_dataset, mock_agent_context, temp_model_dir):
    """
    Test artifact metadata is stored alongside model.

    NECESSARY: Normal operation test
    AC-1.5: Validate metadata file creation (ensemble_v{version}_metadata.json)

    AAA Pattern:
    - Arrange: Mock dataset, temp model dir
    - Act: Run retraining
    - Assert: Metadata JSON file created with training date, metrics
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(
        context=mock_agent_context, cv_folds=5, model_output_dir=temp_model_dir
    )

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
                version="v1.3",
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"

    # Check metadata file exists
    metadata_path = Path(temp_model_dir) / "ensemble_v1.3_metadata.json"
    assert metadata_path.exists(), f"Metadata file should exist at {metadata_path}"

    # Validate metadata content
    import json

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    assert "training_date" in metadata, "Metadata must have training_date"
    assert "average_accuracy" in metadata, "Metadata must have average_accuracy"
    assert "version" in metadata, "Metadata must have version"


# ==============================================================================
# Test Category 5: VectorStore Metrics Storage (3 tests)
# ==============================================================================


def test_store_metrics_to_vectorstore(mock_training_dataset, mock_agent_context):
    """
    Test metrics are stored to VectorStore (Article IV compliance).

    NECESSARY: Normal operation test
    AC-1.6: Validate VectorStore storage (cross-session learning)

    AAA Pattern:
    - Arrange: Mock dataset, mock AgentContext
    - Act: Run retraining
    - Assert: context.store_memory called with metrics
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"
    assert mock_agent_context.store_memory.called, "Metrics should be stored to VectorStore"

    # Validate stored content
    call_args = mock_agent_context.store_memory.call_args
    # call_args is a tuple of (args, kwargs), access via kwargs
    stored_content = call_args.kwargs["content"]

    assert "average_accuracy" in stored_content, "Stored content must have average_accuracy"
    assert "fold_metrics" in stored_content, "Stored content must have fold_metrics"
    assert "version" in stored_content, "Stored content must have version"


def test_vectorstore_tags_include_retraining(mock_training_dataset, mock_agent_context):
    """
    Test VectorStore tags include ["retraining", "validation", "leap5_phase4"].

    NECESSARY: Normal operation test
    AC-1.6: Validate correct tags for searchability

    AAA Pattern:
    - Arrange: Mock dataset
    - Act: Run retraining
    - Assert: store_memory called with correct tags
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"

    # Validate tags
    call_args = mock_agent_context.store_memory.call_args
    stored_tags = call_args.kwargs["tags"]  # Keyword argument

    assert "retraining" in stored_tags, "Tags must include 'retraining'"
    assert "validation" in stored_tags, "Tags must include 'validation'"
    assert "leap5_phase4" in stored_tags, "Tags must include 'leap5_phase4'"


def test_metrics_include_confidence_score(mock_training_dataset, mock_agent_context):
    """
    Test stored metrics include confidence score (0.0-1.0).

    NECESSARY: Normal operation test
    AC-1.6: Validate confidence score for VectorStore queries

    AAA Pattern:
    - Arrange: Mock dataset
    - Act: Run retraining
    - Assert: Stored content has confidence field (≥0.6)
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            # Act
            result = retrainer.retrain_ensemble(
                dataset=mock_training_dataset,
                current_accuracy=0.980,
                random_state=42,
            )

    # Assert
    assert result.is_ok(), "Retraining should succeed"

    # Validate confidence in stored content
    call_args = mock_agent_context.store_memory.call_args
    stored_content = call_args.kwargs["content"]

    assert "confidence" in stored_content, "Stored content must have confidence score"
    assert 0.0 <= stored_content["confidence"] <= 1.0, "Confidence must be in [0.0, 1.0]"
    assert stored_content["confidence"] >= 0.6, "Confidence should be ≥0.6 for VectorStore"


# ==============================================================================
# Test Category 6: Error Handling (3 tests)
# ==============================================================================


def test_insufficient_training_samples_returns_err():
    """
    Test <50 training samples returns Err.

    NECESSARY: Error condition test
    AC-1.7: Validate minimum training sample requirement

    AAA Pattern:
    - Arrange: Dataset with only 40 training samples
    - Act: Run retraining
    - Assert: Returns Err with insufficient data message
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    context = Mock(spec=AgentContext)
    retrainer = ModelRetrainer(context=context, cv_folds=5)

    # Create dataset with only 40 train samples
    samples = []
    for tier in [1, 2, 3]:
        for i in range(16):
            features = Mock(spec=TaskFeatureVector)
            features.to_flat_array = Mock(return_value=np.random.rand(1644))

            sample = TrainingSample(
                features=features,
                label=tier,
                confidence=0.8,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    train_indices = list(range(0, 40))  # Only 40 train samples
    val_indices = list(range(40, 48))

    metadata = DatasetMetadata(
        total_samples=48,
        train_count=40,
        val_count=8,
        label_distribution={1: 16, 2: 16, 3: 16},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )

    # Act
    result = retrainer.retrain_ensemble(
        dataset=dataset,
        current_accuracy=0.980,
        random_state=42,
    )

    # Assert
    assert result.is_err(), "Retraining should fail with <50 train samples"
    error_msg = result.unwrap_err()
    assert "insufficient" in error_msg.lower(), f"Error should mention insufficient data, got: {error_msg}"


def test_cv_training_failure_returns_err(mock_training_dataset, mock_agent_context):
    """
    Test sklearn cross-validation failure is handled gracefully.

    NECESSARY: Error condition test
    AC-1.7: Validate sklearn error handling

    AAA Pattern:
    - Arrange: Mock cross_val_score to raise exception
    - Act: Run retraining
    - Assert: Returns Err with sklearn error message
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(context=mock_agent_context, cv_folds=5)

    with patch(
        "tools.ml_routing.model_retrainer.cross_val_score", side_effect=ValueError("sklearn CV error")
    ):
        # Act
        result = retrainer.retrain_ensemble(
            dataset=mock_training_dataset,
            current_accuracy=0.980,
            random_state=42,
        )

    # Assert
    assert result.is_err(), "Retraining should fail with sklearn exception"
    error_msg = result.unwrap_err()
    assert "sklearn" in error_msg.lower() or "cv" in error_msg.lower(), f"Error should mention sklearn, got: {error_msg}"


def test_serialization_failure_returns_err(mock_training_dataset, mock_agent_context, temp_model_dir):
    """
    Test joblib serialization failure is handled gracefully.

    NECESSARY: Error condition test
    AC-1.7: Validate serialization error handling

    AAA Pattern:
    - Arrange: Mock joblib.dump to raise exception
    - Act: Run retraining
    - Assert: Returns Err with serialization error message
    """
    # Arrange
    from tools.ml_routing.model_retrainer import ModelRetrainer

    retrainer = ModelRetrainer(
        context=mock_agent_context, cv_folds=5, model_output_dir=temp_model_dir
    )

    with patch("tools.ml_routing.model_retrainer.cross_val_score", return_value=np.array([0.985] * 5)):
        with patch(
            "tools.ml_routing.model_retrainer.confusion_matrix",
            return_value=np.array([[27, 0, 0], [0, 26, 0], [0, 0, 26]]),
        ):
            with patch("tools.ml_routing.model_retrainer.joblib.dump", side_effect=IOError("Disk full")):
                # Act
                result = retrainer.retrain_ensemble(
                    dataset=mock_training_dataset,
                    current_accuracy=0.980,
                    random_state=42,
                    version="v1.4",
                )

    # Assert
    assert result.is_err(), "Retraining should fail with serialization error"
    error_msg = result.unwrap_err()
    assert "serialization" in error_msg.lower() or "save" in error_msg.lower(), f"Error should mention serialization, got: {error_msg}"


# ==============================================================================
# End of Test Suite
# ==============================================================================
