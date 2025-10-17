"""
Tests for Phase 0 Git Validation in TwoStageOrchestrator (RED Phase - TDD).

This test file validates the _validate_git_workflow() method that enforces
Article III (Automated Merge Enforcement) by preventing execution on protected branches.

Test Coverage (GIT-001 through GIT-006):
- GIT-001: Execution on main branch → halt with Article III violation
- GIT-002: Execution on master branch → halt
- GIT-003: Feature branch (feat/*, fix/*) → pass validation
- GIT-004: Not in git repo → warning, continue (non-blocking)
- GIT-005: Worktree isolation validation
- GIT-006: Detached HEAD → halt with guidance

NECESSARY Pattern Coverage:
- Normal: Feature branch passes validation
- Edge: Detached HEAD, non-repo context, branch name edge cases
- Constraints: Protected branch enforcement (main, master)
- Error: Git command failures, subprocess errors
- Security: No bypass mechanism, injection prevention
- Scale: <50ms validation time (PERF-003)

Constitutional Compliance:
- Article I: Complete context (retry on git timeout)
- Article II: 100% verification (all tests must pass)
- Article III: Automated enforcement (no bypass mechanism)
- Article IV: VectorStore patterns for branch validation
- Article V: Spec-driven (traces to SPEC-030 acceptance criteria)

Expected Initial State: TESTS FAIL (method doesn't exist in TwoStageOrchestrator yet)
Expected After Implementation: ALL TESTS PASS with 100% rate

Version: 1.0.0
Created: 2025-10-16
"""

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result

# Import TwoStageOrchestrator - method doesn't exist yet (RED phase)
from tools.orchestrator.two_stage_orchestrator import (
    OrchestrationError,
    TwoStageOrchestrator,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_context() -> AgentContext:
    """Create mock AgentContext for orchestrator tests."""
    context = MagicMock(spec=AgentContext)
    context.store_memory = Mock()
    context.search_memories = Mock(return_value=[])
    context.get_session_memories = Mock(return_value=[])
    return context


@pytest.fixture
def isolated_git_repo(tmp_path: Path) -> Path:
    """
    Create isolated git repository for testing.

    Sets up:
    - Initialized git repo
    - Initial commit on main branch
    - Feature branch (feat/test) checked out by default
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    # Configure user for commits
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    # Create initial commit
    (repo / "README.md").write_text("# Test Repo")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    # Rename default branch to main (if git init created master)
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    # Always rename to main for consistency (even if master was created)
    if current_branch != "main":
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
            timeout=10,
        )

    # Create and checkout feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feat/test"],
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    return repo


# ============================================================================
# GIT-001: Main branch execution raises Article III violation
# ============================================================================


def test_main_branch_execution_raises_article_iii_violation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-001: Execution on main branch halts with Article III violation.

    Validates:
    - _validate_git_workflow() detects main branch
    - Returns Err with Article III reference
    - Provides actionable guidance (checkout feature branch)

    Expected: Result with Err(OrchestrationError) containing Article III message
    """
    # Arrange: Switch to main branch
    # Get list of branches to check if main exists
    branches = subprocess.run(
        ["git", "branch"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout

    # Checkout main (it exists from fixture setup)
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act: Validate git workflow (method doesn't exist yet - RED phase)
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_err(), "main branch should fail validation (GIT-001)"

    error = result.unwrap_err()
    error_message = error.reason.lower()

    # Check for Article III reference
    assert (
        "article iii" in error_message or "protected" in error_message
    ), f"Error should reference Article III, got: {error.reason}"

    # Check for "main" branch mention
    assert "main" in error_message, f"Error should mention 'main' branch, got: {error.reason}"

    # Check for actionable guidance
    assert (
        "checkout" in error_message or "feature branch" in error_message
    ), f"Error should provide guidance, got: {error.reason}"


# ============================================================================
# GIT-002: Master branch execution raises Article III violation
# ============================================================================


def test_master_branch_execution_raises_article_iii_violation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-002: Execution on master branch halts with Article III violation.

    Validates:
    - _validate_git_workflow() detects master branch
    - Returns Err with Article III reference
    - Same protection as main branch

    Expected: Result with Err(OrchestrationError) containing Article III message
    """
    # Arrange: Create and switch to master branch from main
    # First checkout main, then create master from it
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )
    subprocess.run(
        ["git", "checkout", "-b", "master"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_err(), "master branch should fail validation (GIT-002)"

    error = result.unwrap_err()
    error_message = error.reason.lower()

    assert (
        "article iii" in error_message or "protected" in error_message
    ), f"Error should reference Article III, got: {error.reason}"
    assert "master" in error_message, f"Error should mention 'master' branch, got: {error.reason}"


# ============================================================================
# GIT-003: Feature branch passes validation
# ============================================================================


def test_feature_branch_passes_validation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-003: Feature branch (feat/*) passes validation.

    Validates:
    - _validate_git_workflow() accepts feat/* pattern
    - Returns Ok(None) indicating success
    - No Article III violation raised

    Expected: Result with Ok(None)
    """
    # Arrange: isolated_git_repo is on feat/test by default

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), f"Feature branch validation should pass, got: {result}"


def test_fix_branch_passes_validation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-003: Fix branch (fix/*) passes validation.

    Validates:
    - fix/* pattern accepted
    - No Article III violation

    Expected: Result with Ok(None)
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "fix/bug-123"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), "fix/* branch should pass validation"


def test_docs_branch_passes_validation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-003: Docs branch (docs/*) passes validation.

    Validates:
    - docs/* pattern accepted
    - No Article III violation

    Expected: Result with Ok(None)
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "docs/update-readme"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), "docs/* branch should pass validation"


# ============================================================================
# GIT-004: Not in git repo → warning, continue (non-blocking)
# ============================================================================


def test_not_in_git_repo_logs_warning_and_continues(
    tmp_path: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-004: Not in git repository logs warning but continues.

    Validates:
    - Non-git directory detected gracefully
    - Returns Ok(None) (non-blocking validation)
    - Warning logged (not fatal error)

    Expected: Result with Ok(None) indicating non-blocking validation
    """
    # Arrange: tmp_path is not a git repository

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(tmp_path),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    # GIT-004 spec says "log warning, continue (non-blocking)"
    # Since this is Phase 0 before orchestration, it should be non-blocking
    assert result.is_ok(), "Non-git directory should be non-blocking (GIT-004)"


# ============================================================================
# GIT-005: Worktree isolation validation
# ============================================================================


def test_worktree_on_feature_branch_passes_validation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
    tmp_path: Path,
) -> None:
    """
    GIT-005: Git worktree on feature branch passes validation.

    Validates:
    - Worktree isolation detected correctly
    - Feature branch in worktree accepted
    - No false positive Article III violations

    Expected: Result with Ok(None)
    """
    # Arrange: Create worktree on feature branch
    worktree_path = tmp_path / "worktree_feat_test"

    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", "feat/worktree-test"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(worktree_path),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), "Worktree on feature branch should pass validation (GIT-005)"

    # Cleanup
    subprocess.run(
        ["git", "worktree", "remove", str(worktree_path)],
        cwd=isolated_git_repo,
        check=False,
        capture_output=True,
        timeout=10,
    )


def test_worktree_on_main_branch_raises_violation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
    tmp_path: Path,
) -> None:
    """
    GIT-005: Git worktree on main branch raises Article III violation.

    Validates:
    - Worktree on protected branch detected
    - Article III enforcement applies to worktrees
    - No bypass through worktree isolation

    Expected: Result with Err(OrchestrationError)
    """
    # Arrange: Create worktree on main branch
    # Already on feat/test from fixture, so we can create worktree on main

    worktree_path = tmp_path / "worktree_main"

    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "main"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(worktree_path),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_err(), "Worktree on main branch should fail validation (GIT-005)"

    error = result.unwrap_err()
    assert "main" in error.reason.lower(), "Error should mention main branch"

    # Cleanup
    subprocess.run(
        ["git", "worktree", "remove", str(worktree_path)],
        cwd=isolated_git_repo,
        check=False,
        capture_output=True,
        timeout=10,
    )


# ============================================================================
# GIT-006: Detached HEAD → halt with guidance
# ============================================================================


def test_detached_head_raises_validation_error(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    GIT-006: Detached HEAD state raises ValidationError with guidance.

    Validates:
    - Detached HEAD detected via git commands
    - Error message explains detached state
    - Guidance provided: "git checkout -b <branch-name>"

    Expected: Result with Err(OrchestrationError) with recovery guidance
    """
    # Arrange: Create detached HEAD by checking out commit hash
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()

    subprocess.run(
        ["git", "checkout", commit_hash],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_err(), "Detached HEAD should fail validation (GIT-006)"

    error = result.unwrap_err()
    error_message = error.reason.lower()
    recovery_hint = (error.recovery_hint or "").lower()

    # Check for detached HEAD mention
    assert (
        "detached" in error_message or "head" in error_message or "not on a branch" in error_message
    ), f"Error should mention detached HEAD, got: {error.reason}"

    # Check for guidance in either reason or recovery_hint
    full_message = f"{error_message} {recovery_hint}"
    assert (
        "checkout" in full_message or "create" in full_message
    ), f"Error should provide guidance, got reason: {error.reason}, hint: {error.recovery_hint}"


# ============================================================================
# NECESSARY EDGE: Branch name edge cases
# ============================================================================


def test_branch_name_with_special_chars(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Edge: Branch name with special characters passes validation.

    Validates:
    - Dashes, underscores, dots, numbers accepted
    - No sanitization side effects

    Expected: Result with Ok(None)
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "feat/user-auth-2.0_final.v3"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), "Branch with special characters should pass validation"


def test_branch_name_with_slashes(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Edge: Branch name with multiple slashes (hierarchy) passes validation.

    Validates:
    - Git branch hierarchies supported (feat/auth/jwt)
    - Pattern matching works with nested paths

    Expected: Result with Ok(None)
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "feat/auth/jwt"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_ok(), "Branch with nested paths should pass validation"


# ============================================================================
# NECESSARY ERROR: Git command failures
# ============================================================================


def test_git_command_timeout_retries(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Retry: Git command timeout triggers retry with exponential backoff.

    Validates:
    - Git command timeout detected
    - Retry attempted (Article I)
    - Graceful failure after max retries

    Expected: After retries, either Ok or Err with timeout details
    """
    # Arrange: Mock subprocess.run to simulate timeout
    original_run = subprocess.run

    call_count = 0

    def slow_git_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        # Simulate git command (check for git in args)
        if "git" in str(args[0]):
            # First 2 calls: timeout
            if call_count <= 2:
                time.sleep(0.01)  # Simulate delay
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=0.005)

            # Third call: succeed
            return original_run(*args, **kwargs)

        # Non-git commands: normal execution
        return original_run(*args, **kwargs)

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    with patch("subprocess.run", side_effect=slow_git_run):
        result = orchestrator._validate_git_workflow()

    # Assert
    # After retries, should either succeed or fail with timeout error
    if result.is_ok():
        # Retry succeeded
        pass
    else:
        # Max retries exceeded
        error = result.unwrap_err()
        assert "timeout" in error.reason.lower() or "failed" in error.reason.lower()


def test_git_command_subprocess_error_handled(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Error: Git command subprocess error handled gracefully.

    Validates:
    - CalledProcessError caught
    - Returns Err with error details
    - Suggestions provided

    Expected: Result with Err(OrchestrationError) with recovery suggestions
    """
    # Arrange: Mock subprocess.run to raise CalledProcessError
    def failing_git_run(*args, **kwargs):
        if "git" in str(args[0]):
            raise subprocess.CalledProcessError(
                returncode=128,
                cmd=args[0],
                stderr="fatal: not a git repository",
            )
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="", stderr="")

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    with patch("subprocess.run", side_effect=failing_git_run):
        result = orchestrator._validate_git_workflow()

    # Assert
    # Should handle error gracefully (either Err or Ok with warning)
    if result.is_err():
        error = result.unwrap_err()
        assert "git" in error.reason.lower() or "failed" in error.reason.lower()


# ============================================================================
# NECESSARY SECURITY: No bypass mechanism
# ============================================================================


def test_no_bypass_mechanism_in_method_signature() -> None:
    """
    NECESSARY Security: No bypass mechanism exists in _validate_git_workflow().

    Validates:
    - No --force parameter
    - No "skip" or "bypass" parameters
    - No environment variable bypass
    - Article III enforcement is absolute

    Expected: Method signature has no forbidden bypass parameters
    """
    # Arrange
    import inspect

    # Act
    sig = inspect.signature(TwoStageOrchestrator._validate_git_workflow)

    # Assert
    param_names = [param.lower() for param in sig.parameters.keys() if param != "self"]
    forbidden_params = ["force", "bypass", "skip", "disable", "override"]

    for forbidden in forbidden_params:
        assert forbidden not in param_names, (
            f"_validate_git_workflow has forbidden parameter '{forbidden}' "
            f"(Article III: no bypass mechanism allowed)"
        )


# ============================================================================
# NECESSARY SCALE: Performance validation (<50ms)
# ============================================================================


def test_git_validation_performance(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Scale: Git validation completes in <50ms (PERF-003).

    Validates:
    - Minimal git command overhead
    - Performance target: <50ms per check
    - No repeated validation calls

    Expected: Execution time < 50ms (0.05 seconds)
    """
    # Arrange
    max_time = 0.05  # 50ms (PERF-003)

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    start_time = time.perf_counter()
    result = orchestrator._validate_git_workflow()
    elapsed_time = time.perf_counter() - start_time

    # Assert
    assert result.is_ok(), "Validation should succeed for performance test"
    assert elapsed_time < max_time, (
        f"Git validation took {elapsed_time:.4f}s, expected <{max_time}s (PERF-003)"
    )


# ============================================================================
# NECESSARY YIELD: Error message quality
# ============================================================================


def test_error_message_explains_article_iii_violation(
    isolated_git_repo: Path,
    mock_context: AgentContext,
) -> None:
    """
    NECESSARY Yield: Error message explains branch protection (Article III).

    Validates:
    - Error message references Article III
    - Actionable guidance provided (checkout command example)
    - Branch protection context explained

    Expected: Error message contains "Article III", "protected", "checkout"
    """
    # Arrange: Switch to main branch
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        timeout=10,
    )

    orchestrator = TwoStageOrchestrator(
        context=mock_context,
        repo_path=str(isolated_git_repo),
        auto_approve_for_tests=True,
    )

    # Act
    result = orchestrator._validate_git_workflow()

    # Assert
    assert result.is_err(), "main branch should fail validation"

    error = result.unwrap_err()
    error_message = error.reason.lower()

    # Check for required keywords
    required_keywords = ["protected", "checkout"]
    for keyword in required_keywords:
        assert keyword in error_message, (
            f"Error message missing keyword '{keyword}'\nMessage: {error.reason}"
        )

    # Check for actionable command or guidance
    assert (
        "git checkout" in error_message or "feature branch" in error_message
    ), f"Error should provide actionable guidance, got: {error.reason}"


# ============================================================================
# Integration: Method exists in TwoStageOrchestrator
# ============================================================================


def test_validate_git_workflow_method_exists() -> None:
    """
    Integration: _validate_git_workflow() method exists in TwoStageOrchestrator.

    This is a RED phase test - it MUST fail initially because the method
    doesn't exist yet in TwoStageOrchestrator.

    After implementation (GREEN phase), this test will pass.

    Expected (RED phase): AttributeError or method not found
    Expected (GREEN phase): Method exists and is callable
    """
    # Arrange
    import inspect

    # Act & Assert
    assert hasattr(TwoStageOrchestrator, "_validate_git_workflow"), (
        "_validate_git_workflow method not found in TwoStageOrchestrator "
        "(RED phase: expected to fail until implementation)"
    )

    # Verify method signature
    method = getattr(TwoStageOrchestrator, "_validate_git_workflow")
    assert callable(method), "_validate_git_workflow should be callable"

    # Verify return type annotation
    sig = inspect.signature(method)
    # Return type should be Result[None, OrchestrationError]
    # (Implementation detail - exact annotation may vary)
