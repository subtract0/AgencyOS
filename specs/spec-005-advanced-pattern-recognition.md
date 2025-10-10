# Specification: Leap 5 - Advanced Pattern Recognition with Machine Learning

**Spec ID**: `spec-005-advanced-pattern-recognition`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**: `spec-004-quality-feedback-loop.md` (Leap 4)
**Related ADRs**: `ADR-024: Adaptive Model Router`, `ADR-004: Continuous Learning`

---

## Executive Summary

Leap 5 evolves the rule-based quality feedback loop (Leap 4) into an ML-powered pattern recognition system that predicts task complexity with >98% accuracy and <$0.01 per classification. By training supervised classifiers on historical VectorStore data, the system learns nuanced patterns that transcend hand-crafted rules, achieving true autonomous routing intelligence.

**Key Innovation**: Hybrid architecture combining rule-based fallbacks (Leap 4) with ML predictions (Leap 5), enabling gradual training without disrupting production routing.

---

## Goals

### Primary Goals

- **Goal 1**: Achieve >98% routing accuracy with ML-based classification (baseline: 85-90% with Leap 4 rules)
- **Goal 2**: Reduce classification cost to <$0.01 per task (current: $0.02-0.05 with rule refinement)
- **Goal 3**: Enable continuous online learning from production feedback (model adapts to new task patterns)
- **Goal 4**: Maintain <50ms p99 classification latency (no degradation from Leap 4)

### Success Metrics

| Metric | Baseline (Leap 4) | Target (Leap 5) | Measurement Method |
|--------|-------------------|-----------------|-------------------|
| **Routing Accuracy** | 85-90% (rule-based) | >98% | 100-task validation set (manual ground truth) |
| **Classification Cost** | $0.02-0.05/task | <$0.01/task | Embedding + inference costs tracked |
| **Latency (p99)** | <50ms | <50ms | Telemetry logging per classification |
| **False Negative Rate** | ~5% | <2% | Complex tasks routed to simple tier |
| **Model Drift Detection** | N/A (stateless rules) | <3% accuracy degradation/month | Rolling 7-day accuracy window |
| **Training Data Quality** | N/A | >90% high-confidence labels | Confidence scores from Leap 4 feedback |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Real-time LLM-based classification (too expensive, >$0.05/task for GPT-5)
- **Non-Goal 2**: Unsupervised clustering without labels (accuracy insufficient for production)
- **Non-Goal 3**: Deep learning models (BERT, transformers) requiring GPU inference (latency >200ms)
- **Non-Goal 4**: Custom embedding models (use OpenAI text-embedding-3-small for consistency)

### Future Considerations

- **Future Enhancement 1**: Multi-task learning (predict tier + execution time + test count simultaneously)
- **Future Enhancement 2**: Active learning (agent requests human labels for uncertain tasks)
- **Future Enhancement 3**: Reinforcement learning from cost/quality rewards (optimize for $savings + accuracy)
- **Future Enhancement 4**: Federated learning across multiple Agency deployments (institutional knowledge sharing)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Adaptive Router Agent (Primary Consumer)

- **Description**: Intelligent routing system that classifies task complexity using ML predictions
- **Goals**: >98% accuracy, <$0.01/task cost, <50ms latency, zero manual tuning
- **Pain Points**: Rule-based system (Leap 4) requires manual threshold tuning, struggles with edge cases
- **Technical Proficiency**: Autonomous agent with VectorStore + ML model integration

#### Persona 2: ML Training Pipeline (System Component)

- **Description**: Automated pipeline that trains/updates models from VectorStore feedback
- **Goals**: Continuous improvement without human intervention, constitutional compliance (Article IV)
- **Pain Points**: Training data quality (noisy labels), model drift, retraining costs
- **Technical Proficiency**: Batch processing system with Pydantic models, scikit-learn integration

#### Persona 3: Development Team (Monitoring & Debugging)

- **Description**: Engineers monitoring routing accuracy, investigating misclassifications
- **Goals**: Transparent ML decisions (explainability), A/B testing framework, rollback capability
- **Pain Points**: Black-box models hard to debug, need SHAP/LIME explanations
- **Technical Proficiency**: Senior engineers with ML/DevOps expertise

### User Journeys

#### Journey 1: ML-Powered Classification (Primary Use Case)

```
1. User starts with: New task arrives at AdaptiveRouterAgent
2. System needs to: Predict complexity tier (simple/moderate/complex) with >98% accuracy
3. System performs:
   - Extract task features (description length, keyword presence, historical patterns)
   - Generate task embedding (text-embedding-3-small, 1536-dim, $0.00002/task)
   - Query trained ML model (scikit-learn RandomForest, <10ms inference)
   - Apply confidence threshold (if confidence <0.7, fallback to Leap 4 rules)
   - Return tier prediction with confidence score
4. System achieves:
   - Tier prediction: "complex" (confidence=0.92)
   - Latency: 35ms (25ms embedding + 10ms inference)
   - Cost: $0.008 ($0.00002 embedding + $0 inference)
   - VectorStore learning: Store prediction for future training
```

#### Journey 2: Continuous Training Pipeline (Secondary Use Case)

```
1. System starts with: 100 new quality feedback records from Leap 4 (1 week accumulation)
2. System needs to: Retrain ML model to adapt to new task patterns
3. System performs:
   - Extract training data from VectorStore (filter confidence ≥0.7)
   - Feature engineering: description embedding + task metadata (TF-IDF, length, keywords)
   - Split train/validation (80/20 stratified by tier)
   - Train ensemble model (RandomForest + GradientBoosting, 5-fold CV)
   - Evaluate on validation set (accuracy, precision, recall, F1)
   - A/B test: 10% traffic to new model, 90% to current model
   - Deploy if new model accuracy ≥current + 0.5% (confidence ≥95%)
4. System achieves:
   - Training time: <5 minutes (batch job, not blocking)
   - Validation accuracy: 98.2% (up from 97.8% current model)
   - A/B test passed: Deploy new model to 100% traffic
   - VectorStore update: Mark training data as "used in model_v5"
```

#### Journey 3: Model Explainability (Debugging Use Case)

```
1. Developer starts with: Task misclassified (simple → should be complex)
2. System needs to: Explain why ML model predicted "simple"
3. System performs:
   - Load SHAP explainer (pre-trained on current model)
   - Compute feature importances for this task
   - Generate explanation: "Predicted simple (confidence=0.65) because:
     - Description length: 20 words (short, weight=-0.3)
     - Keyword 'refactor': absent (weight=-0.2)
     - Historical similar tasks: 8/10 were simple (weight=-0.1)
     - OVERRIDE: Confidence <0.7, fallback to Leap 4 rules"
4. System achieves:
   - Developer understands: Model over-weighted short description
   - Action: Retrain with description length normalization
   - Improvement: Next model version fixes edge case
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: ML Model Training Pipeline

- **AC-1.1**: Scikit-learn RandomForestClassifier with 100 trees, max_depth=10 (baseline model)
- **AC-1.2**: Feature engineering: task embedding (1536-dim) + TF-IDF (top 100 keywords) + metadata (length, keyword flags)
- **AC-1.3**: Training data from VectorStore with confidence ≥0.7 (high-quality labels only)
- **AC-1.4**: 5-fold cross-validation with stratified sampling (balanced tier distribution)
- **AC-1.5**: Model serialization to `~/.agency/models/routing_classifier_v{N}.pkl` (versioned)

#### Feature Component 2: Inference Integration

- **AC-2.1**: HybridExecutor integration: ML prediction with rule-based fallback (confidence <0.7)
- **AC-2.2**: Feature extraction pipeline: task description → embedding → feature vector (cached per task)
- **AC-2.3**: Model loading: lazy init on first classification, cached in memory (no repeated disk reads)
- **AC-2.4**: Confidence threshold tuning: environment variable `ML_CONFIDENCE_THRESHOLD=0.7` (default)
- **AC-2.5**: Graceful degradation: if ML model unavailable, fallback to Leap 4 rules (no crash)

#### Feature Component 3: Online Learning & Retraining

- **AC-3.1**: Incremental training: weekly batch retraining from new VectorStore feedback (automated cron job)
- **AC-3.2**: A/B testing framework: 10% traffic to new model, 90% to current (gradual rollout)
- **AC-3.3**: Accuracy monitoring: rolling 7-day window with drift detection (alert if drop >3%)
- **AC-3.4**: Model versioning: semantic versioning (v1.0, v1.1, v2.0), rollback capability
- **AC-3.5**: Training data curation: filter noisy labels (conflicting feedback, oscillation >3 iterations)

#### Feature Component 4: Model Explainability

- **AC-4.1**: SHAP integration: compute feature importances for top 10 features per prediction
- **AC-4.2**: Explanation storage: VectorStore stores SHAP values for misclassified tasks (debugging)
- **AC-4.3**: Dashboard visualization: feature importance bar chart, confidence distribution histogram
- **AC-4.4**: Debugging CLI: `agency explain-classification <task_id>` shows SHAP explanation
- **AC-4.5**: LIME fallback: if SHAP unavailable, use LIME for local explanations (linear approximation)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Classification latency <50ms p99 (25ms embedding + 10ms inference + 15ms overhead)
- **AC-P.2**: Training time <5 minutes for 1,000 samples (batch job, not blocking production)
- **AC-P.3**: Model size <50MB serialized (fast loading, fits in memory on 8GB machines)
- **AC-P.4**: Embedding cache: 1,000 task embeddings = 6MB (1536-dim × 4 bytes × 1,000)

#### Quality

- **AC-Q.1**: Validation accuracy >98% on 100-task held-out test set (never seen during training)
- **AC-Q.2**: False negative rate <2% (complex tasks routed to simple tier, critical metric)
- **AC-Q.3**: Training data quality: >90% high-confidence labels (confidence ≥0.7 from Leap 4)
- **AC-Q.4**: Model stability: <3% accuracy degradation per month (drift detection)

#### Cost

- **AC-C.1**: Embedding cost: $0.00002/task (OpenAI text-embedding-3-small, $0.02/1M tokens)
- **AC-C.2**: Inference cost: $0/task (local scikit-learn, no API calls)
- **AC-C.3**: Training cost: <$5/month ($0.50 per weekly retraining × 10 retrainings)
- **AC-C.4**: Total classification cost: <$0.01/task (10x cheaper than GPT-5 classification)

#### Security

- **AC-S.1**: Model files: secure permissions (0600, owner-only read/write)
- **AC-S.2**: Training data: no sensitive task content logged (only embeddings + metadata)
- **AC-S.3**: API keys: OpenAI key for embeddings, stored in env vars (not in code)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Training data: complete VectorStore query (all feedback since last training)
- **AC-CI.2**: Feature extraction: retry on embedding API timeout (2x, 3x up to 10x)
- **AC-CI.3**: Model validation: 100% of validation set evaluated (no incomplete results)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Training tests: 20+ unit tests (feature extraction, model training, inference)
- **AC-CII.2**: Integration tests: 5+ end-to-end tests (full pipeline, A/B testing, rollback)
- **AC-CII.3**: Validation set: never used for training (strict train/val/test split)

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: A/B testing: automated deployment only if new model accuracy ≥current + 0.5%
- **AC-CIII.2**: Rollback: automated if production accuracy drops >3% after deployment

#### Article IV: Continuous Learning and Improvement (MANDATORY)

- **AC-CIV.1**: VectorStore integration: all ML predictions stored for future training
- **AC-CIV.2**: Weekly retraining: automated pipeline triggered every 7 days (cron job)
- **AC-CIV.3**: Feedback loop: misclassifications from production → VectorStore → next training batch
- **AC-CIV.4**: Cross-session learning: model trained on all historical data (not just current session)

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows this specification (no deviation without spec update)
- **AC-CV.2**: Model architecture changes versioned (breaking changes require new spec version)

---

## Technical Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Leap 5: ML-Powered Pattern Recognition                                │
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ Feature          │    │ ML Model         │    │ Fallback         │ │
│  │ Extraction       │───▶│ Inference        │───▶│ (Leap 4 Rules)   │ │
│  │                  │    │                  │    │                  │ │
│  │ - Embedding      │    │ - RandomForest   │    │ - Rule-based     │ │
│  │ - TF-IDF         │    │ - Confidence     │    │ - Threshold      │ │
│  │ - Metadata       │    │ - Explainability │    │ - Deterministic  │ │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘ │
│           │                       │                       │            │
│           └───────────────────────┴───────────────────────┘            │
│                                   │                                    │
│                   ┌───────────────▼───────────────┐                    │
│                   │ VectorStore (Article IV)      │                    │
│                   │ - Predictions logged          │                    │
│                   │ - Quality feedback collected  │                    │
│                   │ - Training data curated       │                    │
│                   └───────────────┬───────────────┘                    │
│                                   │                                    │
│                   ┌───────────────▼───────────────┐                    │
│                   │ Training Pipeline (Weekly)    │                    │
│                   │ - Data extraction             │                    │
│                   │ - Feature engineering         │                    │
│                   │ - Model training (5-fold CV)  │                    │
│                   │ - A/B testing (10% traffic)   │                    │
│                   │ - Automated deployment        │                    │
│                   └───────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 ML Model Selection

#### Model Comparison

| Model | Accuracy | Latency | Training Time | Explainability | Cost |
|-------|----------|---------|---------------|----------------|------|
| **RandomForest (Recommended)** | 97-98% | <10ms | <5min | Good (feature importance) | $0 inference |
| **GradientBoosting** | 98-99% | <15ms | <10min | Moderate (SHAP) | $0 inference |
| **Logistic Regression** | 92-94% | <5ms | <1min | Excellent (coefficients) | $0 inference |
| **XGBoost** | 98-99% | <12ms | <8min | Good (SHAP) | $0 inference |
| **GPT-5 (baseline)** | 95-97% | 500ms | N/A | Poor (LLM black box) | $0.05/task |
| **BERT (deep learning)** | 99%+ | 200ms | 2 hours | Poor (attention weights) | $0.02/task (GPU) |

**Decision: RandomForest (100 trees, max_depth=10)**

**Rationale:**
- **Accuracy**: 97-98% meets >98% target with ensemble tuning
- **Latency**: <10ms meets <50ms p99 target
- **Training**: <5min enables weekly retraining
- **Explainability**: Feature importances + SHAP values (critical for debugging)
- **Cost**: $0 inference cost (local scikit-learn, no GPU/API)
- **Stability**: Less prone to overfitting than GradientBoosting
- **Simplicity**: No hyperparameter tuning needed (compared to XGBoost)

**Ensemble Architecture (Production)**:
- **Primary**: RandomForest (100 trees, max_depth=10, min_samples_split=5)
- **Secondary**: GradientBoosting (50 estimators, learning_rate=0.1)
- **Voting**: Soft voting (average class probabilities, weight RF=0.7, GB=0.3)
- **Confidence**: Ensemble confidence = weighted average of model confidences

### 5.3 Feature Engineering

#### Feature Vector Schema (1636 dimensions)

```python
class TaskFeatureVector(BaseModel):
    """
    Feature vector for ML classification.

    Dimensions:
    - Embedding: 1536-dim (text-embedding-3-small)
    - TF-IDF: 100-dim (top 100 keywords from historical tasks)
    - Metadata: 8-dim (length, keyword flags, complexity hints)

    Total: 1644-dim (1536 + 100 + 8)
    """

    # Semantic Features (1536-dim)
    embedding: list[float] = Field(
        ...,
        description="Task description embedding from text-embedding-3-small",
        min_length=1536,
        max_length=1536
    )

    # TF-IDF Features (100-dim)
    tfidf_features: list[float] = Field(
        ...,
        description="TF-IDF scores for top 100 keywords (e.g., 'refactor', 'async', 'test')",
        min_length=100,
        max_length=100
    )

    # Metadata Features (8-dim)
    description_length: int = Field(..., ge=0, description="Character count of task description")
    word_count: int = Field(..., ge=0, description="Word count of task description")
    has_refactor_keyword: int = Field(..., ge=0, le=1, description="Binary: 'refactor' in description")
    has_test_keyword: int = Field(..., ge=0, le=1, description="Binary: 'test' in description")
    has_async_keyword: int = Field(..., ge=0, le=1, description="Binary: 'async' in description")
    has_fix_keyword: int = Field(..., ge=0, le=1, description="Binary: 'fix' in description")
    estimated_time_seconds: float = Field(..., ge=0, description="User-provided estimate (if available)")
    historical_tier_mode: int = Field(..., ge=0, le=2, description="Most common tier for similar tasks (0=simple, 1=moderate, 2=complex)")

    class Config:
        json_schema_extra = {
            "example": {
                "embedding": [0.023, -0.045, ...],  # 1536 floats
                "tfidf_features": [0.12, 0.0, 0.08, ...],  # 100 floats
                "description_length": 120,
                "word_count": 20,
                "has_refactor_keyword": 1,
                "has_test_keyword": 0,
                "has_async_keyword": 1,
                "has_fix_keyword": 0,
                "estimated_time_seconds": 300.0,
                "historical_tier_mode": 2  # complex
            }
        }
```

#### Feature Extraction Pipeline

```python
class FeatureExtractor:
    """
    Extract ML features from task description.

    Constitutional Compliance:
    - Article I: Retry on embedding API timeout
    - Article II: Result pattern for error handling
    - Article IV: Cache features in VectorStore
    """

    def __init__(self, openai_api_key: str, tfidf_vocabulary: list[str]):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.tfidf_vectorizer = TfidfVectorizer(
            vocabulary=tfidf_vocabulary,
            max_features=100,
            stop_words='english'
        )
        self.embedding_cache: dict[str, list[float]] = {}

    def extract_features(
        self,
        task_description: str,
        task_metadata: dict[str, Any] | None = None
    ) -> Result[TaskFeatureVector, str]:
        """
        Extract feature vector from task description.

        Args:
            task_description: Task description text
            task_metadata: Optional metadata (estimated_time, etc.)

        Returns:
            Result with TaskFeatureVector or error message

        Performance:
        - Embedding: <25ms (cached if duplicate task)
        - TF-IDF: <5ms (pre-fitted vectorizer)
        - Metadata: <1ms (simple parsing)
        - Total: <50ms p99
        """
        try:
            # Step 1: Generate embedding (with cache)
            task_hash = hash(task_description)

            if task_hash in self.embedding_cache:
                embedding = self.embedding_cache[task_hash]
            else:
                # Article I: Retry on timeout
                for attempt in range(1, 4):  # 3 attempts
                    try:
                        response = self.openai_client.embeddings.create(
                            model="text-embedding-3-small",
                            input=task_description
                        )
                        embedding = response.data[0].embedding
                        self.embedding_cache[task_hash] = embedding  # Cache for future
                        break
                    except openai.APITimeoutError:
                        if attempt == 3:
                            return Err("Embedding API timeout after 3 attempts")
                        time.sleep(2 ** attempt)  # Exponential backoff

            # Step 2: TF-IDF features
            tfidf_vector = self.tfidf_vectorizer.transform([task_description])
            tfidf_features = tfidf_vector.toarray()[0].tolist()  # 100-dim

            # Step 3: Metadata features
            metadata = task_metadata or {}
            description_length = len(task_description)
            word_count = len(task_description.split())

            # Keyword flags (binary)
            has_refactor = int('refactor' in task_description.lower())
            has_test = int('test' in task_description.lower())
            has_async = int('async' in task_description.lower())
            has_fix = int('fix' in task_description.lower())

            estimated_time = metadata.get('estimated_time_seconds', 0.0)
            historical_tier_mode = metadata.get('historical_tier_mode', 0)  # Default: simple

            # Step 4: Construct feature vector
            features = TaskFeatureVector(
                embedding=embedding,
                tfidf_features=tfidf_features,
                description_length=description_length,
                word_count=word_count,
                has_refactor_keyword=has_refactor,
                has_test_keyword=has_test,
                has_async_keyword=has_async,
                has_fix_keyword=has_fix,
                estimated_time_seconds=estimated_time,
                historical_tier_mode=historical_tier_mode
            )

            return Ok(features)

        except Exception as e:
            return Err(f"Feature extraction failed: {e}")
```

### 5.4 Training Pipeline

#### Training Data Preparation

```python
class TrainingDataPreparer:
    """
    Prepare training data from VectorStore quality feedback.

    Article IV Compliance: Query VectorStore for all historical feedback.
    """

    def __init__(self, context: AgentContext):
        self.context = context

    def prepare_training_data(
        self,
        min_confidence: float = 0.7,
        min_samples_per_class: int = 50
    ) -> Result[TrainingDataset, str]:
        """
        Extract training data from VectorStore.

        Args:
            min_confidence: Minimum confidence score for labels (filter noisy data)
            min_samples_per_class: Minimum samples per tier (balanced dataset)

        Returns:
            Result with TrainingDataset or error message

        Quality Filters:
        - Confidence ≥0.7 (high-quality labels from Leap 4)
        - No oscillation (iteration_count ≤3, avoid conflicting labels)
        - No duplicates (unique task descriptions)
        - Balanced classes (50+ samples per tier, stratified sampling)
        """
        try:
            # Query VectorStore for all quality feedback (Article IV)
            feedback_patterns = self.context.search_memories(
                tags=["quality_feedback", "misclassification"],
                include_session=False  # Cross-session learning
            )

            # Filter high-quality labels
            filtered = [
                p for p in feedback_patterns
                if p.get("confidence", 0.0) >= min_confidence
                and p.get("iteration_count", 0) <= 3  # No oscillation
            ]

            # Extract features and labels
            X_features = []
            y_labels = []
            task_ids = []

            feature_extractor = FeatureExtractor(...)

            for pattern in filtered:
                task_description = pattern.get("task_description", "")
                corrected_tier = pattern.get("corrected_tier", "simple")

                # Extract features
                features_result = feature_extractor.extract_features(task_description)

                if features_result.is_ok():
                    features = features_result.unwrap()
                    X_features.append(self._vectorize_features(features))
                    y_labels.append(self._encode_tier(corrected_tier))
                    task_ids.append(pattern.get("task_id", ""))

            # Check class balance
            tier_counts = Counter(y_labels)

            if any(count < min_samples_per_class for count in tier_counts.values()):
                return Err(
                    f"Insufficient training data: {dict(tier_counts)}. "
                    f"Need {min_samples_per_class}+ samples per class."
                )

            # Split train/validation (80/20 stratified)
            X_train, X_val, y_train, y_val = train_test_split(
                X_features, y_labels,
                test_size=0.2,
                stratify=y_labels,
                random_state=42
            )

            dataset = TrainingDataset(
                X_train=X_train,
                X_val=X_val,
                y_train=y_train,
                y_val=y_val,
                task_ids=task_ids,
                feature_names=self._get_feature_names()
            )

            return Ok(dataset)

        except Exception as e:
            return Err(f"Training data preparation failed: {e}")

    def _vectorize_features(self, features: TaskFeatureVector) -> list[float]:
        """Flatten TaskFeatureVector to 1644-dim array."""
        return (
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

    def _encode_tier(self, tier: str) -> int:
        """Encode tier string to integer label (0=simple, 1=moderate, 2=complex)."""
        mapping = {"simple": 0, "moderate": 1, "complex": 2}
        return mapping.get(tier, 0)
```

#### Model Training

```python
class MLModelTrainer:
    """
    Train ML model for task classification.

    Article II Compliance: 5-fold CV for validation, strict train/val split.
    """

    def train_ensemble_model(
        self,
        dataset: TrainingDataset
    ) -> Result[EnsembleModel, str]:
        """
        Train ensemble model with 5-fold CV.

        Returns:
            Result with trained EnsembleModel or error message

        Performance Target:
        - Training time: <5 minutes for 1,000 samples
        - Validation accuracy: >98%
        - False negative rate: <2%
        """
        try:
            # Model 1: RandomForest (primary)
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1  # Parallel training
            )

            # Model 2: GradientBoosting (secondary)
            gb_model = GradientBoostingClassifier(
                n_estimators=50,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )

            # 5-fold cross-validation
            rf_scores = cross_val_score(
                rf_model, dataset.X_train, dataset.y_train,
                cv=5, scoring='accuracy'
            )

            gb_scores = cross_val_score(
                gb_model, dataset.X_train, dataset.y_train,
                cv=5, scoring='accuracy'
            )

            logger.info(f"RF CV accuracy: {rf_scores.mean():.3f} ±{rf_scores.std():.3f}")
            logger.info(f"GB CV accuracy: {gb_scores.mean():.3f} ±{gb_scores.std():.3f}")

            # Train on full training set
            rf_model.fit(dataset.X_train, dataset.y_train)
            gb_model.fit(dataset.X_train, dataset.y_train)

            # Validate on held-out set
            rf_val_acc = rf_model.score(dataset.X_val, dataset.y_val)
            gb_val_acc = gb_model.score(dataset.X_val, dataset.y_val)

            logger.info(f"RF validation accuracy: {rf_val_acc:.3f}")
            logger.info(f"GB validation accuracy: {gb_val_acc:.3f}")

            # Create ensemble
            ensemble = VotingClassifier(
                estimators=[('rf', rf_model), ('gb', gb_model)],
                voting='soft',  # Average class probabilities
                weights=[0.7, 0.3]  # RF weighted higher
            )

            # Fit ensemble
            ensemble.fit(dataset.X_train, dataset.y_train)
            ensemble_acc = ensemble.score(dataset.X_val, dataset.y_val)

            logger.info(f"Ensemble validation accuracy: {ensemble_acc:.3f}")

            # Check acceptance criteria
            if ensemble_acc < 0.98:
                return Err(f"Model accuracy {ensemble_acc:.3f} below 98% target")

            # Calculate false negative rate
            y_pred = ensemble.predict(dataset.X_val)
            fn_rate = self._calculate_false_negative_rate(dataset.y_val, y_pred)

            if fn_rate > 0.02:
                return Err(f"False negative rate {fn_rate:.3f} above 2% target")

            model = EnsembleModel(
                ensemble=ensemble,
                rf_model=rf_model,
                gb_model=gb_model,
                validation_accuracy=ensemble_acc,
                false_negative_rate=fn_rate,
                training_date=datetime.now(UTC).isoformat(),
                feature_names=dataset.feature_names
            )

            return Ok(model)

        except Exception as e:
            return Err(f"Model training failed: {e}")

    def _calculate_false_negative_rate(self, y_true: list[int], y_pred: list[int]) -> float:
        """
        Calculate false negative rate for complex tasks.

        False Negative: Complex task predicted as simple/moderate.
        Critical metric: We MUST catch complex tasks (quality risk if misclassified).
        """
        complex_label = 2  # complex

        # Find true complex tasks
        true_complex_indices = [i for i, label in enumerate(y_true) if label == complex_label]

        if not true_complex_indices:
            return 0.0

        # Count false negatives (complex predicted as non-complex)
        false_negatives = sum(
            1 for i in true_complex_indices
            if y_pred[i] != complex_label
        )

        return false_negatives / len(true_complex_indices)
```

### 5.5 Inference Integration

```python
class MLClassifier:
    """
    ML-powered task classifier with rule-based fallback.

    Hybrid Architecture:
    - Primary: ML model prediction with confidence scoring
    - Fallback: Leap 4 rule-based classification (if confidence <0.7)

    Article IV Compliance: Store all predictions in VectorStore.
    """

    def __init__(
        self,
        context: AgentContext,
        model_path: str,
        confidence_threshold: float = 0.7
    ):
        self.context = context
        self.confidence_threshold = confidence_threshold
        self.feature_extractor = FeatureExtractor(...)

        # Lazy load model (on first classification)
        self._model: EnsembleModel | None = None
        self._model_path = model_path

        # Fallback to Leap 4 rules
        self.rule_classifier = RuleBasedClassifier()  # Leap 4

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
            task_metadata: Optional metadata

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
            # Step 1: Extract features
            features_result = self.feature_extractor.extract_features(
                task_description, task_metadata
            )

            if features_result.is_err():
                # Feature extraction failed, fallback to rules
                logger.warning(
                    f"Feature extraction failed for {task_id}: {features_result.unwrap_err()}"
                )
                return self._fallback_to_rules(task_id, task_description)

            features = features_result.unwrap()
            feature_vector = self._vectorize_features(features)

            # Step 2: Load model (lazy)
            if self._model is None:
                self._model = self._load_model()

            # Step 3: ML prediction with confidence
            proba = self._model.ensemble.predict_proba([feature_vector])[0]  # [P(simple), P(moderate), P(complex)]
            predicted_tier_idx = proba.argmax()
            confidence = proba[predicted_tier_idx]

            tier_names = ["simple", "moderate", "complex"]
            predicted_tier = tier_names[predicted_tier_idx]

            # Step 4: Confidence threshold check
            if confidence >= self.confidence_threshold:
                # High confidence ML prediction
                result = ClassificationResult(
                    task_id=task_id,
                    tier=predicted_tier,
                    confidence=confidence,
                    method="ml_model",
                    model_version=self._model.training_date,
                    features=features,
                    class_probabilities={
                        "simple": proba[0],
                        "moderate": proba[1],
                        "complex": proba[2]
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
                    f"ML confidence {confidence:.3f} < {self.confidence_threshold}, "
                    f"falling back to rules for {task_id}"
                )
                return self._fallback_to_rules(task_id, task_description)

        except Exception as e:
            logger.error(f"ML classification failed for {task_id}: {e}")
            return self._fallback_to_rules(task_id, task_description)

    def _fallback_to_rules(
        self,
        task_id: str,
        task_description: str
    ) -> Result[ClassificationResult, str]:
        """Fallback to Leap 4 rule-based classification."""
        rule_result = self.rule_classifier.classify(task_description)

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

    def _store_prediction(self, result: ClassificationResult) -> None:
        """Store prediction in VectorStore (Article IV)."""
        self.context.store_memory(
            key=f"ml_classification_{result.task_id}",
            content={
                "task_id": result.task_id,
                "tier": result.tier,
                "confidence": result.confidence,
                "method": result.method,
                "model_version": result.model_version,
                "class_probabilities": result.class_probabilities,
                "timestamp": datetime.now(UTC).isoformat()
            },
            tags=["ml_classification", "leap5", result.tier, result.method]
        )
```

### 5.6 Online Learning & Retraining

#### Automated Retraining Pipeline

```python
class OnlineLearningPipeline:
    """
    Automated pipeline for continuous model improvement.

    Article IV Compliance: Weekly retraining from VectorStore feedback.
    """

    def __init__(self, context: AgentContext):
        self.context = context
        self.trainer = MLModelTrainer()
        self.data_preparer = TrainingDataPreparer(context)

    def run_weekly_retraining(self) -> Result[RetrainingResult, str]:
        """
        Execute weekly retraining pipeline.

        Workflow:
        1. Extract new training data from VectorStore (since last training)
        2. Merge with historical data (cumulative learning)
        3. Train new model with 5-fold CV
        4. A/B test: 10% traffic to new model, 90% to current model
        5. If new model accuracy ≥current + 0.5%: deploy to 100%
        6. Else: rollback to current model

        Returns:
            Result with RetrainingResult (success, metrics, deployment status)

        Schedule: Cron job every Sunday 2am UTC
        """
        try:
            logger.info("🔄 Starting weekly retraining pipeline")

            # Step 1: Extract training data
            dataset_result = self.data_preparer.prepare_training_data()

            if dataset_result.is_err():
                return Err(f"Training data preparation failed: {dataset_result.unwrap_err()}")

            dataset = dataset_result.unwrap()

            logger.info(
                f"Training data: {len(dataset.X_train)} train, {len(dataset.X_val)} val"
            )

            # Step 2: Train new model
            model_result = self.trainer.train_ensemble_model(dataset)

            if model_result.is_err():
                return Err(f"Model training failed: {model_result.unwrap_err()}")

            new_model = model_result.unwrap()

            logger.info(
                f"New model trained: accuracy={new_model.validation_accuracy:.3f}, "
                f"FN_rate={new_model.false_negative_rate:.3f}"
            )

            # Step 3: Load current production model
            current_model = self._load_current_model()

            # Step 4: A/B testing (10% traffic to new model)
            ab_test_result = self._run_ab_test(
                current_model=current_model,
                new_model=new_model,
                test_traffic_pct=0.1,
                test_duration_hours=24
            )

            # Step 5: Deploy if new model is better
            if ab_test_result.new_model_accuracy >= ab_test_result.current_model_accuracy + 0.005:  # +0.5%
                logger.info(
                    f"✅ New model is better ({ab_test_result.new_model_accuracy:.3f} vs "
                    f"{ab_test_result.current_model_accuracy:.3f}), deploying to 100%"
                )

                self._deploy_model(new_model)

                return Ok(RetrainingResult(
                    success=True,
                    new_model_accuracy=new_model.validation_accuracy,
                    current_model_accuracy=current_model.validation_accuracy,
                    deployed=True,
                    ab_test_metrics=ab_test_result
                ))

            else:
                logger.warning(
                    f"⚠️  New model not better ({ab_test_result.new_model_accuracy:.3f} vs "
                    f"{ab_test_result.current_model_accuracy:.3f}), keeping current model"
                )

                return Ok(RetrainingResult(
                    success=True,
                    new_model_accuracy=new_model.validation_accuracy,
                    current_model_accuracy=current_model.validation_accuracy,
                    deployed=False,
                    ab_test_metrics=ab_test_result
                ))

        except Exception as e:
            return Err(f"Retraining pipeline failed: {e}")

    def _run_ab_test(
        self,
        current_model: EnsembleModel,
        new_model: EnsembleModel,
        test_traffic_pct: float,
        test_duration_hours: int
    ) -> ABTestResult:
        """
        Run A/B test: 10% traffic to new model, 90% to current model.

        Duration: 24 hours (1 day of production traffic)
        Metric: Routing accuracy (measured via Leap 4 feedback loop)
        """
        # Implementation: Route traffic based on task_id hash
        # Store results in VectorStore
        # Calculate accuracy from quality feedback
        ...
```

### 5.7 Model Explainability (SHAP Integration)

```python
class ModelExplainer:
    """
    Generate explanations for ML predictions using SHAP.

    Use Case: Debugging misclassifications, understanding model behavior.
    """

    def __init__(self, model: EnsembleModel, background_data: np.ndarray):
        self.model = model
        self.explainer = shap.TreeExplainer(model.rf_model)  # Use RandomForest for SHAP
        self.background_data = background_data

    def explain_prediction(
        self,
        task_id: str,
        feature_vector: list[float],
        feature_names: list[str]
    ) -> Result[ExplanationResult, str]:
        """
        Generate SHAP explanation for prediction.

        Args:
            task_id: Task identifier
            feature_vector: 1644-dim feature vector
            feature_names: Feature names (for visualization)

        Returns:
            Result with ExplanationResult (SHAP values, feature importances)

        Performance: <100ms (pre-computed explainer)
        """
        try:
            # Compute SHAP values
            shap_values = self.explainer.shap_values(np.array([feature_vector]))

            # Extract top 10 features by absolute SHAP value
            shap_values_single = shap_values[0][0]  # [simple, moderate, complex] -> take predicted class
            feature_importances = list(zip(feature_names, shap_values_single))
            feature_importances.sort(key=lambda x: abs(x[1]), reverse=True)
            top_features = feature_importances[:10]

            explanation = ExplanationResult(
                task_id=task_id,
                shap_values=shap_values_single.tolist(),
                top_features=top_features,
                explanation_text=self._generate_text_explanation(top_features)
            )

            return Ok(explanation)

        except Exception as e:
            return Err(f"SHAP explanation failed: {e}")

    def _generate_text_explanation(self, top_features: list[tuple[str, float]]) -> str:
        """Generate human-readable explanation from SHAP values."""
        lines = ["Top factors influencing prediction:"]

        for i, (feature_name, shap_value) in enumerate(top_features[:5], 1):
            direction = "increases" if shap_value > 0 else "decreases"
            lines.append(f"{i}. {feature_name}: {direction} complexity (SHAP={shap_value:.3f})")

        return "\n".join(lines)
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `scikit-learn>=1.3.0` - ML model training (RandomForest, GradientBoosting)
- **Dependency 2**: `openai>=1.0.0` - Embedding generation (text-embedding-3-small)
- **Dependency 3**: `shap>=0.42.0` - Model explainability (SHAP values)
- **Dependency 4**: `agency_memory/vector_store.py` - Training data storage (Article IV)

### External Dependencies

- **External Dep 1**: OpenAI API - Embedding generation ($0.02/1M tokens)
- **External Dep 2**: VectorStore - Historical quality feedback (Leap 4 dependency)

### Technical Constraints

- **Constraint 1**: Classification latency <50ms p99 (no degradation from Leap 4)
- **Constraint 2**: Training time <5 minutes for 1,000 samples (weekly retraining feasible)
- **Constraint 3**: Model size <50MB serialized (fast loading, fits in memory)
- **Constraint 4**: Training data quality >90% high-confidence labels (VectorStore filter)

### Business Constraints

- **Constraint 1**: Classification cost <$0.01/task (10x cheaper than GPT-5)
- **Constraint 2**: Routing accuracy >98% (no degradation from Leap 4 target)
- **Constraint 3**: False negative rate <2% (critical metric for complex tasks)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Insufficient training data** (need 50+ samples per tier for baseline model) - *Mitigation*: Bootstrap with Leap 4 rule-based labels, collect 300+ samples before ML training
- **Risk 2**: **Model drift** (accuracy degrades as task patterns evolve) - *Mitigation*: Weekly retraining, 7-day rolling accuracy monitoring, alert if drop >3%

### Medium Risk Items

- **Risk 3**: **Training data quality** (noisy labels from Leap 4 misclassifications) - *Mitigation*: Filter confidence ≥0.7, remove oscillating tasks (iteration_count >3)
- **Risk 4**: **Overfitting** (model memorizes training data, poor generalization) - *Mitigation*: 5-fold CV, stratified sampling, validation set never used for training

### Low Risk Items

- **Risk 5**: **Embedding API failures** (OpenAI downtime) - *Mitigation*: Fallback to Leap 4 rules, embedding cache (1,000 tasks)
- **Risk 6**: **Model loading latency** (first classification delayed) - *Mitigation*: Lazy loading (on first use), warm-up endpoint

### Constitutional Risks

- **Constitutional Risk 1**: **Article IV violation** (predictions not stored in VectorStore) - *Mitigation*: Assert VectorStore storage in integration test, telemetry logging
- **Constitutional Risk 2**: **Article II violation** (incomplete validation)** - *Mitigation*: Strict train/val/test split, 100% validation set evaluated

---

## Integration Points

### Agent Integration

- **HybridExecutor**: Primary consumer of ML classifications (replaces Leap 4 rule-based routing)
- **QualityEnforcerAgent**: Monitors ML accuracy metrics, triggers alerts on drift
- **LearningAgent**: Extracts ML training patterns for cross-session learning

### System Integration

- **VectorStore**: Training data source (quality feedback from Leap 4), prediction storage (Article IV)
- **Telemetry System**: ML accuracy metrics, A/B test results, model version tracking

### External Integration

- **OpenAI API**: Embedding generation (text-embedding-3-small, $0.02/1M tokens)

---

## Testing Strategy

### Test Categories

- **Unit Tests** (30+ tests): Feature extraction, model training, inference, confidence thresholding
- **Integration Tests** (10+ tests): End-to-end pipeline (VectorStore → training → inference → storage)
- **Performance Tests** (5+ tests): Classification latency <50ms p99, training time <5min
- **Constitutional Compliance Tests** (5+ tests): Article I retry logic, Article II validation, Article IV VectorStore storage

### Test Data Requirements

- **Test Data 1**: 100-task validation set with manual ground truth labels (never used for training)
- **Test Data 2**: 1,000+ historical quality feedback records from VectorStore (training data)
- **Test Data 3**: Edge cases (ambiguous tasks, short descriptions, novel patterns)

### Test Environment Requirements

- **Environment 1**: OpenAI API key for embedding generation (test account with quota)
- **Environment 2**: VectorStore with 1,000+ quality feedback records (Leap 4 data)
- **Environment 3**: Scikit-learn>=1.3.0, SHAP>=0.42.0 installed

---

## Implementation Phases

### Phase 1: Feature Engineering & Data Pipeline (Week 1, Day 1-3)

- **Scope**: Feature extraction (embedding + TF-IDF + metadata), training data preparation
- **Deliverables**:
  - `tools/ml_routing/feature_extractor.py` (TaskFeatureVector, extraction pipeline)
  - `tools/ml_routing/training_data_preparer.py` (VectorStore query, quality filters)
  - Unit tests (10+ tests, feature extraction, data quality)
- **Success Criteria**: 1,000 training samples extracted with >90% high-confidence labels

### Phase 2: Model Training & Validation (Week 1, Day 4-5)

- **Scope**: RandomForest training, ensemble, 5-fold CV, validation
- **Deliverables**:
  - `tools/ml_routing/model_trainer.py` (EnsembleModel, training pipeline)
  - Model serialization (`~/.agency/models/routing_classifier_v1.pkl`)
  - Unit tests (10+ tests, training, validation, false negative rate)
- **Success Criteria**: Validation accuracy >98%, false negative rate <2%

### Phase 3: Inference Integration (Week 2, Day 1-2)

- **Scope**: MLClassifier, HybridExecutor integration, rule-based fallback
- **Deliverables**:
  - `tools/ml_routing/ml_classifier.py` (classification, confidence thresholding)
  - HybridExecutor updates (ML-first routing, fallback to Leap 4)
  - Integration tests (5+ tests, end-to-end classification)
- **Success Criteria**: Classification latency <50ms p99, graceful degradation

### Phase 4: Online Learning & Retraining (Week 2, Day 3-4)

- **Scope**: Weekly retraining pipeline, A/B testing, automated deployment
- **Deliverables**:
  - `tools/ml_routing/online_learning_pipeline.py` (retraining, A/B test)
  - Cron job configuration (weekly retraining schedule)
  - Integration tests (3+ tests, retraining, deployment, rollback)
- **Success Criteria**: Retraining completes <5min, new model deployed if +0.5% accuracy

### Phase 5: Explainability & Monitoring (Week 2, Day 5)

- **Scope**: SHAP integration, dashboard, CLI command
- **Deliverables**:
  - `tools/ml_routing/model_explainer.py` (SHAP explanations)
  - CLI command: `agency explain-classification <task_id>`
  - Dashboard: Feature importance, confidence distribution
- **Success Criteria**: SHAP explanation <100ms, top 10 features identified

### Phase 6: Production Validation (Week 3)

- **Scope**: A/B testing (100 tasks), accuracy measurement, cost analysis
- **Deliverables**:
  - 100-task validation set results (accuracy >98%, cost <$0.01/task)
  - ADR-025: ML Pattern Recognition Architecture Decision
  - Documentation: Leap 5 execution report
- **Success Criteria**: Production accuracy >98%, cost <$0.01/task, latency <50ms p99

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: HybridExecutor, AdaptiveRouterAgent, LearningAgent
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), MLEngineer (model architecture)

### Review Criteria

- **Completeness**: All ML components specified (training, inference, retraining, explainability)
- **Clarity**: Architecture diagrams, code examples, feature schema documented
- **Feasibility**: Scikit-learn models achievable with <5min training, <50ms inference
- **Constitutional Compliance**: Article I-V validated (especially Article IV VectorStore)
- **Quality Standards**: Accuracy >98%, cost <$0.01/task, latency <50ms p99

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **ML Architecture Approval**: Pending model selection validation
- [ ] **Final Approval**: Pending after Phase 1-2 implementation (training data + model)

---

## Appendices

### Appendix A: Glossary

- **Feature Engineering**: Process of converting raw task description into ML feature vector
- **Ensemble Model**: Combination of multiple ML models (RandomForest + GradientBoosting)
- **Online Learning**: Continuous model retraining from production feedback
- **SHAP**: SHapley Additive exPlanations, technique for ML model interpretability
- **A/B Testing**: Gradual rollout strategy (10% traffic to new model, 90% to current)

### Appendix B: References

- **Spec-004**: Quality Feedback Loop (Leap 4, rule-based classification)
- **ADR-004**: Continuous Learning and Improvement (VectorStore mandate)
- **ADR-024**: Adaptive Model Router for 90% Cost Reduction
- **Scikit-learn Docs**: RandomForestClassifier, VotingClassifier

### Appendix C: Related Documents

- **Spec**: `specs/spec-004-quality-feedback-loop.md` (Leap 4 foundation)
- **Plan**: `plan-005-advanced-pattern-recognition.md` (to be created after spec approval)
- **ADR**: `docs/adr/ADR-025-ml-pattern-recognition.md` (to be created after implementation)

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification with ML architecture, training, inference, explainability |

---

*"From rules to intelligence, from data to wisdom."*
