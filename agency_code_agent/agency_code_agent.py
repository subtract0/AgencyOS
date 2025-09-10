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

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


def create_agency_code_agent(
    model: str = "gpt-5", reasoning_effort: str = "high"
) -> Agent:
    """Factory that returns a fresh AgencyCodeAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    is_openai = "gpt" in model
    is_claude = "claude" in model
    is_grok = "grok" in model

    if not is_openai:
        BASE_URL = "http://localhost:4000"
        client = AsyncOpenAI(base_url=BASE_URL, api_key="any-key")
        set_default_openai_client(client)
        set_tracing_disabled(disabled=True)
        set_default_openai_api("chat_completions")

    return Agent(
        name="AgencyCodeAgent",
        description=(
            "An interactive CLI tool that helps users with software engineering tasks. "
            "Assists with defensive security tasks only. Provides concise, direct, "
            "and to-the-point responses for command line interface interactions."
        ),
        # instructions are in shared_instructions.md for agency
        instructions=None,
        tools_folder=os.path.join(current_dir, "tools"),
        model=model,
        openai_client=None if is_openai else client,
        # Only works with OpenAI models
        tools=[WebSearchTool()] if is_openai else [],
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
