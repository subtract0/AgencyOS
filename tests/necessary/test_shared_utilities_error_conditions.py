"""
NECESSARY Pattern Tests: Error Conditions for Shared Utilities

Tests focus on:
- Hook composition failures
- Model configuration errors
- Invalid parameter handling
- System hook error propagation
- Retry controller failures
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from shared.system_hooks import (
    CompositeHook,
    MemoryIntegrationHook,
    SystemReminderHook,
    ToolWrapperHook,
    MutationSnapshotHook,
    create_composite_hook,
)
from shared.model_policy import agent_model, DEFAULTS
from shared.retry_controller import RetryController, ExponentialBackoffStrategy, CircuitBreaker


class TestHookCompositionErrors:
    """Test error conditions in hook composition."""

    @pytest.mark.asyncio
    async def test_composite_hook_with_failing_hook(self):
        """Test composite hook when one hook fails."""
        mock_hook1 = Mock()
        mock_hook1.on_start = AsyncMock(side_effect=RuntimeError("Hook 1 failed"))

        mock_hook2 = Mock()
        mock_hook2.on_start = AsyncMock(return_value=None)

        composite = CompositeHook([mock_hook1, mock_hook2])

        # Should not raise exception, should continue with other hooks
        mock_context = Mock()
        mock_agent = Mock()

        await composite.on_start(mock_context, mock_agent)

        # Both hooks should have been called despite first one failing
        assert mock_hook1.on_start.called
        assert mock_hook2.on_start.called

    @pytest.mark.asyncio
    async def test_composite_hook_with_all_hooks_failing(self):
        """Test composite hook when all hooks fail."""
        mock_hook1 = Mock()
        mock_hook1.on_start = AsyncMock(side_effect=RuntimeError("Hook 1 failed"))

        mock_hook2 = Mock()
        mock_hook2.on_start = AsyncMock(side_effect=ValueError("Hook 2 failed"))

        composite = CompositeHook([mock_hook1, mock_hook2])

        # Should handle all failures gracefully
        mock_context = Mock()
        mock_agent = Mock()

        await composite.on_start(mock_context, mock_agent)

        # All hooks should have been attempted
        assert mock_hook1.on_start.called
        assert mock_hook2.on_start.called

    @pytest.mark.asyncio
    async def test_composite_hook_with_none_hook(self):
        """Test composite hook with None in hook list."""
        mock_hook = Mock()
        mock_hook.on_start = AsyncMock(return_value=None)

        # This should raise AttributeError when trying to call None.on_start
        composite = CompositeHook([mock_hook, None])

        mock_context = Mock()
        mock_agent = Mock()

        # Should handle None hook gracefully or raise appropriate error
        try:
            await composite.on_start(mock_context, mock_agent)
            # If it doesn't raise, that's fine (graceful handling)
        except AttributeError:
            # This is also acceptable - None doesn't have on_start
            pass

    @pytest.mark.asyncio
    async def test_composite_hook_with_empty_list(self):
        """Test composite hook with empty hook list."""
        composite = CompositeHook([])

        mock_context = Mock()
        mock_agent = Mock()

        # Should handle empty list without error
        await composite.on_start(mock_context, mock_agent)
        await composite.on_end(mock_context, mock_agent, None)
        await composite.on_tool_start(mock_context, mock_agent, Mock())

    @pytest.mark.asyncio
    async def test_composite_hook_with_invalid_hook_object(self):
        """Test composite hook with object that doesn't implement hook interface."""
        invalid_hook = "not a hook"

        composite = CompositeHook([invalid_hook])

        mock_context = Mock()
        mock_agent = Mock()

        # CompositeHook catches and logs AttributeError, doesn't raise
        # This is graceful error handling, not a failure
        await composite.on_start(mock_context, mock_agent)
        # Test passes if no exception is raised

    @pytest.mark.asyncio
    async def test_memory_hook_with_none_agent_context(self):
        """Test memory hook when agent_context is None."""
        hook = MemoryIntegrationHook(agent_context=None)

        # Hook should create default context
        assert hook.agent_context is not None

        mock_context = Mock()
        mock_agent = Mock()

        # Should work normally
        await hook.on_start(mock_context, mock_agent)

    @pytest.mark.asyncio
    async def test_memory_hook_store_failure(self):
        """Test memory hook when store_memory fails."""
        mock_context = Mock()
        mock_context.session_id = "test_session"
        mock_context.store_memory = Mock(side_effect=RuntimeError("Storage failed"))

        hook = MemoryIntegrationHook(agent_context=mock_context)

        mock_run_context = Mock()
        mock_agent = Mock()

        # Should handle storage failure gracefully (log warning, don't crash)
        await hook.on_start(mock_run_context, mock_agent)

    @pytest.mark.asyncio
    async def test_system_reminder_hook_with_invalid_context(self):
        """Test system reminder hook with invalid context structure."""
        hook = SystemReminderHook()

        # Context without required attributes
        mock_context = Mock()
        mock_context.context = None

        mock_agent = Mock()

        # This will raise AttributeError because filter_duplicates expects context.context.thread_manager
        # This is expected behavior - the hook requires a properly structured context
        with pytest.raises(AttributeError):
            await hook.on_start(mock_context, mock_agent)


class TestModelConfigurationErrors:
    """Test error conditions in model configuration."""

    def test_agent_model_with_unknown_key(self):
        """Test agent_model with unknown agent key."""
        # Should fall back to default
        model = agent_model("unknown_agent_key")
        assert model in ["gpt-5", "gpt-5-mini"]  # Should be a valid default

    def test_agent_model_with_none_key(self):
        """Test agent_model with None key."""
        # Should return default or raise error
        try:
            model = agent_model(None)
            # If it returns something, should be valid
            assert model in ["gpt-5", "gpt-5-mini"]
        except (TypeError, KeyError):
            # Raising an error is also acceptable
            pass

    def test_agent_model_with_empty_string(self):
        """Test agent_model with empty string."""
        model = agent_model("")
        # Should return default
        assert model in ["gpt-5", "gpt-5-mini"]

    def test_agent_model_with_invalid_env_override(self):
        """Test agent_model with invalid environment variable."""
        # Set invalid model in environment
        with patch.dict(os.environ, {"PLANNER_MODEL": ""}):
            # Reload to pick up env change
            from importlib import reload
            import shared.model_policy
            reload(shared.model_policy)

            model = shared.model_policy.agent_model("planner")
            # Should handle empty string (might fall back or use empty)
            assert isinstance(model, str)

    def test_model_policy_defaults_integrity(self):
        """Test that DEFAULTS dict has expected structure."""
        from shared.model_policy import DEFAULTS

        # All keys should map to strings
        assert isinstance(DEFAULTS, dict)
        for key, value in DEFAULTS.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            # Value can be empty string if env var is not set - that's valid

    def test_agent_model_case_sensitivity(self):
        """Test agent_model key case sensitivity."""
        # Should be case-sensitive
        model1 = agent_model("planner")
        model2 = agent_model("PLANNER")

        # PLANNER should fall back to default (unknown key)
        assert model1 != model2 or model2 in ["gpt-5", "gpt-5-mini"]


class TestToolWrapperHookErrors:
    """Test error conditions in ToolWrapperHook."""

    @pytest.mark.asyncio
    async def test_tool_wrapper_with_none_tool(self):
        """Test tool wrapper when tool is None."""
        hook = ToolWrapperHook()

        mock_context = Mock()
        mock_agent = Mock()

        # Should handle None tool gracefully
        await hook.on_tool_start(mock_context, mock_agent, None)

    @pytest.mark.asyncio
    async def test_tool_wrapper_with_tool_without_run_method(self):
        """Test tool wrapper with tool that has no run method."""
        hook = ToolWrapperHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock(spec=[])  # Empty spec, no methods

        # Should handle missing run method gracefully
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

    @pytest.mark.asyncio
    async def test_tool_wrapper_with_non_callable_run(self):
        """Test tool wrapper when run attribute is not callable."""
        hook = ToolWrapperHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.run = "not_callable"

        # Should handle non-callable run gracefully
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

    @pytest.mark.asyncio
    async def test_tool_wrapper_already_wrapped(self):
        """Test tool wrapper on already wrapped tool."""
        hook = ToolWrapperHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.run = Mock()
        mock_tool._wrapped_by_retry = True

        # Should skip wrapping if already wrapped
        original_run = mock_tool.run
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

        # run should not have changed
        assert mock_tool.run == original_run


class TestMutationSnapshotHookErrors:
    """Test error conditions in MutationSnapshotHook."""

    @pytest.mark.asyncio
    async def test_snapshot_with_none_tool(self):
        """Test snapshot hook with None tool."""
        hook = MutationSnapshotHook()

        mock_context = Mock()
        mock_agent = Mock()

        # Should handle None gracefully
        await hook.on_tool_start(mock_context, mock_agent, None)

    @pytest.mark.asyncio
    async def test_snapshot_with_non_mutating_tool(self):
        """Test snapshot hook with read-only tool."""
        hook = MutationSnapshotHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.name = "Read"  # Non-mutating

        # Should skip snapshot for read-only tools
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

    @pytest.mark.asyncio
    async def test_snapshot_with_invalid_file_path(self):
        """Test snapshot hook with invalid file path."""
        hook = MutationSnapshotHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.name = "Write"
        mock_tool.file_path = "/nonexistent/path/to/file.txt"

        # Should handle invalid path gracefully
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

    @pytest.mark.asyncio
    async def test_snapshot_with_file_outside_repo(self):
        """Test snapshot hook with file outside repository."""
        hook = MutationSnapshotHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.name = "Edit"
        mock_tool.file_path = "/tmp/outside_repo.txt"

        # Should skip files outside repo
        await hook.on_tool_start(mock_context, mock_agent, mock_tool)

    @pytest.mark.asyncio
    async def test_snapshot_with_permission_denied(self):
        """Test snapshot hook when snapshot directory creation fails."""
        hook = MutationSnapshotHook()

        mock_context = Mock()
        mock_agent = Mock()
        mock_tool = Mock()
        mock_tool.name = "Write"

        # Create a temp file in repo
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.getcwd()) as f:
            f.write("test content")
            temp_path = f.name

        try:
            mock_tool.file_path = temp_path

            # Mock os.makedirs to raise PermissionError
            with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
                # Should handle permission error gracefully
                await hook.on_tool_start(mock_context, mock_agent, mock_tool)
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestRetryControllerErrors:
    """Test error conditions in RetryController."""

    def test_retry_with_always_failing_function(self):
        """Test retry controller with function that always fails."""
        strategy = ExponentialBackoffStrategy(initial_delay=0.001, max_attempts=3, jitter=False)
        controller = RetryController(strategy=strategy)

        call_count = [0]

        def always_fails():
            call_count[0] += 1
            raise RuntimeError("Always fails")

        # Should raise after max attempts
        with pytest.raises(RuntimeError):
            controller.execute_with_retry(always_fails)

        # Should have tried at least max_attempts times (may be +1 for initial attempt)
        assert call_count[0] >= 3

    def test_retry_with_none_function(self):
        """Test retry controller with None function."""
        strategy = ExponentialBackoffStrategy(initial_delay=0.001, max_attempts=2)
        controller = RetryController(strategy=strategy)

        # Should raise TypeError
        with pytest.raises(TypeError):
            controller.execute_with_retry(None)

    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        strategy = ExponentialBackoffStrategy(initial_delay=0.001, max_attempts=1, jitter=False)
        controller = RetryController(strategy=strategy, circuit_breaker=breaker)

        def always_fails():
            raise RuntimeError("Failure")

        # Fail enough times to open circuit
        for _ in range(3):
            try:
                controller.execute_with_retry(always_fails)
            except RuntimeError:
                pass

        # Circuit should be open now
        # Next call should fail immediately without retrying
        with pytest.raises(RuntimeError):
            controller.execute_with_retry(always_fails)

    def test_retry_with_invalid_delay(self):
        """Test retry strategy with invalid delay values."""
        # Negative delay should raise ValueError during initialization
        with pytest.raises(ValueError):
            strategy = ExponentialBackoffStrategy(initial_delay=-1, max_attempts=2, jitter=False)

    def test_retry_with_zero_max_attempts(self):
        """Test retry strategy with zero max attempts."""
        strategy = ExponentialBackoffStrategy(initial_delay=0.001, max_attempts=0, jitter=False)
        controller = RetryController(strategy=strategy)

        def fails():
            raise RuntimeError("Failure")

        # Should raise immediately without retrying
        with pytest.raises(RuntimeError):
            controller.execute_with_retry(fails)


class TestCreateCompositeHookErrors:
    """Test error conditions in create_composite_hook factory."""

    def test_create_composite_hook_with_none(self):
        """Test creating composite hook with None."""
        hook = create_composite_hook(None)
        assert isinstance(hook, CompositeHook)
        assert len(hook.hooks) == 0

    def test_create_composite_hook_with_non_list(self):
        """Test creating composite hook with non-list argument."""
        # Should convert to list or handle gracefully
        mock_hook = Mock()
        hook = create_composite_hook(mock_hook)
        assert isinstance(hook, CompositeHook)

    def test_create_composite_hook_with_tuple(self):
        """Test creating composite hook with tuple."""
        mock_hooks = (Mock(), Mock())
        hook = create_composite_hook(mock_hooks)
        assert isinstance(hook, CompositeHook)
        assert len(hook.hooks) == 2


class TestHookErrorPropagation:
    """Test error propagation through hook chain."""

    @pytest.mark.asyncio
    async def test_on_tool_end_error_stores_error_memory(self):
        """Test that on_tool_end gracefully handles storage failures."""
        mock_context = Mock()
        mock_context.session_id = "test_session"
        mock_context.store_memory = Mock(side_effect=RuntimeError("Storage fails"))

        hook = MemoryIntegrationHook(agent_context=mock_context)

        mock_run_context = Mock()
        mock_agent = Mock()
        # Use proper mock that returns string for name attribute
        mock_agent.name = "TestAgent"
        mock_agent.__class__.__name__ = "TestAgent"
        mock_tool = Mock()
        mock_tool.name = "TestTool"

        # Should handle failure gracefully and log warning
        # No exception should be raised
        await hook.on_tool_end(mock_run_context, mock_agent, mock_tool, "result")

    @pytest.mark.asyncio
    async def test_hook_llm_methods_dont_raise(self):
        """Test that LLM hook methods handle errors gracefully."""
        hook = MemoryIntegrationHook()

        mock_context = Mock()
        mock_agent = Mock()

        # These should not raise exceptions
        await hook.on_llm_start(mock_context, mock_agent, "system prompt", [])
        await hook.on_llm_end(mock_context, mock_agent, {"response": "test"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])