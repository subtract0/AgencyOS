import os

from agency_swarm import Agent as _Agent

from shared.agent_context import AgentContext, create_agent_context
from shared.constitutional_validator import constitutional_compliance

# Create module-level alias for Agent to enable proper mocking
# When tests patch 'learning_agent.Agent', this will be the target
Agent = _Agent
from shared.agent_utils import (
    create_model_settings,
    get_model_instance,
    select_instructions_file,
)
from shared.system_hooks import (
    create_composite_hook,
    create_memory_integration_hook,
    create_message_filter_hook,
)
from tools import (
    LS,
    Glob,
    Grep,
    Read,
    TodoWrite,
)

from .tools.analyze_session import AnalyzeSession
from .tools.consolidate_learning import ConsolidateLearning
from .tools.cross_session_learner import CrossSessionLearner
from .tools.extract_insights import ExtractInsights
from .tools.self_healing_pattern_extractor import SelfHealingPatternExtractor
from .tools.store_knowledge import StoreKnowledge
from .tools.telemetry_pattern_analyzer import TelemetryPatternAnalyzer

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


@constitutional_compliance
def create_learning_agent(
    model: str = "gpt-5",
    reasoning_effort: str = "high",
    agent_context: AgentContext | None = None,
) -> Agent:
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
            "session_id": agent_context.session_id,
        },
        ["agency", "learning", "creation"],
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
        "PROACTIVE knowledge curator, institutional memory curator, and pattern recognition specialist. Continuously extracts patterns "
        "from all agent sessions, telemetry streams, and autonomous healing operations for cross-session learning. Proactively triggered: "
        "(a) after successful task completions, (b) when error resolutions occur, (c) at session end for consolidation, and (d) on-demand "
        "by PlannerAgent or ChiefArchitectAgent for strategic insights. INTELLIGENTLY coordinates with: ALL AGENTS to collect learning data "
        "and provide pattern-based recommendations, enabling collective intelligence across the multi-agent system to improve agency performance. "
        "Analyzes logs/sessions/ for successful workflows and successful strategies, identifies recurring patterns and common pitfalls (min confidence "
        "0.6, min evidence 3 occurrences), and stores validated learnings and consolidated knowledge in VectorStore for semantic search. PROACTIVELY "
        "suggests: workflow optimizations, cost reduction strategies, quality improvements, and reusable patterns based on historical data. Maintains Article IV "
        "(Continuous Learning) compliance by ensuring all agents benefit from shared knowledge. Uses sentence-transformers for semantic pattern "
        "matching and Firestore for cross-session persistence. When prompting, specify session data or request pattern analysis for specific domain."
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
    "create_learning_agent",
    "Agent",
    "create_agent_context",
    "select_instructions_file",
    "create_model_settings",
    "get_model_instance",
    "create_message_filter_hook",
    "create_memory_integration_hook",
    "create_composite_hook",
]

# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_learning_agent() directly or import and call when needed.
