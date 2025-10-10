"""
Comprehensive TDD tests for TrainingDataMerger with NECESSARY pattern.

Tests incremental learning workflow: VectorStore queries, deduplication,
class balancing, train/val splitting, and version management.

Constitutional Compliance:
- Article I: Complete context (all samples validated before merge)
- Article II: 100% verification (Result pattern, strict typing)
- Article IV: VectorStore integration (query/merge predictions)
- Law #1: TDD - tests written BEFORE implementation
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: AAA pattern (Arrange, Act, Assert)

Coverage Target: >95% for tools/ml_routing/training_data_merger.py

Test Categories (NECESSARY Pattern):
- N: Normal operation (happy path merge)
- E: Edge cases (empty VectorStore, insufficient samples)
- C: Corner cases (duplicate task_ids, label conflicts)
- E: Error conditions (invalid tiers, balancing failures)
- S: Security (data integrity validation)
- S: Stress tests (large dataset merges)
- A: Accessibility (clear error messages)
- R: Regression (version increments, metadata updates)
- Y: Yield tests (output validation, Result pattern)

Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.3
Author: TestGeneratorAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from agency_memory import Memory
from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import (
    DatasetMetadata,
    TrainingDataset,
    TrainingSample,
)
from shared.type_definitions.result import Err, Ok
from tools.ml_routing.feature_extractor import FeatureExtractor
from tools.ml_routing.training_data_merger import TrainingDataMerger


# ============================================================================
# FIXTURES (AAA Pattern - Arrange)
# ============================================================================


@pytest.fixture
def mock_context():
    """
    Create AgentContext with mock VectorStore.

    Returns:
        AgentContext: Configured context for testing
    """
    return AgentContext(memory=Memory(), session_id="test_merger_session")


@pytest.fixture
def mock_feature_extractor():
    """
    Mock FeatureExtractor for testing (no OpenAI API calls).

    Returns:
        Mock: Configured FeatureExtractor mock
    """
    extractor = Mock(spec=FeatureExtractor)

    # Mock extract_features to return valid TaskFeatureVector
    def mock_extract(task_description: str):
        from shared.type_definitions.result import Ok

        features = TaskFeatureVector(
            embedding=[0.1] * 1536,
            tfidf_features=[0.05] * 100,
            description_length=len(task_description),
            word_count=len(task_description.split()),
            has_refactor_keyword=1 if "refactor" in task_description.lower() else 0,
            has_test_keyword=1 if "test" in task_description.lower() else 0,
            has_async_keyword=1 if "async" in task_description.lower() else 0,
            has_fix_keyword=1 if "fix" in task_description.lower() else 0,
            estimated_time_seconds=300.0,
            historical_tier_mode=2,
        )
        return Ok(features)

    extractor.extract_features.side_effect = mock_extract
    return extractor


@pytest.fixture
def sample_existing_dataset():
    """
    Create sample existing training dataset (500 samples).

    Returns:
        TrainingDataset: Sample dataset for merge testing
    """
    # Create 500 samples (balanced: 166 P3, 167 P2, 167 P1)
    samples = []
    base_time = datetime.now(UTC)

    for i in range(500):
        label = (i % 3) + 1  # 1, 2, 3 (P3, P2, P1)
        # historical_tier_mode is 0-indexed: 0=P3, 1=P2, 2=P1
        historical_tier = label - 1  # Convert 1,2,3 → 0,1,2

        features = TaskFeatureVector(
            embedding=[0.1] * 1536,
            tfidf_features=[0.05] * 100,
            description_length=100,
            word_count=20,
            has_refactor_keyword=0,
            has_test_keyword=0,
            has_async_keyword=0,
            has_fix_keyword=0,
            estimated_time_seconds=300.0,
            historical_tier_mode=historical_tier,
        )

        sample = TrainingSample(
            features=features,
            label=label,
            confidence=0.85,
            source="manual_label",
            task_id=f"existing_task_{i}",
            timestamp=base_time - timedelta(days=30),
        )
        samples.append(sample)

    # 80/20 split: 400 train, 100 val
    train_indices = list(range(400))
    val_indices = list(range(400, 500))

    metadata = DatasetMetadata(
        total_samples=500,
        train_count=400,
        val_count=100,
        label_distribution={1: 166, 2: 167, 3: 167},
        created_at=base_time - timedelta(days=30),
        version="v1.0",
        min_confidence=0.6,
        source="manual_label",
    )

    return TrainingDataset(
        samples=samples,
        train_indices=train_indices,
        val_indices=val_indices,
        metadata=metadata,
    )


@pytest.fixture
def sample_predictions():
    """
    Create sample VectorStore predictions (100 new samples).

    Returns:
        list[PredictionLog]: Sample predictions with actual_tier
    """
    predictions = []
    base_time = datetime.now(UTC)

    for i in range(100):
        tier_map = {0: "P3", 1: "P2", 2: "P1"}
        tier = tier_map[i % 3]

        prediction = PredictionLog(
            task_id=f"new_task_{i}",
            predicted_tier=tier,
            actual_tier=tier,  # Ground truth available
            confidence=0.85,
            timestamp=base_time - timedelta(days=2),
            method="ml",
        )
        predictions.append(prediction)

    return predictions


# ============================================================================
# Test Category 1: query_predictions() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestQueryPredictionsNormalOperation:
    """Test query_predictions() retrieves predictions from VectorStore."""

    def test_query_predictions_success(self, mock_context, mock_feature_extractor):
        """
        Test AC-1: query_predictions() retrieves predictions from VectorStore.

        Article IV: VectorStore integration (cross-session learning).
        NECESSARY: N (Normal operation - happy path).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Store predictions in VectorStore
        base_time = datetime.now(UTC)
        for i in range(10):
            prediction = PredictionLog(
                task_id=f"task_{i}",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=base_time - timedelta(days=1),
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_task_{i}",
                content=prediction.to_dict(),
                tags=["prediction"],
            )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Result is Ok
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"

        # Assert: 10 predictions retrieved
        predictions = result.unwrap()
        assert len(predictions) == 10
        assert all(isinstance(p, PredictionLog) for p in predictions)

    def test_query_predictions_filters_by_timestamp(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-2: query_predictions() filters by timestamp (days_back).

        Article I: Complete context (time window filtering).
        NECESSARY: N (Normal operation - timestamp filter).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        base_time = datetime.now(UTC)

        # Store old predictions (outside time window)
        for i in range(5):
            old_prediction = PredictionLog(
                task_id=f"old_task_{i}",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=base_time - timedelta(days=10),  # 10 days old
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_old_task_{i}",
                content=old_prediction.to_dict(),
                tags=["prediction"],
            )

        # Store recent predictions (within time window)
        for i in range(3):
            recent_prediction = PredictionLog(
                task_id=f"recent_task_{i}",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=base_time - timedelta(days=2),  # 2 days old
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_recent_task_{i}",
                content=recent_prediction.to_dict(),
                tags=["prediction"],
            )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Only recent predictions retrieved (3 samples, not 8)
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 3
        assert all("recent" in p.task_id for p in predictions)

    def test_query_predictions_filters_by_confidence(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-3: query_predictions() filters by min_confidence.

        Article II: 100% verification (confidence threshold).
        NECESSARY: N (Normal operation - confidence filter).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        base_time = datetime.now(UTC)

        # Store low-confidence predictions
        for i in range(5):
            low_conf = PredictionLog(
                task_id=f"low_conf_task_{i}",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.5,  # Below threshold
                timestamp=base_time - timedelta(days=1),
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_low_conf_task_{i}",
                content=low_conf.to_dict(),
                tags=["prediction"],
            )

        # Store high-confidence predictions
        for i in range(7):
            high_conf = PredictionLog(
                task_id=f"high_conf_task_{i}",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.9,  # Above threshold
                timestamp=base_time - timedelta(days=1),
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_high_conf_task_{i}",
                content=high_conf.to_dict(),
                tags=["prediction"],
            )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Only high-confidence predictions retrieved (7, not 12)
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 7
        assert all(p.confidence >= 0.8 for p in predictions)


# ============================================================================
# Test Category 2: convert_predictions_to_samples() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestConvertPredictionsToSamplesNormalOperation:
    """Test convert_predictions_to_samples() converts predictions to TrainingSample."""

    def test_convert_predictions_success(self, mock_context, mock_feature_extractor):
        """
        Test AC-4: convert_predictions_to_samples() converts PredictionLog to TrainingSample.

        Article II: Result pattern, strict typing.
        NECESSARY: N (Normal operation - happy path conversion).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        predictions = [
            PredictionLog(
                task_id="task_123",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=datetime.now(UTC),
                method="ml",
            ),
            PredictionLog(
                task_id="task_456",
                predicted_tier="P1",
                actual_tier="P1",
                confidence=0.92,
                timestamp=datetime.now(UTC),
                method="ml",
            ),
        ]

        # Act
        result = merger.convert_predictions_to_samples(predictions)

        # Assert: Result is Ok
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"

        # Assert: 2 samples converted
        samples = result.unwrap()
        assert len(samples) == 2
        assert all(isinstance(s, TrainingSample) for s in samples)

        # Assert: Labels correct (P2→2, P1→3)
        assert samples[0].label == 2
        assert samples[1].label == 3

    def test_convert_predictions_re_extracts_features(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-5: convert_predictions_to_samples() re-extracts features.

        Article IV: Feature extraction from task descriptions.
        NECESSARY: N (Normal operation - feature extraction).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        predictions = [
            PredictionLog(
                task_id="refactor authentication module",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=datetime.now(UTC),
                method="ml",
            ),
        ]

        # Act
        result = merger.convert_predictions_to_samples(predictions)

        # Assert: Features extracted
        assert result.is_ok()
        samples = result.unwrap()

        # Assert: FeatureExtractor called with task_id (used as proxy for description)
        mock_feature_extractor.extract_features.assert_called_once_with(
            task_description="refactor authentication module"
        )

        # Assert: Features populated
        sample = samples[0]
        assert len(sample.features.embedding) == 1536
        assert len(sample.features.tfidf_features) == 100


# ============================================================================
# Test Category 3: merge_datasets() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestMergeDatasetsNormalOperation:
    """Test merge_datasets() merges existing dataset with new predictions."""

    def test_merge_datasets_success(
        self,
        mock_context,
        mock_feature_extractor,
        sample_existing_dataset,
        sample_predictions,
    ):
        """
        Test AC-6: merge_datasets() merges existing + new samples.

        Article I: Complete validation before merge.
        NECESSARY: N (Normal operation - happy path merge).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act
        result = merger.merge_datasets(
            existing_dataset=sample_existing_dataset,
            new_predictions=sample_predictions,
            version_increment="minor",
        )

        # Assert: Result is Ok
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err()}"

        # Assert: Merged dataset has more samples
        merged = result.unwrap()
        assert merged.metadata.total_samples > 500
        assert merged.metadata.version == "v1.1"

    def test_merge_datasets_increments_version(
        self,
        mock_context,
        mock_feature_extractor,
        sample_existing_dataset,
        sample_predictions,
    ):
        """
        Test AC-7: merge_datasets() increments version correctly.

        Article V: Spec-driven (version management).
        NECESSARY: R (Regression - version increments).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act: Minor increment
        result_minor = merger.merge_datasets(
            existing_dataset=sample_existing_dataset,
            new_predictions=sample_predictions,
            version_increment="minor",
        )

        # Assert: v1.0 → v1.1
        assert result_minor.is_ok()
        assert result_minor.unwrap().metadata.version == "v1.1"

        # Arrange: Change existing version to v1.9
        sample_existing_dataset.metadata.version = "v1.9"

        # Act: Major increment
        result_major = merger.merge_datasets(
            existing_dataset=sample_existing_dataset,
            new_predictions=sample_predictions,
            version_increment="major",
        )

        # Assert: v1.9 → v2.0
        assert result_major.is_ok()
        assert result_major.unwrap().metadata.version == "v2.0"


# ============================================================================
# Test Category 4: _deduplicate_samples() - Corner Cases (NECESSARY: C)
# ============================================================================


class TestDeduplicateSamplesCornerCases:
    """Test _deduplicate_samples() handles duplicates correctly."""

    def test_deduplicate_removes_duplicates_keeps_latest(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-8: _deduplicate_samples() removes duplicates, keeps latest by timestamp.

        Article I: Complete context (deduplication by task hash).
        NECESSARY: C (Corner case - duplicate task_ids).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        base_time = datetime.now(UTC)

        # Create samples with duplicate task_ids (same task_id, different timestamps)
        samples = [
            TrainingSample(
                features=TaskFeatureVector(
                    embedding=[0.1] * 1536,
                    tfidf_features=[0.05] * 100,
                    description_length=100,
                    word_count=20,
                    has_refactor_keyword=0,
                    has_test_keyword=0,
                    has_async_keyword=0,
                    has_fix_keyword=0,
                    estimated_time_seconds=300.0,
                    historical_tier_mode=2,
                ),
                label=2,
                confidence=0.7,
                source="vectorstore",
                task_id="duplicate_task",
                timestamp=base_time - timedelta(days=3),  # Older
            ),
            TrainingSample(
                features=TaskFeatureVector(
                    embedding=[0.2] * 1536,
                    tfidf_features=[0.1] * 100,
                    description_length=100,
                    word_count=20,
                    has_refactor_keyword=0,
                    has_test_keyword=0,
                    has_async_keyword=0,
                    has_fix_keyword=0,
                    estimated_time_seconds=300.0,
                    historical_tier_mode=2,
                ),
                label=2,
                confidence=0.9,
                source="vectorstore",
                task_id="duplicate_task",
                timestamp=base_time - timedelta(days=1),  # Newer (should keep this)
            ),
            TrainingSample(
                features=TaskFeatureVector(
                    embedding=[0.3] * 1536,
                    tfidf_features=[0.15] * 100,
                    description_length=100,
                    word_count=20,
                    has_refactor_keyword=0,
                    has_test_keyword=0,
                    has_async_keyword=0,
                    has_fix_keyword=0,
                    estimated_time_seconds=300.0,
                    historical_tier_mode=1,
                ),
                label=1,
                confidence=0.85,
                source="vectorstore",
                task_id="unique_task",
                timestamp=base_time - timedelta(days=2),
            ),
        ]

        # Act
        deduped = merger._deduplicate_samples(samples)

        # Assert: 2 unique samples (1 duplicate removed)
        assert len(deduped) == 2

        # Assert: Kept latest duplicate (confidence 0.9, not 0.7)
        duplicate_sample = next(s for s in deduped if s.task_id == "duplicate_task")
        assert duplicate_sample.confidence == 0.9
        assert duplicate_sample.timestamp == base_time - timedelta(days=1)


# ============================================================================
# Test Category 5: _balance_classes() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestBalanceClassesNormalOperation:
    """Test _balance_classes() undersamples majority tier."""

    def test_balance_classes_undersamples_majority(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-9: _balance_classes() undersamples majority tier to ±10%.

        Article II: 100% verification (class balance).
        NECESSARY: N (Normal operation - class balancing).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Create imbalanced dataset: 80% P3, 10% P2, 10% P1
        samples = []
        base_time = datetime.now(UTC)

        for i in range(80):  # P3 majority
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=0,  # 0=P3 (simple)
                    ),
                    label=1,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p3_task_{i}",
                    timestamp=base_time,
                )
            )

        for i in range(10):  # P2 minority
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=1,  # 1=P2 (moderate)
                    ),
                    label=2,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p2_task_{i}",
                    timestamp=base_time,
                )
            )

        for i in range(10):  # P1 minority
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=2,  # 2=P1 (complex)
                    ),
                    label=3,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p1_task_{i}",
                    timestamp=base_time,
                )
            )

        # Act
        balanced = merger._balance_classes(samples)

        # Assert: Balanced samples (~11 per tier: min 10 * 1.1)
        label_counts = {1: 0, 2: 0, 3: 0}
        for sample in balanced:
            label_counts[sample.label] += 1

        # Assert: P3 undersampled from 80 to ~11
        assert label_counts[1] <= 11  # Target: 10 * 1.1 = 11

        # Assert: P2 and P1 unchanged (already at minority count)
        assert label_counts[2] == 10
        assert label_counts[3] == 10


# ============================================================================
# Test Category 6: _validate_class_balance() - Error Conditions (NECESSARY: E)
# ============================================================================


class TestValidateClassBalanceErrorConditions:
    """Test _validate_class_balance() detects imbalance."""

    def test_validate_class_balance_fails_for_imbalance(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-10: _validate_class_balance() returns Err for imbalance >10%.

        Article II: 100% verification before training.
        NECESSARY: E (Error condition - class imbalance).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Create imbalanced samples: 50 P3, 10 P2, 10 P1 (imbalance ratio = 400%)
        samples = []
        base_time = datetime.now(UTC)

        for i in range(50):
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=0,  # 0=P3 (simple)
                    ),
                    label=1,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p3_task_{i}",
                    timestamp=base_time,
                )
            )

        for i in range(10):
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=1,  # 1=P2 (moderate)
                    ),
                    label=2,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p2_task_{i}",
                    timestamp=base_time,
                )
            )

        for i in range(10):
            samples.append(
                TrainingSample(
                    features=TaskFeatureVector(
                        embedding=[0.1] * 1536,
                        tfidf_features=[0.05] * 100,
                        description_length=100,
                        word_count=20,
                        has_refactor_keyword=0,
                        has_test_keyword=0,
                        has_async_keyword=0,
                        has_fix_keyword=0,
                        estimated_time_seconds=300.0,
                        historical_tier_mode=2,  # 2=P1 (complex)
                    ),
                    label=3,
                    confidence=0.85,
                    source="vectorstore",
                    task_id=f"p1_task_{i}",
                    timestamp=base_time,
                )
            )

        # Act
        result = merger._validate_class_balance(samples)

        # Assert: Result is Err
        assert result.is_err(), "Expected Err for imbalanced classes"

        # Assert: Error message contains "imbalance"
        error_msg = result.unwrap_err()
        assert "imbalance" in error_msg.lower()


# ============================================================================
# Test Category 7: _stratified_split() - Normal Operation (NECESSARY: N)
# ============================================================================


class TestStratifiedSplitNormalOperation:
    """Test _stratified_split() creates stratified train/val splits."""

    def test_stratified_split_preserves_class_distribution(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-11: _stratified_split() preserves class distribution in train/val.

        Article I: Complete context (stratified split).
        NECESSARY: N (Normal operation - stratified split).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
            train_val_ratio=0.8,
        )

        # Create balanced samples: 100 P3, 100 P2, 100 P1
        samples = []
        base_time = datetime.now(UTC)

        for label in [1, 2, 3]:
            for i in range(100):
                # historical_tier_mode is 0-indexed: 0=P3, 1=P2, 2=P1
                historical_tier = label - 1  # Convert 1,2,3 → 0,1,2
                samples.append(
                    TrainingSample(
                        features=TaskFeatureVector(
                            embedding=[0.1] * 1536,
                            tfidf_features=[0.05] * 100,
                            description_length=100,
                            word_count=20,
                            has_refactor_keyword=0,
                            has_test_keyword=0,
                            has_async_keyword=0,
                            has_fix_keyword=0,
                            estimated_time_seconds=300.0,
                            historical_tier_mode=historical_tier,
                        ),
                        label=label,
                        confidence=0.85,
                        source="vectorstore",
                        task_id=f"p{4-label}_task_{i}",
                        timestamp=base_time,
                    )
                )

        # Act
        train_indices, val_indices = merger._stratified_split(samples, 0.8)

        # Assert: 80/20 split
        assert len(train_indices) == 240  # 300 * 0.8
        assert len(val_indices) == 60  # 300 * 0.2

        # Assert: Class distribution preserved
        train_labels = [samples[i].label for i in train_indices]
        val_labels = [samples[i].label for i in val_indices]

        train_label_counts = {1: train_labels.count(1), 2: train_labels.count(2), 3: train_labels.count(3)}
        val_label_counts = {1: val_labels.count(1), 2: val_labels.count(2), 3: val_labels.count(3)}

        # Assert: Each label has ~80 train samples and ~20 val samples
        for label in [1, 2, 3]:
            assert train_label_counts[label] == 80  # 100 * 0.8
            assert val_label_counts[label] == 20  # 100 * 0.2


# ============================================================================
# Test Category 8: Edge Cases (NECESSARY: E)
# ============================================================================


class TestEdgeCases:
    """Test edge cases: empty VectorStore, insufficient samples, etc."""

    def test_query_predictions_empty_vectorstore(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-12: query_predictions() returns Ok with empty list for empty VectorStore.

        Article IV: VectorStore integration (handle empty state).
        NECESSARY: E (Edge case - empty VectorStore).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act: Query empty VectorStore
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Result is Ok with empty list
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 0

    def test_convert_predictions_no_valid_samples(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-13: convert_predictions_to_samples() returns Err if no valid samples.

        Article II: 100% verification (no empty training data).
        NECESSARY: E (Edge case - all conversions fail).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Mock feature extraction to always fail
        from shared.type_definitions.result import Err

        mock_feature_extractor.extract_features.side_effect = lambda task_description: Err(
            "Feature extraction failed"
        )

        predictions = [
            PredictionLog(
                task_id="task_123",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=datetime.now(UTC),
                method="ml",
            ),
        ]

        # Act
        result = merger.convert_predictions_to_samples(predictions)

        # Assert: Result is Err
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "No valid samples" in error_msg

    def test_query_predictions_filters_missing_actual_tier(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-14: query_predictions() filters predictions without actual_tier.

        Article I: Complete context (only predictions with ground truth).
        NECESSARY: E (Edge case - missing actual_tier).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        base_time = datetime.now(UTC)

        # Store predictions WITHOUT actual_tier
        for i in range(5):
            prediction = PredictionLog(
                task_id=f"task_{i}",
                predicted_tier="P2",
                actual_tier=None,  # Missing ground truth
                confidence=0.85,
                timestamp=base_time - timedelta(days=1),
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_task_{i}",
                content=prediction.to_dict(),
                tags=["prediction"],
            )

        # Store predictions WITH actual_tier
        for i in range(3):
            prediction = PredictionLog(
                task_id=f"task_with_ground_truth_{i}",
                predicted_tier="P2",
                actual_tier="P2",  # Ground truth available
                confidence=0.85,
                timestamp=base_time - timedelta(days=1),
                method="ml",
            )
            mock_context.store_memory(
                key=f"prediction_task_with_ground_truth_{i}",
                content=prediction.to_dict(),
                tags=["prediction"],
            )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Only predictions with actual_tier retrieved (3, not 8)
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 3
        assert all(p.actual_tier is not None for p in predictions)


# ============================================================================
# Test Category 9: Version Increment (NECESSARY: R)
# ============================================================================


class TestVersionIncrement:
    """Test _increment_version() handles semantic versioning."""

    def test_increment_version_minor(self, mock_context, mock_feature_extractor):
        """
        Test AC-15: _increment_version() increments minor version correctly.

        Article V: Spec-driven (version management).
        NECESSARY: R (Regression - version increments).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act
        new_version = merger._increment_version("v1.0", "minor")

        # Assert: v1.0 → v1.1
        assert new_version == "v1.1"

    def test_increment_version_major(self, mock_context, mock_feature_extractor):
        """
        Test AC-16: _increment_version() increments major version correctly.

        Article V: Spec-driven (version management).
        NECESSARY: R (Regression - version increments).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act
        new_version = merger._increment_version("v1.9", "major")

        # Assert: v1.9 → v2.0
        assert new_version == "v2.0"

    def test_increment_version_invalid_format(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-17: _increment_version() raises ValueError for invalid version format.

        Article II: 100% verification (strict validation).
        NECESSARY: E (Error condition - invalid version).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act & Assert: Invalid version format raises ValueError
        with pytest.raises(ValueError, match="Invalid version format"):
            merger._increment_version("v1", "minor")

    def test_increment_version_invalid_increment_type(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-18: _increment_version() raises ValueError for invalid increment_type.

        Article II: 100% verification (strict validation).
        NECESSARY: E (Error condition - invalid increment type).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act & Assert: Invalid increment type raises ValueError
        with pytest.raises(ValueError, match="Invalid increment_type"):
            merger._increment_version("v1.0", "patch")


# ============================================================================
# Test Category 10: Error Handling (NECESSARY: E)
# ============================================================================


class TestErrorHandling:
    """Test error handling for VectorStore failures and invalid data."""

    def test_query_predictions_handles_vectorstore_exception(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-21: query_predictions() returns Err if VectorStore fails.

        Article II: Result pattern for error handling.
        NECESSARY: E (Error condition - VectorStore exception).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Mock search_memories to raise exception
        mock_context.search_memories = Mock(side_effect=Exception("VectorStore error"))

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Result is Err
        assert result.is_err()
        error_msg = result.unwrap_err()
        assert "VectorStore query failed" in error_msg

    def test_query_predictions_filters_invalid_timestamp_format(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-22: query_predictions() filters predictions with invalid timestamp.

        Article I: Complete context (validate timestamps).
        NECESSARY: E (Error condition - invalid timestamp).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Store prediction with invalid timestamp
        prediction = PredictionLog(
            task_id="task_invalid_ts",
            predicted_tier="P2",
            actual_tier="P2",
            confidence=0.85,
            timestamp=datetime.now(UTC) - timedelta(days=1),
            method="ml",
        )
        prediction_dict = prediction.to_dict()
        prediction_dict["timestamp"] = "invalid-timestamp"  # Corrupt timestamp

        mock_context.store_memory(
            key="prediction_invalid_ts",
            content=prediction_dict,
            tags=["prediction"],
        )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Invalid prediction filtered out
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 0

    def test_query_predictions_filters_missing_required_fields(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-23: query_predictions() filters predictions missing required fields.

        Article I: Complete context (validate required fields).
        NECESSARY: E (Error condition - missing fields).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Store incomplete prediction (missing confidence field)
        incomplete_prediction = {
            "task_id": "task_incomplete",
            "predicted_tier": "P2",
            "actual_tier": "P2",
            # Missing "confidence" field
            "timestamp": datetime.now(UTC).isoformat(),
            "method": "ml",
        }

        mock_context.store_memory(
            key="prediction_incomplete",
            content=incomplete_prediction,
            tags=["prediction"],
        )

        # Act
        result = merger.query_predictions(days_back=7, min_confidence=0.8)

        # Assert: Incomplete prediction filtered out
        assert result.is_ok()
        predictions = result.unwrap()
        assert len(predictions) == 0

    def test_convert_predictions_handles_parse_failure(
        self, mock_context, mock_feature_extractor
    ):
        """
        Test AC-24: convert_predictions_to_samples() filters samples that fail parsing.

        Article II: 100% verification (strict validation).
        NECESSARY: E (Error condition - parse failure).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Create prediction with valid tier
        predictions = [
            PredictionLog(
                task_id="task_123",
                predicted_tier="P2",
                actual_tier="P2",
                confidence=0.85,
                timestamp=datetime.now(UTC),
                method="ml",
            ),
        ]

        # Mock _convert_single_prediction to fail
        with patch.object(
            merger,
            "_convert_single_prediction",
            return_value=Err("Parse failed"),
        ):
            # Act
            result = merger.convert_predictions_to_samples(predictions)

            # Assert: Conversion fails (no valid samples)
            assert result.is_err()
            assert "No valid samples" in result.unwrap_err()

    def test_merge_datasets_handles_conversion_failure(
        self,
        mock_context,
        mock_feature_extractor,
        sample_existing_dataset,
        sample_predictions,
    ):
        """
        Test AC-25: merge_datasets() returns Err if conversion fails.

        Article II: Result pattern error handling.
        NECESSARY: E (Error condition - conversion failure).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Mock convert_predictions_to_samples to fail
        with patch.object(
            merger,
            "convert_predictions_to_samples",
            return_value=Err("Conversion failed"),
        ):
            # Act
            result = merger.merge_datasets(
                existing_dataset=sample_existing_dataset,
                new_predictions=sample_predictions,
                version_increment="minor",
            )

            # Assert: Merge fails
            assert result.is_err()
            assert "Conversion failed" in result.unwrap_err()

    def test_merge_datasets_handles_general_exception(
        self,
        mock_context,
        mock_feature_extractor,
        sample_existing_dataset,
        sample_predictions,
    ):
        """
        Test AC-26: merge_datasets() returns Err if unexpected exception occurs.

        Article II: Result pattern error handling.
        NECESSARY: E (Error condition - unexpected exception).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Mock _prepare_merged_samples to raise exception
        with patch.object(
            merger,
            "_prepare_merged_samples",
            side_effect=Exception("Unexpected error"),
        ):
            # Act
            result = merger.merge_datasets(
                existing_dataset=sample_existing_dataset,
                new_predictions=sample_predictions,
                version_increment="minor",
            )

            # Assert: Merge fails with Err
            assert result.is_err()
            assert "Dataset merge failed" in result.unwrap_err()


# ============================================================================
# Test Category 11: Hash Function (NECESSARY: Y)
# ============================================================================


class TestHashFunction:
    """Test _hash_task_id() generates consistent hashes."""

    def test_hash_task_id_consistency(self, mock_context, mock_feature_extractor):
        """
        Test AC-19: _hash_task_id() generates consistent hashes for same input.

        Article II: 100% verification (deterministic hashing).
        NECESSARY: Y (Yield test - output validation).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        task_id = "test_task_123"

        # Act: Hash same task_id twice
        hash1 = merger._hash_task_id(task_id)
        hash2 = merger._hash_task_id(task_id)

        # Assert: Hashes are identical
        assert hash1 == hash2

    def test_hash_task_id_uniqueness(self, mock_context, mock_feature_extractor):
        """
        Test AC-20: _hash_task_id() generates different hashes for different inputs.

        Article II: 100% verification (collision resistance).
        NECESSARY: Y (Yield test - output validation).
        """
        # Arrange
        merger = TrainingDataMerger(
            context=mock_context,
            feature_extractor=mock_feature_extractor,
        )

        # Act: Hash different task_ids
        hash1 = merger._hash_task_id("task_abc")
        hash2 = merger._hash_task_id("task_xyz")

        # Assert: Hashes are different
        assert hash1 != hash2
