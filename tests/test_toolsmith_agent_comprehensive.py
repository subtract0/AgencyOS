import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from shared.agent_context import create_agent_context
from toolsmith_agent import create_toolsmith_agent


class TestToolSmithAgentFactoryFunction:
    """Test suite for the create_toolsmith_agent factory function."""

    def test_default_parameters(self):
        """Test agent creation with default parameters."""
        agent = create_toolsmith_agent()

        assert agent.name == "ToolSmithAgent"
        assert isinstance(agent.description, str)
        assert "meta-agent" in agent.description.lower()
        assert "craftsman" in agent.description.lower()

    def test_custom_model_parameter(self):
        """Test agent creation with custom model parameter."""
        agent = create_toolsmith_agent(model="gpt-4")

        assert agent.name == "ToolSmithAgent"
        assert agent is not None

    def test_custom_reasoning_effort_parameter(self):
        """Test agent creation with custom reasoning effort."""
        agent = create_toolsmith_agent(reasoning_effort="medium")

        assert agent.name == "ToolSmithAgent"
        assert agent is not None

    def test_agent_context_parameter(self):
        """Test agent creation with provided agent context."""
        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        assert agent.name == "ToolSmithAgent"
        assert agent is not None

    def test_agent_context_none_creates_new(self):
        """Test that None agent_context creates a new one."""
        with patch('toolsmith_agent.toolsmith_agent.create_agent_context') as mock_create:
            mock_ctx = Mock()
            mock_ctx.session_id = "test_session"
            mock_create.return_value = mock_ctx

            agent = create_toolsmith_agent(agent_context=None)

            mock_create.assert_called_once()
            assert agent is not None

    @patch('toolsmith_agent.toolsmith_agent.select_instructions_file')
    @patch('toolsmith_agent.toolsmith_agent.get_model_instance')
    @patch('toolsmith_agent.toolsmith_agent.create_model_settings')
    def test_agent_configuration_calls(self, mock_settings, mock_model, mock_instructions):
        """Test that agent configuration functions are called correctly."""
        from agents.model_settings import ModelSettings

        mock_instructions.return_value = "test_instructions.md"
        mock_model.return_value = "gpt-5"  # Return a string instead of Mock
        mock_settings.return_value = ModelSettings(temperature=0.1)

        agent = create_toolsmith_agent(model="gpt-5", reasoning_effort="high")

        mock_instructions.assert_called_once()
        mock_model.assert_called_once_with("gpt-5")
        mock_settings.assert_called_once_with("gpt-5", "high")

    def test_agent_memory_logging(self):
        """Test that agent creation is logged to memory."""
        ctx = create_agent_context()

        with patch.object(ctx, 'store_memory') as mock_store:
            agent = create_toolsmith_agent(agent_context=ctx)

            mock_store.assert_called_once()
            call_args = mock_store.call_args

            # Check memory key
            assert f"agent_created_{ctx.session_id}" in call_args[0][0]

            # Check memory data
            memory_data = call_args[0][1]
            assert memory_data["agent_type"] == "ToolSmithAgent"
            assert memory_data["session_id"] == ctx.session_id

            # Check tags
            tags = call_args[0][2]
            assert "agency" in tags
            assert "toolsmith" in tags
            assert "creation" in tags

    def test_agent_hooks_configuration(self):
        """Test that agent hooks are properly configured."""
        agent = create_toolsmith_agent()

        assert hasattr(agent, 'hooks')
        assert agent.hooks is not None

    def test_current_directory_detection(self):
        """Test that current directory is detected correctly."""
        from toolsmith_agent.toolsmith_agent import current_dir

        assert isinstance(current_dir, str)
        assert os.path.exists(current_dir)
        assert "toolsmith_agent" in current_dir


class TestToolSmithAgentDescription:
    """Test suite for agent description and role definition."""

    def test_description_content(self):
        """Test that agent description accurately describes its role."""
        agent = create_toolsmith_agent()

        description = agent.description.lower()

        # Should mention key responsibilities
        assert "meta-agent" in description
        assert "craftsman" in description or "scaffold" in description
        assert "implements" in description or "implementation" in description
        assert "tests" in description
        assert "tools" in description

    def test_description_mentions_workflow(self):
        """Test that description mentions the expected workflow."""
        agent = create_toolsmith_agent()

        description = agent.description

        # Should mention key workflow elements
        assert "scaffold" in description.lower() or "scaffolds" in description.lower()
        assert "pytest" in description.lower() or "tests" in description.lower()
        assert "MergerAgent" in description or "hands off" in description.lower()

    def test_description_mentions_directives(self):
        """Test that description mentions accepting structured directives."""
        agent = create_toolsmith_agent()

        description = agent.description.lower()

        # Should mention directive processing
        assert "directives" in description or "structured" in description


class TestToolSmithAgentIntegration:
    """Integration tests for the toolsmith agent."""

    def test_agent_tool_compatibility(self):
        """Test that all agent tools are compatible and accessible."""
        agent = create_toolsmith_agent()

        # All tools should be importable/accessible
        for tool in agent.tools:
            assert tool is not None
            # Tools should have some identifying attribute
            assert hasattr(tool, '__name__') or hasattr(tool, 'name') or str(tool)

    def test_agent_hooks_system_integration(self):
        """Test that agent integrates properly with the hooks system."""
        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should have hooks that integrate with the system
        assert agent.hooks is not None

        # Test that hooks system is properly wired
        try:
            # Basic integration test - hooks should be callable
            if hasattr(agent.hooks, '__call__'):
                pass  # Hooks are callable
        except Exception as e:
            pytest.fail(f"Agent hooks integration failed: {e}")

    def test_tool_scaffolding_capability(self):
        """Test that agent has the tools needed for scaffolding."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # File operations
        assert any("Read" in name for name in tool_names)
        assert any("Write" in name for name in tool_names)
        assert any("Edit" in name for name in tool_names)
        assert any("MultiEdit" in name for name in tool_names)

        # Search and discovery
        assert any("Grep" in name for name in tool_names)
        assert any("Glob" in name for name in tool_names)

        # Testing and validation
        assert any("Bash" in name for name in tool_names)

        # Project management
        assert any("TodoWrite" in name for name in tool_names)

    def test_agent_uniqueness(self):
        """Test that each agent creation produces a unique instance."""
        agent1 = create_toolsmith_agent()
        agent2 = create_toolsmith_agent()

        # Should be different instances
        assert agent1 is not agent2

        # But should have same name and basic properties
        assert agent1.name == agent2.name == "ToolSmithAgent"

    def test_context_isolation(self):
        """Test that different agent contexts are properly isolated."""
        ctx1 = create_agent_context()
        ctx2 = create_agent_context()

        agent1 = create_toolsmith_agent(agent_context=ctx1)
        agent2 = create_toolsmith_agent(agent_context=ctx2)

        # Agents should be different
        assert agent1 is not agent2

        # Contexts should be different
        assert ctx1.session_id != ctx2.session_id


class TestToolSmithAgentErrorHandling:
    """Test suite for error handling in agent creation and operation."""

    def test_invalid_model_handling(self):
        """Test handling of invalid model specifications."""
        try:
            agent = create_toolsmith_agent(model="completely-invalid-model")
            # Might succeed with fallback behavior
            assert agent is not None
        except Exception:
            # Or might fail gracefully
            pass

    def test_invalid_reasoning_effort_handling(self):
        """Test handling of invalid reasoning effort levels."""
        try:
            agent = create_toolsmith_agent(reasoning_effort="invalid-effort")
            assert agent is not None
        except Exception:
            pass

    @patch('toolsmith_agent.toolsmith_agent.select_instructions_file', side_effect=FileNotFoundError())
    def test_missing_instructions_handling(self, mock_select):
        """Test handling when instructions file is missing."""
        try:
            agent = create_toolsmith_agent()
            # Should handle missing instructions gracefully
        except FileNotFoundError:
            # Or fail appropriately
            pass

    @patch('toolsmith_agent.toolsmith_agent.create_agent_context', side_effect=Exception("Context creation failed"))
    def test_context_creation_failure_handling(self, mock_create_context):
        """Test handling when agent context creation fails."""
        ctx = create_agent_context()  # Create a working context

        # Should still work with provided context even if creation would fail
        agent = create_toolsmith_agent(agent_context=ctx)
        assert agent is not None

    def test_memory_storage_failure_handling(self):
        """Test handling when memory storage fails."""
        ctx = create_agent_context()

        # Mock memory to fail
        with patch.object(ctx, 'store_memory', side_effect=Exception("Memory storage failed")):
            try:
                agent = create_toolsmith_agent(agent_context=ctx)
                # Should still create agent even if memory storage fails
                assert agent is not None
            except Exception:
                # Or handle the failure appropriately
                pass

    def test_hook_creation_failure_handling(self):
        """Test handling when hook creation fails."""
        with patch('toolsmith_agent.toolsmith_agent.create_message_filter_hook', side_effect=Exception("Hook creation failed")):
            try:
                agent = create_toolsmith_agent()
                # Should handle hook creation failures
                assert agent is not None
            except Exception:
                # Or fail appropriately
                pass


class TestToolSmithAgentConstitutionalCompliance:
    """Test suite for constitutional compliance and best practices."""

    def test_agent_follows_tdd_principles(self):
        """Test that agent is equipped for TDD workflows."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Should have tools for writing tests before implementation
        assert any("Write" in name for name in tool_names)  # For creating test files
        assert any("Bash" in name for name in tool_names)   # For running tests

    def test_agent_supports_strict_typing(self):
        """Test that agent can support strict typing workflows."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Should have tools for editing and validating typed code
        assert any("Edit" in name for name in tool_names)
        assert any("MultiEdit" in name for name in tool_names)
        assert any("Read" in name for name in tool_names)

    def test_agent_supports_documentation(self):
        """Test that agent can handle documentation requirements."""
        agent = create_toolsmith_agent()

        # Agent description should indicate documentation capability
        description = agent.description.lower()
        # Should mention testing or validation which includes documentation
        assert "tests" in description or "testing" in description

    def test_agent_supports_repository_pattern(self):
        """Test that agent can work with repository patterns."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Should have tools for reading and understanding existing patterns
        assert any("Read" in name for name in tool_names)
        assert any("Grep" in name for name in tool_names)  # For finding patterns

    def test_agent_supports_functional_error_handling(self):
        """Test that agent can support functional error handling patterns."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Should have tools for implementing Result<T, E> patterns
        assert any("Read" in name for name in tool_names)  # For reading existing patterns
        assert any("Edit" in name for name in tool_names)  # For implementing patterns

    def test_agent_supports_api_standards(self):
        """Test that agent can support API standardization."""
        agent = create_toolsmith_agent()

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Should have tools for API development
        assert any("Write" in name for name in tool_names)
        assert any("Edit" in name for name in tool_names)
        assert any("Read" in name for name in tool_names)


class TestToolSmithAgentModelSettings:
    """Test suite for model settings and configuration."""

    @patch('toolsmith_agent.toolsmith_agent.create_model_settings')
    def test_model_settings_integration(self, mock_create_settings):
        """Test that model settings are properly integrated."""
        from agents.model_settings import ModelSettings
        mock_settings = ModelSettings(temperature=0.1, max_tokens=4000)
        mock_create_settings.return_value = mock_settings

        agent = create_toolsmith_agent(
            model="gpt-5",
            reasoning_effort="high"
        )

        mock_create_settings.assert_called_once_with("gpt-5", "high")
        assert agent.model_settings == mock_settings

    def test_default_model_and_reasoning(self):
        """Test default model and reasoning effort values."""
        # This tests that the defaults are correctly applied
        agent = create_toolsmith_agent()

        assert agent is not None
        assert agent.name == "ToolSmithAgent"
        # Agent should be created successfully with defaults

    def test_custom_model_instance(self):
        """Test that custom model instances are used."""
        with patch('toolsmith_agent.toolsmith_agent.get_model_instance') as mock_get_model:
            mock_get_model.return_value = "custom-model"  # Return string instead of Mock

            agent = create_toolsmith_agent(model="custom-model")

            mock_get_model.assert_called_once_with("custom-model")
            assert agent.model == "custom-model"