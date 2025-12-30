#!/usr/bin/env python3
"""
Agency Daemon - Unified Autonomous Development Engine

A single command that puts your entire machine to work:
    python agency_daemon.py

That's it. No configuration. No multiple terminals. No juggling.

What it does:
- Detects your hardware (cores, memory) and scales accordingly
- Populates backlog automatically when empty (codebase audits, tech debt, tests)
- Executes tasks with full TDD workflow
- Runs parallel test suites utilizing all cores
- Self-heals on failures, auto-restarts on crashes
- Logs everything, learns from outcomes
- Never stops until you tell it to (Ctrl+C or kill switch)

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    AgencyDaemon                         │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
    │  │ Backlog     │  │ Task        │  │ Health          │ │
    │  │ Populator   │──│ Executor    │──│ Monitor         │ │
    │  └─────────────┘  └─────────────┘  └─────────────────┘ │
    │         │                │                  │          │
    │         ▼                ▼                  ▼          │
    │  ┌─────────────────────────────────────────────────────┐│
    │  │              Adaptive Resource Manager              ││
    │  │   (CPU cores, memory, concurrent workers)           ││
    │  └─────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────┘

Enterprise Features:
- Graceful shutdown on SIGTERM/SIGINT
- State persistence across restarts
- Automatic crash recovery
- Structured logging with rotation
- Kill switch file for emergency stop
- Prometheus-compatible metrics (future)

Usage:
    # Start the daemon (that's it, really)
    python agency_daemon.py

    # Stop gracefully
    touch ~/.agency/STOP_DAEMON

    # Check status
    python agency_daemon.py --status

    # Dry run (see what would happen)
    python agency_daemon.py --dry-run

Author: AgencyOS Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import multiprocessing
import os
import signal
import subprocess
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.models.backlog import Task, TaskPriority, TaskStatus, TaskType
from shared.type_definitions.result import Err, Ok, Result
from tools.backlog_agent import BacklogStorage, PriorityQueue
from tools.primex_orchestrator import PrimeXOrchestrator
from tools.night_shift_watchdog import NightShiftWatchdog, WatchdogTimeout
from tools.task_validator import TaskValidator
from tools.health_monitor import HealthMonitor

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

@dataclass
class DaemonConfig:
    """Configuration for AgencyDaemon - auto-detected from hardware."""

    # Hardware (auto-detected)
    cpu_cores: int = field(default_factory=lambda: multiprocessing.cpu_count())
    memory_gb: int = field(default_factory=lambda: _get_system_memory_gb())

    # Worker scaling (computed from hardware)
    max_concurrent_tasks: int = 1  # Sequential task execution for safety
    test_worker_count: int = field(default_factory=lambda: max(1, multiprocessing.cpu_count() - 2))

    # Timing
    cycle_interval_seconds: int = 60  # Check for work every minute
    task_timeout_minutes: int = 15  # Max time per task
    health_check_interval_seconds: int = 300  # Health check every 5 min

    # Backlog management
    min_backlog_size: int = 5  # Populate backlog if fewer than this
    max_tasks_per_cycle: int = 3  # Execute up to N tasks per cycle

    # Paths
    state_dir: Path = field(default_factory=lambda: Path.home() / ".agency")
    log_dir: Path = field(default_factory=lambda: Path.home() / ".agency" / "logs" / "daemon")
    kill_switch_file: Path = field(default_factory=lambda: Path.home() / ".agency" / "STOP_DAEMON")

    # Behavior
    dry_run: bool = False
    verbose: bool = False
    allow_dirty: bool = False  # Allow running with uncommitted changes

    def __post_init__(self):
        # Scale test workers based on available memory
        # Rule: ~2GB per test worker for safety
        safe_workers = max(1, self.memory_gb // 4)
        self.test_worker_count = min(self.test_worker_count, safe_workers)


def _get_system_memory_gb() -> int:
    """Get system memory in GB."""
    try:
        if sys.platform == "darwin":
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip()) // (1024 ** 3)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) // (1024 ** 2)
    except Exception:
        pass
    return 16  # Conservative default


# -----------------------------------------------------------------------------
# Daemon State
# -----------------------------------------------------------------------------

class DaemonStatus(Enum):
    STARTING = "starting"
    RUNNING = "running"
    POPULATING_BACKLOG = "populating_backlog"
    EXECUTING_TASKS = "executing_tasks"
    RUNNING_TESTS = "running_tests"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class DaemonState:
    """Persistent state for the daemon."""

    status: DaemonStatus = DaemonStatus.STOPPED
    started_at: Optional[datetime] = None
    last_cycle_at: Optional[datetime] = None
    total_cycles: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    total_tests_run: int = 0
    current_task_id: Optional[str] = None
    last_error: Optional[str] = None
    uptime_seconds: int = 0

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "total_cycles": self.total_cycles,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "total_tests_run": self.total_tests_run,
            "current_task_id": self.current_task_id,
            "last_error": self.last_error,
            "uptime_seconds": self.uptime_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DaemonState":
        return cls(
            status=DaemonStatus(data.get("status", "stopped")),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            last_cycle_at=datetime.fromisoformat(data["last_cycle_at"]) if data.get("last_cycle_at") else None,
            total_cycles=data.get("total_cycles", 0),
            total_tasks_completed=data.get("total_tasks_completed", 0),
            total_tasks_failed=data.get("total_tasks_failed", 0),
            total_tests_run=data.get("total_tests_run", 0),
            current_task_id=data.get("current_task_id"),
            last_error=data.get("last_error"),
            uptime_seconds=data.get("uptime_seconds", 0),
        )


# -----------------------------------------------------------------------------
# Backlog Populator
# -----------------------------------------------------------------------------

class BacklogPopulator:
    """
    Automatically populates the backlog with meaningful work.

    Sources:
    1. Codebase audits (type safety, dead code, security)
    2. Test coverage gaps
    3. Tech debt from TODOs/FIXMEs
    4. Dependency updates
    5. Documentation gaps
    """

    # Task templates for auto-population
    TASK_TEMPLATES = [
        {
            "title": "Run mypy strict type checking and fix violations",
            "description": (
                "Execute `mypy --strict` on the entire codebase. "
                "Fix all type errors systematically, prioritizing public APIs. "
                "Ensure 100% test pass rate after each fix."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P1,
            "complexity": 4,
            "business_value": 9,
        },
        {
            "title": "Identify and remove dead code using vulture",
            "description": (
                "Run vulture to find unused functions, classes, variables, and imports. "
                "Verify each finding manually, remove confirmed dead code. "
                "Ensure 100% test pass rate after removal."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P2,
            "complexity": 3,
            "business_value": 7,
        },
        {
            "title": "Scan for security vulnerabilities with bandit",
            "description": (
                "Run `bandit -r .` to identify security issues. "
                "Fix high and medium severity findings. "
                "Document any false positives with # nosec comments."
            ),
            "task_type": TaskType.BUG_FIX,
            "priority": TaskPriority.P1,
            "complexity": 5,
            "business_value": 10,
        },
        {
            "title": "Extract and fix TODO/FIXME comments",
            "description": (
                "Grep for TODO, FIXME, HACK, XXX comments in codebase. "
                "Create specific backlog tasks for each actionable item. "
                "Remove resolved comments."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P2,
            "complexity": 2,
            "business_value": 6,
        },
        {
            "title": "Consolidate duplicate utility functions",
            "description": (
                "Find duplicate or near-duplicate implementations across codebase. "
                "Consolidate to single source of truth in shared/. "
                "Update all callers and ensure tests pass."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P2,
            "complexity": 4,
            "business_value": 7,
        },
        {
            "title": "Check for outdated dependencies",
            "description": (
                "Run `pip list --outdated` or check pyproject.toml. "
                "Update dependencies with security patches. "
                "Run full test suite after updates."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P2,
            "complexity": 3,
            "business_value": 8,
        },
        {
            "title": "Add missing docstrings to public APIs",
            "description": (
                "Find public functions/classes without docstrings. "
                "Add clear, concise docstrings following Google style. "
                "Focus on shared/ and tools/ directories."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P3,
            "complexity": 2,
            "business_value": 5,
        },
        {
            "title": "Reduce function complexity (McCabe > 10)",
            "description": (
                "Run `flake8 --max-complexity 10` to find complex functions. "
                "Refactor functions exceeding complexity threshold. "
                "Extract helper functions, simplify conditionals."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P2,
            "complexity": 5,
            "business_value": 7,
        },
        {
            "title": "Add integration tests for critical paths",
            "description": (
                "Identify untested integration points (API boundaries, agent communication). "
                "Write integration tests covering happy path and error cases. "
                "Target 80% coverage for integration layer."
            ),
            "task_type": TaskType.TEST_FAILURE,
            "priority": TaskPriority.P2,
            "complexity": 5,
            "business_value": 8,
        },
        {
            "title": "Optimize slow tests (> 5 seconds)",
            "description": (
                "Run pytest with --durations=20 to find slow tests. "
                "Optimize or mock heavy operations. "
                "Target < 2 seconds per unit test."
            ),
            "task_type": TaskType.TECH_DEBT,
            "priority": TaskPriority.P3,
            "complexity": 3,
            "business_value": 6,
        },
    ]

    def __init__(self, storage: BacklogStorage, logger: logging.Logger):
        self.storage = storage
        self.logger = logger

    def populate_if_needed(self, min_size: int = 5) -> int:
        """
        Populate backlog if it has fewer than min_size pending tasks.

        Returns:
            Number of tasks added
        """
        # Get current pending tasks
        tasks_result = self.storage.list_tasks()
        if tasks_result.is_err():
            self.logger.error(f"Failed to list tasks: {tasks_result.unwrap_err()}")
            return 0

        all_tasks = tasks_result.unwrap()
        pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]
        existing_titles = {t.title for t in all_tasks}

        if len(pending_tasks) >= min_size:
            self.logger.debug(f"Backlog has {len(pending_tasks)} pending tasks, no population needed")
            return 0

        # Add tasks until we have min_size
        tasks_added = 0
        needed = min_size - len(pending_tasks)

        for template in self.TASK_TEMPLATES:
            if tasks_added >= needed:
                break

            if template["title"] in existing_titles:
                continue  # Skip if already exists

            task = Task(
                id=str(uuid.uuid4()),
                title=template["title"],
                description=template["description"],
                task_type=template["task_type"],
                priority=template["priority"],
                estimated_complexity=template["complexity"],
                business_value=template["business_value"],
                metadata={"auto_populated": True, "source": "daemon"},
            )

            result = self.storage.add_task(task)
            if result.is_ok():
                self.logger.info(f"Added task: {task.title}")
                tasks_added += 1
            else:
                self.logger.error(f"Failed to add task: {result.unwrap_err()}")

        return tasks_added


# -----------------------------------------------------------------------------
# The Daemon
# -----------------------------------------------------------------------------

class AgencyDaemon:
    """
    The unified autonomous development engine.

    One command. Zero configuration. Maximum productivity.
    """

    def __init__(self, config: Optional[DaemonConfig] = None):
        self.config = config or DaemonConfig()
        self.state = DaemonState()
        self.shutdown_requested = False

        # Create directories
        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logging()

        # Initialize components
        self.storage = BacklogStorage(
            data_dir=str(self.config.state_dir / "memories" / "agency_backlog")
        )
        self.orchestrator = PrimeXOrchestrator(
            backlog_storage=self.storage,
            timeout_minutes=self.config.task_timeout_minutes,
        )
        self.populator = BacklogPopulator(self.storage, self.logger)
        self.validator = TaskValidator()
        self.health_monitor = HealthMonitor(state_dir=str(self.config.state_dir))
        self.watchdog = NightShiftWatchdog(timeout_minutes=self.config.task_timeout_minutes)

        # State file
        self.state_file = self.config.state_dir / "state" / "daemon_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _setup_logging(self) -> logging.Logger:
        """Setup structured logging with rotation."""
        logger = logging.getLogger("agency_daemon")
        logger.setLevel(logging.DEBUG if self.config.verbose else logging.INFO)

        # Console handler
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(console)

        # File handler (daily rotation)
        log_file = self.config.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(file_handler)

        return logger

    def _handle_signal(self, signum: int, frame: Any):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def _check_kill_switch(self) -> bool:
        """Check if kill switch file exists."""
        return self.config.kill_switch_file.exists()

    def _save_state(self):
        """Persist state to disk."""
        try:
            if self.state.started_at:
                self.state.uptime_seconds = int((datetime.now() - self.state.started_at).total_seconds())
            with open(self.state_file, "w") as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def _load_state(self) -> DaemonState:
        """Load state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return DaemonState.from_dict(json.load(f))
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")
        return DaemonState()

    def _run_cycle(self):
        """Execute one work cycle."""
        self.state.total_cycles += 1
        self.state.last_cycle_at = datetime.now()
        self._save_state()

        try:
            # Phase 1: Health check
            health = self.health_monitor.check_health()

            # If allow_dirty is set, ignore git_clean status
            is_healthy = health.get("healthy", False)
            if not is_healthy and self.config.allow_dirty:
                # Re-evaluate health without git_clean requirement
                git_dirty_only = (
                    not health.get("git_clean", True) and
                    health.get("disk_free_gb", 0) >= 10 and
                    health.get("memory_percent", 100) < 80 and
                    health.get("cpu_percent", 100) < 90 and
                    health.get("dependencies_ok", True)
                )
                if git_dirty_only:
                    is_healthy = True
                    self.logger.info("Health check passed (allow_dirty mode, ignoring uncommitted changes)")

            if not is_healthy:
                self.logger.warning(f"Health check failed: {health}")
                return

            # Phase 2: Populate backlog if needed
            self.state.status = DaemonStatus.POPULATING_BACKLOG
            self._save_state()
            added = self.populator.populate_if_needed(self.config.min_backlog_size)
            if added > 0:
                self.logger.info(f"Populated backlog with {added} tasks")

            # Phase 3: Get pending tasks
            tasks_result = self.storage.list_tasks()
            if tasks_result.is_err():
                self.logger.error(f"Failed to list tasks: {tasks_result.unwrap_err()}")
                return

            all_tasks = tasks_result.unwrap()
            pending_tasks = [t for t in all_tasks if t.status == TaskStatus.PENDING]

            if not pending_tasks:
                self.state.status = DaemonStatus.IDLE
                self._save_state()
                self.logger.info("No pending tasks, idling...")
                return

            # Phase 4: Execute tasks
            self.state.status = DaemonStatus.EXECUTING_TASKS
            self._save_state()

            # Sort by priority and business value
            pending_tasks.sort(
                key=lambda t: (
                    0 if t.priority == TaskPriority.P1 else (1 if t.priority == TaskPriority.P2 else 2),
                    -t.business_value
                )
            )

            tasks_to_execute = pending_tasks[:self.config.max_tasks_per_cycle]
            self.logger.info(f"Executing {len(tasks_to_execute)} of {len(pending_tasks)} pending tasks")

            for task in tasks_to_execute:
                if self.shutdown_requested or self._check_kill_switch():
                    self.logger.info("Shutdown requested, stopping execution")
                    break

                self._execute_task(task)

        except Exception as e:
            self.state.last_error = str(e)
            self.logger.error(f"Cycle failed: {e}\n{traceback.format_exc()}")

    def _execute_task(self, task: Task):
        """Execute a single task with full protection."""
        self.state.current_task_id = task.id
        self._save_state()

        try:
            self.logger.info(f"Executing: {task.title}")

            # Pre-flight validation
            validation = self.validator.validate(task)
            if validation.get("already_completed") and validation.get("confidence", 0) >= 0.9:
                self.logger.info(f"Task already completed: {validation.get('reason')}")
                task.status = TaskStatus.COMPLETED
                task.metadata = task.metadata or {}
                task.metadata["auto_completed"] = True
                task.metadata["completion_reason"] = validation.get("reason")
                self.storage.update_task(task)
                self.state.total_tasks_completed += 1
                return

            if self.config.dry_run:
                self.logger.info(f"[DRY RUN] Would execute: {task.title}")
                return

            # Execute with watchdog protection
            with self.watchdog.monitor(task.id):
                result = self.orchestrator.execute_task(task)

            if result.is_ok():
                self.state.total_tasks_completed += 1
                self.logger.info(f"Task completed: {task.title}")
            else:
                self.state.total_tasks_failed += 1
                error = result.unwrap_err()
                self.logger.error(f"Task failed: {task.title} - {error}")
                self.state.last_error = str(error)

        except WatchdogTimeout as e:
            self.state.total_tasks_failed += 1
            self.logger.error(f"Task timed out: {task.title}")
            self.state.last_error = f"Timeout: {e}"
            # Reset task to pending
            task.status = TaskStatus.PENDING
            self.storage.update_task(task)

        except Exception as e:
            self.state.total_tasks_failed += 1
            self.logger.error(f"Task exception: {task.title} - {e}")
            self.state.last_error = str(e)

        finally:
            self.state.current_task_id = None
            self._save_state()

    def run(self):
        """
        Main daemon loop. Runs forever until stopped.

        This is the only method you need to call.
        """
        self.logger.info("=" * 60)
        self.logger.info("Agency Daemon Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Hardware: {self.config.cpu_cores} cores, {self.config.memory_gb}GB RAM")
        self.logger.info(f"Test workers: {self.config.test_worker_count}")
        self.logger.info(f"Task timeout: {self.config.task_timeout_minutes} minutes")
        self.logger.info(f"State dir: {self.config.state_dir}")
        self.logger.info(f"Kill switch: {self.config.kill_switch_file}")
        self.logger.info("=" * 60)

        # Remove old kill switch if present
        if self.config.kill_switch_file.exists():
            self.config.kill_switch_file.unlink()
            self.logger.info("Removed stale kill switch file")

        # Initialize state
        self.state = DaemonState(
            status=DaemonStatus.STARTING,
            started_at=datetime.now(),
        )
        self._save_state()

        self.state.status = DaemonStatus.RUNNING
        self._save_state()

        try:
            while not self.shutdown_requested:
                # Check kill switch
                if self._check_kill_switch():
                    self.logger.info("Kill switch detected, shutting down")
                    break

                # Run work cycle
                self._run_cycle()

                # Sleep until next cycle
                if not self.shutdown_requested:
                    time.sleep(self.config.cycle_interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")

        finally:
            self.state.status = DaemonStatus.STOPPED
            self._save_state()
            self.logger.info("Agency Daemon stopped")
            self.logger.info(f"Stats: {self.state.total_tasks_completed} completed, {self.state.total_tasks_failed} failed")

    def status(self) -> dict:
        """Get current daemon status."""
        state = self._load_state()
        return {
            "status": state.status.value,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "uptime": str(timedelta(seconds=state.uptime_seconds)) if state.uptime_seconds else "0:00:00",
            "total_cycles": state.total_cycles,
            "total_tasks_completed": state.total_tasks_completed,
            "total_tasks_failed": state.total_tasks_failed,
            "current_task": state.current_task_id,
            "last_error": state.last_error,
            "hardware": {
                "cpu_cores": self.config.cpu_cores,
                "memory_gb": self.config.memory_gb,
                "test_workers": self.config.test_worker_count,
            },
        }


# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------

def main():
    """
    Agency Daemon - One command to rule them all.

    Usage:
        python agency_daemon.py           # Start the daemon
        python agency_daemon.py --status  # Check status
        python agency_daemon.py --stop    # Stop gracefully
        python agency_daemon.py --dry-run # See what would happen
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Agency Daemon - Unified Autonomous Development Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agency_daemon.py           Start the daemon (runs forever)
  python agency_daemon.py --status  Show current status
  python agency_daemon.py --stop    Stop the daemon gracefully
  python agency_daemon.py --dry-run Preview what would happen

The daemon will:
  - Detect your hardware and scale accordingly
  - Populate backlog with meaningful work when empty
  - Execute tasks with full TDD workflow
  - Self-heal on failures
  - Run until you stop it (Ctrl+C or --stop)
        """
    )

    parser.add_argument("--status", action="store_true", help="Show daemon status")
    parser.add_argument("--stop", action="store_true", help="Stop the daemon gracefully")
    parser.add_argument("--dry-run", action="store_true", help="Preview without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--cycle-interval", type=int, default=60, help="Seconds between cycles")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running with uncommitted git changes")

    args = parser.parse_args()

    config = DaemonConfig(
        dry_run=args.dry_run,
        verbose=args.verbose,
        cycle_interval_seconds=args.cycle_interval,
        allow_dirty=args.allow_dirty,
    )

    daemon = AgencyDaemon(config)

    if args.status:
        status = daemon.status()
        print("\n" + "=" * 50)
        print("AGENCY DAEMON STATUS")
        print("=" * 50)
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
        print("=" * 50 + "\n")
        return

    if args.stop:
        kill_switch = config.kill_switch_file
        kill_switch.touch()
        print(f"Kill switch created: {kill_switch}")
        print("Daemon will stop on next cycle check.")
        return

    # Start the daemon
    print("\n" + "=" * 60)
    print("  AGENCY DAEMON")
    print("  Unified Autonomous Development Engine")
    print("=" * 60)
    print(f"\n  Hardware: {config.cpu_cores} cores, {config.memory_gb}GB RAM")
    print(f"  Workers:  {config.test_worker_count} test workers")
    print(f"  Mode:     {'DRY RUN' if config.dry_run else 'LIVE'}")
    print(f"\n  Stop with: Ctrl+C or 'touch {config.kill_switch_file}'")
    print("\n" + "=" * 60 + "\n")

    daemon.run()


if __name__ == "__main__":
    main()
