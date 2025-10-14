# Test Failure Inventory
**Date**: 2025-10-14
**Total Tests Collected**: 5,545 tests (excluding firestore, e2e, vectorstore_performance, checkpoint_manager)
**Test Run Status**: Incomplete (hangs at ~29% completion, multiple timeouts at 10-minute mark)
**Analysis Method**: Sequential test execution with --tb=no flag, multiple retry attempts

## Executive Summary

### Test Suite Health
- **Passing Tests (0-29%)**: ~1,600 tests (estimated from 29% progress)
- **Failing Tests (Known)**: 4 confirmed assertion failures
- **Hanging Tests**: 3 confirmed (test_checkpoint_manager.py, test_vectorstore_performance.py, unknown test at 29% mark)
- **Skipped Tests**: 44+ integration tests (Ollama, firestore-dependent)
- **Root Cause Issues**:
  1. **pytest-rerunfailures plugin incompatibility** with Python 3.13 (causes segfault)
  2. **Resource accumulation** causing hangs after ~1,600 tests
  3. **Async/networking test leaks** (sockets, connections not properly closed)

### Blocker Issues (P0)
1. **Test suite hangs at 29% completion** - prevents full inventory collection
2. **pytest-rerunfailures segfault** - identified in previous analysis (ADR-030)
3. **test_checkpoint_manager.py** - hangs at test 9/20
4. **test_vectorstore_performance.py** - hangs after 2 tests

---

## Category 1: HANG (Timeout) - **P0 BLOCKERS**

These tests prevent the full suite from completing and must be fixed first.

### test_vectorstore_performance.py
- **Status**: HANG
- **Location**: tests/benchmarks/test_vectorstore_performance.py
- **Symptoms**: Hangs after completing 2 tests, no output
- **Impact**: Blocks benchmark test category
- **Root Cause**: Likely VectorStore resource cleanup issue (torch tensors, embeddings not released)
- **Recommended Fix**:
  - Add explicit cleanup in test teardown (torch.cuda.empty_cache(), del model)
  - Use pytest fixtures with proper `yield` and cleanup
  - Disable VectorStore entirely for tests (USE_ENHANCED_MEMORY=false already set)
- **Effort**: MODERATE (2-4 hours) - requires investigation of VectorStore initialization
- **Priority**: **P0** - Currently excluded from test runs

### test_checkpoint_manager.py
- **Status**: HANG
- **Location**: tests/test_checkpoint_manager.py
- **Symptoms**: Hangs at test 9/20 (test_restore_from_checkpoint or similar)
- **Impact**: Blocks checkpoint/session management tests
- **Root Cause**: Likely file handle leak or async operation not awaited
- **Recommended Fix**:
  - Review test 9 for unclosed file handles
  - Add timeout decorators (@pytest.mark.timeout(30))
  - Ensure all async operations use `await` properly
- **Effort**: MODERATE (2-3 hours)
- **Priority**: **P0** - Currently excluded from test runs

### Unknown Hang at ~29% Mark
- **Status**: HANG
- **Location**: Between tests/test_enhanced_memory_store_result.py and tests/test_ensemble_model.py
- **Symptoms**: Test suite consistently times out after ~1,600 tests (29% completion)
- **Tests Passing Before Hang**: test_ensemble_model.py, test_event_detection.py (both pass individually)
- **Root Cause**: **Resource accumulation** - likely memory leak, socket exhaustion, or file handle buildup
- **Recommended Fix**:
  - Run tests in smaller batches with subprocess isolation
  - Add pytest plugin to force garbage collection between test modules
  - Investigate async test cleanup (event loops, asyncio tasks not cancelled)
  - **CRITICAL**: Disable pytest-rerunfailures plugin (confirmed incompatibility with Python 3.13)
- **Effort**: COMPLEX (6-8 hours) - requires systematic binary search through test range
- **Priority**: **P0** - Prevents full test inventory

---

## Category 2: ASSERTION FAILURES - **P1 CRITICAL**

These tests have logic errors and must be fixed to restore 100% pass rate.

### test_ab_rollout_controller.py::TestABRolloutController::test_execute_stage_with_ab_config
- **Status**: FAILED
- **File**: tests/test_ab_rollout_controller.py
- **Error Type**: `pydantic_core._pydantic_core.ValidationError`
- **Error Message**: "5 validation errors for Predi..." (truncated)
- **Root Cause**: Pydantic model validation failure - incorrect field types or missing required fields
- **Impact**: AB testing / staged rollout functionality broken
- **Recommended Fix**:
  - Review PredictionLog or related Pydantic model changes
  - Check for recent schema migrations (model_id, timestamp, feature_vector fields)
  - Verify test fixtures match current Pydantic model schema
- **Effort**: TRIVIAL (30-60 minutes)
- **Priority**: **P1** - Core ML routing functionality

### test_dashboard_snapshot.py (3 failures)
- **Status**: FAILED (3 tests)
- **File**: tests/test_dashboard_snapshot.py
- **Tests Failing**:
  1. Test 8/18 (likely `test_snapshot_accuracy_metrics`)
  2. Test 13/18 (likely `test_snapshot_with_missing_data`)
  3. Test 17/18 (likely `test_snapshot_serialization`)
- **Error Type**: Unknown (--tb=no suppressed tracebacks)
- **Root Cause**: Likely assertion failures on accuracy metrics or snapshot structure
- **Impact**: Dashboard/monitoring visibility broken
- **Recommended Fix**:
  - Rerun with `--tb=short` to see actual vs expected values
  - Check for schema changes in accuracy dashboard models
  - Verify JSON serialization of new Pydantic fields
- **Effort**: MODERATE (2-3 hours)
- **Priority**: **P1** - Monitoring and observability critical

---

## Category 3: SKIPPED TESTS - **P2 IMPORTANT**

These tests are skipped due to missing dependencies or environment flags.

### Ollama Integration Tests (140 tests)
- **Status**: SKIPPED
- **Reason**: `SKIP_OLLAMA_TESTS=1` environment variable set (no Docker services running)
- **Files**:
  - tests/trinity_protocol/ (all Ollama-dependent tests)
  - tests/test_init_ollama_model.py (22 tests)
  - tests/test_ollama_health_check.py (12 tests)
  - tests/test_ollama_health_check_comprehensive.py (17 tests)
- **Impact**: Local model routing, hybrid executor tests not validated
- **Recommended Fix**: Run with `--with-docker` flag to enable Docker Compose Ollama services
- **Effort**: TRIVIAL (5 minutes) - just run: `python run_tests.py --with-docker --run-all`
- **Priority**: **P2** - Important for Phase 3 local model cost savings, but not blocking

### Integration Tests (13 skipped)
- **Status**: SKIPPED
- **Files**:
  - tests/integration/test_ambient_to_witness.py (7 tests)
  - tests/integration/test_epic4_2_complete.py (6 tests)
- **Reason**: Integration marker, likely require external services
- **Impact**: End-to-end workflow validation missing
- **Recommended Fix**: Review skip conditions, enable integration tests in CI
- **Effort**: MODERATE (1-2 hours per test file)
- **Priority**: **P2** - Important for E2E validation

### Intent Parser Tests (31 skipped)
- **Status**: SKIPPED
- **File**: tests/orchestrator/test_intent_parser.py (all 31 tests)
- **Reason**: Unknown (possibly missing dependency or conditional skip)
- **Impact**: Intent parsing for /primeA, /primeccc commands not tested
- **Recommended Fix**: Investigate skip reason (check @pytest.mark.skipif conditions)
- **Effort**: TRIVIAL (30 minutes)
- **Priority**: **P2** - Core orchestrator functionality, should not be skipped

---

## Category 4: EXCLUDED TESTS - **KNOWN ISSUES**

These test files are explicitly excluded from test runs due to known issues.

### test_firestore_learning_persistence.py
- **Status**: EXCLUDED (--ignore flag)
- **Reason**: Hangs at collection time (imports Firestore at module level)
- **Impact**: Firestore learning backend not tested
- **Recommended Fix**: Refactor to use lazy imports, add mocking for Firestore client
- **Effort**: MODERATE (3-4 hours)
- **Priority**: **P3** - Firestore backend is optional (VectorStore primary)

### test_firestore_mock_integration.py
- **Status**: EXCLUDED (--ignore flag)
- **Reason**: Hangs at collection time
- **Impact**: Mock Firestore integration tests not run
- **Recommended Fix**: Same as above (lazy imports, proper mocking)
- **Effort**: MODERATE (2-3 hours)
- **Priority**: **P3** - Mock tests, not production-critical

### tests/e2e/
- **Status**: EXCLUDED (--ignore directory)
- **Reason**: Imports agency at module level, causes circular dependency issues
- **Impact**: End-to-end agency.py orchestration tests not run
- **Recommended Fix**: Refactor e2e tests to use subprocess or isolated pytest sessions
- **Effort**: COMPLEX (4-6 hours)
- **Priority**: **P3** - E2E tests valuable but not blocking unit tests

---

## Recommended Execution Order (Fix Strategy)

### Phase 1: Unblock Test Suite (P0 - 1-2 days)
1. **Disable pytest-rerunfailures** (IMMEDIATE - 5 minutes)
   - Edit pytest.ini: Remove or comment out `reruns = 3`
   - Or uninstall: `pip uninstall pytest-rerunfailures`
   - **Impact**: Eliminates segfault root cause (ADR-030 finding)

2. **Fix 29% Hang** (CRITICAL - 6-8 hours)
   - Binary search test range to isolate hanging test
   - Add resource cleanup (garbage collection, socket closure)
   - Consider pytest-timeout plugin for all tests

3. **Fix test_checkpoint_manager.py** (2-3 hours)
   - Add timeout decorators
   - Review file handle cleanup in test 9

4. **Fix test_vectorstore_performance.py** (2-4 hours)
   - Add explicit torch cleanup
   - Verify VectorStore disabled for tests

### Phase 2: Restore 100% Pass Rate (P1 - 1 day)
5. **Fix test_ab_rollout_controller.py** (30-60 minutes)
   - Run with traceback to see Pydantic validation errors
   - Update test fixtures for current schema

6. **Fix test_dashboard_snapshot.py** (2-3 hours)
   - Run with traceback for all 3 failures
   - Update assertions for new metrics structure

### Phase 3: Enable Skipped Tests (P2 - 2 days)
7. **Enable Ollama Tests** (5 minutes)
   - Run: `python run_tests.py --with-docker --run-all`
   - Verify all 140 Ollama tests pass

8. **Enable Intent Parser Tests** (30 minutes)
   - Investigate skip conditions
   - Remove unnecessary skips

9. **Enable Integration Tests** (1-2 hours each)
   - Fix ambient_to_witness, epic4_2_complete
   - Ensure external service mocking

### Phase 4: Re-enable Excluded Tests (P3 - 3-4 days)
10. **Fix Firestore Tests** (3-4 hours)
    - Lazy imports, proper mocking

11. **Fix E2E Tests** (4-6 hours)
    - Subprocess isolation or pytest-forked plugin

---

## Test Execution Command Reference

### Current Working Command (Partial Suite)
```bash
env PYTEST_ADDOPTS="" USE_ENHANCED_MEMORY=false AGENCY_NESTED_TEST=1 \
  PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 \
  SKIP_OLLAMA_TESTS=1 \
  uv run pytest tests/ --tb=short -v --strict-markers \
  --ignore=tests/test_firestore_learning_persistence.py \
  --ignore=tests/test_firestore_mock_integration.py \
  --ignore=tests/e2e/ \
  --ignore=tests/benchmarks/test_vectorstore_performance.py \
  --ignore=tests/test_checkpoint_manager.py
```
**Result**: Hangs at 29% (1,600 tests), finds 4 assertion failures

### Recommended Fix Command (After Phase 1)
```bash
# 1. Disable pytest-rerunfailures first
pip uninstall pytest-rerunfailures

# 2. Run with timeout per test
env USE_ENHANCED_MEMORY=false AGENCY_NESTED_TEST=1 SKIP_OLLAMA_TESTS=1 \
  uv run pytest tests/ --tb=short -v --strict-markers \
  --timeout=30 --timeout-method=thread \
  --ignore=tests/test_firestore_learning_persistence.py \
  --ignore=tests/test_firestore_mock_integration.py \
  --ignore=tests/e2e/
```
**Expected**: Complete test run in 15-20 minutes, full failure inventory

### Full Suite with Ollama (After Phase 3)
```bash
python run_tests.py --with-docker --run-all
```
**Expected**: 1,762 tests (including 140 Ollama integration tests), 100% pass rate

---

## Detailed Failure Analysis (from partial run)

### Tests Completed Before Hang (0-29%)
- ✅ tests/adr/ (25 tests) - All PASSED
- ✅ tests/agents/ (27 tests) - All PASSED
- ✅ tests/benchmarks/test_performance.py (8 tests) - All PASSED
- ✅ tests/chaos/ (11 tests) - 10 PASSED, 1 XPASSED
- ✅ tests/commands/ (20 tests) - All PASSED
- ✅ tests/docs/ (33 tests) - All PASSED
- ✅ tests/fixtures/ (21 tests) - All PASSED
- ⏭️ tests/integration/ (13 tests) - 4 PASSED, 7 SKIPPED, 6 SKIPPED
- ✅ tests/meta_learning/ (15 tests) - All PASSED
- ✅ tests/necessary/ (118 tests) - All PASSED
- ⏭️ tests/orchestrator/test_intent_parser.py (31 tests) - All SKIPPED
- ✅ tests/orchestrator/ (other files, 143 tests) - All PASSED
- ✅ tests/stress/ (8 tests) - All PASSED
- ❌ tests/test_ab_rollout_controller.py (22 tests) - 21 PASSED, **1 FAILED**
- ✅ tests/test_ab_test_config.py through test_context_handoff_tool.py (~400 tests) - Mostly PASSED
- ❌ tests/test_dashboard_snapshot.py (18 tests) - 14 PASSED, **3 FAILED**
- ✅ tests/test_distributed_locks.py through test_enhanced_memory_store_result.py (~600 tests) - Mostly PASSED
- ⏸️ **HANG** at ~29% mark (after test_enhanced_memory_store_result.py)

### Tests Not Yet Run (30-100%)
- ❓ tests/test_ensemble_model.py (25 tests) - **Passes individually**, suspected next in sequence
- ❓ tests/test_event_detection.py through end (~3,900+ tests) - **Unknown status**

---

## Constitutional Compliance Notes

### Article I: Complete Context Before Action
- ❌ **VIOLATION**: Test suite does not complete, preventing full context
- **Retry Attempts**: 3 full runs attempted, all timeout at 10 minutes
- **Recommendation**: Implement binary search with smaller test batches (Article I: retry with smaller scope)

### Article II: 100% Verification and Stability
- ❌ **VIOLATION**: Cannot verify 100% pass rate until all tests complete
- **Current Known Failure Rate**: 4 failures out of ~1,600 tested = **99.75% pass rate** (incomplete data)
- **Target**: 1,762 tests at 100% pass rate (1,622 unit + 140 integration with Docker)

### Article IV: Continuous Learning and Improvement
- ✅ **COMPLIANCE**: Patterns identified:
  - **Pattern 1**: pytest-rerunfailures + Python 3.13 = segfault (stored in ADR-030)
  - **Pattern 2**: Resource accumulation causes hangs after ~1,600 tests
  - **Pattern 3**: Pydantic validation errors indicate schema drift between tests and models
- **VectorStore Storage**: These patterns should be stored for future test suite debugging

---

## Next Steps (Immediate Actions)

1. **IMMEDIATE** (5 minutes): Disable pytest-rerunfailures to eliminate segfault risk
   ```bash
   pip uninstall pytest-rerunfailures
   # OR edit pytest.ini to remove 'reruns = 3'
   ```

2. **URGENT** (1 hour): Binary search to isolate 29% hang
   ```bash
   # Test hypothesis: Run tests from 30% mark onward
   uv run pytest tests/test_exit_plan_mode.py::* --tb=short -v
   # If passes, run batch: tests/test_e*.py tests/test_f*.py ...
   ```

3. **HIGH PRIORITY** (2 hours): Fix known assertion failures
   ```bash
   # Get full tracebacks for the 4 failures
   uv run pytest tests/test_ab_rollout_controller.py::TestABRolloutController::test_execute_stage_with_ab_config -vvs
   uv run pytest tests/test_dashboard_snapshot.py -vvs
   ```

4. **DOCUMENTATION** (30 minutes): Update ADR-030 with findings
   - Add resource accumulation as secondary hang cause
   - Document 29% hang point for future reference
   - Recommend pytest-timeout plugin for all tests

---

## Estimated Total Effort

- **Phase 1 (Unblock)**: 10-18 hours (1-2 days)
- **Phase 2 (Fix Failures)**: 3-4 hours (0.5 day)
- **Phase 3 (Enable Skipped)**: 4-6 hours (0.5-1 day)
- **Phase 4 (Re-enable Excluded)**: 7-10 hours (1-1.5 days)

**Total**: 24-38 hours (3-5 days) to achieve 100% test suite health

---

## Success Criteria

- ✅ All 5,545 tests complete without hanging (no 10-minute timeouts)
- ✅ 100% pass rate on unit tests (5,545 tests)
- ✅ 100% pass rate on integration tests with Docker (140 Ollama tests)
- ✅ Zero assertion failures (currently 4 known)
- ✅ All skipped tests investigated (44 skips reduced to intentional integration-only tests)
- ✅ Test suite completes in < 20 minutes (sequential) or < 5 minutes (parallel with fixed xdist)
- ✅ No segfaults, no hangs, no resource exhaustion

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14 by AuditorAgent
**Status**: DRAFT - Incomplete inventory due to 29% hang, 4 confirmed failures catalogued
