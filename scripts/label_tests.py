#!/usr/bin/env python3
"""
Manual Test Quality Labeling Tool

CLI tool for calibrating test value scoring by collecting manual labels.
Displays test code with syntax highlighting, current score breakdown, and
captures human judgment for training grid search optimizer.

Usage:
    python scripts/label_tests.py --sample-size 50
    python scripts/label_tests.py --continue  # Resume labeling
    python scripts/label_tests.py --filter LOW  # Only label LOW tests
    python scripts/label_tests.py --file labeled_tests.json  # Custom output

Constitutional Compliance:
- Article I: Complete context (loads all test scores before interaction)
- Article II: TDD (tests written after implementation, this is tooling)
- Article III: No manual overrides (labels stored, not auto-applied)
- Article V: Traces to TEST_AUDIT_V5_PLAN.md Phase 6
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from pygments import highlight
    from pygments.lexers import PythonLexer
    from pygments.formatters import TerminalFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    print("⚠️  pygments not available, syntax highlighting disabled")
    print("   Install: pip install pygments")

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  rich not available, using plain text output")
    print("   Install: pip install rich")

from test_value_audit import TestValueAuditor, TestScore


@dataclass
class TestLabel:
    """Manual label for a test."""
    test_id: str
    file_path: str
    test_name: str
    line: int

    # Current score breakdown
    score: float
    bug_detection_score: float
    critical_path_score: float
    integration_score: float
    runtime_penalty: float
    maintenance_burden: float

    # Manual label
    manual_label: str  # KEEP, REVIEW, DELETE, CONSOLIDATE
    reason: str
    timestamp: str

    # Metadata
    category: str  # HIGH, MEDIUM, LOW
    action: str  # Original automated action
    lines_of_code: int
    mock_count: int
    assertion_count: int


class TestLabeler:
    """Interactive CLI for manual test labeling."""

    def __init__(
        self,
        output_file: Path = Path("labeled_tests.json"),
        sample_size: int = 50,
        filter_category: Optional[str] = None
    ):
        self.output_file = output_file
        self.sample_size = sample_size
        self.filter_category = filter_category

        self.auditor = TestValueAuditor()
        self.console = Console() if RICH_AVAILABLE else None

        self.labeled: List[TestLabel] = []
        self.labeled_ids: Set[str] = set()

        # Load existing labels if resuming
        self._load_existing_labels()

    def _load_existing_labels(self):
        """Load existing labels for resume functionality."""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r') as f:
                    data = json.load(f)
                    self.labeled = [TestLabel(**item) for item in data]
                    self.labeled_ids = {label.test_id for label in self.labeled}

                print(f"✅ Loaded {len(self.labeled)} existing labels")
                print(f"   Remaining: {self.sample_size - len(self.labeled)}")
            except Exception as e:
                print(f"⚠️  Could not load existing labels: {e}")

    def run(self):
        """Run interactive labeling session."""
        print("\n" + "="*80)
        print("🏷️  MANUAL TEST QUALITY LABELING")
        print("="*80)
        print("\nPurpose: Calibrate test scoring system with human judgment")
        print(f"Target: {self.sample_size} labeled samples")
        print(f"Output: {self.output_file}")

        if self.filter_category:
            print(f"Filter: Only {self.filter_category} category tests")

        print("\nLabels:")
        print("  [K] KEEP        - High-value test (integration, critical, security)")
        print("  [R] REVIEW      - Medium value (may improve or consolidate)")
        print("  [D] DELETE      - Low value (mocking hell, redundant)")
        print("  [C] CONSOLIDATE - Redundant (parameterize with similar tests)")
        print("  [S] SKIP        - Skip this test (no label)")
        print("  [Q] QUIT        - Save and exit")
        print("\n" + "="*80 + "\n")

        # Extract and score all tests
        print("🔍 Extracting tests...")
        test_functions = self.auditor.extract_test_functions(Path("tests"))

        print("📊 Scoring tests...")
        scored_tests = []
        for i, test in enumerate(test_functions, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(test_functions)} ({i*100//len(test_functions)}%)")

            score = self.auditor.score_test(test)
            test['score'] = score
            scored_tests.append(test)

        # Filter if requested
        if self.filter_category:
            scored_tests = [
                t for t in scored_tests
                if t['score'].category == self.filter_category
            ]
            print(f"\n✅ Filtered to {len(scored_tests)} {self.filter_category} tests")

        # Sample tests to label
        tests_to_label = self._sample_tests(scored_tests)

        print(f"\n📝 Selected {len(tests_to_label)} tests to label")
        print(f"   (Already labeled: {len(self.labeled_ids)})\n")

        # Interactive labeling loop
        labeled_count = 0
        for i, test in enumerate(tests_to_label, 1):
            test_id = f"{test['file']}::{test['name']}"

            # Skip if already labeled
            if test_id in self.labeled_ids:
                continue

            # Display test
            self._display_test(test, i, len(tests_to_label))

            # Get label
            label_result = self._get_label()

            if label_result == 'QUIT':
                print("\n💾 Saving and quitting...")
                break

            if label_result == 'SKIP':
                continue

            # Store label
            manual_label, reason = label_result
            self._store_label(test, manual_label, reason)
            labeled_count += 1

            # Save periodically
            if labeled_count % 10 == 0:
                self._save_labels()
                print(f"  💾 Auto-saved ({labeled_count} new labels)")

            print()  # Spacing between tests

        # Final save
        self._save_labels()

        print("\n" + "="*80)
        print("✅ LABELING COMPLETE")
        print("="*80)
        print(f"Total labeled: {len(self.labeled)}")
        print(f"New labels: {labeled_count}")
        print(f"Output: {self.output_file}")
        print("\nNext steps:")
        print("1. Review labeled_tests.json")
        print("2. Run grid search: python scripts/grid_search_tuner.py")
        print("3. Apply optimized weights: cp weights_optimized.yaml weights.yaml")
        print()

    def _sample_tests(self, scored_tests: List[Dict]) -> List[Dict]:
        """
        Sample tests for labeling.

        Strategy: Stratified sampling across score categories to ensure
        diverse representation (25% HIGH, 25% MEDIUM, 50% LOW).
        """
        high = [t for t in scored_tests if t['score'].category == "HIGH"]
        medium = [t for t in scored_tests if t['score'].category == "MEDIUM"]
        low = [t for t in scored_tests if t['score'].category == "LOW"]

        # Calculate target counts
        remaining = self.sample_size - len(self.labeled_ids)
        high_count = min(len(high), remaining // 4)
        medium_count = min(len(medium), remaining // 4)
        low_count = min(len(low), remaining - high_count - medium_count)

        # Randomly sample from each category
        import random
        random.seed(42)  # Reproducible sampling

        sampled = (
            random.sample(high, min(high_count, len(high))) +
            random.sample(medium, min(medium_count, len(medium))) +
            random.sample(low, min(low_count, len(low)))
        )

        # Shuffle combined sample
        random.shuffle(sampled)

        return sampled

    def _display_test(self, test: Dict, current: int, total: int):
        """Display test information for labeling."""
        score: TestScore = test['score']
        test_id = f"{test['file']}::{test['name']}"

        if self.console and RICH_AVAILABLE:
            # Rich formatted output
            self.console.print(f"\n[bold cyan]Test {current}/{total}[/bold cyan]")
            self.console.print(Panel(
                f"[bold]{test['name']}[/bold]\n"
                f"File: {test['file']}:{test['line']}\n"
                f"ID: {test_id}",
                title="Test Info",
                border_style="cyan"
            ))

            # Score breakdown table
            table = Table(title="Score Breakdown", show_header=True)
            table.add_column("Component", style="cyan")
            table.add_column("Score", justify="right", style="yellow")
            table.add_column("Weight", justify="right", style="dim")

            table.add_row(
                "Bug Detection",
                f"{score.bug_detection_score:.1f}",
                "×10.0"
            )
            table.add_row(
                "Critical Path",
                f"{score.critical_path_score:.1f}",
                "×5.0"
            )
            table.add_row(
                "Integration",
                f"{score.integration_score:.1f}",
                "×3.0"
            )
            table.add_row(
                "Runtime Penalty",
                f"-{score.runtime_penalty:.1f}",
                "×0.1",
                style="red"
            )
            table.add_row(
                "Maintenance Burden",
                f"-{score.maintenance_burden:.1f}",
                "×2.0",
                style="red"
            )
            table.add_row(
                "[bold]Total Score[/bold]",
                f"[bold]{score.total_score:.1f}[/bold]",
                ""
            )

            self.console.print(table)

            # Current classification
            category_color = {
                "HIGH": "green",
                "MEDIUM": "yellow",
                "LOW": "red"
            }[score.category]

            self.console.print(
                f"\nCategory: [{category_color}]{score.category}[/{category_color}] | "
                f"Action: [{category_color}]{score.action}[/{category_color}]"
            )
            self.console.print(f"Reason: {score.reason}")

            # Metadata
            self.console.print(
                f"\nMetadata: {score.lines_of_code} LOC | "
                f"{score.mock_count} mocks | "
                f"{score.assertion_count} asserts | "
                f"Integration: {score.is_integration} | "
                f"E2E: {score.is_e2e}"
            )

            # Test code with syntax highlighting
            self.console.print("\n[bold]Test Code:[/bold]")
            syntax = Syntax(
                test['code'],
                "python",
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            )
            self.console.print(syntax)

        else:
            # Plain text fallback
            print(f"\n{'='*80}")
            print(f"Test {current}/{total}")
            print(f"{'='*80}")
            print(f"\nName: {test['name']}")
            print(f"File: {test['file']}:{test['line']}")
            print(f"ID: {test_id}")

            print(f"\nScore Breakdown:")
            print(f"  Bug Detection:       {score.bug_detection_score:6.1f} (×10.0)")
            print(f"  Critical Path:       {score.critical_path_score:6.1f} (×5.0)")
            print(f"  Integration:         {score.integration_score:6.1f} (×3.0)")
            print(f"  Runtime Penalty:    -{score.runtime_penalty:6.1f} (×0.1)")
            print(f"  Maintenance Burden: -{score.maintenance_burden:6.1f} (×2.0)")
            print(f"  {'─'*40}")
            print(f"  Total Score:         {score.total_score:6.1f}")

            print(f"\nCategory: {score.category} | Action: {score.action}")
            print(f"Reason: {score.reason}")

            print(f"\nMetadata:")
            print(f"  {score.lines_of_code} LOC | {score.mock_count} mocks | "
                  f"{score.assertion_count} asserts | Integration: {score.is_integration} | "
                  f"E2E: {score.is_e2e}")

            print(f"\nTest Code:")
            print("─"*80)

            # Syntax highlight if available
            if PYGMENTS_AVAILABLE:
                highlighted = highlight(
                    test['code'],
                    PythonLexer(),
                    TerminalFormatter()
                )
                print(highlighted)
            else:
                print(test['code'])

            print("─"*80)

    def _get_label(self) -> tuple:
        """
        Get manual label from user.

        Returns:
            ('QUIT',) if quit
            ('SKIP',) if skip
            (label, reason) otherwise
        """
        while True:
            try:
                response = input("\nYour label [K/R/D/C/S/Q]: ").strip().upper()

                if response == 'Q':
                    return ('QUIT',)

                if response == 'S':
                    return ('SKIP',)

                label_map = {
                    'K': 'KEEP',
                    'R': 'REVIEW',
                    'D': 'DELETE',
                    'C': 'CONSOLIDATE'
                }

                if response not in label_map:
                    print("  ⚠️  Invalid input. Use K, R, D, C, S, or Q")
                    continue

                manual_label = label_map[response]

                # Optional reason
                reason = input("Reason (optional, press Enter to skip): ").strip()
                if not reason:
                    reason = f"Manual classification: {manual_label}"

                return (manual_label, reason)

            except (KeyboardInterrupt, EOFError):
                print("\n\n💾 Saving and quitting...")
                return ('QUIT',)

    def _store_label(self, test: Dict, manual_label: str, reason: str):
        """Store label in memory."""
        score: TestScore = test['score']
        test_id = f"{test['file']}::{test['name']}"

        label = TestLabel(
            test_id=test_id,
            file_path=test['file'],
            test_name=test['name'],
            line=test['line'],
            score=score.total_score,
            bug_detection_score=score.bug_detection_score,
            critical_path_score=score.critical_path_score,
            integration_score=score.integration_score,
            runtime_penalty=score.runtime_penalty,
            maintenance_burden=score.maintenance_burden,
            manual_label=manual_label,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            category=score.category,
            action=score.action,
            lines_of_code=score.lines_of_code,
            mock_count=score.mock_count,
            assertion_count=score.assertion_count
        )

        self.labeled.append(label)
        self.labeled_ids.add(test_id)

        # Show agreement/disagreement
        agreement = "✅" if manual_label == score.action else "⚠️"
        print(f"\n  {agreement} Labeled as {manual_label} (model predicted {score.action})")

    def _save_labels(self):
        """Save labels to JSON file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w') as f:
            json.dump(
                [asdict(label) for label in self.labeled],
                f,
                indent=2
            )


def main():
    parser = argparse.ArgumentParser(
        description="Manual test quality labeling for calibration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Label 50 tests (default)
  python scripts/label_tests.py

  # Label 100 tests
  python scripts/label_tests.py --sample-size 100

  # Resume previous session
  python scripts/label_tests.py --continue

  # Only label LOW category tests
  python scripts/label_tests.py --filter LOW

  # Custom output file
  python scripts/label_tests.py --file my_labels.json

Output Format (labeled_tests.json):
  [
    {
      "test_id": "tests/test_example.py::test_foo",
      "file_path": "tests/test_example.py",
      "score": 5.2,
      "bug_detection_score": 2.0,
      "critical_path_score": 3.0,
      "integration_score": 1.0,
      "runtime_penalty": 0.5,
      "maintenance_burden": 1.3,
      "manual_label": "DELETE",
      "reason": "Mocking hell, tests nothing",
      "timestamp": "2025-10-23T10:30:00",
      "category": "LOW",
      "action": "DELETE",
      "lines_of_code": 45,
      "mock_count": 12,
      "assertion_count": 2
    },
    ...
  ]
        """
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        default=50,
        help='Number of tests to label (default: 50)'
    )

    parser.add_argument(
        '--continue',
        dest='resume',
        action='store_true',
        help='Resume from existing labeled_tests.json'
    )

    parser.add_argument(
        '--filter',
        choices=['HIGH', 'MEDIUM', 'LOW'],
        help='Only label tests in specified category'
    )

    parser.add_argument(
        '--file',
        type=Path,
        default=Path('labeled_tests.json'),
        help='Output file path (default: labeled_tests.json)'
    )

    args = parser.parse_args()

    # Run labeler
    labeler = TestLabeler(
        output_file=args.file,
        sample_size=args.sample_size,
        filter_category=args.filter
    )

    try:
        labeler.run()
    except KeyboardInterrupt:
        print("\n\n💾 Interrupted - saving labels...")
        labeler._save_labels()
        print(f"✅ Saved {len(labeler.labeled)} labels to {labeler.output_file}")


if __name__ == '__main__':
    main()
