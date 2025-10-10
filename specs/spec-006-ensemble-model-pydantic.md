# Specification: EnsembleModel Pydantic Model

**Spec ID**: `spec-006-ensemble-model-pydantic`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Related Specs**: `spec-005-advanced-pattern-recognition.md` (Parent)
**Related Plans**: `plan-005-advanced-pattern-recognition.md` (Phase 2, Task 2.1)
**Related ADRs**: `ADR-008: Strict Typing`, `ADR-002: 100% Verification`

---

## Executive Summary

The EnsembleModel Pydantic model provides a strictly-typed, validated schema for serializing and deserializing trained ML ensemble classifiers (RandomForest + GradientBoosting) with comprehensive metadata. This specification defines the exact field types, validators, acceptance criteria, and constitutional compliance requirements for Phase 2 (Task 2.1) of Leap 5 implementation.

**Key Innovation**: Combines sklearn model serialization with Pydantic validation, ensuring >98% validation accuracy and <2% false negative rate through strict type enforcement.

---

## Goals

### Primary Goals

- **Goal 1**: Define EnsembleModel schema with 7 required fields (ensemble, rf_model, gb_model, validation_accuracy, false_negative_rate, training_date, feature_names)
- **Goal 2**: Enforce validation_accuracy ≥0.98 and false_negative_rate ≤0.02 through Pydantic validators
- **Goal 3**: Ensure compatibility with scikit-learn VotingClassifier serialization (joblib)
- **Goal 4**: Provide clear, measurable acceptance criteria for Phase 2 implementation

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Field Completeness** | 7/7 required fields | Schema validation |
| **Validator Coverage** | 100% (all critical fields) | Pydantic validator count |
| **Serialization Size** | <50MB | joblib.dump() output |
| **Validation Accuracy** | ≥0.98 (98%) | Held-out validation set |
| **False Negative Rate** | ≤0.02 (2%) | Complex task misclassification rate |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Model training logic (separate concern, see `model_trainer.py`)
- **Non-Goal 2**: Feature extraction pipeline (see `TaskFeatureVector` in spec-005)
- **Non-Goal 3**: Inference/classification logic (see `MLClassifier` in Phase 3)
- **Non-Goal 4**: Model versioning strategy (see `ModelStorage` in Task 2.2)

### Future Considerations

- **Future Enhancement 1**: Model compression techniques (quantization, pruning)
- **Future Enhancement 2**: Multi-model ensembles (XGBoost, LightGBM, etc.)
- **Future Enhancement 3**: AutoML hyperparameter tuning integration
- **Future Enhancement 4**: SHAP explainer serialization (currently computed on-demand)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: Model Training Pipeline (System Component)

- **Description**: Automated pipeline that trains ensemble models from TrainingDataset
- **Goals**: Serialize trained models with metadata, validate accuracy thresholds
- **Pain Points**: Need strict validation to prevent deploying low-accuracy models
- **Technical Proficiency**: ML pipeline engineer (automated system)

#### Persona 2: ML Classifier (Inference System)

- **Description**: Runtime classifier that loads EnsembleModel for task routing predictions
- **Goals**: Fast model loading (<1s), reliable deserialization, metadata access
- **Pain Points**: Model schema changes break inference, missing feature names
- **Technical Proficiency**: Production ML system (automated)

#### Persona 3: ML Engineer (Monitoring & Debugging)

- **Description**: Engineer analyzing model performance, investigating accuracy degradation
- **Goals**: Inspect model metadata (accuracy, FN_rate, training date), compare versions
- **Pain Points**: Need clear metadata structure, version traceability
- **Technical Proficiency**: Senior ML engineer with sklearn expertise

### User Journeys

#### Journey 1: Training Pipeline Serialization (Primary Use Case)

```
1. System starts with: Trained ensemble (RandomForest + GradientBoosting), validation metrics
2. System needs to: Serialize model with metadata, validate accuracy thresholds
3. System performs:
   - Create EnsembleModel instance with all 7 fields
   - Pydantic validates: validation_accuracy ≥0.98, false_negative_rate ≤0.02
   - If validation fails: Raise ValueError with detailed error message
   - If validation succeeds: Return validated EnsembleModel
4. System achieves:
   - EnsembleModel instance ready for serialization
   - Accuracy thresholds enforced at schema level
   - No low-quality models can be deployed
```

#### Journey 2: Inference System Deserialization (Secondary Use Case)

```
1. System starts with: Serialized model file (routing_classifier_v1.0.pkl)
2. System needs to: Load model for inference, access feature names for validation
3. System performs:
   - Deserialize EnsembleModel using joblib.load()
   - Access feature_names field (1644 dimensions)
   - Validate feature compatibility with TaskFeatureVector
   - Load ensemble classifier for predict_proba()
4. System achieves:
   - Model loaded in <1s (lazy loading)
   - Feature names validated (compatibility check)
   - Ready for production inference
```

#### Journey 3: ML Engineer Metadata Inspection (Debugging Use Case)

```
1. Engineer starts with: Routing accuracy dropped from 98.4% to 97.1%
2. Engineer needs to: Compare current model vs previous model metadata
3. Engineer performs:
   - Load current model: routing_classifier_v1.1.pkl
   - Load previous model: routing_classifier_v1.0.pkl
   - Compare validation_accuracy, false_negative_rate, training_date
   - Inspect feature_names to detect schema changes
4. Engineer achieves:
   - Identified: false_negative_rate increased from 1.8% to 2.3%
   - Root cause: Training data quality degradation
   - Action: Retrain with filtered high-confidence labels
```

---

## Acceptance Criteria

### Functional Requirements

#### Feature Component 1: Schema Definition

- **AC-1.1**: `ensemble` field typed as `sklearn.ensemble.VotingClassifier` (soft voting, RF+GB)
- **AC-1.2**: `rf_model` field typed as `sklearn.ensemble.RandomForestClassifier` (100 trees, max_depth=10)
- **AC-1.3**: `gb_model` field typed as `sklearn.ensemble.GradientBoostingClassifier` (50 estimators, lr=0.1)
- **AC-1.4**: `validation_accuracy` field typed as `float` (range: 0.0-1.0)
- **AC-1.5**: `false_negative_rate` field typed as `float` (range: 0.0-1.0)
- **AC-1.6**: `training_date` field typed as `str` (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ)
- **AC-1.7**: `feature_names` field typed as `List[str]` (exactly 1644 items)

#### Feature Component 2: Pydantic Validators

- **AC-2.1**: `@field_validator("validation_accuracy")` enforces ≥0.98 threshold
  - Raise `ValueError` if validation_accuracy < 0.98 with message: "Model accuracy {value:.3f} below 98% target (Article II violation: Insufficient verification)"
- **AC-2.2**: `@field_validator("false_negative_rate")` enforces ≤0.02 threshold
  - Raise `ValueError` if false_negative_rate > 0.02 with message: "False negative rate {value:.3f} above 2% target (Article II violation: Complex tasks at risk)"
- **AC-2.3**: `@field_validator("feature_names")` enforces exactly 1644 items
  - Raise `ValueError` if len(feature_names) != 1644 with message: "Feature names must have 1644 items (matching TaskFeatureVector), got {len(feature_names)}"
- **AC-2.4**: `@model_validator` ensures ensemble contains rf_model and gb_model
  - Validate ensemble.estimators_ includes ('rf', rf_model) and ('gb', gb_model)
  - Raise `ValueError` if model mismatch detected

#### Feature Component 3: Utility Methods

- **AC-3.1**: `to_dict()` method exports metadata (exclude sklearn models)
  - Return dict with keys: validation_accuracy, false_negative_rate, training_date, feature_names
  - Format: `{"validation_accuracy": 0.984, "false_negative_rate": 0.018, "training_date": "2025-10-10T12:00:00Z", "feature_names": [...1644 items...]}`
- **AC-3.2**: `from_dict(data: Dict)` method deserializes from metadata
  - Load metadata only (models loaded separately via joblib)
  - Validate all fields present in data dict
  - Return EnsembleModel instance with models=None (placeholder)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Serialization size <50MB (joblib.dump() output)
- **AC-P.2**: Deserialization time <1s (joblib.load() latency)
- **AC-P.3**: Pydantic validation overhead <10ms (schema validation)

#### Quality

- **AC-Q.1**: All 7 fields strictly typed (no `Any` types, ADR-008 compliance)
- **AC-Q.2**: Validators cover 100% of critical fields (accuracy, FN_rate, feature_names)
- **AC-Q.3**: Schema compatible with scikit-learn 1.3.0+ (VotingClassifier, RandomForest, GradientBoosting)

#### Security

- **AC-S.1**: No sensitive data in serialized model (only metadata + sklearn parameters)
- **AC-S.2**: Validation prevents deploying models below quality thresholds

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: All 7 fields required (no optional fields, complete model specification)
- **AC-CI.2**: Feature names validated (1644 items, matching TaskFeatureVector dimensions)
- **AC-CI.3**: Model compatibility validated (ensemble contains rf_model and gb_model)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Validation accuracy ≥0.98 enforced at schema level (no low-quality models deployed)
- **AC-CII.2**: False negative rate ≤0.02 enforced at schema level (complex tasks protected)
- **AC-CII.3**: Pydantic validators raise clear errors with constitutional references

#### Article IV: Continuous Learning and Improvement

- **AC-CIV.1**: Training date stored (temporal tracking for model versioning)
- **AC-CIV.2**: Feature names stored (schema evolution tracking)
- **AC-CIV.3**: Metadata exportable for VectorStore learning analysis

#### Article V: Spec-Driven Development

- **AC-CV.1**: Schema traced to spec-005 section 4.2.1 (ensemble model requirements)
- **AC-CV.2**: All design decisions reference plan-005 Phase 2, Task 2.1

---

## Technical Design

### 4.1 Schema Definition

```python
"""
EnsembleModel Pydantic schema for trained ML ensemble classifiers.

Constitutional compliance:
- Article I: Complete context (all 7 fields required)
- Article II: 100% verification (strict validators, accuracy thresholds)
- Article IV: VectorStore integration (metadata for learning analysis)
- Article V: Spec-driven (follows spec-006)

Reference: specs/spec-006-ensemble-model-pydantic.md
Author: PlannerAgent
Date: 2025-10-10
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any
from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier


class EnsembleModel(BaseModel):
    """
    Trained ML ensemble model with validation metadata.

    Combines RandomForest + GradientBoosting classifiers with soft voting
    for task complexity classification. Enforces >98% validation accuracy
    and <2% false negative rate through Pydantic validators.

    Fields:
    - ensemble: VotingClassifier (soft voting, RF+GB, weights=[0.7, 0.3])
    - rf_model: RandomForestClassifier (100 trees, max_depth=10)
    - gb_model: GradientBoostingClassifier (50 estimators, lr=0.1)
    - validation_accuracy: Float (≥0.98, measured on held-out validation set)
    - false_negative_rate: Float (≤0.02, complex → simple/moderate misclassifications)
    - training_date: ISO 8601 timestamp (model versioning)
    - feature_names: List[str] (1644 items, matching TaskFeatureVector)

    Constitutional Alignment:
    - Article I: All 7 fields required (complete model specification)
    - Article II: Strict validators (accuracy ≥0.98, FN_rate ≤0.02)
    - Article IV: Metadata for VectorStore learning analysis
    - Article V: Spec-driven (traceability to spec-006)

    Example:
        >>> from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
        >>> rf = RandomForestClassifier(n_estimators=100, max_depth=10)
        >>> gb = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1)
        >>> ensemble = VotingClassifier(estimators=[('rf', rf), ('gb', gb)], voting='soft', weights=[0.7, 0.3])
        >>> model = EnsembleModel(
        ...     ensemble=ensemble,
        ...     rf_model=rf,
        ...     gb_model=gb,
        ...     validation_accuracy=0.984,
        ...     false_negative_rate=0.018,
        ...     training_date="2025-10-10T12:00:00Z",
        ...     feature_names=["embedding_0", "embedding_1", ..., "historical_tier_mode"]  # 1644 items
        ... )
    """

    # Model Fields (sklearn classifiers)
    ensemble: VotingClassifier = Field(
        ...,
        description=(
            "VotingClassifier combining RandomForest + GradientBoosting with soft voting. "
            "Weights: [0.7, 0.3] (RF weighted higher for stability). "
            "Trained on TaskFeatureVector (1644-dim) with 3-class labels (simple/moderate/complex)."
        )
    )

    rf_model: RandomForestClassifier = Field(
        ...,
        description=(
            "RandomForestClassifier (primary model). "
            "Hyperparameters: n_estimators=100, max_depth=10, min_samples_split=5. "
            "Provides feature importances for SHAP explainability."
        )
    )

    gb_model: GradientBoostingClassifier = Field(
        ...,
        description=(
            "GradientBoostingClassifier (secondary model). "
            "Hyperparameters: n_estimators=50, learning_rate=0.1, max_depth=5. "
            "Complements RandomForest with boosting approach."
        )
    )

    # Validation Metrics (quality thresholds)
    validation_accuracy: float = Field(
        ...,
        ge=0.98,  # Pydantic built-in constraint
        le=1.0,
        description=(
            "Validation accuracy on held-out validation set (20% of training data). "
            "MUST be ≥0.98 (98%) to meet Article II verification requirements. "
            "Calculated as correct_predictions / total_predictions on validation set."
        )
    )

    false_negative_rate: float = Field(
        ...,
        ge=0.0,
        le=0.02,  # Pydantic built-in constraint
        description=(
            "False negative rate for complex tasks (critical metric). "
            "MUST be ≤0.02 (2%) to protect against complex → simple misclassifications. "
            "Calculated as FN_complex / (FN_complex + TP_complex) where: "
            "- FN_complex: Complex tasks predicted as simple/moderate (false negatives) "
            "- TP_complex: Complex tasks predicted correctly (true positives)"
        )
    )

    # Metadata Fields (versioning, traceability)
    training_date: str = Field(
        ...,
        description=(
            "ISO 8601 timestamp when model was trained (UTC). "
            "Format: YYYY-MM-DDTHH:MM:SSZ (e.g., '2025-10-10T12:00:00Z'). "
            "Used for model versioning and drift detection (Article IV)."
        )
    )

    feature_names: List[str] = Field(
        ...,
        description=(
            "Feature names (1644 items) matching TaskFeatureVector dimensions. "
            "Order: [embedding_0...embedding_1535, tfidf_0...tfidf_99, "
            "description_length, word_count, has_refactor, has_test, "
            "has_async, has_fix, estimated_time, historical_tier_mode]. "
            "Used for feature validation and SHAP explainability."
        )
    )

    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True  # Allow sklearn model types
        json_schema_extra = {
            "example": {
                "ensemble": "VotingClassifier(estimators=[('rf', RandomForestClassifier()), ('gb', GradientBoostingClassifier())], voting='soft', weights=[0.7, 0.3])",
                "rf_model": "RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5)",
                "gb_model": "GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, max_depth=5)",
                "validation_accuracy": 0.984,
                "false_negative_rate": 0.018,
                "training_date": "2025-10-10T12:00:00Z",
                "feature_names": ["embedding_0", "embedding_1", "...", "historical_tier_mode"]  # 1644 items
            },
            "description": (
                "EnsembleModel: Trained ML ensemble (RandomForest + GradientBoosting) "
                "with validation metadata. Enforces >98% accuracy and <2% false negative rate. "
                "Constitutional compliance: Article I (complete context), Article II (100% verification)."
            )
        }

    @field_validator("validation_accuracy")
    @classmethod
    def validate_accuracy_threshold(cls, v: float) -> float:
        """
        Enforce validation accuracy ≥0.98 (98%) threshold.

        Article II compliance: 100% verification before deployment.

        Args:
            v: Validation accuracy to validate

        Returns:
            Validated accuracy (≥0.98)

        Raises:
            ValueError: If accuracy below 98% threshold
        """
        if v < 0.98:
            raise ValueError(
                f"Model accuracy {v:.3f} below 98% target. "
                f"Article II violation: Insufficient verification. "
                f"Models must achieve ≥98% validation accuracy before deployment. "
                f"Consider: (1) Collect more training data, (2) Improve feature engineering, "
                f"(3) Tune hyperparameters with GridSearchCV."
            )
        return v

    @field_validator("false_negative_rate")
    @classmethod
    def validate_fn_rate_threshold(cls, v: float) -> float:
        """
        Enforce false negative rate ≤0.02 (2%) threshold.

        Article II compliance: Protect complex tasks from misclassification.

        Critical Metric: Complex tasks routed incorrectly to simple tier
        pose quality risks (insufficient model capacity, rushed execution).

        Args:
            v: False negative rate to validate

        Returns:
            Validated FN_rate (≤0.02)

        Raises:
            ValueError: If FN_rate above 2% threshold
        """
        if v > 0.02:
            raise ValueError(
                f"False negative rate {v:.3f} above 2% target. "
                f"Article II violation: Complex tasks at risk of misclassification. "
                f"FN_rate measures: (False Negatives Complex) / (FN_complex + TP_complex). "
                f"Consider: (1) Increase training data for complex tier, "
                f"(2) Adjust class weights to penalize FN_complex, "
                f"(3) Use cost-sensitive learning (higher cost for FN_complex)."
            )
        return v

    @field_validator("feature_names")
    @classmethod
    def validate_feature_dimensions(cls, v: List[str]) -> List[str]:
        """
        Enforce feature_names has exactly 1644 items (matching TaskFeatureVector).

        Article I compliance: Complete context validation.

        Args:
            v: Feature names list to validate

        Returns:
            Validated feature names (1644 items)

        Raises:
            ValueError: If dimension mismatch detected
        """
        expected_dim = 1644  # 1536 embedding + 100 TF-IDF + 8 metadata
        if len(v) != expected_dim:
            raise ValueError(
                f"Feature names must have {expected_dim} items (matching TaskFeatureVector), "
                f"got {len(v)}. "
                f"Article I violation: Incomplete context (feature dimension mismatch). "
                f"Expected: 1536 embedding + 100 TF-IDF + 8 metadata = 1644 total."
            )
        return v

    @field_validator("training_date")
    @classmethod
    def validate_iso8601_format(cls, v: str) -> str:
        """
        Validate training_date is ISO 8601 format.

        Article IV compliance: Temporal tracking for model versioning.

        Args:
            v: Training date string to validate

        Returns:
            Validated ISO 8601 timestamp

        Raises:
            ValueError: If date format invalid
        """
        try:
            # Parse ISO 8601 format (e.g., "2025-10-10T12:00:00Z")
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(
                f"training_date must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ), got '{v}'. "
                f"Article IV violation: Invalid timestamp format. "
                f"Example: '2025-10-10T12:00:00Z'. Error: {e}"
            )
        return v

    @model_validator(mode="after")
    def validate_ensemble_composition(self) -> "EnsembleModel":
        """
        Validate ensemble contains rf_model and gb_model.

        Article I compliance: Complete context validation.

        Ensures ensemble.estimators_ includes the exact rf_model and gb_model
        instances provided in the schema (not copies or different models).

        Returns:
            Validated EnsembleModel instance

        Raises:
            ValueError: If ensemble composition mismatch detected
        """
        # Check ensemble has exactly 2 estimators
        if len(self.ensemble.estimators_) != 2:
            raise ValueError(
                f"Ensemble must have exactly 2 estimators (rf + gb), "
                f"got {len(self.ensemble.estimators_)}. "
                f"Article I violation: Incomplete ensemble composition."
            )

        # Extract estimator names and models
        estimator_dict = dict(self.ensemble.estimators_)

        # Check 'rf' estimator exists
        if 'rf' not in estimator_dict:
            raise ValueError(
                f"Ensemble missing 'rf' (RandomForest) estimator. "
                f"Found estimators: {list(estimator_dict.keys())}. "
                f"Article I violation: Incomplete ensemble composition."
            )

        # Check 'gb' estimator exists
        if 'gb' not in estimator_dict:
            raise ValueError(
                f"Ensemble missing 'gb' (GradientBoosting) estimator. "
                f"Found estimators: {list(estimator_dict.keys())}. "
                f"Article I violation: Incomplete ensemble composition."
            )

        # Check model identity (same instances)
        if estimator_dict['rf'] is not self.rf_model:
            raise ValueError(
                f"Ensemble 'rf' estimator is not the same instance as rf_model. "
                f"Article I violation: Model identity mismatch."
            )

        if estimator_dict['gb'] is not self.gb_model:
            raise ValueError(
                f"Ensemble 'gb' estimator is not the same instance as gb_model. "
                f"Article I violation: Model identity mismatch."
            )

        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Export metadata to dictionary (exclude sklearn models).

        Used for:
        - JSON serialization (models too large for JSON)
        - VectorStore learning analysis (Article IV)
        - Model comparison (debugging, drift detection)

        Returns:
            Dictionary with metadata fields (4 keys)

        Example:
            >>> model = EnsembleModel(...)
            >>> metadata = model.to_dict()
            >>> metadata.keys()
            dict_keys(['validation_accuracy', 'false_negative_rate', 'training_date', 'feature_names'])
        """
        return {
            "validation_accuracy": self.validation_accuracy,
            "false_negative_rate": self.false_negative_rate,
            "training_date": self.training_date,
            "feature_names": self.feature_names
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnsembleModel":
        """
        Deserialize metadata from dictionary (models loaded separately).

        Used for:
        - JSON deserialization (models loaded via joblib)
        - Metadata-only operations (comparison, versioning)

        Note: Requires models to be loaded separately via joblib.load()
        and then added to the returned instance.

        Args:
            data: Dictionary with metadata fields (4 keys minimum)

        Returns:
            EnsembleModel instance with models=None (placeholders)

        Raises:
            ValueError: If required fields missing

        Example:
            >>> import joblib
            >>> metadata = {"validation_accuracy": 0.984, ...}
            >>> model = EnsembleModel.from_dict(metadata)
            >>> # Load sklearn models separately
            >>> model.ensemble = joblib.load("ensemble.pkl")
            >>> model.rf_model = joblib.load("rf_model.pkl")
            >>> model.gb_model = joblib.load("gb_model.pkl")
        """
        required_fields = {"validation_accuracy", "false_negative_rate", "training_date", "feature_names"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(
                f"Missing required fields in metadata: {missing_fields}. "
                f"Required: {required_fields}. "
                f"Article I violation: Incomplete context (metadata missing)."
            )

        # Create placeholder models (to be loaded separately)
        # Note: This will fail validators if used before loading actual models
        return cls(
            ensemble=None,  # type: ignore (placeholder, loaded separately)
            rf_model=None,  # type: ignore (placeholder, loaded separately)
            gb_model=None,  # type: ignore (placeholder, loaded separately)
            validation_accuracy=data["validation_accuracy"],
            false_negative_rate=data["false_negative_rate"],
            training_date=data["training_date"],
            feature_names=data["feature_names"]
        )
```

### 4.2 Example Usage

#### Example 1: Training Pipeline (Model Creation)

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from datetime import datetime
from shared.models.ensemble_model import EnsembleModel

# Step 1: Train models (Phase 2, Task 2.1)
rf = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5, random_state=42)
gb = GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, max_depth=5, random_state=42)

rf.fit(X_train, y_train)
gb.fit(X_train, y_train)

# Step 2: Create ensemble
ensemble = VotingClassifier(
    estimators=[('rf', rf), ('gb', gb)],
    voting='soft',
    weights=[0.7, 0.3]
)
ensemble.fit(X_train, y_train)

# Step 3: Calculate validation metrics
y_pred = ensemble.predict(X_val)
validation_accuracy = (y_pred == y_val).mean()  # e.g., 0.984

# False negative rate for complex tier
complex_label = 2  # 0=simple, 1=moderate, 2=complex
true_complex_indices = [i for i, label in enumerate(y_val) if label == complex_label]
false_negatives = sum(1 for i in true_complex_indices if y_pred[i] != complex_label)
false_negative_rate = false_negatives / len(true_complex_indices) if true_complex_indices else 0.0

# Step 4: Create EnsembleModel (Pydantic validates thresholds)
try:
    model = EnsembleModel(
        ensemble=ensemble,
        rf_model=rf,
        gb_model=gb,
        validation_accuracy=validation_accuracy,  # ≥0.98 enforced
        false_negative_rate=false_negative_rate,  # ≤0.02 enforced
        training_date=datetime.now().isoformat() + "Z",
        feature_names=feature_names  # 1644 items
    )
    print("✅ Model validation passed")
except ValueError as e:
    print(f"❌ Model validation failed: {e}")
    # Retrain or adjust hyperparameters
```

#### Example 2: Model Serialization (Storage)

```python
import joblib
from pathlib import Path

# Save model to disk (Task 2.2)
model_path = Path("~/.agency/models/routing_classifier_v1.0.pkl").expanduser()
joblib.dump(model, model_path)

# Save metadata separately (JSON)
metadata_path = model_path.with_suffix(".json")
import json
with open(metadata_path, "w") as f:
    json.dump(model.to_dict(), f, indent=2)

print(f"✅ Model saved: {model_path} ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"✅ Metadata saved: {metadata_path}")
```

#### Example 3: Model Deserialization (Inference)

```python
import joblib
from pathlib import Path
from shared.models.ensemble_model import EnsembleModel

# Load model from disk (Phase 3, Task 3.1)
model_path = Path("~/.agency/models/routing_classifier_v1.0.pkl").expanduser()
model: EnsembleModel = joblib.load(model_path)

# Access model components
print(f"Validation accuracy: {model.validation_accuracy:.3f}")
print(f"False negative rate: {model.false_negative_rate:.3f}")
print(f"Training date: {model.training_date}")
print(f"Feature dimensions: {len(model.feature_names)}")

# Use for inference
X_test_flat = test_feature_vector.to_flat_array()  # 1644-dim
y_proba = model.ensemble.predict_proba([X_test_flat])[0]
predicted_tier = ["simple", "moderate", "complex"][y_proba.argmax()]
confidence = y_proba.max()

print(f"Prediction: {predicted_tier} (confidence={confidence:.3f})")
```

#### Example 4: Validation Failure (Accuracy Below Threshold)

```python
from shared.models.ensemble_model import EnsembleModel

# Attempt to create model with low accuracy
try:
    model = EnsembleModel(
        ensemble=ensemble,
        rf_model=rf,
        gb_model=gb,
        validation_accuracy=0.96,  # ❌ Below 0.98 threshold
        false_negative_rate=0.018,
        training_date="2025-10-10T12:00:00Z",
        feature_names=feature_names
    )
except ValueError as e:
    print(f"❌ Validation failed: {e}")
    # Output:
    # ❌ Validation failed: Model accuracy 0.960 below 98% target.
    #    Article II violation: Insufficient verification.
    #    Models must achieve ≥98% validation accuracy before deployment.
    #    Consider: (1) Collect more training data, (2) Improve feature engineering,
    #    (3) Tune hyperparameters with GridSearchCV.
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `scikit-learn>=1.3.0` - RandomForest, GradientBoosting, VotingClassifier
- **Dependency 2**: `pydantic>=2.0.0` - Schema validation, field validators
- **Dependency 3**: `joblib>=1.3.0` - Model serialization/deserialization
- **Dependency 4**: `TaskFeatureVector` (spec-005) - Feature schema compatibility

### External Dependencies

- **External Dep 1**: Training pipeline (Phase 2, Task 2.1) - Provides trained sklearn models
- **External Dep 2**: ModelStorage (Phase 2, Task 2.2) - Handles versioning and file I/O

### Technical Constraints

- **Constraint 1**: Serialization size <50MB (fast loading, fits in memory)
- **Constraint 2**: Feature names must match TaskFeatureVector (1644 dimensions)
- **Constraint 3**: sklearn version compatibility (1.3.0+ required for VotingClassifier soft voting)

### Business Constraints

- **Constraint 1**: Validation accuracy ≥0.98 (quality threshold)
- **Constraint 2**: False negative rate ≤0.02 (complex task protection)
- **Constraint 3**: No manual threshold overrides (constitutional enforcement)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Validation thresholds too strict** (98% accuracy hard to achieve) - *Mitigation*: Collect 1,000+ high-quality training samples, use 5-fold CV for robust validation
- **Risk 2**: **Schema evolution breaks compatibility** (feature dimension changes) - *Mitigation*: Version schema with major/minor versioning, feature name validation enforces backward compatibility

### Medium Risk Items

- **Risk 3**: **Serialization size >50MB** (slow loading) - *Mitigation*: Use joblib compression (compress=3), test with max_depth=10 (avoids overly deep trees)
- **Risk 4**: **Pydantic validation overhead** (>10ms latency) - *Mitigation*: Use Pydantic v2 (Rust backend), validators only run once during instantiation (not inference)

### Low Risk Items

- **Risk 5**: **sklearn version incompatibility** (VotingClassifier API changes) - *Mitigation*: Pin scikit-learn>=1.3.0, test with multiple versions
- **Risk 6**: **Metadata corruption** (JSON serialization issues) - *Mitigation*: Use structured to_dict() method, validate before saving

### Constitutional Risks

- **Constitutional Risk 1**: **Article II violation** (low-accuracy models deployed) - *Mitigation*: Pydantic validators enforce thresholds at schema level (cannot be bypassed)
- **Constitutional Risk 2**: **Article I violation** (incomplete model specification) - *Mitigation*: All 7 fields required, model_validator ensures ensemble composition

---

## Integration Points

### Agent Integration

- **ModelTrainer (Phase 2, Task 2.1)**: Creates EnsembleModel instances after training
- **ModelStorage (Phase 2, Task 2.2)**: Serializes/deserializes EnsembleModel with versioning
- **MLClassifier (Phase 3, Task 3.1)**: Loads EnsembleModel for inference

### System Integration

- **VectorStore**: Stores model metadata (to_dict()) for learning analysis (Article IV)
- **Telemetry**: Logs model validation metrics (accuracy, FN_rate, training date)

### External Integration

- **scikit-learn**: VotingClassifier, RandomForest, GradientBoosting serialization

---

## Testing Strategy

### Test Categories

- **Unit Tests** (15+ tests): Field validation, Pydantic validators, utility methods
- **Integration Tests** (5+ tests): Training pipeline → EnsembleModel → serialization → deserialization
- **Constitutional Compliance Tests** (5+ tests): Article I, II, IV validators

### Test Coverage Requirements

- **Test Coverage 1**: All 4 Pydantic field validators (accuracy, FN_rate, feature_names, training_date)
- **Test Coverage 2**: model_validator (ensemble composition validation)
- **Test Coverage 3**: to_dict() and from_dict() methods
- **Test Coverage 4**: Serialization/deserialization roundtrip

### Example Test Cases

```python
import pytest
from shared.models.ensemble_model import EnsembleModel

def test_validation_accuracy_threshold():
    """Test AC-2.1: Validation accuracy ≥0.98 enforced."""
    with pytest.raises(ValueError, match="Model accuracy .* below 98% target"):
        EnsembleModel(
            ensemble=mock_ensemble,
            rf_model=mock_rf,
            gb_model=mock_gb,
            validation_accuracy=0.96,  # ❌ Below threshold
            false_negative_rate=0.018,
            training_date="2025-10-10T12:00:00Z",
            feature_names=["f1"] * 1644
        )

def test_false_negative_rate_threshold():
    """Test AC-2.2: False negative rate ≤0.02 enforced."""
    with pytest.raises(ValueError, match="False negative rate .* above 2% target"):
        EnsembleModel(
            ensemble=mock_ensemble,
            rf_model=mock_rf,
            gb_model=mock_gb,
            validation_accuracy=0.984,
            false_negative_rate=0.025,  # ❌ Above threshold
            training_date="2025-10-10T12:00:00Z",
            feature_names=["f1"] * 1644
        )

def test_feature_names_dimension():
    """Test AC-2.3: Feature names exactly 1644 items."""
    with pytest.raises(ValueError, match="Feature names must have 1644 items"):
        EnsembleModel(
            ensemble=mock_ensemble,
            rf_model=mock_rf,
            gb_model=mock_gb,
            validation_accuracy=0.984,
            false_negative_rate=0.018,
            training_date="2025-10-10T12:00:00Z",
            feature_names=["f1"] * 1000  # ❌ Wrong dimension
        )

def test_ensemble_composition_validation():
    """Test AC-2.4: Ensemble contains rf_model and gb_model."""
    # Create mismatched models
    wrong_rf = RandomForestClassifier()

    with pytest.raises(ValueError, match="Model identity mismatch"):
        EnsembleModel(
            ensemble=VotingClassifier(estimators=[('rf', wrong_rf), ('gb', mock_gb)]),
            rf_model=mock_rf,  # ❌ Different instance
            gb_model=mock_gb,
            validation_accuracy=0.984,
            false_negative_rate=0.018,
            training_date="2025-10-10T12:00:00Z",
            feature_names=["f1"] * 1644
        )

def test_to_dict_metadata_export():
    """Test AC-3.1: to_dict() exports metadata (exclude sklearn models)."""
    model = EnsembleModel(...)  # Valid model
    metadata = model.to_dict()

    assert "validation_accuracy" in metadata
    assert "false_negative_rate" in metadata
    assert "training_date" in metadata
    assert "feature_names" in metadata
    assert len(metadata) == 4  # Only 4 keys (no sklearn models)
```

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: ModelTrainer (Phase 2), MLClassifier (Phase 3)
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), PlannerAgent (spec-plan alignment)

### Review Criteria

- **Completeness**: All 7 fields specified with types, validators, descriptions
- **Clarity**: Example usage, error messages, constitutional references
- **Feasibility**: Pydantic validators achievable, sklearn compatibility verified
- **Constitutional Compliance**: Articles I, II, IV validated
- **Quality Standards**: Accuracy ≥0.98, FN_rate ≤0.02 enforced at schema level

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Schema Validation**: Pending Pydantic field validator implementation
- [ ] **Final Approval**: Pending after Phase 2, Task 2.1 implementation

---

## Appendices

### Appendix A: Glossary

- **Ensemble Model**: Combination of multiple ML models (RandomForest + GradientBoosting)
- **Soft Voting**: Averaging class probabilities from multiple models (vs hard voting = majority class)
- **False Negative Rate**: Proportion of complex tasks incorrectly predicted as simple/moderate
- **Validation Accuracy**: Accuracy on held-out validation set (never used for training)
- **Feature Names**: List of feature identifiers (1644 items) for SHAP explainability

### Appendix B: References

- **Spec-005**: Advanced Pattern Recognition (Leap 5, Section 4.2.1 - EnsembleModel requirements)
- **Plan-005**: Advanced Pattern Recognition (Phase 2, Task 2.1 - Model Training)
- **ADR-008**: Strict Typing (no Dict[Any, Any], explicit Pydantic models)
- **ADR-002**: 100% Verification (accuracy ≥0.98, FN_rate ≤0.02)
- **TaskFeatureVector**: spec-005 Section 5.3 (1644-dimension feature vector)

### Appendix C: Constitutional Alignment

| Article | Requirement | Implementation |
|---------|------------|----------------|
| **Article I** | Complete context before action | All 7 fields required, feature names validated (1644 items) |
| **Article II** | 100% verification | Validators enforce accuracy ≥0.98, FN_rate ≤0.02 |
| **Article III** | Automated enforcement | Pydantic validators cannot be bypassed (schema-level enforcement) |
| **Article IV** | Continuous learning | Metadata exportable (to_dict()), training date tracked |
| **Article V** | Spec-driven development | Schema traced to spec-006, all decisions reference plan-005 |

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification: EnsembleModel schema, validators, acceptance criteria |

---

*"In validation we trust, in quality we excel, in accuracy we protect."*
