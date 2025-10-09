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

    def test_acquire_lock_already_locked_returns_error(self, lock_manager, temp_lock_dir):
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
