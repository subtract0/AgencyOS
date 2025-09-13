import os

from agency_swarm import Agent
from agents import ModelSettings
from openai.types.shared.reasoning import Reasoning

from system_reminder_hook import create_system_reminder_hook

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


def select_instructions_file(model: str) -> str:
    """Return absolute path to the appropriate instructions file for the model.
    Uses instructions-gpt-5.md for any gpt-5* model, otherwise instructions.md.
    """
    filename = (
        "instructions-gpt-5.md"
        if model.lower().startswith("gpt-5")
        else "instructions.md"
    )
    return os.path.join(current_dir, filename)


def create_planner_agent(model: str = "gpt-5", reasoning_effort: str = "high") -> Agent:
    """Factory that returns a fresh PlannerAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    reminder_hook = create_system_reminder_hook()

    return Agent(
        name="PlannerAgent",
        description=(
            "A strategic planning and task breakdown specialist that helps organize "
            "and structure software development projects into manageable, actionable tasks. "
            "Provides clear project roadmaps and coordinates with the AgencyCodeAgent for execution."
        ),
        instructions=select_instructions_file(model),
        model=model,
        hooks=reminder_hook,
        model_settings=ModelSettings(
            reasoning=Reasoning(effort=reasoning_effort, summary="auto")
            if model.lower().startswith("gpt-5")
            else None,
        ),
    )


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_planner_agent() directly or import and call when needed.
