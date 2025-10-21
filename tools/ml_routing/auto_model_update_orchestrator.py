"""
AutoModelUpdateOrchestrator: End-to-end retraining → A/B rollout pipeline.

Orchestrates complete model update workflow:
1. Trigger WeeklyRetrainingScheduler (merge data, retrain, validate)
2. Validate accuracy improvement ≥ 0.5% threshold
3. If improvement sufficient:
   a. Normal mode: Start ABRolloutController (10% → 50% → 100%)
   b. Emergency mode: Immediate 100% deployment (skip A/B)
4. Store pipeline execution metadata to VectorStore (Article IV)

Constitutional Compliance:
- Article I: Complete context (validate each stage before proceeding)
- Article II: 100% verification (Result pattern, accuracy thresholds)
- Article III: Automated pipeline (no manual intervention)
- Article IV: VectorStore integration (pipeline metadata storage)
- Article V: Spec-driven (follows task requirements)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines each

Reference: Task description - AutoModelUpdateOrchestrator implementation
Author: CodingAgent
Date: 2025-10-10
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result
from tools.ml_routing.ab_rollout_controller import ABRolloutController, RolloutConfig
from tools.ml_routing.model_artifact_manager import ModelArtifactManager
from tools.ml_routing.weekly_retraining_scheduler import (
    RetrainingReport,
    SchedulerConfig,
    WeeklyRetrainingScheduler,
)

logger = logging.getLogger(__name__)


class OrchestrationError(str, Enum):
    """Error types for orchestration pipeline."""

    RETRAINING_FAILED = "retraining_failed"
    ACCURACY_BELOW_THRESHOLD = "accuracy_below_threshold"
    ROLLOUT_FAILED = "rollout_failed"
    ARTIFACT_LOAD_FAILED = "artifact_load_failed"
    EMERGENCY_DEPLOY_FAILED = "emergency_deploy_failed"


class OrchestratorConfig(BaseModel):
    """
    Configuration for AutoModelUpdateOrchestrator.

    Fields:
        retraining_enabled: Enable retraining stage (default: True)
        ab_rollout_enabled: Enable A/B rollout stage (default: True)
        emergency_mode: Skip A/B testing, immediate 100% (default: False)
        min_accuracy_improvement: Required accuracy improvement (default: 0.5%)
        model_output_dir: Directory for model artifacts (default: "models")

    Example:
        >>> config = OrchestratorConfig(emergency_mode=True)
        >>> config.ab_rollout_enabled  # Ignored in emergency mode
        True
        >>> config.emergency_mode
        True
    """

    retraining_enabled: bool = Field(default=True, description="Enable retraining stage")

    ab_rollout_enabled: bool = Field(default=True, description="Enable A/B rollout stage")

    emergency_mode: bool = Field(
        default=False,
        description="Emergency mode: skip A/B, immediate 100% deployment",
    )

    min_accuracy_improvement: float = Field(
        default=0.005,
        ge=0.0,
        le=1.0,
        description="Required accuracy improvement (0.5%)",
    )

    model_output_dir: str = Field(default="models", description="Model artifact directory")


class UpdateResult(BaseModel):
    """
    Result of pipeline execution with stage completion status.

    Fields:
        success: Overall pipeline success (True if deployed, False if rollback)
        version: Model version deployed or attempted (e.g., "v2.0")
        retraining_completed: True if retraining stage completed
        rollout_completed: True if A/B rollout completed (or skipped)
        new_accuracy: New model validation accuracy
        previous_accuracy: Previous model validation accuracy
        rollback_occurred: True if rollback was triggered
        message: Human-readable pipeline result message

    Example:
        >>> result = UpdateResult(
        ...     success=True,
        ...     version="v2.0",
        ...     retraining_completed=True,
        ...     rollout_completed=True,
        ...     new_accuracy=0.986,
        ...     previous_accuracy=0.980,
        ...     rollback_occurred=False,
        ...     message="Pipeline completed: v2.0 deployed"
        ... )
    """

    success: bool = Field(..., description="Overall pipeline success")
    version: str = Field(..., description="Model version (e.g., 'v2.0')")
    retraining_completed: bool = Field(..., description="Retraining stage completed")
    rollout_completed: bool = Field(..., description="A/B rollout completed")
    new_accuracy: float = Field(..., ge=0.0, le=1.0, description="New model accuracy")
    previous_accuracy: float = Field(..., ge=0.0, le=1.0, description="Previous model accuracy")
    rollback_occurred: bool = Field(..., description="Rollback triggered")
    message: str = Field(..., description="Pipeline result message")


class AutoModelUpdateOrchestrator:
    """
    Orchestrator for end-to-end retraining → A/B rollout pipeline.

    Workflow:
    1. Call WeeklyRetrainingScheduler.run_retraining()
       - Merge VectorStore predictions with training data
       - Retrain ensemble model with 5-fold CV
       - Validate accuracy improvement ≥ 0.5%
       - Serialize artifacts

    2. If retraining successful (accuracy improved ≥ 0.5%):
       a. Normal mode: Start A/B rollout via ABRolloutController
          - Stage 1: 10% traffic → 16 hours
          - Stage 2: 50% traffic → 16 hours
          - Stage 3: 100% traffic → 16 hours
          - Rollback if new_accuracy < current - 2%

       b. Emergency mode: Skip A/B testing
          - Immediate 100% deployment via ModelArtifactManager
          - Update ensemble_active.pkl symlink

    3. Store pipeline execution metadata to VectorStore (Article IV)

    Constitutional Requirements:
    - Article I: Complete context (validate each stage before proceeding)
    - Article III: Automated pipeline (no manual intervention)

    Example:
        >>> context = create_agent_context(session_id="pipeline_001")
        >>> config = OrchestratorConfig(emergency_mode=False)
        >>> orchestrator = AutoModelUpdateOrchestrator(context, config)
        >>> result = orchestrator.execute_pipeline()
        >>> if result.is_ok():
        ...     print(f"Pipeline: {result.unwrap().message}")
    """

    def __init__(
        self,
        context: AgentContext,
        config: OrchestratorConfig,
        scheduler: WeeklyRetrainingScheduler | None = None,
        artifact_manager: ModelArtifactManager | None = None,
    ):
        """
        Initialize AutoModelUpdateOrchestrator.

        Args:
            context: AgentContext for VectorStore access (Article IV)
            config: OrchestratorConfig with pipeline settings
            scheduler: Optional WeeklyRetrainingScheduler (for testing)
            artifact_manager: Optional ModelArtifactManager (for testing)
        """
        self.context = context
        self.config = config

        # Initialize pipeline components (allow dependency injection for testing)
        if scheduler is None:
            scheduler_config = SchedulerConfig(
                model_output_dir=config.model_output_dir,
                min_accuracy_improvement=config.min_accuracy_improvement,
            )
            self.scheduler = WeeklyRetrainingScheduler(context=context, config=scheduler_config)
        else:
            self.scheduler = scheduler

        if artifact_manager is None:
            self.artifact_manager = ModelArtifactManager(models_dir=Path(config.model_output_dir))
        else:
            self.artifact_manager = artifact_manager

        logger.info(
            f"AutoModelUpdateOrchestrator initialized: emergency_mode={config.emergency_mode}"
        )

    def execute_pipeline(self) -> Result[UpdateResult, str]:
        """
        Execute end-to-end retraining → A/B rollout pipeline.

        Returns:
            Result[UpdateResult, str] - Ok(result) or Err(message)

        Workflow:
        1. Call WeeklyRetrainingScheduler.run_retraining()
        2. Validate accuracy improvement ≥ min_accuracy_improvement
        3. If emergency mode: Immediate 100% deployment
           Else: A/B rollout via ABRolloutController
        4. Store pipeline metadata to VectorStore (Article IV)

        Constitutional Requirements:
        - Article I: Complete context (validate all stages)
        - Article III: Automated pipeline (no manual intervention)
        """
        logger.info("Starting AutoModelUpdateOrchestrator pipeline...")

        # Stage 1: Retraining
        if not self.config.retraining_enabled:
            return Err("Retraining disabled in config")

        retraining_result = self._execute_retraining_stage()
        if retraining_result.is_err():
            return Err(f"Retraining failed: {retraining_result.unwrap_err()}")

        retraining_report = retraining_result.unwrap()

        # Validate accuracy improvement
        improvement_check = self._validate_accuracy_improvement(retraining_report)
        if improvement_check.is_err():
            # Insufficient improvement - stop pipeline but return Ok
            # (retraining succeeded, just didn't meet threshold)
            return Ok(
                UpdateResult(
                    success=False,
                    version=retraining_report.version,
                    retraining_completed=True,
                    rollout_completed=False,
                    new_accuracy=retraining_report.new_accuracy,
                    previous_accuracy=retraining_report.previous_accuracy,
                    rollback_occurred=False,
                    message=improvement_check.unwrap_err(),
                )
            )

        # Stage 2: Rollout (A/B or emergency)
        rollout_result = self._execute_rollout_stage(retraining_report)

        # Store pipeline metadata (Article IV)
        self._store_pipeline_metadata(retraining_report, rollout_result)

        return rollout_result

    def _execute_retraining_stage(self) -> Result[RetrainingReport, str]:
        """
        Execute retraining stage via WeeklyRetrainingScheduler.

        Returns:
            Result[RetrainingReport, str] - Ok(report) or Err(message)

        Article I: Complete context (validate retraining before proceeding)
        """
        logger.info("Stage 1: Running WeeklyRetrainingScheduler...")

        retraining_result = self.scheduler.run_retraining()

        if retraining_result.is_err():
            return Err(retraining_result.unwrap_err())

        report = retraining_result.unwrap()

        logger.info(
            f"Retraining completed: {report.version}, "
            f"accuracy={report.new_accuracy:.3f} (+{report.accuracy_improvement:.3%})"
        )

        return Ok(report)

    def _validate_accuracy_improvement(self, report: RetrainingReport) -> Result[None, str]:
        """
        Validate accuracy improvement meets threshold.

        Args:
            report: RetrainingReport from retraining stage

        Returns:
            Result[None, str] - Ok(None) if sufficient, Err(message) if not

        Article II: 100% verification (accuracy thresholds)
        """
        if report.accuracy_improvement < self.config.min_accuracy_improvement:
            message = (
                f"Accuracy improvement below threshold: "
                f"{report.accuracy_improvement:.3%} < "
                f"{self.config.min_accuracy_improvement:.3%} (min required). "
                f"Rollout skipped."
            )
            logger.warning(message)
            return Err(message)

        return Ok(None)

    def _execute_rollout_stage(
        self, retraining_report: RetrainingReport
    ) -> Result[UpdateResult, str]:
        """
        Execute rollout stage (A/B or emergency).

        Args:
            retraining_report: RetrainingReport from retraining stage

        Returns:
            Result[UpdateResult, str] - Ok(result) or Err(message)

        Workflow:
        - Emergency mode: Immediate 100% deployment (skip A/B)
        - Normal mode: A/B rollout via ABRolloutController

        Article III: Automated rollout (no manual intervention)
        """
        if self.config.emergency_mode:
            return self._execute_emergency_deployment(retraining_report)

        if not self.config.ab_rollout_enabled:
            return Ok(
                UpdateResult(
                    success=True,
                    version=retraining_report.version,
                    retraining_completed=True,
                    rollout_completed=False,
                    new_accuracy=retraining_report.new_accuracy,
                    previous_accuracy=retraining_report.previous_accuracy,
                    rollback_occurred=False,
                    message=(
                        f"Retraining completed: {retraining_report.version}, "
                        f"A/B rollout skipped (disabled in config)"
                    ),
                )
            )

        return self._execute_ab_rollout(retraining_report)

    def _execute_emergency_deployment(
        self, retraining_report: RetrainingReport
    ) -> Result[UpdateResult, str]:
        """
        Execute emergency deployment: immediate 100% (skip A/B).

        Args:
            retraining_report: RetrainingReport from retraining stage

        Returns:
            Result[UpdateResult, str] - Ok(result) or Err(message)

        Article III: Automated emergency deployment
        """
        logger.warning(f"Emergency mode: Immediate 100% deployment of {retraining_report.version}")

        # Update active symlink to new model (immediate deployment)
        symlink_result = self.artifact_manager._update_active_symlink(
            Path(retraining_report.artifact_path)
        )

        if symlink_result.is_err():
            return Err(f"Emergency deployment failed: {symlink_result.unwrap_err()}")

        logger.info(f"Emergency deployment completed: {retraining_report.version}")

        return Ok(
            UpdateResult(
                success=True,
                version=retraining_report.version,
                retraining_completed=True,
                rollout_completed=False,  # A/B skipped
                new_accuracy=retraining_report.new_accuracy,
                previous_accuracy=retraining_report.previous_accuracy,
                rollback_occurred=False,
                message=(
                    f"Emergency mode: {retraining_report.version} deployed "
                    f"immediately (100%, A/B skipped)"
                ),
            )
        )

    def _execute_ab_rollout(self, retraining_report: RetrainingReport) -> Result[UpdateResult, str]:
        """
        Execute A/B rollout via ABRolloutController.

        Args:
            retraining_report: RetrainingReport from retraining stage

        Returns:
            Result[UpdateResult, str] - Ok(result) or Err(message)

        Article III: Automated A/B rollout with rollback
        """
        logger.info(f"Stage 2: Starting A/B rollout for {retraining_report.version}...")

        # Infer current model version from retraining report
        current_version = self._infer_current_version(retraining_report.version)

        # Create rollout controller
        rollout_controller = self._create_rollout_controller(
            new_version=retraining_report.version,
            current_version=current_version,
        )

        # Execute rollout
        rollout_result = rollout_controller.execute_rollout()

        if rollout_result.is_err():
            return Err(f"Rollout failed: {rollout_result.unwrap_err()}")

        rollout = rollout_result.unwrap()

        # Build UpdateResult from rollout outcome
        return Ok(
            UpdateResult(
                success=rollout.success,
                version=retraining_report.version,
                retraining_completed=True,
                rollout_completed=rollout.success,
                new_accuracy=rollout.new_model_accuracy,
                previous_accuracy=rollout.current_model_accuracy,
                rollback_occurred=rollout.rollback_triggered,
                message=rollout.message,
            )
        )

    def _create_rollout_controller(
        self, new_version: str, current_version: str
    ) -> ABRolloutController:
        """
        Create ABRolloutController with default config.

        Args:
            new_version: New model version (e.g., "v2.0")
            current_version: Current model version (e.g., "v1.0")

        Returns:
            ABRolloutController instance
        """
        rollout_config = RolloutConfig()  # Default: 10% → 50% → 100%

        return ABRolloutController(
            context=self.context,
            config=rollout_config,
            new_model_version=new_version,
            current_model_version=current_version,
            models_dir=Path(self.config.model_output_dir),
        )

    def _infer_current_version(self, new_version: str) -> str:
        """
        Infer current model version from new version.

        Args:
            new_version: New model version (e.g., "v2.0")

        Returns:
            Current model version (e.g., "v1.0")

        Example:
            >>> orchestrator._infer_current_version("v2.0")
            "v1.0"
            >>> orchestrator._infer_current_version("v1.1")
            "v1.0"
        """
        # Parse version (e.g., "v2.0" → (2, 0))
        version_str = new_version.lstrip("v")
        parts = version_str.split(".")

        if len(parts) != 2:
            return "v1.0"  # Default fallback

        major, minor = int(parts[0]), int(parts[1])

        # Decrement minor version (v2.1 → v2.0)
        if minor > 0:
            return f"v{major}.{minor - 1}"

        # Decrement major version (v2.0 → v1.0)
        if major > 1:
            return f"v{major - 1}.0"

        return "v1.0"  # Minimum version

    def _store_pipeline_metadata(
        self,
        retraining_report: RetrainingReport,
        rollout_result: Result[UpdateResult, str],
    ) -> None:
        """
        Store pipeline execution metadata to VectorStore (Article IV).

        Args:
            retraining_report: RetrainingReport from retraining stage
            rollout_result: Result[UpdateResult, str] from rollout stage

        Article IV: Cross-session learning via VectorStore
        """
        # Extract rollout info (if available)
        if rollout_result.is_ok():
            update_result = rollout_result.unwrap()
            rollout_success = update_result.success
            rollback_occurred = update_result.rollback_occurred
            message = update_result.message
        else:
            rollout_success = False
            rollback_occurred = False
            message = rollout_result.unwrap_err()

        # Build metadata content
        content = {
            "version": retraining_report.version,
            "retraining_completed": True,
            "rollout_completed": rollout_success,
            "new_accuracy": retraining_report.new_accuracy,
            "previous_accuracy": retraining_report.previous_accuracy,
            "accuracy_improvement": retraining_report.accuracy_improvement,
            "rollback_occurred": rollback_occurred,
            "emergency_mode": self.config.emergency_mode,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
            "confidence": min(retraining_report.new_accuracy, 1.0),
        }

        # Store to VectorStore
        self.context.store_memory(
            key=f"pipeline_execution_{retraining_report.version}_{datetime.now(UTC).isoformat()}",
            content=content,
            tags=["orchestrator", "pipeline", "leap5_phase4", "auto_update"],
        )

        logger.info(f"Pipeline metadata stored to VectorStore: {retraining_report.version}")
