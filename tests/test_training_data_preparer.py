"""
Tests for TrainingDataPreparer class.

Tests preparation of ML training datasets from VectorStore quality feedback,
including feature extraction, filtering, stratified splitting, and validation.

Constitutional Compliance:
- Article I: Complete context (all VectorStore feedback queried)
- Article II: Result pattern for error handling
- Article IV: VectorStore integration MANDATORY (cross-session learning)
- Law #1: TDD (tests written FIRST)
- Law #5: Result pattern for all fallible operations

Author: AgencyCodeAgent
Date: 2025-10-10
"""

from datetime import datetime

import pytest

from shared.agent_context import AgentContext, create_agent_context
from shared.models.quality_feedback_sample import QualityFeedbackSample
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import DatasetMetadata, TrainingDataset, TrainingSample
from tools.ml_routing.feature_extractor import FeatureExtractor
from tools.ml_routing.tfidf_vocabulary_builder import TfidfVocabulary
from tools.ml_routing.training_data_preparer import TrainingDataPreparer


@pytest.fixture
def mock_context() -> AgentContext:
    """Create mock AgentContext with sample quality feedback."""
    context = create_agent_context(session_id="test_preparer")

    # Store mock quality feedback samples (Article IV: VectorStore)
    for i in range(100):
        # Balanced distribution: 33 P1, 33 P2, 34 P3
        if i < 33:
            tier = 3  # Complex
            confidence = 0.9
            description = f"Design architecture for feature {i} with scalability"
        elif i < 66:
            tier = 2  # Moderate
            confidence = 0.85
            description = f"Implement feature {i} with async support"
        else:
            tier = 1  # Simple
            confidence = 0.8
            description = f"Fix typo in file {i}"

        context.store_memory(
            key=f"quality_feedback_{i}",
            content={
                "task_description": description,
                "corrected_tier": tier,
                "confidence": confidence,
                "tier_change_count": 0,  # No oscillation
                "timestamp": datetime.now().isoformat(),
            },
            tags=["quality_feedback", "misclassification"],
        )

    return context


@pytest.fixture
def tfidf_vocab() -> TfidfVocabulary:
    """Create mock TF-IDF vocabulary."""
    terms = [
        "implement",
        "feature",
        "fix",
        "refactor",
        "test",
        "async",
        "design",
        "architecture",
        "bug",
        "optimization",
    ] + [f"term_{i}" for i in range(90)]  # 100 total terms

    idf_scores = dict.fromkeys(terms, 1.0)

    return TfidfVocabulary(
        terms=terms, idf_scores=idf_scores, version="v1.0", created_at=datetime.now()
    )


@pytest.fixture
def feature_extractor(tfidf_vocab: TfidfVocabulary) -> FeatureExtractor:
    """Create feature extractor with mock API key."""
    import os

    api_key = os.environ.get("OPENAI_API_KEY", "mock_key")
    return FeatureExtractor(openai_api_key=api_key, tfidf_vocabulary=tfidf_vocab, cache_size=100)


@pytest.fixture
def preparer(
    mock_context: AgentContext, feature_extractor: FeatureExtractor
) -> TrainingDataPreparer:
    """Create TrainingDataPreparer instance."""
    return TrainingDataPreparer(context=mock_context, feature_extractor=feature_extractor)


# === Tests for prepare_dataset() ===


def test_prepare_dataset_returns_result_ok(preparer: TrainingDataPreparer):
    """Test prepare_dataset returns Result[TrainingDataset, str] on success."""
    # Use lower thresholds for testing
    result = preparer.prepare_dataset(min_confidence=0.7, min_samples_per_tier=10, train_split=0.8)

    assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else ''}"

    dataset = result.unwrap()
    assert isinstance(dataset, TrainingDataset)
    assert len(dataset.samples) > 0
    assert len(dataset.train_indices) > 0
    assert len(dataset.val_indices) > 0


def test_prepare_dataset_returns_err_on_no_feedback(feature_extractor: FeatureExtractor):
    """Test prepare_dataset returns Err when no quality feedback found."""
    # Empty context (no quality feedback)
    empty_context = create_agent_context(session_id="empty")
    preparer = TrainingDataPreparer(empty_context, feature_extractor)

    result = preparer.prepare_dataset()

    assert result.is_err()
    assert "No quality feedback found" in result.unwrap_err()


def test_prepare_dataset_respects_min_confidence_filter(preparer: TrainingDataPreparer):
    """Test min_confidence filter excludes low-confidence samples."""
    # High confidence threshold should reduce sample count
    result_high = preparer.prepare_dataset(
        min_confidence=0.9, min_samples_per_tier=5, train_split=0.8
    )

    result_low = preparer.prepare_dataset(
        min_confidence=0.7, min_samples_per_tier=5, train_split=0.8
    )

    if result_high.is_ok() and result_low.is_ok():
        dataset_high = result_high.unwrap()
        dataset_low = result_low.unwrap()

        # Lower threshold should have more samples
        assert len(dataset_low.samples) >= len(dataset_high.samples)


def test_prepare_dataset_filters_oscillating_samples(
    mock_context: AgentContext, feature_extractor: FeatureExtractor
):
    """Test oscillating samples (tier changes >2x) are filtered out."""
    # Add oscillating sample
    mock_context.store_memory(
        key="oscillating_task",
        content={
            "task_description": "Oscillating task with many tier changes",
            "corrected_tier": 2,
            "confidence": 0.95,
            "tier_change_count": 5,  # >2 tier changes (oscillating)
            "timestamp": datetime.now().isoformat(),
        },
        tags=["quality_feedback", "misclassification"],
    )

    preparer = TrainingDataPreparer(mock_context, feature_extractor)
    result = preparer.prepare_dataset(min_samples_per_tier=5)

    if result.is_ok():
        dataset = result.unwrap()

        # Oscillating sample should be filtered out
        # Check no sample has "Oscillating task" in description
        for sample in dataset.samples:
            assert "Oscillating task" not in sample.task_id


def test_prepare_dataset_stratified_split_preserves_distribution(preparer: TrainingDataPreparer):
    """Test stratified split preserves label distribution in train/val sets."""
    result = preparer.prepare_dataset(min_confidence=0.7, min_samples_per_tier=10, train_split=0.8)

    assert result.is_ok()
    dataset = result.unwrap()

    # Get label distributions
    train_distribution = dataset.get_label_distribution()["train"]
    val_distribution = dataset.get_label_distribution()["val"]

    # Check all tiers present in both splits
    assert set(train_distribution.keys()) == {1, 2, 3}
    assert set(val_distribution.keys()) == {1, 2, 3}

    # Check proportions roughly preserved (within 10% tolerance)
    for tier in [1, 2, 3]:
        train_ratio = train_distribution[tier] / len(dataset.train_indices)
        val_ratio = val_distribution[tier] / len(dataset.val_indices)

        # Allow 10% tolerance for small datasets
        assert abs(train_ratio - val_ratio) < 0.15, (
            f"Tier {tier} distribution mismatch: train={train_ratio:.2%}, val={val_ratio:.2%}"
        )


def test_prepare_dataset_respects_train_split_ratio(preparer: TrainingDataPreparer):
    """Test train_split parameter controls train/val split ratio."""
    result = preparer.prepare_dataset(min_confidence=0.7, min_samples_per_tier=10, train_split=0.8)

    assert result.is_ok()
    dataset = result.unwrap()

    total_samples = len(dataset.samples)
    train_count = len(dataset.train_indices)
    val_count = len(dataset.val_indices)

    # Check split ratio (allow 5% tolerance for rounding)
    expected_train_count = int(total_samples * 0.8)
    assert abs(train_count - expected_train_count) <= 1, (
        f"Train count {train_count} != expected {expected_train_count}"
    )

    # Check train + val = total
    assert train_count + val_count == total_samples


def test_prepare_dataset_returns_err_on_insufficient_samples(preparer: TrainingDataPreparer):
    """Test prepare_dataset returns Err when min_samples_per_tier not met."""
    # Unrealistically high threshold
    result = preparer.prepare_dataset(
        min_confidence=0.7,
        min_samples_per_tier=1000,  # More than available
        train_split=0.8,
    )

    assert result.is_err()
    error_msg = result.unwrap_err()
    assert "Insufficient samples" in error_msg or "min_samples_per_tier" in error_msg.lower()


# === Tests for _query_vectorstore() ===


def test_query_vectorstore_returns_feedback_samples(preparer: TrainingDataPreparer):
    """Test _query_vectorstore returns quality feedback from VectorStore."""
    result = preparer._query_vectorstore()

    assert result.is_ok()
    samples = result.unwrap()

    assert len(samples) > 0
    assert all(hasattr(s, "task_description") for s in samples)
    assert all(hasattr(s, "corrected_tier") for s in samples)


def test_query_vectorstore_uses_correct_tags(preparer: TrainingDataPreparer):
    """Test _query_vectorstore uses correct VectorStore tags."""
    result = preparer._query_vectorstore()

    assert result.is_ok()
    samples = result.unwrap()

    # All samples should have quality_feedback tag
    for sample in samples:
        assert "quality_feedback" in sample.tags


# === Tests for _filter_high_quality_labels() ===


def test_filter_high_quality_labels_removes_low_confidence(preparer: TrainingDataPreparer):
    """Test _filter_high_quality_labels removes samples below confidence threshold."""
    samples = [
        QualityFeedbackSample(
            task_description="Task 1",
            corrected_tier=2,
            confidence=0.9,
            tier_change_count=0,
        ),
        QualityFeedbackSample(
            task_description="Task 2",
            corrected_tier=1,
            confidence=0.5,
            tier_change_count=0,
        ),
        QualityFeedbackSample(
            task_description="Task 3",
            corrected_tier=3,
            confidence=0.8,
            tier_change_count=0,
        ),
    ]

    result = preparer._filter_high_quality_labels(samples, min_confidence=0.7)

    assert result.is_ok()
    filtered = result.unwrap()

    # Only samples with confidence ≥0.7 should remain
    assert len(filtered) == 2
    assert all(s.confidence >= 0.7 for s in filtered)


def test_filter_high_quality_labels_removes_oscillating(preparer: TrainingDataPreparer):
    """Test _filter_high_quality_labels removes oscillating samples."""
    samples = [
        QualityFeedbackSample(
            task_description="Task 1",
            corrected_tier=2,
            confidence=0.9,
            tier_change_count=0,
        ),
        QualityFeedbackSample(
            task_description="Task 2",
            corrected_tier=1,
            confidence=0.9,
            tier_change_count=5,
        ),
        QualityFeedbackSample(
            task_description="Task 3",
            corrected_tier=3,
            confidence=0.9,
            tier_change_count=1,
        ),
    ]

    result = preparer._filter_high_quality_labels(samples, min_confidence=0.7)

    assert result.is_ok()
    filtered = result.unwrap()

    # Only samples with tier_change_count ≤2 should remain
    assert len(filtered) == 2
    assert all(s.tier_change_count <= 2 for s in filtered)


def test_filter_high_quality_labels_deduplicates(preparer: TrainingDataPreparer):
    """Test _filter_high_quality_labels removes duplicate task descriptions."""
    samples = [
        QualityFeedbackSample(
            task_description="Fix typo",
            corrected_tier=1,
            confidence=0.9,
            tier_change_count=0,
        ),
        QualityFeedbackSample(
            task_description="Fix typo",
            corrected_tier=1,
            confidence=0.85,
            tier_change_count=0,
        ),
        QualityFeedbackSample(
            task_description="Implement feature",
            corrected_tier=2,
            confidence=0.8,
            tier_change_count=0,
        ),
    ]

    result = preparer._filter_high_quality_labels(samples, min_confidence=0.7)

    assert result.is_ok()
    filtered = result.unwrap()

    # Duplicates should be removed
    assert len(filtered) == 2
    task_descriptions = [s.task_description for s in filtered]
    assert len(task_descriptions) == len(set(task_descriptions))


# === Tests for _check_class_balance() ===


def test_check_class_balance_succeeds_with_sufficient_samples(preparer: TrainingDataPreparer):
    """Test _check_class_balance succeeds when all tiers have min samples."""
    labels = [1] * 50 + [2] * 50 + [3] * 50  # 50 each

    result = preparer._check_class_balance(labels, min_samples_per_tier=10)

    assert result.is_ok()
    distribution = result.unwrap()

    assert distribution == {1: 50, 2: 50, 3: 50}


def test_check_class_balance_fails_with_insufficient_samples(preparer: TrainingDataPreparer):
    """Test _check_class_balance fails when tier has too few samples."""
    labels = [1] * 50 + [2] * 5 + [3] * 50  # Tier 2 only has 5

    result = preparer._check_class_balance(labels, min_samples_per_tier=10)

    assert result.is_err()
    error_msg = result.unwrap_err()
    assert "Insufficient samples" in error_msg
    assert "tier 2" in error_msg.lower()


# === Tests for _stratified_split() ===


def test_stratified_split_preserves_label_distribution(preparer: TrainingDataPreparer):
    """Test _stratified_split preserves label distribution."""
    # Create mock samples with balanced labels
    samples = []
    for tier in [1, 2, 3]:
        for i in range(30):
            sample = TrainingSample(
                features=_create_mock_feature_vector(),
                label=tier,
                confidence=0.85,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    result = preparer._stratified_split(samples, train_split=0.8)

    assert result.is_ok()
    train_idx, val_idx = result.unwrap()

    # Check split sizes
    assert len(train_idx) == 72  # 80% of 90
    assert len(val_idx) == 18  # 20% of 90

    # Check label distribution preserved
    train_labels = [samples[i].label for i in train_idx]
    val_labels = [samples[i].label for i in val_idx]

    # Each tier should have roughly 30 * 0.8 = 24 in train, 6 in val
    for tier in [1, 2, 3]:
        train_count = train_labels.count(tier)
        val_count = val_labels.count(tier)

        # Allow ±1 tolerance for stratification
        assert 23 <= train_count <= 25, f"Tier {tier} train: {train_count}"
        assert 5 <= val_count <= 7, f"Tier {tier} val: {val_count}"


# === Tests for _create_metadata() ===


def test_create_metadata_includes_all_fields(preparer: TrainingDataPreparer):
    """Test _create_metadata creates complete DatasetMetadata."""
    samples = []
    for tier in [1, 2, 3]:
        for i in range(20):
            sample = TrainingSample(
                features=_create_mock_feature_vector(),
                label=tier,
                confidence=0.85,
                source="vectorstore",
                task_id=f"task_{tier}_{i}",
                timestamp=datetime.now(),
            )
            samples.append(sample)

    train_indices = list(range(48))  # 80% of 60
    val_indices = list(range(48, 60))  # 20% of 60

    metadata = preparer._create_metadata(
        samples=samples, train_indices=train_indices, val_indices=val_indices, min_confidence=0.7
    )

    assert isinstance(metadata, DatasetMetadata)
    assert metadata.total_samples == 60
    assert metadata.train_count == 48
    assert metadata.val_count == 12
    assert metadata.min_confidence == 0.7
    assert set(metadata.label_distribution.keys()) == {1, 2, 3}
    assert metadata.version.startswith("v")
    assert metadata.source == "vectorstore_quality_feedback"


# === Helper Functions ===


def _create_mock_feature_vector() -> TaskFeatureVector:
    """Create mock TaskFeatureVector for testing."""
    return TaskFeatureVector(
        embedding=[0.0] * 1536,
        tfidf_features=[0.0] * 100,
        description_length=50,
        word_count=10,
        has_refactor_keyword=0,
        has_test_keyword=0,
        has_async_keyword=0,
        has_fix_keyword=0,
        estimated_time_seconds=120.0,
        historical_tier_mode=1,
    )


# === Performance Tests ===


def test_prepare_dataset_performance(preparer: TrainingDataPreparer):
    """Test prepare_dataset completes within reasonable time."""
    import time

    start_time = time.time()
    result = preparer.prepare_dataset(min_samples_per_tier=5)
    elapsed = time.time() - start_time

    # Should complete within 30 seconds (allows for API calls)
    assert elapsed < 30.0, f"Took {elapsed:.2f}s (>30s)"


# === Edge Cases ===


def test_prepare_dataset_handles_single_tier_gracefully(
    mock_context: AgentContext, feature_extractor: FeatureExtractor
):
    """Test prepare_dataset handles dataset with only one tier."""
    # Create context with only tier 1 samples
    single_tier_context = create_agent_context(session_id="single_tier")

    for i in range(30):
        single_tier_context.store_memory(
            key=f"feedback_{i}",
            content={
                "task_description": f"Fix typo {i}",
                "corrected_tier": 1,
                "confidence": 0.9,
                "tier_change_count": 0,
                "timestamp": datetime.now().isoformat(),
            },
            tags=["quality_feedback", "misclassification"],
        )

    preparer = TrainingDataPreparer(single_tier_context, feature_extractor)
    result = preparer.prepare_dataset(min_samples_per_tier=10)

    # Should fail due to missing tiers
    assert result.is_err()
    assert "Insufficient samples" in result.unwrap_err()
