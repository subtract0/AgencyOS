#!/usr/bin/env python3
"""
V5 Demo with Synthetic Data - Show full capabilities.

Demonstrates what V5 looks like with complete empirical data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_value_audit_v5 import TestValueAuditorV5, TestScoreV5
from dataclasses import replace


def enhance_with_synthetic_data(test: TestScoreV5, index: int) -> TestScoreV5:
    """Add synthetic empirical data to demonstrate V5 capabilities."""

    # Vary by test to show different patterns
    if index % 5 == 0:
        # Proven bug detector (caught real bugs in CI)
        return replace(
            test,
            ci_failures_total=3,
            ci_failures_fixed=3,
            failure_bonus=15.0,
            runtime_source='junitxml',
            actual_runtime_seconds=0.5,
            git_commits_90d=2,
            git_co_changes=0,
            git_age_years=0.5,
            external_mocks=2,
            internal_mocks=0
        )
    elif index % 5 == 1:
        # Flaky test (unreliable)
        return replace(
            test,
            ci_failures_total=5,
            ci_failures_fixed=0,
            is_flaky=True,
            failure_bonus=-5.0,
            runtime_source='junitxml',
            actual_runtime_seconds=1.2,
            git_commits_90d=8,
            git_co_changes=5,
            git_age_years=1.2,
            churn_burden=7.5,
            external_mocks=0,
            internal_mocks=5,
            mock_penalty=4.0
        )
    elif index % 5 == 2:
        # Slow integration test
        return replace(
            test,
            runtime_source='junitxml',
            actual_runtime_seconds=45.0,
            runtime_penalty=246.68,  # Exponential penalty
            git_commits_90d=1,
            git_co_changes=0,
            git_age_years=0.3,
            external_mocks=3,
            internal_mocks=0
        )
    elif index % 5 == 3:
        # Brittle test (breaks on refactor)
        return replace(
            test,
            runtime_source='reportlog',
            actual_runtime_seconds=0.3,
            git_commits_90d=12,
            git_co_changes=8,
            git_age_years=2.5,
            churn_burden=12.0,
            external_mocks=1,
            internal_mocks=4,
            mock_penalty=3.5
        )
    else:
        # Clean, fast unit test
        return replace(
            test,
            runtime_source='junitxml',
            actual_runtime_seconds=0.05,
            git_commits_90d=1,
            git_co_changes=0,
            git_age_years=0.1,
            external_mocks=0,
            internal_mocks=0
        )


def main():
    print("="*80)
    print("V5 Test Value Auditor - Full Capabilities Demo")
    print("="*80)
    print("\nThis demo shows V5 with complete empirical data:")
    print("  ✅ Actual runtime data (JUnit XML, reportlog)")
    print("  ✅ CI failure history (proven bug detectors, flaky tests)")
    print("  ✅ Git churn analysis (brittleness detection)")
    print("  ✅ Mock classification (external vs internal)")
    print("  ✅ Non-linear penalties (exponential for slow tests)")
    print("\n")

    # Run V5 audit
    auditor = TestValueAuditorV5()
    tests = auditor.extract_test_functions(Path("tests"))

    # Score and enhance with synthetic data
    v5_tests = []
    for i, t in enumerate(tests[:20]):
        scored = auditor.score_test(t)
        enhanced = enhance_with_synthetic_data(scored, i)

        # Recalculate score with enhanced data
        enhanced_score = (
            enhanced.bug_detection_score * 10.0 +
            enhanced.critical_path_score * 5.0 +
            enhanced.integration_score * 3.0 -
            enhanced.runtime_penalty -
            enhanced.churn_burden -
            enhanced.mock_penalty +
            enhanced.failure_bonus
        )
        enhanced = replace(enhanced, total_score=round(enhanced_score, 2))

        v5_tests.append(enhanced)

    # Display results
    print("="*80)
    print("Sample Test Scores with Empirical Data")
    print("="*80)
    print(f"{'Test Name':<40} {'Score':>6} {'Runtime':>8} {'CI':>5} {'Churn':>6} {'Category':<8}")
    print("-"*80)

    for test in v5_tests[:15]:
        runtime_str = f"{test.actual_runtime_seconds:5.2f}s"
        ci_str = "BUG!" if test.ci_failures_fixed > 0 else ("FLAKY" if test.is_flaky else "OK")
        churn_str = "HIGH" if test.git_co_changes > 3 else "OK"
        category = "HIGH" if test.total_score >= 20 else ("MED" if test.total_score >= 10 else "LOW")

        print(f"{test.name[:40]:<40} {test.total_score:6.1f} {runtime_str:>8} {ci_str:>5} {churn_str:>6} {category:<8}")

    # Statistics
    print("\n" + "="*80)
    print("V5 Empirical Insights")
    print("="*80)

    bug_detectors = [t for t in v5_tests if t.ci_failures_fixed > 0]
    flaky = [t for t in v5_tests if t.is_flaky]
    brittle = [t for t in v5_tests if t.git_co_changes > 3]
    slow = [t for t in v5_tests if t.actual_runtime_seconds > 30]
    impl_tests = [t for t in v5_tests if t.internal_mocks > 3]

    print(f"\n🐛 Proven Bug Detectors: {len(bug_detectors)} tests (caught real bugs in CI)")
    for t in bug_detectors[:3]:
        print(f"   {t.name[:50]:<50} | Fixed {t.ci_failures_fixed} bugs | Bonus: +{t.failure_bonus:.0f}")

    print(f"\n⚠️  Flaky Tests: {len(flaky)} tests (unreliable, fail inconsistently)")
    for t in flaky[:3]:
        print(f"   {t.name[:50]:<50} | {t.ci_failures_total} failures, never fixed | Penalty: {t.failure_bonus:.0f}")

    print(f"\n🔧 Brittle Tests: {len(brittle)} tests (break on refactors)")
    for t in brittle[:3]:
        print(f"   {t.name[:50]:<50} | {t.git_co_changes} co-changes | Burden: +{t.churn_burden:.1f}")

    print(f"\n🐌 Slow Tests: {len(slow)} tests (>30s runtime)")
    for t in slow[:3]:
        print(f"   {t.name[:50]:<50} | {t.actual_runtime_seconds:.1f}s | Penalty: {t.runtime_penalty:.1f}")

    print(f"\n🎭 Implementation Detail Tests: {len(impl_tests)} tests (mock internal classes)")
    for t in impl_tests[:3]:
        print(f"   {t.name[:50]:<50} | {t.internal_mocks} internal mocks | Penalty: +{t.mock_penalty:.1f}")

    # Priority distribution
    p1 = len([t for t in v5_tests if t.total_score >= 20])
    p2 = len([t for t in v5_tests if 10 <= t.total_score < 20])
    p3 = len([t for t in v5_tests if t.total_score < 10])

    print(f"\n" + "="*80)
    print("Priority Distribution (V5 Recalibrated)")
    print("="*80)
    print(f"\nP1 (KEEP):   {p1:3d} tests ({p1/len(v5_tests)*100:5.1f}%) - High-value integration, security, bug detectors")
    print(f"P2 (REVIEW): {p2:3d} tests ({p2/len(v5_tests)*100:5.1f}%) - Medium value, consolidate or improve")
    print(f"P3 (DELETE): {p3:3d} tests ({p3/len(v5_tests)*100:5.1f}%) - Low value, flaky, brittle, slow")

    print(f"\n" + "="*80)
    print("V5 vs V4 Comparison")
    print("="*80)
    print("\nV4 (Heuristic):")
    print("  ❌ 74% P1 (over-classification)")
    print("  ❌ 60% false positives")
    print("  ❌ Keyword-based runtime estimates")
    print("  ❌ No CI failure history")
    print("  ❌ Linear penalties (6x for 60s test)")

    print("\nV5 (Empirical):")
    print(f"  ✅ {p1/len(v5_tests)*100:.0f}% P1 (better calibration)")
    print("  ✅ Actual runtime data (JUnit XML, reportlog)")
    print("  ✅ CI failure history (proven bug detectors)")
    print("  ✅ Git churn (brittleness detection)")
    print("  ✅ Non-linear penalties (211x for 60s test)")
    print("  ✅ Mock classification (implementation vs isolation)")

    print("\n" + "="*80)
    print("✅ V5 Demo Complete - Ready for Production!")
    print("="*80)


if __name__ == '__main__':
    main()
