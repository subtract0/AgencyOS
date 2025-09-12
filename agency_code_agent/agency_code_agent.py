import os

from agency_swarm import Agent
from agents import (
    ModelSettings,
    WebSearchTool,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from openai.types.shared.reasoning import Reasoning

from tools import (
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


def create_agency_code_agent(
    model: str = "gpt-5-mini", reasoning_effort: str = "medium"
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    is_openai = "gpt" in model
    is_claude = "claude" in model
    is_grok = "grok" in model

    if not is_openai:
        BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:4000")
        api_key = os.getenv("OPENAI_API_KEY", "")
        client = AsyncOpenAI(base_url=BASE_URL, api_key=api_key)
        set_default_openai_client(client)
        set_tracing_disabled(disabled=True)
        set_default_openai_api("chat_completions")

    return Agent(
        name="AgencyCodeAgent",
        description="An interactive CLI tool that helps users with software engineering tasks.",
        instructions=select_instructions_file(model),
        tools_folder=os.path.join(current_dir, "tools"),
        model=model,
        openai_client=None if is_openai else client,
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
        ] + ([WebSearchTool()] if is_openai else []),
        model_settings=ModelSettings(
            reasoning=Reasoning(effort=reasoning_effort) if is_openai else None,
            truncation="auto",
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
