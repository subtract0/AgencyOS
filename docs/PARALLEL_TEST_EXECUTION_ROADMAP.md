# Parallel Test Execution Roadmap - Re-enabling 8+ Workers

**Goal**: Restore parallel test execution (~8 workers) while maintaining 100% pass rate through smart test isolation and orchestration.

**Current State**: Serial execution (-n 1) ensures 100% reliability but is ~3x slower (~15min vs ~5min).

**Target State**: Parallel execution (-n 8) with proper isolation for 100% reliability + 3x speedup.

---

## Strategy: Test Isolation with Smart Orchestration

### Phase 1: Test Classification & Isolation (Week 1-2)

**Objective**: Identify and mark parallel-safe vs serial-only tests

**Tasks**:

1. **Test Analysis Tool** - Analyze test dependencies
   ```python
   # tools/test_isolation_analyzer.py
   class TestIsolationAnalyzer:
       def analyze_test_dependencies(self, test_file: str) -> TestProfile:
           """
           Detect shared resources:
           - Global state (singletons, class variables)
           - File system operations
           - Environment variables
           - Database/VectorStore access
           - Network ports
           """
           return TestProfile(
               uses_global_state=bool,
               uses_filesystem=bool,
               uses_database=bool,
               uses_network=bool,
               safe_for_parallel=bool
           )
   ```

2. **Mark Tests with Isolation Markers**
   ```python
   # Parallel-safe tests (no shared state)
   @pytest.mark.parallel_safe
   def test_pure_function():
       result = add(2, 2)
       assert result == 4

   # Serial-only tests (shared state)
   @pytest.mark.serial_only
   def test_agency_singleton():
       agency = Agency.get_instance()  # Singleton!
       ...
   ```

3. **Auto-detect Unsafe Patterns** via AST analysis
   - Singleton pattern usage
   - Global variable mutations
   - `os.environ` modifications without `monkeypatch`
   - File operations outside `tmp_path` fixture
   - Database queries without per-worker isolation

**Deliverables**:
- `tools/test_isolation_analyzer.py` - AST-based analyzer
- Test markers applied to all 1,762 tests
- Classification report: X% parallel-safe, Y% need refactoring

---

### Phase 2: Test Fixtures for Isolation (Week 3-4)

**Objective**: Create fixtures that automatically isolate shared resources

**1. Worker-Scoped Temp Directories**
```python
# conftest.py
@pytest.fixture(scope="function", autouse=True)
def isolated_workspace(tmp_path, worker_id):
    """Each test gets its own temp directory per worker."""
    if worker_id == "master":
        # Serial execution
        workspace = tmp_path / "test_workspace"
    else:
        # Parallel execution - worker-specific directory
        workspace = tmp_path / f"worker_{worker_id}" / "test_workspace"

    workspace.mkdir(parents=True, exist_ok=True)

    # Monkey-patch temp directory functions
    with patch.dict(os.environ, {"PYTEST_WORKSPACE": str(workspace)}):
        yield workspace

    # Cleanup happens automatically via tmp_path
```

**2. Per-Worker Agency Instances**
```python
@pytest.fixture(scope="function")
def isolated_agency(isolated_workspace, monkeypatch):
    """Fresh Agency instance per test, isolated to worker."""
    # Clear singleton cache
    Agency._instances.clear()

    # Use worker-specific directories
    monkeypatch.setenv("AGENCY_WORKSPACE", str(isolated_workspace))
    monkeypatch.setenv("AGENCY_MEMORY_DIR", str(isolated_workspace / "memory"))

    agency = Agency()
    yield agency

    # Cleanup
    agency.shutdown()
    Agency._instances.clear()
```

**3. Database/VectorStore Isolation**
```python
@pytest.fixture(scope="function")
def isolated_vectorstore(worker_id):
    """Per-worker VectorStore namespace."""
    namespace = f"test_{worker_id}_{uuid.uuid4().hex[:8]}"

    store = VectorStore(namespace=namespace)
    yield store

    # Cleanup namespace
    store.clear_namespace(namespace)
```

**4. Environment Variable Isolation**
```python
@pytest.fixture(scope="function", autouse=True)
def isolated_environment(monkeypatch):
    """Auto-isolate environment for every test."""
    # Snapshot current environment
    original_env = os.environ.copy()

    yield monkeypatch

    # Restore environment (monkeypatch does this automatically)
```

**Deliverables**:
- `conftest.py` with isolation fixtures
- All tests use `isolated_agency` instead of bare `Agency()`
- 100% pass rate with `-n 2` workers (prove isolation works)

---

### Phase 3: Smart Test Orchestration (Week 5-6)

**Objective**: Intelligently distribute tests across workers based on resource usage

**1. Test Grouping by Resource Type**
```python
# pytest.ini or conftest.py
pytest_configure():
    # Group tests by resource type to minimize conflicts
    groups = {
        "filesystem": tests using file operations,
        "database": tests using VectorStore/Firestore,
        "network": tests using ports/API calls,
        "pure": tests with no shared state (fastest)
    }

    # pytest-xdist loadgroup strategy
    # Tests in same group run on same worker (minimize cleanup)
    # Pure tests distributed across all workers (max parallelism)
```

**2. Dynamic Worker Allocation**
```python
# run_tests.py enhancement
def get_optimal_worker_count(test_profile: TestProfile) -> int:
    """
    Determine worker count based on:
    - Available memory (existing logic)
    - Test mix (more pure tests = more workers)
    - Resource contention risk
    """
    memory_based = get_safe_worker_count()  # Existing

    # Calculate contention risk
    contention_risk = (
        test_profile.serial_only_tests / test_profile.total_tests
    )

    if contention_risk > 0.5:
        # Lots of serial-only tests - cap workers
        return min(memory_based, 4)
    elif contention_risk > 0.2:
        # Moderate contention - standard parallelism
        return min(memory_based, 8)
    else:
        # Mostly parallel-safe - max parallelism
        return min(memory_based, 12)
```

**3. Two-Pass Execution Strategy**
```python
# run_tests.py
def run_tests_with_smart_orchestration():
    """
    Pass 1: Parallel-safe tests (-n 8)
    Pass 2: Serial-only tests (-n 1)
    """
    # Pass 1: Fast parallel tests
    run_pytest(
        markers="-m 'parallel_safe'",
        workers=8,
        expected_time="3-4 min"
    )

    # Pass 2: Serial-only tests
    run_pytest(
        markers="-m 'serial_only'",
        workers=1,
        expected_time="2-3 min"
    )

    # Total: 5-7 minutes (vs 15 min serial, 29 failures parallel)
```

**Deliverables**:
- Enhanced `run_tests.py` with two-pass strategy
- Test grouping by resource type
- 100% pass rate with `-n 8` workers (prove full parallelism works)

---

### Phase 4: Continuous Validation (Week 7+)

**Objective**: Prevent regression - ensure new tests are parallel-safe

**1. Pre-commit Hook for Test Isolation**
```python
# .pre-commit-config.yaml addition
- repo: local
  hooks:
  - id: test-isolation-check
    name: Check new tests for parallel safety
    entry: python tools/test_isolation_analyzer.py
    language: system
    types: [python]
    files: ^tests/.*\.py$
```

**2. CI Matrix Testing**
```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    workers: [1, 4, 8, 12]  # Test with different parallelism levels

steps:
  - name: Run tests with ${{ matrix.workers }} workers
    env:
      PYTEST_WORKERS: ${{ matrix.workers }}
    run: python run_tests.py --run-all

  - name: Fail if results differ across worker counts
    run: |
      # All worker counts must have identical results
      # No "works with -n 1 but fails with -n 8" scenarios
```

**3. Flakiness Dashboard**
```python
# tools/test_flakiness_detector.py
class FlakinessDetector:
    """Track tests that fail inconsistently across runs."""

    def detect_flaky_tests(self, runs: List[TestRun]) -> List[str]:
        """
        Identify tests that:
        - Pass sometimes, fail sometimes (flaky)
        - Fail only with specific worker counts (isolation issue)
        """
        flaky = []
        for test in all_tests:
            pass_rate = test.passes / test.total_runs
            if 0.1 < pass_rate < 0.9:
                flaky.append(test.name)
        return flaky
```

**Deliverables**:
- Pre-commit hook prevents new unsafe tests
- CI matrix validates parallel execution
- Flakiness dashboard tracks regression

---

## Implementation Timeline

| Phase | Duration | Outcome |
|-------|----------|---------|
| **Phase 1**: Classification | 2 weeks | All tests marked `parallel_safe` or `serial_only` |
| **Phase 2**: Fixtures | 2 weeks | 100% pass rate with `-n 2` workers |
| **Phase 3**: Orchestration | 2 weeks | 100% pass rate with `-n 8` workers, 3x speedup |
| **Phase 4**: Validation | Ongoing | Prevent regression, maintain 100% pass rate |

**Total**: 6 weeks to full parallel execution

---

## Expected Results

### Before (Current State)
```bash
python run_tests.py --run-all
# Workers: 1 (serial)
# Time: ~15 minutes
# Pass rate: 100% (5,714 passed, 146 skipped)
```

### After (Phase 3 Complete)
```bash
python run_tests.py --run-all
# Workers: 8 (intelligent parallelism)
# Time: ~5 minutes (3x faster)
# Pass rate: 100% (5,714 passed, 146 skipped)
```

### Two-Pass Breakdown
```
Pass 1: Parallel-safe tests (80% of suite)
  - Workers: 8
  - Tests: ~4,500 tests
  - Time: ~3 minutes
  - Pass rate: 100%

Pass 2: Serial-only tests (20% of suite)
  - Workers: 1
  - Tests: ~1,200 tests
  - Time: ~2 minutes
  - Pass rate: 100%

Total: ~5 minutes (vs 15 min serial)
```

---

## Key Architectural Changes

### 1. Agency Singleton Refactoring
**Problem**: Shared singleton across tests causes race conditions

**Solution**: Dependency injection with factory pattern
```python
# Before (singleton - race conditions)
class Agency:
    _instance = None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Agency()
        return cls._instance

# After (factory - test isolation)
@pytest.fixture
def agency_factory(isolated_workspace):
    """Factory creates fresh instances per test."""
    def _create_agency(**kwargs):
        return Agency(
            workspace=isolated_workspace,
            memory_dir=isolated_workspace / "memory",
            **kwargs
        )
    return _create_agency

# Test usage
def test_agency_feature(agency_factory):
    agency = agency_factory(model="gpt-5")
    # Fresh instance, no shared state
```

### 2. File System Operations
**Problem**: Tests write to `/tmp` causing conflicts

**Solution**: Worker-scoped temp directories via `tmp_path` fixture
```python
# Before (conflicts)
def test_file_write():
    with open("/tmp/test.txt", "w") as f:
        f.write("data")

# After (isolated)
def test_file_write(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")
```

### 3. Environment Variables
**Problem**: Tests mutate `os.environ` globally

**Solution**: `monkeypatch` fixture (pytest built-in)
```python
# Before (global mutation)
def test_env_var():
    os.environ["KEY"] = "value"
    # Other tests see this change!

# After (isolated)
def test_env_var(monkeypatch):
    monkeypatch.setenv("KEY", "value")
    # Auto-restored after test
```

---

## Cost-Benefit Analysis

### Costs
- **Development Time**: 6 weeks (1 engineer)
- **Complexity**: Increased test infrastructure
- **Maintenance**: Ongoing fixture maintenance

### Benefits
- **3x Faster CI/CD**: 15min → 5min
- **3x Faster Local Dev**: Faster feedback loop
- **Better Test Quality**: Explicit isolation = fewer bugs
- **Scalability**: Can scale to 12+ workers on beefy machines

### ROI
- **Developer Time Saved**: ~10 minutes per test run
- **Test Runs per Day**: ~10-20 (during active development)
- **Time Saved per Day**: 100-200 minutes (1.5-3 hours)
- **Payback Period**: ~2 weeks

---

## Alternative: Pytest Plugins

Consider existing plugins for test isolation:

1. **pytest-xdist** (already using)
   - Pros: Mature, well-tested
   - Cons: Doesn't auto-isolate resources

2. **pytest-randomly**
   - Randomizes test order to catch hidden dependencies
   - Good for validating isolation

3. **pytest-split**
   - Intelligent test splitting across workers
   - Considers test duration for optimal distribution

4. **pytest-timeout**
   - Prevents hung tests from blocking workers
   - Already configured (120s timeout)

---

## Success Metrics

1. **Pass Rate**: 100% with `-n 8` workers (no regression)
2. **Execution Time**: ≤ 6 minutes (3x speedup from serial)
3. **Flakiness**: 0% (no tests fail inconsistently)
4. **Developer Satisfaction**: Faster feedback loop

---

## Next Steps

1. **Approve Roadmap**: Review and approve this plan
2. **Create Epic**: Break down into implementable tasks
3. **Phase 1 Sprint**: Start with test classification
4. **Iterative Validation**: Validate at end of each phase

---

**Related Documentation**:
- `docs/TEST_RACE_CONDITIONS_FIX.md` - Current serial execution fix
- `tools/memory_aware_test_runner.py` - Worker count logic
- ADR-023 - Memory-aware test execution

**Status**: ✅ Roadmap complete, awaiting approval
**Priority**: High (quality of life improvement)
**Effort**: 6 weeks
**Impact**: 3x faster test execution
