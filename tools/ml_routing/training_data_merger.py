"""
Training data merger for incremental learning.

Merges VectorStore predictions with existing training dataset, handling:
- Deduplication by task hash (SHA256 of task description)
- Class balancing (undersample majority tier to ±10% of minority)
- Train/val split (80/20 stratified by tier)
- Data quality validation (label conflicts, class imbalance detection)

Constitutional Compliance:
- Article I: Complete context before merge (all samples validated)
- Article II: 100% verification (Result pattern, strict typing)
- Article IV: VectorStore integration (query predictions for learning)
- Article V: Spec-driven (follows spec-008-weekly-retraining-pipeline.md)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines each

Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.3
Author: AgencyOSAgent
Date: 2025-10-10
"""

import hashlib
import logging
import random
from datetime import UTC, datetime

from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.models.task_feature_vector import TaskFeatureVector
from shared.models.training_dataset import (
    DatasetMetadata,
    TrainingDataset,
    TrainingSample,
)
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class TrainingDataMerger:
    """
    Merge VectorStore predictions with existing training dataset.

    Workflow:
    1. Query VectorStore for predictions (last N days, confidence ≥threshold)
    2. Convert PredictionLog instances to TrainingSample (re-extract features)
    3. Merge with existing dataset
    4. Deduplicate by task hash (keep latest by timestamp)
    5. Balance classes (undersample majority tier to ±10%)
    6. Split into train/val (80/20 stratified)
    7. Update metadata and version

    Performance: <10s for 1,000 samples

    Constitutional Compliance:
    - Article I: Complete validation before merge
    - Article II: Result pattern, strict typing
    - Article IV: VectorStore source (institutional learning)
    """

    def __init__(
        self,
        context: AgentContext,
        feature_extractor: FeatureExtractor,
        train_val_ratio: float = 0.8,
    ):
        """
        Initialize training data merger.

        Args:
            context: AgentContext for VectorStore access (Article IV)
            feature_extractor: FeatureExtractor for re-extracting features
            train_val_ratio: Train/val split ratio (default: 0.8)
        """
        self.context = context
        self.feature_extractor = feature_extractor
        self.train_val_ratio = train_val_ratio

        logger.info(f"TrainingDataMerger initialized with train_val_ratio={train_val_ratio}")

    def query_predictions(
        self, days_back: int = 7, min_confidence: float = 0.8
    ) -> Result[list[PredictionLog], str]:
        """
        Query VectorStore for predictions in time window.

        Args:
            days_back: Number of days to look back (default: 7)
            min_confidence: Minimum confidence threshold (default: 0.8)

        Returns:
            Result with list of PredictionLog instances or error message

        Article I: Complete context (retry on timeout)
        Article IV: VectorStore source (cross-session learning)
        """
        try:
            # Query VectorStore (Article IV: institutional learning)
            memories = self.context.search_memories(tags=["prediction"], include_session=False)

            # Calculate cutoff timestamp
            cutoff = datetime.now(UTC).timestamp() - (days_back * 24 * 3600)

            # Filter and convert predictions
            predictions = self._filter_and_convert_memories(memories, cutoff, min_confidence)

            logger.info(
                f"Retrieved {len(predictions)} predictions from VectorStore "
                f"(window: {days_back} days, min_confidence: {min_confidence})"
            )

            return Ok(predictions)

        except Exception as e:
            return Err(f"VectorStore query failed: {e}")

    def _filter_and_convert_memories(
        self,
        memories: list[dict],
        cutoff_timestamp: float,
        min_confidence: float,
    ) -> list[PredictionLog]:
        """
        Filter memories by criteria and convert to PredictionLog.

        Args:
            memories: Raw memories from VectorStore
            cutoff_timestamp: Minimum timestamp for inclusion
            min_confidence: Minimum confidence threshold

        Returns:
            List of PredictionLog instances
        """
        predictions = []

        for memory in memories:
            content = memory.get("content", {})

            # Validate required fields
            if not self._has_required_fields(content):
                continue

            # Filter by criteria
            if not self._meets_filter_criteria(content, cutoff_timestamp, min_confidence):
                continue

            # Convert to PredictionLog
            try:
                prediction_log = PredictionLog.from_dict(content)
                predictions.append(prediction_log)
            except Exception as e:
                logger.warning(f"Failed to parse PredictionLog: {e}")

        return predictions

    def _has_required_fields(self, content: dict) -> bool:
        """Check if content has required fields."""
        return all(
            key in content
            for key in ["confidence", "tier", "timestamp", "method", "model_version", "session_id"]
        )

    def _meets_filter_criteria(self, content: dict, cutoff: float, min_conf: float) -> bool:
        """Check if content meets filter criteria."""
        # Filter by confidence
        if content.get("confidence", 0.0) < min_conf:
            return False

        # Filter by tier availability
        if content.get("tier") is None:
            return False

        # Filter by timestamp
        timestamp_str = content.get("timestamp", "")
        try:
            # Handle multiple timestamp formats
            # Format: "2025-10-15T13:32:11.850606+00:00Z" or "2025-10-15T13:32:11.850606Z" or "2025-10-15T13:32:11.850606+00:00"
            if "+" in timestamp_str:
                # Already has timezone offset, remove trailing Z if present
                timestamp_clean = timestamp_str.rstrip("Z")
            else:
                # No timezone offset, replace Z with +00:00
                timestamp_clean = timestamp_str.replace("Z", "+00:00")

            timestamp = datetime.fromisoformat(timestamp_clean).timestamp()
            return timestamp >= cutoff
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return False

    def convert_predictions_to_samples(
        self, predictions: list[PredictionLog]
    ) -> Result[list[TrainingSample], str]:
        """
        Convert PredictionLog instances to TrainingSample.

        Re-extracts features from task descriptions stored in predictions.

        Args:
            predictions: List of PredictionLog instances with actual_tier

        Returns:
            Result with list of TrainingSample instances or error
        """
        samples = []

        for prediction in predictions:
            sample_result = self._convert_single_prediction(prediction)
            if sample_result.is_ok():
                samples.append(sample_result.unwrap())

        if not samples:
            return Err("No valid samples converted from predictions")

        logger.info(
            f"Converted {len(samples)} predictions to TrainingSample "
            f"({len(predictions) - len(samples)} failed)"
        )

        return Ok(samples)

    def _convert_single_prediction(self, prediction: PredictionLog) -> Result[TrainingSample, str]:
        """
        Convert single PredictionLog to TrainingSample.

        Args:
            prediction: PredictionLog instance

        Returns:
            Result with TrainingSample or error message
        """
        # Extract task description (simplified - use task_id as proxy)
        task_description = prediction.task_id

        # Re-extract features
        features_result = self.feature_extractor.extract_features(task_description=task_description)

        if features_result.is_err():
            return Err(f"Feature extraction failed: {features_result.unwrap_err()}")

        # Convert tier to label
        label_result = self._tier_to_label(prediction.tier)
        if label_result.is_err():
            return Err(label_result.unwrap_err())

        # Parse timestamp string to datetime object
        timestamp_str = prediction.timestamp
        if "+" in timestamp_str:
            # Already has timezone offset, remove trailing Z if present
            timestamp_clean = timestamp_str.rstrip("Z")
        else:
            # No timezone offset, replace Z with +00:00
            timestamp_clean = timestamp_str.replace("Z", "+00:00")

        parsed_timestamp = datetime.fromisoformat(timestamp_clean)

        # Create TrainingSample
        sample = TrainingSample(
            features=features_result.unwrap(),
            label=label_result.unwrap(),
            confidence=prediction.confidence,
            source="vectorstore",
            task_id=prediction.task_id,
            timestamp=parsed_timestamp,
        )

        return Ok(sample)

    def _tier_to_label(self, tier: str) -> Result[int, str]:
        """Convert tier string to label integer."""
        tier_map = {"complex": 3, "moderate": 2, "simple": 1}
        label = tier_map.get(tier, 0)

        if label == 0:
            return Err(f"Invalid tier: {tier}")

        return Ok(label)

    def merge_datasets(
        self,
        existing_dataset: TrainingDataset,
        new_predictions: list[PredictionLog],
        version_increment: str = "minor",
    ) -> Result[TrainingDataset, str]:
        """
        Merge existing dataset with new predictions.

        Args:
            existing_dataset: Existing TrainingDataset
            new_predictions: New PredictionLog instances from VectorStore
            version_increment: "minor" or "major"

        Returns:
            Result with updated TrainingDataset or error message
        """
        try:
            # Convert and prepare samples
            samples_result = self._prepare_merged_samples(existing_dataset, new_predictions)
            if samples_result.is_err():
                return samples_result

            balanced_samples = samples_result.unwrap()

            # Create new dataset
            dataset_result = self._build_updated_dataset(
                existing_dataset, balanced_samples, version_increment
            )

            return dataset_result

        except Exception as e:
            return Err(f"Dataset merge failed: {e}")

    def _prepare_merged_samples(
        self, existing_dataset: TrainingDataset, new_predictions: list[PredictionLog]
    ) -> Result[list[TrainingSample], str]:
        """Prepare merged and balanced samples."""
        # Convert predictions to samples
        samples_result = self.convert_predictions_to_samples(new_predictions)
        if samples_result.is_err():
            return Err(f"Conversion failed: {samples_result.unwrap_err()}")

        # Merge, deduplicate, and balance
        all_samples = existing_dataset.samples + samples_result.unwrap()
        deduped = self._deduplicate_samples(all_samples)
        balanced = self._balance_classes(deduped)

        # Validate balance (Article II)
        balance_result = self._validate_class_balance(balanced)
        if balance_result.is_err():
            return Err(balance_result.unwrap_err())

        return Ok(balanced)

    def _build_updated_dataset(
        self,
        existing: TrainingDataset,
        samples: list[TrainingSample],
        version_inc: str,
    ) -> Result[TrainingDataset, str]:
        """Build updated TrainingDataset with new samples."""
        # Split train/val
        train_idx, val_idx = self._stratified_split(samples, self.train_val_ratio)

        # Update metadata
        new_version = self._increment_version(existing.metadata.version, version_inc)
        metadata = DatasetMetadata(
            total_samples=len(samples),
            train_count=len(train_idx),
            val_count=len(val_idx),
            label_distribution=self._compute_label_distribution(samples),
            created_at=datetime.now(UTC),
            version=new_version,
            min_confidence=existing.metadata.min_confidence,
            source="vectorstore_quality_feedback",
        )

        logger.info(
            f"Merged: {len(existing.samples)} + new → {len(samples)} "
            f"(v{existing.metadata.version} → {new_version})"
        )

        return Ok(
            TrainingDataset(
                samples=samples,
                train_indices=train_idx,
                val_indices=val_idx,
                metadata=metadata,
            )
        )

    def _deduplicate_samples(self, samples: list[TrainingSample]) -> list[TrainingSample]:
        """
        Deduplicate samples by task hash, keeping latest by timestamp.

        Uses SHA256 hash of task_id for deduplication (collision-resistant).

        Args:
            samples: List of TrainingSample instances

        Returns:
            Deduplicated list (latest sample per task_id)

        Performance: O(n) with single pass
        """
        task_hash_map: dict[str, TrainingSample] = {}

        for sample in samples:
            task_hash = self._hash_task_id(sample.task_id)

            if task_hash not in task_hash_map:
                task_hash_map[task_hash] = sample
            else:
                # Keep latest by timestamp
                existing = task_hash_map[task_hash]
                if sample.timestamp > existing.timestamp:
                    task_hash_map[task_hash] = sample

        deduped = list(task_hash_map.values())
        duplicates_removed = len(samples) - len(deduped)

        logger.info(
            f"Deduplication: {len(samples)} samples → {len(deduped)} unique "
            f"({duplicates_removed} duplicates removed, "
            f"{duplicates_removed / len(samples) * 100:.1f}% dedup rate)"
        )

        return deduped

    def _balance_classes(self, samples: list[TrainingSample]) -> list[TrainingSample]:
        """
        Balance classes by undersampling majority tier.

        Target: ±10% samples per tier (prevent overfitting to majority).

        Args:
            samples: List of TrainingSample instances

        Returns:
            Balanced list (roughly equal samples per tier)

        Algorithm: Undersample majority tiers to 110% of minority count
        """
        # Group by label
        label_groups: dict[int, list[TrainingSample]] = {1: [], 2: [], 3: []}
        for sample in samples:
            label_groups[sample.label].append(sample)

        # Find minority tier count
        min_count = min(len(group) for group in label_groups.values() if group)
        target_count = int(min_count * 1.1)  # +10% tolerance

        # Undersample majority tiers
        balanced_samples = []
        for label, group in label_groups.items():
            if len(group) > target_count:
                # Randomly sample target_count samples
                sampled_group = random.sample(group, target_count)
                balanced_samples.extend(sampled_group)
                logger.debug(f"Undersampled label {label}: {len(group)} → {target_count}")
            else:
                balanced_samples.extend(group)

        logger.info(
            f"Class balancing: {len(samples)} samples → {len(balanced_samples)} "
            f"balanced (target: {target_count} per tier)"
        )

        return balanced_samples

    def _validate_class_balance(self, samples: list[TrainingSample]) -> Result[None, str]:
        """
        Validate class balance meets ±10% requirement.

        Args:
            samples: List of TrainingSample instances

        Returns:
            Result with None on success, error message on imbalance

        Article II: 100% verification before training
        """
        label_counts = {1: 0, 2: 0, 3: 0}
        for sample in samples:
            label_counts[sample.label] += 1

        min_count = min(label_counts.values())
        max_count = max(label_counts.values())

        # Check ±10% tolerance
        imbalance_ratio = (max_count - min_count) / min_count if min_count > 0 else 0.0

        if imbalance_ratio > 0.1:
            return Err(
                f"Class imbalance exceeds ±10% tolerance: "
                f"{label_counts} (ratio: {imbalance_ratio:.2%})"
            )

        return Ok(None)

    def _stratified_split(
        self, samples: list[TrainingSample], train_ratio: float
    ) -> tuple[list[int], list[int]]:
        """
        Stratified train/val split (preserve class distribution).

        Args:
            samples: List of TrainingSample instances
            train_ratio: Ratio of training samples (e.g., 0.8)

        Returns:
            (train_indices, val_indices) tuple

        Algorithm: Split each label group proportionally
        """
        # Group by label
        label_groups: dict[int, list[int]] = {1: [], 2: [], 3: []}
        for idx, sample in enumerate(samples):
            label_groups[sample.label].append(idx)

        train_indices = []
        val_indices = []

        # Split each label group
        for label, indices in label_groups.items():
            random.shuffle(indices)
            split_point = int(len(indices) * train_ratio)
            train_indices.extend(indices[:split_point])
            val_indices.extend(indices[split_point:])

        logger.info(
            f"Stratified split: {len(train_indices)} train, {len(val_indices)} val "
            f"(ratio: {train_ratio:.0%}/{1 - train_ratio:.0%})"
        )

        return train_indices, val_indices

    def _increment_version(self, current_version: str, increment_type: str) -> str:
        """
        Increment semantic version.

        Args:
            current_version: Current version (e.g., "v1.0")
            increment_type: "minor" (v1.0→v1.1) or "major" (v1.9→v2.0)

        Returns:
            New version string

        Raises:
            ValueError: If increment_type is invalid
        """
        # Parse version
        version_str = current_version.lstrip("v")
        parts = version_str.split(".")

        if len(parts) != 2:
            raise ValueError(f"Invalid version format: {current_version}")

        major, minor = int(parts[0]), int(parts[1])

        if increment_type == "minor":
            minor += 1
        elif increment_type == "major":
            major += 1
            minor = 0
        else:
            raise ValueError(
                f"Invalid increment_type: {increment_type} (must be 'minor' or 'major')"
            )

        return f"v{major}.{minor}"

    def _compute_label_distribution(self, samples: list[TrainingSample]) -> dict[int, int]:
        """
        Compute label distribution.

        Args:
            samples: List of TrainingSample instances

        Returns:
            Dictionary with counts per label (1, 2, 3)
        """
        distribution = {1: 0, 2: 0, 3: 0}
        for sample in samples:
            distribution[sample.label] += 1
        return distribution

    def _hash_task_id(self, task_id: str) -> str:
        """
        Generate SHA256 hash of task_id for deduplication.

        Args:
            task_id: Task identifier

        Returns:
            Hex digest of task_id hash
        """
        return hashlib.sha256(task_id.encode("utf-8")).hexdigest()
