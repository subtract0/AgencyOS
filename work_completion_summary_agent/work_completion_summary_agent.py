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

current_dir = os.path.dirname(os.path.abspath(__file__))


def create_work_completion_summary_agent(
    model: str = "gpt-5", reasoning_effort: str = "low", agent_context: AgentContext | None = None
) -> Agent:
    """Factory to create the WorkCompletionSummaryAgent.

    Proactively triggered when work is completed to provide concise audio summaries and suggest next steps.
    If they say 'tts' or 'tts summary' or 'audio summary' use this agent. When you prompt this agent, describe
    exactly what you want them to communicate to the user. Remember, this agent has no context about any
    questions or previous conversations between you and the user.
    """
    if agent_context is None:
        agent_context = create_agent_context()

    # Hooks (memory + filter)
    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([filter_hook, memory_hook])

    # Log creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "WorkCompletionSummaryAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
        },
        ["agency", "summary", "creation"],
    )

    return Agent(
        name="WorkCompletionSummaryAgent",
        description=(
            "Proactively triggered when work is completed to provide concise audio summaries and suggest next steps. "
            "If they say 'tts' or 'tts summary' or 'audio summary' use this agent. When you prompt this agent, describe "
            "exactly what you want them to communicate to the user. Remember, this agent has no context about any "
            "questions or previous conversations between you and the user."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
        tools=[],
    )
