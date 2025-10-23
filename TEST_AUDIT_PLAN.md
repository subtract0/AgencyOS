# Test Suite Audit & Cleanup Plan

**Goal**: Achieve 100% green tests in serial mode, then optimize for parallel execution

## Phase 1: Identify & Fix Slow Tests (CURRENT)

### Tests with Intentional Delays (53 files)
Found 53 test files using `sleep()` - candidates for removal or mocking

**High Priority (known slow tests from logs)**:
1. `tests/test_planner_agent.py` - 106s, 34s, 22s, 18s, 14s slowest tests
2. `tests/test_model_trainer.py` - 11s, 9s slowest tests
3. `tests/test_tool_integration.py` - 9s slowest test
4. `tests/test_leap5_phase2_integration.py` - 10s slowest test
5. `tests/test_git_tool.py` - 12s slowest test

### Action Items:

**Option A: Remove intentional delays** (RECOMMENDED)
- Replace `time.sleep()` with mocks
- Use `freezegun` for time-based tests
- Mock external API calls instead of waiting

**Option B: Mark as slow tests**
- Add `@pytest.mark.slow` marker
- Exclude from default test runs
- Run separately in CI/overnight

**Option C: Delete if not valuable**
- E2E tests that duplicate unit test coverage
- Obsolete integration tests
- Tests for experimental features

## Phase 2: Fix Actual Test Failures

### Current Known Failures (from background processes):
```
FAILED tests/test_merger_integration.py - (FIXED: workflow file assertions)
FAILED tests/test_planner_agent.py - AttributeError: 'Agency' object has no attribute 'get_response'
FAILED tests/test_tool_integration.py - AttributeError: 'Agency' object has no attribute 'get_response'
FAILED tests/test_lean_adapter.py - AssertionError (tool conversion issues)
FAILED tests/test_toolsmith_agent_comprehensive.py - Model settings integration
```

**Fix Strategy**:
1. Update tests to use correct Agency API (no `get_response` method)
2. Fix tool adapter conversion logic
3. Update model settings tests to match new policy

## Phase 3: Optimize Memory-Aware Runner

### Current State:
- Serial execution (1 worker) - STABLE but SLOW (15-20 min)
- 120-second timeout per test

### Proposed Smart Runner:
```python
def get_smart_worker_count() -> int:
    """Intelligent worker allocation based on test characteristics."""

    # Fast unit tests: 4 workers (parallel)
    # Slow integration tests: 1 worker (serial)
    # Memory-intensive tests: 1 worker (serial)

    # Use test markers to determine execution strategy:
    # - @pytest.mark.unit → 4 workers
    # - @pytest.mark.integration → 1 worker
    # - @pytest.mark.memory_intensive → 1 worker

    return dynamic_worker_count_per_test_group
```

## Execution Plan:

### Step 1: Quick Win - Remove Intentional Delays
```bash
# Find and remove time.sleep() in tests
grep -r "time.sleep\|asyncio.sleep" tests/ --include="*.py" | grep -v "# NECESSARY"
```

### Step 2: Fix Test Failures
```bash
# Run failed tests individually
uv run pytest tests/test_planner_agent.py -v -x
uv run pytest tests/test_tool_integration.py -v -x
```

### Step 3: Validate 100% Green
```bash
# Full suite in serial mode
python run_tests.py
# Expected: All pass, ~10-15 min runtime
```

### Step 4: Re-enable Parallelism (FUTURE)
```bash
# Smart parallel execution
python run_tests.py --smart-parallel
# Expected: All pass, ~5-8 min runtime
```

## Metrics:

### Current:
- **Total tests**: 5,891
- **Passing**: ~5,746 (97.5%)
- **Failing**: ~29 (0.5%)
- **Skipped**: ~140 (2.4%)
- **Runtime (serial)**: 15-20 minutes
- **Timeouts**: Multiple tests >60s

### Target (Phase 3):
- **Total tests**: ~5,800 (after cleanup)
- **Passing**: 100%
- **Failing**: 0
- **Runtime (smart parallel)**: 5-8 minutes
- **Timeouts**: 0

## Next Actions:

1. ✅ Create this audit plan
2. ⏭️ Run focused test on slowest tests
3. ⏭️ Remove/mock intentional delays
4. ⏭️ Fix Agency API failures
5. ⏭️ Achieve 100% green in serial
6. ⏭️ Design smart parallel runner
