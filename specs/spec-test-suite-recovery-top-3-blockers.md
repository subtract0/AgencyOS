# Specification: Test Suite Recovery - Top 3 Critical Blockers

**Spec ID**: `spec-test-suite-recovery-top-3-blockers`
**Status**: `Draft`
**Author**: PrimeA Orchestrator (Two-Stage Workflow)
**Created**: 2025-10-15
**Priority**: P1 - CRITICAL
**Related Analysis**: `test_suite_health_analysis.md`, `test_suite_fix_plan.md`

---

## Executive Summary

**Problem**: 133 test failures across test suite, with 56 failures (42%) concentrated in 3 critical blockers that share a common root cause: TDD pattern enforcement via Pydantic validation.

**Solution**: Fix top 3 critical blockers in targeted order to unblock 56 tests (42% of all failures) through systematic fixture rewriting, test enablement, and Pydantic model alignment.

**Impact**:
- **Immediate**: 56 failures → 0 (42% resolution)
- **Cascading**: Unblocks orchestrator core, Leap 7 validation, E2E workflows
- **Foundation**: Establishes correct TDD pattern for future test development

---

## Goals

### Primary Goals

1. **Fix TaskGraph TDD Validation** (24 failures → 0)
   - Rewrite test fixtures to follow Article II TDD pattern (Test BEFORE Code)
   - Update 6 core fixtures in `tests/orchestrator/test_unified_primea_orchestrator.py`
   - Verify TaskGraph Pydantic validation passes

2. **Enable Two-Stage Orchestrator Tests** (13 failures → 0)
   - Rename `test_two_stage_orchestrator.py.skip` → `test_two_stage_orchestrator.py`
   - Update imports to use real implementation (1094 lines already complete)
   - Validate integration with actual TwoStageOrchestrator

3. **Fix Pydantic Validation Errors** (19 failures → 0)
   - Add required `agent` and `description` fields to Task fixtures
   - Add `session_id` field to SkillVector fixtures
   - Remove deprecated `agent_name` parameter from `create_agent_context()` calls

### Success Metrics

- **Test Pass Rate**: 5,796 → 5,852 passing (97.8% → 98.7%)
- **Critical Blocker Resolution**: 56 failures → 0 (100% of targeted failures)
- **No Regressions**: All currently passing tests remain passing
- **Constitutional Compliance**: All fixes validate against Articles I-V
- **Execution Time**: 6-8 hours total (3 points + 2 points + 1 point)

---

## Non-Goals

- Fixing remaining 77 failures (HIGH/MEDIUM/LOW priority) - deferred to Phase 2
- Implementing missing functions (e.g., CI Monitor CLI) - separate mission
- Training ML Classifier models - separate mission
- Ollama infrastructure fixes - separate mission

---

## Background & Context

### Root Cause Analysis

All 3 blockers stem from **TDD constitutional enforcement** (Article II) added via Pydantic validators:

**Article II Requirement**:
> Every Code task MUST have a Test task dependency. Test task must come BEFORE Code task in dependencies (RED-GREEN-REFACTOR). Test task must have `verification_target` pointing to Code task.

**Problem**: Tests written BEFORE Article II strict enforcement became mandatory now violate the validators they're meant to test.

**Evidence from Analysis**:
```python
# CURRENT PATTERN (VIOLATES ARTICLE II)
code_task = Task(id="code_task", type=TaskType.CODE, dependencies=[])
test_task = Task(id="test_task", type=TaskType.TEST, dependencies=["code_task"])
# ❌ Code comes BEFORE Test - violates TDD

# REQUIRED PATTERN (ARTICLE II COMPLIANT)
test_task = Task(id="test_code_task", type=TaskType.TEST, dependencies=[], verification_target="code_task")
code_task = Task(id="code_task", type=TaskType.CODE, dependencies=["test_code_task"])
# ✅ Test comes BEFORE Code - follows TDD
```

### Cascading Impact

**Fix #1 (TaskGraph)** unblocks:
- 24 orchestrator core tests
- Foundation for Fix #2 (two-stage tests likely depend on valid TaskGraph)

**Fix #2 (Two-Stage)** enables:
- 13 Leap 7 validation tests
- TDD workflow end-to-end verification

**Fix #3 (Pydantic Fixtures)** unblocks:
- 19 E2E workflow tests
- Integration validation across codebase

**Total Cascade**: 56 tests unblocked → enables Phase 2 fixes (remaining 77 failures)

---

## Acceptance Criteria

### AC-1: TaskGraph TDD Validation (Fix #1)

**Given** test fixtures in `tests/orchestrator/test_unified_primea_orchestrator.py`
**When** tests are executed with `pytest tests/orchestrator/test_unified_primea_orchestrator.py -v`
**Then**:
- ✅ All 24 previously failing tests now pass
- ✅ No Pydantic ValidationError for "missing Test dependency"
- ✅ Test fixtures follow pattern: `test_task` dependency → `code_task`
- ✅ All Test tasks have `verification_target` field set

**Fixtures to Update**:
1. `simple_task_graph` (lines 86-120) - 2 tasks (test → code)
2. `circular_task_graph` (used in DAG validation tests)
3. `_create_foundation_graph()` method - 7 foundation tasks
4. `_create_stub_graph()` method - minimal graph for error cases
5. Phase-specific graph builders (if any)

**Verification**:
```bash
# All tests pass
pytest tests/orchestrator/test_unified_primea_orchestrator.py::test_step_3_1_dag_validation_pass -v
pytest tests/orchestrator/test_unified_primea_orchestrator.py -v
# Expected: 24/24 tests pass (was 0/24)
```

---

### AC-2: Two-Stage Orchestrator Tests Enabled (Fix #2)

**Given** implementation file `tools/orchestrator/two_stage_orchestrator.py` (1094 lines complete)
**When** tests are executed with `pytest tests/orchestrator/test_two_stage_orchestrator.py -v`
**Then**:
- ✅ All 13 tests execute (no longer skipped)
- ✅ Tests import real `TwoStageOrchestrator` class (not TDD placeholder)
- ✅ Integration with actual implementation validates correctly
- ✅ Any revealed issues from integration are fixed

**Changes Required**:
1. Rename file: `mv tests/orchestrator/test_two_stage_orchestrator.py.skip tests/orchestrator/test_two_stage_orchestrator.py`
2. Update imports:
   ```python
   # OLD (TDD placeholder)
   class TwoStageOrchestrator:
       async def orchestrate(...) -> Result[PRUrl, str]:
           raise NotImplementedError("TDD: Implement after tests pass")

   # NEW (real implementation)
   from tools.orchestrator.two_stage_orchestrator import TwoStageOrchestrator
   ```
3. Fix any integration issues revealed by tests (likely TaskGraph validation from Fix #1)

**Verification**:
```bash
# All tests pass
pytest tests/orchestrator/test_two_stage_orchestrator.py::test_orchestrate_when_full_workflow_succeeds_then_returns_pr_url -v
pytest tests/orchestrator/test_two_stage_orchestrator.py -v
# Expected: 13/13 tests pass (was 0/13 skipped)
```

---

### AC-3: Pydantic Validation Errors Fixed (Fix #3)

**Given** test fixtures in multiple test files with Pydantic validation errors
**When** tests are executed with affected test files
**Then**:
- ✅ All 19 tests pass (no Pydantic ValidationError)
- ✅ Task fixtures include required `agent` and `description` fields
- ✅ SkillVector fixtures include required `session_id` field
- ✅ No calls to `create_agent_context(agent_name=...)` (deprecated parameter removed)

**Files to Update**:
1. `tests/conftest.py` - Update Task fixture factory
2. `tests/foundation_automation/test_e2e_natural_language_flow.py` - 5 tests with Task validation errors
3. `tests/test_leap3_e2e_integration.py` - 14 tests with SkillVector/AgentContext errors

**Required Changes**:

**Task Fixtures** (add required fields):
```python
# BEFORE (missing required fields)
Task(
    id="task_1",
    title="Implement feature",
    type=TaskType.CODE,
    tier=TaskTier.TIER_2,
    dependencies=[]
)

# AFTER (all required fields)
Task(
    id="task_1",
    title="Implement feature",
    agent="coder",              # REQUIRED: Added
    description="Implement feature with tests",  # REQUIRED: Added
    type=TaskType.CODE,
    tier=TaskTier.TIER_2,
    dependencies=[]
)
```

**SkillVector Fixtures** (add session_id):
```python
# BEFORE (missing session_id)
SkillVector(agent_name="coder", ...)

# AFTER (session_id required)
SkillVector(session_id="test_session", ...)
```

**AgentContext Calls** (remove agent_name):
```python
# BEFORE (agent_name deprecated)
context = create_agent_context(agent_name="coder", session_id="test")

# AFTER (agent_name removed from API)
context = create_agent_context(session_id="test")
```

**Verification**:
```bash
# E2E tests pass
pytest tests/foundation_automation/test_e2e_natural_language_flow.py::test_e2e_minimal_graph_edge -v
pytest tests/foundation_automation/test_e2e_natural_language_flow.py -v
# Expected: 5/5 Pydantic error tests now pass

# Leap 3 tests pass
pytest tests/test_leap3_e2e_integration.py -v
# Expected: 14/14 setup error tests now pass
```

---

## Technical Implementation Details

### Fix #1: TaskGraph TDD Validation (3 points, 4-6 hours)

**Step 1: Identify All Fixtures** (30 min)
```bash
# Find all fixtures creating TaskGraph objects
rg "simple_task_graph|circular_task_graph|_create.*graph" tests/orchestrator/test_unified_primea_orchestrator.py
```

**Step 2: Rewrite Fixture Pattern** (2 hours)

**Template for TDD-Compliant TaskGraph**:
```python
@pytest.fixture
def simple_task_graph():
    """TDD-compliant task graph: Test BEFORE Code (Article II)."""

    # STEP 1: Create Test task FIRST (no dependencies)
    test_task = Task(
        id="test_code_task",
        title="Test code functionality",
        agent="test_generator",
        description="Write tests for code task following NECESSARY pattern",
        type=TaskType.TEST,
        tier=TaskTier.TIER_2,
        dependencies=[],  # Test has no dependencies (RED phase)
        verification_target="code_task",  # Points to future Code task
        acceptance_criteria=[
            "Test covers normal operation",
            "Test covers edge cases",
            "Test follows AAA pattern"
        ]
    )

    # STEP 2: Create Code task SECOND (depends on Test)
    code_task = Task(
        id="code_task",
        title="Implement functionality",
        agent="coder",
        description="Implement feature after tests are written",
        type=TaskType.CODE,
        tier=TaskTier.TIER_2,
        dependencies=["test_code_task"],  # Code depends on Test (TDD)
        acceptance_criteria=[
            "All tests pass",
            "Code follows Result<T,E> pattern",
            "Type hints complete"
        ]
    )

    # STEP 3: Create TaskGraph with TDD ordering
    return TaskGraph(
        mission="Simple task graph for testing",
        phases=[
            Phase(
                id="phase_1",
                title="Implementation Phase",
                tasks=[test_task, code_task]  # Test → Code ordering
            )
        ]
    )
```

**Step 3: Update All 6 Fixtures** (2 hours)
- `simple_task_graph`
- `circular_task_graph` (if used in cycle detection - ensure valid DAG)
- `_create_foundation_graph()` - apply pattern to 7 foundation tasks
- `_create_stub_graph()` - minimal 2-task graph (test → code)
- Any phase-specific builders

**Step 4: Run Tests** (30 min)
```bash
# Incremental validation
pytest tests/orchestrator/test_unified_primea_orchestrator.py::test_step_3_1_dag_validation_pass -xvs
pytest tests/orchestrator/test_unified_primea_orchestrator.py::test_create_foundation_graph_dependencies -xvs

# Full suite
pytest tests/orchestrator/test_unified_primea_orchestrator.py -v --tb=short
```

**Step 5: Fix Revealed Issues** (1 hour)
- Adjust test assertions if they expect old pattern
- Update documentation in test docstrings
- Ensure constitutional compliance notes are clear

---

### Fix #2: Enable Two-Stage Orchestrator Tests (2 points, 2-4 hours)

**Step 1: Rename File** (5 min)
```bash
cd tests/orchestrator
mv test_two_stage_orchestrator.py.skip test_two_stage_orchestrator.py
```

**Step 2: Update Imports** (15 min)

**Find TDD Placeholder**:
```python
# SEARCH FOR THIS PATTERN
class TwoStageOrchestrator:
    """TDD PLACEHOLDER: This class will be implemented AFTER tests pass."""

    async def orchestrate(...) -> Result[PRUrl, str]:
        raise NotImplementedError("TDD: Implement after tests pass")
```

**Replace With Real Import**:
```python
from tools.orchestrator.two_stage_orchestrator import TwoStageOrchestrator
```

**Step 3: Run Tests** (30 min)
```bash
# Incremental
pytest tests/orchestrator/test_two_stage_orchestrator.py::test_orchestrate_when_full_workflow_succeeds_then_returns_pr_url -xvs

# Full suite
pytest tests/orchestrator/test_two_stage_orchestrator.py -v --tb=short
```

**Step 4: Fix Integration Issues** (1-2 hours)

**Likely Issue #1**: TaskGraph validation errors (depends on Fix #1 completing first)
**Solution**: Ensure test fixtures follow TDD pattern from Fix #1

**Likely Issue #2**: Mock expectations vs actual implementation signature
**Solution**: Update mocks to match real `TwoStageOrchestrator.orchestrate()` signature

**Likely Issue #3**: Async/await mismatches
**Solution**: Ensure test functions are marked `async def` and use `await` correctly

---

### Fix #3: Fix Pydantic Validation Errors (1 point, 2 hours)

**Step 1: Update Task Fixture Factory** (30 min)

**Location**: `tests/conftest.py`

**Before**:
```python
def task_factory(**overrides):
    defaults = {
        "id": "test_task",
        "title": "Test task",
        "type": TaskType.CODE,
        "tier": TaskTier.TIER_2,
        "dependencies": []
    }
    return Task(**{**defaults, **overrides})
```

**After** (add required fields):
```python
def task_factory(**overrides):
    defaults = {
        "id": "test_task",
        "title": "Test task",
        "agent": "coder",  # REQUIRED: Added default
        "description": "Test task description",  # REQUIRED: Added default
        "type": TaskType.CODE,
        "tier": TaskTier.TIER_2,
        "dependencies": []
    }
    return Task(**{**defaults, **overrides})
```

**Step 2: Update E2E Test Fixtures** (30 min)

**Location**: `tests/foundation_automation/test_e2e_natural_language_flow.py`

**Find All Task Creation Calls**:
```bash
rg "Task\(" tests/foundation_automation/test_e2e_natural_language_flow.py | head -20
```

**Apply Pattern**:
```python
# For each Task creation, add agent and description
Task(
    id="...",
    title="...",
    agent="coder",  # or "test_generator", "planner", etc.
    description="Full description of what this task does",
    type=TaskType.CODE,
    ...
)
```

**Step 3: Update Leap 3 Fixtures** (30 min)

**Location**: `tests/test_leap3_e2e_integration.py`

**Issue #1**: SkillVector requires `session_id`
```python
# BEFORE
skill = SkillVector(agent_name="coder", proficiency=0.8)

# AFTER
skill = SkillVector(session_id="test_session", proficiency=0.8)
```

**Issue #2**: `create_agent_context()` no longer accepts `agent_name`
```python
# BEFORE
context = create_agent_context(agent_name="coder", session_id="test_id")

# AFTER
context = create_agent_context(session_id="test_id")
# Note: agent_name removed from API signature
```

**Step 4: Run Tests** (30 min)
```bash
# E2E tests
pytest tests/foundation_automation/test_e2e_natural_language_flow.py -k "minimal_graph or high_parallelism or parallel_task" -xvs
pytest tests/foundation_automation/test_e2e_natural_language_flow.py -v

# Leap 3 tests
pytest tests/test_leap3_e2e_integration.py -v --tb=short
```

---

## Constitutional Compliance

### Article I: Complete Context Before Action
- ✅ All 56 test failures analyzed with root cause identified
- ✅ Retry logic: Tests re-run after each fix to validate completion
- ✅ No partial fixes: Each blocker resolved to 100% before moving to next

### Article II: 100% Verification and Stability
- ✅ Fix #1: 24/24 tests must pass (not 20/24)
- ✅ Fix #2: 13/13 tests must pass (not 10/13)
- ✅ Fix #3: 19/19 tests must pass (not 15/19)
- ✅ Zero regressions: All currently passing tests remain passing

### Article III: Automated Merge Enforcement
- ✅ TaskGraph Pydantic validators enforce TDD pattern automatically
- ✅ No manual override mechanism for validation
- ✅ Quality gates absolute: Tests must pass before PR merge

### Article IV: Continuous Learning and Improvement
- ✅ Store successful TDD fixture patterns to VectorStore (confidence ≥0.6)
- ✅ Query VectorStore for similar past fixes before implementing
- ✅ Extract learnings: "Always write Test BEFORE Code in fixtures" (confidence 1.0)

### Article V: Spec-Driven Development
- ✅ This specification defines acceptance criteria for all 3 fixes
- ✅ Implementation traces back to AC-1, AC-2, AC-3
- ✅ Test plan validates spec requirements

---

## Test Plan (NECESSARY Pattern)

### Normal Operation Tests

**N-1: TaskGraph TDD Validation - Simple Graph**
```python
def test_simple_task_graph_tdd_compliant():
    """Normal: Simple graph with 1 test → 1 code task validates."""
    graph = simple_task_graph()  # Uses updated fixture
    assert graph.validate().is_ok()
    tasks = graph.all_tasks()
    assert len(tasks) == 2
    assert tasks[0].type == TaskType.TEST
    assert tasks[1].type == TaskType.CODE
    assert tasks[1].id in tasks[0].dependencies  # Code depends on Test
```

**N-2: Two-Stage Orchestrator - Happy Path**
```python
async def test_two_stage_orchestrator_full_workflow():
    """Normal: Full two-stage workflow (spec → approval → execution) succeeds."""
    orchestrator = TwoStageOrchestrator()  # Real implementation
    result = await orchestrator.orchestrate(
        intent="Build simple feature",
        visualize=False,
        auto_pr=False
    )
    assert result.is_ok()
    pr_url = result.unwrap()
    assert pr_url.startswith("https://github.com/")
```

**N-3: Pydantic Fixtures - Task Creation**
```python
def test_task_fixture_with_all_required_fields():
    """Normal: Task created with agent and description validates."""
    task = Task(
        id="test_task",
        title="Test",
        agent="coder",
        description="Full description",
        type=TaskType.CODE,
        tier=TaskTier.TIER_2,
        dependencies=[]
    )
    assert task.agent == "coder"
    assert task.description == "Full description"
```

### Edge Case Tests

**E-1: TaskGraph - Circular Dependencies Still Rejected**
```python
def test_circular_dependencies_rejected():
    """Edge: Circular dependencies still caught even with TDD pattern."""
    # Create valid TDD tasks but with cycle
    test_a = Task(id="test_a", type=TaskType.TEST, dependencies=["test_b"], ...)
    test_b = Task(id="test_b", type=TaskType.TEST, dependencies=["test_a"], ...)

    with pytest.raises(ValidationError, match="circular"):
        TaskGraph(phases=[Phase(id="p1", tasks=[test_a, test_b])])
```

**E-2: Two-Stage - Spec Rejection Handled**
```python
async def test_two_stage_spec_rejected_retry():
    """Edge: User rejects spec, orchestrator regenerates and retries."""
    orchestrator = TwoStageOrchestrator()
    # Mock user rejection on first attempt
    result = await orchestrator.orchestrate(intent="...", spec_approval=False)
    # Verify regeneration triggered
    assert result.is_ok() or "retry" in str(result.unwrap_err())
```

**E-3: Pydantic - Missing Fields Caught**
```python
def test_task_missing_agent_field_raises():
    """Edge: Missing 'agent' field raises Pydantic ValidationError."""
    with pytest.raises(ValidationError, match="agent"):
        Task(
            id="task",
            title="Test",
            # agent missing
            description="Desc",
            type=TaskType.CODE,
            tier=TaskTier.TIER_2,
            dependencies=[]
        )
```

### Security Tests

**S-1: TaskGraph - Injection Prevention**
```python
def test_task_graph_injection_attempt_sanitized():
    """Security: Malicious task IDs sanitized in dependencies."""
    malicious_task = Task(
        id="task; rm -rf /",
        agent="coder",
        description="Test",
        type=TaskType.CODE,
        tier=TaskTier.TIER_2,
        dependencies=[]
    )
    # Verify ID sanitization or rejection
    assert "rm -rf" not in malicious_task.id
```

**S-2: Two-Stage - Untrusted Intent Validated**
```python
async def test_two_stage_sql_injection_rejected():
    """Security: SQL injection in intent rejected by slop guardian."""
    orchestrator = TwoStageOrchestrator()
    result = await orchestrator.orchestrate(
        intent="'; DROP TABLE users; --",
        visualize=False,
        auto_pr=False
    )
    assert result.is_err()  # Slop guardian should reject
```

### Stress Tests

**ST-1: TaskGraph - Large Graph Performance**
```python
def test_large_task_graph_validates_quickly():
    """Stress: 100-task graph validates in <1 second."""
    import time
    tasks = [create_task(i) for i in range(100)]
    start = time.time()
    graph = TaskGraph(phases=[Phase(id="p1", tasks=tasks)])
    elapsed = time.time() - start
    assert elapsed < 1.0
```

---

## Estimated Effort & Timeline

### Total Effort: 6 story points (~8 hours)

| Fix | Effort | Timeline | Dependencies |
|-----|--------|----------|--------------|
| Fix #1: TaskGraph TDD Validation | 3 points | 4-6 hours | None |
| Fix #2: Two-Stage Tests | 2 points | 2-4 hours | Fix #1 (likely) |
| Fix #3: Pydantic Fixtures | 1 point | 2 hours | None (can parallelize) |

### Execution Plan

**Hour 1-2**: Fix #1 - Rewrite core fixtures (simple_task_graph, circular_task_graph)
**Hour 3-4**: Fix #1 - Update foundation graph builders, run tests
**Hour 5**: Fix #1 - Fix revealed issues, achieve 24/24 pass rate

**Hour 6**: Fix #2 - Rename file, update imports, run tests
**Hour 7**: Fix #2 - Fix integration issues, achieve 13/13 pass rate

**Hour 8**: Fix #3 - Update all Pydantic fixtures, run tests, achieve 19/19 pass rate

---

## Risks & Mitigation

### Risk #1: Cascading Test Failures
**Description**: Fixing TaskGraph validation may reveal new failures in other tests
**Likelihood**: Medium
**Impact**: HIGH
**Mitigation**:
- Run full test suite after each fix (`pytest tests/ -v`)
- Use `--tb=short` to identify new failures quickly
- Add new failures to backlog for Phase 2

### Risk #2: Two-Stage Integration Issues
**Description**: Real TwoStageOrchestrator may have different signature than test expectations
**Likelihood**: Medium
**Impact**: MEDIUM
**Mitigation**:
- Read implementation before updating imports
- Verify method signatures match test mocks
- Run incremental tests (one test at a time) to isolate issues

### Risk #3: Time Overrun
**Description**: Fixes take longer than 8-hour estimate
**Likelihood**: Low
**Impact**: LOW
**Mitigation**:
- Timebox each fix (no more than 6 hours for Fix #1)
- If blocked, move to next fix and return later
- Prioritize Fix #1 (highest impact: 24 tests)

---

## Success Validation

### Final Validation Commands

```bash
# 1. Run all affected tests
pytest tests/orchestrator/test_unified_primea_orchestrator.py -v
pytest tests/orchestrator/test_two_stage_orchestrator.py -v
pytest tests/foundation_automation/test_e2e_natural_language_flow.py -v
pytest tests/test_leap3_e2e_integration.py -v

# Expected: 56/56 tests pass (0 failures)

# 2. Run full test suite (verify no regressions)
python run_tests.py --run-all

# Expected: Pass rate increases from 97.8% to 98.7%
# Expected: 5,796 → 5,852 passing tests

# 3. Verify constitutional compliance
pytest tests/ -v -m "not integration" | grep -E "(PASSED|FAILED|ERROR)" | tail -20

# Expected: No new failures, all constitutional validators passing
```

### Definition of Done

- [ ] AC-1: 24/24 TaskGraph TDD validation tests pass
- [ ] AC-2: 13/13 two-stage orchestrator tests pass
- [ ] AC-3: 19/19 Pydantic validation tests pass
- [ ] Zero regressions: All currently passing tests still pass
- [ ] Full test suite: Pass rate ≥98.7% (5,852/5,929 passing)
- [ ] Constitutional compliance: Articles I-V validated
- [ ] Code review: Changes reviewed for quality
- [ ] Documentation: Test patterns documented for future reference
- [ ] VectorStore: Successful patterns stored (confidence ≥0.6)

---

## Next Steps (Post-Mission)

After completing these 3 fixes (56 failures → 0):

1. **Phase 2**: Fix remaining 77 failures (HIGH/MEDIUM/LOW priority)
   - CI Monitor CLI implementation (11 failures)
   - ML Classifier training (19 failures)
   - Constitutional gates (6 failures)
   - Input validation (3 failures)
   - Ollama infrastructure (4 failures)
   - Miscellaneous (34 failures)

2. **Extract Learnings**: Store TDD fixture patterns to VectorStore
   - Pattern: "Test BEFORE Code in fixtures" (confidence 1.0)
   - Pattern: "Pydantic validators enforce constitutional compliance" (confidence 0.9)
   - Pattern: "Enable tests immediately after implementation complete" (confidence 0.8)

3. **Update Documentation**:
   - `TESTING_GUIDE.md`: Add TDD fixture pattern section
   - `CLAUDE.md`: Update test suite status (133 → 77 failures)
   - `test_suite_health_analysis.md`: Mark top 3 blockers as resolved

4. **Propose Next Mission**: Generate Leap 10 proposal based on remaining gaps

---

**Specification Version**: 1.0
**Ready for Execution**: YES
**Estimated Duration**: 6-8 hours (1 developer)
