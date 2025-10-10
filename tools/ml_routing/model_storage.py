"""
ModelStorage for versioning and persisting trained ensemble models.

Provides semantic versioning (v1.0, v1.1, v2.0), joblib serialization,
metadata tracking, and model lifecycle management.

Constitutional compliance:
- Article I: Complete context (all training metadata saved)
- Article II: 100% verification (model size <50MB, load time <1s)
- Article IV: VectorStore integration (models persisted for cross-session use)
- Article V: Spec-driven (follows spec-005 section 4.2.3)

Reference: specs/spec-005-advanced-pattern-recognition.md (section 4.2.3)
Author: CodeAgent
Date: 2025-10-10
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import joblib
import sklearn
from pydantic import BaseModel, ConfigDict, Field

from shared.models import EnsembleModel
from shared.type_definitions import Err, Ok, Result


class ModelMetadata(BaseModel):
    """
    Metadata for stored ML model (versioning and tracking).

    Fields:
        version: Semantic version (e.g., "v1.0", "v2.5")
        training_date: ISO 8601 timestamp when model was trained
        validation_accuracy: Validation accuracy (≥0.98)
        false_negative_rate: False negative rate (≤0.02)
        feature_count: Number of features (1644 for TaskFeatureVector)
        model_size_mb: Model file size in megabytes
        sklearn_version: Scikit-learn version used for training
        file_path: Path to serialized model file

    Example:
        >>> metadata = ModelMetadata(
        ...     version="v1.0",
        ...     training_date="2025-10-10T12:00:00Z",
        ...     validation_accuracy=0.984,
        ...     false_negative_rate=0.018,
        ...     feature_count=1644,
        ...     model_size_mb=12.5,
        ...     sklearn_version="1.3.0",
        ...     file_path=Path("/path/to/model.pkl")
        ... )
    """

    version: str = Field(
        ...,
        description="Semantic version (e.g., 'v1.0', 'v2.5')",
    )

    training_date: str = Field(
        ...,
        description="ISO 8601 timestamp when model was trained",
    )

    validation_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Validation accuracy (0-1 range)",
    )

    false_negative_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="False negative rate for complex tasks (0-1 range)",
    )

    feature_count: int = Field(
        ...,
        ge=1,
        description="Number of features (should be 1644 for TaskFeatureVector)",
    )

    model_size_mb: float = Field(
        ...,
        ge=0.0,
        description="Model file size in megabytes",
    )

    sklearn_version: str = Field(
        ...,
        description="Scikit-learn version used for training",
    )

    file_path: Path = Field(
        ...,
        description="Path to serialized model file",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ModelStorage:
    """
    Storage manager for trained ML models with versioning.

    Provides:
    - Semantic versioning (v1.0, v1.1, v2.0)
    - Joblib serialization with compression
    - Metadata tracking (accuracy, size, date)
    - Model lifecycle management (save, load, list, rollback)

    Directory structure:
        ~/.agency/models/
        ├── routing_classifier_v1.0.pkl  (model file)
        ├── routing_classifier_v1.0.json (metadata)
        ├── routing_classifier_v1.1.pkl
        ├── routing_classifier_v1.1.json
        ├── routing_classifier_v2.0.pkl
        ├── routing_classifier_v2.0.json
        └── routing_classifier_latest.pkl -> routing_classifier_v2.0.pkl

    Example:
        >>> storage = ModelStorage()
        >>> result = storage.save_model(ensemble_model, version="v1.0")
        >>> if result.is_ok():
        ...     print(f"Model saved to: {result.unwrap()}")
        >>>
        >>> load_result = storage.load_model(version="latest")
        >>> if load_result.is_ok():
        ...     model = load_result.unwrap()
        ...     predictions = model.ensemble.predict(X_test)
    """

    def __init__(self, base_dir: Path | None = None):
        """
        Initialize ModelStorage with base directory.

        Args:
            base_dir: Base directory for model storage (default: ~/.agency/models)
        """
        if base_dir is None:
            self.base_dir = Path.home() / ".agency" / "models"
        else:
            self.base_dir = base_dir

    def save_model(
        self,
        model: EnsembleModel,
        version: str | None = None,
        breaking_change: bool = False,
    ) -> Result[Path, str]:
        """
        Save ensemble model to disk with metadata.

        Args:
            model: EnsembleModel to save
            version: Semantic version (e.g., "v1.0"), auto-generated if None
            breaking_change: If True, increment major version (v1.x -> v2.0)

        Returns:
            Result with Path to saved model file or error message

        Workflow:
        1. Create base directory if not exists
        2. Generate version number (if not provided)
        3. Serialize model with joblib (compress=3, protocol=4)
        4. Save metadata JSON (accuracy, size, date, version)
        5. Update 'latest' symlink
        6. Set secure permissions (0600)

        Performance:
        - Model size: <50MB target (warning if exceeded)
        - Serialization: <5s for 50MB model
        - Compression: ~3x size reduction (compress=3)

        Example:
            >>> storage = ModelStorage()
            >>> result = storage.save_model(model, version="v1.0")
            >>> if result.is_ok():
            ...     print(f"Saved to: {result.unwrap()}")
        """
        try:
            # Step 1: Create directory
            self.base_dir.mkdir(parents=True, exist_ok=True)

            # Step 2: Generate version
            if version is None:
                version = self._generate_version_number(breaking_change)
            else:
                # Validate version format (vX.Y)
                import re
                if not re.match(r"^v\d+\.\d+", version):
                    return Err(
                        f"Invalid version format: '{version}'. "
                        "Expected semantic version (e.g., 'v1.0', 'v2.5')"
                    )

            # Step 3: Serialize model
            model_path = self.base_dir / f"routing_classifier_{version}.pkl"

            try:
                joblib.dump(model, model_path, compress=3, protocol=4)
            except Exception as e:
                return Err(f"Failed to serialize model: {e}")

            # Step 4: Save metadata
            model_size_mb = model_path.stat().st_size / (1024 * 1024)
            metadata = {
                "version": version,
                "training_date": model.training_date,
                "validation_accuracy": model.validation_accuracy,
                "false_negative_rate": model.false_negative_rate,
                "feature_count": len(model.feature_names),
                "model_size_mb": round(model_size_mb, 2),
                "sklearn_version": sklearn.__version__,
                "file_path": str(model_path),
            }

            metadata_path = self.base_dir / f"routing_classifier_{version}.json"
            try:
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                return Err(f"Failed to save metadata: {e}")

            # Step 5: Update symlink
            latest_link = self.base_dir / "routing_classifier_latest.pkl"
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(model_path.name)

            # Step 6: Set permissions (0600)
            os.chmod(model_path, 0o600)
            os.chmod(metadata_path, 0o600)

            # Validate model size <50MB
            if model_size_mb > 50:
                print(
                    f"⚠️  Warning: Model size {model_size_mb:.1f}MB exceeds 50MB target"
                )

            return Ok(model_path)

        except Exception as e:
            return Err(f"Failed to save model: {e}")

    def load_model(self, version: str = "latest") -> Result[EnsembleModel, str]:
        """
        Load ensemble model from disk.

        Args:
            version: Version to load ("latest" or specific version like "v1.0")

        Returns:
            Result with loaded EnsembleModel or error message

        Workflow:
        1. Resolve version (latest -> specific version)
        2. Load metadata JSON (validate compatibility)
        3. Deserialize model with joblib
        4. Validate load time <1s (warning if exceeded)

        Validation:
        - Feature count must match 1644 (TaskFeatureVector dimensions)
        - Model file must exist
        - Metadata must exist

        Performance:
        - Load time: <1s target (warning if exceeded)
        - Lazy loading: Only load when needed

        Example:
            >>> storage = ModelStorage()
            >>> result = storage.load_model(version="latest")
            >>> if result.is_ok():
            ...     model = result.unwrap()
            ...     predictions = model.ensemble.predict(X_test)
        """
        try:
            # Step 1: Resolve version
            if version == "latest":
                latest_link = self.base_dir / "routing_classifier_latest.pkl"
                if not latest_link.exists():
                    return Err(
                        "No models found (routing_classifier_latest.pkl missing)"
                    )
                try:
                    model_path = latest_link.resolve()
                    # Check if resolved path exists (symlink could be broken)
                    if not model_path.exists():
                        return Err(
                            f"Model file not found (broken symlink: {model_path.name})"
                        )
                except Exception as e:
                    return Err(f"Failed to resolve latest symlink: {e}")
            else:
                model_path = self.base_dir / f"routing_classifier_{version}.pkl"
                if not model_path.exists():
                    return Err(f"Model version {version} not found")

            # Step 2: Load metadata (validate compatibility)
            metadata_path = model_path.with_suffix(".json")
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
            except Exception as e:
                return Err(f"Failed to load metadata: {e}")

            # Validate feature count
            if metadata["feature_count"] != 1644:
                return Err(
                    f"Incompatible model: {metadata['feature_count']} features (expected 1644)"
                )

            # Step 3: Deserialize model
            start_time = time.perf_counter()
            try:
                model = joblib.load(model_path)
            except Exception as e:
                return Err(f"Failed to load model: {e}")

            load_time = time.perf_counter() - start_time

            # Step 4: Validate load time <1s
            if load_time > 1.0:
                print(
                    f"⚠️  Warning: Model load time {load_time:.2f}s exceeds 1s target"
                )

            return Ok(model)

        except Exception as e:
            return Err(f"Failed to load model: {e}")

    def list_models(self) -> list[ModelMetadata]:
        """
        List all stored models with metadata.

        Returns:
            List of ModelMetadata (sorted by version, newest first)

        Example:
            >>> storage = ModelStorage()
            >>> models = storage.list_models()
            >>> for model in models:
            ...     print(f"{model.version}: {model.validation_accuracy:.3f} accuracy")
            v2.0: 0.984 accuracy
            v1.1: 0.978 accuracy
            v1.0: 0.972 accuracy
        """
        if not self.base_dir.exists():
            return []

        models = []
        for pkl_file in self.base_dir.glob("routing_classifier_v*.pkl"):
            metadata_path = pkl_file.with_suffix(".json")
            if metadata_path.exists():
                try:
                    with open(metadata_path) as f:
                        data = json.load(f)
                        models.append(ModelMetadata(**data))
                except Exception:
                    # Skip malformed metadata
                    continue

        # Sort by version (newest first)
        models.sort(key=lambda m: self._parse_version(m.version), reverse=True)
        return models

    def _generate_version_number(self, breaking_change: bool) -> str:
        """
        Generate next semantic version number.

        Args:
            breaking_change: If True, increment major version (v1.x -> v2.0)

        Returns:
            Version string (e.g., "v1.0", "v1.1", "v2.0")

        Versioning Rules:
        - First model: v1.0
        - Minor update: v1.0 -> v1.1 -> v1.2
        - Breaking change: v1.x -> v2.0

        Example:
            >>> storage = ModelStorage()
            >>> storage._generate_version_number(breaking_change=False)
            'v1.0'  # First model
            >>> storage.save_model(model, version="v1.0")
            >>> storage._generate_version_number(breaking_change=False)
            'v1.1'  # Incremental update
            >>> storage._generate_version_number(breaking_change=True)
            'v2.0'  # Breaking change
        """
        existing_models = self.list_models()

        if not existing_models:
            return "v1.0"

        latest = existing_models[0]
        major, minor = self._parse_version(latest.version)

        if breaking_change:
            return f"v{major + 1}.0"
        else:
            return f"v{major}.{minor + 1}"

    def _parse_version(self, version: str) -> tuple[int, int]:
        """
        Parse semantic version string to (major, minor) tuple.

        Args:
            version: Version string (e.g., "v1.0", "v2.5")

        Returns:
            Tuple of (major, minor) as integers

        Example:
            >>> storage = ModelStorage()
            >>> storage._parse_version("v1.0")
            (1, 0)
            >>> storage._parse_version("v2.5")
            (2, 5)
        """
        # Remove 'v' prefix and split
        version_parts = version.lstrip("v").split(".")
        major = int(version_parts[0])
        minor = int(version_parts[1])
        return (major, minor)
