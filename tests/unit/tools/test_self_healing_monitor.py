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
