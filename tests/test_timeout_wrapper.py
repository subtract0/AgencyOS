"""
Tests for Constitutional Timeout Wrapper (ADR-018)
Reference: bash.py:535-599 (proven implementation pattern)
"""
import pytest
import time
from unittest.mock import Mock
from shared.timeout_wrapper import (
    TimeoutConfig,
    TimeoutError,
    TimeoutExhaustedError,
    IncompleteContextError,
    run_with_constitutional_timeout,
    with_constitutional_timeout,
    _validate_completeness,
)


class TestTimeoutConfig:
    """Test TimeoutConfig model validation."""

    def test_default_config(self):
        """Test default configuration values match ADR-018."""
        config = TimeoutConfig()
        assert config.base_timeout_ms == 120000  # 2 minutes
        assert config.max_retries == 5
        assert config.multipliers == [1, 2, 3, 5, 10]  # Article I pattern
        assert config.completeness_check is True
        assert config.telemetry_enabled is True
        assert config.pause_between_retries_sec == 2.0

    def test_custom_config(self):
        """Test custom configuration."""
        config = TimeoutConfig(
            base_timeout_ms=60000,
            max_retries=3,
            multipliers=[1, 2, 3]
        )
        assert config.base_timeout_ms == 60000
        assert config.max_retries == 3
        assert config.multipliers == [1, 2, 3]


class TestCompletenessValidation:
    """Test output completeness validation logic."""

    def test_complete_output(self):
        """Test complete output passes validation."""
        result = "This is a complete output with no issues"
        is_complete, indicator = _validate_completeness(result)
        assert is_complete is True
        assert indicator is None

    def test_truncated_output(self):
        """Test truncated output detected."""
        result = "Output... (truncated)"
        is_complete, indicator = _validate_completeness(result)
        assert is_complete is False
        assert indicator == "... (truncated)"

    def test_terminated_output(self):
        """Test terminated output detected."""
        result = "Process was Terminated unexpectedly"
        is_complete, indicator = _validate_completeness(result)
        assert is_complete is False
        assert indicator == "Terminated"


class TestRunWithConstitutionalTimeout:
    """Test core timeout retry logic."""

    def test_success_first_attempt(self):
        """Test operation succeeds on first attempt."""
        def operation(timeout_ms):
            return "success"

        result = run_with_constitutional_timeout(operation)
        assert result == "success"

    def test_retry_then_success(self):
        """Test operation fails then succeeds on retry."""
        attempt_count = 0

        def operation(timeout_ms):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise Exception("Timeout")
            return "success_after_retry"

        result = run_with_constitutional_timeout(operation)
        assert result == "success_after_retry"
        assert attempt_count == 2

    def test_timeout_multipliers_progression(self):
        """Verify timeout multipliers follow Article I pattern."""
        timeouts_received = []

        def operation(timeout_ms):
            timeouts_received.append(timeout_ms)
            if len(timeouts_received) < 3:
                raise Exception("Timeout")
            return "success"

        config = TimeoutConfig(base_timeout_ms=5000)
        result = run_with_constitutional_timeout(operation, config=config)

        # Should have tried: 1x, 2x, then 3x (success)
        assert timeouts_received == [5000, 10000, 15000]
        assert result == "success"

    def test_exhausted_timeout(self):
        """Test timeout exhausted after max retries."""
        def operation(timeout_ms):
            raise Exception("Always fails")

        config = TimeoutConfig(base_timeout_ms=5000, max_retries=2)

        with pytest.raises(TimeoutExhaustedError) as exc:
            run_with_constitutional_timeout(operation, config=config)

        assert exc.value.attempts == 2


class TestWithConstitutionalTimeoutDecorator:
    """Test decorator pattern."""

    def test_decorator_basic_success(self):
        """Test decorator with successful operation."""
        @with_constitutional_timeout()
        def my_operation():
            return "decorated_success"

        result = my_operation()
        assert result == "decorated_success"

    def test_decorator_with_timeout_parameter(self):
        """Test decorator injects timeout parameter."""
        timeout_received = None

        @with_constitutional_timeout()
        def my_operation(timeout=None):
            nonlocal timeout_received
            timeout_received = timeout
            return "success"

        result = my_operation()

        assert result == "success"
        assert timeout_received == 120000  # Uses default config (120000ms)

    def test_decorator_retry_on_exception(self):
        """Test decorator retries on exception."""
        attempt_count = 0

        @with_constitutional_timeout()
        def my_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise Exception("First attempt fails")
            return "success_second_attempt"

        result = my_operation()
        assert result == "success_second_attempt"
        assert attempt_count == 2


class TestErrorTypes:
    """Test custom error types."""

    def test_timeout_exhausted_error(self):
        """Test TimeoutExhaustedError contains attempt info."""
        error = TimeoutExhaustedError(
            attempts=5,
            total_time_ms=10000,
            last_error=Exception("test")
        )

        assert error.attempts == 5
        assert error.total_time_ms == 10000
        assert "5 attempts" in str(error)
        assert "Article I" in str(error)

    def test_incomplete_context_error(self):
        """Test IncompleteContextError contains indicator."""
        error = IncompleteContextError(indicator="truncated")

        assert error.indicator == "truncated"
        assert "truncated" in str(error)
        assert "Article I" in str(error)


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_slow_operation_eventually_succeeds(self):
        """Test operation that needs multiple retries to succeed."""
        attempts = 0

        def slow_operation(timeout_ms):
            nonlocal attempts
            attempts += 1
            # Succeed on 3rd attempt
            if attempts < 3:
                raise Exception(f"Timeout on attempt {attempts}")
            return f"Completed after {attempts} attempts"

        config = TimeoutConfig(base_timeout_ms=5000, pause_between_retries_sec=0.1)
        result = run_with_constitutional_timeout(slow_operation, config=config)

        assert "Completed after 3 attempts" in result
        assert attempts == 3

    def test_completeness_check_triggers_retry(self):
        """Test incomplete output triggers retry even without exception."""
        attempts = 0

        def operation_with_incomplete_output(timeout_ms):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return "Output... (truncated)"  # Incomplete
            return "Complete output"  # Complete

        config = TimeoutConfig(
            base_timeout_ms=5000,
            completeness_check=True,
            pause_between_retries_sec=0.1
        )
        result = run_with_constitutional_timeout(operation_with_incomplete_output, config=config)

        assert result == "Complete output"
        assert attempts == 2  # Should retry due to incomplete output
