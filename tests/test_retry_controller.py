"""
Test suite for RetryController implementing NECESSARY pattern.
Following ADR-002: Test-First Development - tests written before implementation.
"""

import asyncio
import threading
import time
import unittest
from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestRetryStrategy:
    """N: No Missing Behaviors - Test abstract retry strategy interface."""

    def test_strategy_abstract_interface(self):
        """Test that RetryStrategy enforces abstract methods."""
        from shared.retry_controller import RetryStrategy

        # Cannot instantiate abstract base class
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            RetryStrategy()

    def test_strategy_must_implement_calculate_delay(self):
        """Test that strategies must implement calculate_delay method."""
        from shared.retry_controller import RetryStrategy

        class IncompleteStrategy(RetryStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()

    def test_strategy_must_implement_should_retry(self):
        """Test that strategies must implement should_retry method."""
        from shared.retry_controller import RetryStrategy

        class PartialStrategy(RetryStrategy):
            def calculate_delay(self, attempt: int) -> float:
                return 1.0

        with pytest.raises(TypeError):
            PartialStrategy()


class TestExponentialBackoffStrategy:
    """E: Edge Cases - Test exponential backoff with various edge conditions."""

    def test_default_parameters(self):
        """Test exponential backoff with default parameters."""
        from shared.retry_controller import ExponentialBackoffStrategy

        strategy = ExponentialBackoffStrategy()

        # Default: 1s initial, 2x multiplier
        assert strategy.calculate_delay(0) == pytest.approx(1.0, rel=0.5)  # With jitter
        assert strategy.calculate_delay(1) >= 1.5  # At least 1.5x
        assert strategy.calculate_delay(2) >= 3.0  # At least 3x

    def test_custom_parameters(self):
        """C: Comprehensive - Test with custom configuration."""
        from shared.retry_controller import ExponentialBackoffStrategy

        strategy = ExponentialBackoffStrategy(
            initial_delay=0.5,
            max_delay=10.0,
            multiplier=3.0,
            jitter=False
        )

        assert strategy.calculate_delay(0) == 0.5
        assert strategy.calculate_delay(1) == 1.5
        assert strategy.calculate_delay(2) == 4.5
        assert strategy.calculate_delay(3) == 10.0  # Capped at max_delay

    def test_zero_initial_delay(self):
        """E: Edge Cases - Test with zero initial delay."""
        from shared.retry_controller import ExponentialBackoffStrategy

        strategy = ExponentialBackoffStrategy(initial_delay=0.0, jitter=False)

        assert strategy.calculate_delay(0) == 0.0
        assert strategy.calculate_delay(1) == 0.0
        assert strategy.calculate_delay(10) == 0.0

    def test_negative_parameters(self):
        """E: Error Conditions - Test with invalid parameters."""
        from shared.retry_controller import ExponentialBackoffStrategy

        with pytest.raises(ValueError, match="initial_delay must be non-negative"):
            ExponentialBackoffStrategy(initial_delay=-1.0)

        with pytest.raises(ValueError, match="max_delay must be positive"):
            ExponentialBackoffStrategy(max_delay=0.0)

        with pytest.raises(ValueError, match="multiplier must be >= 1"):
            ExponentialBackoffStrategy(multiplier=0.5)

    def test_jitter_adds_randomness(self):
        """S: State Validation - Test that jitter adds randomness."""
        from shared.retry_controller import ExponentialBackoffStrategy

        strategy = ExponentialBackoffStrategy(initial_delay=1.0, jitter=True)

        delays = [strategy.calculate_delay(1) for _ in range(10)]
        # With jitter, delays should vary
        assert len(set(delays)) > 1
        # But all within expected range (1.5 to 2.5 for attempt 1)
        assert all(1.5 <= d <= 2.5 for d in delays)

    def test_should_retry_logic(self):
        """Test retry decision logic based on attempts and exceptions."""
        from shared.retry_controller import ExponentialBackoffStrategy

        strategy = ExponentialBackoffStrategy(max_attempts=3)

        # Should retry on early attempts
        assert strategy.should_retry(0, Exception("test"))
        assert strategy.should_retry(1, Exception("test"))
        assert strategy.should_retry(2, Exception("test"))

        # Should not retry after max attempts
        assert not strategy.should_retry(3, Exception("test"))

        # Should not retry on certain exceptions
        assert not strategy.should_retry(0, KeyboardInterrupt())
        assert not strategy.should_retry(0, SystemExit())


class TestLinearBackoffStrategy:
    """Test linear backoff strategy implementation."""

    def test_linear_progression(self):
        """Test that delay increases linearly."""
        from shared.retry_controller import LinearBackoffStrategy

        strategy = LinearBackoffStrategy(initial_delay=1.0, increment=0.5)

        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 1.5
        assert strategy.calculate_delay(2) == 2.0
        assert strategy.calculate_delay(3) == 2.5

    def test_max_delay_cap(self):
        """Test that delays are capped at max_delay."""
        from shared.retry_controller import LinearBackoffStrategy

        strategy = LinearBackoffStrategy(
            initial_delay=1.0,
            increment=2.0,
            max_delay=5.0
        )

        assert strategy.calculate_delay(0) == 1.0
        assert strategy.calculate_delay(1) == 3.0
        assert strategy.calculate_delay(2) == 5.0
        assert strategy.calculate_delay(3) == 5.0  # Capped

    def test_zero_increment(self):
        """E: Edge Cases - Test with zero increment (constant delay)."""
        from shared.retry_controller import LinearBackoffStrategy

        strategy = LinearBackoffStrategy(initial_delay=2.0, increment=0.0)

        assert strategy.calculate_delay(0) == 2.0
        assert strategy.calculate_delay(5) == 2.0
        assert strategy.calculate_delay(10) == 2.0


class TestRetryController:
    """Test main RetryController orchestration class."""

    @pytest.fixture
    def mock_context(self):
        """Create mock AgentContext for testing."""
        context = MagicMock()
        context.add_memory = MagicMock()
        return context

    @pytest.fixture
    def controller(self, mock_context):
        """Create RetryController instance with mock context."""
        from shared.retry_controller import RetryController, ExponentialBackoffStrategy

        return RetryController(
            strategy=ExponentialBackoffStrategy(initial_delay=0.01, jitter=False),
            agent_context=mock_context
        )

    def test_successful_execution_no_retry(self, controller):
        """Test successful execution without retries."""
        mock_func = MagicMock(return_value="success")

        result = controller.execute_with_retry(mock_func, "arg1", key="value")

        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_once_with("arg1", key="value")

    def test_transient_failure_recovery(self, controller):
        """R: Regression Prevention - Test recovery from transient failures."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            "success"
        ]

        result = controller.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_permanent_failure_exhaustion(self, controller):
        """E: Error Conditions - Test when all retries are exhausted."""
        mock_func = MagicMock(side_effect=Exception("Permanent failure"))

        with pytest.raises(Exception, match="Permanent failure"):
            controller.execute_with_retry(mock_func)

        # Should attempt max_attempts times
        assert mock_func.call_count == 4  # 1 initial + 3 retries

    def test_memory_tracking(self, controller, mock_context):
        """S: Side Effects - Test memory integration for retry tracking."""
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("Error"), "success"]

        controller.execute_with_retry(mock_func)

        # Should record retry attempt in memory
        memory_calls = mock_context.add_memory.call_args_list
        assert len(memory_calls) >= 2  # At least start and retry event

        # Check retry event structure
        retry_event = None
        for call in memory_calls:
            if "retry" in str(call):
                retry_event = call
                break

        assert retry_event is not None

    def test_wrap_tool_functionality(self, controller):
        """Test wrapping a tool with retry functionality."""
        mock_tool = MagicMock()
        mock_tool.run = MagicMock(return_value="tool_result")

        wrapped_tool = controller.wrap_tool(mock_tool)

        result = wrapped_tool.run("arg")
        assert result == "tool_result"
        mock_tool.run.assert_called_once_with("arg")

    def test_wrapped_tool_with_retry(self, controller):
        """Test wrapped tool handles retries."""
        mock_tool = MagicMock()
        mock_tool.run = MagicMock()
        mock_tool.run.side_effect = [Exception("Error"), "success"]

        wrapped_tool = controller.wrap_tool(mock_tool)

        result = wrapped_tool.run()
        assert result == "success"
        assert mock_tool.run.call_count == 2

    @pytest.mark.asyncio
    async def test_async_execution_with_retry(self, controller):
        """A: Async Operations - Test async function retry."""
        mock_async_func = AsyncMock()
        mock_async_func.side_effect = [Exception("Async error"), "async_success"]

        result = await controller.execute_with_retry_async(mock_async_func)

        assert result == "async_success"
        assert mock_async_func.call_count == 2

    def test_concurrent_retry_operations(self, controller):
        """A: Async Operations - Test thread safety of retry controller."""
        results = []
        errors = []

        def flaky_function(thread_id):
            """Function that fails first time for each thread."""
            key = f"thread_{thread_id}"
            if not hasattr(flaky_function, key):
                setattr(flaky_function, key, True)
                raise Exception(f"First attempt for thread {thread_id}")
            return f"success_{thread_id}"

        def thread_worker(thread_id):
            try:
                result = controller.execute_with_retry(flaky_function, thread_id)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(5):
            t = threading.Thread(target=thread_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All threads should succeed after retry
        assert len(results) == 5
        assert len(errors) == 0
        assert all(f"success_{i}" in results for i in range(5))

    def test_timeout_handling(self, controller):
        """E: Error Conditions - Test timeout during retry."""
        from shared.retry_controller import RetryController, LinearBackoffStrategy

        # Controller with very short timeout
        controller = RetryController(
            strategy=LinearBackoffStrategy(initial_delay=2.0),  # 2 second delay
            timeout=1.0  # 1 second timeout
        )

        def slow_function():
            time.sleep(3)
            return "never_reached"

        with pytest.raises(TimeoutError):
            controller.execute_with_retry(slow_function)

    def test_non_retryable_exceptions(self, controller):
        """Test that certain exceptions are not retried."""
        mock_func = MagicMock(side_effect=KeyboardInterrupt())

        with pytest.raises(KeyboardInterrupt):
            controller.execute_with_retry(mock_func)

        # Should not retry on KeyboardInterrupt
        assert mock_func.call_count == 1

    def test_custom_retry_condition(self, controller):
        """Test custom retry condition callback."""
        from shared.retry_controller import RetryController, ExponentialBackoffStrategy

        def custom_should_retry(attempt: int, exception: Exception) -> bool:
            # Only retry on specific error messages
            return "retry_me" in str(exception)

        strategy = ExponentialBackoffStrategy(
            initial_delay=0.01,
            should_retry_callback=custom_should_retry
        )
        controller = RetryController(strategy=strategy)

        # Should retry this error
        mock_func1 = MagicMock()
        mock_func1.side_effect = [Exception("retry_me please"), "success"]
        result = controller.execute_with_retry(mock_func1)
        assert result == "success"
        assert mock_func1.call_count == 2

        # Should not retry this error
        mock_func2 = MagicMock(side_effect=Exception("do not retry"))
        with pytest.raises(Exception, match="do not retry"):
            controller.execute_with_retry(mock_func2)
        assert mock_func2.call_count == 1

    def test_retry_with_backoff_timing(self, controller):
        """S: State Validation - Test that backoff delays are applied."""
        from shared.retry_controller import RetryController, LinearBackoffStrategy

        controller = RetryController(
            strategy=LinearBackoffStrategy(initial_delay=0.1, increment=0.1)
        )

        mock_func = MagicMock()
        mock_func.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "success"
        ]

        start_time = time.time()
        result = controller.execute_with_retry(mock_func)
        elapsed = time.time() - start_time

        assert result == "success"
        # Should have delays: 0.1 (after first failure) + 0.2 (after second)
        assert elapsed >= 0.3
        assert mock_func.call_count == 3

    def test_retry_context_preservation(self, controller):
        """Y: Yielding Confidence - Test that context is preserved across retries."""
        context_data = {"request_id": "12345", "user": "test_user"}

        def context_aware_function(**kwargs):
            if not hasattr(context_aware_function, "called"):
                context_aware_function.called = True
                raise Exception("First attempt fails")
            return kwargs

        result = controller.execute_with_retry(
            context_aware_function,
            **context_data
        )

        assert result == context_data

    def test_statistics_tracking(self, controller, mock_context):
        """S: State Validation - Test retry statistics tracking."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "success"
        ]

        result = controller.execute_with_retry(mock_func)

        stats = controller.get_statistics()
        assert stats["total_executions"] == 1
        assert stats["total_retries"] == 2
        assert stats["successful_recoveries"] == 1
        assert stats["failed_exhaustions"] == 0

    def test_retry_with_different_strategies(self):
        """C: Comprehensive - Test switching between different strategies."""
        from shared.retry_controller import (
            RetryController,
            ExponentialBackoffStrategy,
            LinearBackoffStrategy
        )

        mock_func = MagicMock()
        mock_func.side_effect = [Exception("Error"), "success"]

        # Test with exponential strategy
        exp_controller = RetryController(
            strategy=ExponentialBackoffStrategy(initial_delay=0.01)
        )
        result = exp_controller.execute_with_retry(mock_func)
        assert result == "success"

        # Reset mock
        mock_func.reset_mock()
        mock_func.side_effect = [Exception("Error"), "success"]

        # Test with linear strategy
        lin_controller = RetryController(
            strategy=LinearBackoffStrategy(initial_delay=0.01)
        )
        result = lin_controller.execute_with_retry(mock_func)
        assert result == "success"


class TestIntegrationWithTools:
    """Integration tests with actual tool implementations."""

    @pytest.mark.integration
    def test_bash_tool_with_retry(self, tmp_path):
        """Test RetryController integration with Bash tool."""
        from shared.retry_controller import RetryController, ExponentialBackoffStrategy
        from tools.bash import BashTool

        controller = RetryController(
            strategy=ExponentialBackoffStrategy(initial_delay=0.01)
        )

        bash_tool = BashTool()
        wrapped_bash = controller.wrap_tool(bash_tool)

        # Should handle transient failures
        result = wrapped_bash.run(command="echo 'test'")
        assert "test" in result

    @pytest.mark.integration
    def test_edit_tool_with_retry(self, tmp_path):
        """Test RetryController integration with Edit tool."""
        from shared.retry_controller import RetryController, ExponentialBackoffStrategy
        from tools.edit import EditTool

        controller = RetryController(
            strategy=ExponentialBackoffStrategy(initial_delay=0.01)
        )

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        edit_tool = EditTool()
        wrapped_edit = controller.wrap_tool(edit_tool)

        result = wrapped_edit.run(
            file_path=str(test_file),
            old_string="original",
            new_string="modified"
        )

        assert "successfully" in result.lower()
        assert test_file.read_text() == "modified content"

    @pytest.mark.integration
    def test_memory_persistence_across_retries(self, mock_context):
        """S: Side Effects - Test that memory persists retry patterns."""
        from shared.retry_controller import RetryController, ExponentialBackoffStrategy

        controller = RetryController(
            strategy=ExponentialBackoffStrategy(initial_delay=0.01),
            agent_context=mock_context
        )

        # Simulate multiple retry scenarios
        for i in range(3):
            mock_func = MagicMock()
            if i < 2:
                # First two succeed after retry
                mock_func.side_effect = [Exception(f"Error {i}"), f"success {i}"]
            else:
                # Last one fails completely
                mock_func.side_effect = Exception("Permanent failure")

            try:
                controller.execute_with_retry(mock_func)
            except:
                pass

        stats = controller.get_statistics()
        assert stats["successful_recoveries"] == 2
        assert stats["failed_exhaustions"] == 1

        # Memory should contain retry events
        assert mock_context.add_memory.called
        memory_calls = mock_context.add_memory.call_args_list
        retry_events = [c for c in memory_calls if "retry" in str(c)]
        assert len(retry_events) > 0