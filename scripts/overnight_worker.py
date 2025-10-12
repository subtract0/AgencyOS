#!/usr/bin/env python3
"""
Overnight worker for autonomous night watch system (spec-029).

This worker claims tasks from the queue, executes them in isolated git branches,
and reports results back to the orchestrator.

Constitutional compliance:
- Article I: Retry with exponential backoff on lock contention
- Article II: Verify all tests pass before marking success
- Article V: Traceable to spec-029
"""

import fcntl
import json
import logging
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from shared.models.night_watch import TaskQueue, TaskQueueItem, TaskStatus


class SuccessCriteria(BaseModel):
    """Success criteria validation result (spec-029 section 7.6)."""

    exit_code_zero: bool
    tests_pass: bool
    git_clean: bool
    branch_pushed: bool
    all_criteria_met: bool


def acquire_lock(lock_file: str, timeout: float = 5.0) -> Optional[int]:
    """
    Acquire exclusive file lock with timeout.

    Args:
        lock_file: Path to lock file
        timeout: Maximum time to wait for lock (seconds)

    Returns:
        File descriptor if lock acquired, None if timeout
    """
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_WRONLY)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except BlockingIOError:
                time.sleep(0.1)

        # Timeout
        os.close(fd)
        return None
    except Exception as e:
        logging.error(f"Failed to acquire lock: {e}")
        return None


def release_lock(fd: int) -> None:
    """
    Release file lock.

    Args:
        fd: File descriptor to unlock
    """
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    except Exception as e:
        logging.error(f"Failed to release lock: {e}")


def acquire_lock_with_retry(
    lock_file: str, max_retries: int = 3, timeout: float = 5.0
) -> Optional[int]:
    """
    Acquire lock with exponential backoff retry (Article I compliance).

    Args:
        lock_file: Path to lock file
        max_retries: Maximum number of retry attempts
        timeout: Timeout per attempt (seconds)

    Returns:
        File descriptor if successful, None otherwise
    """
    backoff = 0.1  # Initial backoff 100ms

    for attempt in range(max_retries):
        fd = acquire_lock(lock_file, timeout)
        if fd is not None:
            return fd

        if attempt < max_retries - 1:
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff

    return None


def claim_next_task(queue_file: str, worker_id: str) -> Optional[TaskQueueItem]:
    """
    Claim next pending task from queue with file locking.

    Args:
        queue_file: Path to task_queue.json
        worker_id: Unique worker identifier

    Returns:
        Claimed task or None if no tasks available
    """
    lock_file = queue_file + ".lock"
    fd = acquire_lock_with_retry(lock_file, max_retries=3, timeout=5.0)

    if fd is None:
        logging.error("Failed to acquire lock for task queue")
        return None

    try:
        # Read queue
        queue = TaskQueue.model_validate_json(Path(queue_file).read_text())

        # Find next pending task (sorted by priority)
        pending_tasks = [t for t in queue.tasks if t.status == TaskStatus.PENDING]

        if not pending_tasks:
            return None

        # Claim first pending task
        task = pending_tasks[0]
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_to = worker_id
        task.started_at = datetime.now(UTC)

        # Write updated queue
        Path(queue_file).write_text(queue.model_dump_json(indent=2))

        return task

    finally:
        release_lock(fd)


def generate_branch_name(title: str, timestamp: str) -> str:
    """
    Generate git branch name following spec-029 convention.

    Pattern: night-watch/{mission-slug}-{timestamp}
    Example: night-watch/pydantic-migration-20251012-0315

    Args:
        title: Mission title or ID
        timestamp: Timestamp string (YYYYMMDD-HHMM format)

    Returns:
        Branch name string
    """
    # Convert title to slug (lowercase, hyphens)
    mission_slug = title.lower().replace("_", "-").replace(" ", "-")

    return f"night-watch/{mission_slug}-{timestamp}"


def generate_branch_name_from_task(task: TaskQueueItem) -> str:
    """
    Generate git branch name from task object.

    Args:
        task: Task to generate branch name for

    Returns:
        Branch name string
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    return generate_branch_name(task.mission_id, timestamp)


def create_mission_branch(repo_path: str, mission_id: str, timestamp: str) -> str:
    """
    Create and checkout mission branch in repository.

    Args:
        repo_path: Path to git repository
        mission_id: Mission identifier
        timestamp: Timestamp string

    Returns:
        Created branch name

    Raises:
        RuntimeError: If branch creation fails
    """
    branch_name = generate_branch_name(mission_id, timestamp)

    # Check if branch exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if branch_name in result.stdout:
        # Branch exists, append suffix
        suffix = int(time.time() * 1000) % 10000
        branch_name = f"{branch_name}-{suffix}"

    # Create and checkout branch
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create branch: {result.stderr}")

    return branch_name


def create_and_checkout_branch(branch_name: str) -> bool:
    """
    Create and checkout new git branch.

    Args:
        branch_name: Name of branch to create

    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Failed to create branch {branch_name}: {e}")
        return False


def execute_primea_command(command: str, repo_path: str, timeout: int = 3600) -> None:
    """
    Execute /primeA command safely without shell injection.

    Args:
        command: Command to execute
        repo_path: Repository path for working directory
        timeout: Maximum execution time in seconds

    Raises:
        Exception: If command execution fails
    """
    # Parse command into list for safe execution (no shell=True)
    # Expected format: "/primeA 'Task description'"
    cmd_parts = command.split(" ", 1)  # Split on first space only

    result = subprocess.run(
        cmd_parts,
        shell=False,  # Security: No shell injection
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise Exception(f"Command failed with exit code {result.returncode}: {result.stderr}")


def execute_with_timeout(func, timeout_seconds: int):
    """
    Execute function with timeout.

    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds

    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Function exceeded timeout of {timeout_seconds} seconds")


def push_branch_with_retry(
    repo_path: str, branch_name: str, max_retries: int = 3, backoff_seconds: float = 1.0
) -> bool:
    """
    Push branch with retry logic and exponential backoff.

    Args:
        repo_path: Path to git repository
        branch_name: Branch name to push
        max_retries: Maximum number of retry attempts
        backoff_seconds: Initial backoff delay in seconds

    Returns:
        True if push succeeded, False otherwise
    """
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return True

        except subprocess.CalledProcessError:
            if attempt < max_retries - 1:
                time.sleep(backoff_seconds)
                backoff_seconds *= 2  # Exponential backoff
            continue

    return False


def execute_task_command(
    task: TaskQueueItem, log_file: str, timeout: int = 3600
) -> int:
    """
    Execute /primeA command for task.

    Args:
        task: Task to execute
        log_file: Path to log file for output
        timeout: Maximum execution time in seconds (default: 60 minutes)

    Returns:
        Exit code (0 = success, -1 = timeout, other = failure)
    """
    try:
        # Log command execution
        log_task_progress(log_file, task, f"Executing command: {task.command}")

        # Execute command
        result = subprocess.run(
            task.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Log output
        with open(log_file, "a") as f:
            f.write(f"\n=== Command Output ===\n")
            f.write(result.stdout)
            if result.stderr:
                f.write(f"\n=== Command Errors ===\n")
                f.write(result.stderr)

        return result.returncode

    except subprocess.TimeoutExpired:
        logging.error(f"Task {task.id} timed out after {timeout} seconds")
        log_task_progress(log_file, task, f"TIMEOUT: Exceeded {timeout}s limit")
        return -1
    except Exception as e:
        logging.error(f"Failed to execute task {task.id}: {e}")
        log_task_progress(log_file, task, f"ERROR: {e}")
        return 1


def validate_success_criteria(
    command_exit_code: int,
    tests_passed: bool,
    git_clean: bool,
    branch_pushed: bool,
) -> dict[str, bool]:
    """
    Validate all 4 success criteria from spec-029 section 7.6.

    Args:
        command_exit_code: Exit code of command
        tests_passed: Whether tests passed
        git_clean: Whether git status is clean
        branch_pushed: Whether branch was pushed

    Returns:
        Dict with criteria validation results
    """
    return {
        "command_success": command_exit_code == 0,
        "tests_pass": tests_passed,
        "git_status_clean": git_clean,
        "branch_pushed": branch_pushed,
    }


def verify_success_criteria(
    _run_tests: bool = True, _check_git: bool = True, _push_branch: bool = True
) -> SuccessCriteria:
    """
    Verify all 4 success criteria from spec-029 section 7.6.

    Criteria:
    1. Command exited with code 0
    2. All tests pass
    3. Git status clean
    4. Branch pushed successfully

    Args:
        _run_tests: Internal flag for test mocking
        _check_git: Internal flag for test mocking
        _push_branch: Internal flag for test mocking

    Returns:
        SuccessCriteria with validation results
    """
    criteria = SuccessCriteria(
        exit_code_zero=False,
        tests_pass=False,
        git_clean=False,
        branch_pushed=False,
        all_criteria_met=False,
    )

    # Criterion 1: Exit code 0 (checked by caller)
    criteria.exit_code_zero = True

    # Criterion 2: All tests pass
    if _run_tests:
        try:
            result = subprocess.run(
                ["python", "run_tests.py", "--run-all"],
                capture_output=True,
                text=True,
                timeout=600,
            )
            criteria.tests_pass = result.returncode == 0
        except Exception as e:
            logging.error(f"Test execution failed: {e}")
            criteria.tests_pass = False

    # Criterion 3: Git status clean
    if _check_git:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
            )
            criteria.git_clean = len(result.stdout.strip()) == 0
        except Exception as e:
            logging.error(f"Git status check failed: {e}")
            criteria.git_clean = False

    # Criterion 4: Branch pushed
    if _push_branch:
        try:
            current_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()

            result = subprocess.run(
                ["git", "push", "-u", "origin", current_branch],
                capture_output=True,
                text=True,
                timeout=60,
            )
            criteria.branch_pushed = result.returncode == 0
        except Exception as e:
            logging.error(f"Git push failed: {e}")
            criteria.branch_pushed = False

    # All criteria must be met
    criteria.all_criteria_met = (
        criteria.exit_code_zero
        and criteria.tests_pass
        and criteria.git_clean
        and criteria.branch_pushed
    )

    return criteria


def mark_task_completed(queue_file: str, task_id: str, branch_name: str) -> None:
    """
    Mark task as completed in queue.

    Args:
        queue_file: Path to task_queue.json
        task_id: Task ID to update
        branch_name: Git branch name
    """
    update_task_status(queue_file, task_id, TaskStatus.COMPLETED, branch_name=branch_name)


def mark_task_failed(queue_file: str, task_id: str, error_message: str) -> None:
    """
    Mark task as failed in queue.

    Args:
        queue_file: Path to task_queue.json
        task_id: Task ID to update
        error_message: Error message
    """
    update_task_status(queue_file, task_id, TaskStatus.FAILED, error_message=error_message)


def update_task_status(
    queue_file: str,
    task_id: str,
    status: TaskStatus,
    branch_name: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    Update task status in queue with file locking.

    Args:
        queue_file: Path to task_queue.json
        task_id: Task ID to update
        status: New status
        branch_name: Git branch name (optional)
        error_message: Error message if failed (optional)
    """
    lock_file = queue_file + ".lock"
    fd = acquire_lock_with_retry(lock_file, max_retries=3, timeout=5.0)

    if fd is None:
        logging.error("Failed to acquire lock for status update")
        return

    try:
        # Read queue
        queue = TaskQueue.model_validate_json(Path(queue_file).read_text())

        # Find and update task
        for task in queue.tasks:
            if task.id == task_id:
                task.status = status
                task.completed_at = datetime.now(UTC)

                if branch_name:
                    task.branch_name = branch_name

                if error_message:
                    task.error_message = error_message

                break

        # Write updated queue
        Path(queue_file).write_text(queue.model_dump_json(indent=2))

    finally:
        release_lock(fd)


def create_worker_log_file(worker_id: str, log_dir: str = "logs/overnight") -> str:
    """
    Create log file for worker with timestamp.

    Args:
        worker_id: Worker identifier
        log_dir: Directory for log files

    Returns:
        Path to created log file
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    log_file = Path(log_dir) / f"{worker_id}-{timestamp}.log"
    log_file.touch()
    return str(log_file)


def log_task_progress(log_file: str, task: TaskQueueItem, message: str) -> None:
    """
    Log task progress to worker log file.

    Args:
        log_file: Path to log file
        task: Task being processed
        message: Progress message
    """
    timestamp = datetime.now(UTC).isoformat()
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Task {task.id} ({task.title}): {message}\n")


def process_worker_queue(
    queue_file: str, worker_id: str, log_dir: str = "logs/overnight"
) -> None:
    """
    Main worker loop: claim tasks, execute, report results.

    Args:
        queue_file: Path to task_queue.json
        worker_id: Unique worker identifier
        log_dir: Directory for worker logs
    """
    log_file = create_worker_log_file(worker_id, log_dir)
    logging.info(f"Worker {worker_id} started, logging to {log_file}")

    while True:
        # Claim next task
        task = claim_next_task(queue_file, worker_id)

        if task is None:
            logging.info(f"Worker {worker_id}: No more tasks available")
            break

        log_task_progress(log_file, task, "Task claimed")

        # Generate branch name
        branch_name = generate_branch_name_from_task(task)
        log_task_progress(log_file, task, f"Creating branch: {branch_name}")

        # Create and checkout branch
        if not create_and_checkout_branch(branch_name):
            error_msg = f"Failed to create branch {branch_name}"
            log_task_progress(log_file, task, f"ERROR: {error_msg}")
            update_task_status(queue_file, task.id, TaskStatus.FAILED, error_message=error_msg)
            continue

        # Execute command
        log_task_progress(log_file, task, "Executing command")
        exit_code = execute_task_command(task, log_file, timeout=3600)

        if exit_code != 0:
            error_msg = f"Command failed with exit code {exit_code}"
            log_task_progress(log_file, task, f"ERROR: {error_msg}")

            if exit_code == -1:
                update_task_status(
                    queue_file,
                    task.id,
                    TaskStatus.TIMEOUT,
                    branch_name=branch_name,
                    error_message="Task exceeded 60 minute limit",
                )
            else:
                update_task_status(
                    queue_file,
                    task.id,
                    TaskStatus.FAILED,
                    branch_name=branch_name,
                    error_message=error_msg,
                )
            continue

        # Verify success criteria
        log_task_progress(log_file, task, "Verifying success criteria")
        criteria = verify_success_criteria()

        if criteria.all_criteria_met:
            log_task_progress(log_file, task, "All success criteria met")
            update_task_status(queue_file, task.id, TaskStatus.COMPLETED, branch_name=branch_name)
        else:
            error_msg = "Success criteria not met: "
            if not criteria.tests_pass:
                error_msg += "tests failed, "
            if not criteria.git_clean:
                error_msg += "uncommitted changes, "
            if not criteria.branch_pushed:
                error_msg += "push failed"

            log_task_progress(log_file, task, f"ERROR: {error_msg}")
            update_task_status(
                queue_file,
                task.id,
                TaskStatus.FAILED,
                branch_name=branch_name,
                error_message=error_msg.rstrip(", "),
            )

    logging.info(f"Worker {worker_id} finished")


def main() -> int:
    """
    Main entry point for worker script.

    Returns:
        Exit code (0 = success)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Overnight worker for autonomous night watch")
    parser.add_argument("--queue-file", required=True, help="Path to task_queue.json")
    parser.add_argument("--worker-id", required=True, help="Unique worker identifier")
    parser.add_argument(
        "--log-dir", default="logs/overnight", help="Directory for worker logs"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Process queue
    process_worker_queue(args.queue_file, args.worker_id, args.log_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
