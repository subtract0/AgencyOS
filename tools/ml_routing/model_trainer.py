"""
ML model trainer for task complexity classification.

Trains RandomForest + GradientBoosting ensemble with strict quality thresholds:
- Validation accuracy >98% (Article II requirement)
- False negative rate <2% for complex tasks (critical metric)
- 5-fold cross-validation for robustness
- <5 minute training time for 1,000 samples

Constitutional Compliance:
- Article I: Complete context (all CV folds complete, full validation set)
- Article II: 100% verification (accuracy/FN thresholds enforced)
- Article IV: VectorStore integration (training data from quality feedback)
- Article V: Spec-driven (follows spec-005 section 5.4.2)
- Law #2: Strict typing with Pydantic models
- Law #5: Result pattern for all operations
- Law #8: Functions <50 lines each

Reference: specs/spec-005-advanced-pattern-recognition.md Section 5.4
Author: AgencyOSAgent
Date: 2025-10-10
"""

import logging
import time
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_score

from shared.models.ensemble_model import EnsembleModel
from shared.models.training_dataset import TrainingDataset
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)

# Model Hyperparameters (from spec-005 section 5.2)
RF_CONFIG = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "random_state": 42,
    "n_jobs": -1,  # Parallel training
}

GB_CONFIG = {
    "n_estimators": 50,
    "learning_rate": 0.1,
    "max_depth": 5,
    "random_state": 42,
}

VOTING_CONFIG = {
    "voting": "soft",  # Average class probabilities
    "weights": [0.7, 0.3],  # RF weighted higher for stability
}

# Quality Thresholds (Article II: 100% verification)
MIN_VALIDATION_ACCURACY = 0.98  # 98%
MAX_FALSE_NEGATIVE_RATE = 0.02  # 2%
MAX_TRAINING_TIME_SECONDS = 300  # 5 minutes (informational, not blocking)


class MLModelTrainer:
    """
    Train ML ensemble model for task classification.

    Ensemble Architecture:
    - Primary: RandomForestClassifier (100 trees, max_depth=10)
    - Secondary: GradientBoostingClassifier (50 estimators, lr=0.1)
    - Voting: Soft voting (average class probabilities, weight RF=0.7, GB=0.3)

    Quality Enforcement:
    - Validation accuracy ≥98% (Article II)
    - False negative rate ≤2% for complex tasks (critical metric)
    - 5-fold cross-validation for robustness
    - Complete validation set evaluation (Article I)

    Example:
        >>> trainer = MLModelTrainer()
        >>> result = trainer.train_ensemble_model(dataset)
        >>> if result.is_ok():
        ...     model = result.unwrap()
        ...     print(f"Accuracy: {model.validation_accuracy:.3f}")
    """

    def train_ensemble_model(
        self, dataset: TrainingDataset, random_state: int = 42
    ) -> Result[EnsembleModel, str]:
        """
        Train ensemble model with 5-fold cross-validation.

        Workflow:
        1. Validate training data (Article I: complete context)
        2. Extract features and labels from train/val splits
        3. Train RandomForest (primary model)
        4. Train GradientBoosting (secondary model)
        5. Run 5-fold cross-validation for robustness
        6. Create VotingClassifier ensemble
        7. Validate on held-out validation set
        8. Calculate false negative rate for complex tier
        9. Enforce quality thresholds (Article II)
        10. Create EnsembleModel with metadata

        Args:
            dataset: TrainingDataset with train/val splits
            random_state: Random seed for reproducibility (default: 42)

        Returns:
            Result containing trained EnsembleModel or error message

        Performance Target: <5 minutes for 1,000 samples
        Quality Target: Validation accuracy >98%, FN_rate <2%
        """
        start_time = time.perf_counter()

        # Step 1: Validate training data (Article I)
        validation_result = self._validate_training_data(dataset)
        if validation_result.is_err():
            return validation_result

        # Step 2: Extract features and labels
        feature_extraction_result = self._extract_features_and_labels(dataset)
        if feature_extraction_result.is_err():
            return Err(feature_extraction_result.unwrap_err())

        X_train, y_train, X_val, y_val = feature_extraction_result.unwrap()

        logger.info(
            f"Training data extracted: {len(X_train)} train samples, "
            f"{len(X_val)} validation samples"
        )

        # Step 3: Train RandomForest (primary)
        rf_result = self._train_random_forest(X_train, y_train, random_state)
        if rf_result.is_err():
            return Err(rf_result.unwrap_err())

        rf_model = rf_result.unwrap()

        # Step 4: Train GradientBoosting (secondary)
        gb_result = self._train_gradient_boosting(X_train, y_train, random_state)
        if gb_result.is_err():
            return Err(gb_result.unwrap_err())

        gb_model = gb_result.unwrap()

        # Step 5: Run 5-fold cross-validation (Article II: robustness)
        cv_result = self._run_cross_validation(rf_model, gb_model, X_train, y_train)
        if cv_result.is_err():
            logger.warning(f"Cross-validation warning (non-blocking): {cv_result.unwrap_err()}")

        # Step 6: Create VotingClassifier ensemble
        ensemble_result = self._create_voting_ensemble(rf_model, gb_model)
        if ensemble_result.is_err():
            return Err(ensemble_result.unwrap_err())

        ensemble = ensemble_result.unwrap()
        ensemble.fit(X_train, y_train)

        # Step 7: Validate on held-out set (Article I: complete validation)
        y_pred = ensemble.predict(X_val)
        validation_accuracy = accuracy_score(y_val, y_pred)

        logger.info(f"Ensemble validation accuracy: {validation_accuracy:.4f}")

        # Step 8: Calculate false negative rate for complex tier (label=3)
        fn_rate_result = self._calculate_false_negative_rate(y_val, y_pred, complex_label=3)
        if fn_rate_result.is_err():
            return Err(fn_rate_result.unwrap_err())

        false_negative_rate = fn_rate_result.unwrap()

        logger.info(f"False negative rate (complex): {false_negative_rate:.4f}")

        # Step 9: Validate quality thresholds (Article II: 100% verification)
        threshold_result = self._validate_quality_thresholds(
            validation_accuracy, false_negative_rate
        )
        if threshold_result.is_err():
            return threshold_result

        # Check training time (informational, not blocking)
        training_time = time.perf_counter() - start_time
        self._log_training_time(training_time)

        # Step 10: Create EnsembleModel with metadata
        return self._create_ensemble_model(
            ensemble,
            rf_model,
            gb_model,
            validation_accuracy,
            false_negative_rate,
            dataset,
        )

    def _validate_training_data(self, dataset: TrainingDataset) -> Result[None, str]:
        """
        Validate training data completeness and quality.

        Article I compliance: Complete context before training.

        Args:
            dataset: TrainingDataset to validate

        Returns:
            Result indicating success or error message
        """
        train_samples = dataset.get_train_samples()
        val_samples = dataset.get_val_samples()

        # Check minimum sample counts
        if len(train_samples) < 50:
            return Err(
                f"Insufficient training data: {len(train_samples)} samples "
                f"(need ≥50). Article I violation: Incomplete context."
            )

        if len(val_samples) < 10:
            return Err(
                f"Insufficient validation data: {len(val_samples)} samples "
                f"(need ≥10). Article I violation: Incomplete validation."
            )

        # Check label distribution (avoid single-class datasets)
        train_labels = [s.label for s in train_samples]
        unique_labels = set(train_labels)

        if len(unique_labels) < 2:
            return Err(
                f"Training data must have ≥2 classes, found {len(unique_labels)}. "
                f"Article II violation: Cannot train classifier with single class."
            )

        logger.info(
            f"Training data validated: {len(train_samples)} train, "
            f"{len(val_samples)} val, {len(unique_labels)} classes"
        )

        return Ok(None)

    def _extract_features_and_labels(
        self, dataset: TrainingDataset
    ) -> Result[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], str]:
        """
        Extract feature arrays and labels from TrainingDataset.

        Args:
            dataset: TrainingDataset with samples and indices

        Returns:
            Result containing (X_train, y_train, X_val, y_val) or error
        """
        try:
            train_samples = dataset.get_train_samples()
            val_samples = dataset.get_val_samples()

            # Extract train features/labels
            X_train = np.array([sample.features.to_flat_array() for sample in train_samples])
            y_train = np.array([sample.label for sample in train_samples])

            # Extract validation features/labels
            X_val = np.array([sample.features.to_flat_array() for sample in val_samples])
            y_val = np.array([sample.label for sample in val_samples])

            # Validate dimensions (Article II)
            if X_train.shape[1] != 1644:
                return Err(f"Invalid feature dimension: expected 1644, got {X_train.shape[1]}")

            return Ok((X_train, y_train, X_val, y_val))

        except Exception as e:
            return Err(f"Feature extraction failed: {e}")

    def _train_random_forest(
        self, X_train: np.ndarray, y_train: np.ndarray, random_state: int
    ) -> Result[RandomForestClassifier, str]:
        """
        Train RandomForestClassifier (primary model).

        Args:
            X_train: Training features (n_samples, 1644)
            y_train: Training labels (n_samples,)
            random_state: Random seed

        Returns:
            Result containing trained RandomForestClassifier or error
        """
        try:
            # Override random_state from RF_CONFIG with provided value
            rf_config = {**RF_CONFIG, "random_state": random_state}
            model = RandomForestClassifier(**rf_config)
            model.fit(X_train, y_train)

            train_accuracy = model.score(X_train, y_train)
            logger.info(
                f"RandomForest trained: {RF_CONFIG['n_estimators']} trees, "
                f"train accuracy={train_accuracy:.4f}"
            )

            return Ok(model)

        except Exception as e:
            return Err(f"RandomForest training failed: {e}")

    def _train_gradient_boosting(
        self, X_train: np.ndarray, y_train: np.ndarray, random_state: int
    ) -> Result[GradientBoostingClassifier, str]:
        """
        Train GradientBoostingClassifier (secondary model).

        Args:
            X_train: Training features (n_samples, 1644)
            y_train: Training labels (n_samples,)
            random_state: Random seed

        Returns:
            Result containing trained GradientBoostingClassifier or error
        """
        try:
            # Override random_state from GB_CONFIG with provided value
            gb_config = {**GB_CONFIG, "random_state": random_state}
            model = GradientBoostingClassifier(**gb_config)
            model.fit(X_train, y_train)

            train_accuracy = model.score(X_train, y_train)
            logger.info(
                f"GradientBoosting trained: {GB_CONFIG['n_estimators']} estimators, "
                f"train accuracy={train_accuracy:.4f}"
            )

            return Ok(model)

        except Exception as e:
            return Err(f"GradientBoosting training failed: {e}")

    def _run_cross_validation(
        self,
        rf_model: RandomForestClassifier,
        gb_model: GradientBoostingClassifier,
        X_train: np.ndarray,
        y_train: np.ndarray,
        cv: int = 5,
    ) -> Result[dict[str, dict[str, float]], str]:
        """
        Run 5-fold stratified cross-validation.

        Article II compliance: Robustness validation.

        Args:
            rf_model: RandomForestClassifier
            gb_model: GradientBoostingClassifier
            X_train: Training features
            y_train: Training labels
            cv: Number of CV folds (default: 5)

        Returns:
            Result containing CV scores or error message
        """
        try:
            skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

            # RF cross-validation
            rf_accuracy = cross_val_score(
                rf_model, X_train, y_train, cv=skf, scoring="accuracy", n_jobs=-1
            )
            rf_precision = cross_val_score(
                rf_model,
                X_train,
                y_train,
                cv=skf,
                scoring="precision_macro",
                n_jobs=-1,
            )
            rf_recall = cross_val_score(
                rf_model, X_train, y_train, cv=skf, scoring="recall_macro", n_jobs=-1
            )

            # GB cross-validation
            gb_accuracy = cross_val_score(
                gb_model, X_train, y_train, cv=skf, scoring="accuracy", n_jobs=-1
            )
            gb_precision = cross_val_score(
                gb_model,
                X_train,
                y_train,
                cv=skf,
                scoring="precision_macro",
                n_jobs=-1,
            )
            gb_recall = cross_val_score(
                gb_model, X_train, y_train, cv=skf, scoring="recall_macro", n_jobs=-1
            )

            rf_scores = {
                "accuracy_mean": float(rf_accuracy.mean()),
                "accuracy_std": float(rf_accuracy.std()),
                "precision_mean": float(rf_precision.mean()),
                "recall_mean": float(rf_recall.mean()),
            }

            gb_scores = {
                "accuracy_mean": float(gb_accuracy.mean()),
                "accuracy_std": float(gb_accuracy.std()),
                "precision_mean": float(gb_precision.mean()),
                "recall_mean": float(gb_recall.mean()),
            }

            logger.info(
                f"RF CV scores: accuracy={rf_scores['accuracy_mean']:.3f} "
                f"±{rf_scores['accuracy_std']:.3f}, "
                f"precision={rf_scores['precision_mean']:.3f}, "
                f"recall={rf_scores['recall_mean']:.3f}"
            )

            logger.info(
                f"GB CV scores: accuracy={gb_scores['accuracy_mean']:.3f} "
                f"±{gb_scores['accuracy_std']:.3f}, "
                f"precision={gb_scores['precision_mean']:.3f}, "
                f"recall={gb_scores['recall_mean']:.3f}"
            )

            return Ok({"rf": rf_scores, "gb": gb_scores})

        except Exception as e:
            return Err(f"Cross-validation failed: {e}")

    def _create_voting_ensemble(
        self, rf_model: RandomForestClassifier, gb_model: GradientBoostingClassifier
    ) -> Result[VotingClassifier, str]:
        """
        Create VotingClassifier ensemble.

        Soft voting: Average class probabilities (weight RF=0.7, GB=0.3).

        Args:
            rf_model: RandomForestClassifier
            gb_model: GradientBoostingClassifier

        Returns:
            Result containing VotingClassifier or error
        """
        try:
            ensemble = VotingClassifier(
                estimators=[("rf", rf_model), ("gb", gb_model)], **VOTING_CONFIG
            )

            logger.info(f"Ensemble created: soft voting, weights={VOTING_CONFIG['weights']}")

            return Ok(ensemble)

        except Exception as e:
            return Err(f"Ensemble creation failed: {e}")

    def _calculate_false_negative_rate(
        self, y_true: np.ndarray, y_pred: np.ndarray, complex_label: int = 3
    ) -> Result[float, str]:
        """
        Calculate false negative rate for complex tasks.

        False Negative: Complex task predicted as simple/moderate.
        Critical metric: We MUST catch complex tasks (quality risk if missed).

        Formula: FN_rate = FN_complex / (FN_complex + TP_complex)

        Args:
            y_true: True labels
            y_pred: Predicted labels
            complex_label: Label for complex tier (default: 3)

        Returns:
            Result containing FN_rate (0.0-1.0) or error message
        """
        try:
            # Get unique labels from data
            unique_labels = sorted(set(y_true) | set(y_pred))

            # Build confusion matrix with explicit labels
            cm = confusion_matrix(y_true, y_pred, labels=unique_labels)

            # Find complex label index
            complex_idx = list(unique_labels).index(complex_label)

            # False negatives: complex → simple or moderate
            # Sum all non-diagonal elements in complex row
            fn_complex = cm[complex_idx, :].sum() - cm[complex_idx, complex_idx]

            # True positives: complex → complex
            tp_complex = cm[complex_idx, complex_idx]

            # Handle edge case: no complex samples in validation set
            if tp_complex + fn_complex == 0:
                logger.warning(
                    f"No complex samples (label={complex_label}) in validation set. "
                    f"FN_rate set to 0.0 (no false negatives possible)."
                )
                return Ok(0.0)

            fn_rate = float(fn_complex / (fn_complex + tp_complex))

            logger.info(
                f"Complex tier metrics: TP={tp_complex}, FN={fn_complex}, FN_rate={fn_rate:.4f}"
            )

            return Ok(fn_rate)

        except ValueError as e:
            return Err(f"Complex label {complex_label} not found in validation data: {e}")
        except Exception as e:
            return Err(f"False negative rate calculation failed: {e}")

    def _validate_quality_thresholds(
        self, validation_accuracy: float, false_negative_rate: float
    ) -> Result[None, str]:
        """
        Validate model meets quality thresholds.

        Article II compliance: 100% verification before deployment.

        Thresholds:
        - Validation accuracy ≥98%
        - False negative rate ≤2%

        Args:
            validation_accuracy: Accuracy on validation set
            false_negative_rate: FN_rate for complex tasks

        Returns:
            Result indicating success or error message
        """
        if validation_accuracy < MIN_VALIDATION_ACCURACY:
            return Err(
                f"Validation accuracy {validation_accuracy:.4f} below 98% threshold. "
                f"Article II violation: Insufficient verification. "
                f"Consider: (1) Collect more training data, "
                f"(2) Improve feature engineering, "
                f"(3) Tune hyperparameters with GridSearchCV."
            )

        if false_negative_rate > MAX_FALSE_NEGATIVE_RATE:
            return Err(
                f"False negative rate {false_negative_rate:.4f} above 2% threshold. "
                f"Article II violation: Complex tasks at risk of misclassification. "
                f"Consider: (1) Increase training data for complex tier, "
                f"(2) Adjust class weights to penalize FN_complex, "
                f"(3) Use cost-sensitive learning."
            )

        logger.info(
            f"✓ Quality thresholds met: accuracy={validation_accuracy:.4f} (≥0.98), "
            f"FN_rate={false_negative_rate:.4f} (≤0.02)"
        )

        return Ok(None)

    def _log_training_time(self, training_time_seconds: float) -> None:
        """
        Log training time with warning if exceeds target.

        Target: <5 minutes (300 seconds) for 1,000 samples.
        Non-blocking: Exceeding target is informational only.

        Args:
            training_time_seconds: Training time in seconds
        """
        if training_time_seconds > MAX_TRAINING_TIME_SECONDS:
            logger.warning(
                f"⚠️  Training time {training_time_seconds:.1f}s exceeded "
                f"{MAX_TRAINING_TIME_SECONDS}s target (informational, non-blocking)"
            )
        else:
            logger.info(f"Training time: {training_time_seconds:.1f}s")

    def _create_ensemble_model(
        self,
        ensemble: VotingClassifier,
        rf_model: RandomForestClassifier,
        gb_model: GradientBoostingClassifier,
        validation_accuracy: float,
        false_negative_rate: float,
        dataset: TrainingDataset,
    ) -> Result[EnsembleModel, str]:
        """
        Create EnsembleModel with metadata.

        Args:
            ensemble: Trained VotingClassifier
            rf_model: Trained RandomForestClassifier
            gb_model: Trained GradientBoostingClassifier
            validation_accuracy: Validation accuracy
            false_negative_rate: False negative rate for complex tier
            dataset: TrainingDataset (for feature names)

        Returns:
            Result containing EnsembleModel or error message
        """
        try:
            # Generate feature names (1644 total)
            feature_names = self._generate_feature_names()

            model = EnsembleModel(
                ensemble=ensemble,
                rf_model=rf_model,
                gb_model=gb_model,
                validation_accuracy=float(validation_accuracy),
                false_negative_rate=float(false_negative_rate),
                training_date=datetime.now().isoformat(),
                feature_names=feature_names,
            )

            logger.info(
                f"✓ EnsembleModel created: accuracy={validation_accuracy:.4f}, "
                f"FN_rate={false_negative_rate:.4f}"
            )

            return Ok(model)

        except Exception as e:
            return Err(f"EnsembleModel creation failed: {e}")

    def _generate_feature_names(self) -> list[str]:
        """
        Generate feature names for 1644-dimension feature vector.

        Feature composition:
        - embedding_0 ... embedding_1535 (1536 dims)
        - tfidf_0 ... tfidf_99 (100 dims)
        - description_length, word_count, has_refactor_keyword, etc. (8 dims)

        Returns:
            List of 1644 feature names
        """
        feature_names = []

        # Embedding features (1536)
        feature_names.extend([f"embedding_{i}" for i in range(1536)])

        # TF-IDF features (100)
        feature_names.extend([f"tfidf_{i}" for i in range(100)])

        # Metadata features (8)
        feature_names.extend(
            [
                "description_length",
                "word_count",
                "has_refactor_keyword",
                "has_test_keyword",
                "has_async_keyword",
                "has_fix_keyword",
                "estimated_time_seconds",
                "historical_tier_mode",
            ]
        )

        return feature_names
