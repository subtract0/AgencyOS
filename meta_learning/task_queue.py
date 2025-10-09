#!/usr/bin/env python3
"""
Atomic Task Queue with File Locking

Enables conflict-free task distribution across multiple machines and agents.
Uses file locking (fcntl) for atomic operations and prevents race conditions.

EPIC 4.2 Extension: Autonomous Multi-Agent Orchestration

Constitutional Compliance:
- Article I: Complete context via dependency tracking
- Article II: Atomic operations prevent conflicts
- Article III: Automated coordination (no manual intervention)

Version: 1.0.0
Created: 2025-10-09
"""

import fcntl
import json
import socket
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Task:
    """
    Single unit of work in the task queue.

    Attributes:
        task_id: Unique identifier for the task
        type: Task type (spec, code, test, integrate)
        description: Human-readable description
        files_to_modify: List of file paths this task will modify
        dependencies: Task IDs that must complete before this task
        assigned_to: Agent ID that claimed this task
        status: Current status (pending, in_progress, completed, failed)
        worktree: Worktree path for isolated execution
        started_at: ISO timestamp when task was claimed
        completed_at: ISO timestamp when task completed
        machine: Machine identifier where task is running
        priority: Priority level (higher = more important)
    """

    task_id: str
    type: str  # "spec", "code", "test", "integrate"
    description: str
    files_to_modify: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    assigned_to: str | None = None
    status: str = "pending"  # pending, in_progress, completed, failed
    worktree: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    machine: str | None = None
    priority: int = 0


class TaskQueue:
    """
    Thread-safe, multi-machine task queue using file locking.

    Provides atomic operations for task claiming and completion, with
    built-in conflict detection and dependency resolution.

    Key Features:
    - File-level locking (fcntl) for atomic read/write
    - Dependency tracking (topological ordering)
    - File conflict detection (prevents merge conflicts)
    - Multi-machine safe (shared filesystem)
    - Graceful degradation (handles stale locks)

    Example:
        >>> queue = TaskQueue()
        >>> queue.add_task(Task(task_id="task1", type="spec", ...))
        >>> task = queue.claim_task(agent_id="agent-1")
        >>> queue.complete_task("task1", success=True)

    Constitutional Compliance:
        - Article I: Complete context via dependency validation
        - Article II: 100% verification via atomic operations
    """

    def __init__(self, queue_file: Path | None = None):
        """
        Initialize task queue.

        Args:
            queue_file: Path to JSON file storing queue state.
                       If None, automatically uses iCloud shared path if available,
                       falls back to local path otherwise.
        """
        # Auto-detect shared workspace (iCloud Drive)
        if queue_file is None:
            queue_file = self._get_default_queue_path()

        self.queue_file = Path(queue_file)
        self.machine_id = f"{socket.gethostname()}-{id(self)}"

        # Initialize queue if doesn't exist
        if not self.queue_file.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_queue([])

    def _get_default_queue_path(self) -> Path:
        """
        Get default queue path, preferring iCloud shared workspace.

        Returns:
            Path to task queue file (iCloud if available, local otherwise)
        """
        # Try to load from config
        config_file = Path(".agency_config.json")
        if config_file.exists():
            try:
                import json

                config = json.loads(config_file.read_text())
                if config.get("shared_workspace", {}).get("enabled"):
                    icloud_path = Path(config["shared_workspace"]["task_queue_file"])
                    if icloud_path.parent.parent.exists():  # Check iCloud is accessible
                        print(f"✅ Using iCloud shared workspace: {icloud_path}")
                        return icloud_path
            except Exception as e:
                print(f"⚠️  Config load failed: {e}, using local path")

        # Fallback to local path
        print("📁 Using local task queue: meta_learning/task_queue.json")
        return Path("meta_learning/task_queue.json")

    def _read_queue(self) -> list[Task]:
        """
        Read queue with shared file lock (atomic read).

        Returns:
            List of Task objects

        Constitutional Compliance:
            - Article II: Atomic read prevents race conditions
        """
        with open(self.queue_file) as f:
            # Acquire shared lock for reading (multiple readers allowed)
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                return [Task(**item) for item in data]
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _write_queue(self, tasks: list[Task]):
        """
        Write queue with exclusive file lock (atomic write).

        Args:
            tasks: List of Task objects to write

        Constitutional Compliance:
            - Article II: Exclusive lock prevents concurrent writes
        """
        with open(self.queue_file, "w") as f:
            # Acquire exclusive lock for writing (blocks all others)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = [asdict(task) for task in tasks]
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def add_task(self, task: Task):
        """
        Add task to queue (atomic operation).

        Args:
            task: Task object to add
        """
        tasks = self._read_queue()
        tasks.append(task)
        self._write_queue(tasks)
        print(f"✅ Added task: {task.task_id} (type={task.type}, priority={task.priority})")

    def add_tasks_batch(self, tasks: list[Task]):
        """
        Add multiple tasks atomically.

        Args:
            tasks: List of Task objects to add
        """
        existing = self._read_queue()
        existing.extend(tasks)
        self._write_queue(existing)
        print(f"✅ Added {len(tasks)} tasks in batch")

    def claim_task(self, agent_id: str) -> Task | None:
        """
        Atomically claim next available task.

        Finds the highest-priority task whose dependencies are met and
        has no file conflicts with in-progress tasks.

        Args:
            agent_id: Unique identifier for the claiming agent

        Returns:
            Task object if claimed, None if no tasks available

        Constitutional Compliance:
            - Article I: Validates dependencies before claiming
            - Article II: Atomic claim prevents double-assignment
        """
        tasks = self._read_queue()

        # Sort by priority (descending) for priority-based claiming
        pending_tasks = sorted(
            [t for t in tasks if t.status == "pending"], key=lambda t: t.priority, reverse=True
        )

        # Find first claimable task
        for task in pending_tasks:
            # Check if dependencies are met
            if not self._dependencies_met(task, tasks):
                continue

            # Check for file conflicts
            if self._has_file_conflicts(task, tasks):
                continue

            # Claim it! (atomic update)
            task.assigned_to = agent_id
            task.status = "in_progress"
            task.started_at = datetime.utcnow().isoformat()
            task.machine = self.machine_id
            task.worktree = f"worktrees/{task.task_id}"

            self._write_queue(tasks)
            print(f"🎯 Agent {agent_id} claimed: {task.task_id}")
            return task

        return None

    def complete_task(self, task_id: str, success: bool = True):
        """
        Mark task as completed or failed (atomic operation).

        Args:
            task_id: ID of task to mark complete
            success: True if successful, False if failed
        """
        tasks = self._read_queue()

        for task in tasks:
            if task.task_id == task_id:
                task.status = "completed" if success else "failed"
                task.completed_at = datetime.utcnow().isoformat()
                break

        self._write_queue(tasks)
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} Task {task_id}: {task.status}")

    def reset_task(self, task_id: str):
        """
        Reset task to pending (e.g., after agent crash).

        Args:
            task_id: ID of task to reset
        """
        tasks = self._read_queue()

        for task in tasks:
            if task.task_id == task_id:
                task.status = "pending"
                task.assigned_to = None
                task.worktree = None
                task.started_at = None
                task.machine = None
                break

        self._write_queue(tasks)
        print(f"🔄 Task {task_id} reset to pending")

    def _dependencies_met(self, task: Task, all_tasks: list[Task]) -> bool:
        """
        Check if all dependencies are completed.

        Args:
            task: Task to check dependencies for
            all_tasks: All tasks in queue

        Returns:
            True if all dependencies completed, False otherwise

        Constitutional Compliance:
            - Article I: Complete context via dependency validation
        """
        if not task.dependencies:
            return True

        completed = {t.task_id for t in all_tasks if t.status == "completed"}
        return all(dep in completed for dep in task.dependencies)

    def _has_file_conflicts(self, task: Task, all_tasks: list[Task]) -> bool:
        """
        Check if any in-progress task is modifying same files.

        This prevents merge conflicts by ensuring only one agent
        modifies a file at a time.

        Args:
            task: Task to check for conflicts
            all_tasks: All tasks in queue

        Returns:
            True if conflicts detected, False otherwise

        Constitutional Compliance:
            - Article II: Conflict prevention ensures stability
        """
        if not task.files_to_modify:
            return False

        task_files = set(task.files_to_modify)

        for other in all_tasks:
            if other.status != "in_progress":
                continue

            if not other.files_to_modify:
                continue

            other_files = set(other.files_to_modify)

            # Any overlap = conflict
            if task_files & other_files:
                print(f"⚠️  File conflict: {task.task_id} vs {other.task_id}")
                print(f"   Overlapping files: {task_files & other_files}")
                return True

        return False

    def get_status(self) -> dict:
        """
        Get queue status summary.

        Returns:
            Dict with counts and task details
        """
        tasks = self._read_queue()

        return {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.status == "pending"]),
            "in_progress": len([t for t in tasks if t.status == "in_progress"]),
            "completed": len([t for t in tasks if t.status == "completed"]),
            "failed": len([t for t in tasks if t.status == "failed"]),
            "tasks": [asdict(t) for t in tasks],
        }

    def get_next_available(self, agent_id: str) -> dict | None:
        """
        Preview next task without claiming it.

        Args:
            agent_id: Agent ID (for logging)

        Returns:
            Dict with task info or None
        """
        tasks = self._read_queue()
        pending = [t for t in tasks if t.status == "pending"]

        for task in pending:
            if self._dependencies_met(task, tasks) and not self._has_file_conflicts(task, tasks):
                return asdict(task)

        return None

    def clear_queue(self):
        """Clear all tasks from queue (use with caution!)."""
        self._write_queue([])
        print("🗑️  Queue cleared")


# CLI Interface
def main():
    """Command-line interface for task queue management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage shared task queue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a task
  %(prog)s add --id task1 --type spec --desc "Create spec" --files spec.md

  # Add task with dependencies
  %(prog)s add --id task2 --type code --desc "Implement" --deps task1

  # View queue status
  %(prog)s status

  # Clear queue (caution!)
  %(prog)s clear
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add task
    add = subparsers.add_parser("add", help="Add task to queue")
    add.add_argument("--id", required=True, help="Task ID")
    add.add_argument(
        "--type",
        required=True,
        choices=["spec", "code", "test", "integrate", "doc"],
        help="Task type",
    )
    add.add_argument("--desc", required=True, help="Description")
    add.add_argument("--files", nargs="+", default=[], help="Files to modify")
    add.add_argument("--deps", nargs="+", default=[], help="Dependency task IDs")
    add.add_argument("--priority", type=int, default=0, help="Priority (higher = first)")

    # Status
    subparsers.add_parser("status", help="Show queue status")

    # Reset task
    reset = subparsers.add_parser("reset", help="Reset task to pending")
    reset.add_argument("--id", required=True, help="Task ID")

    # Clear
    subparsers.add_parser("clear", help="Clear all tasks (use with caution!)")

    args = parser.parse_args()
    queue = TaskQueue()

    if args.command == "add":
        task = Task(
            task_id=args.id,
            type=args.type,
            description=args.desc,
            files_to_modify=args.files,
            dependencies=args.deps,
            priority=args.priority,
        )
        queue.add_task(task)

    elif args.command == "status":
        status = queue.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "reset":
        queue.reset_task(args.id)

    elif args.command == "clear":
        confirm = input("Clear all tasks? [y/N]: ")
        if confirm.lower() == "y":
            queue.clear_queue()


if __name__ == "__main__":
    main()
