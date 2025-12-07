"""
Tests for AgencyDaemon - TDD Protocol (Article VI)

These tests were written FIRST before the implementation was complete.
"""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import threading

import pytest

from agency_daemon import (
    AgencyDaemon,
    DaemonConfig,
    DaemonState,
    DaemonStatus,
    BacklogPopulator,
    _get_system_memory_gb,
)
from shared.models.backlog import Task, TaskPriority, TaskStatus, TaskType
from tools.backlog_agent import BacklogStorage


class TestDaemonConfig:
    """Test DaemonConfig auto-detection and scaling."""

    def test_auto_detects_cpu_cores(self):
        """Verify CPU cores are auto-detected."""
        import multiprocessing
        config = DaemonConfig()
        assert config.cpu_cores == multiprocessing.cpu_count()

    def test_auto_detects_memory(self):
        """Verify memory is auto-detected."""
        config = DaemonConfig()
        assert config.memory_gb > 0  # Should detect something

    def test_scales_test_workers_based_on_memory(self):
        """Verify test workers scale with available memory."""
        # 128GB should allow many workers (memory_gb // 4 = 32, but capped by cpu_cores - 2)
        config = DaemonConfig()
        config.memory_gb = 128
        config.__post_init__()
        # Should scale up based on memory (at least more than low-memory scenario)
        assert config.test_worker_count >= 10

    def test_limits_test_workers_for_low_memory(self):
        """Verify test workers are limited on low memory systems."""
        config = DaemonConfig()
        config.memory_gb = 8
        config.__post_init__()
        assert config.test_worker_count <= 2

    def test_default_paths(self):
        """Verify default paths are set correctly."""
        config = DaemonConfig()
        assert config.state_dir == Path.home() / ".agency"
        assert config.kill_switch_file == Path.home() / ".agency" / "STOP_DAEMON"


class TestDaemonState:
    """Test DaemonState serialization."""

    def test_to_dict_and_back(self):
        """Verify state can be serialized and deserialized."""
        state = DaemonState(
            status=DaemonStatus.RUNNING,
            started_at=datetime.now(),
            total_cycles=5,
            total_tasks_completed=3,
        )

        data = state.to_dict()
        restored = DaemonState.from_dict(data)

        assert restored.status == DaemonStatus.RUNNING
        assert restored.total_cycles == 5
        assert restored.total_tasks_completed == 3

    def test_handles_none_values(self):
        """Verify None values are handled correctly."""
        state = DaemonState()
        data = state.to_dict()
        restored = DaemonState.from_dict(data)

        assert restored.started_at is None
        assert restored.current_task_id is None


class TestBacklogPopulator:
    """Test BacklogPopulator auto-population."""

    def test_populates_when_below_threshold(self):
        """Verify backlog is populated when below min_size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = BacklogStorage(data_dir=tmpdir)
            logger = MagicMock()
            populator = BacklogPopulator(storage, logger)

            # Should add tasks since backlog is empty
            added = populator.populate_if_needed(min_size=3)

            assert added == 3
            tasks = storage.list_tasks().unwrap()
            assert len(tasks) == 3

    def test_does_not_populate_when_above_threshold(self):
        """Verify backlog is not populated when above min_size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = BacklogStorage(data_dir=tmpdir)
            logger = MagicMock()
            populator = BacklogPopulator(storage, logger)

            # Add 5 tasks manually
            for i in range(5):
                task = Task(
                    id=f"task-{i}",
                    title=f"Existing task {i}",
                    description="Test",
                    task_type=TaskType.TECH_DEBT,
                    priority=TaskPriority.P2,
                    estimated_complexity=2,
                )
                storage.add_task(task)

            # Should not add any tasks
            added = populator.populate_if_needed(min_size=3)

            assert added == 0

    def test_does_not_duplicate_existing_tasks(self):
        """Verify same task title is not added twice."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = BacklogStorage(data_dir=tmpdir)
            logger = MagicMock()
            populator = BacklogPopulator(storage, logger)

            # First population
            added1 = populator.populate_if_needed(min_size=2)

            # Mark all as completed
            for task in storage.list_tasks().unwrap():
                task.status = TaskStatus.COMPLETED
                storage.update_task(task)

            # Second population should add different tasks
            added2 = populator.populate_if_needed(min_size=2)

            # Total unique tasks should be added1 + added2
            all_tasks = storage.list_tasks().unwrap()
            titles = [t.title for t in all_tasks]
            assert len(titles) == len(set(titles))  # All unique


class TestAgencyDaemon:
    """Test AgencyDaemon core functionality."""

    def _make_daemon(self, tmpdir: str) -> AgencyDaemon:
        """Create daemon with test configuration."""
        config = DaemonConfig(
            state_dir=Path(tmpdir),
            log_dir=Path(tmpdir) / "logs",
            kill_switch_file=Path(tmpdir) / "STOP",
            cycle_interval_seconds=1,
            dry_run=True,
        )
        return AgencyDaemon(config)

    def test_initializes_components(self):
        """Verify all components are initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)

            assert daemon.storage is not None
            assert daemon.orchestrator is not None
            assert daemon.populator is not None
            assert daemon.validator is not None
            assert daemon.health_monitor is not None
            assert daemon.watchdog is not None

    def test_creates_directories(self):
        """Verify required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)

            assert daemon.config.state_dir.exists()
            assert daemon.config.log_dir.exists()

    def test_saves_and_loads_state(self):
        """Verify state persistence works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)
            daemon.state.total_tasks_completed = 42
            daemon.state.status = DaemonStatus.RUNNING
            daemon._save_state()

            # Load in new daemon instance
            daemon2 = self._make_daemon(tmpdir)
            loaded_state = daemon2._load_state()

            assert loaded_state.total_tasks_completed == 42
            assert loaded_state.status == DaemonStatus.RUNNING

    def test_kill_switch_detection(self):
        """Verify kill switch is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)

            # No kill switch initially
            assert not daemon._check_kill_switch()

            # Create kill switch
            daemon.config.kill_switch_file.touch()
            assert daemon._check_kill_switch()

    def test_status_returns_correct_info(self):
        """Verify status() returns complete information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)
            daemon.state.total_tasks_completed = 10
            daemon.state.started_at = datetime.now()
            daemon._save_state()

            status = daemon.status()

            assert "status" in status
            assert "hardware" in status
            assert status["total_tasks_completed"] == 10
            assert status["hardware"]["cpu_cores"] > 0

    def test_dry_run_does_not_execute(self):
        """Verify dry run mode doesn't execute tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            daemon = self._make_daemon(tmpdir)

            # Add a task
            task = Task(
                id="test-task",
                title="Test task",
                description="Test",
                task_type=TaskType.TECH_DEBT,
                priority=TaskPriority.P2,
                estimated_complexity=2,
            )
            daemon.storage.add_task(task)

            # Mock orchestrator to verify it's not called
            daemon.orchestrator.execute_task = MagicMock()

            # Run one cycle
            daemon._run_cycle()

            # Orchestrator should NOT be called in dry run
            daemon.orchestrator.execute_task.assert_not_called()

    def test_handles_empty_backlog(self):
        """Verify daemon handles empty backlog gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DaemonConfig(
                state_dir=Path(tmpdir),
                log_dir=Path(tmpdir) / "logs",
                kill_switch_file=Path(tmpdir) / "STOP",
                min_backlog_size=0,  # Disable auto-population
                dry_run=True,
            )
            daemon = AgencyDaemon(config)

            # Mock health check to pass
            daemon.health_monitor.check_health = MagicMock(return_value={"healthy": True})

            # Should not raise
            daemon._run_cycle()

            # Status should be IDLE (no tasks) or remain unchanged
            assert daemon.state.status in (DaemonStatus.IDLE, DaemonStatus.STOPPED)


class TestDaemonSignalHandling:
    """Test graceful shutdown on signals."""

    def test_shutdown_on_sigterm(self):
        """Verify SIGTERM triggers graceful shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DaemonConfig(
                state_dir=Path(tmpdir),
                log_dir=Path(tmpdir) / "logs",
                kill_switch_file=Path(tmpdir) / "STOP",
                cycle_interval_seconds=10,
                dry_run=True,
            )
            daemon = AgencyDaemon(config)

            # Simulate signal
            daemon._handle_signal(15, None)  # SIGTERM

            assert daemon.shutdown_requested is True


class TestSystemMemoryDetection:
    """Test system memory detection."""

    def test_returns_positive_value(self):
        """Verify memory detection returns positive value."""
        memory = _get_system_memory_gb()
        assert memory > 0

    def test_returns_reasonable_value(self):
        """Verify memory detection returns reasonable value (1-1024 GB)."""
        memory = _get_system_memory_gb()
        assert 1 <= memory <= 1024
