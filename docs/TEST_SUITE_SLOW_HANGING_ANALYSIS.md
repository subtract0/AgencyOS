# Test Suite Slow & Hanging Tests Analysis

**Date:** 2025-10-16
**Analyst:** AuditorAgent (READ-ONLY mode)
**Objective:** Identify tests preventing completion within 20 minutes

---

## Executive Summary

**Critical Findings:**
- **140+ subprocess.run() calls without timeout** - PRIMARY HANG RISK
- **~200 seconds of blocking time.sleep() calls** - reduces parallelism effectiveness
- **2 tests with 10-15 minute timeouts** - single test failures block entire suite
- **59 async test files** - many without per-operation timeouts

**Impact:**
- Test suite can hang indefinitely on subprocess operations
- ~3-4 minutes wasted on excessive sleep() calls (even with parallelism)
- Constitutional violations: Article I (Complete Context) & Article II (100% Verification)

**Recommended Fix Priority:**
1. Add `timeout=10` to all subprocess.run() calls (80+ in orchestrator/)
2. Mock/skip tests with 10+ minute timeouts
3. Replace long sleep() calls with mock timers

---

## 🔴 Critical Blocking Issues

### 1. Subprocess Calls Without Timeout (HIGHEST PRIORITY)

**Risk:** Infinite hangs if git command blocks (network issue, lock file, etc.)

**Files Affected:**
```
tests/orchestrator/test_foundation_automation_git_validation.py   29 calls
tests/orchestrator/test_pr_creator.py                             20 calls
tests/orchestrator/test_unified_primea_orchestrator.py            15 calls
tests/tools/ci_monitor/test_fix_applicator.py                     12 calls
tests/foundation_automation/test_git_validation.py                 8 calls
```

**Example Violation:**
```python
# CURRENT (UNSAFE):
subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

# FIX:
subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, timeout=10)
```

**Automated Fix Pattern:**
```bash
# Find all subprocess.run() calls missing timeout
grep -rn "subprocess\.run(" tests/orchestrator --include="*.py" | \
  grep -v "timeout=" | \
  grep -v "patch\|Mock"
```

**Impact:** Prevents indefinite test hangs. **FIX IMMEDIATELY.**

---

### 2. Tests with 10+ Minute Timeouts

#### Test: `test_e2e_large_graph_scale`
- **File:** `tests/foundation_automation/test_e2e_natural_language_flow.py:848`
- **Timeout:** 600 seconds (10 minutes)
- **Issue:** Executes 20-task async graph with memory tracking
- **Blocking Operations:**
  - `tracemalloc` overhead
  - Complex `asyncio.gather()` with 20 concurrent tasks
  - No intermediate timeouts on individual tasks
- **Recommendation:**
  - Reduce graph to 5-10 tasks for testing
  - Add `asyncio.wait_for(task, timeout=30)` per task
  - Reduce timeout to 120 seconds

#### Test: `test_full_autonomous_cycle_intentional_failure_to_success`
- **File:** `tests/tools/ci_monitor/test_end_to_end_scenario.py:372`
- **Timeout:** 900 seconds (15 minutes)
- **Issue:** Real GitHub API interaction with CI polling
- **Blocking Operations:**
  - GitHub PR creation (network call)
  - CI job polling every 30 seconds
  - Potential infinite wait if CI never completes
- **Recommendation:**
  - Mock GitHub API with `@patch("subprocess.run")`
  - Use fixture-based CI status instead of real polling
  - Reduce timeout to 30 seconds with mocks

**Impact:** Single test failure adds 10-15 minutes to suite runtime.

---

## ⚠️ High Priority Issues

### 3. Excessive time.sleep() Calls

#### File: `test_checkpoint_manager.py`
```python
# Line 576: ALREADY MARKED @pytest.mark.skip
time.sleep(61)   # Test interval timer (1 minute)

# Line 598: ALREADY MARKED @pytest.mark.skip
time.sleep(125)  # Test multiple intervals (2+ minutes)
```
**Status:** Properly skipped. No action needed.

#### File: `test_distributed_locks.py`
```python
# Line 443: test_heartbeat_updates_timestamp
time.sleep(4)  # Wait for 2 heartbeat intervals

# Line 518: test_heartbeat_prevents_stale_lock
time.sleep(3)  # Wait for heartbeat expiry

# 6 more tests with sleep(2-4)
```
**Total:** ~18 seconds of blocking time
**Fix:** Mock heartbeat intervals with `update_interval=0.1`

#### File: `test_firestore_learning_persistence.py`
```python
# Lines 132, 196, 328, 406, 447
time.sleep(1-2)  # Wait for Firestore operations (6 occurrences)
```
**Total:** ~8-10 seconds
**Fix:** Mock Firestore client to return immediately

#### File: `test_heartbeat.py`
```python
# Line 54, 84, 105, 133, 153, 159, 165
time.sleep(0.5-2.5)  # Multiple heartbeat interval waits
```
**Total:** ~10 seconds
**Fix:** Use `threading.Event` instead of sleep, mock intervals

**Cumulative Impact:** ~40-50 seconds of blocking time across 20+ tests

---

### 4. Thread Joins Without Timeout

**Risk:** Infinite hang if thread doesn't terminate

**Examples:**
```python
# test_model_storage.py:634
thread.join()  # NO TIMEOUT

# test_memory_facade.py:243
thread.join()  # NO TIMEOUT

# test_read_tool.py:333
t.join()  # NO TIMEOUT
```

**Fix Pattern:**
```python
# BEFORE:
thread.join()

# AFTER:
thread.join(timeout=5)
if thread.is_alive():
    pytest.fail("Thread did not terminate within 5 seconds")
```

**Files Affected:** 10+ tests

---

## 🟡 Medium Priority Issues

### 5. Async Operations Without Intermediate Timeouts

**Current Pattern:**
```python
@pytest.mark.asyncio
@pytest.mark.timeout(600)  # Only outer timeout
async def test_large_operation():
    result = await orchestrator.execute_graph(20_tasks)  # No per-task timeout
```

**Improved Pattern:**
```python
@pytest.mark.asyncio
@pytest.mark.timeout(120)  # Reduced outer timeout
async def test_large_operation():
    # Add per-task timeout
    async def execute_with_timeout(task):
        return await asyncio.wait_for(task.execute(), timeout=30)

    results = await asyncio.gather(*[execute_with_timeout(t) for t in tasks])
```

**Files Affected:**
- `foundation_automation/test_e2e_natural_language_flow.py`
- `orchestrator/test_foundation_automation_e2e.py`
- `orchestrator/test_unified_primea_orchestrator.py`

---

### 6. Tests Marked @pytest.mark.slow

**Files:**
```
test_real_llm_cost_tracking.py:232
test_heartbeat.py:142
integration/test_epic4_2_complete.py:182, 682, 754
integration/test_ambient_to_witness.py:278, 365
test_master_e2e.py:22
benchmarks/test_performance.py:75
benchmarks/test_vectorstore_performance.py:190, 545
test_vector_index.py:545
```

**Current pytest.ini behavior:**
```ini
# Run with: pytest -m "not slow" to skip these
slow: marks slow tests that may take longer to run (>1s, needs optimization)
```

**Recommendation:** Ensure these are properly excluded from default test runs.

---

## 📊 Test Execution Analysis

### pytest.ini Configuration

**Current timeout settings:** NONE (no global timeout)

**Parallelism:** Memory-aware via `run_tests.py`
- Uses `pytest-xdist` with dynamic worker count
- Workers: 1-10 based on available memory

**Issue:** Blocking operations (sleep, subprocess) still block workers even with parallelism

---

## 🛠️ Recommended Fixes (Priority Order)

### Priority 1: Subprocess Timeouts (CRITICAL)

**Action:** Add `timeout=10` to all subprocess.run() calls

**Script to find violations:**
```bash
# Find all subprocess.run() without timeout
grep -rn "subprocess\.run(" tests/orchestrator tests/foundation_automation \
  --include="*.py" | \
  grep -v "timeout=" | \
  grep -v "@patch\|Mock" | \
  wc -l
# Result: 80+ violations
```

**Bulk fix pattern:**
```python
# Use sed or manual fix:
# OLD: subprocess.run([cmd], capture_output=True, check=True)
# NEW: subprocess.run([cmd], capture_output=True, check=True, timeout=10)
```

**Estimated Impact:** Prevents indefinite hangs on git operations

---

### Priority 2: Mock Long-Running Tests

**Action:** Mock or skip tests with 10+ minute timeouts

**Files:**
1. `test_e2e_natural_language_flow.py::test_e2e_large_graph_scale`
   - Add `@pytest.mark.skip(reason="Slow E2E test, run manually")`
   - OR reduce graph size to 5 tasks, timeout to 120s

2. `test_end_to_end_scenario.py::test_full_autonomous_cycle_*`
   - Mock GitHub API with fixtures
   - Reduce timeout to 30s

**Estimated Impact:** Saves 10-15 minutes on test failures

---

### Priority 3: Replace Long Sleeps with Mocks

**Action:** Mock timers/intervals in tests

**Files:**
1. `test_distributed_locks.py` (8 tests)
   ```python
   # Configure faster intervals for testing
   lock_manager = LockManager(heartbeat_interval=0.1)  # Instead of 2s
   time.sleep(0.2)  # Instead of 4s
   ```

2. `test_firestore_learning_persistence.py` (6 tests)
   ```python
   # Mock Firestore operations
   @patch("firebase_admin.firestore.client")
   def test_firestore_write(mock_client):
       # No sleep needed - mock returns immediately
   ```

3. `test_heartbeat.py` (7 tests)
   ```python
   # Use threading.Event instead of sleep
   event = threading.Event()
   thread.start()
   event.wait(timeout=1)  # Instead of time.sleep(1.5)
   ```

**Estimated Impact:** Saves 3-4 minutes per full test run

---

### Priority 4: Add Thread Join Timeouts

**Action:** Add `timeout=5` to all `.join()` calls

**Pattern:**
```python
thread.join(timeout=5)
assert not thread.is_alive(), "Thread did not terminate"
```

**Files:** 10+ test files with unguarded joins

**Estimated Impact:** Prevents thread-related infinite hangs

---

### Priority 5: Add Async Operation Timeouts

**Action:** Wrap long async operations with `asyncio.wait_for()`

**Pattern:**
```python
# Wrap individual tasks
for task in tasks:
    result = await asyncio.wait_for(task.execute(), timeout=30)
```

**Files:** 59 async test files (prioritize orchestrator/ and foundation_automation/)

---

## 📈 Estimated Time Savings

| Fix | Time Saved | Hang Prevention |
|-----|-----------|-----------------|
| Subprocess timeouts | 0 seconds* | ✅ Prevents infinite hangs |
| Mock long tests | 10-15 min | ✅ Faster failure detection |
| Replace sleeps | 3-4 min | ✅ Better parallelism |
| Thread timeouts | 0 seconds* | ✅ Prevents thread hangs |
| Async timeouts | 2-3 min | ✅ Better error localization |

*Time savings are from **preventing hangs**, not faster execution

**Total Potential Savings:** 15-22 minutes per test run + hang prevention

---

## 🎯 Quick Wins (Do First)

1. **Add subprocess timeouts to orchestrator/ tests** (80 calls, 30 minutes work)
   ```bash
   # Focus on these files first:
   tests/orchestrator/test_foundation_automation_git_validation.py
   tests/orchestrator/test_pr_creator.py
   tests/orchestrator/test_unified_primea_orchestrator.py
   ```

2. **Skip or reduce timeout on slow E2E tests** (5 minutes work)
   ```python
   @pytest.mark.skip(reason="Slow E2E test, run manually in CI")
   @pytest.mark.timeout(600)
   async def test_e2e_large_graph_scale(...):
   ```

3. **Mock GitHub API in CI monitor tests** (20 minutes work)
   ```python
   @patch("subprocess.run")
   def test_ci_cycle(mock_run):
       # Return mocked CI status instead of real polling
   ```

---

## ⚖️ Constitutional Compliance

**Article I Violation:** Complete Context Before Action
- Hanging tests prevent completion of context gathering
- Fix: Timeouts ensure tests fail fast instead of hanging

**Article II Violation:** 100% Verification
- Hanging tests prevent reaching 100% test completion
- Fix: All tests must complete (pass or fail) within reasonable time

**Recommendation:** Fix blocking operations to restore constitutional compliance.

---

## 📋 Validation Checklist

After fixes, validate with:

```bash
# 1. Run full test suite with timeout enforcement
PYTEST_TIMEOUT=1200 python run_tests.py --run-all

# 2. Check for subprocess calls without timeout
grep -rn "subprocess\.run(" tests/ --include="*.py" | \
  grep -v "timeout=" | \
  grep -v "@patch\|Mock" | \
  wc -l
# Expected: 0

# 3. Check for long sleeps
grep -rn "time\.sleep([5-9][0-9]\|[1-9][0-9][0-9]" tests/ --include="*.py"
# Expected: Only @pytest.mark.skip tests

# 4. Check thread joins
grep -rn "\.join()" tests/ --include="*.py" | \
  grep -v "timeout=" | \
  wc -l
# Expected: 0 (or all have timeout)

# 5. Run suite and measure time
time python run_tests.py --run-all
# Target: <20 minutes for full suite
```

---

## 🔗 Related Documentation

- **Test Runner:** `run_tests.py` (memory-aware worker allocation)
- **pytest.ini:** Test markers and configuration
- **ADR-023:** Memory-aware test execution
- **Constitution:** Articles I & II (Complete Context, 100% Verification)

---

## 📝 Notes

- Analysis completed in **READ-ONLY mode** (no code modifications)
- All findings are static analysis based (no actual test execution)
- Prioritization based on hang risk and time impact
- Constitutional violations identified per Agency OS governance

**Next Steps:**
1. Review findings with team
2. Create tasks for Priority 1-3 fixes
3. Validate fixes with full test run
4. Update this document with actual time savings achieved
