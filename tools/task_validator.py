"""
Task Validator - Pre-flight validation to prevent stale task execution.

Prevents Night Shift from wasting time on already-completed tasks by validating
that the task is still relevant before execution.

Layer 1: Static Analysis Validation
Layer 2: AST-based Code Validation
Layer 3: Pattern Matching for Common Scenarios

Usage:
    validator = TaskValidator()
    result = validator.validate(task)

    if result["already_completed"]:
        # Auto-complete the task, skip execution
        logger.info(f"Task already completed: {result['reason']}")
        mark_task_completed(task, result["evidence"])
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.models.backlog import Task, TaskType
from shared.type_definitions.result import Err, Ok, Result


class TaskValidator:
    """
    Validates tasks before execution to detect already-completed work.

    Prevents:
    - Fixing imports that already exist
    - Adding functions that are already present
    - Fixing bugs that are already fixed
    - Implementing features that already exist
    """

    def __init__(self):
        """Initialize task validator."""
        self.validators = {
            TaskType.BUG_FIX: self._validate_bug_fix,
            TaskType.FEATURE_REQUEST: self._validate_feature,
            TaskType.TECH_DEBT: self._validate_tech_debt,
            TaskType.TEST_FAILURE: self._validate_test_failure,
        }

    def validate(self, task: Task) -> Dict[str, Any]:
        """
        Validate if task is still relevant (not already completed).

        Args:
            task: Task to validate

        Returns:
            Dict with keys:
            - already_completed: bool - True if task is already done
            - reason: str - Why task is already completed
            - evidence: str - File/line showing completion
            - confidence: float - Confidence score (0.0-1.0)
        """
        # Get task-type specific validator
        validator_fn = self.validators.get(task.task_type)

        if not validator_fn:
            # No validator for this type, assume task is valid
            return {
                "already_completed": False,
                "reason": f"No validator for {task.task_type}",
                "evidence": "",
                "confidence": 0.0
            }

        # Run validation
        return validator_fn(task)

    def _validate_bug_fix(self, task: Task) -> Dict[str, Any]:
        """
        Validate bug fix tasks.

        Common patterns:
        - "Fix missing X import" → Check if import exists
        - "Fix NameError: X" → Check if X is defined
        - "Fix TypeError in Y" → Check if Y has type annotations
        """
        title = task.title.lower()
        description = task.description.lower()
        metadata = task.metadata or {}

        # Pattern 1: Missing import
        if "missing" in title and "import" in title:
            return self._check_missing_import(task)

        # Pattern 2: NameError
        if "nameerror" in description or "name" in description and "not defined" in description:
            return self._check_nameerror(task)

        # Pattern 3: File-specific bug with line number
        if "file" in metadata and "line" in metadata:
            return self._check_file_line_bug(task)

        # Default: Assume task is still valid
        return {
            "already_completed": False,
            "reason": "No pattern match for validation",
            "evidence": "",
            "confidence": 0.0
        }

    def _check_missing_import(self, task: Task) -> Dict[str, Any]:
        """
        Check if import is already present in file.

        Example: "Fix missing Path import in test_foo.py"
        → Check if "from pathlib import Path" exists in file
        """
        metadata = task.metadata or {}
        file_path = metadata.get("file")

        if not file_path:
            # Try to extract from title/description
            file_match = re.search(r"in (.+\.py)", task.title)
            if file_match:
                file_path = file_match.group(1)

        if not file_path:
            return {"already_completed": False, "reason": "No file specified", "evidence": "", "confidence": 0.0}

        # Extract what import to check for
        import_match = re.search(r"(missing|add|fix)\s+(.+?)\s+import", task.title.lower())
        if not import_match:
            return {"already_completed": False, "reason": "Cannot parse import name", "evidence": "", "confidence": 0.0}

        import_name = import_match.group(2).strip()

        # Check if file exists
        project_root = Path.cwd()
        full_path = project_root / file_path

        if not full_path.exists():
            return {"already_completed": False, "reason": f"File not found: {file_path}", "evidence": "", "confidence": 0.0}

        # Read file and check for import
        try:
            content = full_path.read_text()

            # Pattern matching for common import formats
            patterns = [
                f"from pathlib import {import_name}",  # Specific import
                f"from pathlib import.*{import_name}",  # Wildcard
                f"import {import_name}",  # Direct import
                f"from .* import.*{import_name}",  # Any module
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Find line number
                    for i, line in enumerate(content.split('\n'), 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            return {
                                "already_completed": True,
                                "reason": f"Import '{import_name}' already exists",
                                "evidence": f"{file_path}:{i} - {line.strip()}",
                                "confidence": 0.95
                            }

            # Import not found
            return {
                "already_completed": False,
                "reason": f"Import '{import_name}' not found in {file_path}",
                "evidence": "",
                "confidence": 0.0
            }

        except Exception as e:
            return {
                "already_completed": False,
                "reason": f"Error reading file: {e}",
                "evidence": "",
                "confidence": 0.0
            }

    def _check_nameerror(self, task: Task) -> Dict[str, Any]:
        """Check if NameError is already fixed (name is now defined)."""
        # Similar pattern to _check_missing_import
        # Extract variable name and check if it's defined in the file
        return {
            "already_completed": False,
            "reason": "NameError validation not yet implemented",
            "evidence": "",
            "confidence": 0.0
        }

    def _check_file_line_bug(self, task: Task) -> Dict[str, Any]:
        """Check if bug at specific file:line is already fixed."""
        # Read file, check if error pattern still exists at that line
        return {
            "already_completed": False,
            "reason": "File/line validation not yet implemented",
            "evidence": "",
            "confidence": 0.0
        }

    def _validate_feature(self, task: Task) -> Dict[str, Any]:
        """Validate feature request tasks."""
        # Check if feature already exists (function/class/file)
        return {
            "already_completed": False,
            "reason": "Feature validation not yet implemented",
            "evidence": "",
            "confidence": 0.0
        }

    def _validate_tech_debt(self, task: Task) -> Dict[str, Any]:
        """Validate tech debt tasks."""
        # Check if refactoring already done
        return {
            "already_completed": False,
            "reason": "Tech debt validation not yet implemented",
            "evidence": "",
            "confidence": 0.0
        }

    def _validate_test_failure(self, task: Task) -> Dict[str, Any]:
        """Validate test failure tasks."""
        # Run the test to see if it still fails
        return {
            "already_completed": False,
            "reason": "Test failure validation not yet implemented",
            "evidence": "",
            "confidence": 0.0
        }
