from agency_swarm import Agency
from claude_code_agent import claude_code_agent
import os
import platform
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))

from dotenv import load_dotenv
load_dotenv()

with open(os.path.join(current_dir, "instructions.md"), "r") as f:
    instructions = f.read()
    instructions = instructions.format(
        cwd=os.getcwd(),
        is_git_repo=os.path.isdir(".git"),
        platform=platform.system(),
        os_version=platform.release(),
        today=datetime.now().strftime("%Y-%m-%d")
    )

agency = Agency(
    claude_code_agent,
    communication_flows=[],
    shared_instructions=instructions,
)

if __name__ == "__main__":
    agency.terminal_demo()