# Specification: Weekly Retraining Pipeline (Leap 5 Phase 4)

**Spec ID**: `spec-008-weekly-retraining-pipeline`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**:
- `spec-007-phase3-ml-inference.md` (Leap 5 Phase 3 - ML Inference)
- `spec-006-ensemble-model-pydantic.md` (Phase 2 - Model Training)
- `spec-005-advanced-pattern-recognition.md` (Phase 1 - Feature Engineering)
**Related ADRs**:
- `ADR-004: Continuous Learning` (VectorStore integration mandatory)
- `ADR-024: Adaptive Model Router` (cost optimization)
- `ADR-026: ML Classifier Integration` (Phase 3 inference)

---

## Executive Summary

Leap 5 Phase 4 delivers **automated weekly retraining** that transforms production predictions into improved ML models, achieving continuous improvement through online learning. The system queries VectorStore for 7-day prediction windows, merges with existing training data, trains new models with 5-fold cross-validation, and deploys via A/B testing with semantic versioning.

**Key Innovation**: Zero-manual-intervention retraining loop that ensures model accuracy never degrades below production baseline through automated quality gates and rollback mechanisms.

---

## Goals

### Primary Goals

- **Goal 1**: VectorStore query system retrieves 7-day prediction windows with filtering (confidence ≥0.6, actual_tier present)
- **Goal 2**: Incremental learning merges new predictions with existing training dataset (deduplication, class balancing)
- **Goal 3**: 5-fold stratified cross-validation ensures model generalization (accuracy ≥current + 0.5% required for deployment)
- **Goal 4**: Semantic versioning scheme tracks model evolution (v1.0 → v1.1 for weekly updates, v2.0 for architecture changes)
- **Goal 5**: Automated weekly scheduler (cron job) with monitoring, alerting, and rollback capability

### Success Metrics

| Metric | Target | Measurement Method | Baseline |
|--------|--------|-------------------|----------|
| **Retraining Accuracy** | ≥Current + 0.5% | 5-fold CV validation | 98.2% (Phase 3) |
| **Data Freshness** | <7 days | VectorStore query window | Real-time (Phase 3 logging) |
| **Training Time** | <30 min | End-to-end pipeline timing | N/A (new metric) |
| **Deployment Success Rate** | >90% | New model passes A/B test | N/A (new feature) |
| **Rollback Rate** | <10% | Model degradation triggers | N/A (new metric) |
| **Class Balance** | ±10% per tier | Train set label distribution | Balanced (Phase 2: 33/33/33%) |
| **Deduplication Rate** | >95% | Duplicate task_id removal | N/A (new metric) |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time model updates during production (weekly batch retraining sufficient, see Phase 6 for online learning)
- **Non-Goal 2**: Multi-model ensemble beyond current architecture (RandomForest + GradientBoosting only, no neural networks)
- **Non-Goal 3**: Active learning with human labeling (fully automated, no manual intervention)
- **Non-Goal 4**: Custom hyperparameter tuning per retraining cycle (fixed hyperparameters from Phase 2, tune manually if accuracy degrades)

### Future Considerations

- **Future Enhancement 1**: Active learning loop (request human labels for low-confidence predictions)
- **Future Enhancement 2**: Real-time model updates (incremental training with mini-batches)
- **Future Enhancement 3**: Multi-model A/B testing (champion/challenger/contender framework)
- **Future Enhancement 4**: AutoML hyperparameter optimization (grid search during retraining)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Retraining Scheduler (Automated System)

- **Description**: Cron job that triggers weekly retraining pipeline every Sunday 2am UTC
- **Goals**: Zero manual intervention, <30 min training time, automated deployment via A/B test
- **Pain Points**: Training failures, insufficient new data (<100 samples), model degradation
- **Technical Proficiency**: Autonomous system with error handling, rollback logic, alerting

#### Persona 2: ML Model (Component)

- **Description**: EnsembleModel that evolves weekly through incremental training on production data
- **Goals**: Accuracy improvement (≥+0.5% per cycle), stable predictions, generalization to novel tasks
- **Pain Points**: Overfitting to recent data, class imbalance, forgetting old patterns
- **Technical Proficiency**: Scikit-learn ensemble (RandomForest + GradientBoosting), pickle serialization

#### Persona 3: Development Team (Monitoring & Operations)

- **Description**: Engineers monitoring retraining metrics, investigating failures, managing rollbacks
- **Goals**: Dashboard visibility, automated alerts, rollback capability, training logs
- **Pain Points**: Silent failures, model drift, insufficient observability
- **Technical Proficiency**: ML operations, telemetry analysis, VectorStore queries

### User Journeys

#### Journey 1: Successful Weekly Retraining (Primary Use Case)

```
1. System starts with: Sunday 2am UTC, cron job triggers
2. System needs to: Retrain model on last 7 days of production data
3. System performs:
   - Query VectorStore: 7-day window (confidence ≥0.6, actual_tier present) → 450 new samples
   - Load existing dataset: models/training_dataset_v1.0.pkl → 500 samples
   - Merge datasets: Deduplicate by task_id (5 duplicates removed) → 945 samples total
   - Balance classes: Undersample majority tier (P2: 400 → 315 samples) → 945 balanced
   - Split data: 80% train (756 samples), 20% val (189 samples)
   - Train model: 5-fold CV with RandomForest + GradientBoosting → 30 min training
   - Validate model: CV accuracy 98.8% > current 98.2% + 0.5% ✅
   - Version model: v1.0 → v1.1 (weekly update)
   - Save artifacts: models/routing_classifier_v1.1.pkl + metadata
   - Deploy A/B test: 10% traffic to v1.1, 90% to v1.0
   - Monitor 24h: v1.1 accuracy 98.7% > v1.0 accuracy 98.2% ✅
   - Promote model: Set v1.1 as default, retire v1.0
4. System achieves:
   - New model accuracy: 98.8% (validation), 98.7% (production)
   - Improvement: +0.6% over current model (target: ≥+0.5% ✅)
   - Training time: 28 min (target: <30 min ✅)
   - Deployment: Automated promotion to 100% traffic
```

#### Journey 2: Insufficient Data (Graceful Degradation)

```
1. System starts with: Sunday 2am UTC, cron job triggers
2. System needs to: Retrain model but insufficient new data available
3. System performs:
   - Query VectorStore: 7-day window → 45 new samples (target: ≥100)
   - Check data threshold: 45 < 100 → insufficient data ❌
   - Skip retraining: Log warning "Insufficient data for retraining (45 < 100)"
   - Send alert: Email/Slack notification to ops team
   - Keep current model: v1.0 remains active (no downgrade)
   - Retry next week: Cumulative 14-day window may have ≥100 samples
4. System achieves:
   - No model degradation (current model unchanged)
   - Alert sent to ops team (investigate low prediction volume)
   - Retry logic (next week with 14-day window)
```

#### Journey 3: Model Degradation (Rollback Required)

```
1. System starts with: New model v1.1 deployed via A/B test (10% traffic)
2. System needs to: Detect degradation and rollback to v1.0
3. System performs:
   - Monitor 24h: v1.1 accuracy 96.5% < v1.0 accuracy 98.2% ❌
   - Detect degradation: Accuracy drop >3% (threshold for rollback)
   - Automatic rollback: Set A/B percentage to 0% (all traffic to v1.0)
   - Send alert: Critical alert "Model v1.1 degraded (96.5% < 98.2%)"
   - Log failure: Store failure reason in VectorStore (learning for future)
   - Analyze misclassifications: Compare v1.1 vs v1.0 predictions
4. System achieves:
   - Production stability: Rollback to v1.0 within 5 min of detection
   - Zero user impact: Automatic fallback, no manual intervention
   - Learning capture: Failure analysis stored for future debugging
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: VectorStore Query System

- **AC-1.1**: `query_predictions()` method retrieves 7-day prediction window (default) with configurable lookback
- **AC-1.2**: Filters predictions by confidence ≥0.6 and actual_tier is not None (only ground truth labels)
- **AC-1.3**: Returns `List[PredictionLog]` with deduplication by task_id (keep latest prediction)
- **AC-1.4**: Query performance <5 seconds for 1,000 predictions (VectorStore index required)
- **AC-1.5**: Empty result handling: Returns empty list if no predictions found (graceful degradation)

#### Feature Component 2: Training Data Merger

- **AC-2.1**: `merge_datasets()` combines existing training dataset with new VectorStore predictions
- **AC-2.2**: Deduplication: Removes duplicate task_ids (keep latest by timestamp) with >95% dedup rate
- **AC-2.3**: Class balancing: Undersamples majority tier to ±10% of minority tier (prevent overfitting)
- **AC-2.4**: Train/val split: 80% train, 20% val (stratified by tier label)
- **AC-2.5**: Metadata update: Increments version (v1.0 → v1.1), updates created_at timestamp

#### Feature Component 3: Model Retrainer

- **AC-3.1**: `retrain_model()` trains new EnsembleModel with 5-fold stratified cross-validation
- **AC-3.2**: Hyperparameters fixed from Phase 2 (RandomForest: n_estimators=100, GradientBoosting: n_estimators=50)
- **AC-3.3**: Validation: CV accuracy ≥current model + 0.5% required for deployment (quality gate)
- **AC-3.4**: Training time <30 min for 1,000 samples (parallel training with joblib)
- **AC-3.5**: Model serialization: Saves to `~/.agency/models/routing_classifier_v{version}.pkl` with metadata JSON

#### Feature Component 4: Semantic Versioning

- **AC-4.1**: Version scheme: `v{major}.{minor}` (e.g., v1.0, v1.1, v2.0)
- **AC-4.2**: Weekly updates: Increment minor version (v1.0 → v1.1, v1.1 → v1.2)
- **AC-4.3**: Architecture changes: Increment major version (v1.9 → v2.0 for new ensemble architecture)
- **AC-4.4**: Version metadata: Store training_date, dataset_version, validation_accuracy in JSON
- **AC-4.5**: Backward compatibility: Old versions retained for 30 days (rollback capability)

#### Feature Component 5: Automated Scheduler

- **AC-5.1**: Cron job triggers every Sunday 2am UTC (configurable schedule)
- **AC-5.2**: Lockfile prevents concurrent runs (prevent race conditions)
- **AC-5.3**: Error handling: Retries 3x on transient failures (VectorStore timeout, disk full)
- **AC-5.4**: Alerting: Sends email/Slack notification on failure or degradation
- **AC-5.5**: Logging: Writes training logs to `logs/retraining/retraining_{timestamp}.log` (debugging)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: VectorStore query <5s for 1,000 predictions (indexed by timestamp and task_id)
- **AC-P.2**: Deduplication <10s for 1,000 samples (in-memory hash set)
- **AC-P.3**: Training time <30 min for 1,000 samples (parallel CV with joblib)
- **AC-P.4**: A/B deployment <1 min (atomic file swap for model path)

#### Quality

- **AC-Q.1**: Retraining accuracy ≥current + 0.5% on validation set (5-fold CV)
- **AC-Q.2**: Class balance ±10% per tier (prevent overfitting to majority class)
- **AC-Q.3**: Deduplication rate >95% (minimize training on stale data)
- **AC-Q.4**: Test pass rate 100% (all 30+ retraining tests passing)

#### Reliability

- **AC-R.1**: Rollback capability: Automatic rollback if new model accuracy <current - 3%
- **AC-R.2**: Data validation: Rejects training data with <100 new samples (insufficient data)
- **AC-R.3**: Model validation: EnsembleModel validates accuracy ≥0.98 before deployment
- **AC-R.4**: Atomic deployment: A/B test prevents partial rollouts (all-or-nothing promotion)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: VectorStore query completes or errors (no partial results, retry 3x on timeout)
- **AC-CI.2**: Training dataset fully loaded before merge (validate sample count matches metadata)
- **AC-CI.3**: 5-fold CV completes all folds (no partial validation, fail if any fold fails)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: New model accuracy ≥current + 0.5% validated via 5-fold CV
- **AC-CII.2**: 100% test pass rate on retraining tests (30+ tests covering pipeline)
- **AC-CII.3**: Class balance validated (±10% per tier, fail if imbalanced)

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: Automated deployment: If CV accuracy ≥current + 0.5%, promote to 100% (no manual approval)
- **AC-CIII.2**: Automated rollback: If production accuracy <current - 3%, rollback to previous version
- **AC-CIII.3**: No manual override flags (scheduler fully automated, disable via cron only)

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: All predictions from VectorStore used for retraining (institutional memory)
- **AC-CIV.2**: Training logs stored in VectorStore (success/failure patterns for future learning)
- **AC-CIV.3**: Misclassification analysis stored (compare new model vs old model predictions)
- **AC-CIV.4**: Cross-session learning: VectorStore queries use `include_session=False` (accumulate all predictions)

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Phase 4 scope limited to weekly retraining (no real-time updates, see Phase 6)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Leap 5 Phase 4: Weekly Retraining Pipeline                            │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ Cron Scheduler   │───▶│ Retraining       │───▶│ Model Deployment │ │
│  │                  │    │ Orchestrator     │    │                  │ │
│  │ - Sunday 2am UTC │    │ - VectorStore    │    │ - A/B testing    │ │
│  │ - Lockfile       │    │   query          │    │ - Atomic swap    │ │
│  │ - Error handling │    │ - Data merge     │    │ - Rollback       │ │
│  └──────────────────┘    │ - Model training │    └──────────────────┘ │
│                          │ - Validation     │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   ▼                        │            │
│                          ┌──────────────────┐             │            │
│                          │ VectorStore      │             │            │
│                          │ (Article IV)     │             │            │
│                          │                  │             │            │
│                          │ - Predictions    │             │            │
│                          │ - Ground truth   │             │            │
│                          │ - 7-day window   │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   ▼                        │            │
│                          ┌──────────────────┐             │            │
│                          │ Training Data    │             │            │
│                          │ Merger           │             │            │
│                          │                  │             │            │
│                          │ - Deduplication  │             │            │
│                          │ - Class balance  │             │            │
│                          │ - Train/val split│             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   ▼                        │            │
│                          ┌──────────────────┐             │            │
│                          │ Model Retrainer  │             │            │
│                          │                  │             │            │
│                          │ - 5-fold CV      │             │            │
│                          │ - Ensemble train │             │            │
│                          │ - Validation     │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   ▼                        │            │
│                          ┌──────────────────┐             │            │
│                          │ Model Versioning │             │            │
│                          │                  │             │            │
│                          │ - Semantic ver   │             │            │
│                          │ - Metadata JSON  │             │            │
│                          │ - Storage        │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   └────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 VectorStore Query System

```python
"""
VectorStore query system for retrieving production predictions.

Constitutional compliance:
- Article I: Complete context (retry on timeout, validate results)
- Article IV: VectorStore source (institutional learning)
- Article V: Spec-driven (follows spec-008)
"""

from datetime import datetime, timedelta, UTC
from typing import List

from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.type_definitions.result import Result, Ok, Err


class PredictionQueryService:
    """
    Service for querying production predictions from VectorStore.

    Workflow:
    1. Define time window (default: 7 days)
    2. Query VectorStore with filters (confidence ≥0.6, actual_tier present)
    3. Deduplicate by task_id (keep latest)
    4. Return validated PredictionLog instances

    Performance: <5s for 1,000 predictions
    """

    def __init__(self, context: AgentContext):
        """
        Initialize query service.

        Args:
            context: AgentContext for VectorStore access (Article IV)
        """
        self.context = context

    def query_predictions(
        self,
        days_back: int = 7,
        min_confidence: float = 0.6
    ) -> Result[List[PredictionLog], str]:
        """
        Query VectorStore for production predictions in time window.

        Args:
            days_back: Number of days to look back (default: 7)
            min_confidence: Minimum confidence threshold (default: 0.6)

        Returns:
            Result with list of PredictionLog instances or error message

        Workflow:
        1. Calculate time window (now - days_back to now)
        2. Query VectorStore with tags=["prediction", "ml_model"]
        3. Filter by confidence ≥min_confidence and actual_tier is not None
        4. Deduplicate by task_id (keep latest by timestamp)
        5. Convert to PredictionLog instances

        Performance: <5s for 1,000 predictions (indexed VectorStore query)
        """
        try:
            # Step 1: Calculate time window
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(days=days_back)

            # Step 2: Query VectorStore (Article IV)
            raw_predictions = self.context.search_memories(
                tags=["prediction"],
                include_session=False,  # Cross-session learning (Article IV)
                filters={
                    "timestamp_gte": start_time.isoformat(),
                    "timestamp_lte": end_time.isoformat()
                }
            )

            # Step 3: Filter by confidence and ground truth availability
            filtered_predictions = [
                pred for pred in raw_predictions
                if pred.get("confidence", 0.0) >= min_confidence
                and pred.get("actual_tier") is not None
            ]

            # Step 4: Deduplicate by task_id (keep latest)
            deduped_predictions = self._deduplicate_by_task_id(filtered_predictions)

            # Step 5: Convert to PredictionLog instances
            prediction_logs = []
            for pred_dict in deduped_predictions:
                try:
                    prediction_log = PredictionLog.from_dict(pred_dict)
                    prediction_logs.append(prediction_log)
                except Exception as e:
                    # Log validation error but continue (partial success)
                    logger.warning(
                        f"Failed to parse prediction {pred_dict.get('task_id')}: {e}"
                    )

            logger.info(
                f"Retrieved {len(prediction_logs)} predictions from VectorStore "
                f"(window: {days_back} days, min_confidence: {min_confidence})"
            )

            return Ok(prediction_logs)

        except Exception as e:
            return Err(f"Failed to query VectorStore: {e}")

    def _deduplicate_by_task_id(
        self,
        predictions: List[dict]
    ) -> List[dict]:
        """
        Deduplicate predictions by task_id, keeping latest by timestamp.

        Args:
            predictions: List of prediction dictionaries

        Returns:
            Deduplicated list (latest prediction per task_id)

        Algorithm:
        - Group by task_id
        - Keep prediction with latest timestamp per group
        - O(n) time complexity with single pass
        """
        task_id_map = {}

        for pred in predictions:
            task_id = pred.get("task_id")
            timestamp = datetime.fromisoformat(pred.get("timestamp"))

            if task_id not in task_id_map:
                task_id_map[task_id] = pred
            else:
                existing_timestamp = datetime.fromisoformat(
                    task_id_map[task_id].get("timestamp")
                )
                if timestamp > existing_timestamp:
                    task_id_map[task_id] = pred  # Keep latest

        return list(task_id_map.values())
```

### 5.3 Training Data Merger

```python
"""
Training data merger for incremental learning.

Merges VectorStore predictions with existing training dataset,
handling deduplication, class balancing, and train/val splitting.

Constitutional compliance:
- Article I: Complete validation before merge
- Article II: Strict typing, comprehensive validation
- Article V: Spec-driven (follows spec-008)
"""

from datetime import datetime, UTC
from typing import List
import random

from shared.models.training_dataset import (
    TrainingSample,
    DatasetMetadata,
    TrainingDataset
)
from shared.models.prediction_log import PredictionLog
from shared.models.task_feature_vector import TaskFeatureVector
from shared.type_definitions.result import Result, Ok, Err


class TrainingDataMerger:
    """
    Merges VectorStore predictions with existing training dataset.

    Workflow:
    1. Load existing training dataset
    2. Convert PredictionLog instances to TrainingSample
    3. Deduplicate by task_id (keep latest)
    4. Balance classes (undersample majority tier)
    5. Split into train/val (80/20 stratified)
    6. Update metadata and version

    Performance: <10s for 1,000 samples
    """

    def __init__(self, train_val_ratio: float = 0.8):
        """
        Initialize merger.

        Args:
            train_val_ratio: Ratio of training samples (default: 0.8)
        """
        self.train_val_ratio = train_val_ratio

    def merge_datasets(
        self,
        existing_dataset: TrainingDataset,
        new_predictions: List[PredictionLog],
        version_increment: str = "minor"
    ) -> Result[TrainingDataset, str]:
        """
        Merge existing dataset with new predictions.

        Args:
            existing_dataset: Existing TrainingDataset from Phase 2/3
            new_predictions: New PredictionLog instances from VectorStore
            version_increment: "minor" (v1.0→v1.1) or "major" (v1.9→v2.0)

        Returns:
            Result with updated TrainingDataset or error message

        Workflow:
        1. Convert new_predictions to TrainingSample (extract features)
        2. Merge with existing samples
        3. Deduplicate by task_id (keep latest by timestamp)
        4. Balance classes (undersample majority to ±10% of minority)
        5. Split train/val (80/20 stratified)
        6. Update metadata (version, created_at, counts)

        Performance: <10s for 1,000 samples
        """
        try:
            # Step 1: Convert predictions to training samples
            new_samples_result = self._convert_predictions_to_samples(
                new_predictions
            )
            if new_samples_result.is_err():
                return Err(
                    f"Failed to convert predictions: {new_samples_result.unwrap_err()}"
                )

            new_samples = new_samples_result.unwrap()

            # Step 2: Merge with existing samples
            all_samples = existing_dataset.samples + new_samples

            # Step 3: Deduplicate by task_id
            deduped_samples = self._deduplicate_samples(all_samples)

            # Step 4: Balance classes
            balanced_samples = self._balance_classes(deduped_samples)

            # Step 5: Split train/val (stratified)
            train_indices, val_indices = self._stratified_split(
                balanced_samples,
                self.train_val_ratio
            )

            # Step 6: Update metadata
            new_version = self._increment_version(
                existing_dataset.metadata.version,
                version_increment
            )

            label_distribution = self._compute_label_distribution(balanced_samples)

            new_metadata = DatasetMetadata(
                total_samples=len(balanced_samples),
                train_count=len(train_indices),
                val_count=len(val_indices),
                label_distribution=label_distribution,
                created_at=datetime.now(UTC),
                version=new_version,
                min_confidence=existing_dataset.metadata.min_confidence,
                source="vectorstore_quality_feedback"
            )

            new_dataset = TrainingDataset(
                samples=balanced_samples,
                train_indices=train_indices,
                val_indices=val_indices,
                metadata=new_metadata
            )

            logger.info(
                f"Merged datasets: {len(existing_dataset.samples)} existing + "
                f"{len(new_samples)} new → {len(balanced_samples)} total "
                f"(version: {existing_dataset.metadata.version} → {new_version})"
            )

            return Ok(new_dataset)

        except Exception as e:
            return Err(f"Failed to merge datasets: {e}")

    def _convert_predictions_to_samples(
        self,
        predictions: List[PredictionLog]
    ) -> Result[List[TrainingSample], str]:
        """
        Convert PredictionLog to TrainingSample.

        Requires re-extracting features from task description stored in
        PredictionLog metadata (or retrieved from VectorStore).

        Args:
            predictions: List of PredictionLog instances

        Returns:
            Result with list of TrainingSample instances

        Note: This assumes PredictionLog stores task_description or
        we can retrieve it from VectorStore using task_id.
        """
        # Implementation note: Feature extraction required here
        # This is simplified - actual implementation needs feature extractor
        raise NotImplementedError(
            "Feature extraction from PredictionLog requires FeatureExtractor "
            "integration (see spec-008 section 5.4)"
        )

    def _deduplicate_samples(
        self,
        samples: List[TrainingSample]
    ) -> List[TrainingSample]:
        """
        Deduplicate samples by task_id, keeping latest by timestamp.

        Args:
            samples: List of TrainingSample instances

        Returns:
            Deduplicated list (latest sample per task_id)
        """
        task_id_map = {}

        for sample in samples:
            task_id = sample.task_id
            timestamp = sample.timestamp

            if task_id not in task_id_map:
                task_id_map[task_id] = sample
            else:
                existing_timestamp = task_id_map[task_id].timestamp
                if timestamp > existing_timestamp:
                    task_id_map[task_id] = sample  # Keep latest

        return list(task_id_map.values())

    def _balance_classes(
        self,
        samples: List[TrainingSample]
    ) -> List[TrainingSample]:
        """
        Balance classes by undersampling majority tier.

        Target: ±10% samples per tier (prevent overfitting to majority).

        Args:
            samples: List of TrainingSample instances

        Returns:
            Balanced list (roughly equal samples per tier)
        """
        # Group by label
        label_groups = {1: [], 2: [], 3: []}
        for sample in samples:
            label_groups[sample.label].append(sample)

        # Find minority tier count
        min_count = min(len(group) for group in label_groups.values())
        target_count = int(min_count * 1.1)  # +10% tolerance

        # Undersample majority tiers
        balanced_samples = []
        for label, group in label_groups.items():
            if len(group) > target_count:
                # Randomly sample target_count samples
                sampled_group = random.sample(group, target_count)
                balanced_samples.extend(sampled_group)
            else:
                balanced_samples.extend(group)

        return balanced_samples

    def _stratified_split(
        self,
        samples: List[TrainingSample],
        train_ratio: float
    ) -> tuple[List[int], List[int]]:
        """
        Stratified train/val split (preserve class distribution).

        Args:
            samples: List of TrainingSample instances
            train_ratio: Ratio of training samples (e.g., 0.8)

        Returns:
            (train_indices, val_indices) tuple
        """
        # Group by label
        label_groups = {1: [], 2: [], 3: []}
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

        return train_indices, val_indices

    def _increment_version(
        self,
        current_version: str,
        increment_type: str
    ) -> str:
        """
        Increment semantic version.

        Args:
            current_version: Current version (e.g., "v1.0")
            increment_type: "minor" (v1.0→v1.1) or "major" (v1.9→v2.0)

        Returns:
            New version string
        """
        major, minor = map(int, current_version.lstrip("v").split("."))

        if increment_type == "minor":
            minor += 1
        elif increment_type == "major":
            major += 1
            minor = 0
        else:
            raise ValueError(f"Invalid increment_type: {increment_type}")

        return f"v{major}.{minor}"

    def _compute_label_distribution(
        self,
        samples: List[TrainingSample]
    ) -> dict[int, int]:
        """Compute label distribution."""
        distribution = {1: 0, 2: 0, 3: 0}
        for sample in samples:
            distribution[sample.label] += 1
        return distribution
```

### 5.4 Model Retrainer with 5-Fold CV

```python
"""
Model retrainer with 5-fold stratified cross-validation.

Trains new EnsembleModel on merged dataset with quality gates:
- CV accuracy ≥current + 0.5% (deployment threshold)
- Training time <30 min for 1,000 samples
- Stratified splits (preserve class distribution)

Constitutional compliance:
- Article I: Complete training (all 5 folds finish)
- Article II: 100% validation (accuracy threshold enforced)
- Article V: Spec-driven (follows spec-008)
"""

from datetime import datetime, UTC
from typing import Tuple
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier

from shared.models.ensemble_model import EnsembleModel
from shared.models.training_dataset import TrainingDataset
from shared.type_definitions.result import Result, Ok, Err
from tools.ml_routing.model_storage import ModelStorage


class ModelRetrainer:
    """
    Retrains EnsembleModel with 5-fold CV validation.

    Workflow:
    1. Extract X, y from TrainingDataset
    2. 5-fold stratified CV (preserve class distribution)
    3. Train RandomForest + GradientBoosting ensemble
    4. Validate CV accuracy ≥current + 0.5%
    5. Create EnsembleModel with metadata
    6. Save to disk with versioning

    Performance: <30 min for 1,000 samples
    """

    def __init__(
        self,
        current_accuracy: float,
        min_improvement: float = 0.005  # 0.5%
    ):
        """
        Initialize retrainer.

        Args:
            current_accuracy: Current model validation accuracy
            min_improvement: Minimum accuracy improvement required (default: 0.5%)
        """
        self.current_accuracy = current_accuracy
        self.min_improvement = min_improvement

    def retrain_model(
        self,
        dataset: TrainingDataset,
        n_folds: int = 5
    ) -> Result[Tuple[EnsembleModel, float], str]:
        """
        Retrain model with 5-fold CV.

        Args:
            dataset: TrainingDataset with train/val splits
            n_folds: Number of CV folds (default: 5)

        Returns:
            Result with (EnsembleModel, cv_accuracy) or error message

        Workflow:
        1. Extract training data (X, y from train_indices)
        2. 5-fold stratified CV
        3. Train ensemble on full training set
        4. Validate CV accuracy ≥current + min_improvement
        5. Create EnsembleModel with metadata

        Performance: <30 min for 1,000 samples (parallel with joblib)
        """
        try:
            # Step 1: Extract training data
            train_samples = dataset.get_train_samples()

            X_train = np.array([
                sample.features.to_flat_array()
                for sample in train_samples
            ])
            y_train = np.array([sample.label for sample in train_samples])

            # Step 2: 5-fold stratified CV
            cv_scores = self._cross_validate(
                X_train, y_train, n_folds
            )
            cv_accuracy = np.mean(cv_scores)

            logger.info(
                f"5-fold CV accuracy: {cv_accuracy:.4f} "
                f"(current: {self.current_accuracy:.4f}, "
                f"target: ≥{self.current_accuracy + self.min_improvement:.4f})"
            )

            # Step 3: Validate quality gate
            if cv_accuracy < self.current_accuracy + self.min_improvement:
                return Err(
                    f"New model accuracy {cv_accuracy:.4f} below threshold "
                    f"{self.current_accuracy + self.min_improvement:.4f}. "
                    f"Improvement: {cv_accuracy - self.current_accuracy:.4f} "
                    f"(required: ≥{self.min_improvement:.4f})"
                )

            # Step 4: Train final ensemble on full training set
            ensemble = self._train_ensemble(X_train, y_train)

            # Step 5: Validate on validation set
            val_samples = dataset.get_val_samples()
            X_val = np.array([
                sample.features.to_flat_array()
                for sample in val_samples
            ])
            y_val = np.array([sample.label for sample in val_samples])

            val_accuracy = ensemble.score(X_val, y_val)

            # Calculate false negative rate (complex tasks misclassified)
            y_pred = ensemble.predict(X_val)
            false_negatives = np.sum((y_val == 3) & (y_pred != 3))  # P1=3 is complex
            total_complex = np.sum(y_val == 3)
            fn_rate = false_negatives / total_complex if total_complex > 0 else 0.0

            # Step 6: Create EnsembleModel
            model = EnsembleModel(
                ensemble=ensemble,
                training_date=datetime.now(UTC).isoformat(),
                validation_accuracy=val_accuracy,
                false_negative_rate=fn_rate,
                feature_count=X_train.shape[1],
                training_sample_count=len(train_samples)
            )

            logger.info(
                f"Trained model: CV accuracy {cv_accuracy:.4f}, "
                f"Val accuracy {val_accuracy:.4f}, FN rate {fn_rate:.4f}"
            )

            return Ok((model, cv_accuracy))

        except Exception as e:
            return Err(f"Failed to retrain model: {e}")

    def _cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_folds: int
    ) -> np.ndarray:
        """
        5-fold stratified CV.

        Args:
            X: Feature matrix (n_samples, 1644)
            y: Labels (n_samples,)
            n_folds: Number of folds

        Returns:
            Array of CV scores (one per fold)
        """
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        cv_scores = []

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y[train_idx], y[val_idx]

            # Train ensemble
            ensemble = self._train_ensemble(X_fold_train, y_fold_train)

            # Validate
            fold_accuracy = ensemble.score(X_fold_val, y_fold_val)
            cv_scores.append(fold_accuracy)

            logger.debug(f"Fold {fold_idx + 1}/{n_folds}: accuracy {fold_accuracy:.4f}")

        return np.array(cv_scores)

    def _train_ensemble(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> VotingClassifier:
        """
        Train RandomForest + GradientBoosting ensemble.

        Hyperparameters fixed from Phase 2 (no tuning).

        Args:
            X: Feature matrix
            y: Labels

        Returns:
            Trained VotingClassifier
        """
        rf = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1  # Parallel training
        )

        gb = GradientBoostingClassifier(
            n_estimators=50,
            random_state=42
        )

        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb)],
            voting="soft"  # Use probability estimates
        )

        ensemble.fit(X, y)

        return ensemble
```

### 5.5 Weekly Retraining Scheduler

```bash
#!/bin/bash
# Weekly retraining scheduler (cron job)
# Schedule: Every Sunday 2am UTC
# File: scripts/setup_weekly_retraining.sh

set -euo pipefail

# Configuration
LOCKFILE="/tmp/retraining_pipeline.lock"
LOG_DIR="logs/retraining"
ALERT_EMAIL="ops@agency.com"

# Create log directory
mkdir -p "$LOG_DIR"

# Acquire lockfile (prevent concurrent runs)
if ! mkdir "$LOCKFILE" 2>/dev/null; then
    echo "Retraining already running (lockfile exists)"
    exit 1
fi

# Cleanup on exit
trap 'rmdir "$LOCKFILE"' EXIT

# Log timestamp
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/retraining_$TIMESTAMP.log"

echo "Starting weekly retraining pipeline at $(date -u)" | tee -a "$LOG_FILE"

# Run retraining pipeline
python tools/ml_routing/weekly_retraining_pipeline.py 2>&1 | tee -a "$LOG_FILE"

# Check exit code
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "Retraining completed successfully" | tee -a "$LOG_FILE"
else
    echo "Retraining failed" | tee -a "$LOG_FILE"

    # Send alert
    mail -s "ML Retraining FAILED" "$ALERT_EMAIL" < "$LOG_FILE"

    exit 1
fi

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "retraining_*.log" -mtime +30 -delete

echo "Pipeline finished at $(date -u)" | tee -a "$LOG_FILE"
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `PredictionLog` Pydantic schema (spec-007, Phase 3 deliverable)
- **Dependency 2**: `TrainingDataset` Pydantic schema (spec-005, Phase 2 deliverable)
- **Dependency 3**: `EnsembleModel` Pydantic schema (spec-006, Phase 2 deliverable)
- **Dependency 4**: VectorStore with prediction logs (spec-007, Phase 3 production data)

### External Dependencies

- **External Dep 1**: scikit-learn>=1.3.0 (StratifiedKFold, ensemble models)
- **External Dep 2**: numpy (array operations, CV splits)
- **External Dep 3**: joblib (parallel training, model serialization)

### Technical Constraints

- **Constraint 1**: Training time <30 min for 1,000 samples (parallel training required)
- **Constraint 2**: VectorStore query <5s for 1,000 predictions (indexed queries required)
- **Constraint 3**: Minimum 100 new samples required for retraining (data sufficiency)
- **Constraint 4**: Model versioning via semantic versioning (v1.0, v1.1, v2.0)

### Business Constraints

- **Constraint 1**: Accuracy improvement ≥0.5% required for deployment (quality gate)
- **Constraint 2**: Rollback within 5 min if new model degrades >3% (reliability)
- **Constraint 3**: Weekly schedule (Sunday 2am UTC, non-critical hours)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Insufficient new data (<100 samples)** - *Mitigation*: Skip retraining, retry next week with 14-day window
- **Risk 2**: **New model degrades accuracy (<current - 3%)** - *Mitigation*: Automatic rollback, alert ops team

### Medium Risk Items

- **Risk 3**: **Training timeout (>30 min)** - *Mitigation*: Parallel training with joblib, kill if timeout exceeded
- **Risk 4**: **Class imbalance in new data** - *Mitigation*: Undersample majority tier to ±10% of minority

### Low Risk Items

- **Risk 5**: **VectorStore query timeout** - *Mitigation*: Retry 3x with exponential backoff
- **Risk 6**: **Disk full during model save** - *Mitigation*: Check disk space before training, alert if <10GB free

### Constitutional Risks

- **Constitutional Risk 1**: **Article IV violation (predictions not used)** - *Mitigation*: Assert VectorStore query success in tests
- **Constitutional Risk 2**: **Article I violation (partial CV folds)** - *Mitigation*: Validate all 5 folds complete before averaging

---

## Testing Strategy

### Test Categories

#### Unit Tests (20+ tests)

1. **PredictionQueryService Tests** (6 tests)
   - Query 7-day window (success, no data, timeout)
   - Filter by confidence ≥0.6 (boundary testing)
   - Deduplicate by task_id (keep latest)
   - Cross-session query (`include_session=False`)

2. **TrainingDataMerger Tests** (8 tests)
   - Merge datasets (existing + new predictions)
   - Deduplicate samples (remove duplicates by task_id)
   - Balance classes (undersample majority tier)
   - Stratified split (80/20, preserve class distribution)
   - Version increment (v1.0 → v1.1, v1.9 → v2.0)

3. **ModelRetrainer Tests** (6 tests)
   - 5-fold CV (validate accuracy ≥current + 0.5%)
   - Training timeout (<30 min for 1,000 samples)
   - Quality gate (reject if accuracy <threshold)
   - Ensemble training (RandomForest + GradientBoosting)

#### Integration Tests (10+ tests)

1. **End-to-End Pipeline** (4 tests)
   - Full pipeline: VectorStore → merge → train → validate → save
   - Insufficient data: Skip retraining if <100 new samples
   - Model degradation: Rollback if accuracy <current - 3%
   - Weekly schedule: Cron job triggers correctly

2. **VectorStore Integration** (3 tests)
   - Query predictions with filters (confidence, actual_tier)
   - Cross-session learning (`include_session=False`)
   - Deduplication across sessions (task_id uniqueness)

3. **Model Deployment** (3 tests)
   - A/B test with new model (10% traffic)
   - Atomic deployment (all-or-nothing promotion)
   - Rollback mechanism (automatic if degradation detected)

### Test Data Requirements

- **Test Data 1**: 500 PredictionLog instances with ground truth (actual_tier set)
- **Test Data 2**: Existing TrainingDataset (500 samples from Phase 2)
- **Test Data 3**: Trained EnsembleModel (98.2% accuracy from Phase 3)

### Test Environment Requirements

- **Environment 1**: VectorStore with 500+ predictions (7-day window)
- **Environment 2**: `~/.agency/models/` directory with existing models
- **Environment 3**: Scikit-learn 1.3.0+ installed (StratifiedKFold, ensemble)

---

## Implementation Phases

### Phase 4.1: VectorStore Query System (Day 1, 4 hours)

- **Scope**: PredictionQueryService class, query logic, deduplication
- **Deliverables**:
  - `tools/ml_routing/prediction_query_service.py` (200 lines)
  - Unit tests (6 tests, query, filter, dedup)
- **Success Criteria**: Query <5s for 1,000 predictions, dedup >95%

### Phase 4.2: Training Data Merger (Day 1-2, 6 hours)

- **Scope**: TrainingDataMerger class, merge logic, class balancing
- **Deliverables**:
  - `tools/ml_routing/training_data_merger.py` (400 lines)
  - Unit tests (8 tests, merge, dedup, balance, split)
- **Success Criteria**: Merge <10s for 1,000 samples, balance ±10%

### Phase 4.3: Model Retrainer (Day 2-3, 8 hours)

- **Scope**: ModelRetrainer class, 5-fold CV, quality gates
- **Deliverables**:
  - `tools/ml_routing/model_retrainer.py` (350 lines)
  - Unit tests (6 tests, CV, training, validation)
- **Success Criteria**: Train <30 min for 1,000 samples, CV accuracy validated

### Phase 4.4: Weekly Scheduler (Day 3, 4 hours)

- **Scope**: Cron job, lockfile, error handling, alerting
- **Deliverables**:
  - `scripts/setup_weekly_retraining.sh` (150 lines)
  - Integration tests (4 tests, pipeline, schedule)
- **Success Criteria**: Cron triggers Sunday 2am UTC, alerts on failure

### Phase 4.5: Production Validation (Day 3-4, 2 hours)

- **Scope**: End-to-end testing, A/B deployment, monitoring
- **Deliverables**:
  - End-to-end tests (4 tests)
  - Monitoring dashboard (retraining metrics)
- **Success Criteria**: Pipeline runs successfully, metrics logged

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: HybridExecutor, MLClassifier, LearningAgent
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), MLEngineer (retraining validation)

### Review Criteria

- **Completeness**: All retraining components specified (query, merge, train, deploy)
- **Clarity**: Architecture diagrams, code examples, integration points documented
- **Feasibility**: <30 min training time achievable with parallel CV, <5s VectorStore query validated
- **Constitutional Compliance**: Article I-V validated (especially Article IV VectorStore integration)
- **Quality Standards**: Accuracy ≥current + 0.5%, training time <30 min, 100% test pass rate

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **ML Training Approval**: Pending 5-fold CV validation (Phase 4.3)
- [ ] **Final Approval**: Pending after Phase 4.4 implementation (weekly scheduler)

---

## Appendices

### Appendix A: Glossary

- **Incremental Learning**: Training on new data while preserving knowledge from old data (merge strategy)
- **5-Fold CV**: Cross-validation technique that splits data into 5 subsets, trains on 4, validates on 1 (repeated 5 times)
- **Stratified Split**: Train/val split that preserves class distribution (same % of P1/P2/P3 in both sets)
- **Semantic Versioning**: Version scheme (v{major}.{minor}) where minor increments weekly, major on architecture change
- **Class Balancing**: Undersampling majority tier to prevent overfitting (target: ±10% samples per tier)

### Appendix B: References

- **Spec-007**: ML Inference Integration (Leap 5 Phase 3, PredictionLog schema)
- **Spec-006**: Ensemble Model Pydantic (Phase 2, model training)
- **Spec-005**: Advanced Pattern Recognition (Phase 1, feature engineering)
- **ADR-004**: Continuous Learning (VectorStore mandate)
- **ADR-024**: Adaptive Model Router (cost optimization)

### Appendix C: Related Documents

- **Spec**: `specs/spec-008-weekly-retraining-pipeline.md` (this document)
- **Plan**: `plans/plan-008-weekly-retraining-pipeline.md` (to be created after spec approval)
- **Tests**: `tests/test_prediction_query_service.py`, `tests/test_training_data_merger.py`, `tests/test_model_retrainer.py`

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification: VectorStore query, data merger, 5-fold CV, semantic versioning, weekly scheduler |

---

*"From predictions to patterns, from feedback to intelligence, from weekly cycles to continuous evolution."*
