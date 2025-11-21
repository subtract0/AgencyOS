"""
Tests for Task Validator - Pre-flight validation to prevent stale task execution.

TDD Protocol (Article VI):
- These tests written FIRST (RED phase)
- Implementation in tools/task_validator.py makes them pass (GREEN phase)
"""

import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from tools.task_validator import TaskValidator
from shared.models.backlog import Task, TaskType, TaskPriority, TaskStatus


class TestTaskValidator:
    """Test suite for TaskValidator."""

    def test_init(self):
        """Test TaskValidator initialization."""
        validator = TaskValidator()
        assert validator is not None
        assert len(validator.validators) == 4

    def test_validate_missing_import_already_exists(self, tmp_path):
        """Test validation detects when import already exists."""
        # Create test file with Path import
        test_file = tmp_path / "test_file.py"
        test_file.write_text("from pathlib import Path\n\ndef test():\n    pass\n")

        # Create task to add Path import
        task = Task(
            id="test-123",
            title="Fix missing Path import in test_file.py",
            description="Add missing `from pathlib import Path` import",
            task_type=TaskType.BUG_FIX,
            priority=TaskPriority.P1,
            status=TaskStatus.PENDING,
            metadata={"file": str(test_file.relative_to(Path.cwd()))}
        )

        validator = TaskValidator()

        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = validator.validate(task)

        # Should detect import already exists
        assert result["already_completed"] is True
        assert "already exists" in result["reason"].lower()
        assert result["confidence"] >= 0.9
        assert str(test_file.name) in result["evidence"]

    def test_validate_missing_import_not_present(self, tmp_path):
        """Test validation detects when import is missing."""
        # Create test file WITHOUT Path import
        test_file = tmp_path / "test_file.py"
        test_file.write_text("def test():\n    pass\n")

        # Create task to add Path import
        task = Task(
            id="test-123",
            title="Fix missing Path import in test_file.py",
            description="Add missing `from pathlib import Path` import",
            task_type=TaskType.BUG_FIX,
            priority=TaskPriority.P1,
            status=TaskStatus.PENDING,
            metadata={"file": str(test_file.relative_to(Path.cwd()))}
        )

        validator = TaskValidator()

        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = validator.validate(task)

        # Should detect import is still missing
        assert result["already_completed"] is False
        assert "not found" in result["reason"].lower()
        assert result["confidence"] == 0.0

    def test_validate_non_bug_fix_task(self):
        """Test validation for non-bug-fix tasks."""
        task = Task(
            id="test-123",
            title="Add new feature X",
            description="Implement feature X",
            task_type=TaskType.FEATURE_REQUEST,
            priority=TaskPriority.P2,
            status=TaskStatus.PENDING
        )

        validator = TaskValidator()
        result = validator.validate(task)

        # Should have no validation for feature requests (not yet implemented)
        assert result["already_completed"] is False

    def test_validate_file_not_found(self):
        """Test validation when file doesn't exist."""
        task = Task(
            id="test-123",
            title="Fix missing Path import in nonexistent.py",
            description="Add import",
            task_type=TaskType.BUG_FIX,
            priority=TaskPriority.P1,
            status=TaskStatus.PENDING,
            metadata={"file": "nonexistent.py"}
        )

        validator = TaskValidator()
        result = validator.validate(task)

        # Should handle missing file gracefully
        assert result["already_completed"] is False
        assert "not found" in result["reason"].lower()
