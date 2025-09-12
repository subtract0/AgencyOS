import os
import platform
from datetime import datetime

from agency_swarm import Agency
from dotenv import load_dotenv

from agency_code_agent.agency_code_agent import create_agency_code_agent
from planner_agent.planner_agent import create_planner_agent

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))


def render_instructions(template_path: str, model_name: str) -> str:
    with open(template_path, "r") as f:
        content = f.read()
    placeholders = {
        "{cwd}": os.getcwd(),
        "{is_git_repo}": os.path.isdir(".git"),
        "{platform}": platform.system(),
        "{os_version}": platform.release(),
        "{today}": datetime.now().strftime("%Y-%m-%d"),
        "{model}": model_name,
    }
    for key, value in placeholders.items():
        content = content.replace(key, str(value))
    return content


# Create agents
planner = create_planner_agent(model="gpt-5", reasoning_effort="high")
# coder = create_agency_code_agent(model="litellm/anthropic/claude-sonnet-4-20250514")
coder = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="medium")

# Choose shared instructions template based on coder model
shared_template = (
    os.path.join(current_dir, "agency_code_agent", "instructions-gpt-5.md")
    if coder.model.lower().startswith("gpt-5")
    else os.path.join(current_dir, "agency_code_agent", "instructions.md")
)
instructions = render_instructions(shared_template, coder.model)

# Set up mutual handoffs after both agents are created
planner.handoffs = [coder]
coder.handoffs = [planner]

agency = Agency(
    coder,
    shared_instructions=instructions,
)

if __name__ == "__main__":
    agency.terminal_demo()
