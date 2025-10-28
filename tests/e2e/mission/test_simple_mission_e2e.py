"""
Mission E2E Tests - NECESSARY Pattern Compliance

End-to-end tests for simple mission execution through /primeA command.

CONSTITUTIONAL MANDATE:
- Article I: Complete context before action (mission waits for VectorStore query)
- Article IV: VectorStore integration (mission queries before action, stores after success)
- Article VI: TDD (tests written first, implementation second)
- ADR-037: E2E testing framework for multi-agent workflows

NECESSARY Coverage:
- Normal: Simple mission execution from intent to completion
- Validation: VectorStore query/store compliance
- Error: Mission failure handling and rollback
- Regression: Mission doesn't break existing functionality
"""

import pytest
import subprocess
import json
from pathlib import Path


# =============================================================================
# NORMAL OPERATION TESTS
# =============================================================================


@pytest.mark.e2e
def test_simple_mission_completes_end_to_end(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify simple mission executes from intent to completion.

    Pattern: NECESSARY - Normal operation
    Workflow: Intent → Scout → Plan → Test → Code → Verify → PR
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Simple mission intent
    mission_intent = "Add type hints to validate_email function"

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=mission_intent,
        two_stage=False  # Single-stage execution for simple task
    )

    # Assert: Mission completes successfully
    assert result.is_ok()
    mission_result = result.unwrap()

    # Assert: All phases completed
    assert mission_result.get("phases_completed") >= 4  # Scout, Plan, Test, Code
    assert mission_result.get("status") == "complete"

    # Assert: Tests were written and pass
    assert mission_result.get("tests_written") > 0
    assert mission_result.get("tests_passing") is True

    # Assert: Code was generated
    assert mission_result.get("code_generated") is True


@pytest.mark.e2e
def test_two_stage_mission_pauses_for_spec_approval(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify two-stage mission pauses after spec generation for user approval.

    Pattern: NECESSARY - Normal operation
    Workflow: Intent → Spec → [PAUSE] → Tests → Code
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Complex mission requiring spec
    mission_intent = "Build JWT authentication system with refresh tokens"

    # Act: Execute Stage 1 (Intent → Spec)
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=mission_intent,
        two_stage=True,
        stage=1  # Only run Stage 1
    )

    # Assert: Stage 1 completes with spec
    assert result.is_ok()
    stage1_result = result.unwrap()

    assert stage1_result.get("stage") == 1
    assert stage1_result.get("spec_generated") is True
    assert stage1_result.get("spec_path") is not None

    # Assert: Spec file exists
    spec_path = Path(stage1_result["spec_path"])
    assert spec_path.exists()

    # Assert: Execution paused for approval
    assert stage1_result.get("awaiting_approval") is True

    # Act: Approve spec and run Stage 2
    result2 = orchestrator.execute_mission(
        spec_path=str(spec_path),
        two_stage=True,
        stage=2  # Run Stage 2
    )

    # Assert: Stage 2 completes
    assert result2.is_ok()
    stage2_result = result2.unwrap()

    assert stage2_result.get("stage") == 2
    assert stage2_result.get("tests_written") > 0
    assert stage2_result.get("code_generated") is True


@pytest.mark.e2e
def test_mission_auto_selects_from_backlog(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission auto-selects top priority task when no intent provided.

    Pattern: NECESSARY - Normal operation
    Validates: Backlog integration
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Populate backlog
    backlog_file = Path.home() / ".agency/memories/agency_backlog/test_suite_gaps.md"
    backlog_file.parent.mkdir(parents=True, exist_ok=True)
    backlog_file.write_text("""
# Test Suite Gaps

## Priority 1: Critical
- [ ] Fix NoneType errors in agent_context.py (191 test failures)

## Priority 2: Important
- [ ] Add type hints to legacy modules
""")

    # Act: Execute mission without intent (auto-select)
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=None,  # Auto-select from backlog
        two_stage=False
    )

    # Assert: Mission selected from backlog
    assert result.is_ok()
    mission_result = result.unwrap()

    assert mission_result.get("auto_selected") is True
    assert mission_result.get("selected_from") == "backlog"
    assert "NoneType" in mission_result.get("intent", "") or \
           mission_result.get("priority") == 1


# =============================================================================
# VALIDATION TESTS
# =============================================================================


@pytest.mark.e2e
def test_mission_queries_vectorstore_before_action(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission queries VectorStore for patterns before implementation (Article IV).

    Pattern: NECESSARY - Validation
    Constitutional: Article IV (VectorStore integration mandatory)
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Store relevant pattern in VectorStore
    full_agent_context.store_memory(
        key="pattern_type_hints",
        content={
            "pattern": "Add type hints using mypy",
            "success_rate": 0.95,
            "example": "def func(x: int) -> str:"
        },
        tags=["pattern", "type_hints", "success"]
    )

    # Act: Execute mission requiring type hints
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent="Add type hints to calculate_total function",
        two_stage=False
    )

    # Assert: Mission queried VectorStore
    assert result.is_ok()
    mission_result = result.unwrap()

    assert mission_result.get("vectorstore_queried") is True
    assert mission_result.get("patterns_found") > 0

    # Assert: Relevant pattern was used
    patterns_used = mission_result.get("patterns_used", [])
    assert any("type_hints" in p for p in patterns_used)


@pytest.mark.e2e
def test_mission_stores_patterns_after_success(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission stores successful patterns to VectorStore (Article IV).

    Pattern: NECESSARY - Validation
    Constitutional: Article IV (learning mandatory)
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Act: Execute successful mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent="Fix typo in docstring",
        two_stage=False
    )

    # Assert: Mission succeeded
    assert result.is_ok()
    mission_result = result.unwrap()
    assert mission_result.get("status") == "complete"

    # Assert: Pattern stored in VectorStore
    assert mission_result.get("pattern_stored") is True

    # Verify: Pattern can be retrieved
    learnings = full_agent_context.search_memories(
        tags=["mission", "success"],
        query="docstring typo fix"
    )
    assert len(learnings) > 0


@pytest.mark.e2e
def test_mission_complies_with_tdd_workflow(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission follows TDD: tests BEFORE implementation (Article VI).

    Pattern: NECESSARY - Validation
    Constitutional: Article VI (TDD mandatory)
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent="Add validation function for email addresses",
        two_stage=False
    )

    # Assert: Tests written first
    assert result.is_ok()
    mission_result = result.unwrap()

    # Assert: TDD workflow followed
    workflow = mission_result.get("workflow", [])
    test_index = next((i for i, phase in enumerate(workflow) if phase == "test_generation"), -1)
    code_index = next((i for i, phase in enumerate(workflow) if phase == "code_generation"), -1)

    assert test_index != -1, "Tests must be generated"
    assert code_index != -1, "Code must be generated"
    assert test_index < code_index, "Tests MUST come before code (TDD)"

    # Assert: Tests failed initially (RED phase)
    assert mission_result.get("initial_test_status") == "failing"

    # Assert: Tests pass after implementation (GREEN phase)
    assert mission_result.get("final_test_status") == "passing"


# =============================================================================
# ERROR CONDITION TESTS
# =============================================================================


@pytest.mark.e2e
def test_mission_handles_test_failure_gracefully(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission handles test failures with rollback.

    Pattern: NECESSARY - Error condition
    Validates: Failure recovery and error reporting
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Mission that will generate failing tests
    mission_intent = "Implement complex algorithm with edge cases"

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=mission_intent,
        two_stage=False
    )

    # If tests fail, mission should report error
    if result.is_err():
        error = result.error

        # Assert: Error is descriptive
        assert "test" in str(error).lower()
        assert error.get("failed_tests") is not None

        # Assert: Rollback occurred
        assert error.get("rollback_completed") is True

    # If mission succeeds, tests must be passing
    else:
        mission_result = result.unwrap()
        assert mission_result.get("tests_passing") is True


@pytest.mark.e2e
def test_mission_handles_missing_dependencies(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission handles missing dependencies gracefully.

    Pattern: NECESSARY - Error condition
    Validates: Dependency validation
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Mission requiring nonexistent dependency
    mission_intent = "Use nonexistent library XYZ for task"

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent=mission_intent,
        two_stage=False
    )

    # Assert: Mission detects missing dependency
    if result.is_err():
        error = result.error
        assert "dependency" in str(error).lower() or "import" in str(error).lower()


# =============================================================================
# REGRESSION TESTS
# =============================================================================


@pytest.mark.e2e
def test_mission_doesnt_break_existing_tests(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission doesn't introduce regressions to existing test suite.

    Pattern: NECESSARY - Regression
    Validates: Test suite stability
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Run tests before mission
    result_before = subprocess.run(
        ["pytest", "tests/", "--co", "-q"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    )
    tests_before = len(result_before.stdout.strip().split("\n"))

    # Act: Execute mission
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent="Add new utility function",
        two_stage=False
    )

    # Assert: Existing tests still exist
    result_after = subprocess.run(
        ["pytest", "tests/", "--co", "-q"],
        cwd=tmp_git_repo,
        capture_output=True,
        text=True
    )
    tests_after = len(result_after.stdout.strip().split("\n"))

    assert tests_after >= tests_before, "Mission should not delete existing tests"


# =============================================================================
# STRESS TESTS
# =============================================================================


@pytest.mark.e2e
@pytest.mark.slow
def test_mission_handles_large_codebase(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission scales to large codebases.

    Pattern: NECESSARY - Stress
    Validates: Performance with realistic codebase size
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Create large codebase (100 files)
    for i in range(100):
        module_file = tmp_git_repo / "modules" / f"module_{i}.py"
        module_file.parent.mkdir(exist_ok=True)
        module_file.write_text(f"""
def function_{i}(x: int) -> int:
    return x * {i}
""")

    # Act: Execute mission in large codebase
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo
    )

    result = orchestrator.execute_mission(
        intent="Add logging to module_50",
        two_stage=False
    )

    # Assert: Mission completes despite large codebase
    assert result.is_ok()
    mission_result = result.unwrap()
    assert mission_result.get("status") == "complete"


# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================


@pytest.mark.e2e
def test_mission_provides_progress_updates(full_agent_context, tmp_git_repo, mock_openai_api):
    """
    Verify mission provides real-time progress updates.

    Pattern: NECESSARY - Accessibility
    Validates: User experience and transparency
    """
    from tools.orchestrator.prime_a_orchestrator import PrimeAOrchestrator

    # Arrange: Progress callback
    progress_updates = []

    def progress_callback(phase: str, status: str):
        progress_updates.append({"phase": phase, "status": status})

    # Act: Execute mission with progress tracking
    orchestrator = PrimeAOrchestrator(
        agent_context=full_agent_context,
        working_dir=tmp_git_repo,
        progress_callback=progress_callback
    )

    result = orchestrator.execute_mission(
        intent="Add feature X",
        two_stage=False
    )

    # Assert: Progress updates received
    assert len(progress_updates) > 0

    # Assert: Key phases reported
    phases = [update["phase"] for update in progress_updates]
    assert "scout" in phases or "plan" in phases
    assert "test" in phases
    assert "code" in phases
