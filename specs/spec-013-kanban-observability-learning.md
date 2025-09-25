# Spec 013: Kanban Observability + Learning Board

Owner: ChiefArchitectAgent
Status: Draft
Timebox: 4 hours
Budget: $10 LLM spend (tight summaries, low-cost models)

Problem
- Today, discoveries, anomalies, and unexpected errors surface across logs/telemetry/autonomous_healing/memory, but there is no unified, human-friendly view that shows what’s unusual, what became actionable, and what was learned to avoid repeat failures.
- We need a minimal, additive, reversible way to visualize these signals and close the loop from anomaly -> task -> learned remediation, without weakening tests or introducing heavy UI dependencies.

Goals
- Provide a minimal Trello-like Kanban board that shows:
  - To Investigate: new anomalies/errors/unexpected events
  - In Progress: tasks started
  - Learned: extracted patterns, anti-patterns, recommendations
  - Resolved: successfully finished tasks or remediated anomalies
- Convert runtime signals into Cards via adapters (telemetry + learning).
- Demonstrate learning: when the same issue reoccurs, show that a learned hint can be applied to prevent repeat failure (simulated in tests).

Scope (minimal, additive)
- Static HTML + small CSS/JS served by a tiny endpoint (stdlib http.server or minimal FastAPI/Flask if already present; prefer stdlib to avoid deps).
- JSON feed at /kanban/cards.json aggregating recent signals from:
  - Telemetry: logs/telemetry/events-*.jsonl (via tools/telemetry/aggregator.list_events)
  - Learning store: core/patterns.UnifiedPatternStore (enhanced events like pattern_extracted, antipattern_learned)
  - Optional: logs/autonomous_healing/* for additional anomaly signals (best effort)
- Optional opt-in ingestion from untracked files with privacy filters.

Data Model (Card)
- id: string (stable hash of source + ts)
- type: one of {error, task, pattern, antipattern, discovery}
- title: short human label
- summary: brief description (<= 200 chars)
- source_ref: reference to origin (event id, file path)
- status: one of {To Investigate, In Progress, Learned, Resolved}
- created_at: ISO timestamp
- links: [urls]
- tags: [strings]

Event-to-Card Mapping
- task_started -> type=task, status=In Progress, title="Task started: {agent/id}"
- task_finished status=success -> type=task, status=Resolved, title="Task success: {agent/id}"
- task_finished status in {failed, timeout} -> type=error, status=To Investigate, title="Task failed: {agent/id}"; summary from error fields if present
- pattern_extracted or pattern_store.pattern_added -> type=pattern, status=Learned
- antipattern_learned -> type=antipattern, status=Learned
- Any telemetry event containing typical error keys (error, exception) -> type=error, status=To Investigate

Learning Hint Registry
- A small, versioned JSON registry mapping pattern triggers to safe remediations.
- Format (JSON):
  {
    "version": 1,
    "hints": [
      {"match": {"error_type": "ModuleNotFoundError"}, "action": {"env": {"PYTHONPATH_APPEND": "src"}, "args": []}, "confidence": 0.5},
      {"match": {"error_pattern": "AttributeError.*NoneType"}, "action": {"code_hint": "add null check"}, "confidence": 0.4}
    ]
  }
- Runtime application is opt-in and conservative: hints can be surfaced in Kanban and optionally exported for application by hooks.

Configuration Flags
- ENABLE_KANBAN_UI=true|false (default false): enable serving the UI endpoint
- LEARNING_UNTRACKED=true|false (default false): allow ingestion of selected untracked files (with privacy filters)
- KANBAN_PORT (default 8765)

API Endpoints
- GET /kanban/cards.json: returns { cards: [Card, ...], generated_at: iso }
- GET /kanban: serves static HTML/JS page (reads cards.json periodically)

Security & Privacy
- No secrets in UI. Redact any suspected secrets from summaries.
- Untracked ingestion off by default; when on, apply allowlist globs and redact tokens/keys.

Acceptance Criteria
1) Adapter unit tests:
   - Given synthetic telemetry events, produces correct Cards and statuses.
   - Redacts sensitive keys in summaries.
2) Learning registry unit tests:
   - Can register a hint; persists to JSON; loads it back; matches on a repeat error.
3) Smoke test (no server):
   - Simulate an error event; simulate a learned pattern; assert Learned card appears and subsequent identical error is flagged with an available hint.
4) No test weakening; entire suite stays green.

Out of Scope (for this iteration)
- Real-time websockets; multi-user auth; persistent UI state; heavy frontend frameworks.

Rollout
- Default off behind ENABLE_KANBAN_UI.
- Purely additive files; minimal changes to agency.py to add a "kanban" CLI subcommand.

Reversibility
- Remove the /tools/kanban/* and CLI subcommand to revert. No API breaks.
