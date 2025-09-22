import os

from agency_swarm import Agent

from agents import (
    WebSearchTool,
)
from shared.agent_context import AgentContext, create_agent_context
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import (
    create_system_reminder_hook,
    create_memory_integration_hook,
    create_composite_hook,
)
from tools import (
    LS,
    Bash,
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
    ClaudeWebSearch,
)

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))



def create_agency_code_agent(
    model: str = "gpt-5-mini", reasoning_effort: str = "medium", agent_context: AgentContext = None
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.

    Args:
        model: Model name to use
        reasoning_effort: Reasoning effort level
        agent_context: Optional AgentContext for memory integration
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
    combined_hook = create_composite_hook([
        reminder_hook,
        memory_hook,
    ])

    # Log agent creation
    agent_context.store_memory(
        f"agent_created_{agent_context.session_id}",
        {
            "agent_type": "AgencyCodeAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id
        },
        ["agency", "coder", "creation"]
    )

    return Agent(
        name="AgencyCodeAgent",
        description=(
            "The primary software engineer and implementation specialist. Proactively triggered when code changes are needed, "
            "files require editing, or technical implementation is requested. Executes all hands-on development tasks including "
            "writing, editing, debugging, and testing code. Works from detailed plans provided by the PlannerAgent. "
            "When prompting this agent, provide specific file paths, code requirements, and any architectural constraints. "
            "Remember, this agent has full access to all development tools and is responsible for maintaining code quality standards."
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


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_agency_code_agent() directly or import and call when needed.
