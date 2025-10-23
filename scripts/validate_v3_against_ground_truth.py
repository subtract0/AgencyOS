#!/usr/bin/env python3
"""
Validate V3 Audit Results Against Sonnet 4.5 Ground Truth

This script compares V3's classifications against the ground truth I established.
Success criteria: V3's priorities should match ground truth ≥85% of the time.
"""

import json
from pathlib import Path
from collections import defaultdict

def load_json(path: Path):
    with open(path, 'r') as f:
        return json.load(f)

def validate_v3():
    """Compare V3 results against ground truth."""

    # Load files
    print("Loading ground truth and V3 results...")
    ground_truth = load_json(Path("audit_reports/ground_truth_100_tests.json"))

    # Try V4 reprocessed first, then V3
    v4_results_files = sorted(Path("audit_reports").glob("marathon_audit_v4_reprocessed_*.json"))
    v3_results_files = sorted(Path("audit_reports").glob("marathon_audit_v3_*.json"))

    if v4_results_files:
        results_file = v4_results_files[-1]
        version = "V4"
    elif v3_results_files:
        results_file = v3_results_files[-1]
        version = "V3"
    else:
        print("❌ No V3/V4 results found!")
        return

    v3_data = load_json(results_file)  # Latest

    # V3 results can be either a list or dict with 'results' key
    if isinstance(v3_data, dict) and 'results' in v3_data:
        v3_results = v3_data['results']
    else:
        v3_results = v3_data

    print(f"  ✅ Ground Truth: {len(ground_truth)} tests")
    print(f"  ✅ {version} Results: {len(v3_results)} tests")
    print(f"  ✅ {version} File: {results_file.name}\n")

    # Create lookups
    gt_lookup = {gt['test_name']: gt for gt in ground_truth}
    v3_lookup = {v3['name']: v3 for v3 in v3_results}

    # Validation metrics (only compare tests in both datasets)
    common_tests = set(gt_lookup.keys()) & set(v3_lookup.keys())
    total_tests = len(common_tests)
    priority_matches = 0
    purpose_matches = 0
    priority_errors = []
    purpose_errors = []

    print(f"  ℹ️  Common tests (both GT and V3): {total_tests}\n")

    # Compare each test
    for test_name in common_tests:

        gt = gt_lookup[test_name]
        v3 = v3_lookup[test_name]

        # Check priority match
        if gt['correct_priority'] == v3['healing_priority']:
            priority_matches += 1
        else:
            priority_errors.append({
                'test': test_name,
                'ground_truth': gt['correct_priority'],
                'v3_result': v3['healing_priority'],
                'gt_purpose': gt['test_purpose'],
                'v3_purpose': v3.get('test_purpose', 'unknown'),
                'gt_gaps': gt['legitimate_gaps'],
                'v3_gaps': v3['necessary_gaps']
            })

        # Check purpose match
        if gt['test_purpose'] == v3.get('test_purpose', 'unknown'):
            purpose_matches += 1
        else:
            purpose_errors.append({
                'test': test_name,
                'ground_truth': gt['test_purpose'],
                'v3_result': v3.get('test_purpose', 'unknown')
            })

    # Calculate accuracy
    priority_accuracy = (priority_matches / total_tests) * 100
    purpose_accuracy = (purpose_matches / total_tests) * 100

    # Print results
    print("="*80)
    print("📊 V3 VALIDATION RESULTS")
    print("="*80)
    print()
    print(f"Total Tests: {total_tests}")
    print()
    print(f"Priority Accuracy: {priority_matches}/{total_tests} ({priority_accuracy:.1f}%)")
    print(f"Purpose Accuracy: {purpose_matches}/{total_tests} ({purpose_accuracy:.1f}%)")
    print()

    # Success criteria
    if priority_accuracy >= 85:
        print("✅ VALIDATION PASSED: Priority accuracy ≥85%")
    else:
        print(f"❌ VALIDATION FAILED: Priority accuracy {priority_accuracy:.1f}% < 85%")

    if purpose_accuracy >= 90:
        print("✅ VALIDATION PASSED: Purpose accuracy ≥90%")
    else:
        print(f"⚠️  Purpose accuracy {purpose_accuracy:.1f}% < 90% (informational only)")

    # Priority distribution comparison
    print("\n" + "="*80)
    print("PRIORITY DISTRIBUTION COMPARISON")
    print("="*80 + "\n")

    gt_priorities = defaultdict(int)
    v3_priorities = defaultdict(int)

    for gt in ground_truth:
        gt_priorities[gt['correct_priority']] += 1

    for v3 in v3_results:
        v3_priorities[v3['healing_priority']] += 1

    print("| Priority | Ground Truth | V3 Result | Match? |")
    print("|----------|--------------|-----------|--------|")
    for p in ['P0', 'P1', 'P2', 'P3']:
        gt_count = gt_priorities.get(p, 0)
        v3_count = v3_priorities.get(p, 0)
        gt_pct = (gt_count / total_tests) * 100
        v3_pct = (v3_count / total_tests) * 100
        delta = abs(gt_pct - v3_pct)
        match = "✅" if delta < 5 else "⚠️" if delta < 10 else "❌"
        print(f"| {p:8s} | {gt_count:3d} ({gt_pct:5.1f}%) | {v3_count:3d} ({v3_pct:5.1f}%) | {match:6s} |")

    # Show top priority errors
    if priority_errors:
        print("\n" + "="*80)
        print(f"TOP 10 PRIORITY ERRORS (out of {len(priority_errors)} total)")
        print("="*80 + "\n")

        for i, error in enumerate(priority_errors[:10], 1):
            print(f"{i}. {error['test']}")
            print(f"   Ground Truth: {error['ground_truth']} (purpose: {error['gt_purpose']})")
            print(f"   V3 Result:    {error['v3_result']} (purpose: {error['v3_purpose']})")
            print(f"   GT Gaps:      {error['gt_gaps']}")
            print(f"   V3 Gaps:      {error['v3_gaps']}")
            print()

    # Overall assessment
    print("="*80)
    print("OVERALL ASSESSMENT")
    print("="*80 + "\n")

    if priority_accuracy >= 90:
        print("🎯 EXCELLENT: V3 is production-ready")
        print(f"   - Priority accuracy: {priority_accuracy:.1f}%")
        print(f"   - Purpose detection: {purpose_accuracy:.1f}%")
        print("\n✅ Proceed to full 5,408-test audit")
    elif priority_accuracy >= 85:
        print("✅ GOOD: V3 meets success criteria")
        print(f"   - Priority accuracy: {priority_accuracy:.1f}%")
        print(f"   - Minor errors: {len(priority_errors)}")
        print("\n✅ Ready for larger sample (500 tests)")
    else:
        print("⚠️  NEEDS IMPROVEMENT")
        print(f"   - Priority accuracy: {priority_accuracy:.1f}% < 85%")
        print(f"   - Errors to fix: {len(priority_errors)}")
        print("\n❌ Review errors and refine classification logic")

    # Save detailed error report
    error_report_path = Path("audit_reports/v3_validation_errors.json")
    with open(error_report_path, 'w') as f:
        json.dump({
            "summary": {
                "total_tests": total_tests,
                "priority_matches": priority_matches,
                "purpose_matches": purpose_matches,
                "priority_accuracy": priority_accuracy,
                "purpose_accuracy": purpose_accuracy
            },
            "priority_errors": priority_errors,
            "purpose_errors": purpose_errors
        }, f, indent=2)

    print(f"\n📄 Detailed error report: {error_report_path}")

if __name__ == "__main__":
    validate_v3()
