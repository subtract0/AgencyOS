import os

from shared.utils import silence_warnings_and_logs

silence_warnings_and_logs()

import litellm  # noqa: E402 - must import after warning suppression
from agency_swarm import Agency  # noqa: E402 - must import after warning suppression
from agency_swarm.tools import (
    SendMessageHandoff,  # noqa: E402 - must import after warning suppression
)
from dotenv import load_dotenv  # noqa: E402 - must import after warning suppression

from agency_code_agent.agency_code_agent import (  # noqa: E402 - must import after warning suppression
    create_agency_code_agent,
)
from planner_agent.planner_agent import (  # noqa: E402 - must import after warning suppression
    create_planner_agent,
)
from subagent_example.subagent_example import (  # noqa: E402 - must import after warning suppression
    create_subagent_example,
)

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True

# switch between models here
# model = "anthropic/claude-sonnet-4-20250514"
model = "gpt-5"

# create agents
planner = create_planner_agent(
    model=model, reasoning_effort="high"
)
# coder = create_agency_code_agent(model="gpt-5", reasoning_effort="high")
coder = create_agency_code_agent(
    model=model, reasoning_effort="high"
)
subagent_example = create_subagent_example(
    model=model, reasoning_effort="high"
)

agency = Agency(
    coder, planner,
    name="AgencyCode",
    communication_flows=[
        (coder, planner, SendMessageHandoff),
        (planner, coder, SendMessageHandoff),
        # (coder, subagent_example) # example for how to add a subagent
    ],
    shared_instructions="./project-overview.md",
)

if __name__ == "__main__":
    agency.terminal_demo(show_reasoning=False if model.startswith("anthropic") else True)
    # agency.visualize()
