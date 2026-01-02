"""
Mars Rover Reliability - Phase 1: Circuit Breaker Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article II: 100% verification (circuit breaker prevents cascading failures)
- Article III: Automated enforcement (auto-trips on threshold)

Acceptance Criteria:
1. Circuit breaker has three states: CLOSED, OPEN, HALF_OPEN
2. CLOSED state allows requests and tracks failures
3. OPEN state rejects requests immediately
4. HALF_OPEN state allows limited test requests
5. Automatic recovery after timeout
6. Per-service circuit breaker isolation
7. Failure rate threshold configuration
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCircuitBreakerStates:
    """Circuit breaker state transition tests."""

    def test_initial_state_is_closed(self) -> None:
        """Circuit breaker should start in CLOSED state."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=5)

        assert cb.state == CircuitState.CLOSED, "Initial state should be CLOSED"

    def test_transitions_to_open_on_threshold(self) -> None:
        """Circuit breaker should transition to OPEN after failure threshold."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3)

        # Record failures up to threshold
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN, "Should be OPEN after threshold failures"

    def test_transitions_to_half_open_after_timeout(self) -> None:
        """Circuit breaker should transition to HALF_OPEN after recovery timeout."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=1)

        # Trip the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Check state - should allow probe
        assert cb.state == CircuitState.HALF_OPEN, "Should be HALF_OPEN after timeout"

    def test_transitions_to_closed_on_success_in_half_open(self) -> None:
        """Successful request in HALF_OPEN should close circuit."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=0.1)

        # Trip and wait for half-open
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.15)

        assert cb.state == CircuitState.HALF_OPEN

        # Record success
        cb.record_success()

        assert cb.state == CircuitState.CLOSED, "Should close on success in HALF_OPEN"

    def test_returns_to_open_on_failure_in_half_open(self) -> None:
        """Failure in HALF_OPEN should reopen circuit."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=0.1)

        # Trip and wait for half-open
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.15)

        assert cb.state == CircuitState.HALF_OPEN

        # Record failure
        cb.record_failure()

        assert cb.state == CircuitState.OPEN, "Should reopen on failure in HALF_OPEN"


class TestCircuitBreakerClosedState:
    """Tests for CLOSED state behavior."""

    def test_allows_requests_when_closed(self) -> None:
        """CLOSED state should allow requests."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        assert cb.allow_request(), "Should allow requests when CLOSED"

    def test_tracks_failures_when_closed(self) -> None:
        """CLOSED state should track failure count."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        cb.record_failure()
        cb.record_failure()

        assert cb.failure_count == 2, "Should track failures"

    def test_resets_failures_on_success(self) -> None:
        """Success should reset failure count in CLOSED state."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb.failure_count == 0, "Success should reset failure count"


class TestCircuitBreakerOpenState:
    """Tests for OPEN state behavior."""

    def test_rejects_requests_when_open(self) -> None:
        """OPEN state should reject requests immediately."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3)

        # Trip the circuit
        for _ in range(3):
            cb.record_failure()

        assert not cb.allow_request(), "Should reject requests when OPEN"

    def test_raises_exception_on_call_when_open(self) -> None:
        """Calling through OPEN circuit should raise CircuitOpenError."""
        from tools.mars_rover.circuit_breaker import (
            CircuitBreaker,
            CircuitOpenError,
        )

        cb = CircuitBreaker(failure_threshold=3)

        # Trip the circuit
        for _ in range(3):
            cb.record_failure()

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "result")


class TestCircuitBreakerHalfOpenState:
    """Tests for HALF_OPEN state behavior."""

    def test_allows_limited_requests_when_half_open(self) -> None:
        """HALF_OPEN should allow limited test requests."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout_seconds=0.1,
            half_open_max_requests=2,
        )

        # Trip and wait
        for _ in range(3):
            cb.record_failure()
        time.sleep(0.15)

        assert cb.state == CircuitState.HALF_OPEN

        # Should allow limited requests
        assert cb.allow_request(), "First request should be allowed"
        assert cb.allow_request(), "Second request should be allowed"
        # Third might be blocked depending on implementation
        # (some implementations allow all in half-open)


class TestCircuitBreakerCallWrapper:
    """Tests for the call() wrapper method."""

    def test_call_returns_result_when_closed(self) -> None:
        """call() should return function result when circuit is CLOSED."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        result = cb.call(lambda: "success")

        assert result == "success"

    def test_call_records_success(self) -> None:
        """Successful call should record success."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()  # Add a failure first

        cb.call(lambda: "success")

        assert cb.failure_count == 0, "Success should reset failures"

    def test_call_records_failure_on_exception(self) -> None:
        """Failed call should record failure."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert cb.failure_count == 1, "Exception should record failure"


class TestCircuitBreakerAsync:
    """Async circuit breaker tests."""

    @pytest.mark.asyncio
    async def test_async_call_wrapper(self) -> None:
        """async_call() should work with async functions."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        async def async_operation():
            return "async_success"

        result = await cb.async_call(async_operation)

        assert result == "async_success"

    @pytest.mark.asyncio
    async def test_async_call_records_failure(self) -> None:
        """Async failure should record failure."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        async def failing_operation():
            raise ValueError("Async failure")

        try:
            await cb.async_call(failing_operation)
        except ValueError:
            pass

        assert cb.failure_count == 1


class TestCircuitBreakerRegistry:
    """Tests for per-service circuit breaker isolation."""

    def test_get_or_create_circuit_breaker(self) -> None:
        """Registry should create and cache circuit breakers per service."""
        from tools.mars_rover.circuit_breaker import CircuitBreakerRegistry

        registry = CircuitBreakerRegistry()

        cb1 = registry.get_or_create("service_a")
        cb2 = registry.get_or_create("service_a")
        cb3 = registry.get_or_create("service_b")

        assert cb1 is cb2, "Same service should return same circuit breaker"
        assert cb1 is not cb3, "Different services should have different breakers"

    def test_isolated_failure_tracking(self) -> None:
        """Failures should be isolated per service."""
        from tools.mars_rover.circuit_breaker import CircuitBreakerRegistry, CircuitState

        registry = CircuitBreakerRegistry(default_failure_threshold=3)

        cb_a = registry.get_or_create("service_a")
        cb_b = registry.get_or_create("service_b")

        # Trip service_a
        for _ in range(3):
            cb_a.record_failure()

        assert cb_a.state == CircuitState.OPEN, "Service A should be OPEN"
        assert cb_b.state == CircuitState.CLOSED, "Service B should still be CLOSED"


class TestCircuitBreakerConfiguration:
    """Configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.circuit_breaker import CircuitBreakerConfig

        config = CircuitBreakerConfig()

        assert config.failure_threshold > 0
        assert config.recovery_timeout_seconds > 0
        assert config.half_open_max_requests > 0

    def test_custom_configuration(self) -> None:
        """Custom configuration should be applied."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout_seconds=60,
            half_open_max_requests=5,
        )

        assert cb.failure_threshold == 10
        assert cb.recovery_timeout_seconds == 60
        assert cb.half_open_max_requests == 5


class TestCircuitBreakerMetrics:
    """Metrics and monitoring tests."""

    def test_tracks_total_calls(self) -> None:
        """Should track total number of calls."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=5)

        cb.call(lambda: "a")
        cb.call(lambda: "b")
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        metrics = cb.get_metrics()

        assert metrics["total_calls"] == 3, "Should track all calls"
        assert metrics["successful_calls"] == 2
        assert metrics["failed_calls"] == 1

    def test_get_status_summary(self) -> None:
        """Should provide status summary."""
        from tools.mars_rover.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(failure_threshold=5)

        status = cb.get_status()

        assert "state" in status
        assert status["state"] == CircuitState.CLOSED.value
        assert "failure_count" in status
        assert "failure_threshold" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
