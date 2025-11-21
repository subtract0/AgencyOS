"""
Night Shift Scheduler - Mission 5 Autonomous 24/7 Operation

Orchestrates scheduled execution of primeX orchestrator during off-hours,
enabling continuous autonomous development without human intervention.

TDD Protocol (Article VI):
- Tests written FIRST in tests/test_night_shift_scheduler.py (13 tests)
- This implementation makes tests pass (GREEN phase)

Usage:
    # Start Night Shift scheduler
    python tools/night_shift_scheduler.py start

    # Stop Night Shift scheduler
    python tools/night_shift_scheduler.py stop

    # Check status
    python tools/night_shift_scheduler.py status

    # Run one cycle (for testing)
    python tools/night_shift_scheduler.py run-once
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to path for imports
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# from croniter import croniter
from shared.models.night_shift import NightShiftConfig, NightShiftState
from shared.type_definitions.result import Err, Ok, Result
from tools.backlog_agent import BacklogStorage
from shared.models.backlog import Task, TaskPriority, TaskStatus, TaskType
from tools.health_monitor import HealthMonitor
from tools.primex_orchestrator import PrimeXOrchestrator
from tools.auto_recovery import AutoRecovery
from tools.task_validator import TaskValidator
from tools.night_shift_watchdog import NightShiftWatchdog
from agency_memory.learning import CmpStore, CmpEvent
import uuid

logger = logging.getLogger(__name__)
_MAX_CRON_LOOKAHEAD_MINUTES = 60 * 24 * 366  # look ahead up to one year


class NightShiftScheduler:
    """
    Night Shift Scheduler - Autonomous 24/7 Operation (Mission 5).

    Orchestrates scheduled execution of primeX orchestrator, enabling:
    - Scheduled execution at configurable intervals (cron syntax)
    - Rate limiting to prevent system overload
    - Graceful shutdown and resume capabilities
    - Health monitoring and resource checks
    - Comprehensive logging

    Methods:
    - run(): Main execution loop
    - run_cycle(): Execute one cycle
    - get_next_execution_time(): Calculate next run time
    - check_kill_switch(): Check for manual shutdown request
    - save_state(): Persist state for resume
    """

    def __init__(
        self,
        config: Optional[NightShiftConfig] = None,
        state_dir: Optional[str] = None,
    ):
        """
        Initialize Night Shift scheduler.

        Args:
            config: Configuration (default: load from file or defaults)
            state_dir: Directory for state and logs (default: ~/.agency)
        """
        if config is None:
            config = NightShiftConfig()

        if state_dir is None:
            state_dir = str(Path.home() / ".agency")

        self.config = config
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / "state" / "night_shift_state.json"
        self.log_dir = self.state_dir / "logs" / "night_shift"
        self.kill_switch_file = self.state_dir / "STOP_NIGHT_SHIFT"

        # Create directories
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "state").mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load or create state
        self.state = self.load_state()

        # Shutdown flag (set by signal handlers)
        self.shutdown_requested = False

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)

        # Initialize components
        self.backlog_storage = BacklogStorage(data_dir=str(self.state_dir / "memories" / "agency_backlog"))
        self.orchestrator = PrimeXOrchestrator(backlog_storage=self.backlog_storage)
        self.health_monitor = HealthMonitor(state_dir=str(self.state_dir))
        self.auto_recovery = AutoRecovery(state_dir=str(self.state_dir))
        self.cmp_store = CmpStore()
        self.auto_seed_enabled = True  # Allow tests to disable auto-seeding
        self.task_validator = TaskValidator()
        self.validation_confidence_threshold = 0.9
        self.watchdog = NightShiftWatchdog(timeout_minutes=self.config.max_task_duration_minutes)

        # Setup logging
        self._setup_logging()

        # Hot reload: track modification times of critical files
        self.watched_files: Dict[Path, float] = self._init_file_tracking()

    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        # Primary log handler (~/.agency/logs/night_shift/)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

        # Mirror log handler (workspace logs/night_shift/)
        workspace_log_dir = Path.cwd() / "logs" / "night_shift"
        workspace_log_dir.mkdir(parents=True, exist_ok=True)
        workspace_log_file = workspace_log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

        workspace_handler = logging.FileHandler(workspace_log_file)
        workspace_handler.setLevel(logging.INFO)
        workspace_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(workspace_handler)

    def _init_file_tracking(self) -> Dict[Path, float]:
        """
        Initialize file tracking for hot reload.

        Returns:
            Dict mapping file paths to their modification times
        """
        watched_files = [
            Path(__file__),  # This file (night_shift_scheduler.py)
            Path(__file__).parent / "primex_orchestrator.py",
            Path(__file__).parent / "backlog_agent.py",
            Path(__file__).parent / "auto_recovery.py",
            Path(__file__).parent / "health_monitor.py",
        ]

        file_mtimes = {}
        for file_path in watched_files:
            if file_path.exists():
                file_mtimes[file_path] = file_path.stat().st_mtime
            else:
                logger.warning(f"Watched file not found: {file_path}")

        logger.info(f"Hot reload enabled, watching {len(file_mtimes)} files")
        return file_mtimes

    def _check_for_code_changes(self) -> bool:
        """
        Check if any watched files have changed since startup.

        Returns:
            True if code changed and restart is needed, False otherwise
        """
        for file_path, original_mtime in self.watched_files.items():
            if not file_path.exists():
                logger.warning(f"Watched file disappeared: {file_path}")
                continue

            current_mtime = file_path.stat().st_mtime
            if current_mtime > original_mtime:
                logger.info(f"Code change detected: {file_path} (mtime: {original_mtime} -> {current_mtime})")
                logger.info("Initiating hot reload (auto-restart)...")
                return True

        return False

    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals (SIGTERM, SIGINT)."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True

    def load_state(self) -> NightShiftState:
        """Load state from file or create new state."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state_data = json.load(f)
                    return NightShiftState(**state_data)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, creating new state")
        baseline = datetime.now() - timedelta(minutes=self.config.min_interval_minutes)
        return NightShiftState(last_execution_time=baseline)

    def save_state(self):
        """Save current state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state.model_dump(), f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_next_execution_time(self) -> datetime:
        """
        Calculate next execution time respecting cron-like schedule and min interval.
        """
        now = datetime.now().replace(second=0, microsecond=0)
        scheduled_time = self._compute_next_run_from_schedule(start_from=self.state.last_execution_time)
        if scheduled_time < now:
            scheduled_time = now
        interval_time = self.state.last_execution_time + timedelta(
            minutes=self.config.min_interval_minutes
        )
        return max(scheduled_time, interval_time)

    def _compute_next_run_from_schedule(self, start_from: Optional[datetime] = None) -> datetime:
        """Compute next run time that matches the configured cron expression."""
        schedule = (self.config.schedule or "* * * * *").strip()
        if start_from is None:
            start = datetime.now()
        else:
            start = start_from
        start = start.replace(second=0, microsecond=0)
        fields = schedule.split()
        if len(fields) != 5:
            logger.warning("Invalid schedule '%s', falling back to min interval", schedule)
            return start + timedelta(minutes=self.config.min_interval_minutes)

        minute_field, hour_field, dom_field, month_field, dow_field = fields

        for offset in range(1, _MAX_CRON_LOOKAHEAD_MINUTES):
            candidate = start + timedelta(minutes=offset)
            if self._schedule_matches_datetime(
                candidate, minute_field, hour_field, dom_field, month_field, dow_field
            ):
                return candidate

        # Fallback if no match found in reasonable window
        logger.warning(
            "Failed to find schedule match for '%s', defaulting to min interval window",
            schedule,
        )
        return start + timedelta(minutes=self.config.min_interval_minutes)

    @staticmethod
    def _cron_weekday(dt: datetime) -> int:
        """Convert datetime.weekday() (Mon=0) to cron format (Sun=0)."""
        return (dt.weekday() + 1) % 7

    def _schedule_matches_datetime(
        self,
        dt: datetime,
        minute_field: str,
        hour_field: str,
        dom_field: str,
        month_field: str,
        dow_field: str,
    ) -> bool:
        """Check if datetime matches cron-like fields."""
        minute_match = self._match_cron_field(dt.minute, minute_field, 0, 59)
        hour_match = self._match_cron_field(dt.hour, hour_field, 0, 23)
        month_match = self._match_cron_field(dt.month, month_field, 1, 12)

        day_match_dom = self._match_cron_field(dt.day, dom_field, 1, 31)
        day_match_dow = self._match_cron_field(self._cron_weekday(dt), dow_field, 0, 6)

        if dom_field != "*" and dow_field != "*":
            day_match = day_match_dom or day_match_dow
        else:
            day_match = day_match_dom and day_match_dow

        return minute_match and hour_match and month_match and day_match

    def _match_cron_field(self, value: int, token: str, minimum: int, maximum: int) -> bool:
        """Evaluate a cron field token against a specific value."""
        token = token.strip()
        if token == "*":
            return True

        parts = [part.strip() for part in token.split(",") if part.strip()]
        if not parts:
            return False

        for part in parts:
            if part == "*":
                return True
            if part.startswith("*/"):
                try:
                    step = int(part[2:])
                except ValueError:
                    continue
                if step > 0 and (value - minimum) % step == 0:
                    return True
                continue
            if "-" in part:
                try:
                    start_str, end_str = part.split("-", 1)
                    start = int(start_str)
                    end = int(end_str)
                except ValueError:
                    continue
                if start <= value <= end:
                    return True
                continue
            try:
                exact = int(part)
            except ValueError:
                continue

            if minimum <= exact <= maximum:
                if exact == value:
                    return True
                # Cron allows Sunday to be 0 or 7
                if maximum == 6 and exact == 7 and value == 0:
                    return True

        return False

    def check_kill_switch(self) -> bool:
        """
        Check if kill switch file exists.

        Returns:
            bool: True if kill switch active, False otherwise
        """
        return self.kill_switch_file.exists()

    def should_execute_now(self) -> bool:
        """
        Check if we should execute now based on schedule and min interval.

        Returns:
            bool: True if should execute, False otherwise
        """
        next_run = self.get_next_execution_time()
        now = datetime.now()
        if now >= next_run:
            return True

        logger.info(
            "Skipping execution (next run scheduled for %s, now=%s)",
            next_run,
            now,
        )
        return False

    def run_cycle(self):
        """
        Execute one cycle of Night Shift operations.

        Steps:
        1. Health check
        2. Select tasks from backlog (up to max_tasks_per_execution)
        3. Execute tasks (or log if dry_run)
        4. Update state
        """
        logger.info("Starting Night Shift cycle")

        # Reset cycle counter
        self.state.tasks_completed_this_cycle = 0

        try:
            # Health check
            health = self.health_monitor.check_health()
            self.state.health_status = health

            if not health.get("healthy", False):
                logger.warning(f"Health check failed: {health}, aborting cycle")
                return

            # Get tasks from backlog
            tasks_result = self.backlog_storage.list_tasks()
            if tasks_result.is_err():
                logger.error(f"Failed to list tasks: {tasks_result.unwrap_err()}")
                return

            all_tasks = tasks_result.unwrap()
            pending_tasks = [t for t in all_tasks if t.status.value == "pending"]

            # If no pending tasks, auto-seed discovery/audit work so Night Shift never idles
            if not pending_tasks and self.auto_seed_enabled:
                self._seed_backlog_if_empty(existing_tasks=all_tasks)
                # Reload tasks after seeding
                tasks_result = self.backlog_storage.list_tasks()
                if tasks_result.is_err():
                    logger.error(f"Failed to list tasks after seeding: {tasks_result.unwrap_err()}")
                    return
                all_tasks = tasks_result.unwrap()
                pending_tasks = [t for t in all_tasks if t.status.value == "pending"]

            # Limit to max_tasks_per_execution
            tasks_to_execute = pending_tasks[: self.config.max_tasks_per_execution]

            logger.info(f"Found {len(pending_tasks)} pending tasks, executing {len(tasks_to_execute)}")

            # Execute tasks
            for task in tasks_to_execute:
                if self.shutdown_requested or self.check_kill_switch():
                    logger.info("Shutdown requested, stopping task execution")
                    break

                if self.config.dry_run:
                    logger.info(f"[DRY RUN] Would execute task: {task.id} - {task.title}")
                    continue

                # Pre-flight validation (skip if already completed)
                if self._auto_complete_task_if_applicable(task):
                    continue

                logger.info(f"Executing task: {task.id} - {task.title}")
                with self.watchdog.monitor(task.id):
                    result = self._execute_task(task)

                if result.get("success", False):
                    self.state.tasks_completed_this_cycle += 1
                    self.state.total_tasks_completed += 1
                    logger.info(f"Task completed successfully: {task.id}")
                else:
                    self.state.total_failures += 1
                    logger.error(f"Task failed: {task.id}, error: {result.get('error', 'unknown')}")

            logger.info(f"Cycle complete: {self.state.tasks_completed_this_cycle} tasks completed")
        finally:
            self.state.last_execution_time = datetime.now()
            self.save_state()

    def _auto_complete_task_if_applicable(self, task: Task) -> bool:
        """
        Run pre-flight validation; auto-complete task if validator is confident it's already done.
        """
        if not hasattr(self, "task_validator"):
            return False

        validation = self.task_validator.validate(task)
        if validation.get("already_completed") and validation.get("confidence", 0.0) >= self.validation_confidence_threshold:
            return self._complete_task_without_execution(task, validation)
        return False

    def _complete_task_without_execution(self, task: Task, validation: Dict[str, Any]) -> bool:
        """Mark task as completed without execution and record CMP event."""
        try:
            logger.info(f"Auto-completing task {task.id} ({task.title}) - {validation.get('reason')}")
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now()
            metadata = task.metadata or {}
            metadata["auto_complete_reason"] = validation.get("reason", "")
            metadata["auto_complete_confidence"] = validation.get("confidence", 0.0)
            metadata["auto_complete_evidence"] = validation.get("evidence", "")
            task.metadata = metadata

            update_result = self.backlog_storage.update_task(task)
            if update_result.is_err():
                logger.error(f"Failed to auto-complete task {task.id}: {update_result.unwrap_err()}")
                return False

            self.state.tasks_completed_this_cycle += 1
            self.state.total_tasks_completed += 1
            self._record_cmp_event(
                task,
                {
                    "auto_completed": True,
                    "reason": validation.get("reason", ""),
                    "confidence": validation.get("confidence", 0.0),
                    "evidence": validation.get("evidence", ""),
                },
                success=True,
            )
            return True
        except Exception as e:
            logger.error(f"Auto-complete failed for task {task.id}: {e}", exc_info=True)
            return False

    def _seed_backlog_if_empty(self, existing_tasks: list[Task]) -> None:
        """
        Seed the backlog with discovery/audit tasks when empty.

        This prevents idle cycles and bootstraps new work by asking the system
        to audit the codebase and propose concrete backlog items.
        """
        # method body ...
        try:
            existing_titles = {t.title for t in existing_tasks}
            seeds = [
                {
                    "title": "Auto-seed: Audit codebase for new backlog items",
                    "description": (
                        "Run an agentic audit of the repository to propose specific tasks "
                        "(bugs, tech debt, test gaps). Produce concrete backlog entries "
                        "with file paths and expected outcomes."
                    ),
                    "task_type": TaskType.TECH_DEBT,
                    "priority": TaskPriority.P1,
                    "estimated_complexity": 3,
                    "business_value": 8,
                },
                {
                    "title": "Auto-seed: Generate backlog from recent logs/issues",
                    "description": (
                        "Ingest local logs and recent task history to surface actionable items. "
                        "Create backlog entries that reference the evidence found."
                    ),
                    "task_type": TaskType.TECH_DEBT,
                    "priority": TaskPriority.P2,
                    "estimated_complexity": 2,
                    "business_value": 6,
                },
            ]

            for seed in seeds:
                if seed["title"] in existing_titles:
                    continue
                task = Task(
                    id=str(uuid.uuid4()),
                    title=seed["title"],
                    description=seed["description"],
                    task_type=seed["task_type"],
                    priority=seed["priority"],
                    estimated_complexity=seed["estimated_complexity"],
                    business_value=seed["business_value"],
                    metadata={"auto_seeded": True},
                )
                add_result = self.backlog_storage.add_task(task)
                if add_result.is_ok():
                    logger.info(f"Auto-seeded backlog task: {task.title}")
                else:
                    logger.error(f"Failed to auto-seed task {task.title}: {add_result.unwrap_err()}")
        except Exception as e:
            logger.error(f"Failed to seed backlog: {e}", exc_info=True)

    def _execute_task(self, task) -> dict[str, Any]:
        """
        Execute a single task using primeX orchestrator with AutoRecovery and CMP tracking.

        Args:
            task: Task to execute

        Returns:
            dict: Execution result
        """
        snapshot = None
        start_time = datetime.now()

        try:
            # Set current task
            self.state.current_task_id = task.id
            self.save_state()

            # Phase 1: Create snapshot before execution (AutoRecovery)
            logger.info(f"Creating snapshot for task {task.id}")
            snapshot = self.auto_recovery.create_snapshot(task.id)
            logger.info(f"Snapshot created: {snapshot}")
            if hasattr(self, "watchdog"):
                self.watchdog.heartbeat()

            # Phase 2: Execute via primeX orchestrator
            # Note: Task status is updated to IN_PROGRESS inside execute_task()
            # Execute THE SPECIFIC TASK (not auto-select)
            result = self.orchestrator.execute_task(task)
            if hasattr(self, "watchdog"):
                self.watchdog.heartbeat()

            # Phase 3: Handle result
            if result.is_ok():
                execution_result = result.unwrap()

                # Record CMP event (success)
                self._record_cmp_event(task, execution_result, success=True)

                # Return success flag for run_cycle() to count completions
                return {"success": True, **execution_result}
            else:
                error = result.unwrap_err()
                logger.error(f"Task execution failed: {error}")

                # Record CMP event (failure)
                self._record_cmp_event(task, {"error": str(error)}, success=False)

                # Phase 4: Auto-recovery on failure
                if snapshot:
                    logger.info("Attempting auto-recovery...")
                    self.state.total_escalations += 1
                    # Note: For now we just log the failure and move on
                    # Future: Implement retry logic and rollback

                return {"success": False, "error": str(error)}

        except Exception as e:
            logger.error(f"Task execution failed with exception: {e}", exc_info=True)

            # Record CMP event (exception)
            self._record_cmp_event(task, {"error": str(e), "exception": True}, success=False)

            # Escalate on exception
            if snapshot:
                self.state.total_escalations += 1

            return {"success": False, "error": str(e)}

        finally:
            # Clear current task
            self.state.current_task_id = None
            self.save_state()

    def _record_cmp_event(self, task, execution_result: dict[str, Any], success: bool):
        """
        Record CMP (Clade Metaproductivity) event for learning.

        Args:
            task: Task that was executed
            execution_result: Execution result dictionary
            success: Whether the task succeeded
        """
        try:
            # Generate clade ID
            # Format: agent::model::task_type::strategy
            clade_id = f"night_shift::primex::{task.task_type.value}::auto"

            # Create CmpEvent instance (required by CmpStore.record_event)
            event = CmpEvent(
                id=str(uuid.uuid4()),
                pr_id=-1,  # Placeholder (Night Shift doesn't create PRs yet)
                branch_name="nightshift-auto",
                agent_id="night_shift",
                clade_id=clade_id,
                task_type=f"night_shift_{task.task_type.value}",
                created_at=int(datetime.now().timestamp()),
                closed_at=int(datetime.now().timestamp()),
                reinforcement_signal="approved" if success else "rejected",
                reverted=False,
                size_loc_delta=0,  # Unknown until PR created
                files_touched=execution_result.get("files_changed", []),  # Now captured from PrimeCCCAgent
                test_status="pass" if execution_result.get("tests_passed", False) else "fail",
                test_suites=["night_shift"],
                human_review_time_sec=None,
                extra_metadata={
                    "task_id": task.id,
                    "task_title": task.title,
                    "task_priority": task.priority.value,
                    "task_complexity": task.estimated_complexity,
                    "task_business_value": task.business_value,
                    "pr_url": execution_result.get("pr_url"),
                    "commit_sha": execution_result.get("commit_sha"),  # Now logged!
                    "error": execution_result.get("error") if not success else None,
                },
            )

            # Record event to CmpStore
            self.cmp_store.record_event(event)

            logger.info(f"CMP event recorded: {event.id} - {clade_id} - {'success' if success else 'failure'}")

        except Exception as e:
            logger.warning(f"Failed to record CMP event: {e}", exc_info=True)

    def run(self):
        """
        Main execution loop.

        Runs continuously until shutdown requested or kill switch activated.
        """
        logger.info("Night Shift scheduler starting")
        logger.info(f"Schedule: {self.config.schedule}")
        logger.info(f"Max tasks per execution: {self.config.max_tasks_per_execution}")
        logger.info(f"Dry run: {self.config.dry_run}")

        while not self.shutdown_requested:
            # Check kill switch
            if self.check_kill_switch():
                logger.info("Kill switch detected, shutting down")
                break

            # Hot reload: check for code changes and restart if needed
            if self._check_for_code_changes():
                logger.info("Restarting Night Shift with updated code...")
                self.save_state()  # Save state before restart
                os.execv(sys.executable, [sys.executable] + sys.argv)

            # Check if should execute now
            if self.should_execute_now():
                try:
                    self.run_cycle()
                except Exception as e:
                    logger.error(f"Cycle execution failed: {e}", exc_info=True)
                    self.state.total_failures += 1
                    self.save_state()

            # Sleep for 1 minute before next check
            time.sleep(60)

        logger.info("Night Shift scheduler stopped")
        self.save_state()


def main():
    """CLI entry point for Night Shift scheduler."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Night Shift Scheduler - Autonomous 24/7 Operation"
    )
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "run-once"],
        help="Action to perform",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        help="Cron schedule (default: '0 */4 * * *')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (log intent without execution)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create config
    config = NightShiftConfig(
        schedule=args.schedule if args.schedule else "0 */4 * * *",
        dry_run=args.dry_run,
    )

    # Create scheduler
    scheduler = NightShiftScheduler(config=config)

    # Execute action
    if args.action == "start":
        scheduler.run()
    elif args.action == "stop":
        # Create kill switch file
        kill_switch = Path.home() / ".agency" / "STOP_NIGHT_SHIFT"
        kill_switch.touch()
        print("Kill switch activated. Scheduler will stop on next check.")
    elif args.action == "status":
        state = scheduler.load_state()
        print(f"Last execution: {state.last_execution_time}")
        print(f"Total tasks completed: {state.total_tasks_completed}")
        print(f"Total failures: {state.total_failures}")
        print(f"Total escalations: {state.total_escalations}")
        print(f"Health status: {state.health_status}")
    elif args.action == "run-once":
        scheduler.run_cycle()
        print("Cycle complete.")

    sys.exit(0)


if __name__ == "__main__":
    main()
