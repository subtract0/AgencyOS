import os
from typing import Optional

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
from tools import (
    Bash,
    GitUnified,
    Read,
    Grep,
    Glob,
    TodoWrite,
)

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


@constitutional_compliance
def create_merger_agent(
    model: str = "gpt-5",
    reasoning_effort: str = "high",
    agent_context: Optional[AgentContext] = None,
    cost_tracker = None
) -> Agent:
    """Factory that returns a fresh MergerAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
        cost_tracker: Optional CostTracker for real-time LLM cost tracking
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
            "agent_type": "MergerAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
            "cost_tracker_enabled": cost_tracker is not None
        },
        ["agency", "merger", "creation"]
    )

    # Store cost_tracker in agent context for later use
    if cost_tracker is not None:
        agent_context.cost_tracker = cost_tracker

    # Create agent
    agent = Agent(
        name="MergerAgent",
        description=(
            "PROACTIVE integration and release management specialist with Git workflow automation. Acts as the quality gatekeeper - final "
            "quality gate before code reaches main branch. AUTOMATICALLY triggered when AgencyCodeAgent completes implementation and tests pass. "
            "INTELLIGENTLY coordinates with: (1) QualityEnforcerAgent for final constitutional compliance check, "
            "(2) TestGeneratorAgent to verify 100% test success requirement, (3) AuditorAgent for pre-merge quality validation, "
            "and (4) WorkCompletionSummaryAgent for change documentation. PROACTIVELY performs: (a) git status/diff analysis, "
            "(b) test suite validation via run_tests.py --run-all, (c) lint checking, (d) constitutional compliance verification, "
            "(e) intelligent commit message generation following repository conventions. Creates pull requests with comprehensive "
            "summaries, test plans, and constitutional compliance attestations. Enforces ADR-002 (Article II: 100% tests pass) and "
            "Article III (automated enforcement - no bypasses) at merge time. Uses gh CLI for PR operations and maintains full audit trails. "
            "NEVER allows merges without green CI and 100% test success - has non-negotiable veto power to block merges. When prompting, provide task context and changes to integrate."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            Bash,
            GitUnified,
            Read,
            Grep,
            Glob,
            TodoWrite,
        ],
        model_settings=create_model_settings(model, reasoning_effort),
    )

    # Enable cost tracking if provided
    if cost_tracker is not None:
        from shared.llm_cost_wrapper import wrap_agent_with_cost_tracking
        wrap_agent_with_cost_tracking(agent, cost_tracker)

    return agent


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_merger_agent() directly or import and call when needed.