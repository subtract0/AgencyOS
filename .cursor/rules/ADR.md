# ADR (Summary) - Per-Agent Model Policy and Mini-First Strategy

Status: Accepted
Date: 2025-09-27
Ref: 688cf28d-e69c-4624-b7cb-0725f36f9518

- Centralized per-agent model selection added at shared/model_policy.py.
- Safe defaults: planner=o3; critical agents=gpt-5; summaries/minor agents=gpt-5-mini.
- AGENCY_MODEL and per-agent env vars allow overrides.
- Agency wiring updated to use policy.
- Future: guarded mini-first with validation and escalation to gpt-5; verbose fallbacks per rule.

See detailed ADR: docs/adr/ADR-005-per-agent-model-policy-and-mini-first.md
