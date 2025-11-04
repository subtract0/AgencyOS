"""
Tests for Atomic Operations - Phase 1, Task 3
Transaction-like guarantees for multi-file changes

TDD: Tests written FIRST (Article VI compliance)
"""

from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

import pytest

from tools.atomic_ops import (
    AtomicTransaction,
    FileOperation,
    OperationType,
    TransactionStatus,
)


class TestAtomicTransactionInit:
    """Test atomic transaction initialization"""

    def test_init_default(self):
        """Should initialize with default staging directory"""
        tx = AtomicTransaction()
        assert tx.status == TransactionStatus.PENDING
        assert len(tx.operations) == 0

    def test_init_custom_staging_dir(self, tmp_path):
        """Should initialize with custom staging directory"""
        staging = tmp_path / "staging"
        tx = AtomicTransaction(staging_dir=staging)
        assert tx.staging_dir == staging


class TestFileOperations:
    """Test individual file operations"""

    def test_add_file_write(self, tmp_path):
        """Should add file write operation"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        target = tmp_path / "test.txt"
        content = "Hello World"

        result = tx.add_write(target, content)

        assert result.is_ok()
        assert len(tx.operations) == 1
        assert tx.operations[0].operation_type == OperationType.WRITE
        assert tx.operations[0].target_path == target

    def test_add_file_edit(self, tmp_path):
        """Should add file edit operation"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        target = tmp_path / "test.txt"

        # Create original file
        target.write_text("Original content")

        result = tx.add_edit(target, "Original", "Modified")

        assert result.is_ok()
        assert len(tx.operations) == 1
        assert tx.operations[0].operation_type == OperationType.EDIT

    def test_add_file_delete(self, tmp_path):
        """Should add file delete operation"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        target = tmp_path / "test.txt"

        # Create file to delete
        target.write_text("To be deleted")

        result = tx.add_delete(target)

        assert result.is_ok()
        assert len(tx.operations) == 1
        assert tx.operations[0].operation_type == OperationType.DELETE

    def test_add_multiple_operations(self, tmp_path):
        """Should add multiple operations"""
        tx = AtomicTransaction(staging_dir=tmp_path)

        tx.add_write(tmp_path / "file1.txt", "Content 1")
        tx.add_write(tmp_path / "file2.txt", "Content 2")
        tx.add_write(tmp_path / "file3.txt", "Content 3")

        assert len(tx.operations) == 3


class TestTransactionStaging:
    """Test transaction staging"""

    def test_stage_write_operation(self, tmp_path):
        """Should stage write operation"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        target = tmp_path / "test.txt"

        tx.add_write(target, "Test content")
        result = tx.stage()

        assert result.is_ok()
        # Staged file should exist in staging directory
        staged_files = list(tx.staging_dir.glob("*"))
        assert len(staged_files) > 0

    def test_stage_edit_operation(self, tmp_path):
        """Should stage edit operation with backup"""
        target = tmp_path / "test.txt"
        target.write_text("Original content")

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_edit(target, "Original", "Modified")

        result = tx.stage()

        assert result.is_ok()
        # Original file should be backed up
        assert any("backup" in str(f) for f in tx.staging_dir.glob("*"))

    def test_stage_delete_operation(self, tmp_path):
        """Should stage delete operation with backup"""
        target = tmp_path / "test.txt"
        target.write_text("To be deleted")

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_delete(target)

        result = tx.stage()

        assert result.is_ok()
        # Original should be backed up before delete
        backups = list(tx.staging_dir.glob("*backup*"))
        assert len(backups) > 0

    def test_stage_empty_transaction(self, tmp_path):
        """Should handle empty transaction"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        result = tx.stage()

        # Should succeed but do nothing
        assert result.is_ok()


class TestTransactionCommit:
    """Test transaction commit"""

    def test_commit_write_operations(self, tmp_path):
        """Should commit write operations"""
        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        target1 = tmp_path / "file1.txt"
        target2 = tmp_path / "file2.txt"

        tx.add_write(target1, "Content 1")
        tx.add_write(target2, "Content 2")

        # Stage and commit
        tx.stage()
        result = tx.commit()

        assert result.is_ok()
        assert target1.read_text() == "Content 1"
        assert target2.read_text() == "Content 2"
        assert tx.status == TransactionStatus.COMMITTED

    def test_commit_edit_operations(self, tmp_path):
        """Should commit edit operations"""
        target = tmp_path / "test.txt"
        target.write_text("Original content")

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_edit(target, "Original", "Modified")

        tx.stage()
        result = tx.commit()

        assert result.is_ok()
        assert "Modified" in target.read_text()
        assert tx.status == TransactionStatus.COMMITTED

    def test_commit_delete_operations(self, tmp_path):
        """Should commit delete operations"""
        target = tmp_path / "test.txt"
        target.write_text("To be deleted")

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_delete(target)

        tx.stage()
        result = tx.commit()

        assert result.is_ok()
        assert not target.exists()
        assert tx.status == TransactionStatus.COMMITTED

    def test_commit_without_staging(self, tmp_path):
        """Should fail to commit without staging"""
        tx = AtomicTransaction(staging_dir=tmp_path)
        tx.add_write(tmp_path / "test.txt", "Content")

        result = tx.commit()

        assert result.is_err()
        assert tx.status == TransactionStatus.PENDING

    def test_commit_partial_failure_rollback(self, tmp_path):
        """Should rollback on partial failure"""
        tx = AtomicTransaction(staging_dir=tmp_path / "staging")

        # Add operations - one will fail
        tx.add_write(tmp_path / "file1.txt", "Content 1")
        tx.add_write(Path("/invalid/path/file2.txt"), "Content 2")  # Will fail

        tx.stage()
        result = tx.commit()

        # Should fail and rollback
        assert result.is_err()
        assert tx.status == TransactionStatus.ROLLED_BACK
        # First file should not exist (rolled back)
        assert not (tmp_path / "file1.txt").exists()


class TestTransactionRollback:
    """Test transaction rollback"""

    def test_rollback_after_staging(self, tmp_path):
        """Should rollback staged operations"""
        target = tmp_path / "test.txt"

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_write(target, "New content")

        tx.stage()
        result = tx.rollback()

        assert result.is_ok()
        assert tx.status == TransactionStatus.ROLLED_BACK
        # File should not exist (was never committed)
        assert not target.exists()

    def test_rollback_after_edit(self, tmp_path):
        """Should restore original file after edit rollback"""
        target = tmp_path / "test.txt"
        original_content = "Original content"
        target.write_text(original_content)

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_edit(target, "Original", "Modified")

        tx.stage()
        tx.rollback()

        # Original should be restored
        assert target.read_text() == original_content

    def test_rollback_after_delete(self, tmp_path):
        """Should restore deleted file"""
        target = tmp_path / "test.txt"
        original_content = "To be deleted"
        target.write_text(original_content)

        tx = AtomicTransaction(staging_dir=tmp_path / "staging")
        tx.add_delete(target)

        tx.stage()
        tx.rollback()

        # File should still exist
        assert target.exists()
        assert target.read_text() == original_content


class TestTransactionContextManager:
    """Test context manager usage"""

    def test_context_manager_success(self, tmp_path):
        """Should commit on successful context exit"""
        target = tmp_path / "test.txt"

        with AtomicTransaction(staging_dir=tmp_path / "staging") as tx:
            tx.add_write(target, "Content")
            tx.stage()

        # Should be committed
        assert tx.status == TransactionStatus.COMMITTED
        assert target.read_text() == "Content"

    def test_context_manager_exception_rollback(self, tmp_path):
        """Should rollback on exception"""
        target = tmp_path / "test.txt"

        try:
            with AtomicTransaction(staging_dir=tmp_path / "staging") as tx:
                tx.add_write(target, "Content")
                tx.stage()
                raise ValueError("Simulated error")
        except ValueError:
            pass

        # Should be rolled back
        assert tx.status == TransactionStatus.ROLLED_BACK
        assert not target.exists()


class TestAtomicOperationsHelpers:
    """Test helper functions"""

    def test_atomic_write_helper(self, tmp_path):
        """Should perform atomic write"""
        from tools.atomic_ops import atomic_write

        target = tmp_path / "test.txt"
        result = atomic_write(target, "Test content")

        assert result.is_ok()
        assert target.read_text() == "Test content"

    def test_atomic_multi_write_helper(self, tmp_path):
        """Should perform atomic multi-file write"""
        from tools.atomic_ops import atomic_multi_write

        files = {
            tmp_path / "file1.txt": "Content 1",
            tmp_path / "file2.txt": "Content 2",
            tmp_path / "file3.txt": "Content 3",
        }

        result = atomic_multi_write(files)

        assert result.is_ok()
        for path, content in files.items():
            assert path.read_text() == content

    def test_atomic_multi_write_rollback_on_failure(self, tmp_path):
        """Should rollback all writes on any failure"""
        from tools.atomic_ops import atomic_multi_write

        files = {
            tmp_path / "file1.txt": "Content 1",
            Path("/invalid/path/file2.txt"): "Content 2",  # Will fail
        }

        result = atomic_multi_write(files)

        assert result.is_err()
        # First file should not exist (rolled back)
        assert not (tmp_path / "file1.txt").exists()
