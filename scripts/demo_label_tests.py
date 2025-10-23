#!/usr/bin/env python3
"""
Demo: Manual Test Labeling Tool

Demonstrates the label_tests.py CLI tool with simulated user interactions.
Shows how the tool displays test code, score breakdowns, and captures labels.

Usage:
    python scripts/demo_label_tests.py
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from label_tests import TestLabeler


def demo_labeling_session():
    """Run a simulated labeling session."""

    print("\n" + "="*80)
    print("🎬 DEMO: Manual Test Quality Labeling Tool")
    print("="*80)
    print("\nThis demo shows how the labeling tool works with simulated inputs.")
    print("In real usage, you would interactively label tests.\n")

    # Create labeler with small sample
    output_file = Path("demo_labeled_tests.json")
    labeler = TestLabeler(
        output_file=output_file,
        sample_size=3,
        filter_category='LOW'  # Focus on LOW tests for demo
    )

    # Simulate user inputs for 3 tests
    # Format: [label, reason] for each test, then 'Q' to quit
    simulated_inputs = [
        # Test 1: Label as DELETE
        'D',
        'Mocking hell - tests implementation details',

        # Test 2: Label as KEEP (disagreeing with model)
        'K',
        'Actually useful despite low score - critical edge case',

        # Test 3: Label as REVIEW
        'R',
        'Could be improved with refactoring',

        # Quit after 3 labels
        'Q'
    ]

    print("📝 Starting labeling session with simulated inputs...\n")

    # Mock user input
    with patch('builtins.input', side_effect=simulated_inputs):
        try:
            labeler.run()
        except Exception as e:
            # Handle case where not enough tests available
            print(f"\n⚠️  Demo completed with exception: {e}")
            print("   (This is expected if <3 LOW tests exist)")

    # Show results
    if output_file.exists():
        print("\n" + "="*80)
        print("✅ DEMO RESULTS")
        print("="*80)

        import json
        with open(output_file, 'r') as f:
            labels = json.load(f)

        print(f"\nLabeled {len(labels)} tests:")
        for i, label in enumerate(labels, 1):
            print(f"\n{i}. {label['test_name']}")
            print(f"   Score: {label['score']:.1f} ({label['category']})")
            print(f"   Model predicted: {label['action']}")
            print(f"   Manual label: {label['manual_label']}")
            print(f"   Reason: {label['reason']}")

            # Show agreement
            if label['action'] == label['manual_label']:
                print("   ✅ Agreement with model")
            else:
                print("   ⚠️  Disagreement (will improve calibration)")

        print(f"\n📄 Full results saved to: {output_file}")
        print("\nNext step: Run grid search to optimize weights")
        print("  python scripts/grid_search_tuner.py")
    else:
        print("\n⚠️  No labels generated (tests may not be available)")

    print("\n" + "="*80)
    print("🎬 DEMO COMPLETE")
    print("="*80)


if __name__ == '__main__':
    demo_labeling_session()
