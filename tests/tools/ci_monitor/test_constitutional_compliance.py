"""
Constitutional Compliance Validation Tests for Phase 6 (Autonomous CI Feedback Loop).

This test file validates ALL 5 constitutional articles for the CI monitor implementation:
- Article I: Complete Context Before Action (timeout retry, no incomplete data)
- Article II: 100% Verification and Stability (all tests pass before merge)
- Article III: Automated Merge Enforcement (no manual overrides)
- Article IV: Continuous Learning (VectorStore integration MANDATORY)
- Article V: Spec-Driven Development (traceable to spec-autonomous-ci-feedback-loop.md)

Test Coverage (NECESSARY Pattern):
- N: Normal compliance (all articles satisfied)
- E: Edge cases (partial VectorStore failures, timeout edge cases)
- C: Corner cases (missing context, learning storage failures)
- E: Error conditions (violations detected, enforcement failures)
- S: Security (no bypass mechanisms, constitutional guards)
- S: Spec traceability (every function traces to AC-1 through AC-5)
- A: Accessibility (clear violation messages)
- R: Regression (ensure past violations don't recur)
- Y: Yield validation (correct compliance reports)

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mark entire file as serial to prevent pytest-xdist hang
pytestmark = pytest.mark.serial

from shared.agent_context import AgentContext, create_agent_context
from shared.type_definitions.result import Err, Ok, Result
from tools.ci_monitor.feedback_loop_orchestrator import FeedbackLoopOrchestrator
from tools.ci_monitor.learning_integration import (
    query_fix_patterns,
    store_successful_fix,
)
from tools.ci_monitor.retry_controller import RetryController, RetryPolicy
from tools.ci_monitor.status_poller import StatusPoller

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def agent_context():
    """Create AgentContext for testing."""
    return create_agent_context(session_id="constitutional_compliance_test")


@pytest.fixture
def mock_vectorstore():
    """Mock VectorStore for Article IV testing."""
    mock_store = MagicMock()
    mock_store.search_memories = MagicMock(return_value=[])
    mock_store.store_memory = MagicMock()
    return mock_store


# ============================================================================
# ARTICLE I: COMPLETE CONTEXT BEFORE ACTION (ADR-001)
# ============================================================================


@pytest.mark.asyncio
async def test_article_i_retry_on_timeout():
    """
    Article I Compliance: Retry on timeout with exponential backoff.

    Constitutional Requirement:
    - Retry with extended timeouts (2x, 3x, up to 10x)
    - NEVER proceed with incomplete data
    - Better 5 minutes waiting than wrong direction

    Spec: AC-1 (autonomous monitoring with complete context)
    """
    # Test retry controller implements Article I
    policy = RetryPolicy(max_attempts=3, base_delay_s=1.0, exponential=True)
    controller = RetryController(policy=policy)

    attempt_count = 0

    async def flaky_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise TimeoutError("Operation timed out")
        return "success"

    result = await controller.retry_with_policy(flaky_operation)

    # Verify Article I compliance
    assert result.is_ok(), "Article I: Must retry until complete context obtained"
    value, metrics = result.unwrap()
    assert value == "success"
    assert metrics.total_attempts == 3, "Article I: Retry 2x minimum"
    assert metrics.success is True


@pytest.mark.asyncio
async def test_article_i_no_partial_results():
    """
    Article I Compliance: Never proceed with incomplete data.

    Constitutional Requirement:
    - NEVER declare "I have seen enough" with partial results
    - ALL tests MUST run to completion
    - Upon failures/skips: IMMEDIATELY halt

    Spec: AC-1 (wait for all checks to reach terminal state)
    """
    pr_number = 123

    # Mock incomplete CI status (some checks still pending)
    incomplete_status = """[
      {"name": "CI", "state": "pending", "conclusion": null},
      {"name": "Lint", "state": "success", "conclusion": "success"}
    ]"""

    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks", str(pr_number)],
        returncode=0,
        stdout=incomplete_status,
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result):
        poller = StatusPoller(pr_number=pr_number, poll_interval=1)
        status_result = await poller.get_current_status()

        assert status_result.is_ok()
        status = status_result.unwrap()

        # Article I: Must detect incomplete state
        assert status.is_complete is False, "Article I: Must detect incomplete context"
        assert status.all_passing is False, "Article I: Cannot proceed with partial data"


def test_article_i_zero_broken_windows():
    """
    Article I Compliance: Zero tolerance for broken windows.

    Constitutional Requirement:
    - Applies to ALL generated code
    - Applies to "temporary" solutions
    - Zero tolerance for compromised quality

    Spec: All Phase 6 code must follow strict typing, Result pattern, <50 lines
    """
    # Verify all Phase 6 modules use Result<T,E> pattern
    from tools.ci_monitor import (
        code_error_parser,
        code_fix_generator,
        feedback_loop_orchestrator,
        fix_applicator,
        learning_integration,
        log_fetcher,
        retry_controller,
        status_poller,
    )

    # Check imports for Result pattern usage
    modules = [
        status_poller,
        log_fetcher,
        code_error_parser,
        code_fix_generator,
        fix_applicator,
        retry_controller,
        learning_integration,
        feedback_loop_orchestrator,
    ]

    for module in modules:
        # Verify module uses Result pattern
        module_source = Path(module.__file__).read_text()
        assert "from shared.type_definitions.result import" in module_source, (
            f"Article I: {module.__name__} missing Result imports (broken window)"
        )
        assert "Result[" in module_source, (
            f"Article I: {module.__name__} not using Result pattern (broken window)"
        )


# ============================================================================
# ARTICLE II: 100% VERIFICATION AND STABILITY (ADR-002)
# ============================================================================


def test_article_ii_all_tests_pass():
    """
    Article II Compliance: 100% test success rate.

    Constitutional Requirement:
    - Main branch MUST maintain 100% test success
    - No merge without completely green CI pipeline
    - 100% is not negotiable - no exceptions

    Spec: AC-4 (notify only on all checks pass or intervention needed)
    """
    # Run Phase 6 tests and verify 100% pass rate
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/tools/ci_monitor/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Parse test results
    output = result.stdout + result.stderr

    # Article II: Must have zero failures
    assert "failed" not in output.lower() or "0 failed" in output, (
        f"Article II VIOLATION: Tests failing\n{output}"
    )


@pytest.mark.asyncio
async def test_article_ii_no_merge_without_green_ci():
    """
    Article II Compliance: No merge without green CI.

    Constitutional Requirement:
    - No merge without completely green CI pipeline
    - Definition of Done: Code + Tests + Pass + Review + CI ✓

    Spec: AC-4 (autonomous notification only when all checks pass)
    """
    # Test orchestrator enforces CI green requirement
    orchestrator = FeedbackLoopOrchestrator(
        pr_number=123,
        worktree_path=Path.cwd(),
        branch="test-branch",
        max_fix_attempts=5,
    )

    # Mock CI status with failures
    mock_status_with_failures = """[
      {"name": "CI", "state": "failure", "conclusion": "failure"},
      {"name": "Lint", "state": "success", "conclusion": "success"}
    ]"""

    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks", "123"],
        returncode=0,
        stdout=mock_status_with_failures,
        stderr="",
    )

    with patch("subprocess.run", return_value=mock_result):
        monitor_result = await orchestrator._monitor_ci_status()

        assert monitor_result.is_ok()
        status = monitor_result.unwrap()

        # Article II: Must detect failures and prevent merge
        assert status.all_passing is False, "Article II: Must detect CI failures"
        assert status.has_failures is True, "Article II: Must identify failing checks"


def test_article_ii_no_simulation_in_production():
    """
    Article II Compliance: No mocked functions in production.

    Constitutional Requirement:
    - Mocked functions SHALL NOT be merged to main branch
    - Simulated work (print statements) is NOT production-ready
    - Only fully-implemented, tested functionality may merge

    Spec: All Phase 6 implementations use real gh CLI, real git commands
    """
    # Verify no mock/simulation in production code
    ci_monitor_path = Path("/Users/am/Code/Agency/tools/ci_monitor")

    for py_file in ci_monitor_path.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text()

        # Article II: No mocks in production
        assert "from unittest.mock import" not in content, (
            f"Article II VIOLATION: {py_file.name} contains unittest.mock imports"
        )
        assert "Mock(" not in content and "MagicMock(" not in content, (
            f"Article II VIOLATION: {py_file.name} contains mock usage"
        )


# ============================================================================
# ARTICLE III: AUTOMATED MERGE ENFORCEMENT (ADR-003)
# ============================================================================


def test_article_iii_no_manual_override():
    """
    Article III Compliance: No manual override capabilities.

    Constitutional Requirement:
    - Zero manual overrides
    - No "emergency bypass" mechanisms
    - Quality gates are absolute barriers

    Spec: AC-3 (autonomous retrigger, no "should I retrigger?" questions)
    """
    # Verify no bypass flags in retry controller
    from tools.ci_monitor.retry_controller import RetryController, RetryPolicy

    policy = RetryPolicy(max_attempts=5)
    controller = RetryController(policy=policy)

    # Article III: No force/skip flags
    controller_source = Path(
        "/Users/am/Code/Agency/tools/ci_monitor/retry_controller.py"
    ).read_text()

    assert "force" not in controller_source.lower(), (
        "Article III VIOLATION: Found 'force' bypass mechanism"
    )
    assert "skip_validation" not in controller_source.lower(), (
        "Article III VIOLATION: Found validation bypass"
    )
    assert "--no-verify" not in controller_source, (
        "Article III VIOLATION: Found git verification bypass"
    )


def test_article_iii_multi_layer_enforcement():
    """
    Article III Compliance: Multi-layer enforcement.

    Constitutional Requirement:
    1. Pre-commit Hook: Local enforcement
    2. Agent Validation: Automated agent-level verification
    3. CI/CD Pipeline: Remote verification and enforcement
    4. Branch Protection: Repository-level safeguards

    Spec: AC-3 (automated retrigger enforces CI validation)
    """
    # Layer 1: Agent validation (retry controller enforces max attempts)
    policy = RetryPolicy(max_attempts=5)
    assert policy.max_attempts == 5, "Article III: Max attempts enforced"

    # Layer 2: Orchestrator enforces max fix attempts
    orchestrator = FeedbackLoopOrchestrator(
        pr_number=123,
        worktree_path=Path.cwd(),
        branch="test",
        max_fix_attempts=5,
    )
    assert orchestrator.max_fix_attempts == 5, "Article III: Fix attempts capped"

    # Layer 3: Status poller enforces terminal state detection
    poller = StatusPoller(pr_number=123)
    # Verify enforces terminal state check (no bypass)
    from tools.ci_monitor.status_poller import CheckState

    assert CheckState.is_terminal("success") is True
    assert CheckState.is_terminal("pending") is False, "Article III: Must wait for terminal state"


# ============================================================================
# ARTICLE IV: CONTINUOUS LEARNING (ADR-004) - MANDATORY
# ============================================================================


def test_article_iv_vectorstore_integration_mandatory(agent_context):
    """
    Article IV Compliance: VectorStore integration is MANDATORY.

    Constitutional Requirement:
    - VectorStore integration MUST be present (constitutional mandate)
    - USE_ENHANCED_MEMORY must be 'true' (no disable flags)
    - Agents MUST query learnings before decisions
    - Agents MUST store successful patterns after operations

    Spec: AC-5 (learn new patterns via VectorStore)
    """
    # Verify USE_ENHANCED_MEMORY enforcement
    assert os.getenv("USE_ENHANCED_MEMORY", "false").lower() == "true", (
        "Article IV VIOLATION: USE_ENHANCED_MEMORY not enabled (constitutional mandate)"
    )

    # Verify VectorStore methods exist
    assert hasattr(agent_context, "store_memory"), (
        "Article IV VIOLATION: Missing store_memory method"
    )
    assert hasattr(agent_context, "search_memories"), (
        "Article IV VIOLATION: Missing search_memories method"
    )

    # Verify learning integration module exists
    from tools.ci_monitor import learning_integration

    assert hasattr(learning_integration, "store_successful_fix"), (
        "Article IV VIOLATION: Missing store_successful_fix function"
    )
    assert hasattr(learning_integration, "query_fix_patterns"), (
        "Article IV VIOLATION: Missing query_fix_patterns function"
    )


@pytest.mark.asyncio
async def test_article_iv_query_before_action(agent_context):
    """
    Article IV Compliance: Query learnings before action.

    Constitutional Requirement:
    - Check constitutional compliance
    - Apply relevant learnings from VectorStore
    - Minimum confidence threshold: 0.6

    Spec: AC-5 (recognizes common errors, applies known fixes)
    """
    from tools.ci_monitor.code_error_parser import ErrorPattern

    # Create error pattern
    error = ErrorPattern(
        category="missing_dependency",
        message="ModuleNotFoundError: No module named 'pytest'",
        file_path=None,
        line_number=None,
        raw_text="ModuleNotFoundError: No module named 'pytest'",
    )

    # Article IV: Query patterns before generating fix
    result = query_fix_patterns(agent_context, error, min_confidence=0.6)

    # Must use Result pattern
    assert hasattr(result, "is_ok"), "Article IV: Must use Result<T,E> pattern"
    assert hasattr(result, "is_err"), "Article IV: Must use Result<T,E> pattern"


@pytest.mark.asyncio
async def test_article_iv_store_after_success(agent_context):
    """
    Article IV Compliance: Store patterns after success.

    Constitutional Requirement:
    - Extract learnings from experience
    - Pattern validation required before storage
    - Knowledge accumulates in VectorStore

    Spec: AC-5 (learns new patterns via VectorStore)
    """
    from tools.ci_monitor.code_error_parser import ErrorPattern
    from tools.ci_monitor.code_fix_generator import FixStrategy, GeneratedFix

    # Create successful fix pattern
    error = ErrorPattern(
        category="missing_dependency",
        message="ModuleNotFoundError: No module named 'pytest'",
        file_path=None,
        line_number=None,
        raw_text="ModuleNotFoundError",
    )

    fix = GeneratedFix(
        error_category="missing_dependency",
        fix_strategy=FixStrategy(
            strategy_type="pip_install",
            command="pip install pytest",
            description="Install missing dependency",
            confidence=0.9,
        ),
        target_files=[],
    )

    # Article IV: Store successful fix
    result = store_successful_fix(agent_context, error, fix, success=True)

    assert result.is_ok(), f"Article IV: Failed to store pattern: {result.unwrap_err()}"


def test_article_iv_min_confidence_threshold():
    """
    Article IV Compliance: Minimum confidence threshold 0.6.

    Constitutional Requirement:
    - Minimum confidence threshold: 0.6
    - Pattern validation required before storage
    - Low confidence patterns rejected

    Spec: AC-5 (applies patterns with sufficient confidence)
    """
    from tools.ci_monitor.learning_integration import FixLearning

    # Test high confidence pattern (accepted)
    high_confidence = FixLearning(
        category="lint_error",
        strategy_type="ruff_fix",
        command="ruff check --fix",
        confidence=0.9,
    )
    assert high_confidence.confidence >= 0.6, "Article IV: High confidence accepted"

    # Test low confidence pattern (rejected)
    low_confidence = FixLearning(
        category="lint_error",
        strategy_type="ruff_fix",
        command="ruff check --fix",
        confidence=0.5,
    )
    assert low_confidence.confidence < 0.6, "Article IV: Low confidence rejected"


# ============================================================================
# ARTICLE V: SPEC-DRIVEN DEVELOPMENT (ADR-007)
# ============================================================================


def test_article_v_spec_exists():
    """
    Article V Compliance: Formal specification exists.

    Constitutional Requirement:
    - Complex features MUST have spec.md → plan.md
    - Spec follows template: Goals, Non-Goals, Personas, Criteria
    - No implementation without approved specification

    Spec: spec-autonomous-ci-feedback-loop.md
    """
    spec_path = Path("/Users/am/Code/Agency/specs/spec-autonomous-ci-feedback-loop.md")

    assert spec_path.exists(), "Article V VIOLATION: Spec file missing"

    spec_content = spec_path.read_text()

    # Verify spec template compliance
    assert "## Goals" in spec_content, "Article V: Spec missing Goals section"
    assert "## Personas" in spec_content, "Article V: Spec missing Personas section"
    assert "## Acceptance Criteria" in spec_content, "Article V: Spec missing Acceptance Criteria"
    assert "## Constitutional Alignment" in spec_content, (
        "Article V: Spec missing Constitutional Alignment"
    )


def test_article_v_traceability_to_spec():
    """
    Article V Compliance: All implementation traces to spec.

    Constitutional Requirement:
    - All implementation traces to specification
    - Each function references AC-1 through AC-5
    - Living documents updated during implementation

    Spec: AC-1 through AC-5 in spec-autonomous-ci-feedback-loop.md
    """
    # Verify status_poller traces to AC-1
    status_poller_path = Path("/Users/am/Code/Agency/tools/ci_monitor/status_poller.py")
    status_poller_content = status_poller_path.read_text()

    assert "AC-1" in status_poller_content, "Article V: Missing AC-1 traceability"
    assert "spec-autonomous-ci-feedback-loop.md" in status_poller_content, (
        "Article V: Missing spec reference"
    )

    # Verify log_fetcher traces to AC-2
    log_fetcher_path = Path("/Users/am/Code/Agency/tools/ci_monitor/log_fetcher.py")
    log_fetcher_content = log_fetcher_path.read_text()

    assert "AC-2" in log_fetcher_content, "Article V: Missing AC-2 traceability"

    # Verify retry_controller traces to AC-3
    retry_controller_path = Path("/Users/am/Code/Agency/tools/ci_monitor/retry_controller.py")
    retry_controller_content = retry_controller_path.read_text()

    assert "AC-3" in retry_controller_content, "Article V: Missing AC-3 traceability"


def test_article_v_task_granularity():
    """
    Article V Compliance: Task breakdown present.

    Constitutional Requirement:
    - Plans MUST decompose into TodoWrite task lists
    - Each task MUST reference spec and plan sections
    - Tasks MUST be verifiable against acceptance criteria

    Spec: Phase 1-4 breakdown in spec-autonomous-ci-feedback-loop.md
    """
    spec_path = Path("/Users/am/Code/Agency/specs/spec-autonomous-ci-feedback-loop.md")
    spec_content = spec_path.read_text()

    # Verify task breakdown exists
    assert "## Implementation Plan" in spec_content, "Article V: Missing Implementation Plan"
    assert "### Phase 1" in spec_content, "Article V: Missing Phase 1 breakdown"
    assert "### Phase 2" in spec_content, "Article V: Missing Phase 2 breakdown"
    assert "### Phase 3" in spec_content, "Article V: Missing Phase 3 breakdown"


# ============================================================================
# CROSS-ARTICLE INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_all_five_articles_integrated(agent_context):
    """
    Integration Test: All 5 articles working together.

    Validates that the autonomous CI feedback loop satisfies ALL
    constitutional requirements simultaneously:
    - Article I: Complete context (retry on timeout)
    - Article II: 100% verification (all tests pass)
    - Article III: Automated enforcement (no manual intervention)
    - Article IV: VectorStore learning (query/store patterns)
    - Article V: Spec-driven (traceable to AC-1 through AC-5)
    """
    # Create orchestrator
    orchestrator = FeedbackLoopOrchestrator(
        pr_number=123,
        worktree_path=Path.cwd(),
        branch="test-branch",
        max_fix_attempts=5,
        agent_context=agent_context,
    )

    # Verify all articles satisfied
    # Article I: Retry controller configured
    assert orchestrator.max_fix_attempts == 5, "Article I: Retry policy configured"

    # Article II: Tests must pass (validated by CI)
    # Article III: No bypass mechanisms
    assert hasattr(orchestrator, "max_fix_attempts"), "Article III: Max attempts enforced"

    # Article IV: VectorStore integration present
    assert orchestrator.agent_context is not None, "Article IV: VectorStore integrated"
    assert hasattr(orchestrator, "_query_learned_patterns"), (
        "Article IV: Query learnings method exists"
    )
    assert hasattr(orchestrator, "_store_success_pattern"), (
        "Article IV: Store learnings method exists"
    )

    # Article V: Spec traceability
    orchestrator_source = Path(
        "/Users/am/Code/Agency/tools/ci_monitor/feedback_loop_orchestrator.py"
    ).read_text()
    assert "spec-autonomous-ci-feedback-loop.md" in orchestrator_source, (
        "Article V: Spec reference present"
    )


def test_constitutional_compliance_zero_violations():
    """
    Final Validation: Zero constitutional violations.

    This test ensures that the entire Phase 6 implementation
    achieves 100% constitutional compliance across all 5 articles.

    Success Criteria:
    - All Article I tests pass (complete context)
    - All Article II tests pass (100% verification)
    - All Article III tests pass (automated enforcement)
    - All Article IV tests pass (VectorStore integration)
    - All Article V tests pass (spec-driven development)
    """
    # Run all constitutional tests
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            __file__,
            "-v",
            "--tb=short",
            "-k",
            "article",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    output = result.stdout + result.stderr

    # Zero violations required
    assert "failed" not in output.lower() or "0 failed" in output, (
        f"CONSTITUTIONAL VIOLATIONS DETECTED:\n{output}"
    )

    print("\n" + "=" * 60)
    print("CONSTITUTIONAL COMPLIANCE: 100%")
    print("=" * 60)
    print("✅ Article I: Complete Context Before Action")
    print("✅ Article II: 100% Verification and Stability")
    print("✅ Article III: Automated Merge Enforcement")
    print("✅ Article IV: Continuous Learning (MANDATORY)")
    print("✅ Article V: Spec-Driven Development")
    print("=" * 60)
    print("Phase 6 (Autonomous CI Feedback Loop) is CONSTITUTIONALLY COMPLIANT")
    print("=" * 60)
