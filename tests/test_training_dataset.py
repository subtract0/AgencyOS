"""
Tests for TrainingDataset model (Leap 5 - ML training data).

Constitutional compliance:
- Article I: Complete context (all samples validated before training)
- Article II: 100% verification (strict typing, comprehensive validators)
- Article IV: VectorStore integration (samples from quality feedback)
- Article V: Spec-driven (traceability to spec-005)

Tests cover:
1. TrainingSample creation and validation
2. DatasetMetadata creation and validation
3. TrainingDataset creation and validation
4. Utility methods (get_train_samples, get_val_samples, etc.)
5. Edge cases (empty datasets, invalid splits, etc.)
6. JSON serialization/deserialization

Author: ChiefArchitectAgent
Date: 2025-10-10
"""

import json
from datetime import datetime

import pytest

from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import (
    DatasetMetadata,
    TrainingDataset,
    TrainingSample,
)


@pytest.fixture
def valid_features() -> TaskFeatureVector:
    """Create valid TaskFeatureVector for testing."""
    return TaskFeatureVector(
        embedding=[0.023] * 1536,
        tfidf_features=[0.12] * 100,
        description_length=120,
        word_count=20,
        has_refactor_keyword=1,
        has_test_keyword=0,
        has_async_keyword=1,
        has_fix_keyword=0,
        estimated_time_seconds=300.0,
        historical_tier_mode=2,
    )


@pytest.fixture
def valid_sample(valid_features: TaskFeatureVector) -> TrainingSample:
    """Create valid TrainingSample for testing."""
    return TrainingSample(
        features=valid_features,
        label=2,
        confidence=0.85,
        source="vectorstore",
        task_id="task_001",
        timestamp=datetime.now(),
    )


@pytest.fixture
def valid_metadata() -> DatasetMetadata:
    """Create valid DatasetMetadata for testing."""
    return DatasetMetadata(
        total_samples=10,
        train_count=8,
        val_count=2,
        label_distribution={1: 3, 2: 4, 3: 3},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.6,
        source="vectorstore_quality_feedback",
    )


@pytest.fixture
def valid_dataset(
    valid_features: TaskFeatureVector, valid_metadata: DatasetMetadata
) -> TrainingDataset:
    """Create valid TrainingDataset for testing."""
    samples = []
    for i in range(10):
        samples.append(
            TrainingSample(
                features=valid_features,
                label=(i % 3) + 1,  # Cycle through 1, 2, 3
                confidence=0.85,
                source="vectorstore",
                task_id=f"task_{i:03d}",
                timestamp=datetime.now(),
            )
        )

    return TrainingDataset(
        samples=samples,
        train_indices=[0, 1, 2, 3, 4, 5, 6, 7],
        val_indices=[8, 9],
        metadata=valid_metadata,
    )


# TrainingSample Tests


def test_training_sample_valid_creation(valid_sample: TrainingSample) -> None:
    """Test creating a valid TrainingSample."""
    assert valid_sample.label == 2
    assert valid_sample.confidence == 0.85
    assert valid_sample.source == "vectorstore"
    assert valid_sample.task_id == "task_001"


def test_training_sample_label_validation_tier_1(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with label=1 (simple)."""
    sample = TrainingSample(
        features=valid_features,
        label=1,
        confidence=0.9,
        source="vectorstore",
        task_id="task_simple",
        timestamp=datetime.now(),
    )
    assert sample.label == 1


def test_training_sample_label_validation_tier_3(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with label=3 (complex)."""
    sample = TrainingSample(
        features=valid_features,
        label=3,
        confidence=0.9,
        source="vectorstore",
        task_id="task_complex",
        timestamp=datetime.now(),
    )
    assert sample.label == 3


def test_training_sample_invalid_label_0(valid_features: TaskFeatureVector) -> None:
    """Test TrainingSample rejects label=0 (Article II: strict validation)."""
    with pytest.raises(ValueError, match="Label must be 1.*2.*or 3"):
        TrainingSample(
            features=valid_features,
            label=0,  # Invalid: 0-indexed labels not allowed
            confidence=0.85,
            source="vectorstore",
            task_id="task_001",
            timestamp=datetime.now(),
        )


def test_training_sample_invalid_label_4(valid_features: TaskFeatureVector) -> None:
    """Test TrainingSample rejects label=4 (Article II: strict validation)."""
    with pytest.raises(ValueError, match="Label must be 1.*2.*or 3"):
        TrainingSample(
            features=valid_features,
            label=4,  # Invalid: only 1, 2, 3 allowed
            confidence=0.85,
            source="vectorstore",
            task_id="task_001",
            timestamp=datetime.now(),
        )


def test_training_sample_confidence_boundary_0(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with confidence=0.0 (boundary)."""
    sample = TrainingSample(
        features=valid_features,
        label=2,
        confidence=0.0,
        source="vectorstore",
        task_id="task_low_conf",
        timestamp=datetime.now(),
    )
    assert sample.confidence == 0.0


def test_training_sample_confidence_boundary_1(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with confidence=1.0 (boundary)."""
    sample = TrainingSample(
        features=valid_features,
        label=2,
        confidence=1.0,
        source="manual_label",
        task_id="task_high_conf",
        timestamp=datetime.now(),
    )
    assert sample.confidence == 1.0


def test_training_sample_invalid_confidence_negative(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample rejects negative confidence (Article II)."""
    with pytest.raises(Exception, match="greater than or equal to 0"):
        TrainingSample(
            features=valid_features,
            label=2,
            confidence=-0.1,  # Invalid: negative
            source="vectorstore",
            task_id="task_001",
            timestamp=datetime.now(),
        )


def test_training_sample_invalid_confidence_over_1(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample rejects confidence > 1.0 (Article II)."""
    with pytest.raises(Exception, match="less than or equal to 1"):
        TrainingSample(
            features=valid_features,
            label=2,
            confidence=1.5,  # Invalid: > 1.0
            source="vectorstore",
            task_id="task_001",
            timestamp=datetime.now(),
        )


def test_training_sample_valid_source_vectorstore(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with source='vectorstore'."""
    sample = TrainingSample(
        features=valid_features,
        label=2,
        confidence=0.85,
        source="vectorstore",
        task_id="task_001",
        timestamp=datetime.now(),
    )
    assert sample.source == "vectorstore"


def test_training_sample_valid_source_manual(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingSample with source='manual_label'."""
    sample = TrainingSample(
        features=valid_features,
        label=2,
        confidence=0.85,
        source="manual_label",
        task_id="task_001",
        timestamp=datetime.now(),
    )
    assert sample.source == "manual_label"


def test_training_sample_invalid_source(valid_features: TaskFeatureVector) -> None:
    """Test TrainingSample rejects invalid source (Article IV)."""
    with pytest.raises(ValueError, match="Source must be one of"):
        TrainingSample(
            features=valid_features,
            label=2,
            confidence=0.85,
            source="unknown_source",  # Invalid: not vectorstore or manual_label
            task_id="task_001",
            timestamp=datetime.now(),
        )


# DatasetMetadata Tests


def test_dataset_metadata_valid_creation(valid_metadata: DatasetMetadata) -> None:
    """Test creating valid DatasetMetadata."""
    assert valid_metadata.total_samples == 10
    assert valid_metadata.train_count == 8
    assert valid_metadata.val_count == 2
    assert valid_metadata.version == "v1.0"


def test_dataset_metadata_split_sum_validation_valid() -> None:
    """Test DatasetMetadata accepts valid train + val = total."""
    metadata = DatasetMetadata(
        total_samples=100,
        train_count=80,
        val_count=20,  # Valid: 80 + 20 = 100
        label_distribution={1: 30, 2: 40, 3: 30},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.6,
        source="vectorstore_quality_feedback",
    )
    assert metadata.total_samples == 100


def test_dataset_metadata_split_sum_validation_invalid() -> None:
    """Test DatasetMetadata rejects train + val != total (Article I)."""
    with pytest.raises(ValueError, match="must equal total_samples"):
        DatasetMetadata(
            total_samples=100,
            train_count=80,
            val_count=30,  # Invalid: 80 + 30 = 110 != 100
            label_distribution={1: 30, 2: 40, 3: 30},
            created_at=datetime.now(),
            version="v1.0",
            min_confidence=0.6,
            source="vectorstore_quality_feedback",
        )


def test_dataset_metadata_negative_count_total() -> None:
    """Test DatasetMetadata rejects negative total_samples (Article II)."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        DatasetMetadata(
            total_samples=-10,  # Invalid: negative
            train_count=8,
            val_count=2,
            label_distribution={1: 3, 2: 4, 3: 3},
            created_at=datetime.now(),
            version="v1.0",
            min_confidence=0.6,
            source="vectorstore_quality_feedback",
        )


def test_dataset_metadata_negative_count_train() -> None:
    """Test DatasetMetadata rejects negative train_count (Article II)."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        DatasetMetadata(
            total_samples=10,
            train_count=-8,  # Invalid: negative
            val_count=18,
            label_distribution={1: 3, 2: 4, 3: 3},
            created_at=datetime.now(),
            version="v1.0",
            min_confidence=0.6,
            source="vectorstore_quality_feedback",
        )


def test_dataset_metadata_invalid_label_distribution_key() -> None:
    """Test DatasetMetadata rejects invalid label keys (Article II)."""
    with pytest.raises(ValueError, match="invalid labels"):
        DatasetMetadata(
            total_samples=10,
            train_count=8,
            val_count=2,
            label_distribution={
                0: 3,
                2: 4,
                3: 3,
            },  # Invalid: 0 not allowed (must be 1, 2, 3)
            created_at=datetime.now(),
            version="v1.0",
            min_confidence=0.6,
            source="vectorstore_quality_feedback",
        )


# TrainingDataset Tests


def test_training_dataset_valid_creation(valid_dataset: TrainingDataset) -> None:
    """Test creating valid TrainingDataset."""
    assert len(valid_dataset.samples) == 10
    assert len(valid_dataset.train_indices) == 8
    assert len(valid_dataset.val_indices) == 2


def test_training_dataset_get_train_samples(valid_dataset: TrainingDataset) -> None:
    """Test get_train_samples() utility method."""
    train_samples = valid_dataset.get_train_samples()
    assert len(train_samples) == 8
    assert all(isinstance(s, TrainingSample) for s in train_samples)


def test_training_dataset_get_val_samples(valid_dataset: TrainingDataset) -> None:
    """Test get_val_samples() utility method."""
    val_samples = valid_dataset.get_val_samples()
    assert len(val_samples) == 2
    assert all(isinstance(s, TrainingSample) for s in val_samples)


def test_training_dataset_get_label_distribution(
    valid_dataset: TrainingDataset,
) -> None:
    """Test get_label_distribution() utility method."""
    distribution = valid_dataset.get_label_distribution()
    assert "train" in distribution
    assert "val" in distribution
    assert set(distribution["train"].keys()) == {1, 2, 3}
    assert set(distribution["val"].keys()) == {1, 2, 3}


def test_training_dataset_get_confidence_stats(valid_dataset: TrainingDataset) -> None:
    """Test get_confidence_stats() utility method."""
    stats = valid_dataset.get_confidence_stats()
    assert "train" in stats
    assert "val" in stats
    assert "mean" in stats["train"]
    assert "min" in stats["train"]
    assert "max" in stats["train"]
    assert stats["train"]["mean"] == 0.85


def test_training_dataset_overlapping_indices(
    valid_features: TaskFeatureVector, valid_metadata: DatasetMetadata
) -> None:
    """Test TrainingDataset rejects overlapping train/val indices (Article II)."""
    samples = [
        TrainingSample(
            features=valid_features,
            label=(i % 3) + 1,
            confidence=0.85,
            source="vectorstore",
            task_id=f"task_{i:03d}",
            timestamp=datetime.now(),
        )
        for i in range(10)
    ]

    with pytest.raises(ValueError, match="must not overlap"):
        TrainingDataset(
            samples=samples,
            train_indices=[0, 1, 2, 3, 4, 5, 6, 7, 8],
            val_indices=[8, 9],  # Invalid: 8 overlaps with train
            metadata=valid_metadata,
        )


def test_training_dataset_invalid_train_index(
    valid_features: TaskFeatureVector, valid_metadata: DatasetMetadata
) -> None:
    """Test TrainingDataset rejects invalid train indices (Article I)."""
    samples = [
        TrainingSample(
            features=valid_features,
            label=(i % 3) + 1,
            confidence=0.85,
            source="vectorstore",
            task_id=f"task_{i:03d}",
            timestamp=datetime.now(),
        )
        for i in range(10)
    ]

    with pytest.raises(ValueError, match="train_indices contains.*invalid"):
        TrainingDataset(
            samples=samples,
            train_indices=[0, 1, 2, 3, 4, 5, 6, 15],  # Invalid: 15 out of range
            val_indices=[8, 9],
            metadata=valid_metadata,
        )


def test_training_dataset_invalid_val_index(
    valid_features: TaskFeatureVector, valid_metadata: DatasetMetadata
) -> None:
    """Test TrainingDataset rejects invalid val indices (Article I)."""
    samples = [
        TrainingSample(
            features=valid_features,
            label=(i % 3) + 1,
            confidence=0.85,
            source="vectorstore",
            task_id=f"task_{i:03d}",
            timestamp=datetime.now(),
        )
        for i in range(10)
    ]

    with pytest.raises(ValueError, match="val_indices contains.*invalid"):
        TrainingDataset(
            samples=samples,
            train_indices=[0, 1, 2, 3, 4, 5, 6, 7],
            val_indices=[8, 20],  # Invalid: 20 out of range
            metadata=valid_metadata,
        )


def test_training_dataset_incomplete_coverage(
    valid_features: TaskFeatureVector, valid_metadata: DatasetMetadata
) -> None:
    """Test TrainingDataset rejects incomplete sample coverage (Article I)."""
    samples = [
        TrainingSample(
            features=valid_features,
            label=(i % 3) + 1,
            confidence=0.85,
            source="vectorstore",
            task_id=f"task_{i:03d}",
            timestamp=datetime.now(),
        )
        for i in range(10)
    ]

    with pytest.raises(ValueError, match="must equal total samples"):
        TrainingDataset(
            samples=samples,
            train_indices=[0, 1, 2, 3, 4, 5, 6],  # Missing samples 7, 8, 9
            val_indices=[],
            metadata=valid_metadata,
        )


def test_training_dataset_json_serialization(valid_dataset: TrainingDataset) -> None:
    """Test JSON serialization/deserialization (Article II)."""
    # Serialize
    json_str = valid_dataset.model_dump_json()
    assert isinstance(json_str, str)
    assert len(json_str) > 0

    # Parse
    parsed = json.loads(json_str)
    assert "samples" in parsed
    assert "train_indices" in parsed
    assert "val_indices" in parsed
    assert "metadata" in parsed

    # Deserialize
    deserialized = TrainingDataset.model_validate_json(json_str)
    assert len(deserialized.samples) == len(valid_dataset.samples)
    assert deserialized.train_indices == valid_dataset.train_indices
    assert deserialized.val_indices == valid_dataset.val_indices


def test_training_dataset_empty_val_set(
    valid_features: TaskFeatureVector,
) -> None:
    """Test TrainingDataset with empty validation set (edge case)."""
    samples = [
        TrainingSample(
            features=valid_features,
            label=(i % 3) + 1,
            confidence=0.85,
            source="vectorstore",
            task_id=f"task_{i:03d}",
            timestamp=datetime.now(),
        )
        for i in range(10)
    ]

    metadata = DatasetMetadata(
        total_samples=10,
        train_count=10,
        val_count=0,  # No validation samples
        label_distribution={1: 3, 2: 4, 3: 3},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.6,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(
        samples=samples, train_indices=list(range(10)), val_indices=[], metadata=metadata
    )

    assert len(dataset.get_val_samples()) == 0
    assert dataset.get_confidence_stats()["val"]["mean"] == 0.0


def test_training_dataset_confidence_stats_empty() -> None:
    """Test get_confidence_stats() with empty dataset."""
    samples: list[TrainingSample] = []

    metadata = DatasetMetadata(
        total_samples=0,
        train_count=0,
        val_count=0,
        label_distribution={1: 0, 2: 0, 3: 0},
        created_at=datetime.now(),
        version="v1.0",
        min_confidence=0.6,
        source="vectorstore_quality_feedback",
    )

    dataset = TrainingDataset(samples=samples, train_indices=[], val_indices=[], metadata=metadata)

    stats = dataset.get_confidence_stats()
    assert stats["train"]["mean"] == 0.0
    assert stats["val"]["mean"] == 0.0
