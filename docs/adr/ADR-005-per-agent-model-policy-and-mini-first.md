# ADR-005: Per-Agent Model Policy and Token-Efficient “Mini-First” Strategy

Status: Accepted
Date: 2025-09-27
Ref: 688cf28d-e69c-4624-b7cb-0725f36f9518

Context
- We want to reduce token cost while preserving quality and stability.
- Critical flows (coding, merges, constitutional checks, audits) cannot regress.
- The project rules require: o3 for planning, gpt-5 for coding, verbose fallbacks, and formal ADRs for key decisions.

Decision
1) Centralize model selection with per-agent defaults and environment overrides.
   - Implemented shared/model_policy.py, exposing agent_model(agent_key: str) with safe defaults:
     - planner = o3
     - chief_architect, coder, auditor, quality_enforcer, merger, learning, test_generator = gpt-5
     - summary, subagent_example = gpt-5-mini
   - AGENCY_MODEL provides a global fallback; per-agent env vars override (e.g., CODER_MODEL).
   - agency.py now calls agent_model(...) for each agent.

2) Establish a “mini-first where safe” strategy (foundation only in this change):
   - Use gpt-5-mini for low-risk tasks (summaries, listings, simple transformations).
   - Critical flows remain on gpt-5 by default.
   - Future wiring for guardrails: validation gates will escalate from gpt-5-mini to gpt-5 on failure, with loud logs (per rules).
   - Complexity heuristics (e.g., prompt token thresholds) will skip mini upfront.

Consequences
- Token savings accrue immediately for low-risk agents without risking critical flows.
- Operators can fine-tune per deployment using environment variables.
- The design is reversible and observable; telemetry can track usage and escalation rates.

Alternatives Considered
- Global model toggle: rejected (too coarse, risks quality).
- Deep interception/hook-based fallback on every LLM call today: deferred for now to avoid invasive changes. This ADR lays groundwork.

Implementation Notes
- Code changes are localized to new shared/model_policy.py and agency.py wiring.
- Tests for instruction path selection continue to pass based on model names.
- Future PR will introduce optional guardrails for mini-first execution pathways with explicit validation and escalation.

References
- MCP Identifier (Ref): 688cf28d-e69c-4624-b7cb-0725f36f9518
- Rules: o3 for planning; gpt-5 for coding; verbose fallbacks; no broken windows; ADR required.
