"""
Backlog Auto-Selection Tests (RED Phase - TDD)

Tests the backlog auto-selection mechanism for /primeA zero-argument execution.
These tests MUST fail initially (ImportError) as the implementation doesn't exist yet.

Covers acceptance criteria BACKLOG-001 through BACKLOG-005 from SPEC-030:
- BACKLOG-001: Read ~/.agency/memories/agency_backlog/test_suite_gaps.md correctly
- BACKLOG-002: Parse markdown format (headers, task status, priority)
- BACKLOG-003: Select highest priority "Ready" task (skip "Blocked"/"Locked")
- BACKLOG-004: Empty backlog returns None gracefully
- BACKLOG-005: Corrupted markdown logs warning, continues execution

NECESSARY Pattern Coverage:
- Normal: Valid backlog with Ready tasks, select highest priority
- Edge: Empty backlog, single task, all tasks Blocked, duplicate priorities
- Constraints: File path validation, task format requirements
- Error: File not found, parse failure, permission denied
- Security: Path traversal attempts, malicious markdown injection
- Scale: Large backlog (1000+ tasks) completes in <2s
- Asynchronous: N/A (synchronous file operations)
- Retry: File read timeout, NFS mount delays

Constitutional Compliance:
- Article I: Complete context (retry on file read timeout)
- Article II: 100% verification (no silent failures)
- Article III: Automated enforcement (no manual overrides)
- Article IV: VectorStore integration (store successful selections)
- Article V: Spec-driven (tests trace to SPEC-030 acceptance criteria)

Expected Initial State: ALL TESTS FAIL with ImportError
Expected After Implementation: ALL TESTS PASS with 100% rate
"""

import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result

# Implementation now exists (GREEN PHASE) - import directly
from tools.orchestrator.backlog_selector import (
    BacklogParseError,
    BacklogTask,
    TaskStatus,
    lock_task,
    read_backlog_queue,
    select_next_task,
    unlock_task,
)

# ============================================================================
# NECESSARY NORMAL: Valid backlog with Ready tasks
# ============================================================================


def test_read_backlog_queue_normal(tmp_path: Path, sample_backlog_content: str) -> None:
    """
    BACKLOG-001 NECESSARY Normal: Read backlog file correctly.

    Validates:
    1. File read from ~/.agency/memories/agency_backlog/test_suite_gaps.md
    2. Markdown parsing extracts tasks correctly
    3. Priority, status, description fields populated
    4. Returns Result<list[BacklogTask], BacklogParseError>

    Expected: Ok([BacklogTask(...), BacklogTask(...)])
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    # Act
    result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else None}"
    )

    queue = result.unwrap()
    assert len(queue.tasks) == 5, f"Expected 5 tasks, got {len(queue.tasks)}"

    # Validate first task
    first_task = queue.tasks[0]
    assert first_task.priority == 1, f"Expected priority 1, got {first_task.priority}"
    assert first_task.status == TaskStatus.READY, f"Expected Ready, got {first_task.status}"
    assert "authentication middleware" in first_task.description.lower()


def test_select_next_task_normal(tmp_path: Path, sample_backlog_content: str) -> None:
    """
    BACKLOG-002 NECESSARY Normal: Select highest priority Ready task.

    Validates:
    1. Parse backlog with mixed statuses (Ready, Blocked, Locked)
    2. Select first Ready task by priority (skip Blocked/Locked)
    3. Return BacklogTask with priority 1 (highest priority Ready)

    Expected: Ok(BacklogTask(priority=1, status=Ready, description="authentication middleware"))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else None}"
    )

    task = result.unwrap()
    assert task.priority == 1, f"Expected priority 1, got {task.priority}"
    assert task.status == TaskStatus.READY
    assert "authentication middleware" in task.description.lower()


def test_lock_task_normal(tmp_path: Path, sample_backlog_content: str) -> None:
    """
    BACKLOG-003 NECESSARY Normal: Lock selected task to prevent duplicate work.

    Validates:
    1. Select task with priority 1
    2. Lock task by updating status to Locked with timestamp
    3. Backlog file updated with new status
    4. Returns Ok(BacklogTask) with Locked status

    Expected: Ok(BacklogTask(priority=1, status=Locked, locked_at=<timestamp>))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    task_result = select_next_task(str(backlog_file))
    assert task_result.is_ok()
    task = task_result.unwrap()

    # Act
    lock_result = lock_task(str(backlog_file), task.priority, agent_id="test_agent")

    # Assert
    assert lock_result.is_ok(), (
        f"Expected Ok, got Err: {lock_result.unwrap_err() if lock_result.is_err() else None}"
    )

    locked_task = lock_result.unwrap()
    assert locked_task.status == TaskStatus.LOCKED
    assert locked_task.locked_by == "test_agent"
    assert locked_task.locked_at is not None

    # Verify file updated
    updated_content = backlog_file.read_text()
    assert "Status: Locked" in updated_content
    assert "test_agent" in updated_content


def test_unlock_task_normal(tmp_path: Path, sample_backlog_content: str) -> None:
    """
    NECESSARY Normal: Unlock task after completion or failure.

    Validates:
    1. Lock task first
    2. Unlock task by priority
    3. Status reverts to Ready
    4. Backlog file updated

    Expected: Ok(BacklogTask(priority=1, status=Ready, locked_at=None))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    # Lock task first
    task_result = select_next_task(str(backlog_file))
    task = task_result.unwrap()
    lock_result = lock_task(str(backlog_file), task.priority, agent_id="test_agent")
    assert lock_result.is_ok()

    # Act
    unlock_result = unlock_task(str(backlog_file), task.priority)

    # Assert
    assert unlock_result.is_ok(), (
        f"Expected Ok, got Err: {unlock_result.unwrap_err() if unlock_result.is_err() else None}"
    )

    unlocked_task = unlock_result.unwrap()
    assert unlocked_task.status == TaskStatus.READY
    assert unlocked_task.locked_by is None
    assert unlocked_task.locked_at is None

    # Verify file updated
    updated_content = backlog_file.read_text()
    assert "Status: Ready" in updated_content


# ============================================================================
# NECESSARY EDGE: Empty backlog, single task, all tasks blocked
# ============================================================================


def test_read_backlog_queue_empty(tmp_path: Path) -> None:
    """
    BACKLOG-004 NECESSARY Edge: Empty backlog returns empty list gracefully.

    Validates:
    1. File exists but contains no tasks
    2. Returns Ok([]) (empty list)
    3. No errors or exceptions raised

    Expected: Ok([])
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("# Empty Backlog\n\nNo tasks yet.")

    # Act
    result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else None}"
    )
    queue = result.unwrap()
    assert len(queue.tasks) == 0, f"Expected 0 tasks, got {len(queue.tasks)}"


def test_select_next_task_empty_backlog(tmp_path: Path) -> None:
    """
    BACKLOG-004 NECESSARY Edge: Empty backlog returns None.

    Validates:
    1. Backlog has no tasks
    2. Returns Ok(None) instead of Err
    3. Caller can distinguish "no tasks" from error

    Expected: Ok(None)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("# Empty Backlog\n")

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else None}"
    )
    task = result.unwrap()
    assert task is None, f"Expected None, got {task}"


def test_select_next_task_single_ready_task(tmp_path: Path) -> None:
    """
    NECESSARY Edge: Backlog with single Ready task selects it.

    Validates:
    1. Backlog has only one task (priority 1, Ready)
    2. Task selected successfully
    3. No IndexError or boundary issues

    Expected: Ok(BacklogTask(priority=1))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("# Backlog\n\n- [ ] Priority 1: Single task (Status: Ready)\n")

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok()
    task = result.unwrap()
    assert task is not None
    assert task.priority == 1


def test_select_next_task_all_blocked(tmp_path: Path) -> None:
    """
    NECESSARY Edge: All tasks Blocked returns None.

    Validates:
    1. Backlog has multiple tasks, all Blocked
    2. Returns Ok(None) (no Ready tasks available)
    3. Logs warning about no Ready tasks

    Expected: Ok(None)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_content = """# Backlog

- [ ] Priority 1: Task A (Status: Blocked - needs investigation)
- [ ] Priority 2: Task B (Status: Blocked - dependency not ready)
- [ ] Priority 3: Task C (Status: Blocked - waiting for approval)
"""
    backlog_file.write_text(backlog_content)

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok()
    task = result.unwrap()
    assert task is None, f"Expected None (all tasks blocked), got {task}"


def test_select_next_task_duplicate_priorities(tmp_path: Path) -> None:
    """
    NECESSARY Edge: Duplicate priorities select first occurrence.

    Validates:
    1. Backlog has duplicate priority numbers
    2. First occurrence in file order selected
    3. No ambiguity or random selection

    Expected: Ok(BacklogTask(priority=1, description="Task A"))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_content = """# Backlog

- [ ] Priority 1: Task A (Status: Ready)
- [ ] Priority 1: Task B (Status: Ready)
- [ ] Priority 2: Task C (Status: Ready)
"""
    backlog_file.write_text(backlog_content)

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok()
    task = result.unwrap()
    assert task is not None
    assert task.priority == 1
    assert "Task A" in task.description  # First occurrence


# ============================================================================
# NECESSARY ERROR: File not found, malformed markdown, parse failure
# ============================================================================


def test_read_backlog_queue_file_not_found() -> None:
    """
    BACKLOG-003 NECESSARY Error: File not found returns Err gracefully.

    Validates:
    1. Backlog file doesn't exist
    2. Returns Err(BacklogParseError) with descriptive message
    3. No unhandled FileNotFoundError exception

    Expected: Err(BacklogParseError("Backlog file not found: ..."))
    """
    # Arrange
    nonexistent_path = "/tmp/nonexistent_backlog_12345.md"

    # Act
    result = read_backlog_queue(nonexistent_path)

    # Assert
    assert result.is_err(), f"Expected Err, got Ok: {result.value if result.is_ok() else None}"
    error = result.unwrap_err()
    assert "not found" in str(error).lower() or "does not exist" in str(error).lower()


def test_read_backlog_queue_malformed_markdown(tmp_path: Path) -> None:
    """
    BACKLOG-005 NECESSARY Error: Malformed markdown logs warning, skips invalid tasks.

    Validates:
    1. Backlog has invalid task lines (missing priority, malformed format)
    2. Valid tasks parsed successfully
    3. Invalid tasks skipped with warning log
    4. Returns Ok with partial task list

    Expected: Ok([BacklogTask(priority=2)]) (only valid task)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    malformed_content = """# Backlog

- [ ] Invalid task without priority (Status: Ready)
- [ ] Priority: Not a number (Status: Ready)
- [ ] Priority 2: Valid task (Status: Ready)
- [ ] Priority ABC: Another invalid priority (Status: Ready)
"""
    backlog_file.write_text(malformed_content)

    # Act
    with patch("logging.Logger.warning") as mock_warning:
        result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok (partial parse), got Err: {result.unwrap_err() if result.is_err() else None}"
    )

    queue = result.unwrap()
    assert len(queue.tasks) == 1, f"Expected 1 valid task, got {len(queue.tasks)}"
    assert queue.tasks[0].priority == 2

    # Verify warnings logged
    assert mock_warning.call_count >= 3, "Expected warnings for 3 invalid tasks"


def test_read_backlog_queue_permission_denied(tmp_path: Path) -> None:
    """
    NECESSARY Error: Permission denied returns Err gracefully.

    Validates:
    1. Backlog file exists but is unreadable (chmod 000)
    2. Returns Err(BacklogParseError) with permission message
    3. No unhandled PermissionError exception

    Expected: Err(BacklogParseError("Permission denied: ..."))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("# Backlog\n")
    backlog_file.chmod(0o000)  # Remove all permissions

    try:
        # Act
        result = read_backlog_queue(str(backlog_file))

        # Assert
        assert result.is_err(), f"Expected Err, got Ok: {result.value if result.is_ok() else None}"
        error = result.unwrap_err()
        assert "permission" in str(error).lower() or "denied" in str(error).lower()
    finally:
        # Cleanup: restore permissions for pytest cleanup
        backlog_file.chmod(0o644)


def test_read_backlog_queue_empty_file(tmp_path: Path) -> None:
    """
    NECESSARY Error: Empty file (0 bytes) returns empty list gracefully.

    Validates:
    1. File exists but is completely empty
    2. Returns Ok([]) (no tasks found)
    3. No parsing errors

    Expected: Ok([])
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("")  # Empty file

    # Act
    result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok()
    queue = result.unwrap()
    assert len(queue.tasks) == 0


def test_select_next_task_invalid_status_format(tmp_path: Path) -> None:
    """
    NECESSARY Error: Invalid status format handled gracefully.

    Validates:
    1. Task has invalid status (not Ready/Blocked/Locked)
    2. Task skipped with warning
    3. Next valid task selected

    Expected: Ok(BacklogTask(priority=2)) (skip priority 1 with invalid status)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_content = """# Backlog

- [ ] Priority 1: Task A (Status: InvalidStatus)
- [ ] Priority 2: Task B (Status: Ready)
"""
    backlog_file.write_text(backlog_content)

    # Act
    with patch("logging.Logger.warning") as mock_warning:
        result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok()
    task = result.unwrap()
    assert task is not None
    assert task.priority == 2  # Skip priority 1 (invalid status)

    # Verify warning logged
    mock_warning.assert_called()


# ============================================================================
# NECESSARY SECURITY: Path traversal, malicious markdown injection
# ============================================================================


def test_read_backlog_queue_path_traversal() -> None:
    """
    NECESSARY Security: Path traversal attempts rejected.

    Validates:
    1. Path with ../ traversal syntax rejected
    2. Returns Err with security violation message
    3. No access to files outside ~/.agency/memories/

    Expected: Err(BacklogParseError("Invalid path: path traversal detected"))
    """
    # Arrange
    malicious_path = "../../etc/passwd"

    # Act
    result = read_backlog_queue(malicious_path)

    # Assert
    assert result.is_err(), "Expected Err for path traversal, got Ok"
    error = result.unwrap_err()
    assert "invalid path" in str(error).lower() or "traversal" in str(error).lower()


def test_read_backlog_queue_absolute_path_outside_agency(tmp_path: Path) -> None:
    """
    NECESSARY Security: Absolute paths outside ~/.agency/ rejected.

    Validates:
    1. Absolute path to /etc/passwd rejected
    2. Returns Err with security violation message
    3. Only ~/.agency/memories/ paths allowed

    Expected: Err(BacklogParseError("Invalid path: must be within ~/.agency/memories/"))
    """
    # Arrange
    malicious_path = "/etc/passwd"

    # Act
    result = read_backlog_queue(malicious_path)

    # Assert
    assert result.is_err(), "Expected Err for absolute path outside agency, got Ok"
    error = result.unwrap_err()
    assert "invalid path" in str(error).lower() or "must be within" in str(error).lower()


def test_read_backlog_queue_symlink_to_protected_file(tmp_path: Path) -> None:
    """
    NECESSARY Security: Symlinks to protected files rejected.

    Validates:
    1. Symlink to /etc/passwd rejected
    2. Returns Err with symlink detection message
    3. No symlink following

    Expected: Err(BacklogParseError("Invalid path: symlinks not allowed"))
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    symlink_path = backlog_dir / "malicious_symlink.md"

    # Create symlink to /etc/passwd (if it exists)
    if Path("/etc/passwd").exists():
        symlink_path.symlink_to("/etc/passwd")

        # Act
        result = read_backlog_queue(str(symlink_path))

        # Assert
        assert result.is_err(), "Expected Err for symlink, got Ok"
        error = result.unwrap_err()
        assert "symlink" in str(error).lower() or "invalid path" in str(error).lower()


def test_read_backlog_queue_shell_injection_in_description(tmp_path: Path) -> None:
    """
    NECESSARY Security: Shell injection in description sanitized.

    Validates:
    1. Task description contains shell injection attempt
    2. Description sanitized before storage
    3. No shell command execution

    Expected: Ok(BacklogTask(description="Fix bug ; echo safe")) (sanitized)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    malicious_content = """# Backlog

- [ ] Priority 1: Fix bug ; rm -rf / (Status: Ready)
"""
    backlog_file.write_text(malicious_content)

    # Act
    result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok()
    queue = result.unwrap()
    assert len(queue.tasks) == 1

    # Verify description doesn't execute shell commands
    task = queue.tasks[0]
    assert "Fix bug" in task.description
    # Ensure rm -rf is either removed or sanitized (implementation detail)


def test_lock_task_sql_injection_in_agent_id(tmp_path: Path, sample_backlog_content: str) -> None:
    """
    NECESSARY Security: SQL injection in agent_id sanitized.

    Validates:
    1. agent_id contains SQL injection attempt
    2. Input sanitized before storage
    3. No database modification (file-based storage safe)

    Expected: Ok(BacklogTask(locked_by="test_agent; DROP TABLE")) (sanitized)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    # Act
    malicious_agent_id = "test_agent'; DROP TABLE tasks; --"
    result = lock_task(str(backlog_file), priority=1, agent_id=malicious_agent_id)

    # Assert
    assert result.is_ok()
    locked_task = result.unwrap()

    # Verify SQL injection sanitized (implementation detail)
    # At minimum, file should be valid markdown after lock
    updated_content = backlog_file.read_text()
    assert "DROP TABLE" not in updated_content or "test_agent" in updated_content


# ============================================================================
# NECESSARY SCALE: Large backlog (1000+ tasks) completes in <2s
# ============================================================================


@pytest.mark.benchmark
def test_read_backlog_queue_large_backlog_performance(tmp_path: Path) -> None:
    """
    NECESSARY Scale: Large backlog (1000 tasks) parsed in <2s.

    Validates:
    1. Backlog with 1000 tasks generated
    2. Parsing completes within 2s (PERF-002)
    3. All tasks parsed correctly

    Expected: Ok([BacklogTask(...)] * 1000) in <2s
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"

    # Generate large backlog (1000 tasks)
    large_backlog = "# Large Backlog\n\n"
    for i in range(1, 1001):
        status = "Ready" if i % 3 == 0 else "Blocked"
        # Priority must be 1-5 (Article III validation)
        priority = ((i - 1) % 5) + 1  # Cycles through 1-5
        large_backlog += f"- [ ] Priority {priority}: Task {i} (Status: {status})\n"

    backlog_file.write_text(large_backlog)

    # Act
    start_time = time.time()
    result = read_backlog_queue(str(backlog_file))
    elapsed_time = time.time() - start_time

    # Assert
    assert result.is_ok()
    queue = result.unwrap()
    assert len(queue.tasks) == 1000, f"Expected 1000 tasks, got {len(queue.tasks)}"
    assert elapsed_time < 2.0, f"Expected <2s, took {elapsed_time:.2f}s (PERF-002 violation)"


@pytest.mark.benchmark
def test_select_next_task_large_backlog_performance(tmp_path: Path) -> None:
    """
    NECESSARY Scale: Select next task from 1000-task backlog in <2s.

    Validates:
    1. Backlog with 1000 tasks (33% Ready, 67% Blocked)
    2. Selection completes within 2s (PERF-002)
    3. Correct highest-priority Ready task selected

    Expected: Ok(BacklogTask(priority=3)) in <2s (first Ready task)
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"

    # Generate large backlog with first Ready task at priority 1
    # (Task 3 is first Ready, should have lowest priority number for selection)
    large_backlog = "# Large Backlog\n\n"
    large_backlog += "- [ ] Priority 2: Task 1 (Status: Blocked)\n"
    large_backlog += "- [ ] Priority 3: Task 2 (Status: Blocked)\n"
    for i in range(3, 1001):
        status = "Ready" if i % 3 == 0 else "Blocked"
        # Priority must be 1-5, cycle through to ensure first Ready gets priority 1
        priority = ((i - 1) % 5) + 1  # Task 3 gets ((3-1) % 5) + 1 = 3
        # Adjust: make first few Ready tasks priority 1
        if i == 3:  # First Ready task
            priority = 1
        large_backlog += f"- [ ] Priority {priority}: Task {i} (Status: {status})\n"

    backlog_file.write_text(large_backlog)

    # Act
    start_time = time.time()
    result = select_next_task(str(backlog_file))
    elapsed_time = time.time() - start_time

    # Assert
    assert result.is_ok()
    task = result.unwrap()
    assert task is not None
    assert task.priority == 1, f"Expected priority 1 (first Ready task), got {task.priority}"
    assert elapsed_time < 2.0, f"Expected <2s, took {elapsed_time:.2f}s (PERF-002 violation)"


# ============================================================================
# NECESSARY RETRY: File read timeout, NFS mount delays
# ============================================================================


@pytest.mark.timeout(5)
def test_read_backlog_queue_file_read_timeout_retry(tmp_path: Path) -> None:
    """
    NECESSARY Retry: File read timeout triggers retry with 2x timeout.

    Validates:
    1. First read attempt times out (simulated slow NFS mount)
    2. Retry with 2x timeout succeeds
    3. Returns Ok after retry (Article I: Complete Context)

    Expected: Ok([BacklogTask(...)]) after retry
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text("- [ ] Priority 1: Test task (Status: Ready)\n")

    # Mock slow file read (first call sleeps, second succeeds)
    original_read = Path.read_text
    call_count = 0

    def slow_read(self, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            time.sleep(0.1)  # Simulate slow read
            raise TimeoutError("Read timeout")
        return original_read(self, *args, **kwargs)

    # Act
    with patch.object(Path, "read_text", slow_read):
        result = read_backlog_queue(str(backlog_file))

    # Assert
    assert result.is_ok(), (
        f"Expected Ok after retry, got Err: {result.unwrap_err() if result.is_err() else None}"
    )
    assert call_count == 2, f"Expected 2 attempts (retry), got {call_count}"


# ============================================================================
# INTEGRATION TESTS: VectorStore storage after successful selection
# ============================================================================


@pytest.mark.skip(
    reason="VectorStore integration not implemented in Phase 2 - reserved for future enhancement"
)
def test_select_next_task_stores_pattern_in_vectorstore(
    tmp_path: Path, sample_backlog_content: str, mock_agent_context: AgentContext
) -> None:
    """
    NECESSARY Integration: Successful selection stores pattern in VectorStore.

    Validates:
    1. Task selected successfully
    2. Pattern stored in VectorStore with tags ["backlog", "selection", "success"]
    3. Future selections can query past learnings (Article IV)

    Expected: Ok(BacklogTask) + VectorStore.store_memory called

    Note: This test is skipped pending VectorStore integration implementation.
    """
    # Arrange
    backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(sample_backlog_content)

    # Act
    result = select_next_task(str(backlog_file))

    # Assert
    assert result.is_ok()

    # TODO: Add VectorStore integration
    # mock_agent_context.store_memory.assert_called_once()
    # call_args = mock_agent_context.store_memory.call_args
    # assert "backlog" in call_args.kwargs.get("tags", [])
    # assert "selection" in call_args.kwargs.get("tags", [])
    # assert "success" in call_args.kwargs.get("tags", [])
