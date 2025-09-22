"""
Unit tests for ChiefArchitectAgent initialization and configuration.
Tests agent creation, tool setup, and hook integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from chief_architect_agent.chief_architect_agent import create_chief_architect_agent


class TestChiefArchitectAgentInitialization:
    """Test ChiefArchitectAgent creation and configuration."""

    def test_basic_agent_creation(self, mock_agent_context):
        """Test basic agent creation with default parameters."""
        with patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5"
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify agent creation
            assert mock_agent_class.called
            assert agent == mock_agent

            # Check agent parameters
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['name'] == "ChiefArchitectAgent"
            assert "autonomous strategic leader" in call_kwargs['description']
            assert "RunArchitectureLoop" in call_kwargs['description']

    def test_model_configuration(self, mock_agent_context):
        """Test model configuration with different model types."""
        test_cases = [
            ("gpt-5", "high"),
            ("gpt-4o", "medium"),
            ("claude-3-sonnet", "low"),
        ]

        for model, effort in test_cases:
            with patch('chief_architect_agent.chief_architect_agent.Agent'), \
                 patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model, \
                 patch('chief_architect_agent.chief_architect_agent.create_model_settings') as mock_settings:

                mock_model.return_value = model
                mock_settings.return_value = {"reasoning_effort": effort}

                create_chief_architect_agent(
                    model=model,
                    reasoning_effort=effort,
                    agent_context=mock_agent_context
                )

                # Verify model settings creation
                mock_settings.assert_called_with(model, effort)
                mock_model.assert_called_with(model)

    def test_tool_configuration(self, mock_agent_context):
        """Test that all required tools are configured."""
        with patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5"

            create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Check tools configuration
            call_kwargs = mock_agent_class.call_args[1]
            assert 'tools' in call_kwargs
            tools = call_kwargs['tools']

            # Verify tool names (checking types as strings since they're imported)
            tool_names = [str(tool) for tool in tools]
            assert len(tools) == 9  # LS, Read, Grep, Glob, TodoWrite, Write, Edit, Bash, RunArchitectureLoop

            # Verify RunArchitectureLoop is included
            assert any('RunArchitectureLoop' in str(tool.__name__) if hasattr(tool, '__name__') else False
                      for tool in tools)

    def test_hooks_integration(self, mock_agent_context):
        """Test that all system hooks are properly integrated."""
        with patch('chief_architect_agent.chief_architect_agent.create_message_filter_hook') as mock_filter, \
             patch('chief_architect_agent.chief_architect_agent.create_memory_integration_hook') as mock_memory, \
             patch('chief_architect_agent.chief_architect_agent.create_composite_hook') as mock_composite, \
             patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            # Setup hook mocks
            filter_hook = Mock(name='filter_hook')
            memory_hook = Mock(name='memory_hook')
            composite_hook = Mock(name='composite_hook')

            mock_filter.return_value = filter_hook
            mock_memory.return_value = memory_hook
            mock_composite.return_value = composite_hook
            mock_model.return_value = "gpt-5"

            create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify hooks were created
            assert mock_filter.called
            assert mock_memory.called
            assert mock_composite.called

            # Verify composite hook was created with correct hooks
            composite_args = mock_composite.call_args[0][0]
            assert len(composite_args) == 2
            assert filter_hook in composite_args
            assert memory_hook in composite_args

            # Verify hooks were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'hooks' in call_kwargs
            assert call_kwargs['hooks'] == composite_hook

    def test_memory_storage(self, mock_agent_context):
        """Test that agent creation is stored in memory."""
        with patch('chief_architect_agent.chief_architect_agent.Agent'), \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5"

            create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify memory storage was called
            assert mock_agent_context.store_memory.called

            # Check memory storage parameters
            call_args = mock_agent_context.store_memory.call_args
            memory_key = call_args[0][0]
            memory_data = call_args[0][1]
            memory_tags = call_args[0][2]

            assert f"agent_created_{mock_agent_context.session_id}" == memory_key
            assert memory_data['agent_type'] == "ChiefArchitectAgent"
            assert memory_data['model'] == "gpt-5"
            assert memory_data['reasoning_effort'] == "high"
            assert memory_data['session_id'] == mock_agent_context.session_id
            assert memory_tags == ["agency", "chief_architect", "creation"]

    def test_auto_context_creation(self):
        """Test that agent context is auto-created when not provided."""
        with patch('chief_architect_agent.chief_architect_agent.create_agent_context') as mock_create, \
             patch('chief_architect_agent.chief_architect_agent.Agent'), \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_context = Mock()
            mock_context.session_id = "auto_created_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context
            mock_model.return_value = "gpt-5"

            # Create agent without providing context
            create_chief_architect_agent(model="gpt-5")

            # Verify context was auto-created
            assert mock_create.called
            assert mock_context.store_memory.called

    def test_instructions_file_selection(self, mock_agent_context):
        """Test that correct instructions file is selected."""
        with patch('chief_architect_agent.chief_architect_agent.select_instructions_file') as mock_select, \
             patch('chief_architect_agent.chief_architect_agent.Agent'), \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_select.return_value = "/path/to/instructions.md"
            mock_model.return_value = "gpt-5"

            create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify instructions file selection
            assert mock_select.called
            # Just verify it was called with the model, don't check the path
            call_args = mock_select.call_args[0]
            assert call_args[1] == "gpt-5"

    def test_tools_folder_configuration(self, mock_agent_context):
        """Test that tools folder is correctly configured."""
        with patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model, \
             patch('os.path.join') as mock_join:

            mock_join.return_value = "/path/to/chief_architect_agent/tools"
            mock_model.return_value = "gpt-5"

            create_chief_architect_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Check that tools_folder was passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'tools_folder' in call_kwargs

            # Verify join was called to create tools path
            assert mock_join.called

    def test_default_parameters(self):
        """Test agent creation with default parameters."""
        with patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.create_agent_context') as mock_create, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_context = Mock()
            mock_context.session_id = "default_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context
            mock_model.return_value = "gpt-5"

            # Create with defaults
            create_chief_architect_agent()

            # Verify defaults were used
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['name'] == "ChiefArchitectAgent"

            # Check model settings defaults
            memory_call = mock_context.store_memory.call_args[0][1]
            assert memory_call['model'] == "gpt-5"
            assert memory_call['reasoning_effort'] == "high"

    def test_error_handling(self, mock_agent_context):
        """Test error handling during agent initialization."""
        with patch('chief_architect_agent.chief_architect_agent.Agent') as mock_agent_class, \
             patch('chief_architect_agent.chief_architect_agent.get_model_instance') as mock_model:

            mock_model.return_value = "gpt-5"
            mock_agent_class.side_effect = ValueError("Invalid configuration")

            with pytest.raises(ValueError):
                create_chief_architect_agent(
                    model="invalid-model",
                    reasoning_effort="high",
                    agent_context=mock_agent_context
                )