"""Unit tests for rollback system.

Tests the rollback functionality for autonomous operations:
- Snapshot creation
- File restoration
- Context manager usage
"""

import pytest
from pathlib import Path

import sys

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSnapshotCreation:
    """Tests for snapshot creation."""

    def test_create_snapshot_returns_result(self, tmp_path):
        """Test that create_snapshot returns a Result."""
        from tools.rollback import RollbackManager

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.create_snapshot([str(test_file)], "test snapshot")

        assert result.is_ok()

    def test_create_snapshot_captures_content(self, tmp_path):
        """Test that snapshot captures file content."""
        from tools.rollback import RollbackManager

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.create_snapshot([str(test_file)], "test snapshot")

        assert result.is_ok()
        snapshot = result.unwrap()
        assert str(test_file) in snapshot.files
        assert snapshot.files[str(test_file)] == "original content"

    def test_create_snapshot_generates_id(self, tmp_path):
        """Test that snapshot generates unique ID."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.create_snapshot([str(test_file)], "test")

        assert result.is_ok()
        snapshot = result.unwrap()
        assert snapshot.id.startswith("snap_")

    def test_create_snapshot_saves_to_disk(self, tmp_path):
        """Test that snapshot is saved to disk."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.create_snapshot([str(test_file)], "test")

        assert result.is_ok()
        snapshot = result.unwrap()

        # Check file exists
        snapshot_file = tmp_path / "snapshots" / f"{snapshot.id}.json"
        assert snapshot_file.exists()

    def test_create_snapshot_handles_nonexistent_file(self, tmp_path):
        """Test that snapshot handles non-existent files (for new file creation)."""
        from tools.rollback import RollbackManager

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.create_snapshot([str(tmp_path / "nonexistent.py")], "test")

        # Should succeed - records empty content for deletion on rollback
        assert result.is_ok()


class TestSnapshotLoading:
    """Tests for loading snapshots."""

    def test_load_snapshot_returns_result(self, tmp_path):
        """Test that load_snapshot returns a Result."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        create_result = manager.create_snapshot([str(test_file)], "test")
        snapshot_id = create_result.unwrap().id

        load_result = manager.load_snapshot(snapshot_id)
        assert load_result.is_ok()

    def test_load_snapshot_restores_data(self, tmp_path):
        """Test that loaded snapshot has correct data."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        create_result = manager.create_snapshot([str(test_file)], "test description")
        snapshot_id = create_result.unwrap().id

        # Clear current snapshot
        manager.current_snapshot = None

        load_result = manager.load_snapshot(snapshot_id)
        assert load_result.is_ok()

        snapshot = load_result.unwrap()
        assert snapshot.description == "test description"
        assert str(test_file) in snapshot.files

    def test_load_nonexistent_snapshot_returns_error(self, tmp_path):
        """Test that loading non-existent snapshot returns error."""
        from tools.rollback import RollbackManager

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        result = manager.load_snapshot("snap_nonexistent")

        assert result.is_err()
        assert "not found" in result.unwrap_err()


class TestRollback:
    """Tests for rollback functionality."""

    def test_rollback_restores_content(self, tmp_path):
        """Test that rollback restores file content."""
        from tools.rollback import RollbackManager

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        # Create snapshot
        result = manager.create_snapshot([str(test_file)], "test")
        assert result.is_ok()

        # Modify file
        test_file.write_text("modified content")
        assert test_file.read_text() == "modified content"

        # Rollback
        rollback_result = manager.rollback()
        assert rollback_result.is_ok()

        # Verify restored
        assert test_file.read_text() == "original content"

    def test_rollback_returns_result_with_info(self, tmp_path):
        """Test that rollback returns result with restoration info."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        manager.create_snapshot([str(test_file)], "test")

        test_file.write_text("modified")

        result = manager.rollback()
        assert result.is_ok()

        rollback_result = result.unwrap()
        assert rollback_result.success
        assert len(rollback_result.files_restored) > 0

    def test_rollback_by_id(self, tmp_path):
        """Test rollback by specific snapshot ID."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("version 1")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        # Create first snapshot
        result1 = manager.create_snapshot([str(test_file)], "snapshot 1")
        snap_id = result1.unwrap().id

        # Create second version
        test_file.write_text("version 2")
        manager.create_snapshot([str(test_file)], "snapshot 2")

        # Modify again
        test_file.write_text("version 3")

        # Rollback to first snapshot
        result = manager.rollback(snap_id)
        assert result.is_ok()
        assert test_file.read_text() == "version 1"

    def test_rollback_without_snapshot_returns_error(self, tmp_path):
        """Test that rollback without snapshot returns error."""
        from tools.rollback import RollbackManager

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")
        manager.current_snapshot = None

        result = manager.rollback()
        assert result.is_err()
        assert "No snapshot" in result.unwrap_err()


class TestContextManager:
    """Tests for with_rollback context manager."""

    def test_context_manager_creates_snapshot(self, tmp_path):
        """Test that context manager creates snapshot."""
        from tools.rollback import with_rollback, RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        # Override global manager for test
        import tools.rollback
        original_manager = tools.rollback._ROLLBACK
        tools.rollback._ROLLBACK = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        try:
            with with_rollback([str(test_file)], "test") as snapshot:
                assert snapshot is not None
                assert snapshot.id.startswith("snap_")
        finally:
            tools.rollback._ROLLBACK = original_manager

    def test_context_manager_rollback_on_exception(self, tmp_path):
        """Test that context manager rolls back on exception."""
        from tools.rollback import with_rollback, RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("original")

        import tools.rollback
        original_manager = tools.rollback._ROLLBACK
        tools.rollback._ROLLBACK = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        try:
            with pytest.raises(ValueError):
                with with_rollback([str(test_file)], "test"):
                    test_file.write_text("modified")
                    raise ValueError("Test error")

            # File should be restored
            assert test_file.read_text() == "original"
        finally:
            tools.rollback._ROLLBACK = original_manager

    def test_context_manager_keeps_changes_on_success(self, tmp_path):
        """Test that context manager keeps changes on success."""
        from tools.rollback import with_rollback, RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("original")

        import tools.rollback
        original_manager = tools.rollback._ROLLBACK
        tools.rollback._ROLLBACK = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        try:
            with with_rollback([str(test_file)], "test"):
                test_file.write_text("modified")

            # File should keep changes
            assert test_file.read_text() == "modified"
        finally:
            tools.rollback._ROLLBACK = original_manager


class TestSnapshotCleanup:
    """Tests for snapshot cleanup."""

    def test_cleanup_removes_old_snapshots(self, tmp_path):
        """Test that cleanup removes old snapshots."""
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        # Create multiple snapshots
        for i in range(10):
            manager.create_snapshot([str(test_file)], f"snapshot {i}")

        # Cleanup, keeping only 3
        removed = manager.cleanup_old_snapshots(keep_last=3)

        assert removed == 7
        remaining = list((tmp_path / "snapshots").glob("snap_*.json"))
        assert len(remaining) == 3

    def test_list_snapshots_returns_recent(self, tmp_path):
        """Test that list_snapshots returns recent snapshots."""
        from tools.rollback import RollbackManager
        import time

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        manager = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        # Create snapshots with slight delay for unique timestamps
        for i in range(5):
            manager.create_snapshot([str(test_file)], f"snapshot {i}")
            time.sleep(0.01)

        snapshots = manager.list_snapshots(limit=3)
        assert len(snapshots) == 3
        assert all("id" in s for s in snapshots)
        assert all("timestamp" in s for s in snapshots)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_snapshot_function(self, tmp_path):
        """Test create_snapshot convenience function."""
        from tools.rollback import create_snapshot, get_rollback_manager

        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        # Override manager
        import tools.rollback
        from tools.rollback import RollbackManager
        original = tools.rollback._ROLLBACK
        tools.rollback._ROLLBACK = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        try:
            result = create_snapshot([str(test_file)], "test")
            assert result.is_ok()
        finally:
            tools.rollback._ROLLBACK = original

    def test_rollback_function(self, tmp_path):
        """Test rollback convenience function."""
        from tools.rollback import create_snapshot, rollback
        from tools.rollback import RollbackManager

        test_file = tmp_path / "test.py"
        test_file.write_text("original")

        import tools.rollback
        original = tools.rollback._ROLLBACK
        tools.rollback._ROLLBACK = RollbackManager(snapshot_dir=tmp_path / "snapshots")

        try:
            create_snapshot([str(test_file)], "test")
            test_file.write_text("modified")

            result = rollback()
            assert result.is_ok()
            assert test_file.read_text() == "original"
        finally:
            tools.rollback._ROLLBACK = original
