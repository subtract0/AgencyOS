#!/usr/bin/env python3
"""
Demo: Grid Search Tuner with Sample Labeled Tests

Shows how grid search optimization works with a small labeled dataset.
"""

import json
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from grid_search_tuner import GridSearchTuner


def create_demo_labeled_tests(output_path: Path) -> None:
    """Create sample labeled_tests.json for demonstration."""
    demo_labels = {
        "labels": [
            # HIGH VALUE tests (KEEP)
            {
                "test_id": "tests/test_auth.py::test_jwt_validation",
                "file_path": "tests/test_auth.py",
                "test_name": "test_jwt_validation",
                "line": 45,
                "score": 28.0,
                "bug_detection_score": 2.8,
                "critical_path_score": 2.5,
                "integration_score": 1.9,
                "runtime_penalty": 0.5,
                "maintenance_burden": 1.2,
                "manual_label": "KEEP",
                "reason": "Critical security test, catches real bugs",
                "timestamp": "2025-10-23T10:00:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 42,
                "mock_count": 2,
                "assertion_count": 6
            },
            {
                "test_id": "tests/test_payment.py::test_payment_flow_e2e",
                "file_path": "tests/test_payment.py",
                "test_name": "test_payment_flow_e2e",
                "line": 120,
                "score": 32.0,
                "bug_detection_score": 3.2,
                "critical_path_score": 2.8,
                "integration_score": 2.5,
                "runtime_penalty": 1.0,
                "maintenance_burden": 0.8,
                "manual_label": "KEEP",
                "reason": "Critical E2E test for business revenue",
                "timestamp": "2025-10-23T10:05:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 65,
                "mock_count": 1,
                "assertion_count": 8
            },
            {
                "test_id": "tests/test_api.py::test_rate_limiting",
                "file_path": "tests/test_api.py",
                "test_name": "test_rate_limiting",
                "line": 88,
                "score": 24.0,
                "bug_detection_score": 2.4,
                "critical_path_score": 2.0,
                "integration_score": 1.5,
                "runtime_penalty": 0.8,
                "maintenance_burden": 1.5,
                "manual_label": "KEEP",
                "reason": "Security critical, prevents DoS",
                "timestamp": "2025-10-23T10:10:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 50,
                "mock_count": 3,
                "assertion_count": 5
            },
            {
                "test_id": "tests/test_db.py::test_transaction_rollback",
                "file_path": "tests/test_db.py",
                "test_name": "test_transaction_rollback",
                "line": 210,
                "score": 26.0,
                "bug_detection_score": 2.6,
                "critical_path_score": 2.2,
                "integration_score": 1.8,
                "runtime_penalty": 0.6,
                "maintenance_burden": 1.0,
                "manual_label": "KEEP",
                "reason": "Data integrity critical",
                "timestamp": "2025-10-23T10:15:00",
                "category": "HIGH",
                "action": "KEEP",
                "lines_of_code": 58,
                "mock_count": 2,
                "assertion_count": 7
            },
            # MEDIUM VALUE tests (REVIEW)
            {
                "test_id": "tests/test_utils.py::test_date_parsing_edge_cases",
                "file_path": "tests/test_utils.py",
                "test_name": "test_date_parsing_edge_cases",
                "line": 45,
                "score": 15.0,
                "bug_detection_score": 1.5,
                "critical_path_score": 1.0,
                "integration_score": 0.8,
                "runtime_penalty": 1.2,
                "maintenance_burden": 2.0,
                "manual_label": "REVIEW",
                "reason": "Good edge case coverage, but complex",
                "timestamp": "2025-10-23T10:20:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 72,
                "mock_count": 5,
                "assertion_count": 4
            },
            {
                "test_id": "tests/test_cache.py::test_cache_invalidation",
                "file_path": "tests/test_cache.py",
                "test_name": "test_cache_invalidation",
                "line": 92,
                "score": 13.0,
                "bug_detection_score": 1.3,
                "critical_path_score": 0.9,
                "integration_score": 0.6,
                "runtime_penalty": 1.5,
                "maintenance_burden": 2.5,
                "manual_label": "REVIEW",
                "reason": "Performance optimization test",
                "timestamp": "2025-10-23T10:25:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 68,
                "mock_count": 6,
                "assertion_count": 3
            },
            {
                "test_id": "tests/test_validators.py::test_email_validation_complex",
                "file_path": "tests/test_validators.py",
                "test_name": "test_email_validation_complex",
                "line": 156,
                "score": 12.0,
                "bug_detection_score": 1.2,
                "critical_path_score": 0.8,
                "integration_score": 0.5,
                "runtime_penalty": 1.8,
                "maintenance_burden": 2.8,
                "manual_label": "REVIEW",
                "reason": "Many edge cases, brittle",
                "timestamp": "2025-10-23T10:30:00",
                "category": "MEDIUM",
                "action": "REVIEW",
                "lines_of_code": 85,
                "mock_count": 7,
                "assertion_count": 2
            },
            # LOW VALUE tests (DELETE)
            {
                "test_id": "tests/test_models.py::test_user_model_repr",
                "file_path": "tests/test_models.py",
                "test_name": "test_user_model_repr",
                "line": 34,
                "score": 6.0,
                "bug_detection_score": 0.4,
                "critical_path_score": 0.3,
                "integration_score": 0.2,
                "runtime_penalty": 2.5,
                "maintenance_burden": 4.5,
                "manual_label": "DELETE",
                "reason": "Tests implementation detail (__repr__)",
                "timestamp": "2025-10-23T10:35:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 95,
                "mock_count": 10,
                "assertion_count": 1
            },
            {
                "test_id": "tests/test_internal.py::test_private_method",
                "file_path": "tests/test_internal.py",
                "test_name": "test_private_method",
                "line": 78,
                "score": 4.0,
                "bug_detection_score": 0.3,
                "critical_path_score": 0.2,
                "integration_score": 0.1,
                "runtime_penalty": 3.0,
                "maintenance_burden": 5.0,
                "manual_label": "DELETE",
                "reason": "Tests private method, mocking hell",
                "timestamp": "2025-10-23T10:40:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 110,
                "mock_count": 12,
                "assertion_count": 1
            },
            {
                "test_id": "tests/test_legacy.py::test_deprecated_function",
                "file_path": "tests/test_legacy.py",
                "test_name": "test_deprecated_function",
                "line": 145,
                "score": 3.0,
                "bug_detection_score": 0.2,
                "critical_path_score": 0.1,
                "integration_score": 0.05,
                "runtime_penalty": 3.5,
                "maintenance_burden": 6.0,
                "manual_label": "DELETE",
                "reason": "Tests deprecated code",
                "timestamp": "2025-10-23T10:45:00",
                "category": "LOW",
                "action": "DELETE",
                "lines_of_code": 125,
                "mock_count": 15,
                "assertion_count": 1
            }
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(demo_labels, f, indent=2)

    print(f"✅ Created demo labeled tests: {output_path}")
    print(f"   Distribution: 4 KEEP, 3 REVIEW, 3 DELETE")


def main():
    """Run grid search demo."""
    print("=" * 70)
    print("GRID SEARCH TUNER DEMO")
    print("=" * 70)
    print("\nThis demo shows how to optimize test value scoring weights")
    print("using manual labels from human reviewers.\n")

    # Create demo data
    demo_labels_path = Path("demo_labeled_tests.json")
    demo_output_path = Path("demo_weights_optimized.yaml")

    print("Step 1: Creating sample labeled tests...")
    create_demo_labeled_tests(demo_labels_path)

    print("\nStep 2: Running grid search optimization...")
    print("   Search space: 6 dimensions (64 combinations)")
    print("   Samples: 10 labeled tests")
    print("   Optimization metric: Accuracy (predicted vs manual labels)\n")

    # Initialize tuner
    tuner = GridSearchTuner(
        labeled_tests_path=demo_labels_path,
        output_path=demo_output_path
    )

    # Run quick search
    result = tuner.grid_search(quick_search=True)

    # Print results
    print("\n" + "=" * 70)
    print("OPTIMIZATION RESULTS")
    print("=" * 70)
    tuner.print_results(result)

    # Save optimized weights
    tuner.save_optimized_weights(result)

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(f"1. Review optimized weights: {demo_output_path}")
    print(f"2. Copy to production: cp {demo_output_path} weights.yaml")
    print(f"3. Run V5 audit: python scripts/test_value_audit_v5.py")
    print(f"4. Validate accuracy on full test suite")
    print("\nFor production use:")
    print("  - Label 50+ diverse tests (python scripts/label_tests.py --sample-size 50)")
    print("  - Run full grid search (remove --quick flag for 15,625 combinations)")
    print("  - Target: >90% accuracy\n")

    # Cleanup demo files
    print("Cleaning up demo files...")
    demo_labels_path.unlink()
    demo_output_path.unlink()
    print("✅ Demo complete!\n")


if __name__ == '__main__':
    main()
