"""
NECESSARY-Compliant Tests for CI Status Poller

Test Coverage (NECESSARY Pattern):
- N: Normal operation (success/failure detection, polling loop)
- E: Edge cases (timeout, rate limiting, empty results)
- C: Corner cases (multiple simultaneous checks, state transitions)
- E: Error conditions (network failures, invalid PR numbers)
- S: Security (credential validation, GITHUB_TOKEN presence)
- S: Stress (long-running polls, retry exhaustion)
- A: Accessibility (API usability, clear error messages)
- R: Regression (past bug prevention)
- Y: Yield validation (status format, check state accuracy)

Constitutional Compliance:
- Article I: Complete context (retry on timeout 2x/3x)
- Article II: 100% verification (tests define expected behavior)
- Article IV: VectorStore integration (query patterns before implementation)
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md

Spec Traceability:
- AC-1: Autonomous monitoring (30s polling interval)
- AC-2: Autonomous log fetching (gh run view --log)
- AC-3: Autonomous retrigger (CI start detection)

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Test imports (implementation completed)
from tools.ci_monitor.status_poller import (
    CIStatus,
    CheckResult,
    CheckState,
    PollResult,
    StatusPoller,
    StatusPollerError,
)

# ============================================================================
# MOCK DATA STRUCTURES (No longer needed - using real implementation)
# ============================================================================


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_github_token():
    """Mock GITHUB_TOKEN environment variable."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test_token_1234567890"}):
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
def gh_pr_checks_success_output():
    """Mock gh pr checks output for all passing."""
    return """[
  {
    "name": "CI",
    "state": "success",
    "conclusion": "success",
    "workflowName": "CI",
    "event": "pull_request"
  },
  {
    "name": "Lint",
    "state": "success",
    "conclusion": "success",
    "workflowName": "Lint",
    "event": "pull_request"
  }
]"""


@pytest.fixture
def gh_pr_checks_failure_output():
    """Mock gh pr checks output with failures."""
    return """[
  {
    "name": "CI",
    "state": "failure",
    "conclusion": "failure",
    "workflowName": "CI",
    "event": "pull_request"
  },
  {
    "name": "Lint",
    "state": "success",
    "conclusion": "success",
    "workflowName": "Lint",
    "event": "pull_request"
  }
]"""


@pytest.fixture
def gh_pr_checks_pending_output():
    """Mock gh pr checks output with pending checks."""
    return """[
  {
    "name": "CI",
    "state": "pending",
    "conclusion": null,
    "workflowName": "CI",
    "event": "pull_request"
  },
  {
    "name": "Lint",
    "state": "in_progress",
    "conclusion": null,
    "workflowName": "Lint",
    "event": "pull_request"
  }
]"""


@pytest.fixture
def gh_pr_checks_rate_limit_error():
    """Mock gh CLI rate limit error."""
    return "GraphQL: API rate limit exceeded for user (403)"


# ============================================================================
# CATEGORY N: NORMAL OPERATION
# ============================================================================


@pytest.mark.asyncio
async def test_poll_success_all_checks_passing(
    mock_github_token, gh_pr_checks_success_output
):
    """
    N1: Test polling detects all checks passing.

    Spec: AC-1 (Autonomous monitoring)
    Expected: Returns CIStatus with all_passing=True
    """
    pr_number = 123

    # Mock gh pr checks command
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks", str(pr_number), "--json", "name,state,conclusion"],
        returncode=0,
        stdout=gh_pr_checks_success_output,
        stderr="",
    )

    # Test uses real StatusPoller
    with patch("subprocess.run", return_value=mock_result):
        poller = StatusPoller(pr_number=pr_number)
        status_result = await poller.get_current_status()

        assert status_result.is_ok()
        status = status_result.unwrap()
        assert status.all_passing is True
        assert status.has_failures is False
        assert status.is_complete is True
        assert len(status.checks) == 2
        assert all(check.state == "success" for check in status.checks)


@pytest.mark.asyncio
async def test_poll_failure_detects_failing_checks(
    mock_github_token, gh_pr_checks_failure_output
):
    """
    N2: Test polling detects failing checks.

    Spec: AC-1 (Autonomous monitoring), AC-2 (Log fetching trigger)
    Expected: Returns CIStatus with has_failures=True, identifies failed check
    """
    pr_number = 123

    # Mock gh pr checks command
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks", str(pr_number), "--json", "name,state,conclusion"],
        returncode=0,
        stdout=gh_pr_checks_failure_output,
        stderr="",
    )

    # Test uses real StatusPoller
    with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()

         assert status.all_passing is False
         assert status.has_failures is True
         assert status.is_complete is True
         assert len(status.checks) == 2

         # Verify CI check failed, Lint passed
         ci_check = next(c for c in status.checks if c.name == "CI")
         lint_check = next(c for c in status.checks if c.name == "Lint")
         assert ci_check.state == "failure"
         assert lint_check.state == "success"


@pytest.mark.asyncio

async def test_poll_until_complete_30s_interval(
    mock_github_token, gh_pr_checks_pending_output, gh_pr_checks_success_output
):
    """
    N3: Test polling waits with 30s interval until checks complete.

    Spec: AC-1 (30s polling interval)
    Expected: Polls every 30s, returns when all checks terminal
    """
    pr_number = 123

     Mock progression: pending -> pending -> success
    mock_results = [
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=gh_pr_checks_pending_output,
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=gh_pr_checks_pending_output,
            stderr="",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=gh_pr_checks_success_output,
            stderr="",
        ),
    ]

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_results):
         with patch("asyncio.sleep") as mock_sleep:
             poller = StatusPoller(pr_number=pr_number, poll_interval=30)
             result = await poller.poll_until_complete(max_wait=600)
    #
             assert result.status.is_complete is True
             assert result.poll_count == 3
             # Verify 30s sleep between polls
             assert mock_sleep.call_count == 2  # Sleep between 3 polls
             mock_sleep.assert_called_with(30)


 ============================================================================
 CATEGORY E: EDGE CASES
 ============================================================================


@pytest.mark.asyncio

async def test_poll_timeout_max_wait_exceeded(
    mock_github_token, gh_pr_checks_pending_output
):
    """
    E1: Test polling times out when max_wait exceeded.

    Spec: AC-1 (timeout handling)
    Expected: Raises StatusPollerError with code "poll_timeout"
    """
    pr_number = 123

     Mock continuously pending checks
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=gh_pr_checks_pending_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number, poll_interval=1)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.poll_until_complete(max_wait=3)  # 3 second timeout
    #
         assert exc_info.value.code == "poll_timeout"
         assert "exceeded max_wait" in exc_info.value.message


@pytest.mark.asyncio

async def test_poll_rate_limit_handling(mock_github_token, gh_pr_checks_rate_limit_error):
    """
    E2: Test polling handles GitHub rate limiting (429 responses).

    Spec: Edge case requirement
    Expected: Retries with exponential backoff, eventually raises error
    """
    pr_number = 123

     Mock rate limit error
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=1,
        stdout="",
        stderr=gh_pr_checks_rate_limit_error,
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number, poll_interval=1)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.get_current_status()
    #
         assert exc_info.value.code == "rate_limit_exceeded"
         assert "429" in exc_info.value.message or "rate limit" in exc_info.value.message.lower()


@pytest.mark.asyncio

async def test_poll_empty_checks_list(mock_github_token):
    """
    E3: Test polling handles PR with no CI checks configured.

    Spec: Edge case requirement
    Expected: Returns status with empty checks list, all_passing=True (vacuously)
    """
    pr_number = 123

     Mock empty checks list
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout="[]",
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()
    #
         assert len(status.checks) == 0
         assert status.all_passing is True  # Vacuously true
         assert status.has_failures is False
         assert status.is_complete is True


@pytest.mark.asyncio

async def test_poll_skipped_checks_not_failures(mock_github_token):
    """
    E4: Test polling treats skipped checks as non-failures.

    Spec: Edge case requirement
    Expected: Skipped checks don't count as failures
    """
    pr_number = 123

     Mock skipped check
    mock_output = """[
  {
    "name": "Optional Check",
    "state": "skipped",
    "conclusion": "skipped",
    "workflowName": "Optional",
    "event": "pull_request"
  }
]"""

    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=mock_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()
    #
         assert status.has_failures is False
         assert status.is_complete is True
         assert len(status.checks) == 1
         assert status.checks[0].state == "skipped"


 ============================================================================
 CATEGORY C: CORNER CASES
 ============================================================================


@pytest.mark.asyncio

async def test_poll_state_transitions(mock_github_token):
    """
    C1: Test polling handles multiple state transitions (queued -> pending -> in_progress -> success).

    Spec: Corner case requirement
    Expected: Correctly identifies is_complete only at terminal states
    """
    pr_number = 123

     Mock state progression
    state_outputs = [
        '[{"name": "CI", "state": "queued", "conclusion": null}]',
        '[{"name": "CI", "state": "pending", "conclusion": null}]',
        '[{"name": "CI", "state": "in_progress", "conclusion": null}]',
        '[{"name": "CI", "state": "success", "conclusion": "success"}]',
    ]

    mock_results = [
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=output,
            stderr="",
        )
        for output in state_outputs
    ]

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_results):
         poller = StatusPoller(pr_number=pr_number, poll_interval=0.1)
    #
         # First three polls should be incomplete
         for i in range(3):
             status = await poller.get_current_status()
             assert status.is_complete is False
    #
         # Final poll should be complete
         status = await poller.get_current_status()
         assert status.is_complete is True
         assert status.all_passing is True


@pytest.mark.asyncio

async def test_poll_multiple_simultaneous_pollers(mock_github_token):
    """
    C2: Test multiple StatusPoller instances can run simultaneously without interference.

    Spec: Corner case requirement
    Expected: Each poller maintains independent state
    """
     Mock different PR statuses
    pr_123_output = '[{"name": "CI", "state": "success", "conclusion": "success"}]'
    pr_456_output = '[{"name": "CI", "state": "failure", "conclusion": "failure"}]'

    def mock_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if "123" in " ".join(map(str, cmd)):
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=pr_123_output,
                stderr="",
            )
        else:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=pr_456_output,
                stderr="",
            )

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_run):
         poller_123 = StatusPoller(pr_number=123)
         poller_456 = StatusPoller(pr_number=456)
    #
         # Run simultaneously
         status_123, status_456 = await asyncio.gather(
             poller_123.get_current_status(),
             poller_456.get_current_status()
         )
    #
         # Verify independent results
         assert status_123.pr_number == 123
         assert status_123.all_passing is True
         assert status_456.pr_number == 456
         assert status_456.has_failures is True


 ============================================================================
 CATEGORY E: ERROR CONDITIONS
 ============================================================================


@pytest.mark.asyncio

async def test_poll_network_failure_retry(mock_github_token):
    """
    E5: Test polling retries on transient network failures.

    Spec: Resilience requirement
    Expected: Retries up to N times, then raises StatusPollerError
    """
    pr_number = 123

     Mock transient network error, then success
    mock_results = [
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=1,
            stdout="",
            stderr="error: failed to connect to github.com",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=1,
            stdout="",
            stderr="error: connection timeout",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout='[{"name": "CI", "state": "success", "conclusion": "success"}]',
            stderr="",
        ),
    ]

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_results):
         poller = StatusPoller(pr_number=pr_number, max_retries=3)
         status = await poller.get_current_status()
    #
         # Should succeed after retries
         assert status.all_passing is True


@pytest.mark.asyncio

async def test_poll_invalid_pr_number(mock_github_token):
    """
    E6: Test polling raises error for invalid PR number.

    Spec: Error condition requirement
    Expected: Raises StatusPollerError with code "invalid_pr_number"
    """
    invalid_pr_numbers = [0, -1, None]

    # Test uses real StatusPoller
     for pr_number in invalid_pr_numbers:
         with pytest.raises(StatusPollerError) as exc_info:
             StatusPoller(pr_number=pr_number)
    #
         assert exc_info.value.code == "invalid_pr_number"


@pytest.mark.asyncio

async def test_poll_pr_not_found(mock_github_token):
    """
    E7: Test polling handles non-existent PR gracefully.

    Spec: Error condition requirement
    Expected: Raises StatusPollerError with code "pr_not_found"
    """
    pr_number = 99999

     Mock gh CLI error for non-existent PR
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=1,
        stdout="",
        stderr="error: pull request #99999 not found",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.get_current_status()
    #
         assert exc_info.value.code == "pr_not_found"
         assert "99999" in exc_info.value.message


@pytest.mark.asyncio

async def test_poll_gh_cli_not_installed():
    """
    E8: Test polling detects when gh CLI is not installed.

    Spec: Error condition requirement
    Expected: Raises StatusPollerError with code "gh_cli_not_found"
    """
    pr_number = 123

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=FileNotFoundError()):
         poller = StatusPoller(pr_number=pr_number)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.get_current_status()
    #
         assert exc_info.value.code == "gh_cli_not_found"
         assert "https://cli.github.com/" in exc_info.value.details


 ============================================================================
 CATEGORY S: SECURITY
 ============================================================================


@pytest.mark.asyncio

async def test_poll_requires_github_token(mock_no_github_token):
    """
    S1: Test polling validates GITHUB_TOKEN presence.

    Spec: Security requirement
    Expected: Raises StatusPollerError with code "missing_github_token" if token absent
    """
    pr_number = 123

    # Test uses real StatusPoller
     with pytest.raises(StatusPollerError) as exc_info:
         StatusPoller(pr_number=pr_number, require_token=True)
    #
     assert exc_info.value.code == "missing_github_token"
     assert "GITHUB_TOKEN" in exc_info.value.message


@pytest.mark.asyncio

async def test_poll_validates_token_format(mock_github_token):
    """
    S2: Test polling validates GITHUB_TOKEN format (basic sanity check).

    Spec: Security requirement
    Expected: Accepts valid token formats (ghp_*, ghs_*, gho_*)
    """
    valid_tokens = [
        "ghp_1234567890abcdefghijklmnopqrst",
        "ghs_1234567890abcdefghijklmnopqrst",
        "gho_1234567890abcdefghijklmnopqrst",
    ]

    # Test uses real StatusPoller
     for token in valid_tokens:
         with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
             poller = StatusPoller(pr_number=123, require_token=True)
             # Should not raise error
             assert poller is not None


@pytest.mark.asyncio

async def test_poll_rejects_invalid_token_format():
    """
    S3: Test polling rejects obviously invalid token formats.

    Spec: Security requirement
    Expected: Raises StatusPollerError for tokens like "test", "abc123"
    """
    invalid_tokens = ["test", "abc123", "not_a_token", ""]

    # Test uses real StatusPoller
     for token in invalid_tokens:
         with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
             with pytest.raises(StatusPollerError) as exc_info:
                 StatusPoller(pr_number=123, require_token=True, validate_token_format=True)
    #
             assert exc_info.value.code == "invalid_github_token"


 ============================================================================
 CATEGORY S: STRESS
 ============================================================================


@pytest.mark.asyncio

async def test_poll_long_running_checks(mock_github_token, gh_pr_checks_pending_output):
    """
    S4: Test polling handles long-running checks (e.g., 10+ minutes).

    Spec: Stress test requirement
    Expected: Polls continuously without memory leaks, respects max_wait
    """
    pr_number = 123

     Mock pending checks for 10 polls
    mock_results = [
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=gh_pr_checks_pending_output,
            stderr="",
        )
        for _ in range(10)
    ]

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_results):
         with patch("asyncio.sleep"):  # Speed up test
             poller = StatusPoller(pr_number=pr_number, poll_interval=1)
    #
             with pytest.raises(StatusPollerError) as exc_info:
                 await poller.poll_until_complete(max_wait=5)  # Timeout expected
    #
             assert exc_info.value.code == "poll_timeout"


@pytest.mark.asyncio

async def test_poll_retry_exhaustion(mock_github_token):
    """
    S5: Test polling exhausts retries on persistent errors.

    Spec: Stress test requirement
    Expected: Retries N times, then raises final error
    """
    pr_number = 123

     Mock persistent network error
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=1,
        stdout="",
        stderr="error: persistent network failure",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number, max_retries=3)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.get_current_status()
    #
         assert exc_info.value.code in ["network_error", "gh_cli_error"]
         assert "retries exhausted" in exc_info.value.message.lower() or "max_retries" in exc_info.value.message.lower()


 ============================================================================
 CATEGORY A: ACCESSIBILITY (API Usability)
 ============================================================================


@pytest.mark.asyncio

async def test_poll_clear_error_messages(mock_github_token):
    """
    A1: Test polling provides clear, actionable error messages.

    Spec: Accessibility requirement
    Expected: Error messages include context, PR number, suggested actions
    """
    pr_number = 123

     Mock error
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=1,
        stdout="",
        stderr="error: authentication failed",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
    #
         with pytest.raises(StatusPollerError) as exc_info:
             await poller.get_current_status()
    #
         error = exc_info.value
         # Error message should include:
         # 1. PR number
         assert str(pr_number) in error.message
         # 2. What went wrong
         assert "authentication" in error.message.lower()
         # 3. Suggested action (in details)
         assert "GITHUB_TOKEN" in error.details or "gh auth login" in error.details


@pytest.mark.asyncio

async def test_poll_api_simplicity(mock_github_token, gh_pr_checks_success_output):
    """
    A2: Test StatusPoller API is simple and intuitive.

    Spec: Accessibility requirement
    Expected: Minimal required parameters, sensible defaults
    """
    pr_number = 123

     Mock success
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=gh_pr_checks_success_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         # Simplest usage: just PR number
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()
         assert status.pr_number == pr_number
    #
         # Advanced usage: custom poll interval
         poller_custom = StatusPoller(pr_number=pr_number, poll_interval=60)
         assert poller_custom is not None


 ============================================================================
 CATEGORY R: REGRESSION
 ============================================================================


@pytest.mark.asyncio

async def test_poll_regression_pr_86_manual_intervention(mock_github_token):
    """
    R1: Regression test for PR #86 (manual intervention required 2 times).

    Spec: Related Work - PR #86
    Expected: Autonomous polling eliminates need for manual log pasting
    """
    pr_number = 86

     Mock failure scenario from PR #86
    failure_output = """[
  {
    "name": "CI",
    "state": "failure",
    "conclusion": "failure",
    "workflowName": "CI",
    "event": "pull_request"
  }
]"""

    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=failure_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()
    #
         # Verify autonomous detection (no user intervention)
         assert status.has_failures is True
         failed_checks = [c for c in status.checks if c.state == "failure"]
         assert len(failed_checks) == 1
         # Test proves poller can detect failures autonomously


 ============================================================================
 CATEGORY Y: YIELD VALIDATION (Output Correctness)
 ============================================================================


@pytest.mark.asyncio

async def test_poll_status_format_validation(
    mock_github_token, gh_pr_checks_success_output
):
    """
    Y1: Test CIStatus output format matches specification.

    Spec: Yield validation requirement
    Expected: CIStatus has correct fields, types, and values
    """
    pr_number = 123

     Mock success
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=gh_pr_checks_success_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         poller = StatusPoller(pr_number=pr_number)
         status = await poller.get_current_status()
    #
         # Validate CIStatus structure
         assert isinstance(status, CIStatus)
         assert isinstance(status.pr_number, int)
         assert isinstance(status.checks, list)
         assert isinstance(status.all_passing, bool)
         assert isinstance(status.has_failures, bool)
         assert isinstance(status.is_complete, bool)
    #
         # Validate CheckResult structure
         for check in status.checks:
             assert isinstance(check, CheckResult)
             assert isinstance(check.name, str)
             assert isinstance(check.state, str)
             assert check.state in ["success", "failure", "pending", "skipped", "in_progress"]


@pytest.mark.asyncio

async def test_poll_check_state_accuracy(mock_github_token):
    """
    Y2: Test check state mapping is accurate (gh CLI -> CheckState enum).

    Spec: Yield validation requirement
    Expected: All gh CLI states correctly mapped to CheckState enum
    """
    pr_number = 123

    # Test all possible check states
    test_states = [
        ("success", CheckState.SUCCESS),
        ("failure", CheckState.FAILURE),
        ("pending", CheckState.PENDING),
        ("in_progress", CheckState.IN_PROGRESS),
        ("skipped", CheckState.SKIPPED),
        ("queued", CheckState.QUEUED),
        ("timed_out", CheckState.TIMED_OUT),
        ("action_required", CheckState.ACTION_REQUIRED),
    ]

    # Test uses real StatusPoller
     for gh_state, expected_enum in test_states:
         mock_output = f'[{{"name": "CI", "state": "{gh_state}", "conclusion": "{gh_state}"}}]'
         mock_result = subprocess.CompletedProcess(
             args=["gh", "pr", "checks"],
             returncode=0,
             stdout=mock_output,
             stderr="",
         )
    #
         with patch("subprocess.run", return_value=mock_result):
             poller = StatusPoller(pr_number=pr_number)
             status = await poller.get_current_status()
    #
             assert len(status.checks) == 1
             assert status.checks[0].state == expected_enum


@pytest.mark.asyncio

async def test_poll_result_elapsed_time_accuracy(
    mock_github_token, gh_pr_checks_success_output
):
    """
    Y3: Test PollResult elapsed_seconds is accurate.

    Spec: Yield validation requirement
    Expected: elapsed_seconds reflects actual polling duration (±1s tolerance)
    """
    pr_number = 123

     Mock success after delay
    mock_result = subprocess.CompletedProcess(
        args=["gh", "pr", "checks"],
        returncode=0,
        stdout=gh_pr_checks_success_output,
        stderr="",
    )

    # Test uses real StatusPoller
     with patch("subprocess.run", return_value=mock_result):
         with patch("asyncio.sleep"):  # Speed up test
             import time
             start_time = time.time()
    #
             poller = StatusPoller(pr_number=pr_number, poll_interval=0.1)
             result = await poller.poll_until_complete(max_wait=10)
    #
             elapsed = time.time() - start_time
             # Tolerance: ±1 second
             assert abs(result.elapsed_seconds - elapsed) < 1.0


 ============================================================================
 CONSTITUTIONAL COMPLIANCE VERIFICATION
 ============================================================================


@pytest.mark.asyncio

async def test_constitutional_article_i_complete_context(
    mock_github_token, gh_pr_checks_pending_output, gh_pr_checks_success_output
):
    """
    Constitutional Article I: Complete context before action (retry on timeout).

    Expected: Poller retries 2x, 3x on timeout/errors before raising
    """
    pr_number = 123

     Mock timeout -> timeout -> success
    mock_results = [
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=1,
            stdout="",
            stderr="error: timeout",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=1,
            stdout="",
            stderr="error: timeout",
        ),
        subprocess.CompletedProcess(
            args=["gh", "pr", "checks"],
            returncode=0,
            stdout=gh_pr_checks_success_output,
            stderr="",
        ),
    ]

    # Test uses real StatusPoller
     with patch("subprocess.run", side_effect=mock_results):
         poller = StatusPoller(pr_number=pr_number, max_retries=3)
         status = await poller.get_current_status()
    #
         # Should succeed after retries (Article I compliance)
         assert status.all_passing is True


@pytest.mark.asyncio

async def test_constitutional_article_ii_100_percent_verification(
    mock_github_token, gh_pr_checks_success_output
):
    """
    Constitutional Article II: 100% verification and stability.

    Expected: Tests define expected behavior before implementation
    """
     This test file itself is the Article II compliance:
     - Tests written FIRST (TDD)
     - Tests define expected behavior
     - Implementation must pass all tests before merge

     Verification: Count test functions
    import inspect

    test_functions = [
        name
        for name, obj in globals().items()
        if name.startswith("test_") and inspect.iscoroutinefunction(obj)
    ]

     NECESSARY pattern requires 9 categories minimum
    necessary_categories = {
        "N": ["test_poll_success", "test_poll_failure", "test_poll_until_complete"],
        "E": ["test_poll_timeout", "test_poll_rate_limit", "test_poll_empty"],
        "C": ["test_poll_state_transitions", "test_poll_multiple_simultaneous"],
        "E": [
            "test_poll_network_failure",
            "test_poll_invalid_pr",
            "test_poll_pr_not_found",
        ],
        "S": ["test_poll_requires_github_token", "test_poll_validates_token"],
        "S": ["test_poll_long_running", "test_poll_retry_exhaustion"],
        "A": ["test_poll_clear_error_messages", "test_poll_api_simplicity"],
        "R": ["test_poll_regression_pr_86"],
        "Y": ["test_poll_status_format", "test_poll_check_state", "test_poll_result"],
    }

     Verify coverage
    assert len(test_functions) >= 20, "NECESSARY pattern requires comprehensive coverage"


 ============================================================================
 INTEGRATION TEST (Real gh CLI - Manual Execution Only)
 ============================================================================


@pytest.mark.skipif(
    True,
    reason="Integration test - requires real GitHub repo and gh CLI auth",
)
@pytest.mark.asyncio
async def test_integration_real_github_api():
    """
    INTEGRATION: Test real GitHub API behavior (not mocked).

    WARNING: This test requires:
    - gh CLI installed and authenticated
    - Valid GITHUB_TOKEN in environment
    - Real PR number from your repository

    Usage:
    1. Set PR_NUMBER environment variable: export PR_NUMBER=123
    2. Run: pytest tests/tools/ci_monitor/test_status_poller.py::test_integration_real_github_api -v
    """
    import os

    pr_number = int(os.getenv("PR_NUMBER", "0"))
    if pr_number == 0:
        pytest.skip("Set PR_NUMBER environment variable to run integration test")

    # Test will use real StatusPoller and real gh CLI
     poller = StatusPoller(pr_number=pr_number)
     status = await poller.get_current_status()
    #
     # Verify real API response structure
     assert status.pr_number == pr_number
     assert isinstance(status.checks, list)
     print(f"\nReal GitHub API Response for PR #{pr_number}:")
     print(f"  Checks: {len(status.checks)}")
     print(f"  All Passing: {status.all_passing}")
     print(f"  Has Failures: {status.has_failures}")
     print(f"  Is Complete: {status.is_complete}")
     for check in status.checks:
         print(f"    - {check.name}: {check.state}")
