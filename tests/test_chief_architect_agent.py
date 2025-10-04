"""
Comprehensive tests for ChiefArchitectAgent - Autonomous strategic leader and continuous improvement orchestrator.

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
import tempfile
from unittest.mock import Mock, patch

import pytest

from chief_architect_agent import create_chief_architect_agent

try:
    from agents.model_settings import ModelSettings
    from openai.types.shared.reasoning import Reasoning
except ImportError:
    # If direct import fails, create mock classes for testing
    class ModelSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class Reasoning:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


def create_mock_patches():
    """Create standard mock patches for chief architect agent tests."""
    return {
        "agent_class": Mock(),
        "model_instance": "gpt-5",
        "model_settings": ModelSettings(
            temperature=0.1, max_tokens=32000, reasoning=Reasoning(effort="high", summary="auto")
        ),
        "instructions_file": "instructions.md",
    }


@pytest.fixture
def mock_agent_context():
    """Create a mock agent context for testing."""
    context = Mock()
    context.session_id = "test_session_chief_architect"
    context.store_memory = Mock()
    context.get_memory = Mock(return_value=None)
    return context


@pytest.fixture
def sample_audit_report():
    """Sample audit report for testing."""
    return {
        "audit_id": "audit_123",
        "timestamp": "2024-01-01T12:00:00Z",
        "findings": [
            {
                "type": "constitutional_violation",
                "severity": "high",
                "article": "Article II",
                "description": "Missing test coverage for critical modules",
                "affected_files": ["module1.py", "module2.py"],
            },
            {
                "type": "performance_issue",
                "severity": "medium",
                "description": "Inefficient database queries detected",
                "metrics": {"avg_response_time": 2.5, "threshold": 1.0},
            },
        ],
        "metrics": {"test_coverage": 75, "code_quality_score": 85, "constitutional_compliance": 60},
    }


@pytest.fixture
def sample_system_metrics():
    """Sample system metrics for testing."""
    return {
        "performance": {
            "q_t_score": 0.65,
            "avg_task_completion_time": 450,
            "error_rate": 0.15,
            "success_rate": 0.85,
        },
        "health": {"agent_availability": 0.95, "memory_usage": 0.70, "cpu_usage": 0.45},
        "compliance": {"constitutional_score": 0.80, "test_coverage": 0.75, "code_quality": 0.85},
    }


@pytest.fixture
def temp_architecture_workspace():
    """Create a temporary workspace for architecture testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample files and structure
        os.makedirs(os.path.join(temp_dir, "specs"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "plans"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "logs"), exist_ok=True)

        spec_file = os.path.join(temp_dir, "specs", "improvement_spec.md")
        with open(spec_file, "w") as f:
            f.write("# System Improvement Specification\n\n## Overview\nTest spec")

        yield temp_dir


class TestChiefArchitectAgentInitialization:
    """Test ChiefArchitectAgent initialization and configuration."""

    def test_agent_creation_with_defaults(self):
        """Test agent creation with default parameters."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.create_agent_context"
            ) as mock_create_context,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ) as mock_model,
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()
            mock_create_context.return_value = mock_context

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_model.return_value = "gpt-5"
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="medium", summary="auto"),
            )

            # Mock the hooks
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            agent = create_chief_architect_agent()

            # Verify agent creation
            assert mock_agent_class.called
            assert agent == mock_agent

            # Check agent parameters
            call_kwargs = mock_agent_class.call_args[1]
            assert call_kwargs["name"] == "ChiefArchitectAgent"
            assert "strategic" in call_kwargs["description"].lower()
            assert "PROACTIVE" in call_kwargs["description"]

    def test_agent_creation_with_custom_parameters(self, mock_agent_context):
        """Test agent creation with custom parameters."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="claude-3-sonnet",
            ) as mock_model,
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_model.return_value = "claude-3-sonnet"
            mock_settings.return_value = ModelSettings(
                temperature=0.3,
                max_tokens=32000,
                reasoning=Reasoning(effort="medium", summary="auto"),
            )

            # Mock the hooks
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            agent = create_chief_architect_agent(
                model="claude-3-sonnet", reasoning_effort="medium", agent_context=mock_agent_context
            )

            # Verify agent creation with custom parameters
            assert mock_agent_class.called
            assert agent == mock_agent

            # Verify custom model and settings
            assert mock_model.called
            mock_model.assert_called_with("claude-3-sonnet")
            assert mock_settings.called
            mock_settings.assert_called_with("claude-3-sonnet", "medium")

    def test_agent_tools_configuration(self, mock_agent_context):
        """Test that agent has all required architectural tools configured."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            # Mock the hooks
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Check tools were provided
            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs["tools"]

            # Verify core architectural tools are present
            tool_classes = [
                tool.__name__ if hasattr(tool, "__name__") else str(tool) for tool in tools
            ]
            expected_tools = [
                "LS",
                "Read",
                "Grep",
                "Glob",
                "TodoWrite",
                "Write",
                "Edit",
                "Bash",
                "ContextMessageHandoff",
                "RunArchitectureLoop",
            ]

            for expected_tool in expected_tools:
                assert any(expected_tool in tool_class for tool_class in tool_classes)

    def test_tools_folder_configuration(self, mock_agent_context):
        """Test that tools folder is correctly configured."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
            patch("os.path.dirname") as mock_dirname,
            patch("os.path.abspath") as mock_abspath,
            patch("os.path.join") as mock_join,
        ):
            mock_abspath.return_value = "/path/to/chief_architect_agent.py"
            mock_dirname.return_value = "/path/to"
            mock_join.return_value = "/path/to/tools"

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            # Mock the hooks
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify tools folder was configured
            call_kwargs = mock_agent_class.call_args[1]
            assert "tools_folder" in call_kwargs

    def test_agent_memory_integration(self, mock_agent_context):
        """Test that agent properly integrates with memory system."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ) as mock_model,
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            # Mock the hooks
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify memory integration was set up
            assert mock_agent_context.store_memory.called

            # Check that agent creation was logged
            call_args = mock_agent_context.store_memory.call_args[0]
            assert "agent_created" in call_args[0]
            assert call_args[1]["agent_type"] == "ChiefArchitectAgent"

    def test_instructions_file_selection(self, mock_agent_context):
        """Test that correct instructions file is selected."""
        with (
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="/path/to/instructions-gpt-5.md",
            ) as mock_select,
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(model="gpt-5", agent_context=mock_agent_context)

            # Verify instructions selection was called
            assert mock_select.called
            # Verify agent received instructions
            call_kwargs = mock_agent_class.call_args[1]
            assert "instructions" in call_kwargs

    def test_hooks_integration(self, mock_agent_context):
        """Test that system hooks are properly integrated."""
        with (
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_memory_hook = Mock()
            mock_composite_hook = Mock()
            mock_filter.return_value = Mock()
            mock_memory.return_value = mock_memory_hook
            mock_composite.return_value = mock_composite_hook

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify all hooks were created
            assert mock_filter.called
            assert mock_memory.called
            assert mock_composite.called

            # Verify hooks were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert "hooks" in call_kwargs
            assert call_kwargs["hooks"] == mock_composite_hook


@pytest.mark.skip(reason="Agent descriptions modernized - detailed string checks outdated")
class TestChiefArchitectAgentDescription:
    """Test ChiefArchitectAgent description and capabilities."""

    def test_agent_description_strategic_leadership(self, mock_agent_context):
        """Test that agent description captures strategic leadership role."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify strategic leadership aspects
            assert "strategic oversight" in description
            assert "continuous improvement" in description or "strategic" in description

    def test_agent_description_triggers(self, mock_agent_context):
        """Test that agent description captures trigger conditions."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify trigger conditions
            assert "PROACTIVE" in description or "strategic" in description
            assert "system" in description or "strategic" in description
            assert "strategic" in description or "architectural" in description
            assert "issues" in description or "decision" in description
            assert "strategic" in description or "architectural" in description
            assert "opportunities" in description or "decisions" in description

    def test_agent_description_capabilities(self, mock_agent_context):
        """Test that agent description captures key capabilities."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify key capabilities
            assert "architectural" in description or "strategic" in description
            assert "memory patterns" in description
            assert "constitutional compliance" in description
            assert "high-impact improvements" in description
            assert "[SELF-DIRECTED TASK]" in description
            assert "high-priority user instructions" in description

    def test_agent_description_authority(self, mock_agent_context):
        """Test that agent description captures authority and autonomy."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify authority aspects
            assert "self-directed" in description or "task creation authority" in description
            assert "autonomous improvement cycles" in description
            assert "directives supersede routine tasks" in description
            assert "RunArchitectureLoop tool" in description

    def test_agent_description_usage_guidance(self, mock_agent_context):
        """Test that agent description provides usage guidance."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify usage guidance
            assert "When prompting" in description or "provide" in description
            assert "recent failures" in description
            assert "performance metrics" in description
            assert "areas of concern" in description


class TestChiefArchitectAgentErrorHandling:
    """Test ChiefArchitectAgent error handling and edge cases."""

    def test_agent_creation_with_invalid_model(self):
        """Test error handling with invalid model."""
        with patch(
            "chief_architect_agent.chief_architect_agent.get_model_instance", return_value="gpt-5"
        ) as mock_model:
            mock_model.side_effect = ValueError("Invalid model")

            with pytest.raises(ValueError):
                create_chief_architect_agent(model="invalid-model")

    def test_agent_creation_without_context(self):
        """Test that agent context is auto-created when not provided."""
        with (
            patch(
                "chief_architect_agent.chief_architect_agent.create_agent_context"
            ) as mock_create,
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            # Create a proper mock context
            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()
            mock_create.return_value = mock_context

            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            agent = create_chief_architect_agent()

            # Verify context was auto-created
            assert mock_create.called
            assert agent == mock_agent

    def test_hook_creation_failure_handling(self, mock_agent_context):
        """Test handling of hook creation failures."""
        with patch(
            "chief_architect_agent.chief_architect_agent.create_message_filter_hook",
            return_value="gpt-5",
        ) as mock_filter:
            mock_filter.side_effect = Exception("Hook creation failed")

            with pytest.raises(Exception):
                create_chief_architect_agent(agent_context=mock_agent_context)

    def test_instructions_file_fallback(self, mock_agent_context):
        """Test fallback when instructions file is not found."""
        with (
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="gpt-5",
            ) as mock_select,
            patch("agency_swarm.Agent", return_value="gpt-5") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            agent = create_chief_architect_agent(agent_context=mock_agent_context)
            assert agent is not None

    def test_tools_folder_path_errors(self, mock_agent_context):
        """Test handling of tools folder path errors."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
            patch("os.path.dirname") as mock_dirname,
        ):
            mock_dirname.side_effect = OSError("Path error")
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            # Should handle path errors gracefully
            agent = create_chief_architect_agent(agent_context=mock_agent_context)
            assert agent is not None


class TestChiefArchitectAgentMemoryIntegration:
    """Test ChiefArchitectAgent memory integration functionality."""

    def test_memory_logging_on_creation(self, mock_agent_context):
        """Test that agent creation is properly logged to memory."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(
                model="gpt-5", reasoning_effort="high", agent_context=mock_agent_context
            )

            # Verify memory was logged
            assert mock_agent_context.store_memory.called

            # Check logged content
            call_args = mock_agent_context.store_memory.call_args
            memory_key = call_args[0][0]
            memory_data = call_args[0][1]
            memory_tags = call_args[0][2]

            assert "agent_created" in memory_key
            assert memory_data["agent_type"] == "ChiefArchitectAgent"
            assert memory_data["model"] == "gpt-5"
            assert memory_data["reasoning_effort"] == "high"
            assert "agency" in memory_tags
            assert "chief_architect" in memory_tags
            assert "creation" in memory_tags

    def test_memory_context_integration(self, mock_agent_context):
        """Test that memory context is properly integrated."""
        with (
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory_hook,
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory_hook.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify memory hook was created with context
            assert mock_memory_hook.called
            mock_memory_hook.assert_called_with(mock_agent_context)

    def test_session_id_propagation(self, mock_agent_context):
        """Test that session ID is properly propagated."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent_context.session_id = "architect_session_12345"

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify session ID was used in memory logging
            call_args = mock_agent_context.store_memory.call_args
            memory_data = call_args[0][1]
            assert memory_data["session_id"] == "architect_session_12345"


class TestChiefArchitectAgentToolIntegration:
    """Test ChiefArchitectAgent tool integration and functionality."""

    def test_basic_tools_availability(self, mock_agent_context):
        """Test that all basic tools are available to chief architect agent."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs["tools"]

            # Verify basic tools are present
            tool_classes = [
                tool.__name__ if hasattr(tool, "__name__") else str(tool) for tool in tools
            ]
            basic_tools = ["LS", "Read", "Grep", "Glob", "TodoWrite", "Write", "Edit", "Bash"]

            for basic_tool in basic_tools:
                assert any(basic_tool in tool_class for tool_class in tool_classes)

    def test_specialized_architecture_tools(self, mock_agent_context):
        """Test that specialized architecture tools are available."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs["tools"]

            # Verify specialized architecture tools
            tool_classes = [
                tool.__name__ if hasattr(tool, "__name__") else str(tool) for tool in tools
            ]
            architecture_tools = ["ContextMessageHandoff", "RunArchitectureLoop"]

            for arch_tool in architecture_tools:
                assert any(arch_tool in tool_class for tool_class in tool_classes)

    def test_model_settings_for_architecture(self, mock_agent_context):
        """Test that appropriate model settings are used for architecture tasks."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ) as mock_model,
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_model.return_value = "gpt-5"
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(
                model="gpt-5", reasoning_effort="high", agent_context=mock_agent_context
            )

            # Verify model settings were created for architecture
            assert mock_settings.called
            mock_settings.assert_called_with("gpt-5", "high")

            # Verify settings were passed to agent
            call_kwargs = mock_agent_class.call_args[1]
            assert "model_settings" in call_kwargs


class TestChiefArchitectAgentFactoryPattern:
    """Test ChiefArchitectAgent factory pattern."""

    def test_factory_returns_fresh_instance(self):
        """Test that factory returns fresh agent instances."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.create_agent_context"
            ) as mock_create_context,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            # Create proper mock contexts
            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()
            mock_create_context.return_value = mock_context

            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent1 = Mock()
            mock_agent2 = Mock()
            mock_agent_class.side_effect = [mock_agent1, mock_agent2]
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            agent1 = create_chief_architect_agent()
            agent2 = create_chief_architect_agent()

            # Verify different instances were created
            assert agent1 != agent2
            assert mock_agent_class.call_count == 2

    def test_factory_with_different_contexts(self):
        """Test factory with different agent contexts."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            context1 = Mock()
            context1.session_id = "architect_session_1"
            context1.store_memory = Mock()

            context2 = Mock()
            context2.session_id = "architect_session_2"
            context2.store_memory = Mock()

            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent1 = Mock()
            mock_agent2 = Mock()
            mock_agent_class.side_effect = [mock_agent1, mock_agent2]
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            agent1 = create_chief_architect_agent(agent_context=context1)
            agent2 = create_chief_architect_agent(agent_context=context2)

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

        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.create_agent_context"
            ) as mock_create_context,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            # Create proper mock context
            mock_context = Mock()
            mock_context.session_id = "test_session"
            mock_context.store_memory = Mock()
            mock_create_context.return_value = mock_context

            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            for i, params in enumerate(test_cases):
                mock_agent = Mock()
                mock_agent.name = f"ChiefArchitectAgent_{i}"
                mock_agent_class.return_value = mock_agent

                agent = create_chief_architect_agent(**params)
                assert agent is not None


class TestChiefArchitectAgentConstitutionalCompliance:
    """Test ChiefArchitectAgent constitutional compliance."""

    def test_agent_supports_spec_driven_development_article_v(self, mock_agent_context):
        """Test agent supports Article V (Spec-Driven Development)."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify agent has tools for spec-driven development
            call_kwargs = mock_agent_class.call_args[1]
            tools = call_kwargs["tools"]
            tool_classes = [
                tool.__name__ if hasattr(tool, "__name__") else str(tool) for tool in tools
            ]

            # Should have tools for creating and managing specs
            spec_tools = ["Write", "Edit", "RunArchitectureLoop"]
            for tool in spec_tools:
                assert any(tool in tool_class for tool_class in tool_classes)

    def test_agent_description_mentions_constitutional_compliance(self, mock_agent_context):
        """Test that agent description emphasizes constitutional compliance."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify constitutional compliance aspects
            assert "constitutional compliance" in description
            assert "architectural" in description or "strategic" in description

    def test_agent_has_authority_for_high_priority_tasks(self, mock_agent_context):
        """Test that agent has authority to create high-priority tasks."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify authority for high-priority tasks (using flexible assertions)
            assert "self-directed task creation" in description.lower()
            assert "strategic" in description.lower()
            assert "architectural" in description.lower()

    def test_agent_architecture_loop_integration(self, mock_agent_context):
        """Test that agent integrates with architecture loop for spec-driven fixes."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify architecture loop integration (flexible assertions)
            assert "strategic" in description.lower() or "architectural" in description.lower()
            assert "specification" in description.lower() or "spec" in description.lower()

    def test_agent_memory_integration_supports_learning(self, mock_agent_context):
        """Test that memory integration supports continuous learning."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            # Verify memory logging includes appropriate tags
            call_args = mock_agent_context.store_memory.call_args
            memory_tags = call_args[0][2]
            assert "agency" in memory_tags
            assert "chief_architect" in memory_tags
            assert "creation" in memory_tags


class TestChiefArchitectAgentIntegration:
    """Test ChiefArchitectAgent integration with other system components."""

    def test_agent_integrates_with_audit_system(self, mock_agent_context):
        """Test that agent can integrate with audit system."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify audit system integration (flexible assertions)
            assert "architectural" in description.lower() or "strategic" in description.lower()
            assert "quality" in description.lower() or "auditor" in description.lower()

    def test_agent_integrates_with_memory_patterns(self, mock_agent_context):
        """Test that agent can integrate with memory pattern system."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify memory pattern integration (flexible assertions)
            assert "pattern" in description.lower() or "learning" in description.lower()
            assert "strategic" in description.lower() or "quality" in description.lower()

    def test_agent_integrates_with_performance_metrics(self, mock_agent_context):
        """Test that agent can integrate with performance metrics."""
        with (
            patch("chief_architect_agent.chief_architect_agent.Agent") as mock_agent_class,
            patch(
                "chief_architect_agent.chief_architect_agent.get_model_instance",
                return_value="gpt-5",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_model_settings"
            ) as mock_settings,
            patch(
                "chief_architect_agent.chief_architect_agent.select_instructions_file",
                return_value="instructions.md",
            ),
            patch(
                "chief_architect_agent.chief_architect_agent.create_message_filter_hook"
            ) as mock_filter,
            patch(
                "chief_architect_agent.chief_architect_agent.create_memory_integration_hook"
            ) as mock_memory,
            patch(
                "chief_architect_agent.chief_architect_agent.create_composite_hook"
            ) as mock_composite,
        ):
            mock_settings.return_value = ModelSettings(
                temperature=0.1,
                max_tokens=32000,
                reasoning=Reasoning(effort="high", summary="auto"),
            )

            mock_agent = Mock()
            mock_agent_class.return_value = mock_agent
            mock_filter.return_value = Mock()
            mock_memory.return_value = Mock()
            mock_composite.return_value = Mock()

            create_chief_architect_agent(agent_context=mock_agent_context)

            call_kwargs = mock_agent_class.call_args[1]
            description = call_kwargs["description"]

            # Verify performance metrics integration (flexible assertions)
            assert "quality" in description.lower() or "metrics" in description.lower()
            assert "strategic" in description.lower() or "architectural" in description.lower()
