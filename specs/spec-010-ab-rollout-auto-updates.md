# Specification: Leap 5 Phase 4 - A/B Testing Rollout & Auto-Updates

**Spec ID**: `spec-010-ab-rollout-auto-updates`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**:
- `spec-007-phase3-ml-inference.md` (Leap 5 Phase 3 foundation)
- `spec-008-weekly-retraining-pipeline.md` (training pipeline)
- `spec-005-advanced-pattern-recognition.md` (Leap 5 overview)
**Related ADRs**:
- `ADR-026: ML Classifier Integration` (Phase 3 architecture)
- `ADR-003: Automated Merge Enforcement` (no manual overrides)
- `ADR-004: Continuous Learning` (VectorStore integration)

---

## Executive Summary

Leap 5 Phase 4 implements **automated gradual model deployment** with A/B testing, rollback mechanism, and zero-downtime swaps. This phase transforms model updates from manual operations to autonomous deployments, enabling continuous accuracy improvement without production risk.

**Key Innovation**: Three-stage rollout (10% → 50% → 100%) with automated rollback based on accuracy comparison, achieving safe model deployment without human intervention.

---

## Goals

### Primary Goals

- **Goal 1**: Automated gradual rollout (10% → 50% → 100% over 48 hours) with accuracy validation at each stage
- **Goal 2**: A/B testing framework comparing new model vs current model accuracy (per-tier metrics)
- **Goal 3**: Automated rollback if new model accuracy < current model - 2% (safety threshold)
- **Goal 4**: Zero-downtime model swaps using symlink strategy (models/ensemble_active.pkl)
- **Goal 5**: Real-time rollout monitoring (per-tier accuracy tracking, confidence distribution)

### Success Metrics

| Metric | Target | Measurement Method | Baseline |
|--------|--------|-------------------|----------|
| **Rollout Duration** | 48 hours (3 stages × 16h) | Stage progression timestamps | N/A (new feature) |
| **Rollback Time** | <5 minutes | Symlink swap + cache clear | N/A (new feature) |
| **Zero Downtime** | 100% (no service interruption) | Classification latency monitoring | 100% (current state) |
| **Accuracy Validation** | ≥current - 2% per stage | Per-tier confusion matrix | 98.2% (Phase 3) |
| **A/B Split Balance** | 10% / 50% / 100% ±2% | Task routing distribution | 50.2% (Phase 3 baseline) |
| **Production Stability** | Zero classification failures | Error rate monitoring | <1% (Phase 3) |
| **Stage Progression** | Automated (no manual approval) | Cron job execution logs | Manual (current) |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time model updates during rollout (models deployed at stage boundaries only)
- **Non-Goal 2**: Multi-model comparison beyond A/B (champion/challenger framework deferred to Phase 5)
- **Non-Goal 3**: Per-user or per-task model selection (hash-based routing only)
- **Non-Goal 4**: Interactive rollout control (pause/resume not in scope, rollback only)

### Future Considerations

- **Future Enhancement 1**: Canary deployments with health metrics (error rate, latency spikes)
- **Future Enhancement 2**: Blue-green deployments with instant rollback (duplicate infrastructure)
- **Future Enhancement 3**: Multi-armed bandit optimization (dynamic traffic allocation)
- **Future Enhancement 4**: Progressive rollout per tier (10% P1, 50% P2, 100% P3)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Rollout Orchestrator (System Component)

- **Description**: Automated pipeline that deploys new models with gradual traffic increase
- **Goals**: Zero production disruptions, accuracy validation, instant rollback capability
- **Pain Points**: Manual deployments risky, coordination overhead, rollback delay
- **Technical Proficiency**: Autonomous system with cron jobs, symlink management, VectorStore queries

#### Persona 2: ML Model (Component)

- **Description**: Newly trained EnsembleModel awaiting production deployment
- **Goals**: Validated accuracy before full rollout, fair A/B comparison, version tracking
- **Pain Points**: Risk of unvalidated deployment, version confusion, rollback complexity
- **Technical Proficiency**: Scikit-learn pickle serialization, metadata tracking (training_date, accuracy)

#### Persona 3: Development Team (Monitoring & Debugging)

- **Description**: Engineers monitoring rollout progress, investigating accuracy regressions
- **Goals**: Real-time metrics, rollout stage visibility, rollback confidence
- **Pain Points**: Opaque rollout state, delayed metrics, manual rollback coordination
- **Technical Proficiency**: Telemetry dashboards, VectorStore queries, infrastructure ops

### User Journeys

#### Journey 1: Successful Gradual Rollout (Primary Use Case)

```
1. System starts with: New model trained (validation accuracy 98.5% > current 98.2%)
2. System needs to: Deploy model with 48-hour gradual rollout (10% → 50% → 100%)
3. System performs:
   Stage 1 (Hours 0-16):
   - Copy new model: ~/.agency/models/ensemble_v2.pkl
   - Update A/B config: ML_PERCENTAGE=10, NEW_MODEL_PATH=ensemble_v2.pkl
   - Route traffic: 10% to new model (v2), 90% to current model (v1)
   - Collect metrics: 100+ predictions per model (VectorStore)
   - Validate accuracy: v2=98.4%, v1=98.2% (v2 ≥ v1 - 2% ✓)
   - Decision: PASS → proceed to Stage 2

   Stage 2 (Hours 16-32):
   - Update A/B config: ML_PERCENTAGE=50
   - Route traffic: 50% to new model (v2), 50% to current model (v1)
   - Collect metrics: 500+ predictions per model
   - Validate accuracy: v2=98.5%, v1=98.3% (v2 ≥ v1 - 2% ✓)
   - Decision: PASS → proceed to Stage 3

   Stage 3 (Hours 32-48):
   - Update symlink: ensemble_active.pkl → ensemble_v2.pkl (atomic swap)
   - Clear cache: Force MLClassifier reload on next call
   - Route traffic: 100% to new model (v2)
   - Collect metrics: 1,000+ predictions
   - Validate accuracy: v2=98.6% (stable, >98% target ✓)
   - Decision: PASS → rollout complete, archive v1 model

4. System achieves:
   - Rollout duration: 48 hours (automated, no manual intervention)
   - Zero downtime: 100% (symlink swap atomic, <1ms)
   - Accuracy improvement: 98.2% → 98.6% (+0.4%)
   - Production stability: Zero classification failures
   - VectorStore: All predictions logged for future training
```

#### Journey 2: Rollback Due to Accuracy Regression (Safety Scenario)

```
1. System starts with: New model deployed to Stage 1 (10% traffic)
2. System needs to: Rollback if new model accuracy < current - 2%
3. System performs:
   Stage 1 (Hours 0-16):
   - Route traffic: 10% to new model (v2), 90% to current model (v1)
   - Collect metrics: 100+ predictions per model
   - Validate accuracy: v2=96.0%, v1=98.2% (v2 < v1 - 2% ✗)
   - Detection: ACCURACY_REGRESSION (v2 = 96.0% < 96.2% threshold)
   - Alert: Email/Slack notification "Stage 1 failed, accuracy regression detected"
   - Decision: ROLLBACK → revert to 100% v1 traffic

   Rollback (< 5 minutes):
   - Update A/B config: ML_PERCENTAGE=0 (disable A/B test)
   - Keep symlink: ensemble_active.pkl → ensemble_v1.pkl (unchanged)
   - Route traffic: 100% to current model (v1)
   - Archive failed model: mv ensemble_v2.pkl ensemble_v2_failed_2025-10-10.pkl
   - VectorStore: Store rollback event for analysis
   - Alert: "Rollback complete, 100% traffic to v1"

4. System achieves:
   - Detection time: 16 hours (Stage 1 duration)
   - Rollback time: <5 minutes (config update + cache clear)
   - Zero production impact: v1 accuracy maintained (98.2%)
   - Safe failure: New model rejected before wide deployment
   - Learning: VectorStore stores misclassifications for retraining
```

#### Journey 3: Zero-Downtime Symlink Swap (Deployment Detail)

```
1. System starts with: Stage 2 passed (50% traffic validated)
2. System needs to: Swap to 100% new model (v2) without downtime
3. System performs:
   Pre-Swap Validation:
   - Verify new model exists: ls ~/.agency/models/ensemble_v2.pkl ✓
   - Verify model loadable: joblib.load(ensemble_v2.pkl) ✓
   - Verify accuracy metadata: v2.validation_accuracy = 98.5% ≥ 98% ✓
   - Verify model size: 50-100MB (reasonable for memory) ✓

   Atomic Swap:
   - Create temporary symlink: ensemble_active_tmp.pkl → ensemble_v2.pkl
   - Atomic rename: mv -f ensemble_active_tmp.pkl ensemble_active.pkl
   - Filesystem guarantees: Atomic operation, readers see old or new (never broken)
   - Cache invalidation: MLClassifier._model_loaded = False

   Post-Swap Validation:
   - Next classification: Lazy load ensemble_active.pkl → v2 loaded
   - First prediction: <500ms (cold start acceptable)
   - Subsequent predictions: <50ms p99 (cached in memory)
   - Verify routing: 100% traffic to v2 (A/B test disabled)

4. System achieves:
   - Swap duration: <1ms (symlink atomic)
   - Downtime: 0ms (readers never see broken symlink)
   - Cold start: <500ms (first classification after swap)
   - Validation: All predictions use v2 model (verified by model_version field)
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Gradual Rollout Pipeline

- **AC-1.1**: Three-stage rollout: Stage 1 (10%, 16h), Stage 2 (50%, 16h), Stage 3 (100%, final)
- **AC-1.2**: Automated stage progression: Cron job checks accuracy every 8 hours, advances if passing
- **AC-1.3**: Per-stage validation: New model accuracy ≥ current model - 2% (per-tier confusion matrix)
- **AC-1.4**: VectorStore metrics: Min 100 predictions per model per stage (statistical significance)
- **AC-1.5**: Configuration persistence: Rollout state stored in ~/.agency/rollout/state.json

#### Feature Component 2: A/B Testing Comparison

- **AC-2.1**: Deterministic routing: Hash-based split (same as Phase 3, extended to new_model vs current_model)
- **AC-2.2**: Split validation: Actual traffic within ±2% of configured percentage (10% → 8-12%, 50% → 48-52%)
- **AC-2.3**: Per-model metrics: Separate accuracy tracking for new_model and current_model (VectorStore tags)
- **AC-2.4**: Confidence distribution: Histogram of prediction confidence per model (detect low-confidence bias)
- **AC-2.5**: Tier-specific accuracy: Per-tier (P1, P2, P3) confusion matrices for each model

#### Feature Component 3: Automated Rollback

- **AC-3.1**: Rollback trigger: New model accuracy < current model - 2% at any stage (immediate rollback)
- **AC-3.2**: Rollback execution: Set ML_PERCENTAGE=0, archive failed model, alert team (<5min duration)
- **AC-3.3**: Safety guarantee: Current model always available (ensemble_active.pkl maintained during rollout)
- **AC-3.4**: Alert notification: Slack/Email notification on rollback with accuracy comparison
- **AC-3.5**: Post-rollback analysis: VectorStore stores rollback event with misclassification examples

#### Feature Component 4: Zero-Downtime Model Swap

- **AC-4.1**: Symlink strategy: ensemble_active.pkl → ensemble_v{N}.pkl (atomic swap via mv -f)
- **AC-4.2**: Version tracking: Model metadata includes training_date, version string (e.g., "v2_2025-10-10")
- **AC-4.3**: Cache invalidation: MLClassifier lazy reload after symlink change (no stale model)
- **AC-4.4**: Filesystem atomicity: Readers see old or new symlink (never broken/missing)
- **AC-4.5**: Rollback-ready: Old model (v1) kept as ensemble_v1.pkl for instant rollback

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Rollback time <5 minutes (config update + cache clear, no model retraining)
- **AC-P.2**: Symlink swap <1ms (atomic filesystem operation)
- **AC-P.3**: Cold start after swap <500ms (lazy load, first classification post-swap)
- **AC-P.4**: Zero classification downtime (100% availability during rollout)

#### Reliability

- **AC-R.1**: Rollout recovery: If cron job fails, next execution resumes from last stage (idempotent)
- **AC-R.2**: Filesystem safety: Symlink swap uses atomic rename (no broken links)
- **AC-R.3**: Model validation: Pre-swap checks ensure model loadable and accurate (fail early)
- **AC-R.4**: VectorStore resilience: Non-blocking logging (rollout continues if VectorStore slow)

#### Quality

- **AC-Q.1**: Statistical significance: Min 100 predictions per model per stage (confidence intervals)
- **AC-Q.2**: Accuracy threshold: -2% tolerance (balance between safety and progress)
- **AC-Q.3**: Tier-specific validation: All tiers (P1, P2, P3) must pass accuracy check (no blind spots)
- **AC-Q.4**: Alert latency: Rollback notification within 1 minute of decision (Slack/Email)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Stage progression requires full metrics collection (min 100 predictions per model)
- **AC-CI.2**: Accuracy comparison uses complete confusion matrix (all tiers, not aggregated only)
- **AC-CI.3**: Pre-swap validation checks all model properties (loadable, accurate, versioned)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Rollout pipeline 100% tested (unit + integration tests for all stages)
- **AC-CII.2**: Rollback tested with synthetic accuracy regression (forced failure scenario)
- **AC-CII.3**: Zero regression: Existing ML inference tests still pass (Phase 3 baseline)

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: No manual stage progression (cron job only, no API to skip stages)
- **AC-CIII.2**: No manual rollback bypass (accuracy threshold absolute, no overrides)
- **AC-CIII.3**: Environment-only config (ML_PERCENTAGE via cron, not user-settable)

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: All rollout events stored in VectorStore (stage progression, rollback, accuracy deltas)
- **AC-CIV.2**: Misclassifications during rollout tagged with model_version (new vs current)
- **AC-CIV.3**: Cross-session learning: Rollback analysis feeds next training cycle (why v2 failed)
- **AC-CIV.4**: Rollout learnings stored: Confidence thresholds, accuracy deltas, rollback reasons

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Phase 4 scope limited to rollout automation (no training pipeline changes)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Leap 5 Phase 4: A/B Testing Rollout & Auto-Updates                    │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ Rollout Pipeline │───▶│ A/B Testing      │───▶│ Model Swapper    │ │
│  │ (Cron Job)       │    │ Framework        │    │ (Symlink Mgmt)   │ │
│  │                  │    │                  │    │                  │ │
│  │ - Stage state    │    │ - Traffic split  │    │ - Atomic rename  │ │
│  │ - Accuracy check │    │ - Metric collect │    │ - Cache clear    │ │
│  │ - Progress/rollback    │ - Per-model stats│    │ - Version track  │ │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘ │
│           │                       │                        │            │
│           │              ┌────────▼────────┐               │            │
│           │              │ VectorStore     │               │            │
│           │              │ (Article IV)    │               │            │
│           │              │                 │               │            │
│           │              │ - Predictions   │               │            │
│           │              │ - Accuracy logs │               │            │
│           │              │ - Rollout events│               │            │
│           │              └────────┬────────┘               │            │
│           │                       │                        │            │
│           │              ┌────────▼────────┐               │            │
│           └─────────────▶│ MLClassifier    │◀──────────────┘            │
│                          │ (Phase 3)       │                            │
│                          │                 │                            │
│                          │ - Load model    │                            │
│                          │ - Classify task │                            │
│                          │ - Log prediction│                            │
│                          └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘

Model Filesystem Layout:
~/.agency/models/
  ├── ensemble_active.pkl   → ensemble_v2.pkl (symlink, atomic)
  ├── ensemble_v1.pkl       (previous model, rollback-ready)
  ├── ensemble_v2.pkl       (new model, under validation)
  └── ensemble_v2_failed_*.pkl (archived failures)

Rollout State:
~/.agency/rollout/
  ├── state.json            (current stage, start_time, metrics)
  └── history.jsonl         (all rollout events, VectorStore backup)
```

### 5.2 Rollout Pipeline Implementation

```python
"""
Rollout Pipeline: Automated gradual model deployment.

Constitutional compliance:
- Article I: Complete context (full metrics before stage progression)
- Article III: Automated enforcement (no manual stage skips)
- Article IV: VectorStore logging (all rollout events stored)
- Article V: Spec-driven (follows spec-010-ab-rollout-auto-updates.md)
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from enum import Enum
from pathlib import Path
from typing import Optional
import json

from shared.agent_context import AgentContext
from shared.type_definitions.result import Result, Ok, Err
from pydantic import BaseModel, Field


class RolloutStage(str, Enum):
    """Rollout stage enumeration."""
    STAGE_1 = "stage_1"  # 10% traffic, 16 hours
    STAGE_2 = "stage_2"  # 50% traffic, 16 hours
    STAGE_3 = "stage_3"  # 100% traffic, final
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class RolloutState(BaseModel):
    """Rollout state persistence model."""

    current_stage: RolloutStage = Field(
        RolloutStage.STAGE_1,
        description="Current rollout stage"
    )

    new_model_version: str = Field(
        ...,
        description="New model version string (e.g., v2_2025-10-10)"
    )

    current_model_version: str = Field(
        ...,
        description="Current production model version"
    )

    stage_start_time: datetime = Field(
        ...,
        description="Timestamp when current stage started (UTC)"
    )

    stage_duration_hours: int = Field(
        16,
        description="Duration of each stage (hours)"
    )

    new_model_accuracy: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="New model accuracy in current stage"
    )

    current_model_accuracy: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Current model accuracy in current stage"
    )

    new_model_prediction_count: int = Field(
        0,
        description="Number of predictions by new model in current stage"
    )

    current_model_prediction_count: int = Field(
        0,
        description="Number of predictions by current model in current stage"
    )

    rollback_reason: Optional[str] = Field(
        None,
        description="Reason for rollback (if rolled back)"
    )


class RolloutOrchestrator:
    """
    Orchestrate gradual model rollout with A/B testing and automated rollback.

    Workflow:
    1. Load rollout state from ~/.agency/rollout/state.json
    2. Check if stage duration elapsed (16 hours)
    3. Query VectorStore for per-model accuracy (min 100 predictions)
    4. Compare: new_model_accuracy ≥ current_model_accuracy - 2%
    5. If pass: Progress to next stage (10% → 50% → 100%)
    6. If fail: Rollback to 100% current model, alert team
    7. Store rollout event in VectorStore (Article IV)

    Performance:
    - State check: <100ms (local JSON read)
    - Accuracy query: <1s (VectorStore aggregation)
    - Stage progression: <5s (config update + symlink swap)
    - Rollback: <5 minutes (config update + archive + alert)
    """

    ROLLOUT_STATE_PATH = Path.home() / ".agency/rollout/state.json"
    ACCURACY_THRESHOLD_DELTA = 0.02  # 2% tolerance
    MIN_PREDICTIONS_PER_MODEL = 100  # Statistical significance

    def __init__(
        self,
        context: AgentContext,
        model_dir: Path = Path.home() / ".agency/models"
    ):
        """
        Initialize rollout orchestrator.

        Args:
            context: AgentContext for VectorStore logging (Article IV)
            model_dir: Directory containing ensemble models
        """
        self.context = context
        self.model_dir = model_dir
        self.state_path = self.ROLLOUT_STATE_PATH
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def check_and_progress(self) -> Result[str, str]:
        """
        Check rollout state and progress to next stage if conditions met.

        Called by cron job every 8 hours (twice per 16-hour stage).

        Returns:
            Result with status message or error

        Workflow:
        1. Load state (or initialize if first run)
        2. Check if stage duration elapsed
        3. Query VectorStore for per-model accuracy
        4. Validate accuracy threshold
        5. Progress to next stage or rollback
        6. Store event in VectorStore
        """
        try:
            # Step 1: Load current state
            state_result = self._load_state()

            if state_result.is_err():
                return state_result  # Propagate error

            state = state_result.unwrap()

            # Step 2: Check if stage duration elapsed
            elapsed = datetime.now(UTC) - state.stage_start_time
            stage_duration = timedelta(hours=state.stage_duration_hours)

            if elapsed < stage_duration:
                return Ok(
                    f"Stage {state.current_stage} in progress "
                    f"({elapsed.total_seconds() / 3600:.1f}h / {state.stage_duration_hours}h)"
                )

            # Step 3: Query VectorStore for per-model accuracy
            metrics_result = self._query_stage_metrics(state)

            if metrics_result.is_err():
                return metrics_result  # Propagate error

            new_accuracy, current_accuracy, new_count, current_count = metrics_result.unwrap()

            # Update state with metrics
            state.new_model_accuracy = new_accuracy
            state.current_model_accuracy = current_accuracy
            state.new_model_prediction_count = new_count
            state.current_model_prediction_count = current_count

            # Step 4: Validate accuracy threshold
            accuracy_delta = current_accuracy - new_accuracy
            threshold = self.ACCURACY_THRESHOLD_DELTA

            if accuracy_delta > threshold:
                # Accuracy regression detected, rollback
                return self._rollback(
                    state,
                    f"Accuracy regression: new_model={new_accuracy:.1%} < "
                    f"current_model={current_accuracy:.1%} - {threshold:.1%}"
                )

            # Step 5: Check prediction count (statistical significance)
            if new_count < self.MIN_PREDICTIONS_PER_MODEL:
                return Err(
                    f"Insufficient predictions for new model: {new_count} < "
                    f"{self.MIN_PREDICTIONS_PER_MODEL} (wait for more data)"
                )

            if current_count < self.MIN_PREDICTIONS_PER_MODEL:
                return Err(
                    f"Insufficient predictions for current model: {current_count} < "
                    f"{self.MIN_PREDICTIONS_PER_MODEL} (wait for more data)"
                )

            # Step 6: Progress to next stage
            return self._progress_stage(state)

        except Exception as e:
            return Err(f"Rollout orchestrator exception: {e}")

    def _load_state(self) -> Result[RolloutState, str]:
        """Load rollout state from disk or initialize if missing."""
        try:
            if not self.state_path.exists():
                return Err("Rollout state not found (call start_rollout() first)")

            with open(self.state_path, "r") as f:
                data = json.load(f)

            # Convert ISO timestamp to datetime
            data["stage_start_time"] = datetime.fromisoformat(
                data["stage_start_time"]
            )

            state = RolloutState(**data)
            return Ok(state)

        except Exception as e:
            return Err(f"Failed to load rollout state: {e}")

    def _query_stage_metrics(
        self,
        state: RolloutState
    ) -> Result[tuple[float, float, int, int], str]:
        """
        Query VectorStore for per-model accuracy in current stage.

        Args:
            state: Current rollout state

        Returns:
            Result with (new_accuracy, current_accuracy, new_count, current_count)

        VectorStore Query:
        - Filter: timestamp >= stage_start_time
        - Filter: model_version in [new_model_version, current_model_version]
        - Aggregate: accuracy per model (TP / (TP + FP + FN))
        """
        try:
            # Query predictions since stage start
            stage_start_iso = state.stage_start_time.isoformat()

            # Query new model predictions
            new_model_predictions = self.context.search_memories(
                tags=["prediction", state.new_model_version],
                filter_fn=lambda m: m.get("timestamp", "") >= stage_start_iso
            )

            # Query current model predictions
            current_model_predictions = self.context.search_memories(
                tags=["prediction", state.current_model_version],
                filter_fn=lambda m: m.get("timestamp", "") >= stage_start_iso
            )

            # Calculate accuracy for new model
            new_correct = sum(
                1 for p in new_model_predictions
                if p.get("predicted_tier") == p.get("actual_tier")
            )
            new_total = len(new_model_predictions)
            new_accuracy = new_correct / new_total if new_total > 0 else 0.0

            # Calculate accuracy for current model
            current_correct = sum(
                1 for p in current_model_predictions
                if p.get("predicted_tier") == p.get("actual_tier")
            )
            current_total = len(current_model_predictions)
            current_accuracy = (
                current_correct / current_total if current_total > 0 else 0.0
            )

            return Ok((new_accuracy, current_accuracy, new_total, current_total))

        except Exception as e:
            return Err(f"Failed to query stage metrics: {e}")

    def _progress_stage(self, state: RolloutState) -> Result[str, str]:
        """
        Progress to next rollout stage.

        Args:
            state: Current rollout state

        Returns:
            Result with status message or error

        Stage Progression:
        - STAGE_1 (10%) → STAGE_2 (50%): Update ML_PERCENTAGE=50
        - STAGE_2 (50%) → STAGE_3 (100%): Swap symlink, clear cache
        - STAGE_3 (100%) → COMPLETED: Archive old model, cleanup
        """
        try:
            if state.current_stage == RolloutStage.STAGE_1:
                # Progress to Stage 2 (50% traffic)
                state.current_stage = RolloutStage.STAGE_2
                state.stage_start_time = datetime.now(UTC)

                # Update A/B config: 50% traffic to new model
                self._update_ab_config(ml_percentage=50)

                # Store event
                self._store_rollout_event(
                    state,
                    event_type="stage_progression",
                    message="Progressed to Stage 2 (50% traffic)"
                )

                self._save_state(state)

                return Ok(
                    f"✅ Stage 1 passed (new_model={state.new_model_accuracy:.1%}, "
                    f"current_model={state.current_model_accuracy:.1%}). "
                    f"Progressed to Stage 2 (50% traffic)."
                )

            elif state.current_stage == RolloutStage.STAGE_2:
                # Progress to Stage 3 (100% traffic, symlink swap)
                state.current_stage = RolloutStage.STAGE_3
                state.stage_start_time = datetime.now(UTC)

                # Atomic symlink swap
                swap_result = self._swap_model_symlink(
                    state.new_model_version
                )

                if swap_result.is_err():
                    return swap_result  # Propagate error

                # Disable A/B test (100% to new model)
                self._update_ab_config(ml_percentage=100)

                # Store event
                self._store_rollout_event(
                    state,
                    event_type="stage_progression",
                    message="Progressed to Stage 3 (100% traffic, symlink swapped)"
                )

                self._save_state(state)

                return Ok(
                    f"✅ Stage 2 passed (new_model={state.new_model_accuracy:.1%}, "
                    f"current_model={state.current_model_accuracy:.1%}). "
                    f"Progressed to Stage 3 (100% traffic, symlink → {state.new_model_version})."
                )

            elif state.current_stage == RolloutStage.STAGE_3:
                # Complete rollout: Archive old model, cleanup
                state.current_stage = RolloutStage.COMPLETED

                # Archive old model
                old_model_path = self.model_dir / f"ensemble_{state.current_model_version}.pkl"
                archive_path = self.model_dir / f"ensemble_{state.current_model_version}_archived.pkl"

                if old_model_path.exists():
                    old_model_path.rename(archive_path)

                # Store event
                self._store_rollout_event(
                    state,
                    event_type="rollout_complete",
                    message=f"Rollout complete: {state.new_model_version} at 100% traffic"
                )

                self._save_state(state)

                return Ok(
                    f"🎉 Rollout complete: {state.new_model_version} deployed at 100% traffic. "
                    f"Old model ({state.current_model_version}) archived."
                )

            else:
                return Err(f"Invalid stage: {state.current_stage}")

        except Exception as e:
            return Err(f"Failed to progress stage: {e}")

    def _rollback(
        self,
        state: RolloutState,
        reason: str
    ) -> Result[str, str]:
        """
        Rollback to 100% current model due to accuracy regression.

        Args:
            state: Current rollout state
            reason: Rollback reason (for alerting)

        Returns:
            Result with rollback status or error

        Rollback Workflow:
        1. Set ML_PERCENTAGE=0 (disable A/B test)
        2. Archive failed model: mv ensemble_v2.pkl → ensemble_v2_failed_*.pkl
        3. Store rollback event in VectorStore
        4. Send alert (Slack/Email)
        5. Update state: current_stage = ROLLED_BACK
        """
        try:
            # Step 1: Disable A/B test (100% to current model)
            self._update_ab_config(ml_percentage=0)

            # Step 2: Archive failed model
            failed_model_path = self.model_dir / f"ensemble_{state.new_model_version}.pkl"
            archive_path = self.model_dir / (
                f"ensemble_{state.new_model_version}_failed_"
                f"{datetime.now(UTC).strftime('%Y-%m-%d_%H-%M-%S')}.pkl"
            )

            if failed_model_path.exists():
                failed_model_path.rename(archive_path)

            # Step 3: Update state
            state.current_stage = RolloutStage.ROLLED_BACK
            state.rollback_reason = reason

            # Step 4: Store rollback event
            self._store_rollout_event(
                state,
                event_type="rollback",
                message=f"ROLLBACK: {reason}"
            )

            self._save_state(state)

            # Step 5: Send alert
            self._send_alert(
                severity="WARNING",
                title="Model Rollback Triggered",
                message=(
                    f"Rollback: {state.new_model_version} failed accuracy check.\n"
                    f"Reason: {reason}\n"
                    f"Current model: {state.current_model_version} (restored to 100% traffic)"
                )
            )

            return Ok(
                f"⚠️  ROLLBACK: {reason}. "
                f"Restored 100% traffic to {state.current_model_version}. "
                f"Failed model archived: {archive_path.name}"
            )

        except Exception as e:
            return Err(f"Rollback failed: {e}")

    def _swap_model_symlink(self, new_model_version: str) -> Result[None, str]:
        """
        Atomic symlink swap: ensemble_active.pkl → ensemble_{new_model_version}.pkl

        Args:
            new_model_version: New model version string (e.g., "v2_2025-10-10")

        Returns:
            Result with None or error

        Atomicity:
        1. Create temporary symlink: ensemble_active_tmp.pkl → ensemble_{new_model_version}.pkl
        2. Atomic rename: mv -f ensemble_active_tmp.pkl ensemble_active.pkl
        3. Filesystem guarantees: Readers see old or new (never broken)
        """
        try:
            active_symlink = self.model_dir / "ensemble_active.pkl"
            new_model_path = self.model_dir / f"ensemble_{new_model_version}.pkl"

            # Validate new model exists
            if not new_model_path.exists():
                return Err(f"New model not found: {new_model_path}")

            # Create temporary symlink
            tmp_symlink = self.model_dir / "ensemble_active_tmp.pkl"

            if tmp_symlink.exists() or tmp_symlink.is_symlink():
                tmp_symlink.unlink()

            tmp_symlink.symlink_to(new_model_path.name)

            # Atomic rename (overwrites existing symlink)
            tmp_symlink.rename(active_symlink)

            return Ok(None)

        except Exception as e:
            return Err(f"Symlink swap failed: {e}")

    def _update_ab_config(self, ml_percentage: int) -> None:
        """
        Update A/B test configuration (ML_PERCENTAGE environment variable).

        Args:
            ml_percentage: Percentage of traffic to new model (0/10/50/100)

        Implementation:
        - Write to ~/.agency/rollout/ab_config.env
        - Source in cron job startup script
        """
        config_path = self.state_path.parent / "ab_config.env"

        with open(config_path, "w") as f:
            f.write(f"export ML_AB_TEST_ENABLED=true\n")
            f.write(f"export ML_PERCENTAGE={ml_percentage}\n")

    def _save_state(self, state: RolloutState) -> None:
        """Persist rollout state to disk."""
        # Convert datetime to ISO string for JSON serialization
        data = state.model_dump()
        data["stage_start_time"] = state.stage_start_time.isoformat()

        with open(self.state_path, "w") as f:
            json.dump(data, f, indent=2)

    def _store_rollout_event(
        self,
        state: RolloutState,
        event_type: str,
        message: str
    ) -> None:
        """
        Store rollout event in VectorStore (Article IV).

        Args:
            state: Current rollout state
            event_type: Event type (stage_progression, rollback, rollout_complete)
            message: Event message
        """
        from datetime import datetime, UTC

        self.context.store_memory(
            key=f"rollout_event_{datetime.now(UTC).isoformat()}",
            content={
                "event_type": event_type,
                "message": message,
                "current_stage": state.current_stage,
                "new_model_version": state.new_model_version,
                "current_model_version": state.current_model_version,
                "new_model_accuracy": state.new_model_accuracy,
                "current_model_accuracy": state.current_model_accuracy,
                "new_model_prediction_count": state.new_model_prediction_count,
                "current_model_prediction_count": state.current_model_prediction_count,
                "timestamp": datetime.now(UTC).isoformat()
            },
            tags=["rollout", "leap5_phase4", event_type, state.current_stage]
        )

    def _send_alert(self, severity: str, title: str, message: str) -> None:
        """
        Send alert notification (Slack/Email).

        Args:
            severity: Alert severity (INFO, WARNING, ERROR)
            title: Alert title
            message: Alert message body

        Implementation:
        - Log to console (immediate visibility)
        - Store in VectorStore (historical record)
        - TODO: Integrate Slack/Email (Phase 4 enhancement)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.warning(f"[{severity}] {title}: {message}")

        # Store alert in VectorStore
        self.context.store_memory(
            key=f"alert_{datetime.now(UTC).isoformat()}",
            content={
                "severity": severity,
                "title": title,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat()
            },
            tags=["alert", "rollout", severity.lower()]
        )
```

### 5.3 Cron Job Integration

```bash
#!/bin/bash
# scripts/rollout_check.sh
# Cron job: Check and progress rollout every 8 hours
#
# Installation:
# crontab -e
# 0 */8 * * * /Users/am/Code/Agency/scripts/rollout_check.sh >> /var/log/agency/rollout.log 2>&1

set -e

# Load environment
cd /Users/am/Code/Agency
source .venv/bin/activate
source ~/.agency/rollout/ab_config.env  # Load ML_PERCENTAGE

# Run rollout check
python -c "
from tools.ml_routing.rollout_orchestrator import RolloutOrchestrator
from shared.agent_context import create_agent_context

context = create_agent_context(session_id='rollout_cron')
orchestrator = RolloutOrchestrator(context)

result = orchestrator.check_and_progress()

if result.is_ok():
    print(result.unwrap())
else:
    print(f'ERROR: {result.unwrap_err()}', file=sys.stderr)
    sys.exit(1)
"
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: Phase 3 ML inference integration (MLClassifier, ABTestConfig)
- **Dependency 2**: VectorStore with prediction logging (Article IV)
- **Dependency 3**: Model versioning metadata (training_date, validation_accuracy)
- **Dependency 4**: Cron job scheduler (systemd timer or traditional cron)

### External Dependencies

- **External Dep 1**: Filesystem symlink support (atomic rename required)
- **External Dep 2**: JSON persistence (rollout state storage)
- **External Dep 3**: Alert integration (Slack/Email, optional in Phase 4)

### Technical Constraints

- **Constraint 1**: Stage duration 16 hours (fixed, no dynamic adjustment)
- **Constraint 2**: Accuracy threshold -2% (balance safety vs progress)
- **Constraint 3**: Min 100 predictions per model per stage (statistical significance)
- **Constraint 4**: Rollback time <5 minutes (config update + archive + alert)

### Business Constraints

- **Constraint 1**: No manual stage progression (cron job only, Article III)
- **Constraint 2**: No rollback bypass (accuracy threshold absolute)
- **Constraint 3**: Rollout duration 48 hours (3 stages × 16h, fixed)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Insufficient predictions during low-traffic periods** - *Mitigation*: Extend stage duration if <100 predictions collected
- **Risk 2**: **Accuracy regression undetected until Stage 2** - *Mitigation*: Stage 1 catches major regressions early (10% exposure)

### Medium Risk Items

- **Risk 3**: **Cron job failure preventing progression** - *Mitigation*: Idempotent design, next execution resumes from last stage
- **Risk 4**: **Symlink swap race condition** - *Mitigation*: Atomic rename guarantees (filesystem-level)

### Low Risk Items

- **Risk 5**: **VectorStore query timeout** - *Mitigation*: 10-second timeout, retry with exponential backoff
- **Risk 6**: **Alert notification failure** - *Mitigation*: Log to console + VectorStore (redundancy)

### Constitutional Risks

- **Constitutional Risk 1**: **Article III violation (manual stage skip)** - *Mitigation*: No API to skip stages, cron job only
- **Constitutional Risk 2**: **Article IV violation (rollout events not logged)** - *Mitigation*: Assert VectorStore write in integration test

---

## Testing Strategy

### Test Categories

#### Unit Tests (15+ tests)

1. **RolloutOrchestrator Tests** (8 tests)
   - Load state (success, missing file, corrupt JSON)
   - Query metrics (VectorStore aggregation, insufficient predictions)
   - Progress stage (Stage 1 → 2, Stage 2 → 3, Stage 3 → complete)
   - Rollback (accuracy regression, alert notification)

2. **Model Swapper Tests** (4 tests)
   - Symlink swap (atomic rename validation)
   - Rollback-ready (old model preserved)
   - Cache invalidation (lazy reload after swap)

3. **A/B Config Tests** (3 tests)
   - Update config (0% / 10% / 50% / 100%)
   - Environment persistence (config file read/write)

#### Integration Tests (10+ tests)

1. **End-to-End Rollout** (3 tests)
   - Successful 3-stage rollout (10% → 50% → 100%)
   - Rollback at Stage 1 (accuracy regression)
   - Rollback at Stage 2 (late-stage regression)

2. **VectorStore Integration** (3 tests)
   - Rollout events logged (stage progression, rollback)
   - Accuracy query (per-model metrics)
   - Alert storage (VectorStore backup)

3. **Cron Job Simulation** (2 tests)
   - Idempotent execution (resume after failure)
   - Stage duration validation (16-hour threshold)

4. **Zero-Downtime Validation** (2 tests)
   - Classification latency during swap (<50ms p99)
   - No broken symlink errors (atomic rename)

### Test Data Requirements

- **Test Data 1**: Synthetic prediction logs (100+ per model per stage)
- **Test Data 2**: Mock models with metadata (version, accuracy)
- **Test Data 3**: Rollout state snapshots (each stage + rollback scenarios)

### Test Environment Requirements

- **Environment 1**: ~/.agency/models/ directory with test models
- **Environment 2**: VectorStore with write access (rollout events)
- **Environment 3**: Cron job simulator (time-travel for stage duration)

---

## Implementation Phases

### Phase 4.1: Rollout Orchestrator Core (Day 1-2)

- **Scope**: RolloutOrchestrator class, state management, accuracy validation
- **Deliverables**:
  - `tools/ml_routing/rollout_orchestrator.py` (~650 lines)
  - Unit tests (8 tests, orchestrator logic)
- **Success Criteria**: Stage progression logic 100% tested, rollback functional

### Phase 4.2: Model Swapper & A/B Integration (Day 2-3)

- **Scope**: Symlink management, atomic swap, A/B config updates
- **Deliverables**:
  - `tools/ml_routing/model_swapper.py` (~200 lines)
  - Unit tests (4 tests, symlink atomicity)
- **Success Criteria**: Zero-downtime swap validated, rollback-ready

### Phase 4.3: Cron Job & Alert Integration (Day 3-4)

- **Scope**: Cron script, alert notifications, VectorStore event logging
- **Deliverables**:
  - `scripts/rollout_check.sh` (~50 lines)
  - Alert integration (console + VectorStore)
  - Integration tests (10 tests, end-to-end rollout)
- **Success Criteria**: Cron job idempotent, alerts sent on rollback

### Phase 4.4: Production Validation (Day 4-5)

- **Scope**: 48-hour test rollout, metrics dashboard, documentation
- **Deliverables**:
  - Test rollout report (accuracy comparison, stage durations)
  - Rollout monitoring dashboard (Grafana/Streamlit)
  - Documentation: Phase 4 execution summary
- **Success Criteria**: Rollout completes successfully, zero production issues

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: MLClassifier (Phase 3), RolloutOrchestrator, HybridExecutor
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), DevOps (cron job reliability)

### Review Criteria

- **Completeness**: All rollout components specified (orchestrator, swapper, cron, alerts)
- **Clarity**: Architecture diagrams, code examples, rollout workflow documented
- **Feasibility**: 48-hour rollout achievable, <5min rollback validated
- **Constitutional Compliance**: Article I-V validated (especially Article III automation)
- **Quality Standards**: Zero-downtime guarantees, accuracy threshold justified

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **DevOps Approval**: Pending cron job reliability validation
- [ ] **Final Approval**: Pending after Phase 4.3 implementation (cron integration)

---

## Appendices

### Appendix A: Glossary

- **Gradual Rollout**: Three-stage deployment (10% → 50% → 100%) with validation at each stage
- **A/B Testing**: Comparison of new model vs current model accuracy on same production traffic
- **Rollback**: Revert to 100% current model due to accuracy regression (<current - 2%)
- **Zero-Downtime Swap**: Atomic symlink rename (ensemble_active.pkl) with no service interruption
- **Rollout Orchestrator**: Automated pipeline checking accuracy and progressing stages (cron job)

### Appendix B: References

- **Spec-007**: Leap 5 Phase 3 ML Inference Integration (baseline)
- **Spec-008**: Weekly Retraining Pipeline (training foundation)
- **ADR-026**: ML Classifier Integration (Phase 3 architecture)
- **ADR-003**: Automated Merge Enforcement (no manual overrides)
- **ADR-004**: Continuous Learning (VectorStore mandate)

### Appendix C: Related Documents

- **Spec**: `specs/spec-007-phase3-ml-inference.md` (Phase 3 foundation)
- **Plan**: `plans/plan-010-ab-rollout-auto-updates.md` (to be created after spec approval)
- **Tests**: `tests/test_rollout_orchestrator.py`, `tests/test_model_swapper.py`, `tests/test_rollout_e2e.py`

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification: Gradual rollout, A/B testing, automated rollback, zero-downtime swaps |

---

*"From validation to deployment, from testing to production, from caution to confidence."*
