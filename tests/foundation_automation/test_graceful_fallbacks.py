"""
Graceful Fallback Tests for Foundation Automation (RED Phase - TDD)

Tests graceful degradation when external dependencies fail during orchestrator execution.
These tests MUST fail initially (ImportError) as the implementation doesn't exist yet.

Covers acceptance criteria FALLBACK-001 through FALLBACK-007 from SPEC-030:
- FALLBACK-001: VectorStore unavailable → log warning, continue execution
- FALLBACK-002: VectorStore error → skip learning queries, execution continues
- FALLBACK-003: Local model unreachable → use gpt-4o for P3 tasks
- FALLBACK-004: Ollama health check timeout (5s) → fallback to cloud
- FALLBACK-005: GitHub API 429 rate limit → retry with exponential backoff
- FALLBACK-006: Pre-commit hook failure → display error, suggest fixes
- FALLBACK-007: Linting errors → auto-fix with ruff, retry commit

NECESSARY Pattern Coverage:
- Normal: Fallbacks activated when external dependencies fail
- Edge: Multiple simultaneous failures, retry exhaustion
- Constraints: Timeout limits, retry count limits, error message format
- Error: Permanent failures vs transient failures, fallback chain exhaustion
- Security: Fallbacks don't bypass constitutional requirements
- Scale: Fallback latency <100ms, exponential backoff timing
- Asynchronous: Parallel fallback checks, no race conditions
- Retry: Exponential backoff (2s, 4s, 8s, 16s, 32s), max 5 attempts

Constitutional Compliance:
- Article I: Complete context (retries ensure context availability)
- Article II: 100% verification (fallbacks don't skip tests)
- Article III: Automated enforcement (no manual bypasses)
- Article IV: VectorStore fallback doesn't block execution
- Article V: Spec-driven (tests trace to FALLBACK-001 through FALLBACK-007)

Expected Initial State: ALL TESTS FAIL with ImportError
Expected After Implementation: ALL TESTS PASS with 100% rate
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from shared.agent_context import AgentContext
from shared.models.orchestrator_models import GitHubAPIResponse, HealthCheckResponse
from shared.type_definitions.result import Err, Ok, Result

# THESE IMPORTS WILL FAIL - IMPLEMENTATION DOESN'T EXIST YET (RED PHASE)
# Tests will fail with ImportError when fallback_handler.py doesn't exist
try:
    from tools.orchestrator.fallback_handler import (
        FallbackError,
        FallbackResult,
        FallbackStrategy,
        handle_github_rate_limit,
        handle_local_model_unavailable,
        handle_precommit_failure,
        handle_vectorstore_unavailable,
        retry_with_exponential_backoff,
    )
except ImportError:
    # Expected in RED phase - mark tests as expected to fail
    FallbackError = None  # type: ignore
    FallbackResult = None  # type: ignore
    FallbackStrategy = None  # type: ignore
    handle_github_rate_limit = None  # type: ignore
    handle_local_model_unavailable = None  # type: ignore
    handle_precommit_failure = None  # type: ignore
    handle_vectorstore_unavailable = None  # type: ignore
    retry_with_exponential_backoff = None  # type: ignore


# ============================================================================
# NECESSARY NORMAL: Fallbacks activated when external dependencies fail
# ============================================================================


def test_vectorstore_unavailable_logs_warning_continues_execution(
    mock_agent_context: AgentContext,
) -> None:
    """
    FALLBACK-001 NECESSARY Normal: VectorStore unavailable → log warning, continue execution.

    Validates:
    - VectorStore connection error detected
    - Warning logged with actionable message
    - Execution continues without VectorStore queries
    - Session memory used as fallback

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=SESSION_ONLY)
    """
    # Arrange: Simulate VectorStore connection error
    mock_agent_context.search_memories = Mock(
        side_effect=ConnectionError("VectorStore unreachable")
    )

    # Act
    result = handle_vectorstore_unavailable(context=mock_agent_context, operation="search_patterns")

    # Assert
    assert result.is_ok(), f"VectorStore fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.SESSION_ONLY
    assert "VectorStore unavailable" in fallback_result.warning_message
    assert fallback_result.execution_continues is True
    assert "session memory" in fallback_result.warning_message.lower()


def test_vectorstore_timeout_skips_learning_queries(
    mock_agent_context: AgentContext,
) -> None:
    """
    FALLBACK-002 NECESSARY Normal: VectorStore timeout → skip learning queries, continue.

    Validates:
    - VectorStore query timeout detected (>10s)
    - Learning queries skipped for performance
    - Execution continues without learnings
    - Timeout logged for monitoring

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=SKIP_LEARNING)
    """
    # Arrange: Simulate VectorStore timeout
    mock_agent_context.search_memories = Mock(side_effect=TimeoutError("VectorStore timeout"))

    # Act
    result = handle_vectorstore_unavailable(
        context=mock_agent_context, operation="query_learnings", timeout_ms=10000
    )

    # Assert
    assert result.is_ok(), f"VectorStore timeout fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.SKIP_LEARNING
    assert "timeout" in fallback_result.warning_message.lower()
    assert fallback_result.execution_continues is True
    assert fallback_result.latency_ms < 100  # Fallback should be fast (<100ms)


@pytest.mark.asyncio
async def test_local_model_unavailable_routes_to_cloud(
    mock_agent_context: AgentContext,
) -> None:
    """
    FALLBACK-003 NECESSARY Normal: Local model unreachable → use gpt-4o for P3 tasks.

    Validates:
    - Ollama health check fails
    - P3 tasks routed to gpt-4o (cloud API)
    - Model selection updated dynamically
    - Cost tracking updated for cloud usage

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=CLOUD_ROUTING)
    """
    # Arrange: Simulate Ollama health check failure
    mock_health_check = AsyncMock(
        return_value={"status": "unhealthy", "error": "Connection refused"}
    )

    # Act
    result = await handle_local_model_unavailable(
        context=mock_agent_context,
        health_check_fn=mock_health_check,
        task_tier="P3",  # Simple tasks normally use local model
    )

    # Assert
    assert result.is_ok(), f"Local model fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.CLOUD_ROUTING
    assert "gpt-4o" in fallback_result.warning_message
    assert fallback_result.execution_continues is True
    assert "cloud api" in fallback_result.warning_message.lower()


@pytest.mark.asyncio
async def test_ollama_health_check_timeout_fallback_to_cloud(
    mock_agent_context: AgentContext,
) -> None:
    """
    FALLBACK-004 NECESSARY Normal: Ollama health check timeout (5s) → fallback to cloud.

    Validates:
    - Health check timeout (5s limit)
    - Immediate fallback to cloud API
    - No retry attempts on health check
    - Timeout logged for diagnostics

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=CLOUD_ROUTING)
    """

    # Arrange: Simulate health check timeout
    async def slow_health_check() -> HealthCheckResponse:
        await asyncio.sleep(6)  # Exceeds 5s timeout
        return HealthCheckResponse(status="healthy")

    # Act
    start_time = time.time()
    result = await handle_local_model_unavailable(
        context=mock_agent_context,
        health_check_fn=slow_health_check,
        timeout_seconds=5,
    )
    elapsed_time = time.time() - start_time

    # Assert
    assert result.is_ok(), f"Health check timeout fallback should succeed, got: {result}"
    assert elapsed_time < 6, "Fallback should abort health check before completion"

    fallback_result = result.unwrap()
    assert fallback_result.strategy == FallbackStrategy.CLOUD_ROUTING
    assert "timeout" in fallback_result.warning_message.lower()


@pytest.mark.asyncio
async def test_github_api_rate_limit_exponential_backoff(
    mock_agent_context: AgentContext,
) -> None:
    """
    FALLBACK-005 NECESSARY Normal: GitHub API 429 rate limit → retry with exponential backoff.

    Validates:
    - 429 status code detected
    - Exponential backoff: 2s, 4s, 8s, 16s, 32s
    - Retry succeeds on 3rd attempt
    - Backoff timing logged

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=RETRY_SUCCESS)
    """
    # Arrange: Simulate GitHub API 429 rate limit
    attempt_count = 0

    async def mock_github_api_call() -> GitHubAPIResponse:
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise Exception("HTTP 429: API rate limit exceeded")
        else:
            return GitHubAPIResponse(
                status="success", pr_url="https://github.com/org/repo/pull/123"
            )

    # Act
    start_time = time.time()
    result = await handle_github_rate_limit(
        context=mock_agent_context,
        api_call_fn=mock_github_api_call,
        max_retries=5,
    )
    elapsed_time = time.time() - start_time

    # Assert
    assert result.is_ok(), f"GitHub rate limit fallback should succeed, got: {result}"
    assert attempt_count == 3, "Should succeed on 3rd attempt"

    # Verify exponential backoff timing (2s + 4s = 6s total, allow ±1s margin)
    assert 5.0 < elapsed_time < 8.0, f"Backoff timing incorrect: {elapsed_time}s"

    fallback_result = result.unwrap()
    assert fallback_result.strategy == FallbackStrategy.RETRY_SUCCESS
    assert fallback_result.retry_count == 2  # 2 retries (3rd attempt succeeds)


def test_precommit_hook_failure_displays_actionable_error(tmp_path: Path) -> None:
    """
    FALLBACK-006 NECESSARY Normal: Pre-commit hook failure → display error, suggest fixes.

    Validates:
    - Pre-commit hook failure detected
    - Error message extracted from hook output
    - Actionable suggestions provided (ruff, pytest commands)
    - User guidance for manual fix

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=USER_INTERVENTION)
    """
    # Arrange: Simulate pre-commit hook failure
    hook_output = """
[INFO] Installing environment for https://github.com/astral-sh/ruff-pre-commit.
[INFO] Ruff....................................................................Failed
- hook id: ruff
- exit code: 1

tests/test_example.py:10:5: F401 [*] `os` imported but unused
Found 1 error.
"""

    # Act
    result = handle_precommit_failure(hook_output=hook_output, repo_path=tmp_path, auto_fix=False)

    # Assert
    assert result.is_ok(), f"Pre-commit fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.USER_INTERVENTION
    assert "F401" in fallback_result.warning_message  # Error code preserved
    assert "ruff check" in fallback_result.suggested_fix.lower()
    assert "imported but unused" in fallback_result.warning_message


def test_linting_errors_auto_fix_with_ruff_retry_commit(tmp_path: Path) -> None:
    """
    FALLBACK-007 NECESSARY Normal: Linting errors → auto-fix with ruff, retry commit.

    Validates:
    - Linting errors detected (unused imports, formatting)
    - ruff --fix applied automatically
    - Commit retried after fixes
    - Success logged

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=AUTO_FIX_SUCCESS)
    """
    # Arrange: Create test file with linting errors
    test_file = tmp_path / "test_example.py"
    test_file.write_text("import os\n\ndef test_example():\n    pass\n")

    hook_output = "tests/test_example.py:1:1: F401 [*] `os` imported but unused"

    # Act
    result = handle_precommit_failure(hook_output=hook_output, repo_path=tmp_path, auto_fix=True)

    # Assert
    assert result.is_ok(), f"Linting auto-fix fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.AUTO_FIX_SUCCESS
    assert fallback_result.retry_count == 1
    assert "ruff --fix" in fallback_result.warning_message.lower()
    assert fallback_result.execution_continues is True


# ============================================================================
# NECESSARY EDGE: Multiple simultaneous failures, retry exhaustion
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_fallbacks_simultaneously_no_race_conditions(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Edge: Multiple fallbacks triggered simultaneously → no race conditions.

    Validates:
    - VectorStore + Local Model failures handled in parallel
    - No deadlocks or race conditions
    - Both fallbacks complete successfully
    - Independent fallback strategies applied

    Expected: Both fallbacks succeed independently
    """
    # Arrange: Simulate both VectorStore and local model failures
    mock_agent_context.search_memories = Mock(
        side_effect=ConnectionError("VectorStore unreachable")
    )

    async def failing_health_check() -> HealthCheckResponse:
        raise ConnectionError("Ollama unreachable")

    # Act: Run both fallbacks in parallel
    results = await asyncio.gather(
        asyncio.to_thread(handle_vectorstore_unavailable, mock_agent_context, "search_patterns"),
        handle_local_model_unavailable(mock_agent_context, failing_health_check),
        return_exceptions=True,
    )

    # Assert
    assert len(results) == 2
    assert all(isinstance(r, Result) and r.is_ok() for r in results)

    vectorstore_result = results[0].unwrap()
    local_model_result = results[1].unwrap()

    assert vectorstore_result.strategy == FallbackStrategy.SESSION_ONLY
    assert local_model_result.strategy == FallbackStrategy.CLOUD_ROUTING


@pytest.mark.asyncio
async def test_retry_exhaustion_after_max_attempts(mock_agent_context: AgentContext) -> None:
    """
    NECESSARY Edge: GitHub API retries exhausted (5 attempts) → return error with details.

    Validates:
    - Exponential backoff retries 5 times
    - All retries fail
    - Error returned with retry count
    - Timing logged for diagnostics

    Expected: Result<FallbackResult, FallbackError> with Err(RETRY_EXHAUSTED)
    """

    # Arrange: Simulate permanent GitHub API failure
    async def permanent_failure() -> GitHubAPIResponse:
        raise Exception("HTTP 429: API rate limit exceeded")

    # Act
    result = await handle_github_rate_limit(
        context=mock_agent_context,
        api_call_fn=permanent_failure,
        max_retries=5,
    )

    # Assert
    assert result.is_err(), "Retry exhaustion should return error"
    error = result.unwrap_err()

    assert error.error_type == "RETRY_EXHAUSTED"
    assert error.retry_count == 5
    assert "429" in error.message
    assert error.permanent_failure is True


def test_vectorstore_partial_failure_query_succeeds_store_fails(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Edge: VectorStore partially available (query OK, store fails) → log warning.

    Validates:
    - Query operations succeed
    - Store operations fail
    - Warning logged for partial availability
    - Execution continues (read-only mode)

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=READ_ONLY)
    """
    # Arrange: Query succeeds, store fails
    mock_agent_context.search_memories = Mock(return_value=[{"pattern": "TDD"}])
    mock_agent_context.store_memory = Mock(side_effect=ConnectionError("Write operation failed"))

    # Act
    result = handle_vectorstore_unavailable(context=mock_agent_context, operation="store_pattern")

    # Assert
    assert result.is_ok(), f"Partial VectorStore failure should fallback, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.READ_ONLY
    assert "read-only" in fallback_result.warning_message.lower()
    assert fallback_result.execution_continues is True


@pytest.mark.asyncio
async def test_local_model_latency_spike_fallback_after_5s(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Edge: Local model latency spike (>5s) → fallback to cloud.

    Validates:
    - Health check takes >5s (slow response, not timeout)
    - Fallback triggered on latency spike
    - Cloud routing applied
    - Latency logged for monitoring

    Expected: Result<FallbackResult, FallbackError> with OK(strategy=CLOUD_ROUTING)
    """

    # Arrange: Simulate slow health check
    async def slow_health_check() -> HealthCheckResponse:
        await asyncio.sleep(6)
        return HealthCheckResponse(status="healthy")

    # Act
    result = await handle_local_model_unavailable(
        context=mock_agent_context,
        health_check_fn=slow_health_check,
        timeout_seconds=5,
    )

    # Assert
    assert result.is_ok(), f"Latency spike fallback should succeed, got: {result}"
    fallback_result = result.unwrap()

    assert fallback_result.strategy == FallbackStrategy.CLOUD_ROUTING
    assert (
        "latency" in fallback_result.warning_message.lower()
        or "timeout" in fallback_result.warning_message.lower()
    )


# ============================================================================
# NECESSARY CONSTRAINTS: Timeout limits, retry count limits
# ============================================================================


def test_vectorstore_timeout_limit_10_seconds(mock_agent_context: AgentContext) -> None:
    """
    NECESSARY Constraints: VectorStore timeout limit is 10 seconds (default).

    Validates:
    - Timeout enforced at 10s
    - TimeoutError raised if exceeded
    - Fallback triggered after timeout

    Expected: Fallback activated after 10s timeout
    """

    # Arrange: Simulate timeout error
    def timeout_query(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise TimeoutError("VectorStore query exceeded 10s timeout")

    mock_agent_context.search_memories = timeout_query

    # Act
    start_time = time.time()
    result = handle_vectorstore_unavailable(
        context=mock_agent_context, operation="search_patterns", timeout_ms=10000
    )
    elapsed_time = time.time() - start_time

    # Assert
    assert elapsed_time < 1.0, "Should return immediately on TimeoutError"
    assert result.is_ok(), "Timeout should trigger fallback"
    assert result.unwrap().strategy == FallbackStrategy.SKIP_LEARNING


@pytest.mark.asyncio
async def test_github_api_retry_limit_5_attempts(mock_agent_context: AgentContext) -> None:
    """
    NECESSARY Constraints: GitHub API retry limit is 5 attempts maximum.

    Validates:
    - Max 5 retry attempts enforced
    - No 6th attempt made
    - Error returned after 5 failures

    Expected: Err(RETRY_EXHAUSTED) after exactly 5 attempts
    """
    # Arrange: Count retry attempts
    attempt_count = 0

    async def always_fails() -> GitHubAPIResponse:
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("HTTP 429: Rate limit")

    # Act
    result = await handle_github_rate_limit(
        context=mock_agent_context,
        api_call_fn=always_fails,
        max_retries=5,
    )

    # Assert
    assert result.is_err(), "Should return error after max retries"
    assert attempt_count == 5, f"Should attempt exactly 5 times, got {attempt_count}"


@pytest.mark.asyncio
async def test_exponential_backoff_timing_validation() -> None:
    """
    NECESSARY Constraints: Exponential backoff follows 2s, 4s, 8s, 16s, 32s timing.

    Validates:
    - First retry: 2s delay
    - Second retry: 4s delay
    - Third retry: 8s delay
    - Timing accuracy ±500ms

    Expected: Retry delays match exponential backoff formula
    """
    # Arrange: Track retry timings
    retry_times: list[float] = []
    start_time = time.time()

    async def mock_operation() -> None:
        retry_times.append(time.time() - start_time)
        if len(retry_times) < 4:
            raise Exception("Transient failure")

    # Act
    result = await retry_with_exponential_backoff(
        operation_fn=mock_operation,
        max_retries=3,
        base_delay_seconds=2,
    )

    # Assert
    assert result.is_ok(), "Should succeed on 4th attempt"
    assert len(retry_times) == 4, "Should have 4 attempts"

    # Verify exponential backoff timing (±500ms tolerance)
    # Attempt 1: 0s, Attempt 2: ~2s, Attempt 3: ~6s (2+4), Attempt 4: ~14s (2+4+8)
    expected_timings = [0, 2, 6, 14]
    tolerance = 0.5

    for i, expected in enumerate(expected_timings):
        actual = retry_times[i]
        assert abs(actual - expected) < tolerance, (
            f"Retry {i + 1} timing: expected ~{expected}s, got {actual:.2f}s"
        )


# ============================================================================
# NECESSARY ERROR: Permanent failures vs transient failures
# ============================================================================


@pytest.mark.asyncio
async def test_transient_failure_recovers_on_retry(mock_agent_context: AgentContext) -> None:
    """
    NECESSARY Error: Transient GitHub API failure → recovers on retry.

    Validates:
    - First attempt fails (transient network error)
    - Second attempt succeeds
    - Retry count logged
    - Success message includes retry info

    Expected: Result<FallbackResult, FallbackError> with OK(retry_count=1)
    """
    # Arrange: Transient failure on first attempt
    attempt_count = 0

    async def transient_failure() -> GitHubAPIResponse:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise Exception("Connection timeout")
        return GitHubAPIResponse(status="success")

    # Act
    result = await handle_github_rate_limit(
        context=mock_agent_context,
        api_call_fn=transient_failure,
        max_retries=3,
    )

    # Assert
    assert result.is_ok(), "Transient failure should recover on retry"
    assert attempt_count == 2, "Should succeed on 2nd attempt"

    fallback_result = result.unwrap()
    assert fallback_result.retry_count == 1


def test_permanent_vectorstore_failure_no_retry_immediate_fallback(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Error: Permanent VectorStore failure (auth error) → immediate fallback.

    Validates:
    - Authentication error detected (not retryable)
    - No retry attempts made
    - Immediate fallback to session memory
    - Permanent failure logged

    Expected: Result<FallbackResult, FallbackError> with OK(retry_count=0)
    """
    # Arrange: Simulate authentication error
    mock_agent_context.search_memories = Mock(
        side_effect=PermissionError("VectorStore authentication failed")
    )

    # Act
    result = handle_vectorstore_unavailable(context=mock_agent_context, operation="search_patterns")

    # Assert
    assert result.is_ok(), "Permanent failure should fallback immediately"
    fallback_result = result.unwrap()

    assert fallback_result.retry_count == 0, "No retries for auth errors"
    assert fallback_result.permanent_failure is True
    assert "authentication" in fallback_result.warning_message.lower()


@pytest.mark.asyncio
async def test_invalid_api_key_permanent_failure_no_retry(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Error: Invalid GitHub API key → permanent failure, no retry.

    Validates:
    - 401 Unauthorized detected (not retryable)
    - No retry attempts made
    - Error returned with actionable guidance
    - API key validation suggested

    Expected: Result<FallbackResult, FallbackError> with Err(PERMANENT_FAILURE)
    """

    # Arrange: Simulate invalid API key
    async def invalid_api_key() -> GitHubAPIResponse:
        raise Exception("HTTP 401: Unauthorized")

    # Act
    result = await handle_github_rate_limit(
        context=mock_agent_context,
        api_call_fn=invalid_api_key,
        max_retries=5,
    )

    # Assert
    assert result.is_err(), "Invalid API key should return error"
    error = result.unwrap_err()

    assert error.error_type == "PERMANENT_FAILURE"
    assert error.retry_count == 0, "No retries for auth errors"
    assert "401" in error.message
    assert "API key" in error.suggested_fix


# ============================================================================
# NECESSARY SECURITY: Fallbacks don't bypass constitutional requirements
# ============================================================================


def test_vectorstore_fallback_does_not_bypass_article_two_verification(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Security: VectorStore fallback → tests still required (Article II).

    Validates:
    - VectorStore unavailable
    - Test verification still enforced
    - No bypass mechanism exists
    - Constitutional gate remains active

    Expected: Fallback allows execution, but tests still required before merge
    """
    # Arrange: VectorStore unavailable
    mock_agent_context.search_memories = Mock(
        side_effect=ConnectionError("VectorStore unreachable")
    )

    # Act
    result = handle_vectorstore_unavailable(context=mock_agent_context, operation="search_patterns")

    # Assert
    assert result.is_ok(), "Fallback should succeed"
    fallback_result = result.unwrap()

    # Verify constitutional compliance preserved
    assert fallback_result.constitutional_bypass is False
    assert fallback_result.test_verification_required is True
    assert "Article II" in fallback_result.compliance_notes


@pytest.mark.asyncio
async def test_local_model_fallback_does_not_bypass_article_three_budget_guard(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Security: Local model fallback → budget guard still enforced (Article III).

    Validates:
    - Cloud routing fallback active
    - Budget guard still checks costs
    - No bypass for budget limits
    - Cost tracking updated for cloud usage

    Expected: Fallback triggers budget validation before execution
    """

    # Arrange: Local model unavailable
    async def failing_health_check() -> HealthCheckResponse:
        raise ConnectionError("Ollama unreachable")

    # Act
    result = await handle_local_model_unavailable(
        context=mock_agent_context,
        health_check_fn=failing_health_check,
    )

    # Assert
    assert result.is_ok(), "Fallback should succeed"
    fallback_result = result.unwrap()

    # Verify budget guard enforcement preserved
    assert fallback_result.constitutional_bypass is False
    assert fallback_result.budget_guard_active is True
    assert "Article III" in fallback_result.compliance_notes


def test_precommit_auto_fix_does_not_skip_test_verification(tmp_path: Path) -> None:
    """
    NECESSARY Security: Pre-commit auto-fix → tests still run before merge.

    Validates:
    - Linting auto-fix applied
    - Test suite still required
    - No bypass mechanism for test gate
    - Article II enforcement preserved

    Expected: Auto-fix succeeds, but tests still mandatory
    """
    # Arrange: Linting errors with auto-fix
    test_file = tmp_path / "test_example.py"
    test_file.write_text("import os\n\ndef test_example():\n    pass\n")

    hook_output = "tests/test_example.py:1:1: F401 [*] `os` imported but unused"

    # Act
    result = handle_precommit_failure(hook_output=hook_output, repo_path=tmp_path, auto_fix=True)

    # Assert
    assert result.is_ok(), "Auto-fix should succeed"
    fallback_result = result.unwrap()

    # Verify test verification still required
    assert fallback_result.test_verification_required is True
    assert fallback_result.constitutional_bypass is False
    assert "pytest" in fallback_result.next_steps.lower()


# ============================================================================
# NECESSARY SCALE: Fallback latency <100ms
# ============================================================================


def test_vectorstore_fallback_latency_under_100ms(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Scale: VectorStore fallback completes in <100ms.

    Validates:
    - Fallback detection fast (<100ms)
    - No blocking operations
    - Session memory activated immediately
    - Latency logged for monitoring

    Expected: Fallback latency <100ms
    """
    # Arrange: VectorStore unavailable
    mock_agent_context.search_memories = Mock(
        side_effect=ConnectionError("VectorStore unreachable")
    )

    # Act
    start_time = time.time()
    result = handle_vectorstore_unavailable(context=mock_agent_context, operation="search_patterns")
    elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

    # Assert
    assert result.is_ok(), "Fallback should succeed"
    assert elapsed_time < 100, f"Fallback latency {elapsed_time:.2f}ms exceeds 100ms limit"


@pytest.mark.asyncio
async def test_local_model_health_check_abort_latency_under_100ms(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Scale: Local model health check abort <100ms after timeout.

    Validates:
    - Health check timeout detected quickly
    - Abort operation fast (<100ms overhead)
    - Cloud routing activated immediately
    - No resource leaks from aborted check

    Expected: Timeout detection + fallback <100ms overhead
    """

    # Arrange: Health check that will timeout
    async def slow_health_check() -> HealthCheckResponse:
        await asyncio.sleep(10)
        return HealthCheckResponse(status="healthy")

    # Act
    start_time = time.time()
    result = await handle_local_model_unavailable(
        context=mock_agent_context,
        health_check_fn=slow_health_check,
        timeout_seconds=5,
    )
    elapsed_time = time.time() - start_time

    # Assert
    assert result.is_ok(), "Fallback should succeed"
    # Allow 5s timeout + <100ms overhead = 5.1s max
    assert elapsed_time < 5.1, f"Fallback took {elapsed_time:.2f}s, expected <5.1s"


# ============================================================================
# NECESSARY ASYNCHRONOUS: Parallel fallback checks, no race conditions
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_fallback_checks_no_deadlocks(
    mock_agent_context: AgentContext,
) -> None:
    """
    NECESSARY Asynchronous: Parallel VectorStore + TRM fallbacks → no deadlocks.

    Validates:
    - Multiple fallbacks triggered simultaneously
    - No shared state mutations
    - No deadlocks or race conditions
    - All fallbacks complete successfully

    Expected: All fallbacks succeed independently
    """
    # Arrange: Simulate multiple failures
    mock_agent_context.search_memories = Mock(
        side_effect=ConnectionError("VectorStore unreachable")
    )

    async def failing_health_check() -> HealthCheckResponse:
        raise ConnectionError("Ollama unreachable")

    async def failing_github_api() -> GitHubAPIResponse:
        raise Exception("HTTP 429: Rate limit")

    # Act: Run all fallbacks in parallel
    results = await asyncio.gather(
        asyncio.to_thread(handle_vectorstore_unavailable, mock_agent_context, "search_patterns"),
        handle_local_model_unavailable(mock_agent_context, failing_health_check),
        handle_github_rate_limit(mock_agent_context, failing_github_api, max_retries=1),
        return_exceptions=True,
    )

    # Assert
    assert len(results) == 3
    # VectorStore and local model should succeed, GitHub should fail (max retries)
    assert results[0].is_ok() and results[1].is_ok()


# ============================================================================
# NECESSARY RETRY: Exponential backoff validation
# ============================================================================


@pytest.mark.asyncio
async def test_exponential_backoff_timing_2s_4s_8s_16s_32s() -> None:
    """
    NECESSARY Retry: GitHub API exponential backoff follows 2s, 4s, 8s, 16s, 32s.

    Validates:
    - Retry delays match exponential formula: 2^n seconds
    - Timing accuracy ±500ms
    - Max 5 retries enforced
    - Backoff logged for monitoring

    Expected: Retry delays match [2s, 4s, 8s, 16s, 32s]
    """
    # Arrange: Track retry timings
    retry_delays: list[float] = []
    last_attempt_time: float | None = None
    attempt_count = 0

    async def track_retry_timing() -> GitHubAPIResponse:
        nonlocal last_attempt_time, attempt_count
        current_time = time.time()
        attempt_count += 1

        # Record delay for all attempts except the first (attempt 1 has no prior delay)
        if last_attempt_time is not None:
            retry_delays.append(current_time - last_attempt_time)

        last_attempt_time = current_time

        # Succeed on 6th attempt (after 5 retry delays recorded)
        if attempt_count < 6:
            raise Exception("Transient failure")
        return GitHubAPIResponse(status="success")

    # Act
    result = await retry_with_exponential_backoff(
        operation_fn=track_retry_timing,
        max_retries=5,
        base_delay_seconds=2,
    )

    # Assert
    assert result.is_ok(), "Should succeed on 6th attempt"
    assert len(retry_delays) == 5, "Should have 5 retry delays"

    # Verify exponential backoff: [2s, 4s, 8s, 16s, 32s]
    expected_delays = [2.0, 4.0, 8.0, 16.0, 32.0]
    tolerance = 0.5

    for i, expected in enumerate(expected_delays):
        actual = retry_delays[i]
        assert abs(actual - expected) < tolerance, (
            f"Retry {i + 1} delay: expected {expected}s, got {actual:.2f}s"
        )


@pytest.mark.asyncio
async def test_retry_abort_on_permanent_error_code_401() -> None:
    """
    NECESSARY Retry: 401 Unauthorized → abort retry immediately, no backoff.

    Validates:
    - Permanent error codes detected (401, 403)
    - Retry loop aborted immediately
    - No exponential backoff wasted
    - Error returned with guidance

    Expected: Err(PERMANENT_FAILURE) on first attempt, no retries
    """
    # Arrange: Permanent failure (invalid API key)
    attempt_count = 0

    async def permanent_auth_failure() -> GitHubAPIResponse:
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("HTTP 401: Unauthorized")

    # Act
    result = await retry_with_exponential_backoff(
        operation_fn=permanent_auth_failure,
        max_retries=5,
        base_delay_seconds=2,
        abort_on_errors=["401", "403"],  # Permanent error codes
    )

    # Assert
    assert result.is_err(), "Permanent error should abort retries"
    assert attempt_count == 1, "Should abort on first attempt, no retries"

    error = result.unwrap_err()
    assert error.error_type == "PERMANENT_FAILURE"
    assert "401" in error.message
