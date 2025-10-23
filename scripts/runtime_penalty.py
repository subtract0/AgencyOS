#!/usr/bin/env python3
"""
Non-Linear Runtime Penalty Function

Replaces linear penalty with exponential penalty for slow tests.

Linear (V4): penalty = runtime * 0.1
Non-Linear (V5): Steep penalty for tests >30s

Formula:
  - Tests <10s: Minimal penalty (<1 point)
  - Tests 10-30s: Moderate penalty (1-3 points)
  - Tests >30s: Steep penalty (5-20 points)
  - Tests >60s: Extreme penalty (20+ points)

Constitutional Article V: Configurable via weights.yaml
"""

import math
from typing import Dict, Any


class RuntimePenaltyCalculator:
    """Calculate non-linear runtime penalties for tests."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize with configurable weights.

        Args:
            config: Optional weights dict with keys:
                - fast_threshold: Tests <this are minimal penalty (default: 10s)
                - moderate_threshold: Moderate penalty up to this (default: 30s)
                - slow_threshold: Steep penalty starts here (default: 30s)
                - extreme_threshold: Extreme penalty starts here (default: 60s)
                - base_weight: Base multiplier (default: 0.1)
                - exponential_factor: Exponential growth rate (default: 10)
        """
        if config is None:
            config = {}

        self.fast_threshold = config.get('fast_threshold', 10.0)
        self.moderate_threshold = config.get('moderate_threshold', 30.0)
        self.slow_threshold = config.get('slow_threshold', 30.0)
        self.extreme_threshold = config.get('extreme_threshold', 60.0)
        self.base_weight = config.get('base_weight', 0.1)
        self.exponential_factor = config.get('exponential_factor', 10.0)

    def calculate_penalty(self, runtime_seconds: float) -> float:
        """
        Calculate runtime penalty with non-linear scaling.

        Formula:
          if runtime <= fast_threshold (10s):
            penalty = runtime * base_weight (linear, minimal)

          elif runtime <= moderate_threshold (30s):
            penalty = fast_penalty + (runtime - fast_threshold) * 0.15

          elif runtime <= extreme_threshold (60s):
            penalty = runtime * (1 + exp((runtime - slow_threshold) / exponential_factor))

          else:  # > 60s
            penalty = 20 + (runtime - extreme_threshold) * 0.5

        Args:
            runtime_seconds: Test execution time in seconds

        Returns:
            Penalty score (positive number, higher = worse)
        """
        if runtime_seconds < 0:
            return 0.0

        # Fast tests (<10s): Minimal linear penalty
        if runtime_seconds <= self.fast_threshold:
            return runtime_seconds * self.base_weight

        # Moderate tests (10-30s): Moderate linear penalty
        elif runtime_seconds <= self.moderate_threshold:
            fast_penalty = self.fast_threshold * self.base_weight
            moderate_penalty = (runtime_seconds - self.fast_threshold) * 0.15
            return fast_penalty + moderate_penalty

        # Slow tests (30-60s): Exponential penalty
        elif runtime_seconds <= self.extreme_threshold:
            penalty = runtime_seconds * (
                1 + math.exp((runtime_seconds - self.slow_threshold) / self.exponential_factor)
            )
            return penalty

        # Extreme tests (>60s): Very high penalty
        else:
            base_extreme_penalty = 20.0  # Base penalty at 60s
            additional_penalty = (runtime_seconds - self.extreme_threshold) * 0.5
            return base_extreme_penalty + additional_penalty

    def get_penalty_breakdown(self, runtime_seconds: float) -> Dict[str, Any]:
        """
        Get detailed penalty breakdown for debugging/explanation.

        Returns:
            {
                'runtime_seconds': float,
                'penalty': float,
                'category': str,  # 'fast', 'moderate', 'slow', 'extreme'
                'explanation': str
            }
        """
        penalty = self.calculate_penalty(runtime_seconds)

        if runtime_seconds <= self.fast_threshold:
            category = 'fast'
            explanation = f"Fast test (<{self.fast_threshold}s): Minimal linear penalty"
        elif runtime_seconds <= self.moderate_threshold:
            category = 'moderate'
            explanation = f"Moderate test ({self.fast_threshold}-{self.moderate_threshold}s): Linear penalty"
        elif runtime_seconds <= self.extreme_threshold:
            category = 'slow'
            explanation = f"Slow test ({self.moderate_threshold}-{self.extreme_threshold}s): Exponential penalty"
        else:
            category = 'extreme'
            explanation = f"Extreme test (>{self.extreme_threshold}s): Very high penalty"

        return {
            'runtime_seconds': runtime_seconds,
            'penalty': penalty,
            'category': category,
            'explanation': explanation
        }

    def compare_penalties(self, runtime_seconds: float) -> Dict[str, float]:
        """
        Compare linear (V4) vs non-linear (V5) penalties.

        Useful for demonstrating improvement.
        """
        linear_penalty = runtime_seconds * 0.1  # V4 formula
        nonlinear_penalty = self.calculate_penalty(runtime_seconds)

        return {
            'runtime': runtime_seconds,
            'linear_v4': linear_penalty,
            'nonlinear_v5': nonlinear_penalty,
            'difference': nonlinear_penalty - linear_penalty,
            'ratio': nonlinear_penalty / linear_penalty if linear_penalty > 0 else float('inf')
        }


def generate_penalty_table() -> str:
    """Generate a comparison table of penalties at different runtimes."""
    calculator = RuntimePenaltyCalculator()

    test_runtimes = [0.1, 1, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180]

    lines = []
    lines.append("Runtime Penalty Comparison (V4 Linear vs V5 Non-Linear)")
    lines.append("=" * 80)
    lines.append(f"{'Runtime':<12} {'V4 Linear':<15} {'V5 Non-Linear':<20} {'Difference':<15} {'Category'}")
    lines.append("-" * 80)

    for runtime in test_runtimes:
        breakdown = calculator.get_penalty_breakdown(runtime)
        comparison = calculator.compare_penalties(runtime)

        lines.append(
            f"{runtime:>6.1f}s      "
            f"{comparison['linear_v4']:>8.2f}        "
            f"{comparison['nonlinear_v5']:>10.2f}         "
            f"{comparison['difference']:>+8.2f}       "
            f"{breakdown['category']}"
        )

    return "\n".join(lines)


if __name__ == '__main__':
    # Demo: Show penalty comparison
    print(generate_penalty_table())
    print("\n")

    # Show specific examples
    calculator = RuntimePenaltyCalculator()

    print("Example Penalties:")
    print("-" * 60)

    examples = [
        (0.1, "Fast unit test"),
        (5.0, "Typical unit test"),
        (10.0, "Slower unit test"),
        (30.0, "Integration test"),
        (60.0, "E2E test"),
        (120.0, "Very slow E2E test"),
    ]

    for runtime, description in examples:
        breakdown = calculator.get_penalty_breakdown(runtime)
        print(f"{description:30} ({runtime:5.1f}s): {breakdown['penalty']:6.2f} penalty ({breakdown['category']})")
