"""
Retry Controller with Exponential Backoff.

Constitutional Compliance:
- Article I: Complete context (retry 2x, 3x, up to 10x on timeout)
- Article II: 100% verification (all tests pass before merge)
- Article IV: VectorStore learning integration
- Article V: Traceable to spec-autonomous-ci-feedback-loop.md

Spec Traceability:
- AC-3: Autonomous retrigger (auto-retry with exponential backoff)
- AC-4: Max 5 retry attempts (smart notification on exhaustion)
- CI timeout: 600s limit (GitHub Actions workflow timeout)

Version: 1.0.0
Created: 2025-10-11
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from shared.type_definitions.result import Err, Ok, Result

T = TypeVar("T")


# ============================================================================
# PYDANTIC MODELS (Constitutional Law #2: Strict Typing)
# ============================================================================


class RetryPolicy(BaseModel):
    """
    Retry policy configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts (AC-4: 5 for CI)
        base_delay_s: Base delay in seconds (30s for CI)
        max_delay_s: Maximum delay cap (120s for CI)
        exponential: Use exponential backoff (True for CI)
    """

    max_attempts: int = Field(default=5, ge=1, le=10)
    base_delay_s: float = Field(default=30.0, ge=0.0)
    max_delay_s: float = Field(default=120.0, ge=0.0)
    exponential: bool = Field(default=True)


class RetryMetrics(BaseModel):
    """
    Retry execution metrics.

    Attributes:
        total_attempts: Total number of attempts made
        total_delay_s: Total delay time accumulated
        success: Whether the operation succeeded
        errors: List of error messages from failed attempts
    """

    total_attempts: int = Field(ge=0)
    total_delay_s: float = Field(ge=0.0)
    success: bool
    errors: list[str] = Field(default_factory=list)


class RetryExhausted(Exception):
    """
    Raised when retry attempts are exhausted.

    Attributes:
        attempts: Number of attempts made
        errors: List of error messages
    """

    def __init__(self, attempts: int, errors: list[str]):
        self.attempts = attempts
        self.errors = errors
        super().__init__(f"Retry exhausted after {attempts} attempts")


# ============================================================================
# RETRY CONTROLLER (Constitutional Law #8: Functions <50 lines)
# ============================================================================


class RetryController:
    """
    Retry controller with exponential backoff.

    Constitutional compliance:
    - Article I: Retries on timeout/failure (complete context)
    - Article IV: VectorStore integration for pattern learning
    """

    def __init__(
        self,
        policy: RetryPolicy,
        timeout_s: float | None = None,
        agent_context: Any | None = None,
    ):
        """
        Initialize retry controller.

        Args:
            policy: Retry policy configuration
            timeout_s: Optional global timeout in seconds
            agent_context: Optional AgentContext for VectorStore learning
        """
        self.policy = policy
        self.timeout_s = timeout_s
        self.agent_context = agent_context

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt (exponential backoff).

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds (capped at max_delay_s)
        """
        if not self.policy.exponential or self.policy.base_delay_s == 0:
            return self.policy.base_delay_s

        # Exponential backoff: base * 2^(attempt-1)
        delay = self.policy.base_delay_s * (2 ** (attempt - 1))
        return min(delay, self.policy.max_delay_s)

    def _should_retry_error(self, exception: Exception) -> bool:
        """
        Determine if error is retryable.

        Non-retryable errors (fail immediately):
        - KeyboardInterrupt (user intervention)
        - SystemExit (system shutdown)

        Args:
            exception: Exception to check

        Returns:
            True if error should be retried
        """
        non_retryable = (KeyboardInterrupt, SystemExit)
        return not isinstance(exception, non_retryable)

    async def retry_with_policy(
        self,
        operation: Callable[[], Any],  # Can be sync or async
        should_retry: Callable[[Exception], bool] | None = None,
    ) -> Result[tuple[T, RetryMetrics], RetryExhausted]:
        """
        Execute operation with retry policy (Constitutional Law #5).

        Args:
            operation: Async function to execute
            should_retry: Optional predicate for selective retry

        Returns:
            Result containing (value, metrics) or RetryExhausted error
        """
        # Query VectorStore for retry patterns (Article IV)
        if self.agent_context:
            try:
                learnings = self.agent_context.search_memories(
                    tags=["retry", "pattern", "success"],
                    include_session=False,
                )
            except Exception:
                learnings = []

        errors: list[str] = []
        total_delay = 0.0
        start_time = time.time()

        for attempt in range(1, self.policy.max_attempts + 1):
            # Check global timeout
            if self.timeout_s and (time.time() - start_time) > self.timeout_s:
                return Err(
                    RetryExhausted(
                        attempts=attempt - 1,
                        errors=errors + ["Global timeout exceeded"],
                    )
                )

            try:
                # Execute operation
                result = await operation()

                # Success - store pattern (Article IV)
                metrics = RetryMetrics(
                    total_attempts=attempt,
                    total_delay_s=total_delay,
                    success=True,
                    errors=errors,
                )

                if self.agent_context:
                    try:
                        self.agent_context.store_memory(
                            key=f"retry_success_{int(time.time())}",
                            content={
                                "attempts": attempt,
                                "total_delay": total_delay,
                                "success": True,
                            },
                            tags=["retry", "success", "ci_monitor"],
                        )
                    except Exception:
                        pass

                return Ok((result, metrics))

            except Exception as exc:
                # Check if error is retryable
                if not self._should_retry_error(exc):
                    raise

                # Check custom retry predicate
                if should_retry and not should_retry(exc):
                    return Err(RetryExhausted(attempts=attempt, errors=errors + [str(exc)]))

                # Record error
                errors.append(str(exc))

                # Max attempts reached
                if attempt >= self.policy.max_attempts:
                    return Err(RetryExhausted(attempts=attempt, errors=errors))

                # Calculate and apply backoff delay
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
                total_delay += delay

        # Should never reach here (max attempts checked above)
        return Err(RetryExhausted(attempts=self.policy.max_attempts, errors=errors))


# ============================================================================
# CONVENIENCE FUNCTION (Article V: Spec-Driven API)
# ============================================================================


def retry_with_backoff(
    operation: Callable[[], T],
    max_attempts: int = 5,
) -> Result[T, RetryExhausted]:
    """
    Simplified retry with exponential backoff (30s, 60s, 120s).

    This is a synchronous wrapper for common use cases.
    For full async support, use RetryController directly.

    Args:
        operation: Function to execute
        max_attempts: Maximum retry attempts (default: 5)

    Returns:
        Result containing value or RetryExhausted error

    Example:
        >>> def flaky_task():
        ...     return "success"
        >>> result = retry_with_backoff(flaky_task, max_attempts=3)
        >>> if result.is_ok():
        ...     print(result.unwrap())
    """
    policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay_s=30.0,
        max_delay_s=120.0,
        exponential=True,
    )
    controller = RetryController(policy=policy)

    # Run async operation in sync context
    async def async_wrapper():
        async def operation_wrapper():
            return operation()

        return await controller.retry_with_policy(operation_wrapper)

    try:
        import asyncio

        result = asyncio.run(async_wrapper())
        if result.is_ok():
            value, _metrics = result.unwrap()
            return Ok(value)
        return result
    except Exception as e:
        return Err(RetryExhausted(attempts=1, errors=[str(e)]))
