# Specification: Comprehensive Test Validation Strategy

**ID**: SPEC-027
**Status**: Draft
**Created**: 2025-10-24
**Updated**: 2025-10-24
**Owner**: PlannerAgent
**Type**: Strategic Specification (Tier 1)

---

## Goals

**Primary Objective**: Achieve and maintain 100% green test suite across all 6,099 tests (290 test files) with zero regressions and comprehensive validation strategy.

**Success Metrics**:
- ✅ 100% test pass rate (6,099/6,099 tests passing)
- ✅ Zero skipped tests (excluding legitimate platform/integration markers)
- ✅ Zero xfail tests (all known failures fixed)
- ✅ Complete test execution (no timeouts, Article I compliance)
- ✅ Memory-aware execution (ADR-023 compliance, no kernel panics)
- ✅ Systematic failure categorization taxonomy
- ✅ Prioritization matrix for critical path tests
- ✅ Rollback strategy for regression detection

---

## Non-Goals

**Explicitly out of scope**:
- ❌ Test suite reduction (Article VII "Value-First Testing" is separate initiative)
- ❌ Performance optimization of individual tests (separate from validation)
- ❌ Rewriting test framework or infrastructure
- ❌ Adding new test coverage (focus is validating existing tests)
- ❌ Deleting low-value tests (separate Value Audit process)
- ❌ CI/CD pipeline optimization (local validation primary, CI optional per Article III)

---

## Personas

### Persona 1: QualityEnforcer Agent
- **Context**: Autonomous test validation and constitutional compliance
- **Need**: Systematic strategy to validate 100% of tests against Constitutional Articles I-VII
- **Interaction**: Executes validation phases, categorizes failures, prioritizes fixes

### Persona 2: CodingAgent
- **Context**: Fixing test failures identified by validation process
- **Need**: Clear categorization of failure types (Pydantic, fixtures, imports, assertions)
- **Interaction**: Receives prioritized test fix tasks from validation results

### Persona 3: Human Operator (@am)
- **Context**: Strategic oversight of test suite health
- **Need**: Dashboard view of test health, regression alerts, rollback decisions
- **Interaction**: Reviews validation reports, approves high-risk fixes, triggers rollbacks if needed

---

## Current State Analysis

### Test Suite Metrics (2025-10-24)

**Inventory**:
- **Total tests**: 6,099 test functions across 290 test files
- **Current status**: 6,258 items collected (includes fixtures, parameterized variations)
- **Pass rate**: ~99.2% (13 skipped tests observed in sample run)
- **Recent fixes**: Division-by-zero, fixture determinism, Pydantic validation, Leap 3 E2E (14/14 passing)

**Skipped Test Analysis** (Article II violation candidates):
```
Skip markers found: 65 occurrences across 33 files
Breakdown by reason:
- Integration tests requiring Docker: ~20 tests (test_docker_ollama_*.py)
- Platform-specific skips: ~10 tests (Windows/Linux conditional)
- Slow benchmarks: ~5 tests (test_vectorstore_performance.py)
- Feature flags: ~5 tests (test_real_llm_cost_tracking.py)
- Work-in-progress: ~25 tests (various, need audit)
```

**Memory Context** (ADR-023):
- **Hardware**: Apple M4 Pro, 48GB unified memory
- **Local model footprint**: 38GB (Qwen3-Coder 30B Q8_0: 19GB model + 16GB KV cache + 3GB overhead)
- **Test parallelism**: Adaptive (1-10 workers based on available memory)
- **Safety margin**: 5GB for system stability

### Recent Victories (Context for Learnings)

**Phase 1 Consolidation** (Commit 35df6e7d):
- Removed "dead weight" tests with zero regression
- Proves safe test removal is possible when validated

**Leap 3 E2E Fixes** (Recent):
- 14/14 tests now passing (was 0/14)
- Demonstrates systematic fix approach works

**Pydantic Validation Fixes** (Commit 8e73edb2):
- Resolved dependency and validation errors
- Established pattern for Pydantic v2 migration

---

## Acceptance Criteria

### Functional Criteria

**AC-1: Complete Test Execution** (Article I)
- [ ] All 6,099 tests execute to completion (no timeouts)
- [ ] Retry logic with 2x, 3x, 10x timeout extensions implemented
- [ ] Memory-aware execution prevents kernel panics
- [ ] Test results fully captured (no incomplete runs)

**AC-2: 100% Pass Rate** (Article II)
- [ ] Zero test failures (6,099/6,099 passing)
- [ ] Zero xfail markers (all known failures fixed or justified)
- [ ] Skipped tests < 15 total (only legitimate platform/integration exclusions)
- [ ] All "Delete the Fire First" tests green before proceeding

**AC-3: Failure Categorization Taxonomy**
- [ ] All test failures categorized into taxonomy (see Section: Taxonomy)
- [ ] Each category has documented fix pattern
- [ ] VectorStore query results applied to categorization
- [ ] Historical fix patterns referenced in taxonomy

**AC-4: Prioritization Matrix**
- [ ] All tests assigned priority tier (P0/P1/P2/P3)
- [ ] Critical path tests identified (authentication, data integrity, security)
- [ ] Blast radius calculated for each test failure
- [ ] Dependency graph mapped (test interdependencies)

**AC-5: Execution Strategy**
- [ ] Memory-aware worker count strategy defined (1/3/6/10 workers)
- [ ] Sequential validation phases documented (smoke → unit → integration → e2e)
- [ ] Parallel execution opportunities maximized (independent test groups)
- [ ] Timeout budgets allocated per test category

**AC-6: Rollback Strategy**
- [ ] Pre-validation snapshot mechanism defined
- [ ] Regression detection threshold set (any new failure = rollback trigger)
- [ ] Automated rollback script available
- [ ] Manual override procedure for false positives

### Non-Functional Criteria

**Performance**:
- Test suite completion time: <10 minutes (local model OFF, 10 workers)
- Test suite completion time: <30 minutes (local model ON, 3 workers)
- Memory usage: <40GB peak (5GB safety margin)
- CPU utilization: <80% average (thermal management)

**Reliability**:
- Test flakiness rate: <0.1% (max 6 flaky tests out of 6,099)
- Consecutive passes: 10 runs without failure (stability proof)
- Deterministic fixtures: 100% (no random failures)

**Constitutional Compliance**:
- Article I: Complete context verified (100% test execution)
- Article II: 100% verification achieved (zero failures)
- Article III: Local enforcement gates active (pre-commit hooks)
- Article IV: VectorStore learnings applied (past fix patterns queried)
- Article V: Spec-driven process followed (this document)
- Article VI: TDD workflow validated (tests exist before implementation)
- Article VII: Value-first philosophy respected (keep high-value tests)

---

## Test Failure Categorization Taxonomy

### Category 1: Pydantic Validation Errors
**Signature**: `ValidationError`, `pydantic.error_wrappers`, `Field required`

**Common Causes**:
- Missing required fields in model instantiation
- Type mismatches (int vs str, dict vs model)
- Pydantic v2 migration issues (Config → model_config)
- Extra fields not allowed in strict mode

**Fix Pattern**:
```python
# Before (Pydantic v1)
class Config:
    extra = "forbid"

# After (Pydantic v2)
model_config = ConfigDict(extra="forbid")
```

**Priority**: P1 (High) - Blocks model usage, cascading failures

**Estimated Prevalence**: ~5% of failures (based on recent commit 8e73edb2)

### Category 2: Fixture Errors
**Signature**: `fixture 'X' not found`, `fixture is not defined`, `TypeError: fixture()`

**Common Causes**:
- Missing fixture imports (conftest.py not loaded)
- Fixture scope mismatch (function vs session)
- Circular fixture dependencies
- Fixture teardown failures (resource leaks)

**Fix Pattern**:
```python
# Ensure conftest.py in correct location
tests/conftest.py  # Root fixtures
tests/unit/conftest.py  # Unit-specific fixtures

# Check fixture scope
@pytest.fixture(scope="session")  # Reuse across tests
@pytest.fixture(scope="function")  # Fresh per test
```

**Priority**: P0 (Critical) - Blocks entire test file execution

**Estimated Prevalence**: ~10% of failures (fixtures are foundation)

### Category 3: Import/Dependency Errors
**Signature**: `ModuleNotFoundError`, `ImportError`, `AttributeError: module has no attribute`

**Common Causes**:
- Missing package dependencies (not in requirements.txt)
- Circular import chains
- Relative import path errors
- Conditional imports failing (missing optional deps)

**Fix Pattern**:
```python
# Use absolute imports
from shared.agent_context import AgentContext  # ✅ Good
from ..shared.agent_context import AgentContext  # ❌ Fragile

# Handle optional dependencies
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

@pytest.mark.skipif(not HAS_ANTHROPIC, reason="anthropic not installed")
def test_anthropic_feature(): ...
```

**Priority**: P0 (Critical) - Prevents test discovery/collection

**Estimated Prevalence**: ~2% of failures (infrastructure issue)

### Category 4: Assertion Failures
**Signature**: `AssertionError`, `assert X == Y`, `Expected X but got Y`

**Common Causes**:
- Implementation bug (real code defect)
- Test expectation mismatch (test needs update)
- Flaky test (non-deterministic behavior)
- Race condition (async timing issue)

**Fix Pattern**:
```python
# Deterministic assertions
assert result.value == "expected"  # ✅ Good (exact match)
assert "substring" in result.message  # ⚠️ Fragile (order-dependent)

# Async assertions with retry
async def test_async_operation():
    result = await operation()
    await asyncio.sleep(0.1)  # Allow event loop processing
    assert result.is_complete()
```

**Priority**: P2 (Medium) - Test-specific, isolated blast radius

**Estimated Prevalence**: ~30% of failures (most common type)

### Category 5: Timeout Errors
**Signature**: `TimeoutExpired`, `pytest.timeout`, `asyncio.TimeoutError`

**Common Causes**:
- Slow integration tests (Docker startup, network calls)
- Infinite loops (logic bug)
- Memory exhaustion (thrashing, swapping)
- Deadlocks (async resource contention)

**Fix Pattern** (Article I compliance):
```python
# Progressive timeout extension
@pytest.mark.timeout(120)  # Start with 2 minutes
def test_slow_operation():
    result = run_operation(timeout_multiplier=2)
    assert result.is_ok()

# Retry logic with backoff
for attempt in range(3):
    try:
        result = run_with_timeout(timeout=60 * (2 ** attempt))
        break
    except TimeoutError:
        if attempt == 2:
            raise
```

**Priority**: P1 (High) - Violates Article I (incomplete context)

**Estimated Prevalence**: ~8% of failures (common in integration tests)

### Category 6: Memory/Resource Errors
**Signature**: `MemoryError`, `OSError: [Errno 24] Too many open files`, `psutil.NoSuchProcess`

**Common Causes**:
- Memory leak (unclosed resources)
- File descriptor exhaustion (missing context managers)
- Local model + parallel tests = memory pressure (ADR-023)
- Temp file accumulation (/tmp full)

**Fix Pattern** (ADR-023 compliance):
```python
# Memory-aware test execution
from tools.memory_aware_test_runner import get_safe_worker_count

worker_count = get_safe_worker_count()
# Returns: 1 (<10GB), 3 (local model ON), 10 (cloud only), or 6 (moderate)

# Resource cleanup
@pytest.fixture
def temp_resource():
    resource = create_resource()
    yield resource
    resource.cleanup()  # ALWAYS cleanup in fixture
```

**Priority**: P0 (Critical) - Can cause kernel panics, Article I violation

**Estimated Prevalence**: ~5% of failures (hardware-constrained)

### Category 7: Mock/Patch Errors
**Signature**: `MagicMock has no attribute`, `patch target not found`, `assert_called_once() failed`

**Common Causes**:
- Incorrect patch target path
- Mock not configured (missing return_value)
- Over-mocking (testing mocks, not real code)
- Mock state leakage between tests

**Fix Pattern** (Article VII compliance):
```python
# Prefer real components over mocks
def test_memory_store():
    store = MemoryStore()  # ✅ Real component
    store.set("key", "value")
    assert store.get("key") == "value"

# NOT this:
def test_memory_store_mocked():
    mock_store = MagicMock()  # ❌ Mocking hell
    mock_store.get.return_value = "value"
    assert mock_store.get("key") == "value"  # Tests nothing real
```

**Priority**: P3 (Low) - Often indicates low-value test (Article VII)

**Estimated Prevalence**: ~15% of failures (anti-pattern legacy)

### Category 8: Async/Concurrency Errors
**Signature**: `RuntimeError: Event loop is closed`, `asyncio.CancelledError`, `Task was destroyed but pending`

**Common Causes**:
- Event loop not properly closed
- Async fixture not awaited
- Task cancellation not handled
- Race condition in parallel execution

**Fix Pattern**:
```python
# Proper async test setup
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result.is_ok()

# Event loop cleanup
@pytest.fixture
async def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    # Cleanup pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
```

**Priority**: P1 (High) - Affects async-heavy components (memory, agents)

**Estimated Prevalence**: ~10% of failures (async complexity)

### Category 9: Database/Persistence Errors
**Signature**: `sqlite3.OperationalError`, `FileNotFoundError: db.sqlite`, `IntegrityError`

**Common Causes**:
- Database not initialized
- Schema migration not applied
- File permissions issue
- Stale database state between tests

**Fix Pattern**:
```python
# Fresh database per test
@pytest.fixture
def db_session():
    db_path = Path(tempfile.mkdtemp()) / "test.db"
    db = initialize_database(db_path)
    yield db
    db.close()
    db_path.unlink()  # Clean up
```

**Priority**: P1 (High) - Data integrity critical

**Estimated Prevalence**: ~5% of failures (persistence layer)

### Category 10: Docker/Integration Errors
**Signature**: `requests.exceptions.ConnectionError`, `Docker daemon not running`, `Service unhealthy`

**Common Causes**:
- Docker not installed/running
- Service startup timeout
- Port conflict (11434 already bound)
- Health check failure

**Fix Pattern** (docker-compose.yml from run_tests.py):
```python
# Graceful Docker handling
@pytest.mark.skipif(not docker_available(), reason="Docker not available")
def test_ollama_integration():
    client = OllamaClient("http://localhost:11434")
    assert client.health_check()
```

**Priority**: P2 (Medium) - Integration tests, not critical path

**Estimated Prevalence**: ~10% of failures (integration layer, legitimate skips)

---

## Prioritization Matrix

### Priority Tiers

**P0: Critical Path (Blocking)**
- **Criteria**: Test blocks multiple other tests, affects core functionality, constitutional violation
- **Examples**:
  - Fixture initialization failures (blocks entire test file)
  - Import errors (prevents test collection)
  - Memory exhaustion (kernel panic risk, Article I violation)
  - Database schema corruption (data integrity)
- **Action**: Fix IMMEDIATELY before any other work
- **Estimated count**: ~50 tests (0.8% of total)
- **Blast radius**: >100 tests affected per P0 failure

**P1: High Priority (Urgent)**
- **Criteria**: Core business logic, security-critical, frequent regressions
- **Examples**:
  - Authentication/authorization tests
  - Pydantic model validation (cascading failures)
  - Async/concurrency edge cases
  - Constitutional compliance tests (Article I-VII validation)
- **Action**: Fix within 24 hours
- **Estimated count**: ~300 tests (5% of total)
- **Blast radius**: 10-100 tests affected per P1 failure

**P2: Medium Priority (Important)**
- **Criteria**: Feature-specific, isolated blast radius, non-critical path
- **Examples**:
  - Agent-specific unit tests (planner, coder, quality_enforcer)
  - Tool-specific tests (git, bash, memory)
  - Assertion failures in edge cases
  - Integration tests for non-critical services
- **Action**: Fix within 1 week
- **Estimated count**: ~2,500 tests (41% of total)
- **Blast radius**: 1-10 tests affected per P2 failure

**P3: Low Priority (Nice to Have)**
- **Criteria**: Mock-heavy tests, implementation detail tests, redundant coverage
- **Examples**:
  - Mocking hell tests (>10 mocks, Article VII candidates for deletion)
  - Framework behavior tests (testing pytest, not our code)
  - Duplicate parameterized tests (redundant coverage)
  - Slow benchmark tests (>10s runtime)
- **Action**: Fix opportunistically OR delete per Article VII
- **Estimated count**: ~3,200 tests (52% of total, Value Audit targets)
- **Blast radius**: 0 tests affected (isolated)

### Critical Path Tests (Must Always Pass)

**Authentication & Authorization**:
- `tests/test_anthropic_memory_security.py` (30 tests, security-critical)
- `tests/unit/shared/test_hitl_protocol.py` (human-in-the-loop auth)

**Data Integrity**:
- `tests/test_enhanced_memory_store_*.py` (VectorStore persistence)
- `tests/test_vector_store_lifecycle.py` (memory lifecycle)

**Constitutional Compliance**:
- `tests/adr/test_adr_026_validation.py` (TDD workflow validation)
- `tests/tools/constitutional_intelligence/` (Article I-VII enforcement)

**Core Agent Functionality**:
- `tests/test_quality_enforcer_agent.py` (autonomous quality checks)
- `tests/unit/test_chief_architect_agent.py` (ADR creation logic)

**Integration Workflows**:
- `tests/test_leap3_e2e_integration.py` (14 tests, Leap 3 E2E)
- `tests/test_leap4_e2e_quality_feedback.py` (Leap 4 quality feedback loop)

---

## Execution Strategy

### Phase 1: Smoke Tests (30 seconds)
**Objective**: Verify test infrastructure and critical path

**Tests**: ~100 tests (1.6% of total)
- Fixture initialization (conftest.py tests)
- Import sanity checks (can load all modules?)
- Memory availability check (psutil verification)
- Docker availability check (if integration enabled)

**Workers**: 1 (sequential, fast feedback)

**Exit Criteria**:
- ✅ All smoke tests pass → Proceed to Phase 2
- ❌ Any failure → STOP, fix infrastructure first (Article I)

### Phase 2: Unit Tests (3-8 minutes)
**Objective**: Validate isolated component logic

**Tests**: ~4,000 tests (65% of total, fast tests <1s each)
- Agent unit tests (planner, coder, quality_enforcer, etc.)
- Tool unit tests (git, bash, memory, constitutional)
- Shared utility tests (model_policy, agent_context, type_definitions)
- Pydantic model validation tests

**Workers**:
- Local model OFF: 10 workers (3 min runtime)
- Local model ON: 3 workers (8 min runtime, ADR-023)

**Exit Criteria**:
- ✅ 100% pass rate → Proceed to Phase 3
- ❌ Failures categorized → Fix by priority (P0 → P1 → P2)

### Phase 3: Integration Tests (5-15 minutes)
**Objective**: Validate component interactions

**Tests**: ~1,800 tests (30% of total, slower tests 1-10s each)
- Agent integration tests (planner → coder workflow)
- Memory integration tests (VectorStore + Firestore)
- Docker integration tests (Ollama, if enabled)
- End-to-end workflows (Leap 3, Leap 4)

**Workers**:
- Docker OFF: 6 workers (5 min runtime)
- Docker ON: 3 workers (15 min runtime, service startup overhead)

**Exit Criteria**:
- ✅ 100% pass rate → Proceed to Phase 4
- ❌ Docker failures → Legitimate skips OK (per Article II amendment)
- ❌ Non-Docker failures → Fix immediately (P1 priority)

### Phase 4: End-to-End Tests (2-5 minutes)
**Objective**: Validate complete user workflows

**Tests**: ~300 tests (5% of total, full workflows)
- Leap 3 E2E integration (14 tests, recently fixed)
- Leap 4 quality feedback (E2E quality loop)
- Trinity Protocol orchestration
- PrimeA autonomous workflows

**Workers**: 1 (sequential, avoid race conditions)

**Exit Criteria**:
- ✅ 100% pass rate → SUCCESS, all phases complete
- ❌ Any failure → ROLLBACK candidate (E2E regressions critical)

### Memory-Aware Execution (ADR-023)

**Worker Count Decision Tree**:
```python
def get_safe_worker_count() -> int:
    mem_gb = psutil.virtual_memory().available / (1024 ** 3)
    ollama_running = check_ollama_process()

    # Critical memory: sequential execution
    if mem_gb < 10:
        return 1  # 3GB budget

    # Local model active: conservative
    if ollama_running and mem_gb < 15:
        return 3  # 9GB budget (safe for 48GB Mac)

    # Plenty of memory: full parallelism
    if mem_gb >= 20:
        return 10  # 30GB budget

    # Moderate memory: balanced
    return 6  # 18GB budget
```

**Total Memory Budget**:
- System overhead: 8GB (macOS, background apps)
- Local model (if active): 38GB (19GB + 16GB KV + 3GB)
- Test workers: 3-30GB (1-10 workers × 3GB/worker)
- Safety margin: 5GB
- **Total**: 46GB (safe for 48GB system)

### Parallel Execution Opportunities

**Independent Test Groups** (can run in parallel):
- Agent tests (planner, coder, quality_enforcer) → No shared state
- Tool tests (git, bash, memory) → Isolated fixtures
- Unit vs Integration → Different worker pools

**Sequential Requirements** (must run serially):
- E2E tests (shared database state)
- Docker integration tests (port conflicts)
- Property-based tests (resource-intensive, avoid contention)

---

## Rollback Strategy

### Pre-Validation Snapshot

**Objective**: Create git snapshot before any test fixes for safe rollback

**Mechanism**:
```bash
# Before starting validation/fixes
git stash push -u -m "Pre-validation snapshot $(date +%Y%m%d_%H%M%S)"
git tag "test-validation-start-$(date +%Y%m%d-%H%M%S)"

# Record baseline test results
python run_tests.py --run-all > baseline_results.json
```

**Snapshot Contents**:
- All uncommitted changes (git stash)
- Git tag for reference point
- Baseline test results (JSON format)
- Memory/system state (psutil snapshot)

### Regression Detection

**Threshold**: Any new test failure = regression (zero tolerance)

**Detection Mechanism**:
```python
def detect_regression(baseline: dict, current: dict) -> bool:
    """
    Compare test results for regressions.

    Regression = any test that passed in baseline now fails.
    """
    baseline_passes = set(baseline["passed"])
    current_failures = set(current["failed"])

    # Check for new failures
    new_failures = current_failures - (set(baseline["failed"]))

    if new_failures:
        print(f"❌ REGRESSION: {len(new_failures)} new failures")
        for test in new_failures:
            print(f"   - {test}")
        return True

    return False
```

**Regression Response**:
1. **STOP immediately** (Article I: complete context)
2. **Log regression details** (which tests, failure messages)
3. **Notify human operator** (requires decision)
4. **Offer rollback options** (see below)

### Rollback Options

**Option 1: Full Rollback** (Nuclear option)
```bash
# Revert to pre-validation state
git reset --hard test-validation-start-TIMESTAMP
git stash pop  # Restore original changes
```
**When to use**: Multiple regressions, unclear root cause, high blast radius

**Option 2: Partial Rollback** (Surgical option)
```bash
# Revert specific file
git checkout test-validation-start-TIMESTAMP -- path/to/problematic_file.py

# Re-run tests to verify
python run_tests.py path/to/problematic_test.py
```
**When to use**: Single file regression, clear root cause, isolated failure

**Option 3: Forward Fix** (Iterative option)
```bash
# Fix the regression inline
# (Human operator decision required)

# Verify fix
python run_tests.py --run-all
# Must show: baseline_failures - fixed_count = current_failures
```
**When to use**: Obvious fix, low risk, regression understood

### False Positive Handling

**Scenario**: Test appears to regress but it's a flaky test (non-deterministic)

**Detection**:
```python
# Run test 10 times to confirm flakiness
for i in range(10):
    result = run_test(test_name)
    if result.passed:
        flaky_count += 1

if flaky_count > 0 and flaky_count < 10:
    print(f"⚠️  FLAKY TEST: {test_name} ({flaky_count}/10 passes)")
```

**Response**:
1. Mark test as flaky (add `@pytest.mark.flaky` decorator)
2. File issue for flaky test investigation
3. Proceed with validation (not a true regression)
4. Fix flakiness in separate task (P1 priority)

---

## Success Metrics

### Quantitative Metrics

**Test Health Score** (0-100):
```python
test_health_score = (
    (pass_rate * 100) * 0.5 +              # 50%: Pass rate (100% = 50 points)
    ((1 - skip_rate) * 100) * 0.2 +        # 20%: Low skip rate (0% = 20 points)
    ((1 - xfail_rate) * 100) * 0.1 +       # 10%: Zero xfails (0% = 10 points)
    ((1 - flaky_rate) * 100) * 0.1 +       # 10%: Low flakiness (0% = 10 points)
    (execution_completeness * 100) * 0.1   # 10%: Complete runs (100% = 10 points)
)
```
**Target**: >95/100 (currently estimated ~92/100)

**Pass Rate**: 6,099 passed / 6,099 total = 100.0%
**Target**: 100% (zero tolerance, Article II)

**Skip Rate**: 13 skipped / 6,099 total = 0.21%
**Target**: <0.25% (only legitimate platform/integration skips)

**Execution Time**:
- Local model OFF: <10 minutes (10 workers)
- Local model ON: <30 minutes (3 workers, ADR-023)
**Target**: Meet or beat current times (no performance regression)

**Memory Peak**: <40GB (5GB safety margin)
**Target**: Zero kernel panics, zero OOM kills

### Qualitative Metrics

**Constitutional Compliance**:
- ✅ Article I: Complete context (100% test execution, no timeouts)
- ✅ Article II: 100% verification (zero failures, zero xfails)
- ✅ Article III: Local enforcement active (pre-commit hooks)
- ✅ Article IV: VectorStore learnings applied (past patterns referenced)
- ✅ Article V: Spec-driven process (this document follows spec-kit)
- ✅ Article VI: TDD workflow (tests before implementation validated)
- ✅ Article VII: Value-first philosophy (prioritization matrix respects value)

**Developer Confidence**:
- Can run `python run_tests.py --run-all` and trust 100% green = ship-ready
- Regressions detected immediately (within 1 commit)
- Rollback available with <5 minute recovery time

**Maintenance Burden**:
- Test fixes categorized and documented (taxonomy above)
- Fix patterns reusable (VectorStore storage)
- Flaky tests identified and tracked (<0.1% flaky rate)

---

## VectorStore Learnings Integration (Article IV)

### Query Results Summary

**Status**: VectorStore query attempted but API signature mismatch detected:
```python
TypeError: AgentContext.search_memories() got an unexpected keyword argument 'limit'
```

**Action Taken**: Manual review of recent commit history for test recovery patterns

**Learnings Extracted** (from git log):

1. **Pydantic Validation Pattern** (Commit 8e73edb2):
   - Fix: Resolve dependency and Pydantic validation errors
   - Pattern: Systematic migration to Pydantic v2 (Config → model_config)
   - Application: Category 1 taxonomy (Pydantic errors)

2. **Fixture Determinism Pattern** (Commit 15b02b9b):
   - Fix: Division-by-zero and fixture determinism issues
   - Pattern: Ensure fixtures return consistent values across runs
   - Application: Category 2 taxonomy (Fixture errors)

3. **Phase 1 Consolidation Pattern** (Commit 35df6e7d):
   - Fix: Remove "dead weight" tests with zero regression
   - Pattern: Safe test deletion when validated (Article VII compliance)
   - Application: P3 priority tier (low-value test candidates)

4. **V5 Calibration Pattern** (Commit 16b8cf82):
   - Fix: 16% HIGH classification + fix ALL tests
   - Pattern: Systematic quality classification before fixing
   - Application: Prioritization matrix (P0/P1/P2/P3 tiers)

5. **Leap 3 E2E Pattern** (Recent success):
   - Fix: 0/14 → 14/14 tests passing
   - Pattern: Sequential fixing of E2E dependencies (fix fixtures → fix assertions)
   - Application: Phase 4 execution strategy (E2E tests)

### VectorStore Storage Plan (Post-Validation)

**Store after successful 100% pass validation**:
```python
context.store_memory(
    key=f"test_validation_success_{timestamp}",
    content={
        "total_tests": 6099,
        "pass_rate": 1.0,
        "categories_fixed": ["pydantic", "fixture", "assertion", "timeout"],
        "rollback_triggered": False,
        "execution_time_seconds": execution_time,
        "memory_peak_gb": memory_peak,
        "worker_count": worker_count,
        "taxonomy": taxonomy_dict,
        "prioritization_matrix": priority_dict
    },
    tags=["test", "validation", "success", "100_percent", "article_ii"]
)
```

**Future agents can query**:
```python
# Query for successful validation patterns
learnings = context.search_memories(
    tags=["test", "validation", "success"],
    include_session=False  # Cross-session learning
)

# Apply to new test failures
for learning in learnings:
    if learning["categories_fixed"] includes current_failure_type:
        apply_pattern(learning["fix_pattern"])
```

---

## Dependencies

- **SPEC-023**: Ollama Docker Integration (memory constraints, ADR-023)
- **ADR-001**: Complete Context Before Action (timeout retry logic)
- **ADR-002**: 100% Verification and Stability (zero tolerance for failures)
- **ADR-023**: Memory-Aware Test Execution (worker count strategy)
- **Article I-VII**: Constitutional compliance requirements

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Regression during fixing** | High | Medium | Rollback strategy (git snapshot), regression detection |
| **Memory exhaustion (kernel panic)** | Critical | Low | ADR-023 worker limits, 5GB safety margin, cloud fallback |
| **Timeout on full test suite** | Medium | Medium | Phase-based execution, progressive timeout extension (2x/3x/10x) |
| **Flaky test false positives** | Medium | Medium | 10-run flakiness detection, mark flaky tests, investigate separately |
| **Docker unavailable (integration tests)** | Low | High | Legitimate skip markers, graceful degradation per Article II |
| **VectorStore query failure** | Low | Low | Manual pattern extraction from git history (fallback) |
| **Circular test dependencies** | Medium | Low | Dependency graph analysis, break cycles with mocks |
| **Local model interference** | Medium | Medium | Adaptive worker count (3 workers when local model active) |

---

## Implementation Plan Reference

**Note**: Full technical plan will be created in `plans/plan-027-test-validation-strategy.md` after this spec is approved (Article V requirement).

**Preview of plan phases**:
1. **Phase 1**: Infrastructure setup (baseline snapshot, regression detection script)
2. **Phase 2**: Smoke test validation (fixture/import sanity)
3. **Phase 3**: Systematic failure categorization (run all tests, categorize failures)
4. **Phase 4**: Prioritized fixing (P0 → P1 → P2, skip P3 for Value Audit)
5. **Phase 5**: Validation and rollback readiness (10 consecutive green runs)
6. **Phase 6**: VectorStore learning storage (success patterns for future)

---

## References

- **ADR-001**: Complete Context Before Action (timeout retry logic)
- **ADR-002**: 100% Verification and Stability (zero failure tolerance)
- **ADR-023**: Memory-Aware Test Execution (worker count, memory budgets)
- **Article I-VII**: Constitutional Articles (compliance requirements)
- **run_tests.py**: Test runner implementation (memory-aware, Docker lifecycle)
- **Recent commits**: 15b02b9b (fixture fixes), 8e73edb2 (Pydantic fixes), 35df6e7d (consolidation)

---

## Appendix A: Test Count Breakdown

**Total Tests**: 6,099 test functions
**Total Files**: 290 test files (306 Python files in tests/)
**Skip Markers**: 65 occurrences across 33 files

**By Test Type** (estimated):
- Unit tests: ~4,000 (65%)
- Integration tests: ~1,800 (30%)
- End-to-end tests: ~300 (5%)

**By Priority** (estimated):
- P0 (Critical): ~50 tests (0.8%)
- P1 (High): ~300 tests (5%)
- P2 (Medium): ~2,500 tests (41%)
- P3 (Low): ~3,200 tests (52%, Article VII deletion candidates)

**By Module**:
- Agent tests: ~1,500 (planner, coder, quality_enforcer, chief_architect, etc.)
- Tool tests: ~2,000 (git, bash, memory, constitutional, orchestrator, etc.)
- Shared tests: ~500 (agent_context, model_policy, type_definitions, utils)
- Integration tests: ~1,800 (Leap 3/4 E2E, Trinity Protocol, memory lifecycle)
- Property tests: ~200 (hypothesis-driven, critical properties)

---

## Appendix B: Memory Budget Details

**System Configuration**:
- **Hardware**: Apple M4 Pro, 48GB unified memory, 273 GB/s bandwidth
- **macOS overhead**: ~8GB (system, WindowServer, background services)
- **Available RAM**: 40GB (48GB - 8GB)
- **Safety margin**: 5GB (for system stability)

**Local Model Footprint** (Qwen3-Coder 30B Q8_0):
- Model weights: 19GB (Q4_K_M quantization)
- KV cache: 16GB (Q8_0 quantization, 2x memory savings vs F16)
- Overhead: 3GB (context buffer, GGML runtime)
- **Total**: 38GB

**Test Worker Memory**:
- Worker footprint: ~3GB per worker (pytest overhead, test fixtures, temp data)
- 1 worker: 3GB
- 3 workers: 9GB (local model ON, safe for 48GB Mac)
- 6 workers: 18GB (moderate parallelism)
- 10 workers: 30GB (full parallelism, local model OFF)

**Total Memory Usage**:
- **Local model ON**: 38GB (model) + 9GB (3 workers) = 47GB (1GB margin, safe)
- **Local model OFF**: 0GB (model) + 30GB (10 workers) = 30GB (10GB margin, optimal)

**Fallback Triggers**:
- Available memory < 10GB → 1 worker (sequential)
- Available memory < 8GB → Cloud API fallback (disable local model for P3 tasks)

---

## Appendix C: Constitutional Compliance Checklist

**Before any test validation action**:
- [x] **Article I**: Complete Context Before Action
  - Retry on timeout (2x, 3x, 10x)
  - ALL tests run to completion
  - Never proceed with incomplete data
  - Zero broken windows tolerance

- [x] **Article II**: 100% Verification and Stability
  - Main branch: 100% test success ALWAYS
  - No merge without 100% test pass
  - Definition of Done: Code + Tests + Pass + Review + Quality Gates ✓
  - Local test verification constitutionally equivalent to CI

- [x] **Article III**: Automated Local Enforcement
  - Zero manual overrides for quality standards
  - Multi-layer LOCAL enforcement (pre-commit, pre-push, agent validation)
  - Quality gates are absolute barriers
  - CI/CD is OPTIONAL (local gates sufficient)

- [x] **Article IV**: Continuous Learning and Improvement
  - VectorStore integration is constitutionally required
  - Agents MUST query learnings before decisions
  - Agents MUST store successful patterns after operations
  - Cross-session pattern recognition (institutional memory)

- [x] **Article V**: Spec-Driven Development
  - Complex features: spec.md → plan.md → TodoWrite tasks
  - This specification follows spec-kit methodology
  - Living document (will be updated during implementation)

- [x] **Article VI**: Red-Green-Refactor TDD Workflow
  - Tests written FIRST (must fail initially)
  - Implementation SECOND (iterate until 100% pass)
  - NO "pragmatic shortcuts" that skip RED phase
  - Validation confirms tests exist before implementation

- [x] **Article VII**: Value-First Testing Philosophy
  - Tests prioritize bug detection over coverage
  - Integration > Unit (behavior > implementation)
  - Prioritization matrix respects test value scores
  - P3 tests are Article VII deletion candidates

---

**End of Specification**

**Next Steps** (Article V workflow):
1. Await spec approval from Human Operator (@am)
2. Create technical plan: `plans/plan-027-test-validation-strategy.md`
3. Generate TodoWrite tasks from approved plan
4. Handoff to QualityEnforcer/CodingAgent for execution
5. Store learnings in VectorStore after 100% green validation
