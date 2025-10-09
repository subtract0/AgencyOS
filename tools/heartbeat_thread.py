"""
Heartbeat thread for lock freshness monitoring.

Constitutional compliance:
- Article I: Complete context before action (verify ownership before updates)
- ADR-008: Strict typing
- Constitutional Law #8: Focused functions under 50 lines
"""

import threading
import time
from datetime import datetime
from pathlib import Path


class HeartbeatThread(threading.Thread):
    """
    Background thread to update lock heartbeat every N seconds.

    Exits gracefully when:
    - Lock file is removed (lock released)
    - Lock ownership changes (another agent took over)
    - stop() method is called
    """

    def __init__(
        self,
        lock_file: Path,
        session_id: str,
        update_interval: int = 60,
    ):
        """
        Initialize HeartbeatThread.

        Args:
            lock_file: Path to lock file to update
            session_id: Session that owns the lock (for ownership verification)
            update_interval: Seconds between heartbeat updates (default 60)
        """
        super().__init__(
            daemon=True,  # Don't block process exit
            name=f"Heartbeat-{lock_file.stem}",
        )

        self.lock_file = Path(lock_file)
        self.session_id = session_id
        self.update_interval = update_interval
        self._stop_event = threading.Event()

    def run(self):
        """
        Update heartbeat timestamp every update_interval seconds.

        Exits when:
        - Lock file removed
        - Ownership changed
        - Stop event set

        Uses fine-grained 1-second checks for fast exit detection.
        """
        while not self._stop_event.is_set():
            # CRITICAL FIX: Check stop event every 1 second instead of full interval
            # This allows fast exit when lock released or file deleted
            for _ in range(self.update_interval):
                if self._stop_event.wait(timeout=1.0):  # Check every 1 second
                    return  # Exit immediately if stop requested

            # Check if lock still exists (fast detection)
            if not self.lock_file.exists():
                return  # Lock released, exit thread

            # Update heartbeat with retry logic
            update_success = self._update_heartbeat_with_retry()
            if not update_success:
                return  # Ownership lost or unrecoverable error

    def stop(self):
        """Signal thread to stop gracefully."""
        self._stop_event.set()

    def _update_heartbeat(self) -> bool:
        """
        Update heartbeat timestamp (line 3) in lock file.

        DEPRECATED: Use _update_heartbeat_with_retry() instead.

        Returns:
            True if updated successfully, False if ownership lost or error
        """
        try:
            # Read current lock file
            with self.lock_file.open("r") as f:
                lines = f.readlines()

            # Verify ownership (line 1)
            if len(lines) < 6:
                return False  # Malformed lock file

            holder = lines[0].strip()
            if holder != self.session_id:
                return False  # Ownership changed, exit thread

            # Update heartbeat (line 3, index 2)
            lines[2] = f"{datetime.now().isoformat()}\n"

            # Write updated lock file
            with self.lock_file.open("w") as f:
                f.writelines(lines)

            return True

        except Exception:
            # Transient filesystem error, log warning but don't exit
            # (Could be temporary file system issue)
            return True  # Continue running

    def _update_heartbeat_with_retry(self, max_retries: int = 3) -> bool:
        """
        Update heartbeat with exponential backoff retry for temporary IO errors.

        Args:
            max_retries: Maximum retry attempts (default 3)

        Returns:
            True if updated successfully
            False if ownership lost or unrecoverable error after retries
        """
        for attempt in range(max_retries):
            try:
                # Read current lock file
                with self.lock_file.open("r") as f:
                    lines = f.readlines()

                # Verify ownership (line 1)
                if len(lines) < 6:
                    return False  # Malformed lock file

                holder = lines[0].strip()
                if holder != self.session_id:
                    return False  # Ownership changed, exit thread

                # Update heartbeat (line 3, index 2)
                lines[2] = f"{datetime.now().isoformat()}\n"

                # Write updated lock file
                with self.lock_file.open("w") as f:
                    f.writelines(lines)

                return True  # Success

            except (OSError, PermissionError):
                # Temporary filesystem error, retry with backoff
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff: 1s, 2s, 4s
                    continue
                else:
                    # Unrecoverable after 3 attempts, exit thread
                    return False

            except Exception:
                # Unexpected error, exit thread immediately
                return False

        return False
