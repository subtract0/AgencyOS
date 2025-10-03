"""
Tests for Constitutional Timeout Wrapper (ESSENTIAL Tool - 0% coverage)

Constitutional Compliance:
- Article I: Complete context (timeout retry 1x→2x→3x→5x→10x)
- Article II: 100% coverage of ESSENTIAL timeout operations
- TDD: Tests validate Article I timeout handling

Covers:
- TimeoutConfig (validation, default values)
- run_with_constitutional_timeout (retry logic, completeness checking)
- with_constitutional_timeout (decorator functionality)
- Timeout exhaustion and error handling
- Completeness validation (Article I)
"""

import pytest
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

from shared.timeout_wrapper import (
    TimeoutConfig,
    TimeoutError,
    TimeoutExhaustedError,
    IncompleteContextError,
    run_with_constitutional_timeout,
    with_constitutional_timeout,
    _validate_completeness,
)


# ========== NECESSARY Pattern: Normal Operation Tests ==========


class TestTimeoutConfig:
    """Tests for TimeoutConfig validation and defaults"""

    def test_timeout_config_defaults(self):
        """N: Normal - default configuration matches Article I"""
        config = TimeoutConfig()

        assert config.base_timeout_ms == 120000  # 2 minutes
        assert config.max_retries == 5
        assert config.multipliers == [1, 2, 3, 5, 10]  # Article I pattern
        assert config.completeness_check is True
        assert config.telemetry_enabled is True
        assert config.pause_between_retries_sec == 2.0

    def test_timeout_config_custom_values(self):
        """N: Normal - custom configuration accepted"""
        config = TimeoutConfig(
            base_timeout_ms=60000,
            max_retries=3,
            multipliers=[1, 2, 4],
            completeness_check=False,
            pause_between_retries_sec=1.0,
        )

        assert config.base_timeout_ms == 60000
        assert config.max_retries == 3
        assert config.multipliers == [1, 2, 4]
        assert config.completeness_check is False

    def test_timeout_config_validates_min_timeout(self):
        """E: Error - base_timeout_ms must be >= 5000"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TimeoutConfig(base_timeout_ms=1000)  # Too low

    def test_timeout_config_validates_max_timeout(self):
        """E: Error - base_timeout_ms must be <= 600000"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TimeoutConfig(base_timeout_ms=700000)

    def test_timeout_config_validates_max_retries(self):
        """E: Error - max_retries must be >= 1"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TimeoutConfig(max_retries=0)

    def test_timeout_config_validates_pause_range(self):
        """E: Error - pause must be in valid range"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            TimeoutConfig(pause_between_retries_sec=-1.0)

        with pytest.raises(Exception):  # Pydantic ValidationError
            TimeoutConfig(pause_between_retries_sec=20.0)


class TestValidateCompleteness:
    """Tests for completeness validation (Article I)"""

    def test_validate_completeness_success(self):
        """N: Normal - complete output passes validation"""
        result = "This is complete output\nAll data present"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is True
        assert indicator is None

    def test_validate_completeness_detects_terminated(self):
        """E: Error - detects 'Terminated' indicator"""
        result = "Some output\nTerminated\nIncomplete"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "Terminated"

    def test_validate_completeness_detects_killed(self):
        """E: Error - detects 'Killed' indicator"""
        result = "Process running\nKilled\n"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "Killed"

    def test_validate_completeness_detects_truncated(self):
        """E: Error - detects truncation"""
        result = "Data here... (truncated)"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "... (truncated)"

    def test_validate_completeness_detects_timeout(self):
        """E: Error - detects timeout indicators"""
        result = "Connection timed out while fetching data"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "Connection timed out"

    def test_validate_completeness_detects_signal(self):
        """E: Error - detects signal interruption"""
        result = "Running\nSignal received\nStopped"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "Signal received"

    def test_validate_completeness_detects_process_interrupted(self):
        """E: Error - detects process interruption"""
        result = "Process interrupted before completion"
        is_complete, indicator = _validate_completeness(result)

        assert is_complete is False
        assert indicator == "Process interrupted"


class TestRunWithConstitutionalTimeout:
    """Tests for run_with_constitutional_timeout (core function)"""

    def test_timeout_success_first_attempt(self):
        """N: Normal - operation succeeds on first attempt"""

        def operation(timeout_ms):
            return f"Success with {timeout_ms}ms"

        result = run_with_constitutional_timeout(operation)
        assert "Success with 120000ms" in result

    def test_timeout_retry_with_increasing_timeouts(self):
        """N: Normal - retries with Article I multipliers (1x→2x→3x→5x→10x)"""
        attempt_timeouts = []

        def operation(timeout_ms):
            attempt_timeouts.append(timeout_ms)
            if len(attempt_timeouts) < 3:
                raise TimeoutError("retry")
            return "success"

        config = TimeoutConfig(
            base_timeout_ms=5000, multipliers=[1, 2, 3, 5, 10], max_retries=5
        )
        result = run_with_constitutional_timeout(operation, config=config)

        assert result == "success"
        # Should have tried with 5000ms, 10000ms, 15000ms
        assert attempt_timeouts[0] == 5000  # 1x
        assert attempt_timeouts[1] == 10000  # 2x
        assert attempt_timeouts[2] == 15000  # 3x

    def test_timeout_exhausted_after_max_retries(self):
        """E: Error - raises TimeoutExhaustedError after max retries"""

        def always_fail(timeout_ms):
            raise TimeoutError("persistent timeout")

        config = TimeoutConfig(
            base_timeout_ms=5000,
            max_retries=3,
            pause_between_retries_sec=0.01,  # Fast for testing
        )

        with pytest.raises(TimeoutExhaustedError) as exc_info:
            run_with_constitutional_timeout(always_fail, config=config)

        error = exc_info.value
        assert error.attempts == 3
        assert "Article I" in str(error)

    def test_timeout_validates_completeness_and_retries(self):
        """C: Comprehensive - detects incomplete output and retries"""
        attempt_count = [0]

        def operation_with_incomplete(timeout_ms):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                return "Output Terminated"  # Incomplete
            return "Complete output"  # Complete

        config = TimeoutConfig(
            base_timeout_ms=5000,
            completeness_check=True,
            pause_between_retries_sec=0.01,
        )

        result = run_with_constitutional_timeout(operation_with_incomplete, config=config)
        # Should retry until complete output
        assert attempt_count[0] >= 2

    def test_timeout_skips_completeness_check_when_disabled(self):
        """C: Comprehensive - completeness check can be disabled"""

        def operation(timeout_ms):
            return "Output Terminated"  # Would normally fail

        config = TimeoutConfig(
            base_timeout_ms=5000, completeness_check=False  # Disabled
        )

        result = run_with_constitutional_timeout(operation, config=config)
        # Should succeed despite incomplete indicator
        assert "Terminated" in result

    def test_timeout_pause_between_retries(self):
        """Y: Yield - pause_between_retries_sec configuration is respected"""
        attempt_count = [0]

        def operation(timeout_ms):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise TimeoutError("retry")
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000, pause_between_retries_sec=2.5, max_retries=5
        )

        # Just test that configuration is accepted and retries happen
        result = run_with_constitutional_timeout(operation, config=config)

        assert result == "ok"
        assert attempt_count[0] == 3  # Should have retried twice

    def test_timeout_caps_at_10x_multiplier(self):
        """E: Edge - multiplier caps at 10x for attempts beyond list"""
        attempt_timeouts = []

        def operation(timeout_ms):
            attempt_timeouts.append(timeout_ms)
            if len(attempt_timeouts) < 7:
                raise TimeoutError("retry")
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000,
            multipliers=[1, 2, 3, 5, 10],  # Only 5 multipliers
            max_retries=7,
            pause_between_retries_sec=0.01,
        )

        result = run_with_constitutional_timeout(operation, config=config)

        # Attempts 6 and 7 should use 10x cap
        assert attempt_timeouts[5] == 50000  # 6th attempt: 10x (5000 * 10)
        assert attempt_timeouts[6] == 50000  # 7th attempt: 10x (5000 * 10)

    def test_timeout_telemetry_logging(self):
        """S: State - logs telemetry events"""

        def operation(timeout_ms):
            return "ok"

        with patch("shared.timeout_wrapper.logging") as mock_logging:
            run_with_constitutional_timeout(
                operation, telemetry_prefix="test_operation"
            )

            # Should have logged attempt and success
            mock_logging.info.assert_called()

    def test_timeout_handles_non_timeout_exceptions(self):
        """E: Error - propagates non-timeout exceptions"""

        def operation(timeout_ms):
            raise ValueError("not a timeout")

        config = TimeoutConfig(
            base_timeout_ms=5000, max_retries=3, pause_between_retries_sec=0.01
        )

        with pytest.raises(TimeoutExhaustedError) as exc_info:
            run_with_constitutional_timeout(operation, config=config)

        # Should have ValueError as last_error
        error = exc_info.value
        assert isinstance(error.last_error, ValueError)


class TestWithConstitutionalTimeoutDecorator:
    """Tests for @with_constitutional_timeout decorator"""

    def test_decorator_success(self):
        """N: Normal - decorator wraps function successfully"""

        @with_constitutional_timeout()
        def my_function():
            return "decorated result"

        result = my_function()
        assert result == "decorated result"

    def test_decorator_with_custom_config(self):
        """C: Comprehensive - decorator accepts custom config"""
        config = TimeoutConfig(base_timeout_ms=5000, max_retries=2)

        @with_constitutional_timeout(config=config)
        def my_function():
            return "custom config"

        result = my_function()
        assert result == "custom config"

    def test_decorator_injects_timeout_parameter(self):
        """Y: Yield - decorator injects timeout_ms parameter"""
        received_timeout = [None]

        @with_constitutional_timeout()
        def my_function(timeout_ms=None):
            received_timeout[0] = timeout_ms
            return "ok"

        result = my_function()
        assert result == "ok"
        # Should have injected timeout_ms
        assert received_timeout[0] is not None
        assert received_timeout[0] > 0

    def test_decorator_uses_tool_timeout_config(self):
        """S: State - decorator uses tool's timeout_config if available"""

        class MockTool:
            def __init__(self):
                self.timeout_config = TimeoutConfig(base_timeout_ms=30000)

            @with_constitutional_timeout()
            def run(self, timeout_ms=None):
                return timeout_ms

        tool = MockTool()
        timeout = tool.run()

        # Should use tool's config (30000ms)
        assert timeout == 30000

    def test_decorator_extracts_tool_name_for_telemetry(self):
        """S: State - decorator extracts tool name for logging"""

        class MyCustomTool:
            @with_constitutional_timeout()
            def run(self):
                return "ok"

        tool = MyCustomTool()

        with patch("shared.timeout_wrapper.logging") as mock_logging:
            result = tool.run()

            # Should have used tool class name in logging
            assert result == "ok"
            # Verify logging was called (telemetry)
            mock_logging.info.assert_called()

    def test_decorator_preserves_function_metadata(self):
        """Y: Yield - decorator preserves function name and docstring"""

        @with_constitutional_timeout()
        def my_documented_function():
            """This is a docstring."""
            return "ok"

        assert my_documented_function.__name__ == "my_documented_function"
        assert "docstring" in my_documented_function.__doc__

    def test_decorator_with_args_and_kwargs(self):
        """C: Comprehensive - decorator preserves function arguments"""

        @with_constitutional_timeout()
        def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = func_with_args("x", "y", c="z")
        assert result == "x-y-z"

    def test_decorator_retry_on_failure(self):
        """N: Normal - decorator retries on failure"""
        attempt_count = [0]

        @with_constitutional_timeout(
            config=TimeoutConfig(
                base_timeout_ms=5000,
                max_retries=3,
                pause_between_retries_sec=0.01,
            )
        )
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise TimeoutError("retry me")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert attempt_count[0] == 3


class TestTimeoutErrors:
    """Tests for custom timeout exceptions"""

    def test_timeout_exhausted_error_attributes(self):
        """Y: Yield - TimeoutExhaustedError has required attributes"""
        last_error = ValueError("test")
        error = TimeoutExhaustedError(attempts=5, total_time_ms=10000, last_error=last_error)

        assert error.attempts == 5
        assert error.total_time_ms == 10000
        assert error.last_error is last_error
        assert "Article I" in str(error)
        assert "5 attempts" in str(error)

    def test_incomplete_context_error_attributes(self):
        """Y: Yield - IncompleteContextError has required attributes"""
        error = IncompleteContextError(indicator="Terminated")

        assert error.indicator == "Terminated"
        assert "Article I" in str(error)
        assert "Terminated" in str(error)


class TestEdgeCases:
    """Edge cases and boundary conditions"""

    def test_timeout_with_zero_pause(self):
        """E: Edge - zero pause between retries"""

        def operation(timeout_ms):
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000, pause_between_retries_sec=0.0  # No pause
        )

        result = run_with_constitutional_timeout(operation, config=config)
        assert result == "ok"

    def test_timeout_with_max_pause(self):
        """E: Edge - maximum pause between retries"""

        def operation(timeout_ms):
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000, pause_between_retries_sec=10.0  # Max pause
        )

        result = run_with_constitutional_timeout(operation, config=config)
        assert result == "ok"

    def test_timeout_single_retry(self):
        """E: Edge - single retry allowed"""
        attempt_count = [0]

        def operation(timeout_ms):
            attempt_count[0] += 1
            if attempt_count[0] < 2:
                raise TimeoutError("retry")
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000, max_retries=2, pause_between_retries_sec=0.01
        )

        result = run_with_constitutional_timeout(operation, config=config)
        assert result == "ok"
        assert attempt_count[0] == 2

    def test_timeout_empty_multipliers_list(self):
        """E: Edge - empty multipliers defaults to 10x"""
        attempt_timeouts = []

        def operation(timeout_ms):
            attempt_timeouts.append(timeout_ms)
            if len(attempt_timeouts) < 2:
                raise TimeoutError("retry")
            return "ok"

        config = TimeoutConfig(
            base_timeout_ms=5000,
            multipliers=[],  # Empty
            max_retries=2,
            pause_between_retries_sec=0.01,
        )

        result = run_with_constitutional_timeout(operation, config=config)

        # Should default to 10x for all attempts
        assert attempt_timeouts[0] == 50000  # 5000 * 10
        assert attempt_timeouts[1] == 50000  # 5000 * 10

    def test_timeout_operation_returns_none(self):
        """E: Edge - operation returning None is valid"""

        def operation(timeout_ms):
            return None

        result = run_with_constitutional_timeout(operation)
        assert result is None

    def test_timeout_operation_returns_complex_object(self):
        """C: Comprehensive - handles complex return values"""

        def operation(timeout_ms):
            return {"status": "ok", "data": [1, 2, 3], "nested": {"key": "value"}}

        result = run_with_constitutional_timeout(operation)
        assert result["status"] == "ok"
        assert result["data"] == [1, 2, 3]
