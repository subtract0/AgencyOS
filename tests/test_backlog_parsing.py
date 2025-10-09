"""
Tests for backlog parsing and priority queue management.

Constitutional compliance:
- Article I: Complete context before action
- Article II: 100% test success (TDD-first)
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling
"""

import pytest

from shared.models.priority_task import BacklogError, PriorityTask
from tools.priority_queue_manager import PriorityQueueManager


class TestPriorityTaskModel:
    """Test PriorityTask Pydantic model validation."""

    def test_priority_task_valid(self):
        """Test valid PriorityTask creation."""
        # Arrange & Act
        task = PriorityTask(
            rank=1,
            id="test_task",
            description="Test Task",
            value=9,
            effort=2,
            roi=4.5,
            status="Ready",
            command='/primeccc "Test task"',
            next_step="Implement feature X",
        )

        # Assert
        assert task.rank == 1
        assert task.id == "test_task"
        assert task.status == "Ready"
        assert task.roi == 4.5

    def test_priority_task_rank_validation(self):
        """Test rank must be between 1 and 20."""
        # Arrange & Act & Assert - Rank too low
        with pytest.raises(ValueError):
            PriorityTask(
                rank=0,  # Invalid
                id="test",
                description="Test",
                value=5,
                effort=5,
                roi=1.0,
                status="Ready",
                command="test",
                next_step="test",
            )

        # Rank too high
        with pytest.raises(ValueError):
            PriorityTask(
                rank=21,  # Invalid
                id="test",
                description="Test",
                value=5,
                effort=5,
                roi=1.0,
                status="Ready",
                command="test",
                next_step="test",
            )

    def test_priority_task_status_validation(self):
        """Test status must be one of: Ready, Blocked, In Progress, Done."""
        # Arrange & Act & Assert - Invalid status
        with pytest.raises(ValueError):
            PriorityTask(
                rank=1,
                id="test",
                description="Test",
                value=5,
                effort=5,
                roi=1.0,
                status="Invalid Status",  # Not in allowed values
                command="test",
                next_step="test",
            )

    def test_priority_task_calculate_roi(self):
        """Test ROI calculation helper."""
        # Arrange & Act
        roi = PriorityTask.calculate_roi(value=9, effort=2)

        # Assert
        assert roi == 4.5

    def test_priority_task_forbids_extra_fields(self):
        """Test that extra fields are forbidden (strict typing)."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            PriorityTask(
                rank=1,
                id="test",
                description="Test",
                value=5,
                effort=5,
                roi=1.0,
                status="Ready",
                command="test",
                next_step="test",
                extra_field="not_allowed",  # Should be forbidden
            )


class TestPriorityQueueManager:
    """Test PriorityQueueManager for backlog parsing."""

    @pytest.fixture
    def sample_backlog_markdown(self):
        """Sample backlog markdown file content."""
        return """# Agency Backlog: Test Suite Gaps

## TOP 20 PRIORITY QUEUE

### Priority #1: Ollama Docker Compose Setup
- **Status**: Ready
- **Value**: 9/10 (critical functionality)
- **Effort**: 2/10 (straightforward fix)
- **ROI**: 4.5
- **Command**: `/primeccc "Set up Ollama Docker Compose"`
- **Next Step**: Create docker-compose.yml with Ollama service

### Priority #2: Fix Integration Tests
- **Status**: Blocked
- **Value**: 8/10 (high priority)
- **Effort**: 5/10 (moderate work)
- **ROI**: 1.6
- **Command**: `/primeccc "Fix integration tests"`
- **Next Step**: Debug failing integration tests

### Priority #3: Add Type Safety
- **Status**: In Progress
- **Value**: 7/10 (important)
- **Effort**: 3/10 (easy)
- **ROI**: 2.33
- **Command**: `/primeccc "Add type safety"`
- **Next Step**: Run mypy on codebase
"""

    @pytest.fixture
    def priority_queue_manager(self, tmp_path):
        """Create PriorityQueueManager with temporary directory."""
        return PriorityQueueManager()

    def test_parse_backlog_returns_priority_tasks(
        self, priority_queue_manager, sample_backlog_markdown
    ):
        """Test that parse_backlog returns list of PriorityTask objects."""
        # Act
        result = priority_queue_manager.parse_backlog(sample_backlog_markdown)

        # Assert
        assert result.is_ok()
        tasks = result.unwrap()
        assert len(tasks) == 3

        # Verify first task
        assert tasks[0].rank == 1
        assert tasks[0].id == "ollama_docker_compose_setup"
        assert tasks[0].status == "Ready"
        assert tasks[0].value == 9
        assert tasks[0].effort == 2
        assert tasks[0].roi == 4.5

    def test_parse_backlog_with_malformed_input(self, priority_queue_manager):
        """Test that malformed backlog returns empty list (no matches)."""
        # Arrange - Missing required fields (won't match regex)
        malformed = """# Agency Backlog

### Priority #1: Task
- **Status**: Ready
# Missing value, effort, roi, command, next_step
"""

        # Act
        result = priority_queue_manager.parse_backlog(malformed)

        # Assert - Should return empty list (no valid matches)
        assert result.is_ok()
        tasks = result.unwrap()
        assert len(tasks) == 0

    def test_filter_ready_tasks(self, priority_queue_manager, sample_backlog_markdown):
        """Test filter_ready_tasks returns only Ready status tasks."""
        # Arrange
        parse_result = priority_queue_manager.parse_backlog(sample_backlog_markdown)
        all_tasks = parse_result.unwrap()

        # Act
        ready_tasks = priority_queue_manager.filter_ready_tasks(all_tasks)

        # Assert
        assert len(ready_tasks) == 1
        assert ready_tasks[0].rank == 1
        assert ready_tasks[0].status == "Ready"

    def test_filter_ready_tasks_excludes_blocked(
        self, priority_queue_manager, sample_backlog_markdown
    ):
        """Test that Blocked tasks are excluded from ready list."""
        # Arrange
        parse_result = priority_queue_manager.parse_backlog(sample_backlog_markdown)
        all_tasks = parse_result.unwrap()

        # Act
        ready_tasks = priority_queue_manager.filter_ready_tasks(all_tasks)

        # Assert - Should not include Priority #2 (Blocked)
        task_ids = [t.id for t in ready_tasks]
        assert "fix_integration_tests" not in task_ids

    def test_filter_ready_tasks_excludes_in_progress(
        self, priority_queue_manager, sample_backlog_markdown
    ):
        """Test that In Progress tasks are excluded from ready list."""
        # Arrange
        parse_result = priority_queue_manager.parse_backlog(sample_backlog_markdown)
        all_tasks = parse_result.unwrap()

        # Act
        ready_tasks = priority_queue_manager.filter_ready_tasks(all_tasks)

        # Assert - Should not include Priority #3 (In Progress)
        task_ids = [t.id for t in ready_tasks]
        assert "add_type_safety" not in task_ids

    def test_parse_empty_backlog(self, priority_queue_manager):
        """Test parsing empty backlog returns empty list."""
        # Arrange
        empty_backlog = """# Agency Backlog

## TOP 20 PRIORITY QUEUE

(No tasks)
"""

        # Act
        result = priority_queue_manager.parse_backlog(empty_backlog)

        # Assert
        assert result.is_ok()
        tasks = result.unwrap()
        assert len(tasks) == 0

    def test_parse_backlog_preserves_order(self, priority_queue_manager, sample_backlog_markdown):
        """Test that parsed tasks preserve priority order."""
        # Act
        result = priority_queue_manager.parse_backlog(sample_backlog_markdown)

        # Assert
        tasks = result.unwrap()
        assert tasks[0].rank == 1
        assert tasks[1].rank == 2
        assert tasks[2].rank == 3


class TestBacklogErrorModel:
    """Test BacklogError Pydantic model."""

    def test_backlog_error_parse_error(self):
        """Test BacklogError.parse_error factory method."""
        # Act
        error = BacklogError.parse_error("Invalid format", line_number=42)

        # Assert
        assert error.error_type == "ParseError"
        assert "Invalid format" in error.message
        assert error.line_number == 42

    def test_backlog_error_not_found(self):
        """Test BacklogError.not_found factory method."""
        # Act
        error = BacklogError.not_found("Task not found")

        # Assert
        assert error.error_type == "NotFound"
        assert error.message == "Task not found"

    def test_backlog_error_io_error(self):
        """Test BacklogError.io_error factory method."""
        # Act
        error = BacklogError.io_error("File not readable")

        # Assert
        assert error.error_type == "IOError"
        assert "File not readable" in error.message
