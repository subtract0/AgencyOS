---
description: Query Architectural Decision Records for guidance on technical decisions
argument-hint: [topic] [format]
model: claude-sonnet-4-5-20250929
---

# Agent ADR Query

## Purpose

**Strategic guidance tool** for querying Architectural Decision Records (ADRs) to inform technical decisions with institutional wisdom and architectural precedent.

## Variables

- `topic`: Decision topic (`typing` | `testing` | `patterns` | `architecture` | `all`)
- `format`: Output format (`summary` | `detailed` | `reference`)

## Instructions

You are querying **institutional architectural wisdom** from ADRs to make informed decisions consistent with established precedent.

## Step 1: Identify Relevant ADRs

**ADR Index**: Read `docs/adr/ADR-INDEX.md` for complete list.

**Topic Mapping**:

**Typing & Type Safety** (`topic=typing`):
- ADR-008: Strict Typing Requirement (No Dict[Any, Any])
- ADR-013: TypeScript Strict Mode Enforcement

**Testing** (`topic=testing`):
- ADR-002: 100% Verification and Stability
- ADR-011: NECESSARY Pattern for Test Cases
- ADR-012: Test-Driven Development Mandate

**Patterns & Practices** (`topic=patterns`):
- ADR-010: Result Pattern for Error Handling
- ADR-009: Function Complexity Limits (<50 lines)
- ADR-014: Repository Pattern for Data Access

**Architecture** (`topic=architecture`):
- ADR-001: Complete Context Before Action
- ADR-004: Continuous Learning and Improvement
- ADR-007: Spec-Driven Development Workflow
- ADR-006: Claude Agent SDK Integration

**Memory & Learning** (`topic=learning`):
- ADR-004: VectorStore Integration (Mandatory)
- ADR-015: Cross-Session Pattern Recognition

**All ADRs** (`topic=all`):
- Returns index of all 15+ ADRs

## Step 2: Read Relevant ADRs

For each relevant ADR, extract:

1. **Decision**: What was decided?
2. **Context**: Why was it decided?
3. **Consequences**: What are the implications?
4. **Status**: Active, superseded, deprecated?
5. **Enforcement**: How is it enforced?

**Example**:
```markdown
# ADR-008: Strict Typing Requirement

## Decision
NEVER use `any` (TypeScript) or `Dict[Any, Any]` (Python). 
Use Pydantic models with explicit field types.

## Context
Type safety prevents runtime errors and improves maintainability.
Historical data shows 73% of bugs relate to type mismatches.

## Consequences
- All code must have explicit types
- Pydantic models required for complex data
- Mypy/TSC must pass with zero errors
- Pre-commit hooks enforce this

## Enforcement
- Constitutional Law #2
- Pre-commit type checks
- QualityEnforcer autonomous healing
```

## Step 3: Apply to Current Decision

**Decision Template**:

```
## Technical Decision Required

**Question**: [Your technical question]

**Relevant ADRs**:
1. ADR-[N]: [Title]
   - **Guidance**: [What this ADR says about your question]
   - **Precedent**: [How similar decisions were made]

2. ADR-[M]: [Title]
   - **Guidance**: [Additional relevant guidance]

**Recommendation Based on ADRs**:
[Synthesized recommendation following architectural precedent]

**Rationale**:
- Consistent with ADR-[N] decision on [topic]
- Aligns with ADR-[M] pattern for [use case]
- Precedent: [Similar past decision]

**Implementation**:
[Concrete steps to implement recommendation]

**New ADR Needed?**
[YES/NO - If yes, this decision creates new precedent requiring ADR]
```

## Step 4: Format Output

### Summary Format (`format=summary`)
```
## ADR Query: [topic]

**Relevant ADRs**: [N] found

1. **ADR-008**: Strict Typing
   - Use Pydantic, not Dict[Any, Any]
   - Enforced by Law #2

2. **ADR-010**: Result Pattern
   - Functional error handling
   - No try/catch for control flow

**Quick Reference**: [Key points from ADRs]
```

### Detailed Format (`format=detailed`)
```
## ADR Query: [topic]

### ADR-008: Strict Typing Requirement

**Decision**:
[Full decision text]

**Context**:
[Why this decision was made]

**Consequences**:
[Positive impacts]
[Negative tradeoffs]

**Examples**:
```python
# ✅ Correct
class UserData(BaseModel):
    email: str
    name: str

# ❌ Wrong
user_data: Dict[Any, Any]
```

[Repeat for all relevant ADRs]

**Cross-References**:
- ADR-010 (Result Pattern) complements this decision
- ADR-002 (100% Verification) enforces this via tests
```

### Reference Format (`format=reference`)
```
**ADRs on [topic]**:
- ADR-008: Strict Typing (docs/adr/ADR-008-strict-typing.md)
- ADR-013: TypeScript Strict Mode (docs/adr/ADR-013-typescript-strict.md)

Read full ADRs for detailed guidance.
```

## Step 5: Suggest New ADR if Needed

If current decision represents **new architectural precedent**:

```
⚠️ **New ADR Recommended**

Your decision about [topic] is not covered by existing ADRs.

**Suggested ADR**:
- **Title**: ADR-[next-number]: [Decision Title]
- **Decision**: [What you're deciding]
- **Rationale**: [Why this is architectural]
- **Impact**: [Who/what is affected]

**Action**:
1. Use `/prime create_tool` → Choose "Create ADR"
2. Work with ChiefArchitect to formalize decision
3. Get approval before implementation
```

## Use Cases

### 1. Code Agent: "Should I use Result or exceptions?"
```
Query: /agent-adr-query patterns summary
Result: 
  - ADR-010: Use Result<T,E> for expected errors
  - ADR-005: Exceptions only for unexpected failures
  - Recommendation: Result pattern for this use case
```

### 2. Chief Architect: "How do we handle type safety?"
```
Query: /agent-adr-query typing detailed
Result:
  - ADR-008: Complete guidance on strict typing
  - ADR-013: TypeScript-specific rules
  - Examples and enforcement mechanisms provided
```

### 3. Quality Enforcer: "What are the function complexity limits?"
```
Query: /agent-adr-query patterns summary
Result:
  - ADR-009: Functions must be <50 lines
  - ADR-009: Single Responsibility Principle enforced
  - ADR-009: Cyclomatic complexity <10
```

### 4. New Feature: "How should we architect this?"
```
Query: /agent-adr-query architecture detailed
Result:
  - ADR-007: Spec-driven development required
  - ADR-001: Complete context before action
  - ADR-004: Query VectorStore for patterns
  - Workflow: spec.md → plan.md → implementation
```

## Integration with Agent Workflows

**MANDATORY for Architectural Decisions**:

```markdown
## Decision-Making Protocol

### 1. Query Existing ADRs (MANDATORY)
Use `/agent-adr-query [topic] summary` to check architectural precedent

### 2. Follow Established Precedent
If ADR exists, FOLLOW its guidance (no deviation without approval)

### 3. Escalate Novel Decisions
If no ADR covers decision, escalate to ChiefArchitect for ADR creation

[remaining workflow]
```

## ADR Index Quick Reference

**Core Articles** (Constitutional):
- ADR-001: Complete Context Before Action (Article I)
- ADR-002: 100% Verification and Stability (Article II)
- ADR-003: Automated Merge Enforcement (Article III)
- ADR-004: Continuous Learning (Article IV - VectorStore mandatory)
- ADR-007: Spec-Driven Development (Article V)

**Code Quality**:
- ADR-008: Strict Typing (No any/Dict[Any,Any])
- ADR-009: Function Complexity (<50 lines)
- ADR-010: Result Pattern (Functional error handling)
- ADR-011: NECESSARY Pattern (9 test categories)
- ADR-012: TDD Mandate (Tests first, always)

**Architecture**:
- ADR-006: Claude Agent SDK Integration
- ADR-014: Repository Pattern
- ADR-015: Cross-Session Learning

**Technology**:
- ADR-013: TypeScript Strict Mode
- ADR-016: Python Pydantic Models

## Success Metrics

- **Decision Consistency**: >95% of decisions align with ADRs
- **Query Time**: <2 seconds for summary format
- **Precedent Application**: >80% of queries result in actionable guidance
- **New ADR Rate**: <10% (most decisions covered by existing ADRs)
- **Deviation Rate**: <5% (rare cases requiring new precedent)

## Benefits

**For Agents**:
- Instant access to architectural wisdom
- Consistent decision-making across sessions
- No need to re-learn established patterns

**For Architecture**:
- Enforces consistency across codebase
- Documents institutional knowledge
- Prevents architectural drift

---

**Remember**: Don't reinvent decisions. Query ADRs first, follow precedent, escalate novel cases.
