# Specification: Leap 5 Phase 4 - Misclassification Detection & Drift Monitoring

**Spec ID**: `spec-009-misclassification-detection`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**:
- `spec-007-phase3-ml-inference.md` (Leap 5 Phase 3 ML inference integration)
- `spec-004-quality-feedback-loop.md` (Leap 4 quality signals)
- `spec-008-weekly-retraining-pipeline.md` (Leap 5 Phase 4 retraining)
**Related ADRs**:
- `ADR-026: ML Classifier Integration` (Phase 3 foundation)
- `ADR-025: Quality Feedback Loop` (Leap 4 quality signals)
- `ADR-004: Continuous Learning` (VectorStore integration)

---

## Executive Summary

Leap 5 Phase 4 implements **continuous accuracy monitoring and drift detection** for the ML-powered routing system (Phase 3). This phase adds real-time accuracy tracking, automated alert triggers when accuracy degrades >5%, and emergency retraining protocol when drift is detected. Target: Detect drift within 24 hours, maintain >98% accuracy indefinitely.

**Key Innovation**: Rolling 7-day accuracy window with VectorStore-backed prediction history, enabling statistical drift detection without manual monitoring.

---

## Goals

### Primary Goals

- **Goal 1**: Accuracy drift detection with rolling 7-day window (baseline: current 98.2%, alert threshold: <93.2%)
- **Goal 2**: VectorStore-backed prediction history for statistical analysis (Article IV: all predictions stored, queryable)
- **Goal 3**: Automated alert mechanism when accuracy drops >5% (integrated with Leap 4 quality signals)
- **Goal 4**: Emergency retraining protocol triggered by drift detection (same-day retraining, skip A/B rollout)
- **Goal 5**: Real-time accuracy dashboard with 24-hour trend chart (monitoring without manual queries)

### Success Metrics

| Metric | Target | Measurement Method | Baseline |
|--------|--------|-------------------|----------|
| **Drift Detection Latency** | <24 hours | Time from accuracy drop to alert | N/A (new feature) |
| **Alert Precision** | >90% | True alerts / (true + false alerts) | N/A (new feature) |
| **Dashboard Refresh Rate** | <5s | React dashboard polling interval | N/A (new feature) |
| **VectorStore Query Latency** | <200ms p99 | 7-day prediction retrieval (1,000+ predictions) | N/A (new metric) |
| **Emergency Retraining Time** | <4 hours | Drift detected → new model deployed | N/A (new feature) |
| **Accuracy Recovery Rate** | >95% | Tasks with accuracy restored >98% after retraining | N/A (new metric) |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time model updates during inference (weekly batch retraining sufficient)
- **Non-Goal 2**: Predictive drift detection (statistical forecasting of future drift, Phase 5 enhancement)
- **Non-Goal 3**: Multi-model ensemble for drift mitigation (single model with retraining is simpler)
- **Non-Goal 4**: Custom alerting channels (Slack, PagerDuty, etc., log-based alerts only for MVP)

### Future Considerations

- **Future Enhancement 1**: Predictive drift detection (detect degradation before <93.2% threshold)
- **Future Enhancement 2**: Automated model rollback (if retraining fails, revert to previous model)
- **Future Enhancement 3**: Multi-region drift tracking (separate accuracy metrics per deployment region)
- **Future Enhancement 4**: Custom alert channels (Slack webhooks, PagerDuty integration)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Drift Detector (Component)

- **Description**: Background service monitoring accuracy trends via VectorStore queries (rolling 7-day window)
- **Goals**: Detect accuracy drops >5% within 24 hours, trigger alerts, log telemetry events
- **Pain Points**: VectorStore query latency for large prediction histories (1,000+ predictions/day)
- **Technical Proficiency**: Autonomous agent with statistical analysis, VectorStore integration, alert triggering

#### Persona 2: Emergency Retraining Pipeline (Component)

- **Description**: Triggered by drift alerts, retrains model using recent VectorStore predictions (last 7 days)
- **Goals**: Complete retraining <4 hours, restore accuracy >98%, deploy without A/B testing (emergency bypass)
- **Pain Points**: Sufficient training data available (need >300 samples), model convergence time
- **Technical Proficiency**: ML training pipeline with fast convergence (1-2 iterations), VectorStore data extraction

#### Persona 3: Development Team (Monitoring & Response)

- **Description**: Engineers responding to drift alerts, investigating root causes, validating emergency retraining
- **Goals**: Understand why accuracy degraded, validate retraining effectiveness, prevent future drift
- **Pain Points**: Black-box ML drift (need explainability), alert fatigue (false positives), manual validation overhead
- **Technical Proficiency**: ML debugging, VectorStore queries, telemetry dashboards, constitutional compliance

### User Journeys

#### Journey 1: Drift Detection (Primary Use Case)

```
1. System starts with: Hourly cron job triggers drift detection check
2. System needs to: Detect if ML accuracy has dropped >5% in rolling 7-day window
3. System performs:
   - Query VectorStore: Last 7 days of predictions (task_id, predicted_tier, actual_tier, confidence)
   - Filter predictions: Only tasks with actual_tier set (post-execution quality feedback, Leap 4)
   - Calculate accuracy: correct = (predicted_tier == actual_tier).sum(), total = predictions.count()
   - Rolling window: current_accuracy = correct / total (last 7 days)
   - Baseline comparison: accuracy_drop = baseline_accuracy (98.2%) - current_accuracy
   - Alert trigger: if accuracy_drop > 5% (threshold: <93.2%), log alert + trigger retraining
4. System achieves:
   - Drift detected: Yes (accuracy = 91.5%, drop = 6.7%, threshold exceeded)
   - Alert logged: VectorStore event + telemetry (tags: ["drift_alert", "critical"])
   - Emergency retraining: Triggered (Phase 4 pipeline starts)
   - Latency: <24 hours (hourly checks, worst-case 1-hour delay)
```

#### Journey 2: Emergency Retraining (Secondary Use Case)

```
1. System starts with: Drift alert received (accuracy = 91.5%, baseline = 98.2%)
2. System needs to: Retrain model using recent predictions and restore accuracy >98%
3. System performs:
   - Query VectorStore: Last 7 days of predictions with actual_tier (300+ samples required)
   - Extract training data: TaskFeatureVector + actual_tier labels
   - Train new model: EnsembleModel (RandomForest + GradientBoosting, 3 iterations)
   - Validate accuracy: 80/20 split, target ≥98% validation accuracy
   - Deploy model: Copy to ~/.agency/models/routing_classifier_latest.pkl (skip A/B test)
   - Verify recovery: Run drift check again (post-deployment, expect accuracy >98%)
4. System achieves:
   - Training time: 2.5 hours (300 samples, 3 iterations)
   - Validation accuracy: 98.7% (target: ≥98% ✅)
   - Deployment: Emergency rollout (ML_PERCENTAGE=100, immediate)
   - Accuracy recovery: Post-deployment check = 98.5% (drift resolved ✅)
   - Total latency: <4 hours (alert → retraining → deployment)
```

#### Journey 3: Dashboard Monitoring (User Interaction)

```
1. User starts with: Open accuracy dashboard (React web UI, http://localhost:3000/accuracy)
2. User needs to: Visualize accuracy trend over last 24 hours, identify anomalies
3. System performs:
   - Dashboard loads: Fetch last 24 hours of accuracy data (hourly buckets)
   - Chart rendering: Line chart with accuracy (%) on Y-axis, time (hourly) on X-axis
   - Baseline overlay: Horizontal line at 98.2% (green zone), alert threshold at 93.2% (red zone)
   - Drift indicators: Red highlight when accuracy <93.2%, orange when 93.2-96%
   - Refresh: Auto-refresh every 5s (WebSocket updates)
4. User achieves:
   - Visualization: Accuracy trend chart (last 24 hours)
   - Anomaly detection: Red spike at hour 18 (accuracy = 91.5%, drift alert)
   - Root cause: Click spike → view misclassified tasks (top 10 by confidence)
   - Validation: Confirm emergency retraining restored accuracy (hour 22 = 98.5%)
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Drift Detector

- **AC-1.1**: `DriftDetector` class queries VectorStore for last 7 days of predictions (filtered by `actual_tier != null`)
- **AC-1.2**: Rolling 7-day accuracy calculated: `accuracy = correct_predictions / total_predictions`
- **AC-1.3**: Baseline comparison: `accuracy_drop = baseline_accuracy - current_accuracy`
- **AC-1.4**: Alert trigger: if `accuracy_drop > 5%` (threshold: <93.2%), log alert + trigger retraining
- **AC-1.5**: Hourly cron job: `@hourly drift_detector.check()` (systemd timer or cron)

#### Feature Component 2: Emergency Retraining Pipeline

- **AC-2.1**: Triggered by drift alert (automated, no manual approval required for emergency)
- **AC-2.2**: VectorStore query: Extract last 7 days of predictions with `actual_tier` (training data)
- **AC-2.3**: Training requirement: ≥300 samples required (fail if insufficient data)
- **AC-2.4**: Model training: EnsembleModel with 3 iterations (fast convergence, <4 hours total)
- **AC-2.5**: Validation gate: New model accuracy ≥98% on validation set (80/20 split)
- **AC-2.6**: Emergency deployment: Copy model to `routing_classifier_latest.pkl`, set `ML_PERCENTAGE=100` (skip A/B test)

#### Feature Component 3: VectorStore Integration

- **AC-3.1**: Predictions stored with `actual_tier` field (updated post-execution by Leap 4 quality feedback)
- **AC-3.2**: Query API: `get_predictions(start_date, end_date, filter_by_actual_tier=True)` (<200ms p99)
- **AC-3.3**: Indexing: VectorStore indexed on `timestamp` and `actual_tier` fields (fast queries)
- **AC-3.4**: Cross-session queries: `include_session=False` (institutional memory, Article IV)
- **AC-3.5**: Prediction schema: `task_id`, `predicted_tier`, `actual_tier`, `confidence`, `timestamp`

#### Feature Component 4: Accuracy Dashboard

- **AC-4.1**: Real-time dashboard: React web UI at `http://localhost:3000/accuracy` (optional for MVP)
- **AC-4.2**: 24-hour trend chart: Line chart with hourly accuracy buckets (rolling window visualization)
- **AC-4.3**: Baseline overlay: Green zone (98.2%), yellow zone (96-98%), red zone (<93.2%)
- **AC-4.4**: Drift indicators: Red highlight when accuracy <93.2%, orange when 93.2-96%
- **AC-4.5**: Auto-refresh: 5-second polling interval or WebSocket updates (real-time without manual refresh)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: VectorStore query latency <200ms p99 (7-day prediction retrieval, 1,000+ predictions)
- **AC-P.2**: Drift detection latency <24 hours (hourly cron checks, worst-case 1-hour delay)
- **AC-P.3**: Emergency retraining time <4 hours (alert → training → validation → deployment)
- **AC-P.4**: Dashboard load time <2s (initial chart rendering)

#### Quality

- **AC-Q.1**: Alert precision >90% (true drift alerts / (true + false alerts))
- **AC-Q.2**: Accuracy recovery >95% (tasks with accuracy restored >98% after retraining)
- **AC-Q.3**: False positive rate <10% (false drift alerts / total alerts)
- **AC-Q.4**: Training data sufficiency: Emergency retraining fails gracefully if <300 samples (log warning, retry next hour)

#### Reliability

- **AC-R.1**: Idempotent drift checks: Multiple calls with same data → same alert decision (no alert fatigue)
- **AC-R.2**: Graceful degradation: VectorStore unavailable → log warning, retry next hour (no crash)
- **AC-R.3**: Rollback safety: Old model preserved at `routing_classifier_v{timestamp}.pkl` (manual rollback possible)
- **AC-R.4**: Alert deduplication: Only 1 alert per 24-hour window (prevent alert spam)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Full 7-day prediction history retrieved before accuracy calculation (no partial data)
- **AC-CI.2**: VectorStore query retries on timeout (2x, 3x, up to 10x per Article I)
- **AC-CI.3**: Training data validation: Ensure ≥300 samples before retraining (complete context)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Drift detection logic 100% tested (unit tests for threshold, rolling window, alert trigger)
- **AC-CII.2**: Emergency retraining validates new model accuracy ≥98% (validation gate, no deployment without pass)
- **AC-CII.3**: Integration test: End-to-end drift detection → retraining → accuracy recovery

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: Drift detection automated (hourly cron, no manual triggers)
- **AC-CIII.2**: Emergency retraining automated (triggered by alert, no manual approval)
- **AC-CIII.3**: Deployment automated (model copied to production path, ML_PERCENTAGE=100)

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: All drift alerts stored in VectorStore (tags: ["drift_alert", severity])
- **AC-CIV.2**: Retraining history logged (training_date, validation_accuracy, sample_count)
- **AC-CIV.3**: Cross-session learning: VectorStore queries include all predictions (institutional memory)
- **AC-CIV.4**: Pattern extraction: Analyze misclassified tasks for common patterns (future Phase 5 enhancement)

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Phase 4 scope limited to drift detection + emergency retraining (weekly scheduled retraining in spec-008)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Leap 5 Phase 4: Misclassification Detection & Drift Monitoring        │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ Hourly Cron      │───▶│ DriftDetector    │───▶│ VectorStore      │ │
│  │                  │    │                  │    │                  │ │
│  │ - @hourly trigger│    │ - Query 7-day    │    │ - Predictions    │ │
│  │ - Check drift    │    │   predictions    │    │ - actual_tier    │ │
│  │ - Log results    │    │ - Calculate acc  │    │ - timestamps     │ │
│  └──────────────────┘    │ - Compare baseline│   └──────────────────┘ │
│                          │ - Trigger alert  │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                       (accuracy drop >5%)                  │            │
│                                   ▼                        │            │
│                          ┌──────────────────┐             │            │
│                          │ Emergency        │             │            │
│                          │ Retraining       │             │            │
│                          │                  │             │            │
│                          │ - Extract data   │─────────────┘            │
│                          │ - Train model    │                          │
│                          │ - Validate acc   │                          │
│                          │ - Deploy         │                          │
│                          └──────────────────┘                          │
│                                   │                                    │
│                                   ▼                                    │
│                          ┌──────────────────┐                          │
│                          │ Accuracy         │                          │
│                          │ Dashboard        │                          │
│                          │                  │                          │
│                          │ - 24-hour chart  │                          │
│                          │ - Drift indicators│                         │
│                          │ - Auto-refresh   │                          │
│                          └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 DriftDetector Implementation

```python
"""
DriftDetector: Monitor accuracy drift and trigger alerts.

Constitutional compliance:
- Article I: Complete context (full 7-day prediction history retrieved)
- Article II: 100% verification (drift logic fully tested)
- Article IV: VectorStore integration (all predictions queryable)
- Article V: Spec-driven (follows spec-009-misclassification-detection.md)
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from dataclasses import dataclass

from shared.agent_context import AgentContext
from shared.type_definitions.result import Result, Ok, Err


@dataclass
class DriftReport:
    """Drift detection report."""

    current_accuracy: float  # Rolling 7-day accuracy (0.0-1.0)
    baseline_accuracy: float  # Baseline accuracy (default: 0.982)
    accuracy_drop: float  # baseline - current (positive = degradation)
    is_drift_detected: bool  # True if accuracy_drop > threshold
    drift_threshold: float  # Alert threshold (default: 0.05 = 5%)
    total_predictions: int  # Total predictions in 7-day window
    correct_predictions: int  # Correct predictions (predicted == actual)
    detection_timestamp: str  # ISO 8601 timestamp of detection


class DriftDetector:
    """
    Monitor ML accuracy drift using rolling 7-day window.

    Workflow:
    1. Query VectorStore: Last 7 days of predictions with actual_tier
    2. Calculate accuracy: correct / total (predicted_tier == actual_tier)
    3. Compare baseline: accuracy_drop = baseline_accuracy - current_accuracy
    4. Alert trigger: if accuracy_drop > 5%, log alert + trigger retraining

    Performance:
    - VectorStore query: <200ms p99 (1,000+ predictions)
    - Drift detection: <24 hours latency (hourly cron checks)
    - Alert precision: >90% (true alerts / (true + false alerts))
    """

    def __init__(
        self,
        context: AgentContext,
        baseline_accuracy: float = 0.982,  # Phase 3 baseline (98.2%)
        drift_threshold: float = 0.05,  # 5% drop threshold
        window_days: int = 7
    ):
        """
        Initialize DriftDetector.

        Args:
            context: AgentContext for VectorStore queries (Article IV)
            baseline_accuracy: Expected accuracy (default: 98.2%)
            drift_threshold: Alert threshold (default: 5% drop)
            window_days: Rolling window size (default: 7 days)
        """
        self.context = context
        self.baseline_accuracy = baseline_accuracy
        self.drift_threshold = drift_threshold
        self.window_days = window_days

    def check_drift(self) -> Result[DriftReport, str]:
        """
        Check for accuracy drift in rolling 7-day window.

        Returns:
            Result with DriftReport or error message

        Workflow:
        1. Query VectorStore: Last 7 days of predictions
        2. Filter predictions: Only tasks with actual_tier set (post-execution)
        3. Calculate accuracy: correct = (predicted == actual).sum()
        4. Compare baseline: accuracy_drop = baseline - current
        5. Alert trigger: if accuracy_drop > threshold

        Performance:
        - VectorStore query: <200ms p99 (Article I: complete context)
        - Drift detection: <1s total (query + calculation)
        """
        try:
            # Step 1: Query VectorStore for last 7 days (Article I: complete context)
            start_date = datetime.now(UTC) - timedelta(days=self.window_days)
            end_date = datetime.now(UTC)

            predictions_result = self._query_predictions(start_date, end_date)

            if predictions_result.is_err():
                return predictions_result  # Propagate error

            predictions = predictions_result.unwrap()

            # Step 2: Filter predictions with actual_tier (Leap 4 quality feedback)
            predictions_with_actual = [
                p for p in predictions
                if p.get("actual_tier") is not None
            ]

            if len(predictions_with_actual) < 100:
                # Insufficient data (need ≥100 samples for statistical significance)
                return Err(
                    f"Insufficient data for drift detection: "
                    f"{len(predictions_with_actual)} predictions "
                    f"(minimum: 100 required)"
                )

            # Step 3: Calculate accuracy
            correct_predictions = sum(
                1 for p in predictions_with_actual
                if p["predicted_tier"] == p["actual_tier"]
            )
            total_predictions = len(predictions_with_actual)
            current_accuracy = correct_predictions / total_predictions

            # Step 4: Compare baseline
            accuracy_drop = self.baseline_accuracy - current_accuracy
            is_drift_detected = accuracy_drop > self.drift_threshold

            # Step 5: Build report
            report = DriftReport(
                current_accuracy=current_accuracy,
                baseline_accuracy=self.baseline_accuracy,
                accuracy_drop=accuracy_drop,
                is_drift_detected=is_drift_detected,
                drift_threshold=self.drift_threshold,
                total_predictions=total_predictions,
                correct_predictions=correct_predictions,
                detection_timestamp=datetime.now(UTC).isoformat()
            )

            # Step 6: Log alert if drift detected (Article IV)
            if is_drift_detected:
                self._log_drift_alert(report)

            return Ok(report)

        except Exception as e:
            return Err(f"Drift detection failed: {e}")

    def _query_predictions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Result[list[dict], str]:
        """
        Query VectorStore for predictions in date range.

        Args:
            start_date: Start of rolling window
            end_date: End of rolling window

        Returns:
            Result with list of predictions or error message

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
                        "$lte": end_date.isoformat()
                    }
                }
            )

            return Ok(predictions)

        except Exception as e:
            return Err(f"VectorStore query failed: {e}")

    def _log_drift_alert(self, report: DriftReport) -> None:
        """
        Log drift alert to VectorStore and telemetry.

        Args:
            report: Drift detection report with current accuracy

        Logging:
        - VectorStore: Stores alert for historical analysis
        - Telemetry: Logs alert event for monitoring dashboards
        - Tags: ["drift_alert", "critical"] (searchable)
        """
        from tools.telemetry.telemetry_log import log_event

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
                "severity": "critical" if report.accuracy_drop > 0.10 else "warning"
            },
            tags=["drift_alert", "critical", "leap5_phase4"]
        )

        # Log to telemetry (monitoring)
        log_event(
            event_type="accuracy_drift_detected",
            current_accuracy=report.current_accuracy,
            baseline_accuracy=report.baseline_accuracy,
            accuracy_drop=report.accuracy_drop,
            total_predictions=report.total_predictions,
            severity="critical"
        )
```

### 5.3 Emergency Retraining Pipeline

```python
"""
Emergency Retraining Pipeline: Triggered by drift alerts.

Constitutional compliance:
- Article I: Complete context (≥300 training samples required)
- Article II: Validation gate (new model accuracy ≥98%)
- Article III: Automated deployment (no manual approval)
- Article IV: VectorStore training data extraction
"""

from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Optional

from shared.agent_context import AgentContext
from shared.models.ensemble_model import EnsembleModel
from shared.type_definitions.result import Result, Ok, Err
from tools.ml_routing.feature_extractor import FeatureExtractor
from tools.ml_routing.model_trainer import ModelTrainer


class EmergencyRetrainingPipeline:
    """
    Emergency retraining triggered by drift alerts.

    Workflow:
    1. Extract training data: VectorStore predictions (last 7 days)
    2. Validate sample count: ≥300 samples required (fail if insufficient)
    3. Train new model: EnsembleModel with 3 iterations (fast convergence)
    4. Validate accuracy: New model ≥98% on validation set (80/20 split)
    5. Deploy model: Copy to production path, set ML_PERCENTAGE=100

    Performance:
    - Training time: <4 hours (300+ samples, 3 iterations)
    - Validation accuracy: ≥98% (target threshold)
    - Deployment: Emergency rollout (skip A/B test)
    """

    MIN_TRAINING_SAMPLES = 300  # Minimum samples for emergency retraining
    VALIDATION_ACCURACY_THRESHOLD = 0.98  # 98% validation accuracy required

    def __init__(
        self,
        context: AgentContext,
        feature_extractor: FeatureExtractor,
        model_trainer: ModelTrainer,
        model_output_path: str = "~/.agency/models/routing_classifier_latest.pkl"
    ):
        """
        Initialize EmergencyRetrainingPipeline.

        Args:
            context: AgentContext for VectorStore data extraction
            feature_extractor: FeatureExtractor for TaskFeatureVector generation
            model_trainer: ModelTrainer for EnsembleModel training
            model_output_path: Output path for trained model
        """
        self.context = context
        self.feature_extractor = feature_extractor
        self.model_trainer = model_trainer
        self.model_output_path = Path(model_output_path).expanduser()

    def retrain(self, drift_report: DriftReport) -> Result[EnsembleModel, str]:
        """
        Retrain model using recent VectorStore predictions.

        Args:
            drift_report: Drift detection report triggering retraining

        Returns:
            Result with new EnsembleModel or error message

        Workflow:
        1. Extract training data from VectorStore (last 7 days)
        2. Validate sample count (≥300 required)
        3. Generate features (TaskFeatureVector for each sample)
        4. Train EnsembleModel (3 iterations, fast convergence)
        5. Validate accuracy (≥98% on validation set)
        6. Deploy model (emergency rollout)

        Performance:
        - Training time: <4 hours (300+ samples, 3 iterations)
        - Validation accuracy: ≥98% (gate enforced)
        """
        try:
            # Step 1: Extract training data (Article I: complete context)
            training_data_result = self._extract_training_data()

            if training_data_result.is_err():
                return training_data_result

            training_data = training_data_result.unwrap()

            # Step 2: Validate sample count
            if len(training_data) < self.MIN_TRAINING_SAMPLES:
                return Err(
                    f"Insufficient training data: {len(training_data)} samples "
                    f"(minimum: {self.MIN_TRAINING_SAMPLES} required)"
                )

            # Step 3: Train new model (Article II: verification required)
            train_result = self.model_trainer.train(
                training_data=training_data,
                validation_split=0.2,  # 80/20 train/validation
                n_estimators=100,
                max_depth=10,
                n_iterations=3  # Fast convergence for emergency
            )

            if train_result.is_err():
                return train_result

            new_model = train_result.unwrap()

            # Step 4: Validate accuracy (Article II: quality gate)
            if new_model.validation_accuracy < self.VALIDATION_ACCURACY_THRESHOLD:
                return Err(
                    f"New model accuracy {new_model.validation_accuracy:.1%} "
                    f"< threshold {self.VALIDATION_ACCURACY_THRESHOLD:.1%}. "
                    "Emergency retraining failed, keeping current model."
                )

            # Step 5: Deploy model (Article III: automated)
            deploy_result = self._deploy_model(new_model)

            if deploy_result.is_err():
                return deploy_result

            # Log successful retraining (Article IV)
            self._log_retraining_success(new_model, drift_report)

            return Ok(new_model)

        except Exception as e:
            return Err(f"Emergency retraining failed: {e}")

    def _extract_training_data(self) -> Result[list[dict], str]:
        """
        Extract training data from VectorStore (last 7 days of predictions).

        Returns:
            Result with training data or error message

        Training Data Schema:
        - task_id: str
        - task_description: str
        - predicted_tier: str
        - actual_tier: str (ground truth from Leap 4 quality feedback)
        - confidence: float
        - timestamp: str
        """
        start_date = datetime.now(UTC) - timedelta(days=7)
        end_date = datetime.now(UTC)

        try:
            predictions = self.context.search_memories(
                tags=["prediction", "ml_classification"],
                include_session=False,
                filters={
                    "timestamp": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    },
                    "actual_tier": {"$ne": None}  # Only predictions with ground truth
                }
            )

            return Ok(predictions)

        except Exception as e:
            return Err(f"Training data extraction failed: {e}")

    def _deploy_model(self, model: EnsembleModel) -> Result[None, str]:
        """
        Deploy new model to production (emergency rollout, skip A/B test).

        Args:
            model: Trained EnsembleModel

        Returns:
            Result with None or error message

        Deployment:
        - Backup current model: routing_classifier_v{timestamp}.pkl
        - Copy new model: routing_classifier_latest.pkl
        - Set ML_PERCENTAGE=100 (emergency rollout, no A/B test)
        """
        try:
            import joblib

            # Backup current model (rollback safety)
            if self.model_output_path.exists():
                backup_path = self.model_output_path.parent / (
                    f"routing_classifier_v{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pkl"
                )
                import shutil
                shutil.copy(self.model_output_path, backup_path)

            # Deploy new model
            joblib.dump(model, self.model_output_path)

            # Set emergency rollout (ML_PERCENTAGE=100)
            import os
            os.environ["ML_PERCENTAGE"] = "100"

            return Ok(None)

        except Exception as e:
            return Err(f"Model deployment failed: {e}")

    def _log_retraining_success(
        self,
        model: EnsembleModel,
        drift_report: DriftReport
    ) -> None:
        """
        Log successful retraining to VectorStore and telemetry.

        Args:
            model: New trained model
            drift_report: Original drift report triggering retraining
        """
        from tools.telemetry.telemetry_log import log_event

        # VectorStore logging (Article IV)
        self.context.store_memory(
            key=f"emergency_retraining_{datetime.now(UTC).isoformat()}",
            content={
                "training_date": model.training_date,
                "validation_accuracy": model.validation_accuracy,
                "sample_count": model.sample_count,
                "trigger_accuracy": drift_report.current_accuracy,
                "baseline_accuracy": drift_report.baseline_accuracy,
                "accuracy_drop": drift_report.accuracy_drop
            },
            tags=["emergency_retraining", "success", "leap5_phase4"]
        )

        # Telemetry logging
        log_event(
            event_type="emergency_retraining_success",
            validation_accuracy=model.validation_accuracy,
            sample_count=model.sample_count,
            trigger_accuracy=drift_report.current_accuracy
        )
```

### 5.4 Hourly Cron Integration

```bash
#!/bin/bash
# scripts/drift_detection_cron.sh
# Hourly drift detection check (systemd timer or cron)

set -euo pipefail

# Activate virtual environment
source /Users/am/Code/Agency/.venv/bin/activate

# Run drift detector
cd /Users/am/Code/Agency
python -c "
from shared.agent_context import create_agent_context
from tools.ml_routing.drift_detector import DriftDetector

# Initialize drift detector
context = create_agent_context('drift_detection')
detector = DriftDetector(context)

# Check for drift
report_result = detector.check_drift()

if report_result.is_ok():
    report = report_result.unwrap()

    if report.is_drift_detected:
        # Drift detected, trigger emergency retraining
        print(f'⚠️ DRIFT DETECTED: Accuracy {report.current_accuracy:.1%} (drop: {report.accuracy_drop:.1%})')

        # Trigger emergency retraining
        from tools.ml_routing.emergency_retraining import EmergencyRetrainingPipeline
        from tools.ml_routing.feature_extractor import FeatureExtractor
        from tools.ml_routing.model_trainer import ModelTrainer

        pipeline = EmergencyRetrainingPipeline(
            context=context,
            feature_extractor=FeatureExtractor(context),
            model_trainer=ModelTrainer()
        )

        retrain_result = pipeline.retrain(report)

        if retrain_result.is_ok():
            print('✅ Emergency retraining successful')
        else:
            print(f'❌ Emergency retraining failed: {retrain_result.unwrap_err()}')
    else:
        print(f'✅ No drift detected. Accuracy: {report.current_accuracy:.1%}')
else:
    print(f'❌ Drift detection failed: {report_result.unwrap_err()}')
"
```

**Cron Setup**:
```bash
# Add to crontab (hourly checks at minute 0)
0 * * * * /Users/am/Code/Agency/scripts/drift_detection_cron.sh >> /var/log/drift_detection.log 2>&1
```

**Systemd Timer** (alternative to cron):
```ini
# /etc/systemd/system/drift-detection.timer
[Unit]
Description=Hourly Drift Detection Check
Requires=drift-detection.service

[Timer]
OnCalendar=hourly
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/drift-detection.service
[Unit]
Description=Agency ML Drift Detection
After=network.target

[Service]
Type=oneshot
User=am
WorkingDirectory=/Users/am/Code/Agency
ExecStart=/Users/am/Code/Agency/scripts/drift_detection_cron.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `spec-007-phase3-ml-inference.md` (Phase 3 ML inference, prediction logging)
- **Dependency 2**: `spec-004-quality-feedback-loop.md` (Leap 4 quality signals, actual_tier updates)
- **Dependency 3**: `shared/models/prediction_log.py` (Phase 3 Pydantic schema)
- **Dependency 4**: `tools/ml_routing/model_trainer.py` (Phase 2 training pipeline)

### External Dependencies

- **External Dep 1**: VectorStore backend (Firestore or JSONL files)
- **External Dep 2**: Cron daemon or systemd (hourly drift checks)
- **External Dep 3**: React (optional dashboard, MVP can use CLI)

### Technical Constraints

- **Constraint 1**: VectorStore query latency <200ms p99 (1,000+ predictions, indexed on timestamp)
- **Constraint 2**: Drift detection latency <24 hours (hourly cron checks)
- **Constraint 3**: Emergency retraining time <4 hours (300+ samples, 3 iterations)
- **Constraint 4**: Minimum 300 training samples required (fail gracefully if insufficient)

### Business Constraints

- **Constraint 1**: Alert precision >90% (minimize false positives)
- **Constraint 2**: Accuracy recovery >95% (retraining must restore >98% accuracy)
- **Constraint 3**: Zero manual intervention (fully automated pipeline, Article III)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Insufficient training data (<300 samples)** - *Mitigation*: Fail gracefully, retry next hour, log warning
- **Risk 2**: **False positive drift alerts (alert fatigue)** - *Mitigation*: 5% threshold (conservative), 7-day rolling window (smooth outliers), alert deduplication (1 per 24 hours)

### Medium Risk Items

- **Risk 3**: **VectorStore query timeout (>200ms)** - *Mitigation*: Retry with backoff (Article I), graceful degradation (log warning, retry next hour)
- **Risk 4**: **Emergency retraining fails to converge (<98%)** - *Mitigation*: Validation gate (no deployment if <98%), keep current model, retry next hour

### Low Risk Items

- **Risk 5**: **Cron daemon failures** - *Mitigation*: Systemd timer alternative, monitoring alerts
- **Risk 6**: **Dashboard load time >2s** - *Mitigation*: Client-side caching, 5s refresh interval

### Constitutional Risks

- **Constitutional Risk 1**: **Article I violation (incomplete training data)** - *Mitigation*: ≥300 sample requirement enforced, integration test validates
- **Constitutional Risk 2**: **Article IV violation (drift alerts not logged)** - *Mitigation*: Assert VectorStore write in drift detector, all alerts stored

---

## Testing Strategy

### Test Categories

#### Unit Tests (25+ tests)

1. **DriftDetector Tests** (12 tests)
   - Query VectorStore for 7-day predictions (success, timeout, empty result)
   - Calculate rolling accuracy (100%, 95%, 90%, 85% accuracy scenarios)
   - Compare baseline (drift detected, no drift, edge cases)
   - Alert trigger (accuracy drop >5%, <5%, exactly 5%)
   - Insufficient data handling (<100 samples)

2. **EmergencyRetrainingPipeline Tests** (8 tests)
   - Extract training data (≥300 samples, <300 samples)
   - Train new model (success, convergence failure)
   - Validation gate (≥98%, <98%)
   - Deploy model (success, file write failure)
   - Backup current model (rollback safety)

3. **Cron Integration Tests** (5 tests)
   - Hourly execution (systemd timer, cron)
   - Drift detection triggered (automated)
   - Emergency retraining triggered (automated)
   - Logging (stdout, telemetry, VectorStore)
   - Error handling (VectorStore unavailable, training failure)

#### Integration Tests (10+ tests)

1. **End-to-End Drift Detection** (3 tests)
   - Full pipeline: VectorStore query → accuracy calculation → alert → retraining
   - Drift detected scenario (accuracy = 91.5%, alert logged, retraining triggered)
   - No drift scenario (accuracy = 98.5%, no alert, no retraining)

2. **VectorStore Integration** (3 tests)
   - Query latency <200ms p99 (1,000+ predictions)
   - Cross-session queries (include_session=False)
   - Prediction schema validation (actual_tier field present)

3. **Emergency Retraining Validation** (2 tests)
   - Retraining success (validation accuracy ≥98%, model deployed)
   - Retraining failure (validation accuracy <98%, current model kept)

4. **Accuracy Recovery** (2 tests)
   - Post-deployment drift check (accuracy restored >98%)
   - Accuracy recovery rate >95% (statistical validation)

### Test Data Requirements

- **Test Data 1**: 1,000 prediction samples (7-day history) with actual_tier field
- **Test Data 2**: Drift scenario dataset (accuracy = 91.5%, 300+ samples)
- **Test Data 3**: Baseline scenario dataset (accuracy = 98.5%, 300+ samples)

### Test Environment Requirements

- **Environment 1**: VectorStore with 7+ days of prediction history
- **Environment 2**: Cron daemon or systemd timer (hourly execution)
- **Environment 3**: Trained EnsembleModel for baseline comparisons

---

## Implementation Phases

### Phase 4.1: Drift Detector Core (Day 1-2)

- **Scope**: DriftDetector class, VectorStore queries, alert triggering
- **Deliverables**:
  - `tools/ml_routing/drift_detector.py` (DriftReport, DriftDetector)
  - Unit tests (12 tests, drift detection logic, alert trigger)
- **Success Criteria**: Drift detection <24 hours, alert precision >90%

### Phase 4.2: Emergency Retraining Pipeline (Day 2-3)

- **Scope**: EmergencyRetrainingPipeline class, model training, deployment
- **Deliverables**:
  - `tools/ml_routing/emergency_retraining.py` (EmergencyRetrainingPipeline)
  - Unit tests (8 tests, training, validation, deployment)
- **Success Criteria**: Retraining time <4 hours, validation accuracy ≥98%

### Phase 4.3: Cron Integration (Day 3-4)

- **Scope**: Hourly cron job, systemd timer, logging
- **Deliverables**:
  - `scripts/drift_detection_cron.sh` (hourly execution script)
  - Systemd timer/service files (alternative to cron)
  - Integration tests (5 tests, cron execution, error handling)
- **Success Criteria**: Hourly execution, automated retraining, zero manual intervention

### Phase 4.4: Dashboard Implementation (Day 4-5, Optional MVP)

- **Scope**: React dashboard, 24-hour accuracy chart, auto-refresh
- **Deliverables**:
  - `tools/dashboard/accuracy_dashboard.tsx` (React component)
  - Backend API (`/api/accuracy?hours=24`)
  - Integration tests (dashboard load time <2s)
- **Success Criteria**: Real-time visualization, <5s refresh rate

### Phase 4.5: Production Validation (Day 5-6)

- **Scope**: End-to-end testing, drift simulation, accuracy recovery validation
- **Deliverables**:
  - Performance benchmarks (VectorStore query latency, retraining time)
  - Drift simulation report (inject 91.5% accuracy, validate alert + retraining)
  - Documentation: Phase 4 execution summary
- **Success Criteria**: Alert precision >90%, accuracy recovery >95%, <4 hour retraining

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: DriftDetector, EmergencyRetrainingPipeline, LearningAgent
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), MLEngineer (drift detection validation)

### Review Criteria

- **Completeness**: All drift detection components specified (DriftDetector, retraining, cron)
- **Clarity**: Architecture diagrams, code examples, integration points documented
- **Feasibility**: <24 hour drift detection achievable, <4 hour retraining validated
- **Constitutional Compliance**: Article I-V validated (especially Article IV VectorStore queries)
- **Quality Standards**: Alert precision >90%, accuracy recovery >95%, <200ms VectorStore query

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Drift Detection Approval**: Pending alert precision validation (Phase 4.5)
- [ ] **Final Approval**: Pending after Phase 4.3 implementation (cron integration)

---

## Appendices

### Appendix A: Glossary

- **Drift Detection**: Monitoring ML accuracy degradation over time (rolling 7-day window)
- **Rolling Window**: Time-based window for accuracy calculation (default: 7 days)
- **Baseline Accuracy**: Expected accuracy from Phase 3 validation (98.2%)
- **Accuracy Drop**: Baseline accuracy - current accuracy (positive = degradation)
- **Emergency Retraining**: Automated model retraining triggered by drift alerts (<4 hours)

### Appendix B: References

- **Spec-007**: ML Inference Integration (Leap 5 Phase 3 foundation)
- **Spec-004**: Quality Feedback Loop (Leap 4 actual_tier updates)
- **Spec-008**: Weekly Retraining Pipeline (scheduled retraining, not emergency)
- **ADR-026**: ML Classifier Integration (Phase 3 architecture)
- **ADR-025**: Quality Feedback Loop (Leap 4 quality signals)
- **ADR-004**: Continuous Learning (VectorStore mandate)

### Appendix C: Related Documents

- **Spec**: `specs/spec-007-phase3-ml-inference.md` (Phase 3 prediction logging)
- **Plan**: `plans/plan-009-drift-monitoring.md` (to be created after spec approval)
- **Tests**: `tests/test_drift_detector.py`, `tests/test_emergency_retraining.py`, `tests/test_drift_cron.py`

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification: DriftDetector, emergency retraining, cron integration, dashboard |

---

*"Not just detecting drift—recovering before users notice."*
