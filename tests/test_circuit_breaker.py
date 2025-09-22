import pytest

from shared.retry_controller import RetryController, ExponentialBackoffStrategy, CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_opens_and_blocks_subsequent_calls():
    calls = {"count": 0}

    def always_fail():
        calls["count"] += 1
        raise ValueError("boom")

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
    strat = ExponentialBackoffStrategy(initial_delay=0.0, jitter=False, max_attempts=2)
    controller = RetryController(strategy=strat, circuit_breaker=breaker)

    # First execution: retries then raises, should open breaker by the end
    with pytest.raises(ValueError):
        controller.execute_with_retry(always_fail)

    prev_calls = calls["count"]

    # Second execution should be blocked immediately by breaker
    with pytest.raises(CircuitBreakerOpenError):
        controller.execute_with_retry(always_fail)

    assert calls["count"] == prev_calls, "Function should not be called when breaker is open"
