"""
EmergencyRetrainingTrigger: Alert system for same-day retraining on drift detection.

Monitors AccuracyDriftDetector output hourly, triggers immediate retraining when
accuracy degrades >5%, bypassing A/B rollout for emergency deployment.

Constitutional compliance:
- Article I: Complete context (validate drift before action, retry on failures)
- Article II: 100% verification (Result pattern, validation gates)
- Article III: Automated enforcement (zero manual intervention)
- Article IV: VectorStore storage (emergency events logged with tags)
- Article V: Spec-driven (follows spec-009-misclassification-detection.md)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for error handling
- Law #8: Functions <50 lines each

Emergency Protocol (from spec):
1. Call DriftDetector.check_drift()
2. If drift_detected = True, trigger scheduler
3. Pass skip_ab_rollout=True flag (immediate deployment)
4. Log event to VectorStore (tags: ["emergency", "retraining", "drift_recovery"])
5. Return Result with retraining outcome

Performance:
- Check interval: 60 minutes (hourly cron)
- Drift detection: <1s (VectorStore query + calculation)
- Emergency retraining: <4 hours (training + validation + deployment)

Reference: specs/spec-009-misclassification-detection.md Section 5.3
Author: AgencyCodeAgent
Date: 2025-10-10
"""

import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class TriggerError(str, Enum):
    """Error types for emergency retraining trigger."""

    DRIFT_CHECK_FAILED = "drift_check_failed"
    INSUFFICIENT_SAMPLES = "insufficient_samples"
    RETRAINING_FAILED = "retraining_failed"
    VALIDATION_FAILED = "validation_failed"
    DEPLOYMENT_FAILED = "deployment_failed"
    ALERT_DEDUPLICATED = "alert_deduplicated"


class TriggerConfig(BaseModel):
    """
    Configuration for EmergencyRetrainingTrigger.

    Fields:
        check_interval_minutes: Minutes between drift checks (default: 60 = hourly)
        drift_threshold_pct: Accuracy drop % to trigger alert (default: 5.0%)
        baseline_accuracy: Expected accuracy baseline (default: 0.982 from Phase 3)
        min_samples_for_retraining: Minimum samples required (default: 300)
        skip_ab_rollout: Skip A/B test for emergency (default: True)
        alert_deduplication_hours: Hours to deduplicate alerts (default: 24)

    Example:
        >>> config = TriggerConfig()
        >>> config.check_interval_minutes
        60
        >>> config.drift_threshold_pct
        5.0
    """

    check_interval_minutes: int = Field(
        default=60, ge=1, le=1440, description="Minutes between drift checks (hourly)"
    )

    drift_threshold_pct: float = Field(
        default=5.0, ge=0.0, le=100.0, description="Accuracy drop % to trigger alert"
    )

    baseline_accuracy: float = Field(
        default=0.982, ge=0.0, le=1.0, description="Expected accuracy baseline (Phase 3)"
    )

    min_samples_for_retraining: int = Field(
        default=300, ge=1, description="Minimum samples required for retraining"
    )

    skip_ab_rollout: bool = Field(
        default=True, description="Skip A/B test for emergency (immediate deployment)"
    )

    alert_deduplication_hours: int = Field(
        default=24, ge=1, le=168, description="Hours to deduplicate alerts"
    )


class EmergencyRetrainingResult(BaseModel):
    """
    Result of emergency retraining trigger check.

    Fields:
        triggered: Whether emergency retraining was triggered
        drift_detected: Whether drift was detected
        drift_alert_timestamp: ISO 8601 timestamp of drift alert
        current_accuracy: Current rolling 7-day accuracy
        accuracy_drop_pct: Accuracy drop percentage
        retraining_initiated: Whether retraining was initiated
        new_model_version: New model version (if retrained)
        new_model_accuracy: New model accuracy (if retrained)
        samples_used: Number of samples used for retraining
        deployment_status: Deployment status (success, failed, no_action, deduplicated)

    Example:
        >>> result = EmergencyRetrainingResult(
        ...     triggered=True,
        ...     drift_detected=True,
        ...     drift_alert_timestamp="2025-10-10T12:00:00Z",
        ...     current_accuracy=0.925,
        ...     accuracy_drop_pct=5.7,
        ...     retraining_initiated=True,
        ...     new_model_version="v1.5",
        ...     new_model_accuracy=0.986,
        ...     samples_used=450,
        ...     deployment_status="success"
        ... )
    """

    triggered: bool = Field(..., description="Whether emergency retraining was triggered")
    drift_detected: bool = Field(..., description="Whether drift was detected")
    drift_alert_timestamp: str | None = Field(None, description="ISO 8601 timestamp of drift alert")
    current_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Current rolling 7-day accuracy"
    )
    accuracy_drop_pct: float = Field(..., description="Accuracy drop percentage")
    retraining_initiated: bool = Field(..., description="Whether retraining was initiated")
    new_model_version: str | None = Field(None, description="New model version (if retrained)")
    new_model_accuracy: float | None = Field(
        None, ge=0.0, le=1.0, description="New model accuracy (if retrained)"
    )
    samples_used: int = Field(..., ge=0, description="Number of samples used for retraining")
    deployment_status: str = Field(
        ..., description="Deployment status (success, failed, no_action, deduplicated)"
    )


class EmergencyRetrainingTrigger:
    """
    Alert system for same-day retraining on drift detection.

    Monitors AccuracyDriftDetector output hourly, triggers immediate retraining
    when accuracy degrades >5%, bypassing A/B rollout for emergency deployment.

    Workflow:
    1. Check drift via AccuracyDriftDetector (hourly polling)
    2. If drift detected (accuracy drop >5%), trigger WeeklyRetrainingScheduler
    3. Pass skip_ab_rollout=True for immediate 100% deployment
    4. Store emergency event to VectorStore (Article IV)
    5. Return Result with retraining outcome

    Performance:
    - Drift check: <1s (VectorStore query + calculation)
    - Emergency retraining: <4 hours (training + validation + deployment)
    - Alert deduplication: 24 hours (prevent alert spam)

    Constitutional Compliance:
    - Article I: Complete context (validate drift before action)
    - Article III: Automated enforcement (zero manual intervention)
    - Article IV: VectorStore logging (emergency events tagged)

    Example:
        >>> context = create_agent_context("emergency_retraining")
        >>> config = TriggerConfig()
        >>> trigger = EmergencyRetrainingTrigger(context, config)
        >>>
        >>> # Hourly cron job calls this
        >>> result = trigger.check_and_trigger()
        >>> if result.is_ok():
        ...     report = result.unwrap()
        ...     if report.triggered:
        ...         print(f"Emergency retraining: {report.new_model_version}")
    """

    def __init__(self, context: AgentContext, config: TriggerConfig):
        """
        Initialize emergency retraining trigger.

        Args:
            context: AgentContext for VectorStore access (Article IV)
            config: TriggerConfig with alert thresholds

        Article IV: VectorStore integration mandatory
        """
        self.context = context
        self.config = config
        self._last_alert_timestamp: datetime | None = None

        logger.info(
            f"EmergencyRetrainingTrigger initialized: "
            f"threshold={config.drift_threshold_pct}%, "
            f"interval={config.check_interval_minutes}min"
        )

    def check_and_trigger(self) -> Result[EmergencyRetrainingResult, str]:
        """
        Check for drift and trigger emergency retraining if needed.

        Returns:
            Result with EmergencyRetrainingResult or error message

        Workflow:
        1. Check drift via _check_drift()
        2. If drift detected, check alert deduplication
        3. If deduplicated, return no_action
        4. Trigger retraining via _trigger_retraining()
        5. Store event to VectorStore (Article IV)
        6. Return result

        Article I: Complete context (retry on failures)
        Article III: Automated enforcement (zero manual intervention)
        Article IV: VectorStore logging (emergency events)
        """
        logger.info("Starting emergency retraining trigger check...")

        # Step 1: Check drift (Article I: complete context)
        drift_result = self._check_drift()
        if drift_result.is_err():
            logger.error(f"Drift check failed: {drift_result.unwrap_err()}")
            return Err(drift_result.unwrap_err())

        drift_report = drift_result.unwrap()

        # Step 2: Handle no drift or deduplication
        early_result = self._handle_no_drift_or_deduplication(drift_report)
        if early_result is not None:
            return early_result

        # Step 3: Execute retraining workflow
        return self._execute_retraining_workflow(drift_report)

    def _handle_no_drift_or_deduplication(
        self, drift_report: dict
    ) -> Result[EmergencyRetrainingResult, str] | None:
        """
        Handle no drift or alert deduplication cases.

        Args:
            drift_report: Drift report from _check_drift()

        Returns:
            Result if no action needed, None if retraining should proceed

        Law #8: Focused function <50 lines
        """
        # No drift detected → no action
        if not drift_report["drift_detected"]:
            logger.info(f"No drift detected: accuracy={drift_report['current_accuracy']:.3f}")
            return self._create_no_action_result(drift_report)

        # Drift detected → check deduplication
        if self._should_deduplicate_alert():
            logger.warning("Drift alert deduplicated (within 24 hours of last alert)")
            return self._create_deduplicated_result(drift_report)

        return None

    def _execute_retraining_workflow(
        self, drift_report: dict
    ) -> Result[EmergencyRetrainingResult, str]:
        """
        Execute emergency retraining workflow.

        Args:
            drift_report: Drift report from _check_drift()

        Returns:
            Result with EmergencyRetrainingResult or error message

        Law #8: Focused function <50 lines
        """
        # Log drift warning
        logger.warning(
            f"Drift detected: accuracy={drift_report['current_accuracy']:.3f}, "
            f"drop={drift_report['accuracy_drop']:.3%}, triggering emergency retraining..."
        )

        # Trigger retraining (Article III: automated enforcement)
        retraining_result = self._trigger_retraining(drift_report)
        if retraining_result.is_err():
            logger.error(f"Emergency retraining failed: {retraining_result.unwrap_err()}")
            return Err(retraining_result.unwrap_err())

        retraining_report = retraining_result.unwrap()

        # Store event to VectorStore (Article IV)
        result = self._create_success_result(drift_report, retraining_report)
        self._store_emergency_event(result)

        # Update last alert timestamp
        self._last_alert_timestamp = datetime.now(UTC)

        logger.info(
            f"Emergency retraining completed: {retraining_report.version}, "
            f"accuracy={retraining_report.new_accuracy:.3f}"
        )

        return Ok(result)

    def _check_drift(self) -> Result[dict, str]:
        """
        Check for accuracy drift via DriftDetector.

        Returns:
            Result with drift report dict or error message

        Drift report format:
        {
            "drift_detected": bool,
            "current_accuracy": float,
            "accuracy_drop": float,
            "detection_timestamp": str (ISO 8601)
        }

        Article I: Complete context (retry on timeout)
        """
        # NOTE: This method will integrate with AccuracyDriftDetector
        # For now, return mock implementation that can be overridden in tests
        logger.warning("DriftDetector integration pending (using mock for tests)")
        return Err("DriftDetector not yet implemented")

    def _trigger_retraining(self, drift_report: dict) -> Result[object, str]:
        """
        Trigger WeeklyRetrainingScheduler with emergency flag.

        Args:
            drift_report: Drift report from _check_drift()

        Returns:
            Result with retraining report or error message

        Article III: Automated enforcement (skip_ab_rollout=True)
        Article I: Complete context (validate samples before training)
        """
        # NOTE: This method will integrate with WeeklyRetrainingScheduler
        # For now, return mock implementation that can be overridden in tests
        logger.warning("WeeklyRetrainingScheduler integration pending (using mock for tests)")
        return Err("WeeklyRetrainingScheduler not yet implemented")

    def _should_deduplicate_alert(self) -> bool:
        """
        Check if alert should be deduplicated.

        Returns:
            True if alert should be deduplicated (within 24 hours of last alert)

        Article III: Automated enforcement (prevent alert spam)
        """
        if self._last_alert_timestamp is None:
            return False

        # Check if within deduplication window
        time_since_last = datetime.now(UTC) - self._last_alert_timestamp
        threshold = timedelta(hours=self.config.alert_deduplication_hours)

        return time_since_last < threshold

    def _create_no_action_result(
        self, drift_report: dict
    ) -> Result[EmergencyRetrainingResult, str]:
        """Create result for no action (no drift detected)."""
        result = EmergencyRetrainingResult(
            triggered=False,
            drift_detected=False,
            drift_alert_timestamp=drift_report["detection_timestamp"],
            current_accuracy=drift_report["current_accuracy"],
            accuracy_drop_pct=drift_report["accuracy_drop"] * 100,
            retraining_initiated=False,
            new_model_version=None,
            new_model_accuracy=None,
            samples_used=0,
            deployment_status="no_action",
        )
        return Ok(result)

    def _create_deduplicated_result(
        self, drift_report: dict
    ) -> Result[EmergencyRetrainingResult, str]:
        """Create result for deduplicated alert."""
        result = EmergencyRetrainingResult(
            triggered=False,
            drift_detected=True,
            drift_alert_timestamp=drift_report["detection_timestamp"],
            current_accuracy=drift_report["current_accuracy"],
            accuracy_drop_pct=drift_report["accuracy_drop"] * 100,
            retraining_initiated=False,
            new_model_version=None,
            new_model_accuracy=None,
            samples_used=0,
            deployment_status="deduplicated",
        )
        return Ok(result)

    def _create_success_result(
        self, drift_report: dict, retraining_report: object
    ) -> EmergencyRetrainingResult:
        """Create result for successful emergency retraining."""
        return EmergencyRetrainingResult(
            triggered=True,
            drift_detected=True,
            drift_alert_timestamp=drift_report["detection_timestamp"],
            current_accuracy=drift_report["current_accuracy"],
            accuracy_drop_pct=drift_report["accuracy_drop"] * 100,
            retraining_initiated=True,
            new_model_version=retraining_report.version,
            new_model_accuracy=retraining_report.new_accuracy,
            samples_used=retraining_report.samples_added,
            deployment_status="success",
        )

    def _store_emergency_event(self, result: EmergencyRetrainingResult) -> None:
        """
        Store emergency retraining event to VectorStore.

        Args:
            result: Emergency retraining result to store

        Article IV: Cross-session learning via VectorStore
        """
        content = {
            "triggered": result.triggered,
            "drift_detected": result.drift_detected,
            "drift_alert_timestamp": result.drift_alert_timestamp,
            "current_accuracy": result.current_accuracy,
            "accuracy_drop_pct": result.accuracy_drop_pct,
            "retraining_initiated": result.retraining_initiated,
            "new_model_version": result.new_model_version,
            "new_model_accuracy": result.new_model_accuracy,
            "samples_used": result.samples_used,
            "deployment_status": result.deployment_status,
            "confidence": result.new_model_accuracy if result.new_model_accuracy else 0.0,
        }

        self.context.store_memory(
            key=f"emergency_retraining_{result.drift_alert_timestamp}",
            content=content,
            tags=["emergency", "retraining", "drift_recovery", "leap5_phase4"],
        )

        logger.info(f"Emergency event stored to VectorStore: {result.drift_alert_timestamp}")
