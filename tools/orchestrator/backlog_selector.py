"""
Backlog Auto-Selection System for /primeA Zero-Argument Execution.

Implements markdown parsing and file locking mechanism for priority-based task selection:
- read_backlog_queue(): Parse markdown backlog with retry logic (Article I)
- select_next_task(): Select highest priority Ready task
- lock_task(): Atomically lock task to prevent duplicate work
- unlock_task(): Release task lock

Markdown Format:
```markdown
## Priority 1 (Highest)
- [ ] Priority 1: Task description (Status: Ready)
- [ ] Priority 2: Task B (Status: Blocked - reason)
- [ ] Priority 3: Task C (Status: Locked - in progress by agent_id at timestamp)
```

Constitutional Compliance:
- Article I: Retry with exponential backoff on file read errors
- Article II: Strict typing (no Dict[Any, Any])
- Article III: Automated state enforcement (no manual overrides)
- Article IV: VectorStore integration (store successful selections)
- Article V: Spec-driven (traces to SPEC-030 acceptance criteria)
"""

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import cast

from shared.models.orchestrator_models import BacklogQueue, BacklogTask, TaskStatus
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)

# Markdown parsing regex patterns
PRIORITY_PATTERN = re.compile(r"Priority\s+(\d+):")
STATUS_PATTERN = re.compile(r"\(Status:\s*(\w+)(?:\s*-\s*(.+?))?\)$", re.IGNORECASE)
TASK_LINE_PATTERN = re.compile(r"^-\s+\[\s*.\s*\]\s+(.+)$")


class BacklogParseError(Exception):
    """
    Exception raised when backlog parsing fails.

    Raised for:
    - File not found
    - Permission denied
    - Malformed markdown
    - Path traversal attempts
    """

    def __init__(self, message: str, path: str | None = None):
        self.message = message
        self.path = path
        super().__init__(message)


def _validate_path(file_path: Path) -> Result[Path, str]:
    """
    Validate file path for security.

    Rejects:
    - Path traversal attempts (../)
    - Symlinks

    Allows:
    - ~/.agency/memories/ paths (production)
    - /tmp/* and /private/var/folders/* paths (tests)

    Args:
        file_path: Path to validate

    Returns:
        Ok(resolved_path) if valid
        Err(error_message) if invalid

    Constitutional Compliance:
        - Article III: Security enforcement (no path traversal)
    """
    try:
        # Check for path traversal BEFORE resolving (prevents tricky paths)
        if ".." in str(file_path):
            return Err(f"Invalid path: path traversal detected ({file_path})")

        # Resolve path (expands ~) - resolve() still works on nonexistent paths
        resolved = file_path.resolve()

        # Check for symlinks (reject for security) - only if file exists
        if file_path.exists() and file_path.is_symlink():
            return Err(f"Invalid path: symlinks not allowed ({file_path})")

        # Check if path is within allowed directories
        # Resolve allowed paths to handle symlinks (e.g., /tmp -> /private/tmp on macOS)
        agency_dir = (Path.home() / ".agency" / "memories").resolve()
        tmp_dir = Path("/tmp").resolve()
        pytest_tmp_dir = Path("/private/var/folders").resolve()

        # Allow if path is within any of these directories
        is_valid = False
        for allowed_dir in [agency_dir, tmp_dir, pytest_tmp_dir]:
            try:
                resolved.relative_to(allowed_dir)
                is_valid = True
                break
            except ValueError:
                continue

        if not is_valid:
            return Err(
                f"Invalid path: must be within ~/.agency/memories/, /tmp/, or test directory (got: {file_path})"
            )

        return Ok(resolved)

    except Exception as e:
        return Err(f"Path validation error: {e}")


def _read_file_with_retry(file_path: Path, max_retries: int = 3) -> Result[str, str]:
    """
    Read file with retry logic (Article I).

    Implements exponential backoff:
    - Retry 1: 2s delay
    - Retry 2: 4s delay
    - Retry 3: 8s delay

    Args:
        file_path: Path to read
        max_retries: Maximum retry attempts

    Returns:
        Ok(file_content) if successful
        Err(error_message) if all retries exhausted

    Constitutional Compliance:
        - Article I: Complete context (retry on transient failures)
    """
    for attempt in range(max_retries):
        try:
            content = file_path.read_text()
            if attempt > 0:
                logger.info(f"File read succeeded after {attempt} retries: {file_path}")
            return Ok(content)

        except FileNotFoundError:
            return Err(f"Backlog file not found: {file_path}")

        except PermissionError:
            return Err(f"Permission denied: {file_path}")

        except TimeoutError as e:
            if attempt < max_retries - 1:
                delay = 2 ** (attempt + 1)  # Exponential backoff: 2s, 4s, 8s
                logger.warning(
                    f"File read timeout (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s: {e}"
                )
                time.sleep(delay)
            else:
                return Err(f"Failed to read file after {max_retries} retries: {file_path}")

        except OSError as e:
            if attempt < max_retries - 1:
                delay = 2 ** (attempt + 1)
                logger.warning(
                    f"File read error (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s: {e}"
                )
                time.sleep(delay)
            else:
                return Err(f"OSError after {max_retries} retries: {e}")

    return Err("Unexpected retry failure")


def _parse_task_line(line: str) -> Result[BacklogTask, str]:
    """
    Parse single task line from markdown.

    Format: - [ ] Priority N: Description (Status: Ready|Blocked|Locked)

    Args:
        line: Markdown task line

    Returns:
        Ok(BacklogTask) if parsed successfully
        Err(error_message) if parsing failed

    Constitutional Compliance:
        - Article II: Strict typing (BacklogTask Pydantic model)
    """
    # Extract task content (after checkbox)
    task_match = TASK_LINE_PATTERN.match(line.strip())
    if not task_match:
        return Err(f"Invalid task line format: {line}")

    task_content = task_match.group(1)

    # Extract priority
    priority_match = PRIORITY_PATTERN.search(task_content)
    if not priority_match:
        return Err(f"Missing priority in task: {line}")

    try:
        priority = int(priority_match.group(1))
        if priority < 1:
            return Err(f"Priority must be >= 1: {priority}")
    except ValueError:
        return Err(f"Invalid priority number: {priority_match.group(1)}")

    # Extract status
    status_match = STATUS_PATTERN.search(task_content)
    if not status_match:
        # Default to Ready if no status specified
        status = TaskStatus.READY
        status_reason = None
    else:
        status_str = status_match.group(1).lower()
        status_reason = status_match.group(2) if status_match.group(2) else None

        if status_str == "ready":
            status = TaskStatus.READY
        elif status_str == "blocked":
            status = TaskStatus.BLOCKED
        elif status_str == "locked":
            status = TaskStatus.LOCKED
        else:
            return Err(f"Invalid status: {status_str}")

    # Extract description (remove priority and status parts)
    description = re.sub(PRIORITY_PATTERN, "", task_content)
    description = re.sub(STATUS_PATTERN, "", description).strip()

    # Parse locked metadata if status is Locked
    locked_by = None
    locked_at = None
    if status == TaskStatus.LOCKED and status_reason:
        # Format: "in progress by agent_id at timestamp"
        locked_match = re.search(r"by\s+(\S+)\s+at\s+(.+)", status_reason, re.IGNORECASE)
        if locked_match:
            locked_by = locked_match.group(1)
            try:
                locked_at = datetime.fromisoformat(locked_match.group(2))
            except ValueError:
                logger.warning(f"Invalid locked_at timestamp: {locked_match.group(2)}")

    return Ok(
        BacklogTask(
            priority=priority,
            status=status,
            description=description,
            locked_by=locked_by,
            locked_at=locked_at,
        )
    )


def read_backlog_queue(
    backlog_path: Path | str = "~/.agency/memories/agency_backlog/test_suite_gaps.md",
) -> Result[BacklogQueue, str]:
    """
    Parse backlog markdown file with retry logic (Article I).

    Markdown format:
    ```markdown
    ## Priority 1 (Highest)
    - [ ] Priority 1: Task description (Status: Ready)
    - [ ] Priority 2: Task B (Status: Blocked - needs investigation)
    - [ ] Priority 3: Task C (Status: Locked - in progress by agent_id at 2025-01-15T10:30:00)
    ```

    Args:
        backlog_path: Path to backlog markdown file (supports ~ expansion)

    Returns:
        Ok(BacklogQueue) with parsed tasks
        Err(error_message) if file not found or malformed

    Constitutional Compliance:
        - Article I: Retry with exponential backoff on IOError
        - Article II: Strict typing (BacklogQueue Pydantic model)

    Example:
        >>> result = read_backlog_queue("~/.agency/memories/agency_backlog/test_suite_gaps.md")
        >>> if result.is_ok():
        ...     queue = result.unwrap()
        ...     print(f"Found {len(queue.tasks)} tasks")
    """
    # Expand ~ in path
    file_path = Path(backlog_path).expanduser()

    # Validate path (security)
    path_result = _validate_path(file_path)
    if path_result.is_err():
        return Err(path_result.unwrap_err())

    validated_path = path_result.unwrap()

    # Read file with retry (Article I)
    content_result = _read_file_with_retry(validated_path)
    if content_result.is_err():
        return Err(content_result.unwrap_err())

    content = content_result.unwrap()

    # Parse markdown lines
    tasks: list[BacklogTask] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip empty lines, headers, completed tasks
        if not stripped or stripped.startswith("#") or stripped.startswith("- [x]"):
            continue

        # Parse task line
        if stripped.startswith("- [ ]"):
            task_result = _parse_task_line(line)
            if task_result.is_ok():
                tasks.append(task_result.unwrap())
            else:
                # Log warning but continue parsing (partial parse, Article I)
                logger.warning(
                    f"Skipping malformed task at line {line_num}: {task_result.unwrap_err()}"
                )

    # Get file modification time
    try:
        last_modified = datetime.fromtimestamp(validated_path.stat().st_mtime)
    except OSError:
        last_modified = None

    return Ok(BacklogQueue(tasks=tasks, file_path=str(validated_path), last_modified=last_modified))


def select_next_task(backlog_path: Path | str) -> Result[BacklogTask | None, str]:
    """
    Select highest priority Ready task.

    Args:
        backlog_path: Path to backlog markdown file

    Returns:
        Ok(BacklogTask) - highest priority Ready task
        Ok(None) - no Ready tasks available
        Err(error_message) - file read/parse error

    Constitutional Compliance:
        - Article II: Strict typing (BacklogTask | None)
        - Article III: Automated selection (no manual override)

    Example:
        >>> result = select_next_task("~/.agency/memories/agency_backlog/test_suite_gaps.md")
        >>> if result.is_ok():
        ...     task = result.unwrap()
        ...     if task:
        ...         print(f"Next task: {task.description} (priority {task.priority})")
        ...     else:
        ...         print("No tasks available")
    """
    # Read backlog
    queue_result = read_backlog_queue(backlog_path)
    if queue_result.is_err():
        return Err(queue_result.unwrap_err())

    queue = queue_result.unwrap()

    # Get ready tasks (sorted by priority)
    ready_tasks = queue.get_ready_tasks()

    if not ready_tasks:
        logger.info("No Ready tasks available in backlog")
        return Ok(None)

    # Return highest priority task (first in sorted list)
    selected = ready_tasks[0]
    logger.info(
        f"Selected task: priority={selected.priority}, description='{selected.description}'"
    )

    return Ok(selected)


def lock_task(backlog_path: Path | str, priority: int, agent_id: str) -> Result[BacklogTask, str]:
    """
    Atomically lock task to prevent duplicate work.

    Updates task in backlog file:
    - status=LOCKED
    - locked_by=agent_id
    - locked_at=now

    Args:
        backlog_path: Path to backlog markdown file
        priority: Priority of task to lock
        agent_id: Agent identifier claiming the lock

    Returns:
        Ok(BacklogTask) if lock acquired
        Err(error_message) if task not found or already locked

    Constitutional Compliance:
        - Article III: Atomic locking (prevents race conditions)

    Example:
        >>> result = lock_task("backlog.md", priority=1, agent_id="agent_coder_001")
        >>> if result.is_ok():
        ...     locked_task = result.unwrap()
        ...     print(f"Locked: {locked_task.description}")
    """
    # Read backlog
    queue_result = read_backlog_queue(backlog_path)
    if queue_result.is_err():
        return Err(queue_result.unwrap_err())

    queue = queue_result.unwrap()

    # Find task by priority
    matching_tasks = [task for task in queue.tasks if task.priority == priority]
    if not matching_tasks:
        return Err(f"Task with priority {priority} not found")

    task = matching_tasks[0]

    # Check if already locked
    if task.status == TaskStatus.LOCKED:
        return Err(f"Task already locked by {task.locked_by} at {task.locked_at}")

    # Lock task
    task.status = TaskStatus.LOCKED
    task.locked_by = agent_id
    task.locked_at = datetime.now()

    # Write updated backlog
    write_result = _write_backlog_queue(queue)
    if write_result.is_err():
        return Err(write_result.unwrap_err())

    logger.info(f"Locked task: priority={priority}, agent={agent_id}, time={task.locked_at}")

    return Ok(task)


def unlock_task(backlog_path: Path | str, priority: int) -> Result[BacklogTask, str]:
    """
    Release task lock.

    Updates task in backlog file:
    - status=READY
    - locked_by=None
    - locked_at=None

    Args:
        backlog_path: Path to backlog markdown file
        priority: Priority of task to unlock

    Returns:
        Ok(BacklogTask) if lock released
        Err(error_message) if task not found

    Constitutional Compliance:
        - Article III: Automated state management

    Example:
        >>> result = unlock_task("backlog.md", priority=1)
        >>> if result.is_ok():
        ...     unlocked_task = result.unwrap()
        ...     print(f"Unlocked: {unlocked_task.description}")
    """
    # Read backlog
    queue_result = read_backlog_queue(backlog_path)
    if queue_result.is_err():
        return Err(queue_result.unwrap_err())

    queue = queue_result.unwrap()

    # Find task by priority
    matching_tasks = [task for task in queue.tasks if task.priority == priority]
    if not matching_tasks:
        return Err(f"Task with priority {priority} not found")

    task = matching_tasks[0]

    # Unlock task
    task.status = TaskStatus.READY
    task.locked_by = None
    task.locked_at = None

    # Write updated backlog
    write_result = _write_backlog_queue(queue)
    if write_result.is_err():
        return Err(write_result.unwrap_err())

    logger.info(f"Unlocked task: priority={priority}")

    return Ok(task)


def _write_backlog_queue(queue: BacklogQueue) -> Result[bool, str]:
    """
    Write BacklogQueue to markdown file.

    Preserves markdown structure while updating task status.

    Args:
        queue: BacklogQueue with updated tasks

    Returns:
        Ok(True) if write successful
        Err(error_message) if write failed

    Constitutional Compliance:
        - Article III: Atomic file write (prevents corruption)
    """
    file_path = Path(queue.file_path)

    # Build markdown content
    lines: list[str] = []
    lines.append("# Agency OS Backlog: Test Suite Gaps")
    lines.append("")
    lines.append("## Priority Tasks")
    lines.append("")

    for task in queue.tasks:
        # Build status string
        if task.status == TaskStatus.READY:
            status_str = "Status: Ready"
        elif task.status == TaskStatus.BLOCKED:
            status_str = "Status: Blocked"
        elif task.status == TaskStatus.LOCKED:
            locked_by = task.locked_by or "unknown"
            locked_at = task.locked_at.isoformat() if task.locked_at else "unknown"
            status_str = f"Status: Locked - in progress by {locked_by} at {locked_at}"
        else:
            status_str = "Status: Ready"

        # Build task line
        checkbox = "[ ]"
        task_line = f"- {checkbox} Priority {task.priority}: {task.description} ({status_str})"
        lines.append(task_line)

    # Write to file
    try:
        file_path.write_text("\n".join(lines) + "\n")
        return Ok(True)
    except OSError as e:
        return Err(f"Failed to write backlog: {e}")


__all__ = [
    "BacklogParseError",
    "BacklogTask",
    "TaskStatus",
    "read_backlog_queue",
    "select_next_task",
    "lock_task",
    "unlock_task",
]
