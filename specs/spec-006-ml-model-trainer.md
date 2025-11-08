# Specification: MLModelTrainer - Ensemble Model Training for Task Routing

**Spec ID**: `spec-006-ml-model-trainer`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**: `spec-005-advanced-pattern-recognition.md` (Leap 5 Parent)
**Related Plans**: `plan-005-advanced-pattern-recognition.md` (Phase 2)
**Related ADRs**: `ADR-024: Adaptive Model Router`, `ADR-004: Continuous Learning`, `ADR-002: 100% Verification`

---

## Executive Summary

The MLModelTrainer component is Layer 4 of Leap 5's ML pipeline, responsible for training high-accuracy ensemble classifiers from prepared TrainingDataset samples. By combining RandomForest (primary) and GradientBoosting (secondary) models with soft voting, the system achieves >98% validation accuracy with <2% false negative rate for complex task detection. Training completes in <5 minutes for 1,000 samples, enabling weekly retraining without production delays.

**Key Innovation**: Constitutional compliance through strict validation gates - models that fail accuracy/FN_rate thresholds are rejected before production deployment, ensuring Article II's 100% verification mandate.

---

## Goals

### Primary Goals

- **Goal 1**: Train RandomForest + GradientBoosting ensemble achieving >98% validation accuracy (baseline: 85-90% rule-based)
- **Goal 2**: Maintain <2% false negative rate for complex task detection (critical safety metric)
- **Goal 3**: Complete training in <5 minutes for 1,000 samples (enables weekly retraining via cron)
- **Goal 4**: Provide 5-fold cross-validation metrics with stratified sampling (robust generalization assessment)

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Validation Accuracy** | >98% | Held-out validation set (20% of data) |
| **False Negative Rate** | <2% | Complex tasks (label=2) misclassified as 0 or 1 |
| **Training Time** | <5 minutes | Wall-clock time for 1,000 samples on current hardware |
| **Cross-Validation Stability** | Std dev <3% | 5-fold CV accuracy variance |
| **Model Size** | <50MB | Serialized .pkl file size |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Deep learning models (BERT, transformers) requiring GPU inference (latency >200ms)
- **Non-Goal 2**: Automated hyperparameter tuning via grid search (training time >30 minutes)
- **Non-Goal 3**: Multi-task learning (predict tier + execution time simultaneously)
- **Non-Goal 4**: Active learning with human-in-the-loop labeling

### Future Considerations

- **Future Enhancement 1**: Ensemble weight optimization via Bayesian search (current: fixed 0.7/0.3)
- **Future Enhancement 2**: Model pruning for <10MB deployment (current: 30-50MB)
- **Future Enhancement 3**: Incremental learning (update model without full retraining)
- **Future Enhancement 4**: Adversarial robustness testing (edge case detection)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Training Pipeline Orchestrator (Primary Consumer)

- **Description**: Automated system that retrains ML model weekly from VectorStore feedback
- **Goals**: >98% accuracy, <5min training time, robust to noisy labels, constitutional compliance
- **Pain Points**: Overfitting on small datasets, class imbalance (simple > moderate > complex)
- **Technical Proficiency**: Scikit-learn pipelines, Pydantic model validation, Result pattern

#### Persona 2: Model Deployment System (Secondary Consumer)

- **Description**: Service that loads trained models for inference in HybridExecutor
- **Goals**: Fast loading (<1s), compatibility validation, rollback capability
- **Pain Points**: Model schema drift, compatibility breaks, large file sizes
- **Technical Proficiency**: Model serialization (joblib), versioning, symlink management

#### Persona 3: ML Engineer (Monitoring & Debugging)

- **Description**: Human monitoring model performance, investigating accuracy drops
- **Goals**: Explainable metrics, feature importances, reproducible training
- **Pain Points**: Black-box models, lack of training logs, missing cross-validation details
- **Technical Proficiency**: Senior ML engineer with scikit-learn, SHAP, telemetry expertise

### User Journeys

#### Journey 1: Weekly Model Retraining (Primary Use Case)

```
1. Orchestrator starts with: 1,000 training samples from VectorStore (800 train, 200 val)
2. System needs to: Train ensemble model with >98% validation accuracy
3. System performs:
   - Validate TrainingDataset (train/val splits, label distribution)
   - Initialize RandomForest (100 trees, max_depth=10)
   - Initialize GradientBoosting (50 estimators, learning_rate=0.1)
   - Run 5-fold stratified cross-validation (accuracy, precision, recall)
   - Train on full training set (800 samples)
   - Create VotingClassifier (soft voting, weights=[0.7, 0.3])
   - Validate on held-out set (200 samples)
   - Calculate false_negative_rate (complex → simple/moderate misclassifications)
   - Check accuracy ≥98% and FN_rate ≤2% (Article II gates)
4. System achieves:
   - Training time: 4.2 minutes
   - CV accuracy: 97.8% ±2.1% (5 folds)
   - Validation accuracy: 98.4%
   - False negative rate: 1.8%
   - Model serialized: ~/.agency/models/routing_classifier_v1.0.pkl (32MB)
```

#### Journey 2: Model Quality Gate Rejection (Safety Scenario)

```
1. Orchestrator starts with: 500 training samples (insufficient for complex patterns)
2. System needs to: Train model but detect insufficient data quality
3. System performs:
   - Validate TrainingDataset (passes: 400 train, 100 val)
   - Initialize models and run 5-fold CV
   - Validation accuracy: 95.2% (below 98% threshold)
   - Calculate false_negative_rate: 4.5% (above 2% threshold)
   - **REJECTION**: Return Err("Model accuracy 95.2% below 98% target")
4. System achieves:
   - No model deployed (Article II compliance)
   - Error logged to telemetry: "Insufficient training data quality"
   - Human alerted: "Collect 500+ more samples before retraining"
   - Production continues with current model v0.9 (stable)
```

#### Journey 3: Model Feature Importance Analysis (Debugging Use Case)

```
1. ML Engineer starts with: Trained model v1.0 with 98.4% accuracy
2. Engineer needs to: Understand which features drive complex task predictions
3. System performs:
   - Load model from ~/.agency/models/routing_classifier_v1.0.pkl
   - Extract feature_importances_ from RandomForest
   - Sort top 20 features by importance
   - Display:
     - 1. embedding_dim_512: 0.18 (embedding semantic features)
     - 2. has_refactor_keyword: 0.12 (keyword indicators)
     - 3. description_length: 0.10 (task complexity proxy)
     - 4. historical_tier_mode: 0.09 (past similar tasks)
     - 5. tfidf_async: 0.07 (TF-IDF async keyword)
4. Engineer achieves:
   - Understanding: "Refactor keyword strongly predicts complex tier"
   - Action: "Improve TF-IDF vocabulary to include more complexity keywords"
   - Validation: "Next model v1.1 includes 'architecture', 'design', 'ADR' keywords"
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Ensemble Model Training

- **AC-1.1**: RandomForestClassifier configured with 100 trees, max_depth=10, min_samples_split=5, n_jobs=-1
- **AC-1.2**: GradientBoostingClassifier configured with 50 estimators, learning_rate=0.1, max_depth=5
- **AC-1.3**: VotingClassifier with soft voting, weights=[0.7 (RF), 0.3 (GB)]
- **AC-1.4**: Class weight balancing: `class_weight="balanced"` for RandomForest (handles imbalanced tiers)
- **AC-1.5**: Random state=42 for reproducibility across retraining runs

#### Feature Component 2: Cross-Validation & Evaluation

- **AC-2.1**: 5-fold stratified cross-validation (balanced tier distribution per fold)
- **AC-2.2**: Metrics computed per fold: accuracy, precision, recall, F1-score
- **AC-2.3**: Cross-validation mean and std dev logged (assess generalization stability)
- **AC-2.4**: Held-out validation set (20% of TrainingDataset) never used for training
- **AC-2.5**: False negative rate calculated: FN_complex / (FN_complex + TP_complex) where label=2

#### Feature Component 3: Quality Gates (Article II)

- **AC-3.1**: Validation accuracy threshold: ≥98% (reject model if below)
- **AC-3.2**: False negative rate threshold: ≤2% (reject model if above)
- **AC-3.3**: Training time budget: <5 minutes (for 1,000 samples, fail if timeout)
- **AC-3.4**: Model size limit: <50MB serialized (warn if exceeded, continue)
- **AC-3.5**: Result pattern: Return `Err(str)` if any quality gate fails (no exception throwing)

#### Feature Component 4: Model Output

- **AC-4.1**: EnsembleModel Pydantic model with typed fields (ensemble, rf_model, gb_model, metadata)
- **AC-4.2**: Validation accuracy stored in model metadata (traceability)
- **AC-4.3**: False negative rate stored in model metadata (critical safety metric)
- **AC-4.4**: Training date (ISO 8601 UTC) stored for versioning
- **AC-4.5**: Feature names stored for SHAP explainability (1644-dim array)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Training time <5 minutes for 1,000 samples (n_jobs=-1 parallelism on 8-core current hardware)
- **AC-P.2**: Memory usage <8GB peak during training (fits in 16GB current hardware with safety margin)
- **AC-P.3**: Model size <50MB serialized (fast loading <1s in production)
- **AC-P.4**: Cross-validation time <3 minutes (5 folds, no excessive overhead)

#### Quality

- **AC-Q.1**: Validation accuracy >98% (measured on held-out 20% validation set)
- **AC-Q.2**: False negative rate <2% (complex tasks correctly classified as complex)
- **AC-Q.3**: Cross-validation stability: std dev <3% (robust across different data splits)
- **AC-Q.4**: Feature importance extraction: Top 20 features with importance scores >0.01

#### Reliability

- **AC-R.1**: Graceful degradation: Return Err() on training failure, never crash orchestrator
- **AC-R.2**: Timeout handling: Training aborted if >10 minutes (2x budget), return Err()
- **AC-R.3**: Input validation: TrainingDataset validated before training (Article I complete context)
- **AC-R.4**: Reproducibility: Same TrainingDataset + random_state=42 → identical model metrics

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: TrainingDataset validated before training (train/val splits, label distribution, no overlaps)
- **AC-CI.2**: All 5 CV folds complete before computing mean accuracy (no partial results)
- **AC-CI.3**: Validation set 100% evaluated (never skip samples, even on timeout)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Validation accuracy ≥98% enforced before model deployment
- **AC-CII.2**: False negative rate ≤2% enforced (complex task safety)
- **AC-CII.3**: Training tests: 10+ unit tests covering happy path, edge cases, quality gate rejections
- **AC-CII.4**: Integration tests: 5+ end-to-end tests with real TrainingDataset samples

#### Article III: Automated Merge Enforcement

- **AC-CIII.1**: Quality gates cannot be bypassed (no env var flags to disable thresholds)
- **AC-CIII.2**: Failed training → Err() return, never deploy low-quality model

#### Article IV: Continuous Learning and Improvement

- **AC-CIV.1**: Training metrics stored in VectorStore (CV scores, validation accuracy, FN_rate)
- **AC-CIV.2**: Feature importances logged for pattern analysis (top 20 features)
- **AC-CIV.3**: Training data source tagged (VectorStore quality feedback, Article IV sourced)
- **AC-CIV.4**: Model versioning: Semantic versioning (v1.0, v1.1, v2.0) for retraining tracking

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation follows Spec-005 Section 4.2.2 (ML model training architecture)
- **AC-CV.2**: Traceability: Code comments reference this spec (spec-006-ml-model-trainer.md)
- **AC-CV.3**: Model schema versioned (breaking changes require new spec version)

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  MLModelTrainer (Layer 4: Model Training)                           │
│                                                                     │
│  Input: TrainingDataset (1644-dim features, 3-class labels)        │
│         ↓                                                           │
│  ┌──────────────────┐    ┌──────────────────┐                      │
│  │ RandomForest     │    │ GradientBoosting │                      │
│  │ (Primary)        │    │ (Secondary)      │                      │
│  │                  │    │                  │                      │
│  │ - 100 trees      │    │ - 50 estimators  │                      │
│  │ - max_depth=10   │    │ - lr=0.1         │                      │
│  │ - balanced       │    │ - max_depth=5    │                      │
│  └────────┬─────────┘    └────────┬─────────┘                      │
│           │                       │                                │
│           └───────────┬───────────┘                                │
│                       ↓                                            │
│           ┌───────────────────────┐                                │
│           │ VotingClassifier      │                                │
│           │ (Soft Voting)         │                                │
│           │                       │                                │
│           │ weights=[0.7, 0.3]    │                                │
│           └───────────┬───────────┘                                │
│                       ↓                                            │
│           ┌───────────────────────┐                                │
│           │ Quality Gates         │                                │
│           │ - Accuracy ≥98%       │                                │
│           │ - FN_rate ≤2%         │                                │
│           │ - Time <5min          │                                │
│           └───────────┬───────────┘                                │
│                       ↓                                            │
│  Output: Result[EnsembleModel, str]                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Class Design

#### MLModelTrainer

```python
class MLModelTrainer:
    """
    Train ensemble model for task complexity classification.

    Constitutional Compliance:
    - Article I: Complete context (all CV folds complete, validation 100%)
    - Article II: Quality gates (accuracy ≥98%, FN_rate ≤2%)
    - Article IV: Metrics stored in VectorStore
    - Article V: Spec-driven (traces to spec-006)

    Example:
        >>> from tools.ml_routing.training_data_preparer import TrainingDataPreparer
        >>> from tools.ml_routing.model_trainer import MLModelTrainer

        >>> preparer = TrainingDataPreparer(context)
        >>> dataset_result = preparer.prepare_training_data(min_confidence=0.7)
        >>> dataset = dataset_result.unwrap()

        >>> trainer = MLModelTrainer()
        >>> model_result = trainer.train_ensemble_model(dataset, random_state=42)

        >>> if model_result.is_ok():
        ...     model = model_result.unwrap()
        ...     print(f"Accuracy: {model.validation_accuracy:.3f}")
        ...     print(f"FN_rate: {model.false_negative_rate:.3f}")
        ... else:
        ...     print(f"Training failed: {model_result.unwrap_err()}")
    """

    def __init__(self):
        """Initialize MLModelTrainer with default configuration."""
        self.rf_config = RF_CONFIG
        self.gb_config = GB_CONFIG
        self.voting_config = VOTING_CONFIG
        self.logger = logging.getLogger(__name__)

    def train_ensemble_model(
        self,
        dataset: TrainingDataset,
        random_state: int = 42
    ) -> Result[EnsembleModel, str]:
        """
        Train RandomForest + GradientBoosting ensemble model.

        Steps:
        1. Validate TrainingDataset (Article I: complete context)
        2. Initialize RandomForest (100 trees, max_depth=10)
        3. Initialize GradientBoosting (50 estimators, lr=0.1)
        4. Run 5-fold stratified CV (accuracy, precision, recall)
        5. Train both models on full training set
        6. Create VotingClassifier (soft voting, weights=[0.7, 0.3])
        7. Validate on held-out validation set
        8. Calculate false_negative_rate (complex → simple/moderate)
        9. Check quality gates (accuracy ≥98%, FN_rate ≤2%)
        10. Return Result[EnsembleModel, str]

        Args:
            dataset: TrainingDataset with train/val splits
            random_state: Random seed for reproducibility (default: 42)

        Returns:
            Ok(EnsembleModel) if validation passes
            Err(str) if accuracy <98% or FN_rate >2%

        Performance:
            - Training time: <5 minutes for 1,000 samples
            - Memory usage: <8GB peak
            - Model size: <50MB serialized

        Constitutional Compliance:
            - Article I: All CV folds complete before returning
            - Article II: Quality gates enforced (no bypass)
            - Article IV: Metrics stored in VectorStore

        Example:
            >>> trainer = MLModelTrainer()
            >>> result = trainer.train_ensemble_model(dataset)
            >>> model = result.unwrap()  # Raises if Err
            >>> print(f"Accuracy: {model.validation_accuracy:.3f}")
            98.4%
        """
        ...

    def _train_random_forest(
        self,
        X: np.ndarray,
        y: np.ndarray,
        random_state: int
    ) -> RandomForestClassifier:
        """
        Train RandomForest classifier (primary model).

        Configuration:
        - n_estimators: 100 (more trees = better accuracy, longer training)
        - max_depth: 10 (prevent overfitting, balance complexity)
        - min_samples_split: 5 (require 5+ samples to split node)
        - max_features: "sqrt" (sqrt(1644) ≈ 40 features per split)
        - class_weight: "balanced" (handle imbalanced tiers)
        - n_jobs: -1 (parallelize across all CPU cores)

        Args:
            X: Feature matrix (N x 1644)
            y: Labels (N,) with values 0, 1, 2
            random_state: Random seed for reproducibility

        Returns:
            Trained RandomForestClassifier

        Performance:
            - Training time: ~3 minutes for 1,000 samples
            - Memory: ~4GB peak
        """
        ...

    def _train_gradient_boosting(
        self,
        X: np.ndarray,
        y: np.ndarray,
        random_state: int
    ) -> GradientBoostingClassifier:
        """
        Train GradientBoosting classifier (secondary model).

        Configuration:
        - n_estimators: 50 (fewer trees than RF, faster training)
        - learning_rate: 0.1 (moderate learning rate, stable convergence)
        - max_depth: 5 (shallower than RF, regularization)
        - subsample: 0.8 (80% sample per tree, prevent overfitting)

        Args:
            X: Feature matrix (N x 1644)
            y: Labels (N,) with values 0, 1, 2
            random_state: Random seed for reproducibility

        Returns:
            Trained GradientBoostingClassifier

        Performance:
            - Training time: ~1.5 minutes for 1,000 samples
            - Memory: ~2GB peak
        """
        ...

    def _create_voting_ensemble(
        self,
        rf: RandomForestClassifier,
        gb: GradientBoostingClassifier
    ) -> VotingClassifier:
        """
        Create VotingClassifier ensemble from trained models.

        Voting Strategy: Soft voting (average class probabilities)
        - RF probability: [0.1, 0.2, 0.7] (complex)
        - GB probability: [0.2, 0.3, 0.5] (complex)
        - Weighted avg: 0.7 * RF + 0.3 * GB = [0.13, 0.23, 0.64] → complex

        Weights:
        - RF: 0.7 (primary model, higher weight)
        - GB: 0.3 (secondary model, regularization)

        Args:
            rf: Trained RandomForestClassifier
            gb: Trained GradientBoostingClassifier

        Returns:
            VotingClassifier with soft voting

        Rationale:
            - Soft voting: Better than hard voting for calibrated probabilities
            - Weights 0.7/0.3: Empirically optimal (validated in Phase 1)
        """
        ...

    def _run_cross_validation(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5
    ) -> dict[str, float]:
        """
        Run stratified K-fold cross-validation.

        Metrics Computed:
        - accuracy: (TP + TN) / (TP + TN + FP + FN)
        - precision: TP / (TP + FP) per class, macro-averaged
        - recall: TP / (TP + FN) per class, macro-averaged
        - f1: 2 * (precision * recall) / (precision + recall)

        Args:
            model: Sklearn estimator (RF or GB)
            X: Feature matrix (N x 1644)
            y: Labels (N,) with values 0, 1, 2
            cv: Number of folds (default: 5)

        Returns:
            Dictionary with mean and std dev per metric:
            {
                "accuracy_mean": 0.978,
                "accuracy_std": 0.021,
                "precision_mean": 0.972,
                "precision_std": 0.019,
                "recall_mean": 0.976,
                "recall_std": 0.023,
                "f1_mean": 0.974,
                "f1_std": 0.020
            }

        Constitutional Compliance:
            - Article I: All 5 folds complete before returning
            - Stratified sampling: Balanced tier distribution per fold
        """
        ...

    def _calculate_false_negative_rate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        complex_label: int = 2
    ) -> float:
        """
        Calculate false negative rate for complex tasks.

        False Negative: Complex task predicted as simple/moderate.
        Critical metric: We MUST catch complex tasks (quality risk if misclassified).

        Formula:
            FN_rate = FN / (FN + TP)

        Where:
        - FN: Complex tasks predicted as simple/moderate
        - TP: Complex tasks correctly predicted as complex

        Args:
            y_true: Ground truth labels (N,) with values 0, 1, 2
            y_pred: Predicted labels (N,) with values 0, 1, 2
            complex_label: Label for complex tier (default: 2)

        Returns:
            False negative rate (0.0-1.0)

        Example:
            >>> y_true = [2, 2, 2, 2, 2]  # 5 complex tasks
            >>> y_pred = [2, 2, 2, 1, 0]  # 3 correct, 2 wrong
            >>> _calculate_false_negative_rate(y_true, y_pred)
            0.4  # 2 FN / (2 FN + 3 TP) = 40%

        Constitutional Compliance:
            - Article II: FN_rate ≤2% enforced before deployment
        """
        ...

    def _validate_training_data(
        self,
        dataset: TrainingDataset
    ) -> Result[None, str]:
        """
        Validate TrainingDataset before training.

        Checks:
        1. Train/val splits are non-empty
        2. Label distribution is balanced (min 50 samples per tier)
        3. Feature dimensions are consistent (1644-dim)
        4. No NaN/inf values in features
        5. Labels are valid (0, 1, 2 only)

        Args:
            dataset: TrainingDataset to validate

        Returns:
            Ok(None) if valid
            Err(str) if validation fails

        Example:
            >>> result = _validate_training_data(dataset)
            >>> if result.is_err():
            ...     print(f"Invalid dataset: {result.unwrap_err()}")

        Constitutional Compliance:
            - Article I: Complete context validation before training
        """
        ...
```

### Configuration Constants

```python
# RandomForest Configuration (Primary Model)
RF_CONFIG = {
    "n_estimators": 100,           # Number of trees (more = better, slower)
    "max_depth": 10,               # Max tree depth (prevent overfitting)
    "min_samples_split": 5,        # Min samples to split node (regularization)
    "max_features": "sqrt",        # Features per split: sqrt(1644) ≈ 40
    "n_jobs": -1,                  # Parallelize across all CPU cores
    "random_state": 42,            # Reproducibility
    "class_weight": "balanced",    # Handle imbalanced tiers
    "bootstrap": True,             # Bootstrap sampling (bagging)
    "oob_score": False,            # Out-of-bag score (disabled for speed)
    "verbose": 0                   # No training logs (quiet)
}

# GradientBoosting Configuration (Secondary Model)
GB_CONFIG = {
    "n_estimators": 50,            # Number of boosting stages (fewer than RF)
    "learning_rate": 0.1,          # Shrinkage rate (0.1 = moderate)
    "max_depth": 5,                # Max tree depth (shallower than RF)
    "subsample": 0.8,              # Subsample ratio (80% per tree)
    "random_state": 42,            # Reproducibility
    "min_samples_split": 5,        # Min samples to split node
    "min_samples_leaf": 2,         # Min samples per leaf (regularization)
    "max_features": "sqrt",        # Features per split
    "verbose": 0                   # No training logs
}

# VotingClassifier Configuration (Ensemble)
VOTING_CONFIG = {
    "voting": "soft",              # Soft voting (average class probabilities)
    "weights": [0.7, 0.3],         # [RF, GB] weights (RF primary)
    "n_jobs": -1,                  # Parallelize prediction
    "flatten_transform": True      # Flatten probability output
}

# Quality Gate Thresholds (Article II)
QUALITY_GATES = {
    "min_validation_accuracy": 0.98,      # 98% validation accuracy
    "max_false_negative_rate": 0.02,      # 2% false negative rate
    "max_training_time_seconds": 300,     # 5 minutes training budget
    "max_model_size_mb": 50,              # 50MB serialized model
    "min_cv_folds": 5,                    # 5-fold cross-validation
    "max_cv_std_dev": 0.03                # 3% CV stability (std dev)
}
```

### Pydantic Models

#### EnsembleModel

```python
class EnsembleModel(BaseModel):
    """
    Trained ensemble model with metadata.

    Represents a versioned ML model for production deployment. Includes
    trained estimators, validation metrics, and feature schema for
    explainability.

    Constitutional Alignment:
    - Article II: Validation accuracy/FN_rate stored (quality gates)
    - Article IV: Training date for VectorStore tracking
    - Article V: Feature names for SHAP explainability

    Example:
        >>> model = EnsembleModel(
        ...     ensemble=voting_clf,
        ...     rf_model=rf_clf,
        ...     gb_model=gb_clf,
        ...     validation_accuracy=0.984,
        ...     false_negative_rate=0.018,
        ...     training_date="2025-10-10T10:00:00Z",
        ...     feature_names=["embedding_0", "embedding_1", ...]
        ... )
    """

    ensemble: VotingClassifier = Field(
        ...,
        description=(
            "Trained VotingClassifier (soft voting, weights=[0.7, 0.3]). "
            "Primary inference model for production."
        )
    )

    rf_model: RandomForestClassifier = Field(
        ...,
        description=(
            "Trained RandomForestClassifier (primary model). "
            "Used for SHAP explainability (TreeExplainer)."
        )
    )

    gb_model: GradientBoostingClassifier = Field(
        ...,
        description=(
            "Trained GradientBoostingClassifier (secondary model). "
            "Provides ensemble diversity and regularization."
        )
    )

    validation_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Validation accuracy on held-out set (target: ≥0.98). "
            "Article II: Quality gate enforced before deployment."
        )
    )

    false_negative_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "False negative rate for complex tasks (target: ≤0.02). "
            "Critical safety metric: complex tasks must not be misclassified. "
            "Article II: Quality gate enforced."
        )
    )

    training_date: str = Field(
        ...,
        description=(
            "ISO 8601 UTC timestamp when model was trained. "
            "Article IV: Versioning and VectorStore tracking. "
            "Format: '2025-10-10T10:00:00Z'"
        )
    )

    feature_names: list[str] = Field(
        ...,
        description=(
            "Feature names for 1644-dim feature vector. "
            "Article V: Required for SHAP explainability. "
            "Format: ['embedding_0', ..., 'embedding_1535', 'tfidf_0', ...]"
        )
    )

    cv_metrics: dict[str, float] | None = Field(
        default=None,
        description=(
            "Cross-validation metrics (mean and std dev). "
            "Optional: {'accuracy_mean': 0.978, 'accuracy_std': 0.021, ...}"
        )
    )

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True  # Allow sklearn objects
        json_schema_extra = {
            "example": {
                "ensemble": "<VotingClassifier object>",
                "rf_model": "<RandomForestClassifier object>",
                "gb_model": "<GradientBoostingClassifier object>",
                "validation_accuracy": 0.984,
                "false_negative_rate": 0.018,
                "training_date": "2025-10-10T10:00:00Z",
                "feature_names": ["embedding_0", "embedding_1"],
                "cv_metrics": {
                    "accuracy_mean": 0.978,
                    "accuracy_std": 0.021
                }
            }
        }
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `scikit-learn>=1.3.0` - ML model training (RandomForest, GradientBoosting, VotingClassifier)
- **Dependency 2**: `numpy>=1.24.0` - Numerical computing (feature matrices, label arrays)
- **Dependency 3**: `joblib>=1.3.0` - Model serialization (save/load .pkl files)
- **Dependency 4**: `shared/models/training_dataset.py` - TrainingDataset Pydantic model (input validation)

### External Dependencies

- **External Dep 1**: TrainingDataPreparer - Provides TrainingDataset with train/val splits
- **External Dep 2**: VectorStore - Stores training metrics for Article IV learning
- **External Dep 3**: Telemetry System - Logs training events (start, complete, reject)

### Technical Constraints

- **Constraint 1**: Training time <5 minutes for 1,000 samples (weekly retraining feasible)
- **Constraint 2**: Memory usage <8GB peak during training (fits in 16GB current hardware)
- **Constraint 3**: Model size <50MB serialized (fast loading <1s in production)
- **Constraint 4**: Feature dimensionality fixed at 1644 (breaking change requires new spec)

### Business Constraints

- **Constraint 1**: Validation accuracy ≥98% (no compromise, Article II mandate)
- **Constraint 2**: False negative rate ≤2% (complex task safety, critical metric)
- **Constraint 3**: Training cost ~$0 (local scikit-learn, no GPU/API)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Overfitting on small datasets** (<500 samples) - *Mitigation*: 5-fold CV, class_weight="balanced", min 50 samples per tier
- **Risk 2**: **Class imbalance** (simple > moderate > complex) - *Mitigation*: class_weight="balanced" for RandomForest, stratified sampling

### Medium Risk Items

- **Risk 3**: **Training timeout** (>5 minutes on slow hardware) - *Mitigation*: n_jobs=-1 parallelism, timeout=600s with Err() return
- **Risk 4**: **Model drift** (accuracy degrades as task patterns evolve) - *Mitigation*: Weekly retraining, 7-day rolling accuracy monitoring

### Low Risk Items

- **Risk 5**: **Memory exhaustion** (>8GB peak on 16GB Mac) - *Mitigation*: Batched training (not needed for 1,000 samples)
- **Risk 6**: **Model corruption** (serialized .pkl file unreadable) - *Mitigation*: Checksum validation, model metadata JSON

### Constitutional Risks

- **Constitutional Risk 1**: **Article II violation** (deploy model with accuracy <98%) - *Mitigation*: Quality gates cannot be bypassed, Err() return enforced
- **Constitutional Risk 2**: **Article I violation** (incomplete CV folds)** - *Mitigation*: Assert all 5 folds complete before computing mean

---

## Integration Points

### Upstream Dependencies

- **TrainingDataPreparer**: Provides TrainingDataset with train/val splits (Layer 3)
- **FeatureExtractor**: Feature schema (1644-dim) defines model input (Layer 2)
- **VectorStore**: Stores training metrics for Article IV learning

### Downstream Consumers

- **ModelStorage**: Serializes and versions EnsembleModel for production (Layer 5)
- **MLClassifier**: Loads trained model for inference in HybridExecutor (Layer 6)
- **OnlineLearningPipeline**: Orchestrates weekly retraining from VectorStore feedback (Layer 7)

### External Integration

- **Telemetry System**: Logs training events (start, complete, reject, metrics)
- **SHAP Explainer**: Uses rf_model for feature importance analysis (Layer 8)

---

## Testing Strategy

### Test Categories

- **Unit Tests** (10+ tests): Training, cross-validation, false negative rate, quality gates
- **Integration Tests** (5+ tests): End-to-end pipeline (TrainingDataset → EnsembleModel → validation)
- **Performance Tests** (3+ tests): Training time <5min, memory <8GB, model size <50MB
- **Constitutional Compliance Tests** (3+ tests): Article I (complete context), Article II (quality gates), Article IV (metrics storage)

### Test Data Requirements

- **Test Data 1**: Mock TrainingDataset with 1,000 samples (800 train, 200 val, balanced tiers)
- **Test Data 2**: Edge case datasets (small, imbalanced, high noise)
- **Test Data 3**: Real VectorStore samples (300+ historical quality feedback records)

### Test Environment Requirements

- **Environment 1**: current hardware Mac with 16GB RAM (8 CPU cores for n_jobs=-1)
- **Environment 2**: Scikit-learn 1.3.0, numpy 1.24.0, joblib 1.3.0
- **Environment 3**: VectorStore with 1,000+ quality feedback records (Leap 4 data)

---

## Implementation Phases

### Phase 2.1: Model Training Core (Task 2.1)

**Duration**: 10 hours
**Files**: `tools/ml_routing/model_trainer.py` (~600 lines)

**Deliverables**:
- MLModelTrainer class with train_ensemble_model() method
- Helper methods: _train_random_forest(), _train_gradient_boosting(), _create_voting_ensemble()
- Configuration constants: RF_CONFIG, GB_CONFIG, VOTING_CONFIG
- Cross-validation: _run_cross_validation() with 5-fold stratified sampling
- False negative rate calculation: _calculate_false_negative_rate()
- Input validation: _validate_training_data()
- EnsembleModel Pydantic model
- 10+ unit tests (happy path, edge cases, quality gate rejections)

**Acceptance Criteria**:
- Ensemble validation accuracy >98%
- False negative rate <2%
- Training time <5 minutes for 1,000 samples
- All 10+ tests passing (100% pass rate)

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: OnlineLearningPipeline, MLClassifier, ModelStorage
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), MLEngineer (model architecture)

### Review Criteria

- **Completeness**: All training methods specified (RF, GB, ensemble, CV, FN_rate)
- **Clarity**: Configuration constants, quality gates, acceptance criteria documented
- **Feasibility**: Scikit-learn models achievable with <5min training, >98% accuracy
- **Constitutional Compliance**: Article I-V validated (especially Article II quality gates)
- **Quality Standards**: Accuracy >98%, FN_rate <2%, time <5min

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **ML Architecture Approval**: Pending model configuration validation
- [ ] **Final Approval**: Pending after Phase 2 implementation (model training complete)

---

## Appendices

### Appendix A: Glossary

- **Ensemble Model**: Combination of multiple ML models (RandomForest + GradientBoosting)
- **Soft Voting**: Average class probabilities from multiple models (vs. hard voting = majority class)
- **False Negative Rate**: Proportion of complex tasks misclassified as simple/moderate
- **Cross-Validation**: Robust evaluation technique (K-fold stratified sampling)
- **Class Weight Balancing**: Adjust class weights to handle imbalanced datasets

### Appendix B: References

- **Spec-005**: Advanced Pattern Recognition (Leap 5 Parent, Section 4.2.2)
- **Plan-005**: Implementation Plan Phase 2 (Model Training & Validation)
- **ADR-002**: 100% Verification and Stability (quality gates mandate)
- **ADR-004**: Continuous Learning (VectorStore metrics storage)
- **ADR-024**: Adaptive Model Router (cost optimization context)
- **Scikit-learn Docs**: RandomForestClassifier, GradientBoostingClassifier, VotingClassifier

### Appendix C: Related Documents

- **Spec**: `specs/spec-005-advanced-pattern-recognition.md` (Leap 5 Parent)
- **Plan**: `plans/plan-005-advanced-pattern-recognition.md` (Phase 2)
- **Models**: `shared/models/training_dataset.py` (TrainingDataset input)
- **Tests**: `tests/test_model_trainer.py` (to be created in Phase 2)

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification with ensemble architecture, quality gates, constitutional compliance |

---

*"From data to models, from validation to confidence."*
