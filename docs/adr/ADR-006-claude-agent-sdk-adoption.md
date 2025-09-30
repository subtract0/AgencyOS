# ADR-006: Adopt Claude Agent SDK (Python) via Env-Gated Wrapper

Date: 2025-09-30

Status: Accepted

## Context
- Claude Code SDK has been renamed to Claude Agent SDK.
- Our repository primarily uses the Claude CLI and GitHub Action; no SDK imports existed.
- We want a minimal, best-practice path to start using the SDK without introducing network calls in tests or hard dependencies on filesystem settings.

## Decision
- Add `claude-agent-sdk>=0.1.0` to `requirements.txt`.
- Introduce `tools/anthropic_agent.py` with:
  - `agent_enabled()` — disabled by default (env: `CLAUDE_AGENT_ENABLE=1` to enable).
  - `get_options_config()` — builds options dict from env (model, systemPrompt preset or string, settingSources).
  - `query_agent(prompt, extra_options=None)` — invokes SDK only when enabled; raises clear errors otherwise.
- Add unit tests that validate environment parsing logic without making network calls.

## Rationale
- Aligns with migration guide breaking changes:
  - No default system prompt; explicitly set via env when desired.
  - Filesystem settings not auto-loaded; opt in via `CLAUDE_AGENT_SETTING_SOURCES`.
- Keeps production safety (no accidental outbound calls) and supports CI determinism.

## Consequences
- To run live queries, users must export:
  - `ANTHROPIC_API_KEY` (secret handled externally)
  - `CLAUDE_AGENT_ENABLE=1`
- Optional behavior can be tuned via:
  - `CLAUDE_AGENT_MODEL` (default `claude-sonnet-4-5`)
  - `CLAUDE_AGENT_SYSTEM_PROMPT` or `CLAUDE_AGENT_SYSTEM_PROMPT_PRESET`
  - `CLAUDE_AGENT_SETTING_SOURCES` (e.g., `project,user,local`)

## Alternatives Considered
- Do nothing (stay CLI-only): simpler but blocks app-level agent usage.
- Full migration with settings auto-loading: conflicts with SDK defaults and CI isolation.

## Links
- Migration Guide: https://docs.claude.com/en/docs/claude-code/sdk/migration-guide
- Agent SDK Overview: https://docs.claude.com/en/api/agent-sdk/overview