"""
Training dataset model for ML-based task routing.

Provides structured representation of training data with train/val splits:
- TrainingSample: Individual training example with features and label
- DatasetMetadata: Dataset statistics and metadata
- TrainingDataset: Complete dataset with train/val splits

Constitutional compliance:
- Article I: Complete context (all samples validated before training)
- Article II: 100% verification (strict typing, comprehensive validators)
- Article IV: VectorStore integration (samples from quality feedback)
- Article V: Spec-driven (follows spec-005-advanced-pattern-recognition.md)

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.4
Author: ChiefArchitectAgent
Date: 2025-10-10
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from .task_feature_vector import TaskFeatureVector


class TrainingSample(BaseModel):
    """
    Single training example with features and label.

    Represents one labeled task for ML training/validation. Features are
    1644-dimensional vectors (embedding + TF-IDF + metadata), labels are
    tier classifications (1=simple, 2=moderate, 3=complex).

    Constitutional Alignment:
    - Article II: Strict typing, comprehensive validators
    - Article IV: Sourced from VectorStore quality feedback

    Example:
        >>> sample = TrainingSample(
        ...     features=TaskFeatureVector(...),
        ...     label=2,  # moderate
        ...     confidence=0.85,
        ...     source="vectorstore",
        ...     task_id="task_123",
        ...     timestamp=datetime.now()
        ... )
    """

    features: TaskFeatureVector = Field(
        ...,
        description=(
            "1644-dimensional feature vector for ML classification. "
            "Includes semantic embedding (1536-dim), TF-IDF scores (100-dim), "
            "and metadata features (8-dim). See TaskFeatureVector for details."
        ),
    )

    label: int = Field(
        ...,
        description=(
            "Tier classification: 1 (simple), 2 (moderate), 3 (complex). "
            "NOT 0-indexed for clarity. Maps to P3, P2, P1 priority tiers. "
            "Sourced from quality feedback or manual labeling."
        ),
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score for this label (0.0-1.0). "
            "From Leap 4 quality feedback system or manual labeling. "
            "High confidence (≥0.8) indicates reliable ground truth."
        ),
    )

    source: str = Field(
        ...,
        description=(
            "Data source: 'vectorstore' (auto-extracted from quality feedback) "
            "or 'manual_label' (human-labeled). "
            "Article IV: VectorStore is primary source for institutional learning."
        ),
    )

    task_id: str = Field(
        ...,
        description=(
            "Unique task identifier for traceability. "
            "Links back to original task execution in session logs. "
            "Format: 'task_{timestamp}_{hash}' or similar."
        ),
    )

    timestamp: datetime = Field(
        ...,
        description=(
            "When this sample was created (UTC). Used for temporal analysis and dataset versioning."
        ),
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "features": {
                    "embedding": [0.023, -0.045] + [0.0] * 1534,
                    "tfidf_features": [0.12, 0.0] + [0.0] * 98,
                    "description_length": 120,
                    "word_count": 20,
                    "has_refactor_keyword": 1,
                    "has_test_keyword": 0,
                    "has_async_keyword": 1,
                    "has_fix_keyword": 0,
                    "estimated_time_seconds": 300.0,
                    "historical_tier_mode": 2,
                },
                "label": 2,
                "confidence": 0.85,
                "source": "vectorstore",
                "task_id": "task_20251010_abc123",
                "timestamp": "2025-10-10T10:00:00Z",
            }
        }

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: int) -> int:
        """
        Ensure label is 1, 2, or 3 (NOT 0-indexed).

        Article II compliance: Strict validation before training.

        Args:
            v: Label value to validate

        Returns:
            Validated label (1, 2, or 3)

        Raises:
            ValueError: If label is not 1, 2, or 3
        """
        if v not in {1, 2, 3}:
            raise ValueError(
                f"Label must be 1 (simple), 2 (moderate), or 3 (complex), got {v}. "
                f"Article II violation: Invalid label for ML training."
            )
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """
        Ensure confidence is between 0.0 and 1.0.

        Article II compliance: Strict validation of confidence scores.

        Args:
            v: Confidence value to validate

        Returns:
            Validated confidence (0.0-1.0)

        Raises:
            ValueError: If confidence is not in [0.0, 1.0]
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {v}. "
                f"Article II violation: Invalid confidence score."
            )
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """
        Ensure source is valid.

        Article IV compliance: VectorStore is primary source.

        Args:
            v: Source value to validate

        Returns:
            Validated source

        Raises:
            ValueError: If source is not 'vectorstore' or 'manual_label'
        """
        valid_sources = {"vectorstore", "manual_label"}
        if v not in valid_sources:
            raise ValueError(
                f"Source must be one of {valid_sources}, got '{v}'. "
                f"Article IV violation: Unknown data source."
            )
        return v


class DatasetMetadata(BaseModel):
    """
    Metadata about the training dataset.

    Provides statistics and versioning information for dataset tracking
    and reproducibility. Includes sample counts, label distribution, and
    quality thresholds.

    Constitutional Alignment:
    - Article II: Strict typing, comprehensive validators
    - Article V: Spec-driven (traceability to spec-005)

    Example:
        >>> metadata = DatasetMetadata(
        ...     total_samples=1000,
        ...     train_count=800,
        ...     val_count=200,
        ...     label_distribution={1: 300, 2: 400, 3: 300},
        ...     created_at=datetime.now(),
        ...     version="v1.0",
        ...     min_confidence=0.6,
        ...     source="vectorstore_quality_feedback"
        ... )
    """

    total_samples: int = Field(
        ...,
        ge=0,
        description=(
            "Total number of samples in dataset (train + val). "
            "Must equal train_count + val_count (validated)."
        ),
    )

    train_count: int = Field(
        ...,
        ge=0,
        description=(
            "Number of training samples. Typically 70-80% of total_samples for train/val split."
        ),
    )

    val_count: int = Field(
        ...,
        ge=0,
        description=(
            "Number of validation samples. Typically 20-30% of total_samples for train/val split."
        ),
    )

    label_distribution: dict[int, int] = Field(
        ...,
        description=(
            "Count of samples per tier label. "
            "Format: {1: count_simple, 2: count_moderate, 3: count_complex}. "
            "Used to detect class imbalance (Article II: complete context)."
        ),
    )

    created_at: datetime = Field(
        ...,
        description=(
            "When this dataset was created (UTC). Used for versioning and reproducibility tracking."
        ),
    )

    version: str = Field(
        ...,
        description=(
            "Dataset version identifier. "
            "Format: 'v{major}.{minor}' (e.g., 'v1.0', 'v2.1'). "
            "Incremented when dataset is updated with new samples."
        ),
    )

    min_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum confidence threshold for including samples. "
            "Samples below this threshold are filtered out. "
            "Default: 0.6 (Article IV: high-quality learning data)."
        ),
    )

    source: str = Field(
        ...,
        description=(
            "Dataset source identifier. "
            "Typically 'vectorstore_quality_feedback' for auto-extracted samples. "
            "Article IV: VectorStore is primary source."
        ),
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_samples": 1000,
                "train_count": 800,
                "val_count": 200,
                "label_distribution": {1: 300, 2: 400, 3: 300},
                "created_at": "2025-10-10T10:00:00Z",
                "version": "v1.0",
                "min_confidence": 0.6,
                "source": "vectorstore_quality_feedback",
            }
        }

    @field_validator("train_count", "val_count", "total_samples")
    @classmethod
    def validate_counts(cls, v: int) -> int:
        """
        Ensure counts are non-negative.

        Article II compliance: Strict validation of sample counts.

        Args:
            v: Count value to validate

        Returns:
            Validated count (≥0)

        Raises:
            ValueError: If count is negative
        """
        if v < 0:
            raise ValueError(
                f"Count must be non-negative, got {v}. Article II violation: Invalid sample count."
            )
        return v

    @model_validator(mode="after")
    def validate_split_sum(self) -> "DatasetMetadata":
        """
        Ensure train + val = total.

        Article I compliance: Complete context validation.

        Returns:
            Validated DatasetMetadata instance

        Raises:
            ValueError: If train_count + val_count != total_samples
        """
        if self.train_count + self.val_count != self.total_samples:
            raise ValueError(
                f"train_count ({self.train_count}) + val_count ({self.val_count}) "
                f"must equal total_samples ({self.total_samples}). "
                f"Article I violation: Incomplete context (split mismatch)."
            )
        return self

    @field_validator("label_distribution")
    @classmethod
    def validate_label_distribution(cls, v: dict[int, int]) -> dict[int, int]:
        """
        Ensure label distribution has valid keys (1, 2, 3).

        Article II compliance: Strict validation of label distribution.

        Args:
            v: Label distribution to validate

        Returns:
            Validated label distribution

        Raises:
            ValueError: If any label key is not 1, 2, or 3
        """
        valid_labels = {1, 2, 3}
        invalid_labels = set(v.keys()) - valid_labels
        if invalid_labels:
            raise ValueError(
                f"Label distribution keys must be {valid_labels}, got invalid labels: {invalid_labels}. "
                f"Article II violation: Invalid label keys."
            )
        return v


class TrainingDataset(BaseModel):
    """
    Complete training dataset with train/val splits.

    Represents a versioned dataset for ML model training, including samples,
    split indices, and metadata. Provides utility methods for accessing
    train/val subsets and analyzing label distribution.

    Constitutional Alignment:
    - Article I: Complete context (all samples validated before training)
    - Article II: 100% verification (strict typing, comprehensive validators)
    - Article IV: VectorStore sourced samples (institutional learning)
    - Article V: Spec-driven (traceability to spec-005)

    Example:
        >>> dataset = TrainingDataset(
        ...     samples=[sample1, sample2, ...],
        ...     train_indices=[0, 1, 2, ...],
        ...     val_indices=[798, 799],
        ...     metadata=metadata
        ... )
        >>> train_samples = dataset.get_train_samples()
        >>> val_samples = dataset.get_val_samples()
        >>> distribution = dataset.get_label_distribution()
    """

    samples: list[TrainingSample] = Field(
        ...,
        description=(
            "All training samples (train + val combined). "
            "Article I: Complete context before splitting."
        ),
    )

    train_indices: list[int] = Field(
        ...,
        description=(
            "Indices into samples array for training set. "
            "Typically 70-80% of total samples. "
            "Must not overlap with val_indices (validated)."
        ),
    )

    val_indices: list[int] = Field(
        ...,
        description=(
            "Indices into samples array for validation set. "
            "Typically 20-30% of total samples. "
            "Must not overlap with train_indices (validated)."
        ),
    )

    metadata: DatasetMetadata = Field(
        ...,
        description=(
            "Dataset statistics and metadata. "
            "Includes sample counts, label distribution, versioning."
        ),
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "samples": [
                    {
                        "features": {
                            "embedding": [0.023] + [0.0] * 1535,
                            "tfidf_features": [0.12] + [0.0] * 99,
                            "description_length": 120,
                            "word_count": 20,
                            "has_refactor_keyword": 1,
                            "has_test_keyword": 0,
                            "has_async_keyword": 1,
                            "has_fix_keyword": 0,
                            "estimated_time_seconds": 300.0,
                            "historical_tier_mode": 2,
                        },
                        "label": 2,
                        "confidence": 0.85,
                        "source": "vectorstore",
                        "task_id": "task_001",
                        "timestamp": "2025-10-10T10:00:00Z",
                    }
                ],
                "train_indices": [0],
                "val_indices": [],
                "metadata": {
                    "total_samples": 1,
                    "train_count": 1,
                    "val_count": 0,
                    "label_distribution": {2: 1},
                    "created_at": "2025-10-10T10:00:00Z",
                    "version": "v1.0",
                    "min_confidence": 0.6,
                    "source": "vectorstore_quality_feedback",
                },
            }
        }

    @model_validator(mode="after")
    def validate_splits(self) -> "TrainingDataset":
        """
        Ensure train/val splits are valid and non-overlapping.

        Article I & II compliance: Complete context + 100% verification.

        Validations:
        1. train_indices and val_indices don't overlap
        2. All indices are valid (within samples range)
        3. train + val = total samples (complete coverage)

        Returns:
            Validated TrainingDataset instance

        Raises:
            ValueError: If any validation fails
        """
        # Check: train_indices and val_indices don't overlap
        train_set = set(self.train_indices)
        val_set = set(self.val_indices)

        overlap = train_set & val_set
        if overlap:
            raise ValueError(
                f"train_indices and val_indices must not overlap. "
                f"Found {len(overlap)} overlapping indices: {sorted(overlap)[:10]}... "
                f"Article II violation: Invalid train/val split."
            )

        # Check: all indices are valid (within samples range)
        max_idx = len(self.samples) - 1
        invalid_train = [idx for idx in self.train_indices if idx < 0 or idx > max_idx]
        invalid_val = [idx for idx in self.val_indices if idx < 0 or idx > max_idx]

        if invalid_train:
            raise ValueError(
                f"train_indices contains {len(invalid_train)} invalid indices. "
                f"Valid range: [0, {max_idx}]. "
                f"Invalid: {invalid_train[:10]}... "
                f"Article I violation: Incomplete context (invalid indices)."
            )

        if invalid_val:
            raise ValueError(
                f"val_indices contains {len(invalid_val)} invalid indices. "
                f"Valid range: [0, {max_idx}]. "
                f"Invalid: {invalid_val[:10]}... "
                f"Article I violation: Incomplete context (invalid indices)."
            )

        # Check: train + val = total samples (complete coverage)
        total_indexed = len(self.train_indices) + len(self.val_indices)
        if total_indexed != len(self.samples):
            raise ValueError(
                f"train_indices ({len(self.train_indices)}) + val_indices ({len(self.val_indices)}) "
                f"must equal total samples ({len(self.samples)}). "
                f"Found: {total_indexed} indexed, {len(self.samples)} total. "
                f"Article I violation: Incomplete context (missing samples)."
            )

        return self

    def get_train_samples(self) -> list[TrainingSample]:
        """
        Get training samples.

        Returns:
            List of training samples (subset of self.samples)

        Example:
            >>> train_samples = dataset.get_train_samples()
            >>> len(train_samples)
            800
        """
        return [self.samples[i] for i in self.train_indices]

    def get_val_samples(self) -> list[TrainingSample]:
        """
        Get validation samples.

        Returns:
            List of validation samples (subset of self.samples)

        Example:
            >>> val_samples = dataset.get_val_samples()
            >>> len(val_samples)
            200
        """
        return [self.samples[i] for i in self.val_indices]

    def get_label_distribution(self) -> dict[str, dict[int, int]]:
        """
        Get label distribution for train and val splits.

        Returns:
            Dictionary with train and val label distributions.
            Format: {
                "train": {1: count_simple, 2: count_moderate, 3: count_complex},
                "val": {1: count_simple, 2: count_moderate, 3: count_complex}
            }

        Example:
            >>> distribution = dataset.get_label_distribution()
            >>> distribution["train"]
            {1: 240, 2: 320, 3: 240}
            >>> distribution["val"]
            {1: 60, 2: 80, 3: 60}
        """
        train_labels = [self.samples[i].label for i in self.train_indices]
        val_labels = [self.samples[i].label for i in self.val_indices]

        return {
            "train": {label: train_labels.count(label) for label in {1, 2, 3}},
            "val": {label: val_labels.count(label) for label in {1, 2, 3}},
        }

    def get_confidence_stats(self) -> dict[str, dict[str, float]]:
        """
        Get confidence statistics for train and val splits.

        Returns:
            Dictionary with confidence statistics (mean, min, max).
            Format: {
                "train": {"mean": 0.85, "min": 0.6, "max": 1.0},
                "val": {"mean": 0.82, "min": 0.6, "max": 0.95}
            }

        Example:
            >>> stats = dataset.get_confidence_stats()
            >>> stats["train"]["mean"]
            0.85
        """
        train_confidences = [self.samples[i].confidence for i in self.train_indices]
        val_confidences = [self.samples[i].confidence for i in self.val_indices]

        def compute_stats(confidences: list[float]) -> dict[str, float]:
            if not confidences:
                return {"mean": 0.0, "min": 0.0, "max": 0.0}
            return {
                "mean": sum(confidences) / len(confidences),
                "min": min(confidences),
                "max": max(confidences),
            }

        return {"train": compute_stats(train_confidences), "val": compute_stats(val_confidences)}
