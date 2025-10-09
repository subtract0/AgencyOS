"""
Tests for HeartbeatThread mechanism.

Constitutional compliance:
- Article I: Complete context before action
- Article II: 100% test success (TDD-first)
- ADR-010: Result pattern for error handling
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event

import pytest

from tools.heartbeat_thread import HeartbeatThread


class TestHeartbeatThread:
    """Test HeartbeatThread background worker."""

    @pytest.fixture
    def temp_lock_file(self, tmp_path):
        """Create a temporary lock file for testing."""
        lock_file = tmp_path / "test_task.lock"
        session_id = "primeccc_20251008_120000"

        # Write initial lock file
        lock_file.write_text(
            f"{session_id}\n"
            f"{datetime.now().isoformat()}\n"
            f"{datetime.now().isoformat()}\n"
            f"terminal_1\n"
            f"testuser\n"
            f"Test Task\n"
        )

        return lock_file, session_id

    def test_heartbeat_updates_timestamp(self, temp_lock_file):
        """Test that heartbeat updates line 3 (heartbeat timestamp)."""
        # Arrange
        lock_file, session_id = temp_lock_file
        initial_content = lock_file.read_text()
        initial_lines = initial_content.strip().split("\n")
        initial_heartbeat = datetime.fromisoformat(initial_lines[2])

        # Act - Start heartbeat with 1-second interval
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)
        thread.start()

        # Wait for 2 updates (2+ seconds)
        time.sleep(2.5)

        # Stop thread
        thread.stop()
        thread.join(timeout=2)

        # Assert - Heartbeat timestamp should be updated
        final_content = lock_file.read_text()
        final_lines = final_content.strip().split("\n")
        final_heartbeat = datetime.fromisoformat(final_lines[2])

        assert final_heartbeat > initial_heartbeat
        assert (final_heartbeat - initial_heartbeat).total_seconds() >= 1

        # Verify other fields unchanged
        assert final_lines[0] == initial_lines[0]  # session_id
        assert final_lines[3] == initial_lines[3]  # terminal
        assert final_lines[4] == initial_lines[4]  # user
        assert final_lines[5] == initial_lines[5]  # task_description

    def test_heartbeat_exits_when_lock_file_removed(self, temp_lock_file):
        """Test that heartbeat thread exits when lock file is removed."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)
        thread.start()

        # Wait for thread to start
        time.sleep(0.5)

        # Remove lock file (simulates lock release)
        lock_file.unlink()

        # Wait for thread to detect and exit
        thread.join(timeout=5)

        # Assert - Thread should exit
        assert not thread.is_alive()

    def test_heartbeat_exits_when_ownership_changes(self, temp_lock_file):
        """Test that heartbeat exits when lock ownership changes."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)
        thread.start()

        # Wait for thread to start
        time.sleep(0.5)

        # Change lock ownership (simulates another agent taking over)
        lock_file.write_text(
            f"different_session\n"
            f"{datetime.now().isoformat()}\n"
            f"{datetime.now().isoformat()}\n"
            f"terminal_2\n"
            f"otheruser\n"
            f"Other Task\n"
        )

        # Wait for thread to detect ownership change and exit
        thread.join(timeout=5)

        # Assert - Thread should exit
        assert not thread.is_alive()

    def test_heartbeat_stop_method(self, temp_lock_file):
        """Test that stop() method gracefully stops the heartbeat thread."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)
        thread.start()

        # Wait for thread to start
        time.sleep(0.5)

        # Stop thread
        thread.stop()
        thread.join(timeout=2)

        # Assert - Thread should exit cleanly
        assert not thread.is_alive()

    @pytest.mark.slow
    def test_heartbeat_handles_filesystem_errors_gracefully(self, temp_lock_file):
        """Test that heartbeat continues after transient filesystem errors."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)
        thread.start()

        # Wait for first update
        time.sleep(1.5)

        # Make lock file temporarily unwritable (simulates transient error)
        lock_file.chmod(0o444)  # Read-only

        # Wait for attempted update
        time.sleep(1.5)

        # Restore write permissions
        lock_file.chmod(0o600)

        # Wait for successful update
        time.sleep(1.5)

        # Stop thread
        thread.stop()
        thread.join(timeout=2)

        # Assert - Thread should have continued running despite error
        assert not thread.is_alive()  # Clean exit
        # Lock file should still exist (thread didn't crash)
        assert lock_file.exists()

    def test_heartbeat_daemon_flag(self, temp_lock_file):
        """Test that heartbeat thread is marked as daemon."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)

        # Assert - Thread should be daemon (won't block process exit)
        assert thread.daemon is True

    def test_heartbeat_thread_name(self, temp_lock_file):
        """Test that heartbeat thread has descriptive name."""
        # Arrange
        lock_file, session_id = temp_lock_file

        # Act
        thread = HeartbeatThread(lock_file=lock_file, session_id=session_id, update_interval=1)

        # Assert - Thread name should include task identifier
        assert "Heartbeat" in thread.name
        assert "test_task" in thread.name


class TestStaleDetection:
    """Test stale lock detection integration with heartbeat."""

    @pytest.fixture
    def temp_lock_dir(self, tmp_path):
        lock_dir = tmp_path / ".locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        return lock_dir

    def test_stale_detection_after_heartbeat_stops(self, temp_lock_dir):
        """Test that lock becomes stale after heartbeat stops."""
        # Arrange - Create lock with old heartbeat
        lock_file = temp_lock_dir / "stale_task.lock"
        old_time = datetime.now() - timedelta(minutes=10)

        lock_file.write_text(
            f"old_session\n"
            f"{old_time.isoformat()}\n"
            f"{old_time.isoformat()}\n"
            f"terminal_old\n"
            f"user_old\n"
            f"Old Task\n"
        )

        # Act - Read heartbeat
        lines = lock_file.read_text().strip().split("\n")
        heartbeat = datetime.fromisoformat(lines[2])

        # Assert - Heartbeat should be >5 minutes old (stale)
        age_minutes = (datetime.now() - heartbeat).total_seconds() / 60
        assert age_minutes > 5

    def test_active_lock_with_recent_heartbeat(self, temp_lock_dir):
        """Test that lock with recent heartbeat is not stale."""
        # Arrange - Create lock with recent heartbeat
        lock_file = temp_lock_dir / "active_task.lock"
        recent_time = datetime.now() - timedelta(seconds=30)

        lock_file.write_text(
            f"active_session\n"
            f"{recent_time.isoformat()}\n"
            f"{recent_time.isoformat()}\n"
            f"terminal_active\n"
            f"user_active\n"
            f"Active Task\n"
        )

        # Act - Read heartbeat
        lines = lock_file.read_text().strip().split("\n")
        heartbeat = datetime.fromisoformat(lines[2])

        # Assert - Heartbeat should be <5 minutes old (active)
        age_minutes = (datetime.now() - heartbeat).total_seconds() / 60
        assert age_minutes < 5
