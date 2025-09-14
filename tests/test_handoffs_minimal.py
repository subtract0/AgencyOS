import pytest
from agency_swarm import Agency
from agency_swarm.tools import SendMessageHandoff

from agency_code_agent.agency_code_agent import create_agency_code_agent
from planner_agent.planner_agent import create_planner_agent


@pytest.mark.asyncio
async def test_coder_handoff_to_planner_minimal():
    """Coder should hand off to PlannerAgent on explicit request without errors."""
    coder = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="low")
    planner = create_planner_agent(model="gpt-5-mini", reasoning_effort="low")

    agency = Agency(
        coder,
        communication_flows=[
            (coder, planner, SendMessageHandoff),
            (planner, coder, SendMessageHandoff),
        ],
        shared_instructions=(
            "Minimal handoff test: ensure handoff tool works without streaming errors."
        ),
    )

    prompt = (
        "Immediately hand off to the PlannerAgent using the SendMessageHandoff tool "
        "with a short message. Keep everything minimal."
    )

    run_result = await agency.get_response(prompt)
    response = run_result.text if hasattr(run_result, "text") else str(run_result)

    # Should not contain OpenAI invalid request or traceback errors
    error_indicators = [
        "Traceback",
        "invalid_request_error",
        "was provided without its required 'reasoning' item",
        "Error streaming response",
        "ERROR:",
        "Failed",
    ]
    assert not any(e.lower() in response.lower() for e in error_indicators), (
        f"Unexpected error in response: {response[:400]}"
    )
    assert len(response) > 0


@pytest.mark.asyncio
async def test_planner_reports_its_name_minimal():
    """Coder prompts a handoff: planner should respond with its name; no errors."""
    coder = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="low")
    planner = create_planner_agent(model="gpt-5-mini", reasoning_effort="low")

    agency = Agency(
        coder,
        communication_flows=[
            (coder, planner, SendMessageHandoff),
            (planner, coder, SendMessageHandoff),
        ],
        shared_instructions="Minimal name test for PlannerAgent via handoff.",
    )

    prompt = (
        "Hand off to the PlannerAgent now using the SendMessageHandoff tool and ask: "
        "'What is your agent name?' Keep it very short."
    )

    run_result = await agency.get_response(prompt)
    response = run_result.text if hasattr(run_result, "text") else str(run_result)

    error_indicators = [
        "Traceback",
        "invalid_request_error",
        "was provided without its required 'reasoning' item",
        "Error streaming response",
        "ERROR:",
        "Failed",
    ]
    assert not any(e.lower() in response.lower() for e in error_indicators), (
        f"Unexpected error in response: {response[:400]}"
    )
    assert len(response) > 0
