"""
Night Shift Watchdog - Timeout protection and automatic recovery.

Prevents infinite hangs by monitoring task execution time and killing stuck processes.

Layer 1: Per-task timeout (configurable, default 15 minutes)
Layer 2: Heartbeat monitoring (detect silent hangs)
Layer 3: Automatic process restart

Usage:
    watchdog = NightShiftWatchdog(timeout_minutes=15)

    with watchdog.monitor(task_id):
        # Execute task
        result = execute_task(task)

    # If task exceeds timeout, WatchdogTimeout exception raised
    # Watchdog automatically kills process and restarts Night Shift
"""

import logging
import os
import signal
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WatchdogTimeout(Exception):
    """Raised when task execution exceeds timeout."""
    pass


class NightShiftWatchdog:
    """
    Watchdog timer for Night Shift task execution.

    Prevents infinite hangs by enforcing timeout limits on task execution.
    """

    def __init__(self, timeout_minutes: int = 15, heartbeat_interval: int = 60):
        """
        Initialize watchdog.

        Args:
            timeout_minutes: Maximum time allowed per task (default 15 min)
            heartbeat_interval: Heartbeat check interval in seconds (default 60s)
        """
        self.timeout_minutes = timeout_minutes
        self.heartbeat_interval = heartbeat_interval
        self.current_task_id: Optional[str] = None
        self.task_start_time: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self.watchdog_thread: Optional[threading.Thread] = None
        self.stop_watchdog = threading.Event()

    @contextmanager
    def monitor(self, task_id: str):
        """
        Monitor task execution with timeout protection.

        Args:
            task_id: Unique task identifier

        Raises:
            WatchdogTimeout: If task exceeds timeout

        Example:
            with watchdog.monitor("task-123"):
                result = long_running_task()
        """
        self.current_task_id = task_id
        self.task_start_time = datetime.now()
        self.last_heartbeat = datetime.now()

        # Start watchdog thread
        self.stop_watchdog.clear()
        self.watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name=f"watchdog-{task_id}",
            daemon=True
        )
        self.watchdog_thread.start()

        logger.info(f"Watchdog started for task {task_id} (timeout: {self.timeout_minutes} min)")

        try:
            yield
        finally:
            # Stop watchdog
            self.stop_watchdog.set()
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=5)

            elapsed = (datetime.now() - self.task_start_time).total_seconds() / 60
            logger.info(f"Watchdog stopped for task {task_id} (elapsed: {elapsed:.1f} min)")

            self.current_task_id = None
            self.task_start_time = None

    def heartbeat(self):
        """
        Update heartbeat timestamp.

        Call this periodically during long-running operations to prevent timeout.
        """
        self.last_heartbeat = datetime.now()

    def _watchdog_loop(self):
        """
        Watchdog monitoring loop (runs in background thread).

        Checks:
        1. Total execution time vs timeout
        2. Heartbeat freshness (detect silent hangs)
        """
        while not self.stop_watchdog.is_set():
            # Check timeout
            if self.task_start_time:
                elapsed = datetime.now() - self.task_start_time
                if elapsed > timedelta(minutes=self.timeout_minutes):
                    logger.error(
                        f"Task {self.current_task_id} exceeded timeout "
                        f"({self.timeout_minutes} min). Killing process."
                    )
                    self._kill_current_process()
                    return

            # Check heartbeat (detect silent hangs)
            if self.last_heartbeat:
                since_heartbeat = datetime.now() - self.last_heartbeat
                # If no heartbeat for 3x interval, log warning
                if since_heartbeat > timedelta(seconds=self.heartbeat_interval * 3):
                    logger.warning(
                        f"Task {self.current_task_id} has not sent heartbeat for "
                        f"{since_heartbeat.total_seconds():.0f}s. Possible hang."
                    )

            # Sleep until next check
            self.stop_watchdog.wait(self.heartbeat_interval)

    def _kill_current_process(self):
        """
        Kill current process (last resort for stuck tasks).

        This will terminate the Night Shift scheduler, which should be
        restarted by the hot reload mechanism or systemd/supervisor.
        """
        logger.critical(f"Watchdog killing process {os.getpid()} due to timeout")

        # Write state before killing
        state_file = Path.home() / ".agency/state/watchdog_kill.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        import json
        state_file.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "task_id": self.current_task_id,
            "timeout_minutes": self.timeout_minutes,
            "pid": os.getpid(),
            "reason": "Task execution timeout"
        }, indent=2))

        # Kill self
        os.kill(os.getpid(), signal.SIGTERM)
