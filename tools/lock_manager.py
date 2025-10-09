"""
File-based lock manager for multi-agent coordination.

Constitutional compliance:
- Article I: Complete context before action (atomic lock operations)
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling
- Constitutional Law #5: Result pattern for all functions that can fail
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from shared.models.lock_metadata import LockError, LockHandle, LockMetadata
from shared.type_definitions.result import Err, Ok, Result
from tools.heartbeat_thread import HeartbeatThread


class LockManager:
    """
    File-based lock manager with enhanced metadata and heartbeat support.

    Provides atomic lock acquisition, metadata storage, and stale lock detection
    for coordinating multiple agent instances on a single machine.
    """

    def __init__(self, lock_dir: Path | None = None):
        """
        Initialize LockManager.

        Args:
            lock_dir: Optional custom lock directory (defaults to ~/.agency/memories/.locks)
        """
        if lock_dir is None:
            self.lock_dir = Path.home() / ".agency" / "memories" / ".locks"
        else:
            self.lock_dir = Path(lock_dir)

        # Ensure lock directory exists with correct permissions
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.lock_dir.chmod(0o700)  # Owner read/write/execute only

    def acquire_lock(
        self,
        task_id: str,
        session_id: str,
        metadata: LockMetadata,
    ) -> Result[LockHandle, LockError]:
        """
        Atomically acquire lock with metadata.

        Algorithm:
        1. Check if lock file exists
        2. If exists, verify not stale (heartbeat <5 min old)
        3. If stale, remove and continue
        4. If active, return Err(AlreadyLocked)
        5. Create lock file with O_EXCL (atomic)
        6. Write 6-line metadata
        7. Return Ok(LockHandle)

        Args:
            task_id: Task identifier (e.g., "priority_1_test")
            session_id: Session acquiring the lock
            metadata: LockMetadata with all required fields

        Returns:
            Ok(LockHandle) if acquired successfully
            Err(LockError) if already locked or filesystem error
        """
        lock_file = self.lock_dir / f"{task_id}.lock"

        # Check for existing lock
        if lock_file.exists():
            stale_check = self._check_and_remove_stale_lock(lock_file)
            if stale_check.is_err():
                return Err(stale_check.unwrap_err())  # Type-safe error extraction

        # Create lock file and start heartbeat
        return self._create_lock_file(lock_file, task_id, session_id, metadata)

    def release_lock(
        self,
        task_id: str,
        session_id: str,
    ) -> Result[bool, LockError]:
        """
        Release lock and stop heartbeat thread.

        Args:
            task_id: Task to release
            session_id: Session that owns the lock

        Returns:
            Ok(True) if released successfully
            Err(LockError.NotOwned) if session doesn't own lock
            Err(LockError.NotFound) if lock doesn't exist
        """
        lock_file = self.lock_dir / f"{task_id}.lock"

        # Check if lock exists
        if not lock_file.exists():
            return Err(LockError.not_found(task_id))

        # Verify ownership
        try:
            with lock_file.open("r") as f:
                holder = f.readline().strip()

            if holder != session_id:
                return Err(LockError.not_owned(task_id, session_id))

            # Remove lock file
            lock_file.unlink()
            return Ok(True)

        except Exception as e:
            return Err(LockError.io_error(str(e), task_id=task_id))

    def list_active_locks(self) -> Result[list[LockMetadata], LockError]:
        """
        List all active locks with metadata.

        Returns:
            Ok(list[LockMetadata]) with all current locks
            Err(LockError.IOError) if can't read lock directory
        """
        try:
            if not self.lock_dir.exists():
                return Ok([])

            locks = []
            for lock_file in sorted(self.lock_dir.glob("*.lock")):
                metadata_result = self._read_lock_metadata(lock_file)
                if metadata_result.is_ok():
                    locks.append(metadata_result.unwrap())

            return Ok(locks)

        except Exception as e:
            return Err(LockError.io_error(f"Failed to list locks: {e}"))

    def check_stale_locks(self, timeout_minutes: int = 5) -> Result[list[str], LockError]:
        """
        Find and remove locks with stale heartbeats.

        Args:
            timeout_minutes: Heartbeat timeout threshold (default 5 minutes)

        Returns:
            Ok(list[task_id]) of cleaned up stale locks
            Err(LockError.IOError) if filesystem error
        """
        try:
            if not self.lock_dir.exists():
                return Ok([])

            stale_locks = []
            cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)

            for lock_file in self.lock_dir.glob("*.lock"):
                try:
                    with lock_file.open("r") as f:
                        lines = f.readlines()

                    # Parse heartbeat (line 3, index 2)
                    if len(lines) >= 3:
                        heartbeat = datetime.fromisoformat(lines[2].strip())

                        # Check if stale
                        if heartbeat < cutoff_time:
                            task_id = lock_file.stem
                            lock_file.unlink()
                            stale_locks.append(task_id)

                except Exception:
                    # Skip malformed lock files
                    continue

            return Ok(stale_locks)

        except Exception as e:
            return Err(LockError.io_error(f"Stale lock check failed: {e}"))

    def _create_lock_file(
        self,
        lock_file: Path,
        task_id: str,
        session_id: str,
        metadata: LockMetadata,
    ) -> Result[LockHandle, LockError]:
        """
        Create lock file atomically with metadata and heartbeat.

        Args:
            lock_file: Path to lock file
            task_id: Task identifier
            session_id: Session acquiring lock
            metadata: Lock metadata

        Returns:
            Ok(LockHandle) if created successfully
            Err(LockError) if file exists or IO error
        """
        try:
            # Use 'x' mode = exclusive create (fails if exists)
            with lock_file.open("x") as f:
                # Write 6-line metadata format
                f.write(f"{session_id}\n")
                f.write(f"{metadata.timestamp.isoformat()}\n")
                f.write(f"{metadata.heartbeat.isoformat()}\n")
                f.write(f"{metadata.terminal}\n")
                f.write(f"{metadata.user}\n")
                f.write(f"{metadata.task_description}\n")

            # Set permissions to 0600 (owner read/write only)
            lock_file.chmod(0o600)

            # Start heartbeat thread
            heartbeat_thread = HeartbeatThread(
                lock_file=lock_file,
                session_id=session_id,
                update_interval=60,  # Update every 60 seconds
            )
            heartbeat_thread.start()

            return Ok(
                LockHandle(
                    task_id=task_id,
                    session_id=session_id,
                    lock_file_path=str(lock_file),
                    heartbeat_thread_id=heartbeat_thread.name,
                )
            )

        except FileExistsError:
            # Race condition: another agent created lock between check and create
            return Err(
                LockError(
                    error_type="AlreadyLocked",
                    message="Race condition: lock created by another agent",
                    task_id=task_id,
                )
            )
        except Exception as e:
            return Err(LockError.io_error(str(e), task_id=task_id))

    def _check_and_remove_stale_lock(self, lock_file: Path) -> Result[bool, LockError]:
        """
        Check if lock is stale and remove if so.

        Args:
            lock_file: Path to lock file

        Returns:
            Ok(True) if stale lock removed
            Err(LockError.AlreadyLocked) if lock is active
        """
        try:
            with lock_file.open("r") as f:
                lines = f.readlines()

            if len(lines) < 3:
                # Malformed lock file, remove it
                lock_file.unlink()
                return Ok(True)

            session_id = lines[0].strip()
            heartbeat = datetime.fromisoformat(lines[2].strip())

            # Check if stale (>5 minutes)
            if (datetime.now() - heartbeat).total_seconds() > 300:
                lock_file.unlink()
                return Ok(True)
            else:
                # Active lock
                return Err(LockError.already_locked(lock_file.stem, session_id))

        except Exception as e:
            # If can't read, assume it's corrupted and remove
            lock_file.unlink()
            return Ok(True)

    def _read_lock_metadata(self, lock_file: Path) -> Result[LockMetadata, LockError]:
        """
        Read and parse lock metadata from file.

        Args:
            lock_file: Path to lock file

        Returns:
            Ok(LockMetadata) if parsed successfully
            Err(LockError) if malformed or read error
        """
        try:
            with lock_file.open("r") as f:
                lines = [line.strip() for line in f.readlines()]

            if len(lines) < 6:
                return Err(
                    LockError.io_error(f"Malformed lock file (expected 6 lines, got {len(lines)})")
                )

            return Ok(
                LockMetadata(
                    session_id=lines[0],
                    timestamp=datetime.fromisoformat(lines[1]),
                    heartbeat=datetime.fromisoformat(lines[2]),
                    terminal=lines[3],
                    user=lines[4],
                    task_description=lines[5],
                )
            )

        except Exception as e:
            return Err(LockError.io_error(f"Failed to read lock metadata: {e}"))
