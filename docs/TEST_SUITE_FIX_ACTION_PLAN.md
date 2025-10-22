# Test Suite Fix Action Plan
## Preventing Hangs & Achieving <20 Minute Runtime

**Target:** Ensure test suite completes within 20 minutes without hangs
**Current Issue:** 140+ blocking operations that can cause indefinite hangs

---

## 🚨 Critical Path (Do First)

### Fix 1: Add Subprocess Timeouts (80+ violations)

**Files (Priority Order):**
1. `tests/orchestrator/test_foundation_automation_git_validation.py` - 29 calls
2. `tests/orchestrator/test_pr_creator.py` - 20 calls
3. `tests/orchestrator/test_unified_primea_orchestrator.py` - 15 calls
4. `tests/foundation_automation/test_git_validation.py` - 8 calls
5. `tests/tools/ci_monitor/test_fix_applicator.py` - 12 calls

**Pattern:**
```python
# BEFORE (UNSAFE):
subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)

# AFTER (SAFE):
subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, timeout=10)
```

**Validation:**
```bash
# Find remaining violations
grep -rn "subprocess\.run(" tests/orchestrator tests/foundation_automation \
  --include="*.py" | grep -v "timeout=" | grep -v "patch\|Mock"
# Expected: 0 after fix
```

**Estimated Work:** 45 minutes
**Impact:** Prevents infinite hangs on git operations

---

### Fix 2: Skip/Mock Long-Running E2E Tests (2 tests)

**Test 1:** `test_e2e_large_graph_scale` (10 min timeout)
```python
# File: tests/foundation_automation/test_e2e_natural_language_flow.py:848

# Option A: Skip for fast runs
@pytest.mark.slow
@pytest.mark.skip(reason="Large E2E test, run manually or in nightly CI")
@pytest.mark.timeout(600)
async def test_e2e_large_graph_scale(...):

# Option B: Reduce scope
# Change: 20 tasks → 5 tasks, timeout 600 → 120
```

**Test 2:** `test_full_autonomous_cycle_*` (15 min timeout)
```python
# File: tests/tools/ci_monitor/test_end_to_end_scenario.py:372

# Mock GitHub API instead of real calls
@patch("subprocess.run")
@pytest.mark.timeout(30)  # Reduced from 900
async def test_full_autonomous_cycle_intentional_failure_to_success(
    mock_run, ...
):
    # Mock gh pr create, gh run view, etc.
    mock_run.return_value = MagicMock(returncode=0, stdout="PR created")
```

**Estimated Work:** 20 minutes
**Impact:** Saves 10-15 minutes on test failures

---

### Fix 3: Add Thread Join Timeouts (10+ tests)

**Pattern:**
```python
# BEFORE:
thread.join()

# AFTER:
thread.join(timeout=5)
assert not thread.is_alive(), "Thread did not terminate within 5 seconds"
```

**Files:**
- `tests/test_model_storage.py:634`
- `tests/test_memory_facade.py:243`
- `tests/test_read_tool.py:333`
- `tests/unit/shared/test_persistent_store.py:379, 411`
- 5+ more

**Estimated Work:** 15 minutes
**Impact:** Prevents thread hang scenarios

---

## 🔧 Performance Improvements (Do Next)

### Fix 4: Replace Long Sleeps with Mocks

**File 1:** `tests/test_distributed_locks.py`
```python
# BEFORE:
time.sleep(4)  # Wait for 2 heartbeat intervals (2s each)

# AFTER:
# Use faster interval for testing
lock_manager = LockManager(heartbeat_interval=0.1)  # Instead of 2.0
time.sleep(0.2)  # Wait for 2 intervals (faster)
```
**Tests affected:** 8 tests, saves ~15 seconds

**File 2:** `tests/test_firestore_learning_persistence.py`
```python
# BEFORE:
time.sleep(1)  # Wait for Firestore write

# AFTER:
@patch("firebase_admin.firestore.client")
def test_firestore_write(mock_client):
    # Mock returns immediately, no sleep needed
```
**Tests affected:** 6 tests, saves ~8 seconds

**File 3:** `tests/test_heartbeat.py`
```python
# BEFORE:
time.sleep(1.5)  # Wait for heartbeat

# AFTER:
event = threading.Event()
thread = HeartbeatThread(..., update_interval=0.1)  # Faster for testing
thread.start()
event.wait(timeout=0.2)  # Faster wait
```
**Tests affected:** 7 tests, saves ~10 seconds

**Estimated Work:** 30 minutes
**Impact:** Saves 3-4 minutes per full test run

---

### Fix 5: Add Async Operation Timeouts

**Pattern:**
```python
# BEFORE:
@pytest.mark.timeout(600)  # Only outer timeout
async def test_large_operation():
    await orchestrator.execute_graph(tasks)

# AFTER:
@pytest.mark.timeout(120)  # Reduced outer timeout
async def test_large_operation():
    # Add per-task timeout
    for task in tasks:
        result = await asyncio.wait_for(task.execute(), timeout=30)
```

**Files:**
- `foundation_automation/test_e2e_natural_language_flow.py`
- `orchestrator/test_foundation_automation_e2e.py`
- `orchestrator/test_two_stage_orchestrator.py`

**Estimated Work:** 25 minutes
**Impact:** Better error localization, faster failure detection

---

## 📋 Validation Steps

After each fix:

```bash
# 1. Run affected tests
python run_tests.py tests/orchestrator/test_foundation_automation_git_validation.py

# 2. Validate no hangs (should complete in <2 minutes)
timeout 120 python run_tests.py tests/orchestrator/

# 3. Check full suite runtime
time python run_tests.py --run-all
# Target: <20 minutes
```

After all fixes:

```bash
# 1. Verify no subprocess calls without timeout
grep -rn "subprocess\.run(" tests/ --include="*.py" | \
  grep -v "timeout=" | grep -v "patch\|Mock" | wc -l
# Expected: 0

# 2. Verify no long sleeps (except skipped tests)
grep -rn "time\.sleep([5-9][0-9]\|[1-9][0-9][0-9]" tests/ --include="*.py"
# Expected: Only @pytest.mark.skip tests

# 3. Full suite with timeout enforcement
PYTEST_TIMEOUT=1200 python run_tests.py --run-all
# Expected: Completes in <20 minutes
```

---

## 🎯 Success Criteria

- ✅ Zero subprocess.run() calls without timeout parameter
- ✅ Zero thread.join() calls without timeout parameter
- ✅ All time.sleep(>5) calls either mocked or in @pytest.mark.skip tests
- ✅ All async tests with outer timeout also have per-operation timeouts
- ✅ Full test suite completes in <20 minutes
- ✅ No infinite hangs (all tests pass or fail within reasonable time)

---

## 📊 Expected Results

| Metric | Before | After |
|--------|--------|-------|
| Subprocess calls without timeout | 140+ | 0 |
| Thread joins without timeout | 10+ | 0 |
| Tests with 10+ min timeout | 2 | 0 |
| Total blocking sleep time | ~200s | ~50s |
| Risk of infinite hang | HIGH | NONE |
| Test suite runtime (full) | UNKNOWN (hangs possible) | <20 min |

---

## 🔗 Related Files

- **Analysis:** `docs/TEST_SUITE_SLOW_HANGING_ANALYSIS.md` (full details)
- **JSON Report:** `docs/audit-test-suite-slow-hanging.json` (structured data)
- **Test Runner:** `run_tests.py` (memory-aware execution)
- **Config:** `pytest.ini` (markers, parallelism settings)

---

## 📝 Implementation Order

**Week 1: Critical Fixes (Prevent Hangs)**
- Day 1: Fix 1 - Subprocess timeouts (45 min)
- Day 2: Fix 2 - Skip/mock long E2E tests (20 min)
- Day 3: Fix 3 - Thread join timeouts (15 min)
- Day 4: Validation & testing

**Week 2: Performance Improvements (Speed Up Suite)**
- Day 1: Fix 4 - Replace long sleeps (30 min)
- Day 2: Fix 5 - Async operation timeouts (25 min)
- Day 3: Final validation & documentation

**Total Estimated Work:** 2.5 hours of focused development + 1 hour validation

---

## 🚀 Quick Start

```bash
# 1. Start with highest-impact file
cd /Users/am/Code/Agency

# 2. Fix subprocess timeouts in first file
# Edit: tests/orchestrator/test_foundation_automation_git_validation.py
# Add timeout=10 to all 29 subprocess.run() calls

# 3. Validate immediately
python run_tests.py tests/orchestrator/test_foundation_automation_git_validation.py

# 4. Repeat for remaining files
# 5. Run full suite validation

# 6. Celebrate 🎉 (no more hangs!)
```
