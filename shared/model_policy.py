import os

# Centralized per-agent model selection with environment overrides.
# Safe defaults prioritize quality-critical agents on gpt-5 and
# allow cost-saving agents to use gpt-5-mini.
#
# Env variables (optional):
# - AGENCY_MODEL: global fallback (default: gpt-5)
# - <AGENT>_MODEL per agent key below (e.g., CODER_MODEL, SUMMARY_MODEL, ...)
#
# Agent keys supported:
#   planner, chief_architect, coder, auditor, quality_enforcer,
#   merger, learning, test_generator, summary, subagent_example, toolsmith
#
# Note: Planner defaults to `o3` per user rule; others stick to gpt-5 except
# where low-risk summaries use gpt-5-mini by default.

DEFAULT_GLOBAL = os.getenv("AGENCY_MODEL", "gpt-5")

DEFAULTS: dict[str, str] = {
    "planner": os.getenv("PLANNER_MODEL", "o3"),
    "chief_architect": os.getenv("CHIEF_ARCHITECT_MODEL", "gpt-5"),
    "coder": os.getenv("CODER_MODEL", "gpt-5"),
    "auditor": os.getenv("AUDITOR_MODEL", "gpt-5"),
    "quality_enforcer": os.getenv("QUALITY_ENFORCER_MODEL", "gpt-5"),
    "merger": os.getenv("MERGER_MODEL", "gpt-5"),
    "learning": os.getenv("LEARNING_MODEL", "gpt-5"),
    "test_generator": os.getenv("TEST_GENERATOR_MODEL", "gpt-5"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-5-mini"),
    "subagent_example": os.getenv("SUBAGENT_EXAMPLE_MODEL", "gpt-5-mini"),
    "toolsmith": os.getenv("TOOLSMITH_MODEL", "gpt-5"),
}


def agent_model(agent_key: str) -> str:
    """Return the model for a given agent key with sane defaults.

    If an unknown key is provided, fall back to DEFAULT_GLOBAL.
    """
    return DEFAULTS.get(agent_key, DEFAULT_GLOBAL)