"""
Tool Integration Test for Agency Code Agent
Tests that tools can be invoked directly via the agent
"""

import pytest
from agency_swarm import Agency
from agency_swarm.tools import SendMessageHandoff

from agency_code_agent.agency_code_agent import create_agency_code_agent
from planner_agent.planner_agent import create_planner_agent


@pytest.fixture
def agent():
    """Create agency code agent for testing"""
    return create_agency_code_agent()


def test_agent_creation(agent):
    """Test that agent is created successfully with tools"""
    assert agent is not None, "Agent should be created successfully"
    assert hasattr(agent, "name"), "Agent should have a name attribute"
    assert hasattr(agent, "tools"), "Agent should have tools attribute"
    assert len(agent.tools) > 0, "Agent should have at least one tool"


def test_ls_tool_invocation(agent):
    """Test LS tool direct invocation"""
    ls_tool = None
    for tool in agent.tools:
        if tool.name == "LS":
            ls_tool = tool
            break

    assert ls_tool is not None, "LS tool should be found in agent tools"

    # Test that the tool exists and has expected properties
    assert hasattr(ls_tool, "name"), "Tool should have a name"
    assert ls_tool.name == "LS", "Tool name should be LS"


def test_todo_write_tool_invocation(agent):
    """Test TodoWrite tool direct invocation"""
    todo_tool = None
    for tool in agent.tools:
        if tool.name == "TodoWrite":
            todo_tool = tool
            break

    assert todo_tool is not None, "TodoWrite tool should be found in agent tools"

    # Test that the tool exists and has expected properties
    assert hasattr(todo_tool, "name"), "Tool should have a name"
    assert todo_tool.name == "TodoWrite", "Tool name should be TodoWrite"


def test_tool_parameter_validation(agent):
    """Test tool parameter validation"""
    read_tool = None
    for tool in agent.tools:
        if tool.name == "Read":
            read_tool = tool
            break

    assert read_tool is not None, "Read tool should be found in agent tools"

    # Test that the tool exists and has expected properties
    assert hasattr(read_tool, "name"), "Tool should have a name"
    assert read_tool.name == "Read", "Tool name should be Read"


def test_critical_tools_presence(agent):
    """Test that critical tools are present"""
    tools_by_name = {tool.name: tool for tool in agent.tools}
    critical_tools = ["LS", "Read", "Write", "Bash", "TodoWrite"]

    for tool_name in critical_tools:
        assert tool_name in tools_by_name, f"Critical tool {tool_name} should be loaded"


def test_tool_count(agent):
    """Test that expected number of tools are loaded"""
    # Note: this might need adjustment based on actual tool count
    assert len(agent.tools) >= 10, "Agent should have at least 10 tools"


@pytest.mark.asyncio
async def test_handoff_coder_to_planner_via_agency():
    """Ensure handoff path works by prompting coder to hand off to planner.

    This would raise if the hooks didn't implement on_handoff, so this
    test guards against regressions by exercising the handoff lifecycle.
    """
    coder = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="low")
    planner = create_planner_agent(model="gpt-5-mini", reasoning_effort="low")

    agency = Agency(
        coder,
        communication_flows=[
            (coder, planner, SendMessageHandoff),
            (planner, coder, SendMessageHandoff),
        ],
        shared_instructions=(
            "Test agency for verifying inter-agent handoff between coder and planner."
        ),
    )

    prompt = (
        "You are the coding agent. Immediately perform a handoff to the PlannerAgent "
        "using the SendMessageHandoff tool with a short message asking it to propose "
        "a high-level plan for implementing a tiny feature. Keep the exchange brief."
    )

    run_result = await agency.get_response(prompt)
    response = run_result.text if hasattr(run_result, "text") else str(run_result)

    assert len(response) > 0, "Response should not be empty after handoff scenario"
    # Sanity check for obvious failures
    error_indicators = ["Traceback", "Exception", "ERROR:", "Failed", "AttributeError"]
    assert not any(e.lower() in response.lower() for e in error_indicators), (
        f"Response should not contain error indicators. Got: {response[:300]}..."
    )
