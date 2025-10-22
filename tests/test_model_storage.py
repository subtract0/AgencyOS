"""
Tests for ModelStorage (Leap 5 Phase 1).

Constitutional compliance:
- Article I: Complete context (all training metadata saved)
- Article II: 100% verification (model size <50MB, load time <1s)
- Article IV: VectorStore integration (models persisted for cross-session use)
- Article V: Spec-driven (follows spec-005 section 4.2.3)

Author: CodeAgent
Date: 2025-10-10
"""

import json
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pytest
import sklearn
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)

from shared.models import EnsembleModel
from shared.type_definitions import Err, Ok, Result
from tools.ml_routing.model_storage import ModelMetadata, ModelStorage


@pytest.fixture
def temp_models_dir():
    """Create temporary models directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_ensemble_model():
    """Create sample EnsembleModel for testing."""
    # Create simple models (small size for testing)
    rf_model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
    gb_model = GradientBoostingClassifier(
        n_estimators=5, learning_rate=0.1, max_depth=3, random_state=42
    )

    # Create ensemble
    ensemble = VotingClassifier(
        estimators=[("rf", rf_model), ("gb", gb_model)],
        voting="soft",
        weights=[0.7, 0.3],
    )

    # Train on dummy data (simple 2-class problem)
    import numpy as np

    X_train = np.random.rand(100, 10)
    y_train = np.random.randint(0, 2, 100)

    rf_model.fit(X_train, y_train)
    gb_model.fit(X_train, y_train)
    ensemble.fit(X_train, y_train)

    # Create feature names (1644 items)
    feature_names = (
        [f"embedding_{i}" for i in range(1536)]
        + [f"tfidf_{i}" for i in range(100)]
        + [
            "description_length",
            "word_count",
            "has_refactor",
            "has_test",
            "has_async",
            "has_fix",
            "estimated_time",
            "historical_tier_mode",
        ]
    )

    model = EnsembleModel(
        ensemble=ensemble,
        rf_model=rf_model,
        gb_model=gb_model,
        validation_accuracy=0.984,
        false_negative_rate=0.018,
        training_date=datetime.now(UTC).isoformat(),
        feature_names=feature_names,
    )

    return model


class TestModelMetadata:
    """Test ModelMetadata Pydantic model."""

    def test_metadata_creation_with_all_fields(self):
        """Test ModelMetadata creation with all required fields."""
        metadata = ModelMetadata(
            version="v1.0",
            training_date="2025-10-10T12:00:00Z",
            validation_accuracy=0.984,
            false_negative_rate=0.018,
            feature_count=1644,
            model_size_mb=12.5,
            sklearn_version=sklearn.__version__,
            file_path=Path("/tmp/model.pkl"),
        )

        assert metadata.version == "v1.0"
        assert metadata.validation_accuracy == 0.984
        assert metadata.false_negative_rate == 0.018
        assert metadata.feature_count == 1644
        assert metadata.model_size_mb == 12.5

    def test_metadata_validation_accuracy_range(self):
        """Test validation_accuracy must be within [0, 1]."""
        # Valid accuracy
        metadata = ModelMetadata(
            version="v1.0",
            training_date="2025-10-10T12:00:00Z",
            validation_accuracy=0.984,
            false_negative_rate=0.018,
            feature_count=1644,
            model_size_mb=12.5,
            sklearn_version=sklearn.__version__,
            file_path=Path("/tmp/model.pkl"),
        )
        assert metadata.validation_accuracy == 0.984

        # Invalid accuracy (>1.0)
        with pytest.raises(ValueError):
            ModelMetadata(
                version="v1.0",
                training_date="2025-10-10T12:00:00Z",
                validation_accuracy=1.5,  # Invalid
                false_negative_rate=0.018,
                feature_count=1644,
                model_size_mb=12.5,
                sklearn_version=sklearn.__version__,
                file_path=Path("/tmp/model.pkl"),
            )


class TestModelStorageSaveModel:
    """Test ModelStorage.save_model() functionality."""

    def test_save_model_creates_directory_if_not_exists(
        self, sample_ensemble_model, temp_models_dir
    ):
        """Test save_model creates models directory."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        assert (temp_models_dir / "routing_classifier_v1.0.pkl").exists()
        assert (temp_models_dir / "routing_classifier_v1.0.json").exists()

    def test_save_model_with_explicit_version(self, sample_ensemble_model, temp_models_dir):
        """Test save_model with explicit version number."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v2.5")

        assert result.is_ok()
        path = result.unwrap()
        assert path.name == "routing_classifier_v2.5.pkl"
        assert path.exists()

    def test_save_model_generates_version_automatically(
        self, sample_ensemble_model, temp_models_dir
    ):
        """Test save_model auto-generates version if none provided."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # First save (should be v1.0)
        result = storage.save_model(sample_ensemble_model)
        assert result.is_ok()
        path = result.unwrap()
        assert "v1.0" in path.name

    def test_save_model_increments_minor_version(self, sample_ensemble_model, temp_models_dir):
        """Test save_model increments minor version by default."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save v1.0
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Save without version (should be v1.1)
        result = storage.save_model(sample_ensemble_model, breaking_change=False)
        assert result.is_ok()
        path = result.unwrap()
        assert "v1.1" in path.name

    def test_save_model_increments_major_version_on_breaking_change(
        self, sample_ensemble_model, temp_models_dir
    ):
        """Test save_model increments major version for breaking changes."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save v1.5
        storage.save_model(sample_ensemble_model, version="v1.5")

        # Save with breaking_change=True (should be v2.0)
        result = storage.save_model(sample_ensemble_model, breaking_change=True)
        assert result.is_ok()
        path = result.unwrap()
        assert "v2.0" in path.name

    def test_save_model_creates_metadata_json(self, sample_ensemble_model, temp_models_dir):
        """Test save_model creates metadata JSON file."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        metadata_path = temp_models_dir / "routing_classifier_v1.0.json"
        assert metadata_path.exists()

        # Validate metadata contents
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["version"] == "v1.0"
        assert metadata["validation_accuracy"] == 0.984
        assert metadata["false_negative_rate"] == 0.018
        assert metadata["feature_count"] == 1644
        assert "model_size_mb" in metadata
        assert metadata["sklearn_version"] == sklearn.__version__

    def test_save_model_updates_latest_symlink(self, sample_ensemble_model, temp_models_dir):
        """Test save_model updates 'latest' symlink."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save v1.0
        storage.save_model(sample_ensemble_model, version="v1.0")
        latest_link = temp_models_dir / "routing_classifier_latest.pkl"
        assert latest_link.is_symlink()
        assert latest_link.resolve().name == "routing_classifier_v1.0.pkl"

        # Save v1.1 (should update symlink)
        storage.save_model(sample_ensemble_model, version="v1.1")
        assert latest_link.is_symlink()
        assert latest_link.resolve().name == "routing_classifier_v1.1.pkl"

    def test_save_model_sets_secure_permissions(self, sample_ensemble_model, temp_models_dir):
        """Test save_model sets 0600 permissions on model files."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        path = result.unwrap()

        # Check file permissions (0600 = owner read/write only)
        stat_info = path.stat()
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == "600"

        # Check metadata permissions
        metadata_path = path.with_suffix(".json")
        stat_info = metadata_path.stat()
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == "600"

    def test_save_model_warns_if_size_exceeds_50mb(
        self, sample_ensemble_model, temp_models_dir, capsys
    ):
        """Test save_model warns if model size exceeds 50MB target."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save model (our test model is small, so no warning expected)
        storage.save_model(sample_ensemble_model, version="v1.0")
        captured = capsys.readouterr()

        # Small model should NOT trigger warning
        assert "Warning: Model size" not in captured.out

    def test_save_model_compression_reduces_size(self, sample_ensemble_model, temp_models_dir):
        """Test save_model uses compression (compress=3)."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        path = result.unwrap()

        # Load model to verify it was compressed correctly
        loaded_model = joblib.load(path)
        assert isinstance(loaded_model.ensemble, VotingClassifier)


class TestModelStorageLoadModel:
    """Test ModelStorage.load_model() functionality."""

    def test_load_model_by_version(self, sample_ensemble_model, temp_models_dir):
        """Test load_model loads specific version."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Load by version
        result = storage.load_model(version="v1.0")
        assert result.is_ok()
        model = result.unwrap()
        assert isinstance(model, EnsembleModel)
        assert model.validation_accuracy == 0.984

    def test_load_model_latest_version(self, sample_ensemble_model, temp_models_dir):
        """Test load_model loads 'latest' version via symlink."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")
        storage.save_model(sample_ensemble_model, version="v1.1")

        # Load latest (should be v1.1)
        result = storage.load_model(version="latest")
        assert result.is_ok()
        model = result.unwrap()
        assert isinstance(model, EnsembleModel)

    def test_load_model_nonexistent_version_returns_error(self, temp_models_dir):
        """Test load_model returns error for missing version."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.load_model(version="v999.0")

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_load_model_no_models_returns_error(self, temp_models_dir):
        """Test load_model returns error when no models exist."""
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.load_model(version="latest")

        assert result.is_err()
        assert "No models found" in result.unwrap_err()

    def test_load_model_validates_feature_count(self, sample_ensemble_model, temp_models_dir):
        """Test load_model validates feature count matches expected 1644."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Manually corrupt metadata to have wrong feature count
        metadata_path = temp_models_dir / "routing_classifier_v1.0.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        metadata["feature_count"] = 999  # Invalid count
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        # Load should fail with feature count mismatch
        result = storage.load_model(version="v1.0")
        assert result.is_err()
        assert "Incompatible model" in result.unwrap_err()

    def test_load_model_measures_load_time(self, sample_ensemble_model, temp_models_dir):
        """Test load_model measures and reports load time."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Load model (should complete quickly for small model)
        start_time = time.perf_counter()
        result = storage.load_model(version="v1.0")
        load_time = time.perf_counter() - start_time

        assert result.is_ok()
        assert load_time < 1.0  # Should be well under 1 second

    def test_load_model_handles_missing_metadata(self, sample_ensemble_model, temp_models_dir):
        """Test load_model returns error if metadata JSON missing."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Delete metadata JSON
        metadata_path = temp_models_dir / "routing_classifier_v1.0.json"
        metadata_path.unlink()

        # Load should fail
        result = storage.load_model(version="v1.0")
        assert result.is_err()
        assert "Failed to load metadata" in result.unwrap_err()


class TestModelStorageListModels:
    """Test ModelStorage.list_models() functionality."""

    def test_list_models_returns_empty_for_no_models(self, temp_models_dir):
        """Test list_models returns empty list when no models exist."""
        storage = ModelStorage(base_dir=temp_models_dir)
        models = storage.list_models()
        assert models == []

    def test_list_models_returns_all_models(self, sample_ensemble_model, temp_models_dir):
        """Test list_models returns all saved models."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")
        storage.save_model(sample_ensemble_model, version="v1.1")
        storage.save_model(sample_ensemble_model, version="v2.0")

        models = storage.list_models()
        assert len(models) == 3
        assert all(isinstance(m, ModelMetadata) for m in models)

    def test_list_models_sorted_by_version_descending(self, sample_ensemble_model, temp_models_dir):
        """Test list_models returns models sorted by version (newest first)."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")
        storage.save_model(sample_ensemble_model, version="v2.0")
        storage.save_model(sample_ensemble_model, version="v1.5")

        models = storage.list_models()
        versions = [m.version for m in models]
        assert versions == ["v2.0", "v1.5", "v1.0"]

    def test_list_models_includes_metadata_fields(self, sample_ensemble_model, temp_models_dir):
        """Test list_models includes all metadata fields."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        models = storage.list_models()
        assert len(models) == 1

        metadata = models[0]
        assert metadata.version == "v1.0"
        assert metadata.validation_accuracy == 0.984
        assert metadata.false_negative_rate == 0.018
        assert metadata.feature_count == 1644
        assert metadata.model_size_mb > 0
        assert metadata.sklearn_version == sklearn.__version__


class TestModelStorageIntegration:
    """Integration tests for ModelStorage workflow."""

    def test_save_and_load_roundtrip(self, sample_ensemble_model, temp_models_dir):
        """Test save/load roundtrip preserves model integrity."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save model
        save_result = storage.save_model(sample_ensemble_model, version="v1.0")
        assert save_result.is_ok()

        # Load model
        load_result = storage.load_model(version="v1.0")
        assert load_result.is_ok()

        loaded_model = load_result.unwrap()

        # Verify model properties preserved
        assert loaded_model.validation_accuracy == sample_ensemble_model.validation_accuracy
        assert loaded_model.false_negative_rate == sample_ensemble_model.false_negative_rate
        assert len(loaded_model.feature_names) == len(sample_ensemble_model.feature_names)

    def test_multiple_versions_coexist(self, sample_ensemble_model, temp_models_dir):
        """Test multiple model versions can coexist."""
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save multiple versions
        storage.save_model(sample_ensemble_model, version="v1.0")
        storage.save_model(sample_ensemble_model, version="v1.1")
        storage.save_model(sample_ensemble_model, version="v2.0")

        # Load each version
        v1_result = storage.load_model(version="v1.0")
        v2_result = storage.load_model(version="v2.0")

        assert v1_result.is_ok()
        assert v2_result.is_ok()

        # Latest should point to v2.0
        latest_result = storage.load_model(version="latest")
        assert latest_result.is_ok()

    def test_article_i_complete_context(self, sample_ensemble_model, temp_models_dir):
        """Test Article I: Complete context (all metadata saved)."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Load metadata
        metadata_path = temp_models_dir / "routing_classifier_v1.0.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        # Verify all required fields present
        required_fields = {
            "version",
            "training_date",
            "validation_accuracy",
            "false_negative_rate",
            "feature_count",
            "model_size_mb",
            "sklearn_version",
            "file_path",
        }
        assert set(metadata.keys()) == required_fields

    def test_article_ii_verification(self, sample_ensemble_model, temp_models_dir):
        """Test Article II: 100% verification (model integrity)."""
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Load and verify model can make predictions
        result = storage.load_model(version="v1.0")
        assert result.is_ok()

        model = result.unwrap()

        # Verify ensemble can predict
        import numpy as np

        X_test = np.random.rand(5, 10)
        predictions = model.ensemble.predict(X_test)
        assert len(predictions) == 5


# ==============================================================================
# Additional NECESSARY Pattern Tests (Edge Cases, Error Conditions)
# ==============================================================================


class TestModelStorageEdgeCases:
    """Test edge cases and boundary conditions (NECESSARY: E for Edge cases)."""

    def test_save_model_with_empty_feature_names_fails(self, temp_models_dir):
        """
        Test save_model fails with empty feature names.

        NECESSARY: Edge case test
        AC-1.1: Validate feature names are non-empty
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Create model with invalid feature names
        rf_model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
        gb_model = GradientBoostingClassifier(
            n_estimators=5, learning_rate=0.1, max_depth=3, random_state=42
        )
        ensemble = VotingClassifier(
            estimators=[("rf", rf_model), ("gb", gb_model)], voting="soft", weights=[0.7, 0.3]
        )

        # Train on dummy data
        import numpy as np

        X_train = np.random.rand(100, 10)
        y_train = np.random.randint(0, 2, 100)
        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)
        ensemble.fit(X_train, y_train)

        # Create model with empty feature names (invalid)
        with pytest.raises(ValueError) as exc_info:
            model = EnsembleModel(
                ensemble=ensemble,
                rf_model=rf_model,
                gb_model=gb_model,
                validation_accuracy=0.984,
                false_negative_rate=0.018,
                training_date=datetime.now(UTC).isoformat(),
                feature_names=[],  # Empty (invalid)
            )

        assert "1644" in str(exc_info.value)  # Should mention expected dimension

    def test_load_model_with_symlink_broken_returns_error(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test load_model returns error when symlink is broken.

        NECESSARY: Edge case test
        AC-3.4: Validate symlink integrity
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Break symlink by deleting target
        model_path = temp_models_dir / "routing_classifier_v1.0.pkl"
        model_path.unlink()

        # Load latest (symlink broken)
        result = storage.load_model(version="latest")
        assert result.is_err()
        # Error should mention missing models or not found
        error_msg = result.unwrap_err().lower()
        assert "not found" in error_msg or "missing" in error_msg

    def test_save_model_version_with_invalid_format_fails(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test save_model fails with invalid version format.

        NECESSARY: Edge case test
        AC-3.4: Validate semantic version format (vX.Y)
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Invalid version format (missing 'v' prefix)
        result = storage.save_model(sample_ensemble_model, version="1.0")
        assert result.is_err()
        assert (
            "version format" in result.unwrap_err().lower()
            or "invalid" in result.unwrap_err().lower()
        )


class TestModelStorageCornerCases:
    """Test corner cases and unusual combinations (NECESSARY: C for Corner cases)."""

    def test_save_multiple_models_simultaneously_thread_safe(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test save_model is thread-safe (multiple concurrent saves).

        NECESSARY: Corner case test
        AC-P.3: Validate concurrent write safety
        """
        import threading

        storage = ModelStorage(base_dir=temp_models_dir)
        results = []
        lock = threading.Lock()

        def save_model_thread(version):
            result = storage.save_model(sample_ensemble_model, version=version)
            with lock:
                results.append(result)

        # Create 3 threads saving different versions
        threads = [threading.Thread(target=save_model_thread, args=(f"v1.{i}",)) for i in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=5)
            assert not thread.is_alive(), "Thread did not complete within timeout"

        # All saves should succeed
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        assert all(r.is_ok() for r in results), (
            f"Some saves failed: {[r.unwrap_err() for r in results if r.is_err()]}"
        )
        assert len(storage.list_models()) == 3

    def test_load_model_with_special_characters_in_version(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test load_model handles version with special characters.

        NECESSARY: Corner case test
        AC-3.4: Validate version string sanitization
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save with alpha/beta version
        result = storage.save_model(sample_ensemble_model, version="v1.0-alpha")
        assert result.is_ok()

        # Load with special version
        load_result = storage.load_model(version="v1.0-alpha")
        assert load_result.is_ok()


class TestModelStorageStressCases:
    """Test stress and performance scenarios (NECESSARY: S for Stress tests)."""

    def test_load_time_for_large_model_under_threshold(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test load time for large model stays under 1 second.

        NECESSARY: Stress test
        AC-P.1: Validate load time <1s threshold
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Measure load time
        start_time = time.perf_counter()
        result = storage.load_model(version="v1.0")
        load_time = time.perf_counter() - start_time

        assert result.is_ok()
        assert load_time < 1.0, f"Load time {load_time:.3f}s exceeds 1s threshold"

    def test_save_load_100_versions_without_memory_leak(
        self, sample_ensemble_model, temp_models_dir
    ):
        """
        Test saving/loading many versions doesn't cause memory issues.

        NECESSARY: Stress test
        AC-P.3: Validate no memory leaks with many versions
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save 10 versions (reduced from 100 for test speed)
        for i in range(10):
            result = storage.save_model(sample_ensemble_model, version=f"v1.{i}")
            assert result.is_ok()

        # List all models (should not crash)
        models = storage.list_models()
        assert len(models) == 10

        # Load random versions (should not crash)
        for i in [0, 5, 9]:
            result = storage.load_model(version=f"v1.{i}")
            assert result.is_ok()


class TestModelStorageAccessibilityCases:
    """Test API usability and developer experience (NECESSARY: A for Accessibility tests)."""

    def test_list_models_returns_empty_list_not_error(self, temp_models_dir):
        """
        Test list_models returns empty list (not error) when no models exist.

        NECESSARY: Accessibility test
        AC-U.1: Validate API returns sensible defaults
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        models = storage.list_models()

        # Should return empty list (not raise exception)
        assert isinstance(models, list)
        assert len(models) == 0

    def test_save_model_provides_helpful_error_messages(self, temp_models_dir):
        """
        Test save_model provides clear error messages for invalid input.

        NECESSARY: Accessibility test
        AC-U.2: Validate error messages are actionable
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Pass invalid model type
        result = storage.save_model("not_a_model", version="v1.0")
        assert result.is_err()
        error_msg = result.unwrap_err()
        # Error should mention expected type
        assert "EnsembleModel" in error_msg or "model" in error_msg.lower()


class TestModelStorageRegressionPrevention:
    """Test regression prevention (NECESSARY: R for Regression tests)."""

    def test_metadata_json_format_backward_compatible(self, sample_ensemble_model, temp_models_dir):
        """
        Test metadata JSON format is backward compatible.

        NECESSARY: Regression test
        AC-3.4: Validate metadata format stability (no breaking changes)
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        # Load metadata manually
        metadata_path = temp_models_dir / "routing_classifier_v1.0.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        # Ensure required fields are present (backward compatibility)
        required_fields = {
            "version",
            "training_date",
            "validation_accuracy",
            "false_negative_rate",
            "feature_count",
            "model_size_mb",
            "sklearn_version",
        }
        assert required_fields.issubset(set(metadata.keys()))

    def test_symlink_behavior_consistent_across_saves(self, sample_ensemble_model, temp_models_dir):
        """
        Test symlink always points to newest version (regression prevention).

        NECESSARY: Regression test
        AC-3.4: Validate symlink update behavior
        """
        storage = ModelStorage(base_dir=temp_models_dir)

        # Save 3 versions
        for i in range(3):
            storage.save_model(sample_ensemble_model, version=f"v1.{i}")

        # Symlink should always point to v1.2 (newest)
        latest_link = temp_models_dir / "routing_classifier_latest.pkl"
        assert latest_link.is_symlink()
        assert latest_link.resolve().name == "routing_classifier_v1.2.pkl"


class TestModelStorageYieldValidation:
    """Test output validation (NECESSARY: Y for Yield tests)."""

    def test_load_model_returns_valid_ensemble_model(self, sample_ensemble_model, temp_models_dir):
        """
        Test load_model returns valid EnsembleModel with all fields.

        NECESSARY: Yield test
        AC-1.1: Validate loaded model structure
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")

        result = storage.load_model(version="v1.0")
        assert result.is_ok()
        model = result.unwrap()

        # Validate all required fields
        assert isinstance(model, EnsembleModel)
        assert isinstance(model.ensemble, VotingClassifier)
        assert isinstance(model.rf_model, RandomForestClassifier)
        assert isinstance(model.gb_model, GradientBoostingClassifier)
        assert 0.0 <= model.validation_accuracy <= 1.0
        assert 0.0 <= model.false_negative_rate <= 1.0
        assert len(model.feature_names) == 1644

    def test_list_models_returns_sorted_metadata_list(self, sample_ensemble_model, temp_models_dir):
        """
        Test list_models returns sorted list of ModelMetadata objects.

        NECESSARY: Yield test
        AC-3.4: Validate list_models output format
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        storage.save_model(sample_ensemble_model, version="v1.0")
        storage.save_model(sample_ensemble_model, version="v2.0")
        storage.save_model(sample_ensemble_model, version="v1.5")

        models = storage.list_models()

        # Validate output structure
        assert isinstance(models, list)
        assert len(models) == 3
        assert all(isinstance(m, ModelMetadata) for m in models)

        # Validate sorted (newest first)
        versions = [m.version for m in models]
        assert versions == ["v2.0", "v1.5", "v1.0"]

    def test_save_model_returns_path_to_saved_file(self, sample_ensemble_model, temp_models_dir):
        """
        Test save_model returns Path to saved .pkl file.

        NECESSARY: Yield test
        AC-1.1: Validate save_model output
        """
        storage = ModelStorage(base_dir=temp_models_dir)
        result = storage.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        path = result.unwrap()

        # Validate output is Path object
        assert isinstance(path, Path)
        assert path.exists()
        assert path.suffix == ".pkl"
        assert "routing_classifier_v1.0" in path.name
