import os

from agency_swarm import Agent
from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    select_instructions_file,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_message_filter_hook, create_memory_integration_hook, create_composite_hook
from tools import (
    LS,
    Read,
    Grep,
    Glob,
    TodoWrite,
)
from .tools.analyze_session import AnalyzeSession
from .tools.extract_insights import ExtractInsights
from .tools.consolidate_learning import ConsolidateLearning
from .tools.store_knowledge import StoreKnowledge

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_learning_agent(model: str = "gpt-5", reasoning_effort: str = "high", agent_context: AgentContext = None) -> Agent:
    """Factory that returns a fresh LearningAgent instance.
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
    combined_hook = create_composite_hook([filter_hook, memory_hook])

    # Log agent creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "LearningAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id
        },
        ["agency", "learning", "creation"]
    )

    return Agent(
        name="LearningAgent",
        description=(
            "A continuous learning specialist that analyzes session transcripts, extracts successful patterns, "
            "and consolidates insights to improve the collective intelligence of the Agency system. "
            "Focuses on tool usage patterns, error resolution strategies, and task completion optimizations."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            LS,
            Read,
            Grep,
            Glob,
            TodoWrite,
            AnalyzeSession,
            ExtractInsights,
            ConsolidateLearning,
            StoreKnowledge,
        ],
        model_settings=create_model_settings(model, reasoning_effort),
    )


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_learning_agent() directly or import and call when needed.