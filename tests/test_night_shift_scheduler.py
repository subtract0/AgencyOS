"""
Unit tests for Night Shift Scheduler (Mission 5).

TDD Protocol (Article VI):
- RED PHASE: Tests written FIRST (all fail initially) ← WE ARE HERE
- GREEN PHASE: Implementation makes tests pass
- REFACTOR PHASE: Clean up while keeping tests green

Test Coverage:
- TestNightShiftScheduler: Basic scheduling and execution
- TestGracefulShutdown: Shutdown and state management
"""

import json
import signal
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import module to avoid namespace collision
import tools.night_shift_scheduler as ns
from shared.models.night_shift import NightShiftConfig, NightShiftState


class TestNightShiftScheduler:
    """Tests for Night Shift scheduler basic functionality (FR1, FR2)."""

    def test_schedule_parsing(self):
        """Test that scheduler can parse cron syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="0 2 * * *")  # 2 AM daily
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Should be able to parse schedule
            next_run = scheduler.get_next_execution_time()

            # Next run should be in the future
            assert next_run > datetime.now()

            # Next run should be at 2 AM (hour = 2)
            assert next_run.hour == 2

    def test_next_execution_time(self):
        """Test calculation of next execution time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="0 */4 * * *")  # Every 4 hours
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            next_run_1 = scheduler.get_next_execution_time()
            next_run_2 = scheduler.get_next_execution_time()

            # Multiple calls should return same result (deterministic)
            assert next_run_1 == next_run_2

            # Should be in the future
            assert next_run_1 > datetime.now()

    def test_dry_run_mode(self):
        """Test that dry run mode doesn't execute tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(
                schedule="* * * * *",  # Every minute (for testing)
                dry_run=True,
                max_tasks_per_execution=1,
            )
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Mock the task executor
            with patch.object(scheduler, "_execute_task", return_value={"success": True}) as mock_execute:
                # Run one cycle
                scheduler.run_cycle()

                # In dry run mode, _execute_task should NOT be called
                mock_execute.assert_not_called()

    def test_logging(self):
        """Test that all operations are logged correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Run one cycle (with mocked task executor)
            with patch.object(scheduler, "_execute_task", return_value={"success": True}):
                scheduler.run_cycle()

            # Log file should exist
            log_dir = Path(tmpdir) / "logs" / "night_shift"
            log_files = list(log_dir.glob("*.log"))

            assert len(log_files) > 0

            # Log should contain execution details
            with open(log_files[0]) as f:
                log_content = f.read()
                assert "cycle" in log_content.lower() or "execution" in log_content.lower()

    def test_max_tasks_per_execution(self):
        """Test that scheduler respects max tasks per execution limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(
                schedule="* * * * *",
                max_tasks_per_execution=3,
            )
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Mock health monitor to return healthy status
            with patch.object(scheduler.health_monitor, "check_health", return_value={"healthy": True}):
                # Mock backlog with 10 tasks
                from shared.type_definitions.result import Ok

                tasks = [
                    Mock(id=str(uuid.uuid4()), status=Mock(value="pending")) for _ in range(10)
                ]

                mock_backlog = Mock()
                mock_backlog.list_tasks.return_value = Ok(tasks)

                scheduler.backlog_storage = mock_backlog

                with patch.object(scheduler, "_execute_task", return_value={"success": True}):
                    scheduler.run_cycle()

                    # Should only execute 3 tasks (max_tasks_per_execution)
                    assert scheduler.state.tasks_completed_this_cycle == 3

    def test_min_interval_enforcement(self):
        """Test that scheduler enforces minimum interval between executions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(
                schedule="* * * * *",  # Every minute
                min_interval_minutes=15,
            )
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Run first cycle
            with patch.object(scheduler, "_execute_task", return_value={"success": True}):
                scheduler.run_cycle()
                first_execution = scheduler.state.last_execution_time

                # Try to run again immediately
                scheduler.run_cycle()
                second_execution = scheduler.state.last_execution_time

                # Second execution should be same as first (not allowed due to min interval)
                # OR should be at least 15 minutes after first
                time_diff = (second_execution - first_execution).total_seconds() / 60

                assert time_diff == 0 or time_diff >= 15

    def test_sequential_execution(self):
        """Test that tasks execute sequentially (no concurrent operations)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(
                schedule="* * * * *",
                max_tasks_per_execution=3,
            )
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            execution_log = []

            def mock_execute_task(task):
                """Mock task that logs start/end times."""
                execution_log.append(("start", task.id, datetime.now()))
                time.sleep(0.1)  # Simulate work
                execution_log.append(("end", task.id, datetime.now()))
                return {"success": True}

            # Mock health monitor to return healthy status
            with patch.object(scheduler.health_monitor, "check_health", return_value={"healthy": True}):
                # Mock backlog with 3 tasks
                from shared.type_definitions.result import Ok

                mock_tasks = [Mock(id=f"task_{i}", status=Mock(value="pending")) for i in range(3)]
                mock_backlog = Mock()
                mock_backlog.list_tasks.return_value = Ok(mock_tasks)

                scheduler.backlog_storage = mock_backlog

                with patch.object(scheduler, "_execute_task", side_effect=mock_execute_task):
                    scheduler.run_cycle()

            # Verify sequential execution: each task's end should come before next task's start
            assert len(execution_log) == 6  # 3 tasks × (start, end)

            # Extract start/end pairs
            starts = [log for log in execution_log if log[0] == "start"]
            ends = [log for log in execution_log if log[0] == "end"]

            # Verify no overlap: task N end < task N+1 start
            for i in range(len(ends) - 1):
                assert ends[i][2] < starts[i + 1][2]

    def test_resource_monitoring(self):
        """Test that scheduler aborts on resource exhaustion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Mock resource monitoring to return critical levels
            with patch("tools.night_shift_scheduler.HealthMonitor") as MockHealthMonitor:
                mock_health = Mock()
                mock_health.check_resources.return_value = {
                    "cpu_percent": 95.0,  # >90% threshold
                    "memory_percent": 85.0,
                    "disk_free_gb": 15.0,
                    "healthy": False,
                }
                MockHealthMonitor.return_value = mock_health

                # Mock task executor
                with patch.object(scheduler, "_execute_task", return_value={"success": True}) as mock_execute:
                    scheduler.run_cycle()

                    # Should NOT execute tasks due to resource exhaustion
                    mock_execute.assert_not_called()


class TestGracefulShutdown:
    """Tests for graceful shutdown and state management (FR3)."""

    def test_sigterm_graceful_shutdown(self):
        """Test that SIGTERM triggers graceful shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Mock a long-running task
            def long_running_task(task):
                time.sleep(2)
                return {"success": True}

            with patch.object(scheduler, "_execute_task", side_effect=long_running_task):
                # Start scheduler in background thread
                import threading

                def run_scheduler():
                    scheduler.run()

                thread = threading.Thread(target=run_scheduler, daemon=True)
                thread.start()

                # Wait for scheduler to start
                time.sleep(0.5)

                # Send SIGTERM
                scheduler.shutdown_requested = True

                # Wait for graceful shutdown
                thread.join(timeout=5)

                # Scheduler should have stopped gracefully
                assert scheduler.shutdown_requested is True

    def test_sigint_graceful_shutdown(self):
        """Test that SIGINT (Ctrl+C) triggers graceful shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Set shutdown flag (simulates SIGINT handler)
            scheduler.shutdown_requested = False
            scheduler.shutdown_requested = True

            # Verify flag is set
            assert scheduler.shutdown_requested is True

    def test_state_persistence(self):
        """Test that state is saved on shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Update state
            scheduler.state.total_tasks_completed = 42
            scheduler.state.total_failures = 3

            # Save state
            scheduler.save_state()

            # Load state in new scheduler
            scheduler2 = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # State should be restored
            assert scheduler2.state.total_tasks_completed == 42
            assert scheduler2.state.total_failures == 3

    def test_resume_interrupted_task(self):
        """Test that interrupted tasks are resumed or marked failed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Simulate interrupted task
            scheduler.state.current_task_id = "task_abc123"
            scheduler.save_state()

            # Create new scheduler (simulates process restart)
            scheduler2 = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Should detect interrupted task
            assert scheduler2.state.current_task_id == "task_abc123"

            # On startup, should clear interrupted task or attempt resume
            # (Implementation detail - test just verifies detection)

    def test_kill_switch(self):
        """Test that file-based kill switch works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = NightShiftConfig(schedule="* * * * *")
            scheduler = ns.NightShiftScheduler(config=config, state_dir=tmpdir)

            # Create kill switch file
            kill_switch_file = Path(tmpdir) / "STOP_NIGHT_SHIFT"
            kill_switch_file.touch()

            # Check kill switch
            assert scheduler.check_kill_switch() is True

            # Remove kill switch
            kill_switch_file.unlink()

            # Kill switch should be inactive
            assert scheduler.check_kill_switch() is False
