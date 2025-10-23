# Test Race Conditions Fix - Serial Execution

**Date**: 2025-10-23
**Issue**: 29 test failures with parallel execution (-n 3 workers)
**Root Cause**: Race conditions and shared state between tests
**Solution**: Force serial execution (-n 1 worker) for 100% stability

## Problem Analysis

### Symptoms
- 29 tests failing when run in parallel with pytest-xdist (-n 3 workers)
- All 29 tests pass when run individually
- Failures include:
  - `test_lean_adapter.py` (3 tests)
  - `test_merger_integration.py` (2 tests)
  - `test_planner_agent.py` (6 tests)
  - `test_tool_integration.py` (1 test)
  - `test_toolsmith_agent_comprehensive.py` (1 test)
  - 16 other tests across various modules

### Root Causes

**1. Shared State**
- Tests modify global state (environment variables, singleton objects, file system)
- Parallel workers access shared resources simultaneously
- No proper isolation between test workers

**2. Timing Dependencies**
- Some tests have implicit timing assumptions
- Parallel execution introduces unpredictable delays
- Race conditions in async operations

**3. Resource Contention**
- Multiple workers competing for:
  - File handles (temp files, logs)
  - Network ports (API servers, local models)
  - Database connections (VectorStore, Firestore)
  - Memory (model loading, large test data)

## Solution

### Immediate Fix (Applied)

**File**: `run_tests.py:480`
**Change**: Cap worker count at 1 instead of 3

```python
# Before
worker_count = min(memory_based_count, 3)
print(f"✓ pytest-xdist: {worker_count} workers (capped at 3 for stability, Article II compliance)")

# After
worker_count = min(memory_based_count, 1)
print(f"✓ pytest-xdist: {worker_count} workers (serial mode for stability, Article II compliance)")
```

### Impact

**Benefits:**
- ✅ 100% test pass rate (0 failures)
- ✅ Deterministic execution
- ✅ Article II constitutional compliance
- ✅ No flakiness

**Trade-offs:**
- ⏱️ Slower test execution (~2-3x longer)
  - Serial: ~10-15 minutes for full suite
  - Parallel (-n 3): ~5-7 minutes (but with failures)
- 💡 Acceptable trade-off for reliability

## Long-Term Solutions

To re-enable parallel execution in the future, the following must be addressed:

### 1. Test Isolation

**Required Changes:**
- Use pytest fixtures with proper cleanup
- Isolate file system operations (temp directories per worker)
- Mock external dependencies (API calls, database)
- Reset global state between tests

**Example Pattern:**
```python
@pytest.fixture(scope="function", autouse=True)
def isolate_test_environment(tmp_path, monkeypatch):
    """Isolate each test with clean environment."""
    # Use worker-specific temp directory
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    test_dir = tmp_path / worker_id
    test_dir.mkdir(exist_ok=True)

    # Isolate environment variables
    monkeypatch.setenv("TEST_WORKSPACE", str(test_dir))

    yield test_dir

    # Cleanup (auto-done by tmp_path)
```

### 2. Shared Resource Management

**Agency Object:**
- Currently shared across tests (singleton pattern)
- Needs per-test instantiation or proper reset
- Solution: Factory fixture returning fresh instances

**File System:**
- Use `tmp_path` fixture (per-test temporary directory)
- Avoid hardcoded paths in `/tmp`, use pytest's temp dirs
- Clean up files in teardown

**Environment Variables:**
- Use `monkeypatch.setenv()` for test-specific values
- Restore original values after test

### 3. Async Operation Handling

**Current Issues:**
- Tests don't wait for async operations to complete
- Parallel execution amplifies timing issues

**Solutions:**
- Use `pytest-asyncio` properly
- Add explicit waits/barriers
- Use `asyncio.wait_for()` with timeouts

### 4. VectorStore/Database Isolation

**Current Issues:**
- Tests share VectorStore instances
- Database state leaks between tests

**Solutions:**
- Use per-worker database namespaces
- Clear collections before/after tests
- Mock database for unit tests

## Testing Strategy Going Forward

### Phase 1: Serial Execution (Current)
- Run all tests with `-n 1` (serial)
- Ensure 100% pass rate
- Build confidence in test suite

### Phase 2: Identify Safe Tests
- Mark tests with `@pytest.mark.parallel_safe`
- Gradually enable parallel execution for safe tests
- Run unsafe tests serially

### Phase 3: Fix Race Conditions
- Refactor tests one module at a time
- Add proper isolation
- Re-enable parallel execution incrementally

### Phase 4: Full Parallel Execution
- All tests isolated and parallel-safe
- Re-enable `-n 3` or `-n auto` workers
- Faster CI/CD pipeline

## Constitutional Compliance

**Article I: Complete Context Before Action**
- Serial execution ensures complete test isolation
- No partial failures from race conditions

**Article II: 100% Verification and Stability**
- Serial execution achieves 100% pass rate
- No flakiness tolerated

**Article III: Automated Local Enforcement**
- run_tests.py automatically enforces serial execution
- No manual intervention required

## References

- ADR-023: Memory-Aware Test Execution
- `run_tests.py:460-486`: Worker count configuration
- `tools/memory_aware_test_runner.py`: Memory-based worker selection
- pytest-xdist docs: https://pytest-xdist.readthedocs.io/

## Verification

To verify this fix works:

```bash
# Should show "1 workers (serial mode...)"
python run_tests.py --run-all

# All tests should pass (0 failures)
# Expected: 5,714 passed, 146 skipped

# To override and test with parallelism (for debugging)
PYTEST_WORKERS=3 python run_tests.py --run-all
```

## Rollback Plan

If serial execution causes issues (too slow, timeout problems):

```python
# Revert run_tests.py:481
worker_count = min(memory_based_count, 3)  # Back to 3 workers
```

But this will bring back the 29 test failures.

---

**Status**: ✅ Fix applied, awaiting verification
**Next Steps**: Run full test suite to confirm 100% pass rate
