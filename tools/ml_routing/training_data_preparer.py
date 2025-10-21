"""
Training data preparer for ML-based task routing.

Prepares training datasets from VectorStore quality feedback with:
- Quality filtering (confidence ≥0.7, no oscillation)
- Feature extraction via FeatureExtractor
- Stratified train/val split (80/20)
- Class balance validation (min 50 samples per tier)

Constitutional Compliance:
- Article I: Complete context (all VectorStore feedback queried)
- Article II: Result pattern for error handling
- Article IV: VectorStore integration MANDATORY (cross-session learning)
- Law #5: Result pattern for all fallible operations
- Law #8: Functions <50 lines each

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.4
Author: AgencyOSAgent
Date: 2025-10-10
"""

import logging
from collections import Counter
from datetime import datetime

from sklearn.model_selection import train_test_split

from shared.agent_context import AgentContext
from shared.models.quality_feedback_sample import QualityFeedbackSample
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.task_metadata import TaskMetadata
from shared.models.training_dataset import (
    DatasetMetadata,
    TrainingDataset,
    TrainingSample,
)
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class TrainingDataPreparer:
    """
    Prepare training datasets from VectorStore quality feedback.

    Constitutional Compliance:
    - Article IV: VectorStore integration MANDATORY (cross-session learning)
    - Article II: Result pattern for error handling
    - Article I: Complete context (all quality feedback samples)

    Example:
        >>> context = create_agent_context(session_id="training")
        >>> extractor = FeatureExtractor(api_key, tfidf_vocab)
        >>> preparer = TrainingDataPreparer(context, extractor)
        >>> result = preparer.prepare_dataset(min_confidence=0.7)
        >>> if result.is_ok():
        ...     dataset = result.unwrap()
        ...     print(f"Dataset: {len(dataset.samples)} samples")
    """

    def __init__(self, context: AgentContext, feature_extractor: FeatureExtractor):
        """
        Initialize with AgentContext and FeatureExtractor.

        Args:
            context: AgentContext for VectorStore access
            feature_extractor: FeatureExtractor for feature generation
        """
        self.context = context
        self.feature_extractor = feature_extractor
        self.logger = logging.getLogger(__name__)

    def prepare_dataset(
        self,
        min_confidence: float = 0.7,
        min_samples_per_tier: int = 50,
        train_split: float = 0.8,
    ) -> Result[TrainingDataset, str]:
        """
        Prepare training dataset from VectorStore quality feedback.

        Query → Filter → Extract features → Validate balance → Split → Dataset

        Returns Result[TrainingDataset, str] with dataset or error message.
        Article IV: MANDATORY VectorStore integration for learning.
        """
        # Step 1-2: Query and filter
        filtered_result = self._query_and_filter(min_confidence)
        if filtered_result.is_err():
            return Err(filtered_result.unwrap_err())
        filtered_samples = filtered_result.unwrap()

        # Step 3: Extract features
        samples_result = self._extract_features_for_samples(filtered_samples)
        if samples_result.is_err():
            return Err(samples_result.unwrap_err())
        training_samples = samples_result.unwrap()

        # Step 4-5: Validate and split
        split_result = self._validate_and_split(training_samples, min_samples_per_tier, train_split)
        if split_result.is_err():
            return Err(split_result.unwrap_err())
        train_indices, val_indices = split_result.unwrap()

        # Step 6: Create dataset
        return self._build_dataset(training_samples, train_indices, val_indices, min_confidence)

    def _query_and_filter(self, min_confidence: float) -> Result[list[QualityFeedbackSample], str]:
        """
        Query VectorStore and filter high-quality samples.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            Result with filtered samples or error message
        """
        feedback_result = self._query_vectorstore()
        if feedback_result.is_err():
            return Err(feedback_result.unwrap_err())

        raw_samples = feedback_result.unwrap()
        self.logger.info(f"Retrieved {len(raw_samples)} samples from VectorStore")

        filtered_result = self._filter_high_quality_labels(raw_samples, min_confidence)
        if filtered_result.is_err():
            return Err(filtered_result.unwrap_err())

        filtered_samples = filtered_result.unwrap()
        self.logger.info(f"Filtered to {len(filtered_samples)} high-quality samples")

        return Ok(filtered_samples)

    def _validate_and_split(
        self,
        training_samples: list[TrainingSample],
        min_samples_per_tier: int,
        train_split: float,
    ) -> Result[tuple[list[int], list[int]], str]:
        """
        Validate class balance and perform stratified split.

        Args:
            training_samples: Training samples to split
            min_samples_per_tier: Minimum samples per tier
            train_split: Training split ratio

        Returns:
            Result with (train_indices, val_indices) or error message
        """
        labels = [sample.label for sample in training_samples]
        balance_result = self._check_class_balance(labels, min_samples_per_tier)
        if balance_result.is_err():
            return Err(balance_result.unwrap_err())

        label_distribution = balance_result.unwrap()
        self.logger.info(f"Label distribution: {label_distribution}")

        split_result = self._stratified_split(training_samples, train_split)
        if split_result.is_err():
            return Err(split_result.unwrap_err())

        train_indices, val_indices = split_result.unwrap()
        self.logger.info(f"Split: {len(train_indices)} train, {len(val_indices)} val")

        return Ok((train_indices, val_indices))

    def _build_dataset(
        self,
        training_samples: list[TrainingSample],
        train_indices: list[int],
        val_indices: list[int],
        min_confidence: float,
    ) -> Result[TrainingDataset, str]:
        """
        Build TrainingDataset with metadata.

        Args:
            training_samples: All training samples
            train_indices: Training set indices
            val_indices: Validation set indices
            min_confidence: Minimum confidence threshold used

        Returns:
            Result with TrainingDataset or error message
        """
        metadata = self._create_metadata(
            samples=training_samples,
            train_indices=train_indices,
            val_indices=val_indices,
            min_confidence=min_confidence,
        )

        dataset = TrainingDataset(
            samples=training_samples,
            train_indices=train_indices,
            val_indices=val_indices,
            metadata=metadata,
        )

        self.logger.info(
            f"Dataset prepared: {metadata.total_samples} samples "
            f"(train={metadata.train_count}, val={metadata.val_count})"
        )

        return Ok(dataset)

    def _query_vectorstore(self) -> Result[list[QualityFeedbackSample], str]:
        """
        Query VectorStore for quality feedback signals.

        Article IV Compliance: MANDATORY VectorStore integration for learning.

        Returns:
            Result with list of quality feedback samples or error message
        """
        try:
            # Query with tags: ["quality_feedback", "misclassification"]
            feedback_patterns = self.context.search_memories(
                tags=["quality_feedback", "misclassification"],
                include_session=False,  # Cross-session learning (Article IV)
            )

            if not feedback_patterns:
                return Err("No quality feedback found in VectorStore")

            # Extract content from memory records and convert to typed models
            samples = []
            for pattern in feedback_patterns:
                content = pattern.get("content", {})
                if isinstance(content, dict):
                    # Add tags to content for filtering
                    content["tags"] = pattern.get("tags", [])
                    # Convert to typed model
                    sample = QualityFeedbackSample.from_vectorstore_content(content)
                    if sample:
                        samples.append(sample)

            if not samples:
                return Err("No valid quality feedback samples found in VectorStore")

            return Ok(samples)

        except Exception as e:
            return Err(f"VectorStore query failed: {e}")

    def _filter_high_quality_labels(
        self, samples: list[QualityFeedbackSample], min_confidence: float
    ) -> Result[list[QualityFeedbackSample], str]:
        """
        Filter samples for high-quality labels.

        Filters:
        - Confidence ≥ min_confidence (default 0.7)
        - No oscillation (tier changes ≤2)
        - No duplicates (unique task descriptions)

        Args:
            samples: Raw samples from VectorStore
            min_confidence: Minimum confidence threshold

        Returns:
            Result with filtered samples or error message
        """
        filtered = []
        seen_tasks = set()

        for sample in samples:
            # Filter 1: Confidence threshold
            if sample.confidence < min_confidence:
                continue

            # Filter 2: Oscillation detection
            if sample.tier_change_count > 2:
                self.logger.debug(
                    f"Skipping oscillating task: {sample.tier_change_count} tier changes"
                )
                continue

            # Filter 3: Deduplication
            if sample.task_description in seen_tasks:
                continue

            seen_tasks.add(sample.task_description)
            filtered.append(sample)

        if not filtered:
            return Err("No samples passed quality filters")

        return Ok(filtered)

    def _extract_features_for_samples(
        self, samples: list[QualityFeedbackSample]
    ) -> Result[list[TrainingSample], str]:
        """
        Extract features for all samples using FeatureExtractor.

        Args:
            samples: Filtered quality feedback samples

        Returns:
            Result with list of TrainingSample or error message
        """
        training_samples = []
        failed_samples = []

        for i, sample in enumerate(samples):
            sample_result = self._extract_features_for_single_sample(i, sample)
            if sample_result.is_ok():
                training_samples.append(sample_result.unwrap())
            else:
                # Log feature extraction failures for debugging
                error_msg = sample_result.unwrap_err()
                failed_samples.append((i, error_msg))
                self.logger.warning(f"Sample {i} feature extraction failed: {error_msg}")

        if not training_samples:
            failure_summary = "; ".join([f"Sample {i}: {err}" for i, err in failed_samples[:5]])
            return Err(
                f"Feature extraction failed for all {len(samples)} samples. First failures: {failure_summary}"
            )

        self.logger.info(f"Extracted features for {len(training_samples)} samples")
        return Ok(training_samples)

    def _extract_features_for_single_sample(
        self, index: int, sample: QualityFeedbackSample
    ) -> Result[TrainingSample, str]:
        """
        Extract features for a single sample.

        Args:
            index: Sample index for logging
            sample: Quality feedback sample

        Returns:
            Result with TrainingSample or error message
        """
        if not sample.task_description:
            return Err(f"Sample {index}: Empty task description")

        # Create typed metadata
        task_metadata = TaskMetadata(
            estimated_time_seconds=sample.estimated_time_seconds,
            historical_tier_mode=sample.historical_tier_mode,
        )

        # Extract features
        features_result = self.feature_extractor.extract_features(
            task_description=sample.task_description,
            task_metadata=task_metadata,
        )

        if features_result.is_err():
            return Err(f"Sample {index}: {features_result.unwrap_err()}")

        # Create TrainingSample
        return Ok(
            TrainingSample(
                features=features_result.unwrap(),
                label=sample.corrected_tier,
                confidence=sample.confidence,
                source="vectorstore",
                task_id=sample.task_id,
                timestamp=datetime.fromisoformat(sample.timestamp),
            )
        )

    def _check_class_balance(
        self, labels: list[int], min_samples_per_tier: int
    ) -> Result[dict[int, int], str]:
        """
        Validate class balance (min samples per tier).

        Args:
            labels: List of tier labels (1, 2, 3)
            min_samples_per_tier: Minimum samples required per tier

        Returns:
            Result[label_distribution, error_msg]
        """
        label_counts = Counter(labels)

        # Check: all tiers (1, 2, 3) present
        for tier in {1, 2, 3}:
            count = label_counts.get(tier, 0)
            if count < min_samples_per_tier:
                return Err(
                    f"Insufficient samples for tier {tier}: {count} < {min_samples_per_tier}"
                )

        return Ok(dict(label_counts))

    def _stratified_split(
        self, samples: list[TrainingSample], train_split: float
    ) -> Result[tuple[list[int], list[int]], str]:
        """
        Stratified train/val split using sklearn.

        Preserves label distribution in train and val sets.

        Args:
            samples: All training samples
            train_split: Training split ratio (0.8 = 80% train, 20% val)

        Returns:
            Result[(train_indices, val_indices), error_msg]
        """
        # Extract labels for stratification
        labels = [sample.label for sample in samples]
        indices = list(range(len(samples)))

        try:
            train_idx, val_idx = train_test_split(
                indices,
                test_size=1.0 - train_split,
                stratify=labels,  # Preserve label distribution
                random_state=42,  # Reproducibility
            )

            return Ok((train_idx, val_idx))

        except Exception as e:
            return Err(f"Stratified split failed: {e}")

    def _create_metadata(
        self,
        samples: list[TrainingSample],
        train_indices: list[int],
        val_indices: list[int],
        min_confidence: float,
    ) -> DatasetMetadata:
        """
        Create DatasetMetadata for TrainingDataset.

        Args:
            samples: All training samples
            train_indices: Training set indices
            val_indices: Validation set indices
            min_confidence: Minimum confidence threshold used

        Returns:
            DatasetMetadata instance
        """
        # Calculate label distribution
        labels = [samples[i].label for i in range(len(samples))]
        label_distribution = dict(Counter(labels))

        # Create metadata
        metadata = DatasetMetadata(
            total_samples=len(samples),
            train_count=len(train_indices),
            val_count=len(val_indices),
            label_distribution=label_distribution,
            created_at=datetime.now(),
            version=f"v1.{len(samples)}",  # Version based on sample count
            min_confidence=min_confidence,
            source="vectorstore_quality_feedback",
        )

        return metadata

    def _detect_oscillation(self, tier_changes: list[int]) -> bool:
        """
        Detect tier oscillation (>2 tier changes).

        Args:
            tier_changes: List of tier changes for a task

        Returns:
            True if task is oscillating (>2 tier changes)
        """
        return len(tier_changes) > 2

    def get_dataset_statistics(
        self, dataset: TrainingDataset
    ) -> dict[str, int | float | dict[int, int] | str]:
        """
        Get comprehensive dataset statistics for monitoring.

        Args:
            dataset: TrainingDataset to analyze

        Returns:
            Dictionary with statistics (typed union for export/monitoring)
        """
        train_samples = dataset.get_train_samples()
        val_samples = dataset.get_val_samples()

        # Label distributions
        label_dist = dataset.get_label_distribution()

        # Confidence statistics
        confidence_stats = dataset.get_confidence_stats()

        return {
            "total_samples": len(dataset.samples),
            "train_count": len(train_samples),
            "val_count": len(val_samples),
            "label_distribution": label_dist,
            "confidence_stats": confidence_stats,
            "train_split_ratio": len(train_samples) / len(dataset.samples),
            "val_split_ratio": len(val_samples) / len(dataset.samples),
            "version": dataset.metadata.version,
            "created_at": dataset.metadata.created_at.isoformat(),
        }
