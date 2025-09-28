import os

from typing import Optional
from agency_swarm import Agent as _Agent
from shared.agent_context import AgentContext, create_agent_context

# Create module-level alias for Agent to enable proper mocking
# When tests patch 'learning_agent.Agent', this will be the target
Agent = _Agent
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
from .tools.telemetry_pattern_analyzer import TelemetryPatternAnalyzer
from .tools.self_healing_pattern_extractor import SelfHealingPatternExtractor
from .tools.cross_session_learner import CrossSessionLearner

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def create_learning_agent(model: str = "gpt-5", reasoning_effort: str = "high", agent_context: Optional[AgentContext] = None) -> Agent:
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

    # Setup hooks and logging
    combined_hook = _setup_agent_hooks(agent_context)
    _log_agent_creation(agent_context, model, reasoning_effort)

    # Create and return the agent
    return _create_agent_instance(model, reasoning_effort, combined_hook)


def _setup_agent_hooks(agent_context: AgentContext):
    """
    Create and combine all necessary hooks for the learning agent.

    Args:
        agent_context: AgentContext for memory integration

    Returns:
        Combined hook for message filtering and memory integration
    """
    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    return create_composite_hook([filter_hook, memory_hook])


def _log_agent_creation(agent_context: AgentContext, model: str, reasoning_effort: str):
    """
    Log the creation of a new learning agent instance.

    Args:
        agent_context: AgentContext for storing the memory
        model: Model name being used
        reasoning_effort: Reasoning effort level
    """
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


def _create_agent_instance(model: str, reasoning_effort: str, combined_hook) -> Agent:
    """
    Create the actual Agent instance with all configuration.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        combined_hook: Combined hooks for the agent

    Returns:
        Configured Agent instance
    """
    # Handle instructions file fallback gracefully
    try:
        instructions = select_instructions_file(current_dir, model)
    except FileNotFoundError:
        instructions = None  # Agent can handle None instructions

    return Agent(
        name="LearningAgent",
        description=_get_agent_description(),
        instructions=instructions,
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=_get_agent_tools(),
        model_settings=create_model_settings(model, reasoning_effort),
    )


def _get_agent_description() -> str:
    """
    Get the standardized description for the learning agent.

    Returns:
        Agent description string
    """
    return (
        "The institutional memory curator and pattern recognition specialist. Proactively triggered after successful "
        "task completions, error resolutions, or at session end to extract learnings. Analyzes transcripts in "
        "logs/sessions/ to identify reusable patterns, successful strategies, and common pitfalls. Stores consolidated "
        "knowledge in VectorStore for future reference by all agents. When prompting this agent, specify the session "
        "or time range to analyze and any specific patterns to look for. Remember, this agent builds the collective "
        "intelligence that improves agency performance over time and its learnings become institutional memory."
    )


def _get_agent_tools() -> list:
    """
    Get the complete list of tools for the learning agent.

    Returns:
        List of tool classes for the agent
    """
    return [
        LS,
        Read,
        Grep,
        Glob,
        TodoWrite,
        AnalyzeSession,
        ExtractInsights,
        ConsolidateLearning,
        StoreKnowledge,
        TelemetryPatternAnalyzer,
        SelfHealingPatternExtractor,
        CrossSessionLearner,
    ]


# Export classes and functions for testing/mocking
__all__ = [
    'create_learning_agent',
    'Agent',
    'create_agent_context',
    'select_instructions_file',
    'create_model_settings',
    'get_model_instance',
    'create_message_filter_hook',
    'create_memory_integration_hook',
    'create_composite_hook'
]

# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_learning_agent() directly or import and call when needed.