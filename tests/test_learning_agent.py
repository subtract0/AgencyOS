"""
Comprehensive tests for LearningAgent - Institutional memory curator and pattern recognition specialist.

Tests following the NECESSARY pattern:
- **N**amed clearly with test purpose
- **E**xecutable in isolation
- **C**omprehensive coverage
- **E**rror handling validated
- **S**tate changes verified
- **S**ide effects controlled
- **A**ssertions meaningful
- **R**epeatable results
- **Y**ield fast execution
"""

import os
import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from learning_agent import create_learning_agent
from shared.agent_context import create_agent_context


@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    context = Mock()
    context.session_id = "test_session_learning"
    context.store_memory = Mock()
    context.get_memory = Mock(return_value=None)
    return context


@pytest.fixture
def sample_session_data():
    """Sample session data for learning analysis."""
    return {
        "session_id": "session_123",
        "timestamp": "2024-01-01T12:00:00Z",
        "messages": [
            {"role": "user", "content": "Please implement a fibonacci function"},
            {"role": "assistant", "content": "I'll implement a fibonacci function with tests"},
            {"role": "tool", "tool": "Write", "result": "Created fibonacci.py"},
            {"role": "tool", "tool": "TestValidator", "result": "Tests passing"}
        ],
        "outcomes": {
            "success": True,
            "patterns": ["test_driven_development", "recursive_implementation"],
            "metrics": {"completion_time": 300, "test_coverage": 100}
        }
    }


@pytest.fixture
def sample_telemetry_data():
    """Sample telemetry data for pattern analysis."""
    return [
        {
            "event_type": "error_resolved",
            "timestamp": "2024-01-01T12:00:00Z",
            "agent": "agency_code_agent",
            "error_type": "NoneType",
            "resolution_pattern": "null_check_added",
            "context": {"file": "test.py", "function": "process_data"}
        },
        {
            "event_type": "test_success",
            "timestamp": "2024-01-01T12:05:00Z",
            "agent": "test_generator_agent",
            "test_type": "unit_test",
            "coverage_increase": 15,
            "context": {"module": "fibonacci", "tests_added": 3}
        }
    ]


@pytest.fixture
def temp_session_file():
    """Create a temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        session_data = {
            "session_id": "test_session",
            "messages": [
                {"role": "user", "content": "Test message"},
                {"role": "assistant", "content": "Test response"}
            ]
        }
        json.dump(session_data, f)
        f.flush()
        yield f.name
    os.unlink(f.name)


class TestLearningAgentInitialization:
    """Test LearningAgent initialization and configuration."""

    def test_agent_creation_with_defaults(self):
        """Test agent creation with default parameters."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.create_agent_context') as mock_create_context:

            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()
            mock_create_context.return_value = mock_context

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_learning_agent()

            # Verify agent creation
            assert mock_agent_class.called
            assert agent == mock_agent

            # Check agent parameters
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs['name'] == "LearningAgent"
            assert "institutional memory curator" in call_kwargs['description']
            assert "pattern recognition specialist" in call_kwargs['description']

    def test_agent_creation_with_custom_parameters(self, mock_agent_context):
        """Test agent creation with custom parameters."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance') as mock_model, \
             patch('learning_agent.learning_agent.create_model_settings') as mock_settings:

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_model.return_value = "claude-3-sonnet"
            from agents.model_settings import ModelSettings
            mock_settings.return_value = ModelSettings(temperature=0.3)

            agent = create_learning_agent(
                model="claude-3-sonnet",
                reasoning_effort="medium",
                agent_context=mock_agent_context
            )

            # Verify agent creation with custom parameters
            assert mock_agent_class.called
            assert agent == mock_agent

            # Verify custom model was used
            assert mock_model.called
            mock_model.assert_called_with("claude-3-sonnet")

            # Verify custom settings were applied
            assert mock_settings.called
            mock_settings.assert_called_with("claude-3-sonnet", "medium")

    def test_agent_tools_configuration(self, mock_agent_context):
        """Test that agent has all required learning tools configured."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            # Check tools were provided
            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs['tools']

            # Verify core learning tools are present
            tool_classes = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in tools]
            expected_learning_tools = [
                'AnalyzeSession',
                'ExtractInsights',
                'ConsolidateLearning',
                'StoreKnowledge',
                'TelemetryPatternAnalyzer',
                'SelfHealingPatternExtractor',
                'CrossSessionLearner'
            ]

            for expected_tool in expected_learning_tools:
                assert any(expected_tool in tool_class for tool_class in tool_classes)

    def test_agent_memory_integration(self, mock_agent_context):
        """Test that agent properly integrates with memory system."""
        with patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            create_learning_agent(agent_context=mock_agent_context)

            # Verify memory integration was set up
            assert mock_agent_context.store_memory.called

            # Check that agent creation was logged
            call_args = mock_agent_context.store_memory.call_args[0]
            assert "agent_created" in call_args[0]
            assert call_args[1]["agent_type"] == "LearningAgent"

    def test_instructions_file_selection(self, mock_agent_context):
        """Test that correct instructions file is selected."""
        with patch('learning_agent.learning_agent.select_instructions_file') as mock_select, \
             patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_select.return_value = "/path/to/instructions-gpt-5.md"
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(model="gpt-5", agent_context=mock_agent_context)

            # Verify instructions selection was called
            assert mock_select.called
            # Verify agent received instructions
            call_kwargs = mock_agent_class.call_args[1]
            assert 'instructions' in call_kwargs

    def test_hooks_integration(self, mock_agent_context):
        """Test that system hooks are properly integrated."""
        with patch('learning_agent.learning_agent.create_message_filter_hook') as mock_filter, \
             patch('learning_agent.learning_agent.create_memory_integration_hook') as mock_memory, \
             patch('learning_agent.learning_agent.create_composite_hook') as mock_composite, \
             patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_filter_hook = Mock()
            mock_memory_hook = Mock()
            mock_composite_hook = Mock()

            mock_filter.return_value = mock_filter_hook
            mock_memory.return_value = mock_memory_hook
            mock_composite.return_value = mock_composite_hook

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            # Verify all hooks were created
            assert mock_filter.called
            assert mock_memory.called
            assert mock_composite.called

            # Verify composite hook was created with both hooks
            composite_args = mock_composite.call_args[0][0]
            assert len(composite_args) == 2
            assert mock_filter_hook in composite_args
            assert mock_memory_hook in composite_args

            # Verify hooks were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'hooks' in call_kwargs
            assert call_kwargs['hooks'] == mock_composite_hook


class TestLearningAgentSessionAnalysis:
    """Test learning agent session analysis capabilities."""

    def test_agent_description_capabilities(self, mock_agent_context):
        """Test that agent description captures learning capabilities."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs['description']

            # Verify key learning capabilities are described
            assert "institutional memory curator" in description
            assert "pattern recognition specialist" in description
            assert "successful task completions" in description
            assert "error resolutions" in description
            assert "logs/sessions/" in description
            assert "VectorStore" in description
            assert "collective intelligence" in description

    def test_learning_triggers_described(self, mock_agent_context):
        """Test that learning triggers are properly described."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs['description']

            # Verify learning triggers are described
            assert "Proactively triggered" in description
            assert "task completions" in description
            assert "error resolutions" in description
            assert "session end" in description

    def test_learning_outputs_described(self, mock_agent_context):
        """Test that learning outputs are properly described."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs['description']

            # Verify learning outputs are described
            assert "reusable patterns" in description
            assert "successful strategies" in description
            assert "common pitfalls" in description
            assert "consolidated knowledge" in description
            assert "institutional memory" in description


class TestLearningAgentToolIntegration:
    """Test learning agent tool integration and functionality."""

    def test_basic_tool_availability(self, mock_agent_context):
        """Test that all basic tools are available to learning agent."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs['tools']

            # Verify basic tools are present
            tool_classes = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in tools]
            basic_tools = ['LS', 'Read', 'Grep', 'Glob', 'TodoWrite']

            for basic_tool in basic_tools:
                assert any(basic_tool in tool_class for tool_class in tool_classes)

    def test_specialized_learning_tools(self, mock_agent_context):
        """Test that specialized learning tools are available."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs['tools']

            # Verify specialized learning tools
            tool_classes = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in tools]
            specialized_tools = [
                'AnalyzeSession',
                'ExtractInsights',
                'ConsolidateLearning',
                'StoreKnowledge',
                'TelemetryPatternAnalyzer',
                'SelfHealingPatternExtractor',
                'CrossSessionLearner'
            ]

            for specialized_tool in specialized_tools:
                assert any(specialized_tool in tool_class for tool_class in tool_classes)

    def test_tool_integration_with_context(self, mock_agent_context):
        """Test that tools are properly integrated with agent context."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            # Verify agent was created (tools will be validated by Agency framework)
            assert mock_agent_class.called

    def test_model_settings_for_learning(self, mock_agent_context):
        """Test that appropriate model settings are used for learning tasks."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance') as mock_model, \
             patch('learning_agent.learning_agent.create_model_settings') as mock_settings:

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_model.return_value = "gpt-5"
            from agents.model_settings import ModelSettings
            mock_settings.return_value = ModelSettings(temperature=0.7)

            create_learning_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify model settings were created for learning
            assert mock_settings.called
            mock_settings.assert_called_with("gpt-5", "high")

            # Verify settings were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert 'model_settings' in call_kwargs


class TestLearningAgentErrorHandling:
    """Test learning agent error handling and edge cases."""

    def test_agent_creation_with_invalid_model(self):
        """Test error handling with invalid model."""
        with patch('learning_agent.learning_agent.get_model_instance') as mock_model:
            mock_model.side_effect = ValueError("Invalid model")

            with pytest.raises(ValueError):
                create_learning_agent(model="invalid-model")

    def test_agent_creation_without_context(self):
        """Test that agent context is auto-created when not provided."""
        with patch('learning_agent.learning_agent.create_agent_context') as mock_create, \
             patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_context = Mock()
            mock_context.session_id = "auto_created"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            agent = create_learning_agent()

            # Verify context was auto-created
            assert mock_create.called
            assert agent == mock_agent

    def test_hook_creation_failure_handling(self, mock_agent_context):
        """Test handling of hook creation failures."""
        with patch('learning_agent.learning_agent.create_message_filter_hook') as mock_filter, \
             patch('learning_agent.learning_agent.create_memory_integration_hook') as mock_memory, \
             patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_filter.side_effect = Exception("Hook creation failed")

            with pytest.raises(Exception):
                create_learning_agent(agent_context=mock_agent_context)

    def test_instructions_file_fallback(self, mock_agent_context):
        """Test fallback when instructions file is not found."""
        with patch('learning_agent.learning_agent.select_instructions_file') as mock_select, \
             patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_select.side_effect = FileNotFoundError("Instructions not found")
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            # Should handle missing instructions gracefully
            agent = create_learning_agent(agent_context=mock_agent_context)
            assert agent is not None


class TestLearningAgentMemoryIntegration:
    """Test learning agent memory integration functionality."""

    def test_memory_logging_on_creation(self, mock_agent_context):
        """Test that agent creation is properly logged to memory."""
        with patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            create_learning_agent(
                model="gpt-5",
                reasoning_effort="high",
                agent_context=mock_agent_context
            )

            # Verify memory was logged
            assert mock_agent_context.store_memory.called

            # Check logged content
            call_args = mock_agent_context.store_memory.call_args
            memory_key = call_args[0][0]
            memory_data = call_args[0][1]
            memory_tags = call_args[0][2]

            assert "agent_created" in memory_key
            assert memory_data["agent_type"] == "LearningAgent"
            assert memory_data["model"] == "gpt-5"
            assert memory_data["reasoning_effort"] == "high"
            assert "agency" in memory_tags
            assert "learning" in memory_tags
            assert "creation" in memory_tags

    def test_memory_context_integration(self, mock_agent_context):
        """Test that memory context is properly integrated."""
        with patch('learning_agent.learning_agent.create_memory_integration_hook') as mock_memory_hook, \
             patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            create_learning_agent(agent_context=mock_agent_context)

            # Verify memory hook was created with context
            assert mock_memory_hook.called
            mock_memory_hook.assert_called_with(mock_agent_context)

    def test_session_id_propagation(self, mock_agent_context):
        """Test that session ID is properly propagated."""
        with patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent_context.session_id = "test_session_12345"

            create_learning_agent(agent_context=mock_agent_context)

            # Verify session ID was used in memory logging
            call_args = mock_agent_context.store_memory.call_args
            memory_data = call_args[0][1]
            assert memory_data["session_id"] == "test_session_12345"

    def test_memory_integration_with_auto_context(self):
        """Test memory integration when context is auto-created."""
        with patch('learning_agent.learning_agent.create_agent_context') as mock_create, \
             patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_context = Mock()
            mock_context.session_id = "auto_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context

            create_learning_agent()

            # Verify auto-created context was used for memory
            assert mock_context.store_memory.called


class TestLearningAgentFactoryPattern:
    """Test learning agent factory pattern and singleton avoidance."""

    def test_factory_returns_fresh_instance(self):
        """Test that factory returns fresh agent instances."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.create_agent_context'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent1 = Mock()
            mock_agent2 = Mock()
            mock_agent_class.side_effect = [mock_agent1, mock_agent2]

            agent1 = create_learning_agent()
            agent2 = create_learning_agent()

            # Verify different instances were created
            assert agent1 != agent2
            assert mock_agent_class.call_count == 2

    def test_factory_with_different_contexts(self):
        """Test factory with different agent contexts."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            context1 = Mock()
            context1.session_id = "session_1"
            context1.store_memory = Mock()

            context2 = Mock()
            context2.session_id = "session_2"
            context2.store_memory = Mock()

            mock_agent1 = Mock()
            mock_agent2 = Mock()
            mock_agent_class.side_effect = [mock_agent1, mock_agent2]

            agent1 = create_learning_agent(agent_context=context1)
            agent2 = create_learning_agent(agent_context=context2)

            # Verify both contexts were used
            assert context1.store_memory.called
            assert context2.store_memory.called
            assert agent1 != agent2

    def test_factory_parameter_combinations(self):
        """Test factory with various parameter combinations."""
        test_cases = [
            {"model": "gpt-5", "reasoning_effort": "low"},
            {"model": "gpt-4o", "reasoning_effort": "medium"},
            {"model": "claude-3-sonnet", "reasoning_effort": "high"},
        ]

        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.create_agent_context'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            for i, params in enumerate(test_cases):
                mock_agent = Mock()
                mock_agent.name = f"LearningAgent_{i}"
                mock_agent_class.return_value = mock_agent

                agent = create_learning_agent(**params)
                assert agent is not None

    def test_no_module_level_singleton(self):
        """Test that no singleton is created at module level."""
        # This test verifies the comment in the module about avoiding singletons
        import learning_agent

        # Check that no agent instance is created at module level
        module_attrs = [attr for attr in dir(learning_agent)
                       if not attr.startswith('_') and not callable(getattr(learning_agent, attr))]

        # Should only have imports, no agent instances
        assert 'create_learning_agent' in dir(learning_agent)
        # Should not have a pre-created agent instance
        assert not any('agent' in attr.lower() and not attr.endswith('_agent')
                      for attr in module_attrs)


class TestLearningAgentConstitutionalCompliance:
    """Test learning agent constitutional compliance."""

    def test_agent_supports_continuous_learning_article_iv(self, mock_agent_context):
        """Test agent supports Article IV (Continuous Learning)."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            # Verify agent has learning tools for Article IV compliance
            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs['tools']
            tool_classes = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in tools]

            # Should have pattern learning and knowledge storage tools
            learning_tools = ['ExtractInsights', 'ConsolidateLearning', 'StoreKnowledge']
            for tool in learning_tools:
                assert any(tool in tool_class for tool_class in tool_classes)

    def test_agent_description_mentions_collective_intelligence(self, mock_agent_context):
        """Test that agent description emphasizes collective intelligence."""
        with patch('learning_agent.learning_agent.Agent') as mock_agent_class, \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_learning_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs['description']

            # Verify collective intelligence aspects
            assert "collective intelligence" in description
            assert "institutional memory" in description
            assert "agency performance" in description

    def test_agent_memory_integration_supports_learning(self, mock_agent_context):
        """Test that memory integration supports learning objectives."""
        with patch('learning_agent.learning_agent.Agent'), \
             patch('learning_agent.learning_agent.get_model_instance'), \
             patch('learning_agent.learning_agent.create_model_settings'):

            create_learning_agent(agent_context=mock_agent_context)

            # Verify memory logging includes learning tags
            call_args = mock_agent_context.store_memory.call_args
            memory_tags = call_args[0][2]
            assert "learning" in memory_tags
            assert "agency" in memory_tags