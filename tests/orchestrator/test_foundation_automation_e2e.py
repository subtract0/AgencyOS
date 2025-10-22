"""
E2E workflow tests for UnifiedPrimeAOrchestrator following NECESSARY pattern.

Tests complete workflows from natural language intent to PR creation.
Implements SPEC-030 requirements for comprehensive E2E testing.

Test Coverage:
- E2E-001: Natural language intent → PR creation (happy path)
- E2E-002: Intent with --two-stage flag → spec approval → execution
- E2E-003: Intent with --no-pr flag → execution without PR
- E2E-004: Intent with --plan-only flag → graph generation only
- E2E-005: Explicit graph file → execution → PR
- E2E-006: Auto-selection from backlog → execution → PR
- E2E-007: Invalid intent → auto-rewrite loop → halt
- E2E-008: Budget exceeded → halt with breakdown

Constitutional Compliance:
- Article I: Complete context (retry logic tested)
- Article II: 100% verification (all tests must pass)
- Article III: Automated enforcement (no manual bypass)
- Article IV: VectorStore integration (mocked)
- Article V: Spec-driven (task graph validation)
"""

import asyncio
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.agent_context import create_agent_context
from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType
from shared.type_definitions.result import Err, Ok
from tools.orchestrator.unified_primea_orchestrator import (
    ExecutionError,
    ExecutionResult,
    UnifiedPrimeAOrchestrator,
)


class TestFoundationAutomationE2E:
    """E2E workflow tests following NECESSARY pattern."""

    @pytest.fixture
    def agent_context(self):
        """Create test agent context with memory disabled."""
        return create_agent_context(session_id="test_e2e")

    @pytest.fixture
    def orchestrator(self, agent_context, tmp_path):
        """Create orchestrator instance for testing (slop immunity disabled)."""
        return UnifiedPrimeAOrchestrator(
            context=agent_context,
            repo_path=str(tmp_path),
            enable_todos=False,  # Disable for tests
            enable_pr_creation=True,  # Enable for E2E tests (mocked when no git repo)
            enable_slop_immunity=False,  # Disable for most tests (except e2e_007)
        )

    @pytest.fixture
    def orchestrator_with_slop(self, agent_context, tmp_path):
        """Create orchestrator with slop immunity enabled (for test_e2e_007)."""
        return UnifiedPrimeAOrchestrator(
            context=agent_context,
            repo_path=str(tmp_path),
            enable_todos=False,
            enable_pr_creation=False,
            enable_slop_immunity=True,  # Enable for slop immunity test
        )

    @pytest.fixture
    def simple_task_graph(self):
        """Create simple 5-task graph for testing (TDD-compliant)."""
        return TaskGraph(
            mission="Test Mission: Simple E2E workflow",
            phases=[
                Phase(
                    id="phase_1",
                    title="Implementation",
                    tasks=[
                        Task(
                            id="task_0",
                            title="Write tests for authentication module",
                            description="Write tests FIRST (TDD - Article II)",
                            type=TaskType.TEST,
                            tier=TaskTier.TIER_2,
                            agent="test_generator",
                            estimated_tokens=3000,
                            verification_target="task_1",  # Will verify task_1
                        ),
                        Task(
                            id="task_1",
                            title="Write authentication module",
                            description="Implement authentication module",
                            type=TaskType.CODE,
                            tier=TaskTier.TIER_2,
                            agent="coder",
                            estimated_tokens=5000,
                            dependencies=["task_0"],  # TDD: Test before code
                        ),
                        Task(
                            id="task_2",
                            title="Verify authentication module",
                            description="Verify authentication module passes tests",
                            type=TaskType.TEST,
                            tier=TaskTier.TIER_2,
                            agent="test_generator",
                            estimated_tokens=2000,
                            dependencies=["task_1"],
                            verification_target="task_1",  # Verify implementation
                        ),
                    ],
                ),
                Phase(
                    id="phase_2",
                    title="Integration",
                    tasks=[
                        Task(
                            id="task_3",
                            title="Write tests for API integration",
                            description="Write tests FIRST for API integration (TDD)",
                            type=TaskType.TEST,
                            tier=TaskTier.TIER_2,
                            agent="test_generator",
                            estimated_tokens=3000,
                            dependencies=["task_2"],
                            verification_target="task_4",  # Will verify task_4
                        ),
                        Task(
                            id="task_4",
                            title="Integrate with API",
                            description="Integrate authentication with API",
                            type=TaskType.CODE,
                            tier=TaskTier.TIER_2,
                            agent="coder",
                            estimated_tokens=4000,
                            dependencies=["task_3"],  # TDD: Test before code
                        ),
                        Task(
                            id="task_5",
                            title="Verify API integration",
                            description="Verify API integration passes tests",
                            type=TaskType.TEST,
                            tier=TaskTier.TIER_2,
                            agent="test_generator",
                            estimated_tokens=2000,
                            dependencies=["task_4"],
                            verification_target="task_4",  # Verify implementation
                        ),
                        Task(
                            id="task_6",
                            title="Final validation",
                            description="Final quality check",
                            type=TaskType.TEST,
                            tier=TaskTier.TIER_1,
                            agent="quality_enforcer",
                            estimated_tokens=1500,
                            dependencies=["task_5"],
                            verification_target="task_5",
                        ),
                    ],
                ),
            ],
        )

    # =========================================================================
    # NECESSARY Pattern: Normal Operation (N)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_e2e_001_natural_language_to_pr_happy_path(self, orchestrator):
        """E2E-001: Natural language intent → task graph → validation → execution → PR."""
        # RED Phase: This test MUST fail initially
        intent = "Add JWT authentication with RSA-256 signing"

        # This method doesn't exist yet - will fail
        result = await orchestrator.execute_e2e_workflow(intent=intent)

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.success
        assert execution.pr_url is not None
        assert "jwt-auth" in execution.pr_url

    @pytest.mark.asyncio
    async def test_e2e_006_auto_selection_from_backlog(self, orchestrator, tmp_path):
        """E2E-006: Auto-selection from backlog → execution → PR."""
        # Setup backlog file
        backlog_dir = tmp_path / ".agency/memories/agency_backlog"
        backlog_dir.mkdir(parents=True, exist_ok=True)
        backlog_file = backlog_dir / "test_suite_gaps.md"
        backlog_file.write_text("""# Test Suite Gaps

- [ ] Priority 1: Fix authentication bug in login flow
- [x] Priority 2: Already completed task
- [ ] Priority 3: Add rate limiting to API endpoints
""")

        # This method doesn't exist yet - will fail
        with patch.object(Path, "home", return_value=tmp_path):
            result = await orchestrator.execute_e2e_workflow()  # No intent provided

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.success
        assert "authentication" in execution.mission.lower()

    @pytest.mark.asyncio
    async def test_e2e_005_explicit_graph_file(self, orchestrator, tmp_path, simple_task_graph):
        """E2E-005: Explicit graph file → validation → execution → PR."""
        # Save task graph to file
        graph_file = tmp_path / "test_graph.json"
        graph_file.write_text(simple_task_graph.model_dump_json())

        # This method doesn't exist yet - will fail
        result = await orchestrator.execute_e2e_workflow(graph_file=str(graph_file))

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.success
        assert execution.tasks_completed == 7  # TDD-compliant graph has 7 tasks

    # =========================================================================
    # NECESSARY Pattern: Edge Cases (E)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_e2e_002_two_stage_workflow_with_approval(self, orchestrator):
        """E2E-002: Intent with --two-stage flag → spec generation → approval → execution."""
        intent = "Build rate limiting middleware"
        flags = {"two_stage": True}

        # This method doesn't exist yet - will fail
        result = await orchestrator.execute_e2e_workflow(intent=intent, flags=flags)

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.spec_approved
        assert execution.two_stage_completed

    @pytest.mark.asyncio
    async def test_e2e_003_no_pr_flag_skips_pr_creation(self, orchestrator):
        """E2E-003: Intent with --no-pr flag → execution completes without PR."""
        intent = "Refactor logging module"
        flags = {"no_pr": True}

        # This method doesn't exist yet - will fail
        result = await orchestrator.execute_e2e_workflow(intent=intent, flags=flags)

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.success
        assert execution.pr_url is None  # No PR created

    @pytest.mark.asyncio
    async def test_e2e_004_plan_only_saves_graph(self, orchestrator, tmp_path):
        """E2E-004: Intent with --plan-only → graph generation → save → exit."""
        intent = "Implement caching layer"
        flags = {"plan_only": True}

        # This method doesn't exist yet - will fail
        result = await orchestrator.execute_e2e_workflow(intent=intent, flags=flags)

        assert result.is_ok()
        execution = result.unwrap()
        assert execution.graph_saved
        assert execution.graph_path.startswith("/tmp/task_graph_")
        assert not execution.tasks_executed  # No execution

    # =========================================================================
    # NECESSARY Pattern: Error Handling (E)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_e2e_007_invalid_intent_auto_rewrite(self, orchestrator_with_slop):
        """E2E-007: Invalid intent → auto-rewrite loop (3 attempts) → halt."""
        intent = "make it better"  # Too vague

        # This method doesn't exist yet - will fail
        result = await orchestrator_with_slop.execute_e2e_workflow(intent=intent)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "Slop immunity failed"
        assert error.rewrite_attempts == 3

    @pytest.mark.asyncio
    async def test_e2e_008_budget_exceeded_halts(self, orchestrator):
        """E2E-008: Budget exceeded → halt with cost breakdown."""
        intent = "Rewrite entire application in Rust"  # Expensive task

        # This method doesn't exist yet - will fail
        with patch.dict(os.environ, {"DAILY_BUDGET_USD": "0.01"}):
            result = await orchestrator.execute_e2e_workflow(intent=intent)

        assert result.is_err()
        error = result.unwrap_err()
        assert error.reason == "Budget exceeded"
        assert error.estimated_cost > 0.01
        assert "--force" in error.suggestions
