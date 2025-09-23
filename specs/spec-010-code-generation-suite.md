# Spec: Intelligent Code Generation Suite (CodeGenEngine)

## Problem
Manual coding loops slow delivery and increase risk of drift between specs, plans, code, and tests. We need an additive, low-churn suite that accelerates development without weakening tests or introducing heavy dependencies.

## Goals
- Smart refactoring suggestions based on static analysis and repository conventions
- Automatic test generation from specs/plans (acceptance criteria → test skeletons)
- Code optimization recommendations (complexity heuristics, hotspots)
- Pattern-based scaffolding for new tools and modules aligned with our templates
- Deterministic behavior, reproducible outputs, and integration with Telemetry/Orchestrator

## Non-Goals (MVP)
- Auto-applying refactors (no in-place code rewriting in MVP)
- Full language server, IDE integration, or complex ML models
- Cross-language support beyond Python repository scope

## Requirements
- Python API
  - from tools.codegen import suggest_refactors, generate_tests_from_spec, scaffold_module
  - suggest_refactors(paths: list[str], rules?: list[str]) -> list[Suggestion]
  - generate_tests_from_spec(spec_path: str, out_dir: str) -> list[GeneratedTest]
  - scaffold_module(template: str, name: str, out_dir: str, params?: dict) -> list[CreatedFile]
- CLI
  - python -m tools.codegen refactor --paths "agency/**.py" --rules basic
  - python -m tools.codegen gen-tests --spec specs/spec-008-orchestrator-engine.md --out tests/generated
  - python -m tools.codegen scaffold --template tool --name orchestrator --out tools/orchestrator
- Data
  - Suggestion: {path, line, severity, rule_id, message, fix_hint?, diff?}
  - GeneratedTest: {path, ac_id, name, status}
  - CreatedFile: {path, template, status}
- Features (MVP)
  1) Refactor suggestions: stdlib AST-based detection of anti-patterns (dead code markers, broad exception catches, long functions, missing type hints in public APIs)
  2) Test generation: parse spec Acceptance Criteria and produce pytest skeletons mapping AC→test_* names with TODOs and sane imports
  3) Scaffolding: render module/file trees from lightweight Jinja-free templates using simple {{var}} placeholders (no heavy deps)
  4) Reports: write summary.json and summary.md under logs/codegen/<timestamp>/
  5) Telemetry: emit llm_call/tool_use=codegen events (no LLM calls in MVP; events still emitted for consistency)
- Compatibility
  - No changes to existing agent APIs; outputs are suggestions and files to be reviewed
  - Integrate with OrchestratorEngine for parallel operations across paths/specs
  - Local-first; minimal dependencies
- Security
  - No secret leakage; scrub env-like strings in generated artifacts
  - Do not read credentials/

## Architecture
- Module: tools/codegen/{__init__.py, analyzer.py, test_gen.py, scaffold.py, cli.py}
- analyzer.py: AST visitors for rule set; configurability via simple rule IDs
- test_gen.py: spec parser (headings, Acceptance Criteria list) → pytest skeletons
- scaffold.py: template renderer + predefined templates (tool, tests)
- cli.py: argparse subcommands (refactor, gen-tests, scaffold)

## Risks & Mitigations
- Over-prescriptive suggestions → keep severity tagging and opt-in rules
- Parsing brittleness → rely on headings and standard spec templates already in repo
- Churn risk → outputs are additive; do not auto-edit existing files

## Testing Strategy
- Unit: analyzer rules, spec parsing, template rendering
- Integration: run gen-tests on a sample spec and assert file outputs; verify idempotency
- Deterministic tests; no network calls

## Acceptance Criteria
- AC1: Refactor suggestions detect at least 4 rule categories (broad except, long func, dead-code markers, missing type hints) on synthetic fixtures
- AC2: generate_tests_from_spec produces pytest skeletons mapping each acceptance criterion to a test function stub with consistent naming
- AC3: scaffold_module renders a simple tool skeleton into a temp dir with correct placeholders
- AC4: CLI commands produce summary.json and summary.md; paths printed to stdout
- AC5: Tests deterministic and CI-green; no weakening of existing tests

## Success Metrics
- <2 minutes to generate tests from a typical spec
- Zero flakes introduced
- Positive delta in test coverage in follow-up PRs that adopt generated skeletons
