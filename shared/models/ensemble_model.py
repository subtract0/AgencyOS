"""
EnsembleModel Pydantic schema for trained ML ensemble classifiers.

Constitutional compliance:
- Article I: Complete context (all 7 fields required)
- Article II: 100% verification (strict validators, accuracy thresholds)
- Article IV: VectorStore integration (metadata for learning analysis)
- Article V: Spec-driven (follows spec-006-ensemble-model-pydantic.md)

Reference: specs/spec-006-ensemble-model-pydantic.md
Author: CodeAgent
Date: 2025-10-10
"""

from datetime import datetime
from typing import Any

import sklearn
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)


class EnsembleModel(BaseModel):
    """
    Trained ML ensemble model with validation metadata.

    Combines RandomForest + GradientBoosting classifiers with soft voting
    for task complexity classification. Enforces >98% validation accuracy
    and <2% false negative rate through Pydantic validators.

    Fields:
        ensemble: VotingClassifier (soft voting, RF+GB, weights=[0.7, 0.3])
        rf_model: RandomForestClassifier (100 trees, max_depth=10)
        gb_model: GradientBoostingClassifier (50 estimators, lr=0.1)
        validation_accuracy: Float (≥0.98, measured on held-out validation set)
        false_negative_rate: Float (≤0.02, complex → simple/moderate misclassifications)
        training_date: ISO 8601 timestamp (model versioning)
        feature_names: List[str] (1644 items, matching TaskFeatureVector)

    Constitutional Alignment:
        Article I: All 7 fields required (complete model specification)
        Article II: Strict validators (accuracy ≥0.98, FN_rate ≤0.02)
        Article IV: Metadata for VectorStore learning analysis
        Article V: Spec-driven (traceability to spec-006)

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
        ),
    )

    rf_model: RandomForestClassifier = Field(
        ...,
        description=(
            "RandomForestClassifier (primary model). "
            "Hyperparameters: n_estimators=100, max_depth=10, min_samples_split=5. "
            "Provides feature importances for SHAP explainability."
        ),
    )

    gb_model: GradientBoostingClassifier = Field(
        ...,
        description=(
            "GradientBoostingClassifier (secondary model). "
            "Hyperparameters: n_estimators=50, learning_rate=0.1, max_depth=5. "
            "Complements RandomForest with boosting approach."
        ),
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
        ),
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
        ),
    )

    # Metadata Fields (versioning, traceability)
    training_date: str = Field(
        ...,
        description=(
            "ISO 8601 timestamp when model was trained (UTC). "
            "Format: YYYY-MM-DDTHH:MM:SSZ (e.g., '2025-10-10T12:00:00Z'). "
            "Used for model versioning and drift detection (Article IV)."
        ),
    )

    feature_names: list[str] = Field(
        ...,
        description=(
            "Feature names (1644 items) matching TaskFeatureVector dimensions. "
            "Order: [embedding_0...embedding_1535, tfidf_0...tfidf_99, "
            "description_length, word_count, has_refactor, has_test, "
            "has_async, has_fix, estimated_time, historical_tier_mode]. "
            "Used for feature validation and SHAP explainability."
        ),
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow sklearn model types
        json_schema_extra={
            "example": {
                "ensemble": "VotingClassifier(estimators=[('rf', RandomForestClassifier()), ('gb', GradientBoostingClassifier())], voting='soft', weights=[0.7, 0.3])",
                "rf_model": "RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5)",
                "gb_model": "GradientBoostingClassifier(n_estimators=50, learning_rate=0.1, max_depth=5)",
                "validation_accuracy": 0.984,
                "false_negative_rate": 0.018,
                "training_date": "2025-10-10T12:00:00Z",
                "feature_names": ["embedding_0", "embedding_1", "...", "historical_tier_mode"],
            },
            "description": (
                "EnsembleModel: Trained ML ensemble (RandomForest + GradientBoosting) "
                "with validation metadata. Enforces >98% accuracy and <2% false negative rate. "
                "Constitutional compliance: Article I (complete context), Article II (100% verification)."
            ),
        },
    )

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
                "Article II violation: Insufficient verification. "
                "Models must achieve ≥98% validation accuracy before deployment. "
                "Consider: (1) Collect more training data, (2) Improve feature engineering, "
                "(3) Tune hyperparameters with GridSearchCV."
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
                "Article II violation: Complex tasks at risk of misclassification. "
                "FN_rate measures: (False Negatives Complex) / (FN_complex + TP_complex). "
                "Consider: (1) Increase training data for complex tier, "
                "(2) Adjust class weights to penalize FN_complex, "
                "(3) Use cost-sensitive learning (higher cost for FN_complex)."
            )
        return v

    @field_validator("feature_names")
    @classmethod
    def validate_feature_dimensions(cls, v: list[str]) -> list[str]:
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
                "Article I violation: Incomplete context (feature dimension mismatch). "
                "Expected: 1536 embedding + 100 TF-IDF + 8 metadata = 1644 total."
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
                "Article IV violation: Invalid timestamp format. "
                f"Example: '2025-10-10T12:00:00Z'. Error: {e}"
            )
        return v

    @model_validator(mode="after")
    def validate_ensemble_composition(self) -> "EnsembleModel":
        """
        Validate ensemble contains rf_model and gb_model.

        Article I compliance: Complete context validation.

        Ensures ensemble was constructed with RandomForest and GradientBoosting
        estimators, and that the provided rf_model and gb_model have compatible
        types and parameters.

        Returns:
            Validated EnsembleModel instance

        Raises:
            ValueError: If ensemble composition mismatch detected
        """
        # Check ensemble has named estimators
        if not hasattr(self.ensemble, "estimators"):
            raise ValueError(
                "Ensemble must have 'estimators' attribute. "
                "Article I violation: Invalid VotingClassifier."
            )

        # Check ensemble has exactly 2 estimators
        if len(self.ensemble.estimators) != 2:
            raise ValueError(
                f"Ensemble must have exactly 2 estimators (rf + gb), "
                f"got {len(self.ensemble.estimators)}. "
                "Article I violation: Incomplete ensemble composition."
            )

        # Extract estimator names and models from estimators (not estimators_)
        estimator_dict = dict(self.ensemble.estimators)

        # Check 'rf' estimator exists
        if "rf" not in estimator_dict:
            raise ValueError(
                f"Ensemble missing 'rf' (RandomForest) estimator. "
                f"Found estimators: {list(estimator_dict.keys())}. "
                "Article I violation: Incomplete ensemble composition."
            )

        # Check 'gb' estimator exists
        if "gb" not in estimator_dict:
            raise ValueError(
                f"Ensemble missing 'gb' (GradientBoosting) estimator. "
                f"Found estimators: {list(estimator_dict.keys())}. "
                "Article I violation: Incomplete ensemble composition."
            )

        # Check model types (not identity, sklearn clones models during fit)
        if not isinstance(estimator_dict["rf"], RandomForestClassifier):
            raise ValueError(
                f"Ensemble 'rf' estimator must be RandomForestClassifier, "
                f"got {type(estimator_dict['rf']).__name__}. "
                "Article I violation: Model type mismatch."
            )

        if not isinstance(estimator_dict["gb"], GradientBoostingClassifier):
            raise ValueError(
                f"Ensemble 'gb' estimator must be GradientBoostingClassifier, "
                f"got {type(estimator_dict['gb']).__name__}. "
                "Article I violation: Model type mismatch."
            )

        # Validate provided models are correct types
        if not isinstance(self.rf_model, RandomForestClassifier):
            raise ValueError(
                f"rf_model must be RandomForestClassifier, got {type(self.rf_model).__name__}. "
                "Article I violation: Model type mismatch."
            )

        if not isinstance(self.gb_model, GradientBoostingClassifier):
            raise ValueError(
                f"gb_model must be GradientBoostingClassifier, got {type(self.gb_model).__name__}. "
                "Article I violation: Model type mismatch."
            )

        return self

    def to_dict(self) -> dict[str, Any]:
        """
        Export metadata to dictionary (exclude sklearn models).

        Used for:
        - JSON serialization (models too large for JSON)
        - VectorStore learning analysis (Article IV)
        - Model comparison (debugging, drift detection)

        Returns:
            Dictionary with metadata fields (5 keys)

        Example:
            >>> model = EnsembleModel(...)
            >>> metadata = model.to_dict()
            >>> metadata.keys()
            dict_keys(['validation_accuracy', 'false_negative_rate', 'training_date', 'feature_count', 'model_type', 'sklearn_version'])
        """
        return {
            "validation_accuracy": self.validation_accuracy,
            "false_negative_rate": self.false_negative_rate,
            "training_date": self.training_date,
            "feature_count": len(self.feature_names),
            "model_type": "RandomForest+GradientBoosting",
            "sklearn_version": sklearn.__version__,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        ensemble: VotingClassifier,
        rf_model: RandomForestClassifier,
        gb_model: GradientBoostingClassifier,
        feature_names: list[str],
    ) -> "EnsembleModel":
        """
        Deserialize metadata from dictionary (models loaded separately).

        Used for:
        - JSON deserialization (models loaded via joblib)
        - Metadata-only operations (comparison, versioning)

        Note: Requires models to be loaded separately via joblib.load()
        and passed as parameters to this method.

        Args:
            data: Dictionary with metadata fields (3 keys minimum)
            ensemble: VotingClassifier loaded via joblib
            rf_model: RandomForestClassifier loaded via joblib
            gb_model: GradientBoostingClassifier loaded via joblib
            feature_names: List of feature names (1644 items)

        Returns:
            EnsembleModel instance with validated models and metadata

        Raises:
            ValueError: If required fields missing

        Example:
            >>> import joblib
            >>> metadata = {"validation_accuracy": 0.984, ...}
            >>> ensemble = joblib.load("ensemble.pkl")
            >>> rf_model = joblib.load("rf_model.pkl")
            >>> gb_model = joblib.load("gb_model.pkl")
            >>> feature_names = joblib.load("feature_names.pkl")
            >>> model = EnsembleModel.from_dict(metadata, ensemble, rf_model, gb_model, feature_names)
        """
        required_fields = {"validation_accuracy", "false_negative_rate", "training_date"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(
                f"Missing required fields in metadata: {missing_fields}. "
                f"Required: {required_fields}. "
                "Article I violation: Incomplete context (metadata missing)."
            )

        # Create instance with loaded models and metadata
        return cls(
            ensemble=ensemble,
            rf_model=rf_model,
            gb_model=gb_model,
            validation_accuracy=data["validation_accuracy"],
            false_negative_rate=data["false_negative_rate"],
            training_date=data["training_date"],
            feature_names=feature_names,
        )
