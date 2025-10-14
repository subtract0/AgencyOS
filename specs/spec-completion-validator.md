# Spec: Autonomous Completion Validator

## Meta Information

- **Status**: Draft
- **Created**: 2025-10-14
- **Author**: ChiefArchitect Agent
- **Constitutional**: Articles I, III, IV, V
- **Related ADRs**: ADR-001 (Complete Context), ADR-002 (100% Verification), ADR-003 (Automated Enforcement)
- **Related Specs**: spec-primea-execution-protocol.md, spec-task-graph.md

---

## Context

### Problem Statement

The `/primeA` orchestrator currently proceeds to report generation (STEP 7) based on procedural sequence rather than validation of actual completion. This creates a critical gap where missions can be marked "complete" despite:

1. **Incomplete tasks**: Task execution returned `None` or error
2. **Unmet acceptance criteria**: Spec tasks' criteria not validated
3. **Incomplete TodoWrite**: Not all todos marked "completed"
4. **Remaining work**: Backlog still contains work items for this mission
5. **Constitutional violations**: Articles I-V not validated
6. **Inefficient context usage**: <80% context used but work incomplete

### Root Cause Analysis

From previous investigation (`analyze_premature_conclusion` task output):

- **Missing Validation Gate**: No validation step between STEP 6 (Reflection) and STEP 7 (Report Generation) in `primeA.md` line ~911
- **Procedural vs. Validation-Based**: Orchestrator follows sequence, not validation
- **TodoWrite Comment**: Line 912 says "Mark all todos complete" but not enforced in code
- **Pattern Extracted**: Completion validation gate (confidence 1.0, VectorStore)

### Constitutional Requirements

- **Article I**: Complete context before action → All task results must be validated
- **Article II**: 100% verification → All acceptance criteria must be met
- **Article III**: Automated enforcement → No manual override of validation
- **Article IV**: Apply VectorStore patterns → Use proven completion validation patterns
- **Article V**: Spec-driven → This specification defines the validation contract

---

## Goals

1. **Prevent premature conclusion**: Block report generation when work is incomplete
2. **Constitutional compliance**: Validate all 5 articles before conclusion
3. **Comprehensive validation**: Check tasks, criteria, todos, backlog, context efficiency
4. **Backward compatibility**: Integrate seamlessly with existing `/primeA` workflow
5. **Actionable feedback**: Provide clear, actionable error messages on validation failure

---

## Non-Goals

1. **Perfect coverage**: Not validating code quality (handled by QualityEnforcer)
2. **Test execution**: Not running tests (handled by TestGenerator/Article II)
3. **Manual approval**: No human-in-the-loop checkpoints (automated enforcement)
4. **Gradual rollout**: Validation is mandatory from day 1 (Article III)

---

## Personas

### Primary User: MasterOrchestrator

**Role**: `/primeA` command handler executing mission task graphs

**Needs**:
- Validation gate before report generation
- Clear pass/fail signal (Result<ValidationReport, ValidationError>)
- Integration point at STEP 6.5 (between Reflection and Report)
- Zero breaking changes to existing task graph schema

**Success Criteria**:
- Validation executes in <3 seconds for typical missions (12 tasks)
- False positive rate <5% (no blocking on valid completions)
- 100% blocking rate on incomplete missions (no premature conclusions)

### Secondary User: Human Developer

**Role**: Developer reviewing mission execution reports

**Needs**:
- Understand why validation failed (detailed violations)
- Know what actions to take (suggested fixes)
- Confidence that "complete" means truly complete

**Success Criteria**:
- Validation report is human-readable
- Error messages reference specific tasks/criteria
- Suggested fixes are actionable

---

## Acceptance Criteria

### AC1: Validation Gate Integration

- [ ] **AC1.1**: Validator inserted at STEP 6.5 in `/primeA` execution protocol
- [ ] **AC1.2**: Validator called BEFORE STEP 7 (Generate Execution Report)
- [ ] **AC1.3**: Report generation BLOCKED if validation fails (Result<T, E> pattern)
- [ ] **AC1.4**: Backward compatibility maintained (existing missions unaffected)

### AC2: Task Completion Validation

- [ ] **AC2.1**: All tasks have `result != None`
- [ ] **AC2.2**: No tasks with `status == "failed"` or `status == "timeout"`
- [ ] **AC2.3**: All Code tasks have corresponding Test task executed
- [ ] **AC2.4**: Test tasks report passing test counts (Article II)

### AC3: Acceptance Criteria Validation

- [ ] **AC3.1**: All Spec tasks' `acceptance_criteria` validated (not empty)
- [ ] **AC3.2**: Acceptance criteria tracked in task results (Evidence of validation)
- [ ] **AC3.3**: Failed criteria listed in validation report with task references

### AC4: TodoWrite Synchronization

- [ ] **AC4.1**: All TodoWrite items have `status == "completed"`
- [ ] **AC4.2**: Todo count matches task count (1:1 mapping validated)
- [ ] **AC4.3**: TodoWrite API queried for final state before validation

### AC5: Backlog Zero Validation

- [ ] **AC5.1**: Memory Tool queried for mission-related backlog items
- [ ] **AC5.2**: Zero remaining work items for current mission ID
- [ ] **AC5.3**: Warning (not block) if backlog query fails (fallback graceful)

### AC6: Constitutional Compliance

- [ ] **AC6.1**: Article I validated (all tasks executed, no incomplete context)
- [ ] **AC6.2**: Article II validated (100% test pass rate for Test tasks)
- [ ] **AC6.3**: Article III validated (no bypass flags detected)
- [ ] **AC6.4**: Article IV validated (VectorStore patterns applied)
- [ ] **AC6.5**: Article V validated (task graph followed, spec-driven)

### AC7: Context Efficiency Warning

- [ ] **AC7.1**: Token usage tracked throughout execution
- [ ] **AC7.2**: Context usage <80% with incomplete work → Warning logged
- [ ] **AC7.3**: Efficiency warning does NOT block completion (advisory only)

### AC8: Validation Report Format

- [ ] **AC8.1**: Report is Pydantic model (`ValidationReport`)
- [ ] **AC8.2**: Contains sections: `valid`, `violations`, `warnings`, `summary`
- [ ] **AC8.3**: Each violation includes: `type`, `severity`, `description`, `suggested_fix`
- [ ] **AC8.4**: Report serializable to JSON for audit trail

### AC9: Performance Requirements

- [ ] **AC9.1**: Validation completes in <3 seconds for 12-task missions
- [ ] **AC9.2**: <5 seconds for 50-task missions
- [ ] **AC9.3**: No memory leaks during validation (idempotent)

### AC10: Error Handling

- [ ] **AC10.1**: Validation errors return `Err(ValidationError)` with details
- [ ] **AC10.2**: Validator never raises unhandled exceptions (Result pattern)
- [ ] **AC10.3**: Partial validation failures collected (all checks run, not fail-fast)

---

## Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  /primeA Execution Protocol (primeA.md)                         │
│                                                                  │
│  STEP 5: Execute Task Graph                                     │
│  STEP 6: Reflection & Evolution                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  STEP 6.5: Autonomous Completion Validation (NEW)       │   │
│  │                                                           │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │  CompletionValidator.validate(execution_result)  │   │   │
│  │  │                                                   │   │   │
│  │  │  1. Task Completion Check                       │   │   │
│  │  │  2. Acceptance Criteria Check                   │   │   │
│  │  │  3. TodoWrite Sync Check                        │   │   │
│  │  │  4. Backlog Zero Check                          │   │   │
│  │  │  5. Constitutional Compliance Check             │   │   │
│  │  │  6. Context Efficiency Warning (advisory)       │   │   │
│  │  │                                                   │   │   │
│  │  │  → Result<ValidationReport, ValidationError>    │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                           │   │
│  │  IF validation.is_err():                                  │   │
│  │      print(validation_error)                              │   │
│  │      exit(1)  # BLOCK report generation                   │   │
│  │                                                           │   │
│  │  ELSE:                                                    │   │
│  │      proceed to STEP 7                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  STEP 7: Generate Execution Report (ONLY if validation passed) │
└─────────────────────────────────────────────────────────────────┘
```

### Data Models

#### ValidationReport (Pydantic Model)

```python
from pydantic import BaseModel, Field
from typing import Literal
from shared.type_definitions.result import Result, Ok, Err

class Violation(BaseModel):
    """Detected validation violation."""
    type: Literal[
        "task_incomplete",
        "acceptance_criteria_unmet",
        "todowrite_incomplete",
        "backlog_not_empty",
        "constitutional_violation",
    ] = Field(..., description="Violation category")
    severity: Literal["critical", "high", "medium", "low"] = Field(
        ..., description="Violation severity"
    )
    description: str = Field(..., description="Human-readable violation description")
    task_id: str | None = Field(None, description="Related task ID if applicable")
    suggested_fix: str = Field(..., description="Actionable fix suggestion")

class ValidationWarning(BaseModel):
    """Non-blocking validation warning."""
    type: Literal["context_efficiency", "backlog_query_failed", "unknown"] = Field(
        ..., description="Warning category"
    )
    description: str = Field(..., description="Human-readable warning")
    recommendation: str = Field(..., description="Recommended action")

class ValidationReport(BaseModel):
    """Autonomous completion validation report."""
    valid: bool = Field(..., description="Whether mission is truly complete")
    violations: list[Violation] = Field(
        default_factory=list, description="Blocking violations"
    )
    warnings: list[ValidationWarning] = Field(
        default_factory=list, description="Non-blocking warnings"
    )
    summary: str = Field(..., description="High-level validation summary")
    tasks_validated: int = Field(..., description="Number of tasks validated")
    acceptance_criteria_met: int = Field(..., description="Number of criteria met")
    todos_completed: int = Field(..., description="Number of todos completed")
    constitutional_compliance: dict[str, bool] = Field(
        ..., description="Per-article compliance status"
    )
    context_usage_pct: float = Field(..., ge=0.0, le=100.0, description="Context usage %")
    validation_time_ms: float = Field(..., description="Validation duration in ms")

    def __str__(self) -> str:
        """Human-readable validation report."""
        status = "✅ VALID" if self.valid else "❌ INVALID"
        lines = [f"{status} Mission Completion Validation"]

        if not self.valid:
            lines.append(f"\n❌ {len(self.violations)} Blocking Violation(s):")
            for v in self.violations:
                lines.append(f"  - [{v.severity.upper()}] {v.type}: {v.description}")
                if v.task_id:
                    lines.append(f"    Task: {v.task_id}")
                lines.append(f"    Fix: {v.suggested_fix}")

        if self.warnings:
            lines.append(f"\n⚠️ {len(self.warnings)} Warning(s):")
            for w in self.warnings:
                lines.append(f"  - {w.type}: {w.description}")
                lines.append(f"    Recommendation: {w.recommendation}")

        lines.append(f"\n📊 Validation Summary:")
        lines.append(f"  - Tasks Validated: {self.tasks_validated}")
        lines.append(f"  - Acceptance Criteria Met: {self.acceptance_criteria_met}")
        lines.append(f"  - TodoWrite Completed: {self.todos_completed}")
        lines.append(f"  - Context Usage: {self.context_usage_pct:.1f}%")
        lines.append(f"  - Validation Time: {self.validation_time_ms:.1f}ms")

        return "\n".join(lines)

class ValidationError(BaseModel):
    """Validation process failure (not mission incompleteness)."""
    error_type: Literal["task_graph_invalid", "validator_failure", "unknown"] = Field(
        ..., description="Error category"
    )
    message: str = Field(..., description="Error message")
    cause: str | None = Field(None, description="Root cause if known")
```

### CompletionValidator Class

```python
from pathlib import Path
from datetime import datetime
from shared.models.task_graph import TaskGraph, ExecutionResult
from shared.agent_context import AgentContext
from shared.constitutional_validator import (
    validate_article_i,
    validate_article_ii,
    validate_article_iii,
    validate_article_iv,
    validate_article_v,
)

class CompletionValidator:
    """
    Autonomous completion validator for /primeA mission execution.

    Validates mission completion before report generation (STEP 6.5).

    Constitutional Compliance:
    - Article I: Complete context validation (all tasks, no incomplete work)
    - Article III: Automated enforcement (no manual overrides)
    - Article IV: VectorStore pattern application (proven validation patterns)
    - Article V: Spec-driven (this spec defines the validation contract)

    Usage:
        validator = CompletionValidator(task_graph, execution_result, agent_context)
        result = validator.validate()

        if result.is_err():
            print(result.unwrap_err())
            exit(1)

        report = result.unwrap()
        if not report.valid:
            print(report)
            exit(1)
    """

    def __init__(
        self,
        task_graph: TaskGraph,
        execution_result: ExecutionResult,
        agent_context: AgentContext,
    ):
        """
        Initialize completion validator.

        Args:
            task_graph: Task graph being executed
            execution_result: Result from task graph execution
            agent_context: Agent context for memory/learning access
        """
        self.task_graph = task_graph
        self.execution_result = execution_result
        self.agent_context = agent_context
        self.violations: list[Violation] = []
        self.warnings: list[ValidationWarning] = []
        self.start_time = datetime.now()

    def validate(self) -> Result[ValidationReport, ValidationError]:
        """
        Execute comprehensive completion validation.

        Validation Steps (executed in sequence, all checks run):
        1. Task completion validation
        2. Acceptance criteria validation
        3. TodoWrite synchronization validation
        4. Backlog zero validation (warning only if fails)
        5. Constitutional compliance validation
        6. Context efficiency validation (warning only)

        Returns:
            Ok(ValidationReport) if validation succeeds (may contain warnings)
            Err(ValidationError) if validator itself fails
        """
        try:
            # Step 1: Task completion
            self._validate_task_completion()

            # Step 2: Acceptance criteria
            self._validate_acceptance_criteria()

            # Step 3: TodoWrite sync
            self._validate_todowrite_sync()

            # Step 4: Backlog zero (warning only)
            self._validate_backlog_zero()

            # Step 5: Constitutional compliance
            self._validate_constitutional_compliance()

            # Step 6: Context efficiency (warning only)
            self._validate_context_efficiency()

            # Build report
            validation_time_ms = (datetime.now() - self.start_time).total_seconds() * 1000

            report = ValidationReport(
                valid=len(self.violations) == 0,
                violations=self.violations,
                warnings=self.warnings,
                summary=self._generate_summary(),
                tasks_validated=len(self.task_graph.all_tasks()),
                acceptance_criteria_met=self._count_acceptance_criteria_met(),
                todos_completed=self._count_todos_completed(),
                constitutional_compliance=self._get_constitutional_status(),
                context_usage_pct=self._calculate_context_usage(),
                validation_time_ms=validation_time_ms,
            )

            return Ok(report)

        except Exception as e:
            return Err(ValidationError(
                error_type="validator_failure",
                message=f"Validation process failed: {str(e)}",
                cause=type(e).__name__,
            ))

    def _validate_task_completion(self) -> None:
        """Validate all tasks completed successfully."""
        for task in self.task_graph.all_tasks():
            # Check task has result
            if task.result is None:
                self.violations.append(Violation(
                    type="task_incomplete",
                    severity="critical",
                    description=f"Task returned no result (None)",
                    task_id=task.id,
                    suggested_fix=f"Re-execute task {task.id} with complete implementation",
                ))

            # Check task status (if tracked)
            if task.result and task.result.get("status") in ["failed", "timeout"]:
                self.violations.append(Violation(
                    type="task_incomplete",
                    severity="critical",
                    description=f"Task failed or timed out: {task.result.get('error', 'Unknown error')}",
                    task_id=task.id,
                    suggested_fix=f"Fix error in task {task.id} and re-execute",
                ))

            # Check Code tasks have corresponding Test tasks executed
            if task.type == TaskType.CODE:
                test_task = self._find_test_for_code_task(task)
                if not test_task:
                    self.violations.append(Violation(
                        type="task_incomplete",
                        severity="critical",
                        description=f"Code task missing Test task (Article II violation)",
                        task_id=task.id,
                        suggested_fix=f"Generate and execute test for {task.id}",
                    ))
                elif test_task.result is None:
                    self.violations.append(Violation(
                        type="task_incomplete",
                        severity="critical",
                        description=f"Test task not executed",
                        task_id=test_task.id,
                        suggested_fix=f"Execute test task {test_task.id}",
                    ))

    def _validate_acceptance_criteria(self) -> None:
        """Validate all acceptance criteria met for Spec tasks."""
        spec_tasks = [t for t in self.task_graph.all_tasks() if t.type == TaskType.SPEC]

        for spec_task in spec_tasks:
            if not spec_task.acceptance_criteria:
                self.violations.append(Violation(
                    type="acceptance_criteria_unmet",
                    severity="high",
                    description=f"Spec task has no acceptance criteria (Article V)",
                    task_id=spec_task.id,
                    suggested_fix=f"Define acceptance criteria for {spec_task.id}",
                ))
                continue

            # Check if criteria tracked in result
            if spec_task.result:
                criteria_results = spec_task.result.get("acceptance_criteria_results", {})
                unmet_criteria = [
                    criterion for criterion in spec_task.acceptance_criteria
                    if not criteria_results.get(criterion, False)
                ]

                if unmet_criteria:
                    self.violations.append(Violation(
                        type="acceptance_criteria_unmet",
                        severity="high",
                        description=f"{len(unmet_criteria)} criteria unmet: {unmet_criteria[:2]}...",
                        task_id=spec_task.id,
                        suggested_fix=f"Validate all acceptance criteria for {spec_task.id}",
                    ))

    def _validate_todowrite_sync(self) -> None:
        """Validate TodoWrite todos are all completed."""
        # Query TodoWrite state (via agent_context or API)
        # NOTE: This requires TodoWrite API integration - placeholder implementation

        # For now, check execution_result metadata
        todos_total = self.execution_result.graph.metadata.get("todos_total", 0)
        todos_completed = self.execution_result.graph.metadata.get("todos_completed", 0)

        if todos_total > 0 and todos_completed < todos_total:
            self.violations.append(Violation(
                type="todowrite_incomplete",
                severity="high",
                description=f"TodoWrite incomplete: {todos_completed}/{todos_total} completed",
                task_id=None,
                suggested_fix="Mark all TodoWrite items as 'completed' before finalizing report",
            ))

    def _validate_backlog_zero(self) -> None:
        """Validate mission backlog is empty (warning only)."""
        try:
            # Query Memory Tool for backlog items related to this mission
            mission_id = self.task_graph.metadata.get("mission_id")
            if not mission_id:
                return  # No mission ID, skip backlog check

            # Search memories for backlog items
            backlog_items = self.agent_context.search_memories(
                tags=["backlog", mission_id],
                include_session=False,
            )

            if backlog_items:
                self.warnings.append(ValidationWarning(
                    type="backlog_not_empty",
                    description=f"{len(backlog_items)} backlog items remaining for mission",
                    recommendation="Review and close backlog items before marking mission complete",
                ))

        except Exception as e:
            self.warnings.append(ValidationWarning(
                type="backlog_query_failed",
                description=f"Failed to query backlog: {str(e)}",
                recommendation="Manually verify backlog is empty",
            ))

    def _validate_constitutional_compliance(self) -> None:
        """Validate all 5 constitutional articles."""
        try:
            # Article I: Complete context
            validate_article_i(agent_context=self.agent_context)

            # Article II: 100% verification (check test pass rate)
            test_tasks = [t for t in self.task_graph.all_tasks() if t.type == TaskType.TEST]
            for test_task in test_tasks:
                if test_task.result:
                    tests_passing = test_task.result.get("tests_passing", 0)
                    tests_total = test_task.result.get("tests_total", 0)
                    if tests_total > 0 and tests_passing < tests_total:
                        self.violations.append(Violation(
                            type="constitutional_violation",
                            severity="critical",
                            description=f"Article II violated: {tests_passing}/{tests_total} tests passing",
                            task_id=test_task.id,
                            suggested_fix=f"Fix failing tests in {test_task.id}",
                        ))

            # Article III: Automated enforcement
            validate_article_iii()

            # Article IV: Learning integration
            validate_article_iv(agent_context=self.agent_context)

            # Article V: Spec-driven development
            validate_article_v()

        except Exception as e:
            self.violations.append(Violation(
                type="constitutional_violation",
                severity="critical",
                description=f"Constitutional compliance check failed: {str(e)}",
                task_id=None,
                suggested_fix="Ensure all 5 constitutional articles are satisfied",
            ))

    def _validate_context_efficiency(self) -> None:
        """Validate context usage efficiency (warning only)."""
        context_usage_pct = self._calculate_context_usage()

        # Warn if context usage <80% but work is incomplete
        if context_usage_pct < 80.0 and self.violations:
            self.warnings.append(ValidationWarning(
                type="context_efficiency",
                description=f"Low context usage ({context_usage_pct:.1f}%) with incomplete work",
                recommendation="Increase context window or optimize token usage to complete mission",
            ))

    # Helper methods

    def _find_test_for_code_task(self, code_task: Task) -> Task | None:
        """Find corresponding test task for code task."""
        test_tasks = [t for t in self.task_graph.all_tasks() if t.type == TaskType.TEST]
        for test_task in test_tasks:
            if test_task.verification_target == code_task.id:
                return test_task
        return None

    def _generate_summary(self) -> str:
        """Generate human-readable validation summary."""
        if len(self.violations) == 0:
            return "✅ Mission complete: All validation checks passed"
        else:
            return f"❌ Mission incomplete: {len(self.violations)} blocking violations detected"

    def _count_acceptance_criteria_met(self) -> int:
        """Count acceptance criteria met across all Spec tasks."""
        count = 0
        spec_tasks = [t for t in self.task_graph.all_tasks() if t.type == TaskType.SPEC]
        for spec_task in spec_tasks:
            if spec_task.result:
                criteria_results = spec_task.result.get("acceptance_criteria_results", {})
                count += sum(1 for met in criteria_results.values() if met)
        return count

    def _count_todos_completed(self) -> int:
        """Count completed TodoWrite items."""
        return self.execution_result.graph.metadata.get("todos_completed", 0)

    def _get_constitutional_status(self) -> dict[str, bool]:
        """Get per-article constitutional compliance status."""
        return {
            "article_i": len([v for v in self.violations if "Article I" in v.description]) == 0,
            "article_ii": len([v for v in self.violations if "Article II" in v.description]) == 0,
            "article_iii": True,  # Validated by validate_article_iii()
            "article_iv": True,  # Validated by validate_article_iv()
            "article_v": len([v for v in self.violations if "Article V" in v.description]) == 0,
        }

    def _calculate_context_usage(self) -> float:
        """Calculate context usage percentage."""
        # This would calculate actual token usage / max context window
        # Placeholder implementation
        total_tokens = sum(t.estimated_tokens or 3000 for t in self.task_graph.all_tasks())
        max_context = 200_000  # Default max context (e.g., GPT-5)
        return min((total_tokens / max_context) * 100, 100.0)
```

### Integration into `/primeA` Execution Protocol

**File**: `.claude/commands/primeA.md`

**Location**: Between STEP 6 (Reflection) and STEP 7 (Report Generation)

**Insertion Point**: Line ~906 (after STEP 6 completes, before STEP 7)

```python
# STEP 6: Reflection & Evolution (existing, lines 820-904)
# ... existing code ...

# ===================================================================
# STEP 6.5: Autonomous Completion Validation (NEW)
# ===================================================================

print("\n" + "="*70)
print("🔍 STEP 6.5: Autonomous Completion Validation")
print("="*70 + "\n")

# Import validator
from tools.orchestrator.completion_validator import CompletionValidator

# Create validator instance
validator = CompletionValidator(
    task_graph=graph,
    execution_result=execution_result,
    agent_context=agent_context,
)

# Execute validation
validation_result = validator.validate()

# Handle validation failure (validator error)
if validation_result.is_err():
    error = validation_result.unwrap_err()
    print(f"""
❌ VALIDATION PROCESS FAILED
Error Type: {error.error_type}
Message: {error.message}
Cause: {error.cause or 'Unknown'}

Cannot proceed to report generation. Fix validation infrastructure and retry.
""")
    exit(1)

# Handle validation report
validation_report = validation_result.unwrap()

print(validation_report)  # Human-readable output

# BLOCKING: Halt if validation fails
if not validation_report.valid:
    print(f"""
❌ MISSION INCOMPLETE - BLOCKED BY VALIDATION

{len(validation_report.violations)} blocking violation(s) detected.
Report generation halted per Article III (Automated Enforcement).

Fix violations above and re-execute mission.
""")
    exit(1)

# Log warnings (non-blocking)
if validation_report.warnings:
    print(f"\n⚠️ {len(validation_report.warnings)} advisory warning(s) detected.")
    print("These are non-blocking but should be reviewed.\n")

print("\n✅ Validation PASSED - Proceeding to report generation\n")

# ===================================================================
# STEP 7: Generate Execution Report (ONLY if validation passed)
# ===================================================================
# ... existing code (lines 908-980) ...
```

---

## Edge Cases

### Edge Case 1: Partial Task Execution

**Scenario**: Task graph has 12 tasks, but only 8 executed before timeout

**Expected Behavior**:
- Validation detects 4 tasks with `result == None`
- Violation type: `task_incomplete`, severity: `critical`
- Suggested fix: "Re-execute incomplete tasks with extended timeout"
- Mission blocked from completion

**Mitigation**: Article I retry mechanism (2x, 3x timeout) prevents this

### Edge Case 2: Acceptance Criteria Not Tracked

**Scenario**: Spec task completes but doesn't populate `acceptance_criteria_results` in result

**Expected Behavior**:
- Validation assumes criteria unmet if not explicitly tracked
- Violation type: `acceptance_criteria_unmet`, severity: `high`
- Suggested fix: "Validate and track acceptance criteria in task result"

**Mitigation**: Update task execution to always populate criteria results

### Edge Case 3: TodoWrite API Unavailable

**Scenario**: TodoWrite service is down during validation

**Expected Behavior**:
- Validation catches exception, adds warning (not violation)
- Warning type: `backlog_query_failed`
- Recommendation: "Manually verify todos completed"
- Validation continues (graceful degradation)

**Mitigation**: TodoWrite validation is non-critical, warns instead of blocks

### Edge Case 4: Constitutional Validator Failure

**Scenario**: `validate_article_iii()` raises unexpected exception

**Expected Behavior**:
- Violation added: type: `constitutional_violation`, severity: `critical`
- Description: "Constitutional compliance check failed: [exception message]"
- Mission blocked from completion

**Mitigation**: Constitutional compliance is mandatory, cannot proceed on failure

### Edge Case 5: Zero-Task Mission

**Scenario**: Task graph has 0 tasks (empty mission)

**Expected Behavior**:
- Validation passes (no tasks to validate)
- Warning added: "Zero-task mission detected"
- Report generation proceeds (edge case, but valid)

**Mitigation**: Task graph schema should prevent empty missions (Pydantic validator)

### Edge Case 6: Context Usage >100%

**Scenario**: Token calculation overflow due to estimation errors

**Expected Behavior**:
- `_calculate_context_usage()` returns `min(usage, 100.0)`
- No warning (usage >80%)
- Validation unaffected

**Mitigation**: Clamp context usage to 100% maximum

---

## Implementation Notes

### File Structure

```
tools/orchestrator/
├── completion_validator.py       # Main validator class (this spec)
├── completion_validator_models.py # Pydantic models (ValidationReport, Violation, etc.)
└── tests/
    ├── test_completion_validator.py              # Unit tests (100% coverage)
    └── test_completion_validator_integration.py  # Integration tests with /primeA
```

### Dependencies

- `pydantic>=2.0`: Data models with validation
- `shared.type_definitions.result`: Result<T, E> pattern
- `shared.models.task_graph`: TaskGraph, ExecutionResult, Task
- `shared.agent_context`: AgentContext for memory/learning
- `shared.constitutional_validator`: validate_article_*() functions

### Testing Strategy

#### Unit Tests (test_completion_validator.py)

1. **Test Task Completion Validation**
   - All tasks completed → No violations
   - Task with `result == None` → Critical violation
   - Task with `status == "failed"` → Critical violation
   - Code task without Test task → Critical violation

2. **Test Acceptance Criteria Validation**
   - Spec task with all criteria met → No violations
   - Spec task with unmet criteria → High violation
   - Spec task with no criteria → High violation

3. **Test TodoWrite Sync Validation**
   - All todos completed → No violations
   - Incomplete todos → High violation
   - TodoWrite API unavailable → Warning (not violation)

4. **Test Backlog Zero Validation**
   - Empty backlog → No violations
   - Non-empty backlog → Warning (not violation)
   - Backlog query fails → Warning with fallback

5. **Test Constitutional Compliance**
   - All articles validated → No violations
   - Article II test failure → Critical violation
   - Article validation exception → Critical violation

6. **Test Context Efficiency**
   - Context usage >80% → No warning
   - Context usage <80% with violations → Warning
   - Context usage <80% without violations → No warning

7. **Test Edge Cases**
   - Zero-task mission → Passes with warning
   - All tasks failed → Multiple critical violations
   - Validator exception → Returns `Err(ValidationError)`

#### Integration Tests (test_completion_validator_integration.py)

1. **Test Integration with /primeA**
   - Execute mission → Validation passes → Report generated
   - Execute mission → Validation fails → Report blocked
   - Execute mission → Warnings only → Report generated with warnings

2. **Test Backward Compatibility**
   - Existing missions (no validator) → Still work
   - Existing missions (with validator) → Pass validation
   - Invalid missions (with validator) → Blocked correctly

### Performance Benchmarks

| Mission Size | Tasks | Expected Validation Time |
|--------------|-------|--------------------------|
| Small        | 6     | <1 second                |
| Medium       | 12    | <3 seconds               |
| Large        | 50    | <5 seconds               |
| Extra Large  | 100   | <10 seconds              |

### Constitutional Compliance

- **Article I**: Complete context → All checks run, no fail-fast behavior
- **Article II**: 100% verification → Test pass rate validated for Test tasks
- **Article III**: Automated enforcement → No manual overrides, Result<T, E> pattern
- **Article IV**: Learning integration → VectorStore patterns applied (proven validation rules)
- **Article V**: Spec-driven → This spec defines the validation contract

---

## Alternative Approaches Considered

### Alternative 1: Lightweight Validation (Rejected)

**Approach**: Only validate task results != None, skip constitutional compliance

**Pros**:
- Faster (<1 second)
- Simpler implementation
- Lower maintenance burden

**Cons**:
- Incomplete validation (misses criteria, todos, constitutional violations)
- Allows missions to complete with unmet acceptance criteria
- Violates Article III (incomplete automated enforcement)

**Rejection Reason**: Insufficient coverage, allows premature conclusion

### Alternative 2: Post-Report Validation (Rejected)

**Approach**: Generate report first, then validate, rollback if invalid

**Pros**:
- Backward compatible (report always generated)
- Validation errors visible in report

**Cons**:
- Report generation wasted effort if validation fails
- Rollback complexity (undo report file creation)
- Violates Article III (validation must be pre-action, not post-action)

**Rejection Reason**: Backward approach, violates constitution

### Alternative 3: Manual Approval Checkpoint (Rejected)

**Approach**: Human reviews validation report, approves/rejects completion

**Pros**:
- Human oversight for edge cases
- Flexibility to override validation

**Cons**:
- Violates Article III (no manual overrides permitted)
- Slow (human bottleneck)
- Reduces autonomy (not truly autonomous)

**Rejection Reason**: Constitutional violation, reduces autonomy

---

## Migration and Rollout

### Phase 1: Implementation (Week 1)

- Implement `CompletionValidator` class
- Implement Pydantic models (`ValidationReport`, `Violation`, `ValidationWarning`)
- Write unit tests (100% coverage)
- Integration tests with mock task graphs

### Phase 2: Integration (Week 1)

- Insert STEP 6.5 into `/primeA` execution protocol
- Update `primeA.md` documentation
- Test with existing mission graphs (backward compatibility)

### Phase 3: Validation (Week 2)

- Run validator on 10 historical missions (verify no false positives)
- Stress test with 100-task missions (performance benchmarking)
- Document known edge cases and mitigations

### Phase 4: Production (Week 2)

- Deploy to production `/primeA` command
- Monitor validation pass/fail rates (target: <5% false positives)
- Store validation reports to audit trail (AGENCY_DATA_DIR)

### Rollback Plan

If validator causes >5% false positive rate:

1. Add `--skip-validation` flag to `/primeA` (temporary escape hatch)
2. Log skipped validations to telemetry (identify patterns)
3. Fix validator logic based on patterns
4. Remove `--skip-validation` flag after fix

---

## Success Metrics

### Primary Metrics

1. **Zero Premature Conclusions**: 0 missions marked "complete" with incomplete work (0% false negatives)
2. **Low False Positive Rate**: <5% missions blocked incorrectly (95% precision)
3. **Fast Validation**: <3 seconds for 12-task missions (99th percentile)
4. **100% Constitutional Compliance**: All missions validated against Articles I-V

### Secondary Metrics

1. **Validation Pass Rate**: >90% of missions pass validation on first attempt
2. **Warning Rate**: <20% of missions have warnings (low advisory noise)
3. **Violation Clarity**: 100% of violations have actionable suggested fixes
4. **Developer Satisfaction**: >80% of developers find validation helpful (survey)

---

## Future Enhancements

### Enhancement 1: Machine Learning Validation

**Description**: Use ML model to predict mission completion likelihood before validation

**Benefits**:
- Proactive warning if mission likely to fail validation
- Reduce wasted execution time on doomed missions

**Implementation**: Train model on historical validation reports, deploy as pre-flight check

### Enhancement 2: Auto-Remediation

**Description**: Validator automatically fixes low-severity violations (e.g., add missing TodoWrite entries)

**Benefits**:
- Reduce manual fix effort
- Increase validation pass rate

**Implementation**: Add `auto_fix: bool` parameter to `CompletionValidator.validate()`

### Enhancement 3: Incremental Validation

**Description**: Validate incrementally during execution (after each phase), not just at end

**Benefits**:
- Catch violations earlier (fail-fast)
- Reduce wasted work on invalid missions

**Implementation**: Add phase-level validation hooks in STEP 5 (Execute Task Graph)

---

## Appendix

### A. Related Documentation

- `constitution.md`: Constitutional articles (Articles I-V)
- `docs/adr/ADR-001-complete-context-before-action.md`: Article I rationale
- `docs/adr/ADR-002-100-verification-and-stability.md`: Article II rationale
- `docs/adr/ADR-003-automated-merge-enforcement.md`: Article III rationale
- `.claude/commands/primeA.md`: Execution protocol documentation

### B. Glossary

- **Completion Validation**: Verification that mission is truly complete (all work done)
- **Premature Conclusion**: Mission marked "complete" despite incomplete work
- **Validation Gate**: Blocking checkpoint that prevents invalid state transitions
- **Constitutional Compliance**: Adherence to all 5 constitutional articles
- **False Positive**: Valid mission blocked incorrectly by validator
- **False Negative**: Invalid mission passes validator incorrectly

---

**End of Specification**
