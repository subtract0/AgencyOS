# Plan 013: Kanban Observability + Learning Board

Owner: PlannerAgent
Timebox: 4 hours
Budget: $10 LLM spend

Approach Summary
- Implement a minimal JSON feed + static HTML Kanban page backed by adapters that consume existing telemetry and learning events.
- Provide a simple Learning Hint Registry (JSON file) and unit tests proving a repeated error produces a Learned hint.
- Add a CLI subcommand "kanban" to run a tiny stdlib HTTP server for local viewing when ENABLE_KANBAN_UI=true.

Design Variants
1) Stdlib HTTP server + static HTML (Chosen)
   - Pros: no new deps, reversible, easy tests
   - Cons: no live push; polling only
2) FastAPI tiny app + static HTML
   - Pros: cleaner routing, JSON schema
   - Cons: new dependency, budget/time risk
3) Reuse existing dashboard CLI
   - Pros: zero new runtime
   - Cons: not a board UI; requires terminal-only experience

Why Variant 1: Best fit for budget/time, minimal surface area, no dependency churn.

Milestones and Budget
- M1 Spec + Plan drafts (0.5h) — $0
- M2 Adapters + tests (1.5h) — $3
- M3 Learning Hint Registry + tests (1.0h) — $3
- M4 Static HTML + stdlib server + CLI subcommand (0.7h) — $2
- M5 Final verification + polish (0.3h) — $2 remainder reserved buffer

Implementation Steps
1) Adapters
   - tools/kanban/adapters.py: build_cards(window: str="1h") -> List[Card]
     - Collect from tools.telemetry.aggregator.list_events
     - Map to Cards per spec; redact sensitive values
     - Optional: merge in patterns from core.patterns.get_pattern_store()
   - tools/kanban/hints.py: LearningHintRegistry for registering and matching hints (JSON persistence under logs/learning/hints.json)
2) Static UI + Server
   - tools/kanban/static/index.html (small HTML/CSS/JS) polling /kanban/cards.json every 5s
   - tools/kanban/server.py: stdlib http.server handler serving index.html and cards.json from adapters
   - agency.py: add subcommand "kanban" to launch server only if ENABLE_KANBAN_UI=true (default port 8765)
3) Tests
   - tests/test_kanban_adapters.py
   - tests/test_learning_hints.py
   - tests/test_kanban_smoke.py (no network; call adapters and registry directly)

Cut Scope Options (if time tight)
- Defer untracked file ingestion to Phase 2; keep flag and stubs
- Skip pattern store merge if unavailable; focus on telemetry-only cards

Risks
- Unexpected test environment constraints; mitigated by stdlib-only server
- Telemetry schema drift; adapter is defensive and ignores unknowns

Success Criteria
- All new tests pass; no regressions
- /kanban/cards.json returns non-empty cards during normal agency activity
- Learned hints are recorded and surfaced on repeat error scenarios
