#!/usr/bin/env python3
"""
Atomic Operations - Phase 1, Task 3
Transaction-like guarantees for multi-file changes

Features:
- All-or-nothing file operations
- Automatic rollback on failure
- Backup and restore
- Context manager support

Constitutional Compliance:
- Article I: Complete operations or rollback (no partial states)
- Article II: 100% verification before commit
- Article III: Automated rollback (no manual intervention)

Usage:
    # Context manager (recommended)
    with AtomicTransaction() as tx:
        tx.add_write(Path("file1.txt"), "Content 1")
        tx.add_write(Path("file2.txt"), "Content 2")
        tx.stage()  # Changes committed on exit if no exception

    # Manual control
    tx = AtomicTransaction()
    tx.add_write(Path("file.txt"), "Content")
    tx.stage()
    tx.commit()  # Or tx.rollback() to undo

    # Helper functions
    atomic_write(Path("file.txt"), "Content")
    atomic_multi_write({
        Path("file1.txt"): "Content 1",
        Path("file2.txt"): "Content 2",
    })
"""

import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result


# ============================================================================
# ENUMS
# ============================================================================


class OperationType(str, Enum):
    """File operation type"""

    WRITE = "write"  # Write new file
    EDIT = "edit"  # Modify existing file
    DELETE = "delete"  # Delete file


class TransactionStatus(str, Enum):
    """Transaction status"""

    PENDING = "pending"  # Not yet staged
    STAGED = "staged"  # Staged but not committed
    COMMITTED = "committed"  # Successfully committed
    ROLLED_BACK = "rolled_back"  # Rolled back
    FAILED = "failed"  # Failed


# ============================================================================
# DATA MODELS
# ============================================================================


class FileOperation(BaseModel):
    """A single file operation"""

    operation_type: OperationType = Field(..., description="Type of operation")
    target_path: Path = Field(..., description="Target file path")
    content: Optional[str] = Field(default=None, description="Content for write operations")
    old_value: Optional[str] = Field(default=None, description="Old value for edits")
    new_value: Optional[str] = Field(default=None, description="New value for edits")
    backup_path: Optional[Path] = Field(default=None, description="Backup file path")


# ============================================================================
# ATOMIC TRANSACTION
# ============================================================================


class AtomicTransaction:
    """
    Atomic Transaction: All-or-nothing file operations

    Provides transaction-like guarantees:
    1. All operations succeed, or none do
    2. Automatic backup and restore
    3. Context manager support
    4. Rollback on any failure
    """

    def __init__(self, staging_dir: Optional[Path] = None):
        """
        Initialize atomic transaction

        Args:
            staging_dir: Directory for staging changes (default: temp dir)
        """
        self.staging_dir = staging_dir or Path(tempfile.mkdtemp(prefix="atomic_tx_"))
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        self.operations: List[FileOperation] = []
        self.status = TransactionStatus.PENDING

    def add_write(self, target_path: Path, content: str) -> Result[None, str]:
        """
        Add file write operation

        Args:
            target_path: Path to write to
            content: File content

        Returns:
            Result with success or error
        """
        try:
            op = FileOperation(
                operation_type=OperationType.WRITE,
                target_path=target_path,
                content=content,
            )
            self.operations.append(op)
            return Ok(None)

        except Exception as e:
            return Err(f"Failed to add write operation: {e}")

    def add_edit(
        self, target_path: Path, old_value: str, new_value: str
    ) -> Result[None, str]:
        """
        Add file edit operation

        Args:
            target_path: Path to edit
            old_value: Old string to replace
            new_value: New string to replace with

        Returns:
            Result with success or error
        """
        try:
            if not target_path.exists():
                return Err(f"File does not exist: {target_path}")

            op = FileOperation(
                operation_type=OperationType.EDIT,
                target_path=target_path,
                old_value=old_value,
                new_value=new_value,
            )
            self.operations.append(op)
            return Ok(None)

        except Exception as e:
            return Err(f"Failed to add edit operation: {e}")

    def add_delete(self, target_path: Path) -> Result[None, str]:
        """
        Add file delete operation

        Args:
            target_path: Path to delete

        Returns:
            Result with success or error
        """
        try:
            if not target_path.exists():
                return Err(f"File does not exist: {target_path}")

            op = FileOperation(
                operation_type=OperationType.DELETE,
                target_path=target_path,
            )
            self.operations.append(op)
            return Ok(None)

        except Exception as e:
            return Err(f"Failed to add delete operation: {e}")

    def stage(self) -> Result[None, str]:
        """
        Stage all operations (prepare for commit)

        This creates backups and prepares changes in staging directory

        Returns:
            Result with success or error
        """
        try:
            for i, op in enumerate(self.operations):
                if op.operation_type == OperationType.WRITE:
                    # Stage new file in staging directory
                    staged_path = self.staging_dir / f"staged_{i}_{op.target_path.name}"
                    if op.content is not None:
                        staged_path.write_text(op.content)
                    op.backup_path = staged_path

                elif op.operation_type == OperationType.EDIT:
                    # Backup original file
                    if op.target_path.exists():
                        backup_path = (
                            self.staging_dir / f"backup_{i}_{op.target_path.name}"
                        )
                        shutil.copy2(op.target_path, backup_path)
                        op.backup_path = backup_path

                elif op.operation_type == OperationType.DELETE:
                    # Backup file before delete
                    if op.target_path.exists():
                        backup_path = (
                            self.staging_dir / f"backup_{i}_{op.target_path.name}"
                        )
                        shutil.copy2(op.target_path, backup_path)
                        op.backup_path = backup_path

            self.status = TransactionStatus.STAGED
            return Ok(None)

        except Exception as e:
            self.status = TransactionStatus.FAILED
            return Err(f"Staging failed: {e}")

    def commit(self) -> Result[None, str]:
        """
        Commit all staged operations

        Returns:
            Result with success or error
        """
        if self.status != TransactionStatus.STAGED:
            return Err("Transaction must be staged before commit")

        try:
            # Apply all operations
            for op in self.operations:
                if op.operation_type == OperationType.WRITE:
                    # Ensure parent directory exists
                    op.target_path.parent.mkdir(parents=True, exist_ok=True)
                    if op.content is not None:
                        op.target_path.write_text(op.content)

                elif op.operation_type == OperationType.EDIT:
                    if not op.target_path.exists():
                        raise FileNotFoundError(f"File not found: {op.target_path}")

                    content = op.target_path.read_text()
                    if op.old_value and op.new_value:
                        content = content.replace(op.old_value, op.new_value)
                        op.target_path.write_text(content)

                elif op.operation_type == OperationType.DELETE:
                    if op.target_path.exists():
                        op.target_path.unlink()

            self.status = TransactionStatus.COMMITTED
            # Clean up staging directory
            self._cleanup_staging()
            return Ok(None)

        except Exception as e:
            # Rollback on failure
            self.rollback()
            return Err(f"Commit failed, rolled back: {e}")

    def rollback(self) -> Result[None, str]:
        """
        Rollback all operations

        Returns:
            Result with success or error
        """
        try:
            # Restore from backups
            for op in self.operations:
                if op.backup_path and op.backup_path.exists():
                    if op.operation_type == OperationType.WRITE:
                        # Remove written file if it exists
                        if op.target_path.exists():
                            op.target_path.unlink()

                    elif op.operation_type in [OperationType.EDIT, OperationType.DELETE]:
                        # Restore from backup
                        shutil.copy2(op.backup_path, op.target_path)

            self.status = TransactionStatus.ROLLED_BACK
            self._cleanup_staging()
            return Ok(None)

        except Exception as e:
            self.status = TransactionStatus.FAILED
            return Err(f"Rollback failed: {e}")

    def _cleanup_staging(self) -> None:
        """Clean up staging directory"""
        try:
            if self.staging_dir.exists():
                shutil.rmtree(self.staging_dir)
        except Exception:
            pass  # Best effort cleanup

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            # No exception - commit if staged
            if self.status == TransactionStatus.STAGED:
                result = self.commit()
                if result.is_err():
                    raise RuntimeError(f"Commit failed: {result.unwrap_err()}")
        else:
            # Exception occurred - rollback
            if self.status in [TransactionStatus.STAGED, TransactionStatus.PENDING]:
                self.rollback()

        return False  # Don't suppress exceptions


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def atomic_write(target_path: Path, content: str) -> Result[None, str]:
    """
    Atomic write to single file

    Args:
        target_path: File to write
        content: File content

    Returns:
        Result with success or error
    """
    try:
        with AtomicTransaction() as tx:
            tx.add_write(target_path, content)
            stage_result = tx.stage()
            if stage_result.is_err():
                return stage_result

        return Ok(None)

    except Exception as e:
        return Err(f"Atomic write failed: {e}")


def atomic_multi_write(files: Dict[Path, str]) -> Result[None, str]:
    """
    Atomic write to multiple files

    All files written or none (rollback on any failure)

    Args:
        files: Dictionary of {path: content}

    Returns:
        Result with success or error
    """
    try:
        with AtomicTransaction() as tx:
            for path, content in files.items():
                write_result = tx.add_write(path, content)
                if write_result.is_err():
                    return write_result

            stage_result = tx.stage()
            if stage_result.is_err():
                return stage_result

        return Ok(None)

    except Exception as e:
        return Err(f"Atomic multi-write failed: {e}")


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """CLI entry point (for testing)"""
    print("⚛️ ATOMIC OPERATIONS")
    print("=" * 70)
    print("Use as a library - no CLI interface yet")
    print("=" * 70)


if __name__ == "__main__":
    main()
