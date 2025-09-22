# Technical Plan: ToolSmithAgent — Meta-Agent for Tool Creation and Deployment

**Plan ID**: `plan-007-toolsmith-agent`
**Spec Reference**: `spec-007-toolsmith-agent.md`
**Status**: Draft
**Author**: PlannerAgent (delegated by ChiefArchitectAgent)
**Created**: 2025-09-22
**Last Updated**: 2025-09-22
**Implementation Start**: 2025-09-22
**Target Completion**: 2025-09-22

---

## Executive Summary

Implement ToolSmithAgent following existing factory and hook patterns. Equip it to receive a structured Tool Directive, scaffold a new tool under `tools/`, generate a corresponding test under `tests/`, run pytest, and when green, hand off to MergerAgent. The initial directive is to add `ContextMessageHandoff`, an additive handoff tool capable of packaging a mission prompt and context for the recipient agent.

---

## Architecture Overview

### High-Level Design
```
┌──────────────────┐    Tool Directive     ┌───────────────────────────┐
│ ChiefArchitect   │ ───────────────────▶ │      ToolSmithAgent       │
└──────────────────┘                       │  (scaffold → test → run)  │
                                          └───────────┬───────────────┘
                                                      │
                                      ┌───────────────▼───────────────┐
                                      │   tools/context_handoff.py    │
                                      │   tests/test_context_*.py     │
                                      └───────────────┬───────────────┘
                                                      │
                                           ┌──────────▼─────────┐
                                           │    MergerAgent     │
                                           │ (verify + integrate) │
                                           └────────────────────┘
```

### Key Components

#### Component 1: ToolSmithAgent
- Purpose: Meta-agent that builds tools + tests and runs verification
- Responsibilities: Parse directive; write files; edit exports; run tests; handoff to MergerAgent
- Dependencies: BaseTool conventions, pytest, existing tool exports
- Interfaces: `create_toolsmith_agent(...)`

#### Component 2: ContextMessageHandoff Tool
- Purpose: Provide mission handoff with prompt + context persistence
- Responsibilities: Validate inputs; write context payload; return deterministic summary
- Dependencies: Standard library (os, json, datetime, pathlib), BaseTool
- Interfaces: Pydantic fields; `run()` returns summary string

### Data Flow
```
Directive → Scaffolding → Test Generation → Pytest Run → Handoff (Merger)
  ↓             ↓                ↓              ↓             ↓
validate    write files     create tests     parse results   send summary
```

---

## Agent Assignments

### Primary Agent: ToolSmithAgent
- Role: Master craftsman (tool creation/testing)
- Tasks:
  - Implement factory and instructions
  - Parse directives and scaffold files
  - Update `tools/__init__.py`
  - Generate tests and run pytest
  - Handoff to MergerAgent when green
- Tools Required: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite
- Deliverables: `toolsmith_agent/` package, new tool + tests, green test run

### Supporting Agent: MergerAgent
- Role: Final verification and integration
- Tasks:
  - Re-run full test suite
  - Enforce ADR-002 gates
- Tools Required: Bash, Git, Read, Grep, Glob, TodoWrite
- Deliverables: Merge approval or actionable failures

### Agent Communication Flow
```
PlannerAgent → ToolSmithAgent → MergerAgent
     ↓                ↓               ↓
  Spec/Plan      Implementation     Verification
```

---

## Tool Requirements

### Core Tools
- Read: load templates and verify exports
- Write/Edit/MultiEdit: create and modify files
- Grep/Glob: discover insertion points and validate presence
- Bash: run pytest and quality commands
- TodoWrite: task breakdown and tracking

### Specialized Tools
- None (additive; uses existing toolkit)

### Tool Integration Patterns
```python
# Example: append export to tools/__init__.py
# Find insertion point and add class + alias to __all__
```

---

## Contracts & Interfaces

### Internal APIs

#### create_toolsmith_agent
```python
def create_toolsmith_agent(model: str = "gpt-5", reasoning_effort: str = "high", agent_context: AgentContext | None = None) -> Agent:
    """Return a ToolSmithAgent configured with memory + filter hooks."""
```

#### Tool Directive Schema (in practice: dict validated at runtime)
```json
{
  "name": "ContextMessageHandoff",
  "module_path": "tools/context_handoff.py",
  "description": "Handoff with mission prompt + structured context",
  "parameters": {"target_agent": "str", "prompt": "str", "context": "dict|str", "tags": "list[str]|None", "persist": "bool"},
  "tests": ["writes file when persist=True", "summary includes prompt + context keys"]
}
```

### Data Contracts
- Handoff payload JSON structure (persisted):
```json
{
  "target_agent": "PlannerAgent",
  "prompt": "Plan feature X",
  "context": {"mission": "...", "priority": "high"},
  "tags": ["handoff", "mission"],
  "created_at": "ISO8601"
}
```

---

## Implementation Strategy

### Development Phases

#### Phase 1: Foundation Setup
Duration: same day
Agents: Planner, ToolSmith
Deliverables:
- [ ] toolsmith_agent/__init__.py
- [ ] toolsmith_agent/toolsmith_agent.py (factory + instructions)
- [ ] tests/test_toolsmith_agent_creation.py

Tasks:
1. Scaffold package and factory (ToolSmithAgent)
2. Hook memory + message filter via CompositeHook
3. Unit test: import + factory behavior

#### Phase 2: Core Implementation — ContextMessageHandoff
Duration: same day
Agents: ToolSmith, AgencyCode
Deliverables:
- [ ] tools/context_handoff.py (BaseTool subclass)
- [ ] tests/test_context_handoff_tool.py
- [ ] tools/__init__.py export updated

Tasks:
1. Implement Pydantic fields: target_agent, prompt, context, tags, persist
2. Implement run(): validate, write JSON under logs/handoffs/, return summary
3. Add export in tools/__init__.py (class + alias)
4. Unit tests: file writing (tmpdir), summary content, large payload safety

#### Phase 3: Integration & Testing
Duration: same day
Agents: ToolSmith, Merger
Deliverables:
- [ ] Green pytest run
- [ ] Handoff summary to MergerAgent

Tasks:
1. Run `python -m pytest tests/ -q`
2. If green, message MergerAgent with artifact summary
3. If failing, fix tests or rollback generated files

### File Structure Plan
```
project_root/
├── toolsmith_agent/
│   ├── __init__.py
│   ├── toolsmith_agent.py
│   └── instructions.md
├── tools/
│   └── context_handoff.py
└── tests/
    ├── test_toolsmith_agent_creation.py
    └── test_context_handoff_tool.py
```

---

## Quality Assurance Strategy

### Testing Framework
- Framework: pytest
- Coverage Target: Maintain 100% pass rate (Article II)
- Categories: unit (toolsmith factory + new tool), integration (pytest invocation)

### Constitutional Compliance Validation
- Article I: Read constitution before scaffolding (unit test may assert presence of requirement in instructions)
- Article II: Block handoff until tests green
- Article III: Use MergerAgent; do not bypass enforcement
- Article IV: Store success/failure learnings via AgentContext
- Article V: Traceability to this spec and plan

### Quality Gates
- [ ] Code Review (by MergerAgent gate)
- [ ] Test Success: 100%
- [ ] No new deps

---

## Risk Mitigation

### Technical Risks
- Risk: Export collision in tools/__init__.py → Mitigation: idempotent insertion; grep before write
- Risk: Slow test runs → Mitigation: target only affected tests locally, but final run uses full suite

### Operational Risks
- Risk: Overreach in v1 → Mitigation: keep additive; feature-gated adoption

### Constitutional Risks
- Risk: Article II violation → Mitigation: abort on any failing tests

---

## Performance Considerations
- File I/O only; use buffered writes
- Avoid large context serialization in summary; cap string in result

---

## Security Considerations
- Validate repo-root relative paths
- Redact secrets if found in context keys like token/key/secret

---

## Learning Integration
- Store directive → outcome pairs (success/failure) via AgentContext.store_memory
- Tag memories: ["toolsmith", "scaffold", "success"|"failure"]

---

## Resource Requirements
- Agent Time Allocation: < 1 day
- Infrastructure: local pytest

---

## Monitoring & Observability
- Write minimal logs to stdout via deterministic summaries
- Optional: memory records for analytics

---

## Rollback Strategy
- Generated files are additive; remove created files and revert tools/__init__.py change when tests fail

---

## Documentation Plan
- Inline docstrings in tool files
- No external docs beyond this spec/plan

---

## Review & Approval

### Technical Review Checklist
- [ ] Architecture: additive, follows patterns
- [ ] Implementation: factory + tool + tests
- [ ] Quality: 100% test pass
- [ ] Security: no secrets logged
- [ ] Constitutional: Articles I–V satisfied

### Approval Status
- [ ] Technical Lead Approval: Pending
- [ ] Security Review: N/A
- [ ] Architecture Review: Pending
- [ ] Constitutional Compliance: Pending
- [ ] Final Approval: Pending

---

## Appendices

### Appendix A: Example Test Assertions
```python
# tools/context_handoff.py behavior
result = tool.run()
assert "Prepared handoff" in result
assert "context saved" in result or not tool.persist
```
