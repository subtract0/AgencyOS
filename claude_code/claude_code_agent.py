from agency_swarm import Agent
import os

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

claude_code_agent = Agent(
    name="ClaudeCodeAgent",
    description="An interactive CLI tool that helps users with software engineering tasks. Assists with defensive security tasks only. Provides concise, direct, and to-the-point responses for command line interface interactions.",
    instructions=os.path.join(current_dir, "instructions.md"),
    tools_folder=os.path.join(current_dir, "tools"),
    model="gpt-4o",
)