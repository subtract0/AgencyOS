import pytest

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
