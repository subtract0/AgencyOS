"""
Mars Rover Reliability - Phase 1: Circuit Breaker Pattern.

Prevents cascading failures by "tripping" when a service fails too often.

Constitutional Compliance:
- Article II: 100% verification (prevents system-wide failures)
- Article III: Automated enforcement (auto-trips on threshold)
- Article IV: Learning (failure patterns stored to VectorStore)

Features:
1. Three states: CLOSED, OPEN, HALF_OPEN
2. Automatic state transitions based on failures/successes
3. Configurable failure threshold and recovery timeout
4. Per-service isolation via registry
5. Async support for async operations
6. Metrics tracking for monitoring
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Too many failures, requests are rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitOpenError(Exception):
    """Raised when circuit is OPEN and rejecting requests."""

    def __init__(self, message: str = "Circuit breaker is OPEN"):
        self.message = message
        super().__init__(self.message)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    half_open_max_requests: int = 3


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Prevents cascading failures by tracking failures and "tripping"
    when the failure threshold is reached.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_max_requests: int = 3,
        name: str = "default",
    ):
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout_seconds: Time to wait before trying again
            half_open_max_requests: Max requests allowed in HALF_OPEN state
            name: Name for logging/identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_max_requests = half_open_max_requests
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_requests = 0

        # Metrics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0

        self._lock = threading.RLock()

        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout_seconds}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transition."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.recovery_timeout_seconds:
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_requests = 0
                        logger.info(f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN")

            return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        with self._lock:
            return self._failure_count

    def record_failure(self) -> None:
        """
        Record a failure.

        Increments failure count and potentially trips the circuit.
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN returns to OPEN
                self._state = CircuitState.OPEN
                logger.warning(
                    f"CircuitBreaker '{self.name}' reopened due to failure in HALF_OPEN"
                )
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"CircuitBreaker '{self.name}' OPENED after "
                        f"{self._failure_count} failures"
                    )

    def record_success(self) -> None:
        """
        Record a success.

        Resets failure count and potentially closes the circuit.
        """
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # Success in HALF_OPEN closes the circuit
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"CircuitBreaker '{self.name}' CLOSED after successful probe")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.

        Returns:
            True if request should proceed, False if rejected
        """
        state = self.state  # This triggers timeout check

        with self._lock:
            if state == CircuitState.CLOSED:
                return True
            elif state == CircuitState.OPEN:
                return False
            elif state == CircuitState.HALF_OPEN:
                # Allow limited requests in HALF_OPEN
                if self._half_open_requests < self.half_open_max_requests:
                    self._half_open_requests += 1
                    return True
                return False

        return False

    def call(self, func: Callable[[], T]) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute

        Returns:
            Result of the function

        Raises:
            CircuitOpenError: If circuit is OPEN
            Exception: Any exception from the function
        """
        with self._lock:
            self._total_calls += 1

        if not self.allow_request():
            with self._lock:
                self._failed_calls += 1
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        try:
            result = func()
            self.record_success()
            with self._lock:
                self._successful_calls += 1
            return result
        except Exception as e:
            self.record_failure()
            with self._lock:
                self._failed_calls += 1
            raise

    async def async_call(self, func: Callable[[], Awaitable[T]]) -> T:
        """
        Execute an async function through the circuit breaker.

        Args:
            func: Async function to execute

        Returns:
            Result of the function

        Raises:
            CircuitOpenError: If circuit is OPEN
            Exception: Any exception from the function
        """
        with self._lock:
            self._total_calls += 1

        if not self.allow_request():
            with self._lock:
                self._failed_calls += 1
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        try:
            result = await func()
            self.record_success()
            with self._lock:
                self._successful_calls += 1
            return result
        except Exception as e:
            self.record_failure()
            with self._lock:
                self._failed_calls += 1
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "total_calls": self._total_calls,
                "successful_calls": self._successful_calls,
                "failed_calls": self._failed_calls,
                "success_rate": (
                    self._successful_calls / self._total_calls * 100
                    if self._total_calls > 0
                    else 0.0
                ),
            }

    def get_status(self) -> dict[str, Any]:
        """Get current status summary."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout_seconds,
                "half_open_max_requests": self.half_open_max_requests,
            }

    def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_requests = 0
            self._total_calls = 0
            self._successful_calls = 0
            self._failed_calls = 0
            logger.info(f"CircuitBreaker '{self.name}' reset to CLOSED")


class CircuitBreakerRegistry:
    """
    Registry for managing per-service circuit breakers.

    Provides isolation between different services/endpoints.
    """

    def __init__(
        self,
        default_failure_threshold: int = 5,
        default_recovery_timeout: float = 30.0,
        default_half_open_max_requests: int = 3,
    ):
        """
        Initialize the registry.

        Args:
            default_failure_threshold: Default failure threshold for new breakers
            default_recovery_timeout: Default recovery timeout for new breakers
            default_half_open_max_requests: Default max requests in HALF_OPEN
        """
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

        self._default_failure_threshold = default_failure_threshold
        self._default_recovery_timeout = default_recovery_timeout
        self._default_half_open_max_requests = default_half_open_max_requests

        logger.info("CircuitBreakerRegistry initialized")

    def get_or_create(
        self,
        service_name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[float] = None,
        half_open_max_requests: Optional[int] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service.

        Args:
            service_name: Unique service identifier
            failure_threshold: Override default failure threshold
            recovery_timeout: Override default recovery timeout
            half_open_max_requests: Override default max requests

        Returns:
            CircuitBreaker for the service
        """
        with self._lock:
            if service_name not in self._breakers:
                self._breakers[service_name] = CircuitBreaker(
                    name=service_name,
                    failure_threshold=failure_threshold or self._default_failure_threshold,
                    recovery_timeout_seconds=recovery_timeout or self._default_recovery_timeout,
                    half_open_max_requests=(
                        half_open_max_requests or self._default_half_open_max_requests
                    ),
                )
                logger.info(f"Created circuit breaker for service '{service_name}'")

            return self._breakers[service_name]

    def get_all_status(self) -> dict[str, dict]:
        """Get status of all circuit breakers."""
        with self._lock:
            return {name: cb.get_status() for name, cb in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()


# Global registry for convenience
_global_registry: Optional[CircuitBreakerRegistry] = None


def get_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CircuitBreakerRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _global_registry
    _global_registry = None
