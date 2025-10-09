"""
Integration tests for Stop hook script.

Tests Definition of Done validation.
"""

import json
import subprocess
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "hook_stop.py"


class TestStopHook:
    """Integration tests for Stop hook."""

    def test_all_tasks_completed_returns_exit_0(self):
        """100% task completion should return exit code 0."""
        input_data = {
            "tasks_completed": ["task1", "task2", "task3"],
            "tasks_total": ["task1", "task2", "task3"],
            "status": "stopping",
        }
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Ignore UV installation output
        assert "Constitutional Violation" not in result.stderr

    def test_95_percent_completion_passes(self):
        """95%+ completion should pass (meets threshold)."""
        input_data = {
            "tasks_completed": ["task1", "task2", "task3", "task4", "task5"],
            "tasks_total": ["task1", "task2", "task3", "task4", "task5"],
            "status": "stopping",
        }
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_low_completion_returns_exit_2(self):
        """<95% completion should return exit code 2."""
        input_data = {
            "tasks_completed": ["task1"],
            "tasks_total": ["task1", "task2", "task3", "task4", "task5"],
            "status": "stopping",
        }
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "Constitutional Violation" in result.stderr
        assert "Article V" in result.stderr
        assert "1/5" in result.stderr or "20" in result.stderr

    def test_no_tasks_defined_passes(self):
        """No tasks defined should allow session end."""
        input_data = {
            "tasks_completed": [],
            "tasks_total": [],
            "status": "stopping",
        }
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_incomplete_tasks_listed_in_stderr(self):
        """Stderr should list incomplete tasks."""
        input_data = {
            "tasks_completed": ["task1"],
            "tasks_total": ["task1", "task2", "task3"],
            "status": "stopping",
        }
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "Incomplete tasks" in result.stderr
        assert "task2" in result.stderr
        assert "task3" in result.stderr
        assert "task1" not in result.stderr or "- task1" not in result.stderr  # Completed

    def test_invalid_json_returns_exit_1(self):
        """Invalid JSON should return exit code 1."""
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input="not valid json",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Invalid JSON" in result.stderr

    def test_missing_required_fields_returns_exit_1(self):
        """Missing required fields should return exit code 1."""
        input_data = {}  # Missing all required fields including status
        result = subprocess.run(
            [str(HOOK_SCRIPT)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
