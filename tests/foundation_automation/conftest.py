"""Shared fixtures for foundation automation tests.

Provides isolated fixtures for testing the /primeA orchestrator workflow:
- Mock agent contexts with unique session IDs
- Isolated git repositories
- Mock VectorStore with predefined patterns
- Mock GitHub API for PR creation
- Sample task graphs and intents
- Backlog file generation

Constitutional Compliance:
- Article I: Complete context (no shared state between tests)
- Article II: 100% verification (fixtures ensure clean state)
- Article III: Automated enforcement (mock services prevent bypasses)
"""

import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from shared.agent_context import AgentContext, create_agent_context
from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType


@pytest.fixture
def mock_agent_context(tmp_path: Path) -> AgentContext:
    """
    Create isolated agent context with memory disabled.

    Returns isolated context with unique session ID to prevent cross-test pollution.
    VectorStore disabled for fast test execution.

    Article I: Complete context isolation (unique session ID per test)
    Article IV: VectorStore mocked (no actual storage during tests)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = str(uuid.uuid4())[:8]
    session_id = f"test_foundation_{timestamp}_{unique_suffix}"

    context = create_agent_context(session_id=session_id)

    # Mock VectorStore methods
    context.store_memory = Mock(return_value=True)
    context.retrieve_memory = Mock(return_value=None)
    context.get_memories_by_tags = Mock(return_value=[])
    context.search_memories = Mock(return_value=[])
    context.get_session_memories = Mock(return_value=[])
    context.set_metadata = Mock()
    context.get_metadata = Mock(return_value=None)

    return context


@pytest.fixture
def isolated_git_repo(tmp_path: Path) -> Path:
    """
    Create isolated git repository for Phase 0 validation tests.

    Returns temporary git repository with:
    - Initial commit
    - Feature branch checked out
    - Git config set

    Article I: Complete context (real git repo for authentic validation)
    Article III: Branch protection enforced (repo starts on feature branch)
    """
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repository
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@agency.example"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Agency Test"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    (repo_dir / "README.md").write_text("# Test Repository")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    # Checkout feature branch (default safe state)
    subprocess.run(
        ["git", "checkout", "-b", "feat/test"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    return repo_dir


@pytest.fixture
def mock_vectorstore() -> Mock:
    """
    Mock VectorStore with predefined learnings.

    Returns mock with realistic search results for pattern queries.

    Article IV: VectorStore integration tested with realistic mock data
    """
    mock_store = Mock()

    # Predefined learnings for common queries
    mock_store.search_memories = Mock(
        return_value=[
            {
                "pattern": "TDD workflow",
                "confidence": 0.85,
                "content": "Write tests first, then implementation",
            },
            {
                "pattern": "Git validation",
                "confidence": 0.90,
                "content": "Enforce feature branch naming convention",
            },
            {
                "pattern": "Result pattern",
                "confidence": 0.88,
                "content": "Use Result<T,E> for error handling",
            },
        ]
    )

    mock_store.store_memory = Mock(return_value=True)

    return mock_store


@pytest.fixture
def mock_github_api() -> Mock:
    """
    Mock GitHub API (gh CLI) for PR creation tests.

    Returns mock subprocess.run for gh CLI commands ONLY (not git commands).
    This prevents interference with git validation which also uses subprocess.run.

    Article III: PR creation tested without actual GitHub API calls
    """
    # Save reference to original subprocess.run before patching
    original_subprocess_run = subprocess.run

    def selective_mock(*args, **kwargs):
        """Mock only 'gh' commands, pass through git commands."""
        cmd = args[0] if args else kwargs.get("args", [])
        if cmd and cmd[0] == "gh":
            # Mock gh pr create response
            return Mock(returncode=0, stdout="https://github.com/org/repo/pull/123", stderr="")
        else:
            # Pass through to original subprocess.run for git commands
            return original_subprocess_run(*args, **kwargs)

    mock_api = Mock(side_effect=selective_mock)
    return mock_api


@pytest.fixture
def simple_task_graph() -> TaskGraph:
    """
    Create simple task graph (5 tasks, 2 phases).

    Returns minimal valid task graph for E2E flow tests.

    Article V: Spec-driven (task graph traces to acceptance criteria)
    """
    return TaskGraph(
        mission="Test Mission: Simple authentication",
        phases=[
            Phase(
                id="phase_1",
                title="Specification",
                tasks=[
                    Task(
                        id="spec_task",
                        title="Create authentication spec",
                        type=TaskType.SPEC,
                        tier=TaskTier.TIER_1,
                        agent="planner",
                        description="Create formal specification for authentication feature",
                        dependencies=[],
                        acceptance_criteria=["Spec follows spec-kit format"],
                    )
                ],
            ),
            Phase(
                id="phase_2",
                title="Implementation",
                tasks=[
                    Task(
                        id="test_task",
                        title="Write authentication tests",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Write comprehensive tests for JWT authentication using NECESSARY pattern",
                        dependencies=["spec_task"],
                        acceptance_criteria=["NECESSARY pattern coverage"],
                        verification_target="code_task",
                    ),
                    Task(
                        id="code_task",
                        title="Implement JWT middleware",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Implement JWT middleware to pass all authentication tests",
                        dependencies=["test_task"],
                        acceptance_criteria=["All tests pass", "Type safety verified"],
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def complex_task_graph() -> TaskGraph:
    """
    Create complex task graph (20 tasks, 5 phases).

    Returns large task graph for scale and performance tests.

    Article I: Complete context (large graphs test retry logic)
    """
    phases = []
    task_id = 0

    for phase_num in range(1, 6):
        tasks = []
        for task_num in range(1, 5):
            task_id += 1
            prev_task_id = f"task_{task_id - 1}" if task_id > 1 else None

            # Article VI: TEST tasks before CODE tasks (TDD workflow)
            task_type = TaskType.TEST if task_num % 2 == 1 else TaskType.CODE
            # For TEST tasks, verification_target is the next CODE task
            next_task_id = f"task_{task_id + 1}" if task_type == TaskType.TEST else None

            tasks.append(
                Task(
                    id=f"task_{task_id}",
                    title=f"Task {task_id}: Phase {phase_num} step {task_num}",
                    type=task_type,
                    tier=TaskTier.TIER_2,
                    agent="test_generator" if task_type == TaskType.TEST else "coder",
                    description=f"Execute phase {phase_num} step {task_num} of complex workflow",
                    dependencies=[prev_task_id] if prev_task_id else [],
                    acceptance_criteria=[f"Complete step {task_num}"],
                    verification_target=next_task_id if task_type == TaskType.TEST else None,
                )
            )

        phases.append(Phase(id=f"phase_{phase_num}", title=f"Phase {phase_num}", tasks=tasks))

    return TaskGraph(mission="Test Mission: Complex multi-phase project", phases=phases)


@pytest.fixture
def sample_backlog_content() -> str:
    """
    Generate sample backlog file content.

    Returns formatted backlog markdown with priority tasks.

    Article IV: Backlog stored in Memory Tool (cross-conversation persistence)
    """
    return """# Agency OS Backlog: Test Suite Gaps

## Priority Tasks

- [ ] Priority 1: Implement authentication middleware (Status: Ready)
- [ ] Priority 2: Add rate limiting to API endpoints (Status: Ready)
- [ ] Priority 3: Fix memory leak in VectorStore (Status: Blocked - needs investigation)
- [ ] Priority 4: Upgrade TypeScript to 5.3 (Status: Ready)
- [ ] Priority 5: Add E2E tests for user registration (Status: Locked - in progress by another agent)

## Completed

- [x] Priority 0: Fix NoneType error in orchestrator (2025-10-10)
"""


@pytest.fixture
def create_backlog_file(tmp_path: Path, sample_backlog_content: str):
    """
    Factory fixture to create backlog file at specified path.

    Returns callable that creates backlog file with given content.

    Usage:
        def test_backlog(create_backlog_file):
            backlog_path = create_backlog_file("test_suite_gaps.md")
            # Test backlog parsing
    """

    def _create_backlog(filename: str = "test_suite_gaps.md") -> Path:
        backlog_dir = tmp_path / ".agency" / "memories" / "agency_backlog"
        backlog_dir.mkdir(parents=True, exist_ok=True)

        backlog_file = backlog_dir / filename
        backlog_file.write_text(sample_backlog_content)

        return backlog_file

    return _create_backlog


@pytest.fixture
def sample_intents() -> dict[str, str]:
    """
    Provide sample natural language intents for E2E tests.

    Returns dictionary of test intents mapped to expected outcomes.

    Article V: Spec-driven (intents trace to acceptance criteria)
    """
    return {
        "simple_valid": "Add JWT authentication middleware to API endpoints",
        "complex_valid": "Implement comprehensive user authentication system with OAuth2, JWT tokens, rate limiting, and audit logging",
        "empty": "",
        "injection_attempt": "'; DROP TABLE tasks; --",
        "special_chars": 'Add feature "user-profile" with special chars: @#$%^&*()',
        "very_long": "A" * 10000,  # 10k characters (LLM context limit)
        "unicode": "实施用户认证系统 with emojis 🔐🚀",
    }


@pytest.fixture
def mock_trm_validator() -> Mock:
    """
    Mock TRM validator for DAG validation tests.

    Returns mock TRM validator with success/failure responses.

    Article III: TRM DAG validation enforced (circular dependency detection)
    """
    mock_validator = Mock()

    # Default: validation passes
    mock_validator.validate_dag = AsyncMock(
        return_value={
            "is_valid": True,
            "is_acyclic": True,
            "cycles": [],
            "validation_time_ms": 50,
        }
    )

    return mock_validator


@pytest.fixture
def mock_slop_guardian() -> Mock:
    """
    Mock Slop Guardian for quality enforcement tests.

    Returns mock guardian with verdict responses.

    Article III: Slop immunity enforced (quality threshold ≥3.5)
    """
    mock_guardian = Mock()

    # Default: quality passes
    mock_guardian.evaluate = AsyncMock(
        return_value={
            "status": "ACCEPT",
            "score": 4.2,
            "reasoning": "Graph structure is clear and well-defined",
        }
    )

    return mock_guardian


@pytest.fixture
def mock_budget_guard() -> Mock:
    """
    Mock Budget Guard for cost enforcement tests.

    Returns mock guard with cost estimates and limits.

    Article III: Budget limits enforced (daily/mission caps)
    """
    mock_guard = Mock()

    # Default: budget OK
    mock_guard.check_budget = AsyncMock(
        return_value={
            "within_budget": True,
            "estimated_cost": 2.50,
            "daily_limit": 100.00,
            "mission_limit": 10.00,
            "daily_used": 15.00,
        }
    )

    return mock_guard


@pytest.fixture
def mock_completion_validator() -> Mock:
    """
    Mock Completion Validator for STEP 6.5 tests.

    Returns mock validator with task completion results.

    Article II: 100% task completion required before PR creation
    """
    mock_validator = Mock()

    # Default: all tasks complete
    mock_validator.validate = AsyncMock(
        return_value={
            "tasks_completed": 5,
            "tasks_total": 5,
            "completion_rate": 1.0,
            "blocking_issues": [],
        }
    )

    return mock_validator


@pytest.fixture(autouse=True)
def cleanup_test_artifacts(tmp_path: Path):
    """
    Global cleanup fixture for test artifacts.

    Automatically removes temporary files after each test.

    Article I: Complete context (clean state prevents pollution)
    """
    yield

    # Cleanup task graph files
    for graph_file in Path("/tmp").glob("task_graph_*.json"):
        try:
            graph_file.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    # Cleanup test logs
    for log_dir in ["logs/sessions", "logs/autonomous_healing"]:
        log_path = Path(log_dir)
        if log_path.exists():
            for log_file in log_path.glob("test_foundation_*.log"):
                try:
                    log_file.unlink()
                except Exception:
                    pass


@pytest.fixture
def performance_baseline() -> dict[str, float]:
    """
    Provide performance baseline targets.

    Returns dictionary of operation names to max execution times (seconds).

    Article I: Performance targets enforce timeout expectations
    """
    return {
        "e2e_simple_task": 120.0,  # PERF-001
        "backlog_selection": 2.0,  # PERF-002
        "git_validation": 0.05,  # PERF-003 (50ms)
        "constitutional_gates": 3.0,  # PERF-004
        "integration_test": 5.0,  # PERF-005
        "memory_overhead_mb": 500.0,  # PERF-006
    }
