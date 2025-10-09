"""
Comprehensive test suite for lean_adapter.py.

Tests backward compatibility layer for agency-swarm migration.

Tests cover:
- Agent class compatibility
- Agency class compatibility
- Instructions loading from file
- Shared instructions
- Tool conversion

Constitutional Compliance:
- Article II: TDD - tests written first
- Article II: 100% verification
- Pydantic models for data structures

Version: 1.0.0
Created: 2025-10-09
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from shared.lean_adapter import Agency, Agent
from shared.lean_agent import Tool, ToolParameter, ToolPropertySchema


class TestAgentAdapter:
    """Test Agent class (backward compatibility adapter)."""

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_minimal_init(self, mock_openai, monkeypatch):
        """Test Agent adapter with minimal parameters."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test_agent", instructions="You are helpful")

        # Assert
        assert agent.config.name == "test_agent"
        assert agent.config.instructions == "You are helpful"
        assert agent.config.model == "gpt-4o"  # Default
        assert len(agent.messages) == 1  # System prompt

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_default_name(self, mock_openai, monkeypatch):
        """Test Agent with default name."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(instructions="Test instructions")

        # Assert
        assert agent.config.name == "agent"  # Default name

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_default_instructions(self, mock_openai, monkeypatch):
        """Test Agent with default instructions generation."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="helper")

        # Assert
        assert "helper" in agent.config.instructions
        assert "helpful" in agent.config.instructions.lower()

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_with_instructions_file(self, mock_openai, monkeypatch):
        """Test Agent loads instructions from file."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange - Create temporary instructions file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("You are a specialized agent.\nYou help with testing.")
            instructions_file = f.name

        try:
            # Act
            agent = Agent(name="file_agent", instructions_file=instructions_file)

            # Assert
            assert "specialized agent" in agent.config.instructions
            assert "testing" in agent.config.instructions
        finally:
            # Cleanup
            Path(instructions_file).unlink()

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_instructions_string_takes_precedence(self, mock_openai, monkeypatch):
        """Test that instructions string overrides instructions_file."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("File instructions")
            instructions_file = f.name

        try:
            # Act - Provide both
            agent = Agent(
                name="test",
                instructions="String instructions",
                instructions_file=instructions_file,
            )

            # Assert - String takes precedence
            assert agent.config.instructions == "String instructions"
        finally:
            Path(instructions_file).unlink()

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_custom_model(self, mock_openai, monkeypatch):
        """Test Agent with custom model."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test", instructions="Test", model="gpt-5")

        # Assert
        assert agent.config.model == "gpt-5"

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_custom_temperature(self, mock_openai, monkeypatch):
        """Test Agent with custom temperature."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test", instructions="Test", temperature=0.2)

        # Assert
        assert agent.config.temperature == 0.2

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_custom_max_tokens(self, mock_openai, monkeypatch):
        """Test Agent with custom max_tokens."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test", instructions="Test", max_tokens=8000)

        # Assert
        assert agent.config.max_tokens == 8000

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_with_tools(self, mock_openai, monkeypatch):
        """Test Agent with tools."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        param = ToolParameter(type="object", properties={}, required=[])
        tool_obj = Tool(name="test_tool", description="Test", parameters=param)

        # Act
        agent = Agent(name="test", instructions="Test", tools=[tool_obj])

        # Assert
        assert len(agent.config.tools) == 1
        assert agent.config.tools[0].name == "test_tool"

    @patch("shared.lean_agent.OpenAI")
    def test_agent_adapter_ignores_unknown_kwargs(self, mock_openai, monkeypatch):
        """Test Agent ignores unknown kwargs (for compatibility)."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act - Pass extra kwargs that agency-swarm might have
        agent = Agent(
            name="test",
            instructions="Test",
            unknown_param="ignored",
            another_param=123,
        )

        # Assert - No error, agent created successfully
        assert agent.config.name == "test"


class TestAgencyAdapter:
    """Test Agency class (backward compatibility adapter)."""

    @patch("shared.lean_agent.OpenAI")
    def test_agency_minimal_init(self, mock_openai, monkeypatch):
        """Test Agency with minimal parameters."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent = Agent(name="test_agent", instructions="Test")

        # Act
        agency = Agency(agents=[agent])

        # Assert
        assert agency.agent == agent
        assert agency.agent.config.name == "test_agent"

    @patch("shared.lean_agent.OpenAI")
    def test_agency_with_multiple_agents_uses_first(self, mock_openai, monkeypatch):
        """Test Agency with multiple agents uses only the first."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent1 = Agent(name="agent1", instructions="First")
        agent2 = Agent(name="agent2", instructions="Second")
        agent3 = Agent(name="agent3", instructions="Third")

        # Act
        agency = Agency(agents=[agent1, agent2, agent3])

        # Assert
        assert agency.agent == agent1
        assert agency.agent.config.name == "agent1"

    @patch("shared.lean_agent.OpenAI")
    def test_agency_requires_at_least_one_agent(self, mock_openai, monkeypatch):
        """Test Agency raises error with empty agent list."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act & Assert
        with pytest.raises(ValueError, match="at least one agent"):
            Agency(agents=[])

    @patch("shared.lean_agent.OpenAI")
    def test_agency_with_shared_instructions_string(self, mock_openai, monkeypatch):
        """Test Agency prepends shared instructions."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent = Agent(name="test", instructions="Original instructions")

        # Act
        agency = Agency(agents=[agent], shared_instructions="Shared context:\n")

        # Assert
        assert "Shared context" in agency.agent.config.instructions
        assert "Original instructions" in agency.agent.config.instructions
        assert agency.agent.config.instructions.index(
            "Shared"
        ) < agency.agent.config.instructions.index("Original")

    @patch("shared.lean_agent.OpenAI")
    def test_agency_with_shared_instructions_file(self, mock_openai, monkeypatch):
        """Test Agency loads shared instructions from file."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Shared Guidelines\n\nFollow these rules.")
            shared_file = f.name

        agent = Agent(name="test", instructions="Agent instructions")

        try:
            # Act
            agency = Agency(agents=[agent], shared_instructions=shared_file)

            # Assert
            assert "Shared Guidelines" in agency.agent.config.instructions
            assert "rules" in agency.agent.config.instructions
            assert "Agent instructions" in agency.agent.config.instructions
        finally:
            Path(shared_file).unlink()

    @patch("shared.lean_agent.OpenAI")
    def test_agency_shared_instructions_nonexistent_file_uses_as_string(
        self, mock_openai, monkeypatch
    ):
        """Test Agency uses nonexistent file path as string."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent = Agent(name="test", instructions="Test")

        # Act - Provide path that doesn't exist
        agency = Agency(agents=[agent], shared_instructions="./nonexistent_file.md")

        # Assert - Uses as string, not file
        assert "./nonexistent_file.md" in agency.agent.config.instructions

    @patch("shared.lean_agent.OpenAI")
    def test_agency_get_completion_simple(self, mock_openai, monkeypatch):
        """Test Agency.get_completion() method."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent = Agent(name="test", instructions="Test")
        agency = Agency(agents=[agent])

        # Mock agent run
        mock_response = Mock()
        mock_response.content = "Hello, how can I help?"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agency.get_completion("Hi there")

        # Assert
        assert result == "Hello, how can I help?"

    @patch("shared.lean_agent.OpenAI")
    def test_agency_get_completion_ignores_recipient_agent(self, mock_openai, monkeypatch):
        """Test Agency.get_completion() ignores recipient_agent parameter."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent1 = Agent(name="agent1", instructions="First")
        agent2 = Agent(name="agent2", instructions="Second")
        agency = Agency(agents=[agent1, agent2])

        mock_response = Mock()
        mock_response.content = "Response"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act - Pass recipient_agent (should be ignored)
        result = agency.get_completion("Test message", recipient_agent=agent2)

        # Assert - Still uses first agent (agent1)
        assert result == "Response"
        # Verify agent1 was used (has new messages)
        assert len(agency.agent.messages) > 1


class TestToolConversion:
    """Test tool conversion in adapter."""

    @patch("shared.lean_agent.OpenAI")
    def test_adapter_converts_tool_objects(self, mock_openai, monkeypatch):
        """Test adapter handles Tool objects."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        param = ToolParameter(
            type="object",
            properties={"x": ToolPropertySchema(type="number")},
            required=["x"],
        )
        tool1 = Tool(name="tool1", description="First tool", parameters=param)
        tool2 = Tool(name="tool2", description="Second tool", parameters=param)

        # Act
        agent = Agent(name="test", instructions="Test", tools=[tool1, tool2])

        # Assert
        assert len(agent.config.tools) == 2
        assert agent.config.tools[0] == tool1
        assert agent.config.tools[1] == tool2

    @patch("shared.lean_agent.OpenAI")
    def test_adapter_filters_non_tool_objects(self, mock_openai, monkeypatch):
        """Test adapter filters out non-Tool objects."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        param = ToolParameter(type="object", properties={}, required=[])
        valid_tool = Tool(name="valid", description="Valid", parameters=param)
        invalid_tool = "not a tool object"  # String, not Tool

        # Act
        agent = Agent(name="test", instructions="Test", tools=[valid_tool, invalid_tool])

        # Assert - Only valid Tool objects are kept
        assert len(agent.config.tools) == 1
        assert agent.config.tools[0] == valid_tool


class TestBackwardCompatibility:
    """Test backward compatibility with agency-swarm patterns."""

    @patch("shared.lean_agent.OpenAI")
    def test_agency_swarm_typical_usage(self, mock_openai, monkeypatch):
        """Test typical agency-swarm usage pattern."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange - Typical agency-swarm code
        coder_agent = Agent(
            name="Coder",
            instructions="You are a Python expert",
            model="gpt-4o",
            temperature=0.3,
        )

        agency = Agency(
            agents=[coder_agent],
            shared_instructions="./constitution.md",  # Common pattern
        )

        mock_response = Mock()
        mock_response.content = "Code written successfully"
        mock_response.tool_calls = None
        mock_openai.return_value.chat.completions.create.return_value.choices = [
            Mock(message=mock_response)
        ]

        # Act
        result = agency.get_completion("Write a hello world function")

        # Assert
        assert "Code written successfully" in result

    @patch("shared.lean_agent.OpenAI")
    def test_autonomous_worker_typical_usage(self, mock_openai, monkeypatch):
        """Test pattern used in autonomous_worker.py."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Arrange - Pattern from autonomous_worker.py
        def create_agent_from_instructions_file(name: str, instructions_file: str):
            return Agent(
                name=name,
                instructions_file=instructions_file,
                model="gpt-4o",
                temperature=0.7,
            )

        # Create temp instructions file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Agent Instructions\n\nYou are autonomous.")
            file_path = f.name

        try:
            agent = create_agent_from_instructions_file("Worker", file_path)

            # Create agency
            agency = Agency(agents=[agent])

            mock_response = Mock()
            mock_response.content = "Task executed"
            mock_response.tool_calls = None
            mock_openai.return_value.chat.completions.create.return_value.choices = [
                Mock(message=mock_response)
            ]

            # Act
            result = agency.get_completion("Execute task")

            # Assert
            assert "Task executed" in result
            assert "autonomous" in agent.config.instructions.lower()
        finally:
            Path(file_path).unlink()


class TestEdgeCases:
    """Test edge cases in adapter."""

    @patch("shared.lean_agent.OpenAI")
    def test_agent_with_none_tools(self, mock_openai, monkeypatch):
        """Test Agent with None tools parameter."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test", instructions="Test", tools=None)

        # Assert
        assert len(agent.config.tools) == 0

    @patch("shared.lean_agent.OpenAI")
    def test_agency_with_none_shared_instructions(self, mock_openai, monkeypatch):
        """Test Agency with None shared_instructions."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        agent = Agent(name="test", instructions="Original")

        # Act
        agency = Agency(agents=[agent], shared_instructions=None)

        # Assert
        assert agency.agent.config.instructions == "Original"

    @patch("shared.lean_agent.OpenAI")
    def test_agent_instructions_file_not_found_uses_default(self, mock_openai, monkeypatch):
        """Test Agent with nonexistent instructions file uses default."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Act
        agent = Agent(name="test_agent", instructions_file="/nonexistent/file.md")

        # Assert - Uses default since file doesn't exist
        assert "test_agent" in agent.config.instructions
        assert "helpful" in agent.config.instructions.lower()

    @patch("shared.lean_agent.OpenAI")
    def test_agency_shared_instructions_absolute_path(self, mock_openai, monkeypatch):
        """Test Agency handles absolute path for shared_instructions."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("Shared content")
            abs_path = str(Path(f.name).absolute())

        agent = Agent(name="test", instructions="Test")

        try:
            # Act
            agency = Agency(agents=[agent], shared_instructions=abs_path)

            # Assert
            assert "Shared content" in agency.agent.config.instructions
        finally:
            Path(abs_path).unlink()

    @patch("shared.lean_agent.OpenAI")
    def test_agency_shared_instructions_relative_path(self, mock_openai, monkeypatch):
        """Test Agency handles relative path for shared_instructions."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, dir=".") as f:
            f.write("Relative content")
            rel_path = f"./{Path(f.name).name}"

        agent = Agent(name="test", instructions="Test")

        try:
            # Act
            agency = Agency(agents=[agent], shared_instructions=rel_path)

            # Assert
            assert "Relative content" in agency.agent.config.instructions
        finally:
            Path(f.name).unlink()


class TestDocumentation:
    """Test that adapter is well-documented for migration."""

    def test_agent_class_has_docstring(self):
        """Test Agent class has migration documentation."""
        assert Agent.__doc__ is not None
        assert "agency_swarm" in Agent.__doc__.lower() or "drop-in" in Agent.__doc__.lower()

    def test_agency_class_has_docstring(self):
        """Test Agency class has documentation."""
        assert Agency.__doc__ is not None

    def test_adapter_module_has_docstring(self):
        """Test module has migration guidance."""
        import shared.lean_adapter as adapter_module

        assert adapter_module.__doc__ is not None
        assert (
            "backward" in adapter_module.__doc__.lower()
            or "compatibility" in adapter_module.__doc__.lower()
        )
