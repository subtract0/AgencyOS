"""
Minimal wrapper for the Claude Agent SDK with safe, env-gated defaults.

- Disabled by default (no network calls unless explicitly enabled)
- Reads configuration from environment variables
- Provides a simple query function when enabled

Environment variables:
- CLAUDE_AGENT_ENABLE: '1'/'true' to enable live calls (default: disabled)
- CLAUDE_AGENT_MODEL: model name (default: 'claude-sonnet-4-5')
- CLAUDE_AGENT_SYSTEM_PROMPT: custom system prompt string
- CLAUDE_AGENT_SYSTEM_PROMPT_PRESET: preset name, e.g., 'claude_code'
- CLAUDE_AGENT_SETTING_SOURCES: comma-separated list like 'project,user,local'

Secrets:
- Uses ANTHROPIC_API_KEY from the environment; do not print or echo it.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional
from shared.type_definitions.json import JSONValue

try:
    # Import is optional until enabled
    from claude_agent_sdk import query  # type: ignore
except Exception:  # pragma: no cover - optional dep may not be available at import time
    query = None  # type: ignore[assignment]


TRUE_VALUES = {"1", "true", "yes", "on"}


def agent_enabled() -> bool:
    """Return True if live Agent SDK calls are enabled by env flag.

    Default is disabled for safety and reproducibility.
    """
    return str(os.getenv("CLAUDE_AGENT_ENABLE", "")).strip().lower() in TRUE_VALUES


def _parse_setting_sources(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def get_options_config() -> Dict[str, JSONValue]:
    """Build a plain dict of options for the Claude Agent SDK.

    We avoid relying on the SDK's typed classes here so this function
    remains importable even if the SDK isn't installed yet.
    """
    cfg: Dict[str, JSONValue] = {}

    # Model
    cfg["model"] = os.getenv("CLAUDE_AGENT_MODEL", "claude-sonnet-4-5")

    # System prompt logic
    sys_str = os.getenv("CLAUDE_AGENT_SYSTEM_PROMPT")
    sys_preset = os.getenv("CLAUDE_AGENT_SYSTEM_PROMPT_PRESET")
    if sys_str:
        cfg["systemPrompt"] = sys_str
    elif sys_preset:
        cfg["systemPrompt"] = {"type": "preset", "preset": sys_preset}

    # Settings sources (project/user/local) are not loaded by default in new SDK
    sources = os.getenv("CLAUDE_AGENT_SETTING_SOURCES")
    if sources:
        cfg["settingSources"] = _parse_setting_sources(sources)

    return cfg


def query_agent(prompt: str, extra_options: Optional[Dict[str, JSONValue]] = None) -> Any:
    """Execute a simple query via the Claude Agent SDK when enabled.

    - Respects agent_enabled() flag
    - Merges extra_options into base options
    - Raises helpful errors when the SDK isn't installed or when disabled
    """
    if not agent_enabled():
        raise RuntimeError(
            "Claude Agent SDK is disabled. Set CLAUDE_AGENT_ENABLE=1 to enable."
        )

    if query is None:  # SDK not importable
        raise ImportError(
            "claude-agent-sdk is not installed. Ensure requirements are installed."
        )

    options: Dict[str, JSONValue] = get_options_config()
    if extra_options:
        options.update(extra_options)

    # Delegate to SDK. The SDK accepts options as a dict.
    return query(prompt=prompt, options=options)


__all__ = [
    "agent_enabled",
    "get_options_config",
    "query_agent",
]