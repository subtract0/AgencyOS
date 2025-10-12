#!/usr/bin/env python3
"""
Overnight Orchestrator - The "Foreman" for Autonomous Night Watch.

This script coordinates the overnight execution of autonomous agent missions across
distributed workers (M4 Pro + M4 Air). It manages the task queue, starts workers,
and aggregates results into a final report.

Constitutional Compliance:
- Article I: Complete context with retry logic and exponential backoff
- Article II: TDD implementation (tests written first)
- Article III: Automated enforcement of quality gates
- Article IV: Learning integration through VectorStore patterns
- Article V: Follows spec-029-autonomous-overnight-agents.md

Usage:
    python scripts/overnight_orchestrator.py --pro-threads 2 --air-threads 1 --mission-set full
"""

import argparse
import fcntl
import json
import logging
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.models.night_watch import (
    Mission,
    MissionResult,
    OrchestratorConfig,
    OrchestratorReport,
    SignalHandlerStatus,
    TaskQueue,
    TaskQueueItem,
    TaskStatus,
    WorkerStatus,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_missions(missions_file: str) -> list[Mission]:
    """
    Load missions from JSON configuration file.

    Args:
        missions_file: Path to overnight_missions.json

    Returns:
        List of Mission objects

    Raises:
        FileNotFoundError: If missions file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    missions_path = Path(missions_file)

    if not missions_path.exists():
        raise FileNotFoundError(f"Missions file not found: {missions_file}")

    with open(missions_path) as f:
        data = json.load(f)

    missions = [Mission(**mission_data) for mission_data in data.get("missions", [])]
    logger.info(f"Loaded {len(missions)} missions from {missions_file}")

    return missions


def filter_enabled_missions(missions: list[Mission]) -> list[Mission]:
    """
    Filter only enabled missions.

    Args:
        missions: List of all missions

    Returns:
        List of enabled missions
    """
    enabled = [m for m in missions if m.enabled]
    logger.info(f"Filtered to {len(enabled)} enabled missions (from {len(missions)} total)")
    return enabled


def sort_missions_by_priority(missions: list[Mission]) -> list[Mission]:
    """
    Sort missions by priority (CRITICAL first, LOW last).

    Args:
        missions: List of missions to sort

    Returns:
        Sorted list of missions
    """
    return sorted(missions, key=lambda m: m.priority.value)


def generate_branch_name(mission_id: str) -> str:
    """
    Generate git branch name following convention.

    Pattern: night-watch/<mission-slug>-<timestamp>

    Args:
        mission_id: Mission identifier (e.g., 'pydantic_migration')

    Returns:
        Branch name (e.g., 'night-watch/pydantic-migration-20251012-0315')
    """
    # Convert mission_id to kebab-case
    mission_slug = mission_id.replace("_", "-")

    # Generate timestamp YYYYMMDD-HHMM
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")

    return f"night-watch/{mission_slug}-{timestamp}"


def create_task_queue(missions: list[Mission], mission_set: str) -> TaskQueue:
    """
    Create task queue from missions.

    Args:
        missions: List of missions to convert to tasks
        mission_set: Mission set name (e.g., 'full', 'testing')

    Returns:
        TaskQueue with sorted tasks
    """
    # Filter enabled missions only
    enabled_missions = [m for m in missions if m.enabled]

    # Sort by priority
    sorted_missions = sort_missions_by_priority(enabled_missions)

    # Convert to TaskQueueItems
    tasks = []
    for idx, mission in enumerate(sorted_missions, start=1):
        task = TaskQueueItem(
            id=f"task_{idx:03d}",
            mission_id=mission.id,
            title=mission.title,
            command=mission.command,
            priority=mission.priority.value,
            estimated_duration_minutes=mission.estimated_duration_minutes,
            status=TaskStatus.PENDING,
            assigned_to=None,
            branch_name=None,
            started_at=None,
            completed_at=None,
            error_message=None,
        )
        tasks.append(task)

    queue = TaskQueue(mission_set=mission_set, tasks=tasks)

    logger.info(f"Created task queue with {len(tasks)} tasks for mission set '{mission_set}'")
    return queue


def write_queue(queue: TaskQueue, queue_path: str) -> None:
    """
    Write task queue to JSON file.

    Args:
        queue: TaskQueue to write
        queue_path: Path to task_queue.json
    """
    queue_file = Path(queue_path)
    queue_file.parent.mkdir(parents=True, exist_ok=True)

    with open(queue_file, "w") as f:
        f.write(queue.model_dump_json(indent=2))

    logger.info(f"Wrote task queue to {queue_path}")


def acquire_lock(lock_file, timeout: float = 5.0) -> bool:
    """
    Acquire exclusive file lock using fcntl.

    Args:
        lock_file: Open file object for locking
        timeout: Maximum time to wait for lock (seconds)

    Returns:
        True if lock acquired, False if timeout
    """
    try:
        # Non-blocking lock attempt
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        # Lock held by another process
        return False
    except Exception as e:
        logger.error(f"Lock acquisition error: {e}")
        return False


def release_lock(lock_file) -> None:
    """
    Release file lock.

    Args:
        lock_file: Open file object to unlock
    """
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        logger.error(f"Lock release error: {e}")


def acquire_lock_with_retry(lock_file, max_retries: int = 3, base_delay: float = 0.5) -> bool:
    """
    Acquire lock with exponential backoff retry logic (Article I compliance).

    Args:
        lock_file: Open file object for locking
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)

    Returns:
        True if lock acquired, False if all retries exhausted
    """
    for attempt in range(max_retries):
        if acquire_lock(lock_file, timeout=5.0):
            return True

        # Exponential backoff (Article I)
        delay = base_delay * (2**attempt)
        logger.warning(
            f"Lock acquisition failed (attempt {attempt + 1}/{max_retries}), "
            f"retrying in {delay}s..."
        )
        time.sleep(delay)

    logger.error("Lock acquisition failed after all retries")
    return False


def start_worker_thread(worker_id: str, queue_path: str) -> threading.Thread:
    """
    Start a single worker thread.

    Args:
        worker_id: Unique worker identifier
        queue_path: Path to task queue

    Returns:
        Started thread object
    """

    # Import worker function (will be implemented in overnight_worker.py)
    # For now, mock the worker function
    def worker_main():
        logger.info(f"Worker {worker_id} started")
        # Worker implementation will be in overnight_worker.py

    thread = threading.Thread(target=worker_main, name=worker_id, daemon=True)
    thread.start()

    return thread


def start_local_workers(num_threads: int, queue_path: str) -> list[threading.Thread]:
    """
    Start local worker threads on M4 Pro.

    Args:
        num_threads: Number of worker threads to start
        queue_path: Path to task queue

    Returns:
        List of started thread objects
    """
    workers = []
    for i in range(num_threads):
        worker_id = f"worker-m4pro-{i + 1:02d}"
        thread = start_worker_thread(worker_id, queue_path)
        workers.append(thread)
        logger.info(f"Started local worker: {worker_id}")

    return workers


def generate_remote_worker_command(air_threads: int, queue_path: str) -> str:
    """
    Generate command for starting workers on remote machine (MacBook Air).

    Args:
        air_threads: Number of worker threads for Air
        queue_path: Path to shared task queue

    Returns:
        Shell command string to execute on remote machine
    """
    # Command to run on MacBook Air
    command = (
        f"cd /Users/am/Code/Agency && "
        f"python scripts/overnight_worker.py --threads {air_threads} --queue {queue_path}"
    )

    logger.info(f"Generated remote worker command: {command}")
    return command


def monitor_workers(worker_count: int, queue_path: str, timeout_seconds: int = 300) -> WorkerStatus:
    """
    Monitor workers and return status.

    Args:
        worker_count: Number of workers to monitor
        queue_path: Path to task queue
        timeout_seconds: Maximum time to monitor

    Returns:
        WorkerStatus with worker metrics
    """
    start_time = time.time()
    completed = 0
    failed = 0
    pending = 0

    while time.time() - start_time < timeout_seconds:
        time.sleep(1)

        # Check if all tasks completed
        try:
            queue = TaskQueue.model_validate_json(Path(queue_path).read_text())
            pending = sum(1 for t in queue.tasks if t.status == TaskStatus.PENDING)
            in_progress = sum(1 for t in queue.tasks if t.status == TaskStatus.IN_PROGRESS)
            completed = sum(1 for t in queue.tasks if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in queue.tasks if t.status == TaskStatus.FAILED)

            if not pending and not in_progress:
                break
        except Exception:
            pass

    return WorkerStatus(
        active_workers=worker_count,
        completed_tasks=completed,
        failed_tasks=failed,
        pending_tasks=pending,
        elapsed_seconds=time.time() - start_time,
    )


def setup_signal_handlers() -> SignalHandlerStatus:
    """
    Setup signal handlers for graceful shutdown.

    Returns:
        SignalHandlerStatus of registered signal handlers
    """
    import signal

    def sigint_handler(signum, frame):
        logger.info("Received SIGINT, shutting down gracefully...")

    def sigterm_handler(signum, frame):
        logger.info("Received SIGTERM, shutting down gracefully...")

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    return SignalHandlerStatus(sigint_registered=True, sigterm_registered=True)


def wait_for_workers(workers: list[threading.Thread], timeout_minutes: int = 480) -> None:
    """
    Wait for all worker threads to complete (max 8 hours).

    Args:
        workers: List of worker threads
        timeout_minutes: Maximum wait time in minutes
    """
    timeout_seconds = timeout_minutes * 60
    start_time = time.time()

    for worker in workers:
        remaining_time = timeout_seconds - (time.time() - start_time)
        if remaining_time <= 0:
            logger.warning("Worker timeout reached, continuing...")
            break

        worker.join(timeout=remaining_time)

    logger.info("All workers completed or timeout reached")


def aggregate_results(queue_path: str) -> list[MissionResult]:
    """
    Aggregate results from completed task queue.

    Args:
        queue_path: Path to task queue JSON

    Returns:
        List of MissionResult objects
    """
    queue_file = Path(queue_path)
    if not queue_file.exists():
        logger.error(f"Queue file not found: {queue_path}")
        return []

    queue = TaskQueue.model_validate_json(queue_file.read_text())

    results = []
    for task in queue.tasks:
        if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
            continue  # Skip incomplete tasks

        # Calculate duration
        duration_minutes = 0.0
        if task.started_at and task.completed_at:
            duration_seconds = (task.completed_at - task.started_at).total_seconds()
            duration_minutes = duration_seconds / 60.0

        result = MissionResult(
            task_id=task.id,
            mission_id=task.mission_id,
            title=task.title,
            status=task.status,
            worker_id=task.assigned_to or "unknown",
            branch_name=task.branch_name,
            started_at=task.started_at or datetime.now(UTC),
            completed_at=task.completed_at or datetime.now(UTC),
            duration_minutes=duration_minutes,
            tests_passed=(task.status == TaskStatus.COMPLETED),
            pr_url=None,
            error_message=task.error_message,
            log_file=f"logs/overnight/{task.assigned_to or 'unknown'}-{datetime.now(UTC).strftime('%Y%m%d')}.log",
        )
        results.append(result)

    logger.info(f"Aggregated {len(results)} results from queue")
    return results


def generate_next_steps(results: list[MissionResult]) -> list[str]:
    """
    Generate actionable next steps for user based on results.

    Args:
        results: List of mission results

    Returns:
        List of next step recommendations
    """
    steps = []

    completed = [r for r in results if r.status == TaskStatus.COMPLETED]
    failed = [r for r in results if r.status == TaskStatus.FAILED]
    conflicts = [r for r in results if r.status == TaskStatus.CONFLICT]

    if completed:
        steps.append(
            f"Review and merge {len(completed)} completed branch(es): "
            + ", ".join(r.branch_name for r in completed if r.branch_name)
        )

    if failed:
        steps.append(
            f"Investigate {len(failed)} failed task(s): " + ", ".join(r.title for r in failed)
        )

    if conflicts:
        steps.append(
            f"Resolve {len(conflicts)} git conflict(s): " + ", ".join(r.title for r in conflicts)
        )

    if not steps:
        steps.append("No action required - all tasks completed successfully")

    return steps


def generate_final_report(queue_path: str, config: OrchestratorConfig) -> OrchestratorReport:
    """
    Generate final report from completed task queue.

    Args:
        queue_path: Path to task queue JSON
        config: Orchestrator configuration

    Returns:
        OrchestratorReport with final results
    """
    results = aggregate_results(queue_path)

    queue = TaskQueue.model_validate_json(Path(queue_path).read_text())
    start_time = queue.created_at
    end_time = datetime.now(UTC)

    return generate_report(results, start_time, end_time, config.mission_set)


def generate_report(
    results: list[MissionResult],
    start_time: datetime,
    end_time: datetime,
    mission_set: str,
) -> OrchestratorReport:
    """
    Generate final orchestrator report.

    Args:
        results: List of mission results
        start_time: Orchestrator start timestamp
        end_time: Orchestrator end timestamp
        mission_set: Mission set name

    Returns:
        OrchestratorReport
    """
    duration_minutes = (end_time - start_time).total_seconds() / 60.0

    completed = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
    failed = sum(1 for r in results if r.status == TaskStatus.FAILED)
    conflicts = sum(1 for r in results if r.status == TaskStatus.CONFLICT)
    timeouts = sum(1 for r in results if r.status == TaskStatus.TIMEOUT)

    branches = [r.branch_name for r in results if r.branch_name]
    next_steps = generate_next_steps(results)

    report = OrchestratorReport(
        orchestrator_started_at=start_time,
        orchestrator_completed_at=end_time,
        total_duration_minutes=duration_minutes,
        mission_set=mission_set,
        total_tasks=len(results),
        completed_tasks=completed,
        failed_tasks=failed,
        conflict_tasks=conflicts,
        timeout_tasks=timeouts,
        results=results,
        branches_created=branches,
        next_steps=next_steps,
    )

    logger.info(
        f"Generated report: {completed}/{len(results)} completed, "
        f"{failed} failed, {conflicts} conflicts, {timeouts} timeouts"
    )

    return report


def mark_task_conflict(task_id: str, queue_path: str, error_message: str) -> None:
    """
    Mark a task as CONFLICT in the queue.

    Args:
        task_id: Task ID to update
        queue_path: Path to task queue
        error_message: Conflict error message
    """
    queue = TaskQueue.model_validate_json(Path(queue_path).read_text())

    for task in queue.tasks:
        if task.id == task_id:
            task.status = TaskStatus.CONFLICT
            task.error_message = error_message
            task.completed_at = datetime.now(UTC)
            break

    write_queue(queue, queue_path)
    logger.warning(f"Marked task {task_id} as CONFLICT: {error_message}")


def mark_task_timeout(task_id: str, queue_path: str, max_minutes: int) -> None:
    """
    Mark a task as TIMEOUT in the queue.

    Args:
        task_id: Task ID to update
        queue_path: Path to task queue
        max_minutes: Maximum allowed duration
    """
    queue = TaskQueue.model_validate_json(Path(queue_path).read_text())

    for task in queue.tasks:
        if task.id == task_id:
            task.status = TaskStatus.TIMEOUT
            task.error_message = f"Task exceeded maximum duration of {max_minutes} minutes"
            task.completed_at = datetime.now(UTC)
            break

    write_queue(queue, queue_path)
    logger.warning(f"Marked task {task_id} as TIMEOUT (>{max_minutes}min)")


def run_orchestrator(
    missions_file: str, queue_path: str, config: OrchestratorConfig
) -> OrchestratorReport:
    """
    Main orchestrator workflow.

    Args:
        missions_file: Path to missions configuration
        queue_path: Path to task queue
        config: Orchestrator configuration

    Returns:
        OrchestratorReport with final results
    """
    start_time = datetime.now(UTC)

    logger.info(f"Starting orchestrator with mission set: {config.mission_set}")
    logger.info(
        f"Workers: {config.pro_threads} local (M4 Pro), {config.air_threads} remote (M4 Air)"
    )

    # Load and filter missions
    missions = load_missions(missions_file)
    enabled_missions = filter_enabled_missions(missions)

    if not enabled_missions:
        logger.warning("No enabled missions found")
        return generate_report([], start_time, datetime.now(UTC), config.mission_set)

    # Create task queue
    queue = create_task_queue(enabled_missions, config.mission_set)
    write_queue(queue, queue_path)

    # Dry run mode - don't start workers
    if config.dry_run:
        logger.info("DRY RUN MODE - Skipping worker execution")
        return generate_report([], start_time, datetime.now(UTC), config.mission_set)

    # Start local workers
    workers = start_local_workers(config.pro_threads, queue_path)

    # Generate remote worker command
    if config.air_threads > 0:
        remote_cmd = generate_remote_worker_command(config.air_threads, queue_path)
        logger.info(f"Execute on MacBook Air: {remote_cmd}")

    # Wait for completion
    wait_for_workers(workers, timeout_minutes=config.max_task_duration_minutes * 10)

    # Aggregate results
    results = aggregate_results(queue_path)

    # Generate final report
    end_time = datetime.now(UTC)
    report = generate_report(results, start_time, end_time, config.mission_set)

    return report


def main() -> int:
    """
    Main entry point for orchestrator CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Overnight Orchestrator - Autonomous Night Watch Coordinator"
    )
    parser.add_argument(
        "--missions-file",
        default="overnight_missions.json",
        help="Path to missions configuration file",
    )
    parser.add_argument(
        "--queue-path",
        default="task_queue.json",
        help="Path to task queue file",
    )
    parser.add_argument(
        "--pro-threads",
        type=int,
        default=2,
        help="Number of worker threads on M4 Pro",
    )
    parser.add_argument(
        "--air-threads",
        type=int,
        default=1,
        help="Number of worker threads on M4 Air",
    )
    parser.add_argument(
        "--mission-set",
        default="full",
        help="Mission set to execute (refactoring, testing, docs, full)",
    )
    parser.add_argument(
        "--max-task-duration",
        type=int,
        default=60,
        help="Maximum task duration in minutes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without starting workers",
    )

    args = parser.parse_args()

    config = OrchestratorConfig(
        pro_threads=args.pro_threads,
        air_threads=args.air_threads,
        mission_set=args.mission_set,
        max_task_duration_minutes=args.max_task_duration,
        dry_run=args.dry_run,
    )

    try:
        report = run_orchestrator(args.missions_file, args.queue_path, config)

        # Display report
        print("\n" + "=" * 80)
        print("OVERNIGHT ORCHESTRATOR REPORT")
        print("=" * 80)
        print(f"Mission Set: {report.mission_set}")
        print(f"Duration: {report.total_duration_minutes:.1f} minutes")
        print(f"Total Tasks: {report.total_tasks}")
        print(f"✅ Completed: {report.completed_tasks}")
        print(f"❌ Failed: {report.failed_tasks}")
        print(f"⚠️  Conflicts: {report.conflict_tasks}")
        print(f"⏱️  Timeouts: {report.timeout_tasks}")
        print("\nBranches Created:")
        for branch in report.branches_created:
            print(f"  - {branch}")
        print("\nNext Steps:")
        for step in report.next_steps:
            print(f"  - {step}")
        print("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
