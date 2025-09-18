from agency_swarm import Agent
import os
import platform
from datetime import datetime
from agents import ModelSettings, WebSearchTool
from openai.types.shared.reasoning import Reasoning
from tools import Read, Bash, LS, Grep, Edit, Write, TodoWrite
from agents.extensions.models.litellm_model import LitellmModel

def render_instructions(template_path: str, model: str) -> str:
    with open("frontend_developer/" + template_path, "r") as f:
        content = f.read()
    placeholders = {
        "{cwd}": os.getcwd(),
        "{is_git_repo}": os.path.isdir(".git"),
        "{platform}": platform.system(),
        "{os_version}": platform.release(),
        "{today}": datetime.now().strftime("%Y-%m-%d"),
        "{model}": model,
    }
    for key, value in placeholders.items():
        content = content.replace(key, str(value))
    return content


def create_frontend_developer_agent(
    model: str = "gpt-5", reasoning_effort: str = "low"
) -> Agent:
    is_openai = "gpt" in model
    is_claude = "claude" in model
    is_grok = "grok" in model

    return Agent(
            name="FrontendDeveloper",
            description="A frontend developer that helps with frontend development tasks.",
            instructions=render_instructions("instructions.md", model),
            tools=[
                Read,
                Bash,
                LS,
                Grep,
                Edit,
                Write,
                TodoWrite,
            ],
            model=LitellmModel(model=model) if not is_openai else model,
            model_settings=ModelSettings(
                reasoning=Reasoning(effort=reasoning_effort, summary="detailed")
            )
        )