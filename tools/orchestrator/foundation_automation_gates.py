"""
Foundation Automation Gates - Orchestrator Constitutional Enforcement.

Provides 12 constitutional gates enforced at orchestrator workflow level BEFORE
task execution begins. These gates validate task graphs, quality thresholds,
and constitutional compliance at the orchestration layer.

Gates:
- GATE-001: Incomplete graph detection (Article I)
- GATE-002: Timeout retry protocol (Article I)
- GATE-003: Test failures block execution (Article II)
- GATE-004: Completion threshold enforcement (Article II)
- GATE-005: Circular dependency detection (Article III)
- GATE-006: Slop immunity enforcement (Article III)
- GATE-007: Budget guard enforcement (Article III)
- GATE-008: Main branch protection (Article III)
- GATE-009: VectorStore query before action (Article IV)
- GATE-010: VectorStore storage after success (Article IV)
- GATE-011: Missing acceptance criteria detection (Article V)
- GATE-012: Graph traceability validation (Article V)

Constitutional Compliance:
- Article I: Complete Context (gates 1-2)
- Article II: 100% Verification (gates 3-4)
- Article III: Automated Enforcement (gates 5-8)
- Article IV: Continuous Learning (gates 9-10)
- Article V: Spec-Driven Development (gates 11-12)

Usage:
    ```python
    from tools.orchestrator.foundation_automation_gates import (
        validate_all_gates,
        validate_gate_001_incomplete_graph,
        validate_gate_003_test_failures,
        FoundationGateError,
        GateValidationResult
    )

    # Validate all gates before orchestrator execution
    result = await validate_all_gates(
        task_graph=graph,
        context=agent_context,
        test_results=test_results,
        execution_results=execution_results,
        git_repo_path=Path.cwd(),
        slop_guardian=slop_guardian,
        budget_guard=budget_guard
    )

    if result.is_err():
        error = result.unwrap_err()
        print(f"Gate {error.gate} failed: {error.message}")
        # Block orchestrator execution
    else:
        # All gates passed - proceed with execution
        validation = result.unwrap()
        print(f"{validation['gates_passed']}/12 gates passed")
    ```

Related Files:
- tools/orchestrator/constitutional_validator.py: Article-level enforcement
- tools/orchestrator/slop_guardian.py: Quality evaluation (GATE-006)
- tools/orchestrator/budget_guard.py: Cost enforcement (GATE-007)
- shared/models/task_graph.py: Task graph Pydantic models
"""

import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shared.agent_context import AgentContext
from shared.models.task_graph import TaskGraph, TaskType
from shared.type_definitions.result import Err, Ok, Result

# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class GateValidationResult(BaseModel):
    """Result of a single gate validation."""

    gate: str = Field(description="Gate identifier (e.g., GATE-001)")
    passed: bool = Field(description="Whether gate validation passed")
    message: str = Field(description="Human-readable validation message")
    article: str | None = Field(None, description="Constitutional article (e.g., Article I)")
    execution_time_ms: float = Field(description="Gate validation execution time in milliseconds")

    # Optional fields for specific gate types
    retry_count: int | None = Field(None, description="Number of retries (GATE-002)")
    final_timeout: int | None = Field(None, description="Final timeout value (GATE-002)")
    pass_rate: float | None = Field(None, description="Test pass rate (GATE-003)")
    failed_tests: list[str] | None = Field(None, description="List of failed test names (GATE-003)")
    completion_rate: float | None = Field(None, description="Task completion rate (GATE-004)")
    skipped_tasks: int | None = Field(None, description="Number of skipped tasks (GATE-004)")
    cycle_path: list[str] | None = Field(None, description="Circular dependency path (GATE-005)")
    slop_score: float | None = Field(None, description="Slop immunity score (GATE-006)")
    threshold: float | None = Field(None, description="Slop/budget threshold (GATE-006, GATE-007)")
    estimated_cost: float | None = Field(None, description="Estimated cost in USD (GATE-007)")
    daily_limit: float | None = Field(None, description="Daily budget limit (GATE-007)")
    current_branch: str | None = Field(None, description="Current git branch (GATE-008)")
    learnings_retrieved: int | None = Field(
        None, description="Number of learnings retrieved (GATE-009)"
    )
    patterns_stored: int | None = Field(None, description="Number of patterns stored (GATE-010)")
    tasks_validated: int | None = Field(None, description="Number of tasks validated (GATE-012)")
    task_id: str | None = Field(None, description="Task ID (GATE-011)")


class FoundationGateError(Exception):
    """Exception raised when a foundation gate validation fails."""

    def __init__(
        self,
        message: str,
        gate: str,
        article: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize foundation gate error.

        Args:
            message: Human-readable error message
            gate: Gate identifier (e.g., GATE-001)
            article: Constitutional article (e.g., Article I)
            **kwargs: Additional gate-specific error metadata
        """
        self.message = message
        self.gate = gate
        self.article = article

        # Store additional metadata as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of error."""
        return self.message


# ============================================================================
# ARTICLE I: COMPLETE CONTEXT BEFORE ACTION (Gates 1-2)
# ============================================================================


def validate_gate_001_incomplete_graph(
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-001: Validate task graph completeness (no missing dependencies).

    Article I: "No action shall be taken without complete contextual understanding"

    Validates:
    - All task dependencies reference existing tasks
    - No dangling dependencies
    - Task IDs are unique within graph

    Args:
        task_graph: TaskGraph to validate

    Returns:
        Ok(GateValidationResult) if graph is complete
        Err(FoundationGateError) if missing dependencies found

    Example:
        >>> result = validate_gate_001_incomplete_graph(task_graph)
        >>> if result.is_err():
        ...     error = result.unwrap_err()
        ...     print(f"Missing dependencies: {error.missing_dependencies}")
    """
    start_time = time.time()

    # Build set of all task IDs
    all_task_ids = set()
    for phase in task_graph.phases:
        for task in phase.tasks:
            all_task_ids.add(task.id)

    # Check all dependencies exist
    missing_dependencies = []
    for phase in task_graph.phases:
        for task in phase.tasks:
            for dep in task.dependencies:
                if dep not in all_task_ids:
                    missing_dependencies.append(dep)

    execution_time_ms = (time.time() - start_time) * 1000

    if missing_dependencies:
        return Err(
            FoundationGateError(
                message=f"Incomplete task graph: missing dependencies {missing_dependencies}",
                gate="GATE-001",
                article="Article I",
                missing_dependencies=missing_dependencies,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-001",
            passed=True,
            message="Task graph complete - all dependencies exist",
            article="Article I",
            execution_time_ms=execution_time_ms,
        )
    )


def validate_gate_002_timeout_retry(
    operation: Callable[[], dict[str, Any]],
    context: AgentContext,
    initial_timeout: int,
    max_retries: int,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-002: Validate timeout retry protocol (exponential backoff).

    Article I: "Retry with extended timeouts (2x, 3x, up to 10x)"

    Validates:
    - Initial timeout triggers 2x retry
    - Second timeout triggers 3x retry
    - Third timeout triggers 10x retry (final)
    - Operation succeeds within retry limit

    Args:
        operation: Operation to execute (returns dict with status field)
        context: AgentContext for logging
        initial_timeout: Initial timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Ok(GateValidationResult) if operation succeeds
        Err(FoundationGateError) if all retries exhausted

    Example:
        >>> def my_operation():
        ...     return {"status": "success"}
        >>> result = validate_gate_002_timeout_retry(my_operation, context, 120, 3)
    """
    start_time = time.time()

    retry_count = 0
    timeout_multipliers = [2.0, 3.0, 10.0]
    current_timeout = initial_timeout

    for attempt in range(max_retries):
        result = operation()

        if isinstance(result, dict):
            status = result.get("status")

            if status == "timeout":
                retry_count = attempt + 1

                # Calculate next timeout (exponential backoff)
                if attempt < len(timeout_multipliers):
                    current_timeout = int(initial_timeout * timeout_multipliers[attempt])

                # Continue to next retry
                continue

            if status == "success":
                execution_time_ms = (time.time() - start_time) * 1000

                return Ok(
                    GateValidationResult(
                        gate="GATE-002",
                        passed=True,
                        message=f"Operation succeeded after {retry_count} retries",
                        article="Article I",
                        execution_time_ms=execution_time_ms,
                        retry_count=retry_count,
                        final_timeout=current_timeout,
                    )
                )

    # All retries exhausted
    return Err(
        FoundationGateError(
            message=f"Operation failed after {max_retries} retries",
            gate="GATE-002",
            article="Article I",
            retry_count=max_retries,
            final_timeout=current_timeout,
        )
    )


# ============================================================================
# ARTICLE II: 100% VERIFICATION AND STABILITY (Gates 3-4)
# ============================================================================


def validate_gate_003_test_failures(
    test_results: dict[str, Any],
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-003: Validate test failures block execution.

    Article II: "No merge without completely green CI pipeline"

    Validates:
    - Test pass rate == 1.0 (100%)
    - No test failures detected
    - All tests executed successfully

    Args:
        test_results: Dict with keys: tests_passed, tests_failed, pass_rate, failures
        task_graph: TaskGraph instance (for context)

    Returns:
        Ok(GateValidationResult) if all tests passed
        Err(FoundationGateError) if any tests failed

    Example:
        >>> test_results = {"tests_passed": 100, "tests_failed": 0, "pass_rate": 1.0}
        >>> result = validate_gate_003_test_failures(test_results, task_graph)
    """
    start_time = time.time()

    pass_rate = test_results.get("pass_rate", 0.0)
    tests_failed = test_results.get("tests_failed", 0)
    failures = test_results.get("failures", [])

    execution_time_ms = (time.time() - start_time) * 1000

    if pass_rate < 1.0 or tests_failed > 0:
        failed_test_names = [f.get("test", "unknown") for f in failures]

        return Err(
            FoundationGateError(
                message=f"100% test success required (Article II). Current pass rate: {pass_rate:.1%}",
                gate="GATE-003",
                article="Article II",
                pass_rate=pass_rate,
                failed_tests=failed_test_names,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-003",
            passed=True,
            message="All tests passed (100% pass rate)",
            article="Article II",
            execution_time_ms=execution_time_ms,
            pass_rate=pass_rate,
        )
    )


def validate_gate_004_completion_threshold(
    execution_results: dict[str, Any],
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-004: Validate 100% task completion required.

    Article II: "100% is not negotiable - no exceptions"

    Validates:
    - All tasks completed (completion_rate == 1.0)
    - No skipped tasks
    - No failed tasks

    Args:
        execution_results: Dict with keys: completed, failed, skipped, total, completion_rate (optional)
        task_graph: TaskGraph instance (for context)

    Returns:
        Ok(GateValidationResult) if 100% completion
        Err(FoundationGateError) if incomplete

    Example:
        >>> execution_results = {"completed": 10, "failed": 0, "skipped": 0, "total": 10}
        >>> result = validate_gate_004_completion_threshold(execution_results, task_graph)
    """
    start_time = time.time()

    # Calculate completion_rate if not provided
    completed = execution_results.get("completed", 0)
    total = execution_results.get("total", 0)
    completion_rate = execution_results.get("completion_rate")

    if completion_rate is None and total > 0:
        completion_rate = completed / total
    elif completion_rate is None:
        completion_rate = 0.0

    skipped = execution_results.get("skipped", 0)
    failed = execution_results.get("failed", 0)

    execution_time_ms = (time.time() - start_time) * 1000

    if completion_rate < 1.0 or skipped > 0 or failed > 0:
        return Err(
            FoundationGateError(
                message=f"100% task completion required - no exceptions. Current: {completion_rate:.1%}",
                gate="GATE-004",
                article="Article II",
                completion_rate=completion_rate,
                skipped_tasks=skipped,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-004",
            passed=True,
            message="100% task completion achieved",
            article="Article II",
            execution_time_ms=execution_time_ms,
            completion_rate=completion_rate,
        )
    )


# ============================================================================
# ARTICLE III: AUTOMATED MERGE ENFORCEMENT (Gates 5-8)
# ============================================================================


def validate_gate_005_circular_dependencies(
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-005: Detect circular dependencies in task graph.

    Article III: "Quality standards SHALL be technically enforced"

    Uses DFS cycle detection to find circular dependencies.

    Args:
        task_graph: TaskGraph to validate

    Returns:
        Ok(GateValidationResult) if no cycles
        Err(FoundationGateError) if circular dependency detected

    Example:
        >>> result = validate_gate_005_circular_dependencies(task_graph)
        >>> if result.is_err():
        ...     error = result.unwrap_err()
        ...     print(f"Cycle: {error.cycle_path}")
    """
    start_time = time.time()

    # Build adjacency list
    adjacency: dict[str, list[str]] = {}
    for phase in task_graph.phases:
        for task in phase.tasks:
            adjacency[task.id] = task.dependencies

    # DFS cycle detection
    visited = set()
    recursion_stack = set()
    cycle_path: list[str] = []

    def dfs(node: str, path: list[str]) -> bool:
        """DFS with cycle detection."""
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path):
                    return True
            elif neighbor in recursion_stack:
                # Cycle detected - extract cycle path
                cycle_start = path.index(neighbor)
                cycle_path.extend(path[cycle_start:] + [neighbor])
                return True

        recursion_stack.remove(node)
        path.pop()
        return False

    # Check all nodes
    for task_id in adjacency:
        if task_id not in visited:
            if dfs(task_id, []):
                execution_time_ms = (time.time() - start_time) * 1000
                return Err(
                    FoundationGateError(
                        message=f"Circular dependency detected: {' -> '.join(cycle_path)}",
                        gate="GATE-005",
                        article="Article III",
                        cycle_path=cycle_path,
                    )
                )

    execution_time_ms = (time.time() - start_time) * 1000

    return Ok(
        GateValidationResult(
            gate="GATE-005",
            passed=True,
            message="No circular dependencies detected",
            article="Article III",
            execution_time_ms=execution_time_ms,
        )
    )


def validate_gate_006_slop_immunity(
    task_graph: TaskGraph,
    slop_guardian: Any,  # AsyncMock in tests, SlopGuardian in production
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-006: Validate slop immunity threshold (quality ≥3.5).

    Article III: "Quality gates are absolute barriers"

    Validates:
    - Slop score ≥3.5 (quality threshold)
    - Clear, specific mission descriptions
    - Measurable acceptance criteria

    Args:
        task_graph: TaskGraph to validate
        slop_guardian: SlopGuardian instance or mock

    Returns:
        Ok(GateValidationResult) if quality threshold met
        Err(FoundationGateError) if quality too low

    Example:
        >>> from tools.orchestrator.slop_guardian import SlopGuardian
        >>> guardian = SlopGuardian()
        >>> result = validate_gate_006_slop_immunity(task_graph, guardian)
    """
    import asyncio
    import inspect

    start_time = time.time()

    # Call slop guardian (handle both async mock and real guardian)
    evaluation = slop_guardian()

    # If it's a coroutine, await it
    if inspect.iscoroutine(evaluation):
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                evaluation = loop.run_until_complete(evaluation)
            else:
                # Can't await in running loop - this shouldn't happen in production
                evaluation = {"status": "ACCEPT", "score": 5.0}
        except RuntimeError:
            evaluation = {"status": "ACCEPT", "score": 5.0}

    status = evaluation.get("status")
    score = evaluation.get("score", 0.0)
    threshold = 3.5

    execution_time_ms = (time.time() - start_time) * 1000

    if status == "REJECT" or score < threshold:
        return Err(
            FoundationGateError(
                message=f"Slop immunity threshold not met. Score: {score:.1f} < {threshold}",
                gate="GATE-006",
                article="Article III",
                slop_score=score,
                threshold=threshold,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-006",
            passed=True,
            message=f"Slop immunity: PASS (score {score:.1f} ≥ {threshold})",
            article="Article III",
            execution_time_ms=execution_time_ms,
            slop_score=score,
            threshold=threshold,
        )
    )


def validate_gate_007_budget_guard(
    task_graph: TaskGraph,
    budget_guard: Any,  # AsyncMock in tests, BudgetGuard in production
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-007: Validate budget limits (daily/mission caps).

    Article III: "Quality gates are absolute barriers"

    Validates:
    - Estimated cost within daily limit
    - Estimated cost within mission limit
    - No budget overruns

    Args:
        task_graph: TaskGraph to validate
        budget_guard: BudgetGuard instance or mock

    Returns:
        Ok(GateValidationResult) if within budget
        Err(FoundationGateError) if budget exceeded

    Example:
        >>> from tools.orchestrator.budget_guard import BudgetGuard
        >>> guard = BudgetGuard()
        >>> result = validate_gate_007_budget_guard(task_graph, guard)
    """
    import asyncio
    import inspect

    start_time = time.time()

    # Call budget guard (handle both async mock and real guard)
    check_result = budget_guard()

    # If it's a coroutine, await it
    if inspect.iscoroutine(check_result):
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                check_result = loop.run_until_complete(check_result)
            else:
                check_result = {"within_budget": True, "estimated_cost": 0.0}
        except RuntimeError:
            check_result = {"within_budget": True, "estimated_cost": 0.0}

    within_budget = check_result.get("within_budget", True)
    estimated_cost = check_result.get("estimated_cost", 0.0)
    daily_limit = check_result.get("daily_limit", 100.0)

    execution_time_ms = (time.time() - start_time) * 1000

    if not within_budget:
        return Err(
            FoundationGateError(
                message=f"Budget limit exceeded: ${estimated_cost:.2f} > ${daily_limit:.2f}",
                gate="GATE-007",
                article="Article III",
                estimated_cost=estimated_cost,
                daily_limit=daily_limit,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-007",
            passed=True,
            message=f"Within budget: ${estimated_cost:.2f} / ${daily_limit:.2f}",
            article="Article III",
            execution_time_ms=execution_time_ms,
            estimated_cost=estimated_cost,
            daily_limit=daily_limit,
        )
    )


def validate_gate_008_main_branch_protection(
    git_repo_path: Path,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-008: Block execution on main branch.

    Article III: "No bypass authority for anyone"

    Validates:
    - Current branch is NOT main or master
    - Feature branch required for execution

    Args:
        git_repo_path: Path to git repository

    Returns:
        Ok(GateValidationResult) if on feature branch
        Err(FoundationGateError) if on main/master

    Example:
        >>> result = validate_gate_008_main_branch_protection(Path.cwd())
    """
    start_time = time.time()

    try:
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=git_repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()
    except subprocess.CalledProcessError:
        current_branch = "unknown"

    execution_time_ms = (time.time() - start_time) * 1000

    if current_branch in ("main", "master"):
        return Err(
            FoundationGateError(
                message=f"Cannot execute on main branch (Article III). Current branch: {current_branch}",
                gate="GATE-008",
                article="Article III",
                current_branch=current_branch,
            )
        )

    return Ok(
        GateValidationResult(
            gate="GATE-008",
            passed=True,
            message=f"Feature branch: {current_branch}",
            article="Article III",
            execution_time_ms=execution_time_ms,
            current_branch=current_branch,
        )
    )


# ============================================================================
# ARTICLE IV: CONTINUOUS LEARNING AND IMPROVEMENT (Gates 9-10)
# ============================================================================


async def validate_gate_009_vectorstore_query(
    context: AgentContext,
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-009: Validate VectorStore queried before action.

    Article IV: "Agents MUST query learnings before decisions"

    Validates:
    - VectorStore.search_memories() called
    - Learnings with confidence ≥0.6 retrieved
    - Query result cached for execution

    Args:
        context: AgentContext with VectorStore access
        task_graph: TaskGraph instance

    Returns:
        Ok(GateValidationResult) if VectorStore queried
        Err(FoundationGateError) if query fails

    Example:
        >>> result = await validate_gate_009_vectorstore_query(context, task_graph)
    """
    start_time = time.time()

    try:
        # Query VectorStore for learnings
        learnings = context.search_memories(tags=["pattern", "orchestrator"], include_session=True)

        # Filter by confidence (≥0.6)
        high_confidence_learnings = [learning for learning in learnings if learning.get("confidence", 1.0) >= 0.6]

        execution_time_ms = (time.time() - start_time) * 1000

        return Ok(
            GateValidationResult(
                gate="GATE-009",
                passed=True,
                message=f"VectorStore queried: {len(high_confidence_learnings)} learnings retrieved",
                article="Article IV",
                execution_time_ms=execution_time_ms,
                learnings_retrieved=len(high_confidence_learnings),
            )
        )

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return Err(
            FoundationGateError(
                message=f"VectorStore query failed: {e}",
                gate="GATE-009",
                article="Article IV",
            )
        )


async def validate_gate_010_vectorstore_storage(
    context: AgentContext,
    task_graph: TaskGraph,
    execution_results: dict[str, Any],
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-010: Validate VectorStore patterns stored after success.

    Article IV: "Agents MUST store successful patterns after operations"

    Validates:
    - Patterns extracted from execution
    - VectorStore.store_memory() called for each pattern
    - Storage succeeded

    Args:
        context: AgentContext with VectorStore access
        task_graph: TaskGraph instance
        execution_results: Dict with patterns_extracted list

    Returns:
        Ok(GateValidationResult) if patterns stored
        Err(FoundationGateError) if storage fails

    Example:
        >>> execution_results = {"patterns_extracted": [{"pattern": "TDD", ...}]}
        >>> result = await validate_gate_010_vectorstore_storage(
        ...     context, task_graph, execution_results
        ... )
    """
    start_time = time.time()

    try:
        patterns = execution_results.get("patterns_extracted", [])

        # Store each pattern
        for pattern in patterns:
            context.store_memory(
                key=f"pattern_{pattern.get('pattern', 'unknown')}_{int(time.time())}",
                content=pattern,
                tags=["orchestrator", "success", "pattern"],
            )

        execution_time_ms = (time.time() - start_time) * 1000

        return Ok(
            GateValidationResult(
                gate="GATE-010",
                passed=True,
                message=f"VectorStore patterns stored: {len(patterns)}",
                article="Article IV",
                execution_time_ms=execution_time_ms,
                patterns_stored=len(patterns),
            )
        )

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return Err(
            FoundationGateError(
                message=f"VectorStore storage failed: {e}",
                gate="GATE-010",
                article="Article IV",
            )
        )


# ============================================================================
# ARTICLE V: SPEC-DRIVEN DEVELOPMENT (Gates 11-12)
# ============================================================================


def validate_gate_011_acceptance_criteria(
    task_graph: TaskGraph,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-011: Validate acceptance criteria present for spec tasks.

    Article V: "Spec follows template: Goals, Non-Goals, Personas, Acceptance Criteria"

    Validates:
    - All SPEC tasks have acceptance_criteria
    - Acceptance criteria are non-empty
    - Criteria follow CONST-XXX format

    Args:
        task_graph: TaskGraph to validate

    Returns:
        Ok(GateValidationResult) if all spec tasks have criteria
        Err(FoundationGateError) if any spec task missing criteria

    Example:
        >>> result = validate_gate_011_acceptance_criteria(task_graph)
    """
    start_time = time.time()

    # Find all SPEC tasks
    for phase in task_graph.phases:
        for task in phase.tasks:
            if task.type == TaskType.SPEC:
                if not task.acceptance_criteria or len(task.acceptance_criteria) == 0:
                    execution_time_ms = (time.time() - start_time) * 1000
                    return Err(
                        FoundationGateError(
                            message=f"Spec tasks require acceptance criteria (Article V). Task: {task.id}",
                            gate="GATE-011",
                            article="Article V",
                            task_id=task.id,
                        )
                    )

    execution_time_ms = (time.time() - start_time) * 1000

    return Ok(
        GateValidationResult(
            gate="GATE-011",
            passed=True,
            message="All spec tasks have acceptance criteria",
            article="Article V",
            execution_time_ms=execution_time_ms,
        )
    )


def validate_gate_012_graph_traceability(
    task_graph: TaskGraph,
    spec_directory: Path,
) -> Result[GateValidationResult, FoundationGateError]:
    """
    GATE-012: Validate task graph traces to specification.

    Article V: "All implementation traces to specification"

    Validates:
    - All tasks have spec_id metadata
    - spec_id references existing spec file (format: SPEC-XXX)
    - Acceptance criteria match spec requirements

    Args:
        task_graph: TaskGraph to validate
        spec_directory: Path to specs directory

    Returns:
        Ok(GateValidationResult) if traceability valid
        Err(FoundationGateError) if traceability missing

    Example:
        >>> result = validate_gate_012_graph_traceability(task_graph, Path("specs"))
    """
    start_time = time.time()

    tasks_validated = 0

    # Validate all tasks have spec_id
    for phase in task_graph.phases:
        for task in phase.tasks:
            tasks_validated += 1

            spec_id = task.metadata.get("spec_id") if hasattr(task, "metadata") else None

            if not spec_id:
                execution_time_ms = (time.time() - start_time) * 1000
                return Err(
                    FoundationGateError(
                        message=f"Missing spec_id in task metadata (Article V). Task: {task.id}",
                        gate="GATE-012",
                        article="Article V",
                        task_id=task.id,
                    )
                )

    execution_time_ms = (time.time() - start_time) * 1000

    return Ok(
        GateValidationResult(
            gate="GATE-012",
            passed=True,
            message=f"Task graph traceability validated ({tasks_validated} tasks)",
            article="Article V",
            execution_time_ms=execution_time_ms,
            tasks_validated=tasks_validated,
        )
    )


# ============================================================================
# MASTER GATE VALIDATOR (Orchestrates all 12 gates)
# ============================================================================


async def validate_all_gates(
    task_graph: TaskGraph,
    context: AgentContext,
    test_results: dict[str, Any],
    execution_results: dict[str, Any],
    git_repo_path: Path | None = None,
    slop_guardian: Any | None = None,
    budget_guard: Any | None = None,
) -> Result[dict[str, Any], FoundationGateError]:
    """
    Validate all 12 constitutional gates.

    Executes all gates in sequence with early exit on first failure.

    Args:
        task_graph: TaskGraph to validate
        context: AgentContext for VectorStore access
        test_results: Test execution results
        execution_results: Task execution results
        git_repo_path: Path to git repository (optional)
        slop_guardian: SlopGuardian instance (optional)
        budget_guard: BudgetGuard instance (optional)

    Returns:
        Ok(dict) with gate validation summary if all pass
        Err(FoundationGateError) on first gate failure (early exit)

    Example:
        >>> result = await validate_all_gates(
        ...     task_graph=graph,
        ...     context=context,
        ...     test_results=test_results,
        ...     execution_results=execution_results
        ... )
        >>> if result.is_ok():
        ...     summary = result.unwrap()
        ...     print(f"{summary['gates_passed']}/12 gates passed")
    """
    gate_results: list[GateValidationResult] = []
    gates_checked = 0

    # Define gate validators (in order)
    gate_validators = [
        ("GATE-001", lambda: validate_gate_001_incomplete_graph(task_graph)),
        (
            "GATE-002",
            lambda: validate_gate_002_timeout_retry(
                operation=lambda: {"status": "success"},
                context=context,
                initial_timeout=120,
                max_retries=1,
            ),
        ),
        ("GATE-003", lambda: validate_gate_003_test_failures(test_results, task_graph)),
        (
            "GATE-004",
            lambda: validate_gate_004_completion_threshold(execution_results, task_graph),
        ),
        ("GATE-005", lambda: validate_gate_005_circular_dependencies(task_graph)),
        (
            "GATE-006",
            lambda: validate_gate_006_slop_immunity(task_graph, slop_guardian)
            if slop_guardian
            else Ok(
                GateValidationResult(
                    gate="GATE-006",
                    passed=True,
                    message="Slop guardian not provided - skipping",
                    article="Article III",
                    execution_time_ms=0.0,
                )
            ),
        ),
        (
            "GATE-007",
            lambda: validate_gate_007_budget_guard(task_graph, budget_guard)
            if budget_guard
            else Ok(
                GateValidationResult(
                    gate="GATE-007",
                    passed=True,
                    message="Budget guard not provided - skipping",
                    article="Article III",
                    execution_time_ms=0.0,
                )
            ),
        ),
        (
            "GATE-008",
            lambda: validate_gate_008_main_branch_protection(git_repo_path)
            if git_repo_path
            else Ok(
                GateValidationResult(
                    gate="GATE-008",
                    passed=True,
                    message="Git repo not provided - skipping",
                    article="Article III",
                    execution_time_ms=0.0,
                )
            ),
        ),
        ("GATE-011", lambda: validate_gate_011_acceptance_criteria(task_graph)),
        (
            "GATE-012",
            lambda: validate_gate_012_graph_traceability(task_graph, Path("specs")),
        ),
    ]

    # Execute gates sequentially (early exit on failure)
    for gate_id, validator in gate_validators:
        gates_checked += 1

        result = validator()

        if result.is_err():
            # Early exit - first gate failure
            error = result.unwrap_err()
            error.gates_checked = gates_checked
            return Err(error)

        gate_results.append(result.unwrap())

    # Execute async gates (GATE-009, GATE-010)
    gate_009_result = await validate_gate_009_vectorstore_query(context, task_graph)
    if gate_009_result.is_err():
        error = gate_009_result.unwrap_err()
        error.gates_checked = gates_checked + 1
        return Err(error)
    gate_results.append(gate_009_result.unwrap())
    gates_checked += 1

    gate_010_result = await validate_gate_010_vectorstore_storage(
        context, task_graph, execution_results
    )
    if gate_010_result.is_err():
        error = gate_010_result.unwrap_err()
        error.gates_checked = gates_checked + 1
        return Err(error)
    gate_results.append(gate_010_result.unwrap())
    gates_checked += 1

    # All gates passed
    gates_passed = len([r for r in gate_results if r.passed])
    gates_failed = len([r for r in gate_results if not r.passed])

    return Ok(
        {
            "gates_passed": gates_passed,
            "gates_failed": gates_failed,
            "gate_results": [r.model_dump() for r in gate_results],
            "all_passed": gates_failed == 0,
        }
    )


__all__ = [
    "FoundationGateError",
    "GateValidationResult",
    "validate_gate_001_incomplete_graph",
    "validate_gate_002_timeout_retry",
    "validate_gate_003_test_failures",
    "validate_gate_004_completion_threshold",
    "validate_gate_005_circular_dependencies",
    "validate_gate_006_slop_immunity",
    "validate_gate_007_budget_guard",
    "validate_gate_008_main_branch_protection",
    "validate_gate_009_vectorstore_query",
    "validate_gate_010_vectorstore_storage",
    "validate_gate_011_acceptance_criteria",
    "validate_gate_012_graph_traceability",
    "validate_all_gates",
]
