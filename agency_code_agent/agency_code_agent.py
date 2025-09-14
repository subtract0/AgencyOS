import os
import platform
from datetime import datetime

from agency_swarm import Agent
from agents import (
    ModelSettings,
    WebSearchTool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from agents.extensions.models.litellm_model import LitellmModel
from openai import AsyncOpenAI
from openai.types.shared.reasoning import Reasoning

from system_reminder_hook import create_system_reminder_hook
from tools import (
    LS,
    Bash,
    Edit,
    ExitPlanMode,
    Glob,
    Grep,
    MultiEdit,
    NotebookEdit,
    NotebookRead,
    Read,
    Task,
    TodoWrite,
    Write,
)

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


def select_instructions_file(model: str) -> str:
    """Return absolute path to the appropriate instructions file for the model.
    Uses instructions-gpt-5.md for any gpt-5* model, otherwise instructions.md.
    """
    filename = (
        "instructions-gpt-5.md"
        if model.lower().startswith("gpt-5")
        else "instructions.md"
    )
    return os.path.join(current_dir, filename)


def render_instructions(template_path: str, model_name: str) -> str:
    with open(template_path, "r") as f:
        content = f.read()
    placeholders = {
        "{cwd}": os.getcwd(),
        "{is_git_repo}": os.path.isdir(".git"),
        "{platform}": platform.system(),
        "{os_version}": platform.release(),
        "{today}": datetime.now().strftime("%Y-%m-%d"),
        "{model}": model_name,
    }
    for key, value in placeholders.items():
        content = content.replace(key, str(value))
    return content


def create_agency_code_agent(
    model: str = "gpt-5-mini", reasoning_effort: str = "medium"
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    is_openai = "gpt" in model
    is_claude = "claude" in model
    is_grok = "grok" in model

    instructions = render_instructions(select_instructions_file(model), model)

    reminder_hook = create_system_reminder_hook()

    return Agent(
        name="AgencyCodeAgent",
        description="An interactive CLI tool that helps users with software engineering tasks.",
        instructions=instructions,
        tools_folder=os.path.join(current_dir, "tools"),
        model=model if is_openai else LitellmModel(model=model),
        hooks=reminder_hook,
        tools=[
            Task,
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
        ]
        + ([WebSearchTool()] if is_openai else []),
        model_settings=ModelSettings(
            reasoning=(
                Reasoning(effort=reasoning_effort, summary="auto")
                if is_openai
                else None
            ),
            truncation="auto",
            max_tokens=32000,
            extra_body=(
                {"web_search_options": {"search_context_size": "medium"}}
                if is_claude
                else {"search_parameters": {"mode": "on", "returnCitations": True}}
                if is_grok
                else None
            ),
        ),
    )


# Note: We don't create a singleton at module level to avoid circular imports.
# Use create_agency_code_agent() directly or import and call when needed.
