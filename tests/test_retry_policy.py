"""
Tests for retry policy with exponential backoff and idempotency.

Test coverage:
- RetryPolicy.compute_delay() with exponential backoff
- IdempotencyKey generation and parsing
- retry_with_policy() async wrapper
- retry_with_policy_sync() synchronous wrapper
- RetryExhausted exception handling
- Constitutional compliance (Articles I, II, IV)
"""

import asyncio
import time

import pytest

from tools.orchestrator.retry_policy import (
    IdempotencyKey,
    RetryExhausted,
    RetryMetrics,
    RetryPolicy,
    retry_with_policy,
    retry_with_policy_sync,
)


class TestRetryPolicy:
    """Test RetryPolicy Pydantic model and compute_delay()."""

    def test_default_policy_values(self) -> None:
        """Test default retry policy configuration."""
        policy = RetryPolicy()

        assert policy.max_attempts == 3
        assert policy.base_delay_s == 1.0
        assert policy.max_delay_s == 60.0
        assert policy.jitter == 0.1

    def test_custom_policy_values(self) -> None:
        """Test custom retry policy configuration."""
        policy = RetryPolicy(
            max_attempts=5,
            base_delay_s=2.0,
            max_delay_s=120.0,
            jitter=0.2,
        )

        assert policy.max_attempts == 5
        assert policy.base_delay_s == 2.0
        assert policy.max_delay_s == 120.0
        assert policy.jitter == 0.2

    def test_exponential_backoff_no_jitter(self) -> None:
        """Test exponential backoff calculation without jitter."""
        policy = RetryPolicy(base_delay_s=1.0, max_delay_s=60.0, jitter=0.0)

        # Attempt 1: 1.0 * 2^0 = 1.0
        assert policy.compute_delay(1) == 1.0

        # Attempt 2: 1.0 * 2^1 = 2.0
        assert policy.compute_delay(2) == 2.0

        # Attempt 3: 1.0 * 2^2 = 4.0
        assert policy.compute_delay(3) == 4.0

        # Attempt 4: 1.0 * 2^3 = 8.0
        assert policy.compute_delay(4) == 8.0

    def test_exponential_backoff_with_max_delay_cap(self) -> None:
        """Test exponential backoff capped at max_delay_s."""
        policy = RetryPolicy(base_delay_s=1.0, max_delay_s=10.0, jitter=0.0)

        # Attempt 10: 1.0 * 2^9 = 512.0, capped at 10.0
        assert policy.compute_delay(10) == 10.0

        # Attempt 20: 1.0 * 2^19 = 524288.0, capped at 10.0
        assert policy.compute_delay(20) == 10.0

    def test_exponential_backoff_with_jitter(self) -> None:
        """Test exponential backoff with jitter randomization."""
        policy = RetryPolicy(base_delay_s=1.0, max_delay_s=60.0, jitter=0.1)

        # Attempt 1: 1.0 * 2^0 = 1.0, jitter adds 0-10% (1.0 to 1.1)
        delay_1 = policy.compute_delay(1)
        assert 1.0 <= delay_1 <= 1.1

        # Attempt 2: 1.0 * 2^1 = 2.0, jitter adds 0-10% (2.0 to 2.2)
        delay_2 = policy.compute_delay(2)
        assert 2.0 <= delay_2 <= 2.2

        # Jitter should produce different values across multiple calls
        delays = [policy.compute_delay(3) for _ in range(10)]
        assert len(set(delays)) > 1, "Jitter should produce varying delays"

    def test_zero_base_delay(self) -> None:
        """Test retry with zero base delay (immediate retry)."""
        policy = RetryPolicy(base_delay_s=0.0, jitter=0.0)

        assert policy.compute_delay(1) == 0.0
        assert policy.compute_delay(5) == 0.0

    def test_pydantic_validation_positive_max_attempts(self) -> None:
        """Test Pydantic validation: max_attempts must be >= 1."""
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            RetryPolicy(max_attempts=0)

    def test_pydantic_validation_jitter_range(self) -> None:
        """Test Pydantic validation: jitter must be in [0.0, 1.0]."""
        with pytest.raises(ValueError, match="less than or equal to 1"):
            RetryPolicy(jitter=1.5)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            RetryPolicy(jitter=-0.1)


class TestIdempotencyKey:
    """Test IdempotencyKey generation and parsing."""

    def test_generate_idempotency_key(self) -> None:
        """Test idempotency key generation with current timestamp."""
        key = IdempotencyKey.generate("task_42", 1)

        assert key.task_id == "task_42"
        assert key.attempt == 1
        assert key.timestamp_ms > 0
        assert isinstance(key.timestamp_ms, int)

    def test_to_string_format(self) -> None:
        """Test idempotency key string format: {task_id}:{attempt}:{timestamp_ms}."""
        key = IdempotencyKey(task_id="task_123", attempt=2, timestamp_ms=1728567825000)
        key_str = key.to_string()

        assert key_str == "task_123:2:1728567825000"

    def test_from_string_valid(self) -> None:
        """Test parsing valid idempotency key string."""
        key_str = "task_456:3:1728567830000"
        key = IdempotencyKey.from_string(key_str)

        assert key.task_id == "task_456"
        assert key.attempt == 3
        assert key.timestamp_ms == 1728567830000

    def test_from_string_invalid_format(self) -> None:
        """Test parsing invalid idempotency key string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid idempotency key format"):
            IdempotencyKey.from_string("invalid_key")

        with pytest.raises(ValueError, match="Invalid idempotency key format"):
            IdempotencyKey.from_string("task:1")  # Missing timestamp

        with pytest.raises(ValueError, match="Invalid idempotency key format"):
            IdempotencyKey.from_string("task:abc:123")  # Non-integer attempt

    def test_idempotency_key_uniqueness(self) -> None:
        """Test that generated keys are unique across attempts and time."""
        key1 = IdempotencyKey.generate("task_1", 1)
        time.sleep(0.001)  # Ensure different timestamp
        key2 = IdempotencyKey.generate("task_1", 1)

        assert key1.to_string() != key2.to_string()

        # Same task, different attempts
        key3 = IdempotencyKey.generate("task_1", 2)
        assert key1.to_string() != key3.to_string()


class TestRetryExhausted:
    """Test RetryExhausted exception."""

    def test_retry_exhausted_message(self) -> None:
        """Test RetryExhausted exception message includes task_id and attempts."""
        errors = ["Network timeout", "Connection refused", "Service unavailable"]
        exc = RetryExhausted("task_99", 3, errors)

        assert exc.task_id == "task_99"
        assert exc.attempts == 3
        assert exc.errors == errors
        assert "task_99" in str(exc)
        assert "3 attempts" in str(exc)


class TestRetryWithPolicyAsync:
    """Test retry_with_policy() async wrapper."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self) -> None:
        """Test operation succeeds on first attempt (no retries)."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_policy("task_1", operation, policy)

        assert result.is_ok()
        output, metrics = result.unwrap()
        assert output == "success"
        assert metrics.total_attempts == 1
        assert metrics.total_delay_s == 0.0
        assert metrics.success is True
        assert len(metrics.idempotency_keys) == 1
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retries(self) -> None:
        """Test operation succeeds after 2 failures (transient errors)."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient network error")
            return "success"

        result = await retry_with_policy("task_2", operation, policy)

        assert result.is_ok()
        output, metrics = result.unwrap()
        assert output == "success"
        assert metrics.total_attempts == 3
        # Delay after attempt 1: 0.1, delay after attempt 2: 0.2
        assert metrics.total_delay_s == pytest.approx(0.3, abs=0.01)
        assert metrics.success is True
        assert len(metrics.idempotency_keys) == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_failure_after_max_attempts(self) -> None:
        """Test operation fails after exhausting all retry attempts."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.05, jitter=0.0)
        call_count = 0

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Permanent error {call_count}")

        result = await retry_with_policy("task_3", operation, policy)

        assert result.is_err()
        exc = result.unwrap_err()
        assert isinstance(exc, RetryExhausted)
        assert exc.task_id == "task_3"
        assert exc.attempts == 3
        assert len(exc.errors) == 3
        assert "Permanent error 1" in exc.errors[0]
        assert "Permanent error 2" in exc.errors[1]
        assert "Permanent error 3" in exc.errors[2]
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_should_retry_predicate(self) -> None:
        """Test should_retry predicate controls which errors are retryable."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.05, jitter=0.0)
        call_count = 0

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            raise PermissionError("Not retryable")

        # Only retry ConnectionError, not PermissionError
        def should_retry(exc: Exception) -> bool:
            return isinstance(exc, ConnectionError)

        result = await retry_with_policy("task_4", operation, policy, should_retry)

        # Should fail immediately without retries
        assert result.is_err()
        exc = result.unwrap_err()
        assert exc.attempts == 1  # Only 1 attempt (no retries)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self) -> None:
        """Test exponential backoff delays are applied correctly."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0
        start_time = time.time()

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Retry me")
            return "success"

        result = await retry_with_policy("task_5", operation, policy)

        elapsed = time.time() - start_time

        assert result.is_ok()
        # Delay after attempt 1: 0.1s, delay after attempt 2: 0.2s
        # Total: ~0.3s (allow for timing variance)
        assert elapsed >= 0.3
        assert elapsed < 0.5  # Shouldn't take much longer

    @pytest.mark.asyncio
    async def test_idempotency_keys_tracked(self) -> None:
        """Test idempotency keys are generated and tracked for each attempt."""
        policy = RetryPolicy(max_attempts=2, base_delay_s=0.05, jitter=0.0)

        async def operation() -> str:
            return "success"

        result = await retry_with_policy("task_6", operation, policy)

        assert result.is_ok()
        _, metrics = result.unwrap()
        assert len(metrics.idempotency_keys) == 1
        # Verify format: task_6:1:{timestamp}
        assert metrics.idempotency_keys[0].startswith("task_6:1:")


class TestRetryWithPolicySync:
    """Test retry_with_policy_sync() synchronous wrapper."""

    def test_sync_success_on_first_attempt(self) -> None:
        """Test synchronous operation succeeds on first attempt."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0

        def operation() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        result = retry_with_policy_sync("sync_task_1", operation, policy)

        assert result.is_ok()
        output, metrics = result.unwrap()
        assert output == 42
        assert metrics.total_attempts == 1
        assert call_count == 1

    def test_sync_success_after_retries(self) -> None:
        """Test synchronous operation succeeds after failures."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.05, jitter=0.0)
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OSError("Transient I/O error")
            return "success"

        result = retry_with_policy_sync("sync_task_2", operation, policy)

        assert result.is_ok()
        output, metrics = result.unwrap()
        assert output == "success"
        assert metrics.total_attempts == 3
        assert call_count == 3

    def test_sync_failure_after_max_attempts(self) -> None:
        """Test synchronous operation fails after max attempts."""
        policy = RetryPolicy(max_attempts=2, base_delay_s=0.05, jitter=0.0)
        call_count = 0

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Always fails")

        result = retry_with_policy_sync("sync_task_3", operation, policy)

        assert result.is_err()
        exc = result.unwrap_err()
        assert exc.attempts == 2
        assert len(exc.errors) == 2
        assert call_count == 2

    def test_sync_exponential_backoff_timing(self) -> None:
        """Test synchronous exponential backoff delays."""
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0
        start_time = time.time()

        def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Retry")
            return "done"

        result = retry_with_policy_sync("sync_task_4", operation, policy)

        elapsed = time.time() - start_time

        assert result.is_ok()
        # Delay: 0.1s + 0.2s = 0.3s total
        assert elapsed >= 0.3
        assert elapsed < 0.5


class TestConstitutionalCompliance:
    """Test constitutional compliance (Articles I, II, IV)."""

    @pytest.mark.asyncio
    async def test_article_i_retry_on_failure(self) -> None:
        """
        Test Article I: Complete Context Before Action.

        Retry on timeout/failure with exponential backoff (2x, 3x).
        """
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)
        call_count = 0

        async def operation() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Article I: retry on timeout")
            return "success"

        result = await retry_with_policy("article_i_task", operation, policy)

        assert result.is_ok()
        _, metrics = result.unwrap()
        # Article I: exponential backoff applied (0.1s, 0.2s)
        assert metrics.total_delay_s == pytest.approx(0.3, abs=0.01)

    def test_article_ii_result_pattern(self) -> None:
        """
        Test Article II: 100% Verification and Stability.

        Use Result pattern (no bare exceptions for control flow).
        """
        policy = RetryPolicy(max_attempts=1, base_delay_s=0.1)

        def operation() -> str:
            raise ValueError("Test error")

        result = retry_with_policy_sync("article_ii_task", operation, policy)

        # Result pattern: no exception raised, error wrapped in Err
        assert result.is_err()
        exc = result.unwrap_err()
        assert isinstance(exc, RetryExhausted)

    @pytest.mark.asyncio
    async def test_article_iv_metrics_for_learning(self) -> None:
        """
        Test Article IV: Continuous Learning and Improvement.

        Collect metrics (attempts, delays, success) for VectorStore storage.
        """
        policy = RetryPolicy(max_attempts=3, base_delay_s=0.1, jitter=0.0)

        async def operation() -> str:
            return "success"

        result = await retry_with_policy("article_iv_task", operation, policy)

        assert result.is_ok()
        _, metrics = result.unwrap()

        # Metrics for learning (Article IV compliance)
        assert metrics.task_id == "article_iv_task"
        assert metrics.total_attempts == 1
        assert metrics.success is True
        assert len(metrics.idempotency_keys) == 1
        # These metrics can be stored in VectorStore for pattern recognition
