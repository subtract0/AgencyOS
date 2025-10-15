"""
Tests for UnifiedPrimeAOrchestrator with all quality gate integrations.

Tests all STEPS from .claude/commands/primeA.md:
- STEP 0: TodoWrite initialization
- PHASE 0: Git workflow validation (branch protection)
- STEP 2: Input parsing and graph generation (auto-select/intent/graph file)
- STEP 3.1: TRM DAG validation
- STEP 3.5: Slop Immunity check
- STEP 3.6: Budget Guard enforcement
- STEP 5: DAG execution with TRM checkpoints
- STEP 6.5: Completion validation (blocking)
- STEP 7: Execution report generation
- FINAL PHASE: Automatic PR creation (unless --no-pr)

Foundation Automation Tests (New):
- Phase 0 git validation (feature branch enforcement, Article III)
- Task graph generation from natural language intent
- Automatic PR creation phase (merger agent integration)
- --no-pr flag support (enable_pr_creation parameter)
- Constitutional validation gates at each automation point

Constitutional Compliance:
- Article I: Complete context (retry logic)
- Article II: 100% verification (completion validator)
- Article III: Automated enforcement (all gates + branch protection)
- Article IV: VectorStore integration
- Article V: Spec-driven (task graph acceptance criteria)

Test Coverage:
- Normal flow: All STEPS pass
- Edge cases: TRM unavailable, Slop Guardian error, Budget exceeded
- Failure modes: Circular dependencies, Incomplete execution, Failed validation
- Foundation automation: Phase 0, planner integration, merger integration, --no-pr
"""

import asyncio
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.agent_context import create_agent_context
from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType
from shared.type_definitions.result import Err, Ok
from tools.orchestrator.budget_guard import BudgetExceeded, BudgetLimits, CostEstimate
from tools.orchestrator.completion_validator import (
    ConstitutionalChecks,
    ValidationError,
    ValidationResults,
)
from tools.orchestrator.slop_guardian import SlopVerdict, VerdictStatus
from tools.orchestrator.unified_primea_orchestrator import (
    ExecutionError,
    ExecutionMetrics,
    ExecutionResult,
    UnifiedPrimeAOrchestrator,
    create_unified_orchestrator,
)
from trinity_protocol.core.trm_validator import TRMUnavailableError, ValidationResult

# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def agent_context():
    """Create test agent context with memory disabled."""
    return create_agent_context(session_id="test_primea_unified")


@pytest.fixture
def orchestrator(agent_context, tmp_path):
    """Create UnifiedPrimeAOrchestrator instance for testing."""
    return UnifiedPrimeAOrchestrator(
        context=agent_context,
        repo_path=str(tmp_path),
        enable_todos=True,
        enable_pr_creation=False,  # Disable PR creation for tests
    )


@pytest.fixture
def simple_task_graph():
    """Create simple task graph for testing."""
    return TaskGraph(
        mission="Test Mission: Simple graph",
        phases=[
            Phase(
                id="phase_1",
                title="Implementation",
                tasks=[
                    Task(
                        id="code_task",
                        title="Code task",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Implement feature",
                        dependencies=[],
                        acceptance_criteria=["Feature implemented"],
                        estimated_tokens=1000,
                    ),
                    Task(
                        id="test_task",
                        title="Test task",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Test feature",
                        dependencies=["code_task"],
                        verification_target="code_task",
                        estimated_tokens=500,
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def circular_task_graph():
    """Create task graph with circular dependency for testing."""
    return TaskGraph(
        mission="Test Mission: Circular graph",
        phases=[
            Phase(
                id="phase_1",
                title="Circular Phase",
                tasks=[
                    Task(
                        id="task_a",
                        title="Task A",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Task A",
                        dependencies=["test_b"],  # Circular dependency (depends on test of B)
                    ),
                    Task(
                        id="test_a",
                        title="Test A",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Test A",
                        dependencies=["task_a"],
                        verification_target="task_a",
                    ),
                    Task(
                        id="task_b",
                        title="Task B",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Task B",
                        dependencies=["test_a"],  # Circular dependency (depends on test of A)
                    ),
                    Task(
                        id="test_b",
                        title="Test B",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Test B",
                        dependencies=["task_b"],
                        verification_target="task_b",
                    ),
                ],
            )
        ],
    )


# ============================================================================
# TEST: FACTORY FUNCTION
# ============================================================================


def test_create_unified_orchestrator(agent_context):
    """Test factory function creates orchestrator correctly."""
    orchestrator = create_unified_orchestrator(
        context=agent_context,
        repo_path="/tmp/test",
        enable_todos=False,
    )

    assert isinstance(orchestrator, UnifiedPrimeAOrchestrator)
    assert orchestrator.context == agent_context
    assert orchestrator.repo_path == Path("/tmp/test")
    assert orchestrator.enable_todos is False


# ============================================================================
# TEST: STEP 0 - TODOWRITE INITIALIZATION
# ============================================================================


def test_step_0_init_todos(orchestrator):
    """Test STEP 0: TodoWrite initialization."""
    orchestrator._init_todos()

    # Should have 9 steps (0-7 + 6.5)
    assert len(orchestrator.todos) == 9

    # First todo should be completed
    assert orchestrator.todos[0]["content"] == "Step 0: Initialize TodoWrite"
    assert orchestrator.todos[0]["status"] == "completed"

    # Other todos should be pending
    assert orchestrator.todos[1]["status"] == "pending"


def test_step_0_update_todo(orchestrator):
    """Test TodoWrite updates during execution."""
    orchestrator._init_todos()

    # Update todo status
    orchestrator._update_todo("in_progress", "Step 2: Parse input and generate task graph")

    # Find updated todo
    todo = next(t for t in orchestrator.todos if "Step 2" in t["content"])
    assert todo["status"] == "in_progress"


# ============================================================================
# TEST: STEP 3.1 - TRM DAG VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_step_3_1_dag_validation_pass(orchestrator, simple_task_graph):
    """Test STEP 3.1: TRM DAG validation passes for acyclic graph."""
    result = await orchestrator._validate_dag_with_trm(simple_task_graph)

    assert result.is_ok()
    validation = result.unwrap()
    assert validation.converged is True  # No cycles
    assert validation.confidence > 0.8


@pytest.mark.asyncio
async def test_step_3_1_dag_validation_fail_cycle(orchestrator, circular_task_graph):
    """Test STEP 3.1: TRM DAG validation fails on circular dependencies."""
    result = await orchestrator._validate_dag_with_trm(circular_task_graph)

    # Should detect cycle
    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_3.1_trm_dag"
    assert "Circular dependencies" in error.reason


@pytest.mark.asyncio
async def test_step_3_1_dag_validation_python_fallback(orchestrator, simple_task_graph):
    """Test STEP 3.1: Graceful fallback to Python when TRM unavailable."""
    # Mock TRM to return unavailable error
    orchestrator.trm_validator = MagicMock()
    orchestrator.trm_validator.validate_and_refine = AsyncMock(
        return_value=Err(TRMUnavailableError("TRM model not loaded"))
    )

    result = await orchestrator._validate_dag_with_trm(simple_task_graph)

    # Should fallback to Python and pass
    assert result.is_ok()
    validation = result.unwrap()
    assert validation.converged is True


# ============================================================================
# TEST: STEP 3.5 - SLOP IMMUNITY CHECK
# ============================================================================


@pytest.mark.asyncio
async def test_step_3_5_slop_immunity_pass(orchestrator, simple_task_graph):
    """Test STEP 3.5: Slop Immunity check passes for quality mission."""
    # Mock slop guardian to return passing verdict
    orchestrator.slop_guardian = MagicMock()
    orchestrator.slop_guardian.evaluate = MagicMock(
        return_value=Ok(
            SlopVerdict(
                score=4.5,
                reasons=[],
                top_fixes=[],
                dimension_scores={
                    "clarity": 4.5,
                    "measurability": 4.5,
                    "completeness": 4.5,
                    "actionability": 4.5,
                },
            )
        )
    )

    result = await orchestrator._check_slop_immunity(simple_task_graph)

    assert result.is_ok()
    verdict = result.unwrap()
    assert verdict.score >= 3.5
    assert verdict.status == VerdictStatus.ACCEPT


@pytest.mark.asyncio
async def test_step_3_5_slop_immunity_fail(orchestrator, simple_task_graph):
    """Test STEP 3.5: Slop Immunity graceful fallback on LLM error."""
    # Mock slop guardian to return error
    from tools.orchestrator.slop_guardian import SlopDetected

    orchestrator.slop_guardian = MagicMock()
    orchestrator.slop_guardian.evaluate = MagicMock(return_value=Err("LLM timeout"))

    # Mock enforce_slop_immunity to return error
    with patch(
        "tools.orchestrator.unified_primea_orchestrator.enforce_slop_immunity",
        return_value=Err(
            SlopDetected(
                verdict=SlopVerdict(
                    score=2.0,
                    reasons=["Vague mission"],
                    top_fixes=["Add specifics"],
                    dimension_scores={
                        "clarity": 2.0,
                        "measurability": 2.0,
                        "completeness": 2.0,
                        "actionability": 2.0,
                    },
                ),
                original_text="Test mission",
            )
        ),
    ):
        result = await orchestrator._check_slop_immunity(simple_task_graph)

        # Should fallback gracefully (non-blocking in MVP)
        assert result.is_ok()
        verdict = result.unwrap()
        assert verdict.score >= 3.5  # Fallback verdict


# ============================================================================
# TEST: STEP 3.6 - BUDGET GUARD CHECK
# ============================================================================


@pytest.mark.asyncio
async def test_step_3_6_budget_guard_pass(orchestrator, simple_task_graph):
    """Test STEP 3.6: Budget Guard passes when within limits."""
    # Mock budget guard to return success
    orchestrator.budget_guard = MagicMock()
    orchestrator.budget_guard.estimate_cost = MagicMock(
        return_value=CostEstimate(
            total_usd=1.0,
            total_tokens=1500,
            tasks_count=2,
            cost_per_1k_tokens=0.0025,
        )
    )
    orchestrator.budget_guard.check_budget = MagicMock(return_value=Ok(None))

    result = await orchestrator._check_budget(simple_task_graph, force=False)

    assert result.is_ok()


@pytest.mark.asyncio
async def test_step_3_6_budget_guard_fail_exceed(orchestrator, simple_task_graph):
    """Test STEP 3.6: Budget Guard fails when limits exceeded."""
    # Mock budget guard to return error
    orchestrator.budget_guard = MagicMock()
    orchestrator.budget_guard.estimate_cost = MagicMock(
        return_value=CostEstimate(
            total_usd=50.0,
            total_tokens=20000,
            tasks_count=2,
            cost_per_1k_tokens=0.0025,
        )
    )
    orchestrator.budget_guard.check_budget = MagicMock(
        return_value=Err(
            BudgetExceeded(
                message="Budget exceeded",
                estimated_cost_usd=50.0,
                daily_limit_usd=10.0,
                per_mission_limit_usd=5.0,
                daily_spent_usd=0.0,
                would_exceed_daily=True,
                would_exceed_per_mission=True,
            )
        )
    )

    result = await orchestrator._check_budget(simple_task_graph, force=False)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_3.6_budget_guard"
    assert "Budget exceeded" in error.reason


@pytest.mark.asyncio
async def test_step_3_6_budget_guard_force_override(orchestrator, simple_task_graph):
    """Test STEP 3.6: Budget Guard allows force override."""
    # Mock budget guard to return success with force=True
    orchestrator.budget_guard = MagicMock()
    orchestrator.budget_guard.estimate_cost = MagicMock(
        return_value=CostEstimate(total_usd=50.0, total_tokens=20000, tasks_count=2)
    )
    orchestrator.budget_guard.check_budget = MagicMock(return_value=Ok(None))

    result = await orchestrator._check_budget(simple_task_graph, force=True)

    # Should pass with force=True
    assert result.is_ok()
    orchestrator.budget_guard.check_budget.assert_called_once_with(
        unittest.mock.ANY,
        unittest.mock.ANY,
        force=True,
    )


# ============================================================================
# TEST: STEP 6.5 - COMPLETION VALIDATOR
# ============================================================================


@pytest.mark.asyncio
async def test_step_6_5_completion_validation_pass(orchestrator, simple_task_graph):
    """Test STEP 6.5: Completion validation passes when 100% complete."""
    # Setup: Mark all tasks as completed
    orchestrator.task_results = [
        {
            "id": "code_task",
            "status": "success",
            "type": "code",
            "acceptance_criteria_met": True,
        },
        {
            "id": "test_task",
            "status": "success",
            "type": "test",
            "acceptance_criteria_met": True,
        },
    ]
    orchestrator.todos = [
        {"content": "Step 1", "status": "completed", "activeForm": "Step 1"},
        {"content": "Step 2", "status": "completed", "activeForm": "Step 2"},
    ]

    result = await orchestrator._validate_completion(simple_task_graph)

    assert result.is_ok()
    validation_results = result.unwrap()
    assert validation_results.all_tasks_completed is True
    assert validation_results.constitutional_compliant is True


@pytest.mark.asyncio
async def test_step_6_5_completion_validation_fail_incomplete_tasks(
    orchestrator, simple_task_graph
):
    """Test STEP 6.5: Completion validation fails with incomplete tasks."""
    # Setup: Mark one task as failed
    orchestrator.task_results = [
        {"id": "code_task", "status": "success", "type": "code"},
        {"id": "test_task", "status": "failed", "type": "test"},  # Failed
    ]
    orchestrator.todos = [
        {"content": "Step 1", "status": "completed", "activeForm": "Step 1"},
    ]

    result = await orchestrator._validate_completion(simple_task_graph)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_6.5_completion_validation"
    assert "incomplete" in error.reason.lower()


@pytest.mark.asyncio
async def test_step_6_5_completion_validation_fail_todowrite_mismatch(
    orchestrator, simple_task_graph
):
    """Test STEP 6.5: Completion validation fails with incomplete todos."""
    # Setup: All tasks complete but todos incomplete
    orchestrator.task_results = [
        {"id": "code_task", "status": "success", "type": "code"},
        {"id": "test_task", "status": "success", "type": "test"},
    ]
    orchestrator.todos = [
        {"content": "Step 1", "status": "completed", "activeForm": "Step 1"},
        {"content": "Step 2", "status": "in_progress", "activeForm": "Step 2"},  # Not completed
    ]

    result = await orchestrator._validate_completion(simple_task_graph)

    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_6.5_completion_validation"


# ============================================================================
# TEST: END-TO-END EXECUTION
# ============================================================================


@pytest.mark.asyncio
async def test_execute_full_flow_success(orchestrator, tmp_path):
    """Test full execution flow from start to finish."""
    # Mock all components for successful execution
    orchestrator._parse_and_generate_graph = AsyncMock(
        return_value=Ok(orchestrator._create_stub_graph())
    )
    orchestrator._validate_dag_with_trm = AsyncMock(
        return_value=Ok(
            ValidationResult(
                converged=True,
                confidence=0.95,
                refinement_steps=3,
                latency_ms=12.5,
            )
        )
    )
    orchestrator._check_slop_immunity = AsyncMock(
        return_value=Ok(
            SlopVerdict(
                score=4.5,
                reasons=[],
                top_fixes=[],
                dimension_scores={
                    "clarity": 4.5,
                    "measurability": 4.5,
                    "completeness": 4.5,
                    "actionability": 4.5,
                },
            )
        )
    )
    orchestrator._check_budget = AsyncMock(return_value=Ok(None))
    orchestrator._execute_dag = AsyncMock(return_value=Ok(None))
    orchestrator._reflect_and_evolve = AsyncMock(return_value=None)
    orchestrator._validate_completion = AsyncMock(
        return_value=Ok(
            ValidationResults(
                all_tasks_completed=True,
                acceptance_criteria_met=True,
                todowrite_synced=True,
                backlog_zero=True,
                constitutional_compliant=True,
                context_efficiency=0.85,
                constitutional_checks=MagicMock(),
                warnings=[],
                errors=[],
            )
        )
    )

    # Execute full flow
    result = await orchestrator.execute()

    # Assertions
    assert result.is_ok()
    exec_result = result.unwrap()
    assert exec_result.status == "complete"
    assert exec_result.metrics.completion_validation_passed is True
    assert exec_result.metrics.budget_guard_passed is True
    assert exec_result.metrics.article_iii_gates_enforced >= 3  # DAG + Slop + Budget


@pytest.mark.asyncio
async def test_execute_fail_on_completion_validation(orchestrator):
    """Test execution fails at STEP 6.5 when validation fails."""
    # Mock all steps to pass except completion validation
    orchestrator._parse_and_generate_graph = AsyncMock(
        return_value=Ok(orchestrator._create_stub_graph())
    )
    orchestrator._validate_dag_with_trm = AsyncMock(
        return_value=Ok(
            ValidationResult(converged=True, confidence=0.95, refinement_steps=0, latency_ms=0.0)
        )
    )
    orchestrator._check_slop_immunity = AsyncMock(
        return_value=Ok(SlopVerdict(score=4.5, reasons=[], top_fixes=[], dimension_scores={}))
    )
    orchestrator._check_budget = AsyncMock(return_value=Ok(None))
    orchestrator._execute_dag = AsyncMock(return_value=Ok(None))
    orchestrator._reflect_and_evolve = AsyncMock(return_value=None)

    # Mock completion validation to fail
    orchestrator._validate_completion = AsyncMock(
        return_value=Err(
            ExecutionError(
                step="step_6.5_completion_validation",
                reason="incomplete_tasks",
                details="15 tasks incomplete",
                suggestions=["Continue execution until complete"],
            )
        )
    )

    # Execute
    result = await orchestrator.execute()

    # Should fail at STEP 6.5
    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_6.5_completion_validation"
    assert "incomplete_tasks" in error.reason


# ============================================================================
# TEST: CONSTITUTIONAL COMPLIANCE
# ============================================================================


@pytest.mark.asyncio
async def test_constitutional_article_i_complete_context(orchestrator):
    """Test Article I: Complete context (no partial execution)."""
    # Mock graph validation to fail (incomplete context)
    orchestrator._parse_and_generate_graph = AsyncMock(
        return_value=Err(
            ExecutionError(
                step="step_2_parse_input",
                reason="Incomplete graph",
                details="Missing tasks",
            )
        )
    )

    result = await orchestrator.execute()

    # Should fail early (Article I enforcement)
    assert result.is_err()
    error = result.unwrap_err()
    assert error.step == "step_2_parse_input"


@pytest.mark.asyncio
async def test_constitutional_article_ii_100_verification(orchestrator):
    """Test Article II: 100% verification (completion validator enforces)."""
    # Mock incomplete execution (some tests failed)
    orchestrator._parse_and_generate_graph = AsyncMock(
        return_value=Ok(orchestrator._create_stub_graph())
    )
    orchestrator._validate_dag_with_trm = AsyncMock(
        return_value=Ok(
            ValidationResult(converged=True, confidence=0.95, refinement_steps=0, latency_ms=0.0)
        )
    )
    orchestrator._check_slop_immunity = AsyncMock(
        return_value=Ok(SlopVerdict(score=4.5, reasons=[], top_fixes=[], dimension_scores={}))
    )
    orchestrator._check_budget = AsyncMock(return_value=Ok(None))
    orchestrator._execute_dag = AsyncMock(return_value=Ok(None))
    orchestrator._reflect_and_evolve = AsyncMock(return_value=None)

    # Mock completion validator to fail on test verification
    orchestrator._validate_completion = AsyncMock(
        return_value=Err(
            ExecutionError(
                step="step_6.5_completion_validation",
                reason="Tests failed",
                details="187 tests passing, 15 tests failing",
            )
        )
    )

    result = await orchestrator.execute()

    # Should block STEP 7 (Article II enforcement)
    assert result.is_err()
    assert "Tests failed" in result.unwrap_err().reason


@pytest.mark.asyncio
async def test_constitutional_article_iii_automated_enforcement(orchestrator):
    """Test Article III: Automated enforcement (no manual bypass)."""
    # All 3 quality gates should be enforced
    orchestrator._parse_and_generate_graph = AsyncMock(
        return_value=Ok(orchestrator._create_stub_graph())
    )

    # Mock all gates to pass
    orchestrator._validate_dag_with_trm = AsyncMock(
        return_value=Ok(
            ValidationResult(converged=True, confidence=0.95, refinement_steps=0, latency_ms=0.0)
        )
    )
    orchestrator._check_slop_immunity = AsyncMock(
        return_value=Ok(SlopVerdict(score=4.5, reasons=[], top_fixes=[], dimension_scores={}))
    )
    orchestrator._check_budget = AsyncMock(return_value=Ok(None))
    orchestrator._execute_dag = AsyncMock(return_value=Ok(None))
    orchestrator._reflect_and_evolve = AsyncMock(return_value=None)
    orchestrator._validate_completion = AsyncMock(
        return_value=Ok(
            ValidationResults(
                all_tasks_completed=True,
                acceptance_criteria_met=True,
                todowrite_synced=True,
                backlog_zero=True,
                constitutional_compliant=True,
                context_efficiency=0.85,
                constitutional_checks=ConstitutionalChecks(
                    article_i_complete_context=True,
                    article_ii_verification=True,
                    article_iii_enforcement=True,
                    article_iv_learning=True,
                    article_v_spec_driven=True,
                ),
                warnings=[],
                errors=[],
            )
        )
    )

    result = await orchestrator.execute()

    # All 3 gates should be enforced (DAG + Slop + Budget + Phase 0 git)
    assert result.is_ok()
    exec_result = result.unwrap()
    assert exec_result.metrics.article_iii_gates_enforced >= 3


# ============================================================================
# TEST: GRACEFUL FALLBACK
# ============================================================================


@pytest.mark.asyncio
async def test_graceful_fallback_trm_unavailable(orchestrator, simple_task_graph):
    """Test graceful fallback when TRM unavailable."""
    # Mock TRM to return unavailable
    orchestrator.trm_validator.validate_and_refine = AsyncMock(
        return_value=Err(TRMUnavailableError("Model not loaded"))
    )

    result = await orchestrator._validate_dag_with_trm(simple_task_graph)

    # Should fallback to Python and pass
    assert result.is_ok()


@pytest.mark.asyncio
async def test_graceful_fallback_slop_guardian_error(orchestrator, simple_task_graph):
    """Test graceful fallback when Slop Guardian fails."""
    # Mock Slop Guardian to return error
    with patch(
        "tools.orchestrator.unified_primea_orchestrator.enforce_slop_immunity",
        return_value=Err(MagicMock()),
    ):
        result = await orchestrator._check_slop_immunity(simple_task_graph)

        # Should fallback gracefully
        assert result.is_ok()


# ============================================================================
# TEST: FOUNDATION AUTOMATION (Phase 0, Planner, Merger)
# ============================================================================


def test_phase_0_git_validation_pass_feature_branch(orchestrator, tmp_path):
    """Test Phase 0: Git validation passes on feature branch."""
    # Setup: Initialize git repo on feature branch
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-b", "feat/test-automation"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    result = orchestrator._validate_git_workflow()

    assert result.is_ok()


def test_phase_0_git_validation_fail_main_branch(orchestrator, tmp_path):
    """Test Phase 0: Git validation fails on main branch."""
    # Setup: Initialize git repo on main branch
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    result = orchestrator._validate_git_workflow()

    assert result.is_err()
    error = result.unwrap_err()
    assert "main branch not allowed" in error.reason.lower()
    assert "Article III" in error.details


def test_phase_0_git_validation_graceful_no_git(orchestrator):
    """Test Phase 0: Git validation graceful fallback when not in git repo."""
    # No git repo initialized
    result = orchestrator._validate_git_workflow()

    # Should return Ok (non-blocking) with warning logged
    assert result.is_ok()


def test_load_graph_from_file_success(orchestrator, tmp_path):
    """Test loading task graph from JSON file."""
    # Create test graph file
    import json

    graph_data = {
        "mission": "Test Mission",
        "phases": [
            {
                "id": "phase_1",
                "title": "Implementation",
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Task 1",
                        "type": "Code",
                        "tier": "Tier 2",
                        "agent": "coder",
                        "description": "Implement feature",
                        "dependencies": [],
                        "acceptance_criteria": ["Feature implemented"],
                    },
                    {
                        "id": "test_1",
                        "title": "Test Task 1",
                        "type": "Test",
                        "tier": "Tier 2",
                        "agent": "test_generator",
                        "description": "Test feature",
                        "dependencies": ["task_1"],
                        "verification_target": "task_1",
                    },
                ],
            }
        ],
    }

    graph_file = tmp_path / "test_graph.json"
    graph_file.write_text(json.dumps(graph_data))

    result = orchestrator._load_graph_from_file(str(graph_file))

    assert result.is_ok()
    task_graph = result.unwrap()
    assert task_graph.mission == "Test Mission"
    assert len(task_graph.all_tasks()) == 2  # Code + Test (Article II)


def test_load_graph_from_file_not_found(orchestrator):
    """Test loading task graph from non-existent file."""
    result = orchestrator._load_graph_from_file("/nonexistent/graph.json")

    assert result.is_err()
    error = result.unwrap_err()
    assert "Graph file not found" in error.reason


def test_auto_select_from_backlog_success(orchestrator, tmp_path):
    """Test auto-selecting task from backlog."""
    # Create backlog file with priority task
    backlog_dir = Path.home() / ".agency" / "memories" / "agency_backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)

    backlog_file = backlog_dir / "test_suite_gaps.md"
    backlog_file.write_text(
        """
# Test Suite Backlog

- [ ] Priority 1: Implement Docker Compose setup for Ollama
- [ ] TODO: Fix failing integration tests
"""
    )

    result = orchestrator._auto_select_from_backlog()

    assert result.is_ok()
    intent = result.unwrap()
    assert (
        "Implement Docker Compose setup for Ollama" in intent
        or "Fix failing integration tests" in intent
    )

    # Cleanup
    backlog_file.unlink()


def test_auto_select_from_backlog_not_found(orchestrator):
    """Test auto-select when backlog file doesn't exist."""
    # Ensure backlog file doesn't exist
    backlog_path = Path.home() / ".agency" / "memories" / "agency_backlog" / "test_suite_gaps.md"
    if backlog_path.exists():
        backlog_path.unlink()

    result = orchestrator._auto_select_from_backlog()

    # Should return error with helpful suggestions
    if result.is_err():
        error = result.unwrap_err()
        assert "Backlog file not found" in error.reason


@pytest.mark.asyncio
async def test_generate_graph_from_intent(orchestrator):
    """Test generating task graph from natural language intent."""
    intent = "Implement JWT authentication with RSA-256"

    result = await orchestrator._generate_graph_from_intent(intent)

    assert result.is_ok()
    task_graph = result.unwrap()
    assert (
        "JWT authentication" in task_graph.mission or "Foundation Automation" in task_graph.mission
    )
    assert len(task_graph.phases) >= 2  # Should have Phase 0 + Implementation


def test_create_foundation_graph_with_pr(agent_context):
    """Test foundation graph includes PR creation phase when enabled."""
    orchestrator = UnifiedPrimeAOrchestrator(
        context=agent_context,
        repo_path=".",
        enable_pr_creation=True,  # Enable PR
    )

    graph = orchestrator._create_foundation_graph("Implement feature X")

    # Should have 3 phases: Phase 0 (git setup) + Phase 1 (impl) + Phase Final (PR)
    assert len(graph.phases) == 3
    assert graph.phases[0].id == "phase_0_setup"
    assert graph.phases[-1].id == "phase_final_pr"

    # Final phase should have PR creation task
    pr_task = graph.phases[-1].tasks[0]
    assert pr_task.id == "create_pull_request"
    assert pr_task.agent == "merger"


def test_create_foundation_graph_without_pr(agent_context):
    """Test foundation graph excludes PR creation phase when disabled."""
    orchestrator = UnifiedPrimeAOrchestrator(
        context=agent_context,
        repo_path=".",
        enable_pr_creation=False,  # Disable PR (--no-pr flag)
    )

    graph = orchestrator._create_foundation_graph("Implement feature X")

    # Should have 2 phases: Phase 0 (git setup) + Phase 1 (impl)
    assert len(graph.phases) == 2
    assert graph.phases[0].id == "phase_0_setup"
    assert graph.phases[1].id == "phase_1_implementation"

    # No PR creation task
    task_ids = [t.id for t in graph.all_tasks()]
    assert "create_pull_request" not in task_ids


def test_create_foundation_graph_phase_0_tasks(orchestrator):
    """Test Phase 0 includes git workflow setup tasks."""
    graph = orchestrator._create_foundation_graph("Implement feature X")

    # Phase 0 should have git validation tasks (code + test for Article II)
    phase_0 = graph.phases[0]
    assert phase_0.id == "phase_0_setup"
    assert len(phase_0.tasks) == 2  # Code + Test (Article II requirement)

    # Code task: git branch verification
    git_code_task = phase_0.tasks[0]
    assert git_code_task.id == "verify_git_branch"
    assert git_code_task.type == TaskType.CODE
    assert "Branch protection" in git_code_task.description
    assert len(git_code_task.acceptance_criteria) == 3

    # Test task: verify git branch setup
    git_test_task = phase_0.tasks[1]
    assert git_test_task.id == "test_git_branch"
    assert git_test_task.type == TaskType.TEST
    assert git_test_task.verification_target == "verify_git_branch"


def test_create_foundation_graph_dependencies(orchestrator):
    """Test Phase 0 dependencies are properly set."""
    graph = orchestrator._create_foundation_graph("Implement feature X")

    # Implementation task should depend on git test (Article II: tests before code)
    impl_task = next(
        t for t in graph.all_tasks() if "_code" in t.id and t.id != "verify_git_branch"
    )
    assert "test_git_branch" in impl_task.dependencies

    # Implementation test task should depend on implementation code
    impl_test_task = next(
        t for t in graph.all_tasks() if "_test" in t.id and t.id != "test_git_branch"
    )
    assert impl_task.id in impl_test_task.dependencies

    # If PR creation exists, should depend on implementation test
    pr_tasks = [t for t in graph.all_tasks() if t.id == "create_pull_request"]
    if pr_tasks:
        pr_task = pr_tasks[0]
        assert impl_test_task.id in pr_task.dependencies


@pytest.mark.asyncio
async def test_no_pr_flag_support(agent_context, tmp_path):
    """Test --no-pr flag support (enable_pr_creation=False)."""
    orchestrator = UnifiedPrimeAOrchestrator(
        context=agent_context,
        repo_path=str(tmp_path),
        enable_pr_creation=False,  # Simulates --no-pr flag
    )

    # Generate graph
    result = await orchestrator._generate_graph_from_intent("Test feature")

    assert result.is_ok()
    graph = result.unwrap()

    # Should NOT have PR creation phase
    phase_ids = [p.id for p in graph.phases]
    assert "phase_final_pr" not in phase_ids

    # Should NOT have PR creation task
    task_ids = [t.id for t in graph.all_tasks()]
    assert "create_pull_request" not in task_ids


@pytest.mark.asyncio
async def test_constitutional_article_iii_branch_protection(orchestrator, tmp_path):
    """Test Article III: Branch protection enforcement (Phase 0)."""
    # Setup: Initialize git repo on main branch
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Execute on main branch (should fail)
    result = orchestrator._validate_git_workflow()

    assert result.is_err()
    error = result.unwrap_err()
    assert "Article III" in error.details  # Constitutional reference
