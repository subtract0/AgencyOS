from agency_swarm import Agent
import os
from tools import Read, Bash, LS, Grep, Edit, Write, TodoWrite
from shared.agent_utils import (
    render_instructions,
    create_model_settings,
    get_model_instance,
)

def create_subagent_example(
    model: str = "gpt-5", reasoning_effort: str = "low"
) -> Agent:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    instructions = render_instructions(current_dir + "/instructions.md", model)
    return Agent(
        name="SubagentExample",
        description="A template subagent that can be customized for specific domain tasks.",
        instructions=instructions,
        tools=[
            Read,
            Bash,
            LS,
            Grep,
            Edit,
            Write,
            TodoWrite,
        ],
        model=get_model_instance(model),
        model_settings=create_model_settings(model, reasoning_effort, "detailed")
    )