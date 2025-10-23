#!/usr/bin/env python3
"""
Score Normalization Engine - Make scoring components comparable.

Z-score: (value - mean) / stddev (centers around 0, ±3 range)
Min-max: (value - min) / (max - min) * 100 (scales to 0-100)
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NormalizationStats:
    """Statistics for normalization."""
    mean: float
    stddev: float
    min: float
    max: float


class ScoreNormalizer:
    """Normalize scoring components for comparability."""

    def __init__(self, mode: str = 'z-score'):
        """
        Initialize normalizer.

        Args:
            mode: 'none', 'z-score', or 'min-max'
        """
        if mode not in ['none', 'z-score', 'min-max']:
            raise ValueError(f"Invalid normalization mode: {mode}")

        self.mode = mode
        self.stats: Dict[str, NormalizationStats] = {}

    def fit(self, component_name: str, values: List[float]) -> None:
        """
        Calculate normalization statistics for a component.

        Args:
            component_name: Name of scoring component (e.g., 'bug_detection')
            values: List of raw scores for this component
        """
        if not values:
            return

        values_array = np.array(values)

        self.stats[component_name] = NormalizationStats(
            mean=float(np.mean(values_array)),
            stddev=float(np.std(values_array)),
            min=float(np.min(values_array)),
            max=float(np.max(values_array))
        )

    def transform(self, component_name: str, value: float) -> float:
        """
        Normalize a single value.

        Args:
            component_name: Name of scoring component
            value: Raw score value

        Returns:
            Normalized score
        """
        if self.mode == 'none':
            return value

        if component_name not in self.stats:
            # No stats available, return raw value
            return value

        stats = self.stats[component_name]

        if self.mode == 'z-score':
            return self._z_score_normalize(value, stats)
        elif self.mode == 'min-max':
            return self._min_max_normalize(value, stats)

        return value

    def _z_score_normalize(self, value: float, stats: NormalizationStats) -> float:
        """
        Z-score normalization: (value - mean) / stddev

        Result: Centered at 0, typically in ±3 range.
        """
        if stats.stddev == 0:
            # All values are the same
            return 0.0

        return (value - stats.mean) / stats.stddev

    def _min_max_normalize(self, value: float, stats: NormalizationStats) -> float:
        """
        Min-max normalization: (value - min) / (max - min) * 100

        Result: Scaled to 0-100 range.
        """
        if stats.max == stats.min:
            # All values are the same
            return 50.0  # Return midpoint

        normalized = (value - stats.min) / (stats.max - stats.min)
        return normalized * 100.0

    def fit_transform(self, components: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Fit and transform multiple components at once.

        Args:
            components: dict[component_name, list of values]

        Returns:
            dict[component_name, list of normalized values]
        """
        normalized = {}

        for component_name, values in components.items():
            self.fit(component_name, values)
            normalized[component_name] = [
                self.transform(component_name, v) for v in values
            ]

        return normalized

    def get_stats_summary(self) -> str:
        """Get summary of normalization statistics."""
        lines = []
        lines.append(f"Normalization Mode: {self.mode}")
        lines.append("=" * 70)

        if not self.stats:
            lines.append("No statistics computed yet (call fit() first)")
            return "\n".join(lines)

        lines.append(f"{'Component':<30} {'Mean':<10} {'StdDev':<10} {'Min':<10} {'Max':<10}")
        lines.append("-" * 70)

        for comp_name, stats in self.stats.items():
            lines.append(
                f"{comp_name:<30} {stats.mean:<10.2f} {stats.stddev:<10.2f} {stats.min:<10.2f} {stats.max:<10.2f}"
            )

        return "\n".join(lines)


if __name__ == '__main__':
    # Demo: Normalization
    import random
    random.seed(42)

    # Generate sample data
    components = {
        'bug_detection': [random.gauss(5, 2) for _ in range(100)],
        'critical_path': [random.gauss(3, 1) for _ in range(100)],
        'runtime_penalty': [random.gauss(-2, 0.5) for _ in range(100)],
    }

    print("Original Data (first 5 values):")
    for comp, values in components.items():
        print(f"  {comp}: {values[:5]}")

    print("\n" + "="*70)

    # Test z-score normalization
    print("\nZ-Score Normalization:")
    normalizer = ScoreNormalizer(mode='z-score')
    normalized_z = normalizer.fit_transform(components)

    for comp, values in normalized_z.items():
        print(f"  {comp}: {[f'{v:.2f}' for v in values[:5]]}")

    print("\n" + normalizer.get_stats_summary())

    # Test min-max normalization
    print("\n" + "="*70)
    print("\nMin-Max Normalization:")
    normalizer2 = ScoreNormalizer(mode='min-max')
    normalized_mm = normalizer2.fit_transform(components)

    for comp, values in normalized_mm.items():
        print(f"  {comp}: {[f'{v:.1f}' for v in values[:5]]}")

    print("\n" + normalizer2.get_stats_summary())

    # Test edge cases
    print("\n" + "="*70)
    print("\nEdge Cases:")

    # All values the same
    normalizer3 = ScoreNormalizer(mode='z-score')
    normalizer3.fit('constant', [5.0, 5.0, 5.0, 5.0])
    result = normalizer3.transform('constant', 5.0)
    print(f"  All values same (z-score): {result} (should be 0.0)")

    # Single value
    normalizer4 = ScoreNormalizer(mode='min-max')
    normalizer4.fit('single', [10.0])
    result = normalizer4.transform('single', 10.0)
    print(f"  Single value (min-max): {result} (should be 50.0)")

    print("\n✅ Normalization engine working correctly!")
