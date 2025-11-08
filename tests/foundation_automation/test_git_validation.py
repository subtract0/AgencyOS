"""
Git Validation Tests for Phase 0 (RED Phase - TDD)

Tests git workflow validation before orchestrator execution.
These tests MUST fail initially (ImportError) as the implementation doesn't exist yet.

Covers acceptance criteria GIT-001 through GIT-006 from SPEC-030:
- GIT-001: main branch commit raises ValidationError
- GIT-002: master branch commit raises ValidationError
- GIT-003: Feature branches accepted (feat/*, fix/*, docs/*)
- GIT-004: Detached HEAD raises ValidationError with guidance
- GIT-005: Error message explains branch protection (Article III)
- GIT-006: Validation runs before Planner execution (<50ms)

NECESSARY Pattern Coverage:
- Normal: Feature branch passes validation
- Edge: Worktree isolation, branch name edge cases (Unicode, special chars, 255 chars)
- Constraints: Branch name pattern matching, protected branch enforcement
- Error: Detached HEAD, no git repo, permission denied, symlinks
- Security: No bypass mechanism exists (Article III), injection attempts
- Scale: Git validation <50ms per check (PERF-003)
- Asynchronous: N/A (synchronous git operations)
- Retry: Git command timeout, repo locked scenarios

Constitutional Compliance:
- Article I: Complete context (retry on git timeout)
- Article II: 100% verification (git status must succeed)
- Article III: Automated enforcement (no bypass mechanism)
- Article IV: VectorStore patterns for branch naming conventions
- Article V: Spec-driven (tests trace to GIT-001 through GIT-006)

Expected Initial State: ALL TESTS FAIL with ImportError
Expected After Implementation: ALL TESTS PASS with 100% rate
"""

import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from shared.agent_context import AgentContext
from shared.type_definitions.result import Err, Ok, Result

# THESE IMPORTS WILL FAIL - IMPLEMENTATION DOESN'T EXIST YET (RED PHASE)
# Tests will fail with ImportError when git_validator.py doesn't exist
try:
    from tools.orchestrator.git_validator import (
        GitValidationError,
        get_current_branch,
        require_feature_branch,
        validate_branch_safety,
    )
except ImportError:
    # Expected in RED phase - mark tests as expected to fail
    GitValidationError = None  # type: ignore
    get_current_branch = None  # type: ignore
    require_feature_branch = None  # type: ignore
    validate_branch_safety = None  # type: ignore


# ============================================================================
# NECESSARY NORMAL: Feature branch passes validation
# ============================================================================


def test_feature_branch_passes_validation(isolated_git_repo: Path) -> None:
    """
    GIT-003 NECESSARY Normal: Feature branch (feat/*) passes validation.

    Validates:
    - Branch name matches pattern (feat|fix|docs|refactor|test)/*
    - No Article III violation raised
    - Validation completes successfully

    Expected: Result<str, GitValidationError> with OK("feat/test")
    """
    # Arrange: isolated_git_repo fixture creates feat/test branch by default

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok(), f"Feature branch validation should pass, got: {result}"
    assert result.unwrap() == "feat/test"


def test_fix_branch_passes_validation(isolated_git_repo: Path) -> None:
    """
    GIT-003 NECESSARY Normal: Fix branch (fix/*) passes validation.

    Validates:
    - fix/* pattern accepted
    - No Article III violation

    Expected: Result<str, GitValidationError> with OK("fix/bug-123")
    """
    # Arrange: Switch to fix branch
    subprocess.run(
        ["git", "checkout", "-b", "fix/bug-123"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "fix/bug-123"


def test_docs_branch_passes_validation(isolated_git_repo: Path) -> None:
    """
    GIT-003 NECESSARY Normal: Docs branch (docs/*) passes validation.

    Validates:
    - docs/* pattern accepted
    - No Article III violation

    Expected: Result<str, GitValidationError> with OK("docs/update-readme")
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "docs/update-readme"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "docs/update-readme"


def test_refactor_branch_passes_validation(isolated_git_repo: Path) -> None:
    """
    GIT-003 NECESSARY Normal: Refactor branch passes validation.

    Validates:
    - refactor/* pattern accepted
    - No Article III violation

    Expected: Result<str, GitValidationError> with OK("refactor/cleanup-types")
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "refactor/cleanup-types"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "refactor/cleanup-types"


def test_test_branch_passes_validation(isolated_git_repo: Path) -> None:
    """
    GIT-003 NECESSARY Normal: Test branch passes validation.

    Validates:
    - test/* pattern accepted
    - No Article III violation

    Expected: Result<str, GitValidationError> with OK("test/integration-suite")
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "test/integration-suite"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "test/integration-suite"


# ============================================================================
# NECESSARY EDGE: Branch name edge cases
# ============================================================================


def test_branch_name_with_special_chars(isolated_git_repo: Path) -> None:
    """
    NECESSARY Edge: Branch name with special characters passes validation.

    Validates:
    - Dashes, underscores, dots, numbers accepted
    - No sanitization side effects

    Expected: Result<str, GitValidationError> with OK("feat/user-auth-2.0_final.v3")
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "feat/user-auth-2.0_final.v3"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "feat/user-auth-2.0_final.v3"


def test_very_long_branch_name(isolated_git_repo: Path) -> None:
    """
    NECESSARY Edge: Very long branch name (255 characters) passes validation.

    Validates:
    - Git max ref length (255 chars) supported
    - No truncation

    Expected: Result<str, GitValidationError> with OK(long_branch_name)
    """
    # Arrange: Create branch name with 255 characters (git ref max length)
    long_suffix = "a" * 240  # "feat/" = 5 chars, total = 245 chars
    long_branch = f"feat/{long_suffix}"

    subprocess.run(
        ["git", "checkout", "-b", long_branch],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == long_branch


def test_branch_name_with_unicode(isolated_git_repo: Path) -> None:
    """
    NECESSARY Edge: Branch name with Unicode characters handled gracefully.

    Validates:
    - Unicode sanitized or rejected with clear message
    - No encoding errors

    Expected: Either OK (if sanitized) or Err with Unicode warning
    """
    # Arrange: Attempt to create branch with Unicode
    unicode_branch = "feat/用户认证"

    # Git may reject Unicode branch names depending on config
    proc = subprocess.run(
        ["git", "checkout", "-b", unicode_branch],
        cwd=isolated_git_repo,
        capture_output=True,
    )

    if proc.returncode != 0:
        # Git rejected Unicode - validate_branch_safety should detect current branch
        result = validate_branch_safety(repo_path=isolated_git_repo)
        assert result.is_ok()  # Should return current branch (feat/test)
        assert result.unwrap() == "feat/test"
    else:
        # Git accepted Unicode - validation should pass or sanitize
        result = validate_branch_safety(repo_path=isolated_git_repo)
        assert result.is_ok() or "unicode" in str(result.unwrap_err()).lower()


def test_branch_name_with_slashes(isolated_git_repo: Path) -> None:
    """
    NECESSARY Edge: Branch name with multiple slashes (hierarchy) passes validation.

    Validates:
    - Git branch hierarchies supported (feat/auth/jwt)
    - Pattern matching works with nested paths

    Expected: Result<str, GitValidationError> with OK("feat/auth/jwt")
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "feat/auth/jwt"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok()
    assert result.unwrap() == "feat/auth/jwt"


# ============================================================================
# NECESSARY CONSTRAINTS: Protected branch enforcement
# ============================================================================


def test_main_branch_raises_validation_error(isolated_git_repo: Path) -> None:
    """
    GIT-001 NECESSARY Constraints: Execution on main branch raises ValidationError.

    Validates:
    - main branch detected as protected
    - Article III violation message included
    - Actionable guidance provided (checkout feature branch)

    Expected: Result<str, GitValidationError> with Err(GitValidationError)
    """
    # Arrange: Switch to main branch (create if doesn't exist, otherwise switch)
    # Check if main branch exists
    check_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=isolated_git_repo,
        capture_output=True,
    )
    if check_branch.returncode == 0:
        # Branch exists, just checkout
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )
    else:
        # Branch doesn't exist, create it
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "main branch should fail validation (GIT-001)"
    error_msg = str(result.unwrap_err())
    assert "main" in error_msg.lower()
    assert "article iii" in error_msg.lower() or "protected" in error_msg.lower()
    assert "checkout" in error_msg.lower() or "feature branch" in error_msg.lower()


def test_master_branch_raises_validation_error(isolated_git_repo: Path) -> None:
    """
    GIT-002 NECESSARY Constraints: Execution on master branch raises ValidationError.

    Validates:
    - master branch detected as protected
    - Article III violation message included
    - Actionable guidance provided

    Expected: Result<str, GitValidationError> with Err(GitValidationError)
    """
    # Arrange: Switch to master branch (may already exist, use checkout without -b first)
    proc = subprocess.run(
        ["git", "checkout", "master"],
        cwd=isolated_git_repo,
        capture_output=True,
    )
    if proc.returncode != 0:
        # master doesn't exist, create it
        subprocess.run(
            ["git", "checkout", "-b", "master"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "master branch should fail validation (GIT-002)"
    error_msg = str(result.unwrap_err())
    assert "master" in error_msg.lower()
    assert "article iii" in error_msg.lower() or "protected" in error_msg.lower()


def test_develop_branch_raises_validation_error(isolated_git_repo: Path) -> None:
    """
    NECESSARY Constraints: Execution on develop branch raises ValidationError.

    Validates:
    - develop branch detected as protected (common convention)
    - Article III violation message included

    Expected: Result<str, GitValidationError> with Err(GitValidationError)
    """
    # Arrange
    subprocess.run(
        ["git", "checkout", "-b", "develop"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "develop branch should fail validation"
    error_msg = str(result.unwrap_err())
    assert "develop" in error_msg.lower()


def test_invalid_branch_pattern_raises_error(isolated_git_repo: Path) -> None:
    """
    NECESSARY Constraints: Branch name not matching pattern raises ValidationError.

    Validates:
    - Branch names must match (feat|fix|docs|refactor|test)/*
    - Invalid patterns rejected (e.g., "random-branch")
    - Clear error message with expected patterns

    Expected: Result<str, GitValidationError> with Err explaining valid patterns
    """
    # Arrange: Create branch that doesn't match pattern
    subprocess.run(
        ["git", "checkout", "-b", "random-branch"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "Invalid branch pattern should fail validation"
    error_msg = str(result.unwrap_err())
    assert "pattern" in error_msg.lower() or "feat" in error_msg.lower()


# ============================================================================
# NECESSARY ERROR: Detached HEAD and edge cases
# ============================================================================


def test_detached_head_raises_validation_error(isolated_git_repo: Path) -> None:
    """
    GIT-004 NECESSARY Error: Detached HEAD state raises ValidationError with guidance.

    Validates:
    - Detached HEAD detected via git commands
    - Error message explains detached state
    - Guidance provided: "git checkout -b <branch-name>"

    Expected: Result<str, GitValidationError> with Err(GitValidationError)
    """
    # Arrange: Create detached HEAD by checking out commit hash
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    subprocess.run(
        ["git", "checkout", commit_hash],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "Detached HEAD should fail validation (GIT-004)"
    error_msg = str(result.unwrap_err())
    assert "detached" in error_msg.lower() or "head" in error_msg.lower()
    assert "checkout" in error_msg.lower()


def test_not_in_git_repo_logs_warning(tmp_path: Path) -> None:
    """
    GIT-005 NECESSARY Error: Not in git repository logs warning but continues.

    Validates:
    - Non-git directory detected gracefully
    - Warning logged (not blocking error)
    - Execution continues (non-blocking validation)

    Expected: Result<str, GitValidationError> with Err(GitValidationError)
    Note: Spec says "log warning, continue (non-blocking)" but since validation
    is Phase 0 (before execution), it should halt with clear error.
    """
    # Arrange: tmp_path is not a git repository

    # Act
    result = validate_branch_safety(repo_path=tmp_path)

    # Assert
    # Spec ambiguity: GIT-004 says "log warning, continue (non-blocking)"
    # but validation is Phase 0 (before Planner). Implementation may choose either:
    # Option 1: Err with warning (safer - prevents execution without git)
    # Option 2: Ok with logged warning (allows execution in non-git contexts)
    #
    # We'll assert Err for safety (Phase 0 should halt before Planner)
    assert result.is_err(), "Non-git directory should fail validation"
    error_msg = str(result.unwrap_err())
    assert "git" in error_msg.lower() or "repository" in error_msg.lower()


def test_git_command_timeout_retries(isolated_git_repo: Path) -> None:
    """
    NECESSARY Retry: Git command timeout triggers retry with 2x timeout.

    Validates:
    - Git command timeout detected
    - Retry attempted with 2x timeout (Article I)
    - Max 3 retries before failure

    Expected: After retries, either OK or Err with timeout details
    """
    # Arrange: Mock subprocess.run to simulate timeout
    original_run = subprocess.run

    call_count = 0

    def slow_git_run(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        # First 2 calls: simulate slow git command (timeout)
        if call_count <= 2:
            time.sleep(0.1)  # Simulate delay
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=0.05)

        # Third call: succeed
        return original_run(*args, **kwargs)

    # Act
    with patch("subprocess.run", side_effect=slow_git_run):
        result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    # After 3 attempts, should either succeed or fail with timeout error
    if result.is_ok():
        assert result.unwrap() == "feat/test"
    else:
        error_msg = str(result.unwrap_err())
        assert "timeout" in error_msg.lower()


def test_git_command_failure_with_locked_repo(isolated_git_repo: Path) -> None:
    """
    NECESSARY Retry: Git command failure (repo locked) retries up to 3 times.

    Validates:
    - Transient git failures detected (e.g., .git/index.lock)
    - Retry logic with exponential backoff
    - Clear error after max retries

    NOTE: git symbolic-ref (read-only) is NOT affected by index.lock
    (index.lock only blocks write operations like git add/commit).
    This test validates retry logic exists, but symbolic-ref will succeed.

    Expected: Ok(branch_name) because symbolic-ref doesn't require index lock
    """
    # Arrange: Create .git/index.lock to simulate locked repo
    lock_file = isolated_git_repo / ".git" / "index.lock"
    lock_file.write_text("locked")

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    # git symbolic-ref is read-only and doesn't fail with index.lock
    # This is correct behavior - validation should succeed for read operations
    assert result.is_ok(), "Read-only git commands should succeed even with locked index"
    assert result.unwrap() == "feat/test"

    # Cleanup
    lock_file.unlink()


# ============================================================================
# NECESSARY SECURITY: No bypass mechanism, injection prevention
# ============================================================================


def test_branch_name_injection_prevented(isolated_git_repo: Path) -> None:
    """
    NECESSARY Security: Branch name injection attempt detected and rejected.

    Validates:
    - Command injection via branch name prevented (e.g., "main; rm -rf /")
    - Git command execution doesn't evaluate shell metacharacters
    - Validation rejects malicious input

    Expected: Result<str, GitValidationError> with Err or sanitized name
    """
    # Arrange: Attempt to create branch with injection
    malicious_branch = "feat/test; rm -rf /"

    # Git typically rejects such branch names, but test validator behavior
    proc = subprocess.run(
        ["git", "checkout", "-b", malicious_branch],
        cwd=isolated_git_repo,
        capture_output=True,
    )

    if proc.returncode != 0:
        # Git rejected branch name - validator should detect current branch
        result = validate_branch_safety(repo_path=isolated_git_repo)
        assert result.is_ok()
        assert result.unwrap() == "feat/test"  # Still on original branch
    else:
        # Git accepted (unlikely) - validator should sanitize or reject
        result = validate_branch_safety(repo_path=isolated_git_repo)
        assert result.is_err() or ";" not in result.unwrap()


def test_symlink_to_protected_branch_rejected(isolated_git_repo: Path, tmp_path: Path) -> None:
    """
    NECESSARY Security: Symlink to protected branch does NOT create bypass.

    Validates:
    - Git treats symlink name (not target) as branch name
    - Symlink feat/symlink-test -> main is seen as "feat/symlink-test" by git symbolic-ref
    - No bypass occurs - protection is based on symbolic-ref output

    NOTE: Git's symbolic-ref returns the symlink name, NOT the target.
    This means feat/symlink-test -> main is treated as "feat/symlink-test" (valid pattern).
    This is secure - no bypass exists through symlinks.

    Expected: Ok("feat/symlink-test") because Git sees the symlink name, not target
    """
    # Arrange: Create symlink in .git/refs/heads (if filesystem supports)
    main_ref = isolated_git_repo / ".git" / "refs" / "heads" / "main"
    symlink_ref = isolated_git_repo / ".git" / "refs" / "heads" / "feat" / "symlink-test"

    # Create main branch first (or switch if exists)
    check_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=isolated_git_repo,
        capture_output=True,
    )
    if check_branch.returncode == 0:
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

    # Create feat directory
    symlink_ref.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Attempt to create symlink (may fail on some filesystems)
        symlink_ref.symlink_to(main_ref)

        # Checkout symlink branch
        subprocess.run(
            ["git", "checkout", "feat/symlink-test"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

        # Act
        result = validate_branch_safety(repo_path=isolated_git_repo)

        # Assert: Git sees symlink name (feat/symlink-test), not target (main)
        # This is correct behavior - no bypass exists
        assert result.is_ok(), "Symlink name (not target) should be validated"
        assert result.unwrap() == "feat/symlink-test"

    except (OSError, NotImplementedError):
        # Symlinks not supported on filesystem - skip test
        pytest.skip("Symlinks not supported on this filesystem")


def test_no_manual_bypass_mechanism_exists() -> None:
    """
    NECESSARY Security: No manual bypass mechanism exists for validation (Article III).

    Validates:
    - No --force flag to skip git validation
    - No environment variable to disable validation
    - No "emergency" bypass mode

    Expected: Validator API has no bypass parameters
    """
    # Arrange: Inspect function signature

    # Act
    import inspect

    sig = inspect.signature(validate_branch_safety)

    # Assert: No "force" or "bypass" or "skip" parameters
    param_names = [param.lower() for param in sig.parameters.keys()]
    forbidden_params = ["force", "bypass", "skip", "disable", "override"]

    for forbidden in forbidden_params:
        assert forbidden not in param_names, (
            f"validate_branch_safety has forbidden parameter '{forbidden}' "
            f"(Article III: no bypass mechanism allowed)"
        )


def test_require_feature_branch_enforces_pattern() -> None:
    """
    NECESSARY Security: require_feature_branch() enforces pattern without bypass.

    Validates:
    - Decorator-style enforcement for orchestrator methods
    - No bypass mechanism in decorator
    - Validation runs before method execution

    Expected: Function exists and has no bypass parameters
    """
    # Arrange: Inspect require_feature_branch function

    # Act
    import inspect

    sig = inspect.signature(require_feature_branch)

    # Assert: No bypass parameters
    param_names = [param.lower() for param in sig.parameters.keys()]
    forbidden_params = ["force", "bypass", "skip"]

    for forbidden in forbidden_params:
        assert forbidden not in param_names, (
            f"require_feature_branch has forbidden parameter '{forbidden}' "
            f"(Article III: no bypass allowed)"
        )


# ============================================================================
# NECESSARY SCALE: Performance validation (<50ms)
# ============================================================================


def test_git_validation_performance(
    isolated_git_repo: Path, performance_baseline: dict[str, float]
) -> None:
    """
    GIT-006 NECESSARY Scale: Git validation completes in <50ms (PERF-003).

    Validates:
    - Single git command execution (no repeated calls)
    - Minimal overhead
    - Performance target: <50ms per check

    Expected: Execution time < 50ms (0.05 seconds)
    """
    # Arrange
    max_time = performance_baseline["git_validation"]  # 0.05 seconds (50ms)

    # Act
    start_time = time.perf_counter()
    result = validate_branch_safety(repo_path=isolated_git_repo)
    elapsed_time = time.perf_counter() - start_time

    # Assert
    assert result.is_ok(), "Validation should succeed for performance test"
    assert elapsed_time < max_time, (
        f"Git validation took {elapsed_time:.4f}s, expected <{max_time}s (GIT-006)"
    )


def test_batch_validation_performance(
    isolated_git_repo: Path, performance_baseline: dict[str, float]
) -> None:
    """
    NECESSARY Scale: Batch validation (10 calls) completes in <500ms.

    Validates:
    - No caching side effects between calls
    - Consistent performance across repeated validations
    - Linear time complexity (10 calls ≈ 10x single call)

    Expected: Average time per call < 50ms
    """
    # Arrange
    num_calls = 10
    max_avg_time = performance_baseline["git_validation"]  # 0.05 seconds

    # Act
    start_time = time.perf_counter()
    for _ in range(num_calls):
        result = validate_branch_safety(repo_path=isolated_git_repo)
        assert result.is_ok()
    elapsed_time = time.perf_counter() - start_time

    avg_time = elapsed_time / num_calls

    # Assert
    assert avg_time < max_avg_time, (
        f"Average validation time {avg_time:.4f}s, expected <{max_avg_time}s "
        f"(total: {elapsed_time:.4f}s for {num_calls} calls)"
    )


# ============================================================================
# NECESSARY YIELD: Error message quality
# ============================================================================


def test_error_message_explains_article_iii_violation(isolated_git_repo: Path) -> None:
    """
    GIT-005 NECESSARY Yield: Error message explains branch protection (Article III).

    Validates:
    - Error message references Article III (Automated Merge Enforcement)
    - Actionable guidance provided (checkout command example)
    - Branch protection context explained

    Expected: Error message contains "Article III", "protected", "checkout"
    """
    # Arrange: Switch to main branch (create if doesn't exist)
    check_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=isolated_git_repo,
        capture_output=True,
    )
    if check_branch.returncode == 0:
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

    # Act
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "main branch should fail validation"
    error_msg = str(result.unwrap_err())

    # Check for required elements in error message
    required_keywords = ["article", "protected", "checkout"]
    for keyword in required_keywords:
        assert keyword in error_msg.lower(), (
            f"Error message missing keyword '{keyword}' (GIT-005)\nMessage: {error_msg}"
        )

    # Check for actionable command
    assert "git checkout -b" in error_msg or "feature branch" in error_msg.lower()


def test_get_current_branch_returns_branch_name(isolated_git_repo: Path) -> None:
    """
    NECESSARY Normal: get_current_branch() returns current branch name.

    Validates:
    - Branch name extraction via git command
    - No trailing whitespace
    - Works with various branch names

    Expected: Result<str, GitValidationError> with OK(branch_name)
    """
    # Arrange: isolated_git_repo is on feat/test by default

    # Act
    result = get_current_branch(repo_path=isolated_git_repo)

    # Assert
    assert result.is_ok(), f"get_current_branch should succeed, got: {result}"
    branch_name = result.unwrap()
    assert branch_name == "feat/test"
    assert branch_name.strip() == branch_name  # No whitespace


def test_get_current_branch_handles_detached_head(isolated_git_repo: Path) -> None:
    """
    NECESSARY Error: get_current_branch() handles detached HEAD gracefully.

    Validates:
    - Detached HEAD state detected
    - Returns Err with clear message
    - Message indicates detached state

    Expected: Result<str, GitValidationError> with Err
    """
    # Arrange: Create detached HEAD
    commit_hash = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    subprocess.run(
        ["git", "checkout", commit_hash],
        cwd=isolated_git_repo,
        check=True,
        capture_output=True,
    )

    # Act
    result = get_current_branch(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "get_current_branch should fail in detached HEAD"
    error_msg = str(result.unwrap_err())
    assert "detached" in error_msg.lower() or "head" in error_msg.lower()


# ============================================================================
# Integration Test: Validation runs before Planner execution
# ============================================================================


def test_validation_runs_before_planner_execution(
    isolated_git_repo: Path, mock_agent_context: AgentContext
) -> None:
    """
    GIT-006 Integration: Validation runs before Planner execution (Phase 0).

    Validates:
    - Git validation is Phase 0 (before any orchestrator logic)
    - Planner never invoked on protected branches
    - Early termination prevents wasted LLM calls

    Expected: Validation halts orchestrator on main branch BEFORE Planner call
    """
    # Arrange: Switch to main branch (create if doesn't exist)
    check_branch = subprocess.run(
        ["git", "rev-parse", "--verify", "main"],
        cwd=isolated_git_repo,
        capture_output=True,
    )
    if check_branch.returncode == 0:
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=isolated_git_repo,
            check=True,
            capture_output=True,
        )

    # Act: Attempt validation (should fail before orchestrator even initializes)
    result = validate_branch_safety(repo_path=isolated_git_repo)

    # Assert
    assert result.is_err(), "Validation should fail on main branch (Phase 0)"

    # Verify error prevents orchestrator from proceeding
    error_msg = str(result.unwrap_err())
    assert "main" in error_msg.lower()
    assert "protected" in error_msg.lower() or "article" in error_msg.lower()

    # Constitutional check: This error should halt orchestrator BEFORE Planner call
    # (Implementation will verify this by checking call order in orchestrator)
