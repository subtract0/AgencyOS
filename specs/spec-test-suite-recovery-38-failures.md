# Specification: Test Suite Recovery - 38 Remaining Failures

**Mission**: Complete test suite recovery by fixing the final 38 test failures across three categories.

**Version**: 1.0.0
**Status**: Approved (Two-Stage Workflow)
**Created**: 2025-10-15
**Leap**: 7 (Test-Driven Autonomy)

---

## Executive Summary

This specification addresses the final 38 test failures preventing 100% test pass rate (Article II constitutional requirement). The failures fall into three distinct categories, each requiring different fix strategies.

**CRITICAL ARCHITECTURAL INSIGHT** (User Feedback):
**The test suite itself may be defective, not the production code.** This specification takes a higher-level architectural view:
1. **Verify production code correctness FIRST** (does the orchestrator actually work?)
2. **Identify test suite defects** (are tests testing the wrong interface?)
3. **Fix the broken component** (production OR tests, not assumed)
4. **Strategic agent orchestration** (Auditor → Architect → Specialized fixers)

**Approach**: German engineering precision - measure twice, cut once. No assumptions.

**Current State**:
- 1,724 tests passing (97.8%)
- 38 tests failing (2.2%)
- Zero broken windows tolerance violated
- **Unknown**: Are tests correct? Is production code correct? Both defective?

**Target State**:
- 1,762 tests passing (100%)
- Zero failures
- Constitutional compliance restored
- **Root cause identified** (production bug vs test suite defect vs both)

---

## Goals

1. **Fix Two-Stage Orchestrator Signature Mismatches** (14 tests)
   - Update test signatures to match real API: `orchestrate(input_value=...)`
   - Remove obsolete parameters: `user_input`, `input_mode`
   - Maintain test coverage while aligning with implementation

2. **Fix Mocked TaskGraph Tests** (6 tests)
   - Identify tests using mocked TaskGraph instead of real implementation
   - Replace mocks with real TaskGraph Pydantic models
   - Ensure validation logic is tested against actual schema

3. **Fix E2E Pydantic Validation Errors** (18 tests)
   - Resolve `extra fields not permitted` errors in test fixtures
   - Align fixture data with strict Pydantic models
   - Ensure constitutional pattern compliance (Result<T,E>, typed models)

---

## Personas

### Primary Stakeholder: QualityEnforcerAgent
- **Needs**: 100% test pass rate for constitutional compliance (Article II)
- **Pain Point**: Cannot enforce Article II with 38 failing tests
- **Success Metric**: Zero test failures, all constitutional checks green

### Secondary Stakeholder: PrimeA Orchestrator
- **Needs**: Reliable test suite for autonomous execution
- **Pain Point**: Cannot create PRs with failing tests (test gate blocks)
- **Success Metric**: All PRs pass CI checks on first attempt

### Tertiary Stakeholder: Development Team
- **Needs**: Fast, reliable test suite for TDD workflow
- **Pain Point**: Broken windows create confusion, reduce confidence
- **Success Metric**: <2 minute test runs, 100% pass rate

---

## Success Criteria (Acceptance Criteria)

### Criterion 1: Two-Stage Orchestrator Tests (14/14 passing)
- ✅ All 14 tests in `test_two_stage_orchestrator.py` pass
- ✅ Test signatures match actual API: `orchestrate(input_value=str|None)`
- ✅ No `user_input` or `input_mode` parameters in test calls
- ✅ Backward compatibility maintained (existing behavior unchanged)

**Verification**:
```bash
python -m pytest tests/orchestrator/test_two_stage_orchestrator.py -v
# Expected: 14/14 passed
```

### Criterion 2: TaskGraph Tests (6/6 passing)
- ✅ All 6 mocked TaskGraph tests replaced with real models
- ✅ Pydantic validation tested (e.g., circular dependency detection)
- ✅ Test coverage maintained or improved
- ✅ No test mocks for core domain models

**Verification**:
```bash
# Find tests with mocked TaskGraph
grep -r "MagicMock.*TaskGraph" tests/ --include="*.py"
# Expected: Zero matches

python -m pytest tests/ -k "task_graph" -v
# Expected: 100% pass rate
```

### Criterion 3: E2E Pydantic Validation (18/18 passing)
- ✅ All E2E test fixtures comply with strict Pydantic models
- ✅ No `extra fields not permitted` errors
- ✅ Fixtures match production data shapes (no test-only fields)
- ✅ Constitutional pattern compliance (Result<T,E>, typed dicts)

**Verification**:
```bash
python -m pytest tests/e2e/ -v --tb=short
# Expected: 18/18 passed, zero Pydantic validation errors
```

### Criterion 4: Full Test Suite (1,762/1,762 passing)
- ✅ Complete test run passes without failures
- ✅ Zero skipped tests (unless Ollama integration with --with-docker)
- ✅ Test execution time <3 minutes (unit tests only)
- ✅ Constitutional compliance verified

**Verification**:
```bash
python run_tests.py --run-all
# Expected: 1,762 passed in <180s
```

### Criterion 5: Constitutional Compliance
- ✅ Article I: Complete context (all 38 failures addressed, no partial fixes)
- ✅ Article II: 100% verification (zero broken windows)
- ✅ Article III: Automated enforcement (test gate works, no bypass)
- ✅ Article IV: Learnings stored (failure patterns extracted to VectorStore)
- ✅ Article V: Spec-driven (this specification drives all fixes)

---

## Test Plan (NECESSARY Pattern)

### Normal (N) - Happy Path Tests
- **N1**: Run full test suite after all fixes
- **N2**: Verify test execution time within acceptable range (<3 min)
- **N3**: Validate TodoWrite todos all marked "completed"

### Edge (E) - Boundary Conditions
- **E1**: Test orchestrator with `None` input (auto-select mode)
- **E2**: Test orchestrator with explicit string input
- **E3**: Verify Pydantic validation catches extra fields

### Cascading (C) - Integration Impact
- **C1**: Run E2E tests to verify no downstream breakage
- **C2**: Test TaskGraph topological sort with complex dependencies
- **C3**: Verify two-stage workflow end-to-end

### Essential (E) - Critical Functionality
- **E1**: Orchestrator must accept correct signature
- **E2**: TaskGraph validation must use real Pydantic models
- **E3**: E2E fixtures must match production schemas

### Security (S) - Threat Validation
- **S1**: Verify no test mocks bypass constitutional validation
- **S2**: Ensure Pydantic strict mode prevents injection
- **S3**: Validate test fixtures don't expose secrets

### Spec (S) - Requirements Traceability
- **S1**: All 38 failures traced to root cause
- **S2**: Each fix mapped to acceptance criterion
- **S3**: Spec criteria verified after implementation

### Accessibility (A) - Usability
- **A1**: Test error messages clear and actionable
- **A2**: Test suite output human-readable
- **A3**: TodoWrite updates visible to user

### Resilience (R) - Fault Tolerance
- **R1**: Test suite recovers from transient failures (retry logic)
- **R2**: Tests don't leak state between runs
- **R3**: Test failures don't block other tests

### Year-round (Y) - Long-term Stability
- **Y1**: No time-dependent test failures
- **Y2**: Tests remain valid after model signature changes
- **Y3**: Test coverage maintained during refactoring

---

## Technical Architecture

### Component 1: Two-Stage Orchestrator Test Signature Update

**Root Cause**:
- Implementation: `async def orchestrate(self, input_value: str | None = None)`
- Tests: `orchestrate(user_input=..., input_mode=...)`
- Result: `TypeError: got an unexpected keyword argument`

**Fix Strategy**:
1. Update all test calls to use `input_value` parameter
2. Remove `input_mode` logic (orchestrator auto-detects from `input_value`)
3. Preserve test intent (e.g., auto-select vs natural language)

**Files Affected**:
- `tests/orchestrator/test_two_stage_orchestrator.py` (14 tests)

**Complexity**: Low (mechanical signature update)

### Component 2: Mocked TaskGraph Replacement

**Root Cause**:
- Tests use `MagicMock(spec=TaskGraph)` instead of real Pydantic models
- Validation logic not tested (mocks bypass Pydantic validators)
- Risk: Tests pass but production code fails

**Fix Strategy**:
1. Search codebase for `MagicMock.*TaskGraph` patterns
2. Replace mocks with real TaskGraph Pydantic instances
3. Use factory functions for test data generation
4. Ensure Pydantic validation runs in tests

**Files Affected** (to be determined via grep):
- Likely: `tests/orchestrator/test_*.py`
- Possibly: `tests/foundation_automation/test_*.py`

**Complexity**: Medium (requires understanding TaskGraph schema)

### Component 3: E2E Pydantic Validation Fixes

**Root Cause**:
- Test fixtures include extra fields not in Pydantic models
- Strict mode (`extra = "forbid"`) rejects unknown fields
- Common culprits: `extra_data`, `test_only_field`, etc.

**Fix Strategy**:
1. Run E2E tests with `--tb=short` to identify extra fields
2. Remove extra fields from fixtures
3. Align fixtures with production models
4. Add `model_validate()` calls to verify compliance

**Files Affected** (to be determined via pytest):
- `tests/e2e/test_*.py` (18 tests failing)

**Complexity**: Medium (requires inspecting Pydantic model schemas)

---

## Dependencies

### Prerequisites
- ✅ Git status clean (pre-flight check complete)
- ✅ No orphaned processes (pre-flight check complete)
- ✅ Test collection works (pre-flight check complete)

### External Dependencies
- Python 3.11+
- pytest 8.0+
- Pydantic 2.0+ (strict mode)
- AgentContext (shared/agent_context.py)
- TaskGraph models (shared/models/task_graph.py)

### Internal Dependencies
- TwoStageOrchestrator (tools/orchestrator/two_stage_orchestrator.py)
- TaskGraph Pydantic models (shared/models/task_graph.py)
- E2E fixtures (tests/e2e/conftest.py or inline)

---

## Implementation Phases

### Phase 0: Comprehensive Test Suite Audit (Tier 1, Auditor + Chief Architect)
**Goal**: Thorough architectural audit - determine what needs revision (production, tests, or both)

**Strategic Principle**: "Trust nothing. Verify everything." (German engineering precision)

**Audit Dimensions**:

#### 1. API Contract Verification (Auditor Agent)
**Question**: Does production API match its documented contract?

**Tasks**:
- Read TwoStageOrchestrator implementation: `orchestrate(input_value: str | None = None)`
- Read spec-011-two-stage-orchestration.md: documented API contract
- Read ADR-027-tdd-first-graph-generation.md: architectural intent
- Cross-reference: implementation ↔ spec ↔ ADR
- **Output**: API Contract Compliance Report (PASS/FAIL with evidence)

#### 2. Test Suite Architecture Review (Auditor Agent)
**Question**: Are tests testing the right thing, the right way?

**Analysis Areas**:
a) **Test-Production Alignment**:
   - Are tests calling production API correctly? (signature match?)
   - Are tests using real models or mocks? (TaskGraph mocking patterns)
   - Do tests reflect current architecture or legacy API?

b) **Test Quality Patterns**:
   - NECESSARY pattern compliance (9/9 categories covered?)
   - AAA pattern (Arrange-Act-Assert) consistency
   - Test isolation (no shared state, no order dependencies?)
   - Mock hygiene (mocking IO, not business logic?)

c) **Fixture Data Integrity**:
   - Do E2E fixtures match production data shapes?
   - Pydantic strict mode compliance (no extra fields?)
   - Type safety (no `Any`, no `Dict[str, Any]`?)

**Output**: Test Suite Quality Report (score 0-10, identified defects)

#### 3. Historical Evolution Analysis (Chief Architect)
**Question**: How did we get here? Was this intentional or drift?

**Tasks**:
- `git log --oneline --all --grep="orchestrate"` (API changes over time)
- `git blame tools/orchestrator/two_stage_orchestrator.py` (who changed what, when)
- `git diff $(git merge-base HEAD main)..HEAD tests/orchestrator/` (what changed in tests)
- Review commit messages: intentional API change or accidental drift?

**Output**: Evolutionary Timeline (API changes → test changes, identify divergence point)

#### 4. Production Validation (Chief Architect)
**Question**: Does production code actually work? Has it ever worked?

**Evidence Collection**:
- Search git history for successful production usage (commits referencing "primeA --two-stage")
- Check logs/ directory for successful two-stage executions
- Review PR history: any PRs created by TwoStageOrchestrator?
- CI/CD pipeline: does two-stage workflow pass in CI?

**Output**: Production Validation Report (empirical evidence of working/broken)

#### 5. Root Cause Synthesis (Chief Architect)
**Question**: What needs fixing - production, tests, or both?

**Decision Matrix**:
```
Production Correct? | Tests Correct? | Action
--------------------|----------------|------------------
YES                 | YES            | Investigate CI/env
YES                 | NO             | Fix tests
NO                  | YES            | Fix production
NO                  | NO             | Fix both (strategic)
UNKNOWN             | UNKNOWN        | Deeper investigation
```

**Decision Criteria**:
1. **Spec alignment**: What does spec-011 say the API should be?
2. **ADR alignment**: What does ADR-027 mandate?
3. **Historical intent**: Was change intentional (documented) or drift?
4. **Production evidence**: Empirical proof of working/broken

**Deliverable**:
- Architectural Decision Document (what to fix, why, evidence)
- Revision Plan (specific changes needed, priority order)
- Risk Assessment (blast radius, rollback strategy)

**Estimated Tokens**: 15,000 (comprehensive audit, requires deep analysis)

### Phase 1: Diagnostic Analysis (Tier 2, Auditor)
**Goal**: Identify all 38 failing tests and categorize by root cause (AFTER Phase 0)

**Tasks**:
1. Run targeted test suites to confirm failure counts
2. Extract error messages and stack traces
3. Categorize failures: signature mismatch, mocked models, Pydantic errors
4. **Map to Phase 0 decision**: which failures are test defects vs production bugs?
5. Create fix priority order (align with architectural decision)

**Estimated Tokens**: 5,000 (analysis, no code changes)

### Phase 2: Strategic Fix Execution (Tier 2, Code Agent OR Test Generator)
**Goal**: Fix 14 signature mismatch failures based on Phase 0 decision

**Scenario A: Tests are defective** (update tests to match production):
1. Update test signatures: `orchestrate(input_value=...)`
2. Remove obsolete parameters: `user_input`, `input_mode`
3. Verify tests now test actual production API
4. Run tests to confirm fixes

**Scenario B: Production is defective** (restore `user_input` parameter):
1. Update TwoStageOrchestrator.orchestrate() signature
2. Add back `user_input` and `input_mode` parameters
3. Verify backward compatibility
4. Run tests to confirm fixes

**Scenario C: Intentional API change** (update tests + migration guide):
1. Update tests to new API (as in Scenario A)
2. Document breaking change in CHANGELOG
3. Update all callers in codebase
4. Verify no regression

**Decision Authority**: Chief Architect (based on Phase 0 analysis)

**Estimated Tokens**: 8,000 (mechanical changes, high confidence AFTER decision)

### Phase 3: TaskGraph Mock Replacement (Tier 2, Code Agent)
**Goal**: Replace 6 mocked TaskGraph tests with real models

**Tasks**:
1. Search for `MagicMock.*TaskGraph` patterns
2. Create TaskGraph factory functions for test data
3. Replace mocks with real instances
4. Verify Pydantic validation runs
5. Run tests to confirm fixes

**Estimated Tokens**: 12,000 (requires schema understanding)

### Phase 4: E2E Pydantic Validation Fixes (Tier 2, Code Agent)
**Goal**: Fix 18 E2E fixture validation errors

**Tasks**:
1. Run E2E tests with full tracebacks
2. Identify extra fields in fixtures
3. Remove extra fields, align with models
4. Add `model_validate()` verification
5. Run tests to confirm fixes

**Estimated Tokens**: 15,000 (model schema alignment)

### Phase 5: Full Test Suite Verification (Tier 1, Test Generator)
**Goal**: Verify 1,762/1,762 tests pass

**Tasks**:
1. Run complete test suite: `python run_tests.py --run-all`
2. Verify zero failures
3. Check execution time <3 minutes
4. Generate test report with metrics

**Estimated Tokens**: 5,000 (verification, reporting)

### Phase 6: Constitutional Compliance Audit (Tier 1, Quality Enforcer)
**Goal**: Validate Articles I-V compliance

**Tasks**:
1. Verify Article I (complete context, all 38 fixed)
2. Verify Article II (100% test pass rate)
3. Verify Article III (test gate works, no bypass)
4. Verify Article IV (patterns stored to VectorStore)
5. Verify Article V (spec-driven, acceptance criteria met)

**Estimated Tokens**: 3,000 (audit, compliance report)

---

## Strategic Agent Orchestration Plan

**Precision Engineering Approach** (German methodology):

### Stage 1: Discovery (Parallel Reconnaissance)
- **Auditor Agent**: Analyze production code architecture (TwoStageOrchestrator)
- **Auditor Agent**: Analyze test suite architecture (test patterns, mocking strategy)
- **Chief Architect**: Review ADRs and specs for design intent
- **Execution**: Parallel (3 agents simultaneously, 5-10 minutes)

### Stage 2: Architectural Decision (Sequential Synthesis)
- **Chief Architect**: Synthesize findings from Stage 1
- **Chief Architect**: Make decision: fix production, tests, or both
- **Chief Architect**: Document decision rationale (ADR if needed)
- **Execution**: Sequential (1 agent, 3-5 minutes)

### Stage 3: Strategic Execution (Conditional, Parallel)
- **IF tests defective**: Test Generator Agent → update tests to match production
- **IF production defective**: Code Agent → update production to match design
- **IF both defective**: Code Agent + Test Generator (parallel coordination)
- **Execution**: Depends on Stage 2 decision (15-25 minutes)

### Stage 4: Verification (Sequential)
- **Quality Enforcer**: Run full test suite, verify 100% pass rate
- **Quality Enforcer**: Validate constitutional compliance (Articles I-V)
- **Execution**: Sequential (1 agent, 3-5 minutes)

### Stage 5: Learning (Parallel)
- **Learning Agent**: Extract patterns from successful fixes
- **Learning Agent**: Store to VectorStore with confidence scores
- **Execution**: Parallel with Stage 4 completion (2-3 minutes)

**Total Orchestration Time**: 30-50 minutes (depends on Stage 2 decision)

---

## Estimated Cost

**Total Tokens**: ~58,000 (increased from ~48,000 due to Phase 0 architectural analysis)
**Tier Breakdown**:
- Tier 1 (complex): 18,000 tokens @ $4.00/1M = $0.072 (Auditor, Chief Architect analysis)
- Tier 2 (moderate): 35,000 tokens @ $1.50/1M = $0.053 (Code/Test fixes)
- Tier 3 (simple): 5,000 tokens @ $0/1M (local) = $0.000 (verification, learning)

**Total Estimated Cost**: $0.125 (~13 cents)

**Value Proposition**: Spend 13 cents to prevent wasting hours on wrong fixes. German engineering precision.

**Estimated Time**: 30-50 minutes (phases run sequentially with parallel sub-tasks)

---

## Risk Assessment

### High Risk
- **Risk**: Pydantic schema changes during fix implementation
- **Mitigation**: Lock Pydantic version, verify schema stability
- **Impact**: Medium (could invalidate fixes mid-execution)

### Medium Risk
- **Risk**: E2E fixtures have undocumented dependencies
- **Mitigation**: Incremental testing, one fixture at a time
- **Impact**: Low (extra time, no correctness issue)

### Low Risk
- **Risk**: Two-stage orchestrator signature changes again
- **Mitigation**: Add integration test for signature stability
- **Impact**: Very Low (caught immediately by tests)

---

## Rollback Plan

If any phase fails:

1. **Immediate**: Rollback to clean git state
   ```bash
   git checkout -- .
   git clean -fd
   ```

2. **Assessment**: Identify root cause of failure
   - Schema mismatch? → Update spec, regenerate fixtures
   - Logic error? → Fix implementation, rerun tests
   - Unknown? → Escalate to human review

3. **Retry**: Apply constitutional retry policy (Article I)
   - Retry 1: 2x timeout
   - Retry 2: 3x timeout
   - Retry 3: 10x timeout, escalate if still failing

4. **Store Learnings**: Update VectorStore with failure patterns (Article IV)

---

## Constitutional Alignment

### Article I: Complete Context Before Action
- ✅ All 38 failures identified and categorized
- ✅ Root causes analyzed before fixes applied
- ✅ No partial fixes (all 38 addressed or none)

### Article II: 100% Verification and Stability
- ✅ Target: 1,762/1,762 tests passing
- ✅ Zero broken windows tolerance
- ✅ Test gate blocks PRs with failures

### Article III: Automated Merge Enforcement
- ✅ Quality gates mandatory (no bypass)
- ✅ CI checks required before merge
- ✅ Branch protection active

### Article IV: Continuous Learning and Improvement
- ✅ Failure patterns stored to VectorStore
- ✅ Fix strategies tagged for future reuse
- ✅ Confidence scores tracked (≥0.6 threshold)

### Article V: Spec-Driven Development
- ✅ This specification drives all implementation
- ✅ Acceptance criteria explicit and measurable
- ✅ Test plan follows NECESSARY pattern

---

## Appendices

### Appendix A: Example Two-Stage Orchestrator Test Fix

**Before** (fails with signature mismatch):
```python
result = await orchestrator.orchestrate(
    user_input="Add JWT authentication",
    input_mode=InputMode.NATURAL_LANGUAGE,
)
```

**After** (matches real API):
```python
result = await orchestrator.orchestrate(
    input_value="Add JWT authentication"  # Auto-detects natural language mode
)
```

### Appendix B: Example TaskGraph Mock Replacement

**Before** (mock bypasses validation):
```python
mock_graph = MagicMock(spec=TaskGraph)
mock_graph.phases = [mock_phase_1, mock_phase_2]
mock_graph.topological_sort = MagicMock(return_value=[[task_1], [task_2]])
```

**After** (real Pydantic model):
```python
real_graph = TaskGraph(
    mission="Test mission",
    phases=[
        Phase(
            id="phase_1",
            title="Phase 1",
            tasks=[task_1]
        ),
        Phase(
            id="phase_2",
            title="Phase 2",
            tasks=[task_2]
        )
    ]
)
# Pydantic validation runs automatically
layers = real_graph.topological_sort()
```

### Appendix C: Example E2E Fixture Pydantic Fix

**Before** (extra field causes validation error):
```python
test_data = {
    "id": "test_123",
    "name": "Test Task",
    "status": "pending",
    "extra_debug_info": "Only used in tests"  # ❌ Not in Pydantic model
}
task = Task(**test_data)  # Fails: extra fields not permitted
```

**After** (aligned with model):
```python
test_data = {
    "id": "test_123",
    "title": "Test Task",  # ✅ Correct field name
    "type": TaskType.CODE,
    "tier": TaskTier.TIER_2,
    "agent": "coder",
    "description": "Test task description",
    "dependencies": []
}
task = Task(**test_data)  # ✅ Passes validation
```

---

## Review Checklist (User Approval Checkpoint)

Before proceeding to Stage 2 (TDD Execution), verify:

- [ ] **Spec Completeness**: All 3 failure categories addressed?
- [ ] **Acceptance Criteria**: Clear, measurable, testable?
- [ ] **Test Plan**: NECESSARY pattern compliance (9/9 categories)?
- [ ] **Risk Assessment**: Mitigation strategies reasonable?
- [ ] **Cost Estimate**: Within budget ($0.085 << $10 limit)?
- [ ] **Constitutional Alignment**: Articles I-V compliance verified?

**Approval Decision**: _______________
**Reason (if rejected)**: _______________
**Suggested Improvements**: _______________

---

**End of Specification**

**Next Step**: Await user approval to proceed to Stage 2 (TDD Execution)
