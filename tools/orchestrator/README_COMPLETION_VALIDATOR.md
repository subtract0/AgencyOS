# Autonomous Completion Validator (STEP 6.5)

**Constitutional Gate**: Enforces 100% task completion before execution report generation.

## Overview

The `CompletionValidator` is a validation gate that ensures primeA autonomous execution reaches 100% completion before generating the final execution report (STEP 7). This enforces constitutional requirements that all tasks must be completed, acceptance criteria met, and TodoWrite synchronized.

## Constitutional Compliance

- **Article I**: Complete context validation (all tasks executed)
- **Article II**: 100% verification requirement (all tests pass)
- **Article III**: Automated enforcement (no manual overrides)
- **Article IV**: VectorStore pattern storage (learned completion patterns)
- **Article V**: Spec-driven validation (acceptance criteria traceability)

## Integration Point

**File**: `.claude/commands/primeA.md`
**Location**: Line ~906, between STEP 6 (Post-Execution Reflection) and STEP 7 (Generate Execution Report)

## Validation Checks

The validator performs 6 critical checks:

### 1. Task Completion
- **Requirement**: All tasks have `status: "success"`
- **Failure**: Returns `Err` with incomplete task IDs
- **Constitutional**: Article I (complete context)

### 2. Acceptance Criteria
- **Requirement**: All tasks have `acceptance_criteria_met: True`
- **Failure**: Returns `Err` with unmet criteria
- **Constitutional**: Article V (spec-driven development)

### 3. TodoWrite Synchronization
- **Requirement**: All todos have `status: "completed"`
- **Failure**: Returns `Err` with incomplete todos
- **Constitutional**: Article I (context reflects reality)

### 4. Backlog Zero
- **Requirement**: No pending backlog items
- **Warning Only**: Logs warning but doesn't block
- **Constitutional**: Article IV (continuous learning)

### 5. Constitutional Compliance
- **Requirement**: All 5 articles validated
- **Failure**: Returns `Err` if any article fails
- **Constitutional**: All articles (comprehensive)

### 6. Context Efficiency
- **Requirement**: Context usage ≥80% (recommended)
- **Warning Only**: Logs warning if below threshold
- **Constitutional**: Article I (efficient context usage)

## Usage

### Basic Usage

```python
from tools.orchestrator.completion_validator import CompletionValidator

# Collect validation inputs
validator = CompletionValidator(
    task_results=[
        {"id": "task1", "status": "success", "acceptance_criteria_met": True},
        {"id": "task2", "status": "success", "acceptance_criteria_met": True},
    ],
    todos=[
        {"content": "Task 1", "status": "completed", "activeForm": "Completed"},
        {"content": "Task 2", "status": "completed", "activeForm": "Completed"},
    ],
    spec_criteria=["Feature A implemented", "Feature B tested"],
    backlog_items=[],
    context_usage=0.85,
)

# Execute validation
result = validator.validate()

if result.is_ok():
    # VALIDATION PASSED - PROCEED TO STEP 7
    validation = result.unwrap()
    print(validation.get_summary())
    proceed_to_step_7()
else:
    # VALIDATION FAILED - CONTINUE EXECUTION
    error = result.unwrap_err()
    print(f"Validation failed: {error.message}")
    return_to_step_4()  # Continue until 100% complete
```

### Integration in primeA.md

```python
# STEP 6.5: Validate Autonomous Completion
from tools.orchestrator.completion_validator import CompletionValidator

# Collect inputs
task_results = [
    {
        "id": task.id,
        "status": task.status,
        "acceptance_criteria_met": task.acceptance_criteria_met,
        "type": task.type,
    }
    for task in graph.get_all_tasks()
]

todos = context.get("todos", [])

# Execute validation
validator = CompletionValidator(
    task_results=task_results,
    todos=todos,
    spec_criteria=spec_criteria,
    backlog_items=backlog_items,
    context_usage=context_usage,
)

validation_result = validator.validate()

if validation_result.is_err():
    # BLOCK STEP 7 - Continue execution
    error = validation_result.unwrap_err()
    raise ValidationError(f"Completion validation failed: {error.message}")
else:
    # PROCEED TO STEP 7
    validation = validation_result.unwrap()
    print(validation.get_summary())
```

## Validation Results

### Success (`Ok`)

```python
ValidationResults(
    all_tasks_completed=True,
    acceptance_criteria_met=True,
    todowrite_synced=True,
    backlog_zero=True,
    constitutional_compliant=True,
    context_efficiency=0.85,
    constitutional_checks=ConstitutionalChecks(...),
    warnings=[],
    errors=[],
)
```

### Failure (`Err`)

```python
ValidationError(
    reason="incomplete_tasks",
    message="Found 2 incomplete task(s): task3, task4",
    failed_checks=["task_completion"],
    suggestions=[
        "Continue execution until all tasks reach 'success' status",
        "Retry failed tasks with constitutional timeout policy (2x, 3x, 10x)",
    ],
)
```

## Error Types

| Reason | Description | Action |
|--------|-------------|--------|
| `no_tasks` | No tasks found in execution | Generate task graph and execute |
| `incomplete_tasks` | Tasks not all `status: "success"` | Continue execution, retry failures |
| `acceptance_criteria_unmet` | Acceptance criteria not met | Review spec, verify implementation |
| `todowrite_mismatch` | TodoWrite out of sync | Update TodoWrite to reflect reality |
| `constitutional_violation` | Any constitutional check failed | Fix violations before STEP 7 |
| `context_inefficiency` | Context usage <80% (warning) | Optimize context or reduce verbosity |
| `unknown` | Unexpected validation error | Debug validation logic |

## Constitutional Checks

The validator validates all 5 constitutional articles:

```python
ConstitutionalChecks(
    article_i=True,   # Complete context (all tasks executed)
    article_ii=True,  # 100% verification (all tests pass)
    article_iii=True, # Automated enforcement (validator itself)
    article_iv=True,  # Continuous learning (VectorStore)
    article_v=True,   # Spec-driven (acceptance criteria)
    details={
        "Article I": "✅ All tasks executed to completion",
        "Article II": "✅ 100% test pass rate",
        "Article III": "✅ Automated validation enforced",
        "Article IV": "✅ VectorStore completion patterns applied (confidence 1.0)",
        "Article V": "✅ 3 acceptance criteria validated",
    },
)
```

## Examples

See `tools/orchestrator/completion_validator_example.py` for comprehensive examples:

```bash
python -m tools.orchestrator.completion_validator_example
```

## Testing

Comprehensive test suite with NECESSARY pattern coverage:

```bash
# Run completion validator tests
python -m pytest tests/tools/orchestrator/test_completion_validator.py -v

# Expected: 14 tests, 100% pass rate
# - 2 normal cases
# - 4 edge cases
# - 1 security case
# - 2 spec traceability cases
# - 2 resilience cases
# - 1 year-round case
# - 2 constitutional compliance cases
```

## Implementation Files

- **Validator**: `tools/orchestrator/completion_validator.py`
- **Tests**: `tests/tools/orchestrator/test_completion_validator.py`
- **Examples**: `tools/orchestrator/completion_validator_example.py`
- **Integration**: `.claude/commands/primeA.md` (STEP 6.5, line ~906)
- **Documentation**: `tools/orchestrator/README_COMPLETION_VALIDATOR.md`

## Key Design Decisions

### Result Pattern
Uses `Result<T, E>` pattern for error handling (no exceptions for control flow).

### Pydantic Models
All data structures are typed Pydantic models (no `Dict[Any, Any]`).

### Constitutional Integration
Validator itself IS the enforcement mechanism for Article III (automated enforcement).

### VectorStore Learning
Successful validations stored with confidence 1.0 for future pattern reuse (Article IV).

### Spec Traceability
Acceptance criteria validated against spec.md (Article V).

## Acceptance Criteria

- ✅ Validator integrated into execution protocol (STEP 6.5)
- ✅ All validation checks implemented and tested (6 checks)
- ✅ Clear error messages when validation fails (suggestions included)
- ✅ Execution continues until 100% complete or explicit failure (no bypass)
- ✅ 14 tests with 100% pass rate
- ✅ Constitutional compliance (Articles I-V)
- ✅ NECESSARY pattern coverage (7 categories)

## Related Documentation

- **Constitution**: `constitution.md` (Articles I-V)
- **ADR-001**: Complete Context Before Action
- **ADR-002**: 100% Verification and Stability
- **ADR-004**: Continuous Learning (VectorStore)
- **ADR-007**: Spec-Driven Development
- **Test Verification Gate**: `tools/orchestrator/test_verification_gate.py`
- **NECESSARY Validator**: `tools/orchestrator/necessary_validator.py`

---

**Version**: 1.0
**Author**: AgencyOS Code Agent
**Date**: 2025-10-14
**Constitutional Compliance**: ✅ All 5 Articles
