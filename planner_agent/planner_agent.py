import os

from agency_swarm import Agent
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_message_filter_hook

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_planner_agent(model: str = "gpt-5", reasoning_effort: str = "high") -> Agent:
    """Factory that returns a fresh PlannerAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    filter_hook = create_message_filter_hook()

    return Agent(
        name="PlannerAgent",
        description=(
            "A strategic planning and task breakdown specialist that helps organize "
            "and structure software development projects into manageable, actionable tasks. "
            "Provides clear project roadmaps and coordinates with the AgencyCodeAgent for execution."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=filter_hook,
        model_settings=create_model_settings(model, reasoning_effort),
    )


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_planner_agent() directly or import and call when needed.
