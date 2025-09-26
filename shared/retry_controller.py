"""
RetryController implementation for robust error handling with configurable backoff strategies.

This module provides a comprehensive retry mechanism with memory integration,
thread-safety, and multiple backoff strategies for handling transient failures.
"""

import asyncio
import logging
import random
import signal
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Dict, Union
from shared.type_definitions.json import JSONValue
from functools import wraps


class RetryStrategy(ABC):
    """Abstract base class defining the interface for retry strategies."""

    @abstractmethod
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            attempt: The current attempt number (0-based)

        Returns:
            Delay in seconds before next retry
        """
        pass

    @abstractmethod
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if retry should be attempted.

        Args:
            attempt: The current attempt number (0-based)
            exception: The exception that occurred

        Returns:
            True if retry should be attempted, False otherwise
        """
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Exponential backoff strategy with configurable parameters and jitter.

    Implements exponential backoff where delay doubles with each attempt,
    with optional jitter to prevent thundering herd problems.
    """

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
        max_attempts: int = 3,
        should_retry_callback: Optional[Callable[[int, Exception], bool]] = None
    ):
        """
        Initialize exponential backoff strategy.

        Args:
            initial_delay: Initial delay in seconds (must be non-negative)
            max_delay: Maximum delay in seconds (must be positive)
            multiplier: Delay multiplier for each attempt (must be >= 1)
            jitter: Whether to add random jitter to delays
            max_attempts: Maximum number of retry attempts
            should_retry_callback: Custom callback to determine if retry should occur

        Raises:
            ValueError: If parameters are invalid
        """
        if initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")
        if max_delay <= 0:
            raise ValueError("max_delay must be positive")
        if multiplier < 1:
            raise ValueError("multiplier must be >= 1")

        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
        self.max_attempts = max_attempts
        self.should_retry_callback = should_retry_callback

    def calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with optional jitter."""
        if self.initial_delay == 0:
            return 0.0

        delay = self.initial_delay * (self.multiplier ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter and delay > 0:
            # Add jitter: delay * (0.75 to 1.25) to keep within expected ranges
            jitter_factor = 0.75 + (random.random() * 0.5)
            delay *= jitter_factor

        return delay

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if retry should be attempted based on attempts and exception type."""
        # Never retry certain system exceptions
        if isinstance(exception, (KeyboardInterrupt, SystemExit)):
            return False

        # Check max attempts
        if attempt >= self.max_attempts:
            return False

        # Use custom callback if provided
        if self.should_retry_callback:
            return self.should_retry_callback(attempt, exception)

        return True


class LinearBackoffStrategy(RetryStrategy):
    """
    Linear backoff strategy with constant increment per attempt.

    Implements linear backoff where delay increases by a fixed amount
    with each attempt, capped at maximum delay.
    """

    def __init__(
        self,
        initial_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0,
        max_attempts: int = 3
    ):
        """
        Initialize linear backoff strategy.

        Args:
            initial_delay: Initial delay in seconds
            increment: Delay increment per attempt
            max_delay: Maximum delay in seconds
            max_attempts: Maximum number of retry attempts
        """
        self.initial_delay = initial_delay
        self.increment = increment
        self.max_delay = max_delay
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int) -> float:
        """Calculate linear backoff delay."""
        delay = self.initial_delay + (self.increment * attempt)
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if retry should be attempted."""
        # Never retry certain system exceptions
        if isinstance(exception, (KeyboardInterrupt, SystemExit)):
            return False

        return attempt < self.max_attempts


class CircuitBreakerOpenError(RuntimeError):
    pass


class CircuitBreaker:
    """Simple circuit breaker to prevent thrashing on repeated failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 5.0):
        self.failure_threshold = max(1, int(failure_threshold))
        self.recovery_timeout = float(recovery_timeout)
        self.state = "closed"
        self.failure_count = 0
        self.opened_at: Optional[float] = None
        self._logger = logging.getLogger("shared.retry_controller")

    def allow_request(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            # Stay open until timeout expires
            if self.opened_at is not None and (time.time() - self.opened_at) >= self.recovery_timeout:
                # Move to half-open (allow a probe)
                self.state = "half_open"
                self._logger.info("circuit_half_open", extra={
                    "failure_threshold": self.failure_threshold,
                    "recovery_timeout": self.recovery_timeout,
                })
                return True
            return False
        if self.state == "half_open":
            # Allow a single probe (the controller will call record_success/failure)
            return True
        return True

    def record_success(self):
        # Reset to closed on any success
        prev_state = self.state
        self.state = "closed"
        self.failure_count = 0
        self.opened_at = None
        if prev_state != "closed":
            self._logger.info("circuit_closed")

    def record_failure(self):
        self.failure_count += 1
        self._logger.info("circuit_failure", extra={"failure_count": self.failure_count})
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.time()
            self._logger.warning("circuit_open", extra={
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            })


class RetryController:
    """
    Main retry controller that orchestrates retry logic with memory integration.

    Provides thread-safe retry functionality with memory tracking,
    timeout handling, and tool wrapping capabilities.
    """

    def __init__(
        self,
        strategy: RetryStrategy,
        agent_context: Optional[Any] = None,
        timeout: Optional[float] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        """
        Initialize retry controller.

        Args:
            strategy: Retry strategy to use
            agent_context: Optional agent context for memory integration
            timeout: Optional timeout for retry operations
            circuit_breaker: Optional CircuitBreaker instance for thrash protection
        """
        self.strategy = strategy
        self.agent_context = agent_context
        self.timeout = timeout
        self.circuit_breaker = circuit_breaker

        # Thread-safe statistics tracking
        self._stats_lock = threading.Lock()
        self._stats = {
            "total_executions": 0,
            "total_retries": 0,
            "successful_recoveries": 0,
            "failed_exhaustions": 0
        }

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result if successful

        Raises:
            Last exception if all retries are exhausted
            TimeoutError: If timeout is exceeded
        """
        start_time = time.time()
        attempt = 0
        last_exception = None

        # Circuit breaker guard
        if self.circuit_breaker and not self.circuit_breaker.allow_request():
            logging.getLogger("shared.retry_controller").warning("circuit_blocked_request")
            self._record_memory_event("circuit_open", {"timeout": self.circuit_breaker.recovery_timeout})
            raise CircuitBreakerOpenError("Circuit breaker open. Try later.")

        with self._stats_lock:
            self._stats["total_executions"] += 1

        # Record start event in memory
        self._record_memory_event("retry_start", {
            "function": func.__name__ if hasattr(func, '__name__') else str(func),
            "timestamp": start_time
        })

        while True:
            # Check timeout before each attempt
            if self.timeout and (time.time() - start_time) > self.timeout:
                raise TimeoutError("Retry operation timed out")

            try:
                # Execute function with timeout monitoring
                if self.timeout:
                    # Calculate remaining time for this attempt
                    elapsed = time.time() - start_time
                    remaining_time = self.timeout - elapsed
                    if remaining_time <= 0:
                        raise TimeoutError("Retry operation timed out")

                    # Execute function with timeout
                    result = self._execute_with_timeout(func, remaining_time, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - record recovery if this was a retry
                if attempt > 0:
                    with self._stats_lock:
                        self._stats["successful_recoveries"] += 1
                    self._record_memory_event("retry_success", {
                        "attempt": attempt,
                        "total_attempts": attempt + 1
                    })
                # Reset breaker on any success
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()

                return result

            except Exception as e:
                # Check if timeout occurred
                if self.timeout and (time.time() - start_time) > self.timeout:
                    raise TimeoutError("Retry operation timed out")

                last_exception = e

                # Update breaker on failure
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()

                # Check if we should retry
                if not self.strategy.should_retry(attempt, e):
                    # Record failure
                    with self._stats_lock:
                        self._stats["failed_exhaustions"] += 1
                    self._record_memory_event("retry_exhausted", {
                        "final_attempt": attempt,
                        "exception": str(e)
                    })
                    raise e

                # Record retry attempt
                with self._stats_lock:
                    self._stats["total_retries"] += 1

                self._record_memory_event("retry_attempt", {
                    "attempt": attempt,
                    "exception": str(e),
                    "delay": self.strategy.calculate_delay(attempt)
                })

                # Calculate and apply delay
                delay = self.strategy.calculate_delay(attempt)
                if delay > 0:
                    # Check timeout before sleeping
                    if self.timeout and (time.time() - start_time + delay) > self.timeout:
                        raise TimeoutError("Retry operation timed out")
                    time.sleep(delay)

                attempt += 1

    async def execute_with_retry_async(self, async_func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with retry logic.

        Args:
            async_func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result if successful

        Raises:
            Last exception if all retries are exhausted
        """
        start_time = time.time()
        attempt = 0

        with self._stats_lock:
            self._stats["total_executions"] += 1

        self._record_memory_event("async_retry_start", {
            "function": async_func.__name__ if hasattr(async_func, '__name__') else str(async_func),
            "timestamp": start_time
        })

        while True:
            try:
                result = await async_func(*args, **kwargs)

                # Success - record recovery if this was a retry
                if attempt > 0:
                    with self._stats_lock:
                        self._stats["successful_recoveries"] += 1
                    self._record_memory_event("async_retry_success", {
                        "attempt": attempt,
                        "total_attempts": attempt + 1
                    })

                return result

            except Exception as e:
                # Check if we should retry
                if not self.strategy.should_retry(attempt, e):
                    with self._stats_lock:
                        self._stats["failed_exhaustions"] += 1
                    self._record_memory_event("async_retry_exhausted", {
                        "final_attempt": attempt,
                        "exception": str(e)
                    })
                    raise e

                # Record retry attempt
                with self._stats_lock:
                    self._stats["total_retries"] += 1

                self._record_memory_event("async_retry_attempt", {
                    "attempt": attempt,
                    "exception": str(e),
                    "delay": self.strategy.calculate_delay(attempt)
                })

                # Calculate and apply delay
                delay = self.strategy.calculate_delay(attempt)
                if delay > 0:
                    await asyncio.sleep(delay)

                attempt += 1

    def wrap_tool(self, tool: Any) -> Any:
        """
        Wrap a tool with retry functionality.

        Args:
            tool: Tool to wrap

        Returns:
            Wrapped tool with retry capability
        """
        class WrappedTool:
            def __init__(self, original_tool, retry_controller):
                self._original_tool = original_tool
                self._retry_controller = retry_controller

                # Copy all attributes from original tool
                for attr_name in dir(original_tool):
                    if not attr_name.startswith('_'):
                        attr_value = getattr(original_tool, attr_name)
                        if callable(attr_value):
                            # Wrap callable methods with retry
                            setattr(self, attr_name, self._wrap_method(attr_value))
                        else:
                            # Copy non-callable attributes as-is
                            setattr(self, attr_name, attr_value)

            def _wrap_method(self, method):
                @wraps(method)
                def wrapper(*args, **kwargs):
                    return self._retry_controller.execute_with_retry(method, *args, **kwargs)
                return wrapper

        return WrappedTool(tool, self)

    def get_statistics(self) -> Dict[str, int]:
        """
        Get retry statistics.

        Returns:
            Dictionary containing retry statistics
        """
        with self._stats_lock:
            return self._stats.copy()

    def _execute_with_timeout(self, func: Callable, timeout_seconds: float, *args, **kwargs) -> Any:
        """Execute function with timeout using threading."""
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)

        if thread.is_alive():
            # Thread is still running, timeout occurred
            raise TimeoutError("Retry operation timed out")

        if exception[0]:
            raise exception[0]

        return result[0]

    def _record_memory_event(self, event_type: str, data: Dict[str, JSONValue]) -> None:
        """Record retry event in agent memory if context is available."""
        if self.agent_context and hasattr(self.agent_context, 'add_memory'):
            try:
                self.agent_context.add_memory(
                    content=f"retry_{event_type}",
                    metadata={
                        "event_type": event_type,
                        "timestamp": time.time(),
                        **data
                    }
                )
            except Exception:
                # Silently fail if memory recording fails
                # Don't let memory failures affect retry logic
                pass