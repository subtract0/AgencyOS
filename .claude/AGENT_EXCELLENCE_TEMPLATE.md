# **AGENT EXCELLENCE TEMPLATE**

**Purpose**: Universal pattern for creating MASTERPIECE-level agent definitions.

**Status**: Meta-framework derived from Quality Enforcer (100/100) + 4 agent self-improvement proposals

**Usage**: Copy sections into any agent definition to achieve A+ grade (95-100/100).

---

## **Section 1: Agent Tools Integration** (MANDATORY)

**Location**: After "Tool Permissions" section

```markdown
## Agent Tools Integration (Constitutional Requirement)

**MANDATORY**: Use these 5 agent tools to enforce constitutional compliance.

### 1. `/agent-memory-query` (Article IV - BEFORE Action)

**Query VectorStore for validated patterns BEFORE performing agent-specific action.**

```python
# Step 2 of workflow (BEFORE main action)
def query_learnings(task_context: str):
    """Article IV requirement - query institutional memory."""

    result = agent_memory_query(
        task_type="[agent_role]",  # e.g., "planning", "architecture", "testing"
        feature_type=task_context,
        confidence_threshold=0.7
    )

    if result.is_ok():
        learnings = result.unwrap()
        high_confidence = learnings["patterns"]["high_confidence"]
        medium_confidence = learnings["patterns"]["medium_confidence"]
    else:
        high_confidence = []
        medium_confidence = []

    return high_confidence, medium_confidence
```

### 2. `/agent-memory-store` (Article IV - AFTER Success)

**Store successful patterns AFTER validation.**

```python
# Step N-1 of workflow (AFTER successful completion)
def store_success_pattern(outcome_data: dict):
    """Article IV requirement - store institutional knowledge."""

    result = agent_memory_store(
        task_type="[agent_role]",
        outcome="success",
        metadata={
            # Agent-specific metadata
            "context": outcome_data["context"],
            "solution": outcome_data["solution"],
            "pattern": outcome_data["pattern"],
            "constitutional_compliance": True
        },
        confidence=0.85,  # High for validated outcomes
        evidence_count=1
    )

    if result.is_err():
        log_warning(f"Failed to store pattern: {result.unwrap_err()}")
```

### 3. `/agent-adr-query` (Article V - Architectural Guidance)

**Query ADRs for precedent BEFORE architectural decisions.**

```python
# When making decisions that affect architecture
def query_adr_guidance(topic: str):
    """Query ADRs for architectural precedent."""

    result = agent_adr_query(topic=topic, format="guidance")
    return result.unwrap() if result.is_ok() else []
```

### 4. `/agent-diff-review` (Article III - Pre-Commit Validation)

**Validate changes against constitutional laws BEFORE committing.**

```python
# BEFORE git commit
def validate_before_commit(files_changed: list[str]):
    """Article III requirement - pre-commit constitutional validation."""

    # Stage files
    for f in files_changed:
        subprocess.run(["git", "add", f], check=True)

    # Review diff
    diff_result = agent_diff_review(
        scope="staged",
        strict=True  # Article III: Zero tolerance
    )

    if diff_result.is_err():
        violations = diff_result.unwrap_err()["violations"]
        print(f"❌ BLOCKED: {len(violations)} constitutional violations")

        # Unstage
        subprocess.run(["git", "restore", "--staged"] + files_changed)
        return Err("Constitutional violations detected")

    return Ok("Validation passed")
```

### 5. `/agent-test-verify` (Article I & II - Verification)

**Verify with constitutional retry protocol AFTER implementation.**

```python
# AFTER making changes
def verify_changes():
    """Article I & II requirement - complete verification with retry."""

    test_result = agent_test_verify(
        scope="all",
        timeout_multiplier=2
    )

    if test_result.is_err():
        error = test_result.unwrap_err()
        if error.type == "TIMEOUT_EXHAUSTED":
            raise ConstitutionalViolation("Article I: Tests timed out after retries")
        else:
            return Err(f"Tests failed: {error.message}")

    return Ok(test_result.unwrap())
```
```

---

## **Section 2: Constitutional Enforcement** (MANDATORY)

**Location**: Near top of agent definition, before "Core Competencies"

```markdown
## Constitutional Compliance

**MANDATORY**: Before any action, validate against all 5 constitutional articles:

### Article I: Complete Context Before Action (ADR-001)

**Enforce:**
- Read ALL relevant files/context before action
- Query VectorStore for similar patterns (use `/agent-memory-query`)
- Retry with extended timeouts (2x, 3x, up to 10x) on incomplete data
- NEVER proceed with partial context

**Violations to Detect:**
- ❌ Acting on incomplete data
- ❌ Skipping VectorStore queries
- ❌ Proceeding after timeout without retry

### Article II: 100% Verification and Stability (ADR-002)

**Enforce:**
- ALL tests must pass (100% success rate)
- Use `/agent-test-verify` for constitutional retry logic
- Zero tolerance for broken tests
- "Delete the Fire First" - fix failures before new features

**Violations to Detect:**
- ❌ ANY test failures
- ❌ Skipped tests without justification
- ❌ Proceeding with <100% pass rate

### Article III: Automated Merge Enforcement (ADR-003)

**Enforce:**
- Use `/agent-diff-review` before ALL commits
- No manual override capabilities
- Zero-tolerance policy for quality gate violations
- Multi-layer enforcement (pre-commit, CI, branch protection)

**Violations to Detect:**
- ❌ Commits without diff review
- ❌ Bypass mechanisms
- ❌ Quality gate circumvention

### Article IV: Continuous Learning (ADR-004)

**Enforce:**
- **MANDATORY**: `/agent-memory-query` BEFORE action
- **MANDATORY**: `/agent-memory-store` AFTER success
- Minimum confidence threshold: 0.6
- VectorStore integration is constitutionally required

**Violations to Detect:**
- ❌ Skipping VectorStore queries
- ❌ Not storing successful patterns
- ❌ Applying low-confidence patterns (<0.6)

### Article V: Spec-Driven Development (ADR-007)

**Enforce:**
- Complex features require approved spec.md → plan.md
- Spec-kit methodology (Goals, Non-Goals, Personas, Criteria)
- TodoWrite task breakdown from approved plans
- Use `/agent-adr-query` for architectural guidance

**Violations to Detect:**
- ❌ Implementation without specification (complex features)
- ❌ Missing spec-kit components
- ❌ Plans without task breakdown

**Validation Pattern:**

```python
def validate_constitutional_compliance(action_context: dict) -> Result[bool, list[Violation]]:
    """
    Validate action against all 5 constitutional articles.

    Returns:
        Result with violations list (empty if compliant)
    """
    violations = []

    # Article I: Complete Context
    if not has_complete_context(action_context):
        violations.append(Violation("Article I", "Incomplete context"))

    # Article II: Testing
    if not all_tests_pass():
        violations.append(Violation("Article II", "Tests failing"))

    # Article III: Quality Gates
    if not quality_gates_pass():
        violations.append(Violation("Article III", "Quality gate failure"))

    # Article IV: Learning
    if not queried_vector_store(action_context):
        violations.append(Violation("Article IV", "VectorStore not queried"))

    # Article V: Spec-Driven
    if is_complex(action_context) and not has_spec(action_context):
        violations.append(Violation("Article V", "Complex feature without spec"))

    if violations:
        return Err(violations)
    return Ok(True)
```
```

---

## **Section 3: JSON Message Formats** (HIGH IMPACT)

**Location**: After "Communication Protocols"

```markdown
## JSON Message Formats (Inter-Agent Communication)

**Standard message structure for all agent interactions:**

### Message to Other Agent

```json
{
  "message_type": "[action_name]",
  "from_agent": "[this_agent]",
  "to_agent": "[target_agent]",
  "timestamp": "2025-10-07T12:00:00Z",
  "payload": {
    "context": "Why this message is being sent",
    "data": {
      // Agent-specific data
    },
    "priority": "HIGH" | "MEDIUM" | "LOW",
    "expected_response": "What response is expected"
  },
  "metadata": {
    "session_id": "session_123",
    "constitutional_compliance": true
  }
}
```

### Response Message

```json
{
  "message_type": "[response_type]",
  "from_agent": "[this_agent]",
  "to_agent": "[requesting_agent]",
  "timestamp": "2025-10-07T12:05:00Z",
  "payload": {
    "status": "SUCCESS" | "FAILURE" | "PENDING",
    "result": {
      // Agent-specific result data
    },
    "errors": [] // If status=FAILURE
  }
}
```

### Message Handling Code

```python
from pydantic import BaseModel
from typing import Literal

class AgentMessage(BaseModel):
    """Type-safe agent message."""
    message_type: str
    from_agent: str
    to_agent: str
    timestamp: str
    payload: dict
    metadata: dict | None = None

def send_message(to_agent: str, message_data: dict) -> Result[str, str]:
    """Send typed message to another agent."""

    message = AgentMessage(
        message_type=message_data["type"],
        from_agent="[this_agent]",
        to_agent=to_agent,
        timestamp=datetime.utcnow().isoformat(),
        payload=message_data["payload"],
        metadata={"constitutional_compliance": True}
    )

    # Send via AgentContext
    result = context.send_message(to_agent, message.dict())
    return result
```
```

---

## **Section 4: Numbered Workflows** (CLARITY)

**Location**: Replace any unnumbered workflow sections

```markdown
## Workflows

### Workflow 1: [Primary Workflow Name]

**Purpose**: [What this workflow accomplishes]

**Steps**:

1. **Receive Input**: [What triggers this workflow]
2. **Query Learnings**: Use `/agent-memory-query` for similar patterns (Article IV)
3. **Validate Context**: Ensure complete context (Article I)
4. **Execute Action**: [Agent-specific action]
5. **Verify Result**: Use `/agent-test-verify` for validation (Article II)
6. **Review Changes**: Use `/agent-diff-review` before commit (Article III)
7. **Store Learnings**: Use `/agent-memory-store` for success patterns (Article IV)
8. **Report Completion**: Return result to requesting agent

**Example**:

```python
def primary_workflow(input_data: dict) -> Result[Output, Error]:
    """Execute primary workflow with constitutional compliance."""

    # Step 2: Query learnings
    learnings = query_learnings(input_data["context"])

    # Step 3: Validate context
    if not has_complete_context(input_data):
        return Err(Error("Incomplete context - Article I violation"))

    # Step 4: Execute action
    result = execute_agent_action(input_data, learnings)

    # Step 5: Verify result
    verification = verify_changes()
    if verification.is_err():
        return verification

    # Step 7: Store learnings
    store_success_pattern({
        "context": input_data["context"],
        "solution": result,
        "pattern": extract_pattern(result)
    })

    return Ok(result)
```

### Workflow 2: [Secondary Workflow Name]

[Repeat pattern above]
```

---

## **Section 5: Quality Metrics** (SELF-IMPROVEMENT)

**Location**: Before "Anti-Patterns" section

```markdown
## Quality Metrics

**Track performance over time for continuous improvement:**

```python
class [Agent]QualityMetrics(BaseModel):
    """Track [agent] performance."""

    # Time metrics
    time_to_completion_hours: float  # Request → delivery
    avg_processing_time_seconds: float  # Per-task time

    # Quality metrics
    success_rate: float  # 0-1 (successful completions)
    error_rate: float  # 0-1 (failures)
    retry_rate: float  # 0-1 (retries needed)

    # Constitutional metrics
    article_i_compliance: bool  # Complete context
    article_ii_compliance: bool  # 100% tests pass
    article_iii_compliance: bool  # Quality gates pass
    article_iv_compliance: bool  # VectorStore used
    article_v_compliance: bool  # Spec-driven (if applicable)

    # Learning metrics
    patterns_queried: int  # VectorStore queries
    patterns_applied: int  # Patterns actually used
    patterns_stored: int  # New patterns learned
    learning_application_rate: float  # Applied/Queried

# Target thresholds
[AGENT]_QUALITY_TARGETS = {
    "time_to_completion_hours": [TARGET_VALUE],
    "success_rate": 0.95,  # 95% success
    "error_rate": 0.05,  # 5% max errors
    "retry_rate": 0.10,  # 10% max retries
    "constitutional_compliance": 1.0,  # 100% (all 5 articles)
    "learning_application_rate": 0.80  # 80% pattern application
}
```

**Dashboard**:

```markdown
### [Agent] Performance (Last 30 Days)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Success Rate** | 97% | 95% | ✅ +2% |
| **Constitutional** | 100% | 100% | ✅ PASS |
| **Learning Application** | 82% | 80% | ✅ +2% |
| **Avg Time** | [VALUE] | [TARGET] | [STATUS] |
```
```

---

## **Section 6: NECESSARY Pattern Checklist** (COMPREHENSIVE QUALITY)

**Location**: In "Quality Checklist" section, add at top

```markdown
## Quality Checklist

**Before completing any action:**

### NECESSARY Pattern (ADR-011) - ALL 9 Categories

- [ ] **N**ormal operation - Happy path scenarios tested/documented
- [ ] **E**dge case handling - Boundary conditions addressed
- [ ] **C**orner case detection - Unusual combinations handled
- [ ] **E**rror handling - Failure scenarios with Result pattern
- [ ] **S**ecurity - Input validation, injection prevention
- [ ] **S**tress patterns - Timeout handling, resource limits, load testing
- [ ] **A**ccessibility - API clarity, usability
- [ ] **R**egression risks - Backward compatibility, change impact
- [ ] **Y**ield quality - Output validation, type safety
```

---

## **Usage Instructions**

### **For New Agent Definitions**:

1. Copy this entire template
2. Replace `[agent_role]` placeholders with specific agent name
3. Customize workflows for agent-specific actions
4. Add agent-specific quality metrics
5. Validate against Gold Standard (Quality Enforcer - 100/100)

### **For Existing Agent Updates**:

1. Identify missing sections using this template
2. Copy relevant sections into agent definition
3. Integrate with existing content (don't duplicate)
4. Update workflows to include tool steps
5. Re-audit to validate improvement

### **Expected Impact**:

- **+15-20 points** for agents missing most sections (e.g., Chief Architect 72→92)
- **+10-15 points** for agents missing some sections (e.g., Planner 80→93)
- **+5-10 points** for agents with partial implementations (e.g., Learning 87→96)

### **Time to Implement**:

- **New agent**: 4-6 hours (complete definition from scratch)
- **Major update**: 2-4 hours (adding missing sections)
- **Minor update**: 1-2 hours (tool integration only)

---

## **Gold Standard Checklist** (Quality Enforcer - 100/100)

Use this to validate your agent definition:

- [ ] **All 5 Articles**: Explicit enforcement with code examples
- [ ] **All 5 Tools**: Integration with usage examples
- [ ] **Numbered Workflows**: Minimum 3 workflows, numbered steps
- [ ] **JSON Messages**: Typed message format examples
- [ ] **AgentContext**: Memory query/store patterns with code
- [ ] **Quality Metrics**: Performance tracking defined
- [ ] **Self-Assessment**: Checklists for self-evaluation
- [ ] **NECESSARY Pattern**: All 9 categories addressed
- [ ] **Communication Protocols**: Inter-agent coordination documented
- [ ] **Error Handling**: Result<T,E> pattern used throughout

**Score Target**: 95-100/100 (A to A+)

---

**Template Version**: 1.0
**Last Updated**: 2025-10-07
**Derived From**: Quality Enforcer (100/100) + 4 agent self-improvement proposals
**Status**: Production-Ready
