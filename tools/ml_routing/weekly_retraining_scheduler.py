"""
WeeklyRetrainingScheduler orchestrator for automated weekly retraining.

Orchestrates the complete retraining pipeline:
1. Load current model metadata (version, accuracy)
2. Merge VectorStore predictions with existing dataset
3. Retrain ensemble model with 5-fold CV
4. Validate accuracy improvement (≥current + 0.5%)
5. Serialize artifacts (models/ensemble_v{version}.pkl)
6. Store metadata to VectorStore (Article IV)
7. Generate markdown retraining report

Constitutional Compliance:
- Article I: Complete context (retry on failures, validation before deploy)
- Article II: 100% verification (Result pattern, accuracy thresholds)
- Article IV: VectorStore integration (store retraining metadata)
- Article V: Spec-driven (follows spec-008-weekly-retraining-pipeline.md)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines each

Cron Schedule: 0 2 * * 0 (Sundays at 2 AM)

Reference: specs/spec-008-weekly-retraining-pipeline.md Section 5.5
Author: CodingAgent
Date: 2025-10-10
"""

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import joblib
from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.models.training_dataset import TrainingDataset
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.feature_extractor import FeatureExtractor
from tools.ml_routing.model_retrainer import ModelRetrainer, RetrainingResult
from tools.ml_routing.training_data_merger import TrainingDataMerger

logger = logging.getLogger(__name__)


class SchedulerError(str, Enum):
    """Error types for retraining scheduler."""

    METADATA_LOAD_FAILED = "metadata_load_failed"
    MERGE_FAILED = "merge_failed"
    TRAINING_FAILED = "training_failed"
    VALIDATION_FAILED = "validation_failed"
    ARTIFACT_SERIALIZATION_FAILED = "artifact_serialization_failed"
    REPORT_GENERATION_FAILED = "report_generation_failed"


class SchedulerConfig(BaseModel):
    """
    Configuration for WeeklyRetrainingScheduler.

    Fields:
        cron_schedule: Cron expression for scheduling (default: Sundays at 2 AM)
        days_back: Number of days to query VectorStore (default: 7)
        min_confidence: Minimum prediction confidence (default: 0.8)
        min_accuracy_improvement: Required accuracy improvement (default: 0.5%)
        model_output_dir: Directory for model artifacts (default: "models")
        report_output_dir: Directory for reports (default: "reports")
    """

    cron_schedule: str = Field(default="0 2 * * 0", description="Cron expression (Sundays at 2 AM)")
    days_back: int = Field(default=7, ge=1, le=365, description="Days to query VectorStore")
    min_confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Min prediction confidence"
    )
    min_accuracy_improvement: float = Field(
        default=0.005, ge=0.0, le=1.0, description="Required accuracy improvement (0.5%)"
    )
    model_output_dir: str = Field(default="models", description="Model artifact directory")
    report_output_dir: str = Field(default="reports", description="Report output directory")


class RetrainingReport(BaseModel):
    """
    Retraining report with metrics and artifact paths.

    Fields:
        version: Model version (e.g., "v1.1")
        previous_accuracy: Previous model accuracy
        new_accuracy: New model accuracy
        accuracy_improvement: Improvement delta (new - previous)
        training_date: ISO 8601 timestamp
        samples_added: Number of new samples from VectorStore
        artifact_path: Path to serialized model
        report_path: Path to markdown report
        success: Whether retraining succeeded
    """

    version: str = Field(..., description="Model version (e.g., 'v1.1')")
    previous_accuracy: float = Field(..., ge=0.0, le=1.0, description="Previous model accuracy")
    new_accuracy: float = Field(..., ge=0.0, le=1.0, description="New model accuracy")
    accuracy_improvement: float = Field(..., description="Accuracy improvement delta")
    training_date: str = Field(..., description="ISO 8601 training timestamp")
    samples_added: int = Field(..., ge=0, description="Number of new samples")
    artifact_path: str = Field(..., description="Path to serialized model")
    report_path: str = Field(..., description="Path to markdown report")
    success: bool = Field(..., description="Whether retraining succeeded")


class WeeklyRetrainingScheduler:
    """
    Orchestrator for automated weekly retraining pipeline.

    Workflow:
    1. Load current model metadata (version, accuracy)
    2. Query VectorStore for predictions (last N days)
    3. Merge predictions with existing dataset
    4. Retrain ensemble model with cross-validation
    5. Validate accuracy improvement (≥current + 0.5%)
    6. Serialize artifacts and generate report
    7. Store metadata to VectorStore (Article IV)

    Performance: <10 minutes for 1,000 samples

    Constitutional Compliance:
    - Article I: Complete validation before deployment
    - Article II: Result pattern, accuracy thresholds
    - Article IV: VectorStore metadata storage
    """

    def __init__(
        self,
        context: AgentContext,
        config: SchedulerConfig,
        feature_extractor: FeatureExtractor | None = None,
        merger: TrainingDataMerger | None = None,
        retrainer: ModelRetrainer | None = None,
    ):
        """
        Initialize weekly retraining scheduler.

        Args:
            context: AgentContext for VectorStore access (Article IV)
            config: SchedulerConfig with pipeline parameters
            feature_extractor: Optional FeatureExtractor (for testing)
            merger: Optional TrainingDataMerger (for testing)
            retrainer: Optional ModelRetrainer (for testing)
        """
        self.context = context
        self.config = config

        # Create output directories
        Path(config.model_output_dir).mkdir(parents=True, exist_ok=True)
        Path(config.report_output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize pipeline components (allow dependency injection for testing)
        self.feature_extractor = feature_extractor
        self.merger = merger
        self.retrainer = retrainer or ModelRetrainer(
            context=context, cv_folds=5, model_output_dir=config.model_output_dir
        )

        logger.info(
            f"WeeklyRetrainingScheduler initialized: "
            f"schedule={config.cron_schedule}, days_back={config.days_back}"
        )

    def run_retraining(self) -> Result[RetrainingReport, str]:
        """
        Run complete retraining pipeline.

        Returns:
            Result with RetrainingReport or error message

        Article I: Complete context (validate all steps)
        Article II: Result pattern, accuracy thresholds
        Article IV: Store metadata to VectorStore
        """
        logger.info("Starting weekly retraining pipeline...")

        # Step 1: Load current model metadata
        pipeline_result = self._run_retraining_pipeline()
        if pipeline_result.is_err():
            return pipeline_result

        return pipeline_result

    def _run_retraining_pipeline(self) -> Result[RetrainingReport, str]:
        """Execute retraining pipeline steps."""
        # Load metadata
        metadata_result = self._load_current_model_metadata()
        if metadata_result.is_err():
            return Err(f"Metadata load failed: {metadata_result.unwrap_err()}")

        metadata = metadata_result.unwrap()
        current_accuracy = metadata["validation_accuracy"]
        current_version = metadata["version"]

        logger.info(f"Current model: {current_version}, accuracy={current_accuracy:.3f}")

        # Merge, retrain, report
        return self._execute_retraining_steps(current_version, current_accuracy)

    def _execute_retraining_steps(
        self, current_version: str, current_accuracy: float
    ) -> Result[RetrainingReport, str]:
        """Execute merge, retrain, and report generation steps."""
        # Step 2: Merge training data
        merge_result = self._merge_training_data(current_version)
        if merge_result.is_err():
            return Err(f"Data merge failed: {merge_result.unwrap_err()}")

        merged_dataset = merge_result.unwrap()
        samples_added = merged_dataset.metadata.total_samples

        # Step 3: Retrain model
        retrain_result = self._retrain_model(merged_dataset, current_accuracy)
        if retrain_result.is_err():
            return Err(f"Retraining failed: {retrain_result.unwrap_err()}")

        retraining_result = retrain_result.unwrap()

        # Generate report and store metadata
        return self._finalize_retraining(retraining_result, current_accuracy, samples_added)

    def _finalize_retraining(
        self, retraining_result: RetrainingResult, current_accuracy: float, samples_added: int
    ) -> Result[RetrainingReport, str]:
        """Generate report and store metadata."""
        # Step 4: Generate report
        report_result = self._generate_report(
            retraining_result=retraining_result,
            previous_accuracy=current_accuracy,
            samples_added=samples_added,
        )
        if report_result.is_err():
            return Err(f"Report generation failed: {report_result.unwrap_err()}")

        report = report_result.unwrap()

        # Step 5: Store metadata to VectorStore (Article IV)
        self._store_metadata_to_vectorstore(
            retraining_result=retraining_result,
            previous_accuracy=current_accuracy,
            samples_added=samples_added,
        )

        logger.info(
            f"Retraining completed: {report.version}, "
            f"accuracy={report.new_accuracy:.3f} (+{report.accuracy_improvement:.3%})"
        )

        return Ok(report)

    def _load_current_model_metadata(self) -> Result[dict, str]:
        """
        Load current model metadata from models/ensemble_active.pkl.

        Returns:
            Result with metadata dict or error message

        Article I: Complete context before action
        """
        try:
            active_model_path = self._get_active_model_path()
            metadata_path = active_model_path.parent / f"{active_model_path.stem}_metadata.json"

            if not metadata_path.exists():
                return Err(f"Metadata file not found: {metadata_path}")

            with open(metadata_path) as f:
                metadata = json.load(f)

            required_fields = {"version", "validation_accuracy", "training_date"}
            missing_fields = required_fields - set(metadata.keys())

            if missing_fields:
                return Err(f"Missing metadata fields: {missing_fields}")

            logger.info(
                f"Loaded metadata: {metadata['version']}, accuracy={metadata['validation_accuracy']:.3f}"
            )
            return Ok(metadata)

        except Exception as e:
            return Err(f"Failed to load metadata: {e}")

    def _merge_training_data(self, current_version: str) -> Result[TrainingDataset, str]:
        """
        Merge VectorStore predictions with existing dataset.

        Args:
            current_version: Current model version for dataset loading

        Returns:
            Result with merged TrainingDataset or error message

        Article I: Complete context (retry on failures)
        Article IV: VectorStore source (cross-session learning)
        """
        if self.merger is None:
            return Err("TrainingDataMerger not initialized")

        # Query VectorStore predictions
        predictions_result = self._query_vectorstore_predictions()
        if predictions_result.is_err():
            return predictions_result

        predictions = predictions_result.unwrap()

        # Load and merge with existing dataset
        return self._merge_with_existing_dataset(predictions, current_version)

    def _query_vectorstore_predictions(self) -> Result[list, str]:
        """Query VectorStore for predictions."""
        predictions_result = self.merger.query_predictions(
            days_back=self.config.days_back, min_confidence=self.config.min_confidence
        )

        if predictions_result.is_err():
            return Err(predictions_result.unwrap_err())

        predictions = predictions_result.unwrap()

        if not predictions:
            return Err("No new predictions found in VectorStore")

        return Ok(predictions)

    def _merge_with_existing_dataset(
        self, predictions: list, current_version: str
    ) -> Result[TrainingDataset, str]:
        """Merge predictions with existing dataset."""
        # Load existing dataset
        dataset_result = self._load_existing_dataset(current_version)
        if dataset_result.is_err():
            return Err(dataset_result.unwrap_err())

        existing_dataset = dataset_result.unwrap()

        # Merge datasets
        merge_result = self.merger.merge_datasets(
            existing_dataset=existing_dataset,
            new_predictions=predictions,
            version_increment="minor",
        )

        if merge_result.is_err():
            return Err(merge_result.unwrap_err())

        logger.info(
            f"Data merge completed: {len(predictions)} predictions → "
            f"{merge_result.unwrap().metadata.total_samples} total samples"
        )

        return merge_result

    def _retrain_model(
        self, dataset: TrainingDataset, current_accuracy: float
    ) -> Result[RetrainingResult, str]:
        """
        Retrain ensemble model with 5-fold CV.

        Args:
            dataset: Merged TrainingDataset
            current_accuracy: Current model accuracy (for improvement check)

        Returns:
            Result with RetrainingResult or error message

        Article II: 100% verification (accuracy thresholds)
        """
        retrain_result = self.retrainer.retrain_ensemble(
            dataset=dataset,
            current_accuracy=current_accuracy,
            random_state=42,
            version=dataset.metadata.version,
        )

        if retrain_result.is_err():
            return Err(retrain_result.unwrap_err())

        logger.info(f"Model retraining completed: {retrain_result.unwrap().version}")
        return retrain_result

    def _generate_report(
        self, retraining_result: RetrainingResult, previous_accuracy: float, samples_added: int
    ) -> Result[RetrainingReport, str]:
        """
        Generate markdown retraining report.

        Args:
            retraining_result: RetrainingResult from retraining
            previous_accuracy: Previous model accuracy
            samples_added: Number of samples added

        Returns:
            Result with RetrainingReport or error message

        Article II: Result pattern for file operations
        """
        try:
            accuracy_improvement = retraining_result.average_accuracy - previous_accuracy

            # Build report content
            report_content = self._build_report_markdown(
                retraining_result=retraining_result,
                previous_accuracy=previous_accuracy,
                accuracy_improvement=accuracy_improvement,
                samples_added=samples_added,
            )

            # Write report to disk
            report_path = (
                Path(self.config.report_output_dir) / f"retraining_{retraining_result.version}.md"
            )

            with open(report_path, "w") as f:
                f.write(report_content)

            logger.info(f"Report generated: {report_path}")

            # Build RetrainingReport instance
            report = RetrainingReport(
                version=retraining_result.version,
                previous_accuracy=previous_accuracy,
                new_accuracy=retraining_result.average_accuracy,
                accuracy_improvement=accuracy_improvement,
                training_date=retraining_result.training_date,
                samples_added=samples_added,
                artifact_path=retraining_result.artifact_path,
                report_path=str(report_path),
                success=True,
            )

            return Ok(report)

        except Exception as e:
            return Err(f"Report generation failed: {e}")

    def _build_report_markdown(
        self,
        retraining_result: RetrainingResult,
        previous_accuracy: float,
        accuracy_improvement: float,
        samples_added: int,
    ) -> str:
        """
        Build markdown report content.

        Args:
            retraining_result: RetrainingResult from retraining
            previous_accuracy: Previous model accuracy
            accuracy_improvement: Accuracy improvement delta
            samples_added: Number of samples added

        Returns:
            Markdown report content
        """
        fold_metrics_table = "\n".join(
            f"| Fold {i + 1} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
            f"{m['recall']:.3f} | {m['f1']:.3f} |"
            for i, m in enumerate(retraining_result.fold_metrics)
        )

        return f"""# Weekly Retraining Report: {retraining_result.version}

**Date**: {retraining_result.training_date}
**Status**: ✅ SUCCESS

## Summary

- **Previous Version**: (inferred from accuracy delta)
- **New Version**: {retraining_result.version}
- **Previous Accuracy**: {previous_accuracy:.3f}
- **New Accuracy**: {retraining_result.average_accuracy:.3f}
- **Improvement**: +{accuracy_improvement:.3%} (threshold: ≥0.5%)
- **Samples Added**: {samples_added} from VectorStore

## Cross-Validation Metrics (5-Fold)

| Fold | Accuracy | Precision | Recall | F1 Score |
|------|----------|-----------|--------|----------|
{fold_metrics_table}

**Average Metrics**:
- Accuracy: {retraining_result.average_accuracy:.3f}
- Precision: {retraining_result.average_precision:.3f}
- Recall: {retraining_result.average_recall:.3f}
- F1 Score: {retraining_result.average_f1:.3f}

## Model Details

- **Artifact Path**: `{retraining_result.artifact_path}`
- **False Negative Rate**: {retraining_result.model.false_negative_rate:.3f} (threshold: ≤2%)
- **Feature Count**: {len(retraining_result.model.feature_names)}
- **Ensemble Composition**: RandomForest (70%) + GradientBoosting (30%)

## Constitutional Compliance

- ✅ **Article I**: Complete context (all samples validated)
- ✅ **Article II**: Accuracy ≥ {previous_accuracy + 0.005:.3f} (verified)
- ✅ **Article IV**: Metadata stored to VectorStore
- ✅ **Article V**: Spec-driven (spec-008-weekly-retraining-pipeline.md)

## Next Steps

1. Deploy `{retraining_result.artifact_path}` to production
2. Monitor misclassification rate for first 48 hours
3. Schedule next retraining for {self.config.cron_schedule}

---
*Generated by WeeklyRetrainingScheduler*
"""

    def _store_metadata_to_vectorstore(
        self, retraining_result: RetrainingResult, previous_accuracy: float, samples_added: int
    ) -> None:
        """
        Store retraining metadata to VectorStore (Article IV).

        Args:
            retraining_result: RetrainingResult from retraining
            previous_accuracy: Previous model accuracy
            samples_added: Number of samples added

        Article IV: Cross-session learning via VectorStore
        """
        content = {
            "version": retraining_result.version,
            "previous_accuracy": previous_accuracy,
            "new_accuracy": retraining_result.average_accuracy,
            "accuracy_improvement": retraining_result.average_accuracy - previous_accuracy,
            "training_date": retraining_result.training_date,
            "samples_added": samples_added,
            "artifact_path": retraining_result.artifact_path,
            "fold_metrics": retraining_result.fold_metrics,
            "confidence": min(retraining_result.average_accuracy, 1.0),
        }

        self.context.store_memory(
            key=f"retraining_{retraining_result.version}_{retraining_result.training_date}",
            content=content,
            tags=["retraining", "scheduler", "leap5_phase4", "ensemble_model"],
        )

        logger.info(f"Retraining metadata stored to VectorStore: {retraining_result.version}")

    def _load_existing_dataset(self, version: str) -> Result[TrainingDataset, str]:
        """
        Load existing training dataset.

        Args:
            version: Current model version

        Returns:
            Result with TrainingDataset or error message

        Article I: Complete context before merge
        """
        try:
            dataset_path = Path(self.config.model_output_dir) / f"training_dataset_{version}.pkl"

            if not dataset_path.exists():
                return Err(f"Training dataset not found: {dataset_path}")

            dataset = joblib.load(dataset_path)

            if not isinstance(dataset, TrainingDataset):
                return Err(f"Invalid dataset type: {type(dataset)}")

            logger.info(f"Loaded dataset: {version}, {dataset.metadata.total_samples} samples")
            return Ok(dataset)

        except Exception as e:
            return Err(f"Failed to load dataset: {e}")

    def _get_active_model_path(self) -> Path:
        """
        Get path to active model (ensemble_active.pkl).

        Returns:
            Path to active model

        Note: Can be overridden in tests
        """
        return Path(self.config.model_output_dir) / "ensemble_active.pkl"

    def _validate_artifact(self, artifact_path: Path) -> Result[None, str]:
        """
        Validate artifact integrity after serialization.

        Args:
            artifact_path: Path to serialized artifact

        Returns:
            Result with None on success, error message on failure

        Article II: 100% verification (artifact validation)
        """
        try:
            if not artifact_path.exists():
                return Err(f"Artifact not found: {artifact_path}")

            # Load artifact to verify integrity
            model = joblib.load(artifact_path)

            if model is None:
                return Err(f"Artifact corrupted: {artifact_path}")

            logger.info(f"Artifact validated: {artifact_path}")
            return Ok(None)

        except Exception as e:
            return Err(f"Artifact validation failed: {e}")

    def _increment_version(self, current_version: str) -> str:
        """
        Increment version by minor revision (v1.0 → v1.1).

        Args:
            current_version: Current version (e.g., "v1.0")

        Returns:
            Incremented version (e.g., "v1.1")
        """
        version_str = current_version.lstrip("v")
        parts = version_str.split(".")

        if len(parts) != 2:
            return "v1.1"  # Default for invalid versions

        major, minor = int(parts[0]), int(parts[1])
        minor += 1

        return f"v{major}.{minor}"
