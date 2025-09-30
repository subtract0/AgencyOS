import os
from contextlib import contextmanager

from tools.anthropic_agent import agent_enabled, get_options_config


@contextmanager
def temp_env(**kwargs):
    old = {k: os.environ.get(k) for k in kwargs}
    try:
        for k, v in kwargs.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_agent_disabled_by_default():
    with temp_env(CLAUDE_AGENT_ENABLE=None):
        assert agent_enabled() is False


def test_system_prompt_preset_parsing():
    with temp_env(CLAUDE_AGENT_SYSTEM_PROMPT=None, CLAUDE_AGENT_SYSTEM_PROMPT_PRESET="claude_code"):
        cfg = get_options_config()
        assert cfg["systemPrompt"] == {"type": "preset", "preset": "claude_code"}


def test_setting_sources_parse():
    with temp_env(CLAUDE_AGENT_SETTING_SOURCES="project,user,local"):
        cfg = get_options_config()
        assert cfg["settingSources"] == ["project", "user", "local"]