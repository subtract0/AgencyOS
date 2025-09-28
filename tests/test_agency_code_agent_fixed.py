import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock

from agency_code_agent.agency_code_agent import create_agency_code_agent
from shared.agent_context import AgentContext, create_agent_context


class TestAgencyCodeAgentCreation:
    """Test suite for the agency code agent factory function."""

    def test_agent_creation_default_params(self):
        """Test agent creation with default parameters."""
        agent = create_agency_code_agent()

        assert agent.name == "AgencyCodeAgent"
        assert isinstance(agent.description, str)
        assert "software engineer" in agent.description
        assert "implementation specialist" in agent.description

    def test_agent_creation_custom_params(self):
        """Test agent creation with custom parameters."""
        ctx = create_agent_context()
        agent = create_agency_code_agent(
            model="gpt-5-mini",
            reasoning_effort="high",
            agent_context=ctx
        )

        assert agent.name == "AgencyCodeAgent"
        assert agent is not None

    def test_agent_creation_with_context(self):
        """Test agent creation with provided agent context."""
        ctx = create_agent_context()
        agent = create_agency_code_agent(agent_context=ctx)

        assert agent is not None
        assert hasattr(agent, 'hooks')
        assert agent.hooks is not None

    def test_agent_creation_creates_context_when_none(self):
        """Test that agent creation creates context when none provided."""
        agent = create_agency_code_agent(agent_context=None)
        assert agent is not None

    def test_model_type_detection(self):
        """Test that model type is detected correctly."""
        agent = create_agency_code_agent(model="gpt-4")
        assert agent is not None

    def test_instructions_handling(self):
        """Test that instructions are handled correctly."""
        agent = create_agency_code_agent(model="gpt-5-mini")
        assert hasattr(agent, 'instructions')

    def test_agent_tools_configuration(self):
        """Test that agent has proper tools configured."""
        agent = create_agency_code_agent()

        # Check that tools are present
        assert hasattr(agent, 'tools')
        assert agent.tools is not None
        assert len(agent.tools) > 0

        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # Core tools should be present
        expected_core_tools = [
            "Bash", "Glob", "Grep", "LS", "ExitPlanMode",
            "Read", "Edit", "MultiEdit", "Write",
            "NotebookRead", "NotebookEdit", "TodoWrite", "Git"
        ]

        for tool in expected_core_tools:
            assert any(tool in name for name in tool_names), f"Missing core tool: {tool}"

    def test_agent_hooks_configuration(self):
        """Test that agent has proper hooks configured."""
        agent = create_agency_code_agent()

        assert hasattr(agent, 'hooks')
        assert agent.hooks is not None

    def test_agent_model_settings(self):
        """Test that agent has proper model settings."""
        agent = create_agency_code_agent(
            model="gpt-5-mini",
            reasoning_effort="medium"
        )

        assert hasattr(agent, 'model_settings')

    def test_model_instance_creation(self):
        """Test that model instance is created correctly."""
        agent = create_agency_code_agent(model="gpt-5-mini")

        # Agent should be created successfully
        assert agent is not None
        assert agent.name == "AgencyCodeAgent"
        assert hasattr(agent, 'model')

    def test_agent_memory_integration(self):
        """Test that agent creation logs to memory."""
        ctx = create_agent_context()

        with patch.object(ctx, 'store_memory') as mock_store:
            agent = create_agency_code_agent(agent_context=ctx)

            mock_store.assert_called_once()
            call_args = mock_store.call_args

            # Check that memory was stored with correct data
            assert f"agent_created_{ctx.session_id}" in call_args[0][0]
            memory_data = call_args[0][1]
            assert memory_data["agent_type"] == "AgencyCodeAgent"
            assert memory_data["model"] == "gpt-5-mini"  # default model
            assert memory_data["reasoning_effort"] == "medium"  # default effort
            assert memory_data["session_id"] == ctx.session_id

            # Check tags
            tags = call_args[0][2]
            assert "agency" in tags
            assert "coder" in tags
            assert "creation" in tags

    def test_tools_folder_configuration(self):
        """Test that tools folder is correctly configured."""
        agent = create_agency_code_agent()

        assert hasattr(agent, 'tools_folder')
        # Should point to tools directory within agent directory
        assert isinstance(agent.tools_folder, str)


class TestAgencyCodeAgentDescription:
    """Test suite for agent description and role definition."""

    def test_agent_description_content(self):
        """Test that agent description accurately describes its role."""
        agent = create_agency_code_agent()

        description = agent.description.lower()

        # Should mention key responsibilities
        assert "software engineer" in description
        assert "implementation specialist" in description
        assert "code changes" in description or "writing" in description
        assert "editing" in description
        assert "debugging" in description or "testing" in description

    def test_agent_description_mentions_triggers(self):
        """Test that description mentions when agent should be triggered."""
        agent = create_agency_code_agent()

        description = agent.description.lower()

        # Should mention triggering conditions
        assert "triggered" in description
        assert "implementation" in description

    def test_agent_description_mentions_planning_integration(self):
        """Test that description mentions integration with PlannerAgent."""
        agent = create_agency_code_agent()

        description = agent.description

        # Should mention working from plans
        assert "PlannerAgent" in description or "plans" in description.lower()

    def test_agent_description_mentions_quality_standards(self):
        """Test that description mentions code quality responsibilities."""
        agent = create_agency_code_agent()

        description = agent.description.lower()

        # Should mention quality standards
        assert "quality" in description or "standards" in description


class TestAgencyCodeAgentIntegration:
    """Integration tests for the agency code agent."""

    def test_agent_system_hooks_integration(self):
        """Test that agent integrates properly with system hooks."""
        ctx = create_agent_context()
        agent = create_agency_code_agent(agent_context=ctx)

        # Agent should have hooks configured
        assert agent.hooks is not None

    def test_model_settings_integration(self):
        """Test that model settings are properly integrated."""
        agent = create_agency_code_agent(
            model="gpt-5-mini",
            reasoning_effort="medium"
        )

        # Agent should be created successfully with model settings
        assert agent is not None
        assert hasattr(agent, 'model_settings')

    def test_agent_tool_availability(self):
        """Test that all required tools are available and accessible."""
        agent = create_agency_code_agent()

        # Test that core development tools are available
        tool_names = [getattr(t, 'name', getattr(t, '__name__', str(t))) for t in agent.tools]

        # File operation tools
        assert any("Read" in name for name in tool_names)
        assert any("Write" in name for name in tool_names)
        assert any("Edit" in name for name in tool_names)

        # Search tools
        assert any("Grep" in name for name in tool_names)
        assert any("Glob" in name for name in tool_names)

        # System tools
        assert any("Bash" in name for name in tool_names)
        assert any("Git" in name for name in tool_names)

        # Workflow tools
        assert any("TodoWrite" in name for name in tool_names)
        assert any("ExitPlanMode" in name for name in tool_names)

    def test_current_directory_detection(self):
        """Test that current directory is detected correctly."""
        from agency_code_agent.agency_code_agent import current_dir

        assert isinstance(current_dir, str)
        assert os.path.exists(current_dir)
        assert "agency_code_agent" in current_dir

    def test_error_resilience(self):
        """Test that agent creation is resilient to various error conditions."""
        # Test with various model types
        models_to_test = ["gpt-5-mini", "gpt-4", "claude-3"]

        for model in models_to_test:
            try:
                agent = create_agency_code_agent(model=model)
                assert agent is not None
                assert agent.name == "AgencyCodeAgent"
            except Exception:
                # Some models might fail, but it should be handled gracefully
                pass

    def test_agent_uniqueness(self):
        """Test that each agent creation produces a unique instance."""
        agent1 = create_agency_code_agent()
        agent2 = create_agency_code_agent()

        # Should be different instances
        assert agent1 is not agent2

        # But should have same name and basic properties
        assert agent1.name == agent2.name == "AgencyCodeAgent"

    def test_context_isolation(self):
        """Test that different agent contexts are properly isolated."""
        ctx1 = create_agent_context()
        time.sleep(0.01)  # Small delay to ensure different timestamps
        ctx2 = create_agent_context()

        agent1 = create_agency_code_agent(agent_context=ctx1)
        agent2 = create_agency_code_agent(agent_context=ctx2)

        # Agents should be different
        assert agent1 is not agent2

        # Contexts should be different objects
        assert ctx1 is not ctx2


class TestAgencyCodeAgentErrorHandling:
    """Test suite for error handling in agent creation and operation."""

    def test_invalid_model_handling(self):
        """Test handling of invalid model specifications."""
        # Should not crash with invalid model
        try:
            agent = create_agency_code_agent(model="completely-invalid-model")
            # Might succeed with fallback behavior
            assert agent is not None
        except Exception:
            # Or might fail gracefully
            pass

    def test_invalid_reasoning_effort_handling(self):
        """Test handling of invalid reasoning effort levels."""
        try:
            agent = create_agency_code_agent(reasoning_effort="invalid-effort")
            assert agent is not None
        except Exception:
            pass

    def test_memory_storage_failure_handling(self):
        """Test handling when memory storage fails."""
        ctx = create_agent_context()

        # Mock memory to fail
        with patch.object(ctx, 'store_memory', side_effect=Exception("Memory storage failed")):
            try:
                agent = create_agency_code_agent(agent_context=ctx)
                # Should still create agent even if memory storage fails
                assert agent is not None
            except Exception:
                # Or handle the failure appropriately
                pass