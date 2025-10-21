"""
Test Suite for TRM-7M Validation Layer

Validates 4 checkpoints with graceful fallback behavior:
1. DAG validation (circular dependency detection)
2. Type constraint validation (Dict[Any, Any] elimination)
3. Edge case inference (boundary condition discovery)
4. Lint/format pre-validation (trivial error elimination)
"""

from pathlib import Path

import pytest

from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType
from tools.trm_training.grid_transformers import (
    apply_lint_fix,
    code_to_lint_grid,
    code_to_type_constraint_grid,
    function_signature_to_grid,
    task_graph_to_adjacency_matrix,
)
from tools.trm_training.validation_checkpoints import (
    apply_trm_validation_gates,
    infer_edge_cases_checkpoint,
    validate_dag_checkpoint,
    validate_lint_checkpoint,
    validate_type_constraints_checkpoint,
)
from trinity_protocol.core.trm_validator import (
    ProblemType,
    ReasoningTask,
    TRMUnavailableError,
    TRMValidator,
    ValidationResult,
)


class TestTRMValidator:
    """Test core TRM validator functionality."""

    @pytest.mark.asyncio
    async def test_dag_validation_no_cycle(self):
        """Test DAG validation passes for acyclic graph."""
        # Create simple DAG: task1 -> task2 -> task3
        adj_matrix = [
            [0, 1, 0],  # task1 -> task2
            [0, 0, 1],  # task2 -> task3
            [0, 0, 0],  # task3 no deps
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.DEPENDENCY_GRAPH,
            input_grid=adj_matrix,
            proposed_solution=adj_matrix,
            constraints=["Must be acyclic (DAG)", "No self-loops"],
            max_refinement_steps=16,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok(), "DAG validation should succeed"

        validation = result.unwrap()
        assert validation.converged is True, "DAG should be validated (no cycle)"
        assert validation.confidence >= 0.85, (
            f"Confidence {validation.confidence} should be >= 0.85"
        )
        assert validation.latency_ms >= 0, "Latency should be non-negative"

    @pytest.mark.asyncio
    async def test_dag_validation_with_cycle(self):
        """Test DAG validation detects circular dependencies."""
        # Create cycle: task1 -> task2 -> task3 -> task1
        adj_matrix = [
            [0, 1, 0],  # task1 -> task2
            [0, 0, 1],  # task2 -> task3
            [1, 0, 0],  # task3 -> task1 (CYCLE!)
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.DEPENDENCY_GRAPH,
            input_grid=adj_matrix,
            proposed_solution=adj_matrix,
            constraints=["Must be acyclic (DAG)", "No self-loops"],
            max_refinement_steps=16,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok(), "Validation should complete (even with cycle)"

        validation = result.unwrap()
        assert validation.converged is False, "Cycle should be detected (converged=False)"

    @pytest.mark.asyncio
    async def test_type_constraint_validation_no_violations(self):
        """Test type constraint validation passes for clean code."""
        # Grid: [has_param_types, has_return_type, uses_any, uses_dict_any]
        type_grid = [
            [1, 1, 0, 0],  # All params typed, return type, no Any, no Dict[Any, Any]
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.TYPE_CONSTRAINTS,
            input_grid=type_grid,
            proposed_solution=None,
            constraints=[
                "No Dict[Any, Any]",
                "All function parameters typed",
                "All return types specified",
            ],
            max_refinement_steps=16,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok()

        validation = result.unwrap()
        assert validation.converged is True, "No type violations should be detected"
        assert len(validation.violations) == 0, "Violations list should be empty"

    @pytest.mark.asyncio
    async def test_type_constraint_validation_dict_any_detected(self):
        """Test type constraint validation detects Dict[Any, Any] violations."""
        # Grid: [has_param_types, has_return_type, uses_any, uses_dict_any]
        type_grid = [
            [1, 1, 1, 1],  # Dict[Any, Any] violation (column 3 = 1)
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.TYPE_CONSTRAINTS,
            input_grid=type_grid,
            proposed_solution=None,
            constraints=["No Dict[Any, Any]"],
            max_refinement_steps=16,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok()

        validation = result.unwrap()
        assert validation.converged is False, "Dict[Any, Any] violation should be detected"
        assert len(validation.violations) > 0, (
            "Violations list should contain Dict[Any, Any] violation"
        )
        assert "dict" in validation.violations[0].description.lower(), (
            f"Expected 'dict' in violation description, got: {validation.violations[0].description}"
        )

    @pytest.mark.asyncio
    async def test_edge_case_inference(self):
        """Test edge case inference discovers boundary conditions."""
        # Grid: [is_int, is_optional, max_value]
        sig_grid = [
            [1, 0, 100],  # requests_per_min: int (max 100)
            [1, 1, 50],  # burst_size: int = 50 (optional)
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.EDGE_CASE_INFERENCE,
            input_grid=sig_grid,
            proposed_solution=None,
            constraints=["Boundary values (min, max)"],
            max_refinement_steps=12,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok()

        inference = result.unwrap()
        assert len(inference.edge_cases) >= 2, "Should discover at least 2 boundary edge cases"
        assert any("min" in ec.description.lower() for ec in inference.edge_cases), (
            "Should discover min boundary"
        )
        assert any("max" in ec.description.lower() for ec in inference.edge_cases), (
            "Should discover max boundary"
        )

    @pytest.mark.asyncio
    async def test_lint_validation_no_violations(self):
        """Test lint validation passes for clean code."""
        # Grid: [length, trailing_space, is_import, sorted]
        lint_grid = [
            [9, 0, 1, 1],  # "import os" (no trailing space, sorted)
            [10, 0, 1, 1],  # "import sys" (no trailing space, sorted)
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.LINT_VALIDATION,
            input_grid=lint_grid,
            proposed_solution=None,
            constraints=["No trailing whitespace", "Imports sorted alphabetically"],
            max_refinement_steps=8,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok()

        validation = result.unwrap()
        assert validation.converged is True, "No lint violations should be detected"
        assert len(validation.fixes) == 0, "No fixes should be needed"

    @pytest.mark.asyncio
    async def test_lint_validation_trailing_space(self):
        """Test lint validation detects trailing whitespace."""
        # Grid: [length, trailing_space, is_import, sorted]
        lint_grid = [
            [9, 1, 0, 0],  # Line with trailing space (column 1 = 1)
        ]

        validator = TRMValidator()
        task = ReasoningTask(
            problem_type=ProblemType.LINT_VALIDATION,
            input_grid=lint_grid,
            proposed_solution=None,
            constraints=["No trailing whitespace"],
            max_refinement_steps=8,
        )

        result = await validator.validate_and_refine(task)
        assert result.is_ok()

        validation = result.unwrap()
        assert len(validation.fixes) > 0, "Trailing space fix should be suggested"
        assert validation.fixes[0].fix_type == "remove_trailing_space"


class TestGridTransformers:
    """Test grid transformation utilities."""

    def test_task_graph_to_adjacency_matrix(self):
        """Test task graph conversion to adjacency matrix."""
        # Create simple task graph using SPEC tasks to avoid Article II validation
        tasks = [
            Task(
                id="task_1",
                title="Task 1",
                type=TaskType.SPEC,  # Use SPEC to avoid Code->Test requirement
                tier=TaskTier.TIER_1,
                agent="planner",
                description="Task 1",
                dependencies=["task_2"],
                acceptance_criteria=["Criteria 1"],
            ),
            Task(
                id="task_2",
                title="Task 2",
                type=TaskType.SPEC,
                tier=TaskTier.TIER_1,
                agent="planner",
                description="Task 2",
                dependencies=[],
                acceptance_criteria=["Criteria 2"],
            ),
        ]

        graph = TaskGraph(
            mission="Test Mission",
            phases=[Phase(id="phase_1", title="Phase 1", tasks=tasks)],
        )

        adj_matrix, task_ids = task_graph_to_adjacency_matrix(graph)

        assert len(adj_matrix) == 2, "Matrix should be 2x2"
        assert task_ids == ["task_1", "task_2"], "Task IDs should match"
        assert adj_matrix[0][1] == 1, "task_1 should depend on task_2"
        assert adj_matrix[1][0] == 0, "task_2 should not depend on task_1"

    def test_code_to_type_constraint_grid(self):
        """Test Python code to type constraint grid conversion."""
        code = """
def process_data(items: list[str], config: Dict[Any, Any]) -> bool:
    return True
"""

        type_grid, line_numbers = code_to_type_constraint_grid(code)

        assert len(type_grid) == 1, "Should extract 1 function"
        assert type_grid[0][0] == 1, "Function should have param types"
        assert type_grid[0][1] == 1, "Function should have return type"
        assert type_grid[0][3] == 1, "Should detect Dict[Any, Any] usage"

    def test_function_signature_to_grid(self):
        """Test function signature to grid conversion."""
        signature = "def rate_limit(requests_per_min: int, burst_size: int = 50) -> bool"

        sig_grid, param_names = function_signature_to_grid(signature)

        assert len(sig_grid) == 2, "Should extract 2 parameters"
        assert sig_grid[0][0] == 1, "requests_per_min should be int"
        assert sig_grid[0][1] == 0, "requests_per_min should not be optional"
        assert sig_grid[1][1] == 1, "burst_size should be optional (has default)"
        assert sig_grid[1][2] == 50, "burst_size max value should be 50"

    def test_code_to_lint_grid(self):
        """Test Python code to lint grid conversion."""
        code = """import os
import sys

def foo():
    x = 1
"""  # Note: trailing space after "x = 1"

        lint_grid, line_numbers = code_to_lint_grid(code)

        assert len(lint_grid) == 6, "Should extract 6 lines"
        # Line 0: import os, Line 1: import sys, Line 2: empty
        assert lint_grid[0][2] == 1, "Line 1 should be import (import os)"
        assert lint_grid[1][2] == 1, "Line 2 should be import (import sys)"
        assert lint_grid[2][2] == 0, "Line 3 should be empty line"


class TestValidationCheckpoints:
    """Test validation checkpoint integration."""

    @pytest.mark.asyncio
    async def test_checkpoint_1_dag_validation_success(self):
        """Test CHECKPOINT 1 DAG validation with acyclic graph."""
        tasks = [
            Task(
                id="task_1",
                title="Task 1",
                type=TaskType.SPEC,  # Use SPEC to avoid validation error
                tier=TaskTier.TIER_1,
                agent="planner",
                description="Task 1",
                dependencies=["task_2"],
                acceptance_criteria=["Criteria 1"],
            ),
            Task(
                id="task_2",
                title="Task 2",
                type=TaskType.SPEC,
                tier=TaskTier.TIER_1,
                agent="planner",
                description="Task 2",
                dependencies=[],
                acceptance_criteria=["Criteria 2"],
            ),
        ]

        graph = TaskGraph(
            mission="Test Mission",
            phases=[Phase(id="phase_1", title="Phase 1", tasks=tasks)],
        )

        validator = TRMValidator(use_mock=True)
        result = await validate_dag_checkpoint(graph, validator)

        assert result.is_ok(), "DAG validation should succeed"
        validation = result.unwrap()
        assert validation.converged is True, "Graph should be acyclic"

    @pytest.mark.asyncio
    async def test_checkpoint_2_type_constraint_validation(self):
        """Test CHECKPOINT 2 type constraint validation (mock)."""
        # Mock task with result containing files_modified
        task = Task(
            id="code_task",
            title="Code Task",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Implement feature",
            dependencies=[],
        )
        task.result = {"files_modified": []}  # No files for mock test

        validator = TRMValidator()
        result = await validate_type_constraints_checkpoint(task, validator)

        assert result.is_ok(), "Type validation should complete"

    @pytest.mark.asyncio
    async def test_checkpoint_3_edge_case_inference(self):
        """Test CHECKPOINT 3 edge case inference (mock)."""
        # Create test task BEFORE code task (TDD workflow, Article II)
        test_task = Task(
            id="test_rate_limit",
            title="Test Rate Limit",
            type=TaskType.TEST,
            tier=TaskTier.TIER_2,
            agent="test_generator",
            description="Test rate limiting",
            dependencies=[],
            verification_target="code_rate_limit",
            acceptance_criteria=[],
        )

        code_task = Task(
            id="code_rate_limit",
            title="Code Rate Limit",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Implement rate_limit(requests_per_min: int, burst_size: int) -> bool",
            dependencies=["test_rate_limit"],  # TDD: Code depends on Test
        )

        graph = TaskGraph(
            mission="Test Mission",
            phases=[
                Phase(id="phase_1", title="Phase 1", tasks=[test_task]),
                Phase(id="phase_2", title="Phase 2", tasks=[code_task]),
            ],
        )

        validator = TRMValidator()
        result = await infer_edge_cases_checkpoint(test_task, graph, validator)

        assert result.is_ok(), "Edge case inference should complete"
        inference = result.unwrap()
        assert len(inference.edge_cases) >= 2, "Should discover boundary edge cases"

    @pytest.mark.asyncio
    async def test_checkpoint_4_lint_validation(self):
        """Test CHECKPOINT 4 lint/format pre-validation (mock)."""
        task = Task(
            id="code_task",
            title="Code Task",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            agent="coder",
            description="Implement feature",
            dependencies=[],
        )
        task.result = {"files_modified": []}  # No files for mock test

        validator = TRMValidator()
        result = await validate_lint_checkpoint(task, validator, auto_fix=True)

        assert result.is_ok(), "Lint validation should complete"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
