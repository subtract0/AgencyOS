# Specification: ToolSmithAgent — Meta-Agent for Tool Creation and Deployment

**Spec ID**: `spec-007-toolsmith-agent`
**Status**: Draft
**Author**: ChiefArchitectAgent
**Created**: 2025-09-22
**Last Updated**: 2025-09-22
**Related Plan**: `plan-007-toolsmith-agent.md`

---

## Executive Summary

Introduce ToolSmithAgent, a meta-agent that designs, scaffolds, implements, tests, and deploys new tools for the Agency. It closes a critical gap in autonomous evolution by enabling rapid, spec-driven tool creation. The first high-impact directive post-creation is to deliver an enhanced handoff tool that can pass a mission prompt and rich context to the recipient agent, enabling true autonomous delegation.

---

## Goals

### Primary Goals
- [ ] Provide `create_toolsmith_agent(model, reasoning_effort, agent_context)` factory following existing patterns
- [ ] Implement end-to-end tool scaffolding workflow: create tool file(s), add exports, generate tests, run tests, and prepare handoff to MergerAgent
- [ ] Support a structured directive format ("Tool Directive") to specify desired new tools
- [ ] Deliver the initial tool: `ContextMessageHandoff` (enhanced handoff with mission prompt + context)

### Success Metrics
- ToolSmithAgent factory can be imported and instantiated with shared hooks
- Running `pytest -k toolsmith` and tests for generated tools passes locally
- After an example directive, a new tool file and test file exist and tests pass
- MergerAgent receives the completed artifact for integration (handoff step executed)

---

## Non-Goals

### Explicit Exclusions
- Direct modification of Agency Swarm internals or protocol-level changes
- Introducing new external dependencies or services
- Replacing existing handoff mechanisms in agency.py (additive/opt-in only)

### Future Considerations
- Automated PR generation via gh once approved by MergerAgent
- DSL for complex multi-file tool bundles
- Template library for common tool types (search, transform, handoff variants)

---

## User Personas & Journeys

### Primary Personas

#### ChiefArchitectAgent
- Description: Sets strategic targets and issues Tool Directives
- Goals: Close systemic gaps with minimal, reversible changes
- Pain Points: Slow iteration on new tools; manual testing burden

#### AgencyCodeAgent
- Description: Implements code; must remain compatible with new tools
- Goals: Clear contracts, minimal churn, green tests
- Pain Points: Ambiguous specifications for new tools

#### MergerAgent
- Description: Quality gatekeeper for integration
- Goals: 100% tests green, clear validation steps
- Pain Points: Incomplete artifacts without tests

### User Journeys

#### Journey 1: Create a new tool from directive
```
1. ChiefArchitect issues a Tool Directive (name, purpose, parameters, behavior)
2. ToolSmithAgent scaffolds tool + test and updates exports
3. ToolSmithAgent runs pytest and ensures all tests pass
4. ToolSmithAgent hands off to MergerAgent for verification and integration
```

#### Journey 2: Deliver enhanced handoff capability
```
1. ChiefArchitect issues directive: "Create ContextMessageHandoff"
2. ToolSmithAgent creates tools/context_handoff.py and tests/test_context_handoff_tool.py
3. Tests validate prompt + context persistence and output contract
4. MergerAgent verifies; agency can opt-in to use new handoff in flows
```

---

## Acceptance Criteria

### Functional Requirements

#### ToolSmithAgent Factory & Capabilities
- [ ] AC-1.1: `toolsmith_agent/` package exposes `create_toolsmith_agent(...)` with shared AgentContext hooks (memory + message filter)
- [ ] AC-1.2: Agent includes tools: Read, Write, Edit, MultiEdit, Grep, Glob, Bash, TodoWrite
- [ ] AC-1.3: Accepts a "Tool Directive" input with fields: `name`, `module_path`, `description`, `parameters` (schema), `behavior` (run contract), `tests` (scenarios)
- [ ] AC-1.4: Generates a new tool file under `/tools/` that subclasses `agency_swarm.tools.BaseTool` and defines Pydantic fields
- [ ] AC-1.5: Updates `tools/__init__.py` to export the tool class and alias (lowercase = class alias)
- [ ] AC-1.6: Creates a corresponding pytest file under `/tests/` covering success and error paths
- [ ] AC-1.7: Executes `pytest` and returns structured results; aborts on failures (Article II)
- [ ] AC-1.8: On success, initiates handoff to MergerAgent for final verification and integration

#### Initial Deliverable: ContextMessageHandoff
- [ ] AC-2.1: New tool: `ContextMessageHandoff` supporting fields: `target_agent: str`, `prompt: str`, `context: dict|str`, `tags: list[str]|None`, `persist: bool=False`
- [ ] AC-2.2: `run()` persists context for retrieval by the recipient (file in `logs/handoffs/` or equivalent additive mechanism) and returns a deterministic summary string
- [ ] AC-2.3: Unit tests validate: file creation when `persist=True`, presence of prompt and context in the result, and safe handling of large payloads
- [ ] AC-2.4: No changes to existing communication_flows; additive adoption documented

### Non-Functional Requirements
- [ ] AC-NF.1: No new external dependencies; Python 3.13 compatible
- [ ] AC-NF.2: Performance: tool generation + test run completes under 2 minutes locally
- [ ] AC-NF.3: Security: no secrets logged; file paths validated under repo root

### Constitutional Compliance

#### Article I: Complete Context Before Action
- [ ] AC-CI.1: ToolSmithAgent reads `/constitution.md` before executing directives
- [ ] AC-CI.2: Timeouts and retries applied to long-running pytest via Bash tool
- [ ] AC-CI.3: No broken windows introduced during scaffolding

#### Article II: 100% Verification and Stability
- [ ] AC-CII.1: All generated tools include unit tests
- [ ] AC-CII.2: Feature completion requires 100% green tests
- [ ] AC-CII.3: No tests weakened or skipped to pass

#### Article III: Automated Merge Enforcement
- [ ] AC-CIII.1: Handoff to MergerAgent occurs only after tests pass
- [ ] AC-CIII.2: No bypass of enforcement mechanisms

#### Article IV: Continuous Learning and Improvement
- [ ] AC-CIV.1: ToolSmithAgent stores learnings about successful scaffolds and failures
- [ ] AC-CIV.2: Applies historical patterns when generating future tools

#### Article V: Spec-Driven Development
- [ ] AC-CV.1: Implementation follows this spec and related plan exactly
- [ ] AC-CV.2: Changes traced back to specification updates

---

## Dependencies & Constraints

### System Dependencies
- Existing `tools/` module with BaseTool pattern and exports in `tools/__init__.py`
- Test framework: pytest; `run_tests.py` present

### External Dependencies
- None (no new libraries)

### Technical Constraints
- Additive changes only; preserve backward compatibility
- Use existing hooks and AgentContext; minimize new APIs

### Business Constraints
- Keep actions minimal, testable, and reversible
- Prefer compatibility over churn

---

## Risk Assessment

### High Risk Items
- Risk: Handoff persistence semantics misaligned with agency flows — Mitigation: additive tool with opt-in usage and file-based persistence in `logs/handoffs/`

### Medium Risk Items
- Risk: Generated tests flaky on CI — Mitigation: deterministic outputs and isolated temp dirs

### Constitutional Risks
- Risk: Weakening tests to achieve green — Mitigation: explicit prohibition and MergerAgent enforcement

---

## Integration Points

### Agent Integration
- PlannerAgent: may draft specs for future tool directives
- AgencyCodeAgent: remains compatible; can import new tools via `tools/__init__.py`
- LearningAgent: records scaffolding patterns and outcomes
- MergerAgent: final verification and integration

### System Integration
- Memory System: optional learnings stored via hooks
- VectorStore: future indexing of tool patterns (out of scope now)
- Tool System: strict adherence to BaseTool + pydantic field conventions

### External Integration
- None

---

## Testing Strategy

### Test Categories
- Unit Tests: ToolSmithAgent factory + ContextMessageHandoff behavior
- Integration Tests: Pytest execution path and export updates
- Constitutional Tests: Enforcement of Article II via failing test aborts

### Test Data Requirements
- Temporary directories for persistence tests
- Sample directives for tool generation

### Test Environment Requirements
- Local pytest via `python -m pytest tests/ -q`

---

## Implementation Phases

### Phase 1: ToolSmithAgent Scaffolding
- Scope: Factory + instructions; directive parsing; minimal execution loop
- Deliverables: `toolsmith_agent/` package, factory, initial tests
- Success Criteria: Factory import and toolset verification tests pass

### Phase 2: Initial Tool Delivery (ContextMessageHandoff)
- Scope: New tool + tests + exports
- Deliverables: `tools/context_handoff.py`, `tests/test_context_handoff_tool.py`, updated exports
- Success Criteria: New tests pass locally

### Phase 3: Handoff & Learnings
- Scope: Handoff to MergerAgent; store learnings
- Deliverables: MergerAgent invocation; memory records
- Success Criteria: MergerAgent verification green

---

## Review & Approval

### Stakeholders
- Primary Stakeholder: @am (Project Owner)
- Technical Reviewers: PlannerAgent, MergerAgent

### Review Criteria
- [ ] Completeness and clarity of contracts
- [ ] Additive compatibility; no breaking changes
- [ ] Constitutional compliance and 100% tests

### Approval Status
- [ ] Stakeholder Approval: Pending
- [ ] Technical Approval: Pending
- [ ] Constitutional Compliance: Pending
- [ ] Final Approval: Pending

---

## Appendices

### Appendix A: Tool Directive (Structured Input)
```
{
  "name": "ContextMessageHandoff",
  "module_path": "tools/context_handoff.py",
  "description": "Handoff with mission prompt + structured context",
  "parameters": {
    "target_agent": "str",
    "prompt": "str",
    "context": "dict|str",
    "tags": "list[str]|None",
    "persist": "bool"
  },
  "behavior": "Persist context under logs/handoffs/ and return deterministic summary",
  "tests": ["writes file when persist=True", "summary includes prompt + context keys", "handles large context safely"]
}
```

### Appendix B: References
- constitution.md
- specs/TEMPLATE.md, plans/TEMPLATE.md
- tools/__init__.py export pattern

### Appendix C: Related Documents
- `plan-007-toolsmith-agent.md`
