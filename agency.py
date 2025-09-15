import os

from agency_swarm import Agency
from agency_swarm.tools import SendMessageHandoff
from dotenv import load_dotenv

from agency_code_agent.agency_code_agent import create_agency_code_agent
from planner_agent.planner_agent import create_planner_agent

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))

# Create agents
planner = create_planner_agent(model="gpt-5", reasoning_effort="high")
# coder = create_agency_code_agent(model="gpt-5", reasoning_effort="high")
coder = create_agency_code_agent(model="anthropic/claude-sonnet-4-20250514")

agency = Agency(
    coder,
    communication_flows=[
        (coder, planner, SendMessageHandoff),
        (planner, coder, SendMessageHandoff),
    ],
    shared_instructions="./shared_instructions.md",
)

if __name__ == "__main__":
    agency.terminal_demo()
    # agency.visualize()
