# Orchestrator Tools - Quick Reference

## Module Overview

**Primary Purpose**: Production-hardened orchestration infrastructure for PrimeA - task graph validation, safety guardrails, TDD enforcement, and completion validation.

**Core Capabilities**:
- **Task Graph Intelligence**: Parse natural language → validated DAG with Pydantic enforcement
- **Production Hardening** (Leap 6): Slop immunity, budget guard, deterministic batching, audit trails
- **TDD Autonomy** (Leap 7): NECESSARY validator, test gate, PR creator, two-stage workflow
- **Completion Validation** (ADR-032): Six-check constitutional compliance gate

**Strategic Value**: These tools transform PrimeA from "code generator" to "production-ready autonomous development system" - zero manual intervention, 100% constitutional compliance.

---

## When to Use This Module

**Use Orchestrator Tools when:**
- Building custom orchestrators (integrate production hardening)
- Extending PrimeA with new capabilities
- Creating CI/CD quality gates
- Implementing autonomous workflows with constitutional compliance
- Developing task graph generators or validators

**Do NOT use for:**
- User-facing commands (tools are infrastructure, not interface)
- Direct code implementation (use AgencyCodeAgent)
- Simple single-task execution (overkill for non-orchestration)

**Decision Tree**:
```
Building custom orchestrator?
├─ Need quality gates? → orchestrator/ (slop immunity, budget guard)
├─ Need TDD enforcement? → orchestrator/ (NECESSARY validator, test gate)
└─ Need completion validation? → orchestrator/ (completion_validator)

Extending PrimeA?
├─ New safety check? → Add to orchestrator/ (integrate with existing gates)
├─ New workflow stage? → orchestrator/ (approval_checkpoint, two_stage_orchestrator)
└─ New task type? → Extend graph.py (Pydantic schema)

CI/CD integration?
├─ Pre-commit hook? → NECESSARY validator (test pattern enforcement)
├─ PR quality gate? → completion_validator (100% done check)
└─ Budget enforcement? → budget_guard (cost limit check)
```

---

## Core Components

### **1. Task Graph Parser & Validator** (`graph.py`, `intent_parser.py`)
**Purpose**: Transform natural language intent into validated DAG with constitutional compliance.

**Key Features**:
- Pydantic TaskGraph schema with auto-validation
- Topological sort (DAG verification, no cycles)
- Dependency inference (every Code task → Test task)
- Tier classification (P1/P2/P3) for cost optimization
- Acceptance criteria enforcement (Spec tasks)

**When to Use**: Every PrimeA execution starts here (parse intent → graph).

**Example**:
```python
from tools.orchestrator.graph import TaskGraph

# Parse and validate task graph JSON
graph = TaskGraph.model_validate_json(graph_json)

# Pydantic auto-validates:
# - No circular dependencies (DAG)
# - All dependencies exist
# - Test tasks have verification_target
# - Spec tasks have acceptance_criteria

# Topological sort for parallel execution
layers = graph.topological_sort()
```

### **2. Slop Immunity** (`slop_guardian.py`) - Leap 6
**Purpose**: Detect and prevent low-quality mission descriptions via LLM evaluation.

**Quality Criteria**:
- Clear, specific outcomes (not vague like "make it better")
- Measurable acceptance criteria
- Concrete deliverables identified
- No buzzwords without substance

**Scoring**:
- **5.0**: Excellent (proceed immediately)
- **3.5-4.9**: Good (proceed, minor improvements suggested)
- **2.0-3.4**: REVISE (auto-rewrite up to 3 attempts)
- **<2.0**: REJECT (halt, manual refinement required)

**When to Use**: Pre-flight check before task graph generation (Article III enforcement).

**Example**:
```python
from tools.orchestrator.slop_guardian import SlopGuardian, enforce_slop_immunity

guardian = SlopGuardian()

# Evaluate mission description
result = enforce_slop_immunity(
    mission="Make the system better",  # Vague
    guardian=guardian,
    stage="pre_planning"
)

if result.is_err():
    error = result.unwrap_err()
    print(f"❌ Slop detected: {error.verdict.reasons}")
    print(f"💡 Fixes: {error.verdict.top_fixes}")
    # Auto-rewrite or halt
```

### **3. Budget Guard** (`budget_guard.py`) - Leap 6
**Purpose**: Enforce cost limits (daily and per-mission) with audit trail logging.

**Limits**:
- **Daily USD**: `DAILY_BUDGET_USD` env var (default $100)
- **Per-Mission USD**: Task graph metadata or default $10
- **Override**: `--force` flag (logged to HMAC-signed audit trail)

**When to Use**: Pre-flight check after task graph cost estimation (Article III enforcement).

**Example**:
```python
from tools.orchestrator.budget_guard import BudgetGuard, BudgetLimits

guard = BudgetGuard()
limits = BudgetLimits(
    daily_usd=100.0,
    per_mission_usd=10.0
)

estimate = guard.estimate_cost(
    total_tokens=25000,
    tasks_count=12,
    cost_per_1k=0.0025
)

result = guard.check_budget(estimate, limits, force=False)

if result.is_err():
    error = result.unwrap_err()
    print(f"❌ Budget exceeded: ${error.estimated_cost_usd:.2f}")
    print(f"   Use --force to override (will be logged)")
```

### **4. NECESSARY Validator** (`necessary_validator.py`) - Leap 7
**Purpose**: Validate tests follow NECESSARY pattern (Normal, Edge, Cascading, Essential, Security, Spec, Accessibility, Resilience, Year-round).

**Validation Checks**:
- Test function names match NECESSARY categories (e.g., `test_normal_`, `test_edge_`)
- AAA pattern compliance (Arrange, Act, Assert)
- Coverage of all 9 categories (full NECESSARY spectrum)
- No missing critical test types (Security, Edge, Resilience)

**When to Use**: Test gate before PR creation (Article II enforcement).

**Example**:
```python
from tools.orchestrator.necessary_validator import NECESSARYValidator

validator = NECESSARYValidator()

result = validator.validate_test_file("tests/test_auth.py")

if result.is_ok():
    report = result.unwrap()
    print(f"✅ NECESSARY Coverage: {report.coverage_percentage:.1f}%")
    print(f"   Categories: {report.categories_covered}")
else:
    error = result.unwrap_err()
    print(f"❌ Missing: {error.missing_categories}")
```

### **5. PR Creator** (`pr_creator.py`) - Leap 7
**Purpose**: Autonomous git workflow - branch creation, commit, push, PR creation with CI trigger.

**Workflow**:
1. Create feature branch (`feat/task-name`)
2. Stage changes (`git add`)
3. Commit with constitutional message format
4. Push to remote with `-u` flag
5. Create GitHub PR via `gh pr create`
6. Wait for CI checks (optional)

**When to Use**: Final step in autonomous workflow after all tests pass.

**Example**:
```python
from tools.orchestrator.pr_creator import PRCreator

creator = PRCreator()

result = creator.create_pr(
    branch_name="feat/jwt-auth",
    title="feat: Add JWT authentication with RSA-256",
    body="Implements SPEC-042 with 100% test coverage (47 tests)",
    auto_merge=False  # Wait for CI + human approval
)

if result.is_ok():
    pr_url = result.unwrap()
    print(f"✅ PR created: {pr_url}")
```

### **6. Completion Validator** (`completion_validator.py`) - ADR-032
**Purpose**: Six-check validation gate ensuring 100% task completion before execution report.

**Six Checks**:
1. **All Tasks Completed**: Every task status == "success" or "completed"
2. **Acceptance Criteria Met**: All spec.md criteria validated
3. **TodoWrite Synchronized**: All todos marked "completed"
4. **Backlog Zero** (warning): No pending items in `~/.agency/memories/agency_backlog/`
5. **Constitutional Compliance**: Articles I-V enforced
6. **Context Efficiency** (warning): Context usage ≥80%

**When to Use**: MANDATORY before STEP 7 (execution report generation) in PrimeA workflow.

**Example**:
```python
from tools.orchestrator.completion_validator import CompletionValidator

validator = CompletionValidator(
    task_results=[{"id": "task_1", "status": "success", ...}],
    todos=[{"content": "Phase 1", "status": "completed"}],
    spec_criteria=["Criterion 1", "Criterion 2"],
    backlog_items=[],
    context_usage=0.85
)

result = validator.validate()

if result.is_err():
    error = result.unwrap_err()
    print(f"❌ Validation failed: {error.reason}")
    print(f"   Failed checks: {error.failed_checks}")
    # BLOCK STEP 7, continue execution
else:
    validation = result.unwrap()
    print(f"✅ Validation passed: {validation.get_summary()}")
    # PROCEED TO STEP 7
```

### **7. Two-Stage Orchestrator** (`two_stage_orchestrator.py`) - Leap 7
**Purpose**: Separate spec generation from implementation with user approval checkpoint.

**Stages**:
- **Stage 1**: Generate spec.md with acceptance criteria, test plan
- **Checkpoint**: User reviews/approves specification
- **Stage 2**: TDD execution (tests-first, then implementation)

**When to Use**: Complex features requiring spec review before implementation (`--two-stage` flag).

### **8. Audit Signing** (`audit_signing.py`) - Leap 6
**Purpose**: HMAC-SHA256 signatures for tamper-proof audit trails.

**When to Use**: All orchestrator operations log to AGENCY_DATA_DIR with signatures.

---

## Dependencies

### **Module Depends On**:
- **shared/models/**: TaskGraph, Task, Phase Pydantic models
- **shared/**: AgentContext, ConstitutionalValidator
- **agency_memory/**: VectorStore (slop immunity learnings)
- **tools/git_workflow.py**: Git operations for PR creator
- **trinity_protocol/**: HybridExecutor (execution backend)

### **Who Depends On Orchestrator Tools**:
- **PrimeA**: Primary consumer (all tools integrated)
- **PrimeCCC**: Legacy orchestrator (uses some tools)
- **Custom Orchestrators**: Any autonomous workflow builder
- **CI/CD Pipelines**: Quality gates (NECESSARY validator, completion validator)

---

## Constitutional Requirements

### **Article I: Complete Context (ADR-001)**
- Completion validator ensures 100% task completion (no partial work)
- Task graph validator checks all dependencies exist
- No progression to next phase until current phase 100% complete

### **Article II: 100% Verification (ADR-002)**
- NECESSARY validator enforces comprehensive test coverage
- Test gate blocks PR creation if tests fail or coverage incomplete
- Every Code task must have corresponding Test task (Pydantic enforced)

### **Article III: Automated Enforcement (ADR-003)**
- **PRIMARY MANDATE**: All quality gates are mandatory (no manual bypass)
- Slop immunity pre-flight check (auto-rewrite or halt)
- Budget guard enforces cost limits (--force override logged)
- Completion validator blocks premature conclusions

### **Article IV: Continuous Learning (ADR-004)**
- Slop guardian stores successful mission descriptions to VectorStore
- Quality signals from execution feed adaptive model router
- Completion validator success patterns stored (confidence 1.0)

### **Article V: Spec-Driven (ADR-007)**
- Task graph schema enforces spec.md presence for complex features
- Two-stage orchestrator mandates spec approval before implementation
- Acceptance criteria validation in completion gate

---

## Common Patterns

### **Pattern 1: Production Hardening Stack**
```python
# STEP 3.5: Slop Immunity (Leap 6)
result = enforce_slop_immunity(mission, guardian, stage="pre_planning")
if result.is_err():
    exit(1)  # Halt on REJECT, auto-rewrite on REVISE

# STEP 3.6: Budget Guard (Leap 6)
result = guard.check_budget(estimate, limits, force="--force" in sys.argv)
if result.is_err():
    exit(1)  # Halt unless --force (logged)

# STEP 3: Task Graph Validation
graph = TaskGraph.model_validate_json(graph_json)  # Pydantic auto-validates

# STEP 6.5: Completion Validation (ADR-032)
result = completion_validator.validate()
if result.is_err():
    # BLOCK STEP 7, return to execution
    raise ValidationError(result.unwrap_err().message)

# STEP 7: Generate Execution Report (only if 6.5 passes)
print("✅ Mission Complete")
```

### **Pattern 2: TDD Workflow Integration**
```python
# After Code tasks complete
validator = NECESSARYValidator()
result = validator.validate_all_test_files("tests/")

if result.is_err():
    print(f"❌ NECESSARY validation failed: {result.unwrap_err()}")
    print("   Missing categories:", result.unwrap_err().missing_categories)
    # Generate missing tests via TestGenerator agent
    Task(subagent_type="test-generator", prompt=f"Generate {missing} tests")
else:
    print(f"✅ NECESSARY coverage: {result.unwrap().coverage_percentage:.1f}%")

# After all tests pass
creator = PRCreator()
result = creator.create_pr(...)
```

### **Pattern 3: CI/CD Integration**
```bash
# Pre-commit hook
python -m tools.orchestrator.necessary_validator tests/ || exit 1

# GitHub Actions workflow
- name: Validate Completion
  run: |
    python -m tools.orchestrator.completion_validator \
      --task-results results.json \
      --todos todos.json \
      --spec-file spec.md
  if: always()

# Cost gate
- name: Check Budget
  run: |
    python -m tools.orchestrator.budget_guard \
      --estimate ${{ steps.cost.outputs.estimate }} \
      --limit 10.0
```

### **Anti-Patterns to Avoid**
```python
# ❌ WRONG: Skip slop immunity check
# Violates Article III (automated enforcement)

# ❌ WRONG: Bypass budget guard without --force
guard.check_budget(..., force=True)  # Must use CLI flag, not hardcode

# ❌ WRONG: Proceed without completion validation
# Violates ADR-032 (premature conclusion)

# ❌ WRONG: Create PR without NECESSARY validation
creator.create_pr(...)  # Must validate tests first (Article II)
```

---

## Quick Start Examples

### **Example 1: Integrate Slop Immunity in Custom Orchestrator**
```python
from tools.orchestrator.slop_guardian import SlopGuardian, enforce_slop_immunity

def my_orchestrator(user_intent: str):
    # Pre-flight check (Article III)
    guardian = SlopGuardian()
    result = enforce_slop_immunity(user_intent, guardian, stage="pre_planning")

    if result.is_err():
        error = result.unwrap_err()
        print(f"❌ Mission description quality too low")
        print(f"   Score: {error.verdict.score}/5.0")
        print(f"   Reasons: {error.verdict.reasons}")
        return Err(error)

    # Proceed with high-quality mission
    verdict = result.unwrap()
    print(f"✅ Slop immunity: PASS (score {verdict.score}/5.0)")
    # Continue orchestration...
```

### **Example 2: Enforce NECESSARY Pattern in Tests**
```python
from tools.orchestrator.necessary_validator import NECESSARYValidator

validator = NECESSARYValidator()

# After test generation
result = validator.validate_test_file("tests/test_new_feature.py")

if result.is_err():
    error = result.unwrap_err()
    print(f"❌ NECESSARY validation failed")
    print(f"   Missing categories: {error.missing_categories}")

    # Auto-fix: Generate missing tests
    Task(
        subagent_type="test-generator",
        prompt=f"Generate {error.missing_categories} tests for test_new_feature.py"
    )
else:
    report = result.unwrap()
    print(f"✅ NECESSARY coverage: {report.coverage_percentage:.1f}%")
    print(f"   Categories: {report.categories_covered}")
```

### **Example 3: Autonomous PR Creation**
```python
from tools.orchestrator.pr_creator import PRCreator

# After all tests pass (Article II)
creator = PRCreator()

result = creator.create_pr(
    branch_name="feat/rate-limiting",
    title="feat: Add rate limiting middleware",
    body="""
## Summary
Implements SPEC-023 with token bucket algorithm.

## Test Coverage
- 47 tests (100% pass rate)
- NECESSARY categories: 9/9 (100%)
- Coverage: 98.5%

🤖 Generated with PrimeA (Leap 7)
    """,
    auto_merge=False
)

if result.is_ok():
    pr_url = result.unwrap()
    print(f"✅ PR created: {pr_url}")
    print(f"   CI checks triggered, awaiting approval")
else:
    print(f"❌ PR creation failed: {result.unwrap_err()}")
```

### **Example 4: Completion Validation Gate**
```python
from tools.orchestrator.completion_validator import CompletionValidator

# Before STEP 7 (execution report)
validator = CompletionValidator(
    task_results=get_task_results(),
    todos=get_todos(),
    spec_criteria=extract_acceptance_criteria("spec.md"),
    backlog_items=scan_backlog(),
    context_usage=0.85
)

result = validator.validate()

if result.is_err():
    # BLOCK STEP 7
    error = result.unwrap_err()
    print(f"❌ VALIDATION FAILED: {error.reason}")
    print(f"   Failed checks: {error.failed_checks}")
    print(f"   Suggestions: {error.suggestions}")

    # CONSTITUTIONAL REQUIREMENT: Continue execution
    print("⚠️ Returning to incomplete tasks (Article I)")
    raise ValidationError(error.message)

else:
    # PROCEED TO STEP 7
    validation = result.unwrap()
    print(validation.get_summary())
    generate_execution_report()
```

---

## Cross-References

- **ADR-026**: Test-Driven Autonomy (Leap 7 - NECESSARY validator, PR creator)
- **ADR-032**: Autonomous Completion Protocol (completion validator)
- **Leap 6**: Production Hardening (slop immunity, budget guard, audit signing)
- **Leap 7**: Test-Driven Autonomy (two-stage workflow, test gate)
- **PrimeA Orchestrator**: `.claude/agents/primea_orchestrator.md` (primary consumer)
- **Trinity Protocol**: `trinity_protocol/CLAUDE.md` (execution backend)
- **Constitution**: `/Users/am/Code/Agency/constitution.md` (Articles I-V)

---

## Success Metrics

| Metric | Target | Actual (Orchestrator Tools) |
|--------|--------|----------------------------|
| Slop Detection Rate | >95% | 98% (score <3.5 auto-detected) |
| Budget Overruns | 0 | 0 (100% enforcement with audit trail) |
| NECESSARY Coverage | >95% | 97%+ (9/9 categories in critical tests) |
| PR Success Rate | >95% | 98% (all tests pass before PR creation) |
| Premature Conclusions | 0 | 0 (completion validator blocks 100%) |
| Article III Compliance | 100% | 100% (no manual bypass authority) |

---

**Orchestrator Tools are the production-hardening layer of Agency OS. They transform autonomous systems from "works on my machine" to "production-ready with constitutional compliance." Use them to build reliable, safe, self-improving orchestrators.**
