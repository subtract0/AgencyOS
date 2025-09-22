import os

from agency_swarm import Agent
from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    select_instructions_file,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import (
    create_message_filter_hook,
    create_memory_integration_hook,
    create_composite_hook,
)
from tools import Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite


current_dir = os.path.dirname(os.path.abspath(__file__))


def create_toolsmith_agent(
    model: str = "gpt-5", reasoning_effort: str = "high", agent_context: AgentContext | None = None
) -> Agent:
    """Factory that returns a fresh ToolSmithAgent instance.

    Follows existing patterns: shared AgentContext hooks, instruction selection,
    and model settings. Provides a curated toolset for scaffolding tools, tests,
    and running verification.
    """
    if agent_context is None:
        agent_context = create_agent_context()

    # Hooks: message filter + memory integration
    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([
        filter_hook,
        memory_hook,
    ])

    # Log agent creation in memory for learning
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "ToolSmithAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
        },
        ["agency", "toolsmith", "creation"],
    )

    return Agent(
        name="ToolSmithAgent",
        description=(
            "Meta-agent craftsman that scaffolds, implements, tests, and hands off new tools. "
            "Accepts structured directives to create tools under /tools with matching tests, "
            "runs pytest, and hands off green artifacts to MergerAgent."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
        tools=[Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite],
    )
