import os

from shared.lean_adapter import Agent as _Agent

from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    create_model_settings,
    get_model_instance,
    render_instructions,
    select_instructions_file,
)
from shared.constitutional_validator import constitutional_compliance
from shared.system_hooks import (
    create_composite_hook,
    create_memory_integration_hook,
    create_message_filter_hook,
)

# Create module-level alias for Agent to enable proper mocking
Agent = _Agent

current_dir = os.path.dirname(os.path.abspath(__file__))


@constitutional_compliance
def create_gatekeeper_agent(
    model: str = "gpt-5",
    reasoning_effort: str = "low",
    agent_context: AgentContext | None = None,
) -> Agent:
    """Factory that returns a fresh Gatekeeper agent instance.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
    """
    if agent_context is None:
        agent_context = create_agent_context()

    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([filter_hook, memory_hook])

    agent_context.store_memory(
        f"gatekeeper_agent_created_{agent_context.session_id}",
        {
            "agent_type": "Gatekeeper",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
        },
        ["agency", "gatekeeper", "creation"],
    )

    instructions_file = select_instructions_file(current_dir, model)
    instructions = render_instructions(instructions_file, model)
    model_settings_obj = create_model_settings(model, reasoning_effort)

    return Agent(
        name="Gatekeeper",
        description=(
            "Der ruhige, verständnisvolle Vorraum zu Klara. Initiale Kontaktstelle für User."
            "Validiert Emotionen (Stress, Zynismus), filtert und öffnet sanft die Tür zu Klara."
            "Gibt keine Ratschläge, sondern bietet emotionale Sicherheit und Hand-off."
        ),
        instructions=instructions,
        model=get_model_instance(model),
        hooks=combined_hook,
        temperature=model_settings_obj.temperature if model_settings_obj.temperature is not None else 0.7,
        max_tokens=model_settings_obj.max_tokens if model_settings_obj.max_tokens is not None else 32000,
    )


__all__ = [
    "create_gatekeeper_agent",
    "Agent",
    "create_agent_context",
    "select_instructions_file",
    "create_model_settings",
    "get_model_instance",
    "create_message_filter_hook",
    "create_memory_integration_hook",
    "create_composite_hook",
]
