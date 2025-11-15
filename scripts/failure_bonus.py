#!/usr/bin/env python3
"""
Failure History Bonus - Reward tests that caught real bugs.

Constitutional Article V: Configurable via weights.yaml

Scoring Logic:
- 0 failures: +0 bonus
- 1-2 fixed failures: +5-10 bonus (proven bug detectors)
- 3+ fixed failures: +15 bonus (critical regression tests)
- Flaky tests (2-9/10, never fixed): -5 penalty (unreliable)
- Consistent failures (10/10): 0 bonus (test bug, not code bug)
"""

from typing import Dict, Any
from pathlib import Path
import sys

# Add scripts to path if running standalone
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent))

try:
    from ci_failure_parser import CIFailureParser
except ImportError:  # pragma: no cover - lightweight fallback for local/dev
    class CIFailureParser:  # type: ignore[override]
        """Fallback parser when CI dependencies are unavailable."""

        def __init__(self, db_path: Path):  # noqa: D401 - mimic real signature
            self.db_path = Path(db_path)

        def is_flaky(self, test_id: str) -> bool:  # noqa: ARG002
            return False

        def get_fixed_failure_count(self, test_id: str, lookback_days: int) -> int:  # noqa: ARG002
            return 0

        def get_failure_count(self, test_id: str, lookback_days: int) -> int:  # noqa: ARG002
            return 0

        def get_database_stats(self) -> Dict[str, int]:
            return {
                "total_failures": 0,
                "fixed_failures": 0,
                "flaky_tests": 0,
                "unique_tests": 0,
            }


class FailureBonusCalculator:
    """Calculate test value bonus based on failure history."""

    def __init__(self, config: Dict[str, Any] = None, db_path: Path = None):
        """
        Initialize with configurable weights.

        Args:
            config: Optional weights dict with keys:
                - failure_bonus_weight: Points per fixed failure (default: 5)
                - flaky_penalty: Penalty for flaky tests (default: -5)
                - min_fixed_for_bonus: Minimum fixed failures for bonus (default: 1)
                - lookback_days: Days to look back for failures (default: 90)
            db_path: Path to SQLite database (default: .audit/failure_history.sqlite)
        """
        if config is None:
            config = {}

        self.failure_bonus_weight = config.get('failure_bonus_weight', 5.0)
        self.flaky_penalty = config.get('flaky_penalty', -5.0)
        self.min_fixed_for_bonus = config.get('min_fixed_for_bonus', 1)
        self.lookback_days = config.get('lookback_days', 90)

        # Initialize parser (with database)
        if db_path is None:
            db_path = Path('.audit/failure_history.sqlite')

        self.parser = CIFailureParser(db_path)

    def calculate_bonus(self, test_id: str) -> float:
        """
        Calculate failure history bonus for a test.

        Returns:
            Bonus score (positive for bug detectors, negative for flaky)
        """
        # Check if test is flaky (unreliable)
        if self.parser.is_flaky(test_id):
            return self.flaky_penalty

        # Count fixed failures (proven bug detectors)
        fixed_failures = self.parser.get_fixed_failure_count(test_id, self.lookback_days)

        if fixed_failures == 0:
            return 0.0

        # Progressive bonus
        if fixed_failures == 1:
            return self.failure_bonus_weight
        elif fixed_failures == 2:
            return self.failure_bonus_weight * 2
        else:  # 3+
            return self.failure_bonus_weight * 3

    def get_bonus_breakdown(self, test_id: str) -> Dict[str, Any]:
        """
        Get detailed bonus breakdown for debugging/explanation.

        Returns:
            {
                'test_id': str,
                'total_failures': int,
                'fixed_failures': int,
                'is_flaky': bool,
                'bonus': float,
                'category': str,  # 'bug_detector', 'flaky', 'no_failures'
                'explanation': str
            }
        """
        total_failures = self.parser.get_failure_count(test_id, self.lookback_days)
        fixed_failures = self.parser.get_fixed_failure_count(test_id, self.lookback_days)
        is_flaky = self.parser.is_flaky(test_id)
        bonus = self.calculate_bonus(test_id)

        # Determine category
        if is_flaky:
            category = 'flaky'
            explanation = f"Flaky test (fails inconsistently, never fully fixed): {self.flaky_penalty} penalty"
        elif fixed_failures > 0:
            category = 'bug_detector'
            if fixed_failures == 1:
                explanation = f"Caught 1 real bug: +{bonus:.0f} bonus (proven bug detector)"
            elif fixed_failures == 2:
                explanation = f"Caught 2 real bugs: +{bonus:.0f} bonus (strong bug detector)"
            else:
                explanation = f"Caught {fixed_failures} real bugs: +{bonus:.0f} bonus (critical regression test)"
        elif total_failures > 0:
            category = 'broken_test'
            explanation = f"{total_failures} failures but never fixed (likely test bug, not code bug): 0 bonus"
        else:
            category = 'no_failures'
            explanation = "No CI failures in last 90 days: 0 bonus"

        return {
            'test_id': test_id,
            'total_failures': total_failures,
            'fixed_failures': fixed_failures,
            'is_flaky': is_flaky,
            'bonus': bonus,
            'category': category,
            'explanation': explanation
        }

    def bulk_calculate_bonuses(self, test_ids: list[str]) -> Dict[str, float]:
        """
        Calculate bonuses for multiple tests efficiently.

        Args:
            test_ids: List of test identifiers

        Returns:
            dict[test_id, bonus]
        """
        bonuses = {}
        for test_id in test_ids:
            bonuses[test_id] = self.calculate_bonus(test_id)
        return bonuses


def generate_bonus_table() -> str:
    """Generate a comparison table showing bonus logic."""
    lines = []
    lines.append("Failure History Bonus Logic")
    lines.append("=" * 80)
    lines.append(f"{'Scenario':<40} {'Fixed Fails':<15} {'Flaky?':<10} {'Bonus'}")
    lines.append("-" * 80)

    scenarios = [
        ("No failures in CI", 0, False, 0),
        ("1 failure, then fixed", 1, False, 5),
        ("2 failures, then fixed", 2, False, 10),
        ("3+ failures, then fixed", 3, False, 15),
        ("Flaky (2-9/10 runs, never fixed)", 0, True, -5),
        ("10+ failures, never fixed", 0, False, 0),
    ]

    for scenario, fixed, flaky, bonus in scenarios:
        flaky_str = "Yes" if flaky else "No"
        bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
        lines.append(f"{scenario:<40} {fixed:<15} {flaky_str:<10} {bonus_str}")

    lines.append("\n" + "=" * 80)
    lines.append("FAILURE_BONUS_WEIGHT = 5 (configurable in weights.yaml)")
    lines.append("FLAKY_PENALTY = -5 (configurable)")
    lines.append("\nFixed Definition: Test passed in 3 consecutive CI runs after failure")
    lines.append("Flaky Definition: Failed 2-9 out of 10 runs, never achieved 3 consecutive passes")
    lines.append("=" * 80)

    return "\n".join(lines)


if __name__ == '__main__':
    # Demo: Show bonus logic
    print(generate_bonus_table())
    print("\n")

    # Initialize calculator
    calc = FailureBonusCalculator()

    # Show database stats
    stats = calc.parser.get_database_stats()
    print(f"📊 Database Statistics:")
    print(f"  Total failures: {stats['total_failures']}")
    print(f"  Fixed failures: {stats['fixed_failures']}")
    print(f"  Flaky tests: {stats['flaky_tests']}")

    # Example: Calculate bonus for a test
    if stats['unique_tests'] > 0:
        print(f"\nExample Bonus Calculation:")
        # This would need actual test IDs from database
        print("  (Run with actual CI data for specific examples)")
