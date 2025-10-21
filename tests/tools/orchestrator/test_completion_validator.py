"""Tests for CompletionValidator (STEP 6.5 validation gate).

Constitutional Compliance:
- Article I: Complete context validation
- Article II: 100% verification (all checks pass)
- Article III: Automated enforcement
- Article IV: VectorStore pattern application
- Article V: Trace to spec (design_completion_validator.md)

Test Pattern: NECESSARY (Normal, Edge, Security, Spec, Accessibility, Resilience, Year-round)
"""

from pathlib import Path

import pytest

from shared.type_definitions.result import Err, Ok
from tools.orchestrator.completion_validator import (
    CompletionValidator,
    ValidationError,
    ValidationResults,
)

# ===== NORMAL CASES =====


def test_validates_successful_completion():
    """N: Validate that all checks pass for successful completion."""
    # Arrange
    validator = CompletionValidator(
        task_results=[
            {"id": "task1", "status": "success", "acceptance_criteria_met": True},
            {"id": "task2", "status": "success", "acceptance_criteria_met": True},
        ],
        todos=[
            {"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"},
            {"content": "Task 2", "status": "completed", "activeForm": "Completed Task 2"},
        ],
        spec_criteria=["Feature A implemented", "Feature B tested"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_ok(), (
        f"Expected Ok, got Err: {result.unwrap_err() if result.is_err() else None}"
    )
    validation = result.unwrap()
    assert validation.all_tasks_completed is True
    assert validation.acceptance_criteria_met is True
    assert validation.todowrite_synced is True
    assert validation.backlog_zero is True
    assert validation.constitutional_compliant is True
    assert len(validation.warnings) == 0
    assert len(validation.errors) == 0


def test_validates_with_backlog_warning():
    """N: Validate with backlog items present (warning only)."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": True}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature implemented"],
        backlog_items=["TODO: Optimize performance"],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_ok()
    validation = result.unwrap()
    assert validation.backlog_zero is False
    assert len(validation.warnings) == 1
    assert "backlog" in validation.warnings[0].lower()


# ===== EDGE CASES =====


def test_validates_empty_task_list():
    """E: Edge case with no tasks (should fail)."""
    # Arrange
    validator = CompletionValidator(
        task_results=[],
        todos=[],
        spec_criteria=["No features"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.reason == "no_tasks"
    assert "no tasks" in error.message.lower()


def test_validates_incomplete_tasks():
    """E: Edge case with incomplete tasks (should fail)."""
    # Arrange
    validator = CompletionValidator(
        task_results=[
            {"id": "task1", "status": "success", "acceptance_criteria_met": True},
            {"id": "task2", "status": "pending", "acceptance_criteria_met": False},
        ],
        todos=[
            {"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"},
            {"content": "Task 2", "status": "in_progress", "activeForm": "Working on Task 2"},
        ],
        spec_criteria=["Feature A", "Feature B"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.reason == "incomplete_tasks"
    assert "task2" in error.message.lower()


def test_validates_todowrite_mismatch():
    """E: Edge case where TodoWrite doesn't match task results."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": True}],
        todos=[{"content": "Task 1", "status": "in_progress", "activeForm": "Working Task 1"}],
        spec_criteria=["Feature A"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.reason == "todowrite_mismatch"
    assert "todo" in error.message.lower()


# ===== SECURITY CASES =====


def test_validates_malicious_task_injection():
    """S: Security - validate against malicious task data."""
    # Arrange
    validator = CompletionValidator(
        task_results=[
            {"id": "'; DROP TABLE tasks; --", "status": "success", "acceptance_criteria_met": True}
        ],
        todos=[{"content": "Normal task", "status": "completed", "activeForm": "Completed"}],
        spec_criteria=["Feature"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert - should handle gracefully without SQL injection
    assert isinstance(result, (Ok, Err))


# ===== SPEC TRACEABILITY =====


def test_validates_spec_criteria_not_met():
    """Sp: Spec - validate acceptance criteria traceability."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": False}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature A: Must validate input", "Feature B: Must handle errors"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.reason == "acceptance_criteria_unmet"
    assert "acceptance criteria" in error.message.lower()


def test_validates_missing_spec_criteria():
    """Sp: Spec - validate with empty spec criteria."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": True}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=[],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert - should warn but not fail
    assert result.is_ok()
    validation = result.unwrap()
    assert len(validation.warnings) == 1
    assert "no spec criteria" in validation.warnings[0].lower()


# ===== RESILIENCE CASES =====


def test_validates_with_null_values():
    """R: Resilience - handle None/null values gracefully."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": None}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert - should handle None gracefully
    assert isinstance(result, (Ok, Err))


def test_validates_with_malformed_data():
    """R: Resilience - handle malformed data structures."""
    # Arrange
    validator = CompletionValidator(
        task_results=[
            {"id": "task1", "status": "success"}  # Missing acceptance_criteria_met
        ],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert - should handle missing fields
    assert isinstance(result, (Ok, Err))


# ===== YEAR-ROUND CASES =====


def test_validates_large_task_count():
    """Y: Year-round - validate with large number of tasks (scalability)."""
    # Arrange
    task_results = [
        {"id": f"task{i}", "status": "success", "acceptance_criteria_met": True}
        for i in range(1000)
    ]
    todos = [
        {"content": f"Task {i}", "status": "completed", "activeForm": f"Completed Task {i}"}
        for i in range(1000)
    ]

    validator = CompletionValidator(
        task_results=task_results,
        todos=todos,
        spec_criteria=["Feature"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert - should handle large datasets efficiently
    assert result.is_ok()
    validation = result.unwrap()
    assert validation.all_tasks_completed is True


# ===== CONSTITUTIONAL COMPLIANCE =====


def test_validates_constitutional_articles():
    """Test that all 5 constitutional articles are checked."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": True}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature"],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_ok()
    validation = result.unwrap()
    assert validation.constitutional_compliant is True
    assert "Article I" in str(validation.constitutional_checks)
    assert "Article II" in str(validation.constitutional_checks)
    assert "Article III" in str(validation.constitutional_checks)
    assert "Article IV" in str(validation.constitutional_checks)
    assert "Article V" in str(validation.constitutional_checks)


def test_validates_context_efficiency():
    """Test context efficiency validation (Article I)."""
    # Arrange
    validator = CompletionValidator(
        task_results=[{"id": "task1", "status": "success", "acceptance_criteria_met": True}],
        todos=[{"content": "Task 1", "status": "completed", "activeForm": "Completed Task 1"}],
        spec_criteria=["Feature"],
        backlog_items=[],
        context_usage=0.45,  # 45% usage (below 80% threshold)
    )

    # Act
    result = validator.validate()

    # Assert - should warn about low context usage
    assert result.is_ok()
    validation = result.unwrap()
    assert len(validation.warnings) >= 1
    assert any("context efficiency" in w.lower() for w in validation.warnings)


# ===== INTEGRATION TESTS =====


def test_integration_with_primeA_execution():
    """Integration: Validate typical primeA execution scenario."""
    # Arrange - Simulate completed primeA execution
    validator = CompletionValidator(
        task_results=[
            {"id": "spec_gen", "status": "success", "acceptance_criteria_met": True},
            {"id": "test_write", "status": "success", "acceptance_criteria_met": True},
            {"id": "impl_code", "status": "success", "acceptance_criteria_met": True},
            {"id": "verify_tests", "status": "success", "acceptance_criteria_met": True},
        ],
        todos=[
            {
                "content": "Phase 1: Spec Generation",
                "status": "completed",
                "activeForm": "Completed",
            },
            {"content": "Phase 2: Test Writing", "status": "completed", "activeForm": "Completed"},
            {
                "content": "Phase 3: Implementation",
                "status": "completed",
                "activeForm": "Completed",
            },
            {"content": "Phase 4: Verification", "status": "completed", "activeForm": "Completed"},
            {
                "content": "Post-execution reflection",
                "status": "completed",
                "activeForm": "Completed",
            },
        ],
        spec_criteria=[
            "All acceptance criteria must be met",
            "100% test pass rate",
            "Constitutional compliance verified",
        ],
        backlog_items=[],
    )

    # Act
    result = validator.validate()

    # Assert
    assert result.is_ok()
    validation = result.unwrap()
    assert validation.all_tasks_completed is True
    assert validation.acceptance_criteria_met is True
    assert validation.todowrite_synced is True
    assert validation.constitutional_compliant is True
    assert len(validation.errors) == 0
