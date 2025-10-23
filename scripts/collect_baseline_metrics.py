#!/usr/bin/env python3
"""
Baseline Metrics Collector for Test Suite Validation

Collects pre-cleanup metrics to establish A/B comparison baseline:
1. CI runtime (pytest --durations=0 repeated 10x)
2. Flaky test rate (tests failing 1-9 out of 10 runs)
3. Test suite size (test count, total LOC)
4. Code coverage (pytest-cov)

Idempotent: Appends timestamped entries (safe re-run, history preserved).
Performance SLA: <30 minutes for 5,408 tests (10 runs).
"""

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import statistics


@dataclass
class BaselineMetrics:
    """Baseline metrics snapshot"""
    timestamp: str
    ci_runtime_avg_sec: float
    ci_runtime_std_dev: float
    ci_runtime_runs: int
    flaky_test_count: int
    flaky_test_names: List[str]
    test_count: int
    test_loc: int
    coverage_pct: float
    collection_duration_sec: float


class BaselineCollector:
    """Collects baseline metrics for test suite validation"""

    def __init__(
        self,
        output_dir: Path = Path(".audit"),
        num_runs: int = 10,
        test_path: str = "tests/"
    ):
        """
        Initialize baseline collector.

        Args:
            output_dir: Where to save metrics_baseline.json
            num_runs: How many times to run tests (for flaky detection)
            test_path: Path to test directory
        """
        self.output_dir = output_dir
        self.num_runs = num_runs
        self.test_path = test_path
        self.output_file = output_dir / "metrics_baseline.json"

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_single_test_suite(self) -> Tuple[float, Dict[str, str]]:
        """
        Run pytest once, measure runtime and collect pass/fail status.

        Returns:
            (runtime_seconds, {test_id: 'passed'|'failed'})
        """
        start = time.time()

        # Run with minimal output, JSON report
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                self.test_path,
                "-q",
                "--tb=no",
                "--json-report",
                "--json-report-file=.audit/pytest_report.json",
                "--json-report-omit=log"
            ],
            capture_output=True,
            text=True,
            timeout=1800  # 30 min max per run
        )

        runtime = time.time() - start

        # Parse JSON report for test outcomes
        report_file = Path(".audit/pytest_report.json")
        test_outcomes = {}

        if report_file.exists():
            with open(report_file) as f:
                report = json.load(f)

            for test in report.get("tests", []):
                test_id = test["nodeid"]
                outcome = test["outcome"]  # passed, failed, skipped
                test_outcomes[test_id] = outcome

        return runtime, test_outcomes

    def collect_flaky_tests(self) -> Tuple[List[float], List[str]]:
        """
        Run test suite multiple times, identify flaky tests.

        Returns:
            (runtimes_list, flaky_test_names)
        """
        runtimes = []
        test_run_outcomes: Dict[str, List[str]] = {}

        print(f"Running test suite {self.num_runs} times to detect flaky tests...")

        for i in range(self.num_runs):
            print(f"  Run {i+1}/{self.num_runs}...", end=" ", flush=True)
            runtime, outcomes = self.run_single_test_suite()
            runtimes.append(runtime)
            print(f"{runtime:.1f}s")

            # Track outcomes per test
            for test_id, outcome in outcomes.items():
                if test_id not in test_run_outcomes:
                    test_run_outcomes[test_id] = []
                test_run_outcomes[test_id].append(outcome)

        # Identify flaky tests (failed 1-9 out of 10 runs)
        flaky_tests = []
        for test_id, outcomes in test_run_outcomes.items():
            failure_count = outcomes.count("failed")
            if 1 <= failure_count < self.num_runs:
                flaky_tests.append(test_id)

        return runtimes, flaky_tests

    def count_test_suite_size(self) -> Tuple[int, int]:
        """
        Count total tests and lines of code.

        Returns:
            (test_count, total_loc)
        """
        # Count tests via collection
        result = subprocess.run(
            ["python", "-m", "pytest", self.test_path, "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse output like "1,762 tests selected"
        test_count = 0
        for line in result.stdout.split("\n"):
            if "test" in line.lower() and "selected" in line.lower():
                # Extract number
                parts = line.split()
                for part in parts:
                    if part.replace(",", "").isdigit():
                        test_count = int(part.replace(",", ""))
                        break

        # Count LOC in all test files
        test_files = list(Path(self.test_path).rglob("test_*.py"))
        total_loc = 0

        for test_file in test_files:
            with open(test_file) as f:
                total_loc += len(f.readlines())

        return test_count, total_loc

    def measure_coverage(self) -> float:
        """
        Run pytest-cov to measure code coverage.

        Returns:
            coverage_percentage (e.g., 87.3)
        """
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                self.test_path,
                "--cov=.",
                "--cov-report=term-missing",
                "-q"
            ],
            capture_output=True,
            text=True,
            timeout=1800
        )

        # Parse coverage from output like "TOTAL    87%"
        coverage_pct = 0.0
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                # Extract percentage
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        coverage_pct = float(part.replace("%", ""))
                        break

        return coverage_pct

    def collect(self) -> BaselineMetrics:
        """
        Collect all baseline metrics.

        Returns:
            BaselineMetrics snapshot
        """
        start_time = time.time()

        print("="*70)
        print("BASELINE METRICS COLLECTION")
        print("="*70)

        # 1. CI runtime and flaky test detection
        print("\n1. Measuring CI runtime and detecting flaky tests...")
        runtimes, flaky_tests = self.collect_flaky_tests()

        ci_runtime_avg = statistics.mean(runtimes)
        ci_runtime_std = statistics.stdev(runtimes) if len(runtimes) > 1 else 0.0

        print(f"   Avg runtime: {ci_runtime_avg:.1f}s (±{ci_runtime_std:.1f}s)")
        print(f"   Flaky tests: {len(flaky_tests)}")

        # 2. Test suite size
        print("\n2. Counting test suite size...")
        test_count, test_loc = self.count_test_suite_size()
        print(f"   Test count: {test_count:,}")
        print(f"   Total LOC: {test_loc:,}")

        # 3. Code coverage
        print("\n3. Measuring code coverage...")
        coverage_pct = self.measure_coverage()
        print(f"   Coverage: {coverage_pct:.1f}%")

        # Create metrics object
        collection_duration = time.time() - start_time

        metrics = BaselineMetrics(
            timestamp=datetime.now().isoformat(),
            ci_runtime_avg_sec=ci_runtime_avg,
            ci_runtime_std_dev=ci_runtime_std,
            ci_runtime_runs=self.num_runs,
            flaky_test_count=len(flaky_tests),
            flaky_test_names=flaky_tests,
            test_count=test_count,
            test_loc=test_loc,
            coverage_pct=coverage_pct,
            collection_duration_sec=collection_duration
        )

        print(f"\n✅ Collection complete in {collection_duration/60:.1f} minutes")

        return metrics

    def save(self, metrics: BaselineMetrics) -> None:
        """
        Save metrics to JSON file (append mode for history).

        Args:
            metrics: Metrics to save
        """
        # Load existing data if present
        existing_data = []
        if self.output_file.exists():
            with open(self.output_file) as f:
                existing_data = json.load(f)

        # Append new entry
        existing_data.append(asdict(metrics))

        # Save back
        with open(self.output_file, "w") as f:
            json.dump(existing_data, f, indent=2)

        print(f"\n📊 Saved to: {self.output_file}")
        print(f"   Total snapshots: {len(existing_data)}")


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Collect baseline test suite metrics")
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of test runs for flaky detection (default: 10)"
    )
    parser.add_argument(
        "--test-path",
        default="tests/",
        help="Path to test directory (default: tests/)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".audit"),
        help="Output directory (default: .audit/)"
    )

    args = parser.parse_args()

    collector = BaselineCollector(
        output_dir=args.output_dir,
        num_runs=args.runs,
        test_path=args.test_path
    )

    metrics = collector.collect()
    collector.save(metrics)

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"CI Runtime:    {metrics.ci_runtime_avg_sec:.1f}s (±{metrics.ci_runtime_std_dev:.1f}s)")
    print(f"Flaky Tests:   {metrics.flaky_test_count}")
    print(f"Test Count:    {metrics.test_count:,}")
    print(f"Test LOC:      {metrics.test_loc:,}")
    print(f"Coverage:      {metrics.coverage_pct:.1f}%")
    print("="*70)


if __name__ == "__main__":
    main()
