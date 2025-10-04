"""
Tests for Retry Controller (ESSENTIAL Tool - 0% coverage)

Constitutional Compliance:
- Article I: Complete context (all retry scenarios tested)
- Article II: 100% coverage of ESSENTIAL retry operations
- TDD: Tests validate production behavior

Covers:
- ExponentialBackoffStrategy (delay calculation, retry logic)
- LinearBackoffStrategy (delay calculation, retry logic)
- CircuitBreaker (state transitions, failure tracking)
- RetryController (execute_with_retry, async, timeout, statistics)
- Memory integration
- Thread safety
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

from shared.retry_controller import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    RetryController,
)

# ========== NECESSARY Pattern: Normal Operation Tests ==========


class TestExponentialBackoffStrategy:
    """Tests for ExponentialBackoffStrategy - happy path and edge cases"""

    def test_exponential_backoff_initial_delay(self):
        """N: Normal - first attempt uses initial delay"""
        strategy = ExponentialBackoffStrategy(initial_delay=1.0, multiplier=2.0, jitter=False)
        delay = strategy.calculate_delay(0)
        assert delay == 1.0

    def test_exponential_backoff_progression(self):
        """N: Normal - delay doubles with each attempt"""
        strategy = ExponentialBackoffStrategy(
            initial_delay=1.0, multiplier=2.0, max_delay=100.0, jitter=False
        )

        assert strategy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert strategy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert strategy.calculate_delay(2) == 4.0  # 1 * 2^2
        assert strategy.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_exponential_backoff_max_delay_cap(self):
        """E: Edge - delay capped at max_delay"""
        strategy = ExponentialBackoffStrategy(
            initial_delay=1.0, multiplier=2.0, max_delay=5.0, jitter=False
        )

        # After a few attempts, should hit max_delay
        delay = strategy.calculate_delay(10)
        assert delay == 5.0

    def test_exponential_backoff_with_jitter(self):
        """C: Comprehensive - jitter adds randomness"""
        strategy = ExponentialBackoffStrategy(
            initial_delay=10.0, multiplier=2.0, max_delay=100.0, jitter=True
        )

        delays = [strategy.calculate_delay(1) for _ in range(10)]

        # All delays should be different (jitter adds randomness)
        assert len(set(delays)) > 1

        # All delays should be in reasonable range (75% to 125% of base)
        base_delay = 20.0  # 10 * 2^1
        for delay in delays:
            assert 15.0 <= delay <= 25.0

    def test_exponential_backoff_zero_initial_delay(self):
        """E: Edge - zero initial delay returns zero"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.0, multiplier=2.0, max_delay=100.0)

        delay = strategy.calculate_delay(5)
        assert delay == 0.0

    def test_exponential_backoff_should_retry_success(self):
        """N: Normal - should retry for normal exceptions"""
        strategy = ExponentialBackoffStrategy(max_attempts=3)

        # First 3 attempts should retry
        assert strategy.should_retry(0, Exception("test")) is True
        assert strategy.should_retry(1, Exception("test")) is True
        assert strategy.should_retry(2, Exception("test")) is True

    def test_exponential_backoff_should_retry_exhausted(self):
        """E: Error - stops retrying after max_attempts"""
        strategy = ExponentialBackoffStrategy(max_attempts=3)

        # Attempt 3 (4th attempt) should not retry
        assert strategy.should_retry(3, Exception("test")) is False

    def test_exponential_backoff_never_retry_keyboard_interrupt(self):
        """S: Security - never retry KeyboardInterrupt"""
        strategy = ExponentialBackoffStrategy(max_attempts=10)

        assert strategy.should_retry(0, KeyboardInterrupt()) is False
        assert strategy.should_retry(0, SystemExit()) is False

    def test_exponential_backoff_custom_callback(self):
        """C: Comprehensive - custom retry callback honored"""

        def custom_callback(attempt, exception):
            # Only retry ValueError
            return isinstance(exception, ValueError)

        strategy = ExponentialBackoffStrategy(max_attempts=5, should_retry_callback=custom_callback)

        # Should retry ValueError
        assert strategy.should_retry(0, ValueError("test")) is True

        # Should not retry TypeError
        assert strategy.should_retry(0, TypeError("test")) is False

    def test_exponential_backoff_invalid_params_negative_initial_delay(self):
        """E: Error - negative initial_delay raises ValueError"""
        with pytest.raises(ValueError, match="initial_delay must be non-negative"):
            ExponentialBackoffStrategy(initial_delay=-1.0)

    def test_exponential_backoff_invalid_params_zero_max_delay(self):
        """E: Error - non-positive max_delay raises ValueError"""
        with pytest.raises(ValueError, match="max_delay must be positive"):
            ExponentialBackoffStrategy(max_delay=0)

    def test_exponential_backoff_invalid_params_low_multiplier(self):
        """E: Error - multiplier < 1 raises ValueError"""
        with pytest.raises(ValueError, match="multiplier must be >= 1"):
            ExponentialBackoffStrategy(multiplier=0.5)


class TestLinearBackoffStrategy:
    """Tests for LinearBackoffStrategy"""

    def test_linear_backoff_initial_delay(self):
        """N: Normal - first attempt uses initial delay"""
        strategy = LinearBackoffStrategy(initial_delay=2.0, increment=1.0)
        delay = strategy.calculate_delay(0)
        assert delay == 2.0

    def test_linear_backoff_progression(self):
        """N: Normal - delay increases linearly"""
        strategy = LinearBackoffStrategy(initial_delay=2.0, increment=3.0, max_delay=100.0)

        assert strategy.calculate_delay(0) == 2.0  # 2 + 3*0
        assert strategy.calculate_delay(1) == 5.0  # 2 + 3*1
        assert strategy.calculate_delay(2) == 8.0  # 2 + 3*2
        assert strategy.calculate_delay(3) == 11.0  # 2 + 3*3

    def test_linear_backoff_max_delay_cap(self):
        """E: Edge - delay capped at max_delay"""
        strategy = LinearBackoffStrategy(initial_delay=1.0, increment=5.0, max_delay=10.0)

        # After a few attempts, should hit max_delay
        delay = strategy.calculate_delay(10)
        assert delay == 10.0

    def test_linear_backoff_should_retry_success(self):
        """N: Normal - should retry for normal exceptions"""
        strategy = LinearBackoffStrategy(max_attempts=3)

        assert strategy.should_retry(0, Exception("test")) is True
        assert strategy.should_retry(1, Exception("test")) is True
        assert strategy.should_retry(2, Exception("test")) is True

    def test_linear_backoff_should_retry_exhausted(self):
        """E: Error - stops retrying after max_attempts"""
        strategy = LinearBackoffStrategy(max_attempts=3)

        assert strategy.should_retry(3, Exception("test")) is False

    def test_linear_backoff_never_retry_system_exit(self):
        """S: Security - never retry system exceptions"""
        strategy = LinearBackoffStrategy(max_attempts=10)

        assert strategy.should_retry(0, KeyboardInterrupt()) is False
        assert strategy.should_retry(0, SystemExit()) is False


class TestCircuitBreaker:
    """Tests for CircuitBreaker state management"""

    def test_circuit_breaker_initially_closed(self):
        """N: Normal - circuit starts in closed state"""
        breaker = CircuitBreaker()
        assert breaker.state == "closed"
        assert breaker.allow_request() is True

    def test_circuit_breaker_opens_after_failures(self):
        """N: Normal - circuit opens after threshold failures"""
        breaker = CircuitBreaker(failure_threshold=3)

        # Record failures
        breaker.record_failure()
        assert breaker.state == "closed"  # Still closed

        breaker.record_failure()
        assert breaker.state == "closed"  # Still closed

        breaker.record_failure()
        assert breaker.state == "open"  # Now open

    def test_circuit_breaker_blocks_when_open(self):
        """E: Error - open circuit blocks requests"""
        breaker = CircuitBreaker(failure_threshold=2)

        breaker.record_failure()
        breaker.record_failure()

        assert breaker.state == "open"
        assert breaker.allow_request() is False

    def test_circuit_breaker_transitions_to_half_open(self):
        """C: Comprehensive - circuit moves to half-open after timeout"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        # Manually set opened_at to a time in the past to simulate timeout passing

        breaker.opened_at = time.time() - 0.1  # 100ms ago

        # Should transition to half-open on next request (timeout has passed)
        result = breaker.allow_request()
        assert result is True
        assert breaker.state == "half_open"

    def test_circuit_breaker_closes_on_success(self):
        """N: Normal - circuit closes on successful request"""
        breaker = CircuitBreaker(failure_threshold=2)

        # Open the circuit
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"

        # Record success
        breaker.record_success()
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

    def test_circuit_breaker_resets_failure_count(self):
        """S: State - success resets failure count"""
        breaker = CircuitBreaker(failure_threshold=3)

        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        breaker.record_success()
        assert breaker.failure_count == 0
        assert breaker.state == "closed"


class TestRetryController:
    """Tests for RetryController execution logic"""

    def test_retry_controller_success_first_attempt(self):
        """N: Normal - function succeeds on first attempt"""
        strategy = ExponentialBackoffStrategy(max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        def success_func():
            return "success"

        result = controller.execute_with_retry(success_func)
        assert result == "success"

        # Check statistics
        stats = controller.get_statistics()
        assert stats["total_executions"] == 1
        assert stats["total_retries"] == 0
        assert stats["successful_recoveries"] == 0

    def test_retry_controller_success_after_retries(self):
        """N: Normal - function succeeds after retries"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        attempt_count = [0]

        def flaky_func():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ValueError("temporary error")
            return "success"

        result = controller.execute_with_retry(flaky_func)
        assert result == "success"
        assert attempt_count[0] == 3

        # Check statistics
        stats = controller.get_statistics()
        assert stats["total_retries"] == 2
        assert stats["successful_recoveries"] == 1

    def test_retry_controller_failure_exhausted(self):
        """E: Error - raises exception after max retries"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        def always_fail():
            raise RuntimeError("persistent error")

        with pytest.raises(RuntimeError, match="persistent error"):
            controller.execute_with_retry(always_fail)

        # Check statistics
        stats = controller.get_statistics()
        assert stats["failed_exhaustions"] == 1

    def test_retry_controller_with_timeout(self):
        """C: Comprehensive - timeout raises TimeoutError when overall timeout exceeded"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.5, max_attempts=10, jitter=False)
        controller = RetryController(strategy, timeout=0.05)

        attempt_count = [0]

        def func_with_retries():
            attempt_count[0] += 1
            # Always fail to force retries
            raise ValueError("keep retrying")

        # The timeout should kick in before max_attempts due to delays
        with pytest.raises(TimeoutError, match="timed out"):
            controller.execute_with_retry(func_with_retries)

    def test_retry_controller_circuit_breaker_integration(self):
        """C: Comprehensive - circuit breaker blocks after failures"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10.0)
        controller = RetryController(strategy, circuit_breaker=breaker)

        def always_fail():
            raise RuntimeError("error")

        # First call - should exhaust retries and open circuit
        with pytest.raises(RuntimeError):
            controller.execute_with_retry(always_fail)

        # Circuit should now be open
        assert breaker.state == "open"

        # Second call - should be blocked by circuit breaker
        with pytest.raises(CircuitBreakerOpenError, match="Circuit breaker open"):
            controller.execute_with_retry(always_fail)

    def test_retry_controller_circuit_breaker_resets_on_success(self):
        """S: State - circuit breaker resets on successful call"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        breaker = CircuitBreaker(failure_threshold=3)
        controller = RetryController(strategy, circuit_breaker=breaker)

        # Simulate some failures
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failure_count == 2

        # Successful call should reset
        def success_func():
            return "ok"

        result = controller.execute_with_retry(success_func)
        assert result == "ok"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_retry_controller_async_success(self):
        """N: Normal - async retry works"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        async def async_success():
            return "async success"

        result = await controller.execute_with_retry_async(async_success)
        assert result == "async success"

    @pytest.mark.asyncio
    async def test_retry_controller_async_retry_after_failures(self):
        """N: Normal - async retry recovers after failures"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        attempt_count = [0]

        async def flaky_async():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ValueError("temporary async error")
            return "async success"

        result = await controller.execute_with_retry_async(flaky_async)
        assert result == "async success"
        assert attempt_count[0] == 3

    @pytest.mark.asyncio
    async def test_retry_controller_async_exhausted(self):
        """E: Error - async raises after exhausted retries"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=2, jitter=False)
        controller = RetryController(strategy)

        async def always_fail_async():
            raise RuntimeError("persistent async error")

        with pytest.raises(RuntimeError, match="persistent async error"):
            await controller.execute_with_retry_async(always_fail_async)

    def test_retry_controller_memory_integration(self):
        """S: State - memory events recorded when context available"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)

        # Mock agent context with memory
        mock_context = MagicMock()
        controller = RetryController(strategy, agent_context=mock_context)

        def success_func():
            return "ok"

        result = controller.execute_with_retry(success_func)
        assert result == "ok"

        # Should have recorded retry_start event
        mock_context.add_memory.assert_called()
        calls = mock_context.add_memory.call_args_list
        assert any("retry_start" in str(call) for call in calls)

    def test_retry_controller_thread_safety(self):
        """C: Comprehensive - statistics thread-safe"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.001, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        results = []

        def concurrent_func():
            try:
                result = controller.execute_with_retry(lambda: "ok")
                results.append(result)
            except Exception:
                pass

        # Run concurrent operations
        threads = [threading.Thread(target=concurrent_func) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should succeed
        assert len(results) == 10

        # Statistics should be accurate
        stats = controller.get_statistics()
        assert stats["total_executions"] == 10

    def test_retry_controller_wrap_tool(self):
        """C: Comprehensive - wrap_tool adds retry to tool methods"""
        strategy = ExponentialBackoffStrategy(initial_delay=0.01, max_attempts=3, jitter=False)
        controller = RetryController(strategy)

        # Create a mock tool
        class MockTool:
            def run(self):
                return "tool result"

            def other_method(self):
                return "other"

        tool = MockTool()
        wrapped_tool = controller.wrap_tool(tool)

        # Wrapped tool should work
        result = wrapped_tool.run()
        assert result == "tool result"

    def test_retry_controller_preserves_function_arguments(self):
        """Y: Yield - function arguments passed correctly"""
        strategy = ExponentialBackoffStrategy(max_attempts=2, jitter=False)
        controller = RetryController(strategy)

        def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = controller.execute_with_retry(func_with_args, "x", "y", c="z")
        assert result == "x-y-z"

    def test_retry_controller_delay_respected(self):
        """Y: Yield - retry delays are calculated correctly"""
        strategy = ExponentialBackoffStrategy(
            initial_delay=0.05, multiplier=2.0, max_attempts=3, jitter=False
        )

        # Test that delays are calculated correctly
        assert strategy.calculate_delay(0) == 0.05  # First retry: 0.05s
        assert strategy.calculate_delay(1) == 0.10  # Second retry: 0.10s

        # Test that retries actually happen with delays
        controller = RetryController(strategy)
        attempt_count = [0]

        def flaky_func():
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise ValueError("retry")
            return "ok"

        result = controller.execute_with_retry(flaky_func)
        assert result == "ok"
        assert attempt_count[0] == 2  # Should have retried once
