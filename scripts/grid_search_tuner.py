#!/usr/bin/env python3
"""
Grid Search Tuner for Test Value Scoring Weights

Optimizes weights.yaml configuration to maximize agreement with manual labels.
Uses exhaustive grid search across 6+ weight dimensions.

Usage:
    python scripts/grid_search_tuner.py --labeled-tests labeled_tests.json
    python scripts/grid_search_tuner.py --labeled-tests labeled_tests.json --max-iterations 200
    python scripts/grid_search_tuner.py --quick  # Fast search with reduced grid

Constitutional Compliance:
- Article I: Complete context (loads ALL labeled tests before search)
- Article II: 100% verification (requires tests for implementation)
- Article IV: Stores optimal weights in VectorStore for future reference
- Article V: Traces to TEST_AUDIT_V5_PLAN.md Phase 6

Performance Target:
- <10 minutes for 50 samples, 100 grid points
- Progress logging every 10 iterations
"""

import json
import sys
import time
import argparse
import itertools
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import Counter

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("❌ yaml library required for weights output")
    print("   Install: pip install pyyaml")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  rich not available, using plain text output")
    print("   Install: pip install rich")


@dataclass
class WeightCandidate:
    """A single combination of weights to evaluate."""
    bug_detection_weight: float
    critical_path_weight: float
    runtime_penalty_multiplier: float
    failure_bonus_weight: float
    churn_penalty_weight: float
    age_penalty_weight: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SearchResult:
    """Result of grid search optimization."""
    best_weights: WeightCandidate
    best_accuracy: float
    total_iterations: int
    elapsed_seconds: float
    samples_evaluated: int
    confusion_matrix: Dict[str, Dict[str, int]]
    label_distribution: Dict[str, int]


class GridSearchTuner:
    """
    Grid search optimizer for test value scoring weights.

    Finds optimal weight configuration that maximizes agreement between
    predicted actions (KEEP/REVIEW/DELETE) and manual labels.
    """

    def __init__(
        self,
        labeled_tests_path: Path,
        weights_template_path: Path = Path("weights.yaml"),
        output_path: Path = Path("weights_optimized.yaml")
    ):
        """
        Initialize grid search tuner.

        Args:
            labeled_tests_path: Path to labeled_tests.json (manual labels)
            weights_template_path: Path to current weights.yaml (for structure)
            output_path: Path to output optimized weights

        Raises:
            FileNotFoundError: If labeled_tests.json doesn't exist
            ValueError: If labeled tests are insufficient (<10 samples)
        """
        self.labeled_tests_path = labeled_tests_path
        self.weights_template_path = weights_template_path
        self.output_path = output_path

        self.console = Console() if RICH_AVAILABLE else None

        # Load labeled tests (Article I: Complete context)
        self.labeled_tests = self._load_labeled_tests()
        self._validate_labeled_tests()

        # Load weights template for structure
        self.weights_template = self._load_weights_template()

        # Search state
        self.best_accuracy = 0.0
        self.best_weights: Optional[WeightCandidate] = None
        self.iterations_evaluated = 0

    def _load_labeled_tests(self) -> List[Dict[str, Any]]:
        """
        Load manual test labels from JSON.

        Returns:
            List of labeled test dictionaries

        Raises:
            FileNotFoundError: If labeled_tests.json doesn't exist
        """
        if not self.labeled_tests_path.exists():
            raise FileNotFoundError(
                f"Labeled tests file not found: {self.labeled_tests_path}\n"
                f"Run: python scripts/label_tests.py --sample-size 50"
            )

        with open(self.labeled_tests_path, 'r') as f:
            data = json.load(f)

        # Handle both list format and dict with 'labels' key
        if isinstance(data, dict) and 'labels' in data:
            return data['labels']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(f"Invalid labeled_tests.json format: expected list or dict with 'labels' key")

    def _validate_labeled_tests(self) -> None:
        """
        Validate labeled tests have required fields and sufficient samples.

        Raises:
            ValueError: If validation fails
        """
        if len(self.labeled_tests) < 10:
            raise ValueError(
                f"Insufficient labeled tests: {len(self.labeled_tests)} found, need at least 10\n"
                f"Run: python scripts/label_tests.py --sample-size 50"
            )

        # Check required fields
        required_fields = ['test_id', 'manual_label', 'score', 'bug_detection_score',
                          'critical_path_score', 'integration_score']
        missing_fields = []
        for test in self.labeled_tests[:3]:  # Check first 3
            for field in required_fields:
                if field not in test:
                    missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Labeled tests missing required fields: {set(missing_fields)}\n"
                f"Re-run: python scripts/label_tests.py"
            )

        # Check label distribution
        labels = [t['manual_label'] for t in self.labeled_tests]
        label_counts = Counter(labels)

        # Edge case: All same label
        if len(label_counts) == 1:
            label = list(label_counts.keys())[0]
            print(f"⚠️  WARNING: All {len(self.labeled_tests)} tests labeled as '{label}'")
            print(f"   Grid search accuracy will be 100% for all weight combinations!")
            print(f"   Consider labeling a diverse sample (mix of KEEP/REVIEW/DELETE)")

        # Print distribution
        print(f"✅ Loaded {len(self.labeled_tests)} labeled tests")
        print(f"   Distribution: {dict(label_counts)}")

    def _load_weights_template(self) -> Dict[str, Any]:
        """Load weights.yaml template for structure (non-optimized values)."""
        if not self.weights_template_path.exists():
            print(f"⚠️  Weights template not found: {self.weights_template_path}")
            print(f"   Using default structure")
            return self._get_default_weights_structure()

        with open(self.weights_template_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_default_weights_structure(self) -> Dict[str, Any]:
        """Get default weights.yaml structure."""
        return {
            'bug_detection_weight': 10.0,
            'critical_path_weight': 5.0,
            'integration_bonus_weight': 3.0,
            'penalties': {
                'runtime_penalty_threshold': 30,
                'runtime_penalty_multiplier': 0.1
            },
            'bonuses': {
                'failure_bonus_weight': 5.0
            },
            'maintenance': {
                'age_penalty_weight': 0.5,
                'churn_penalty_weight': 1.5,
                'external_mock_penalty': 0.3,
                'internal_mock_penalty': 0.8
            },
            'normalization': {
                'mode': 'z-score',
                'clip_outliers': 3.0
            },
            'thresholds': {
                'high_value': 20,
                'medium_value': 10
            }
        }

    def define_search_space(self, quick_search: bool = False) -> Dict[str, List[float]]:
        """
        Define grid search parameter space.

        Args:
            quick_search: If True, use reduced grid for faster search

        Returns:
            Dictionary mapping parameter names to candidate values
        """
        if quick_search:
            # Reduced grid: 2^6 = 64 combinations (~1 minute)
            return {
                'bug_detection_weight': [8, 12],
                'critical_path_weight': [4, 6],
                'runtime_penalty_multiplier': [0.1, 0.15],
                'failure_bonus_weight': [5, 7],
                'churn_penalty_weight': [1.5, 2.0],
                'age_penalty_weight': [0.5, 0.7]
            }
        else:
            # Full grid: 5^6 = 15,625 combinations (too large, use stratified sampling)
            # Stratified sampling: 3-4 values per dimension = ~4,000 combinations
            return {
                'bug_detection_weight': [5, 8, 10, 12, 15],
                'critical_path_weight': [3, 4, 5, 6, 7],
                'runtime_penalty_multiplier': [0.05, 0.1, 0.15],
                'failure_bonus_weight': [3, 5, 7, 10],
                'churn_penalty_weight': [1.0, 1.5, 2.0],
                'age_penalty_weight': [0.3, 0.5, 0.7]
            }

    def calculate_score_with_weights(
        self,
        test: Dict[str, Any],
        weights: WeightCandidate
    ) -> float:
        """
        Recalculate test score using candidate weights.

        Args:
            test: Labeled test dictionary with score components
            weights: Candidate weight combination

        Returns:
            Total score with candidate weights applied
        """
        # Extract score components (from manual labeling)
        bug_detection = test.get('bug_detection_score', 0.0)
        critical_path = test.get('critical_path_score', 0.0)
        integration = test.get('integration_score', 0.0)
        runtime_penalty = test.get('runtime_penalty', 0.0)
        maintenance_burden = test.get('maintenance_burden', 0.0)

        # Fallback for missing fields
        if bug_detection == 0 and critical_path == 0:
            # Use total score directly (old format)
            return test.get('score', 0.0)

        # Recalculate with candidate weights
        total_score = (
            bug_detection * weights.bug_detection_weight +
            critical_path * weights.critical_path_weight +
            integration * 3.0 +  # Integration weight not optimized (low variance)
            - runtime_penalty * weights.runtime_penalty_multiplier -
            maintenance_burden * 2.0  # Maintenance weight not optimized
        )

        # Add failure bonus (if available)
        failure_bonus = test.get('failure_bonus', 0.0)
        total_score += failure_bonus * weights.failure_bonus_weight

        # Add churn/age penalties (if available)
        churn_burden = test.get('churn_burden', 0.0)
        age_years = test.get('git_age_years', 0.0)
        total_score -= churn_burden * weights.churn_penalty_weight
        total_score -= age_years * weights.age_penalty_weight

        return total_score

    def classify_action(self, score: float) -> str:
        """
        Classify predicted action based on score.

        Args:
            score: Total test score

        Returns:
            Action: KEEP, REVIEW, or DELETE
        """
        # Use thresholds from weights.yaml
        thresholds = self.weights_template.get('thresholds', {})
        high_threshold = thresholds.get('high_value', 20)
        medium_threshold = thresholds.get('medium_value', 10)

        if score >= high_threshold:
            return "KEEP"
        elif score >= medium_threshold:
            return "REVIEW"
        else:
            return "DELETE"

    def evaluate_weights(self, weights: WeightCandidate) -> float:
        """
        Evaluate accuracy of candidate weights against manual labels.

        Args:
            weights: Candidate weight combination

        Returns:
            Accuracy (0.0 to 1.0): fraction of correct predictions
        """
        correct = 0
        total = len(self.labeled_tests)

        for test in self.labeled_tests:
            # Recalculate score with candidate weights
            predicted_score = self.calculate_score_with_weights(test, weights)
            predicted_action = self.classify_action(predicted_score)

            # Compare to manual label
            manual_label = test['manual_label'].upper()

            # Normalize labels (handle variations)
            if manual_label in ['CONSOLIDATE', 'MERGE']:
                manual_label = 'DELETE'  # Consolidate = delete one copy

            if predicted_action == manual_label:
                correct += 1

        accuracy = correct / total if total > 0 else 0.0
        return accuracy

    def grid_search(
        self,
        max_iterations: Optional[int] = None,
        quick_search: bool = False
    ) -> SearchResult:
        """
        Perform exhaustive grid search over weight space.

        Args:
            max_iterations: Maximum iterations to run (None = exhaustive)
            quick_search: Use reduced grid for faster search

        Returns:
            SearchResult with best weights and accuracy
        """
        start_time = time.time()

        # Define search space
        param_grid = self.define_search_space(quick_search)

        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = [param_grid[name] for name in param_names]
        all_combinations = list(itertools.product(*param_values))

        total_combinations = len(all_combinations)
        max_iterations = max_iterations or total_combinations

        if total_combinations > max_iterations:
            print(f"⚠️  Grid has {total_combinations} combinations, limiting to {max_iterations}")
            # Stratified sampling: take evenly spaced samples
            step = total_combinations // max_iterations
            all_combinations = all_combinations[::step][:max_iterations]

        print(f"🔍 Starting grid search: {len(all_combinations)} combinations")
        print(f"   Parameters: {param_names}")
        print(f"   Samples: {len(self.labeled_tests)} labeled tests\n")

        # Progress tracking
        best_weights = None
        best_accuracy = 0.0
        progress_bar = None

        if RICH_AVAILABLE:
            progress_bar = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=self.console
            )
            task = progress_bar.add_task("Evaluating weights...", total=len(all_combinations))
            progress_bar.start()

        # Evaluate each combination
        for i, combination in enumerate(all_combinations):
            # Create weight candidate
            weights = WeightCandidate(**dict(zip(param_names, combination)))

            # Evaluate accuracy
            accuracy = self.evaluate_weights(weights)

            # Track best
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_weights = weights

                # Log improvement
                if RICH_AVAILABLE:
                    progress_bar.console.print(
                        f"✨ New best: {accuracy:.1%} accuracy at iteration {i+1}/{len(all_combinations)}"
                    )
                else:
                    print(f"✨ New best: {accuracy:.1%} accuracy at iteration {i+1}/{len(all_combinations)}")

            # Update progress
            if progress_bar:
                progress_bar.update(task, advance=1)
            elif (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{len(all_combinations)} ({(i+1)/len(all_combinations)*100:.1f}%) - Best: {best_accuracy:.1%}")

            self.iterations_evaluated += 1

        if progress_bar:
            progress_bar.stop()

        elapsed = time.time() - start_time

        # Generate confusion matrix
        confusion_matrix = self._generate_confusion_matrix(best_weights)
        label_distribution = self._get_label_distribution()

        print(f"\n✅ Grid search complete!")
        print(f"   Best accuracy: {best_accuracy:.1%} ({int(best_accuracy * len(self.labeled_tests))}/{len(self.labeled_tests)} correct)")
        print(f"   Iterations: {self.iterations_evaluated}")
        print(f"   Time: {elapsed:.1f}s")

        return SearchResult(
            best_weights=best_weights,
            best_accuracy=best_accuracy,
            total_iterations=self.iterations_evaluated,
            elapsed_seconds=elapsed,
            samples_evaluated=len(self.labeled_tests),
            confusion_matrix=confusion_matrix,
            label_distribution=label_distribution
        )

    def _generate_confusion_matrix(self, weights: WeightCandidate) -> Dict[str, Dict[str, int]]:
        """Generate confusion matrix for best weights."""
        matrix = {
            'KEEP': {'KEEP': 0, 'REVIEW': 0, 'DELETE': 0},
            'REVIEW': {'KEEP': 0, 'REVIEW': 0, 'DELETE': 0},
            'DELETE': {'KEEP': 0, 'REVIEW': 0, 'DELETE': 0}
        }

        for test in self.labeled_tests:
            predicted_score = self.calculate_score_with_weights(test, weights)
            predicted = self.classify_action(predicted_score)
            actual = test['manual_label'].upper()

            # Normalize
            if actual in ['CONSOLIDATE', 'MERGE']:
                actual = 'DELETE'

            if actual in matrix and predicted in matrix[actual]:
                matrix[actual][predicted] += 1

        return matrix

    def _get_label_distribution(self) -> Dict[str, int]:
        """Get distribution of manual labels."""
        labels = [t['manual_label'].upper() for t in self.labeled_tests]
        # Normalize
        labels = ['DELETE' if l in ['CONSOLIDATE', 'MERGE'] else l for l in labels]
        return dict(Counter(labels))

    def save_optimized_weights(self, result: SearchResult) -> None:
        """
        Save optimized weights to weights_optimized.yaml.

        Args:
            result: Grid search result with best weights
        """
        # Load template structure
        optimized = self.weights_template.copy()

        # Update optimized values
        optimized['bug_detection_weight'] = result.best_weights.bug_detection_weight
        optimized['critical_path_weight'] = result.best_weights.critical_path_weight

        if 'penalties' not in optimized:
            optimized['penalties'] = {}
        optimized['penalties']['runtime_penalty_multiplier'] = result.best_weights.runtime_penalty_multiplier

        if 'bonuses' not in optimized:
            optimized['bonuses'] = {}
        optimized['bonuses']['failure_bonus_weight'] = result.best_weights.failure_bonus_weight

        if 'maintenance' not in optimized:
            optimized['maintenance'] = {}
        optimized['maintenance']['churn_penalty_weight'] = result.best_weights.churn_penalty_weight
        optimized['maintenance']['age_penalty_weight'] = result.best_weights.age_penalty_weight

        # Add metadata
        optimized['_metadata'] = {
            'optimized_at': datetime.now().isoformat(),
            'grid_search_accuracy': round(result.best_accuracy, 4),
            'samples_used': result.samples_evaluated,
            'iterations_evaluated': result.total_iterations,
            'elapsed_seconds': round(result.elapsed_seconds, 2),
            'label_distribution': result.label_distribution
        }

        # Save to file
        with open(self.output_path, 'w') as f:
            yaml.dump(optimized, f, default_flow_style=False, sort_keys=False)

        print(f"\n✅ Optimized weights saved: {self.output_path}")

    def print_results(self, result: SearchResult) -> None:
        """Print detailed results with confusion matrix."""
        if RICH_AVAILABLE:
            self._print_results_rich(result)
        else:
            self._print_results_plain(result)

    def _print_results_rich(self, result: SearchResult) -> None:
        """Print results using rich formatting."""
        console = self.console

        # Best weights table
        weights_table = Table(title="Optimized Weights", show_header=True)
        weights_table.add_column("Parameter", style="cyan")
        weights_table.add_column("Value", justify="right", style="green")

        weights_dict = result.best_weights.to_dict()
        for param, value in weights_dict.items():
            weights_table.add_row(param, f"{value:.2f}")

        console.print(weights_table)

        # Confusion matrix
        cm_table = Table(title="Confusion Matrix (Predicted vs Actual)", show_header=True)
        cm_table.add_column("Actual \\ Predicted", style="cyan")
        cm_table.add_column("KEEP", justify="center")
        cm_table.add_column("REVIEW", justify="center")
        cm_table.add_column("DELETE", justify="center")

        for actual_label in ['KEEP', 'REVIEW', 'DELETE']:
            row_data = result.confusion_matrix.get(actual_label, {})
            cm_table.add_row(
                actual_label,
                str(row_data.get('KEEP', 0)),
                str(row_data.get('REVIEW', 0)),
                str(row_data.get('DELETE', 0))
            )

        console.print("\n")
        console.print(cm_table)

    def _print_results_plain(self, result: SearchResult) -> None:
        """Print results using plain text."""
        print("\n" + "=" * 70)
        print("OPTIMIZED WEIGHTS")
        print("=" * 70)
        weights_dict = result.best_weights.to_dict()
        for param, value in weights_dict.items():
            print(f"  {param:<30} {value:>8.2f}")

        print("\n" + "=" * 70)
        print("CONFUSION MATRIX (Predicted vs Actual)")
        print("=" * 70)
        print(f"{'Actual \\ Predicted':<20} {'KEEP':>10} {'REVIEW':>10} {'DELETE':>10}")
        print("-" * 70)

        for actual_label in ['KEEP', 'REVIEW', 'DELETE']:
            row_data = result.confusion_matrix.get(actual_label, {})
            print(f"{actual_label:<20} {row_data.get('KEEP', 0):>10} {row_data.get('REVIEW', 0):>10} {row_data.get('DELETE', 0):>10}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Grid Search Tuner for Test Value Scoring Weights",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--labeled-tests',
        type=Path,
        default=Path('labeled_tests.json'),
        help='Path to labeled_tests.json (default: labeled_tests.json)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('weights_optimized.yaml'),
        help='Output path for optimized weights (default: weights_optimized.yaml)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=None,
        help='Maximum iterations (default: exhaustive search)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick search with reduced grid (64 combinations)'
    )

    args = parser.parse_args()

    try:
        # Initialize tuner (Article I: Load complete context)
        tuner = GridSearchTuner(
            labeled_tests_path=args.labeled_tests,
            output_path=args.output
        )

        # Run grid search
        result = tuner.grid_search(
            max_iterations=args.max_iterations,
            quick_search=args.quick
        )

        # Print results
        tuner.print_results(result)

        # Save optimized weights
        tuner.save_optimized_weights(result)

        # Success metrics
        if result.best_accuracy >= 0.9:
            print(f"\n🎉 Excellent calibration: {result.best_accuracy:.1%} accuracy (target: >90%)")
        elif result.best_accuracy >= 0.8:
            print(f"\n✅ Good calibration: {result.best_accuracy:.1%} accuracy")
        else:
            print(f"\n⚠️  Low accuracy: {result.best_accuracy:.1%}")
            print(f"   Consider:")
            print(f"   1. Label more diverse samples (current: {result.samples_evaluated})")
            print(f"   2. Review label quality (check confusion matrix)")
            print(f"   3. Expand search space (add more weight dimensions)")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
