"""
Retry policy implementation with exponential backoff and idempotency.

This module provides resilient task execution with:
- Exponential backoff with jitter
- Idempotency key tracking
- Result pattern error propagation
- Constitutional compliance (Articles I, II, IV)

Part of Leap 6: Bulletproof Orchestrator - Production Hardening.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from shared.type_definitions.result import Err, Ok, Result

T = TypeVar("T")
E = TypeVar("E")


class RetryPolicy(BaseModel):
    """
    Retry policy with exponential backoff and jitter.

    Implements spec-007-resilient-scheduler.md requirements:
    - Configurable max_attempts (default: 3)
    - Exponential backoff: delay = base_delay_s * (2 ** (attempt - 1))
    - Max delay cap to prevent excessive waits
    - Jitter to prevent thundering herd
    """

    model_config = ConfigDict(extra="forbid")

    max_attempts: int = Field(3, ge=1, description="Maximum retry attempts")
    base_delay_s: float = Field(1.0, ge=0.0, description="Base delay in seconds")
    max_delay_s: float = Field(60.0, ge=0.0, description="Maximum delay cap in seconds")
    jitter: float = Field(0.1, ge=0.0, le=1.0, description="Jitter factor (0.0-1.0)")

    def compute_delay(self, attempt: int) -> float:
        """
        Compute retry delay with exponential backoff and jitter.

        Algorithm:
        - Exponential: delay = base_delay_s * (2 ** (attempt - 1))
        - Cap at max_delay_s
        - Add jitter: delay += delay * jitter * random()

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds before next retry

        Examples:
            >>> policy = RetryPolicy(base_delay_s=1.0, max_delay_s=60.0, jitter=0.0)
            >>> policy.compute_delay(1)  # First retry
            1.0
            >>> policy.compute_delay(2)  # Second retry
            2.0
            >>> policy.compute_delay(3)  # Third retry
            4.0
            >>> policy.compute_delay(10)  # Capped at max_delay_s
            60.0
        """
        # Exponential backoff: 2^(attempt-1) * base_delay_s
        delay = self.base_delay_s * (2 ** (attempt - 1))

        # Apply max delay cap (Constitutional Law: prevent infinite waits)
        delay = min(delay, self.max_delay_s)

        # Add jitter to prevent thundering herd
        if self.jitter > 0:
            jitter_amount = delay * self.jitter * random.random()
            delay += jitter_amount

        return delay


class IdempotencyKey(BaseModel):
    """
    Idempotency key for tracking unique task executions.

    Format: {task_id}:{attempt}:{timestamp_ms}

    Ensures same task + same inputs → same result (no duplicate side effects).
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Unique task identifier")
    attempt: int = Field(..., ge=1, description="Attempt number (1-indexed)")
    timestamp_ms: int = Field(..., ge=0, description="Timestamp in milliseconds")

    @classmethod
    def generate(cls, task_id: str, attempt: int) -> IdempotencyKey:
        """
        Generate idempotency key with current timestamp.

        Args:
            task_id: Unique task identifier
            attempt: Attempt number (1-indexed)

        Returns:
            IdempotencyKey instance

        Examples:
            >>> key = IdempotencyKey.generate("task_42", 1)
            >>> key.to_string()
            "task_42:1:1728567825123"
        """
        timestamp_ms = int(time.time() * 1000)
        return cls(task_id=task_id, attempt=attempt, timestamp_ms=timestamp_ms)

    def to_string(self) -> str:
        """
        Convert to string representation.

        Returns:
            Formatted string: {task_id}:{attempt}:{timestamp_ms}
        """
        return f"{self.task_id}:{self.attempt}:{self.timestamp_ms}"

    @classmethod
    def from_string(cls, key_str: str) -> IdempotencyKey:
        """
        Parse idempotency key from string.

        Args:
            key_str: String in format {task_id}:{attempt}:{timestamp_ms}

        Returns:
            IdempotencyKey instance

        Raises:
            ValueError: If string format is invalid
        """
        parts = key_str.split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid idempotency key format: {key_str}")

        task_id = parts[0]
        try:
            attempt = int(parts[1])
            timestamp_ms = int(parts[2])
        except ValueError as e:
            raise ValueError(f"Invalid idempotency key format: {key_str}") from e

        return cls(task_id=task_id, attempt=attempt, timestamp_ms=timestamp_ms)


class RetryExhausted(Exception):
    """
    Exception raised when retry attempts are exhausted.

    Includes attempt count and error history for debugging.
    """

    def __init__(self, task_id: str, attempts: int, errors: list[str]) -> None:
        """
        Create RetryExhausted exception.

        Args:
            task_id: Task identifier
            attempts: Number of attempts made
            errors: List of error messages from each attempt
        """
        self.task_id = task_id
        self.attempts = attempts
        self.errors = errors
        msg = f"Task {task_id} failed after {attempts} attempts. Errors: {', '.join(errors)}"
        super().__init__(msg)


class RetryMetrics(BaseModel):
    """Metrics collected during retry execution."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Task identifier")
    total_attempts: int = Field(..., ge=1, description="Total attempts made")
    total_delay_s: float = Field(..., ge=0.0, description="Total retry delay in seconds")
    success: bool = Field(..., description="Whether task ultimately succeeded")
    idempotency_keys: list[str] = Field(
        default_factory=list, description="All idempotency keys used"
    )


async def retry_with_policy(
    task_id: str,
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    should_retry: Callable[[Exception], bool] | None = None,
) -> Result[tuple[T, RetryMetrics], RetryExhausted]:
    """
    Execute operation with retry policy and exponential backoff.

    Uses Result pattern for error propagation (Constitutional Law #5).
    Tracks idempotency keys for each attempt.

    Args:
        task_id: Unique task identifier
        operation: Async operation to execute (must be idempotent)
        policy: Retry policy configuration
        should_retry: Optional predicate to determine if error is retryable
                     (default: retry all exceptions)

    Returns:
        Result containing (output, metrics) on success, or RetryExhausted on failure

    Examples:
        >>> policy = RetryPolicy(max_attempts=3, base_delay_s=1.0)
        >>> async def fetch_data():
        ...     # May fail with network errors
        ...     return await http.get("/api/data")
        >>> result = await retry_with_policy("fetch_1", fetch_data, policy)
        >>> if result.is_ok():
        ...     data, metrics = result.unwrap()
        ...     print(f"Success after {metrics.total_attempts} attempts")

    Constitutional Compliance:
    - Article I: Retries on failure (exponential backoff up to max_attempts)
    - Article II: Result pattern (no bare exceptions for control flow)
    - Article IV: Metrics stored for learning (attempt count, delay, success)
    """
    if should_retry is None:
        # Default: retry all exceptions
        def should_retry(_: Exception) -> bool:
            return True

    attempts = 0
    total_delay_s = 0.0
    errors: list[str] = []
    idempotency_keys: list[str] = []

    while attempts < policy.max_attempts:
        attempts += 1

        # Generate idempotency key for this attempt
        idem_key = IdempotencyKey.generate(task_id, attempts)
        idempotency_keys.append(idem_key.to_string())

        try:
            # Execute operation
            result = await operation()

            # Success! Return with metrics
            metrics = RetryMetrics(
                task_id=task_id,
                total_attempts=attempts,
                total_delay_s=total_delay_s,
                success=True,
                idempotency_keys=idempotency_keys,
            )
            return Ok((result, metrics))

        except Exception as e:
            error_msg = str(e)
            errors.append(error_msg)

            # Check if we should retry this error
            if not should_retry(e):
                # Non-retryable error, fail immediately
                exhausted = RetryExhausted(task_id, attempts, errors)
                return Err(exhausted)

            # Check if we have attempts remaining
            if attempts >= policy.max_attempts:
                # No more retries, fail with RetryExhausted
                exhausted = RetryExhausted(task_id, attempts, errors)
                return Err(exhausted)

            # Compute backoff delay for next retry
            delay = policy.compute_delay(attempts)
            total_delay_s += delay

            # Wait before next retry (Article I: exponential backoff)
            await asyncio.sleep(delay)

    # Should never reach here, but handle defensively
    exhausted = RetryExhausted(task_id, attempts, errors)
    return Err(exhausted)


# Synchronous version for non-async operations
def retry_with_policy_sync(
    task_id: str,
    operation: Callable[[], T],
    policy: RetryPolicy,
    should_retry: Callable[[Exception], bool] | None = None,
) -> Result[tuple[T, RetryMetrics], RetryExhausted]:
    """
    Synchronous version of retry_with_policy.

    Args:
        task_id: Unique task identifier
        operation: Synchronous operation to execute (must be idempotent)
        policy: Retry policy configuration
        should_retry: Optional predicate to determine if error is retryable

    Returns:
        Result containing (output, metrics) on success, or RetryExhausted on failure

    Examples:
        >>> policy = RetryPolicy(max_attempts=3, base_delay_s=0.5)
        >>> def fetch_config():
        ...     # May fail with IOError
        ...     return read_file("/config.json")
        >>> result = retry_with_policy_sync("config_1", fetch_config, policy)
    """
    if should_retry is None:

        def should_retry(_: Exception) -> bool:
            return True

    attempts = 0
    total_delay_s = 0.0
    errors: list[str] = []
    idempotency_keys: list[str] = []

    while attempts < policy.max_attempts:
        attempts += 1

        # Generate idempotency key
        idem_key = IdempotencyKey.generate(task_id, attempts)
        idempotency_keys.append(idem_key.to_string())

        try:
            # Execute operation
            result = operation()

            # Success!
            metrics = RetryMetrics(
                task_id=task_id,
                total_attempts=attempts,
                total_delay_s=total_delay_s,
                success=True,
                idempotency_keys=idempotency_keys,
            )
            return Ok((result, metrics))

        except Exception as e:
            error_msg = str(e)
            errors.append(error_msg)

            if not should_retry(e):
                exhausted = RetryExhausted(task_id, attempts, errors)
                return Err(exhausted)

            if attempts >= policy.max_attempts:
                exhausted = RetryExhausted(task_id, attempts, errors)
                return Err(exhausted)

            # Synchronous sleep
            delay = policy.compute_delay(attempts)
            total_delay_s += delay
            time.sleep(delay)

    exhausted = RetryExhausted(task_id, attempts, errors)
    return Err(exhausted)


__all__ = [
    "RetryPolicy",
    "IdempotencyKey",
    "RetryExhausted",
    "RetryMetrics",
    "retry_with_policy",
    "retry_with_policy_sync",
]
