# Implementation Plan: Leap 5 Phase 3 - ML Inference Integration

**Plan ID**: `plan-005-phase3-ml-inference`
**Status**: `Draft`
**Related Spec**: `specs/spec-005-phase3-ml-inference.md` (parallel creation)
**Related Plan**: `plans/plan-005-advanced-pattern-recognition.md` (parent plan)
**Author**: PlannerAgent
**Created**: 2025-10-10
**Estimated Duration**: 3 days (24 hours total effort)
**Estimated Cost**: $0.93 (gpt-5 planning + implementation)

---

## Executive Summary

Phase 3 integrates ML-powered task classification into HybridExecutor with rule-based fallback, enabling production inference with <50ms latency and graceful degradation. This phase bridges the gap between trained models (Phase 2) and continuous learning (Phase 4), delivering the core inference pipeline with constitutional compliance (Articles I-V).

**Key Innovation**: Hybrid classification architecture combining ML predictions (primary) with rule-based fallback (Leap 4), ensuring zero degradation even during ML failures.

---

## Prerequisites (Phase 2 Complete)

### Required Deliverables from Phase 2
- ✅ `EnsembleModel` trained (RandomForest + GradientBoosting, >98% accuracy)
- ✅ `~/.agency/models/routing_classifier_v1.0.pkl` serialized model
- ✅ `ModelStorage` class (save/load functionality)
- ✅ Validation accuracy >98%, false negative rate <2%

### Dependencies Validation
```python
# Pre-flight check before Phase 3
def validate_phase2_complete():
    """Ensure Phase 2 deliverables exist before starting Phase 3."""
    checks = [
        ("Model file exists", Path("~/.agency/models/routing_classifier_v1.0.pkl").exists()),
        ("Model metadata exists", Path("~/.agency/models/routing_classifier_v1.0.json").exists()),
        ("ModelStorage tests pass", run_tests("tests/test_model_storage.py")),
        ("ModelTrainer tests pass", run_tests("tests/test_model_trainer.py")),
    ]

    for check_name, result in checks:
        if not result:
            raise Exception(f"Phase 2 incomplete: {check_name} failed")

    logger.info("✅ Phase 2 validation complete, ready for Phase 3")
```

---

## Implementation Schedule

### Phase 3.1: Foundation Models (Day 1)
**Duration**: 8 hours (parallel implementation)
**Critical Path**: Yes (blocks Phase 3.2)

**Deliverables**:
1. `MLClassifier` Pydantic model (~200 lines)
2. `PredictionLog` Pydantic model (~100 lines)
3. `ABTestConfig` Pydantic model (~150 lines)

**Parallel Tasks** (3 engineers):
- Task 1.1: MLClassifier model (Engineer A)
- Task 1.2: PredictionLog model (Engineer B)
- Task 1.3: ABTestConfig model (Engineer C)

### Phase 3.2: Inference Engine (Day 2)
**Duration**: 10 hours (sequential implementation)
**Critical Path**: Yes (blocks Phase 3.3)

**Deliverables**:
1. `MLClassifier` class with classify_task() (~400 lines)
2. Prediction logging to VectorStore (~100 lines)
3. Integration tests (~200 lines)

### Phase 3.3: HybridExecutor Integration (Day 2-3)
**Duration**: 6 hours (sequential implementation)
**Critical Path**: Yes (blocks validation)

**Deliverables**:
1. HybridExecutor ML-first routing (~150 lines modifications)
2. A/B testing integration (~50 lines)
3. End-to-end tests (~150 lines)

---

## Phase 3.1: Foundation Models (Day 1, 8 hours)

### Objectives

1. Create Pydantic models for ML inference pipeline
2. Enable type-safe data flow (Article II compliance)
3. Support A/B testing infrastructure
4. Achieve zero technical debt in model definitions

### Task 1.1: MLClassifier Pydantic Model

**File**: `shared/models/ml_classifier.py`
**Lines**: ~200
**Dependencies**: None (foundation)
**Estimated Time**: 3 hours
**Owner**: Engineer A

#### Implementation Checklist

- [ ] **Create `ClassificationResult` Pydantic model**
  ```python
  class ClassificationResult(BaseModel):
      """
      Result from ML classification with confidence scoring.

      Constitutional Compliance:
      - Article II: Strict typing (no Dict[Any, Any])
      - Article IV: All fields logged to VectorStore
      """

      task_id: str = Field(..., min_length=1, description="Task identifier")
      tier: Literal["simple", "moderate", "complex"] = Field(
          ..., description="Predicted complexity tier"
      )
      confidence: float = Field(
          ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
      )
      method: Literal["ml_model", "rule_based_fallback"] = Field(
          ..., description="Classification method used"
      )
      model_version: str = Field(
          ..., description="Model training date (ISO format)"
      )
      features: Optional["TaskFeatureVector"] = Field(
          None, description="Feature vector for SHAP explainability"
      )
      class_probabilities: Optional[dict[str, float]] = Field(
          None,
          description="Probabilities per tier (simple/moderate/complex)"
      )
      timestamp: datetime = Field(
          default_factory=lambda: datetime.now(UTC),
          description="Classification timestamp"
      )

      class Config:
          json_schema_extra = {
              "example": {
                  "task_id": "task_12345",
                  "tier": "complex",
                  "confidence": 0.92,
                  "method": "ml_model",
                  "model_version": "2025-10-10T12:00:00Z",
                  "class_probabilities": {
                      "simple": 0.03,
                      "moderate": 0.05,
                      "complex": 0.92
                  },
                  "timestamp": "2025-10-10T14:30:00Z"
              }
          }
  ```

- [ ] **Create `MLClassifierConfig` Pydantic model**
  ```python
  class MLClassifierConfig(BaseModel):
      """
      Configuration for ML classifier with environment overrides.

      Constitutional Compliance:
      - Article III: No manual overrides (only env vars)
      """

      model_path: Path = Field(
          default=Path.home() / ".agency" / "models" / "routing_classifier_latest.pkl",
          description="Path to serialized model"
      )
      confidence_threshold: float = Field(
          default=0.7,
          ge=0.0,
          le=1.0,
          description="Minimum confidence for ML prediction (fallback if lower)"
      )
      use_ml_routing: bool = Field(
          default=True,
          description="Enable ML routing (disable for A/B testing)"
      )
      max_cache_size: int = Field(
          default=1000,
          ge=0,
          description="Max embeddings cached (LRU eviction)"
      )

      @classmethod
      def from_env(cls) -> "MLClassifierConfig":
          """Load config from environment variables."""
          return cls(
              confidence_threshold=float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.7")),
              use_ml_routing=os.getenv("USE_ML_ROUTING", "true").lower() == "true",
              max_cache_size=int(os.getenv("ML_CACHE_SIZE", "1000"))
          )
  ```

#### Acceptance Criteria

- **AC-1.1**: `ClassificationResult` model with all required fields (task_id, tier, confidence, method)
- **AC-1.2**: Strict typing (no `Any`, Literal types for enums)
- **AC-1.3**: JSON serialization support (`model_dump_json()`)
- **AC-1.4**: Config loading from environment variables

#### Test Coverage

**File**: `tests/test_ml_classifier_models.py`
**Lines**: ~150
**Tests**: 10+

```python
def test_classification_result_valid():
    """Happy path: Create ClassificationResult with all fields."""
    result = ClassificationResult(
        task_id="task_123",
        tier="complex",
        confidence=0.92,
        method="ml_model",
        model_version="2025-10-10T12:00:00Z",
        class_probabilities={"simple": 0.03, "moderate": 0.05, "complex": 0.92}
    )
    assert result.tier == "complex"
    assert result.confidence == 0.92
    assert result.method == "ml_model"

def test_classification_result_validation():
    """Validation: Confidence out of range (0.0-1.0)."""
    with pytest.raises(ValidationError):
        ClassificationResult(
            task_id="task_123",
            tier="complex",
            confidence=1.5,  # Invalid: >1.0
            method="ml_model",
            model_version="2025-10-10T12:00:00Z"
        )

def test_ml_classifier_config_from_env(monkeypatch):
    """Config loading from environment variables."""
    monkeypatch.setenv("ML_CONFIDENCE_THRESHOLD", "0.8")
    monkeypatch.setenv("USE_ML_ROUTING", "false")

    config = MLClassifierConfig.from_env()
    assert config.confidence_threshold == 0.8
    assert config.use_ml_routing is False
```

---

### Task 1.2: PredictionLog Pydantic Model

**File**: `shared/models/prediction_log.py`
**Lines**: ~100
**Dependencies**: Task 1.1 (ClassificationResult)
**Estimated Time**: 2 hours
**Owner**: Engineer B

#### Implementation Checklist

- [ ] **Create `PredictionLog` Pydantic model**
  ```python
  class PredictionLog(BaseModel):
      """
      Log entry for ML predictions (stored in VectorStore).

      Constitutional Compliance:
      - Article IV: MANDATORY VectorStore logging
      - Used for future retraining and accuracy monitoring
      """

      task_id: str = Field(..., min_length=1)
      predicted_tier: Literal["simple", "moderate", "complex"]
      actual_tier: Optional[Literal["simple", "moderate", "complex"]] = Field(
          None, description="Actual tier from quality feedback (post-execution)"
      )
      confidence: float = Field(..., ge=0.0, le=1.0)
      method: Literal["ml_model", "rule_based_fallback"]
      model_version: str
      features: Optional[dict[str, Any]] = Field(
          None, description="Feature vector snapshot (for retraining)"
      )
      timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

      def is_correct(self) -> bool:
          """Check if prediction matches actual tier (post-execution)."""
          if self.actual_tier is None:
              return None  # Not yet validated
          return self.predicted_tier == self.actual_tier

      def to_vectorstore_dict(self) -> dict[str, Any]:
          """Convert to dict for VectorStore storage."""
          return {
              "task_id": self.task_id,
              "predicted_tier": self.predicted_tier,
              "actual_tier": self.actual_tier,
              "confidence": self.confidence,
              "method": self.method,
              "model_version": self.model_version,
              "timestamp": self.timestamp.isoformat(),
              "is_correct": self.is_correct()
          }
  ```

#### Acceptance Criteria

- **AC-1.2**: `PredictionLog` model with predicted/actual tier comparison
- **AC-1.2**: `is_correct()` method for accuracy calculation
- **AC-1.2**: `to_vectorstore_dict()` for Article IV compliance

#### Test Coverage

**File**: `tests/test_prediction_log.py`
**Lines**: ~80

```python
def test_prediction_log_correct():
    """Correct prediction: predicted matches actual."""
    log = PredictionLog(
        task_id="task_123",
        predicted_tier="complex",
        actual_tier="complex",
        confidence=0.92,
        method="ml_model",
        model_version="v1.0"
    )
    assert log.is_correct() is True

def test_prediction_log_incorrect():
    """Incorrect prediction: predicted != actual."""
    log = PredictionLog(
        task_id="task_123",
        predicted_tier="simple",
        actual_tier="complex",  # Misclassified
        confidence=0.65,
        method="ml_model",
        model_version="v1.0"
    )
    assert log.is_correct() is False

def test_prediction_log_vectorstore_dict():
    """VectorStore serialization."""
    log = PredictionLog(
        task_id="task_123",
        predicted_tier="moderate",
        confidence=0.85,
        method="ml_model",
        model_version="v1.0"
    )
    d = log.to_vectorstore_dict()
    assert d["task_id"] == "task_123"
    assert d["predicted_tier"] == "moderate"
    assert "timestamp" in d
```

---

### Task 1.3: ABTestConfig Pydantic Model

**File**: `shared/models/ab_test_config.py`
**Lines**: ~150
**Dependencies**: None
**Estimated Time**: 3 hours
**Owner**: Engineer C

#### Implementation Checklist

- [ ] **Create `ABTestConfig` Pydantic model**
  ```python
  class ABTestConfig(BaseModel):
      """
      A/B testing configuration for gradual ML rollout.

      Constitutional Compliance:
      - Article III: Automated traffic splitting (no manual overrides)
      """

      enabled: bool = Field(
          default=False,
          description="Enable A/B testing (default: ML routing 100%)"
      )
      ml_percentage: int = Field(
          default=10,
          ge=0,
          le=100,
          description="Percentage of traffic to ML model (0-100)"
      )
      seed: int = Field(
          default=42,
          description="Random seed for deterministic task splitting"
      )

      def should_use_ml(self, task_id: str) -> bool:
          """
          Deterministically route task to ML or rule-based classifier.

          Args:
              task_id: Task identifier (used for consistent hashing)

          Returns:
              True if task routed to ML, False if routed to rules

          Algorithm:
              hash(task_id + seed) % 100 < ml_percentage

          Example:
              >>> config = ABTestConfig(enabled=True, ml_percentage=10)
              >>> config.should_use_ml("task_123")  # Deterministic
              True  # This task always routes to ML (10% traffic)
          """
          if not self.enabled:
              return True  # ML routing 100% (A/B test disabled)

          # Deterministic hash: same task_id always routes to same group
          task_hash = hash(f"{task_id}_{self.seed}")
          return (task_hash % 100) < self.ml_percentage

      @classmethod
      def from_env(cls) -> "ABTestConfig":
          """Load A/B test config from environment variables."""
          return cls(
              enabled=os.getenv("ML_AB_TEST_ENABLED", "false").lower() == "true",
              ml_percentage=int(os.getenv("ML_AB_TEST_PERCENTAGE", "10"))
          )
  ```

#### Acceptance Criteria

- **AC-1.3**: `ABTestConfig` with ml_percentage validation (0-100)
- **AC-1.3**: `should_use_ml()` deterministic routing (same task_id → same group)
- **AC-1.3**: Environment loading (`ML_AB_TEST_ENABLED`, `ML_AB_TEST_PERCENTAGE`)

#### Test Coverage

**File**: `tests/test_ab_test_config.py`
**Lines**: ~120

```python
def test_ab_test_disabled():
    """A/B test disabled: All tasks route to ML."""
    config = ABTestConfig(enabled=False, ml_percentage=10)
    assert config.should_use_ml("task_123") is True
    assert config.should_use_ml("task_456") is True

def test_ab_test_10_percent():
    """A/B test enabled: 10% traffic to ML."""
    config = ABTestConfig(enabled=True, ml_percentage=10, seed=42)

    # Test 100 task IDs
    ml_count = sum(config.should_use_ml(f"task_{i}") for i in range(100))

    # Expect ~10% (allow ±5% variance due to hash distribution)
    assert 5 <= ml_count <= 15

def test_ab_test_deterministic():
    """Same task_id always routes to same group."""
    config = ABTestConfig(enabled=True, ml_percentage=10, seed=42)

    # Call should_use_ml() 10 times with same task_id
    results = [config.should_use_ml("task_stable") for _ in range(10)]

    # All results should be identical (deterministic)
    assert len(set(results)) == 1

def test_ab_test_from_env(monkeypatch):
    """Load A/B config from environment."""
    monkeypatch.setenv("ML_AB_TEST_ENABLED", "true")
    monkeypatch.setenv("ML_AB_TEST_PERCENTAGE", "25")

    config = ABTestConfig.from_env()
    assert config.enabled is True
    assert config.ml_percentage == 25
```

---

### Phase 3.1 Deliverables

**Files Created** (3 files):
1. `shared/models/ml_classifier.py` (~200 lines)
2. `shared/models/prediction_log.py` (~100 lines)
3. `shared/models/ab_test_config.py` (~150 lines)

**Tests Created** (3 files):
1. `tests/test_ml_classifier_models.py` (10+ tests)
2. `tests/test_prediction_log.py` (8+ tests)
3. `tests/test_ab_test_config.py` (10+ tests)

**Phase 3.1 Success Criteria**:
- ✅ 28+ tests passing (100% pass rate)
- ✅ All models strict-typed (no `Any` types)
- ✅ JSON serialization working (model_dump_json())
- ✅ Environment loading functional (from_env())
- ✅ A/B testing deterministic (same task_id → same group)

**Phase 3.1 Checkpoint**: Human review before Phase 3.2
- Review model schemas (validate field types, constraints)
- Test A/B routing logic (10% traffic split correct?)
- Confirm env var loading works (integration with existing config)

---

## Phase 3.2: Inference Engine (Day 2, 10 hours)

### Objectives

1. Implement MLClassifier with classify_task() method
2. Integrate feature extraction and model loading
3. Implement confidence thresholding (fallback to Leap 4)
4. Log all predictions to VectorStore (Article IV)
5. Achieve <50ms p99 classification latency

### Task 2.1: MLClassifier Implementation

**File**: `tools/ml_routing/ml_classifier.py`
**Lines**: ~400
**Dependencies**: Phase 2 (EnsembleModel), Phase 3.1 (models)
**Estimated Time**: 8 hours
**Owner**: Engineer A

#### Implementation Checklist

- [ ] **Import dependencies**
  ```python
  from datetime import datetime
  from datetime import timezone as tz_utc
  from pathlib import Path
  from typing import Any

  from shared.agent_context import AgentContext
  from shared.models.ml_classifier import ClassificationResult, MLClassifierConfig
  from shared.models.prediction_log import PredictionLog
  from shared.type_definitions.result import Result, Ok, Err
  from tools.ml_routing.feature_extractor import FeatureExtractor, TaskFeatureVector
  from tools.ml_routing.model_storage import ModelStorage, EnsembleModel
  from tools.quality_feedback.rule_based_classifier import RuleBasedClassifier  # Leap 4
  ```

- [ ] **Create MLClassifier class with lazy initialization**
  ```python
  class MLClassifier:
      """
      ML-powered task classifier with rule-based fallback.

      Hybrid Architecture:
      - Primary: ML model prediction with confidence scoring
      - Fallback: Leap 4 rule-based classification (if confidence <0.7)

      Constitutional Compliance:
      - Article I: Retry on feature extraction timeout
      - Article II: Result pattern for error handling
      - Article IV: Store all predictions in VectorStore (MANDATORY)
      """

      def __init__(
          self,
          context: AgentContext,
          config: MLClassifierConfig | None = None
      ):
          self.context = context
          self.config = config or MLClassifierConfig.from_env()

          # Lazy initialization (loaded on first classification)
          self._model: EnsembleModel | None = None
          self._feature_extractor: FeatureExtractor | None = None
          self._rule_classifier: RuleBasedClassifier | None = None
          self._model_storage: ModelStorage | None = None

          logger.info(
              f"MLClassifier initialized (confidence_threshold={self.config.confidence_threshold}, "
              f"use_ml_routing={self.config.use_ml_routing})"
          )
  ```

- [ ] **Implement classify_task() with Result pattern**
  ```python
  def classify_task(
      self,
      task_id: str,
      task_description: str,
      task_metadata: dict[str, Any] | None = None
  ) -> Result[ClassificationResult, str]:
      """
      Classify task complexity using ML model + rule fallback.

      Args:
          task_id: Task identifier
          task_description: Task description text
          task_metadata: Optional metadata (estimated_time, etc.)

      Returns:
          Result with ClassificationResult (tier, confidence, method)

      Workflow:
          1. Extract features (embedding + TF-IDF + metadata)
          2. ML model prediction with confidence scoring
          3. If confidence ≥0.7: return ML prediction
          4. Else: fallback to Leap 4 rule-based classification
          5. Store prediction in VectorStore (Article IV)

      Performance:
          - ML path: <50ms p99 (25ms embedding + 10ms inference + 15ms overhead)
          - Fallback path: <100ms p99 (Leap 4 rule evaluation)
      """
      try:
          # Check if ML routing disabled (A/B testing)
          if not self.config.use_ml_routing:
              logger.debug(f"ML routing disabled (USE_ML_ROUTING=false), using rules for {task_id}")
              return self._fallback_to_rules(task_id, task_description)

          # Step 1: Extract features
          features_result = self._get_feature_extractor().extract_features(
              task_description, task_metadata
          )

          if features_result.is_err():
              # Feature extraction failed, fallback to rules
              logger.warning(
                  f"Feature extraction failed for {task_id}: {features_result.unwrap_err()}, "
                  f"falling back to Leap 4 rules"
              )
              return self._fallback_to_rules(task_id, task_description)

          features = features_result.unwrap()
          feature_vector = self._vectorize_features(features)

          # Step 2: Load model (lazy)
          model_result = self._get_model()
          if model_result.is_err():
              logger.warning(
                  f"Model loading failed: {model_result.unwrap_err()}, "
                  f"falling back to Leap 4 rules"
              )
              return self._fallback_to_rules(task_id, task_description)

          model = model_result.unwrap()

          # Step 3: ML prediction with confidence
          proba = model.ensemble.predict_proba([feature_vector])[0]
          # Returns [P(simple), P(moderate), P(complex)]

          predicted_tier_idx = int(proba.argmax())
          confidence = float(proba[predicted_tier_idx])

          tier_names = ["simple", "moderate", "complex"]
          predicted_tier = tier_names[predicted_tier_idx]

          # Step 4: Confidence threshold check
          if confidence >= self.config.confidence_threshold:
              # High confidence ML prediction
              result = ClassificationResult(
                  task_id=task_id,
                  tier=predicted_tier,
                  confidence=confidence,
                  method="ml_model",
                  model_version=model.training_date,
                  features=features,
                  class_probabilities={
                      "simple": float(proba[0]),
                      "moderate": float(proba[1]),
                      "complex": float(proba[2])
                  }
              )

              # Store prediction (Article IV)
              self._store_prediction(result)

              logger.info(
                  f"ML classification: {task_id} → {predicted_tier} "
                  f"(confidence={confidence:.3f})"
              )

              return Ok(result)

          else:
              # Low confidence, fallback to Leap 4 rules
              logger.info(
                  f"ML confidence {confidence:.3f} < {self.config.confidence_threshold}, "
                  f"falling back to rules for {task_id}"
              )
              return self._fallback_to_rules(task_id, task_description)

      except Exception as e:
          logger.error(f"ML classification failed for {task_id}: {e}", exc_info=True)
          return self._fallback_to_rules(task_id, task_description)
  ```

- [ ] **Implement fallback to Leap 4 rules**
  ```python
  def _fallback_to_rules(
      self,
      task_id: str,
      task_description: str
  ) -> Result[ClassificationResult, str]:
      """Fallback to Leap 4 rule-based classification."""
      rule_classifier = self._get_rule_classifier()
      rule_result = rule_classifier.classify(task_description)

      if rule_result.is_ok():
          classification = rule_result.unwrap()

          result = ClassificationResult(
              task_id=task_id,
              tier=classification.tier,
              confidence=classification.confidence,
              method="rule_based_fallback",
              model_version="leap4",
              features=None,
              class_probabilities=None
          )

          # Store fallback prediction (Article IV)
          self._store_prediction(result)

          logger.info(
              f"Rule-based classification: {task_id} → {classification.tier} "
              f"(confidence={classification.confidence:.3f})"
          )

          return Ok(result)
      else:
          return rule_result
  ```

- [ ] **Implement VectorStore storage (Article IV MANDATORY)**
  ```python
  def _store_prediction(self, result: ClassificationResult) -> None:
      """
      Store prediction in VectorStore (Article IV).

      Constitutional Compliance:
      - Article IV: MANDATORY VectorStore logging for all predictions
      - Used for: Retraining, accuracy monitoring, pattern analysis
      """
      prediction_log = PredictionLog(
          task_id=result.task_id,
          predicted_tier=result.tier,
          actual_tier=None,  # Updated post-execution by quality feedback loop
          confidence=result.confidence,
          method=result.method,
          model_version=result.model_version,
          features=result.features.model_dump() if result.features else None
      )

      self.context.store_memory(
          key=f"ml_classification_{result.task_id}",
          content=prediction_log.to_vectorstore_dict(),
          tags=["ml_classification", "leap5", result.tier, result.method]
      )

      logger.debug(f"Stored prediction for {result.task_id} in VectorStore (Article IV)")
  ```

- [ ] **Implement lazy loading helpers**
  ```python
  def _get_model(self) -> Result[EnsembleModel, str]:
      """Lazy load model (cache in memory after first load)."""
      if self._model is None:
          if self._model_storage is None:
              self._model_storage = ModelStorage()

          model_result = self._model_storage.load_model(self.config.model_path)
          if model_result.is_err():
              return model_result

          self._model = model_result.unwrap()
          logger.info(f"Loaded model: {self._model.training_date}")

      return Ok(self._model)

  def _get_feature_extractor(self) -> FeatureExtractor:
      """Lazy initialize feature extractor."""
      if self._feature_extractor is None:
          self._feature_extractor = FeatureExtractor(
              openai_api_key=os.getenv("OPENAI_API_KEY"),
              tfidf_vocabulary=self._load_tfidf_vocabulary(),
              max_cache_size=self.config.max_cache_size
          )
      return self._feature_extractor

  def _get_rule_classifier(self) -> RuleBasedClassifier:
      """Lazy initialize rule-based classifier (Leap 4 fallback)."""
      if self._rule_classifier is None:
          self._rule_classifier = RuleBasedClassifier()
      return self._rule_classifier

  def _vectorize_features(self, features: TaskFeatureVector) -> list[float]:
      """Flatten TaskFeatureVector to 1644-dim array for model input."""
      return (
          features.embedding +
          features.tfidf_features +
          [
              float(features.description_length),
              float(features.word_count),
              float(features.has_refactor_keyword),
              float(features.has_test_keyword),
              float(features.has_async_keyword),
              float(features.has_fix_keyword),
              float(features.estimated_time_seconds),
              float(features.historical_tier_mode)
          ]
      )
  ```

#### Acceptance Criteria

- **AC-2.1**: ML prediction with rule-based fallback (confidence <0.7)
- **AC-2.2**: Feature extraction cached per task (no duplicate embeddings)
- **AC-2.3**: Model loaded once (lazy init, cached in memory)
- **AC-2.4**: Confidence threshold tunable via `ML_CONFIDENCE_THRESHOLD` env var
- **AC-2.5**: Graceful degradation (ML failure → Leap 4 rules)
- **AC-CIV.1**: All predictions stored in VectorStore (Article IV)

#### Test Coverage

**File**: `tests/test_ml_classifier.py`
**Lines**: ~300
**Tests**: 15+

```python
def test_ml_classify_high_confidence(mock_context, mock_model):
    """Happy path: ML classification with high confidence (>0.7)."""
    classifier = MLClassifier(context=mock_context)
    classifier._model = mock_model  # Inject mock

    result = classifier.classify_task(
        task_id="task_123",
        task_description="Implement async webhook handler with retry logic"
    )

    assert result.is_ok()
    classification = result.unwrap()
    assert classification.tier == "complex"
    assert classification.confidence >= 0.7
    assert classification.method == "ml_model"

def test_ml_classify_low_confidence_fallback(mock_context, mock_model_low_confidence):
    """Low confidence (<0.7): Fallback to Leap 4 rules."""
    classifier = MLClassifier(context=mock_context)
    classifier._model = mock_model_low_confidence  # Confidence=0.6

    result = classifier.classify_task(
        task_id="task_456",
        task_description="Fix typo in README"
    )

    assert result.is_ok()
    classification = result.unwrap()
    assert classification.method == "rule_based_fallback"
    assert classification.model_version == "leap4"

def test_ml_classify_feature_extraction_failure(mock_context, mock_feature_extractor_fail):
    """Feature extraction fails: Fallback to Leap 4 rules."""
    classifier = MLClassifier(context=mock_context)
    classifier._feature_extractor = mock_feature_extractor_fail

    result = classifier.classify_task(
        task_id="task_789",
        task_description="Implement feature"
    )

    assert result.is_ok()
    classification = result.unwrap()
    assert classification.method == "rule_based_fallback"

def test_ml_classify_vectorstore_storage(mock_context, mock_model):
    """Article IV: Prediction stored in VectorStore."""
    classifier = MLClassifier(context=mock_context)
    classifier._model = mock_model

    result = classifier.classify_task(
        task_id="task_abc",
        task_description="Complex task"
    )

    # Verify VectorStore storage
    assert mock_context.store_memory.called
    call_args = mock_context.store_memory.call_args
    assert call_args[1]["key"] == "ml_classification_task_abc"
    assert "ml_classification" in call_args[1]["tags"]

def test_ml_classify_lazy_loading(mock_context):
    """Model lazy loaded on first classification."""
    classifier = MLClassifier(context=mock_context)
    assert classifier._model is None  # Not loaded yet

    classifier.classify_task("task_123", "description")

    assert classifier._model is not None  # Loaded after first call

def test_ml_classify_performance(mock_context, mock_model):
    """Performance: Classification latency <50ms p99."""
    classifier = MLClassifier(context=mock_context)
    classifier._model = mock_model

    import time
    latencies = []

    for i in range(100):
        start = time.time()
        classifier.classify_task(f"task_{i}", "description")
        latency = (time.time() - start) * 1000  # ms
        latencies.append(latency)

    p99 = sorted(latencies)[98]  # 99th percentile
    assert p99 < 50, f"p99 latency {p99:.1f}ms exceeds 50ms target"
```

---

### Phase 3.2 Deliverables

**Files Created** (1 file):
1. `tools/ml_routing/ml_classifier.py` (~400 lines)

**Tests Created** (1 file):
1. `tests/test_ml_classifier.py` (15+ tests)

**Phase 3.2 Success Criteria**:
- ✅ 15+ tests passing (100% pass rate)
- ✅ Classification latency <50ms p99 (measured with 100 tasks)
- ✅ Graceful degradation (ML failure → Leap 4 rules)
- ✅ All predictions stored in VectorStore (Article IV)
- ✅ Confidence thresholding working (fallback <0.7)

**Phase 3.2 Checkpoint**: Human review before Phase 3.3
- Test end-to-end classification (task → features → ML → result)
- Verify fallback scenarios (low confidence, ML unavailable)
- Measure latency p99 (<50ms target)
- Confirm VectorStore logging (Article IV compliance)

---

## Phase 3.3: HybridExecutor Integration (Day 2-3, 6 hours)

### Objectives

1. Integrate MLClassifier into HybridExecutor
2. Implement ML-first routing (Priority 1)
3. Add A/B testing support (10% traffic to ML)
4. Validate zero regression (existing tests still pass)
5. End-to-end production workflow functional

### Task 3.1: HybridExecutor ML Integration

**File**: `trinity_protocol/core/hybrid_executor.py`
**Lines**: ~150 (modifications)
**Dependencies**: Phase 3.2 (MLClassifier)
**Estimated Time**: 4 hours
**Owner**: Engineer A

#### Implementation Checklist

- [ ] **Import MLClassifier and models**
  ```python
  from tools.ml_routing.ml_classifier import MLClassifier
  from shared.models.ml_classifier import MLClassifierConfig
  from shared.models.ab_test_config import ABTestConfig
  ```

- [ ] **Add ML classifier to HybridExecutor initialization**
  ```python
  class HybridExecutor:
      def __init__(
          self,
          message_bus: MessageBus,
          cost_tracker: CostTracker,
          agent_context: AgentContext,
          # ... existing params
          enable_ml_routing: bool = True,  # NEW: ML routing flag
      ):
          # ... existing initialization

          # Initialize ML classifier (lazy loading)
          self.ml_classifier: MLClassifier | None = None
          self.ml_config = MLClassifierConfig.from_env()
          self.ab_config = ABTestConfig.from_env()

          if enable_ml_routing and self.ml_config.use_ml_routing:
              self.ml_classifier = MLClassifier(
                  context=agent_context,
                  config=self.ml_config
              )
              logger.info("ML classifier enabled (Leap 5 Phase 3)")
          else:
              logger.info("ML classifier disabled (using Leap 4 rules)")
  ```

- [ ] **Modify task routing to use ML-first strategy**
  ```python
  def _classify_task_complexity(
      self,
      task_id: str,
      task_description: str,
      task_metadata: dict[str, Any] | None = None
  ) -> tuple[str, str]:
      """
      Classify task complexity with ML-first routing.

      Args:
          task_id: Task identifier
          task_description: Task description text
          task_metadata: Optional metadata

      Returns:
          (tier, method) tuple:
              - tier: "simple" | "moderate" | "complex"
              - method: "ml_model" | "rule_based_fallback"

      Routing Priority:
          1. ML classifier (if enabled and A/B test passes)
          2. Rule-based classifier (Leap 4 fallback)
      """

      # Priority 1: ML classifier
      if self.ml_classifier is not None:
          # A/B testing check (deterministic task splitting)
          if self.ab_config.should_use_ml(task_id):
              ml_result = self.ml_classifier.classify_task(
                  task_id=task_id,
                  task_description=task_description,
                  task_metadata=task_metadata
              )

              if ml_result.is_ok():
                  classification = ml_result.unwrap()
                  logger.info(
                      f"ML routing: {task_id} → {classification.tier} "
                      f"(confidence={classification.confidence:.3f}, "
                      f"method={classification.method})"
                  )
                  return classification.tier, classification.method
              else:
                  logger.warning(
                      f"ML classification failed: {ml_result.unwrap_err()}, "
                      f"falling back to Leap 4 rules"
                  )

      # Priority 2: Rule-based classifier (Leap 4 fallback)
      rule_result = self.rule_classifier.classify(task_description)

      if rule_result.is_ok():
          classification = rule_result.unwrap()
          logger.info(
              f"Rule-based routing: {task_id} → {classification.tier} "
              f"(confidence={classification.confidence:.3f})"
          )
          return classification.tier, "rule_based_fallback"
      else:
          # Default to moderate if all classification methods fail
          logger.error(
              f"All classification methods failed for {task_id}, "
              f"defaulting to 'moderate' tier"
          )
          return "moderate", "default_fallback"
  ```

- [ ] **Update execute_task() to use new classification**
  ```python
  async def _execute_task_with_escalation(
      self,
      task: JSONValue,
      task_id: str
  ) -> TaskResult:
      """Execute task with ML-powered complexity classification."""

      # NEW: ML-powered classification
      task_description = task.get("description", "")
      task_metadata = {
          "estimated_time_seconds": task.get("estimated_time_seconds"),
          "complexity_hint": task.get("complexity")  # User-provided hint (optional)
      }

      tier, method = self._classify_task_complexity(
          task_id=task_id,
          task_description=task_description,
          task_metadata=task_metadata
      )

      # Map tier to ModelTier enum
      tier_mapping = {
          "simple": ModelTier.LOCAL,
          "moderate": ModelTier.LOCAL_PLUS,
          "complex": ModelTier.CLOUD
      }
      current_tier = tier_mapping.get(tier, ModelTier.LOCAL_PLUS)

      logger.info(
          f"Task {task_id} classified as {tier} (method={method}), "
          f"routing to {current_tier.value} tier"
      )

      # ... rest of existing escalation logic
  ```

#### Acceptance Criteria

- **AC-3.1**: HybridExecutor uses ML-first routing (Priority 1)
- **AC-3.2**: Fallback to Leap 4 rules if ML unavailable (Priority 2)
- **AC-3.3**: `USE_ML_ROUTING=false` disables ML routing (A/B testing)
- **AC-3.4**: A/B testing support (10% traffic to ML via `ML_AB_TEST_ENABLED`)
- **AC-3.5**: Routing decision logged (tier, method, confidence)

#### Test Coverage

**File**: `tests/test_hybrid_executor_ml_integration.py`
**Lines**: ~250
**Tests**: 12+

```python
def test_hybrid_executor_ml_routing(mock_context, mock_ml_classifier):
    """Happy path: ML routing enabled, task classified via ML."""
    executor = HybridExecutor(
        message_bus=mock_bus,
        cost_tracker=mock_cost_tracker,
        agent_context=mock_context,
        enable_ml_routing=True
    )
    executor.ml_classifier = mock_ml_classifier

    tier, method = executor._classify_task_complexity(
        task_id="task_123",
        task_description="Implement async webhook handler"
    )

    assert tier == "complex"
    assert method == "ml_model"

def test_hybrid_executor_rule_fallback(mock_context):
    """ML disabled: Fallback to Leap 4 rules."""
    executor = HybridExecutor(
        message_bus=mock_bus,
        cost_tracker=mock_cost_tracker,
        agent_context=mock_context,
        enable_ml_routing=False  # ML disabled
    )

    tier, method = executor._classify_task_complexity(
        task_id="task_456",
        task_description="Fix typo in README"
    )

    assert tier == "simple"
    assert method == "rule_based_fallback"

def test_hybrid_executor_ab_testing(mock_context, mock_ml_classifier, monkeypatch):
    """A/B testing: 10% traffic to ML, 90% to rules."""
    monkeypatch.setenv("ML_AB_TEST_ENABLED", "true")
    monkeypatch.setenv("ML_AB_TEST_PERCENTAGE", "10")

    executor = HybridExecutor(
        message_bus=mock_bus,
        cost_tracker=mock_cost_tracker,
        agent_context=mock_context,
        enable_ml_routing=True
    )
    executor.ml_classifier = mock_ml_classifier

    # Classify 100 tasks, count ML vs rule routing
    ml_count = 0
    rule_count = 0

    for i in range(100):
        tier, method = executor._classify_task_complexity(
            task_id=f"task_{i}",
            task_description="description"
        )
        if method == "ml_model":
            ml_count += 1
        else:
            rule_count += 1

    # Expect ~10% ML, ~90% rules (allow ±5% variance)
    assert 5 <= ml_count <= 15
    assert 85 <= rule_count <= 95

@pytest.mark.integration
async def test_hybrid_executor_e2e_ml(mock_context):
    """End-to-end: Task routed through ML classification."""
    executor = HybridExecutor(
        message_bus=InMemoryMessageBus(),
        cost_tracker=CostTracker(),
        agent_context=mock_context,
        enable_ml_routing=True
    )

    # Publish task to execution queue
    await executor.message_bus.publish("execution_queue", {
        "task_id": "task_e2e",
        "description": "Implement JWT authentication",
        "complexity": None  # Let ML classify
    })

    # Wait for task completion
    result = await asyncio.wait_for(
        executor.message_bus.subscribe("telemetry_stream"),
        timeout=30
    )

    assert result["type"] == "task_complete"
    assert result["task_id"] == "task_e2e"
    # Verify ML classification was used (check logs)
```

---

### Phase 3.3 Deliverables

**Files Modified** (1 file):
1. `trinity_protocol/core/hybrid_executor.py` (+150 lines)

**Tests Created** (1 file):
1. `tests/test_hybrid_executor_ml_integration.py` (12+ tests)

**Phase 3.3 Success Criteria**:
- ✅ 12+ integration tests passing (100% pass rate)
- ✅ ML-first routing functional (Priority 1)
- ✅ Fallback to Leap 4 rules working (Priority 2)
- ✅ A/B testing functional (10% traffic split)
- ✅ Zero regression (existing HybridExecutor tests still pass)
- ✅ End-to-end workflow verified (task → ML → execution)

**Phase 3.3 Checkpoint**: Final validation before production
- Run full test suite (1,725+ tests, 100% pass rate)
- Verify ML routing end-to-end (task → classification → execution)
- Test A/B splitting (10% ML, 90% rules)
- Confirm no performance degradation (<50ms classification latency)

---

## Constitutional Compliance Validation

### Article I: Complete Context Before Action ✅

**Retry Logic**:
```python
# FeatureExtractor: Retry on embedding API timeout
for attempt in range(1, 4):  # 3 attempts
    try:
        response = self.openai_client.embeddings.create(...)
        break
    except openai.APITimeoutError:
        if attempt == 3:
            return Err("Embedding API timeout after 3 attempts")
        time.sleep(2 ** attempt)  # Exponential backoff (2s, 4s)
```

**Complete Validation**:
- Feature extraction completes or errors (never partial)
- Model loading validates schema compatibility
- All predictions logged before proceeding

### Article II: 100% Verification and Stability ✅

**Test Coverage**:
- Unit tests: 37+ tests (models, classifier, integration)
- Integration tests: 12+ tests (HybridExecutor end-to-end)
- Performance tests: Latency <50ms p99 (100 tasks)
- Total: 49+ tests (100% pass rate required)

**Result Pattern**:
```python
# All operations return Result<T, E> for error handling
def classify_task(...) -> Result[ClassificationResult, str]:
    try:
        # ... classification logic
        return Ok(result)
    except Exception as e:
        return Err(f"Classification failed: {e}")
```

### Article III: Automated Merge Enforcement ✅

**Automated Routing**:
- No manual model selection in production
- A/B testing automated (deterministic hash-based splitting)
- Environment overrides allowed (testing only, logged)

**Quality Gates**:
- Pre-commit: All tests pass (49+ tests)
- CI pipeline: Full test suite (1,725+ tests)
- Constitutional audit: Article I-V validation

### Article IV: Continuous Learning and Improvement ✅ (CRITICAL)

**VectorStore Integration MANDATORY**:
```python
def _store_prediction(self, result: ClassificationResult) -> None:
    """Article IV: Store prediction in VectorStore (MANDATORY)."""
    prediction_log = PredictionLog(...)

    self.context.store_memory(
        key=f"ml_classification_{result.task_id}",
        content=prediction_log.to_vectorstore_dict(),
        tags=["ml_classification", "leap5", result.tier, result.method]
    )
```

**Learning Workflow**:
1. **Store**: All predictions logged to VectorStore (Article IV)
2. **Feedback**: Quality signals update `actual_tier` post-execution (Leap 4)
3. **Retrain**: Weekly pipeline uses VectorStore data (Phase 4)
4. **Deploy**: A/B test validates new model (Phase 4)

### Article V: Spec-Driven Development ✅

**Process Followed**:
1. **Spec**: `specs/spec-005-phase3-ml-inference.md` (created in parallel)
2. **Plan**: `plans/plan-005-phase3-ml-inference.md` (this document)
3. **Implementation**: Code follows plan structure
4. **Tasks**: TodoWrite breakdown for execution tracking

**Living Documents**:
- Plan updated during implementation (actual vs estimated)
- Spec updated with learnings (edge cases, performance)

---

## Performance Targets & Validation

### Latency Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **ML Classification p99** | <50ms | 100 task benchmark |
| **Feature Extraction p99** | <25ms | Embedding + TF-IDF + metadata |
| **Model Inference p99** | <10ms | scikit-learn predict_proba() |
| **VectorStore Logging p99** | <15ms | context.store_memory() |

**Validation Script**:
```python
# tests/test_performance.py
def test_classification_latency_p99():
    """Performance: Classification latency <50ms p99."""
    classifier = MLClassifier(context=real_context)

    latencies = []
    for i in range(100):
        start = time.perf_counter()
        classifier.classify_task(f"task_{i}", "description")
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    p99 = sorted(latencies)[98]
    assert p99 < 50, f"p99={p99:.1f}ms exceeds 50ms target"
```

### Cost Targets

| Metric | Target | Actual (Estimated) |
|--------|--------|-------------------|
| **Embedding Cost** | $0.00002/task | $0.00002/task (OpenAI) |
| **Inference Cost** | $0/task | $0/task (local scikit-learn) |
| **VectorStore Storage** | $0.001/task | $0.001/task (Firestore estimate) |
| **Total Classification Cost** | <$0.01/task | $0.00202/task ✅ |

### Accuracy Targets

| Metric | Baseline (Leap 4) | Target (Leap 5) | Validation Method |
|--------|-------------------|-----------------|-------------------|
| **Routing Accuracy** | 85-90% | >98% | 100-task validation set (Phase 6) |
| **False Negative Rate** | ~5% | <2% | Complex tasks misclassified as simple |
| **Confidence Calibration** | N/A | ±5% | P(tier\|confidence=0.9) ~ 0.9 |

---

## Risk Management & Mitigation

### High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Phase 2 incomplete** | Low | Critical | Pre-flight validation (required deliverables) |
| **Model loading fails** | Medium | High | Graceful fallback to Leap 4 rules (Article I) |
| **Embedding API timeout** | Medium | Medium | Retry logic (3 attempts, exponential backoff) |
| **Classification latency >50ms** | Low | High | Feature caching, model lazy loading, profiling |

### Medium-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **A/B testing bugs** | Low | Medium | Deterministic hash validation (10% ±5% variance) |
| **VectorStore storage failure** | Low | Medium | Log error but don't crash classification (Article IV) |
| **Feature extraction failure** | Low | Low | Fallback to Leap 4 rules (graceful degradation) |

### Constitutional Risks

| Risk | Article | Mitigation |
|------|---------|------------|
| **Predictions not stored** | Article IV | Assert VectorStore storage in integration test |
| **Incomplete validation** | Article II | 49+ tests with 100% pass rate required |
| **Manual overrides** | Article III | A/B testing automated, env vars logged only |

---

## Success Metrics & Acceptance Criteria

### Phase 3 Complete Criteria

**Deliverables** (9 files):
- ✅ 3 Pydantic models (MLClassifier, PredictionLog, ABTestConfig)
- ✅ 1 inference engine (MLClassifier class)
- ✅ 1 integration (HybridExecutor modifications)
- ✅ 4 test files (28+ models tests, 15+ classifier tests, 12+ integration tests)

**Tests** (49+ tests, 100% pass rate):
- ✅ Unit tests: 37+ tests (models, classifier)
- ✅ Integration tests: 12+ tests (HybridExecutor end-to-end)

**Performance**:
- ✅ Classification latency <50ms p99 (measured with 100 tasks)
- ✅ Feature extraction cached (no duplicate embeddings)
- ✅ Model loaded once (lazy init, cached in memory)

**Functionality**:
- ✅ ML-first routing (Priority 1)
- ✅ Rule-based fallback (Priority 2, confidence <0.7 or ML unavailable)
- ✅ A/B testing (10% traffic to ML, deterministic splitting)
- ✅ VectorStore logging (Article IV, all predictions stored)
- ✅ Graceful degradation (no crashes on ML failure)

**Constitutional Compliance**:
- ✅ Article I: Retry logic (embedding API timeout)
- ✅ Article II: Result pattern, 100% test pass rate
- ✅ Article III: Automated routing, A/B testing
- ✅ Article IV: VectorStore logging MANDATORY
- ✅ Article V: Spec-driven process (Spec-005-Phase3 → Plan-005-Phase3)

### Production Readiness Checklist

**Pre-deployment Validation**:
- [ ] Full test suite passes (1,725+ tests, 100% pass rate)
- [ ] ML classification functional (end-to-end task → classification → execution)
- [ ] A/B testing validated (10% ±5% traffic split)
- [ ] Performance validated (latency <50ms p99, 100-task benchmark)
- [ ] VectorStore logging confirmed (Article IV, all predictions stored)
- [ ] Rollback plan documented (disable ML routing, fallback to Leap 4)

**Post-deployment Monitoring**:
- [ ] Classification latency p99 <50ms (hourly telemetry)
- [ ] VectorStore storage success rate >99% (hourly check)
- [ ] Fallback rate <10% (too many fallbacks = model issues)
- [ ] Zero crashes (graceful degradation working)

---

## Cost Estimate & ROI

### Phase 3 Implementation Cost

**Development Time**:
- Phase 3.1 (Models): 8 hours × $150/hr = $1,200 (3 engineers parallel)
- Phase 3.2 (Inference): 10 hours × $150/hr = $1,500 (1 engineer)
- Phase 3.3 (Integration): 6 hours × $150/hr = $900 (1 engineer)
- **Total Labor**: $3,600

**LLM Cost** (gpt-5 for planning):
- Planning: 80k tokens @ $4/1M = $0.32
- Code generation: 120k tokens @ $4/1M = $0.48
- Review: 30k tokens @ $4/1M = $0.12
- **Total LLM**: $0.92

**Total Phase 3 Cost**: $3,600.92 (labor + LLM)

### Projected Savings (Annual)

**Baseline** (Leap 4 rule-based):
- Classification cost: $0.02-0.05/task
- 10,000 tasks/month × $0.035/task × 12 months = $4,200/year

**Target** (Leap 5 ML-powered):
- Classification cost: $0.008/task (embedding + inference + storage)
- 10,000 tasks/month × $0.008/task × 12 months = $960/year

**Annual Savings**: $4,200 - $960 = **$3,240/year** (77% reduction)

**ROI**: $3,240 / $3,601 = **0.9 years payback period** (~11 months)

---

## Rollback Procedures

### Rollback Triggers

1. **Classification latency >100ms p99** (2x target, degraded performance)
2. **VectorStore storage failure rate >10%** (Article IV violation)
3. **Fallback rate >30%** (ML model unreliable)
4. **Zero division errors, crashes** (code bugs)
5. **Test suite failures** (regression introduced)

### Rollback Steps

**Immediate Actions** (5 minutes):
1. **Disable ML routing globally**:
   ```bash
   # Set environment variable
   export USE_ML_ROUTING=false

   # Restart HybridExecutor (auto-fallback to Leap 4)
   systemctl restart hybrid-executor
   ```

2. **Verify fallback functional**:
   ```bash
   # Check logs for rule-based classification
   tail -f logs/hybrid_executor.log | grep "rule_based_fallback"
   ```

3. **Alert stakeholders**:
   ```python
   # Publish rollback event to telemetry
   telemetry.publish({
       "type": "ml_routing_rollback",
       "reason": "classification_latency_exceeded",
       "timestamp": datetime.now(UTC).isoformat()
   })
   ```

**Root Cause Analysis** (1 hour):
1. Analyze error logs (classification failures, timeouts)
2. Inspect VectorStore storage logs (Article IV compliance)
3. Profile classification latency (feature extraction, model inference)
4. Review recent changes (code diffs, config changes)

**Fix & Re-deploy** (variable, depends on root cause):
1. Fix identified issue (code bug, config error, model corruption)
2. Run full test suite (1,725+ tests, 100% pass rate)
3. Deploy fix to staging (A/B test with 5% traffic)
4. Monitor for 24 hours (latency, fallback rate, accuracy)
5. Deploy to production (gradually increase traffic to 100%)

---

## Next Steps (Phase 4)

### Phase 4: Online Learning & Retraining (Week 2, Day 3-4)

**Prerequisites**:
- ✅ Phase 3 complete (ML inference functional)
- ✅ VectorStore predictions accumulating (Article IV data)
- ✅ Quality feedback loop active (Leap 4, actual_tier updates)

**Objectives**:
1. Implement weekly retraining pipeline (VectorStore → training data → model)
2. Build A/B testing framework (10% traffic to new model)
3. Automate deployment (if new model accuracy ≥current + 0.5%)
4. Enable continuous model improvement from production feedback

**Deliverables** (Phase 4):
- `tools/ml_routing/online_learning_pipeline.py` (~700 lines)
- `scripts/setup_ml_retraining_cron.sh` (~150 lines)
- Weekly retraining cron job (Sunday 2am UTC)
- A/B testing with automated deployment

**Handoff to Phase 4**:
- Validate Phase 3 complete (49+ tests passing)
- Confirm VectorStore predictions accumulating (>100 predictions)
- Verify quality feedback loop active (actual_tier being updated)
- Plan Phase 4 kickoff (review retraining spec, plan)

---

## Appendix A: File Structure

```
Agency/
├── shared/
│   └── models/
│       ├── ml_classifier.py          # NEW: ClassificationResult, MLClassifierConfig
│       ├── prediction_log.py         # NEW: PredictionLog (VectorStore)
│       └── ab_test_config.py         # NEW: ABTestConfig (A/B testing)
│
├── tools/
│   └── ml_routing/
│       ├── ml_classifier.py          # NEW: MLClassifier class (inference)
│       ├── feature_extractor.py      # Phase 1: Feature extraction
│       └── model_storage.py          # Phase 2: Model serialization
│
├── trinity_protocol/
│   └── core/
│       └── hybrid_executor.py        # MODIFIED: ML-first routing (+150 lines)
│
└── tests/
    ├── test_ml_classifier_models.py  # NEW: Model tests (10+ tests)
    ├── test_prediction_log.py        # NEW: PredictionLog tests (8+ tests)
    ├── test_ab_test_config.py        # NEW: ABTestConfig tests (10+ tests)
    ├── test_ml_classifier.py         # NEW: MLClassifier tests (15+ tests)
    └── test_hybrid_executor_ml_integration.py  # NEW: Integration tests (12+ tests)
```

---

## Appendix B: Environment Variables

```bash
# ML Routing Configuration
USE_ML_ROUTING=true                    # Enable ML classification (default: true)
ML_CONFIDENCE_THRESHOLD=0.7            # Min confidence for ML prediction (default: 0.7)
ML_CACHE_SIZE=1000                     # Max embeddings cached (default: 1000)

# A/B Testing Configuration
ML_AB_TEST_ENABLED=false               # Enable A/B testing (default: false)
ML_AB_TEST_PERCENTAGE=10               # ML traffic % (default: 10, range: 0-100)

# Model Configuration
ML_MODEL_PATH=~/.agency/models/routing_classifier_latest.pkl  # Model path

# OpenAI API (Feature Extraction)
OPENAI_API_KEY=<your_key>              # Required for embeddings

# VectorStore (Article IV)
USE_ENHANCED_MEMORY=true               # MANDATORY: VectorStore integration
```

---

## Appendix C: Quick Reference

### Classification Flow

```
Task arrives
    ↓
classify_task_complexity(task_id, description, metadata)
    ↓
┌─────────────────────────────────────┐
│ Priority 1: ML Classifier           │
│ - A/B test check (deterministic)    │
│ - Feature extraction (embedding)    │
│ - Model inference (predict_proba)   │
│ - Confidence check (≥0.7?)          │
│   - YES: Return ML prediction       │
│   - NO: Fallback to Priority 2      │
└─────────────────────────────────────┘
    ↓ (if ML fails or low confidence)
┌─────────────────────────────────────┐
│ Priority 2: Rule-Based Fallback     │
│ - Leap 4 rule classification        │
│ - Return rule-based prediction      │
└─────────────────────────────────────┘
    ↓
Store prediction in VectorStore (Article IV)
    ↓
Route to model tier (simple/moderate/complex)
```

### Debugging Commands

```bash
# Check ML routing status
python -c "from shared.models.ml_classifier import MLClassifierConfig; print(MLClassifierConfig.from_env())"

# Test classification (single task)
python -m tools.ml_routing.ml_classifier "task_123" "Implement JWT authentication"

# Measure latency (100 tasks)
python tests/test_performance.py::test_classification_latency_p99

# Verify VectorStore logging
python -c "from shared.agent_context import create_agent_context; ctx = create_agent_context('test'); print(ctx.search_memories(['ml_classification']))"

# Enable A/B testing (10% traffic to ML)
export ML_AB_TEST_ENABLED=true
export ML_AB_TEST_PERCENTAGE=10
systemctl restart hybrid-executor
```

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial plan for Leap 5 Phase 3 (ML inference integration)            |

---

*"From training to inference, from models to production."*

**Plan Version**: 1.0
**Last Updated**: 2025-10-10
**Next Review**: After Phase 3.1 completion (Day 1)
**Related Documents**:
- Spec: `specs/spec-005-phase3-ml-inference.md`
- Parent Plan: `plans/plan-005-advanced-pattern-recognition.md`
- ADR: `docs/adr/ADR-024-adaptive-model-router.md`
