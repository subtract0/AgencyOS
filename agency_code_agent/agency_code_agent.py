import os

from agency_swarm import Agent

from agents import (
    WebSearchTool,
)
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import create_system_reminder_hook
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
    model: str = "gpt-5-mini", reasoning_effort: str = "medium"
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    is_openai, is_claude, _ = detect_model_type(model)

    instructions_file = select_instructions_file(current_dir, model)
    instructions = render_instructions(instructions_file, model)

    reminder_hook = create_system_reminder_hook()

    return Agent(
        name="AgencyCodeAgent",
        description="An interactive CLI tool that helps users with software engineering tasks.",
        instructions=instructions,
        tools_folder=os.path.join(current_dir, "tools"),
        model=get_model_instance(model),
        hooks=reminder_hook,
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
