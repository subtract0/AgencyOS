# Plan: Intelligent Code Generation Suite (CodeGenEngine)

## Overview
Deliver an additive code generation suite that accelerates development via refactor suggestions, test skeleton generation from specs, and pattern-based scaffolding—all deterministic and CI-safe.

## Milestones
- C0: Scaffold module + CLI
- C1: Analyzer rules (basic set) + unit tests
- C2: Spec→tests generator + integration tests
- C3: Scaffolding templates + tests
- C4: Summaries, Telemetry hooks, docs

## Work Breakdown
- Phase 0: Scaffolding
  - tools/codegen/{__init__.py, analyzer.py, test_gen.py, scaffold.py, cli.py}
  - dataclasses for Suggestion, GeneratedTest, CreatedFile
- Phase 1: Analyzer
  - AST visitors for rules: broad-except, long-function (NLOC threshold), dead-code markers (TODO/XXX left behind), public API no type hints
  - Config via simple rules list; severity tagging; JSON report
- Phase 2: Test generation
  - Parse spec Acceptance Criteria from standard template sections
  - Emit tests under tests/generated/<spec_name>/test_ac_*.py
  - Ensure idempotency (overwrite option, or stable regeneration)
- Phase 3: Scaffolding
  - Minimal placeholder templating ({{var}})
  - Built-in templates: tool module skeleton; tests module skeleton
- Phase 4: Integration + docs
  - CLI subcommands (refactor, gen-tests, scaffold)
  - Summaries under logs/codegen/<timestamp>/
  - README with examples; usage in CONTRIBUTING appendix (follow-up)

## Deliverables
- Code: tools/codegen/*
- Tests: tests/tools/test_codegen/*
- Docs: README in module; spec/plan in repo

## Acceptance Criteria
- AC1: Analyzer produces suggestions across 4 rule categories on synthetic fixtures
- AC2: Spec→tests generator creates one test per AC with consistent naming and imports
- AC3: Scaffolding renders a tool module subtree with placeholders replaced
- AC4: CLI commands emit summary.json and summary.md; print artifact paths
- AC5: All tests green; no weakening existing tests

## Risks & Mitigations
- Rule false positives: keep rules conservative; allow per-rule disable
- Parsing variance: adhere to repo spec templates; add unit fixtures
- Churn: outputs additive; no auto-rewrites

## Timeline (target)
- C0–C1: 1–2 days
- C2–C3: 1–2 days
- C4: 0.5 day

## Rollback Plan
Purely additive; safe to disable by not invoking CLI.
