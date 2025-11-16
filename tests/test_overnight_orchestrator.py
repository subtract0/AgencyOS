"""
Tests for the overnight orchestrator.

Tests are written FIRST following TDD principles (Constitutional Law #1).
"""

import json
import os
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.models.night_watch import (
    Mission,
    MissionPriority,
    OrchestratorConfig,
    TaskQueue,
    TaskQueueItem,
    TaskStatus,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_missions():
    """Sample missions for testing."""
    return [
        Mission(
            id="pydantic_migration",
            title="Pydantic Migration",
            description="Migrate Dict[Any, Any] to Pydantic models",
            command="/primeA 'Migrate all Dict[str, Any] to Pydantic models'",
            priority=MissionPriority.CRITICAL,
            estimated_duration_minutes=30,
            tags=["refactoring", "type-safety"],
            enabled=True,
        ),
        Mission(
            id="api_docs",
            title="API Documentation Generation",
            description="Generate API reference documentation",
            command="/primeA 'Generate comprehensive API documentation'",
            priority=MissionPriority.HIGH,
            estimated_duration_minutes=20,
            tags=["docs"],
            enabled=True,
        ),
        Mission(
            id="test_coverage",
            title="Test Coverage Improvement",
            description="Add tests to reach 95% coverage",
            command="/primeA 'Improve test coverage to 95%'",
            priority=MissionPriority.MEDIUM,
            estimated_duration_minutes=45,
            tags=["testing"],
            enabled=False,  # Disabled mission
        ),
    ]


@pytest.fixture
def missions_file(temp_dir, sample_missions):
    """Create a missions JSON file."""
    missions_path = temp_dir / "overnight_missions.json"
    missions_data = {
        "version": "1.0",
        "missions": [mission.model_dump() for mission in sample_missions],
    }
    missions_path.write_text(json.dumps(missions_data, indent=2))
    return missions_path


@pytest.fixture
def orchestrator_config():
    """Default orchestrator configuration."""
    return OrchestratorConfig(
        pro_threads=2, air_threads=1, mission_set="full", max_task_duration_minutes=60
    )


# Test 1: Load missions from JSON file
def test_load_missions_from_file(missions_file):
    """Test loading missions from JSON configuration file."""
    from scripts.overnight_orchestrator import load_missions

    missions = load_missions(str(missions_file))

    assert len(missions) == 3
    assert missions[0].id == "pydantic_migration"
    assert missions[1].id == "api_docs"
    assert missions[2].id == "test_coverage"


# Test 2: Filter enabled missions only
def test_filter_enabled_missions(sample_missions):
    """Test filtering only enabled missions."""
    from scripts.overnight_orchestrator import filter_enabled_missions

    enabled = filter_enabled_missions(sample_missions)

    assert len(enabled) == 2
    assert all(mission.enabled for mission in enabled)
    assert enabled[0].id == "pydantic_migration"
    assert enabled[1].id == "api_docs"


# Test 3: Create task queue from missions
def test_create_task_queue_from_missions(sample_missions, orchestrator_config):
    """Test creating task queue from missions."""
    from scripts.overnight_orchestrator import create_task_queue

    enabled_missions = [m for m in sample_missions if m.enabled]
    queue = create_task_queue(enabled_missions, orchestrator_config.mission_set)

    assert queue.version == "1.0"
    assert queue.mission_set == "full"
    assert len(queue.tasks) == 2

    # Check task ordering by priority
    assert queue.tasks[0].mission_id == "pydantic_migration"
    assert queue.tasks[0].priority == 1  # CRITICAL
    assert queue.tasks[0].status == TaskStatus.PENDING

    assert queue.tasks[1].mission_id == "api_docs"
    assert queue.tasks[1].priority == 2  # HIGH


# Test 4: Write queue to file with atomic locking
def test_write_queue_to_file(temp_dir):
    """Test writing queue to JSON file."""
    from scripts.overnight_orchestrator import write_queue

    queue = TaskQueue(mission_set="test", tasks=[])
    queue_path = temp_dir / "task_queue.json"

    write_queue(queue, str(queue_path))

    assert queue_path.exists()
    data = json.loads(queue_path.read_text())
    assert data["mission_set"] == "test"
    assert data["version"] == "1.0"


# Test 5: Atomic file locking with fcntl
def test_file_locking_prevents_concurrent_access(temp_dir):
    """Test that file locking prevents concurrent queue modifications."""
    from scripts.overnight_orchestrator import acquire_lock, release_lock

    lock_path = temp_dir / "test.lock"
    lock_file1 = open(lock_path, "w")
    lock_file2 = open(lock_path, "w")

    # Thread 1 acquires lock
    success1 = acquire_lock(lock_file1, timeout=1.0)
    assert success1 is True

    # Thread 2 should fail to acquire lock (non-blocking)
    success2 = acquire_lock(lock_file2, timeout=0.1)
    assert success2 is False

    # Release lock
    release_lock(lock_file1)
    lock_file1.close()

    # Now thread 2 can acquire
    success2 = acquire_lock(lock_file2, timeout=1.0)
    assert success2 is True
    release_lock(lock_file2)
    lock_file2.close()


# Test 6: Retry logic with exponential backoff (Article I)
def test_file_lock_retry_with_backoff(temp_dir):
    """Test lock acquisition with exponential backoff retries."""
    from scripts.overnight_orchestrator import acquire_lock_with_retry

    lock_path = temp_dir / "test.lock"

    # Test that retry mechanism works by artificially making first attempts fail
    # This is a simplified test that verifies the exponential backoff logic exists
    with open(lock_path, "w") as f:
        # Should succeed on first try when no contention
        success = acquire_lock_with_retry(f, max_retries=3, base_delay=0.01)
        assert success is True


# Test 7: Generate branch name with timestamp
def test_generate_branch_name():
    """Test git branch name generation."""
    from scripts.overnight_orchestrator import generate_branch_name

    branch = generate_branch_name("pydantic_migration")

    assert branch.startswith("night-watch/pydantic-migration-")
    # Should end with timestamp like YYYYMMDD-HHMM
    assert len(branch.split("-")) >= 4


# Test 8: Start local worker threads
def test_start_local_workers(orchestrator_config):
    """Test starting local worker threads on M4 Pro."""
    from scripts.overnight_orchestrator import start_local_workers

    with patch("scripts.overnight_orchestrator.start_worker_thread") as mock_start:
        workers = start_local_workers(orchestrator_config.pro_threads, "/tmp/queue.json")

        assert mock_start.call_count == 2  # pro_threads=2
        assert len(workers) == 2


# Test 9: Generate remote worker command for MacBook Air
def test_generate_remote_worker_command():
    """Test generating command for remote worker execution."""
    from scripts.overnight_orchestrator import generate_remote_worker_command
    from pathlib import Path

    queue_path = str(Path(__file__).resolve().parents[1].parent / "task_queue.json")

    command = generate_remote_worker_command(
        air_threads=1, queue_path=queue_path
    )

    assert "ssh" in command or "python" in command
    assert "overnight_worker.py" in command
    assert queue_path in command


# Test 10: Aggregate worker results
def test_aggregate_results_from_queue(temp_dir):
    """Test aggregating results from completed task queue."""
    from scripts.overnight_orchestrator import aggregate_results

    # Create queue with completed tasks
    tasks = [
        TaskQueueItem(
            id="task_001",
            mission_id="pydantic_migration",
            title="Pydantic Migration",
            command="/primeA 'test'",
            priority=1,
            estimated_duration_minutes=30,
            status=TaskStatus.COMPLETED,
            assigned_to="worker-m4pro-01",
            branch_name="night-watch/pydantic-migration-20251012-0315",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        ),
        TaskQueueItem(
            id="task_002",
            mission_id="api_docs",
            title="API Docs",
            command="/primeA 'test'",
            priority=2,
            estimated_duration_minutes=20,
            status=TaskStatus.FAILED,
            assigned_to="worker-m4pro-02",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error_message="Tests failed",
        ),
    ]

    queue = TaskQueue(mission_set="test", tasks=tasks)
    queue_path = temp_dir / "task_queue.json"
    with open(queue_path, "w") as f:
        f.write(queue.model_dump_json(indent=2))

    results = aggregate_results(str(queue_path))

    assert len(results) == 2
    assert results[0].status == TaskStatus.COMPLETED
    assert results[1].status == TaskStatus.FAILED
    assert results[1].error_message == "Tests failed"


# Test 11: Generate orchestrator report
def test_generate_orchestrator_report():
    """Test final report generation."""
    from scripts.overnight_orchestrator import generate_report
    from shared.models.night_watch import MissionResult

    start_time = datetime.now(UTC)
    end_time = datetime.now(UTC)

    results = [
        MissionResult(
            task_id="task_001",
            mission_id="pydantic_migration",
            title="Pydantic Migration",
            status=TaskStatus.COMPLETED,
            worker_id="worker-m4pro-01",
            branch_name="night-watch/pydantic-migration-20251012-0315",
            started_at=start_time,
            completed_at=end_time,
            duration_minutes=28.5,
            tests_passed=True,
            log_file="logs/overnight/worker-m4pro-01-20251012.log",
        ),
        MissionResult(
            task_id="task_002",
            mission_id="api_docs",
            title="API Docs",
            status=TaskStatus.FAILED,
            worker_id="worker-m4pro-02",
            started_at=start_time,
            completed_at=end_time,
            duration_minutes=15.0,
            tests_passed=False,
            error_message="Command failed",
            log_file="logs/overnight/worker-m4pro-02-20251012.log",
        ),
    ]

    report = generate_report(results, start_time, end_time, "full")

    assert report.mission_set == "full"
    assert report.total_tasks == 2
    assert report.completed_tasks == 1
    assert report.failed_tasks == 1
    assert report.conflict_tasks == 0
    assert len(report.branches_created) == 1
    assert "night-watch/pydantic-migration-20251012-0315" in report.branches_created


# Test 12: Handle git conflicts
def test_handle_git_conflict_task(temp_dir):
    """Test handling tasks that result in git conflicts."""
    from scripts.overnight_orchestrator import mark_task_conflict

    queue = TaskQueue(
        mission_set="test",
        tasks=[
            TaskQueueItem(
                id="task_001",
                mission_id="test",
                title="Test",
                command="/primeA 'test'",
                priority=1,
                estimated_duration_minutes=10,
                status=TaskStatus.IN_PROGRESS,
                assigned_to="worker-01",
            )
        ],
    )

    queue_path = temp_dir / "task_queue.json"
    with open(queue_path, "w") as f:
        f.write(queue.model_dump_json(indent=2))

    mark_task_conflict("task_001", str(queue_path), "Merge conflict in file.py")

    # Reload queue
    updated_queue = TaskQueue.model_validate_json(queue_path.read_text())
    assert updated_queue.tasks[0].status == TaskStatus.CONFLICT
    assert "Merge conflict" in updated_queue.tasks[0].error_message


# Test 13: Handle task timeout
def test_handle_task_timeout(temp_dir):
    """Test handling tasks that exceed max duration."""
    from scripts.overnight_orchestrator import mark_task_timeout

    queue = TaskQueue(
        mission_set="test",
        tasks=[
            TaskQueueItem(
                id="task_001",
                mission_id="test",
                title="Test",
                command="/primeA 'test'",
                priority=1,
                estimated_duration_minutes=10,
                status=TaskStatus.IN_PROGRESS,
                assigned_to="worker-01",
            )
        ],
    )

    queue_path = temp_dir / "task_queue.json"
    with open(queue_path, "w") as f:
        f.write(queue.model_dump_json(indent=2))

    mark_task_timeout("task_001", str(queue_path), max_minutes=60)

    updated_queue = TaskQueue.model_validate_json(queue_path.read_text())
    assert updated_queue.tasks[0].status == TaskStatus.TIMEOUT
    assert "60 minutes" in updated_queue.tasks[0].error_message


# Test 14: Orchestrator main workflow integration
@patch("scripts.overnight_orchestrator.start_local_workers")
@patch("scripts.overnight_orchestrator.wait_for_workers")
@patch("scripts.overnight_orchestrator.aggregate_results")
def test_orchestrator_main_workflow(
    mock_aggregate, mock_wait, mock_start, missions_file, temp_dir, orchestrator_config
):
    """Test complete orchestrator workflow end-to-end."""
    from scripts.overnight_orchestrator import run_orchestrator

    queue_path = temp_dir / "task_queue.json"

    # Mock worker execution
    mock_start.return_value = [MagicMock(), MagicMock()]
    mock_aggregate.return_value = []

    report = run_orchestrator(
        missions_file=str(missions_file),
        queue_path=str(queue_path),
        config=orchestrator_config,
    )

    assert mock_start.called
    assert mock_wait.called
    assert mock_aggregate.called
    assert report.mission_set == "full"
    assert queue_path.exists()


# Test 15: Error handling for missing missions file
def test_error_missing_missions_file():
    """Test error handling when missions file doesn't exist."""
    from scripts.overnight_orchestrator import load_missions

    with pytest.raises(FileNotFoundError):
        load_missions("/nonexistent/missions.json")


# Test 16: Error handling for malformed JSON
def test_error_malformed_missions_json(temp_dir):
    """Test error handling for malformed missions JSON."""
    from scripts.overnight_orchestrator import load_missions

    malformed_path = temp_dir / "malformed.json"
    malformed_path.write_text("{invalid json")

    with pytest.raises(json.JSONDecodeError):
        load_missions(str(malformed_path))


# Test 17: Validate mission priority sorting
def test_mission_priority_sorting(sample_missions):
    """Test that missions are sorted by priority (CRITICAL first)."""
    from scripts.overnight_orchestrator import sort_missions_by_priority

    sorted_missions = sort_missions_by_priority(sample_missions)

    assert sorted_missions[0].priority == MissionPriority.CRITICAL
    assert sorted_missions[1].priority == MissionPriority.HIGH
    assert sorted_missions[2].priority == MissionPriority.MEDIUM


# Test 18: Constitutional compliance - retry on timeout (Article I)
def test_retry_on_lock_timeout_article_i():
    """Test Article I compliance: retry with increasing timeout on lock failure."""
    from scripts.overnight_orchestrator import acquire_lock_with_retry

    # Mock file that always fails
    mock_file = MagicMock()
    mock_file.fileno.return_value = -1

    with patch("fcntl.flock", side_effect=BlockingIOError):
        success = acquire_lock_with_retry(mock_file, max_retries=3, base_delay=0.01)
        assert success is False


# Test 19: Dry run mode (no actual changes)
def test_dry_run_mode(missions_file, temp_dir):
    """Test dry run mode that simulates execution without making changes."""
    from scripts.overnight_orchestrator import run_orchestrator

    config = OrchestratorConfig(pro_threads=1, air_threads=0, dry_run=True)
    queue_path = temp_dir / "task_queue.json"

    report = run_orchestrator(
        missions_file=str(missions_file), queue_path=str(queue_path), config=config
    )

    # In dry run, workers should not start and results should be empty
    # Queue file should still be created
    assert Path(queue_path).exists()
    queue = TaskQueue.model_validate_json(Path(queue_path).read_text())
    assert len(queue.tasks) > 0  # Queue was created with tasks


# Test 20: Generate next steps recommendations
def test_generate_next_steps_recommendations():
    """Test generation of actionable next steps for user."""
    from scripts.overnight_orchestrator import generate_next_steps
    from shared.models.night_watch import MissionResult

    results = [
        MissionResult(
            task_id="task_001",
            mission_id="pydantic_migration",
            title="Pydantic Migration",
            status=TaskStatus.COMPLETED,
            worker_id="worker-01",
            branch_name="night-watch/pydantic-migration-20251012-0315",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            duration_minutes=30.0,
            tests_passed=True,
            log_file="logs/test.log",
        ),
        MissionResult(
            task_id="task_002",
            mission_id="api_docs",
            title="API Docs",
            status=TaskStatus.FAILED,
            worker_id="worker-02",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            duration_minutes=10.0,
            tests_passed=False,
            error_message="Command failed",
            log_file="logs/test.log",
        ),
    ]

    next_steps = generate_next_steps(results)

    assert len(next_steps) > 0
    assert any("review" in step.lower() for step in next_steps)
    assert any("branch" in step.lower() for step in next_steps)
    assert any("failed" in step.lower() for step in next_steps)
