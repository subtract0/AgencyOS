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
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# Add project root to path for imports
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from croniter import croniter
from shared.models.night_shift import NightShiftConfig, NightShiftState
from shared.type_definitions.result import Err, Ok, Result
from tools.backlog_agent import BacklogStorage
from shared.models.backlog import Task, TaskPriority, TaskStatus, TaskType
from tools.health_monitor import HealthMonitor
from tools.primex_orchestrator import PrimeXOrchestrator
from tools.auto_recovery import AutoRecovery
from agency_memory.learning import CmpStore, CmpEvent
import uuid

logger = logging.getLogger(__name__)


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
        self.backlog_storage = BacklogStorage()
        self.orchestrator = PrimeXOrchestrator(backlog_storage=self.backlog_storage)
        self.health_monitor = HealthMonitor(state_dir=str(self.state_dir))
        self.auto_recovery = AutoRecovery(state_dir=str(self.state_dir))
        self.cmp_store = CmpStore()
        self.auto_seed_enabled = True  # Allow tests to disable auto-seeding

        # Setup logging
        self._setup_logging()

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
                return NightShiftState()
        else:
            return NightShiftState()

    def save_state(self):
        """Save current state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state.model_dump(), f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_next_execution_time(self) -> datetime:
        """
        Calculate next execution time based on cron schedule.

        Returns:
            datetime: Next execution time
        """
        cron = croniter(self.config.schedule, datetime.now())
        return cron.get_next(datetime)

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
        # Check min interval since last execution
        time_since_last = datetime.now() - self.state.last_execution_time
        min_interval = timedelta(minutes=self.config.min_interval_minutes)

        if time_since_last < min_interval:
            logger.info(f"Skipping execution (min interval not met): {time_since_last} < {min_interval}")
            return False

        # Check cron schedule
        next_run = self.get_next_execution_time()
        now = datetime.now()

        # If next run is within next minute, execute now
        if (next_run - now).total_seconds() < 60:
            return True

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
            else:
                logger.info(f"Executing task: {task.id} - {task.title}")
                result = self._execute_task(task)

                if result.get("success", False):
                    self.state.tasks_completed_this_cycle += 1
                    self.state.total_tasks_completed += 1
                    logger.info(f"Task completed successfully: {task.id}")
                else:
                    self.state.total_failures += 1
                    logger.error(f"Task failed: {task.id}, error: {result.get('error', 'unknown')}")

        # Update state
        self.state.last_execution_time = datetime.now()
        self.save_state()

        logger.info(f"Cycle complete: {self.state.tasks_completed_this_cycle} tasks completed")

    def _seed_backlog_if_empty(self, existing_tasks: list[Task]) -> None:
        """
        Seed the backlog with discovery/audit tasks when empty.

        This prevents idle cycles and bootstraps new work by asking the system
        to audit the codebase and propose concrete backlog items.
        """
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

            # Phase 2: Execute via primeX orchestrator
            # Note: Task status is updated to IN_PROGRESS inside execute_task()
            # Execute THE SPECIFIC TASK (not auto-select)
            result = self.orchestrator.execute_task(task)

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
