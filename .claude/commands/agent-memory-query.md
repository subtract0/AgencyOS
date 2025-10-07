---
description: Query VectorStore for patterns before implementation (Article IV compliance)
argument-hint: [task-type] [confidence-threshold]
model: claude-sonnet-4-5-20250929
---

# Agent Memory Query

## Purpose

**MANDATORY Article IV tool** for all agents to query institutional memory BEFORE taking action. This tool searches VectorStore for validated patterns, historical errors, and successful strategies to inform decision-making.

## Variables

- `task_type`: Category of task (`implementation` | `test` | `refactor` | `fix` | `audit`)
- `confidence_threshold`: Minimum confidence (default: `0.6`, range: `0.0-1.0`)

## Instructions

You are querying the **institutional memory** (VectorStore) to apply learned patterns and avoid known errors. This is a **constitutional requirement** per Article IV.

## Step 1: Define Search Parameters

Based on your task, construct targeted search queries:

**For Implementation Tasks**:
```python
tags = ["pattern", "implementation", "success", task_type]
query = "similar implementation patterns with high success rate"
```

**For Bug Fixes**:
```python
tags = ["error", "resolution", "fix", task_type]
query = "known errors and their validated solutions"
```

**For Refactoring**:
```python
tags = ["refactor", "pattern", "best_practice"]
query = "successful refactoring strategies"
```

**For Testing**:
```python
tags = ["test", "pattern", "tdd", "coverage"]
query = "test patterns with high coverage"
```

**For Auditing**:
```python
tags = ["auditor", "violation", "pattern"]
query = "common code quality violations"
```

## Step 2: Execute VectorStore Query

Use AgentContext to search memories:

```python
from shared.agent_context import AgentContext

context = AgentContext.get_current()

# Query for successful patterns
patterns = context.search_memories(
    tags=tags,
    query=query,
    include_session=False,  # Cross-session learning
    limit=10
)

# Filter by confidence threshold
validated_patterns = [
    p for p in patterns
    if p.get("confidence", 0) >= confidence_threshold
    and p.get("evidence_count", 0) >= 3  # Min evidence requirement
]
```

## Step 3: Analyze Results

For each validated pattern, extract:

1. **Pattern Description**: What is the pattern?
2. **Success Metrics**: How well did it work? (test pass rate, etc.)
3. **Context**: When was it used successfully?
4. **Code Samples**: Reusable implementation examples
5. **Confidence**: How reliable is this pattern? (0.6-1.0)
6. **Evidence Count**: How many times has it been validated?

**Example Result**:
```json
{
  "pattern_name": "Test Fixture Constitutional Violations",
  "pattern_type": "error_resolution",
  "confidence": 0.95,
  "evidence_count": 194,
  "solution": "Initialize mock agents with complete AgentContext",
  "code_sample": "mock_agent = create_mock_agent(context=AgentContext(...))",
  "success_rate": "100% after fix",
  "article_violated": "Article I & II",
  "timestamp": "2025-10-07T18:45:00Z"
}
```

## Step 4: Apply Learnings

**Integration Pattern**:
```python
def apply_validated_patterns(task: Task, patterns: list) -> Approach:
    """Apply learned patterns to current task."""
    
    approach = Approach(task)
    
    for pattern in patterns:
        if pattern["confidence"] >= 0.9:
            # High confidence - apply automatically
            approach.incorporate_pattern(pattern)
        elif pattern["confidence"] >= 0.7:
            # Medium confidence - consider with caution
            approach.consider_pattern(pattern)
        else:
            # Lower confidence - note for reference only
            approach.reference_pattern(pattern)
    
    return approach
```

## Step 5: Report Findings

Provide structured output:

```
## VectorStore Query Results

**Task Type**: [task_type]
**Confidence Threshold**: [threshold]
**Patterns Found**: N validated patterns

### High Confidence Patterns (≥0.9)
1. **[Pattern Name]** (confidence: 0.95, evidence: 194)
   - **Solution**: [Brief description]
   - **Code Sample**: `[code snippet]`
   - **Success Rate**: [metric]
   - **Action**: APPLY automatically

### Medium Confidence Patterns (0.7-0.89)
2. **[Pattern Name]** (confidence: 0.85, evidence: 12)
   - **Solution**: [Brief description]
   - **Context**: [when to use]
   - **Action**: CONSIDER carefully

### Errors to Avoid
⚠️ **[Error Pattern]** (occurred 37 times)
   - **Cause**: [root cause]
   - **Prevention**: [how to avoid]

### Recommendation
[Summary of how to proceed based on learned patterns]
```

## Use Cases

### 1. Code Agent Before Implementation
```
Agent: "I need to implement user authentication"
Tool: Queries VectorStore for authentication patterns
Result: 
  - High confidence pattern: "Use repository pattern with Result<User, AuthError>"
  - Historical error: "Don't store passwords in plain text (3 incidents)"
  - Test pattern: "Mock authentication with create_mock_user fixture"
Agent: Applies patterns, avoids known errors
```

### 2. Test Generator Before Writing Tests
```
Agent: "I need to write tests for payment processing"
Tool: Queries VectorStore for test patterns
Result:
  - AAA pattern with 95% success rate
  - Mock external payment gateway (avoid actual charges)
  - Test edge cases: negative amounts, duplicate transactions
Agent: Generates comprehensive tests using validated patterns
```

### 3. Quality Enforcer Before Healing
```
Agent: "I found Dict[Any, Any] violation"
Tool: Queries VectorStore for type safety fixes
Result:
  - Pattern: "Replace with Pydantic model" (confidence: 0.93)
  - 45 successful applications
  - Code sample provided
Agent: Applies validated healing pattern
```

## Integration with Agent Workflows

**MANDATORY in Agent Definitions**:

All agents MUST query this tool BEFORE action:

```markdown
## Implementation Workflow

### 1. Query Institutional Memory (MANDATORY - Article IV)
Use `/agent-memory-query [task-type] [threshold]` to retrieve validated patterns

### 2. Analyze Task
[existing step]

### 3. Apply Learnings
Incorporate high-confidence patterns from VectorStore

### 4. Proceed with Implementation
[existing workflow]
```

## Success Metrics

- **Pattern Application Rate**: >80% of tasks apply VectorStore patterns
- **Error Avoidance Rate**: >90% reduction in known errors
- **Confidence Threshold**: 0.6 minimum (Article IV requirement)
- **Evidence Requirement**: ≥3 occurrences for validation
- **Query Time**: <500ms for interactive workflows

## Article IV Compliance

This tool enforces **Article IV: Continuous Learning** by:

1. **Querying learnings BEFORE action** (constitutional requirement)
2. **Applying validated patterns** (confidence ≥ 0.6, evidence ≥ 3)
3. **Avoiding known errors** (historical incident prevention)
4. **Cross-session learning** (institutional memory accumulation)

**Without this tool**, agents violate Article IV and lose institutional knowledge.

---

**Remember**: Query first, act second. Institutional memory is your strategic advantage.
