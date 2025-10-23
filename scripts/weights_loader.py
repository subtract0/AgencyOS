#!/usr/bin/env python3
"""
Weights Loader - Load and validate weights.yaml configuration.

Constitutional Article V: All scoring weights are configurable.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ScoringWeights:
    """Validated scoring weights from weights.yaml."""

    # Component weights
    bug_detection_weight: float
    critical_path_weight: float
    integration_bonus_weight: float

    # Penalty weights
    maintenance_burden_weight: float

    # Runtime penalty config
    runtime_fast_threshold: float
    runtime_moderate_threshold: float
    runtime_slow_threshold: float
    runtime_extreme_threshold: float
    runtime_base_weight: float
    runtime_exponential_factor: float

    # Mock penalties
    external_mock_weight: float
    internal_mock_weight: float

    # Git churn
    churn_weight: float
    age_penalty_weight: float

    # Failure history
    failure_bonus_weight: float
    flaky_penalty: float
    min_fixed_for_bonus: int
    lookback_days: int

    # Normalization
    normalization_mode: str  # 'none', 'z-score', 'min-max'

    # Thresholds
    high_value_threshold: float
    medium_value_threshold: float
    low_value_threshold: float


class WeightsLoader:
    """Load and validate weights.yaml configuration."""

    DEFAULT_WEIGHTS_PATH = Path("weights.yaml")

    def __init__(self, weights_path: Optional[Path] = None):
        """
        Initialize weights loader.

        Args:
            weights_path: Optional path to weights.yaml (default: ./weights.yaml)
                         Can also be set via AUDIT_WEIGHTS_FILE env variable.
        """
        if weights_path is None:
            # Check environment variable
            env_path = os.getenv('AUDIT_WEIGHTS_FILE')
            if env_path:
                weights_path = Path(env_path)
            else:
                weights_path = self.DEFAULT_WEIGHTS_PATH

        self.weights_path = weights_path
        self._cached_weights: Optional[ScoringWeights] = None

    def load(self) -> ScoringWeights:
        """
        Load and validate weights from YAML file.

        Returns:
            ScoringWeights object with validated configuration

        Raises:
            FileNotFoundError: If weights file doesn't exist and no defaults available
            ValueError: If weights are invalid (out of range, wrong type, etc.)
        """
        # Return cached weights if already loaded
        if self._cached_weights is not None:
            return self._cached_weights

        # Load from file or use defaults
        if not self.weights_path.exists():
            print(f"⚠️  Weights file not found: {self.weights_path}")
            print("   Using default weights")
            config = self._get_default_config()
        else:
            with open(self.weights_path, 'r') as f:
                config = yaml.safe_load(f)

        # Parse and validate
        weights = self._parse_config(config)
        self._validate_weights(weights)

        # Cache for performance
        self._cached_weights = weights

        return weights

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when weights.yaml is missing."""
        return {
            'bug_detection_weight': 10.0,
            'critical_path_weight': 5.0,
            'integration_bonus_weight': 3.0,
            'maintenance_burden_weight': 2.0,
            'runtime_penalty': {
                'fast_threshold': 10.0,
                'moderate_threshold': 30.0,
                'slow_threshold': 30.0,
                'extreme_threshold': 60.0,
                'base_weight': 0.1,
                'exponential_factor': 10.0,
            },
            'mock_penalties': {
                'external_mock_weight': 0.3,
                'internal_mock_weight': 0.8,
            },
            'git_churn': {
                'churn_weight': 1.5,
                'age_penalty_weight': 0.5,
            },
            'failure_history': {
                'failure_bonus_weight': 5.0,
                'flaky_penalty': -5.0,
                'min_fixed_for_bonus': 1,
                'lookback_days': 90,
            },
            'normalization': {
                'mode': 'z-score',
            },
            'thresholds': {
                'high_value': 20,
                'medium_value': 10,
                'low_value': 10,
            }
        }

    def _parse_config(self, config: Dict[str, Any]) -> ScoringWeights:
        """Parse YAML config into ScoringWeights object."""
        runtime = config.get('runtime_penalty', {})
        mocks = config.get('mock_penalties', {})
        churn = config.get('git_churn', {})
        failure = config.get('failure_history', {})
        norm = config.get('normalization', {})
        thresh = config.get('thresholds', {})

        return ScoringWeights(
            # Component weights
            bug_detection_weight=config.get('bug_detection_weight', 10.0),
            critical_path_weight=config.get('critical_path_weight', 5.0),
            integration_bonus_weight=config.get('integration_bonus_weight', 3.0),

            # Penalty weights
            maintenance_burden_weight=config.get('maintenance_burden_weight', 2.0),

            # Runtime penalty
            runtime_fast_threshold=runtime.get('fast_threshold', 10.0),
            runtime_moderate_threshold=runtime.get('moderate_threshold', 30.0),
            runtime_slow_threshold=runtime.get('slow_threshold', 30.0),
            runtime_extreme_threshold=runtime.get('extreme_threshold', 60.0),
            runtime_base_weight=runtime.get('base_weight', 0.1),
            runtime_exponential_factor=runtime.get('exponential_factor', 10.0),

            # Mock penalties
            external_mock_weight=mocks.get('external_mock_weight', 0.3),
            internal_mock_weight=mocks.get('internal_mock_weight', 0.8),

            # Git churn
            churn_weight=churn.get('churn_weight', 1.5),
            age_penalty_weight=churn.get('age_penalty_weight', 0.5),

            # Failure history
            failure_bonus_weight=failure.get('failure_bonus_weight', 5.0),
            flaky_penalty=failure.get('flaky_penalty', -5.0),
            min_fixed_for_bonus=failure.get('min_fixed_for_bonus', 1),
            lookback_days=failure.get('lookback_days', 90),

            # Normalization
            normalization_mode=norm.get('mode', 'z-score'),

            # Thresholds
            high_value_threshold=thresh.get('high_value', 20),
            medium_value_threshold=thresh.get('medium_value', 10),
            low_value_threshold=thresh.get('low_value', 10),
        )

    def _validate_weights(self, weights: ScoringWeights) -> None:
        """
        Validate weights are within acceptable ranges.

        Raises:
            ValueError: If any weight is invalid
        """
        # Component weights: 0-10
        for attr in ['bug_detection_weight', 'critical_path_weight', 'integration_bonus_weight']:
            value = getattr(weights, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} must be 0-10, got {value}")

        # Penalty weights: 0-10
        for attr in ['maintenance_burden_weight', 'external_mock_weight', 'internal_mock_weight']:
            value = getattr(weights, attr)
            if not (0 <= value <= 10):
                raise ValueError(f"{attr} must be 0-10, got {value}")

        # Runtime thresholds: must be positive and in order
        if not (0 < weights.runtime_fast_threshold < weights.runtime_moderate_threshold):
            raise ValueError("Runtime thresholds must be: 0 < fast < moderate")

        # Normalization mode: must be valid
        if weights.normalization_mode not in ['none', 'z-score', 'min-max']:
            raise ValueError(f"Invalid normalization mode: {weights.normalization_mode}")

        # Thresholds: must be positive
        if not (0 < weights.low_value_threshold < weights.high_value_threshold):
            raise ValueError("Thresholds must be: 0 < low < high")


if __name__ == '__main__':
    # Demo: Load weights
    loader = WeightsLoader()

    try:
        weights = loader.load()

        print("✅ Weights loaded successfully!")
        print("\nConfiguration:")
        print(f"  Bug detection weight: {weights.bug_detection_weight}")
        print(f"  Critical path weight: {weights.critical_path_weight}")
        print(f"  Normalization mode: {weights.normalization_mode}")
        print(f"  High value threshold: {weights.high_value_threshold}")

    except Exception as e:
        print(f"❌ Failed to load weights: {e}")
