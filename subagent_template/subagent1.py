from agency_swarm import Agent
from agents import ModelSettings, WebSearchTool
from openai.types.shared.reasoning import Reasoning
from tools import Read, Bash, LS, Grep
from agents.extensions.models.litellm_model import LitellmModel

subagent1 = Agent(
        name="Subagent1",
        description=(
            "A strategic planning and task breakdown specialist that helps organize "
            "and structure software development projects into manageable, actionable tasks. "
            "Provides clear project roadmaps and coordinates with the AgencyCodeAgent for execution."
        ),
        instructions="./instructions.md",
        tools=[
            Read,
            Bash,
            LS,
            Grep,
            WebSearchTool(),
        ],
        model=LitellmModel(model="gpt-5"),
        model_settings=ModelSettings(
            reasoning=Reasoning(effort="high", summary="detailed")
        )
    )