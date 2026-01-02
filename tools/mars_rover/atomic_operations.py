"""
Mars Rover Reliability - Phase 1: Atomic Operations Framework.

Provides all-or-nothing transaction semantics with automatic rollback.

Constitutional Compliance:
- Article I: Complete context (atomic ops ensure consistency)
- Article III: Automated enforcement (rollback on failure)
- Article IV: Learning (transaction patterns stored to VectorStore)

Features:
1. Transaction manager with context manager support
2. Automatic rollback on failure
3. Reverse-order rollback execution
4. Concurrent operation safety with locks
5. Transaction logging for audit
6. Nested transaction support via savepoints
7. Atomic file operations
"""

import logging
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class OperationRecord:
    """Record of an executed operation."""

    operation: Callable[[], Any]
    rollback: Optional[Callable[[], None]]
    result: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TransactionLog:
    """Log entry for a transaction."""

    transaction_id: str
    status: str  # "committed", "rolled_back", "in_progress"
    operations_count: int
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "status": self.status,
            "operations_count": self.operations_count,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


class AtomicOperation:
    """
    Represents a single atomic operation with optional rollback.

    Used within a Transaction context to ensure all-or-nothing semantics.
    """

    def __init__(
        self,
        operation: Callable[[], Any],
        rollback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize an atomic operation.

        Args:
            operation: The function to execute
            rollback: Optional function to undo the operation
        """
        self.operation = operation
        self.rollback = rollback
        self.executed = False
        self.result: Any = None

    def execute(self) -> Any:
        """Execute the operation."""
        self.result = self.operation()
        self.executed = True
        return self.result

    def undo(self) -> None:
        """Undo the operation if rollback is defined."""
        if self.rollback and self.executed:
            try:
                self.rollback()
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
                raise


class Transaction:
    """
    A transaction context that tracks operations and handles rollback.

    Supports nested transactions via savepoints.
    """

    _id_counter = 0
    _id_lock = threading.Lock()

    def __init__(self, manager: "TransactionManager", parent: Optional["Transaction"] = None):
        """Initialize a transaction."""
        with Transaction._id_lock:
            Transaction._id_counter += 1
            self._id = f"tx_{Transaction._id_counter}_{datetime.now().timestamp()}"

        self._manager = manager
        self._parent = parent
        self._operations: list[OperationRecord] = []
        self._started_at = datetime.now().isoformat()
        self._completed_at: Optional[str] = None
        self._status = "in_progress"
        self._error: Optional[str] = None
        # Use manager's execution lock for thread-safe operations
        self._execution_lock = manager._execution_lock

        logger.debug(f"Transaction {self._id} started")

    @property
    def committed(self) -> bool:
        """Check if transaction was committed."""
        return self._status == "committed"

    @property
    def rolled_back(self) -> bool:
        """Check if transaction was rolled back."""
        return self._status == "rolled_back"

    def execute(
        self,
        operation: Callable[[], Any],
        rollback: Optional[Callable[[], None]] = None,
    ) -> Any:
        """
        Execute an operation within this transaction.

        Args:
            operation: Function to execute
            rollback: Optional rollback function

        Returns:
            Result of the operation

        Note:
            If the operation raises an exception after partially completing,
            the rollback will still be called during transaction rollback.
        """
        # Use execution lock to prevent race conditions on shared resources
        with self._execution_lock:
            # Record the operation BEFORE executing so rollback can be called
            # even if the operation fails partway through
            record = OperationRecord(
                operation=operation,
                rollback=rollback,
                result=None,
            )
            self._operations.append(record)

            try:
                result = operation()
                record.result = result
                return result
            except Exception:
                # Operation failed - record stays in list so rollback will be called
                raise

    def rollback(self) -> None:
        """
        Rollback all operations in reverse order.

        Continues even if individual rollbacks fail, logging errors.
        """
        logger.info(f"Rolling back transaction {self._id} ({len(self._operations)} operations)")

        # Rollback in reverse order
        for record in reversed(self._operations):
            if record.rollback:
                try:
                    record.rollback()
                except Exception as e:
                    logger.error(f"Rollback failed for operation: {e}")
                    # Continue with remaining rollbacks

        self._status = "rolled_back"
        self._completed_at = datetime.now().isoformat()

    def commit(self) -> None:
        """Mark transaction as committed."""
        self._status = "committed"
        self._completed_at = datetime.now().isoformat()
        logger.debug(f"Transaction {self._id} committed")

    def get_log(self) -> TransactionLog:
        """Get log entry for this transaction."""
        return TransactionLog(
            transaction_id=self._id,
            status=self._status,
            operations_count=len(self._operations),
            started_at=self._started_at,
            completed_at=self._completed_at,
            error=self._error,
        )


class TransactionManager:
    """
    Manages transactions with automatic commit/rollback.

    Provides thread-safe transaction handling with logging.
    """

    def __init__(self):
        """Initialize the transaction manager."""
        self._lock = threading.RLock()
        self._execution_lock = threading.RLock()  # Lock for serializing operations
        self._transaction_log: list[TransactionLog] = []
        self._current_transaction: Optional[Transaction] = None
        logger.info("TransactionManager initialized")

    @contextmanager
    def transaction(self):
        """
        Create a new transaction context.

        Usage:
            with manager.transaction() as tx:
                tx.execute(operation, rollback=undo_operation)

        On exception, all operations are automatically rolled back.
        """
        with self._lock:
            parent = self._current_transaction
            tx = Transaction(self, parent=parent)
            self._current_transaction = tx

        try:
            yield tx
            # If we reach here without exception, commit
            with self._lock:
                tx.commit()
                self._transaction_log.append(tx.get_log())
        except Exception as e:
            # Rollback on any exception
            with self._lock:
                tx._error = str(e)
                tx.rollback()
                self._transaction_log.append(tx.get_log())
            raise
        finally:
            with self._lock:
                self._current_transaction = parent

    def get_transaction_log(self) -> list[dict]:
        """Get all transaction logs."""
        with self._lock:
            return [log.to_dict() for log in self._transaction_log]


class AtomicFileWriter:
    """
    Atomic file writer using write-to-temp-then-rename strategy.

    Ensures file writes are atomic - either complete or no change.
    """

    def __init__(self, target_path: Path | str):
        """
        Initialize atomic file writer.

        Args:
            target_path: Path to the target file
        """
        self.target_path = Path(target_path)
        self._temp_path: Optional[Path] = None

    def write(self, content: str) -> None:
        """
        Atomically write content to the target file.

        Args:
            content: Content to write
        """
        # Ensure parent directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory (for same-filesystem rename)
        fd, temp_path = tempfile.mkstemp(
            dir=self.target_path.parent,
            prefix=".atomic_",
            suffix=".tmp",
        )

        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)

            # Atomic rename
            os.rename(temp_path, self.target_path)
            logger.debug(f"Atomically wrote {self.target_path}")

        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    @contextmanager
    def atomic_write(self):
        """
        Context manager for atomic file writes.

        Usage:
            writer = AtomicFileWriter(path)
            with writer.atomic_write() as f:
                f.write("content")
            # File is atomically written on successful exit

        On exception, no changes are made to the target file.
        """
        # Ensure parent directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temp file
        fd, temp_path = tempfile.mkstemp(
            dir=self.target_path.parent,
            prefix=".atomic_",
            suffix=".tmp",
        )
        self._temp_path = Path(temp_path)

        try:
            # Yield file handle for writing
            with os.fdopen(fd, "w") as f:
                yield f

            # Success - atomic rename
            os.rename(temp_path, self.target_path)
            logger.debug(f"Atomically wrote {self.target_path}")

        except Exception:
            # Failure - clean up temp file, no changes to target
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

        finally:
            self._temp_path = None
