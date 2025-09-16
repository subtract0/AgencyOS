import os

from utils import silence_warnings_and_logs

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

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
litellm.modify_params = True

# Create agents
planner = create_planner_agent(
    model="anthropic/claude-sonnet-4-20250514", reasoning_effort="high"
)
# coder = create_agency_code_agent(model="gpt-5", reasoning_effort="high")
coder = create_agency_code_agent(
    model="anthropic/claude-sonnet-4-20250514", reasoning_effort="high"
)

agency = Agency(
    coder,
    planner,
    communication_flows=[
        (coder, planner, SendMessageHandoff),
        (planner, coder, SendMessageHandoff),
    ],
)

if __name__ == "__main__":
    agency.terminal_demo(show_reasoning=False)
    # agency.visualize()
