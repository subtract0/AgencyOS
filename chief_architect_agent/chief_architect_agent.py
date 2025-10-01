import os
from agency_swarm import Agent
from shared.agent_context import AgentContext, create_agent_context
from shared.constitutional_validator import constitutional_compliance
from shared.agent_utils import select_instructions_file, create_model_settings, get_model_instance
from shared.system_hooks import (
    create_message_filter_hook,
    create_memory_integration_hook,
    create_composite_hook,
)
from tools import LS, Read, Grep, Glob, TodoWrite, Write, Edit, Bash, ContextMessageHandoff
from .tools.architecture_loop import RunArchitectureLoop

current_dir = os.path.dirname(os.path.abspath(__file__))


@constitutional_compliance
def create_chief_architect_agent(model: str = "gpt-5", reasoning_effort: str = "high", agent_context: AgentContext | None = None) -> Agent:
    if agent_context is None:
        agent_context = create_agent_context()

    filter_hook = create_message_filter_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([
        filter_hook,
        memory_hook,
    ])

    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "ChiefArchitectAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
        },
        ["agency", "chief_architect", "creation"],
    )

    return Agent(
        name="ChiefArchitectAgent",
        description=(
            "PROACTIVE strategic oversight and self-directed task creation authority. Highest-level architectural decision maker "
            "and ADR (Architecture Decision Record) creator. AUTOMATICALLY monitors system health, quality metrics, and strategic "
            "alignment. INTELLIGENTLY coordinates with: (1) PlannerAgent for specification reviews, (2) LearningAgent for pattern "
            "analysis and strategic insights, (3) AuditorAgent for system-wide quality assessments, (4) QualityEnforcer for "
            "constitutional compliance enforcement, and (5) ALL AGENTS for architectural guidance. PROACTIVELY creates: ADRs for "
            "major decisions (stored in docs/adr/), strategic refactoring plans, technical debt reduction strategies, and long-term "
            "architecture evolution roadmaps. Uses self-directed task creation to initiate improvements without user prompting when "
            "quality thresholds breached or architectural drift detected. Enforces Article V (spec-driven development) by ensuring "
            "all complex features have formal specifications. Maintains ADR index, conducts architectural reviews, and provides "
            "strategic guidance to all agents. When prompting, describe architectural challenges, technology decisions, or request "
            "strategic planning. Uses high reasoning effort for critical architectural decisions."
        ),
        instructions=select_instructions_file(current_dir, model),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[LS, Read, Grep, Glob, TodoWrite, Write, Edit, Bash, ContextMessageHandoff, RunArchitectureLoop],
        tools_folder=os.path.join(current_dir, "tools"),
        model_settings=create_model_settings(model, reasoning_effort),
    )
