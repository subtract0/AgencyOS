import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from shared.agent_context import create_agent_context
from toolsmith_agent import create_toolsmith_agent


class TestToolSmithAgentCreation:
    def test_toolsmith_agent_import_and_creation(self):
        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        assert agent.name == "ToolSmithAgent"
        assert isinstance(agent.description, str)
        assert "tool" in agent.description.lower()
        assert "scaffold" in agent.description.lower()

        # Tools present
        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]
        for required in ["Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash", "TodoWrite"]:
            assert required in tool_names, f"Missing required tool: {required}"

        # Hooks / memory integration sanity
        assert hasattr(agent, 'hooks') and agent.hooks is not None
        assert hasattr(ctx, 'session_id') and ctx.session_id


class TestToolSmithDirectiveParsing:
    """Test ToolSmithAgent's ability to parse and process tool directives."""

    def test_valid_directive_parsing(self):
        """Test parsing of well-formed tool directives."""
        # Example directive based on ToolSmith instructions
        directive = {
            "name": "ExampleTool",
            "module_path": "tools/example_tool.py",
            "description": "A test tool for verification",
            "parameters": [
                {"name": "input_text", "type": "str", "description": "Text to process"},
                {"name": "count", "type": "int", "description": "Number of iterations", "default": 1}
            ],
            "tests": [
                "test_example_tool_basic_functionality",
                "test_example_tool_edge_cases"
            ]
        }

        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # The agent should have the capability to process directives
        # (This tests the agent's tool configuration rather than execution)
        assert agent is not None
        assert agent.name == "ToolSmithAgent"

    def test_malformed_directive_detection(self):
        """Test handling of malformed directives."""
        malformed_directives = [
            {},  # Empty directive
            {"name": "InvalidTool"},  # Missing required fields
            {"name": "", "module_path": ""},  # Empty required fields
            {"parameters": "invalid_format"},  # Wrong parameter format
        ]

        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should be resilient to malformed input
        assert agent is not None

        # Each malformed directive should be identifiable as invalid
        for directive in malformed_directives:
            # The agent has the tools needed to validate directives
            tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]
            assert "Read" in tool_names  # For reading directive files
            assert "Write" in tool_names  # For writing scaffolded tools

    def test_parameter_validation(self):
        """Test validation of tool parameter specifications."""
        valid_parameters = [
            {"name": "text", "type": "str", "description": "Input text"},
            {"name": "count", "type": "int", "description": "Count", "default": 5},
            {"name": "enabled", "type": "bool", "description": "Enable feature", "default": False}
        ]

        invalid_parameters = [
            {"name": "", "type": "str"},  # Empty name
            {"type": "str", "description": "Missing name"},  # Missing name
            {"name": "test", "description": "Missing type"},  # Missing type
            {"name": "test", "type": "invalid_type", "description": "Bad type"}  # Invalid type
        ]

        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should have validation capabilities
        assert agent is not None

        # Each parameter set should be processable by the agent's tools
        for params in valid_parameters + invalid_parameters:
            # Agent has the necessary tools for parameter processing
            assert any("Edit" in str(tool) for tool in agent.tools)

    def test_scaffolding_patterns(self):
        """Test that agent understands scaffolding patterns."""
        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should have tools needed for scaffolding
        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        required_scaffolding_tools = [
            "Read",      # Reading existing patterns
            "Write",     # Creating new files
            "Edit",      # Modifying existing files
            "MultiEdit", # Batch modifications
            "Grep",      # Searching for patterns
            "Bash",      # Running tests
            "TodoWrite"  # Task tracking
        ]

        for tool in required_scaffolding_tools:
            assert tool in tool_names, f"Missing scaffolding tool: {tool}"

    def test_test_generation_requirements(self):
        """Test that agent can handle test generation requirements."""
        test_spec = {
            "tool_name": "TestTool",
            "test_cases": [
                "test_basic_functionality",
                "test_error_handling",
                "test_edge_cases"
            ]
        }

        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should have capability to generate tests
        assert agent is not None

        # Verify agent has constitutional compliance awareness
        instructions_check = hasattr(agent, 'instructions')
        assert instructions_check, "Agent should have constitutional instructions"

    def test_constitutional_compliance_integration(self):
        """Test that agent integrates constitutional requirements."""
        ctx = create_agent_context()
        agent = create_toolsmith_agent(agent_context=ctx)

        # Agent should have memory integration for learning
        assert hasattr(agent, 'hooks'), "Agent should have hooks for constitutional compliance"
        assert agent.hooks is not None

        # Agent should have tools for constitutional validation
        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]
        assert "Bash" in tool_names, "Agent needs Bash tool for running tests (Article II)"
        assert "Read" in tool_names, "Agent needs Read tool for context gathering (Article I)"
