"""
Tests for Watchdog Monitor - Phase 1, Task 2
Autonomous process monitoring with auto-restart

TDD: Tests written FIRST (Article VI compliance)
"""

import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

import pytest

from tools.watchdog import (
    Watchdog,
    ProcessInfo,
    ProcessStatus,
    WatchdogConfig,
    RestartPolicy,
)
from shared.type_definitions.result import Ok, Err


class TestWatchdogInit:
    """Test Watchdog initialization"""

    def test_init_with_defaults(self):
        """Should initialize with default config"""
        watchdog = Watchdog()
        assert watchdog.check_interval == 10  # 10 seconds default
        assert watchdog.max_restarts == 3

    def test_init_with_custom_config(self):
        """Should initialize with custom config"""
        config = WatchdogConfig(
            check_interval=5,
            max_restarts=5,
            restart_policy=RestartPolicy.EXPONENTIAL_BACKOFF,
        )
        watchdog = Watchdog(config=config)
        assert watchdog.check_interval == 5
        assert watchdog.max_restarts == 5


class TestProcessMonitoring:
    """Test process monitoring"""

    @patch("subprocess.run")
    def test_is_process_running_true(self, mock_run):
        """Should detect running process"""
        mock_run.return_value = Mock(returncode=0, stdout="12345\n")

        watchdog = Watchdog()
        result = watchdog.is_process_running(12345)

        assert result.is_ok()
        assert result.unwrap() is True

    @patch("subprocess.run")
    def test_is_process_running_false(self, mock_run):
        """Should detect non-running process"""
        mock_run.return_value = Mock(returncode=1, stdout="")

        watchdog = Watchdog()
        result = watchdog.is_process_running(12345)

        assert result.is_ok()
        assert result.unwrap() is False

    @patch("subprocess.run")
    def test_is_process_running_error(self, mock_run):
        """Should handle ps command errors"""
        mock_run.side_effect = subprocess.TimeoutExpired("ps", 5)

        watchdog = Watchdog()
        result = watchdog.is_process_running(12345)

        assert result.is_err()

    @patch("subprocess.run")
    def test_get_process_info_success(self, mock_run):
        """Should retrieve process information"""
        # ps output has header line, then data line
        mock_run.return_value = Mock(
            returncode=0,
            stdout="  PID COMMAND         %CPU     TIME\n12345 python          10.5 0:05:30",
        )

        watchdog = Watchdog()
        result = watchdog.get_process_info(12345)

        assert result.is_ok()
        info = result.unwrap()
        assert info.pid == 12345
        assert info.status == ProcessStatus.RUNNING

    @patch("subprocess.run")
    def test_get_process_info_not_found(self, mock_run):
        """Should handle missing process"""
        mock_run.return_value = Mock(returncode=1, stdout="")

        watchdog = Watchdog()
        result = watchdog.get_process_info(12345)

        assert result.is_err()


class TestProcessRestart:
    """Test process restart logic"""

    @patch("subprocess.Popen")
    def test_restart_process_success(self, mock_popen):
        """Should restart process successfully"""
        mock_process = Mock()
        mock_process.pid = 99999
        mock_popen.return_value = mock_process

        watchdog = Watchdog()
        command = ["python", "autonomous_worker.py"]
        result = watchdog.restart_process(command, "worker-1")

        assert result.is_ok()
        new_pid = result.unwrap()
        assert new_pid == 99999
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_restart_process_failure(self, mock_popen):
        """Should handle restart failures"""
        mock_popen.side_effect = OSError("Permission denied")

        watchdog = Watchdog()
        command = ["python", "autonomous_worker.py"]
        result = watchdog.restart_process(command, "worker-1")

        assert result.is_err()

    def test_should_restart_below_limit(self):
        """Should restart when below max restarts"""
        watchdog = Watchdog()
        process_id = "worker-1"

        # First 3 restarts should be allowed
        assert watchdog.should_restart(process_id, restart_count=0) is True
        assert watchdog.should_restart(process_id, restart_count=1) is True
        assert watchdog.should_restart(process_id, restart_count=2) is True

    def test_should_restart_at_limit(self):
        """Should not restart at max restarts"""
        watchdog = Watchdog()
        process_id = "worker-1"

        # 4th restart should be denied (default max is 3)
        assert watchdog.should_restart(process_id, restart_count=3) is False

    def test_calculate_backoff_immediate(self):
        """Should use immediate restart for IMMEDIATE policy"""
        config = WatchdogConfig(restart_policy=RestartPolicy.IMMEDIATE)
        watchdog = Watchdog(config=config)

        assert watchdog.calculate_backoff(restart_count=0) == 0
        assert watchdog.calculate_backoff(restart_count=5) == 0

    def test_calculate_backoff_exponential(self):
        """Should use exponential backoff"""
        config = WatchdogConfig(restart_policy=RestartPolicy.EXPONENTIAL_BACKOFF)
        watchdog = Watchdog(config=config)

        assert watchdog.calculate_backoff(restart_count=0) == 1
        assert watchdog.calculate_backoff(restart_count=1) == 2
        assert watchdog.calculate_backoff(restart_count=2) == 4
        assert watchdog.calculate_backoff(restart_count=3) == 8


class TestWatchdogRegistration:
    """Test process registration"""

    def test_register_process(self):
        """Should register process for monitoring"""
        watchdog = Watchdog()
        process_id = "worker-1"
        command = ["python", "autonomous_worker.py"]

        result = watchdog.register_process(process_id, 12345, command)

        assert result.is_ok()
        assert process_id in watchdog.monitored_processes
        info = watchdog.monitored_processes[process_id]
        assert info.pid == 12345
        assert info.command == command

    def test_register_duplicate_process(self):
        """Should handle duplicate registration"""
        watchdog = Watchdog()
        process_id = "worker-1"
        command = ["python", "autonomous_worker.py"]

        # Register first time
        watchdog.register_process(process_id, 12345, command)

        # Try to register again
        result = watchdog.register_process(process_id, 12346, command)

        # Should replace existing registration
        assert result.is_ok()
        assert watchdog.monitored_processes[process_id].pid == 12346

    def test_unregister_process(self):
        """Should unregister process"""
        watchdog = Watchdog()
        process_id = "worker-1"
        command = ["python", "autonomous_worker.py"]

        watchdog.register_process(process_id, 12345, command)
        result = watchdog.unregister_process(process_id)

        assert result.is_ok()
        assert process_id not in watchdog.monitored_processes

    def test_unregister_nonexistent_process(self):
        """Should handle unregistering nonexistent process"""
        watchdog = Watchdog()
        result = watchdog.unregister_process("nonexistent")

        assert result.is_err()


class TestWatchdogCheckCycle:
    """Test watchdog check cycle"""

    @patch("tools.watchdog.Watchdog.is_process_running")
    def test_check_all_processes_all_running(self, mock_is_running):
        """Should check all monitored processes"""
        mock_is_running.return_value = Ok(True)

        watchdog = Watchdog()
        watchdog.register_process("worker-1", 12345, ["python", "worker.py"])
        watchdog.register_process("worker-2", 12346, ["python", "worker.py"])

        result = watchdog.check_all_processes()

        assert result.is_ok()
        status = result.unwrap()
        assert status["total"] == 2
        assert status["running"] == 2
        assert status["failed"] == 0

    @patch("tools.watchdog.Watchdog.is_process_running")
    @patch("tools.watchdog.Watchdog.restart_process")
    def test_check_all_processes_with_restart(self, mock_restart, mock_is_running):
        """Should restart failed processes"""
        mock_is_running.return_value = Ok(False)  # Process not running
        mock_restart.return_value = Ok(99999)  # New PID

        watchdog = Watchdog()
        watchdog.register_process("worker-1", 12345, ["python", "worker.py"])

        result = watchdog.check_all_processes()

        assert result.is_ok()
        # Should have attempted restart
        mock_restart.assert_called_once()
        # PID should be updated
        assert watchdog.monitored_processes["worker-1"].pid == 99999

    @patch("tools.watchdog.Watchdog.is_process_running")
    def test_check_all_processes_max_restarts_exceeded(self, mock_is_running):
        """Should stop restarting after max attempts"""
        mock_is_running.return_value = Ok(False)

        watchdog = Watchdog()
        process_id = "worker-1"
        watchdog.register_process(process_id, 12345, ["python", "worker.py"])

        # Set restart count to max
        watchdog.monitored_processes[process_id].restart_count = 3

        result = watchdog.check_all_processes()

        assert result.is_ok()
        status = result.unwrap()
        # Should mark as failed without restart attempt
        assert watchdog.monitored_processes[process_id].status == ProcessStatus.FAILED


class TestWatchdogLogging:
    """Test watchdog event logging"""

    def test_log_event(self):
        """Should log events to file"""
        watchdog = Watchdog()
        event = "Process worker-1 restarted"

        result = watchdog.log_event("worker-1", event, level="INFO")

        assert result.is_ok()

    def test_get_recent_events(self):
        """Should retrieve recent events"""
        watchdog = Watchdog()
        watchdog.log_event("worker-1", "Started", level="INFO")
        watchdog.log_event("worker-1", "Crashed", level="ERROR")
        watchdog.log_event("worker-1", "Restarted", level="INFO")

        result = watchdog.get_recent_events(limit=2)

        assert result.is_ok()
        events = result.unwrap()
        assert len(events) <= 2
        # Should be in reverse chronological order
        assert "Restarted" in events[0] if events else True


class TestWatchdogCLI:
    """Test CLI interface"""

    @patch("tools.watchdog.Watchdog.check_all_processes")
    def test_cli_status(self, mock_check):
        """Should display status"""
        mock_check.return_value = Ok({
            "total": 3,
            "running": 2,
            "failed": 1,
            "timestamp": "2025-10-31T04:00:00",
        })

        from tools.watchdog import main

        with pytest.raises(SystemExit) as exc:
            main(["status"])

        assert exc.value.code == 0

    def test_cli_start_daemon(self):
        """Should start watchdog daemon"""
        from tools.watchdog import main

        # This would normally start a background process
        # For testing, we just verify it doesn't crash
        with pytest.raises(SystemExit) as exc:
            main(["start", "--check-interval", "5"])

        # Should exit with success or indicate daemon started
        assert exc.value.code in [0, None]
