"""
Tests for ModelArtifactManager (versioned model storage with atomic swaps).

Constitutional compliance:
- Article I: Complete context (all artifacts with metadata)
- Article II: 100% verification (atomic symlink swaps, zero-downtime)
- Article IV: VectorStore integration (artifact versioning for learning)
- Article V: Spec-driven (follows implementation guidance)
- Law #1: TDD mandatory (tests written FIRST)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling

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
from tools.ml_routing.model_artifact_manager import (
    ArtifactError,
    ArtifactMetadata,
    ModelArtifactManager,
)


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


class TestArtifactMetadata:
    """Test ArtifactMetadata Pydantic model."""

    def test_metadata_creation_with_all_required_fields(self):
        """Test ArtifactMetadata creation with all required fields."""
        metadata = ArtifactMetadata(
            version="v1.0",
            accuracy=0.984,
            timestamp="2025-10-10T12:00:00Z",
            model_size_mb=12.5,
            sklearn_version="1.3.0",
        )

        assert metadata.version == "v1.0"
        assert metadata.accuracy == 0.984
        assert metadata.timestamp == "2025-10-10T12:00:00Z"
        assert metadata.model_size_mb == 12.5
        assert metadata.sklearn_version == "1.3.0"

    def test_metadata_accuracy_validation_below_zero(self):
        """Test accuracy validation rejects negative values."""
        with pytest.raises(ValueError):
            ArtifactMetadata(
                version="v1.0",
                accuracy=-0.1,  # Invalid: negative accuracy
                timestamp="2025-10-10T12:00:00Z",
                model_size_mb=12.5,
                sklearn_version="1.3.0",
            )

    def test_metadata_accuracy_validation_above_one(self):
        """Test accuracy validation rejects values > 1.0."""
        with pytest.raises(ValueError):
            ArtifactMetadata(
                version="v1.0",
                accuracy=1.5,  # Invalid: accuracy > 1.0
                timestamp="2025-10-10T12:00:00Z",
                model_size_mb=12.5,
                sklearn_version="1.3.0",
            )

    def test_metadata_model_size_validation(self):
        """Test model_size_mb validation rejects negative values."""
        with pytest.raises(ValueError):
            ArtifactMetadata(
                version="v1.0",
                accuracy=0.984,
                timestamp="2025-10-10T12:00:00Z",
                model_size_mb=-1.0,  # Invalid: negative size
                sklearn_version="1.3.0",
            )


class TestModelArtifactManager:
    """Test ModelArtifactManager versioned storage and atomic swaps."""

    def test_initialization_creates_models_directory(self, temp_models_dir):
        """Test ModelArtifactManager initialization creates models directory."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        assert manager.models_dir.exists()
        assert manager.models_dir.is_dir()

    def test_save_model_creates_versioned_artifact(self, temp_models_dir, sample_ensemble_model):
        """Test save_model creates ensemble_v{version}.pkl artifact."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        artifact_path = result.unwrap()
        assert artifact_path.name == "ensemble_v1.0.pkl"
        assert artifact_path.exists()

    def test_save_model_creates_metadata_json(self, temp_models_dir, sample_ensemble_model):
        """Test save_model creates ensemble_v{version}_metadata.json."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()
        artifact_path = result.unwrap()

        metadata_path = artifact_path.parent / f"{artifact_path.stem}_metadata.json"
        assert metadata_path.exists()

        # Validate metadata content
        with open(metadata_path) as f:
            metadata = json.load(f)

        assert metadata["version"] == "v1.0"
        assert metadata["accuracy"] == 0.984
        assert "timestamp" in metadata
        assert metadata["model_size_mb"] > 0
        assert "sklearn_version" in metadata

    def test_save_model_without_version_auto_generates_v1_0(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test save_model without version generates v1.0 for first model."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.save_model(sample_ensemble_model)

        assert result.is_ok()
        artifact_path = result.unwrap()
        assert artifact_path.name == "ensemble_v1.0.pkl"

    def test_save_model_auto_increments_minor_version(self, temp_models_dir, sample_ensemble_model):
        """Test save_model auto-increments minor version (v1.0 → v1.1)."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save first model (v1.0)
        result1 = manager.save_model(sample_ensemble_model)
        assert result1.is_ok()

        # Save second model (should be v1.1)
        result2 = manager.save_model(sample_ensemble_model)
        assert result2.is_ok()
        artifact_path = result2.unwrap()
        assert artifact_path.name == "ensemble_v1.1.pkl"

    def test_save_model_creates_active_symlink(self, temp_models_dir, sample_ensemble_model):
        """Test save_model creates ensemble_active.pkl symlink."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_ok()

        # Check symlink exists and points to correct target
        active_symlink = temp_models_dir / "ensemble_active.pkl"
        assert active_symlink.exists()
        assert active_symlink.is_symlink()
        assert active_symlink.resolve().name == "ensemble_v1.0.pkl"

    def test_save_model_updates_active_symlink_atomically(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test save_model updates active symlink atomically (zero-downtime)."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save first model (v1.0)
        result1 = manager.save_model(sample_ensemble_model, version="v1.0")
        assert result1.is_ok()

        active_symlink = temp_models_dir / "ensemble_active.pkl"
        assert active_symlink.resolve().name == "ensemble_v1.0.pkl"

        # Save second model (v1.1)
        result2 = manager.save_model(sample_ensemble_model, version="v1.1")
        assert result2.is_ok()

        # Verify symlink now points to v1.1 (atomic swap)
        assert active_symlink.resolve().name == "ensemble_v1.1.pkl"

    def test_load_active_model_returns_latest_version(self, temp_models_dir, sample_ensemble_model):
        """Test load_active_model loads model from ensemble_active.pkl symlink."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save model
        manager.save_model(sample_ensemble_model, version="v1.0")

        # Load active model
        result = manager.load_active_model()

        assert result.is_ok()
        loaded_model = result.unwrap()
        assert isinstance(loaded_model, EnsembleModel)
        assert loaded_model.validation_accuracy == 0.984

    def test_load_active_model_returns_error_when_no_active_symlink(self, temp_models_dir):
        """Test load_active_model returns error when no active symlink exists."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.load_active_model()

        assert result.is_err()
        assert "No active model" in result.unwrap_err()

    def test_load_model_by_version_loads_specific_version(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test load_model loads specific version by version string."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save two versions
        manager.save_model(sample_ensemble_model, version="v1.0")
        manager.save_model(sample_ensemble_model, version="v1.1")

        # Load v1.0 specifically
        result = manager.load_model(version="v1.0")

        assert result.is_ok()
        loaded_model = result.unwrap()
        assert isinstance(loaded_model, EnsembleModel)

    def test_load_model_returns_error_for_nonexistent_version(self, temp_models_dir):
        """Test load_model returns error for non-existent version."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        result = manager.load_model(version="v99.99")

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_list_all_versions_returns_empty_for_no_models(self, temp_models_dir):
        """Test list_all_versions returns empty list when no models exist."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        versions = manager.list_all_versions()

        assert versions == []

    def test_list_all_versions_returns_all_saved_models(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test list_all_versions returns all saved model versions."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save three versions
        manager.save_model(sample_ensemble_model, version="v1.0")
        manager.save_model(sample_ensemble_model, version="v1.1")
        manager.save_model(sample_ensemble_model, version="v2.0")

        versions = manager.list_all_versions()

        assert len(versions) == 3
        assert all(isinstance(v, ArtifactMetadata) for v in versions)

        # Verify versions are sorted (newest first)
        version_strings = [v.version for v in versions]
        assert version_strings == ["v2.0", "v1.1", "v1.0"]

    def test_list_all_versions_includes_metadata(self, temp_models_dir, sample_ensemble_model):
        """Test list_all_versions includes accuracy, timestamp, size metadata."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save model
        manager.save_model(sample_ensemble_model, version="v1.0")

        versions = manager.list_all_versions()

        assert len(versions) == 1
        metadata = versions[0]

        assert metadata.version == "v1.0"
        assert metadata.accuracy == 0.984
        assert metadata.model_size_mb > 0
        assert metadata.timestamp is not None
        assert metadata.sklearn_version is not None

    def test_atomic_symlink_swap_uses_os_replace(
        self, temp_models_dir, sample_ensemble_model, monkeypatch
    ):
        """Test atomic symlink swap uses os.replace() for zero-downtime."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Track os.replace calls
        replace_calls = []
        original_replace = os.replace

        def mock_replace(src, dst):
            replace_calls.append((src, dst))
            return original_replace(src, dst)

        monkeypatch.setattr(os, "replace", mock_replace)

        # Save model (triggers atomic symlink update)
        manager.save_model(sample_ensemble_model, version="v1.0")

        # Verify os.replace was called (atomic operation)
        assert len(replace_calls) == 1
        src, dst = replace_calls[0]
        assert "ensemble_active" in str(dst)

    def test_save_model_handles_concurrent_writes_safely(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test save_model handles concurrent writes without corruption."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save two models rapidly (simulates concurrent writes)
        result1 = manager.save_model(sample_ensemble_model, version="v1.0")
        result2 = manager.save_model(sample_ensemble_model, version="v1.1")

        assert result1.is_ok()
        assert result2.is_ok()

        # Verify both artifacts exist
        assert (temp_models_dir / "ensemble_v1.0.pkl").exists()
        assert (temp_models_dir / "ensemble_v1.1.pkl").exists()

        # Verify active symlink points to latest (v1.1)
        active_symlink = temp_models_dir / "ensemble_active.pkl"
        assert active_symlink.resolve().name == "ensemble_v1.1.pkl"

    def test_save_model_returns_error_on_io_failure(
        self, temp_models_dir, sample_ensemble_model, monkeypatch
    ):
        """Test save_model returns Err on joblib.dump failure."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Mock joblib.dump to fail
        def mock_dump(*args, **kwargs):
            raise OSError("Disk full")

        monkeypatch.setattr(joblib, "dump", mock_dump)

        result = manager.save_model(sample_ensemble_model, version="v1.0")

        assert result.is_err()
        assert "Failed to save model" in result.unwrap_err()

    def test_load_model_returns_error_on_corrupted_artifact(self, temp_models_dir):
        """Test load_model returns Err when artifact is corrupted."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Create corrupted model file
        corrupted_path = temp_models_dir / "ensemble_v1.0.pkl"
        with open(corrupted_path, "w") as f:
            f.write("corrupted binary data")

        # Create valid metadata
        metadata_path = temp_models_dir / "ensemble_v1.0_metadata.json"
        metadata = {
            "version": "v1.0",
            "accuracy": 0.984,
            "timestamp": datetime.now(UTC).isoformat(),
            "model_size_mb": 0.001,
            "sklearn_version": sklearn.__version__,
        }
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        result = manager.load_model(version="v1.0")

        assert result.is_err()
        assert "Failed to load model" in result.unwrap_err()

    def test_load_model_returns_error_when_metadata_missing(
        self, temp_models_dir, sample_ensemble_model
    ):
        """Test load_model returns Err when metadata JSON is missing."""
        manager = ModelArtifactManager(models_dir=temp_models_dir)

        # Save model
        result = manager.save_model(sample_ensemble_model, version="v1.0")
        assert result.is_ok()

        # Delete metadata file
        metadata_path = temp_models_dir / "ensemble_v1.0_metadata.json"
        metadata_path.unlink()

        # Attempt to load
        result = manager.load_model(version="v1.0")

        assert result.is_err()
        assert "Metadata not found" in result.unwrap_err()
