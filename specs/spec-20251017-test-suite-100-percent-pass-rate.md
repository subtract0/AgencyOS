# Specification: Test Suite 100% Pass Rate Achievement

**ID**: SPEC-20251017-test-suite-100-percent
**Status**: Draft
**Created**: 2025-10-17
**Updated**: 2025-10-17
**Owner**: Agency OS Test Recovery Team
**Related**:
- ADR-001 (Complete Context Before Action)
- ADR-002 (100% Verification and Stability)
- ADR-023 (Memory-Aware Test Execution)
- Constitution Article VI (RED-GREEN-REFACTOR TDD)
- spec-test-suite-recovery-top-3-blockers.md
- missions/test_suite_100_percent_green.json

---

## Goals

### Primary Objectives

**GOAL-1: Achieve 100% Test Pass Rate**
- Current: 5,657/5,721 passing (98.9%)
- Target: 5,721/5,721 passing (100.0%)
- Zero failures, zero errors, zero worker crashes
- Success metric: `pytest --run-all` shows 100% pass rate

**GOAL-2: Fix Root Causes, Not Symptoms**
- NO test skipping or disabling
- NO lowering of performance thresholds
- NO workarounds or try/except pass patterns
- Fix implementation bugs, not test expectations

**GOAL-3: Constitutional Compliance**
- All fixes validate against Articles I-VI
- Article VI (TDD) HIGHEST PRIORITY: Tests written FIRST
- Article II: 100% verification - no broken windows
- Article I: Complete context - no incomplete test runs due to worker crashes

**GOAL-4: Maintain Performance**
- Total test runtime: <10 minutes (Article I - complete context mandate)
- Zero worker crashes during execution
- Memory-aware execution (Article II, ADR-023)
- Parallel execution efficiency maintained

**GOAL-5: Learning Integration**
- Store successful patterns in VectorStore (Article IV)
- Document architectural decisions as ADR
- Extract reusable test patterns for future use
- Cross-session learning from recovery process

---

## Non-Goals

**Explicitly OUT of scope:**

**NG-1: Test Coverage Expansion**
- This spec addresses EXISTING failing tests only
- New test creation deferred to separate missions
- Focus: Fix what's broken, not add new coverage

**NG-2: Performance Optimization Beyond Stability**
- Optimize slow tests ONLY if they cause timeouts
- Target: <10 min total runtime (met), not <5 min (stretch goal deferred)
- Rationale: Stability first, speed second

**NG-3: Test Infrastructure Refactoring**
- No pytest plugin changes
- No test framework migrations
- No major fixture refactors (only targeted fixes)
- Rationale: Minimize risk, maximize fix velocity

**NG-4: External Dependency Fixes**
- Ollama integration tests: Skip if Docker unavailable (legitimate skip)
- Firestore tests: Mock if backend unavailable
- GitHub API tests: Always mock (no real API calls in tests)
- Rationale: External dependencies don't block 100% pass rate

**NG-5: Documentation Updates**
- Test documentation updates deferred
- Focus: Make tests pass, document learnings in ADR after completion
- Exception: Critical architecture decisions documented during implementation

**Why These Are Non-Goals:**
Focus on surgical precision to fix 64 failing tests. Expanding scope risks introducing regressions and delays core objective. Performance optimization, infrastructure changes, and documentation are valuable but not critical blockers to 100% pass rate.

---

## Personas

### Persona 1: Autonomous Agent (Primary User)

**Context**: Agent executing `python run_tests.py --run-all` before PR creation
**Need**: 100% test pass rate to satisfy Article II (constitutional gate)
**Current Pain Point**:
- 64 failing tests block PR creation
- Worker crashes prevent complete test runs (Article I violation)
- Unclear failure categories make systematic fixing difficult
**Desired Outcome**:
- Single command execution: `python run_tests.py --run-all` → 100% green
- Zero worker crashes or hangs
- Clear feedback on any new failures
**Interaction Pattern**:
- Pre-commit hook calls test runner
- Test gate blocks commit if failures detected
- Agent queries VectorStore for fix patterns before implementation

### Persona 2: Developer/Contributor (Secondary User)

**Context**: Writing new feature code, running tests locally
**Need**: Fast feedback loop (<10 min), clear failure diagnostics
**Current Pain Point**:
- Worker crashes waste time (5 workers crashed recently)
- Unclear which of 64 failures are real vs. infrastructure issues
- Test runtime unpredictable (can hang indefinitely)
**Desired Outcome**:
- Deterministic test runs (same result every time)
- Clear failure messages pointing to root cause
- Fast iteration cycles
**Interaction Pattern**:
- `pytest tests/path/to/test.py` for targeted testing
- `python run_tests.py` for pre-commit validation
- Review test output to debug failures

### Persona 3: CI/CD Pipeline (System Administrator)

**Context**: GitHub Actions runner executing test suite on PR
**Need**: Reliable test results, predictable runtime, resource efficiency
**Current Pain Point**:
- Worker crashes fail CI without actionable error message
- Unpredictable test runtime (some runs hang >30 min)
- Flaky tests cause false negatives (reduce confidence)
**Desired Outcome**:
- Deterministic pass/fail status
- <10 min runtime for full suite
- Clear failure categorization for debugging
**Interaction Pattern**:
- Pull request trigger → run test suite → report results
- Block merge if tests fail
- Retry logic with exponential backoff (Article I compliance)

---

## Acceptance Criteria

### Functional Criteria (MUST HAVE)

**FC-01: 100% Test Pass Rate**
- Given: Clean checkout of main branch
- When: Execute `python run_tests.py --run-all`
- Then:
  - Output shows `5721 passed` (or final actual count)
  - Zero failures
  - Zero errors
  - Zero worker crashes
- Validation: Run 3 consecutive times, all show 100% pass rate

**FC-02: Worker Stability**
- Given: Full test suite execution
- When: Parallel test execution with N workers (memory-aware)
- Then:
  - Zero worker crashes during execution
  - All workers complete assigned tasks
  - No "maximum crashed workers reached" errors
- Validation: Monitor worker health during test run

**FC-03: Input Validation Coverage**
- Given: Unified PrimeA Orchestrator receives user intent
- When: Intent contains malicious or invalid input
- Then:
  - SQL injection attempts are sanitized
  - Command injection attempts are blocked
  - Intent length >10,000 chars rejected
  - Empty intent strings handled gracefully
  - Malformed JSON inputs rejected with clear error
- Validation: 5 security tests pass (NECESSARY Security pattern)

**FC-04: Missing Orchestrator Methods Implemented**
- Given: Test suite expects orchestrator methods
- When: Tests call `concurrent_validate_graphs()`, timeout handlers, retry logic
- Then:
  - Methods exist with correct signatures
  - Retry logic uses exponential backoff
  - Timeouts prevent indefinite hangs
  - Parallel validation achieves >1.3x speedup
- Validation: 3 orchestrator method tests pass

**FC-05: Performance Thresholds Met**
- Given: Performance-critical operations (constitutional validation, batch processing)
- When: Tests measure execution time
- Then:
  - Constitutional validator completes in <50ms
  - Batch operations achieve >1.3x speedup over sequential
  - 10k operation stress tests complete without memory exhaustion
  - Model storage thread safety tests complete without deadlocks
- Validation: 15+ performance tests pass

**FC-06: Test Fixtures Available**
- Given: Tests require ML model fixtures
- When: Tests load `models/routing_classifier_latest.pkl` and related files
- Then:
  - Fixture files exist or are mocked appropriately
  - PredictionLog schemas validate correctly
  - ML model files are lightweight (<5MB total)
- Validation: 10+ fixture-dependent tests pass

**FC-07: Test Infrastructure Resilience**
- Given: Test execution encounters edge cases
- When: Tests handle long lines, git mock interference, Ollama health checks
- Then:
  - Regex parsing handles lines >10KB without backtracking
  - Git mocks don't interfere with real operations
  - Ollama health checks retry with exponential backoff
  - Thread joins have timeouts (prevent hangs)
- Validation: All remaining infrastructure tests pass

### Non-Functional Criteria (MUST HAVE)

**NF-01: Performance - Total Runtime**
- Target: <10 minutes for full suite (Article I - complete context mandate)
- Measurement: `time python run_tests.py --run-all`
- Acceptance: 95th percentile <600 seconds

**NF-02: Reliability - Deterministic Results**
- Target: 100% consistency across 10 consecutive runs
- Measurement: Run suite 10 times, count pass rate variations
- Acceptance: All 10 runs show identical pass/fail status per test

**NF-03: Security - No Vulnerabilities in Tests**
- All SQL injection test cases pass (5 tests)
- All command injection test cases pass (3 tests)
- All path traversal test cases pass (2 tests)
- Acceptance: NECESSARY Security pattern validated (10 tests)

**NF-04: Type Safety - 100% Type Coverage**
- No `Any` types in test fixtures (except where required by mocking)
- All Pydantic models use strict typing
- All function signatures have type annotations
- Acceptance: `mypy tests/` runs clean (zero errors)

**NF-05: Scalability - Memory-Aware Execution**
- Tests dynamically adjust worker count based on available memory (ADR-023)
- No kernel panics or OOM errors during test execution
- Total memory usage <40GB (85% of 48GB M4 Pro)
- Acceptance: `tools/memory_aware_test_runner.py` validates memory safety

**NF-06: Error Handling - Result Pattern Compliance**
- All test utilities use `Result<T, E>` pattern
- No bare `try/except` for control flow in tests
- All errors are typed and documented
- Acceptance: Constitutional compliance check passes

### Quality Criteria (Constitutional Compliance - MUST HAVE)

**QC-01: Article I Compliance - Complete Context**
- All tests run to completion (no timeouts without retry)
- Worker crashes trigger retry with 2x, 3x, 10x timeout (max)
- No partial test results (all or nothing)
- Acceptance: Zero incomplete test runs

**QC-02: Article II Compliance - 100% Verification**
- Main branch shows 100% test pass rate (target: 5721/5721)
- No test skips except legitimate external dependencies
- Tests verify REAL functionality (not mocked behavior)
- Acceptance: "Delete the Fire First" priority validated

**QC-03: Article III Compliance - Automated Enforcement**
- Pre-commit hook blocks commits with failing tests
- CI pipeline enforces 100% pass rate
- No manual override mechanisms
- Acceptance: Quality gates enforce test pass requirement

**QC-04: Article IV Compliance - Continuous Learning**
- VectorStore queried for similar test fix patterns before implementation
- Successful fix patterns stored after validation
- Cross-session learning applied (min confidence 0.6)
- Acceptance: `agent-memory-store` called for each fix category

**QC-05: Article V Compliance - Spec-Driven Development**
- This specification traces to implementation plan
- All fixes reference acceptance criteria
- Implementation tasks decomposed from spec
- Acceptance: Plan references spec sections explicitly

**QC-06: Article VI Compliance - TDD Workflow**
- All new tests written FIRST (RED phase documented)
- Implementation written SECOND (GREEN phase validated)
- 100% test pass rate achieved before refactoring
- Acceptance: Git history shows test commits BEFORE implementation commits

**QC-07: Code Quality - Zero Linting Errors**
- All test files pass `ruff check tests/`
- Functions <50 lines (Constitutional Law #8)
- Clear test names documenting expected behavior
- Acceptance: Linting pipeline passes

**QC-08: Documentation - Test Intent Clear**
- All tests have docstrings explaining purpose
- Failure messages point to acceptance criteria
- NECESSARY pattern coverage documented per test
- Acceptance: Code review passes documentation check

**QC-09: Test Coverage - NECESSARY Pattern Validated**
- Normal operation tests (happy path)
- Edge case tests (boundaries, limits)
- Error condition tests (invalid inputs, failures)
- Security tests (injection, auth bypass)
- Stress tests (performance, concurrency)
- Acceptance: All 5 NECESSARY categories have tests

**QC-10: Zero Broken Windows**
- No `@pytest.mark.xfail` (except known external issues)
- No commented-out assertions
- No `# TODO: fix this test`
- Acceptance: Broken window audit passes

---

## Functional Requirements

### FR-01: Input Validation Layer (Priority: Critical)

**Description**: Implement comprehensive input validation for Unified PrimeA Orchestrator
**Priority**: Critical
**Complexity**: Medium

**Details**:
- **Behavior 1**: SQL injection sanitization using parameterized queries or input escaping
- **Behavior 2**: Intent length validation (max 10,000 characters)
- **Behavior 3**: Empty intent string rejection with clear error message
- **Behavior 4**: Malformed JSON input validation with schema enforcement
- **Behavior 5**: Command injection protection (shell metacharacter filtering)
- **Constraint**: All validation must complete in <10ms (no performance impact)

**Test Strategy**:
- NECESSARY Security pattern: 5 tests (SQL injection, command injection, length limit, empty input, malformed JSON)
- Performance test: Validation latency <10ms
- Integration test: Valid inputs pass through unchanged

**Files**:
- Implementation: `tools/orchestrator/unified_primea_orchestrator.py`
- Tests: `tests/orchestrator/test_unified_primea_orchestrator.py`

---

### FR-02: Concurrent Graph Validation (Priority: High)

**Description**: Implement parallel graph validation with performance improvements
**Priority**: High
**Complexity**: Medium

**Details**:
- **Behavior 1**: `concurrent_validate_graphs()` method validates multiple graphs in parallel
- **Behavior 2**: Achieves >1.3x speedup over sequential validation
- **Behavior 3**: Thread-safe operation (no race conditions)
- **Behavior 4**: Graceful handling of validation failures (partial success)
- **Constraint**: Max concurrency limited by available CPU cores (14 on M4 Pro)

**Test Strategy**:
- Unit test: `concurrent_validate_graphs()` validates 5 graphs in parallel
- Performance test: Measure speedup ratio (target: >1.3x)
- Concurrency test: 100 graphs validated without race conditions
- Edge case: Empty graph list, single graph, invalid graphs

**Files**:
- Implementation: `tools/orchestrator/unified_primea_orchestrator.py`
- Tests: `tests/orchestrator/test_unified_primea_orchestrator.py`

---

### FR-03: Retry Logic with Exponential Backoff (Priority: High)

**Description**: Implement Article I-compliant retry protocol for transient failures
**Priority**: High
**Complexity**: Low

**Details**:
- **Behavior 1**: Retry failed operations with exponential backoff (1s, 2s, 4s, 8s)
- **Behavior 2**: Max retry attempts: 3 (total 4 attempts including initial)
- **Behavior 3**: Timeout doubling: 120s → 240s → 480s → 960s (10x max per Article I)
- **Behavior 4**: Clear logging of retry attempts for debugging
- **Constraint**: Total retry time <15 minutes (prevents indefinite hangs)

**Test Strategy**:
- Unit test: Verify exponential backoff timing
- Integration test: Simulate transient failures (3 retries succeed)
- Timeout test: Verify max timeout is 10x initial (Article I)
- Failure test: Verify graceful failure after max retries

**Files**:
- Implementation: `shared/retry_controller.py` (reuse existing)
- Tests: `tests/unit/shared/test_retry_controller.py`

---

### FR-04: Performance Optimization - Constitutional Validator (Priority: High)

**Description**: Optimize constitutional validator to meet <50ms latency target
**Priority**: High
**Complexity**: High

**Details**:
- **Behavior 1**: Validator completes all 5 article checks in <50ms (P95)
- **Behavior 2**: Early exit on first failure (short-circuit evaluation)
- **Behavior 3**: Caching of validation results for repeated checks
- **Behavior 4**: Profiling instrumentation to identify bottlenecks
- **Constraint**: No reduction in validation thoroughness

**Test Strategy**:
- Performance test: 1000 validations, P95 latency <50ms
- Correctness test: Caching doesn't hide validation failures
- Stress test: 10k validations complete without memory growth
- Regression test: All existing validation tests still pass

**Files**:
- Implementation: `tools/orchestrator/constitutional_validator.py`
- Tests: `tests/orchestrator/test_constitutional_validator.py`

---

### FR-05: Batch Operation Speedup (Priority: Medium)

**Description**: Optimize batch operations for >1.3x speedup over sequential execution
**Priority**: Medium
**Complexity**: Medium

**Details**:
- **Behavior 1**: Batch operations use `asyncio.gather()` for parallelism
- **Behavior 2**: Achieves >1.3x speedup for batches of 10+ items
- **Behavior 3**: Memory-efficient (no exponential memory growth)
- **Behavior 4**: Graceful degradation for small batches (overhead not worth parallelism)
- **Constraint**: Memory usage increases linearly, not exponentially

**Test Strategy**:
- Performance test: 100-item batch, measure speedup ratio
- Memory test: 10k-item batch, memory usage <1GB
- Edge case: Single-item batch (no crash), empty batch
- Integration test: Real-world batch operations (model predictions)

**Files**:
- Implementation: Various (model storage, training data merger, etc.)
- Tests: `tests/test_model_storage.py`, `tests/test_training_data_merger.py`

---

### FR-06: Test Fixture Generation (Priority: High)

**Description**: Create or mock missing ML model fixtures for test execution
**Priority**: High
**Complexity**: Low

**Details**:
- **Behavior 1**: `models/routing_classifier_latest.pkl` available (real or mock)
- **Behavior 2**: PredictionLog validation schemas up-to-date
- **Behavior 3**: Lightweight fixtures (<5MB total) for fast test execution
- **Behavior 4**: Mock models return deterministic predictions
- **Constraint**: Fixtures committed to git or generated via conftest.py

**Test Strategy**:
- Unit test: Fixture loading succeeds
- Integration test: Model predictions work with fixtures
- Size test: Fixtures <5MB total
- Determinism test: Same input → same output across runs

**Files**:
- Fixtures: `tests/fixtures/ml_models/` or `tests/conftest.py`
- Tests: `tests/test_model_trainer.py`, `tests/test_ml_classifier_performance.py`

---

### FR-07: Regex Backtracking Fix (Priority: Critical)

**Description**: Fix catastrophic regex backtracking in error parser causing worker crashes
**Priority**: Critical (blocks test completion)
**Complexity**: Low

**Details**:
- **Behavior 1**: Add line length limit (5,000 chars) before regex parsing
- **Behavior 2**: Use non-greedy regex patterns (`.*?` instead of `.*`)
- **Behavior 3**: Clear error message for rejected long lines
- **Behavior 4**: No performance regression on normal lines (<1000 chars)
- **Constraint**: Must handle logs with 10KB+ single lines gracefully

**Test Strategy**:
- Edge case: 10KB single line (no crash, clear error)
- Normal case: 100-char line (same behavior as before)
- Performance: 10k normal lines parse in <1 second
- Regression: Existing error parser tests still pass

**Files**:
- Implementation: `tools/ci_monitor/code_error_parser.py`
- Tests: `tests/tools/ci_monitor/test_error_parser.py`

---

### FR-08: Thread Timeout Enforcement (Priority: Medium)

**Description**: Add timeouts to all `thread.join()` calls to prevent hangs
**Priority**: Medium
**Complexity**: Low

**Details**:
- **Behavior 1**: All `thread.join()` calls use `timeout=5` (5 seconds)
- **Behavior 2**: Assert `not thread.is_alive()` after join timeout
- **Behavior 3**: Clear error message if thread doesn't terminate
- **Behavior 4**: Background thread cleanup on timeout
- **Constraint**: 5-second timeout sufficient for all test threads

**Test Strategy**:
- Unit test: Thread joins within timeout (normal case)
- Timeout test: Thread doesn't join, error raised
- Cleanup test: Background threads cleaned up properly
- Regression: Existing thread tests still pass

**Files**:
- Implementation: Multiple test files (`tests/test_model_storage.py`, `tests/test_memory_facade.py`, etc.)
- Pattern: Global search-and-replace for `thread.join()`

---

### FR-09: E2E Test PR Description Format (Priority: Medium)

**Description**: Fix E2E test failure for PR description format validation
**Priority**: Medium
**Complexity**: Low

**Details**:
- **Behavior 1**: PR description includes mission intent summary
- **Behavior 2**: PR description includes task graph visualization (Mermaid)
- **Behavior 3**: PR description includes constitutional compliance checklist
- **Behavior 4**: Format matches expected template exactly
- **Constraint**: Template defined in spec, tests validate format

**Test Strategy**:
- E2E test: Generate PR description, validate format
- Regression test: Existing PR format tests still pass
- Edge case: Empty graph, large graph (100+ tasks)

**Files**:
- Implementation: `tools/orchestrator/pr_creator.py` (likely)
- Tests: `tests/foundation_automation/test_e2e_natural_language_flow.py`

---

### FR-10: Git Mock Isolation (Priority: Medium)

**Description**: Prevent git mocks from interfering with real git operations
**Priority**: Medium
**Complexity**: Medium

**Details**:
- **Behavior 1**: Git mocks scoped to test function only (no global state)
- **Behavior 2**: Mock cleanup in `teardown()` or fixture finalizer
- **Behavior 3**: Real git operations in other tests unaffected
- **Behavior 4**: Clear error if mock leaks to other tests
- **Constraint**: Use `pytest-mock` for automatic cleanup

**Test Strategy**:
- Isolation test: Run git mock test + real git test, both pass
- Cleanup test: Mock state doesn't persist across tests
- Regression: All git validation tests still pass

**Files**:
- Implementation: Multiple test files with git mocks
- Pattern: Use `mocker` fixture instead of `@patch` decorator

---

## Non-Functional Requirements

### NFR-01: Performance - Test Runtime

**Target**: <10 minutes for full suite (5,721 tests)
**Measurement**: `time python run_tests.py --run-all | grep real`
**Acceptance**: 95th percentile <600 seconds (10 minutes)

**Details**:
- Parallel execution with memory-aware worker count (3-10 workers based on available RAM)
- No single test >60 seconds (except legitimately slow E2E tests marked with `@pytest.mark.slow`)
- Fast failure detection (fail fast, don't wait for all tests)

**Test Strategy**:
- Measure total runtime on clean checkout
- Identify slowest 20 tests with `--durations=20`
- Optimize tests with `time.sleep()` >1 second

---

### NFR-02: Security - Input Validation

**Target**: All NECESSARY Security pattern tests pass (10 tests)
**Measurement**: `pytest tests/ -k security -v`
**Acceptance**: 10/10 security tests pass

**Details**:
- SQL injection tests (3 tests)
- Command injection tests (3 tests)
- Path traversal tests (2 tests)
- XSS prevention tests (2 tests)

**Test Strategy**: Security-focused NECESSARY pattern validation

---

### NFR-03: Type Safety - Strict Typing

**Target**: Zero `Any` types in production code (tests can use `Any` for mocking)
**Measurement**: `mypy tests/ --strict`
**Acceptance**: Zero mypy errors

**Details**:
- All Pydantic models use strict typing (no `Dict[Any, Any]`)
- All function signatures have type annotations
- All test fixtures have type hints

**Test Strategy**: Pre-commit hook runs mypy validation

---

### NFR-04: Error Handling - Result Pattern

**Target**: All errors use `Result<T, E>` pattern (Constitutional Law #5)
**Measurement**: Grep for `try/except` in production code, validate Result usage
**Acceptance**: Zero bare exceptions for control flow

**Details**:
- All orchestrator methods return `Result<Success, Error>`
- All errors are typed (Pydantic models)
- Clear error messages point to root cause

**Test Strategy**: Code review validates Result pattern usage

---

### NFR-05: Memory Safety - No OOM Errors

**Target**: Total memory usage <40GB (85% of 48GB M4 Pro)
**Measurement**: `tools/memory_aware_test_runner.py` dynamic worker adjustment
**Acceptance**: Zero kernel panics, zero OOM errors

**Details**:
- Memory-aware worker count: 3 workers if local model active, 10 workers otherwise
- Dynamic fallback to sequential execution if memory pressure detected
- Clear logging of memory state during test runs

**Test Strategy**: Monitor memory usage with `psutil` during full test run

---

## Dependencies

### Internal Dependencies

**SPEC-test-suite-recovery-top-3-blockers** (Prerequisite)
- Fix TaskGraph TDD validation (24 tests)
- Enable two-stage orchestrator tests (13 tests)
- Fix Pydantic validation errors (19 tests)
- Rationale: These 56 tests block systematic fixing of remaining 64 tests

**ADR-023** (Memory-Aware Test Execution)
- Dynamic worker count adjustment based on available memory
- Integration: `tools/memory_aware_test_runner.py`
- Impact: Prevents worker crashes due to memory exhaustion

**ADR-001** (Complete Context Before Action)
- Retry protocol: 2x, 3x, up to 10x timeout
- Integration: `shared/retry_controller.py`
- Impact: All tests run to completion (no partial results)

**ADR-002** (100% Verification and Stability)
- Test pass rate mandate: 100% (no exceptions)
- Integration: Pre-commit hook blocks failing tests
- Impact: Quality gate enforcement

### External Dependencies

**Docker** (Optional - Ollama Integration Tests)
- Version: Docker Desktop 4.x+
- Purpose: Run Ollama container for 140 integration tests
- Impact: Without Docker, 140 tests legitimately skipped
- Mitigation: Tests run in CI with Docker, local execution can skip

**pytest-xdist** (Required - Parallel Execution)
- Version: >=3.3.1
- Purpose: Parallel test execution with `-n` flag
- Impact: Without pytest-xdist, tests run sequentially (slower)
- Mitigation: Install via `uv pip install pytest-xdist`

**psutil** (Required - Memory Monitoring)
- Version: >=5.9.0
- Purpose: Memory-aware worker count adjustment
- Impact: Without psutil, worker count fixed (risk of OOM)
- Mitigation: Install via `uv pip install psutil`

**Pydantic V2** (Required - Validation)
- Version: >=2.0.0
- Purpose: Type-safe data validation
- Impact: Pydantic V1 patterns deprecated (26 warnings)
- Mitigation: Update `.dict()` → `.model_dump()`, `.parse_obj()` → `.model_validate()`

### Dependency Impact Analysis

**Breaking Changes**:
- Pydantic V1 → V2 migration (26 deprecation warnings)
- Git mock cleanup (potential interference with real git operations)
- Constitutional validator optimization (API unchanged, but implementation refactored)

**Integration Points**:
- Pre-commit hook calls `python run_tests.py` (must remain compatible)
- CI pipeline uses `pytest --run-all` (must support same flags)
- VectorStore queries for test fix patterns (Article IV integration)

**Migration Path**:
- Phase 1: Fix critical blockers (worker crashes, regex backtracking)
- Phase 2: Fix systematic failures (input validation, missing methods)
- Phase 3: Optimize performance (constitutional validator, batch operations)
- Phase 4: Validate and document (100% pass rate, ADR creation)

---

## Risks and Mitigations

| ID   | Risk                                     | Impact | Probability | Mitigation Strategy                                                                 | Owner           |
| ---- | ---------------------------------------- | ------ | ----------- | ----------------------------------------------------------------------------------- | --------------- |
| R-01 | Worker crashes prevent test completion   | High   | High        | Fix regex backtracking (FR-07), add thread timeouts (FR-08), memory-aware workers  | CodeAgent       |
| R-02 | Performance regressions from fixes       | Medium | Medium      | Benchmark before/after, validate <10 min target, profile with `--durations=20`      | TestGenerator   |
| R-03 | Pydantic V2 migration breaks tests       | Medium | Medium      | Gradual migration, validate each change, regression tests for all models            | CodeAgent       |
| R-04 | Git mocks interfere with real operations | Medium | Low         | Isolate mocks to test function scope, use `pytest-mock` for auto cleanup           | TestGenerator   |
| R-05 | Fixing one test breaks another           | High   | Medium      | Run full suite after each fix, use TodoWrite to track progress, incremental commits | QualityEnforcer |
| R-06 | External dependencies unavailable        | Low    | Medium      | Mock external services (GitHub API, Ollama), skip if Docker unavailable            | CodeAgent       |
| R-07 | Constitutional compliance violations     | High   | Low         | Validate against all 6 articles before commit, VectorStore query for patterns       | QualityEnforcer |
| R-08 | Memory exhaustion during test runs       | High   | Medium      | Memory-aware worker adjustment (ADR-023), monitor with `psutil`, fallback to seq    | TestGenerator   |

### Risk Mitigation Plan

**High-Risk Items (Impact: High, Probability: Medium/High):**

**R-01: Worker Crashes (CRITICAL)**
- **Detailed Mitigation**:
  1. Fix regex backtracking in error parser (5,000 char line limit)
  2. Add timeouts to all `thread.join()` calls (5-second max)
  3. Memory-aware worker count (3-10 workers based on available RAM)
  4. Retry logic with exponential backoff (2x, 3x, 10x timeout)
- **Contingency Plan**: If worker crashes persist, run tests sequentially with `pytest -n 1`
- **Early Warning**: Monitor worker health with `pytest --verbose --log-cli-level=DEBUG`

**R-05: Fixing One Test Breaks Another (CROSS-CONTAMINATION)**
- **Detailed Mitigation**:
  1. Run full suite after each fix (validate no regressions)
  2. Use TodoWrite to track progress (mark tests fixed, identify dependencies)
  3. Incremental commits (one fix category per commit, easy rollback)
  4. Git bisect if regression detected (identify culprit commit)
- **Contingency Plan**: Revert problematic commit, analyze failure, apply more surgical fix
- **Early Warning**: Automated regression detection in CI (compare pass rate before/after)

**R-08: Memory Exhaustion (OOM KILLER)**
- **Detailed Mitigation**:
  1. Memory-aware worker adjustment (ADR-023): 3 workers if local model active, 10 otherwise
  2. Monitor memory with `psutil.virtual_memory()` (log warnings at 80% usage)
  3. Fallback to sequential execution if memory pressure detected
  4. Docker memory limits (40GB cap for Ollama container)
- **Contingency Plan**: If OOM occurs, reduce worker count to 1, disable local model, retry
- **Early Warning**: Memory usage logs in test output, `docker stats` monitoring

---

## Edge Cases and Error Scenarios

### Edge Case 1: Empty Test Suite

**Scenario**: Test discovery finds zero tests (e.g., all tests skipped)
**Expected Behavior**: Error message "No tests collected", exit code 5 (pytest convention)
**Test Case**: `pytest tests/nonexistent/` should fail with clear message
**Handling**: Pre-commit hook validates >5,000 tests collected before running

### Edge Case 2: All Workers Crash Simultaneously

**Scenario**: Memory exhaustion causes all 10 workers to crash at once
**Expected Behavior**: Graceful fallback to sequential execution, retry with 1 worker
**Test Case**: Simulate OOM condition, verify fallback mechanism
**Handling**: `memory_aware_test_runner.py` detects crash, reduces worker count, retries

### Edge Case 3: Circular Test Dependencies

**Scenario**: Test A mocks module B, Test B mocks module A, both run in parallel
**Expected Behavior**: Pytest isolation prevents cross-contamination, both tests pass
**Test Case**: Create mock collision scenario, validate isolation
**Handling**: Use `pytest-mock` with function scope (auto cleanup)

### Error Scenario 1: Regex Catastrophic Backtracking

**Trigger**: Error parser receives 10KB+ single line with many special characters
**Error Response**: `LineTooLongError` (typed error with line length)
**User Experience**: Clear error "Line exceeds 5,000 character limit, skipping"
**Recovery**: Skip long lines, continue parsing remaining log

### Error Scenario 2: Worker Crash During Test Execution

**Trigger**: Memory exhaustion, timeout, or segfault in worker process
**Error Response**: `WorkerCrashError` (typed error with worker ID, last test)
**User Experience**: "Worker gw3 crashed during test_xyz, retrying with fewer workers"
**Recovery**: Reduce worker count by 1, retry failed tests, log crash details

### Error Scenario 3: Test Timeout Without Retry

**Trigger**: Single test hangs indefinitely (e.g., thread doesn't join)
**Error Response**: `TimeoutError` after 60 seconds (default pytest timeout)
**User Experience**: "Test test_xyz exceeded 60s timeout, aborting"
**Recovery**: Kill test process, mark as failed, continue with remaining tests

### Error Scenario 4: Pydantic Validation Error

**Trigger**: Test fixture missing required field (e.g., `agent`, `description`)
**Error Response**: `ValidationError` with field name and constraint
**User Experience**: "Pydantic validation failed: Field 'agent' is required"
**Recovery**: Update fixture to include required field, rerun tests

### Error Scenario 5: Git Mock Leak

**Trigger**: Git mock not cleaned up after test, interferes with real git operations
**Error Response**: `GitMockLeakError` (custom error from conftest.py)
**User Experience**: "Git mock from test_xyz leaked to test_abc, aborting"
**Recovery**: Isolate mocks with `pytest-mock`, add cleanup in `teardown()`

---

## Performance Requirements

### Latency Targets

**P50**: <5 minutes for full test suite (50th percentile - median case)
**P95**: <10 minutes for full test suite (95th percentile - including slow tests)
**P99**: <15 minutes for full test suite (99th percentile - worst case, includes retries)

### Throughput Targets

**Tests/Second**: >10 tests/second average (5,721 tests in <600 seconds)
**Concurrent Workers**: 3-10 workers (memory-aware adjustment based on available RAM)

### Resource Constraints

**Memory**: <40GB total usage (85% of 48GB M4 Pro, 5GB safety margin)
- Breakdown: 19GB local model + 16GB KV cache + 9GB tests (3 workers) + 5GB safety = 49GB (over budget)
- Mitigation: If local model active, reduce to 3 workers (9GB) → total 44GB (safe)
- Mitigation: If local model inactive, use 10 workers (30GB) → total 30GB (safe)

**CPU**: <100% average utilization (burst to 200% acceptable, M4 Pro has 14 cores)
- Parallel test execution spreads load across cores
- No single test should consume >10% CPU for >10 seconds

**Storage**: <5MB total for test fixtures (ML models, mock data)
- Fixtures stored in `tests/fixtures/` or generated via `conftest.py`
- No large binary files committed to git

**Network**: Zero external API calls in tests (all mocked)
- GitHub API mocked with `subprocess.run` patches
- Ollama API mocked or run in Docker (no external network)

---

## Security Considerations

### Authentication & Authorization

**Auth Mechanism**: Tests do NOT require authentication (all mocked)
**Permission Model**: Tests run with user's filesystem permissions (no elevated privileges)
**Token Management**: GitHub tokens NEVER used in tests (mock all gh CLI commands)

### Input Validation (Constitutional Law #3)

**Validation Layer**: Pydantic models for all test fixtures, orchestrator inputs
**Sanitization**: SQL injection, command injection, path traversal prevention
**Rate Limiting**: Not applicable (tests don't make external requests)

**Details**:
- SQL injection tests validate parameterized queries
- Command injection tests validate shell metacharacter filtering
- Path traversal tests validate `Path(...).resolve()` usage
- XSS tests validate HTML escaping (if applicable)

### Data Protection

**Encryption**: Not applicable (tests use mock data, no real user data)
**PII Handling**: No PII in tests (all data synthetic or anonymized)
**Audit Logging**: Test execution logged to `logs/test_runs/`, includes pass/fail status

**Details**:
- Test logs stored locally, never sent to external services
- No secrets or credentials in test code (use environment variables or mocks)
- Git hooks prevent accidental commit of secrets

---

## Testing Strategy

### Unit Tests (TDD - Law #1)

**Coverage Target**: >95% for all production code
**Test Framework**: pytest (Python)
**Patterns**: AAA (Arrange-Act-Assert)
**Mocking**: Use `pytest-mock` for automatic cleanup

**Details**:
- Each unit test validates one behavior
- Tests run in <1 second each (fast feedback)
- No external dependencies (all mocked)

### Integration Tests

**Scope**: Test interactions between orchestrator, agents, VectorStore
**Environment**: Local filesystem, mock GitHub API, Docker Ollama (optional)
**Data**: Synthetic test graphs, mock model fixtures

**Details**:
- Integration tests validate end-to-end workflows
- Tests may take 5-30 seconds (acceptable)
- Use `@pytest.mark.integration` marker

### End-to-End Tests

**User Flows**:
- Intent → Spec → Tests → Code → PR (full autonomous cycle)
- Git validation → Constitutional compliance → Merge enforcement

**Details**:
- E2E tests validate constitutional compliance
- Tests may take 30-60 seconds (acceptable)
- Use `@pytest.mark.e2e` marker

### NECESSARY Pattern (Comprehensive Coverage)

**N**ormal operation tests (happy path) - 50% of tests
**E**dge case tests (boundaries, limits) - 20% of tests
**C**orner case tests (unusual combinations) - 5% of tests
**E**rror condition tests (invalid inputs, failures) - 15% of tests
**S**ecurity tests (injection, auth bypass) - 5% of tests
**S**tress/performance tests (load, concurrency) - 3% of tests
**A**ccessibility tests (if user-facing) - N/A (no UI)
**R**egression tests (prevent past bugs) - 2% of tests
**Y**ield (output validation) tests - Included in Normal tests

**Total**: 5,721 tests covering all NECESSARY categories

---

## Documentation Requirements

### User Documentation

- [ ] README.md updated with test execution instructions
- [ ] FAQ section for common test failures
- [ ] Troubleshooting guide for worker crashes

### Developer Documentation

- [ ] ADR documenting test suite recovery process
- [ ] Code comments explaining fix rationale
- [ ] VectorStore patterns stored for future reference

### Operational Documentation

- [ ] CI/CD pipeline configuration documented
- [ ] Memory-aware test execution guide
- [ ] Monitoring and alerting setup for test failures

---

## Implementation Guidance

### Recommended Approach

**Phase 1: Critical Blockers (Estimated: 4 hours)**
1. Fix regex backtracking in error parser (FR-07) - 1 hour
2. Add thread timeouts to prevent hangs (FR-08) - 1 hour
3. Fix worker crash scenarios - 2 hours

**Phase 2: Systematic Fixes (Estimated: 8 hours)**
1. Implement input validation layer (FR-01) - 2 hours
2. Implement concurrent graph validation (FR-02) - 2 hours
3. Implement retry logic with exponential backoff (FR-03) - 1 hour
4. Create/mock missing test fixtures (FR-06) - 1 hour
5. Fix Pydantic V2 migration issues - 2 hours

**Phase 3: Performance Optimization (Estimated: 6 hours)**
1. Optimize constitutional validator (FR-04) - 3 hours
2. Optimize batch operations (FR-05) - 2 hours
3. Profile and optimize slow tests - 1 hour

**Phase 4: Quality & Documentation (Estimated: 4 hours)**
1. Validate 100% pass rate (run full suite 10x) - 1 hour
2. Create ADR documenting recovery process - 2 hours
3. Store successful patterns in VectorStore (Article IV) - 1 hour

**Total Estimated Time**: 22 hours (3 business days with focus)

### Key Design Decisions

**Architecture Pattern**: Memory-aware test execution (ADR-023)
- Dynamic worker count based on available memory
- Graceful fallback to sequential execution on memory pressure

**Error Handling**: Result<T, E> pattern (Constitutional Law #5)
- All test utilities return `Result<Success, Error>`
- Typed errors for clear failure diagnosis

**Type Safety**: Pydantic models (Constitutional Law #2)
- All test fixtures use strict Pydantic models
- No `Dict[Any, Any]` or bare `any` types

**Validation**: Input validation at orchestrator boundary (Law #3)
- SQL injection, command injection, path traversal prevention
- Pydantic schemas enforce input constraints

### Constitutional Compliance Checklist

- [x] **Article I**: Complete context gathered via test suite analysis
- [x] **Article II**: 100% test success rate target (5,721/5,721)
- [x] **Article III**: Automated merge enforcement configured (pre-commit hook)
- [x] **Article IV**: VectorStore learnings queried/stored (test fix patterns)
- [x] **Article V**: Spec-driven development followed (this spec → plan → implementation)
- [x] **Article VI**: TDD workflow enforced (tests written FIRST, implementation SECOND)

---

## References

### Related Specifications

**spec-test-suite-recovery-top-3-blockers.md** - Prerequisite fixes (56 tests)
- TaskGraph TDD validation (24 tests)
- Two-stage orchestrator enablement (13 tests)
- Pydantic fixture updates (19 tests)

**spec-test-suite-recovery-38-failures.md** - Previous recovery attempt
- Patterns to reuse from prior analysis
- Lessons learned from incremental fixing

**spec-030-foundation-automation-test-coverage.md** - E2E test coverage
- NECESSARY pattern examples
- Constitutional compliance validation

### Architecture Decision Records

**ADR-001: Complete Context Before Action**
- Retry protocol: 2x, 3x, up to 10x timeout
- No partial test results

**ADR-002: 100% Verification and Stability**
- Test pass rate mandate: 100%
- No broken windows tolerance

**ADR-023: Memory-Aware Test Execution**
- Dynamic worker count adjustment
- Prevents kernel panics and OOM errors

**ADR-026: Test-Driven Autonomy (Leap 7)**
- TDD protocol: Tests FIRST, code SECOND
- NECESSARY pattern validation

### External Documentation

**pytest Documentation** - https://docs.pytest.org/
- Parallel execution with pytest-xdist
- Fixture patterns and best practices

**Pydantic V2 Migration Guide** - https://docs.pydantic.dev/latest/migration/
- `.dict()` → `.model_dump()`
- `.parse_obj()` → `.model_validate()`

**Memory-Aware Testing Best Practices**
- `psutil` documentation for memory monitoring
- Strategies for preventing OOM in test suites

---

## Approval and Sign-Off

**Created By**: SpecGenerator Agent (Constitutional Article V compliance)
**Reviewed By**: Planner, ChiefArchitect
**Approved By**: User/Product Owner

**Approval Criteria**:
- [x] All sections complete
- [x] Acceptance criteria verifiable (100% pass rate measurable)
- [x] Risks identified and mitigated (8 risks with mitigation strategies)
- [x] Constitutional compliance validated (Articles I-VI referenced)
- [x] Stakeholder agreement on scope (64 failing tests → 0)

**Approval Date**: {PENDING USER APPROVAL}
**Approver Signature**: {User/Product Owner}

---

**Living Document**: This specification will be updated during implementation to reflect learnings and refinements. All changes will be tracked in git history.

---

**Success Definition**:
```bash
python run_tests.py --run-all
# Output: 5721 passed in 8.5 minutes
# Zero failures, zero errors, zero worker crashes
# Constitutional compliance: 100%
```

🎯 **Target**: 100% test pass rate (5,721/5,721)
🚀 **Impact**: Unblocks autonomous PR creation, validates Article II compliance
⏱️ **Timeline**: 3 business days (22 hours focused work)
💰 **Cost**: ~$12 (75,000 tokens × $4/1M for gpt-5 orchestration + $3 for Tier 2 agents)

---

**Constitutional Mandate**: This specification traces to all 6 constitutional articles and enforces TDD workflow (Article VI - HIGHEST PRIORITY).

*"In automation we trust, in discipline we excel, in learning we evolve, in autonomy we persist."*
