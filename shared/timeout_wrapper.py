"""
Constitutional Timeout Wrapper - ADR-018 Implementation
Provides Article I compliant timeout handling with exponential retry (1x→2x→3x→5x→10x).

Reference: ADR-018, bash.py:535-599 (proven implementation)
Constitutional Authority: Article I Section 1.2 (Timeout Handling)
"""
import functools
import logging
import time
from datetime import datetime
from typing import TypeVar, Callable, Optional, Tuple, Any, List
from pydantic import BaseModel, Field

# Type variables
T = TypeVar('T')
E = TypeVar('E', bound=Exception)


class TimeoutConfig(BaseModel):
    """Configuration for constitutional timeout behavior."""

    base_timeout_ms: int = Field(
        default=120000,
        description="Base timeout in milliseconds (default: 2 minutes)",
        ge=5000,  # Minimum 5 seconds
        le=600000  # Maximum 10 minutes base
    )

    max_retries: int = Field(
        default=5,
        description="Maximum retry attempts (default: 5 per Article I)",
        ge=1,
        le=10
    )

    multipliers: List[int] = Field(
        default=[1, 2, 3, 5, 10],
        description="Timeout multipliers for each retry (Article I: up to 10x)"
    )

    completeness_check: bool = Field(
        default=True,
        description="Validate output completeness (Article I)"
    )

    telemetry_enabled: bool = Field(
        default=True,
        description="Enable telemetry events for learning (Article IV)"
    )

    pause_between_retries_sec: float = Field(
        default=2.0,
        description="Pause duration between retries (Article I)",
        ge=0.0,
        le=10.0
    )


class TimeoutError(Exception):
    """Base class for timeout-related errors."""
    pass


class TimeoutExhaustedError(TimeoutError):
    """Raised when all retry attempts exhausted."""

    def __init__(
        self,
        attempts: int,
        total_time_ms: int,
        last_error: Optional[Exception]
    ):
        self.attempts = attempts
        self.total_time_ms = total_time_ms
        self.last_error = last_error
        super().__init__(
            f"Constitutional timeout exhausted after {attempts} attempts "
            f"({total_time_ms}ms total). Article I: Unable to obtain complete context."
        )


class IncompleteContextError(TimeoutError):
    """Raised when output appears incomplete (Article I violation)."""

    def __init__(self, indicator: str):
        self.indicator = indicator
        super().__init__(
            f"Incomplete context detected: {indicator}. "
            f"Article I: NEVER proceed with incomplete data."
        )


def _validate_completeness(result: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate if operation result appears complete.

    Reference: bash.py proven patterns
    Constitutional Authority: Article I (Context Verification)

    Returns:
        Tuple[is_complete, incomplete_indicator]
    """
    result_str = str(result)

    # Common incomplete output indicators (from bash.py)
    incomplete_indicators = [
        'Terminated',
        'Killed',
        '... (truncated)',
        'Connection timed out',
        'Resource temporarily unavailable',
        'Signal received',
        'Process interrupted'
    ]

    for indicator in incomplete_indicators:
        if indicator in result_str:
            return (False, indicator)

    return (True, None)


def run_with_constitutional_timeout(
    operation: Callable[[int], T],
    config: Optional[TimeoutConfig] = None,
    telemetry_prefix: str = "operation"
) -> T:
    """
    Execute operation with constitutional timeout retry logic.

    Implements Article I Section 1.2: Timeout Handling
    - Retries with exponential timeout multipliers (1x→2x→3x→5x→10x)
    - Validates output completeness
    - NEVER proceeds with incomplete data

    Args:
        operation: Callable that accepts timeout_ms and returns result
        config: Optional TimeoutConfig (uses defaults if None)
        telemetry_prefix: Prefix for telemetry events

    Returns:
        T: Operation result

    Raises:
        TimeoutExhaustedError: After max_retries exceeded
        IncompleteContextError: If output validation fails

    Reference: bash.py:535-599 (proven implementation)
    """
    if config is None:
        config = TimeoutConfig()

    start_time = datetime.now()
    last_result = None
    last_exception = None

    for attempt in range(config.max_retries):
        # Calculate timeout for this attempt (Article I pattern)
        if attempt < len(config.multipliers):
            current_timeout_ms = config.base_timeout_ms * config.multipliers[attempt]
        else:
            current_timeout_ms = config.base_timeout_ms * 10  # Cap at 10x

        try:
            logging.info(
                f"{telemetry_prefix}: Attempt {attempt + 1}/{config.max_retries}, "
                f"timeout: {current_timeout_ms}ms, "
                f"multiplier: {config.multipliers[attempt] if attempt < len(config.multipliers) else 10}x"
            )

            # Execute operation with current timeout
            result = operation(current_timeout_ms)

            # Article I: Validate completeness if enabled
            if config.completeness_check:
                is_complete, indicator = _validate_completeness(result)
                if not is_complete:
                    logging.warning(
                        f"{telemetry_prefix}: Incomplete output detected "
                        f"(indicator: {indicator}), retrying..."
                    )
                    last_result = result
                    continue  # Retry with next timeout

            # Success
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logging.info(
                f"{telemetry_prefix}: Success on attempt {attempt + 1}, "
                f"elapsed: {elapsed_ms}ms"
            )

            return result

        except Exception as e:
            # Timeout or other error occurred
            logging.warning(
                f"{telemetry_prefix}: Error on attempt {attempt + 1}: {type(e).__name__}"
            )

            last_exception = e

            # Article I: Brief pause for analysis before retry
            if attempt < config.max_retries - 1:
                time.sleep(config.pause_between_retries_sec)
                continue
            else:
                # Final attempt failed
                elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                logging.error(
                    f"{telemetry_prefix}: Timeout exhausted after {config.max_retries} "
                    f"attempts, {elapsed_ms}ms total"
                )

                raise TimeoutExhaustedError(
                    attempts=config.max_retries,
                    total_time_ms=elapsed_ms,
                    last_error=e
                )

    # Should never reach here
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    raise TimeoutExhaustedError(
        attempts=config.max_retries,
        total_time_ms=elapsed_ms,
        last_error=last_exception
    )


def with_constitutional_timeout(
    config: Optional[TimeoutConfig] = None,
    telemetry_prefix: str = "tool"
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for constitutional timeout compliance.

    Usage:
        @with_constitutional_timeout()
        def my_tool_run(self, timeout=None):
            # Implementation uses timeout parameter
            return result

    Args:
        config: Optional TimeoutConfig (uses tool.timeout_config if None)
        telemetry_prefix: Prefix for telemetry events

    Returns:
        Decorated function with timeout retry logic

    Reference: ADR-018 API Design
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Get config from tool instance if available
            actual_config = config
            if actual_config is None and args and hasattr(args[0], 'timeout_config'):
                actual_config = args[0].timeout_config
            if actual_config is None:
                actual_config = TimeoutConfig()  # Use defaults

            # Extract tool name for telemetry
            tool_name = telemetry_prefix
            if args and hasattr(args[0], '__class__'):
                tool_name = args[0].__class__.__name__.lower()

            # Wrap the original function in timeout retry logic
            def operation_wrapper(timeout_ms: int) -> T:
                # Inject timeout into function if it accepts it
                if 'timeout' in func.__code__.co_varnames:
                    kwargs['timeout'] = timeout_ms
                elif 'timeout_ms' in func.__code__.co_varnames:
                    kwargs['timeout_ms'] = timeout_ms
                return func(*args, **kwargs)

            # Execute with constitutional timeout pattern
            return run_with_constitutional_timeout(
                operation=operation_wrapper,
                config=actual_config,
                telemetry_prefix=tool_name
            )

        return wrapper

    return decorator


# Export public API
__all__ = [
    'TimeoutConfig',
    'TimeoutError',
    'TimeoutExhaustedError',
    'IncompleteContextError',
    'run_with_constitutional_timeout',
    'with_constitutional_timeout',
]
