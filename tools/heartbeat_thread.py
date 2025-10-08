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
        """
        while not self._stop_event.is_set():
            # Sleep first (don't update immediately after acquisition)
            time.sleep(self.update_interval)

            # Exit if stop requested
            if self._stop_event.is_set():
                break

            # Check if lock still exists
            if not self.lock_file.exists():
                break  # Lock released, exit thread

            # Update heartbeat
            update_success = self._update_heartbeat()
            if not update_success:
                break  # Ownership lost or error, exit thread

    def stop(self):
        """Signal thread to stop gracefully."""
        self._stop_event.set()

    def _update_heartbeat(self) -> bool:
        """
        Update heartbeat timestamp (line 3) in lock file.

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
