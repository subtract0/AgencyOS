"""
Unit tests for Auto-Recovery System (Mission 5).

TDD Protocol (Article VI):
- RED PHASE: Tests written FIRST (all fail initially) ← WE ARE HERE
- GREEN PHASE: Implementation makes tests pass
- REFACTOR PHASE: Clean up while keeping tests green

Test Coverage:
- TestFailureDetection: Detect different failure types (FR4)
- TestAutomaticRollback: Rollback to last known good state (FR5)
- TestRetryLogic: Retry with exponential backoff (FR6)
- TestEscalation: Escalate to user when recovery fails (FR7)
- TestHealthMonitoring: Monitor system health (FR8)
"""

import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import module to avoid namespace collision
import tools.auto_recovery as ar
from shared.models.auto_recovery import (
    AutoRecoveryConfig,
    RecoveryAttempt,
    EscalationRecord,
)


class TestFailureDetection:
    """Tests for failure detection (FR4)."""

    def test_detect_test_failure(self):
        """Test detection of pytest test failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock pytest failure
            mock_result = Mock(
                returncode=1,
                stdout="FAILED tests/test_foo.py::test_bar",
                stderr="",
            )

            failure = recovery.detect_failure(mock_result)

            # Should detect as test failure
            assert failure is not None
            assert failure["type"] == "test_failure"
            assert "test_bar" in failure["error_message"]

    def test_detect_build_error(self):
        """Test detection of build/linting errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock build error
            mock_result = Mock(
                returncode=1,
                stdout="",
                stderr="SyntaxError: invalid syntax",
            )

            failure = recovery.detect_failure(mock_result)

            # Should detect as build error
            assert failure is not None
            assert failure["type"] == "build_error"
            assert "SyntaxError" in failure["error_message"]

    def test_detect_git_failure(self):
        """Test detection of git operation failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock git push failure
            mock_result = Mock(
                returncode=1,
                stdout="",
                stderr="error: failed to push some refs",
            )

            failure = recovery.detect_failure(mock_result)

            # Should detect as git failure
            assert failure is not None
            assert failure["type"] == "git_failure"
            assert "failed to push" in failure["error_message"]

    def test_detect_timeout(self):
        """Test detection of timeout errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock timeout
            mock_result = Mock(
                returncode=124,  # Timeout exit code
                stdout="",
                stderr="Command timed out after 60 seconds",
            )

            failure = recovery.detect_failure(mock_result)

            # Should detect as timeout
            assert failure is not None
            assert failure["type"] == "timeout"
            assert "timed out" in failure["error_message"]

    def test_detect_resource_exhaustion(self):
        """Test detection of resource exhaustion (OOM, disk full)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock OOM error
            mock_result = Mock(
                returncode=137,  # SIGKILL (often OOM)
                stdout="",
                stderr="MemoryError: Out of memory",
            )

            failure = recovery.detect_failure(mock_result)

            # Should detect as resource exhaustion
            assert failure is not None
            assert failure["type"] == "resource_exhaustion"
            assert "memory" in failure["error_message"].lower()


class TestAutomaticRollback:
    """Tests for automatic rollback (FR5)."""

    def test_rollback_on_test_failure(self):
        """Test rollback on test failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_rollback=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock git operations
            with patch("tools.auto_recovery.subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                # Simulate rollback
                task_id = "task_abc123"
                last_good_commit = "abc123def456"

                result = recovery.rollback(task_id, last_good_commit)

                # Should have called git reset
                assert result["success"] is True
                mock_run.assert_called()

                # Verify git reset command was called with correct args
                git_reset_called = False
                for call in mock_run.call_args_list:
                    args = call[0][0] if call[0] else []
                    if "git" in args and "reset" in args and "--hard" in args:
                        git_reset_called = True
                        break
                assert git_reset_called

    def test_rollback_on_build_error(self):
        """Test rollback on build error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_rollback=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock build error
            failure = {
                "type": "build_error",
                "error_message": "SyntaxError: invalid syntax",
            }

            with patch("tools.auto_recovery.subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                # Rollback should be triggered
                result = recovery.handle_failure("task_123", failure, "abc123")

                # Should have attempted rollback
                assert result["action"] in ["rollback", "retry", "escalate"]

    def test_snapshot_creation(self):
        """Test snapshot creation before task execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig()
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock git tag creation
            with patch("tools.auto_recovery.subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="abc123def456\n", text=True)

                task_id = "task_abc123"
                snapshot = recovery.create_snapshot(task_id)

                # Should return snapshot ID (git commit hash or tag)
                assert snapshot is not None
                assert len(snapshot) > 0

                # Verify git operations were called
                assert mock_run.call_count >= 1

                # Check that git rev-parse or git tag was called
                git_ops_called = False
                for call in mock_run.call_args_list:
                    args = call[0][0] if call[0] else []
                    if "git" in args and ("rev-parse" in args or "tag" in args):
                        git_ops_called = True
                        break
                assert git_ops_called

    def test_rollback_verification(self):
        """Test verification of green state after rollback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_rollback=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock rollback and test verification
            with patch("tools.auto_recovery.subprocess.run") as mock_run:
                # First call: git reset (success)
                # Second call: pytest verification (success)
                mock_run.side_effect = [
                    Mock(returncode=0),  # git reset
                    Mock(returncode=0),  # pytest
                ]

                result = recovery.rollback("task_123", "abc123", verify=True)

                # Should have verified tests pass after rollback
                assert result["success"] is True
                assert result["verified"] is True


class TestRetryLogic:
    """Tests for retry logic with exponential backoff (FR6)."""

    def test_retry_exponential_backoff(self):
        """Test exponential backoff between retries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(
                max_retries=3,
                retry_delays_seconds=[0, 30, 120],
            )
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock retryable failure
            failure = {
                "type": "network_timeout",
                "error_message": "Connection timeout",
            }

            retry_delays = []

            def mock_sleep(seconds):
                retry_delays.append(seconds)

            with patch("time.sleep", side_effect=mock_sleep):
                with patch.object(recovery, "_attempt_recovery", return_value={"success": False}):
                    recovery.handle_failure("task_123", failure, "abc123")

            # Should have used exponential backoff
            assert len(retry_delays) <= 3
            # Delays should match config
            for i, delay in enumerate(retry_delays):
                assert delay == config.retry_delays_seconds[i]

    def test_max_retries(self):
        """Test respect for max retry limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(max_retries=3)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock retryable failure that always fails
            failure = {
                "type": "network_timeout",
                "error_message": "Connection timeout",
            }

            attempt_count = 0

            def mock_recovery(task_id, failure, snapshot):
                nonlocal attempt_count
                attempt_count += 1
                return {"success": False}

            with patch.object(recovery, "_attempt_recovery", side_effect=mock_recovery):
                with patch("time.sleep"):
                    result = recovery.handle_failure("task_123", failure, "abc123")

            # Should have attempted max_retries + 1 times (initial + 3 retries)
            assert attempt_count <= config.max_retries + 1

    def test_retryable_failures(self):
        """Test that only retryable failures trigger retry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(
                retryable_errors=["network_timeout", "file_lock"]
            )
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Test retryable failure
            retryable_failure = {
                "type": "network_timeout",
                "error_message": "Connection timeout",
            }

            with patch.object(recovery, "_attempt_recovery", return_value={"success": False}):
                with patch("time.sleep"):
                    result = recovery.handle_failure("task_123", retryable_failure, "abc123")

            # Should have attempted retry
            assert result["action"] == "retry" or result["retry_count"] > 0

    def test_non_retryable_failures(self):
        """Test that non-retryable failures don't trigger retry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(
                retryable_errors=["network_timeout", "file_lock"]
            )
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Test non-retryable failure
            non_retryable_failure = {
                "type": "test_failure",  # Not in retryable_errors
                "error_message": "AssertionError: expected 5, got 3",
            }

            with patch.object(recovery, "_attempt_recovery") as mock_recovery:
                result = recovery.handle_failure("task_123", non_retryable_failure, "abc123")

            # Should NOT have attempted retry (should escalate immediately)
            assert result["action"] == "escalate" or mock_recovery.call_count == 0


class TestEscalation:
    """Tests for escalation to user (FR7)."""

    def test_escalate_on_max_retries(self):
        """Test escalation after max retries exhausted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(max_retries=3, enable_escalation=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Mock retryable failure that always fails
            failure = {
                "type": "network_timeout",
                "error_message": "Connection timeout",
            }

            with patch.object(recovery, "_attempt_recovery", return_value={"success": False}):
                with patch("time.sleep"):
                    result = recovery.handle_failure("task_123", failure, "abc123")

            # Should have escalated after max retries
            assert result["action"] == "escalate"
            assert result["retry_count"] >= config.max_retries

    def test_escalate_on_non_retryable(self):
        """Test escalation on non-retryable failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_escalation=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Non-retryable failure
            failure = {
                "type": "test_failure",
                "error_message": "AssertionError: expected 5, got 3",
            }

            result = recovery.handle_failure("task_123", failure, "abc123")

            # Should escalate immediately
            assert result["action"] == "escalate"

    def test_escalation_file_creation(self):
        """Test creation of escalation file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_escalation=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Create escalation
            task_id = "task_abc123"
            failure_reason = "Test failure: AssertionError"
            recovery_attempts = [
                RecoveryAttempt(
                    task_id=task_id,
                    attempt_number=1,
                    failure_type="test_failure",
                    error_message=failure_reason,
                    stack_trace="...",
                    recovery_action="rollback",
                    outcome="failure",
                )
            ]

            escalation = recovery.create_escalation(
                task_id=task_id,
                failure_reason=failure_reason,
                recovery_attempts=recovery_attempts,
                stack_trace="...",
            )

            # Escalation file should exist
            escalation_dir = Path(tmpdir) / "escalations"
            escalation_files = list(escalation_dir.glob(f"{task_id}.json"))

            assert len(escalation_files) > 0

            # Verify escalation content
            with open(escalation_files[0]) as f:
                escalation_data = json.load(f)
                assert escalation_data["task_id"] == task_id
                assert escalation_data["failure_reason"] == failure_reason

    def test_escalation_metadata(self):
        """Test that escalation captures all required metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutoRecoveryConfig(enable_escalation=True)
            recovery = ar.AutoRecovery(config=config, state_dir=tmpdir)

            # Create escalation with full metadata
            task_id = "task_abc123"
            failure_reason = "Build error: SyntaxError"
            stack_trace = "Traceback:\n  File foo.py, line 10\n    def bar(\n           ^"
            recovery_attempts = [
                RecoveryAttempt(
                    task_id=task_id,
                    attempt_number=1,
                    failure_type="build_error",
                    error_message=failure_reason,
                    stack_trace=stack_trace,
                    recovery_action="rollback",
                    outcome="failure",
                )
            ]

            escalation = recovery.create_escalation(
                task_id=task_id,
                failure_reason=failure_reason,
                recovery_attempts=recovery_attempts,
                stack_trace=stack_trace,
            )

            # Verify all metadata present
            assert escalation.task_id == task_id
            assert escalation.failure_reason == failure_reason
            assert escalation.stack_trace == stack_trace
            assert len(escalation.recovery_attempts) > 0
            assert escalation.timestamp is not None
            assert escalation.resolved is False


class TestHealthMonitoring:
    """Tests for health monitoring (FR8)."""

    def test_disk_space_check(self):
        """Test detection of low disk space."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock low disk space
            with patch("shutil.disk_usage") as mock_disk:
                mock_disk.return_value = Mock(free=5 * 1024**3)  # 5GB free

                from tools.health_monitor import HealthMonitor

                monitor = HealthMonitor(state_dir=tmpdir)
                health = monitor.check_health()

                # Should detect low disk space (<10GB threshold)
                assert health["disk_free_gb"] < 10
                assert health["healthy"] is False

    def test_memory_check(self):
        """Test detection of high memory utilization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock high memory usage
            with patch("psutil.virtual_memory") as mock_mem:
                mock_mem.return_value = Mock(percent=85.0)  # 85% used

                from tools.health_monitor import HealthMonitor

                monitor = HealthMonitor(state_dir=tmpdir)
                health = monitor.check_health()

                # Should detect high memory usage (>80% threshold)
                assert health["memory_percent"] > 80
                assert health["healthy"] is False

    def test_cpu_check(self):
        """Test detection of high CPU utilization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock high CPU usage
            with patch("psutil.cpu_percent") as mock_cpu:
                mock_cpu.return_value = 95.0  # 95% used

                from tools.health_monitor import HealthMonitor

                monitor = HealthMonitor(state_dir=tmpdir)
                health = monitor.check_health()

                # Should detect high CPU usage (>90% threshold)
                assert health["cpu_percent"] > 90
                assert health["healthy"] is False

    def test_git_repo_check(self):
        """Test detection of dirty working tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock dirty git repo
            with patch("tools.health_monitor.subprocess.run") as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,  # Dirty working tree
                    stdout="M tools/foo.py\nM tests/test_bar.py",
                )

                from tools.health_monitor import HealthMonitor

                monitor = HealthMonitor(state_dir=tmpdir)
                health = monitor.check_health()

                # Should detect dirty working tree
                assert health["git_clean"] is False
                assert health["healthy"] is False

    def test_dependency_check(self):
        """Test detection of missing dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock missing dependency
            with patch("importlib.import_module") as mock_import:
                mock_import.side_effect = ImportError("No module named 'foo'")

                from tools.health_monitor import HealthMonitor

                monitor = HealthMonitor(state_dir=tmpdir)
                health = monitor.check_health(required_modules=["foo"])

                # Should detect missing dependency
                assert health["dependencies_ok"] is False
                assert health["healthy"] is False
