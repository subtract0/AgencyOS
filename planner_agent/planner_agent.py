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

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_planner_agent(model: str = "gpt-5", reasoning_effort: str = "high", agent_context: AgentContext = None) -> Agent:
    """Factory that returns a fresh PlannerAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
    """
    # Create agent context if not provided
    if agent_context is None:
        agent_context = create_agent_context()

    # Create hooks with memory integration
    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([
        filter_hook,
        memory_hook,
    ])

    # Log agent creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "PlannerAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id
        },
        ["agency", "planner", "creation"]
    )

    return Agent(
        name="PlannerAgent",
        description=(
            "The strategic architect and task orchestrator. Proactively triggered when tasks require breakdown into steps, "
            "complex features need planning, or when the user requests architectural guidance. Creates formal specifications "
            "in /specs/ and technical plans in /plans/ following constitutional requirements. Coordinates bidirectional "
            "handoffs with AgencyCodeAgent for implementation. When prompting this agent, describe the high-level goals "
            "and any constraints or requirements. Remember, this agent specializes in spec-driven development and maintains "
            "project-wide consistency."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
    )


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_planner_agent() directly or import and call when needed.
