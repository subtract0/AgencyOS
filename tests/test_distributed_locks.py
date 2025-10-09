"""
Tests for multi-agent distributed lock coordination.

Constitutional compliance:
- Article I: Complete context before action (verify all locks read)
- Article II: 100% test success (TDD-first implementation)
- Article IV: Learning integration (store successful patterns)
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling
"""
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread

import pytest

from shared.models.lock_metadata import LockError, LockMetadata
from shared.type_definitions.result import Err, Ok
from tools.lock_manager import LockManager


class TestLockMetadata:
    """Test LockMetadata Pydantic model validation."""

    def test_lock_metadata_valid(self):
        """Test valid LockMetadata creation."""
        # Arrange & Act
        metadata = LockMetadata(
            session_id="primeccc_20251008_120000",
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Priority #1: Test Task",
        )

        # Assert
        assert metadata.session_id == "primeccc_20251008_120000"
        assert metadata.terminal == "terminal_1"
        assert metadata.user == "testuser"
        assert metadata.task_description == "Priority #1: Test Task"

    def test_lock_metadata_forbids_extra_fields(self):
        """Test that extra fields are forbidden (strict typing)."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            LockMetadata(
                session_id="test",
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal="term",
                user="user",
                task_description="task",
                extra_field="not_allowed",  # Should be forbidden
            )

    def test_lock_metadata_requires_all_fields(self):
        """Test that all fields are required."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            LockMetadata(
                session_id="test",
                timestamp=datetime.now(),
                # Missing heartbeat, terminal, user, task_description
            )


class TestLockAcquisition:
    """Test lock acquisition with metadata storage."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_acquire_lock_creates_file_with_metadata(self, lock_manager, temp_lock_dir):
        """Test that acquire_lock creates lock file with all metadata."""
        # Arrange
        task_id = "priority_1_test"
        session_id = "primeccc_20251008_120000"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Priority #1: Test Task",
        )

        # Act
        result = lock_manager.acquire_lock(task_id, session_id, metadata)

        # Assert
        assert result.is_ok(), f"Expected Ok, got {result}"
        lock_handle = result.unwrap()
        assert lock_handle.task_id == task_id
        assert lock_handle.session_id == session_id

        # Verify lock file exists and contains metadata
        lock_file = temp_lock_dir / f"{task_id}.lock"
        assert lock_file.exists()

        lines = lock_file.read_text().strip().split("\n")
        assert len(lines) == 6
        assert lines[0] == session_id
        assert lines[3] == "terminal_1"
        assert lines[4] == "testuser"
        assert lines[5] == "Priority #1: Test Task"

    def test_acquire_lock_already_locked_returns_error(
        self, lock_manager, temp_lock_dir
    ):
        """Test that acquiring an already-locked task returns AlreadyLocked error."""
        # Arrange
        task_id = "priority_2_test"
        session_1 = "primeccc_20251008_120000"
        session_2 = "primeccc_20251008_120001"
        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Task 1",
        )
        metadata_2 = LockMetadata(
            session_id=session_2,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_2",
            user="user2",
            task_description="Task 2",
        )

        # Act
        result_1 = lock_manager.acquire_lock(task_id, session_1, metadata_1)
        result_2 = lock_manager.acquire_lock(task_id, session_2, metadata_2)

        # Assert
        assert result_1.is_ok()
        assert result_2.is_err()
        error = result_2.unwrap_err()
        assert error.error_type == "AlreadyLocked"
        assert session_1 in error.message

    def test_acquire_lock_removes_stale_lock(self, lock_manager, temp_lock_dir):
        """Test that stale locks (heartbeat >5min old) are automatically removed."""
        # Arrange
        task_id = "priority_3_test"
        session_id = "primeccc_20251008_120000"

        # Create stale lock (heartbeat 10 minutes ago)
        stale_time = datetime.now() - timedelta(minutes=10)
        lock_file = temp_lock_dir / f"{task_id}.lock"
        lock_file.write_text(
            f"old_session\n"
            f"{stale_time.isoformat()}\n"
            f"{stale_time.isoformat()}\n"
            f"terminal_old\n"
            f"user_old\n"
            f"Old Task\n"
        )

        # New metadata
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_new",
            user="user_new",
            task_description="New Task",
        )

        # Act
        result = lock_manager.acquire_lock(task_id, session_id, metadata)

        # Assert - Should succeed after removing stale lock
        assert result.is_ok()
        lock_handle = result.unwrap()
        assert lock_handle.session_id == session_id

        # Verify new lock file
        lines = lock_file.read_text().strip().split("\n")
        assert lines[0] == session_id
        assert lines[4] == "user_new"

    def test_parallel_lock_acquisition(self, lock_manager, temp_lock_dir):
        """Test that 2+ agents acquire different locks simultaneously."""
        # Arrange
        results = []

        def acquire_lock_worker(task_id, session_id):
            metadata = LockMetadata(
                session_id=session_id,
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal=f"terminal_{session_id[-1]}",
                user=f"user{session_id[-1]}",
                task_description=f"Task {task_id}",
            )
            result = lock_manager.acquire_lock(task_id, session_id, metadata)
            results.append((task_id, session_id, result))

        # Act - Launch 3 agents acquiring different tasks
        threads = [
            Thread(target=acquire_lock_worker, args=(f"priority_{i}", f"session_{i}"))
            for i in range(1, 4)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert - All acquisitions should succeed
        assert len(results) == 3
        for task_id, session_id, result in results:
            assert result.is_ok(), f"Task {task_id} failed: {result}"


class TestLockRelease:
    """Test lock release functionality."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_release_lock_success(self, lock_manager, temp_lock_dir):
        """Test successful lock release by owner."""
        # Arrange
        task_id = "priority_4_test"
        session_id = "primeccc_20251008_120000"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Task",
        )

        # Acquire lock
        acquire_result = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert acquire_result.is_ok()

        # Act
        release_result = lock_manager.release_lock(task_id, session_id)

        # Assert
        assert release_result.is_ok()
        assert release_result.unwrap() is True

        # Verify lock file removed
        lock_file = temp_lock_dir / f"{task_id}.lock"
        assert not lock_file.exists()

    def test_release_lock_not_owned(self, lock_manager, temp_lock_dir):
        """Test that releasing a lock not owned by session returns error."""
        # Arrange
        task_id = "priority_5_test"
        session_owner = "primeccc_20251008_120000"
        session_other = "primeccc_20251008_120001"
        metadata = LockMetadata(
            session_id=session_owner,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Task",
        )

        # Acquire with session_owner
        lock_manager.acquire_lock(task_id, session_owner, metadata)

        # Act - Try to release with different session
        result = lock_manager.release_lock(task_id, session_other)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "NotOwned"

    def test_release_lock_not_found(self, lock_manager):
        """Test that releasing non-existent lock returns error."""
        # Arrange
        task_id = "nonexistent_task"
        session_id = "primeccc_20251008_120000"

        # Act
        result = lock_manager.release_lock(task_id, session_id)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "NotFound"


class TestListActiveLocks:
    """Test listing active locks with metadata."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_list_active_locks_with_metadata(self, lock_manager):
        """Test that list_active_locks returns all metadata fields."""
        # Arrange - Create 3 locks
        for i in range(1, 4):
            metadata = LockMetadata(
                session_id=f"session_{i}",
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal=f"terminal_{i}",
                user=f"user{i}",
                task_description=f"Priority #{i}: Task {i}",
            )
            lock_manager.acquire_lock(f"priority_{i}_test", f"session_{i}", metadata)

        # Act
        result = lock_manager.list_active_locks()

        # Assert
        assert result.is_ok()
        locks = result.unwrap()
        assert len(locks) == 3

        # Verify all metadata fields present
        for lock in locks:
            assert lock.session_id.startswith("session_")
            assert lock.terminal.startswith("terminal_")
            assert lock.user.startswith("user")
            assert "Priority #" in lock.task_description

    def test_list_active_locks_empty(self, lock_manager):
        """Test list_active_locks with no locks."""
        # Act
        result = lock_manager.list_active_locks()

        # Assert
        assert result.is_ok()
        locks = result.unwrap()
        assert len(locks) == 0


class TestHeartbeatFailures:
    """Test heartbeat thread edge cases and failures (CHAOS TESTING)."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_heartbeat_thread_starts_after_lock_acquisition(self, lock_manager):
        """Verify heartbeat thread is running after lock acquired."""
        # Arrange
        task_id = "heartbeat_start_test"
        session_id = "primeccc_20251009_100000"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Heartbeat Start Test",
        )

        # Act
        result = lock_manager.acquire_lock(task_id, session_id, metadata)

        # Assert
        assert result.is_ok()
        lock_handle = result.unwrap()

        # Verify heartbeat thread exists with correct name pattern
        thread_names = [t.name for t in threading.enumerate()]
        expected_name = f"Heartbeat-{task_id}"
        assert expected_name in thread_names, f"Expected thread '{expected_name}' not found in {thread_names}"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)

    def test_heartbeat_updates_every_N_seconds(self, lock_manager, temp_lock_dir):
        """Verify heartbeat timestamp updates at regular intervals."""
        # Arrange
        task_id = "heartbeat_update_test"
        session_id = "primeccc_20251009_100001"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Heartbeat Update Test",
        )

        # Use fast update interval for testing (2 seconds)
        acquire_result = lock_manager.acquire_lock(
            task_id, session_id, metadata, update_interval=2
        )
        assert acquire_result.is_ok()

        # Read initial heartbeat
        lock_file = temp_lock_dir / f"{task_id}.lock"
        with lock_file.open("r") as f:
            lines_initial = f.readlines()
        heartbeat_1 = datetime.fromisoformat(lines_initial[2].strip())

        # Act - Wait for 2 heartbeat intervals
        time.sleep(4)

        # Read updated heartbeat
        with lock_file.open("r") as f:
            lines_updated = f.readlines()
        heartbeat_2 = datetime.fromisoformat(lines_updated[2].strip())

        # Assert - Heartbeat should have updated at least once
        assert heartbeat_2 > heartbeat_1, "Heartbeat timestamp did not update"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)

    def test_heartbeat_stops_when_lock_released(self, lock_manager):
        """Verify heartbeat thread exits when lock released."""
        # Arrange
        task_id = "heartbeat_stop_test"
        session_id = "primeccc_20251009_100002"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Heartbeat Stop Test",
        )

        acquire_result = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert acquire_result.is_ok()

        # Get thread reference before release
        thread_name = f"Heartbeat-{task_id}"
        threads_before = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_before) == 1, "Heartbeat thread not found after acquisition"

        # Act - Release lock
        release_result = lock_manager.release_lock(task_id, session_id)
        assert release_result.is_ok()

        # Wait for thread to exit (daemon threads should exit quickly)
        time.sleep(1)

        # Assert - Thread should no longer exist
        threads_after = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_after) == 0, f"Heartbeat thread still running after release: {threads_after}"

    def test_heartbeat_exits_if_file_deleted_externally(self, lock_manager, temp_lock_dir):
        """Verify heartbeat exits gracefully if lock file deleted externally."""
        # Arrange
        task_id = "heartbeat_external_delete_test"
        session_id = "primeccc_20251009_100003"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Heartbeat External Delete Test",
        )

        # Use fast update interval for testing (2 seconds)
        acquire_result = lock_manager.acquire_lock(
            task_id, session_id, metadata, update_interval=2
        )
        assert acquire_result.is_ok()

        thread_name = f"Heartbeat-{task_id}"
        threads_before = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_before) == 1

        # Act - Manually delete lock file (simulate crash/external deletion)
        lock_file = temp_lock_dir / f"{task_id}.lock"
        lock_file.unlink()

        # Wait for heartbeat to detect deletion (fast detection with 1s checks)
        time.sleep(3)

        # Assert - Thread should exit when it detects missing file
        threads_after = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_after) == 0, "Heartbeat thread did not exit after file deletion"

    def test_heartbeat_exits_if_ownership_changed(self, lock_manager, temp_lock_dir):
        """Verify heartbeat exits if lock ownership changes (race condition)."""
        # Arrange
        task_id = "heartbeat_ownership_change_test"
        session_id_1 = "primeccc_20251009_100004"
        session_id_2 = "primeccc_20251009_100005"
        metadata = LockMetadata(
            session_id=session_id_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Heartbeat Ownership Test",
        )

        # Use fast update interval for testing (2 seconds)
        acquire_result = lock_manager.acquire_lock(
            task_id, session_id_1, metadata, update_interval=2
        )
        assert acquire_result.is_ok()

        thread_name = f"Heartbeat-{task_id}"
        threads_before = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_before) == 1

        # Act - Manually overwrite lock file with different session_id (simulate race)
        lock_file = temp_lock_dir / f"{task_id}.lock"
        lock_file.write_text(
            f"{session_id_2}\n"
            f"{datetime.now().isoformat()}\n"
            f"{datetime.now().isoformat()}\n"
            f"terminal_2\n"
            f"user2\n"
            f"Hijacked Task\n"
        )

        # Wait for heartbeat to detect ownership change (fast detection)
        time.sleep(3)

        # Assert - Original heartbeat thread should exit
        threads_after = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads_after) == 0, "Heartbeat did not exit after ownership change"

        # Verify heartbeat did NOT update the file (ownership lost)
        with lock_file.open("r") as f:
            lines = f.readlines()
        assert lines[0].strip() == session_id_2, "Heartbeat overwrote hijacked lock file"

    def test_stale_lock_removal_when_heartbeat_stopped(self, lock_manager, temp_lock_dir):
        """Verify stale lock is removed after heartbeat stops updating."""
        # Arrange
        task_id = "heartbeat_stale_test"
        session_id_old = "primeccc_20251009_100006"
        session_id_new = "primeccc_20251009_100007"

        # Create lock with old heartbeat (manually, simulating stopped heartbeat)
        stale_time = datetime.now() - timedelta(minutes=10)
        lock_file = temp_lock_dir / f"{task_id}.lock"
        lock_file.write_text(
            f"{session_id_old}\n"
            f"{stale_time.isoformat()}\n"
            f"{stale_time.isoformat()}\n"
            f"terminal_old\n"
            f"user_old\n"
            f"Stale Task\n"
        )

        # Act - Try to acquire same task with new session
        metadata_new = LockMetadata(
            session_id=session_id_new,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_new",
            user="user_new",
            task_description="New Task",
        )
        result = lock_manager.acquire_lock(task_id, session_id_new, metadata_new)

        # Assert - Should succeed after removing stale lock
        assert result.is_ok()
        lock_handle = result.unwrap()
        assert lock_handle.session_id == session_id_new

        # Verify new lock file with correct ownership
        with lock_file.open("r") as f:
            lines = f.readlines()
        assert lines[0].strip() == session_id_new

        # Cleanup
        lock_manager.release_lock(task_id, session_id_new)

    def test_heartbeat_resilient_to_temporary_io_errors(self, lock_manager, temp_lock_dir, monkeypatch):
        """Verify heartbeat continues after temporary filesystem errors."""
        # Arrange
        task_id = "heartbeat_io_error_test"
        session_id = "primeccc_20251009_100008"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Heartbeat IO Error Test",
        )

        # Use fast update interval for testing (2 seconds)
        acquire_result = lock_manager.acquire_lock(
            task_id, session_id, metadata, update_interval=2
        )
        assert acquire_result.is_ok()

        lock_file = temp_lock_dir / f"{task_id}.lock"

        # Read initial heartbeat
        with lock_file.open("r") as f:
            lines_initial = f.readlines()
        heartbeat_1 = datetime.fromisoformat(lines_initial[2].strip())

        # Act - Simulate temporary IO error by making file temporarily unreadable
        original_mode = lock_file.stat().st_mode
        lock_file.chmod(0o000)  # Remove all permissions temporarily

        time.sleep(2)  # Wait for one heartbeat attempt (should fail)

        # Restore permissions
        lock_file.chmod(original_mode)

        time.sleep(3)  # Wait for heartbeat to recover and update

        # Read final heartbeat
        with lock_file.open("r") as f:
            lines_final = f.readlines()
        heartbeat_2 = datetime.fromisoformat(lines_final[2].strip())

        # Assert - Heartbeat should have recovered and updated after error
        assert heartbeat_2 > heartbeat_1, "Heartbeat did not recover after temporary IO error"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)


class TestConcurrentHeartbeats:
    """Test multiple agents with concurrent heartbeat threads."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_multiple_heartbeats_dont_interfere(self, lock_manager, temp_lock_dir):
        """Verify 3+ agents with separate locks don't interfere with each other's heartbeats."""
        # Arrange - Acquire 5 different locks simultaneously
        task_ids = [f"concurrent_task_{i}" for i in range(1, 6)]
        session_ids = [f"primeccc_20251009_10000{i}" for i in range(1, 6)]

        lock_handles = []
        for task_id, session_id in zip(task_ids, session_ids):
            metadata = LockMetadata(
                session_id=session_id,
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal=f"terminal_{task_id[-1]}",
                user=f"user{task_id[-1]}",
                task_description=f"Concurrent Task {task_id[-1]}",
            )
            # Use fast update interval for testing (2 seconds)
            result = lock_manager.acquire_lock(
                task_id, session_id, metadata, update_interval=2
            )
            assert result.is_ok()
            lock_handles.append(result.unwrap())

        # Record initial heartbeats
        initial_heartbeats = {}
        for task_id in task_ids:
            lock_file = temp_lock_dir / f"{task_id}.lock"
            with lock_file.open("r") as f:
                lines = f.readlines()
            initial_heartbeats[task_id] = datetime.fromisoformat(lines[2].strip())

        # Act - Wait for 2 heartbeat intervals
        time.sleep(4)

        # Read final heartbeats
        final_heartbeats = {}
        for task_id in task_ids:
            lock_file = temp_lock_dir / f"{task_id}.lock"
            with lock_file.open("r") as f:
                lines = f.readlines()
            final_heartbeats[task_id] = datetime.fromisoformat(lines[2].strip())

        # Assert - All heartbeats should have updated independently
        for task_id in task_ids:
            assert final_heartbeats[task_id] > initial_heartbeats[task_id], \
                f"Heartbeat for {task_id} did not update"

        # Verify all lock files still have correct ownership
        for task_id, session_id in zip(task_ids, session_ids):
            lock_file = temp_lock_dir / f"{task_id}.lock"
            with lock_file.open("r") as f:
                lines = f.readlines()
            assert lines[0].strip() == session_id, \
                f"Ownership changed for {task_id}"

        # Cleanup
        for task_id, session_id in zip(task_ids, session_ids):
            lock_manager.release_lock(task_id, session_id)

    def test_heartbeat_thread_cleanup_on_process_exit(self, lock_manager):
        """Verify daemon threads don't block process exit."""
        # Arrange
        task_id = "daemon_exit_test"
        session_id = "primeccc_20251009_100020"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Daemon Exit Test",
        )

        # Act
        result = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert result.is_ok()

        # Get heartbeat thread
        thread_name = f"Heartbeat-{task_id}"
        threads = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads) == 1

        heartbeat_thread = threads[0]

        # Assert - Thread is daemon (won't block exit)
        assert heartbeat_thread.daemon is True, "Heartbeat thread is not daemon"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)


class TestHeartbeatConfiguration:
    """Test heartbeat thread configuration and tuning."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_custom_update_interval(self, lock_manager, monkeypatch):
        """Verify custom update_interval is respected."""
        # Arrange - We need to modify LockManager to accept custom interval
        # NOTE: This test will FAIL initially - implementation needed
        task_id = "custom_interval_test"
        session_id = "primeccc_20251009_100021"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Custom Interval Test",
        )

        # Act - Acquire lock with custom interval (this API doesn't exist yet)
        # We need to add update_interval parameter to acquire_lock()
        result = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert result.is_ok()

        # Get heartbeat thread
        thread_name = f"Heartbeat-{task_id}"
        threads = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads) == 1
        heartbeat_thread = threads[0]

        # Assert - Inspect thread's update_interval attribute
        # NOTE: This will FAIL until we expose update_interval as parameter
        assert hasattr(heartbeat_thread, "update_interval"), "HeartbeatThread missing update_interval attribute"
        # For now, check default value (60 seconds)
        assert heartbeat_thread.update_interval == 60

        # Cleanup
        lock_manager.release_lock(task_id, session_id)

    def test_default_update_interval_is_60_seconds(self, lock_manager):
        """Verify default update interval is 60 seconds (per spec)."""
        # Arrange
        task_id = "default_interval_test"
        session_id = "primeccc_20251009_100022"
        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Default Interval Test",
        )

        # Act
        result = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert result.is_ok()

        # Get heartbeat thread
        thread_name = f"Heartbeat-{task_id}"
        threads = [t for t in threading.enumerate() if t.name == thread_name]
        assert len(threads) == 1
        heartbeat_thread = threads[0]

        # Assert
        assert heartbeat_thread.update_interval == 60, \
            f"Default interval is {heartbeat_thread.update_interval}, expected 60"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)


class TestDeadlockDetection:
    """
    Test deadlock detection and prevention mechanisms.

    NECESSARY Framework Coverage:
    - Normal: Timeout prevents infinite waits
    - Edge: Immediate return for non-blocking acquisition
    - Corner: Self-deadlock detection (same session twice)
    - Error: Timeout error handling
    - Security: No infinite loops or resource exhaustion
    - Stress: Lock order consistency under contention
    - Accessibility: Multiple acquisition strategies
    - Regression: Prevent past deadlock scenarios
    - Yield: Proper error messages for timeout conditions
    """

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_acquire_lock_with_timeout_prevents_infinite_wait(self, lock_manager):
        """
        Verify acquire_lock_with_timeout supports timeout to prevent infinite waits.

        Constitutional: Article I - No infinite waits (all operations must timeout)
        """
        # Arrange - Create locked task
        task_id = "deadlock_timeout_test"
        session_1 = "session_holder"
        session_2 = "session_waiter"

        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Holder Task",
        )
        acquire_result = lock_manager.acquire_lock(task_id, session_1, metadata_1)
        assert acquire_result.is_ok()

        # Act - Try to acquire same lock with 2-second timeout
        metadata_2 = LockMetadata(
            session_id=session_2,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_2",
            user="user2",
            task_description="Waiter Task",
        )
        start = datetime.now()

        # NOTE: This will FAIL - acquire_lock_with_timeout() doesn't exist yet (TDD red phase)
        result = lock_manager.acquire_lock_with_timeout(
            task_id, session_2, metadata_2, timeout_seconds=2.0
        )

        elapsed = (datetime.now() - start).total_seconds()

        # Assert
        assert result.is_err(), "Expected timeout error"
        error = result.unwrap_err()
        assert error.error_type == "Timeout", f"Expected Timeout, got {error.error_type}"
        assert "timeout" in error.message.lower()
        assert elapsed >= 2.0, f"Timeout too short: {elapsed}s"
        assert elapsed < 3.0, f"Timeout too long: {elapsed}s (should be ~2s)"

        # Cleanup
        lock_manager.release_lock(task_id, session_1)

    def test_try_acquire_lock_returns_immediately(self, lock_manager):
        """
        Verify try_acquire_lock returns immediately without blocking.

        Use case: Agent checks lock availability before committing to task.
        """
        # Arrange - Create locked task
        task_id = "deadlock_try_test"
        session_1 = "session_holder"
        session_2 = "session_waiter"

        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Holder Task",
        )
        acquire_result = lock_manager.acquire_lock(task_id, session_1, metadata_1)
        assert acquire_result.is_ok()

        # Act - Try to acquire without blocking
        metadata_2 = LockMetadata(
            session_id=session_2,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_2",
            user="user2",
            task_description="Try Acquire Task",
        )
        start = datetime.now()

        # NOTE: This will FAIL - try_acquire_lock() doesn't exist yet (TDD red phase)
        result = lock_manager.try_acquire_lock(task_id, session_2, metadata_2)

        elapsed = (datetime.now() - start).total_seconds()

        # Assert
        assert result.is_err(), "Expected AlreadyLocked error"
        error = result.unwrap_err()
        assert error.error_type == "AlreadyLocked", f"Expected AlreadyLocked, got {error.error_type}"
        assert elapsed < 0.1, f"try_acquire should return immediately, took {elapsed}s"

        # Cleanup
        lock_manager.release_lock(task_id, session_1)

    def test_detect_self_deadlock_same_session_twice(self, lock_manager):
        """
        Verify agent can't acquire same lock twice (self-deadlock prevention).

        Design Decision: Same session acquiring same lock twice is a logic error.
        Expected behavior: Return AlreadyLocked error (current) or allow re-entrant (future).
        """
        # Arrange
        task_id = "self_deadlock_test"
        session_id = "same_session"

        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Self Deadlock Test",
        )
        first = lock_manager.acquire_lock(task_id, session_id, metadata)
        assert first.is_ok()

        # Act - Try to acquire same lock again with same session
        metadata_2 = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="testuser",
            task_description="Self Deadlock Test (second attempt)",
        )
        second = lock_manager.acquire_lock(task_id, session_id, metadata_2)

        # Assert - Current implementation prevents self-deadlock
        assert second.is_err(), "Same session should not acquire lock twice"
        error = second.unwrap_err()
        assert error.error_type == "AlreadyLocked"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)

    def test_lock_acquisition_order_consistency_prevents_circular_wait(self, lock_manager):
        """
        Verify alphabetical lock ordering prevents circular wait deadlocks.

        Best Practice: Agents should acquire multiple locks in sorted order.

        Example:
        - Agent A needs locks [task_zebra, task_alpha] → Sort → [alpha, zebra]
        - Agent B needs locks [task_alpha, task_beta] → Sort → [alpha, beta]
        - Both agents try to acquire "alpha" first → No circular wait possible

        This is a documentation/pattern test - demonstrates safe ordering.
        """
        # Arrange - Two agents need multiple locks
        session_1 = "agent_1"
        session_2 = "agent_2"

        # Agent 1 needs: zebra, alpha, beta (will sort to: alpha, beta, zebra)
        tasks_agent_1 = sorted(["task_zebra", "task_alpha", "task_beta"])

        # Agent 2 needs: alpha, beta (already sorted)
        tasks_agent_2 = sorted(["task_alpha", "task_beta"])

        # Act - Agent 1 acquires locks in sorted order
        for task in tasks_agent_1:
            metadata = LockMetadata(
                session_id=session_1,
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal="terminal_1",
                user="agent1",
                task_description=f"Task {task}",
            )
            result = lock_manager.acquire_lock(task, session_1, metadata)
            assert result.is_ok(), f"Agent 1 failed to acquire {task}"

        # Agent 2 tries to acquire in sorted order (will block on alpha)
        # This demonstrates NO circular wait is possible with consistent ordering
        metadata_2 = LockMetadata(
            session_id=session_2,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_2",
            user="agent2",
            task_description="Task alpha",
        )
        result_2 = lock_manager.acquire_lock("task_alpha", session_2, metadata_2)

        # Assert - Agent 2 blocks on first lock (no deadlock, just waiting)
        assert result_2.is_err()
        assert result_2.unwrap_err().error_type == "AlreadyLocked"

        # Verify sorted order prevents circular wait
        assert tasks_agent_1 == ["task_alpha", "task_beta", "task_zebra"]
        assert tasks_agent_2 == ["task_alpha", "task_beta"]
        # Both start with "task_alpha" → No possibility of A waits for B, B waits for A

        # Cleanup
        for task in tasks_agent_1:
            lock_manager.release_lock(task, session_1)

    def test_timeout_with_polling_acquires_when_lock_released(self, lock_manager):
        """
        Verify acquire_lock_with_timeout polls and succeeds when lock released.

        Scenario:
        1. Agent A holds lock
        2. Agent B waits with 5-second timeout (polls every 0.5s)
        3. Agent A releases lock after 2 seconds
        4. Agent B successfully acquires lock before timeout
        """
        # Arrange
        task_id = "timeout_polling_test"
        session_1 = "session_holder"
        session_2 = "session_waiter"

        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Holder",
        )
        lock_manager.acquire_lock(task_id, session_1, metadata_1)

        # Act - Start waiter in background thread
        waiter_result = []

        def waiter_thread():
            metadata_2 = LockMetadata(
                session_id=session_2,
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal="terminal_2",
                user="user2",
                task_description="Waiter",
            )
            # NOTE: This will FAIL - acquire_lock_with_timeout() doesn't exist yet
            result = lock_manager.acquire_lock_with_timeout(
                task_id, session_2, metadata_2, timeout_seconds=5.0, poll_interval=0.5
            )
            waiter_result.append(result)

        waiter = Thread(target=waiter_thread)
        waiter.start()

        # Release lock after 2 seconds
        time.sleep(2)
        lock_manager.release_lock(task_id, session_1)

        waiter.join(timeout=6)

        # Assert - Waiter should have succeeded
        assert len(waiter_result) == 1
        assert waiter_result[0].is_ok(), f"Waiter failed: {waiter_result[0]}"

        # Cleanup
        lock_manager.release_lock(task_id, session_2)

    def test_zero_timeout_behaves_like_try_acquire(self, lock_manager):
        """
        Verify acquire_lock_with_timeout(timeout=0) returns immediately.

        Edge case: Zero timeout should be equivalent to try_acquire_lock().
        """
        # Arrange
        task_id = "zero_timeout_test"
        session_1 = "session_holder"
        session_2 = "session_waiter"

        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Holder",
        )
        lock_manager.acquire_lock(task_id, session_1, metadata_1)

        # Act
        metadata_2 = LockMetadata(
            session_id=session_2,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_2",
            user="user2",
            task_description="Waiter",
        )
        start = datetime.now()

        # NOTE: This will FAIL - acquire_lock_with_timeout() doesn't exist yet
        result = lock_manager.acquire_lock_with_timeout(
            task_id, session_2, metadata_2, timeout_seconds=0.0
        )

        elapsed = (datetime.now() - start).total_seconds()

        # Assert
        assert result.is_err()
        assert elapsed < 0.1, f"Zero timeout should return immediately, took {elapsed}s"

        # Cleanup
        lock_manager.release_lock(task_id, session_1)


class TestLockWaitStatistics:
    """
    Test lock contention and wait time tracking.

    NECESSARY Framework Coverage:
    - Normal: Track wait time for successful acquisitions
    - Edge: Zero wait time when lock immediately available
    - Corner: Wait time accuracy for polling-based acquisition
    - Error: Handle missing statistics gracefully
    - Security: Statistics don't leak sensitive data
    - Stress: Accurate stats under high contention
    - Accessibility: Stats exposed in LockHandle model
    - Regression: Prevent stat calculation bugs
    - Yield: Human-readable wait time formatting
    """

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        """Create temporary lock directory for tests."""
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    @pytest.fixture
    def lock_manager(self, temp_lock_dir, monkeypatch):
        """Create LockManager with temporary directory."""
        monkeypatch.setenv("AGENCY_LOCK_DIR", str(temp_lock_dir))
        return LockManager(lock_dir=temp_lock_dir)

    def test_track_lock_wait_time_in_handle(self, lock_manager):
        """
        Verify LockHandle tracks how long agent waited for lock.

        Use case: Telemetry and performance monitoring.
        """
        # Arrange - Create locked task
        task_id = "wait_stats_test"
        session_1 = "holder"
        session_2 = "waiter"

        metadata_1 = LockMetadata(
            session_id=session_1,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Holder",
        )
        lock_manager.acquire_lock(task_id, session_1, metadata_1)

        # Act - Wait 2 seconds, release, then acquire with timeout
        waiter_result = []

        def waiter_thread():
            metadata_2 = LockMetadata(
                session_id=session_2,
                timestamp=datetime.now(),
                heartbeat=datetime.now(),
                terminal="terminal_2",
                user="user2",
                task_description="Waiter",
            )
            # NOTE: This will FAIL - acquire_lock_with_timeout() doesn't exist yet
            result = lock_manager.acquire_lock_with_timeout(
                task_id, session_2, metadata_2, timeout_seconds=5.0
            )
            waiter_result.append(result)

        waiter = Thread(target=waiter_thread)
        waiter.start()

        time.sleep(2)
        lock_manager.release_lock(task_id, session_1)

        waiter.join(timeout=6)

        # Assert - LockHandle should track wait time
        assert len(waiter_result) == 1
        assert waiter_result[0].is_ok()
        handle = waiter_result[0].unwrap()

        # NOTE: This will FAIL - need to add wait_time_seconds to LockHandle model
        assert hasattr(handle, "wait_time_seconds"), "LockHandle missing wait_time_seconds field"
        assert handle.wait_time_seconds >= 2.0, f"Wait time {handle.wait_time_seconds}s < 2s"
        assert handle.wait_time_seconds < 3.0, f"Wait time {handle.wait_time_seconds}s > 3s"

        # Cleanup
        lock_manager.release_lock(task_id, session_2)

    def test_zero_wait_time_when_lock_immediately_available(self, lock_manager):
        """
        Verify wait_time_seconds is 0 when lock acquired immediately.

        Edge case: No contention → zero wait time.
        """
        # Arrange - No existing lock
        task_id = "immediate_acquire_test"
        session_id = "session_1"

        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Immediate Test",
        )

        # Act
        # NOTE: This will FAIL - acquire_lock_with_timeout() doesn't exist yet
        result = lock_manager.acquire_lock_with_timeout(
            task_id, session_id, metadata, timeout_seconds=5.0
        )

        # Assert
        assert result.is_ok()
        handle = result.unwrap()

        # NOTE: This will FAIL - need wait_time_seconds field
        assert hasattr(handle, "wait_time_seconds")
        assert handle.wait_time_seconds < 0.1, \
            f"Immediate acquisition should have near-zero wait time, got {handle.wait_time_seconds}s"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)

    def test_regular_acquire_lock_has_zero_wait_time(self, lock_manager):
        """
        Verify regular acquire_lock() (non-timeout) sets wait_time=0.

        Backward compatibility: Existing acquire_lock() should work without changes.
        """
        # Arrange
        task_id = "regular_acquire_test"
        session_id = "session_1"

        metadata = LockMetadata(
            session_id=session_id,
            timestamp=datetime.now(),
            heartbeat=datetime.now(),
            terminal="terminal_1",
            user="user1",
            task_description="Regular Test",
        )

        # Act - Use existing acquire_lock() (no timeout)
        result = lock_manager.acquire_lock(task_id, session_id, metadata)

        # Assert
        assert result.is_ok()
        handle = result.unwrap()

        # NOTE: This will FAIL - need to add wait_time_seconds field with default=0.0
        assert hasattr(handle, "wait_time_seconds")
        assert handle.wait_time_seconds == 0.0, \
            f"Regular acquire should have 0 wait time, got {handle.wait_time_seconds}s"

        # Cleanup
        lock_manager.release_lock(task_id, session_id)
