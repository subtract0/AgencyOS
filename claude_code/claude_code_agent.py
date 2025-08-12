from agency_swarm import Agent
import os
import platform
from datetime import datetime

from agents import ModelSettings

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_claude_code_agent() -> Agent:
    """Factory that returns a fresh ClaudeCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """

    return Agent(
        name="ClaudeCodeAgent",
        description=(
            "An interactive CLI tool that helps users with software engineering tasks. "
            "Assists with defensive security tasks only. Provides concise, direct, "
            "and to-the-point responses for command line interface interactions."
        ),
        instructions=None,
        tools_folder=os.path.join(current_dir, "tools"),
        model="gpt-5"            
    )

# Backward-compatible singleton export for non-test usage
claude_code_agent = create_claude_code_agent()