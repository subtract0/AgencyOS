"""
Tests for baseline and post-cleanup metrics collection

Validates:
- Baseline metrics collector
- Post-cleanup metrics comparison
- Report generation
- Validation logic
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

import sys
sys.path.insert(0, "scripts")

from collect_baseline_metrics import BaselineCollector, BaselineMetrics
from collect_post_metrics import PostCleanupCollector, ComparisonMetrics


class TestBaselineCollector:
    """Test baseline metrics collector"""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory"""
        return tmp_path / ".audit"

    @pytest.fixture
    def collector(self, temp_output_dir):
        """Create collector instance"""
        return BaselineCollector(
            output_dir=temp_output_dir,
            num_runs=3,  # Use fewer runs for testing
            test_path="tests/"
        )

    def test_init(self, collector, temp_output_dir):
        """Test initialization"""
        assert collector.output_dir == temp_output_dir
        assert collector.num_runs == 3
        assert collector.test_path == "tests/"
        assert collector.output_file == temp_output_dir / "metrics_baseline.json"

    def test_output_dir_created(self, collector):
        """Test output directory is created"""
        assert collector.output_dir.exists()

    @patch("collect_baseline_metrics.subprocess.run")
    def test_run_single_test_suite(self, mock_run, collector):
        """Test single test suite run"""
        # Create mock JSON report BEFORE running
        report_file = Path(".audit/pytest_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            "tests": [
                {"nodeid": "test_example.py::test_pass", "outcome": "passed"},
                {"nodeid": "test_example.py::test_fail", "outcome": "failed"}
            ]
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f)

        # Mock pytest execution (doesn't actually write report)
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        runtime, outcomes = collector.run_single_test_suite()

        assert isinstance(runtime, float)
        assert runtime >= 0
        assert outcomes == {
            "test_example.py::test_pass": "passed",
            "test_example.py::test_fail": "failed"
        }

    @patch("collect_baseline_metrics.subprocess.run")
    def test_collect_flaky_tests(self, mock_run, collector):
        """Test flaky test detection"""
        # Create mock JSON reports for each run
        report_file = Path(".audit/pytest_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        run_outcomes = [
            # Run 1: test_flaky fails
            {
                "tests": [
                    {"nodeid": "test_a.py::test_stable", "outcome": "passed"},
                    {"nodeid": "test_b.py::test_flaky", "outcome": "failed"}
                ]
            },
            # Run 2: test_flaky passes
            {
                "tests": [
                    {"nodeid": "test_a.py::test_stable", "outcome": "passed"},
                    {"nodeid": "test_b.py::test_flaky", "outcome": "passed"}
                ]
            },
            # Run 3: test_flaky fails again
            {
                "tests": [
                    {"nodeid": "test_a.py::test_stable", "outcome": "passed"},
                    {"nodeid": "test_b.py::test_flaky", "outcome": "failed"}
                ]
            }
        ]

        call_count = [0]

        def write_report_and_execute(*args, **kwargs):
            # Write report to hardcoded location
            with open(report_file, "w") as f:
                json.dump(run_outcomes[call_count[0]], f)
            call_count[0] += 1

            # Return mock result
            mock_result = Mock()
            mock_result.stdout = ""
            return mock_result

        mock_run.side_effect = write_report_and_execute

        runtimes, flaky_tests = collector.collect_flaky_tests()

        assert len(runtimes) == 3
        assert all(isinstance(r, float) for r in runtimes)
        assert "test_b.py::test_flaky" in flaky_tests
        assert "test_a.py::test_stable" not in flaky_tests  # Passed all 3 times

    @patch("collect_baseline_metrics.subprocess.run")
    def test_count_test_suite_size(self, mock_run, collector):
        """Test test suite size counting"""
        # Mock pytest collection
        mock_result = Mock()
        mock_result.stdout = "1,762 tests selected in 0.15s"
        mock_run.return_value = mock_result

        # Create some test files
        test_file = Path(collector.test_path) / "test_example.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(test_file, "w") as f:
            f.write("\n".join([f"# Line {i}" for i in range(100)]))

        test_count, test_loc = collector.count_test_suite_size()

        assert test_count == 1762
        assert test_loc >= 100  # At least the test file we created

    @patch("collect_baseline_metrics.subprocess.run")
    def test_measure_coverage(self, mock_run, collector):
        """Test coverage measurement"""
        # Mock pytest-cov output
        mock_result = Mock()
        mock_result.stdout = """
tests/test_example.py    100%
tools/example.py          85%
TOTAL                     87%
"""
        mock_run.return_value = mock_result

        coverage = collector.measure_coverage()

        assert coverage == 87.0

    @patch.object(BaselineCollector, "collect_flaky_tests")
    @patch.object(BaselineCollector, "count_test_suite_size")
    @patch.object(BaselineCollector, "measure_coverage")
    def test_collect(self, mock_coverage, mock_size, mock_flaky, collector):
        """Test full metrics collection"""
        # Mock individual collectors
        mock_flaky.return_value = ([120.5, 125.3, 122.1], ["test_flaky.py::test_a"])
        mock_size.return_value = (1762, 50000)
        mock_coverage.return_value = 87.3

        metrics = collector.collect()

        assert isinstance(metrics, BaselineMetrics)
        assert 120 <= metrics.ci_runtime_avg_sec <= 126
        assert metrics.ci_runtime_std_dev > 0
        assert metrics.ci_runtime_runs == 3
        assert metrics.flaky_test_count == 1
        assert "test_flaky.py::test_a" in metrics.flaky_test_names
        assert metrics.test_count == 1762
        assert metrics.test_loc == 50000
        assert metrics.coverage_pct == 87.3
        assert metrics.collection_duration_sec > 0

    def test_save(self, collector):
        """Test metrics saving"""
        metrics = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=125.5,
            ci_runtime_std_dev=2.3,
            ci_runtime_runs=10,
            flaky_test_count=3,
            flaky_test_names=["test_a", "test_b"],
            test_count=1762,
            test_loc=50000,
            coverage_pct=87.3,
            collection_duration_sec=600.0
        )

        collector.save(metrics)

        # Verify file exists and contains data
        assert collector.output_file.exists()

        with open(collector.output_file) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["timestamp"] == "2025-10-23T12:00:00"
        assert data[0]["ci_runtime_avg_sec"] == 125.5

    def test_save_appends(self, collector):
        """Test that save appends to existing data"""
        metrics1 = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=125.5,
            ci_runtime_std_dev=2.3,
            ci_runtime_runs=10,
            flaky_test_count=3,
            flaky_test_names=[],
            test_count=1762,
            test_loc=50000,
            coverage_pct=87.3,
            collection_duration_sec=600.0
        )

        metrics2 = BaselineMetrics(
            timestamp="2025-10-23T13:00:00",
            ci_runtime_avg_sec=120.0,
            ci_runtime_std_dev=1.8,
            ci_runtime_runs=10,
            flaky_test_count=2,
            flaky_test_names=[],
            test_count=1750,
            test_loc=49500,
            coverage_pct=88.0,
            collection_duration_sec=590.0
        )

        collector.save(metrics1)
        collector.save(metrics2)

        with open(collector.output_file) as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["timestamp"] == "2025-10-23T12:00:00"
        assert data[1]["timestamp"] == "2025-10-23T13:00:00"


class TestPostCleanupCollector:
    """Test post-cleanup metrics collector"""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory"""
        return tmp_path / ".audit"

    @pytest.fixture
    def baseline_file(self, temp_output_dir):
        """Create baseline metrics file"""
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        baseline_file = temp_output_dir / "metrics_baseline.json"

        baseline_data = [{
            "timestamp": "2025-10-23T12:00:00",
            "ci_runtime_avg_sec": 150.0,
            "ci_runtime_std_dev": 3.0,
            "ci_runtime_runs": 10,
            "flaky_test_count": 10,
            "flaky_test_names": ["test_a", "test_b", "test_c"],
            "test_count": 2000,
            "test_loc": 60000,
            "coverage_pct": 85.0,
            "collection_duration_sec": 900.0
        }]

        with open(baseline_file, "w") as f:
            json.dump(baseline_data, f)

        return baseline_file

    @pytest.fixture
    def collector(self, baseline_file, temp_output_dir):
        """Create collector instance"""
        return PostCleanupCollector(
            baseline_file=baseline_file,
            output_dir=temp_output_dir
        )

    def test_init(self, collector, baseline_file):
        """Test initialization"""
        assert collector.baseline_file == baseline_file
        assert collector.output_file.name == "metrics_comparison.json"
        assert collector.report_file.name == "metrics_comparison_report.md"

    def test_load_baseline(self, collector):
        """Test baseline loading"""
        baseline = collector.load_baseline()

        assert isinstance(baseline, BaselineMetrics)
        assert baseline.timestamp == "2025-10-23T12:00:00"
        assert baseline.ci_runtime_avg_sec == 150.0
        assert baseline.flaky_test_count == 10

    def test_load_baseline_missing_file(self, temp_output_dir):
        """Test error when baseline file missing"""
        collector = PostCleanupCollector(
            baseline_file=temp_output_dir / "nonexistent.json",
            output_dir=temp_output_dir
        )

        with pytest.raises(FileNotFoundError):
            collector.load_baseline()

    def test_calculate_comparison(self, collector):
        """Test comparison calculation"""
        baseline = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=150.0,
            ci_runtime_std_dev=3.0,
            ci_runtime_runs=10,
            flaky_test_count=10,
            flaky_test_names=["test_a", "test_b"],
            test_count=2000,
            test_loc=60000,
            coverage_pct=85.0,
            collection_duration_sec=900.0
        )

        post = BaselineMetrics(
            timestamp="2025-10-24T12:00:00",
            ci_runtime_avg_sec=90.0,  # 40% reduction
            ci_runtime_std_dev=2.0,
            ci_runtime_runs=10,
            flaky_test_count=3,  # 70% reduction
            flaky_test_names=["test_a"],
            test_count=1500,  # 25% reduction
            test_loc=45000,  # 25% reduction
            coverage_pct=86.0,  # +1% coverage
            collection_duration_sec=600.0
        )

        comparison = collector.calculate_comparison(baseline, post)

        assert isinstance(comparison, ComparisonMetrics)

        # Runtime reduction
        assert comparison.runtime_reduction_sec == 60.0
        assert comparison.runtime_reduction_pct == 40.0
        assert comparison.runtime_goal_met  # ≥30%

        # Flaky test reduction
        assert comparison.flaky_test_reduction_count == 7
        assert comparison.flaky_test_reduction_pct == 70.0
        assert comparison.flaky_goal_met  # ≥50%

        # Test count reduction
        assert comparison.test_count_reduction == 500
        assert comparison.test_count_reduction_pct == 25.0

        # Coverage maintained
        assert comparison.coverage_delta_pct == 1.0
        assert comparison.coverage_maintained

    def test_calculate_comparison_goals_not_met(self, collector):
        """Test comparison when goals not met"""
        baseline = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=150.0,
            ci_runtime_std_dev=3.0,
            ci_runtime_runs=10,
            flaky_test_count=10,
            flaky_test_names=[],
            test_count=2000,
            test_loc=60000,
            coverage_pct=90.0,
            collection_duration_sec=900.0
        )

        post = BaselineMetrics(
            timestamp="2025-10-24T12:00:00",
            ci_runtime_avg_sec=140.0,  # Only 6.7% reduction (goal: ≥30%)
            ci_runtime_std_dev=2.5,
            ci_runtime_runs=10,
            flaky_test_count=6,  # Only 40% reduction (goal: ≥50%)
            flaky_test_names=[],
            test_count=1800,
            test_loc=54000,
            coverage_pct=88.0,  # -2% coverage (regression)
            collection_duration_sec=850.0
        )

        comparison = collector.calculate_comparison(baseline, post)

        assert not comparison.runtime_goal_met  # < 30%
        assert not comparison.flaky_goal_met  # < 50%
        assert not comparison.coverage_maintained  # Negative delta

    def test_generate_markdown_report(self, collector):
        """Test Markdown report generation"""
        baseline = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=150.0,
            ci_runtime_std_dev=3.0,
            ci_runtime_runs=10,
            flaky_test_count=10,
            flaky_test_names=[],
            test_count=2000,
            test_loc=60000,
            coverage_pct=85.0,
            collection_duration_sec=900.0
        )

        post = BaselineMetrics(
            timestamp="2025-10-24T12:00:00",
            ci_runtime_avg_sec=90.0,
            ci_runtime_std_dev=2.0,
            ci_runtime_runs=10,
            flaky_test_count=3,
            flaky_test_names=[],
            test_count=1500,
            test_loc=45000,
            coverage_pct=86.0,
            collection_duration_sec=600.0
        )

        comparison = collector.calculate_comparison(baseline, post)
        report = collector.generate_markdown_report(comparison)

        # Verify report contains key sections
        assert "# Test Suite Cleanup: A/B Comparison Report" in report
        assert "Executive Summary" in report
        assert "CI Runtime" in report
        assert "Flaky Tests" in report
        assert "Code Coverage" in report
        assert "Validation Summary" in report

        # Verify metrics present
        assert "150.0s" in report  # Baseline runtime
        assert "90.0s" in report  # Post runtime
        assert "40.0%" in report  # Runtime reduction
        assert "✅ GOAL MET" in report  # Goals met

    def test_generate_markdown_report_with_bug_escape(self, collector):
        """Test report with manual bug escape rate"""
        baseline = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=150.0,
            ci_runtime_std_dev=3.0,
            ci_runtime_runs=10,
            flaky_test_count=10,
            flaky_test_names=[],
            test_count=2000,
            test_loc=60000,
            coverage_pct=85.0,
            collection_duration_sec=900.0
        )

        post = BaselineMetrics(
            timestamp="2025-10-24T12:00:00",
            ci_runtime_avg_sec=90.0,
            ci_runtime_std_dev=2.0,
            ci_runtime_runs=10,
            flaky_test_count=3,
            flaky_test_names=[],
            test_count=1500,
            test_loc=45000,
            coverage_pct=86.0,
            collection_duration_sec=600.0
        )

        comparison = collector.calculate_comparison(baseline, post)
        comparison.bug_escape_rate_baseline = 5
        comparison.bug_escape_rate_post = 2

        report = collector.generate_markdown_report(comparison)

        assert "Bug Escape Rate" in report
        assert "5 bugs" in report
        assert "2 bugs" in report

    def test_save(self, collector):
        """Test saving comparison"""
        baseline = BaselineMetrics(
            timestamp="2025-10-23T12:00:00",
            ci_runtime_avg_sec=150.0,
            ci_runtime_std_dev=3.0,
            ci_runtime_runs=10,
            flaky_test_count=10,
            flaky_test_names=[],
            test_count=2000,
            test_loc=60000,
            coverage_pct=85.0,
            collection_duration_sec=900.0
        )

        post = BaselineMetrics(
            timestamp="2025-10-24T12:00:00",
            ci_runtime_avg_sec=90.0,
            ci_runtime_std_dev=2.0,
            ci_runtime_runs=10,
            flaky_test_count=3,
            flaky_test_names=[],
            test_count=1500,
            test_loc=45000,
            coverage_pct=86.0,
            collection_duration_sec=600.0
        )

        comparison = collector.calculate_comparison(baseline, post)
        collector.save(comparison)

        # Verify JSON file
        assert collector.output_file.exists()
        with open(collector.output_file) as f:
            data = json.load(f)

        assert data["runtime_reduction_pct"] == 40.0

        # Verify Markdown report
        assert collector.report_file.exists()
        with open(collector.report_file) as f:
            report = f.read()

        assert "40.0%" in report
