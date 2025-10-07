---
description: Store successful patterns in VectorStore after completion (Article IV compliance)
argument-hint: [task-type] [outcome]
model: claude-sonnet-4-5-20250929
---

# Agent Memory Store

## Purpose

**MANDATORY Article IV tool** for all agents to store successful patterns and learnings AFTER task completion. This tool builds institutional memory for future use.

## Variables

- `task_type`: Category of completed task (`implementation` | `test` | `refactor` | `fix` | `audit`)
- `outcome`: Result quality (`success` | `partial` | `failure`)

## Instructions

You are **storing institutional knowledge** in VectorStore for future agents. This is a **constitutional requirement** per Article IV.

## Step 1: Evaluate What to Store

**Store if**:
- ✅ Task completed successfully (tests pass, quality verified)
- ✅ Novel pattern or approach discovered
- ✅ Error resolved with validated solution
- ✅ Reusable code pattern created
- ✅ Best practice demonstrated

**Do NOT store if**:
- ❌ Task failed or incomplete
- ❌ Pattern already well-documented in VectorStore
- ❌ Solution is trivial (e.g., fixing typo)
- ❌ No reusable learning extracted

## Step 2: Extract Reusable Pattern

Analyze your work to identify the **transferable pattern**:

**For Successful Implementation**:
```python
pattern = {
    "task_type": "implementation",
    "pattern_name": "Repository pattern for user authentication",
    "description": "Use repository layer with Result pattern for auth",
    "code_sample": """
def authenticate(email: str, password: str) -> Result[User, AuthError]:
    return user_repository.find_by_email(email)
        .and_then(lambda user: verify_password(user, password))
        .map_err(lambda e: AuthError.INVALID_CREDENTIALS)
    """,
    "context": "When implementing authentication in new features",
    "success_metrics": {
        "tests_passed": True,
        "test_count": 15,
        "coverage": "98%"
    }
}
```

**For Error Resolution**:
```python
pattern = {
    "task_type": "fix",
    "pattern_name": "Test fixture constitutional violation fix",
    "error_signature": "AttributeError: 'MockAgent' object has no attribute 'context'",
    "root_cause": "Mock agents not initialized with complete AgentContext",
    "solution": "mock_agent = create_mock_agent(context=AgentContext(...))",
    "validation": "All 194 tests passing after fix",
    "prevention": "Always initialize mocks with full context"
}
```

**For Refactoring**:
```python
pattern = {
    "task_type": "refactor",
    "pattern_name": "Extract duplicate validation logic",
    "before": "Validation duplicated across 5 endpoints",
    "after": "Single Pydantic model with shared validation",
    "impact": {
        "loc_reduced": 145,
        "duplication": "Eliminated",
        "maintainability": "Improved"
    }
}
```

## Step 3: Calculate Confidence Score

**Confidence Scoring (0.0-1.0)**:

```python
def calculate_confidence(outcome: dict) -> float:
    """Calculate pattern confidence based on evidence."""
    score = 0.5  # Baseline
    
    # Test success (+0.3)
    if outcome["tests_passed"] and outcome["test_pass_rate"] == 1.0:
        score += 0.3
    
    # Multiple validations (+0.1 per validation, max +0.3)
    validations = outcome.get("validation_count", 1)
    score += min(validations * 0.1, 0.3)
    
    # Code review approved (+0.1)
    if outcome.get("code_review_approved"):
        score += 0.1
    
    # Production deployment success (+0.1)
    if outcome.get("production_verified"):
        score += 0.1
    
    # CI/CD pipeline passed (+0.1)
    if outcome.get("ci_passed"):
        score += 0.1
    
    return min(score, 1.0)
```

**Example Calculation**:
- Tests pass (100%): +0.3 → 0.8
- Code reviewed: +0.1 → 0.9
- CI passed: +0.1 → 1.0

## Step 4: Store in VectorStore

Use AgentContext to persist the learning:

```python
from shared.agent_context import AgentContext
import uuid
from datetime import datetime

context = AgentContext.get_current()

# Prepare memory entry
memory_key = f"{task_type}_{pattern_name}_{uuid.uuid4()}"
memory_content = {
    "pattern_name": pattern["pattern_name"],
    "task_type": task_type,
    "pattern": pattern,
    "confidence": calculate_confidence(outcome),
    "evidence_count": 1,  # Increment on subsequent occurrences
    "timestamp": datetime.now().isoformat(),
    "agent": "code_agent",  # Or current agent name
    "outcome": outcome,
    "reusable": True,
    "tags": ["pattern", task_type, "success"]
}

# Store in VectorStore
context.store_memory(
    key=memory_key,
    content=memory_content,
    tags=memory_content["tags"]
)
```

## Step 5: Report Storage

Provide confirmation:

```
## Pattern Stored in VectorStore

**Pattern Name**: [name]
**Task Type**: [type]
**Confidence**: [0.XX] (calculated based on validation)
**Evidence Count**: 1 (first occurrence)

**Pattern Summary**:
[Brief description of what was learned]

**Reusable For**:
- [Context 1 where this pattern applies]
- [Context 2 where this pattern applies]

**Success Metrics**:
- Tests: [N] passing (100%)
- Coverage: [X]%
- CI Status: ✅ Passed

**Stored with Tags**: ["pattern", "[task_type]", "success"]

✅ **Future agents can now query this pattern with `/agent-memory-query [task_type]`**
```

## Use Cases

### 1. Code Agent After Successful Implementation
```
Agent: Completed authentication feature with 100% test pass
Tool: Extracts repository + Result pattern approach
Storage: Stores pattern with confidence 0.95
Result: Future agents can reuse this exact pattern
```

### 2. Quality Enforcer After Healing
```
Agent: Fixed 194 test fixture violations
Tool: Extracts "mock agent initialization" pattern
Storage: Stores fix with confidence 0.95, evidence 194
Result: Future healing operations apply this validated fix
```

### 3. Test Generator After Test Creation
```
Agent: Created comprehensive payment tests (98% coverage)
Tool: Extracts AAA pattern with mock gateway
Storage: Stores test pattern with confidence 0.90
Result: Future test generation uses this validated approach
```

## Integration with Agent Workflows

**MANDATORY in Agent Definitions**:

All agents MUST store learnings AFTER success:

```markdown
## Implementation Workflow

[existing steps]

### 8. Store Learnings (MANDATORY - Article IV)
Use `/agent-memory-store [task-type] success` to persist validated patterns

### 9. Report Completion
[existing step]
```

## Incremental Evidence Accumulation

**Pattern Recurrence**:

When storing a pattern that already exists:
```python
# Check for existing pattern
existing = context.search_memories(
    tags=["pattern", pattern_name],
    query=pattern_name
)

if existing:
    # Increment evidence count
    existing[0]["evidence_count"] += 1
    
    # Recalculate confidence (more evidence = higher confidence)
    existing[0]["confidence"] = min(
        existing[0]["confidence"] + 0.05,
        1.0
    )
    
    # Update storage
    context.store_memory(existing[0]["key"], existing[0], existing[0]["tags"])
```

## Success Metrics

- **Storage Rate**: 100% of successful tasks stored
- **Confidence Accuracy**: ≥90% of high-confidence patterns remain valid
- **Reusability**: ≥60% of stored patterns reused by other agents
- **Storage Time**: <200ms for memory persistence
- **Evidence Growth**: Patterns gain evidence over time

## Article IV Compliance

This tool enforces **Article IV: Continuous Learning** by:

1. **Storing learnings AFTER success** (constitutional requirement)
2. **Building institutional memory** (cross-session knowledge)
3. **Enabling pattern reuse** (query by future agents)
4. **Evidence-based validation** (confidence scoring)

**Without this tool**, agents lose all learnings between sessions, violating Article IV.

---

**Remember**: Learn once, reuse forever. Store your success for the collective intelligence.
