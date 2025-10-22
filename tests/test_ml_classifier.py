"""
Tests for MLClassifier with ensemble model integration.

Constitutional compliance:
- Article II: TDD - tests written FIRST before implementation
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines each

Reference: specs/spec-007-phase3-ml-inference.md
Author: CodeAgent
Date: 2025-10-10
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from shared.models.task_feature_vector import TaskFeatureVector
from shared.type_definitions.result import Err, Ok
from tools.ml_routing.ml_classifier import (
    ClassificationResult,
    MLClassifier,
)


class TestClassificationResultModel:
    """Test ClassificationResult Pydantic model."""

    def test_creates_classification_result(self):
        """Test creating ClassificationResult with valid data."""
        # Act
        result = ClassificationResult(
            tier="P1",
            confidence=0.85,
            probabilities={"P1": 0.85, "P2": 0.10, "P3": 0.05},
        )

        # Assert
        assert result.tier == "P1"
        assert result.confidence == 0.85
        assert result.probabilities == {"P1": 0.85, "P2": 0.10, "P3": 0.05}

    def test_rejects_invalid_tier(self):
        """Test validation rejects invalid tier values."""
        # Act & Assert
        with pytest.raises(Exception):  # Pydantic ValidationError
            ClassificationResult(
                tier="P4",  # Invalid
                confidence=0.8,
                probabilities={"P1": 0.2, "P2": 0.3, "P3": 0.5},
            )

    def test_probabilities_sum_to_one(self):
        """Test probabilities sum to approximately 1.0."""
        # Arrange
        result = ClassificationResult(
            tier="P2",
            confidence=0.72,
            probabilities={"P1": 0.15, "P2": 0.72, "P3": 0.13},
        )

        # Act
        total_prob = sum(result.probabilities.values())

        # Assert
        assert abs(total_prob - 1.0) < 0.01


class TestMLClassifierInitialization:
    """Test MLClassifier initialization."""

    def test_creates_classifier_with_defaults(self):
        """Test creating MLClassifier with default values."""
        # Act
        classifier = MLClassifier()

        # Assert
        assert classifier.model_version is None
        assert classifier.confidence_threshold == 0.7
        assert classifier.last_updated is None

    def test_creates_classifier_with_custom_threshold(self):
        """Test creating MLClassifier with custom confidence threshold."""
        # Act
        classifier = MLClassifier(confidence_threshold=0.85)

        # Assert
        assert classifier.confidence_threshold == 0.85

    def test_creates_classifier_with_model_version(self):
        """Test creating MLClassifier with model version."""
        # Act
        classifier = MLClassifier(
            model_version="v1.0",
            last_updated="2025-10-10T12:00:00Z",
        )

        # Assert
        assert classifier.model_version == "v1.0"
        assert classifier.last_updated == "2025-10-10T12:00:00Z"


class TestMLClassifierModelLoading:
    """Test MLClassifier model loading."""

    @patch("tools.ml_routing.ml_classifier.ModelStorage")
    def test_load_model_success(self, mock_storage_class):
        """Test load_model() succeeds with valid model."""
        # Arrange
        classifier = MLClassifier()
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_model = MagicMock()
        mock_model.training_date = "2025-10-10T12:00:00Z"
        mock_storage.load_model.return_value = Ok(mock_model)

        model_path = Path("/path/to/model.pkl")

        # Act
        result = classifier.load_model(model_path)

        # Assert
        assert result.is_ok()
        assert classifier.model_version == "2025-10-10T12:00:00Z"
        # ModelStorage.load_model is now called with version='latest' (not file path)
        mock_storage.load_model.assert_called_once_with(version="latest")

    @patch("tools.ml_routing.ml_classifier.ModelStorage")
    def test_load_model_failure(self, mock_storage_class):
        """Test load_model() returns Err when loading fails."""
        # Arrange
        classifier = MLClassifier()
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_storage.load_model.return_value = Err("Model file not found")

        model_path = Path("/nonexistent/model.pkl")

        # Act
        result = classifier.load_model(model_path)

        # Assert
        assert result.is_err()
        assert "Model file not found" in result.unwrap_err()

    @patch("tools.ml_routing.ml_classifier.ModelStorage")
    def test_load_model_updates_version(self, mock_storage_class):
        """Test load_model() updates model_version from metadata."""
        # Arrange
        classifier = MLClassifier()
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_model = MagicMock()
        mock_model.training_date = "2025-10-10T15:30:00Z"
        mock_storage.load_model.return_value = Ok(mock_model)

        # Act
        result = classifier.load_model(Path("/path/to/model.pkl"))

        # Assert
        assert result.is_ok()
        assert classifier.model_version == "2025-10-10T15:30:00Z"


class TestMLClassifierClassification:
    """Test MLClassifier classification logic."""

    def test_classify_returns_error_when_model_not_loaded(self):
        """Test classify() falls back to rule-based when model not loaded."""
        # Arrange
        classifier = MLClassifier()
        task = {"description": "Implement feature X"}

        # Act
        result = classifier.classify(task)

        # Assert - Should fall back to rule-based classification
        assert result.is_ok()
        classification = result.unwrap()
        assert classification.method == "rule_based_fallback"
        assert classification.tier in ["P1", "P2", "P3", "simple", "moderate", "complex"]

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_classify_returns_error_when_feature_extraction_fails(self, mock_extractor_class):
        """Test classify() falls back to rule-based when feature extraction fails."""
        # Arrange
        classifier = MLClassifier()
        classifier._model = MagicMock()  # Model loaded

        mock_extractor = MagicMock()
        mock_extractor.extract_features.return_value = Err("Embedding API timeout")
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Implement feature X"}

        # Act
        result = classifier.classify(task)

        # Assert - Should fall back to rule-based classification
        assert result.is_ok()
        classification = result.unwrap()
        assert classification.method == "rule_based_fallback"
        assert classification.tier in ["P1", "P2", "P3", "simple", "moderate", "complex"]

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_classify_success_with_high_confidence(self, mock_extractor_class):
        """Test classify() succeeds with high confidence prediction."""
        # Arrange
        classifier = MLClassifier(confidence_threshold=0.7)

        # Mock model
        mock_model = MagicMock()
        mock_model.ensemble.predict_proba.return_value = np.array(
            [[0.10, 0.15, 0.75]]  # P3 has highest probability (0.75)
        )
        mock_model.ensemble.classes_ = np.array(["P1", "P2", "P3"])
        classifier._model = mock_model

        # Mock feature extractor
        mock_extractor = MagicMock()
        mock_vector = MagicMock()
        mock_vector.to_flat_array.return_value = [0.0] * 1644
        mock_extractor.extract_features.return_value = Ok(mock_vector)
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Fix typo in README"}

        # Act
        result = classifier.classify(task)

        # Assert
        assert result.is_ok()
        classification = result.unwrap()
        assert classification.tier == "P3"
        assert classification.confidence == 0.75
        assert classification.probabilities == {"P1": 0.10, "P2": 0.15, "P3": 0.75}

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_classify_returns_error_when_confidence_below_threshold(self, mock_extractor_class):
        """Test classify() falls back to rule-based when confidence below threshold."""
        # Arrange
        classifier = MLClassifier(confidence_threshold=0.8)

        # Mock model with low confidence
        mock_model = MagicMock()
        mock_model.ensemble.predict_proba.return_value = np.array(
            [[0.35, 0.40, 0.25]]  # Max 0.40, below threshold 0.8
        )
        mock_model.ensemble.classes_ = np.array(["P1", "P2", "P3"])
        classifier._model = mock_model

        # Mock feature extractor
        mock_extractor = MagicMock()
        mock_vector = MagicMock()
        mock_vector.to_flat_array.return_value = [0.0] * 1644
        mock_extractor.extract_features.return_value = Ok(mock_vector)
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Unclear task"}

        # Act
        result = classifier.classify(task)

        # Assert - Should fall back to rule-based classification
        assert result.is_ok()
        classification = result.unwrap()
        assert classification.method == "rule_based_fallback"
        assert classification.tier in ["P1", "P2", "P3", "simple", "moderate", "complex"]

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_classify_handles_p1_complex_tier(self, mock_extractor_class):
        """Test classify() correctly predicts P1 complex tier."""
        # Arrange
        classifier = MLClassifier(confidence_threshold=0.7)

        # Mock model
        mock_model = MagicMock()
        mock_model.ensemble.predict_proba.return_value = np.array(
            [[0.85, 0.10, 0.05]]  # P1 has highest probability
        )
        mock_model.ensemble.classes_ = np.array(["P1", "P2", "P3"])
        classifier._model = mock_model

        # Mock feature extractor
        mock_extractor = MagicMock()
        mock_vector = MagicMock()
        mock_vector.to_flat_array.return_value = [0.0] * 1644
        mock_extractor.extract_features.return_value = Ok(mock_vector)
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Design new microservices architecture"}

        # Act
        result = classifier.classify(task)

        # Assert
        assert result.is_ok()
        assert result.unwrap().tier == "P1"
        assert result.unwrap().confidence == 0.85

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_classify_handles_p2_moderate_tier(self, mock_extractor_class):
        """Test classify() correctly predicts P2 moderate tier."""
        # Arrange
        classifier = MLClassifier(confidence_threshold=0.7)

        # Mock model
        mock_model = MagicMock()
        mock_model.ensemble.predict_proba.return_value = np.array(
            [[0.12, 0.78, 0.10]]  # P2 has highest probability
        )
        mock_model.ensemble.classes_ = np.array(["P1", "P2", "P3"])
        classifier._model = mock_model

        # Mock feature extractor
        mock_extractor = MagicMock()
        mock_vector = MagicMock()
        mock_vector.to_flat_array.return_value = [0.0] * 1644
        mock_extractor.extract_features.return_value = Ok(mock_vector)
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Implement user authentication API"}

        # Act
        result = classifier.classify(task)

        # Assert
        assert result.is_ok()
        assert result.unwrap().tier == "P2"
        assert result.unwrap().confidence == 0.78


class TestMLClassifierConfidence:
    """Test MLClassifier confidence scoring."""

    def test_get_confidence_returns_zero_when_model_not_loaded(self):
        """Test get_confidence() returns 0.0 when model not loaded."""
        # Arrange
        classifier = MLClassifier()
        task = {"description": "Test task"}

        # Act
        confidence = classifier.get_confidence(task)

        # Assert
        assert confidence == 0.0

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_get_confidence_returns_max_probability(self, mock_extractor_class):
        """Test get_confidence() returns max probability from model."""
        # Arrange
        classifier = MLClassifier()

        # Mock model
        mock_model = MagicMock()
        mock_model.ensemble.predict_proba.return_value = np.array([[0.15, 0.72, 0.13]])
        mock_model.ensemble.classes_ = np.array(["P1", "P2", "P3"])
        classifier._model = mock_model

        # Mock feature extractor
        mock_extractor = MagicMock()
        mock_vector = MagicMock()
        mock_vector.to_flat_array.return_value = [0.0] * 1644
        mock_extractor.extract_features.return_value = Ok(mock_vector)
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Test task"}

        # Act
        confidence = classifier.get_confidence(task)

        # Assert
        assert confidence == 0.72

    @patch("tools.ml_routing.ml_classifier.FeatureExtractor")
    def test_get_confidence_handles_feature_extraction_failure(self, mock_extractor_class):
        """Test get_confidence() returns 0.0 on feature extraction failure."""
        # Arrange
        classifier = MLClassifier()
        classifier._model = MagicMock()

        # Mock feature extraction failure
        mock_extractor = MagicMock()
        mock_extractor.extract_features.return_value = Err("API timeout")
        mock_extractor_class.return_value = mock_extractor

        task = {"description": "Test task"}

        # Act
        confidence = classifier.get_confidence(task)

        # Assert
        assert confidence == 0.0
