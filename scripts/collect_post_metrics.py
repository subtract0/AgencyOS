#!/usr/bin/env python3
"""
Post-Cleanup Metrics Collector and Comparison Report Generator

Collects post-cleanup metrics and generates A/B comparison report:
1. Re-runs all baseline metrics collection
2. Calculates deltas (runtime reduction %, flaky test reduction)
3. Generates comparison report (Markdown + JSON)
4. Validates KPI improvements (CI ≥30% faster, flaky ≥50% reduction)
"""

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# Import baseline collector
from collect_baseline_metrics import BaselineCollector, BaselineMetrics


@dataclass
class ComparisonMetrics:
    """Comparison between baseline and post-cleanup metrics"""
    baseline: BaselineMetrics
    post_cleanup: BaselineMetrics

    # Deltas
    runtime_reduction_pct: float
    runtime_reduction_sec: float
    flaky_test_reduction_count: int
    flaky_test_reduction_pct: float
    test_count_reduction: int
    test_count_reduction_pct: float
    test_loc_reduction: int
    test_loc_reduction_pct: float
    coverage_delta_pct: float

    # Validation results
    runtime_goal_met: bool  # ≥30% reduction
    flaky_goal_met: bool    # ≥50% reduction
    coverage_maintained: bool  # ≥ baseline

    # Manual input
    bug_escape_rate_baseline: Optional[int] = None
    bug_escape_rate_post: Optional[int] = None


class PostCleanupCollector:
    """Collects post-cleanup metrics and generates comparison"""

    def __init__(
        self,
        baseline_file: Path = Path(".audit/metrics_baseline.json"),
        output_dir: Path = Path(".audit")
    ):
        """
        Initialize post-cleanup collector.

        Args:
            baseline_file: Path to baseline metrics JSON
            output_dir: Where to save comparison report
        """
        self.baseline_file = baseline_file
        self.output_dir = output_dir
        self.output_file = output_dir / "metrics_comparison.json"
        self.report_file = output_dir / "metrics_comparison_report.md"

    def load_baseline(self) -> BaselineMetrics:
        """Load most recent baseline metrics"""
        if not self.baseline_file.exists():
            raise FileNotFoundError(
                f"Baseline file not found: {self.baseline_file}\n"
                "Run collect_baseline_metrics.py first!"
            )

        with open(self.baseline_file) as f:
            data = json.load(f)

        # Get most recent entry
        latest = data[-1]

        return BaselineMetrics(**latest)

    def collect_post_cleanup(self) -> BaselineMetrics:
        """Collect post-cleanup metrics (same as baseline)"""
        print("Collecting post-cleanup metrics...")
        print("(This uses the same methodology as baseline collection)\n")

        collector = BaselineCollector(output_dir=self.output_dir)
        return collector.collect()

    def calculate_comparison(
        self,
        baseline: BaselineMetrics,
        post: BaselineMetrics
    ) -> ComparisonMetrics:
        """Calculate deltas and validation results"""

        # Runtime reduction
        runtime_reduction_sec = baseline.ci_runtime_avg_sec - post.ci_runtime_avg_sec
        runtime_reduction_pct = (runtime_reduction_sec / baseline.ci_runtime_avg_sec) * 100

        # Flaky test reduction
        flaky_reduction_count = baseline.flaky_test_count - post.flaky_test_count
        flaky_reduction_pct = 0.0
        if baseline.flaky_test_count > 0:
            flaky_reduction_pct = (flaky_reduction_count / baseline.flaky_test_count) * 100

        # Test count reduction
        test_count_reduction = baseline.test_count - post.test_count
        test_count_reduction_pct = (test_count_reduction / baseline.test_count) * 100

        # LOC reduction
        loc_reduction = baseline.test_loc - post.test_loc
        loc_reduction_pct = (loc_reduction / baseline.test_loc) * 100

        # Coverage delta
        coverage_delta = post.coverage_pct - baseline.coverage_pct

        # Validate KPIs
        runtime_goal_met = runtime_reduction_pct >= 30.0
        flaky_goal_met = flaky_reduction_pct >= 50.0
        coverage_maintained = coverage_delta >= 0.0

        return ComparisonMetrics(
            baseline=baseline,
            post_cleanup=post,
            runtime_reduction_pct=runtime_reduction_pct,
            runtime_reduction_sec=runtime_reduction_sec,
            flaky_test_reduction_count=flaky_reduction_count,
            flaky_test_reduction_pct=flaky_reduction_pct,
            test_count_reduction=test_count_reduction,
            test_count_reduction_pct=test_count_reduction_pct,
            test_loc_reduction=loc_reduction,
            test_loc_reduction_pct=loc_reduction_pct,
            coverage_delta_pct=coverage_delta,
            runtime_goal_met=runtime_goal_met,
            flaky_goal_met=flaky_goal_met,
            coverage_maintained=coverage_maintained
        )

    def generate_markdown_report(self, comparison: ComparisonMetrics) -> str:
        """Generate Markdown comparison report"""

        def format_delta(value: float, is_percentage: bool = False) -> str:
            """Format delta with color indicator"""
            if value > 0:
                sign = "+"
                emoji = "⬆️"
            elif value < 0:
                sign = ""
                emoji = "⬇️"
            else:
                sign = ""
                emoji = "➡️"

            if is_percentage:
                return f"{sign}{value:.1f}% {emoji}"
            else:
                return f"{sign}{value:.1f} {emoji}"

        def goal_indicator(met: bool) -> str:
            """Goal met indicator"""
            return "✅ GOAL MET" if met else "❌ GOAL NOT MET"

        report = f"""# Test Suite Cleanup: A/B Comparison Report

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

| Metric | Baseline | Post-Cleanup | Delta | Goal |
|--------|----------|--------------|-------|------|
| **CI Runtime** | {comparison.baseline.ci_runtime_avg_sec:.1f}s | {comparison.post_cleanup.ci_runtime_avg_sec:.1f}s | {format_delta(-comparison.runtime_reduction_pct, True)} | {goal_indicator(comparison.runtime_goal_met)} (≥30%) |
| **Flaky Tests** | {comparison.baseline.flaky_test_count} | {comparison.post_cleanup.flaky_test_count} | {format_delta(-comparison.flaky_test_reduction_pct, True)} | {goal_indicator(comparison.flaky_goal_met)} (≥50%) |
| **Test Count** | {comparison.baseline.test_count:,} | {comparison.post_cleanup.test_count:,} | {format_delta(-comparison.test_count_reduction_pct, True)} | - |
| **Test LOC** | {comparison.baseline.test_loc:,} | {comparison.post_cleanup.test_loc:,} | {format_delta(-comparison.test_loc_reduction_pct, True)} | - |
| **Coverage** | {comparison.baseline.coverage_pct:.1f}% | {comparison.post_cleanup.coverage_pct:.1f}% | {format_delta(comparison.coverage_delta_pct, True)} | {goal_indicator(comparison.coverage_maintained)} (≥0%) |

---

## Detailed Metrics

### CI Runtime

**Baseline**:
- Average: {comparison.baseline.ci_runtime_avg_sec:.1f}s ({comparison.baseline.ci_runtime_avg_sec/60:.1f} min)
- Std Dev: ±{comparison.baseline.ci_runtime_std_dev:.1f}s
- Runs: {comparison.baseline.ci_runtime_runs}

**Post-Cleanup**:
- Average: {comparison.post_cleanup.ci_runtime_avg_sec:.1f}s ({comparison.post_cleanup.ci_runtime_avg_sec/60:.1f} min)
- Std Dev: ±{comparison.post_cleanup.ci_runtime_std_dev:.1f}s
- Runs: {comparison.post_cleanup.ci_runtime_runs}

**Improvement**:
- Time saved: {comparison.runtime_reduction_sec:.1f}s ({comparison.runtime_reduction_sec/60:.1f} min)
- Percentage: {comparison.runtime_reduction_pct:.1f}%
- **Goal (≥30% reduction)**: {goal_indicator(comparison.runtime_goal_met)}

---

### Flaky Tests

**Baseline**:
- Count: {comparison.baseline.flaky_test_count}
- Names: {len(comparison.baseline.flaky_test_names)} unique tests

**Post-Cleanup**:
- Count: {comparison.post_cleanup.flaky_test_count}
- Names: {len(comparison.post_cleanup.flaky_test_names)} unique tests

**Improvement**:
- Reduction: {comparison.flaky_test_reduction_count} tests
- Percentage: {comparison.flaky_test_reduction_pct:.1f}%
- **Goal (≥50% reduction)**: {goal_indicator(comparison.flaky_goal_met)}

---

### Test Suite Size

**Baseline**:
- Test count: {comparison.baseline.test_count:,}
- Total LOC: {comparison.baseline.test_loc:,}

**Post-Cleanup**:
- Test count: {comparison.post_cleanup.test_count:,}
- Total LOC: {comparison.post_cleanup.test_loc:,}

**Reduction**:
- Tests removed: {comparison.test_count_reduction:,} ({comparison.test_count_reduction_pct:.1f}%)
- LOC removed: {comparison.test_loc_reduction:,} ({comparison.test_loc_reduction_pct:.1f}%)

---

### Code Coverage

**Baseline**: {comparison.baseline.coverage_pct:.1f}%
**Post-Cleanup**: {comparison.post_cleanup.coverage_pct:.1f}%
**Delta**: {format_delta(comparison.coverage_delta_pct, True)}

**Goal (maintain or improve)**: {goal_indicator(comparison.coverage_maintained)}

---

### Bug Escape Rate (Manual)

"""

        if comparison.bug_escape_rate_baseline is not None:
            bug_delta = comparison.bug_escape_rate_post - comparison.bug_escape_rate_baseline
            report += f"""
**Baseline (30 days pre-cleanup)**: {comparison.bug_escape_rate_baseline} bugs
**Post-Cleanup (30 days post-cleanup)**: {comparison.bug_escape_rate_post} bugs
**Delta**: {format_delta(bug_delta)}

"""
        else:
            report += """
*Manual tracking required - update after 30 days post-cleanup*

To update:
```bash
python scripts/collect_post_metrics.py --bug-escape-baseline 3 --bug-escape-post 2
```

"""

        report += f"""---

## Validation Summary

| Goal | Target | Actual | Status |
|------|--------|--------|--------|
| CI Runtime Reduction | ≥30% | {comparison.runtime_reduction_pct:.1f}% | {goal_indicator(comparison.runtime_goal_met)} |
| Flaky Test Reduction | ≥50% | {comparison.flaky_test_reduction_pct:.1f}% | {goal_indicator(comparison.flaky_goal_met)} |
| Coverage Maintained | ≥0% | {format_delta(comparison.coverage_delta_pct, True)} | {goal_indicator(comparison.coverage_maintained)} |

---

## Next Steps

"""

        if comparison.runtime_goal_met and comparison.flaky_goal_met and comparison.coverage_maintained:
            report += """
✅ **All validation goals met!**

The test suite cleanup was successful. Consider:
1. Documenting learnings in ADR
2. Applying similar cleanup to other test directories
3. Establishing ongoing test value monitoring
"""
        else:
            report += """
⚠️ **Some validation goals not met**

Review the metrics above and consider:
1. Were the right tests removed? (check deletion candidates)
2. Is there more low-value test removal opportunity?
3. Were flaky tests actually removed or just re-run differently?
4. Check for coverage regressions in specific modules
"""

        report += f"""

---

**Report generated**: {datetime.now().isoformat()}
"""

        return report

    def save(self, comparison: ComparisonMetrics) -> None:
        """Save comparison to JSON and Markdown"""

        # JSON (structured data)
        with open(self.output_file, "w") as f:
            json.dump(asdict(comparison), f, indent=2)

        # Markdown (human-readable report)
        report = self.generate_markdown_report(comparison)
        with open(self.report_file, "w") as f:
            f.write(report)

        print(f"\n📊 Saved comparison:")
        print(f"   JSON: {self.output_file}")
        print(f"   Report: {self.report_file}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect post-cleanup metrics and generate comparison report"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(".audit/metrics_baseline.json"),
        help="Path to baseline metrics JSON (default: .audit/metrics_baseline.json)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".audit"),
        help="Output directory (default: .audit/)"
    )
    parser.add_argument(
        "--bug-escape-baseline",
        type=int,
        help="Bugs found in production 30 days pre-cleanup (manual input)"
    )
    parser.add_argument(
        "--bug-escape-post",
        type=int,
        help="Bugs found in production 30 days post-cleanup (manual input)"
    )

    args = parser.parse_args()

    collector = PostCleanupCollector(
        baseline_file=args.baseline,
        output_dir=args.output_dir
    )

    # Load baseline
    print("Loading baseline metrics...")
    baseline = collector.load_baseline()
    print(f"  Baseline timestamp: {baseline.timestamp}")
    print(f"  Baseline runtime: {baseline.ci_runtime_avg_sec:.1f}s")

    # Collect post-cleanup
    post = collector.collect_post_cleanup()

    # Calculate comparison
    print("\nCalculating comparison...")
    comparison = collector.calculate_comparison(baseline, post)

    # Add manual bug escape rate if provided
    if args.bug_escape_baseline is not None:
        comparison.bug_escape_rate_baseline = args.bug_escape_baseline
        comparison.bug_escape_rate_post = args.bug_escape_post

    # Save results
    collector.save(comparison)

    # Print summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"Runtime:      {comparison.runtime_reduction_pct:.1f}% reduction ({'✅ GOAL MET' if comparison.runtime_goal_met else '❌ GOAL NOT MET'})")
    print(f"Flaky Tests:  {comparison.flaky_test_reduction_pct:.1f}% reduction ({'✅ GOAL MET' if comparison.flaky_goal_met else '❌ GOAL NOT MET'})")
    print(f"Coverage:     {comparison.coverage_delta_pct:+.1f}% delta ({'✅ MAINTAINED' if comparison.coverage_maintained else '❌ REGRESSION'})")
    print("="*70)

    # Exit code based on validation
    if comparison.runtime_goal_met and comparison.flaky_goal_met and comparison.coverage_maintained:
        print("\n✅ All validation goals met!")
        sys.exit(0)
    else:
        print("\n⚠️ Some validation goals not met (see report for details)")
        sys.exit(1)


if __name__ == "__main__":
    main()
