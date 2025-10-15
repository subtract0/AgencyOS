"""
Graceful fallback handlers for external dependency failures.

Provides constitutional-compliant fallback strategies when infrastructure
components (VectorStore, local models, GitHub API, etc.) are unavailable.

All fallback functions return Result<FallbackResult, FallbackError> to ensure
graceful degradation without bypassing constitutional requirements.

Constitutional Compliance:
- Article I: Complete context (retries ensure context availability)
- Article II: 100% verification (fallbacks don't skip tests)
- Article III: Automated enforcement (no manual bypasses)
- Article IV: VectorStore fallback doesn't block execution
- Article V: Spec-driven (tests trace to FALLBACK-001 through FALLBACK-007)

Functions:
- handle_vectorstore_unavailable(): VectorStore connection failures
- handle_local_model_unavailable(): Ollama health check failures
- handle_github_rate_limit(): GitHub API 429 rate limits
- handle_precommit_failure(): Pre-commit hook failures
- retry_with_exponential_backoff(): Generic retry utility

Usage:
    from tools.orchestrator.fallback_handler import (
        handle_vectorstore_unavailable,
        handle_local_model_unavailable,
        handle_github_rate_limit,
        handle_precommit_failure,
        retry_with_exponential_backoff,
    )
"""

import asyncio
import subprocess
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypeVar

from shared.agent_context import AgentContext
from shared.models.orchestrator_models import (
    FallbackError,
    FallbackResult,
    FallbackStrategy,
)
from shared.type_definitions.result import Err, Ok, Result

T = TypeVar("T")


def handle_vectorstore_unavailable(
    context: AgentContext,
    operation: str,
    timeout_ms: int = 10000
) -> Result[FallbackResult, FallbackError]:
    """
    Handle VectorStore connection failures gracefully.

    Strategies:
    - SESSION_ONLY: Use session memory instead (connection errors)
    - SKIP_LEARNING: Skip VectorStore queries for performance (timeouts)
    - READ_ONLY: VectorStore read-only mode (store fails, query succeeds)

    Args:
        context: Agent context with memory API
        operation: Operation that failed (e.g., "store_pattern", "search_patterns")
        timeout_ms: Timeout limit in milliseconds (default: 10000)

    Returns:
        Ok(FallbackResult) with strategy and warning
        Err(FallbackError) only for permanent failures

    Constitutional Compliance:
        Article IV: Session memory fallback preserves learning capability
        Article II: Test verification still required

    Example:
        >>> result = handle_vectorstore_unavailable(context, "search_patterns")
        >>> assert result.is_ok()
        >>> fallback = result.unwrap()
        >>> assert fallback.strategy == FallbackStrategy.SESSION_ONLY
    """
    start_time = time.time()

    try:
        # Check if it's a timeout error by attempting VectorStore access
        # This will raise TimeoutError if the timeout was the issue
        try:
            context.search_memories(tags=["test"], max_results=1)
        except TimeoutError:
            # Timeout detected → SKIP_LEARNING
            latency_ms = (time.time() - start_time) * 1000
            return Ok(FallbackResult(
                strategy=FallbackStrategy.SKIP_LEARNING,
                success=True,
                warning_message="VectorStore timeout, skipping learning queries for performance",
                execution_continues=True,
                latency_ms=latency_ms,
                compliance_notes="Article II: Test verification still required. Article IV: Performance optimization, session memory fallback"
            ))
        except PermissionError as e:
            # Permanent failure (auth error)
            latency_ms = (time.time() - start_time) * 1000
            return Ok(FallbackResult(
                strategy=FallbackStrategy.SESSION_ONLY,
                success=True,
                warning_message=f"VectorStore authentication failed: {e}",
                permanent_failure=True,
                retry_count=0,
                latency_ms=latency_ms,
                compliance_notes="Article II: Test verification still required. Article IV: Authentication errors are not retryable"
            ))
        except ConnectionError:
            # Connection error
            pass

        # Detect error type for store operations
        if operation == "store_pattern":
            # Try query to check if read-only
            try:
                test_result = context.search_memories(tags=["test"], max_results=1)
                # Store failed but query works → READ_ONLY
                latency_ms = (time.time() - start_time) * 1000
                return Ok(FallbackResult(
                    strategy=FallbackStrategy.READ_ONLY,
                    success=True,
                    warning_message="VectorStore in read-only mode (write operations unavailable)",
                    execution_continues=True,
                    latency_ms=latency_ms,
                    compliance_notes="Article II: Test verification still required. Article IV: Learning continues via session memory"
                ))
            except (TimeoutError, ConnectionError, PermissionError):
                # Connection/permission error → SESSION_ONLY
                pass

        # Default: SESSION_ONLY fallback
        latency_ms = (time.time() - start_time) * 1000
        return Ok(FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            success=True,
            warning_message="VectorStore unavailable, using session memory as fallback",
            execution_continues=True,
            latency_ms=latency_ms,
            compliance_notes="Article II: Test verification still required. Article IV: Session memory fallback preserves learning capability"
        ))

    except PermissionError as e:
        # Permanent failure (auth error) - top-level catch
        latency_ms = (time.time() - start_time) * 1000
        return Ok(FallbackResult(
            strategy=FallbackStrategy.SESSION_ONLY,
            success=True,
            warning_message=f"VectorStore authentication failed: {e}",
            permanent_failure=True,
            retry_count=0,
            latency_ms=latency_ms,
            compliance_notes="Article II: Test verification still required. Article IV: Authentication errors are not retryable"
        ))


async def handle_local_model_unavailable(
    context: AgentContext,
    health_check_fn: Callable[[], Awaitable[dict[str, Any]]],
    task_tier: str = "P3",
    timeout_seconds: int = 5
) -> Result[FallbackResult, FallbackError]:
    """
    Handle local model (Ollama) unavailability → route to cloud.

    Strategy: CLOUD_ROUTING (P3 tasks to gpt-4o)

    Args:
        context: Agent context
        health_check_fn: Async health check function
        task_tier: Task tier (P1/P2/P3, default: P3)
        timeout_seconds: Health check timeout (default: 5)

    Returns:
        Ok(FallbackResult) with cloud routing details
        Err(FallbackError) should not happen (always fallback)

    Constitutional Compliance:
        Article III: Budget guard still enforces cost limits for cloud usage

    Example:
        >>> result = await handle_local_model_unavailable(
        ...     context,
        ...     health_check_fn=async_health_check,
        ...     task_tier="P3"
        ... )
        >>> assert result.is_ok()
        >>> fallback = result.unwrap()
        >>> assert fallback.strategy == FallbackStrategy.CLOUD_ROUTING
    """
    try:
        # Run health check with timeout
        health_result = await asyncio.wait_for(
            health_check_fn(),
            timeout=timeout_seconds
        )

        # If healthy, return (no fallback needed)
        if health_result.get("status") == "healthy":
            return Ok(FallbackResult(
                strategy=FallbackStrategy.CLOUD_ROUTING,
                success=False,  # No fallback needed
                warning_message="Local model healthy, no fallback required",
                execution_continues=True
            ))

    except (TimeoutError, ConnectionError, Exception) as e:
        # Health check failed or timed out → route to cloud
        error_type = e.__class__.__name__
        return Ok(FallbackResult(
            strategy=FallbackStrategy.CLOUD_ROUTING,
            success=True,
            warning_message=f"Local model unavailable ({error_type}), routing {task_tier} tasks to cloud API (gpt-4o)",
            suggested_fix="Check Ollama service: ollama list",
            execution_continues=True,
            compliance_notes="Article III: Budget guard still enforces cost limits for cloud usage"
        ))

    # Fallback for unhealthy status
    return Ok(FallbackResult(
        strategy=FallbackStrategy.CLOUD_ROUTING,
        success=True,
        warning_message=f"Local model unhealthy, routing {task_tier} tasks to cloud API (gpt-4o)",
        suggested_fix="Check Ollama service: ollama list",
        execution_continues=True,
        compliance_notes="Article III: Budget guard still enforces cost limits for cloud usage",
        budget_guard_active=True
    ))


async def handle_github_rate_limit(
    context: AgentContext,
    api_call_fn: Callable[[], Awaitable[dict[str, Any]]],
    max_retries: int = 5
) -> Result[FallbackResult, FallbackError]:
    """
    Handle GitHub API 429 rate limit with exponential backoff.

    Backoff delays: 2s, 4s, 8s, 16s, 32s (max 5 retries)

    Args:
        context: Agent context
        api_call_fn: Async API call function to retry
        max_retries: Maximum retry attempts (default: 5)

    Returns:
        Ok(FallbackResult) with RETRY_SUCCESS if succeeds
        Err(FallbackError) with RETRY_EXHAUSTED if all fail

    Constitutional Compliance:
        Article I: Exponential backoff retry protocol

    Example:
        >>> result = await handle_github_rate_limit(
        ...     context,
        ...     api_call_fn=github_api_call,
        ...     max_retries=5
        ... )
        >>> assert result.is_ok()
        >>> fallback = result.unwrap()
        >>> assert fallback.strategy == FallbackStrategy.RETRY_SUCCESS
    """
    for attempt in range(max_retries):
        try:
            result = await api_call_fn()

            # Success
            return Ok(FallbackResult(
                strategy=FallbackStrategy.RETRY_SUCCESS,
                success=True,
                warning_message=f"GitHub API call succeeded on attempt {attempt + 1}",
                retry_count=attempt,
                execution_continues=True
            ))

        except Exception as e:
            error_message = str(e)

            # Check if permanent failure (401, 403)
            if "401" in error_message or "403" in error_message:
                return Err(FallbackError(
                    error_type="PERMANENT_FAILURE",
                    message=error_message,
                    retry_count=0,
                    suggested_fix="Check GitHub API key: gh auth status"
                ))

            # Transient failure (429, network)
            if attempt < max_retries - 1:
                delay = 2 ** (attempt + 1)  # 2, 4, 8, 16, 32 seconds
                await asyncio.sleep(delay)
                continue

    # All retries exhausted
    return Err(FallbackError(
        error_type="RETRY_EXHAUSTED",
        message=f"HTTP 429: GitHub API rate limit retry exhausted after {max_retries} attempts",
        retry_count=max_retries,
        suggested_fix="Wait for rate limit reset or increase timeout"
    ))


def handle_precommit_failure(
    hook_output: str,
    repo_path: Path,
    auto_fix: bool = False
) -> Result[FallbackResult, FallbackError]:
    """
    Handle pre-commit hook failures (linting, formatting).

    Strategies:
    - AUTO_FIX_SUCCESS: Apply ruff --fix and retry
    - USER_INTERVENTION: Display error and suggest manual fix

    Args:
        hook_output: Pre-commit hook output containing errors
        repo_path: Repository path for running auto-fix
        auto_fix: Whether to apply auto-fix (default: False)

    Returns:
        Ok(FallbackResult) with strategy

    Constitutional Compliance:
        Article II: Tests still required before merge

    Example:
        >>> result = handle_precommit_failure(
        ...     hook_output="F401 [*] `os` imported but unused",
        ...     repo_path=Path("/repo"),
        ...     auto_fix=True
        ... )
        >>> assert result.is_ok()
        >>> fallback = result.unwrap()
        >>> assert fallback.strategy == FallbackStrategy.AUTO_FIX_SUCCESS
    """
    # Parse error from hook output
    # Example: "tests/test_example.py:10:5: F401 [*] `os` imported but unused"

    if auto_fix and "[*]" in hook_output:  # Auto-fixable error
        # Run ruff --fix
        try:
            subprocess.run(
                ["ruff", "check", "--fix", str(repo_path)],
                capture_output=True,
                text=True,
                check=True
            )

            return Ok(FallbackResult(
                strategy=FallbackStrategy.AUTO_FIX_SUCCESS,
                success=True,
                warning_message="Linting errors auto-fixed with ruff --fix",
                suggested_fix="Commit retried after auto-fix",
                retry_count=1,
                execution_continues=True,
                test_verification_required=True,
                compliance_notes="Article II: Tests still required before merge",
                next_steps="1. Verify auto-fix results\n2. Run tests: pytest\n3. Retry commit"
            ))

        except subprocess.CalledProcessError as e:
            return Ok(FallbackResult(
                strategy=FallbackStrategy.USER_INTERVENTION,
                success=False,
                warning_message=f"Auto-fix failed: {e}",
                suggested_fix="Manually fix linting errors: ruff check --fix .",
                execution_continues=False,
                next_steps="1. Fix linting errors manually\n2. Run tests: pytest\n3. Retry commit"
            ))

    # Manual intervention required
    return Ok(FallbackResult(
        strategy=FallbackStrategy.USER_INTERVENTION,
        success=False,
        warning_message=f"Pre-commit hook failed:\n{hook_output}",
        suggested_fix="Fix errors manually: ruff check --fix . && pytest",
        execution_continues=False,
        next_steps="1. Fix linting errors\n2. Run tests: pytest\n3. Retry commit"
    ))


async def retry_with_exponential_backoff(
    operation_fn: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay_seconds: float = 2.0,
    abort_on_errors: list[str] | None = None
) -> Result[T, FallbackError]:
    """
    Generic retry utility with exponential backoff.

    Args:
        operation_fn: Async function to retry
        max_retries: Max retry attempts (total attempts = max_retries + 1)
        base_delay_seconds: Base delay (2s → 4s → 8s → ...)
        abort_on_errors: Error codes to abort immediately (e.g., ["401", "403"])

    Returns:
        Ok(result) on success
        Err(FallbackError) on exhaustion or permanent failure

    Constitutional Compliance:
        Article I: Exponential backoff retry protocol (2x, 3x, up to 10x)

    Example:
        >>> result = await retry_with_exponential_backoff(
        ...     operation_fn=async_operation,
        ...     max_retries=3,  # 4 total attempts
        ...     base_delay_seconds=2.0,
        ...     abort_on_errors=["401", "403"]
        ... )
        >>> assert result.is_ok()
    """
    abort_on_errors = abort_on_errors or []

    # Total attempts = max_retries + 1 (initial attempt + retries)
    for attempt in range(max_retries + 1):
        try:
            result = await operation_fn()
            return Ok(result)

        except Exception as e:
            error_message = str(e)

            # Check for permanent error codes
            if any(code in error_message for code in abort_on_errors):
                return Err(FallbackError(
                    error_type="PERMANENT_FAILURE",
                    message=error_message,
                    retry_count=attempt,
                    suggested_fix="Fix error before retrying"
                ))

            # Retry with exponential backoff
            if attempt < max_retries:
                delay = base_delay_seconds * (2 ** attempt)
                await asyncio.sleep(delay)
                continue

    return Err(FallbackError(
        error_type="RETRY_EXHAUSTED",
        message=f"Operation failed after {max_retries + 1} attempts",
        retry_count=max_retries + 1
    ))


__all__ = [
    "handle_vectorstore_unavailable",
    "handle_local_model_unavailable",
    "handle_github_rate_limit",
    "handle_precommit_failure",
    "retry_with_exponential_backoff",
]
