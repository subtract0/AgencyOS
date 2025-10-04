# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
import os

from agency_swarm import Agent
from agents import (
    WebSearchTool,
)

from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    create_model_settings,
    detect_model_type,
    get_model_instance,
    render_instructions,
    select_instructions_file,
)
from shared.constitutional_validator import constitutional_compliance
from shared.system_hooks import (
    create_composite_hook,
    create_memory_integration_hook,
    create_system_reminder_hook,
)
from tools import (
    LS,
    Bash,
    ClaudeWebSearch,
    Edit,
    ExitPlanMode,
    Git,
    Glob,
    Grep,
    MultiEdit,
    NotebookEdit,
    NotebookRead,
    Read,
    TodoWrite,
    Write,
)

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


@constitutional_compliance
def create_agency_code_agent(
    model: str = "gpt-5-mini",
    reasoning_effort: str = "medium",
    agent_context: AgentContext = None,
    cost_tracker=None,
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
        cost_tracker: Optional CostTracker for real-time LLM cost tracking
    """
    is_openai, is_claude, _ = detect_model_type(model)

    instructions_file = select_instructions_file(current_dir, model)
    instructions = render_instructions(instructions_file, model)

    # Create agent context if not provided
    if agent_context is None:
        agent_context = create_agent_context()

    # Create hooks with memory integration
    reminder_hook = create_system_reminder_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook(
        [
            reminder_hook,
            memory_hook,
        ]
    )

    # Log agent creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "AgencyCodeAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
            "cost_tracker_enabled": cost_tracker is not None,
        },
        ["agency", "coder", "creation"],
    )

    # Store cost_tracker in agent context for later use
    if cost_tracker is not None:
        agent_context.cost_tracker = cost_tracker

    # Create agent
    agent = Agent(
        name="AgencyCodeAgent",
        description=(
            "PROACTIVE primary software engineer and implementation specialist with autonomous coordination capabilities. "
            "Intelligently triggered when code changes, file edits, or technical implementation is needed. AUTOMATICALLY coordinates "
            "with: (1) PlannerAgent for specifications and strategic guidance, (2) TestGeneratorAgent for TDD test-first development, "
            "(3) QualityEnforcerAgent for constitutional Article II compliance (100% verification), (4) AuditorAgent for quality validation, "
            "and (5) MergerAgent for integration. Executes all hands-on development using strict TDD methodology and Result<T,E> pattern. "
            "PROACTIVELY suggests improvements, refactorings, and optimizations based on VectorStore learning patterns and shared memory. "
            "Maintains real-time cost tracking for all LLM operations and enforces zero Dict[Any, Any] usage per constitutional requirements. "
            "Works from detailed plans in /plans/ and ensures all code meets Article II (100% test success) before handoff to MergerAgent. "
            "When prompting, provide file paths, code requirements, and architectural constraints. Has full tool access including Git, "
            "file operations, web search, and TodoWrite for task coordination."
        ),
        instructions=instructions,
        tools_folder=os.path.join(current_dir, "tools"),
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            Bash,
            Glob,
            Grep,
            LS,
            ExitPlanMode,
            Read,
            Edit,
            MultiEdit,
            Write,
            NotebookRead,
            NotebookEdit,
            TodoWrite,
            Git,
        ]
        + ([WebSearchTool()] if is_openai else [])
        + ([ClaudeWebSearch] if is_claude else []),
        model_settings=create_model_settings(model, reasoning_effort),
    )

    # Enable cost tracking if provided
    if cost_tracker is not None:
        from shared.llm_cost_wrapper import wrap_agent_with_cost_tracking

        wrap_agent_with_cost_tracking(agent, cost_tracker)

    return agent


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_agency_code_agent() directly or import and call when needed.
