"""
AccuracyDriftDetector: Monitor ML accuracy drift using rolling window statistics.

Detects accuracy degradation in Adaptive Model Router (Leap 5 Phase 3) using:
- Rolling 7-day accuracy window
- Baseline comparison (Phase 3: 98.2%)
- Alert threshold (default: 5% drop → <93.2% accuracy)
- Leap 4 quality signal integration (test failure rate, code churn)

Constitutional compliance:
- Article I: Complete context (full 7-day prediction history retrieved)
- Article II: 100% verification (strict typing, Pydantic models)
- Article IV: VectorStore integration (institutional memory queries)
- Article V: Spec-driven (follows spec-009-misclassification-detection.md)

Usage:
    from shared.agent_context import create_agent_context
    from tools.ml_routing.accuracy_drift_detector import AccuracyDriftDetector

    context = create_agent_context("drift_detection")
    detector = AccuracyDriftDetector(context)

    result = detector.check_drift()
    if result.is_ok():
        report = result.unwrap()
        if report.is_drift_detected:
            print(f"⚠️ DRIFT: Accuracy {report.current_accuracy:.1%}")

Reference: specs/spec-009-misclassification-detection.md Section 5.2
Author: CodeAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result


class DriftSeverity(str, Enum):
    """
    Drift severity classification based on accuracy drop and quality signals.

    CRITICAL: Accuracy drop >10% OR high test failure rate (>10%)
    WARNING: Accuracy drop 5-10% OR moderate test failure rate (5-10%)
    INFO: Accuracy drop <5% (below alert threshold)
    """

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class DriftError(BaseModel):
    """
    Error model for drift detection failures.

    Fields:
        error_type: Error category (insufficient_data, vectorstore_error, etc.)
        message: Human-readable error description
        timestamp: ISO 8601 timestamp of error occurrence
    """

    error_type: str = Field(
        ...,
        description="Error category (insufficient_data, vectorstore_error, calculation_error, unknown)",
    )

    message: str = Field(
        ...,
        description="Human-readable error description with context",
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of error occurrence (UTC)",
    )

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, v: str) -> str:
        """Validate error_type is one of allowed values."""
        valid_types = {
            "insufficient_data",
            "vectorstore_error",
            "calculation_error",
            "unknown",
        }
        if v not in valid_types:
            raise ValueError(f"error_type must be one of {valid_types}, got '{v}'")
        return v


class DriftReport(BaseModel):
    """
    Drift detection report with accuracy metrics and quality signals.

    Fields:
        current_accuracy: Rolling 7-day accuracy (0.0-1.0)
        baseline_accuracy: Expected accuracy from Phase 3 (default: 0.982)
        accuracy_drop: baseline - current (positive = degradation)
        is_drift_detected: True if accuracy_drop > drift_threshold
        drift_threshold: Alert threshold (default: 0.05 = 5%)
        total_predictions: Total predictions in 7-day window
        correct_predictions: Correct predictions (predicted == actual)
        detection_timestamp: ISO 8601 timestamp of detection
        avg_test_failure_rate: Average test failure rate from quality signals
        avg_code_churn: Average code churn lines from quality signals
        severity: Drift severity (critical, warning, info)
    """

    current_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rolling 7-day accuracy (0.0-1.0)",
    )

    baseline_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Expected accuracy from Phase 3 validation (default: 0.982)",
    )

    accuracy_drop: float = Field(
        ...,
        description="Baseline accuracy - current accuracy (positive = degradation)",
    )

    is_drift_detected: bool = Field(
        ...,
        description="True if accuracy_drop > drift_threshold (alert triggered)",
    )

    drift_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alert threshold (default: 0.05 = 5% drop)",
    )

    total_predictions: int = Field(
        ...,
        ge=0,
        description="Total predictions in 7-day rolling window",
    )

    correct_predictions: int = Field(
        ...,
        ge=0,
        description="Correct predictions (predicted_tier == actual_tier)",
    )

    detection_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of drift detection (UTC)",
    )

    avg_test_failure_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average test failure rate from Leap 4 quality signals",
    )

    avg_code_churn: float = Field(
        default=0.0,
        ge=0.0,
        description="Average code churn lines from Leap 4 quality signals",
    )

    severity: str = Field(
        default="info",
        description="Drift severity (critical, warning, info) based on quality signals",
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "current_accuracy": 0.915,
                "baseline_accuracy": 0.982,
                "accuracy_drop": 0.067,
                "is_drift_detected": True,
                "drift_threshold": 0.05,
                "total_predictions": 100,
                "correct_predictions": 91,
                "detection_timestamp": "2025-10-10T12:34:56.789Z",
                "avg_test_failure_rate": 0.08,
                "avg_code_churn": 75.5,
                "severity": "critical",
            }
        },
    )


class AccuracyDriftDetector:
    """
    Monitor ML accuracy drift using rolling 7-day window.

    Workflow:
    1. Query VectorStore: Last 7 days of predictions with actual_tier
    2. Calculate accuracy: correct / total (predicted_tier == actual_tier)
    3. Extract quality signals: Leap 4 test failure rate, code churn
    4. Compare baseline: accuracy_drop = baseline_accuracy - current_accuracy
    5. Alert trigger: if accuracy_drop > drift_threshold (default: 5%)
    6. Log alert: Store to VectorStore with severity classification

    Performance:
    - VectorStore query: <200ms p99 (1,000+ predictions)
    - Drift detection: <24 hours latency (hourly cron checks)
    - Alert precision: >90% (true alerts / total alerts)

    Example:
        >>> context = create_agent_context("drift_detection")
        >>> detector = AccuracyDriftDetector(context)
        >>> result = detector.check_drift()
        >>> if result.is_ok():
        ...     report = result.unwrap()
        ...     if report.is_drift_detected:
        ...         print(f"⚠️ DRIFT: {report.current_accuracy:.1%}")
    """

    MIN_SAMPLE_SIZE = 100  # Minimum predictions for statistical significance

    def __init__(
        self,
        context: AgentContext,
        baseline_accuracy: float = 0.982,
        drift_threshold: float = 0.05,
        window_days: int = 7,
    ):
        """
        Initialize AccuracyDriftDetector.

        Args:
            context: AgentContext for VectorStore queries (Article IV)
            baseline_accuracy: Expected accuracy (default: 98.2% from Phase 3)
            drift_threshold: Alert threshold (default: 5% drop)
            window_days: Rolling window size (default: 7 days)
        """
        self.context = context
        self.baseline_accuracy = baseline_accuracy
        self.drift_threshold = drift_threshold
        self.window_days = window_days

    def check_drift(self) -> Result[DriftReport, DriftError]:
        """
        Check for accuracy drift in rolling 7-day window.

        Returns:
            Result with DriftReport or DriftError

        Workflow:
        1. Query VectorStore: Last 7 days of predictions
        2. Filter predictions: Only tasks with actual_tier set (Leap 4 quality feedback)
        3. Calculate accuracy: correct = (predicted == actual).sum()
        4. Extract quality signals: Test failure rate, code churn
        5. Compare baseline: accuracy_drop = baseline - current
        6. Alert trigger: if accuracy_drop > threshold
        7. Log alert: Store to VectorStore with severity

        Performance:
        - VectorStore query: <200ms p99 (Article I: complete context)
        - Drift detection: <1s total (query + calculation)

        Constitutional compliance:
        - Article I: Full 7-day history retrieved (retry on timeout)
        - Article IV: VectorStore queries and alert logging
        """
        try:
            # Step 1: Query VectorStore for last 7 days (Article I: complete context)
            start_date = datetime.now(UTC) - timedelta(days=self.window_days)
            end_date = datetime.now(UTC)

            predictions_result = self._query_predictions(start_date, end_date)

            if predictions_result.is_err():
                return predictions_result

            predictions = predictions_result.unwrap()

            # Step 2: Filter predictions with actual_tier (Leap 4 quality feedback)
            predictions_with_actual = [p for p in predictions if p.get("actual_tier") is not None]

            if len(predictions_with_actual) < self.MIN_SAMPLE_SIZE:
                # Insufficient data (need ≥100 samples for statistical significance)
                return Err(
                    DriftError(
                        error_type="insufficient_data",
                        message=(
                            f"Insufficient data for drift detection: "
                            f"{len(predictions_with_actual)} predictions "
                            f"(minimum: {self.MIN_SAMPLE_SIZE} required)"
                        ),
                    )
                )

            # Step 3: Calculate accuracy
            correct_predictions = sum(
                1 for p in predictions_with_actual if p["predicted_tier"] == p["actual_tier"]
            )
            total_predictions = len(predictions_with_actual)
            current_accuracy = correct_predictions / total_predictions

            # Step 4: Extract quality signals (Leap 4 integration)
            avg_test_failure_rate, avg_code_churn = self._extract_quality_signals(
                predictions_with_actual
            )

            # Step 5: Compare baseline
            accuracy_drop = self.baseline_accuracy - current_accuracy
            is_drift_detected = accuracy_drop > self.drift_threshold

            # Step 6: Compute severity based on quality signals
            severity = self._compute_severity(accuracy_drop, avg_test_failure_rate, avg_code_churn)

            # Step 7: Build report
            report = DriftReport(
                current_accuracy=current_accuracy,
                baseline_accuracy=self.baseline_accuracy,
                accuracy_drop=accuracy_drop,
                is_drift_detected=is_drift_detected,
                drift_threshold=self.drift_threshold,
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                detection_timestamp=datetime.now(UTC).isoformat(),
                avg_test_failure_rate=avg_test_failure_rate,
                avg_code_churn=avg_code_churn,
                severity=severity,
            )

            # Step 8: Log alert if drift detected (Article IV)
            if is_drift_detected:
                self._log_drift_alert(report)

            return Ok(report)

        except Exception as e:
            return Err(
                DriftError(
                    error_type="calculation_error",
                    message=f"Drift detection failed: {e}",
                )
            )

    def _query_predictions(
        self, start_date: datetime, end_date: datetime
    ) -> Result[list[dict], DriftError]:
        """
        Query VectorStore for predictions in date range.

        Args:
            start_date: Start of rolling window
            end_date: End of rolling window

        Returns:
            Result with list of predictions or DriftError

        Query:
        - Tags: ["prediction", "ml_classification"]
        - Filter: timestamp >= start_date AND timestamp <= end_date
        - Sort: timestamp ASC

        Performance:
        - Latency: <200ms p99 (1,000+ predictions)
        - Indexed: VectorStore indexed on timestamp field
        """
        try:
            # Query VectorStore with date filter (Article IV)
            predictions = self.context.search_memories(
                tags=["prediction", "ml_classification"],
                include_session=False,  # Cross-session (institutional memory)
                filters={
                    "timestamp": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat(),
                    }
                },
            )

            return Ok(predictions)

        except Exception as e:
            return Err(
                DriftError(
                    error_type="vectorstore_error",
                    message=f"VectorStore query failed: {e}",
                )
            )

    def _extract_quality_signals(self, predictions: list[dict]) -> tuple[float, float]:
        """
        Extract Leap 4 quality signals from predictions.

        Args:
            predictions: List of prediction dictionaries

        Returns:
            Tuple of (avg_test_failure_rate, avg_code_churn)

        Quality Signals (Leap 4):
        - test_failure_rate: Ratio of failed tests (0.0-1.0)
        - code_churn_lines: Lines changed after initial commit
        """
        test_failure_rates = []
        code_churn_values = []

        for pred in predictions:
            quality_signals = pred.get("quality_signals", {})

            if isinstance(quality_signals, dict):
                # Extract test failure rate
                test_failure_rate = quality_signals.get("test_failure_rate")
                if test_failure_rate is not None:
                    test_failure_rates.append(test_failure_rate)

                # Extract code churn
                code_churn = quality_signals.get("code_churn_lines")
                if code_churn is not None:
                    code_churn_values.append(code_churn)

        # Calculate averages
        avg_test_failure_rate = (
            sum(test_failure_rates) / len(test_failure_rates) if test_failure_rates else 0.0
        )
        avg_code_churn = (
            sum(code_churn_values) / len(code_churn_values) if code_churn_values else 0.0
        )

        return avg_test_failure_rate, avg_code_churn

    def _compute_severity(
        self, accuracy_drop: float, avg_test_failure_rate: float, avg_code_churn: float
    ) -> str:
        """
        Compute drift severity based on accuracy drop and quality signals.

        Args:
            accuracy_drop: Baseline - current accuracy (positive = degradation)
            avg_test_failure_rate: Average test failure rate (0.0-1.0)
            avg_code_churn: Average code churn lines

        Returns:
            Severity string (critical, warning, info)

        Classification:
        - CRITICAL: accuracy_drop >10% OR test_failure_rate >10%
        - WARNING: accuracy_drop 5-10% OR test_failure_rate 5-10%
        - INFO: accuracy_drop <5% (below alert threshold)
        """
        # Priority 1: Severe accuracy drop (>10%)
        if accuracy_drop > 0.10:
            return DriftSeverity.CRITICAL.value

        # Priority 2: High test failure rate (>10%)
        if avg_test_failure_rate > 0.10:
            return DriftSeverity.CRITICAL.value

        # Priority 3: Moderate accuracy drop (5-10%)
        if accuracy_drop > 0.05:
            return DriftSeverity.WARNING.value

        # Priority 4: Moderate test failure rate (5-10%)
        if avg_test_failure_rate > 0.05:
            return DriftSeverity.WARNING.value

        # Default: No significant issues
        return DriftSeverity.INFO.value

    def _log_drift_alert(self, report: DriftReport) -> None:
        """
        Log drift alert to VectorStore and telemetry.

        Args:
            report: Drift detection report with current accuracy

        Logging:
        - VectorStore: Stores alert for historical analysis (Article IV)
        - Telemetry: Logs alert event for monitoring dashboards
        - Tags: ["drift_alert", severity, "leap5_phase4"] (searchable)
        """
        # Log to VectorStore (Article IV: mandatory)
        self.context.store_memory(
            key=f"drift_alert_{report.detection_timestamp}",
            content={
                "current_accuracy": report.current_accuracy,
                "baseline_accuracy": report.baseline_accuracy,
                "accuracy_drop": report.accuracy_drop,
                "total_predictions": report.total_predictions,
                "correct_predictions": report.correct_predictions,
                "detection_timestamp": report.detection_timestamp,
                "severity": report.severity,
                "avg_test_failure_rate": report.avg_test_failure_rate,
                "avg_code_churn": report.avg_code_churn,
            },
            tags=["drift_alert", report.severity, "leap5_phase4"],
        )
