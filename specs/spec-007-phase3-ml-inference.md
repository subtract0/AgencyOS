# Specification: Leap 5 Phase 3 - ML Inference Integration

**Spec ID**: `spec-007-phase3-ml-inference`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**:
- `spec-005-advanced-pattern-recognition.md` (Leap 5 Phase 1-2 foundation)
- `spec-006-ensemble-model-pydantic.md` (EnsembleModel schema)
- `spec-004-quality-feedback-loop.md` (Leap 4 fallback system)
**Related ADRs**:
- `ADR-004: Continuous Learning` (VectorStore integration)
- `ADR-024: Adaptive Model Router` (cost optimization)

---

## Executive Summary

Leap 5 Phase 3 completes the ML-powered routing system by integrating trained ensemble models into HybridExecutor with production-grade inference, A/B testing, and online learning. This phase replaces rule-based classification (Leap 4) with ML predictions while maintaining rule-based fallback for robustness. Target: >98% accuracy, <50ms p99 latency, <$0.01 per classification.

**Key Innovation**: Zero-downtime deployment with A/B testing framework and deterministic traffic splitting for gradual model rollout.

---

## Goals

### Primary Goals

- **Goal 1**: MLClassifier loads trained EnsembleModel and performs inference <50ms p99 (no latency regression vs Leap 4)
- **Goal 2**: HybridExecutor integration with A/B testing (50/50 split, deterministic routing by task_id hash)
- **Goal 3**: Prediction logging for online learning (Article IV: all predictions stored in VectorStore)
- **Goal 4**: Rule-based fallback when ML confidence <0.7 (graceful degradation, no service disruption)
- **Goal 5**: Zero regression in existing HybridExecutor tests (100% backward compatibility)

### Success Metrics

| Metric | Target | Measurement Method | Baseline |
|--------|--------|-------------------|----------|
| **ML Accuracy** | ≥98% | 100-task validation set | 85-90% (Leap 4 rules) |
| **Inference Latency (p99)** | <50ms | Telemetry logging | <50ms (Leap 4) |
| **Model Load Time** | <1s | Cold start timing | N/A (new metric) |
| **A/B Split Balance** | 48-52% | 1,000 samples | Perfect (deterministic hash) |
| **Prediction Logging** | 100% | VectorStore query | N/A (new feature) |
| **Fallback Rate** | <10% | Confidence threshold monitoring | N/A (new metric) |
| **Test Pass Rate** | 100% | Existing HybridExecutor tests | 100% (baseline) |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Automatic model retraining in production (weekly batch retraining sufficient, see Phase 4)
- **Non-Goal 2**: Real-time model updates during inference (models loaded at startup, redeployed after training)
- **Non-Goal 3**: Multi-model comparison beyond A/B (future: champion/challenger framework)
- **Non-Goal 4**: Custom model architectures (scikit-learn ensemble only, keep Phase 2 design)

### Future Considerations

- **Future Enhancement 1**: Champion/challenger framework (3+ models in A/B test simultaneously)
- **Future Enhancement 2**: Online learning (incremental model updates during production)
- **Future Enhancement 3**: Model ensembling with rule-based system (ML + rules weighted voting)
- **Future Enhancement 4**: Active learning (request human labels for uncertain predictions)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: HybridExecutor (Primary Consumer)

- **Description**: Task routing system that uses ML predictions to classify complexity (simple/moderate/complex)
- **Goals**: >98% accuracy, <50ms p99 latency, zero downtime deployments, graceful degradation
- **Pain Points**: Rule-based system (Leap 4) requires manual tuning, struggles with novel task patterns
- **Technical Proficiency**: Autonomous agent with ML model loading, confidence thresholding, fallback logic

#### Persona 2: ML Model (Component)

- **Description**: Trained EnsembleModel (RandomForest + GradientBoosting) loaded from ~/.agency/models/
- **Goals**: Low-latency inference (<10ms), high confidence scores (>0.7), stable predictions
- **Pain Points**: Cold start latency, model drift, version management
- **Technical Proficiency**: Scikit-learn pickle serialization, thread-safe inference

#### Persona 3: Development Team (Monitoring & Debugging)

- **Description**: Engineers monitoring ML accuracy, investigating misclassifications, rolling back models
- **Goals**: A/B test metrics, prediction logs, confidence distribution, rollback capability
- **Pain Points**: Black-box ML decisions, need explainability (SHAP), A/B test validation
- **Technical Proficiency**: ML debugging, telemetry dashboards, VectorStore queries

### User Journeys

#### Journey 1: ML-Powered Classification (Primary Use Case)

```
1. User starts with: New task arrives at HybridExecutor
2. System needs to: Predict complexity tier with >98% accuracy, <50ms latency
3. System performs:
   - Check A/B split: task_id hash → 50% use ML model, 50% use rules (Leap 4)
   - Extract features: task description → TaskFeatureVector (1644-dim)
   - Load ML model: lazy load EnsembleModel from ~/.agency/models/ (cache in memory)
   - Predict tier: model.predict_proba(features) → [P(simple), P(moderate), P(complex)]
   - Check confidence: max(proba) ≥ 0.7 → use ML prediction, else fallback to rules
   - Store prediction: VectorStore logging (Article IV)
   - Return tier: "complex" (confidence=0.92, method="ml_model")
4. System achieves:
   - Tier prediction: "complex" (confidence=0.92)
   - Latency: 42ms (1ms load + 25ms features + 10ms inference + 6ms logging)
   - Cost: $0.00002 (embedding only, inference free)
   - Fallback: None (confidence ≥0.7)
   - VectorStore: Prediction logged for future training
```

#### Journey 2: A/B Testing (Gradual Rollout)

```
1. System starts with: New model trained (validation accuracy 98.5%)
2. System needs to: Validate model in production with 50% traffic
3. System performs:
   - Deploy new model: Copy ensemble.pkl to ~/.agency/models/routing_classifier_v2.pkl
   - Configure A/B: A_B_TEST_ENABLED=true, NEW_MODEL_PCT=0.5
   - Route traffic: task_id hash % 100 < 50 → new model (v2), else old model (v1)
   - Collect metrics: 24 hours of production traffic
   - Analyze accuracy: VectorStore query for quality feedback (Leap 4 integration)
   - Compare models: New model accuracy 98.5% vs old model 98.2% (+0.3%)
   - Decision: Deploy to 100% traffic (accuracy improvement validated)
4. System achieves:
   - A/B split: 50.2% new model, 49.8% old model (deterministic hash)
   - Accuracy: New model 98.5%, old model 98.2% (statistically significant)
   - Cost: Zero incremental cost (same feature extraction)
   - Deployment: Promote v2 to default, retire v1
```

#### Journey 3: Graceful Degradation (Low Confidence Fallback)

```
1. System starts with: Novel task (never seen in training data)
2. System needs to: Handle low-confidence prediction without crashing
3. System performs:
   - Extract features: task description → TaskFeatureVector
   - ML prediction: model.predict_proba(features) → [0.42, 0.35, 0.23] (max=0.42 < 0.7)
   - Detect low confidence: max(proba) < 0.7 → fallback required
   - Fallback to rules: Leap 4 rule-based classifier (test failures, code churn, timing)
   - Rule prediction: "moderate" (confidence=0.8, rule: "has_refactor_keyword=1")
   - Store prediction: VectorStore logging with method="rule_based_fallback"
   - Return tier: "moderate" (confidence=0.8, fallback=True)
4. System achieves:
   - Tier prediction: "moderate" (rule-based)
   - Latency: 85ms (42ms ML + 43ms fallback, still <100ms p99)
   - Robustness: No crash, graceful degradation (Article I: complete context)
   - Learning: Logged as low-confidence case for future training
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: MLClassifier

- **AC-1.1**: `MLClassifier` class loads EnsembleModel from ~/.agency/models/ (lazy init, cached)
- **AC-1.2**: `classify_task()` method returns ClassificationResult (tier, confidence, method, proba)
- **AC-1.3**: Feature extraction: TaskFeatureVector generated from task description (<25ms p99)
- **AC-1.4**: Inference: model.predict_proba() called (<10ms p99 for 1644-dim input)
- **AC-1.5**: Confidence threshold: if max(proba) < 0.7, fallback to Leap 4 rules (graceful degradation)

#### Feature Component 2: HybridExecutor Integration

- **AC-2.1**: HybridExecutor._execute_at_tier() updated to use MLClassifier for tier selection
- **AC-2.2**: A/B testing: task_id hash % 100 < NEW_MODEL_PCT → new model, else old model (deterministic split)
- **AC-2.3**: Backward compatibility: existing tests pass 100% (zero regression)
- **AC-2.4**: Model loading: EnsembleModel loaded at first classification (lazy init, <1s cold start)
- **AC-2.5**: Error handling: if MLClassifier fails, fallback to rule-based (no crash, Article I)

#### Feature Component 3: Prediction Logging

- **AC-3.1**: All ML predictions stored in VectorStore (Article IV: mandatory learning integration)
- **AC-3.2**: Prediction schema: task_id, tier, confidence, method, proba, timestamp, session_id
- **AC-3.3**: Async logging: VectorStore writes non-blocking (<5ms p99, don't delay classification)
- **AC-3.4**: Fallback logging: rule-based predictions also logged (method="rule_based_fallback")
- **AC-3.5**: Query API: VectorStore search by task_id, tier, method, confidence range (debugging)

#### Feature Component 4: A/B Testing Framework

- **AC-4.1**: `ABTestConfig` class: A_B_TEST_ENABLED, NEW_MODEL_PCT, NEW_MODEL_PATH env vars
- **AC-4.2**: Deterministic split: hash(task_id) % 100 < NEW_MODEL_PCT → new model (48-52% for 1,000 samples)
- **AC-4.3**: Metrics collection: A/B group stored in prediction log (telemetry analysis)
- **AC-4.4**: Rollback capability: set NEW_MODEL_PCT=0 to disable new model (instant rollback)
- **AC-4.5**: Promotion: set NEW_MODEL_PCT=100, update default model path (full deployment)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Model load time <1s cold start (pickle deserialization + memory allocation)
- **AC-P.2**: Inference latency <50ms p99 (25ms features + 10ms inference + 15ms overhead)
- **AC-P.3**: Fallback latency <100ms p99 (ML path + rule evaluation)
- **AC-P.4**: Memory overhead <200MB (EnsembleModel + feature cache, 1,000 tasks)

#### Quality

- **AC-Q.1**: ML accuracy ≥98% on validation set (100 held-out tasks with ground truth)
- **AC-Q.2**: A/B split balance 48-52% (1,000 samples, deterministic hash validation)
- **AC-Q.3**: Fallback rate <10% (90% of predictions have confidence ≥0.7)
- **AC-Q.4**: Test pass rate 100% (all existing HybridExecutor tests, zero regression)

#### Reliability

- **AC-R.1**: Thread-safe inference: model.predict_proba() concurrent safe (sklearn guarantees)
- **AC-R.2**: Graceful degradation: MLClassifier failures don't crash HybridExecutor
- **AC-R.3**: Model versioning: EnsembleModel.training_date field tracks model version
- **AC-R.4**: Rollback safety: old model always available (NEW_MODEL_PCT=0 instant rollback)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Feature extraction completes before prediction (no partial features)
- **AC-CI.2**: Model loading retries on failure (2x, 3x timeouts per Article I)
- **AC-CI.3**: Fallback invoked if MLClassifier fails (complete degradation path)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: EnsembleModel validates accuracy ≥0.98 on load (Pydantic validator)
- **AC-CII.2**: 100% test pass rate on existing HybridExecutor tests (integration validated)
- **AC-CII.3**: A/B split validated with 1,000 samples (48-52% balance)

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: A/B test automated: if new model accuracy ≥current + 0.5%, promote to 100%
- **AC-CIII.2**: Rollback automated: if production accuracy drops >3%, set NEW_MODEL_PCT=0

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: All ML predictions stored in VectorStore (constitutional mandate)
- **AC-CIV.2**: Fallback predictions also logged (rule-based method tracked)
- **AC-CIV.3**: Prediction logs query-able for training data extraction (weekly retraining)
- **AC-CIV.4**: Cross-session learning: VectorStore accumulates all predictions (institutional memory)

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Phase 3 scope limited to inference integration (no training pipeline changes)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Leap 5 Phase 3: ML Inference Integration                              │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ HybridExecutor   │───▶│ MLClassifier     │───▶│ EnsembleModel    │ │
│  │                  │    │                  │    │                  │ │
│  │ - Task routing   │    │ - Load model     │    │ - RandomForest   │ │
│  │ - A/B split      │    │ - Extract features│   │ - GradientBoosting│ │
│  │ - Tier selection │    │ - Predict tier   │    │ - Soft voting    │ │
│  └──────────────────┘    │ - Confidence     │    │ - Confidence     │ │
│           │              │   threshold      │    └──────────────────┘ │
│           │              └──────────────────┘             │            │
│           │                       │                        │            │
│           │              (confidence <0.7)                 │            │
│           │                       ▼                        │            │
│           │              ┌──────────────────┐             │            │
│           └─────────────▶│ Rule-Based       │             │            │
│                          │ Fallback (Leap 4)│             │            │
│                          │                  │             │            │
│                          │ - Test failures  │             │            │
│                          │ - Code churn     │             │            │
│                          │ - Timing         │             │            │
│                          └──────────────────┘             │            │
│                                   │                        │            │
│                                   └────────────────────────┘            │
│                                              │                          │
│                                   ┌──────────▼─────────┐                │
│                                   │ VectorStore        │                │
│                                   │ (Article IV)       │                │
│                                   │                    │                │
│                                   │ - Prediction logs  │                │
│                                   │ - A/B group tags   │                │
│                                   │ - Confidence scores│                │
│                                   │ - Method tracking  │                │
│                                   └────────────────────┘                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 MLClassifier Implementation

```python
"""
MLClassifier: Load trained EnsembleModel and perform inference.

Constitutional compliance:
- Article I: Complete context (feature extraction completes before prediction)
- Article II: 100% verification (EnsembleModel validates accuracy ≥0.98)
- Article IV: VectorStore logging (all predictions stored)
- Article V: Spec-driven (follows spec-007-phase3-ml-inference.md)
"""

from pathlib import Path
from typing import Optional
import joblib
import numpy as np

from shared.agent_context import AgentContext
from shared.models.ensemble_model import EnsembleModel
from shared.models.task_feature_vector import TaskFeatureVector
from shared.type_definitions.result import Result, Ok, Err
from tools.ml_routing.feature_extractor import FeatureExtractor
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """ML classification result with confidence and metadata."""

    task_id: str = Field(..., description="Task identifier")
    tier: str = Field(..., description="Predicted tier (simple/moderate/complex)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    method: str = Field(..., description="Classification method (ml_model or rule_based_fallback)")
    model_version: str = Field(..., description="Model training date (version ID)")
    class_probabilities: dict[str, float] = Field(
        ...,
        description="Class probabilities: {simple: 0.1, moderate: 0.2, complex: 0.7}"
    )
    features: Optional[TaskFeatureVector] = Field(None, description="Extracted features")


class MLClassifier:
    """
    ML-powered task classifier with lazy model loading and rule-based fallback.

    Workflow:
    1. Extract features (TaskFeatureVector, 1644-dim)
    2. Load model (lazy init, cached in memory)
    3. Predict tier (model.predict_proba, <10ms)
    4. Check confidence (if <0.7, fallback to Leap 4 rules)
    5. Log prediction (VectorStore, Article IV)

    Performance:
    - Cold start: <1s (model loading)
    - Inference: <50ms p99 (25ms features + 10ms ML + 15ms overhead)
    - Fallback: <100ms p99 (ML + rules)
    """

    def __init__(
        self,
        context: AgentContext,
        model_path: str = "~/.agency/models/routing_classifier_latest.pkl",
        confidence_threshold: float = 0.7,
        feature_extractor: Optional[FeatureExtractor] = None,
    ):
        """
        Initialize MLClassifier with lazy model loading.

        Args:
            context: AgentContext for VectorStore logging (Article IV)
            model_path: Path to serialized EnsembleModel (pickle format)
            confidence_threshold: Min confidence for ML prediction (default 0.7)
            feature_extractor: FeatureExtractor instance (creates if None)
        """
        self.context = context
        self.model_path = Path(model_path).expanduser()
        self.confidence_threshold = confidence_threshold
        self.feature_extractor = feature_extractor or FeatureExtractor(context)

        # Lazy loading (model loaded on first classification)
        self._model: Optional[EnsembleModel] = None
        self._model_loaded = False

        # Tier encoding (matches training data)
        self.tier_names = ["simple", "moderate", "complex"]

    def classify_task(
        self,
        task_id: str,
        task_description: str,
        task_metadata: Optional[dict] = None
    ) -> Result[ClassificationResult, str]:
        """
        Classify task complexity using ML model with rule-based fallback.

        Args:
            task_id: Task identifier
            task_description: Task description text
            task_metadata: Optional metadata (estimated_time, etc.)

        Returns:
            Result with ClassificationResult or error message

        Workflow:
        1. Extract features (TaskFeatureVector)
        2. Load model (lazy init if not loaded)
        3. Predict tier (model.predict_proba)
        4. Check confidence (if <0.7, fallback to rules)
        5. Log prediction (VectorStore, Article IV)

        Performance:
        - Feature extraction: <25ms p99
        - Model inference: <10ms p99
        - Total: <50ms p99 (ML path), <100ms p99 (fallback path)
        """
        try:
            # Step 1: Extract features (Article I: complete context)
            features_result = self.feature_extractor.extract_features(
                task_description, task_metadata
            )

            if features_result.is_err():
                # Feature extraction failed, fallback to rules
                return self._fallback_to_rules(
                    task_id, task_description,
                    f"Feature extraction failed: {features_result.unwrap_err()}"
                )

            features = features_result.unwrap()

            # Step 2: Load model (lazy init, cached)
            if not self._model_loaded:
                load_result = self._load_model()
                if load_result.is_err():
                    return self._fallback_to_rules(
                        task_id, task_description,
                        f"Model loading failed: {load_result.unwrap_err()}"
                    )

            # Step 3: Predict tier with confidence
            feature_vector = self._vectorize_features(features)
            proba = self._model.ensemble.predict_proba([feature_vector])[0]

            predicted_tier_idx = int(np.argmax(proba))
            confidence = float(proba[predicted_tier_idx])
            predicted_tier = self.tier_names[predicted_tier_idx]

            # Build class probabilities dict
            class_probabilities = {
                tier: float(prob) for tier, prob in zip(self.tier_names, proba)
            }

            # Step 4: Confidence threshold check
            if confidence >= self.confidence_threshold:
                # High confidence ML prediction
                result = ClassificationResult(
                    task_id=task_id,
                    tier=predicted_tier,
                    confidence=confidence,
                    method="ml_model",
                    model_version=self._model.training_date,
                    class_probabilities=class_probabilities,
                    features=features
                )

                # Store prediction (Article IV)
                self._store_prediction(result)

                return Ok(result)
            else:
                # Low confidence, fallback to rules
                return self._fallback_to_rules(
                    task_id, task_description,
                    f"ML confidence {confidence:.3f} < {self.confidence_threshold}"
                )

        except Exception as e:
            # Catch-all fallback (graceful degradation)
            return self._fallback_to_rules(
                task_id, task_description,
                f"MLClassifier exception: {e}"
            )

    def _load_model(self) -> Result[EnsembleModel, str]:
        """
        Load EnsembleModel from disk (lazy init, cached).

        Returns:
            Result with EnsembleModel or error message

        Performance:
        - Load time: <1s cold start (pickle deserialization)
        - Memory: ~100MB (model + cache)

        Constitutional Compliance:
        - Article I: Retry on timeout (2x, 3x)
        - Article II: EnsembleModel validates accuracy ≥0.98
        """
        try:
            if not self.model_path.exists():
                return Err(f"Model file not found: {self.model_path}")

            # Load model with joblib (faster than pickle for sklearn)
            self._model = joblib.load(self.model_path)

            # Validate model type (Article II: verification)
            if not isinstance(self._model, EnsembleModel):
                return Err(
                    f"Invalid model type: {type(self._model).__name__}, "
                    "expected EnsembleModel"
                )

            self._model_loaded = True
            return Ok(self._model)

        except Exception as e:
            return Err(f"Model loading failed: {e}")

    def _vectorize_features(self, features: TaskFeatureVector) -> np.ndarray:
        """Flatten TaskFeatureVector to 1644-dim numpy array."""
        return np.array(
            features.embedding +
            features.tfidf_features +
            [
                features.description_length,
                features.word_count,
                features.has_refactor_keyword,
                features.has_test_keyword,
                features.has_async_keyword,
                features.has_fix_keyword,
                features.estimated_time_seconds,
                features.historical_tier_mode
            ]
        )

    def _fallback_to_rules(
        self,
        task_id: str,
        task_description: str,
        reason: str
    ) -> Result[ClassificationResult, str]:
        """
        Fallback to Leap 4 rule-based classification.

        Args:
            task_id: Task identifier
            task_description: Task description text
            reason: Reason for fallback (logged for debugging)

        Returns:
            Result with ClassificationResult (rule-based method)

        Graceful Degradation:
        - Never crashes (Article I: complete context)
        - Logs fallback reason (telemetry)
        - Returns rule-based prediction (Leap 4)
        """
        from tools.quality_feedback.rule_classifier import RuleClassifier

        # Use Leap 4 rule-based classifier
        rule_classifier = RuleClassifier()
        rule_result = rule_classifier.classify(task_description)

        if rule_result.is_err():
            return rule_result  # Propagate error

        rule_prediction = rule_result.unwrap()

        result = ClassificationResult(
            task_id=task_id,
            tier=rule_prediction.tier,
            confidence=rule_prediction.confidence,
            method="rule_based_fallback",
            model_version="leap4_rules",
            class_probabilities={},  # Rules don't provide class probabilities
            features=None
        )

        # Store fallback prediction (Article IV)
        self._store_prediction(result, fallback_reason=reason)

        return Ok(result)

    def _store_prediction(
        self,
        result: ClassificationResult,
        fallback_reason: Optional[str] = None
    ) -> None:
        """
        Store prediction in VectorStore (Article IV: mandatory).

        Args:
            result: Classification result to store
            fallback_reason: Optional reason for fallback (debugging)

        Performance:
        - Async write: <5ms p99 (non-blocking)
        - Storage: ~500 bytes per prediction
        """
        from datetime import datetime, UTC

        self.context.store_memory(
            key=f"ml_classification_{result.task_id}",
            content={
                "task_id": result.task_id,
                "tier": result.tier,
                "confidence": result.confidence,
                "method": result.method,
                "model_version": result.model_version,
                "class_probabilities": result.class_probabilities,
                "fallback_reason": fallback_reason,
                "timestamp": datetime.now(UTC).isoformat()
            },
            tags=["ml_classification", "leap5_phase3", result.tier, result.method]
        )
```

### 5.3 A/B Testing Framework

```python
"""
A/B Testing Framework: Deterministic traffic splitting for gradual rollout.

Constitutional compliance:
- Article II: 100% verification (A/B split validated with 1,000 samples)
- Article III: Automated enforcement (promote if accuracy improvement ≥0.5%)
- Article IV: VectorStore tracking (A/B group logged in predictions)
"""

import hashlib
from dataclasses import dataclass
from typing import Literal


@dataclass
class ABTestConfig:
    """A/B test configuration."""

    enabled: bool = False  # A_B_TEST_ENABLED env var
    new_model_pct: int = 50  # NEW_MODEL_PCT env var (0-100)
    new_model_path: str = "~/.agency/models/routing_classifier_v2.pkl"
    old_model_path: str = "~/.agency/models/routing_classifier_v1.pkl"


class ABTestRouter:
    """
    Deterministic A/B test router using task_id hash.

    Workflow:
    - hash(task_id) % 100 < new_model_pct → new model
    - else → old model

    Properties:
    - Deterministic: Same task_id always routes to same model (reproducible)
    - Balanced: 48-52% split for 1,000 samples (validated in tests)
    - Zero-latency: Hash computation <1μs (no I/O)
    """

    def __init__(self, config: ABTestConfig):
        self.config = config

    def select_model_group(self, task_id: str) -> Literal["new_model", "old_model"]:
        """
        Select A/B group for task using deterministic hash.

        Args:
            task_id: Task identifier

        Returns:
            "new_model" or "old_model"

        Example:
            >>> router = ABTestRouter(ABTestConfig(enabled=True, new_model_pct=50))
            >>> router.select_model_group("task_123")
            "new_model"  # hash("task_123") % 100 = 23 < 50
            >>> router.select_model_group("task_789")
            "old_model"  # hash("task_789") % 100 = 67 >= 50
        """
        if not self.config.enabled:
            return "old_model"  # A/B test disabled, use old model

        # Deterministic hash: MD5(task_id) % 100
        hash_value = int(hashlib.md5(task_id.encode()).hexdigest(), 16) % 100

        if hash_value < self.config.new_model_pct:
            return "new_model"
        else:
            return "old_model"
```

### 5.4 HybridExecutor Integration

```python
"""
HybridExecutor integration with MLClassifier and A/B testing.

Modifications:
1. Add MLClassifier initialization
2. Update _execute_at_tier() to use ML classification
3. Add A/B test routing logic
4. Maintain backward compatibility (100% test pass rate)
"""

class HybridExecutor:
    """Enhanced HybridExecutor with ML classification."""

    def __init__(
        self,
        message_bus: MessageBus,
        cost_tracker: CostTracker,
        agent_context: AgentContext,
        # ... existing params
        enable_ml_classifier: bool = True,  # NEW: Enable ML classification
        ab_test_config: Optional[ABTestConfig] = None,  # NEW: A/B test config
    ):
        # ... existing initialization

        # NEW: ML classification integration
        if enable_ml_classifier:
            self.ml_classifier = MLClassifier(
                context=agent_context,
                confidence_threshold=0.7
            )
            self.ab_router = ABTestRouter(ab_test_config or ABTestConfig())
        else:
            self.ml_classifier = None
            self.ab_router = None

    async def _execute_at_tier(
        self,
        task: JSONValue,
        task_id: str,
        tier: ModelTier,
        attempt_num: int
    ) -> ExecutionAttempt:
        """
        Execute task at specified model tier.

        MODIFICATION: Use MLClassifier for tier selection if enabled.
        """
        # NEW: ML-based tier selection (if enabled)
        if self.ml_classifier and attempt_num == 1:  # Only on first attempt
            # A/B test: Select model group
            if self.ab_router:
                ab_group = self.ab_router.select_model_group(task_id)
                # Switch model path based on A/B group
                if ab_group == "new_model":
                    self.ml_classifier.model_path = Path(
                        self.ab_router.config.new_model_path
                    ).expanduser()
                else:
                    self.ml_classifier.model_path = Path(
                        self.ab_router.config.old_model_path
                    ).expanduser()

            # Classify task with ML
            task_description = task.get("description", "")
            classification_result = self.ml_classifier.classify_task(
                task_id, task_description, task.get("metadata")
            )

            if classification_result.is_ok():
                classification = classification_result.unwrap()

                # Map tier string to ModelTier enum
                tier_mapping = {
                    "simple": ModelTier.LOCAL,
                    "moderate": ModelTier.LOCAL_PLUS,
                    "complex": ModelTier.CLOUD
                }
                tier = tier_mapping.get(classification.tier, tier)

                logger.info(
                    f"🧠 ML classification: {task_id} → {classification.tier} "
                    f"(confidence={classification.confidence:.3f}, "
                    f"method={classification.method})"
                )

        # ... rest of existing _execute_at_tier() logic unchanged
        task_type = TaskType(task.get("task_type", "general"))
        agents_needed = self._select_agents_for_task(task_type)
        # ... execute agents, run tests, return ExecutionAttempt
```

### 5.5 Prediction Logging Schema

```python
"""
Prediction log schema for VectorStore (Article IV).

Stored for every classification (ML or rule-based fallback).
"""

{
    "type": "ml_classification",
    "task_id": "task_abc123",
    "tier": "complex",
    "confidence": 0.92,
    "method": "ml_model",  # or "rule_based_fallback"
    "model_version": "2025-10-10T12:00:00Z",
    "class_probabilities": {
        "simple": 0.03,
        "moderate": 0.05,
        "complex": 0.92
    },
    "ab_group": "new_model",  # or "old_model", null if A/B disabled
    "fallback_reason": null,  # or reason string if fallback used
    "timestamp": "2025-10-10T15:23:45Z",
    "session_id": "session_leap5_phase3_1728567825"
}
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `EnsembleModel` Pydantic schema (spec-006, Phase 2 deliverable)
- **Dependency 2**: `TaskFeatureVector` Pydantic schema (spec-005, Phase 1 deliverable)
- **Dependency 3**: `FeatureExtractor` class (spec-005, Phase 1 deliverable)
- **Dependency 4**: `HybridExecutor` existing implementation (trinity_protocol/core/hybrid_executor.py)

### External Dependencies

- **External Dep 1**: scikit-learn>=1.3.0 (RandomForestClassifier, VotingClassifier)
- **External Dep 2**: joblib (model serialization, faster than pickle for sklearn)
- **External Dep 3**: numpy (feature vectorization, predict_proba input)

### Technical Constraints

- **Constraint 1**: Model load time <1s cold start (pickle deserialization, 100MB model)
- **Constraint 2**: Inference latency <50ms p99 (no regression vs Leap 4 rules)
- **Constraint 3**: Thread-safe inference (sklearn models are thread-safe for predict_proba)
- **Constraint 4**: Model versioning via training_date field (no semantic versioning yet)

### Business Constraints

- **Constraint 1**: Zero regression on existing tests (100% backward compatibility)
- **Constraint 2**: A/B split 48-52% balance (1,000 samples, deterministic hash)
- **Constraint 3**: Fallback rate <10% (90% of predictions have confidence ≥0.7)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Model load latency blocking first classification** - *Mitigation*: Lazy loading cached, warm-up endpoint optional
- **Risk 2**: **A/B split imbalance affecting metrics** - *Mitigation*: Deterministic hash validated with 1,000 samples, 48-52% balance test

### Medium Risk Items

- **Risk 3**: **Low ML confidence rate >10%** - *Mitigation*: Monitor confidence distribution, retrain if fallback rate >15%
- **Risk 4**: **HybridExecutor test regression** - *Mitigation*: 100% test pass gate, rollback if any test fails

### Low Risk Items

- **Risk 5**: **VectorStore write latency** - *Mitigation*: Async logging <5ms p99, non-blocking
- **Risk 6**: **Model file not found** - *Mitigation*: Graceful fallback to rules, error logged

### Constitutional Risks

- **Constitutional Risk 1**: **Article IV violation (predictions not logged)** - *Mitigation*: Assert VectorStore write in integration test
- **Constitutional Risk 2**: **Article I violation (incomplete features)** - *Mitigation*: Feature extraction validates 1644-dim vector

---

## Testing Strategy

### Test Categories

#### Unit Tests (20+ tests)

1. **MLClassifier Tests** (10 tests)
   - Load model from disk (success, file not found, invalid model type)
   - Classify task (high confidence ML, low confidence fallback, exception handling)
   - Vectorize features (1644-dim validation)
   - Store prediction (VectorStore write verified)

2. **ABTestRouter Tests** (5 tests)
   - Deterministic hash (same task_id → same group)
   - Split balance (1,000 samples → 48-52%)
   - Config disabled (always old model)

3. **HybridExecutor Integration Tests** (5 tests)
   - ML classification on first attempt (tier override)
   - A/B group selection (new/old model path)
   - Fallback to rules (low confidence)
   - Existing tests pass 100% (zero regression)

#### Integration Tests (10+ tests)

1. **End-to-End Inference** (3 tests)
   - Full pipeline: task → features → ML → tier (latency <50ms p99)
   - Fallback pipeline: task → features → ML (low confidence) → rules → tier (latency <100ms p99)
   - A/B test: 100 tasks → 48-52% split balance

2. **VectorStore Logging** (3 tests)
   - ML predictions logged (Article IV validation)
   - Fallback predictions logged (method="rule_based_fallback")
   - A/B group tags present (telemetry analysis)

3. **Performance Tests** (2 tests)
   - Model load time <1s cold start (measured)
   - Inference latency <50ms p99 (1,000 samples)

4. **Rollback Tests** (2 tests)
   - Set NEW_MODEL_PCT=0 → all traffic to old model
   - Model file not found → fallback to rules (no crash)

### Test Data Requirements

- **Test Data 1**: 100-task validation set with ground truth labels (accuracy measurement)
- **Test Data 2**: Trained EnsembleModel (validation accuracy 98.5%, FN_rate 1.8%)
- **Test Data 3**: 1,000 task_ids for A/B split balance validation (deterministic hash)

### Test Environment Requirements

- **Environment 1**: ~/.agency/models/ directory with trained model files
- **Environment 2**: VectorStore with write access (prediction logging)
- **Environment 3**: HybridExecutor with enable_ml_classifier=True (integration tests)

---

## Implementation Phases

### Phase 3.1: MLClassifier Core (Day 1-2)

- **Scope**: MLClassifier class, model loading, inference, fallback
- **Deliverables**:
  - `tools/ml_routing/ml_classifier.py` (ClassificationResult, MLClassifier)
  - Unit tests (10 tests, model loading, inference, fallback)
- **Success Criteria**: Inference <50ms p99, fallback rate <10%, tests 100% pass

### Phase 3.2: A/B Testing Framework (Day 2-3)

- **Scope**: ABTestConfig, ABTestRouter, deterministic hash
- **Deliverables**:
  - `tools/ml_routing/ab_test_router.py` (ABTestConfig, ABTestRouter)
  - Unit tests (5 tests, deterministic hash, split balance)
- **Success Criteria**: 1,000 samples → 48-52% split, same task_id → same group

### Phase 3.3: HybridExecutor Integration (Day 3-4)

- **Scope**: HybridExecutor._execute_at_tier() modifications, backward compatibility
- **Deliverables**:
  - Updated `trinity_protocol/core/hybrid_executor.py`
  - Integration tests (5 tests, ML tier override, existing tests pass)
- **Success Criteria**: 100% test pass rate (zero regression), ML classification functional

### Phase 3.4: Prediction Logging (Day 4-5)

- **Scope**: VectorStore integration, async logging, query API
- **Deliverables**:
  - MLClassifier._store_prediction() implementation
  - Integration tests (3 tests, ML/fallback logging, A/B tags)
- **Success Criteria**: 100% predictions logged (Article IV), async write <5ms p99

### Phase 3.5: Production Validation (Day 5-6)

- **Scope**: End-to-end testing, A/B test with 100 tasks, metrics collection
- **Deliverables**:
  - Performance benchmarks (latency p50/p95/p99)
  - A/B test report (accuracy, split balance, confidence distribution)
  - Documentation: Phase 3 execution summary
- **Success Criteria**: Accuracy ≥98%, latency <50ms p99, split 48-52%

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: HybridExecutor, MLClassifier, LearningAgent
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), MLEngineer (inference validation)

### Review Criteria

- **Completeness**: All ML inference components specified (MLClassifier, A/B router, logging)
- **Clarity**: Architecture diagrams, code examples, integration points documented
- **Feasibility**: <50ms p99 latency achievable with sklearn, <1s cold start validated
- **Constitutional Compliance**: Article I-V validated (especially Article IV logging)
- **Quality Standards**: Accuracy ≥98%, latency <50ms p99, 100% test pass rate

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **ML Inference Approval**: Pending latency validation (Phase 3.5)
- [ ] **Final Approval**: Pending after Phase 3.3 implementation (HybridExecutor integration)

---

## Appendices

### Appendix A: Glossary

- **MLClassifier**: Component that loads EnsembleModel and performs inference
- **A/B Testing**: Gradual rollout strategy (50% traffic to new model, 50% to old)
- **Deterministic Hash**: MD5(task_id) % 100 for reproducible traffic splitting
- **Fallback**: Graceful degradation to Leap 4 rules when ML confidence <0.7
- **Prediction Logging**: VectorStore storage of all classifications (Article IV)

### Appendix B: References

- **Spec-005**: Advanced Pattern Recognition (Leap 5 Phase 1-2 foundation)
- **Spec-006**: EnsembleModel Pydantic (Phase 2 deliverable)
- **Spec-004**: Quality Feedback Loop (Leap 4 fallback system)
- **ADR-004**: Continuous Learning (VectorStore mandate)
- **ADR-024**: Adaptive Model Router (cost optimization)

### Appendix C: Related Documents

- **Spec**: `specs/spec-005-advanced-pattern-recognition.md` (Leap 5 overview)
- **Plan**: `plans/plan-007-phase3-ml-inference.md` (to be created after spec approval)
- **Tests**: `tests/test_ml_classifier.py`, `tests/test_ab_test_router.py`, `tests/test_hybrid_executor_ml.py`

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification: MLClassifier, A/B testing, HybridExecutor integration, prediction logging |

---

*"From training to inference, from models to production."*
