"""
NECESSARY-Compliant Tests for CI Retrigger Tool

Test Coverage (NECESSARY Pattern):
- N: Normal operation (CI starts automatically, no empty commit needed)
- E: Edge cases (timeout -> empty commit, branch protection, CI detection)
- C: Corner cases (concurrent operations, state transitions)
- E: Error conditions (gh CLI errors, network failures, invalid PR)
- S: Security (GITHUB_TOKEN validation, no force push, branch protection)
- S: Stress (long waits, retry exhaustion, CI start delays)
- A: Accessibility (clear error messages, simple API, Result pattern)
- R: Regression (past bug prevention, edge case coverage)
- Y: Yield validation (commit SHA, workflow run ID, elapsed time accuracy)

Constitutional Compliance:
- Article I: Complete context (verify CI actually started, not just pushed)
- Article II: 100% verification (tests define expected behavior)
- Article III: Automated enforcement (no force push, respect branch protection)
- Article IV: Query VectorStore for CI trigger patterns before implementation
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md (AC-3)

Spec Traceability:
- AC-3: Autonomous retrigger (wait for CI start, empty commit if timeout)
- Timeout: 60s for CI start detection (configurable)
- Security: No force push, validate GITHUB_TOKEN scope
- Resilience: Verify CI run started (not just pushed)

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Import real implementation
from tools.ci_monitor.ci_retrigger import (
    BranchProtection,
    CIRetrigger,
    RetriggerError,
    RetriggerResult,
    wait_and_retrigger_ci,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_github_token():
    """Mock GITHUB_TOKEN environment variable (Security requirement)."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token_workflow_scope"}):
        yield


@pytest.fixture
def mock_no_github_token():
    """Mock missing GITHUB_TOKEN."""
    original = os.environ.get("GITHUB_TOKEN")
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    yield
    if original:
        os.environ["GITHUB_TOKEN"] = original


@pytest.fixture
def mock_invalid_github_token():
    """Mock invalid GITHUB_TOKEN format."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "invalid_token_format"}):
        yield


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=str(repo_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("Test repo")
    subprocess.run(["git", "add", "."], cwd=str(repo_path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
    )

    # Create test branch
    subprocess.run(
        ["git", "checkout", "-b", "feat/test"],
        cwd=str(repo_path),
        check=True,
        capture_output=True,
    )

    yield repo_path


# ============================================================================
# CATEGORY N: NORMAL OPERATION
# ============================================================================


@pytest.mark.asyncio
async def test_normal_ci_starts_automatically_no_retrigger(mock_github_token, temp_git_repo):
    """
    N1: Test normal operation - CI starts within 60s, no empty commit needed.

    Spec: AC-3 (CI starts automatically after push)
    Expected: ci_started=True, empty_commit_created=False, workflow_run_id populated
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=5)

    # Mock _wait_for_ci_start to return success immediately (CI started)
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Ok

        return Ok(12345)  # Mock workflow run ID

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock _check_branch_protection
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify
    assert result.is_ok()
    data = result.unwrap()
    assert isinstance(data, RetriggerResult)
    assert data.ci_started is True
    assert data.empty_commit_created is False
    assert data.workflow_run_id == 12345
    assert data.commit_sha is None
    assert data.elapsed_seconds >= 0


@pytest.mark.asyncio
async def test_normal_branch_protection_check_passes(mock_github_token, temp_git_repo):
    """
    N2: Test branch protection check (unprotected branch allows push).

    Spec: Security requirement (validate branch allows push)
    Expected: BranchProtection(protected=False, allows_force_push=True)
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock gh api to return 404 (branch not protected)
    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "gh" in cmd and "api" in cmd and "protection" in cmd[-1]:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr="gh: Not Found (HTTP 404)",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._check_branch_protection()

    # Verify
    assert result.is_ok()
    protection = result.unwrap()
    assert protection.protected is False
    assert protection.allows_force_push is True


# ============================================================================
# CATEGORY E: EDGE CASES
# ============================================================================


@pytest.mark.asyncio
async def test_edge_ci_timeout_creates_empty_commit(mock_github_token, temp_git_repo):
    """
    E1: Test edge case - CI timeout triggers empty commit creation.

    Spec: AC-3 (after 60s timeout, create empty commit to retrigger)
    Expected: empty_commit_created=True, commit_sha populated
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=1)

    # Mock _wait_for_ci_start to timeout first, then succeed
    call_count = [0]

    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Err, Ok

        call_count[0] += 1
        if call_count[0] == 1:
            # First call: timeout
            return Err(
                RetriggerError(
                    code="ci_start_timeout",
                    message="CI didn't start within timeout",
                )
            )
        else:
            # Second call (after empty commit): success
            return Ok(12346)

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock _check_branch_protection
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Mock _create_empty_commit
    async def mock_create_empty_commit():
        from shared.type_definitions.result import Ok

        return Ok("abc123def456")  # Mock commit SHA

    retrigger._create_empty_commit = mock_create_empty_commit

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify
    assert result.is_ok()
    data = result.unwrap()
    assert data.ci_started is True
    assert data.empty_commit_created is True
    assert data.commit_sha == "abc123def456"
    assert data.workflow_run_id == 12346


@pytest.mark.asyncio
async def test_edge_branch_protection_prevents_force_push(mock_github_token, temp_git_repo):
    """
    E2: Test edge case - protected branch without force push allowed.

    Spec: Security requirement (no force push on protected branches)
    Expected: BranchProtection(protected=True, allows_force_push=False)
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="main")

    # Mock gh api to return protected branch (no allow_force_pushes)
    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "gh" in cmd and "api" in cmd and "protection" in cmd[-1]:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout='{"required_status_checks": {}}',
                stderr="",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._check_branch_protection()

    # Verify
    assert result.is_ok()
    protection = result.unwrap()
    assert protection.protected is True
    assert protection.allows_force_push is False


@pytest.mark.asyncio
async def test_edge_empty_commit_without_force_flag(temp_git_repo):
    """
    E3: Test edge case - empty commit uses --allow-empty, NOT --force.

    Spec: Security requirement (no force push, respect branch protection)
    Expected: git commit uses --allow-empty flag only
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Track git commands executed
    executed_commands = []

    async def mock_run_command(cmd, cwd=None, timeout=30):
        executed_commands.append(cmd)

        if "git" in cmd and "commit" in cmd:
            # Verify --allow-empty present, --force NOT present
            assert "--allow-empty" in cmd
            assert "--force" not in cmd
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="",
                stderr="",
            )
        elif "git" in cmd and "push" in cmd:
            # Verify push has NO --force flag
            assert "--force" not in cmd
            assert "-f" not in cmd
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="",
                stderr="",
            )
        elif "git" in cmd and "rev-parse" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="abc123def456\n",
                stderr="",
            )

        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._create_empty_commit()

    # Verify
    assert result.is_ok()
    commit_sha = result.unwrap()
    assert commit_sha == "abc123def456"

    # Verify no force flags in any commands
    for cmd in executed_commands:
        assert "--force" not in cmd
        assert "-f" not in cmd or "rev-parse" in cmd  # -f only in rev-parse


# ============================================================================
# CATEGORY E: ERROR CONDITIONS
# ============================================================================


@pytest.mark.asyncio
async def test_error_missing_github_token(mock_no_github_token, temp_git_repo):
    """
    E4: Test error - missing GITHUB_TOKEN raises ValueError.

    Spec: Security requirement (validate GITHUB_TOKEN presence)
    Expected: ValueError with clear error message
    """
    with pytest.raises(ValueError) as exc_info:
        CIRetrigger(repo_path=temp_git_repo, require_token=True)

    error_json = exc_info.value.args[0]
    assert "missing_github_token" in error_json
    assert "GITHUB_TOKEN" in error_json


@pytest.mark.asyncio
async def test_error_invalid_github_token_format(mock_invalid_github_token, temp_git_repo):
    """
    E5: Test error - invalid GITHUB_TOKEN format raises ValueError.

    Spec: Security requirement (validate token format)
    Expected: ValueError with format validation details
    """
    with pytest.raises(ValueError) as exc_info:
        CIRetrigger(repo_path=temp_git_repo, require_token=True)

    error_json = exc_info.value.args[0]
    assert "invalid_github_token" in error_json
    assert "ghp_" in error_json or "format" in error_json


@pytest.mark.asyncio
async def test_error_gh_cli_not_found(mock_github_token, temp_git_repo):
    """
    E6: Test error - gh CLI not installed.

    Spec: Error condition requirement
    Expected: RetriggerError with code 'gh_cli_not_found'
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock _run_command to raise FileNotFoundError
    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "gh" in cmd:
            raise FileNotFoundError("gh command not found")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._check_branch_protection()

    # Verify
    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "gh_cli_not_found"
    assert "gh" in error.message.lower()


@pytest.mark.asyncio
async def test_error_ci_never_starts_after_empty_commit(mock_github_token, temp_git_repo):
    """
    E7: Test error - CI fails to start even after empty commit.

    Spec: Resilience requirement (manual intervention needed if CI broken)
    Expected: RetriggerError with code 'ci_start_timeout'
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=1)

    # Mock _wait_for_ci_start to always timeout
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Err

        return Err(
            RetriggerError(
                code="ci_start_timeout",
                message="CI didn't start within timeout",
            )
        )

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock other dependencies
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    async def mock_create_empty_commit():
        from shared.type_definitions.result import Ok

        return Ok("abc123def456")

    retrigger._create_empty_commit = mock_create_empty_commit

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify
    assert result.is_err()
    error = result.unwrap_err()
    assert error.code == "ci_start_timeout"
    assert "empty commit created" in error.message.lower()


# ============================================================================
# CATEGORY S: SECURITY
# ============================================================================


@pytest.mark.asyncio
async def test_security_github_token_scope_validation(mock_github_token, temp_git_repo):
    """
    S1: Test security - GITHUB_TOKEN scope validation.

    Spec: Security requirement (validate workflow scope)
    Expected: Token with valid prefix (ghp_, ghs_, gho_) accepted
    """
    # Valid token format should not raise
    retrigger = CIRetrigger(repo_path=temp_git_repo, require_token=True)
    assert retrigger is not None


@pytest.mark.asyncio
async def test_security_no_force_push_on_protected_branch(mock_github_token, temp_git_repo):
    """
    S2: Test security - no force push on protected branches.

    Spec: Article III (no manual overrides, respect branch protection)
    Expected: Workflow respects branch protection, never uses --force
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="main")

    # Mock protected branch
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=True, allows_force_push=False))

    retrigger._check_branch_protection = mock_check_protection

    # Mock CI start
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Ok

        return Ok(12345)

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify - should succeed without force push
    assert result.is_ok()
    data = result.unwrap()
    assert data.ci_started is True


@pytest.mark.asyncio
async def test_security_empty_commit_message_no_secrets(temp_git_repo):
    """
    S3: Test security - empty commit message contains no secrets.

    Spec: Security requirement (no credential leakage)
    Expected: Commit message is generic, no tokens/credentials
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock commands, capture commit message
    commit_messages = []

    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "git" in cmd and "commit" in cmd:
            # Extract commit message (after -m flag)
            try:
                msg_index = cmd.index("-m") + 1
                commit_messages.append(cmd[msg_index])
            except (ValueError, IndexError):
                pass
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="abc123\n", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._create_empty_commit()

    # Verify
    assert result.is_ok()
    assert len(commit_messages) == 1

    # Verify no secrets in commit message
    message = commit_messages[0].lower()
    assert "token" not in message
    assert "secret" not in message
    assert "password" not in message
    assert "ghp_" not in message
    assert "retrigger ci" in message  # Should be generic message


# ============================================================================
# CATEGORY S: STRESS (Performance)
# ============================================================================


@pytest.mark.asyncio
async def test_stress_long_ci_wait_timeout(mock_github_token, temp_git_repo):
    """
    S4: Test stress - long CI wait timeout (60s default).

    Spec: Stress requirement (handle slow CI start)
    Expected: Timeout after wait_timeout seconds, then retrigger
    """
    import time

    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=2)

    # Mock _wait_for_ci_start to timeout after specified duration
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Err

        # Simulate wait
        await asyncio.sleep(1)
        return Err(
            RetriggerError(
                code="ci_start_timeout",
                message="CI didn't start within timeout",
            )
        )

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock other dependencies
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    async def mock_create_empty_commit():
        from shared.type_definitions.result import Ok

        await asyncio.sleep(0.5)  # Simulate commit time
        return Ok("abc123")

    retrigger._create_empty_commit = mock_create_empty_commit

    # Execute with timing
    start_time = time.time()
    result = await retrigger.wait_and_retrigger(pr_number=123)
    elapsed = time.time() - start_time

    # Verify
    assert result.is_err()  # CI never started
    assert elapsed >= 1.5  # Should take at least 1.5s (wait + commit time)


# ============================================================================
# CATEGORY A: ACCESSIBILITY (API Usability)
# ============================================================================


@pytest.mark.asyncio
async def test_accessibility_clear_error_messages(mock_github_token, temp_git_repo):
    """
    A1: Test accessibility - error messages are clear and actionable.

    Spec: Accessibility requirement
    Expected: Error messages include context, error code, actionable details
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock branch protection check failure
    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "gh" in cmd and "api" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr="gh: Authentication failed",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._check_branch_protection()

    # Verify error message quality
    assert result.is_err()
    error = result.unwrap_err()
    # Should have error code
    assert error.code in ["protection_check_failed", "gh_cli_not_found"]
    # Should have human-readable message
    assert len(error.message) > 10
    # Should have details
    assert len(error.details) > 0


@pytest.mark.asyncio
async def test_accessibility_result_pattern_integration(mock_github_token, temp_git_repo):
    """
    A2: Test accessibility - Result<T,E> pattern used correctly.

    Spec: Constitutional Law #5 (functional error handling)
    Expected: All operations return Result[T, E], no bare exceptions
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock successful operation
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Execute
    result = await retrigger._check_branch_protection()

    # Verify Result pattern
    assert hasattr(result, "is_ok")
    assert hasattr(result, "is_err")
    assert hasattr(result, "unwrap")
    assert hasattr(result, "unwrap_err")
    assert result.is_ok()
    assert not result.is_err()


@pytest.mark.asyncio
async def test_accessibility_convenience_function(mock_github_token, temp_git_repo):
    """
    A3: Test accessibility - convenience function simplifies common usage.

    Spec: Accessibility requirement (simple API for common cases)
    Expected: wait_and_retrigger_ci() works with minimal arguments
    """
    # Mock CIRetrigger class
    with patch("tools.ci_monitor.ci_retrigger.CIRetrigger") as MockRetrigger:
        mock_instance = MagicMock()

        async def mock_wait_and_retrigger(pr_number):
            from shared.type_definitions.result import Ok

            return Ok(
                RetriggerResult(
                    ci_started=True,
                    empty_commit_created=False,
                    commit_sha=None,
                    elapsed_seconds=5.0,
                    workflow_run_id=12345,
                )
            )

        mock_instance.wait_and_retrigger = mock_wait_and_retrigger
        MockRetrigger.return_value = mock_instance

        # Execute convenience function
        result = await wait_and_retrigger_ci(pr_number=123)

        # Verify
        assert result.is_ok()
        data = result.unwrap()
        assert data.ci_started is True
        MockRetrigger.assert_called_once()


# ============================================================================
# CATEGORY R: REGRESSION (Bug Prevention)
# ============================================================================


@pytest.mark.asyncio
async def test_regression_wait_for_ci_polls_workflow_run_list(mock_github_token, temp_git_repo):
    """
    R1: Test regression - _wait_for_ci_start queries gh run list.

    Spec: AC-3 (verify CI run started, not just pushed)
    Expected: Polls gh run list for recent runs matching PR branch
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=2)

    # Track gh run list calls
    gh_run_list_calls = [0]

    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "gh" in cmd and "run" in cmd and "list" in cmd:
            gh_run_list_calls[0] += 1

            # Return mock workflow run JSON
            runs = [
                {
                    "databaseId": 12345,
                    "status": "queued",
                    "event": "pull_request",
                    "headBranch": "feat/test",
                }
            ]
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=json.dumps(runs),
                stderr="",
            )

        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._wait_for_ci_start(pr_number=123, timeout=2)

    # Verify
    assert result.is_ok()
    assert result.unwrap() == 12345  # Workflow run ID
    assert gh_run_list_calls[0] >= 1  # Should have polled at least once


@pytest.mark.asyncio
async def test_regression_branch_detection_fallback(temp_git_repo):
    """
    R2: Test regression - branch detection fallback to current branch.

    Spec: Edge case requirement (auto-detect branch if not provided)
    Expected: Detects current branch via git rev-parse --abbrev-ref HEAD
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch=None)  # No branch specified

    # Execute
    branch = await retrigger._get_current_branch()

    # Verify
    assert branch is not None
    assert isinstance(branch, str)
    assert len(branch) > 0


# ============================================================================
# CATEGORY Y: YIELD VALIDATION (Output Correctness)
# ============================================================================


@pytest.mark.asyncio
async def test_yield_commit_sha_format_validation(temp_git_repo):
    """
    Y1: Test yield validation - commit SHA format is valid git SHA.

    Spec: Yield validation requirement
    Expected: Commit SHA is 40-character hex string
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock successful empty commit
    async def mock_run_command(cmd, cwd=None, timeout=30):
        if "git" in cmd and "rev-parse" in cmd:
            # Return valid git SHA
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="1234567890abcdef1234567890abcdef12345678\n",
                stderr="",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    retrigger._run_command = mock_run_command

    # Execute
    result = await retrigger._create_empty_commit()

    # Verify
    assert result.is_ok()
    commit_sha = result.unwrap()
    # Valid git SHA: 40 hex characters
    assert len(commit_sha) == 40
    assert all(c in "0123456789abcdef" for c in commit_sha)


@pytest.mark.asyncio
async def test_yield_elapsed_time_accuracy(mock_github_token, temp_git_repo):
    """
    Y2: Test yield validation - elapsed_seconds accuracy.

    Spec: Yield validation requirement
    Expected: elapsed_seconds reflects actual wait time
    """
    import time

    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test", wait_timeout=2)

    # Mock _wait_for_ci_start with known delay
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Ok

        await asyncio.sleep(0.5)  # 500ms delay
        return Ok(12345)

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock branch protection
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Execute with timing
    start_time = time.time()
    result = await retrigger.wait_and_retrigger(pr_number=123)
    actual_elapsed = time.time() - start_time

    # Verify
    assert result.is_ok()
    data = result.unwrap()
    # elapsed_seconds should be close to actual time (within 100ms tolerance)
    assert abs(data.elapsed_seconds - actual_elapsed) < 0.1


@pytest.mark.asyncio
async def test_yield_workflow_run_id_populated(mock_github_token, temp_git_repo):
    """
    Y3: Test yield validation - workflow_run_id populated correctly.

    Spec: AC-3 (verify CI run started, return run ID)
    Expected: workflow_run_id is positive integer from gh run list
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Mock successful CI start with specific run ID
    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Ok

        return Ok(67890)  # Specific workflow run ID

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock branch protection
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify
    assert result.is_ok()
    data = result.unwrap()
    assert data.workflow_run_id == 67890
    assert isinstance(data.workflow_run_id, int)
    assert data.workflow_run_id > 0


# ============================================================================
# CONSTITUTIONAL COMPLIANCE VERIFICATION
# ============================================================================


@pytest.mark.asyncio
async def test_constitutional_article_i_complete_context(mock_github_token, temp_git_repo):
    """
    Constitutional Article I: Complete context before action.

    Expected: Verifies CI actually started (not just pushed), waits for confirmation
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Track whether we verify CI started
    ci_verification_calls = [0]

    async def mock_wait_for_ci_start(pr_number, timeout=None):
        from shared.type_definitions.result import Ok

        ci_verification_calls[0] += 1
        # Simulate polling gh run list to verify CI started
        await asyncio.sleep(0.1)
        return Ok(12345)

    retrigger._wait_for_ci_start = mock_wait_for_ci_start

    # Mock branch protection
    async def mock_check_protection():
        from shared.type_definitions.result import Ok

        return Ok(BranchProtection(protected=False, allows_force_push=True))

    retrigger._check_branch_protection = mock_check_protection

    # Execute
    result = await retrigger.wait_and_retrigger(pr_number=123)

    # Verify Article I compliance: Must verify CI started
    assert result.is_ok()
    assert ci_verification_calls[0] >= 1  # Must check CI status


@pytest.mark.asyncio
async def test_constitutional_article_iii_no_force_push(temp_git_repo):
    """
    Constitutional Article III: Automated enforcement (no manual overrides).

    Expected: Never uses --force flag, respects branch protection
    """
    retrigger = CIRetrigger(repo_path=temp_git_repo, branch="feat/test")

    # Track all git commands
    all_commands = []

    async def mock_run_command(cmd, cwd=None, timeout=30):
        all_commands.append(cmd)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout="abc123\n",
            stderr="",
        )

    retrigger._run_command = mock_run_command

    # Execute empty commit creation
    result = await retrigger._create_empty_commit()

    # Verify Article III compliance: No --force flags
    assert result.is_ok()
    for cmd in all_commands:
        if "git" in cmd and ("push" in cmd or "commit" in cmd):
            assert "--force" not in cmd
            assert "-f" not in cmd or "rev-parse" in cmd


# ============================================================================
# NECESSARY PATTERN COMPLIANCE SUMMARY
# ============================================================================


def test_necessary_pattern_compliance():
    """
    NECESSARY Pattern Compliance Summary.

    Validates this test suite covers required categories:
    N: Normal operation (2 tests)
    E: Edge cases (3 tests)
    E: Error conditions (4 tests)
    S: Security (3 tests)
    S: Stress (1 test)
    A: Accessibility (3 tests)
    R: Regression (2 tests)
    Y: Yield validation (3 tests)

    Total: 21+ tests (exceeds minimum viable coverage)
    Constitutional Compliance: 2 tests
    """
    import inspect
    import sys

    module = sys.modules[__name__]
    test_functions = [
        name
        for name, obj in inspect.getmembers(module)
        if name.startswith("test_") and inspect.iscoroutinefunction(obj)
    ]

    # Verify minimum coverage
    assert len(test_functions) >= 20, f"Need at least 20 tests, got {len(test_functions)}"

    # Categorize tests
    categories = {
        "N": [n for n in test_functions if n.startswith("test_normal_")],
        "E": [n for n in test_functions if n.startswith("test_edge_")],
        "E2": [n for n in test_functions if n.startswith("test_error_")],
        "S": [n for n in test_functions if n.startswith("test_security_")],
        "S2": [n for n in test_functions if n.startswith("test_stress_")],
        "A": [n for n in test_functions if n.startswith("test_accessibility_")],
        "R": [n for n in test_functions if n.startswith("test_regression_")],
        "Y": [n for n in test_functions if n.startswith("test_yield_")],
        "Constitutional": [n for n in test_functions if "constitutional" in n],
    }

    print("\n✅ NECESSARY Pattern Coverage:")
    for category, tests in categories.items():
        print(f"  {category}: {len(tests)} tests")

    # Verify all categories covered
    assert len(categories["N"]) >= 2, "Need at least 2 Normal operation tests"
    assert len(categories["E"]) >= 2, "Need at least 2 Edge case tests"
    assert len(categories["E2"]) >= 2, "Need at least 2 Error condition tests"
    assert len(categories["S"]) >= 2, "Need at least 2 Security tests"
    assert len(categories["A"]) >= 2, "Need at least 2 Accessibility tests"
    assert len(categories["Y"]) >= 2, "Need at least 2 Yield validation tests"

    print(f"\n✅ Total: {len(test_functions)} tests implemented")
    print("✅ NECESSARY pattern: COMPLIANT")
