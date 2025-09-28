# Import everything from learning_agent module that might need to be mocked
from .learning_agent import (
    create_learning_agent,
    Agent,
    create_agent_context,
    select_instructions_file,
    create_model_settings,
    get_model_instance,
    create_message_filter_hook,
    create_memory_integration_hook,
    create_composite_hook
)

__all__ = [
    "create_learning_agent",
    "Agent",
    "create_agent_context",
    "select_instructions_file",
    "create_model_settings",
    "get_model_instance",
    "create_message_filter_hook",
    "create_memory_integration_hook",
    "create_composite_hook"
]