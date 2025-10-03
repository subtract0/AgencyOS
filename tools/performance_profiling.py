"""
Performance Profiling Tools for Test Suite Optimization.

This module provides comprehensive performance profiling capabilities to identify
and analyze test suite bottlenecks, enabling targeted optimization efforts.

Constitutional Compliance:
- Article I: Complete context before action (full test profiling)
- Article II: 100% verification (accurate timing data)
- TDD: All code paths tested
- Result<T,E> pattern for error handling
"""

import cProfile
import pstats
import time
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import io
import sys

from pydantic import BaseModel, Field
from shared.type_definitions.result import Result, Ok, Err


@dataclass
class TestTiming:
    """Timing data for a single test."""
    test_name: str
    duration_seconds: float
    setup_time: float
    teardown_time: float
    memory_usage_mb: float
    file_path: str


@dataclass
class Bottleneck:
    """Represents a performance bottleneck."""
    category: str
    description: str
    impact_seconds: float
    affected_tests: List[str]
    recommendation: str


class PerformanceReport(BaseModel):
    """Performance analysis report."""
    total_duration: float = Field(..., description="Total test suite duration in seconds")
    test_count: int = Field(..., description="Total number of tests analyzed")
    slowest_tests: List[Dict[str, float]] = Field(..., description="Top 10 slowest tests")
    bottlenecks: List[Dict[str, str]] = Field(..., description="Identified bottlenecks")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "total_duration": 226.5,
                "test_count": 2438,
                "slowest_tests": [{"test_name": "test_e2e", "duration": 15.2}],
                "bottlenecks": [{"category": "e2e", "impact": "45s"}],
                "recommendations": ["Enable parallel execution"]
            }
        }


class PerformanceProfiler:
    """Profile test suite performance and identify bottlenecks."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_timings: List[TestTiming] = []
        self.profiler_stats: Optional[pstats.Stats] = None

    def profile_tests(
        self,
        test_path: str = "tests/",
        pytest_args: Optional[List[str]] = None
    ) -> Result[PerformanceReport, str]:
        """
        Profile all tests in path with cProfile integration.

        Args:
            test_path: Path to test directory or file
            pytest_args: Additional pytest arguments

        Returns:
            Result containing PerformanceReport or error message
        """
        try:
            # Setup profiler
            profiler = cProfile.Profile()

            # Build pytest command
            if pytest_args is None:
                pytest_args = []

            cmd = [
                sys.executable, "-m", "pytest",
                test_path,
                "-v",
                "--tb=no",
                "--durations=0",  # Show all test durations
                "--quiet",
                *pytest_args
            ]

            # Start profiling
            profiler.enable()
            start_time = time.time()

            # Run tests
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600
            )

            end_time = time.time()
            profiler.disable()

            # Process profiler stats
            stats_stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative')
            self.profiler_stats = stats

            # Parse pytest output for test durations
            test_timings = self._parse_pytest_durations(result.stdout)
            self.test_timings = test_timings

            # Analyze results
            total_duration = end_time - start_time
            report = self._generate_report(
                total_duration=total_duration,
                test_count=len(test_timings),
                test_timings=test_timings
            )

            return Ok(report)

        except subprocess.TimeoutExpired:
            return Err("Test profiling timed out after 600 seconds")
        except Exception as e:
            return Err(f"Profiling failed: {str(e)}")

    def _parse_pytest_durations(self, pytest_output: str) -> List[TestTiming]:
        """Parse pytest --durations output to extract test timings."""
        timings = []

        # Look for durations section in output
        lines = pytest_output.split('\n')
        in_durations = False

        for line in lines:
            if 'slowest durations' in line.lower():
                in_durations = True
                continue

            if in_durations:
                # Parse lines like: "0.45s call     tests/test_example.py::test_function"
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].endswith('s'):
                    try:
                        duration = float(parts[0].rstrip('s'))
                        phase = parts[1]  # call, setup, teardown
                        test_path = parts[2] if len(parts) > 2 else "unknown"

                        # Extract test name from path
                        if '::' in test_path:
                            file_path, test_name = test_path.split('::', 1)
                        else:
                            file_path = test_path
                            test_name = test_path

                        # Create or update timing entry
                        existing = next(
                            (t for t in timings if t.test_name == test_name),
                            None
                        )

                        if existing:
                            if phase == 'setup':
                                existing.setup_time = duration
                            elif phase == 'teardown':
                                existing.teardown_time = duration
                            else:
                                existing.duration_seconds = duration
                        else:
                            timing = TestTiming(
                                test_name=test_name,
                                duration_seconds=duration if phase == 'call' else 0.0,
                                setup_time=duration if phase == 'setup' else 0.0,
                                teardown_time=duration if phase == 'teardown' else 0.0,
                                memory_usage_mb=0.0,  # Would need tracemalloc for this
                                file_path=file_path
                            )
                            timings.append(timing)
                    except (ValueError, IndexError):
                        continue

        return timings

    def _generate_report(
        self,
        total_duration: float,
        test_count: int,
        test_timings: List[TestTiming]
    ) -> PerformanceReport:
        """Generate comprehensive performance report."""

        # Sort by duration descending
        sorted_timings = sorted(
            test_timings,
            key=lambda t: t.duration_seconds + t.setup_time + t.teardown_time,
            reverse=True
        )

        # Get top 10 slowest
        slowest_tests = [
            {
                "test_name": t.test_name,
                "duration": round(t.duration_seconds + t.setup_time + t.teardown_time, 3),
                "file_path": t.file_path
            }
            for t in sorted_timings[:10]
        ]

        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(sorted_timings)

        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks, total_duration)

        return PerformanceReport(
            total_duration=round(total_duration, 2),
            test_count=test_count,
            slowest_tests=slowest_tests,
            bottlenecks=[asdict(b) for b in bottlenecks],
            recommendations=recommendations
        )

    def _identify_bottlenecks(self, test_timings: List[TestTiming]) -> List[Bottleneck]:
        """Identify performance bottlenecks by category."""
        bottlenecks = []

        # Group tests by category (e2e, integration, slow fixtures, etc.)
        e2e_tests = [t for t in test_timings if 'e2e' in t.test_name.lower() or 'e2e' in t.file_path.lower()]
        integration_tests = [t for t in test_timings if 'integration' in t.file_path.lower()]
        slow_setup_tests = [t for t in test_timings if t.setup_time > 0.5]

        # E2E bottleneck
        if e2e_tests:
            total_e2e_time = sum(t.duration_seconds + t.setup_time + t.teardown_time for t in e2e_tests)
            if total_e2e_time > 10.0:
                bottlenecks.append(Bottleneck(
                    category="E2E Tests",
                    description=f"{len(e2e_tests)} E2E tests taking {total_e2e_time:.1f}s total",
                    impact_seconds=total_e2e_time,
                    affected_tests=[t.test_name for t in e2e_tests[:5]],
                    recommendation="Parallelize E2E tests or mock external dependencies"
                ))

        # Integration bottleneck
        if integration_tests:
            total_integration_time = sum(t.duration_seconds + t.setup_time + t.teardown_time for t in integration_tests)
            if total_integration_time > 20.0:
                bottlenecks.append(Bottleneck(
                    category="Integration Tests",
                    description=f"{len(integration_tests)} integration tests taking {total_integration_time:.1f}s total",
                    impact_seconds=total_integration_time,
                    affected_tests=[t.test_name for t in integration_tests[:5]],
                    recommendation="Use in-memory databases or parallel execution"
                ))

        # Slow fixture bottleneck
        if slow_setup_tests:
            total_setup_time = sum(t.setup_time for t in slow_setup_tests)
            if total_setup_time > 5.0:
                bottlenecks.append(Bottleneck(
                    category="Slow Fixtures",
                    description=f"{len(slow_setup_tests)} tests with slow setup (>0.5s)",
                    impact_seconds=total_setup_time,
                    affected_tests=[t.test_name for t in slow_setup_tests[:5]],
                    recommendation="Optimize fixtures with session/module scope or mocking"
                ))

        return bottlenecks

    def _generate_recommendations(self, bottlenecks: List[Bottleneck], total_duration: float) -> List[str]:
        """Generate actionable optimization recommendations."""
        recommendations = []

        # Always recommend parallel execution if not using it
        recommendations.append(
            "Install pytest-xdist and run with -n auto for parallel execution (2-4x speedup)"
        )

        # Bottleneck-specific recommendations
        for bottleneck in bottlenecks:
            if "E2E" in bottleneck.category:
                recommendations.append(
                    f"Mock external dependencies in E2E tests to save ~{bottleneck.impact_seconds:.1f}s"
                )
            elif "Integration" in bottleneck.category:
                recommendations.append(
                    f"Use in-memory database for integration tests to save ~{bottleneck.impact_seconds * 0.8:.1f}s"
                )
            elif "Fixture" in bottleneck.category:
                recommendations.append(
                    f"Convert slow fixtures to session/module scope to save ~{bottleneck.impact_seconds * 0.6:.1f}s"
                )

        # Target-based recommendation
        target_duration = 60.0
        if total_duration > target_duration:
            speedup_needed = total_duration / target_duration
            recommendations.append(
                f"Target: {target_duration}s (need {speedup_needed:.1f}x speedup from {total_duration:.1f}s)"
            )

        return recommendations

    def identify_slow_tests(self, threshold_seconds: float = 1.0) -> List[TestTiming]:
        """Find tests slower than threshold."""
        return [
            t for t in self.test_timings
            if (t.duration_seconds + t.setup_time + t.teardown_time) > threshold_seconds
        ]

    def save_report(self, report: PerformanceReport, output_path: Path) -> Result[None, str]:
        """Save performance report to file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save JSON report
            json_path = output_path.with_suffix('.json')
            with open(json_path, 'w') as f:
                json.dump(report.model_dump(), f, indent=2)

            # Save markdown report
            md_content = self._format_markdown_report(report)
            with open(output_path, 'w') as f:
                f.write(md_content)

            return Ok(None)

        except Exception as e:
            return Err(f"Failed to save report: {str(e)}")

    def _format_markdown_report(self, report: PerformanceReport) -> str:
        """Format report as markdown."""
        lines = [
            "# Test Suite Performance Analysis",
            "",
            f"**Generated:** {report.timestamp}",
            "",
            "## Summary",
            "",
            f"- **Total Duration:** {report.total_duration:.2f}s",
            f"- **Test Count:** {report.test_count}",
            f"- **Average per Test:** {(report.total_duration / report.test_count):.3f}s",
            "",
            "## Slowest Tests (Top 10)",
            "",
            "| Test Name | Duration (s) | File Path |",
            "|-----------|--------------|-----------|"
        ]

        for test in report.slowest_tests:
            lines.append(
                f"| {test['test_name']} | {test['duration']:.3f} | {test['file_path']} |"
            )

        lines.extend([
            "",
            "## Identified Bottlenecks",
            ""
        ])

        for bottleneck in report.bottlenecks:
            lines.extend([
                f"### {bottleneck['category']}",
                "",
                f"**Description:** {bottleneck['description']}",
                "",
                f"**Impact:** {bottleneck['impact_seconds']:.1f}s",
                "",
                f"**Recommendation:** {bottleneck['recommendation']}",
                "",
                "**Affected Tests:**",
                ""
            ])

            for test in bottleneck.get('affected_tests', [])[:5]:
                lines.append(f"- {test}")

            lines.append("")

        lines.extend([
            "## Optimization Recommendations",
            ""
        ])

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.extend([
            "",
            "---",
            "",
            "*Generated by Agency Performance Profiling System*"
        ])

        return '\n'.join(lines)

    def compare_runs(
        self,
        before: PerformanceReport,
        after: PerformanceReport
    ) -> str:
        """Compare two profiling runs and generate improvement report."""

        duration_delta = after.total_duration - before.total_duration
        duration_percent = (duration_delta / before.total_duration) * 100

        speedup = before.total_duration / after.total_duration if after.total_duration > 0 else 0

        lines = [
            "# Performance Comparison Report",
            "",
            "## Overall Results",
            "",
            f"- **Before:** {before.total_duration:.2f}s",
            f"- **After:** {after.total_duration:.2f}s",
            f"- **Change:** {duration_delta:+.2f}s ({duration_percent:+.1f}%)",
            f"- **Speedup:** {speedup:.2f}x",
            "",
            "## Test Count",
            "",
            f"- **Before:** {before.test_count} tests",
            f"- **After:** {after.test_count} tests",
            f"- **Change:** {after.test_count - before.test_count:+d} tests",
            ""
        ]

        if duration_delta < 0:
            lines.extend([
                "## ✅ Improvements Achieved",
                "",
                f"Successfully reduced test suite duration by {abs(duration_delta):.2f}s",
                f"This represents a {speedup:.2f}x speedup in execution time."
            ])
        else:
            lines.extend([
                "## ⚠️ Performance Regression Detected",
                "",
                f"Test suite duration increased by {duration_delta:.2f}s",
                "Review recent changes for potential performance issues."
            ])

        return '\n'.join(lines)


# CLI Interface
def main() -> int:
    """Command-line interface for performance profiling."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Profile test suite performance and identify bottlenecks"
    )
    parser.add_argument(
        "--test-path",
        default="tests/",
        help="Path to test directory or file (default: tests/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/testing/PERFORMANCE_PROFILE.md"),
        help="Output path for report"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Threshold in seconds for slow test detection (default: 1.0)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format instead of markdown"
    )

    args = parser.parse_args()

    # Run profiler
    project_root = Path.cwd()
    profiler = PerformanceProfiler(project_root)

    print("🔍 Profiling test suite performance...")
    result = profiler.profile_tests(args.test_path)

    if result.is_err():
        print(f"❌ Profiling failed: {result.unwrap_err()}")
        return 1

    report = result.unwrap()

    # Save report
    save_result = profiler.save_report(report, args.output)
    if save_result.is_err():
        print(f"❌ Failed to save report: {save_result.unwrap_err()}")
        return 1

    # Print summary
    print(f"\n✅ Performance analysis complete!")
    print(f"📊 Total duration: {report.total_duration:.2f}s")
    print(f"🧪 Tests analyzed: {report.test_count}")
    print(f"📝 Report saved to: {args.output}")

    # Show slow tests
    slow_tests = profiler.identify_slow_tests(args.threshold)
    if slow_tests:
        print(f"\n⚠️  Found {len(slow_tests)} slow tests (>{args.threshold}s):")
        for test in slow_tests[:5]:
            total_time = test.duration_seconds + test.setup_time + test.teardown_time
            print(f"  - {test.test_name}: {total_time:.3f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
