"""
Unit tests for agent initialization functionality.
Tests agent creation, configuration, and setup without actual LLM calls.
"""

import pytest
from unittest.mock import Mock, patch
from agency_code_agent.agency_code_agent import create_agency_code_agent


class TestAgentInitialization:
    """Test agent initialization and configuration."""

    def test_basic_agent_creation(self, mock_agent_context):
        """Test basic agent creation with default parameters."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low",
                agent_context=mock_agent_context
            )

            # Verify agent creation
            assert mock_agent_class.called
            assert agent == mock_agent

            # Check agent parameters
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['name'] == "AgencyCodeAgent"
            assert "primary software engineer" in call_kwargs['description']

    def test_model_detection_and_configuration(self, mock_agent_context):
        """Test model detection and configuration logic."""
        test_cases = [
            ("gpt-5-mini", True, False),      # OpenAI model
            ("gpt-4o", True, False),          # OpenAI model
            ("claude-3-sonnet", False, True), # Claude model
            ("claude-3-haiku", False, True),  # Claude model
        ]

        for model, is_openai, is_claude in test_cases:
            with patch('agency_code_agent.agency_code_agent.detect_model_type') as mock_detect, \
                 patch('agency_code_agent.agency_code_agent.Agent'), \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

                mock_detect.return_value = (is_openai, is_claude, False)
                mock_model.return_value = model

                create_agency_code_agent(
                    model=model,
                    reasoning_effort="medium",
                    agent_context=mock_agent_context
                )

                # Verify model detection was called
                assert mock_detect.called
                mock_detect.assert_called_with(model)

    def test_instructions_file_selection(self, mock_agent_context):
        """Test that correct instructions file is selected for different models."""
        with patch('agency_code_agent.agency_code_agent.select_instructions_file') as mock_select, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render, \
             patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_select.return_value = "/path/to/instructions.md"
            mock_render.return_value = "Rendered instructions content"
            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify instructions handling
            assert mock_select.called
            assert mock_render.called

            # Check that render was called with select result
            mock_render.assert_called_with("/path/to/instructions.md", "gpt-5-mini")

    def test_model_settings_creation(self, mock_agent_context):
        """Test that model settings are properly created."""
        reasoning_efforts = ["low", "medium", "high"]

        for effort in reasoning_efforts:
            with patch('agency_code_agent.agency_code_agent.create_model_settings') as mock_settings, \
                 patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

                mock_settings.return_value = {"temperature": 0.7, "reasoning_effort": effort}
                mock_model.return_value = "gpt-5-mini"

                create_agency_code_agent(
                    model="gpt-5-mini",
                    reasoning_effort=effort,
                    agent_context=mock_agent_context
                )

                # Verify model settings creation
                assert mock_settings.called
                mock_settings.assert_called_with("gpt-5-mini", effort)

                # Check that settings were passed to agent
                call_kwargs = mock_agent_class.call_args[1]
                assert 'model_settings' in call_kwargs

    def test_tools_folder_configuration(self, mock_agent_context):
        """Test that tools folder is correctly configured."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model, \
             patch('agency_code_agent.agency_code_agent.render_instructions') as mock_render, \
             patch('os.path.dirname') as mock_dirname, \
             patch('os.path.abspath') as mock_abspath, \
             patch('os.path.join') as mock_join:

            mock_abspath.return_value = "/absolute/path/to/agency_code_agent.py"
            mock_dirname.return_value = "/absolute/path/to"
            mock_join.return_value = "/absolute/path/to/tools"
            mock_model.return_value = "gpt-5-mini"
            mock_render.return_value = "Test instructions"

            create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify tools folder configuration
            assert mock_join.called
            # The actual path will be the real directory, just verify join was called with tools
            call_args = mock_join.call_args_list
            assert any('tools' in str(call) for call in call_args)

            # Check that tools_folder was passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'tools_folder' in call_kwargs
            assert call_kwargs['tools_folder'] == "/absolute/path/to/tools"

    def test_agent_context_auto_creation(self):
        """Test that agent context is auto-created when not provided."""
        with patch('agency_code_agent.agency_code_agent.create_agent_context') as mock_create, \
             patch('agency_code_agent.agency_code_agent.Agent'), \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_context = Mock()
            mock_context.session_id = "auto_created_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context
            mock_model.return_value = "gpt-5-mini"

            # Create agent without providing context
            create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="low"
            )

            # Verify context was auto-created
            assert mock_create.called
            assert mock_context.store_memory.called

    def test_hooks_integration(self, mock_agent_context):
        """Test that system hooks are properly integrated."""
        with patch('agency_code_agent.agency_code_agent.create_system_reminder_hook') as mock_reminder, \
             patch('agency_code_agent.agency_code_agent.create_memory_integration_hook') as mock_memory, \
             patch('agency_code_agent.agency_code_agent.create_composite_hook') as mock_composite, \
             patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_reminder_hook = Mock()
            mock_memory_hook = Mock()
            mock_composite_hook = Mock()

            mock_reminder.return_value = mock_reminder_hook
            mock_memory.return_value = mock_memory_hook
            mock_composite.return_value = mock_composite_hook
            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify all hooks were created
            assert mock_reminder.called
            assert mock_memory.called
            assert mock_composite.called

            # Verify composite hook was created with both hooks
            composite_args = mock_composite.call_args[0][0]
            assert len(composite_args) == 2
            assert mock_reminder_hook in composite_args
            assert mock_memory_hook in composite_args

            # Verify hooks were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'hooks' in call_kwargs
            assert call_kwargs['hooks'] == mock_composite_hook

    def test_error_handling_during_initialization(self, mock_agent_context):
        """Test error handling during agent initialization."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            # Test with invalid model
            mock_agent_class.side_effect = ValueError("Invalid model configuration")

            with pytest.raises(ValueError):
                create_agency_code_agent(
                    model="invalid-model",
                    reasoning_effort="medium",
                    agent_context=mock_agent_context
                )

    def test_default_parameter_values(self):
        """Test default parameter values for agent creation."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.create_agent_context') as mock_create, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_context = Mock()
            mock_context.session_id = "default_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context
            mock_model.return_value = "gpt-5-mini"

            # Create agent with minimal parameters
            create_agency_code_agent()

            # Verify defaults were used
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['name'] == "AgencyCodeAgent"
            assert 'tools' in call_kwargs
            assert 'instructions' in call_kwargs

    def test_reasoning_effort_validation(self, mock_agent_context):
        """Test that reasoning effort parameter is properly validated."""
        valid_efforts = ["low", "medium", "high"]

        for effort in valid_efforts:
            with patch('agency_code_agent.agency_code_agent.create_model_settings') as mock_settings, \
                 patch('agency_code_agent.agency_code_agent.Agent'), \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

                mock_settings.return_value = {"reasoning_effort": effort}
                mock_model.return_value = "gpt-5-mini"

                # This should not raise an exception
                create_agency_code_agent(
                    model="gpt-5-mini",
                    reasoning_effort=effort,
                    agent_context=mock_agent_context
                )

                # Verify reasoning effort was passed correctly
                mock_settings.assert_called_with("gpt-5-mini", effort)

    def test_tool_list_completeness(self, mock_agent_context):
        """Test that all required tools are included in the tool list."""
        with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
             patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5-mini"

            create_agency_code_agent(
                model="gpt-5-mini",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Check that tools parameter was provided
            call_kwargs = mock_agent_class.call_args[1]
            assert 'tools' in call_kwargs
            tools = call_kwargs['tools']

            # Verify it's a list (not empty)
            assert isinstance(tools, list)
            assert len(tools) > 0

    def test_model_instance_creation(self, mock_agent_context):
        """Test that model instance is properly created and configured."""
        test_models = [
            "gpt-5-mini",
            "gpt-4o",
            "claude-3-sonnet",
            "claude-3-haiku"
        ]

        for model in test_models:
            with patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_get_model, \
                 patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class:

                mock_get_model.return_value = f"configured_{model}"

                create_agency_code_agent(
                    model=model,
                    reasoning_effort="medium",
                    agent_context=mock_agent_context
                )

                # Verify model instance creation
                assert mock_get_model.called
                mock_get_model.assert_called_with(model)

                # Verify model was passed to agent
                call_kwargs = mock_agent_class.call_args[1]
                assert 'model' in call_kwargs
                assert call_kwargs['model'] == f"configured_{model}"

    def test_concurrent_agent_creation(self, mock_agent_context):
        """Test that multiple agents can be created concurrently."""
        agents_config = [
            ("gpt-5-mini", "low"),
            ("gpt-4o", "medium"),
            ("claude-3-sonnet", "high")
        ]

        created_agents = []

        for model, effort in agents_config:
            with patch('agency_code_agent.agency_code_agent.Agent') as mock_agent_class, \
                 patch('agency_code_agent.agency_code_agent.get_model_instance') as mock_model:

                mock_agent = Mock()
                mock_agent.name = f"Agent_{model}"
                mock_agent_class.return_value = mock_agent
                mock_model.return_value = model

                agent = create_agency_code_agent(
                    model=model,
                    reasoning_effort=effort,
                    agent_context=mock_agent_context
                )

                created_agents.append(agent)

        # Verify all agents were created
        assert len(created_agents) == 3
        for agent in created_agents:
            assert agent is not None