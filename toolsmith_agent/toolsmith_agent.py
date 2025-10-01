import os

from agency_swarm import Agent
from shared.agent_context import AgentContext, create_agent_context
from shared.constitutional_validator import constitutional_compliance
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


@constitutional_compliance
def create_toolsmith_agent(
    model: str = "gpt-5",
    reasoning_effort: str = "high",
    agent_context: AgentContext | None = None,
    cost_tracker = None
) -> Agent:
    """Factory that returns a fresh ToolSmithAgent instance.

    Follows existing patterns: shared AgentContext hooks, instruction selection,
    and model settings. Provides a curated toolset for scaffolding tools, tests,
    and running verification.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
        cost_tracker: Optional CostTracker for real-time LLM cost tracking
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
            "cost_tracker_enabled": cost_tracker is not None
        },
        ["agency", "toolsmith", "creation"],
    )

    # Store cost_tracker in agent context for later use
    if cost_tracker is not None:
        agent_context.cost_tracker = cost_tracker

    # Create agent
    agent = Agent(
        name="ToolSmithAgent",
        description=(
            "PROACTIVE tool development specialist creating reusable, well-tested utilities following TDD methodology. AUTOMATICALLY "
            "triggered when new tool capabilities needed by other agents or workflow automation required. INTELLIGENTLY coordinates with: "
            "(1) PlannerAgent for tool specifications and API design, (2) AgencyCodeAgent for implementation, "
            "(3) TestGeneratorAgent for comprehensive tool testing, (4) AuditorAgent for quality validation, and (5) LearningAgent "
            "to identify tool usage patterns and improvement opportunities. Creates tools using strict TDD: (a) write tests first, "
            "(b) implement minimal functionality, (c) refactor for clarity, (d) document thoroughly. All tools follow Agency Swarm "
            "BaseTool pattern with Pydantic validation, type safety, and error handling via Result pattern. PROACTIVELY suggests "
            "tool improvements based on usage analytics and VectorStore learning patterns. Maintains tool catalog and ensures all "
            "tools have: comprehensive docstrings, usage examples, integration tests, and constitutional compliance. When prompting, "
            "describe tool purpose, inputs/outputs, and integration requirements."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        model_settings=create_model_settings(model, reasoning_effort),
        tools=[Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite],
    )

    # Enable cost tracking if provided
    if cost_tracker is not None:
        from shared.llm_cost_wrapper import wrap_agent_with_cost_tracking
        wrap_agent_with_cost_tracking(agent, cost_tracker)

    return agent
