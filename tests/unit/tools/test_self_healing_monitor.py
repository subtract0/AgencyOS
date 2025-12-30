"""Unit tests for self-healing monitor.

Tests the SelfHealingMonitor class and related functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSelfHealingMonitor:
    """Tests for SelfHealingMonitor class."""

    def test_import_fixes_mapping(self):
        """Test that known import fixes are configured."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        assert "agents" in monitor.IMPORT_FIXES
        assert monitor.IMPORT_FIXES["agents"] == "openai-agents"
        assert "sklearn" in monitor.IMPORT_FIXES
        assert monitor.IMPORT_FIXES["sklearn"] == "scikit-learn"

    def test_health_report_dataclass(self):
        """Test HealthReport dataclass structure."""
        from tools.self_healing_monitor import HealthReport

        report = HealthReport(
            timestamp=datetime.now(),
            test_pass_rate=0.95,
            tests_passed=95,
            tests_failed=5,
            tests_skipped=2,
            tests_error=0,
            collection_errors=0,
            issues_detected=[],
            recommendations=[],
            auto_fixable=[],
        )

        assert report.test_pass_rate == 0.95
        assert report.tests_passed == 95
        assert report.tests_failed == 5

    def test_fix_attempt_dataclass(self):
        """Test FixAttempt dataclass structure."""
        from tools.self_healing_monitor import FixAttempt

        fix = FixAttempt(
            issue_type="import_error",
            file_path="test.py",
            description="Fixed missing import",
            fix_applied="pip install package",
            success=True,
            error_message=None,
        )

        assert fix.issue_type == "import_error"
        assert fix.success is True
        assert fix.error_message is None

    @patch("subprocess.run")
    def test_check_health_returns_result(self, mock_run):
        """Test that check_health returns a Result."""
        from tools.self_healing_monitor import SelfHealingMonitor

        # Mock pytest collection
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="collected 100 items\n",
            stderr="",
        )

        monitor = SelfHealingMonitor()
        result = monitor.check_health()

        assert hasattr(result, "is_ok")
        assert hasattr(result, "is_err")

    @patch("subprocess.run")
    def test_parse_import_errors(self, mock_run):
        """Test parsing of import errors from pytest output."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()

        output = """
        tests/test_foo.py:10: in <module>
            import some_module
        ModuleNotFoundError: No module named 'missing_pkg'
        """

        errors = monitor._parse_import_errors(output)

        assert len(errors) == 1
        assert errors[0]["module"] == "missing_pkg"

    def test_generate_report_format(self):
        """Test that generate_report returns formatted string."""
        from tools.self_healing_monitor import SelfHealingMonitor

        with patch.object(SelfHealingMonitor, "check_health") as mock_check:
            from tools.self_healing_monitor import HealthReport
            from shared.type_definitions.result import Ok

            mock_check.return_value = Ok(HealthReport(
                timestamp=datetime.now(),
                test_pass_rate=1.0,
                tests_passed=100,
                tests_failed=0,
                tests_skipped=0,
                tests_error=0,
                collection_errors=0,
                issues_detected=[],
                recommendations=[],
                auto_fixable=[],
            ))

            monitor = SelfHealingMonitor()
            report = monitor.generate_report()

            assert "AgencyOS Health Report" in report
            assert "Test Pass Rate: 100.0%" in report
            assert "Passed: 100" in report


class TestVLMHealthCheck:
    """Tests for VLM health check functionality."""

    def test_check_vlm_health_returns_dict(self):
        """Test that check_vlm_health returns a status dict."""
        from tools.self_healing_monitor import check_vlm_health

        status = check_vlm_health()

        assert isinstance(status, dict)
        assert "service" in status
        assert "timestamp" in status
        assert "checks" in status
        assert "overall" in status

    def test_check_vlm_health_with_mock_client(self):
        """Test VLM health check with mocked OpenAI client."""
        with patch("openai.OpenAI") as mock_openai:
            # Mock the client
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock models.list
            mock_models = MagicMock()
            mock_models.data = [{"id": "model1"}, {"id": "model2"}]
            mock_client.models.list.return_value = mock_models

            # Mock embeddings.create
            mock_embedding = MagicMock()
            mock_embedding.data = [MagicMock(embedding=[0.1] * 768)]
            mock_client.embeddings.create.return_value = mock_embedding

            from tools.self_healing_monitor import check_vlm_health

            status = check_vlm_health()

            assert status["overall"] == "healthy"
            assert status["checks"]["api"]["status"] == "ok"
            assert status["checks"]["embedding"]["status"] == "ok"


class TestDaemonMode:
    """Tests for daemon mode functionality."""

    def test_run_daemon_with_cycles(self):
        """Test that daemon respects max_cycles parameter."""
        from tools.self_healing_monitor import run_daemon, SelfHealingMonitor
        from shared.type_definitions.result import Ok
        from tools.self_healing_monitor import HealthReport

        with patch.object(SelfHealingMonitor, "check_health") as mock_check:
            with patch("tools.self_healing_monitor.check_vlm_health") as mock_vlm:
                with patch("time.sleep"):
                    mock_check.return_value = Ok(HealthReport(
                        timestamp=datetime.now(),
                        test_pass_rate=1.0,
                        tests_passed=100,
                        tests_failed=0,
                        tests_skipped=0,
                        tests_error=0,
                        collection_errors=0,
                        issues_detected=[],
                        recommendations=[],
                        auto_fixable=[],
                    ))

                    mock_vlm.return_value = {"overall": "healthy", "checks": {}}

                    # Run with 1 cycle
                    run_daemon(interval_seconds=1, max_cycles=1)

                    # Should have been called exactly once
                    assert mock_check.call_count == 1


class TestCodeQualityScan:
    """Tests for code quality scanning."""

    def test_scan_code_quality_returns_list(self):
        """Test that scan_code_quality returns a list of issues."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        issues = monitor.scan_code_quality(paths=["tools/"])

        assert isinstance(issues, list)

    def test_scan_detects_dict_any_any(self, tmp_path):
        """Test that scanner detects Dict[Any, Any] violations."""
        from tools.self_healing_monitor import SelfHealingMonitor

        # Create a test file with a violation
        test_file = tmp_path / "test_bad.py"
        test_file.write_text("from typing import Dict, Any\nx: Dict[Any, Any] = {}")

        monitor = SelfHealingMonitor(project_root=tmp_path)
        issues = monitor.scan_code_quality(paths=["."])

        dict_issues = [i for i in issues if i["pattern"] == "dict_any_any"]
        assert len(dict_issues) >= 1
        assert dict_issues[0]["severity"] == "high"

    def test_code_quality_patterns_structure(self):
        """Test that CODE_QUALITY_PATTERNS has correct structure."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()

        for name, info in monitor.CODE_QUALITY_PATTERNS.items():
            assert "pattern" in info
            assert "description" in info
            assert "severity" in info
            assert info["severity"] in ["high", "medium", "low"]


class TestSemanticClustering:
    """Tests for semantic clustering functionality."""

    def test_get_semantic_clusters_empty(self):
        """Test clustering with empty list."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        clusters = monitor.get_semantic_clusters([])

        assert clusters == {}

    def test_get_semantic_clusters_fallback(self):
        """Test fallback clustering by pattern type."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()

        issues = [
            {"pattern": "dict_any_any", "description": "Test 1", "content": "x"},
            {"pattern": "dict_any_any", "description": "Test 2", "content": "y"},
            {"pattern": "bare_except", "description": "Test 3", "content": "z"},
        ]

        # This will use fallback if VLM is not available
        clusters = monitor.get_semantic_clusters(issues)

        assert isinstance(clusters, dict)
        assert len(clusters) >= 1


class TestDashboard:
    """Tests for dashboard generation."""

    def test_generate_dashboard_returns_string(self):
        """Test that dashboard generation returns markdown string."""
        from tools.self_healing_monitor import SelfHealingMonitor, generate_dashboard
        from tools.self_healing_monitor import HealthReport
        from shared.type_definitions.result import Ok

        monitor = SelfHealingMonitor()

        with patch.object(monitor, "check_health") as mock_check:
            with patch("tools.self_healing_monitor.check_vlm_health") as mock_vlm:
                with patch.object(monitor, "scan_code_quality") as mock_scan:
                    mock_check.return_value = Ok(HealthReport(
                        timestamp=datetime.now(),
                        test_pass_rate=1.0,
                        tests_passed=100,
                        tests_failed=0,
                        tests_skipped=0,
                        tests_error=0,
                        collection_errors=0,
                        issues_detected=[],
                        recommendations=[],
                        auto_fixable=[],
                    ))
                    mock_vlm.return_value = {"overall": "healthy", "checks": {"api": {"status": "ok"}}}
                    mock_scan.return_value = []

                    dashboard = generate_dashboard(monitor)

                    assert isinstance(dashboard, str)
                    assert "# AgencyOS Health Dashboard" in dashboard
                    assert "## System Status" in dashboard


class TestLearning:
    """Tests for VectorStore learning integration."""

    def test_store_learning_requires_success(self):
        """Test that store_learning only stores successful fixes."""
        from tools.self_healing_monitor import SelfHealingMonitor, FixAttempt

        monitor = SelfHealingMonitor()

        failed_fix = FixAttempt(
            issue_type="import_error",
            file_path="test.py",
            description="Failed fix",
            fix_applied="pip install x",
            success=False,
            error_message="Error",
        )

        result = monitor.store_learning(failed_fix)
        assert result == False  # Should not store failed fixes

    def test_query_past_fixes_returns_list(self):
        """Test that query_past_fixes returns a list."""
        from tools.self_healing_monitor import SelfHealingMonitor

        monitor = SelfHealingMonitor()
        results = monitor.query_past_fixes("import_error")

        assert isinstance(results, list)
