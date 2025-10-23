#!/usr/bin/env python3
"""
Compare V4 vs V5 Test Value Audit Results

Shows improvements from empirical data-driven scoring.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from test_value_audit_v5 import TestValueAuditorV5


def load_v4_results(v4_json_path: Path) -> dict:
    """Load V4 audit results from JSON."""
    with open(v4_json_path, 'r') as f:
        return json.load(f)


def run_v5_audit(sample_size: int = 100) -> list:
    """Run V5 audit on sample tests."""
    print(f"🔍 Running V5 audit on {sample_size} tests...")
    auditor = TestValueAuditorV5()

    tests = auditor.extract_test_functions(Path("tests"))
    scored = [auditor.score_test(t) for t in tests[:sample_size]]

    return scored


def compare_priority_distribution(v4_data: dict, v5_tests: list) -> dict:
    """Compare P1/P2/P3 distribution between V4 and V5."""
    # V4 priorities
    v4_priorities = defaultdict(int)
    for test in v4_data.get('tests', []):
        priority = test.get('priority', 'P3')
        v4_priorities[priority] += 1

    # V5 priorities (based on score thresholds)
    v5_priorities = defaultdict(int)
    for test in v5_tests:
        if test.total_score >= 20:
            v5_priorities['P1'] += 1
        elif test.total_score >= 10:
            v5_priorities['P2'] += 1
        else:
            v5_priorities['P3'] += 1

    return {
        'v4': dict(v4_priorities),
        'v5': dict(v5_priorities)
    }


def analyze_runtime_accuracy(v5_tests: list) -> dict:
    """Analyze how many tests have actual vs heuristic runtime data."""
    actual_runtime = sum(1 for t in v5_tests if t.runtime_source != 'heuristic')
    heuristic_runtime = len(v5_tests) - actual_runtime

    return {
        'actual': actual_runtime,
        'heuristic': heuristic_runtime,
        'percentage_actual': (actual_runtime / len(v5_tests) * 100) if v5_tests else 0
    }


def analyze_ci_insights(v5_tests: list) -> dict:
    """Analyze CI failure insights."""
    bug_detectors = [t for t in v5_tests if t.ci_failures_fixed > 0]
    flaky_tests = [t for t in v5_tests if t.is_flaky]
    no_failures = [t for t in v5_tests if t.ci_failures_total == 0]

    return {
        'bug_detectors': len(bug_detectors),
        'flaky_tests': len(flaky_tests),
        'no_failures': len(no_failures),
        'top_bug_detectors': sorted(bug_detectors, key=lambda t: t.ci_failures_fixed, reverse=True)[:5]
    }


def analyze_brittleness(v5_tests: list) -> dict:
    """Analyze test brittleness from git churn."""
    brittle_tests = [t for t in v5_tests if t.git_co_changes >= 3]
    old_tests = [t for t in v5_tests if t.git_age_years > 2]

    return {
        'brittle_tests': len(brittle_tests),
        'old_tests': len(old_tests),
        'avg_co_changes': sum(t.git_co_changes for t in v5_tests) / len(v5_tests) if v5_tests else 0
    }


def analyze_mock_usage(v5_tests: list) -> dict:
    """Analyze mock classification results."""
    internal_heavy = [t for t in v5_tests if t.internal_mocks > 3]
    external_only = [t for t in v5_tests if t.external_mocks > 0 and t.internal_mocks == 0]

    return {
        'internal_heavy': len(internal_heavy),
        'external_only': len(external_only),
        'avg_internal_mocks': sum(t.internal_mocks for t in v5_tests) / len(v5_tests) if v5_tests else 0,
        'avg_external_mocks': sum(t.external_mocks for t in v5_tests) / len(v5_tests) if v5_tests else 0
    }


def generate_comparison_report(v4_json_path: Path, sample_size: int = 100):
    """Generate comprehensive V4 vs V5 comparison report."""
    print("="*80)
    print("V4 vs V5 Test Value Audit Comparison")
    print("="*80)

    # Load V4 data
    try:
        v4_data = load_v4_results(v4_json_path)
        v4_test_count = len(v4_data.get('tests', []))
        print(f"\n✅ Loaded V4 results: {v4_test_count} tests")
    except Exception as e:
        print(f"\n⚠️  Could not load V4 results: {e}")
        v4_data = {'tests': []}
        v4_test_count = 0

    # Run V5 audit
    v5_tests = run_v5_audit(sample_size)
    print(f"✅ Completed V5 audit: {len(v5_tests)} tests\n")

    # Compare priority distribution
    print("\n" + "="*80)
    print("1. Priority Distribution Comparison")
    print("="*80)

    priorities = compare_priority_distribution(v4_data, v5_tests)

    if priorities['v4']:
        v4_total = sum(priorities['v4'].values())
        print(f"\nV4 Results (from {v4_test_count} tests):")
        for p in ['P1', 'P2', 'P3']:
            count = priorities['v4'].get(p, 0)
            pct = (count / v4_total * 100) if v4_total > 0 else 0
            print(f"  {p}: {count:4d} ({pct:5.1f}%)")

    v5_total = len(v5_tests)
    print(f"\nV5 Results (from {v5_total} tests):")
    for p in ['P1', 'P2', 'P3']:
        count = priorities['v5'].get(p, 0)
        pct = (count / v5_total * 100) if v5_total > 0 else 0
        print(f"  {p}: {count:4d} ({pct:5.1f}%)")

    # Runtime accuracy
    print("\n" + "="*80)
    print("2. Runtime Data Accuracy")
    print("="*80)

    runtime_stats = analyze_runtime_accuracy(v5_tests)
    print(f"\nV4: 100% heuristic (keyword-based estimates)")
    print(f"V5: {runtime_stats['percentage_actual']:.1f}% actual runtime data")
    print(f"    {runtime_stats['actual']} with actual data")
    print(f"    {runtime_stats['heuristic']} with heuristics fallback")

    # CI insights
    print("\n" + "="*80)
    print("3. CI Failure Insights (NEW in V5)")
    print("="*80)

    ci_stats = analyze_ci_insights(v5_tests)
    print(f"\nProven Bug Detectors: {ci_stats['bug_detectors']} tests")
    print(f"Flaky Tests: {ci_stats['flaky_tests']} tests")
    print(f"No CI Failures: {ci_stats['no_failures']} tests")

    if ci_stats['top_bug_detectors']:
        print(f"\nTop Bug Detectors:")
        for test in ci_stats['top_bug_detectors']:
            print(f"  {test.name[:50]:<50} | Fixed {test.ci_failures_fixed} bugs | Bonus: +{test.failure_bonus:.0f}")

    # Brittleness analysis
    print("\n" + "="*80)
    print("4. Test Brittleness Analysis (NEW in V5)")
    print("="*80)

    brittle_stats = analyze_brittleness(v5_tests)
    print(f"\nBrittle Tests (high co-change): {brittle_stats['brittle_tests']} tests")
    print(f"Old Tests (>2 years): {brittle_stats['old_tests']} tests")
    print(f"Avg Co-changes: {brittle_stats['avg_co_changes']:.1f}")

    # Mock usage
    print("\n" + "="*80)
    print("5. Mock Usage Classification (NEW in V5)")
    print("="*80)

    mock_stats = analyze_mock_usage(v5_tests)
    print(f"\nInternal Mock Heavy (>3): {mock_stats['internal_heavy']} tests (implementation detail testing)")
    print(f"External Mocks Only: {mock_stats['external_only']} tests (good isolation)")
    print(f"Avg Internal Mocks: {mock_stats['avg_internal_mocks']:.1f}")
    print(f"Avg External Mocks: {mock_stats['avg_external_mocks']:.1f}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY: V5 Improvements Over V4")
    print("="*80)
    print("\n✅ Actual runtime data (not keyword heuristics)")
    print("✅ CI failure history (identifies proven bug detectors)")
    print("✅ Git churn analysis (detects brittle tests)")
    print("✅ Mock classification (external vs internal)")
    print("✅ Non-linear penalties (211x for slow tests)")
    print("✅ Configurable weights (weights.yaml)")

    print("\n" + "="*80)


if __name__ == '__main__':
    # Find most recent V4 audit
    audit_dir = Path("audit_reports")
    v4_files = sorted(audit_dir.glob("marathon_audit_v4_*.json"), reverse=True)

    if v4_files:
        v4_json = v4_files[0]
        print(f"Using V4 results: {v4_json.name}\n")
        generate_comparison_report(v4_json, sample_size=100)
    else:
        print("⚠️  No V4 audit results found in audit_reports/")
        print("Running V5-only analysis...\n")
        v5_tests = run_v5_audit(100)
        print(f"\n✅ V5 audit complete: {len(v5_tests)} tests scored")
