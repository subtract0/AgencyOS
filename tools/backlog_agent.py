"""
Backlog Agent - Intelligent Task Prioritization and Selection (Mission 4)

Provides:
- BacklogStorage: JSONL-based task persistence with CRUD operations
- PriorityQueue: CMP-aware task selection and prioritization
- VectorStore integration for cross-session learning

TDD Protocol (Article VI):
- Tests written FIRST in tests/test_backlog_agent.py
- This implementation makes tests pass (GREEN phase)
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.learning import CmpStore, compute_clade_score
from shared.models.backlog import (
    BacklogMetrics,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
)
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class BacklogStorage:
    """
    JSONL-based task storage with CRUD operations.

    Persistence:
    - Tasks stored in {data_dir}/tasks.jsonl (append-only format)
    - Each line is a JSON object representing one task
    - Atomic writes (write to temp file, then rename)

    Methods:
    - add_task(): Create new task
    - get_task(): Retrieve by ID
    - update_task(): Modify existing task
    - delete_task(): Remove task
    - list_tasks(): Get all tasks with optional filters
    - get_metrics(): Aggregate backlog metrics
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize backlog storage.

        Args:
            data_dir: Directory for tasks.jsonl (default: ~/.agency/memories/agency_backlog)
        """
        if data_dir is None:
            data_dir = str(Path.home() / ".agency" / "memories" / "agency_backlog")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.jsonl"

        # Ensure file exists
        if not self.tasks_file.exists():
            self.tasks_file.touch()

        # Initialize memory store for VectorStore integration
        self.memory_store: Optional[EnhancedMemoryStore] = None

    def add_task(self, task: Task) -> Result[Task, Exception]:
        """
        Add a new task to backlog.

        Args:
            task: Task to add

        Returns:
            Result[Task, Exception]: Added task or error
        """
        try:
            # Set timestamps
            task.created_at = datetime.now()
            task.updated_at = datetime.now()
            task.status = TaskStatus.PENDING

            # Append to JSONL file (atomic write)
            self._append_task(task)

            logger.info(f"Added task: {task.id} - {task.title}")
            return Ok(task)

        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            return Err(e)

    def get_task(self, task_id: str) -> Result[Task, Exception]:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Result[Task, Exception]: Task if found, or error
        """
        try:
            tasks = self._load_all_tasks()

            for task in tasks:
                if task.id == task_id:
                    return Ok(task)

            return Err(Exception(f"Task not found: {task_id}"))

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return Err(e)

    def update_task(self, task: Task) -> Result[Task, Exception]:
        """
        Update an existing task.

        Args:
            task: Task with updated fields

        Returns:
            Result[Task, Exception]: Updated task or error
        """
        try:
            tasks = self._load_all_tasks()
            task_found = False

            # Update task in list
            for i, t in enumerate(tasks):
                if t.id == task.id:
                    task.updated_at = datetime.now()
                    tasks[i] = task
                    task_found = True
                    break

            if not task_found:
                return Err(Exception(f"Task not found: {task.id}"))

            # Rewrite entire file (atomic write)
            self._write_all_tasks(tasks)

            logger.info(f"Updated task: {task.id} - {task.title}")
            return Ok(task)

        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return Err(e)

    def delete_task(self, task_id: str) -> Result[None, Exception]:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            Result[None, Exception]: Success or error
        """
        try:
            tasks = self._load_all_tasks()
            task_found = False

            # Remove task from list
            tasks = [t for t in tasks if t.id != task_id]

            if len(tasks) == len(self._load_all_tasks()):
                return Err(Exception(f"Task not found: {task_id}"))

            # Rewrite entire file (atomic write)
            self._write_all_tasks(tasks)

            logger.info(f"Deleted task: {task_id}")
            return Ok(None)

        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return Err(e)

    def list_tasks(
        self, status: Optional[TaskStatus] = None, priority: Optional[TaskPriority] = None
    ) -> Result[list[Task], Exception]:
        """
        List all tasks with optional filters.

        Args:
            status: Filter by status (optional)
            priority: Filter by priority (optional)

        Returns:
            Result[list[Task], Exception]: List of tasks or error
        """
        try:
            tasks = self._load_all_tasks()

            # Apply filters
            if status:
                tasks = [t for t in tasks if t.status == status]
            if priority:
                tasks = [t for t in tasks if t.priority == priority]

            return Ok(tasks)

        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return Err(e)

    def get_metrics(self) -> Result[BacklogMetrics, Exception]:
        """
        Calculate aggregate backlog metrics.

        Returns:
            Result[BacklogMetrics, Exception]: Metrics or error
        """
        try:
            tasks = self._load_all_tasks()

            if not tasks:
                return Ok(
                    BacklogMetrics(
                        total_tasks=0,
                        pending_tasks=0,
                        in_progress_tasks=0,
                        completed_tasks=0,
                        failed_tasks=0,
                        blocked_tasks=0,
                        avg_completion_time_hours=0.0,
                        p1_count=0,
                        p2_count=0,
                        p3_count=0,
                        oldest_pending_task_age_days=0.0,
                    )
                )

            # Calculate status counts
            pending = [t for t in tasks if t.status == TaskStatus.PENDING]
            in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
            completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            failed = [t for t in tasks if t.status == TaskStatus.FAILED]
            blocked = [t for t in tasks if t.status == TaskStatus.BLOCKED]

            # Calculate priority counts
            p1 = [t for t in tasks if t.priority == TaskPriority.P1]
            p2 = [t for t in tasks if t.priority == TaskPriority.P2]
            p3 = [t for t in tasks if t.priority == TaskPriority.P3]

            # Calculate completion time (for completed tasks)
            completion_times = []
            for task in completed:
                duration = (task.updated_at - task.created_at).total_seconds() / 3600
                completion_times.append(duration)

            avg_completion_time = (
                sum(completion_times) / len(completion_times) if completion_times else 0.0
            )

            # Calculate oldest pending task age
            oldest_age = 0.0
            if pending:
                oldest_task = min(pending, key=lambda t: t.created_at)
                age_seconds = (datetime.now() - oldest_task.created_at).total_seconds()
                oldest_age = age_seconds / 86400  # Convert to days

            return Ok(
                BacklogMetrics(
                    total_tasks=len(tasks),
                    pending_tasks=len(pending),
                    in_progress_tasks=len(in_progress),
                    completed_tasks=len(completed),
                    failed_tasks=len(failed),
                    blocked_tasks=len(blocked),
                    avg_completion_time_hours=avg_completion_time,
                    p1_count=len(p1),
                    p2_count=len(p2),
                    p3_count=len(p3),
                    oldest_pending_task_age_days=oldest_age,
                )
            )

        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return Err(e)

    def store_completion_metadata(
        self, task: Task, duration_hours: float
    ) -> Result[str, Exception]:
        """
        Store task completion metadata in VectorStore.

        Args:
            task: Completed task
            duration_hours: Time taken to complete (hours)

        Returns:
            Result[str, Exception]: Memory ID or error
        """
        try:
            # Initialize memory store if needed
            if self.memory_store is None:
                self.memory_store = EnhancedMemoryStore()

            # Build memory key
            memory_id = self._build_memory_key(task.id)

            # Build content
            content = {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type.value,
                "priority": task.priority.value,
                "complexity": task.estimated_complexity,
                "business_value": task.business_value,
                "duration_hours": duration_hours,
                "status": task.status.value,
                "cmp_related_clade_ids": task.cmp_related_clade_ids,
                "completed_at": task.updated_at.isoformat(),
            }

            # Build tags
            tags = self._build_memory_tags(task)

            # Store in VectorStore
            self.memory_store.store(
                key=memory_id,
                content=json.dumps(content),
                tags=tags,
                agent_id="backlog_agent",
                clade_id=f"backlog_{task.task_type.value}",
                task_type="backlog_completion",
            )

            logger.info(f"Stored completion metadata: {memory_id}")
            return Ok(memory_id)

        except Exception as e:
            logger.error(f"Failed to store completion metadata: {e}")
            return Err(e)

    def _build_memory_key(self, task_id: str) -> str:
        """
        Build memory key for VectorStore.

        Format: backlog_task_{task_id}_{timestamp}

        Args:
            task_id: Task ID

        Returns:
            str: Memory key
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backlog_task_{task_id}_{timestamp}"

    def _build_memory_tags(self, task: Task) -> list[str]:
        """
        Build memory tags for VectorStore.

        Args:
            task: Task to tag

        Returns:
            list[str]: Tags
        """
        return [
            "backlog",
            "task_completion",
            task.priority.value,
            task.task_type.value,
        ]

    def _load_all_tasks(self) -> list[Task]:
        """
        Load all tasks from JSONL file.

        Returns:
            list[Task]: All tasks
        """
        tasks = []

        if not self.tasks_file.exists():
            return tasks

        with open(self.tasks_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    task = Task(**data)
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task line: {e}")
                    continue

        return tasks

    def _append_task(self, task: Task) -> None:
        """
        Append a task to JSONL file (atomic write).

        Args:
            task: Task to append
        """
        # Write to temp file first
        temp_file = self.tasks_file.with_suffix(".tmp")

        # Copy existing content
        if self.tasks_file.exists():
            with open(self.tasks_file, "r") as src:
                with open(temp_file, "w") as dst:
                    dst.write(src.read())

        # Append new task
        with open(temp_file, "a") as f:
            f.write(json.dumps(task.model_dump(), default=str) + "\n")

        # Atomic rename
        temp_file.replace(self.tasks_file)

    def _write_all_tasks(self, tasks: list[Task]) -> None:
        """
        Rewrite entire JSONL file (atomic write).

        Args:
            tasks: All tasks to write
        """
        # Write to temp file first
        temp_file = self.tasks_file.with_suffix(".tmp")

        with open(temp_file, "w") as f:
            for task in tasks:
                f.write(json.dumps(task.model_dump(), default=str) + "\n")

        # Atomic rename
        temp_file.replace(self.tasks_file)

    def release_stale_tasks(self, max_age_minutes: int = 30) -> list[Task]:
        """
        Release tasks stuck in IN_PROGRESS state for longer than max_age_minutes.

        Args:
            max_age_minutes: Maximum allowed age for in-progress tasks

        Returns:
            list[Task]: Tasks that were released
        """
        tasks = self._load_all_tasks()
        if not tasks:
            return []

        now = datetime.now()
        threshold = timedelta(minutes=max_age_minutes)
        released: list[Task] = []
        updated = False

        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                if now - task.updated_at > threshold:
                    task.status = TaskStatus.PENDING
                    task.updated_at = now
                    metadata = dict(task.metadata or {})
                    metadata["stale_release_count"] = metadata.get("stale_release_count", 0) + 1
                    metadata["last_stale_release_at"] = now.isoformat()
                    task.metadata = metadata
                    released.append(task)
                    updated = True

        if updated:
            self._write_all_tasks(tasks)
            logger.info(f"Released {len(released)} stale tasks exceeding {max_age_minutes} minutes")

        return released

    def record_task_failure(
        self, task_id: str, reason: str, max_failures_before_block: int
    ) -> tuple[Task, bool]:
        """
        Increment failure metadata for a task.

        Args:
            task_id: ID of the task
            reason: Failure reason
            max_failures_before_block: Threshold before blocking/escalation

        Returns:
            tuple[Task, bool]: (Updated task, whether escalation/blocking is required)
        """
        tasks = self._load_all_tasks()
        now = datetime.now()
        updated_task: Task | None = None

        for task in tasks:
            if task.id != task_id:
                continue

            metadata = dict(task.metadata or {})
            failure_count = int(metadata.get("failure_count", 0)) + 1
            metadata["failure_count"] = failure_count
            metadata["last_failure_reason"] = reason
            failure_history = metadata.get("failure_history", [])
            failure_history.append({"timestamp": now.isoformat(), "reason": reason})
            metadata["failure_history"] = failure_history[-10:]
            task.metadata = metadata
            task.updated_at = now

            if failure_count >= max_failures_before_block:
                task.status = TaskStatus.BLOCKED
                metadata["blocked_at"] = now.isoformat()
                escalate = True
            else:
                task.status = TaskStatus.PENDING
                escalate = False

            updated_task = task
            break

        if updated_task is None:
            raise ValueError(f"Task not found: {task_id}")

        self._write_all_tasks(tasks)
        return updated_task, escalate

    def reset_task_failures(self, task_id: str) -> None:
        """Reset failure metadata after a successful run."""
        tasks = self._load_all_tasks()
        updated = False
        for task in tasks:
            if task.id != task_id:
                continue

            metadata = dict(task.metadata or {})
            if metadata.get("failure_count"):
                metadata["failure_count"] = 0
            metadata.pop("last_failure_reason", None)
            task.metadata = metadata
            updated = True
            break

        if updated:
            self._write_all_tasks(tasks)

    def append_escalation_note(self, task_id: str, provider: str, analysis: str) -> None:
        """Append escalation details to task metadata."""
        tasks = self._load_all_tasks()
        updated = False
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()

        for task in tasks:
            if task.id != task_id:
                continue

            metadata = dict(task.metadata or {})
            history = metadata.get("escalation_history", [])
            history.append(
                {
                    "provider": provider,
                    "analysis": analysis,
                    "timestamp": now_iso,
                }
            )
            metadata["escalation_history"] = history[-10:]
            task.metadata = metadata
            task.updated_at = now_dt
            updated = True
            break

        if updated:
            self._write_all_tasks(tasks)


class PriorityQueue:
    """
    CMP-aware task prioritization and selection.

    Priority Formula:
        score = (cmp_avg * 0.4) + (business_value/10 * 0.3) + (1/complexity * 0.3)

    Selection Rules:
    - P1 tasks ALWAYS selected before P2/P3 (regardless of score)
    - Within same priority: highest score wins
    - Ties broken by created_at (oldest first)

    Methods:
    - select_next_task(): Select highest-priority pending task
    - _calculate_score(): Calculate priority score
    - _get_cmp_avg_score(): Query CMP scores for task's related clades
    """

    def __init__(self, storage: BacklogStorage):
        """
        Initialize priority queue.

        Args:
            storage: Backlog storage instance
        """
        self.storage = storage
        self.cmp_store: Optional[CmpStore] = None

    def select_next_task(self) -> Result[Task, Exception]:
        """
        Select the next highest-priority pending task.

        Returns:
            Result[Task, Exception]: Selected task or error
        """
        try:
            # Get all pending tasks
            result = self.storage.list_tasks(status=TaskStatus.PENDING)
            if result.is_err():
                return result

            pending_tasks = result.unwrap()

            if not pending_tasks:
                return Err(Exception("Backlog is empty"))

            # Separate by priority (P1 always first)
            p1_tasks = [t for t in pending_tasks if t.priority == TaskPriority.P1]
            p2_tasks = [t for t in pending_tasks if t.priority == TaskPriority.P2]
            p3_tasks = [t for t in pending_tasks if t.priority == TaskPriority.P3]

            # Select from P1 first, then P2, then P3
            if p1_tasks:
                selected = self._select_from_priority_group(p1_tasks)
            elif p2_tasks:
                selected = self._select_from_priority_group(p2_tasks)
            else:
                selected = self._select_from_priority_group(p3_tasks)

            logger.info(f"Selected task: {selected.id} - {selected.title}")
            return Ok(selected)

        except Exception as e:
            logger.error(f"Failed to select next task: {e}")
            return Err(e)

    def _select_from_priority_group(self, tasks: list[Task]) -> Task:
        """
        Select highest-scoring task from a priority group.

        Args:
            tasks: Tasks in same priority group

        Returns:
            Task: Selected task
        """
        # Calculate scores for all tasks
        scored_tasks = []
        for task in tasks:
            cmp_avg = self._get_cmp_avg_score(task)
            score = self._calculate_score(task, cmp_avg)
            scored_tasks.append((task, score))

        # Sort by score (descending), then by created_at (ascending for oldest first)
        scored_tasks.sort(key=lambda x: (-x[1], x[0].created_at))

        return scored_tasks[0][0]

    def _calculate_score(self, task: Task, cmp_avg_score: float) -> float:
        """
        Calculate priority score for a task.

        Formula:
            score = (cmp_avg * 0.4) + (business_value/10 * 0.3) + (1/complexity * 0.3)

        Args:
            task: Task to score
            cmp_avg_score: Average CMP score for related clades

        Returns:
            float: Priority score (0.0-1.0)
        """
        # CMP component (40% weight)
        cmp_component = cmp_avg_score * 0.4

        # Business value component (30% weight)
        business_component = (task.business_value / 10.0) * 0.3

        # Complexity component (30% weight, inverse - simpler tasks score higher)
        complexity_component = (1.0 / task.estimated_complexity) * 0.3

        score = cmp_component + business_component + complexity_component

        logger.debug(
            f"Task {task.id} score: {score:.3f} "
            f"(cmp={cmp_component:.3f}, biz={business_component:.3f}, "
            f"complexity={complexity_component:.3f})"
        )

        return score

    def _get_cmp_avg_score(self, task: Task) -> float:
        """
        Get average CMP score for task's related clades.

        Args:
            task: Task with cmp_related_clade_ids

        Returns:
            float: Average CMP score (0.0-1.0), or 0.5 if no clades
        """
        if not task.cmp_related_clade_ids:
            return 0.5  # Neutral default for tasks with no clades

        try:
            # Initialize CmpStore if needed
            if self.cmp_store is None:
                self.cmp_store = CmpStore()

            # Load CMP events
            events = self.cmp_store.load_events()

            # Calculate score for each clade
            clade_scores = []
            for clade_id in task.cmp_related_clade_ids:
                cmp_score = compute_clade_score(events, clade_id)
                clade_scores.append(cmp_score.score)

            # Return average
            if clade_scores:
                avg_score = sum(clade_scores) / len(clade_scores)
                logger.debug(
                    f"Task {task.id} CMP avg score: {avg_score:.3f} "
                    f"(from {len(clade_scores)} clades)"
                )
                return avg_score
            else:
                return 0.5  # Neutral default

        except Exception as e:
            logger.warning(f"Failed to get CMP scores: {e}, using neutral default")
            return 0.5
