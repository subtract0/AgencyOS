from agency_swarm import Agent
import os
from agents import WebSearchTool, ModelSettings


# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_agency_code_agent(model: str = "gpt-5", reasoning_effort: str = "high") -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    return Agent(
        name="AgencyCodeAgent",
        description=(
            "An interactive CLI tool that helps users with software engineering tasks. "
            "Assists with defensive security tasks only. Provides concise, direct, "
            "and to-the-point responses for command line interface interactions."
        ),
        # instructions are in shared_instructions.md for agency
        instructions=None,
        tools_folder=os.path.join(current_dir, "tools"),
        model=model,
        # only works with openai models
        tools=[WebSearchTool()],
        model_settings=ModelSettings(
            reasoning={
                "effort": reasoning_effort,
            }
        )         
    )

# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_agency_code_agent() directly or import and call when needed.