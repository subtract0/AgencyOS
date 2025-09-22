import pytest

from shared.retry_controller import RetryController, ExponentialBackoffStrategy


def test_non_retryable_exception_does_not_retry():
    attempts = {
        "count": 0
    }

    def should_retry_callback(attempt, exc):
        # Never retry on TypeError
        return not isinstance(exc, TypeError)

    strat = ExponentialBackoffStrategy(initial_delay=0.0, jitter=False, max_attempts=5, should_retry_callback=should_retry_callback)
    controller = RetryController(strategy=strat)

    def func():
        attempts["count"] += 1
        raise TypeError("no retry")

    with pytest.raises(TypeError):
        controller.execute_with_retry(func)

    assert attempts["count"] == 1


def test_max_attempts_limit():
    attempts = {"count": 0}

    max_attempts = 3
    strat = ExponentialBackoffStrategy(initial_delay=0.0, jitter=False, max_attempts=max_attempts)
    controller = RetryController(strategy=strat)

    def func():
        attempts["count"] += 1
        raise ValueError("retryable")

    with pytest.raises(ValueError):
        controller.execute_with_retry(func)

    # Controller retries up to max_attempts times + initial attempt
    assert attempts["count"] == max_attempts + 1
