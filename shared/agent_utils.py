import os
import platform
from datetime import datetime
from typing import Optional

from agents import ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from openai.types.shared.reasoning import Reasoning


def detect_model_type(model: str) -> tuple[bool, bool, bool]:
    """Detect model type and return (is_openai, is_claude, is_grok)."""
    is_openai = "gpt" in model
    is_claude = "claude" in model
    is_grok = "grok" in model
    return is_openai, is_claude, is_grok


def select_instructions_file(base_dir: str, model: str) -> str:
    """Return absolute path to the appropriate instructions file for the model.
    Uses instructions-gpt-5.md for any gpt-5* model, otherwise instructions.md.
    """
    filename = (
        "instructions-gpt-5.md"
        if model.lower().startswith("gpt-5")
        else "instructions.md"
    )
    return os.path.join(base_dir, filename)


def render_instructions(template_path: str, model: str, base_path: Optional[str] = None) -> str:
    """Render instructions template with placeholders replaced."""
    if base_path:
        full_path = os.path.join(base_path, template_path)
    else:
        full_path = template_path

    with open(full_path, "r") as f:
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


def create_model_settings(
    model: str,
    reasoning_effort: str = "medium",
    reasoning_summary: str = "auto",
    max_tokens: int = 32000,
) -> ModelSettings:
    """Create ModelSettings with appropriate configuration for the model type."""
    is_openai, is_claude, is_grok = detect_model_type(model)

    return ModelSettings(
        reasoning=(
            Reasoning(effort=reasoning_effort, summary=reasoning_summary)
            if is_openai or is_claude
            else None
        ),
        truncation="auto",
        max_tokens=max_tokens,
        extra_body=(
            {"search_parameters": {"mode": "on", "returnCitations": True}}
            if is_grok
            else None
        ),
    )


def get_model_instance(model: str):
    """Get the appropriate model instance based on model type."""
    is_openai, _, _ = detect_model_type(model)
    return model if is_openai else LitellmModel(model=model)