"""
Tests for Rollback System - Phase 1, Task 4
Comprehensive state restoration

TDD: Tests written FIRST (Article VI compliance)
"""

from pathlib import Path
from unittest.mock import Mock, patch
import subprocess

import pytest

from tools.rollback_system import (
    RollbackManager,
    Snapshot,
    SnapshotType,
    RollbackResult,
)
from shared.type_definitions.result import Ok, Err


class TestRollbackManagerInit:
    """Test rollback manager initialization"""

    def test_init_default(self):
        """Should initialize with default snapshot directory"""
        rm = RollbackManager()
        assert rm.snapshot_dir.exists()
        assert len(rm.snapshots) == 0

    def test_init_custom_snapshot_dir(self, tmp_path):
        """Should initialize with custom snapshot directory"""
        snapshot_dir = tmp_path / "snapshots"
        rm = RollbackManager(snapshot_dir=snapshot_dir)
        assert rm.snapshot_dir == snapshot_dir


class TestSnapshotCreation:
    """Test snapshot creation"""

    @patch("subprocess.run")
    def test_create_git_snapshot(self, mock_run, tmp_path):
        """Should create git snapshot"""
        mock_run.return_value = Mock(returncode=0, stdout="abc123\n", stderr="")

        rm = RollbackManager(snapshot_dir=tmp_path)

        result = rm.create_snapshot(SnapshotType.GIT, description="Before changes")

        assert result.is_ok()
        snapshot_id = result.unwrap()
        assert snapshot_id in rm.snapshots
        assert rm.snapshots[snapshot_id].snapshot_type == SnapshotType.GIT

    def test_create_file_snapshot(self, tmp_path):
        """Should create file snapshot"""
        rm = RollbackManager(snapshot_dir=tmp_path)
        target_file = tmp_path / "test.txt"
        target_file.write_text("Original content")

        result = rm.create_snapshot(
            SnapshotType.FILE,
            description="File backup",
            metadata={"file_path": str(target_file)},
        )

        assert result.is_ok()
        snapshot_id = result.unwrap()
        assert snapshot_id in rm.snapshots

    @patch("subprocess.run")
    def test_create_full_snapshot(self, mock_run, tmp_path):
        """Should create full system snapshot"""
        mock_run.return_value = Mock(returncode=0, stdout="abc123\n", stderr="")

        rm = RollbackManager(snapshot_dir=tmp_path)

        result = rm.create_snapshot(
            SnapshotType.FULL,
            description="Full backup",
        )

        assert result.is_ok()
        snapshot_id = result.unwrap()
        assert rm.snapshots[snapshot_id].snapshot_type == SnapshotType.FULL


class TestSnapshotRetrieval:
    """Test snapshot retrieval"""

    def test_get_snapshot_by_id(self, tmp_path):
        """Should retrieve snapshot by ID"""
        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(SnapshotType.GIT, "Test")

        snapshot_id = snapshot_id_result.unwrap()
        result = rm.get_snapshot(snapshot_id)

        assert result.is_ok()
        snapshot = result.unwrap()
        assert snapshot.snapshot_id == snapshot_id

    def test_get_nonexistent_snapshot(self, tmp_path):
        """Should handle nonexistent snapshot"""
        rm = RollbackManager(snapshot_dir=tmp_path)

        result = rm.get_snapshot("nonexistent-id")

        assert result.is_err()

    @patch("subprocess.run")
    def test_list_all_snapshots(self, mock_run, tmp_path):
        """Should list all snapshots"""
        mock_run.return_value = Mock(returncode=0, stdout="abc123\n", stderr="")

        rm = RollbackManager(snapshot_dir=tmp_path)

        # Create test file for FILE snapshot
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        rm.create_snapshot(SnapshotType.GIT, "Snapshot 1")
        rm.create_snapshot(SnapshotType.FILE, "Snapshot 2", metadata={"file_path": str(test_file)})
        rm.create_snapshot(SnapshotType.FULL, "Snapshot 3")

        snapshots = rm.list_snapshots()

        assert len(snapshots) == 3

    def test_list_snapshots_by_type(self, tmp_path):
        """Should filter snapshots by type"""
        rm = RollbackManager(snapshot_dir=tmp_path)

        rm.create_snapshot(SnapshotType.GIT, "Git 1")
        rm.create_snapshot(SnapshotType.GIT, "Git 2")
        rm.create_snapshot(SnapshotType.FILE, "File 1")

        git_snapshots = rm.list_snapshots(snapshot_type=SnapshotType.GIT)

        assert len(git_snapshots) == 2
        assert all(s.snapshot_type == SnapshotType.GIT for s in git_snapshots)


class TestGitRollback:
    """Test git rollback"""

    @patch("subprocess.run")
    def test_rollback_git_to_commit(self, mock_run, tmp_path):
        """Should rollback git to specific commit"""
        # Mock git rev-parse for snapshot creation and git cat-file for validation
        def git_side_effect(*args, **kwargs):
            cmd = args[0]
            if "rev-parse" in cmd:
                return Mock(returncode=0, stdout="abc123\n", stderr="")
            elif "cat-file" in cmd:
                return Mock(returncode=0, stdout="", stderr="")
            elif "reset" in cmd:
                return Mock(returncode=0, stdout="", stderr="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = git_side_effect

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(
            SnapshotType.GIT,
            "Before changes",
        )
        snapshot_id = snapshot_id_result.unwrap()

        result = rm.rollback(snapshot_id)

        assert result.is_ok()

    @patch("subprocess.run")
    def test_rollback_git_failure(self, mock_run, tmp_path):
        """Should handle git rollback failure"""
        # Mock successful snapshot creation, validation, but failed rollback
        def git_side_effect(*args, **kwargs):
            cmd = args[0]
            if "rev-parse" in cmd:
                return Mock(returncode=0, stdout="abc123\n", stderr="")
            elif "cat-file" in cmd:
                return Mock(returncode=0, stdout="", stderr="")
            elif "reset" in cmd:
                return Mock(returncode=1, stdout="", stderr="git reset failed")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = git_side_effect

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(
            SnapshotType.GIT,
            "Before changes",
        )
        snapshot_id = snapshot_id_result.unwrap()

        result = rm.rollback(snapshot_id)

        assert result.is_err()


class TestFileRollback:
    """Test file rollback"""

    def test_rollback_file(self, tmp_path):
        """Should rollback file to snapshot state"""
        target_file = tmp_path / "test.txt"
        original_content = "Original content"
        target_file.write_text(original_content)

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(
            SnapshotType.FILE,
            "File backup",
            metadata={"file_path": str(target_file)},
        )
        snapshot_id = snapshot_id_result.unwrap()

        # Modify file
        target_file.write_text("Modified content")

        # Rollback
        result = rm.rollback(snapshot_id)

        assert result.is_ok()
        # File should be restored
        assert target_file.read_text() == original_content

    def test_rollback_deleted_file(self, tmp_path):
        """Should restore deleted file"""
        target_file = tmp_path / "test.txt"
        original_content = "To be deleted"
        target_file.write_text(original_content)

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(
            SnapshotType.FILE,
            "File backup",
            metadata={"file_path": str(target_file)},
        )
        snapshot_id = snapshot_id_result.unwrap()

        # Delete file
        target_file.unlink()

        # Rollback
        result = rm.rollback(snapshot_id)

        assert result.is_ok()
        # File should be restored
        assert target_file.exists()
        assert target_file.read_text() == original_content


class TestFullSystemRollback:
    """Test full system rollback"""

    @patch("subprocess.run")
    def test_rollback_full_system(self, mock_run, tmp_path):
        """Should perform full system rollback"""
        def git_side_effect(*args, **kwargs):
            cmd = args[0]
            if "rev-parse" in cmd:
                return Mock(returncode=0, stdout="abc123\n", stderr="")
            elif "cat-file" in cmd:
                return Mock(returncode=0, stdout="", stderr="")
            elif "reset" in cmd:
                return Mock(returncode=0, stdout="", stderr="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = git_side_effect

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(SnapshotType.FULL, "Full backup")
        snapshot_id = snapshot_id_result.unwrap()

        result = rm.rollback(snapshot_id)

        assert result.is_ok()


class TestSnapshotCleanup:
    """Test snapshot cleanup"""

    def test_delete_snapshot(self, tmp_path):
        """Should delete snapshot"""
        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(SnapshotType.GIT, "Test")
        snapshot_id = snapshot_id_result.unwrap()

        result = rm.delete_snapshot(snapshot_id)

        assert result.is_ok()
        assert snapshot_id not in rm.snapshots

    def test_delete_nonexistent_snapshot(self, tmp_path):
        """Should handle deleting nonexistent snapshot"""
        rm = RollbackManager(snapshot_dir=tmp_path)

        result = rm.delete_snapshot("nonexistent-id")

        assert result.is_err()

    def test_cleanup_old_snapshots(self, tmp_path):
        """Should cleanup snapshots older than retention period"""
        rm = RollbackManager(snapshot_dir=tmp_path, retention_days=7)

        # Create recent snapshots
        rm.create_snapshot(SnapshotType.GIT, "Recent 1")
        rm.create_snapshot(SnapshotType.GIT, "Recent 2")

        # Simulate old snapshots (would need to mock datetime)
        # For now, just verify cleanup doesn't crash
        result = rm.cleanup_old_snapshots()

        assert result.is_ok()


class TestRollbackValidation:
    """Test rollback validation"""

    def test_validate_snapshot_before_rollback(self, tmp_path):
        """Should validate snapshot before rollback"""
        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(SnapshotType.GIT, "Test")
        snapshot_id = snapshot_id_result.unwrap()

        result = rm.validate_snapshot(snapshot_id)

        assert result.is_ok()

    def test_validate_corrupted_snapshot(self, tmp_path):
        """Should detect corrupted snapshot"""
        # Create test file for FILE snapshot
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(
            SnapshotType.FILE,
            "Test",
            metadata={"file_path": str(test_file)},
        )
        snapshot_id = snapshot_id_result.unwrap()

        # Corrupt snapshot by deleting backup file
        snapshot = rm.snapshots[snapshot_id]
        if snapshot.backup_path and snapshot.backup_path.exists():
            snapshot.backup_path.unlink()

        result = rm.validate_snapshot(snapshot_id)

        assert result.is_err()


class TestRollbackHistory:
    """Test rollback history"""

    def test_record_rollback_event(self, tmp_path):
        """Should record rollback events"""
        rm = RollbackManager(snapshot_dir=tmp_path)
        snapshot_id_result = rm.create_snapshot(SnapshotType.GIT, "Test")
        snapshot_id = snapshot_id_result.unwrap()

        rm.rollback(snapshot_id)

        # Should have recorded the rollback
        history = rm.get_rollback_history()
        assert len(history) > 0
        assert history[0]["snapshot_id"] == snapshot_id

    def test_get_rollback_history_limit(self, tmp_path):
        """Should limit rollback history results"""
        rm = RollbackManager(snapshot_dir=tmp_path)

        # Create and rollback multiple snapshots
        for i in range(5):
            snapshot_id_result = rm.create_snapshot(SnapshotType.GIT, f"Test {i}")
            rm.rollback(snapshot_id_result.unwrap())

        # Get limited history
        history = rm.get_rollback_history(limit=3)

        assert len(history) <= 3
