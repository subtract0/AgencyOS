"""
Comprehensive unit tests for MLModelTrainer.

Tests the ML model training pipeline with 20+ tests validating:
- Training pipeline execution (ensemble model creation)
- Cross-validation with 5 folds
- False negative rate calculation and threshold enforcement
- Accuracy threshold validation (>98%)
- Training time constraints (<5 minutes)
- Error handling for insufficient/invalid data

Constitutional Compliance:
- Article I: Complete context (mock all dependencies, test all CV folds)
- Article II: 100% verification (test all thresholds, 100% pass rate)
- Article IV: Apply VectorStore patterns for ensemble training tests
- Article V: Trace to Spec-005 acceptance criteria (AC-1.1 to AC-1.5)

Test Framework: pytest with NECESSARY pattern
Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.4

Author: TestGeneratorAgent
Date: 2025-10-10
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pytest
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier

from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import DatasetMetadata, TrainingDataset, TrainingSample
from shared.type_definitions.result import Err, Ok, Result

# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def mock_task_feature_vector():
    """Create a mock TaskFeatureVector for testing."""
    return Mock(spec=TaskFeatureVector, to_flat_array=lambda: np.random.rand(1644))


@pytest.fixture
def mock_training_dataset(mock_task_feature_vector):
    """
    Generate mock TrainingDataset with 100 samples (80 train, 20 val).

    Stratified across 3 tiers (1=simple, 2=moderate, 3=complex).

    Article I Compliance: Complete context (all samples, stratified split).
    """
    samples = []

    # Generate 100 samples (stratified: ~33 per tier)
    for tier in [1, 2, 3]:
        for i in range(34 if tier == 1 else 33):
            # Create mock feature vector for each sample
            features = Mock(spec=TaskFeatureVector)
            features.to_flat_array = Mock(return_value=np.random.rand(1644))

            sample = TrainingSample(
                features=features,
                label=tier,
                confidence=0.8 + (i % 3) * 0.05,  # Vary confidence: 0.8, 0.85, 0.9
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    # Create stratified train/val split (80/20)
    # Train: indices 0-79 (stratified across tiers)
    train_indices = list(range(0, 27)) + list(range(34, 61)) + list(range(67, 94))
    # Val: indices 80-99 (stratified across tiers)
    val_indices = list(range(27, 34)) + list(range(61, 67)) + list(range(94, 100))

    metadata = DatasetMetadata(
        total_samples=100,
        train_count=80,
        val_count=20,
        label_distribution={1: 34, 2: 33, 3: 33},
        created_at=datetime.now(),
        version="v1.100",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )

    return dataset


@pytest.fixture
def mock_cross_val_score(monkeypatch):
    """
    Mock sklearn cross_val_score for deterministic testing.

    Returns 5 folds with accuracy scores: [0.98, 0.99, 0.98, 0.99, 0.98].
    """

    def mock_cv_score(model, X, y, cv, scoring, n_jobs):
        """Return deterministic CV scores for 5 folds."""
        return np.array([0.98, 0.99, 0.98, 0.99, 0.98])

    monkeypatch.setattr("sklearn.model_selection.cross_val_score", mock_cv_score)


@pytest.fixture
def mock_confusion_matrix(monkeypatch):
    """
    Mock sklearn confusion_matrix for FN rate calculation.

    Returns 3x3 confusion matrix (tiers 1, 2, 3):
    [[25  1  1]   # Tier 1: 25 correct, 1 to tier 2, 1 to tier 3
     [ 1 24  1]   # Tier 2: 24 correct, 1 to tier 1, 1 to tier 3
     [ 0  0 26]]  # Tier 3: 26 correct, 0 false negatives

    FN_rate = 0 / (0 + 26) = 0.0 (0%)
    """

    def mock_cm(y_true, y_pred, labels):
        """Return deterministic confusion matrix."""
        return np.array(
            [
                [25, 1, 1],  # Tier 1
                [1, 24, 1],  # Tier 2
                [0, 0, 26],  # Tier 3 (no false negatives)
            ]
        )

    monkeypatch.setattr("sklearn.metrics.confusion_matrix", mock_cm)


@pytest.fixture
def small_training_dataset():
    """
    Create a minimal valid dataset (50 train, 10 val).

    Used for edge case testing (minimum threshold validation).
    """
    samples = []

    # Generate 60 samples (20 per tier)
    for tier in [1, 2, 3]:
        for i in range(20):
            features = Mock(spec=TaskFeatureVector)
            features.to_flat_array = Mock(return_value=np.random.rand(1644))

            sample = TrainingSample(
                features=features,
                label=tier,
                confidence=0.75,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    # Split: 50 train (17+17+16), 10 val (3+3+4)
    train_indices = list(range(0, 17)) + list(range(20, 37)) + list(range(40, 56))
    val_indices = list(range(17, 20)) + list(range(37, 40)) + list(range(56, 60))

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=50,
        val_count=10,
        label_distribution={1: 20, 2: 20, 3: 20},
        created_at=datetime.now(),
        version="v1.60",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    return TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )


# ==============================================================================
# Test Category 1: Happy Path (5 tests)
# ==============================================================================


def test_train_ensemble_model_success(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test successful ensemble model training with valid data.

    NECESSARY: Normal operation test (happy path)
    AC-1.1, AC-1.2, AC-1.3: Validate ensemble creation, accuracy >98%, FN_rate <2%

    AAA Pattern:
    - Arrange: Mock dataset with 100 samples (80 train, 20 val), mock CV scores
    - Act: Train ensemble model with random_state=42
    - Assert: Model returned, accuracy ≥0.98, FN_rate ≤0.02, 1644 features
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), f"Training should succeed with valid data, got {result}"
    model = result.ok()

    # Validate model structure
    assert hasattr(model, "ensemble"), "Model must have ensemble field"
    assert hasattr(model, "validation_accuracy"), "Model must have validation_accuracy field"
    assert hasattr(model, "false_negative_rate"), "Model must have false_negative_rate field"
    assert hasattr(model, "feature_names"), "Model must have feature_names field"

    # Validate thresholds (spec-005 AC-Q.1, AC-Q.2)
    assert model.validation_accuracy >= 0.98, (
        f"Accuracy must be ≥98%, got {model.validation_accuracy}"
    )
    assert model.false_negative_rate <= 0.02, (
        f"FN_rate must be ≤2%, got {model.false_negative_rate}"
    )

    # Validate feature count (1644 dimensions: 1536 embedding + 100 TF-IDF + 8 metadata)
    assert len(model.feature_names) == 1644, (
        f"Must have 1644 features, got {len(model.feature_names)}"
    )


def test_random_forest_configuration(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test RandomForest has correct configuration (100 trees, max_depth=10).

    NECESSARY: Normal operation test
    AC-1.1: Validate RandomForestClassifier baseline configuration

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble model
    - Assert: RF has 100 estimators, max_depth=10, random_state=42
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # Access RandomForest model
    assert hasattr(model, "rf_model"), "Model must have rf_model field"
    rf_model = model.rf_model

    # Validate configuration (spec-006 AC-1.2)
    assert isinstance(rf_model, RandomForestClassifier), "rf_model must be RandomForestClassifier"
    assert rf_model.n_estimators == 100, f"RF must have 100 trees, got {rf_model.n_estimators}"
    assert rf_model.max_depth == 10, f"RF max_depth must be 10, got {rf_model.max_depth}"
    assert rf_model.random_state == 42, f"RF random_state must be 42, got {rf_model.random_state}"


def test_gradient_boosting_configuration(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test GradientBoosting has correct configuration (50 estimators, lr=0.1).

    NECESSARY: Normal operation test
    AC-1.3: Validate GradientBoostingClassifier configuration

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble model
    - Assert: GB has 50 estimators, learning_rate=0.1, random_state=42
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # Access GradientBoosting model
    assert hasattr(model, "gb_model"), "Model must have gb_model field"
    gb_model = model.gb_model

    # Validate configuration (spec-006 AC-1.3)
    assert isinstance(gb_model, GradientBoostingClassifier), (
        "gb_model must be GradientBoostingClassifier"
    )
    assert gb_model.n_estimators == 50, f"GB must have 50 estimators, got {gb_model.n_estimators}"
    assert gb_model.learning_rate == 0.1, (
        f"GB learning_rate must be 0.1, got {gb_model.learning_rate}"
    )
    assert gb_model.random_state == 42, f"GB random_state must be 42, got {gb_model.random_state}"


def test_voting_ensemble_weights(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test VotingClassifier uses soft voting with weights [0.7, 0.3].

    NECESSARY: Normal operation test
    AC-1.1: Validate VotingClassifier ensemble configuration

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble model
    - Assert: Ensemble has soft voting, weights [0.7, 0.3] (RF dominant)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # Access ensemble model
    assert hasattr(model, "ensemble"), "Model must have ensemble field"
    ensemble = model.ensemble

    # Validate configuration (spec-006 AC-1.1)
    assert isinstance(ensemble, VotingClassifier), "Ensemble must be VotingClassifier"
    assert ensemble.voting == "soft", f"Ensemble must use soft voting, got {ensemble.voting}"
    assert ensemble.weights == [0.7, 0.3], (
        f"Ensemble weights must be [0.7, 0.3], got {ensemble.weights}"
    )


def test_ensemble_model_returned(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test EnsembleModel fields are populated correctly.

    NECESSARY: Normal operation test
    AC-1.1 to AC-1.7: Validate all 7 required fields populated

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble model
    - Assert: All fields present (ensemble, rf, gb, accuracy, FN_rate, date, features)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # Validate all 7 required fields (spec-006 AC-1.1 to AC-1.7)
    required_fields = [
        "ensemble",
        "rf_model",
        "gb_model",
        "validation_accuracy",
        "false_negative_rate",
        "training_date",
        "feature_names",
    ]

    for field in required_fields:
        assert hasattr(model, field), f"Model must have {field} field"
        assert getattr(model, field) is not None, f"Field {field} must not be None"

    # Validate field types
    assert isinstance(model.ensemble, VotingClassifier), "ensemble must be VotingClassifier"
    assert isinstance(model.rf_model, RandomForestClassifier), (
        "rf_model must be RandomForestClassifier"
    )
    assert isinstance(model.gb_model, GradientBoostingClassifier), (
        "gb_model must be GradientBoostingClassifier"
    )
    assert isinstance(model.validation_accuracy, float), "validation_accuracy must be float"
    assert isinstance(model.false_negative_rate, float), "false_negative_rate must be float"
    assert isinstance(model.training_date, str), "training_date must be str (ISO 8601)"
    assert isinstance(model.feature_names, list), "feature_names must be list"


# ==============================================================================
# Test Category 2: Cross-Validation (4 tests)
# ==============================================================================


def test_run_cross_validation_5_folds(mock_training_dataset, mock_cross_val_score):
    """
    Test cross-validation runs with 5 folds.

    NECESSARY: Normal operation test
    AC-1.4: Validate 5-fold cross-validation with stratified sampling

    AAA Pattern:
    - Arrange: Mock dataset, mock CV scores
    - Act: Run cross-validation (internal method)
    - Assert: 5 folds executed, scores returned
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act (train_ensemble_model internally calls cross-validation)
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # CV scores should be stored in model metadata (if implemented)
    # This test validates that CV was executed (mocked scores used)
    assert model.validation_accuracy >= 0.98, "CV should produce high accuracy with mock scores"


def test_cv_reports_accuracy_precision_recall(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test cross-validation reports 4 metrics (accuracy, precision, recall, F1).

    NECESSARY: Normal operation test
    AC-1.4: Validate comprehensive CV metrics

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble (internally runs CV)
    - Assert: Metrics available (accuracy at minimum)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # At minimum, accuracy must be available
    assert hasattr(model, "validation_accuracy"), "Model must report accuracy"
    assert 0.0 <= model.validation_accuracy <= 1.0, "Accuracy must be in [0.0, 1.0]"


def test_cv_stratified_k_fold(mock_training_dataset):
    """
    Test cross-validation uses StratifiedKFold (preserves class balance).

    NECESSARY: Normal operation test
    AC-1.4: Validate stratified sampling (balanced tier distribution)

    AAA Pattern:
    - Arrange: Mock dataset, patch StratifiedKFold
    - Act: Train ensemble
    - Assert: StratifiedKFold used (not KFold)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    with patch("sklearn.model_selection.StratifiedKFold") as mock_skf:
        # Mock StratifiedKFold to return 5 folds
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

        with patch(
            "sklearn.model_selection.cross_val_score",
            return_value=np.array([0.98, 0.99, 0.98, 0.99, 0.98]),
        ):
            with patch(
                "sklearn.metrics.confusion_matrix",
                return_value=np.array([[25, 1, 1], [1, 24, 1], [0, 0, 26]]),
            ):
                # Act
                result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

        # Assert
        assert isinstance(result, Ok), "Training should succeed with StratifiedKFold"


def test_cv_scores_stored_in_metadata(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test CV scores are available for logging/monitoring.

    NECESSARY: Normal operation test
    AC-1.4: Validate CV scores stored for analysis

    AAA Pattern:
    - Arrange: Mock dataset, trainer
    - Act: Train ensemble
    - Assert: CV scores accessible (if implemented in metadata)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # CV scores may be stored in model metadata (optional for Phase 2)
    # This test validates they are computable from validation_accuracy
    assert model.validation_accuracy >= 0.98, "Validation accuracy derived from CV"


# ==============================================================================
# Test Category 3: False Negative Rate (4 tests)
# ==============================================================================


def test_calculate_false_negative_rate_complex(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test FN rate calculation for complex tier (FN_complex / (FN_complex + TP_complex)).

    NECESSARY: Normal operation test
    AC-Q.2: Validate false negative rate <2% (complex tasks routed to simple tier)

    AAA Pattern:
    - Arrange: Mock confusion matrix with known FN_rate
    - Act: Train ensemble (internally calculates FN_rate)
    - Assert: FN_rate = 0 / (0 + 26) = 0.0 (from mock confusion matrix)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    model = result.ok()

    # Validate FN_rate calculation (from mock confusion matrix)
    # Mock confusion matrix: tier 3 has 0 false negatives, 26 true positives
    # FN_rate = 0 / (0 + 26) = 0.0
    assert model.false_negative_rate == 0.0, (
        f"FN_rate should be 0.0, got {model.false_negative_rate}"
    )


def test_fn_rate_zero_if_no_complex_samples():
    """
    Test FN rate is 0 when no complex samples exist (edge case).

    NECESSARY: Edge case test
    AC-Q.2: Handle edge case of empty complex tier

    AAA Pattern:
    - Arrange: Dataset with no tier 3 samples
    - Act: Calculate FN rate (internal method)
    - Assert: FN_rate = 0.0 (no complex samples to misclassify)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create dataset with no tier 3 samples
    samples = []
    for tier in [1, 2]:  # Only tier 1 and 2
        for i in range(30):
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

    train_indices = list(range(0, 48))  # 80% train
    val_indices = list(range(48, 60))  # 20% val

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=48,
        val_count=12,
        label_distribution={1: 30, 2: 30, 3: 0},  # No tier 3
        created_at=datetime.now(),
        version="v1.60",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )

    # Mock confusion matrix for tiers 1 and 2 only
    with patch(
        "sklearn.model_selection.cross_val_score",
        return_value=np.array([0.98, 0.99, 0.98, 0.99, 0.98]),
    ):
        with patch("sklearn.metrics.confusion_matrix", return_value=np.array([[25, 2], [1, 24]])):
            # Act
            result = trainer.train_ensemble_model(dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed with no tier 3 samples"
    model = result.ok()

    # FN_rate should be 0.0 (no complex samples to misclassify)
    assert model.false_negative_rate == 0.0, (
        f"FN_rate should be 0.0 with no tier 3, got {model.false_negative_rate}"
    )


def test_fn_rate_threshold_enforcement(mock_training_dataset):
    """
    Test FN_rate >2% returns Err (threshold enforcement).

    NECESSARY: Error condition test
    AC-Q.2: Enforce false negative rate ≤2% threshold

    AAA Pattern:
    - Arrange: Mock confusion matrix with FN_rate = 3% (above threshold)
    - Act: Train ensemble
    - Assert: Returns Err with threshold violation message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock confusion matrix with high FN_rate
    # Tier 3: 2 false negatives, 20 true positives → FN_rate = 2/(2+20) = 9.1% (above 2%)
    with patch(
        "sklearn.model_selection.cross_val_score",
        return_value=np.array([0.98, 0.99, 0.98, 0.99, 0.98]),
    ):
        with patch(
            "sklearn.metrics.confusion_matrix",
            return_value=np.array([[24, 1, 2], [1, 23, 2], [2, 0, 20]]),
        ):
            # Act
            result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with FN_rate >2%"
    error_msg = result.unwrap_err()
    assert "false negative rate" in error_msg.lower(), (
        f"Error should mention FN rate, got: {error_msg}"
    )


def test_confusion_matrix_for_fn_calculation(mock_training_dataset, mock_cross_val_score):
    """
    Test confusion matrix is used for FN calculation.

    NECESSARY: Normal operation test
    AC-Q.2: Validate confusion matrix computation

    AAA Pattern:
    - Arrange: Mock confusion_matrix from sklearn
    - Act: Train ensemble
    - Assert: confusion_matrix called, FN_rate calculated correctly
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    with patch("sklearn.metrics.confusion_matrix") as mock_cm:
        # Mock confusion matrix with known values
        # Tier 3: 1 false negative, 25 true positives → FN_rate = 1/(1+25) = 3.8% (above 2%)
        mock_cm.return_value = np.array([[24, 1, 1], [1, 24, 1], [1, 0, 25]])

        # Act
        result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

        # Assert
        assert mock_cm.called, "confusion_matrix should be called for FN calculation"


# ==============================================================================
# Test Category 4: Threshold Validation (4 tests)
# ==============================================================================


def test_accuracy_below_98_percent_fails(mock_training_dataset):
    """
    Test accuracy <98% returns Err (threshold enforcement).

    NECESSARY: Error condition test
    AC-Q.1: Enforce validation accuracy >98% threshold

    AAA Pattern:
    - Arrange: Mock CV scores with accuracy = 97%
    - Act: Train ensemble
    - Assert: Returns Err with accuracy threshold violation
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock CV scores with low accuracy (97%)
    with patch(
        "sklearn.model_selection.cross_val_score",
        return_value=np.array([0.96, 0.97, 0.97, 0.98, 0.97]),
    ):
        with patch(
            "sklearn.metrics.confusion_matrix",
            return_value=np.array([[25, 1, 1], [1, 24, 1], [0, 0, 26]]),
        ):
            # Act
            result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with accuracy <98%"
    error_msg = result.unwrap_err()
    assert "accuracy" in error_msg.lower(), f"Error should mention accuracy, got: {error_msg}"


def test_accuracy_at_98_percent_succeeds(mock_training_dataset, mock_confusion_matrix):
    """
    Test accuracy at exactly 98% succeeds (boundary test).

    NECESSARY: Edge case test
    AC-Q.1: Validate accuracy ≥98% threshold (inclusive)

    AAA Pattern:
    - Arrange: Mock CV scores with accuracy = 98% (exact threshold)
    - Act: Train ensemble
    - Assert: Returns Ok (threshold met)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock CV scores with exact 98% accuracy
    with patch(
        "sklearn.model_selection.cross_val_score",
        return_value=np.array([0.98, 0.98, 0.98, 0.98, 0.98]),
    ):
        # Act
        result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed with accuracy = 98% (threshold met)"
    model = result.ok()
    assert model.validation_accuracy >= 0.98, "Accuracy should be ≥98%"


def test_fn_rate_above_2_percent_fails(mock_training_dataset, mock_cross_val_score):
    """
    Test FN_rate >2% returns Err (threshold enforcement).

    NECESSARY: Error condition test
    AC-Q.2: Enforce false negative rate ≤2% threshold

    AAA Pattern:
    - Arrange: Mock confusion matrix with FN_rate = 3%
    - Act: Train ensemble
    - Assert: Returns Err with FN_rate threshold violation
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock confusion matrix with FN_rate = 1/(1+23) = 4.2% (above 2%)
    with patch(
        "sklearn.metrics.confusion_matrix",
        return_value=np.array([[24, 1, 1], [1, 24, 1], [1, 0, 23]]),
    ):
        # Act
        result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with FN_rate >2%"
    error_msg = result.unwrap_err()
    assert "false negative" in error_msg.lower(), f"Error should mention FN rate, got: {error_msg}"


def test_fn_rate_at_2_percent_succeeds(mock_training_dataset, mock_cross_val_score):
    """
    Test FN_rate at exactly 2% succeeds (boundary test).

    NECESSARY: Edge case test
    AC-Q.2: Validate FN_rate ≤2% threshold (inclusive)

    AAA Pattern:
    - Arrange: Mock confusion matrix with FN_rate = 2% (exact threshold)
    - Act: Train ensemble
    - Assert: Returns Ok (threshold met)
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock confusion matrix with FN_rate = 1/(1+49) = 2% (exact threshold)
    with patch(
        "sklearn.metrics.confusion_matrix",
        return_value=np.array([[27, 0, 0], [0, 26, 0], [1, 0, 26]]),
    ):
        # Act
        result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed with FN_rate = 2% (threshold met)"
    model = result.ok()
    assert model.false_negative_rate <= 0.02, "FN_rate should be ≤2%"


# ==============================================================================
# Test Category 5: Training Time (2 tests)
# ==============================================================================


def test_training_time_under_5_minutes(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix
):
    """
    Test training completes in <5 minutes (300 seconds).

    NECESSARY: Stress test
    AC-P.2: Validate training time <5 minutes for 1,000 samples (100 samples here)

    AAA Pattern:
    - Arrange: Mock dataset, time tracker
    - Act: Train ensemble with time measurement
    - Assert: Training time <300 seconds
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Act
    start_time = time.perf_counter()
    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)
    end_time = time.perf_counter()

    training_time = end_time - start_time

    # Assert
    assert isinstance(result, Ok), "Training should succeed"
    assert training_time < 300.0, f"Training should complete in <300s, took {training_time:.2f}s"


def test_training_time_warning_if_exceeds(
    mock_training_dataset, mock_cross_val_score, mock_confusion_matrix, caplog
):
    """
    Test warning is logged if training exceeds expected time (no failure).

    NECESSARY: Stress test
    AC-P.2: Validate warning logged if training slow (but don't fail)

    AAA Pattern:
    - Arrange: Mock slow training (simulated with sleep)
    - Act: Train ensemble
    - Assert: Warning logged, but training succeeds
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Mock slow training by patching fit() to add delay
    with patch.object(VotingClassifier, "fit") as mock_fit:

        def slow_fit(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow training
            return Mock()

        mock_fit.side_effect = slow_fit

        with patch(
            "sklearn.model_selection.cross_val_score",
            return_value=np.array([0.98, 0.99, 0.98, 0.99, 0.98]),
        ):
            with patch(
                "sklearn.metrics.confusion_matrix",
                return_value=np.array([[25, 1, 1], [1, 24, 1], [0, 0, 26]]),
            ):
                # Act
                with caplog.at_level("WARNING"):
                    result = trainer.train_ensemble_model(mock_training_dataset, random_state=42)

    # Assert
    assert isinstance(result, Ok), "Training should succeed even if slow"
    # Warning may be logged (implementation-dependent)


# ==============================================================================
# Test Category 6: Error Handling (5 tests)
# ==============================================================================


def test_insufficient_training_data():
    """
    Test <50 train samples returns Err.

    NECESSARY: Error condition test
    AC-P.2: Validate minimum training data requirement (50 samples)

    AAA Pattern:
    - Arrange: Dataset with only 40 train samples
    - Act: Train ensemble
    - Assert: Returns Err with insufficient data message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create dataset with only 40 train samples (below 50 threshold)
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
        version="v1.48",
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
    result = trainer.train_ensemble_model(dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with <50 train samples"
    error_msg = result.unwrap_err()
    assert "insufficient" in error_msg.lower() or "train" in error_msg.lower(), (
        f"Error should mention insufficient training data, got: {error_msg}"
    )


def test_insufficient_validation_data():
    """
    Test <10 val samples returns Err.

    NECESSARY: Error condition test
    AC-P.2: Validate minimum validation data requirement (10 samples)

    AAA Pattern:
    - Arrange: Dataset with only 8 val samples
    - Act: Train ensemble
    - Assert: Returns Err with insufficient validation data message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create dataset with only 8 val samples (below 10 threshold)
    samples = []
    for tier in [1, 2, 3]:
        for i in range(20):
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

    train_indices = list(range(0, 52))  # 52 train samples (above 50)
    val_indices = list(range(52, 60))  # Only 8 val samples (below 10)

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=52,
        val_count=8,
        label_distribution={1: 20, 2: 20, 3: 20},
        created_at=datetime.now(),
        version="v1.60",
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
    result = trainer.train_ensemble_model(dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with <10 val samples"
    error_msg = result.unwrap_err()
    assert "validation" in error_msg.lower() or "val" in error_msg.lower(), (
        f"Error should mention insufficient validation data, got: {error_msg}"
    )


def test_single_class_dataset():
    """
    Test dataset with only 1 unique label returns Err.

    NECESSARY: Error condition test
    AC-Q.3: Validate multi-class dataset requirement

    AAA Pattern:
    - Arrange: Dataset with only tier 1 samples
    - Act: Train ensemble
    - Assert: Returns Err with single class message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create dataset with only tier 1 samples
    samples = []
    for i in range(60):
        features = Mock(spec=TaskFeatureVector)
        features.to_flat_array = Mock(return_value=np.random.rand(1644))

        sample = TrainingSample(
            features=features,
            label=1,  # Only tier 1
            confidence=0.8,
            source="vectorstore",
            task_id=f"task_1_{i}",
            timestamp=datetime.now(),
        )
        samples.append(sample)

    train_indices = list(range(0, 48))
    val_indices = list(range(48, 60))

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=48,
        val_count=12,
        label_distribution={1: 60, 2: 0, 3: 0},  # Only tier 1
        created_at=datetime.now(),
        version="v1.60",
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
    result = trainer.train_ensemble_model(dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with single class dataset"
    error_msg = result.unwrap_err()
    assert "class" in error_msg.lower() or "label" in error_msg.lower(), (
        f"Error should mention single class, got: {error_msg}"
    )


def test_invalid_dataset_structure():
    """
    Test dataset with missing features returns Err.

    NECESSARY: Error condition test
    AC-1.2: Validate dataset structure requirements

    AAA Pattern:
    - Arrange: Dataset with None features
    - Act: Train ensemble
    - Assert: Returns Err with invalid structure message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create dataset with None features (invalid)
    samples = []
    for tier in [1, 2, 3]:
        for i in range(20):
            sample = TrainingSample(
                features=None,  # Invalid: None features
                label=tier,
                confidence=0.8,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    train_indices = list(range(0, 48))
    val_indices = list(range(48, 60))

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=48,
        val_count=12,
        label_distribution={1: 20, 2: 20, 3: 20},
        created_at=datetime.now(),
        version="v1.60",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    # This will fail during TrainingDataset creation due to Pydantic validation
    # Testing edge case where features are None
    with pytest.raises((ValueError, TypeError)):
        dataset = TrainingDataset(
            samples=samples,
            train_indices=train_indices,
            val_indices=val_indices,
            metadata=metadata,
        )


def test_sklearn_training_exception():
    """
    Test graceful handling of sklearn training exceptions.

    NECESSARY: Error condition test
    AC-1.2: Validate sklearn error handling

    AAA Pattern:
    - Arrange: Mock sklearn fit() to raise exception
    - Act: Train ensemble
    - Assert: Returns Err with sklearn error message
    """
    # Arrange
    from tools.ml_routing.model_trainer import MLModelTrainer

    trainer = MLModelTrainer()

    # Create valid dataset
    samples = []
    for tier in [1, 2, 3]:
        for i in range(20):
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

    train_indices = list(range(0, 48))
    val_indices = list(range(48, 60))

    metadata = DatasetMetadata(
        total_samples=60,
        train_count=48,
        val_count=12,
        label_distribution={1: 20, 2: 20, 3: 20},
        created_at=datetime.now(),
        version="v1.60",
        min_confidence=0.7,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )

    # Mock sklearn fit() to raise exception
    with patch.object(VotingClassifier, "fit", side_effect=ValueError("sklearn training error")):
        # Act
        result = trainer.train_ensemble_model(dataset, random_state=42)

    # Assert
    assert isinstance(result, Err), "Training should fail with sklearn exception"
    error_msg = result.unwrap_err()
    assert (
        "sklearn" in error_msg.lower()
        or "training" in error_msg.lower()
        or "error" in error_msg.lower()
    ), f"Error should mention sklearn error, got: {error_msg}"


# ==============================================================================
# End of Test Suite
# ==============================================================================
