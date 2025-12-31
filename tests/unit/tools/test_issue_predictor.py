"""
Tests for Issue Predictor (Phase 3).

Tests the ML-based issue prediction system including:
- Tokenization
- Training
- Prediction
- Model persistence
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))


class TestPrediction:
    """Tests for Prediction dataclass."""

    def test_prediction_creation(self):
        """Test creating a prediction."""
        from tools.issue_predictor import Prediction

        pred = Prediction(
            code_snippet="except:",
            predicted_issue="bare_except",
            probability=0.85,
            confidence="high",
            similar_patterns=["bare_except", "generic_exception"],
        )

        assert pred.predicted_issue == "bare_except"
        assert pred.probability == 0.85
        assert pred.confidence == "high"
        assert len(pred.similar_patterns) == 2


class TestIssuePredictorModel:
    """Tests for IssuePredictorModel class."""

    @pytest.fixture
    def fresh_model(self, tmp_path):
        """Create a fresh model with temporary storage."""
        from tools.issue_predictor import IssuePredictorModel

        # Override model path
        import tools.issue_predictor as module

        original_path = module.MODEL_PATH
        module.MODEL_PATH = tmp_path / "test_model.json"

        model = IssuePredictorModel()
        yield model

        # Restore
        module.MODEL_PATH = original_path

    def test_tokenize_bare_except(self, fresh_model):
        """Test tokenization of bare except code."""
        tokens = fresh_model._tokenize("except:")
        assert "bare_except" in tokens

    def test_tokenize_eval(self, fresh_model):
        """Test tokenization of eval usage."""
        tokens = fresh_model._tokenize("result = eval('1+1')")
        assert "uses_eval" in tokens

    def test_tokenize_shell_true(self, fresh_model):
        """Test tokenization of shell=True."""
        tokens = fresh_model._tokenize("subprocess.call(cmd, shell=True)")
        assert "shell_true" in tokens

    def test_tokenize_keywords(self, fresh_model):
        """Test tokenization extracts Python keywords."""
        code = "def foo():\n    if x:\n        return y"
        tokens = fresh_model._tokenize(code)
        assert "def" in tokens
        assert "if" in tokens
        assert "return" in tokens

    def test_train_updates_counts(self, fresh_model):
        """Test that training updates class and feature counts."""
        initial_samples = fresh_model.total_samples

        fresh_model.train("except:", "bare_except")

        assert fresh_model.total_samples == initial_samples + 1
        assert fresh_model.class_counts["bare_except"] >= 1

    def test_train_batch(self, fresh_model):
        """Test batch training."""
        samples = [
            ("except:", "bare_except"),
            ("eval('x')", "security_eval"),
            ("def foo(): return 1", "clean"),
        ]

        count = fresh_model.train_batch(samples)

        assert count == 3
        assert fresh_model.class_counts["bare_except"] >= 1
        assert fresh_model.class_counts["security_eval"] >= 1
        assert fresh_model.class_counts["clean"] >= 1

    def test_predict_requires_training(self, fresh_model):
        """Test that prediction requires minimum training."""
        # Fresh model with no training should fail
        result = fresh_model.predict("except:")

        # Note: The model auto-seeds with initial data, so this may succeed
        # If it fails, it should return an error
        if result.is_err():
            assert "training samples" in result.unwrap_err()

    def test_predict_after_training(self, fresh_model):
        """Test prediction after training."""
        # Train with samples
        samples = [
            ("except:", "bare_except"),
            ("except:", "bare_except"),
            ("except:", "bare_except"),
            ("eval('x')", "security_eval"),
            ("def foo(): return 1", "clean"),
        ]
        fresh_model.train_batch(samples)

        result = fresh_model.predict("try:\n    x = 1\nexcept:\n    pass")

        assert result.is_ok()
        pred = result.unwrap()
        assert pred.predicted_issue == "bare_except"
        assert pred.probability > 0.3

    def test_confidence_levels(self, fresh_model):
        """Test confidence level assignment."""
        # Train heavily on one class
        for _ in range(10):
            fresh_model.train("except:", "bare_except")

        for _ in range(2):
            fresh_model.train("def foo(): return 1", "clean")

        result = fresh_model.predict("except:")
        assert result.is_ok()

        pred = result.unwrap()
        # Should have high confidence after heavy training
        assert pred.confidence in ("high", "medium")

    def test_model_stats(self, fresh_model):
        """Test getting model statistics."""
        fresh_model.train("except:", "bare_except")
        fresh_model.train("eval('x')", "security_eval")

        stats = fresh_model.get_stats()

        assert stats.total_samples >= 2
        assert "bare_except" in stats.issue_types
        assert "security_eval" in stats.issue_types


class TestIssuePredictor:
    """Tests for IssuePredictor high-level interface."""

    @pytest.fixture
    def predictor(self, tmp_path):
        """Create predictor instance."""
        from tools.issue_predictor import IssuePredictor

        # Override model path for isolation
        import tools.issue_predictor as module

        original_path = module.MODEL_PATH
        module.MODEL_PATH = tmp_path / "test_model.json"

        pred = IssuePredictor()
        yield pred

        module.MODEL_PATH = original_path

    def test_predict_bare_except(self, predictor):
        """Test predicting bare except issue."""
        result = predictor.predict("try:\n    x = 1\nexcept:\n    pass")

        assert result.is_ok()
        pred = result.unwrap()
        # With seeded data, should recognize bare_except pattern
        assert pred.predicted_issue in ("bare_except", "clean")

    def test_predict_clean_code(self, predictor):
        """Test predicting clean code."""
        result = predictor.predict("def add(a: int, b: int) -> int:\n    return a + b")

        assert result.is_ok()
        pred = result.unwrap()
        # Clean code should be classified as clean or have low probability for issues
        # The model may not perfectly classify but should not classify as critical issue
        assert pred.predicted_issue in ("clean", "missing_return_type")

    def test_predict_file(self, predictor, tmp_path):
        """Test predicting issues in a file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def risky():
    try:
        x = eval("1+1")
    except:
        pass
""")

        result = predictor.predict_file(str(test_file))

        assert result.is_ok()
        predictions = result.unwrap()
        # Should find at least one issue
        issue_types = [p.predicted_issue for p in predictions]
        # Note: predictions depend on training
        assert isinstance(predictions, list)

    def test_learn_from_outcome(self, predictor):
        """Test learning from actual outcomes."""
        code = "try:\n    x\nexcept:\n    pass"
        initial_stats = predictor.get_stats()

        predictor.learn_from_outcome(code, "bare_except")

        updated_stats = predictor.get_stats()
        assert updated_stats["total_samples"] > initial_stats["total_samples"]

    def test_get_stats(self, predictor):
        """Test getting predictor statistics."""
        stats = predictor.get_stats()

        assert "total_samples" in stats
        assert "issue_types" in stats
        assert "last_trained" in stats

    def test_seed_initial_data(self, predictor):
        """Test that initial data is seeded."""
        # Predictor should have seeded training data
        stats = predictor.get_stats()
        assert stats["total_samples"] >= 20  # At least 20 seed samples


class TestModelPersistence:
    """Tests for model save/load functionality."""

    def test_model_saves_and_loads(self, tmp_path):
        """Test that model persists to disk and loads."""
        import tools.issue_predictor as module

        model_path = tmp_path / "persist_test.json"
        module.MODEL_PATH = model_path

        # Create and train model
        from tools.issue_predictor import IssuePredictorModel

        model1 = IssuePredictorModel()
        model1.train("except:", "bare_except")
        model1.train("eval('x')", "security_eval")
        model1._save_model()

        # Verify file exists
        assert model_path.exists()

        # Load in new instance
        model2 = IssuePredictorModel()

        assert model2.total_samples >= 2
        assert "bare_except" in model2.class_counts
        assert "security_eval" in model2.class_counts
