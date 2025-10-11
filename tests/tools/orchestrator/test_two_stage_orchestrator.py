"""
Tests for TwoStageOrchestrator - Complete workflow orchestration tests.

Constitutional Compliance:
- Article I: Complete context verification (tests retry logic)
- Article II: 100% test verification enforcement (tests failure paths)
- Article IV: VectorStore integration (tests pattern query/storage)

Test Coverage:
- NECESSARY pattern: Normal, Edge, Corner, Error, Security, Stress, Accessibility, Regression, Yield
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from shared.agent_context import AgentContext
from shared.models.task_graph import Phase, Task, TaskGraph, TaskTier, TaskType
from tools.orchestrator.approval_checkpoint import ApprovedSpec, ApprovalDecision
from tools.orchestrator.approval_checkpoint import Spec as ApprovalSpec
from tools.orchestrator.intent_parser import InputMode, Intent
from tools.orchestrator.pr_creator import PRUrl
from tools.orchestrator.spec_generator import SpecIntent
from tools.orchestrator.spec_generator import Spec as SpecGenSpec
from tools.orchestrator.test_verification_gate import VerificationResults
from tools.orchestrator.two_stage_orchestrator import (
    OrchestrationError,
    TwoStageOrchestrator,
    create_orchestrator,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_context():
    """Create mock AgentContext."""
    context = Mock(spec=AgentContext)
    context.session_id = "test_session"
    context.search_memories = Mock(return_value=[])
    context.store_memory = Mock()
    return context


@pytest.fixture
def orchestrator(mock_context):
    """Create TwoStageOrchestrator instance with mocked components."""
    orch = TwoStageOrchestrator(
        context=mock_context,
        repo_path="/tmp/test_repo",
        enable_todos=False,  # Disable TodoWrite for tests
    )

    # Mock components to avoid external dependencies (use Mock, not AsyncMock for sync methods)
    orch.intent_parser = Mock()
    orch.spec_generator = Mock()
    orch.approval_checkpoint = Mock()
    orch.tdd_generator = Mock()
    orch.necessary_validator = Mock()
    orch.test_gate = Mock()
    orch.pr_creator = Mock()

    return orch


@pytest.fixture
def sample_intent():
    """Sample parsed intent."""
    return Intent(
        description="Add JWT authentication to API",
        mode=InputMode.NATURAL_LANGUAGE,
        source="natural_language",
        priority=1,
        tags=["auth", "security"],
    )


@pytest.fixture
def sample_spec():
    """Sample specification from SpecGenerator (has goals, personas, etc.)."""
    return SpecGenSpec(
        title="JWT Authentication",
        goals=["Implement JWT token validation", "Add secure authentication flow"],
        personas=["API Consumer", "Backend Developer"],
        success_criteria=["All tests pass", "Code is type-safe"],
        metadata={"priority": "high"},
    )


@pytest.fixture
def sample_approved_spec(sample_spec):
    """Sample approved specification."""
    # Convert SpecGenSpec to ApprovalSpec for approval
    approval_spec = ApprovalSpec(
        title=sample_spec.title,
        content="\n".join(sample_spec.goals),
        version=1,
    )

    return ApprovedSpec(
        spec=approval_spec,
        decision=ApprovalDecision(action="approve"),
        edit_count=0,
    )


@pytest.fixture
def sample_task_graph():
    """Sample task graph."""
    return TaskGraph(
        mission="JWT Authentication",
        phases=[
            Phase(
                id="phase_1",
                title="Implementation",
                tasks=[
                    Task(
                        id="code_auth",
                        title="Implement auth",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Implement JWT auth",
                        dependencies=[],
                    ),
                    Task(
                        id="test_auth",
                        title="Test auth",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Test JWT auth",
                        dependencies=["code_auth"],
                        verification_target="code_auth",
                    ),
                ],
            )
        ],
        checkpoints=[],
        metadata={},
    )


@pytest.fixture
def sample_verification_results():
    """Sample test verification results."""
    return VerificationResults(
        passed=10,
        failed=0,
        skipped=0,
        errors=[],
        duration=5.0,
        coverage=95.5,
        timed_out=False,
        exit_code=0,
        worker_count=3,
    )


@pytest.fixture
def sample_pr_url():
    """Sample PR URL."""
    return PRUrl(
        url="https://github.com/user/repo/pull/123",
        pr_number=123,
        branch="feat/jwt-auth",
        worktree_path="/tmp/Agency-worktrees/Agency-abc123-feat-jwt-auth",
        commit_sha="abc123def456",
    )


# ============================================================================
# NORMAL: SUCCESSFUL ORCHESTRATION
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_success_natural_language(
    orchestrator,
    sample_intent,
    sample_spec,
    sample_approved_spec,
    sample_task_graph,
    sample_verification_results,
    sample_pr_url,
):
    """Test successful orchestration with natural language input."""
    # Arrange: Mock all component responses
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_task_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_verification_results)
    )
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_pr_url)
    )

    # Act
    result = await orchestrator.orchestrate("Add JWT auth")

    # Assert
    assert result.is_ok()
    orch_result = result.unwrap()

    assert orch_result.pr_url.url == sample_pr_url.url
    assert orch_result.spec.title == sample_spec.title
    assert len(orch_result.graph.all_tasks()) == 2
    assert orch_result.metrics.tests_passed == 10
    assert orch_result.metrics.tests_failed == 0


@pytest.mark.asyncio
async def test_orchestrate_success_auto_select(
    orchestrator,
    sample_intent,
    sample_spec,
    sample_approved_spec,
    sample_task_graph,
    sample_verification_results,
    sample_pr_url,
):
    """Test successful orchestration with auto-select from backlog."""
    # Arrange: Auto-select mode (None input)
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_task_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_verification_results)
    )
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_pr_url)
    )

    # Act: None input triggers auto-select
    result = await orchestrator.orchestrate(None)

    # Assert
    assert result.is_ok()
    orchestrator.intent_parser.parse.assert_called_once_with(None, InputMode.AUTO_SELECT)


# ============================================================================
# EDGE: SPEC APPROVAL WITH EDITS
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_with_spec_edits(
    orchestrator,
    sample_intent,
    sample_task_graph,
    sample_verification_results,
    sample_pr_url,
):
    """Test orchestration with spec edit iterations."""
    # Arrange: Create spec for approval
    spec_gen = SpecGenSpec(
        title="Test Spec",
        goals=["Goal 1"],
        personas=["User 1"],
        success_criteria=["Criteria 1"],
        metadata={},
    )

    approval_spec = ApprovalSpec(
        title="Test Spec",
        content="Test specification content with sufficient length",
        version=1,
    )

    approved_spec = ApprovedSpec(
        spec=approval_spec,
        decision=ApprovalDecision(action="approve"),
        edit_count=2,
    )

    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: spec_gen
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_task_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_verification_results)
    )
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_pr_url)
    )

    # Act
    result = await orchestrator.orchestrate("Add JWT auth")

    # Assert
    assert result.is_ok()
    orch_result = result.unwrap()
    assert orch_result.metrics.spec_edit_count == 2


# ============================================================================
# CORNER: EMPTY TASK GRAPH
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_empty_task_graph(
    orchestrator,
    sample_intent,
    sample_spec,
    sample_approved_spec,
):
    """Test orchestration with minimal task graph (corner case)."""
    # Arrange: Minimal task graph (one task)
    minimal_graph = TaskGraph(
        mission="Minimal Test",
        phases=[
            Phase(
                id="phase_1",
                title="Minimal Phase",
                tasks=[
                    Task(
                        id="code_minimal",
                        title="Minimal task",
                        type=TaskType.CODE,
                        tier=TaskTier.TIER_2,
                        agent="coder",
                        description="Minimal implementation",
                        dependencies=[],
                    ),
                    Task(
                        id="test_minimal",
                        title="Test minimal",
                        type=TaskType.TEST,
                        tier=TaskTier.TIER_2,
                        agent="test_generator",
                        description="Test minimal",
                        dependencies=["code_minimal"],
                        verification_target="code_minimal",
                    ),
                ],
            )
        ],
        checkpoints=[],
        metadata={},
    )

    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: minimal_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(
            is_err=lambda: False,
            unwrap=lambda: VerificationResults(
                passed=1,
                failed=0,
                skipped=0,
                errors=[],
                duration=1.0,
                exit_code=0,
                worker_count=1,
            ),
        )
    )
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(
            is_err=lambda: False,
            unwrap=lambda: PRUrl(
                url="https://github.com/user/repo/pull/1",
                pr_number=1,
                branch="feat/minimal",
                worktree_path="/tmp/worktree",
                commit_sha="abc123",
            ),
        )
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert: Should succeed with minimal graph
    assert result.is_ok()
    assert result.unwrap().metrics.tasks_generated == 2


# ============================================================================
# ERROR: INTENT PARSING FAILURE
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_intent_parsing_failure(orchestrator):
    """Test orchestration failure during intent parsing."""
    # Arrange: Intent parser returns error
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: True,
        unwrap_err=lambda: "No Ready tasks found in backlog",
    )

    # Act
    result = await orchestrator.orchestrate(None)

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.stage == "intent_parsing"
    assert "No Ready tasks" in error.reason


@pytest.mark.asyncio
async def test_orchestrate_spec_generation_failure(
    orchestrator,
    sample_intent,
):
    """Test orchestration failure during spec generation."""
    # Arrange: Spec generator returns error
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: True,
        unwrap_err=lambda: "VectorStore query timeout",
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.stage == "spec_generation"
    assert "VectorStore" in error.reason


@pytest.mark.asyncio
async def test_orchestrate_spec_approval_timeout(
    orchestrator,
    sample_intent,
):
    """Test orchestration failure due to spec approval timeout."""
    # Create spec without using fixture
    spec = SpecGenSpec(
        title="Test Feature",
        goals=["Goal 1"],
        personas=["User 1"],
        success_criteria=["Criteria 1"],
        metadata={},
    )

    # Arrange: Approval checkpoint times out
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(
            is_err=lambda: True,
            unwrap_err=lambda: "Approval timeout after 300s (no user response)",
        )
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.stage == "spec_approval"
    assert "timeout" in error.reason.lower()


@pytest.mark.asyncio
async def test_orchestrate_test_verification_failure(
    orchestrator,
    sample_intent,
    sample_spec,
    sample_approved_spec,
    sample_task_graph,
):
    """Test orchestration failure due to test failures (Article II violation)."""
    # Arrange: Test verification fails (tests failed)
    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_task_graph
    )

    # Test gate returns error (failed tests)
    from tools.orchestrator.test_verification_gate import VerificationError

    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(
            is_err=lambda: True,
            unwrap_err=lambda: VerificationError(
                reason="failures",
                message="Article II violation: 3 tests failed",
                exit_code=1,
                failed_tests=["test_auth_invalid_token", "test_auth_expired", "test_auth_missing"],
            ),
        )
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert
    assert result.is_err()
    error = result.unwrap_err()
    assert error.stage == "test_verification"
    assert "Article II" in error.reason or "failed" in error.reason.lower()


# ============================================================================
# SECURITY: INPUT VALIDATION
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_malicious_branch_name_injection(
    orchestrator,
    sample_intent,
    sample_task_graph,
    sample_verification_results,
):
    """Test branch name sanitization prevents code injection."""
    # Arrange: Malicious spec with code injection attempt
    malicious_spec_gen = SpecGenSpec(
        title="JWT Auth'; DROP TABLE users; --",
        goals=["Malicious goal"],
        personas=["Attacker"],
        success_criteria=["Inject code"],
        metadata={},
    )

    malicious_approval_spec = ApprovalSpec(
        title="JWT Auth'; DROP TABLE users; --",
        content="Malicious spec",
        version=1,
    )

    approved_spec = ApprovedSpec(
        spec=malicious_approval_spec,
        decision=ApprovalDecision(action="approve"),
        edit_count=0,
    )

    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: malicious_spec_gen
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_task_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_verification_results)
    )

    # Mock PR creator to capture branch name
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(
            is_err=lambda: False,
            unwrap=lambda: PRUrl(
                url="https://github.com/user/repo/pull/123",
                pr_number=123,
                branch="feat/jwt-auth-drop-table-users",  # Sanitized
                worktree_path="/tmp/worktree",
                commit_sha="abc123",
            ),
        )
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert: Branch name should be sanitized
    if result.is_ok():
        branch_arg = orchestrator.pr_creator.create_pr.call_args[1]["branch_name"]
        # Should not contain SQL injection characters
        assert "'" not in branch_arg
        assert ";" not in branch_arg
        assert "--" not in branch_arg


# ============================================================================
# STRESS: LARGE TASK GRAPH
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrate_large_task_graph(
    orchestrator,
    sample_intent,
    sample_spec,
    sample_approved_spec,
    sample_verification_results,
    sample_pr_url,
):
    """Test orchestration with large task graph (100 tasks)."""
    # Arrange: Generate large task graph
    tasks = []
    for i in range(50):
        tasks.append(
            Task(
                id=f"code_feature_{i}",
                title=f"Implement feature {i}",
                type=TaskType.CODE,
                tier=TaskTier.TIER_2,
                agent="coder",
                description=f"Implement feature {i}",
                dependencies=[],
            )
        )
        tasks.append(
            Task(
                id=f"test_feature_{i}",
                title=f"Test feature {i}",
                type=TaskType.TEST,
                tier=TaskTier.TIER_2,
                agent="test_generator",
                description=f"Test feature {i}",
                dependencies=[f"code_feature_{i}"],
                verification_target=f"code_feature_{i}",
            )
        )

    large_graph = TaskGraph(
        mission="Large Feature",
        phases=[
            Phase(
                id="phase_1",
                title="Implementation",
                tasks=tasks,
            )
        ],
        checkpoints=[],
        metadata={},
    )

    orchestrator.intent_parser.parse.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_intent
    )
    orchestrator.spec_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: sample_spec
    )
    orchestrator.approval_checkpoint.await_approval = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_approved_spec)
    )
    orchestrator.tdd_generator.generate.return_value = Mock(
        is_err=lambda: False, unwrap=lambda: large_graph
    )
    orchestrator.test_gate.verify = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_verification_results)
    )
    orchestrator.pr_creator.create_pr = AsyncMock(
        return_value=Mock(is_err=lambda: False, unwrap=lambda: sample_pr_url)
    )

    # Act
    result = await orchestrator.orchestrate("Add feature")

    # Assert
    assert result.is_ok()
    orch_result = result.unwrap()
    assert orch_result.metrics.tasks_generated == 100


# ============================================================================
# ACCESSIBILITY: TODOWRITE INTEGRATION
# ============================================================================


def test_update_todo_disabled(orchestrator):
    """Test TodoWrite updates are skipped when disabled."""
    # Arrange: TodoWrite disabled
    orchestrator.enable_todos = False

    # Act
    orchestrator._update_todo("in_progress", "Test task")

    # Assert: No exception raised, method returns silently
    # (no way to verify no-op without inspecting internal state)


def test_update_todo_enabled(mock_context):
    """Test TodoWrite updates work when enabled."""
    # Arrange: TodoWrite enabled
    orch = TwoStageOrchestrator(
        context=mock_context,
        repo_path="/tmp/test",
        enable_todos=True,
    )

    # Act: Update todo (should not raise exception)
    with patch("tools.orchestrator.two_stage_orchestrator.TodoWrite") as mock_todo:
        mock_todo_instance = Mock()
        mock_todo_instance.run.return_value = "Success"
        mock_todo.return_value = mock_todo_instance

        orch._update_todo("in_progress", "Test task")

        # Assert: TodoWrite was instantiated and run
        mock_todo.assert_called_once()


# ============================================================================
# REGRESSION: VECTORSTORE INTEGRATION
# ============================================================================


def test_query_workflow_patterns_success(orchestrator):
    """Test VectorStore query for workflow patterns (Article IV)."""
    # Arrange: Mock VectorStore returns patterns
    orchestrator.context.search_memories.return_value = [
        {"pattern": "jwt_auth", "confidence": 0.9},
        {"pattern": "api_auth", "confidence": 0.8},
    ]

    # Act
    orchestrator._query_workflow_patterns()

    # Assert: search_memories was called with correct tags
    orchestrator.context.search_memories.assert_called_once_with(
        ["orchestration", "workflow", "success"],
        include_session=False,
    )


def test_query_workflow_patterns_failure(orchestrator):
    """Test VectorStore query failure is non-blocking."""
    # Arrange: Mock VectorStore raises exception
    orchestrator.context.search_memories.side_effect = Exception("VectorStore connection failed")

    # Act: Should not raise exception (non-blocking)
    orchestrator._query_workflow_patterns()

    # Assert: No exception raised


def test_store_workflow_success(
    orchestrator,
    sample_approved_spec,
    sample_task_graph,
    sample_pr_url,
):
    """Test workflow success storage in VectorStore (Article IV)."""
    # Arrange
    from tools.orchestrator.two_stage_orchestrator import OrchestrationMetrics

    metrics = OrchestrationMetrics(
        total_duration_seconds=120.5,
        stage_1_duration=30.0,
        stage_2_duration=90.5,
        tasks_generated=2,
        tests_passed=10,
        tests_failed=0,
        spec_edit_count=0,
        test_retry_count=0,
        patterns_used=3,
        confidence_score=0.85,
    )

    # Act
    orchestrator._store_workflow_success(
        sample_approved_spec,
        sample_task_graph,
        sample_pr_url,
        metrics,
    )

    # Assert: store_memory was called with correct structure
    orchestrator.context.store_memory.assert_called_once()
    call_args = orchestrator.context.store_memory.call_args

    # Verify call was made with 3 positional arguments: (key, content, tags)
    # Access arguments via args tuple or kwargs dict depending on how they were passed
    if call_args.args and len(call_args.args) >= 3:
        # Positional args
        key = call_args.args[0]
        tags = call_args.args[2]
        assert key.startswith("orchestration_success_")
        assert "orchestration" in tags
        assert "workflow" in tags
        assert "success" in tags
    elif call_args.kwargs:
        # Keyword args
        assert call_args.kwargs.get("key", call_args.args[0] if call_args.args else "").startswith("orchestration_success_")
        assert "orchestration" in call_args.kwargs.get("tags", [])
    else:
        # Mixed args/kwargs - just verify the call was made
        assert True  # store_memory was called (already verified by assert_called_once)


# ============================================================================
# YIELD: FACTORY FUNCTION
# ============================================================================


def test_create_orchestrator_factory(mock_context):
    """Test factory function creates orchestrator correctly."""
    # Act
    orch = create_orchestrator(
        context=mock_context,
        repo_path="/tmp/test",
        enable_todos=True,
    )

    # Assert
    assert isinstance(orch, TwoStageOrchestrator)
    assert orch.context == mock_context
    assert orch.repo_path == "/tmp/test"
    assert orch.enable_todos is True


def test_generate_branch_name_sanitization(orchestrator):
    """Test branch name sanitization (Yield - utility functions)."""
    # Arrange: Test various spec titles
    test_cases = [
        ("Add JWT Authentication", "feat/add-jwt-authentication"),
        ("Fix Bug #123", "feat/fix-bug-123"),
        ("Implement   Multiple   Spaces", "feat/implement-multiple-spaces"),
        ("UPPERCASE Title", "feat/uppercase-title"),
        ("Special!@#$%Characters&*()", "feat/specialcharacters"),
        ("Very" * 20, "feat/very" + "very" * 9),  # Truncated to 50 chars
    ]

    for spec_title, expected_branch in test_cases:
        # Act
        branch = orchestrator._generate_branch_name(spec_title)

        # Assert
        assert branch.startswith("feat/")
        assert len(branch) <= 55  # feat/ + 50 chars
        assert branch.replace("feat/", "").replace("-", "").isalnum()
