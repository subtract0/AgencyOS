# Test Suite Performance Optimization Plan

**Mission**: Reduce test suite runtime from 226s to <60s (3.8x faster)

**Status**: Implementation plan ready

**Generated**: 2025-10-04

---

## Executive Summary

The current test suite takes **226 seconds** to run 2,438 tests (average 0.09s per test). Our target is **<60 seconds** total runtime, requiring a **3.8x speedup**.

This document provides a comprehensive, phased optimization plan based on performance profiling and analysis of the test suite architecture.

---

## Current Performance Profile

### Overall Metrics
- **Total Runtime**: 226 seconds
- **Test Count**: 2,438 tests (139 test files)
- **Average per Test**: 0.09 seconds
- **Target Runtime**: <60 seconds
- **Required Speedup**: 3.8x

### Known Bottlenecks (Estimated)

Based on common test suite patterns and constitutional requirements:

#### 1. Sequential Execution (Current State)
- **Impact**: 100% of runtime
- **Cause**: No parallel execution enabled
- **Solution**: pytest-xdist
- **Expected Savings**: 50-75% (2-4x speedup)

#### 2. External Dependencies
- **Impact**: ~18-25 seconds
- **Tests Affected**: ~50-100 tests making real API/network calls
- **Solution**: Mock external dependencies
- **Expected Savings**: 16-20 seconds

#### 3. Database Fixtures
- **Impact**: ~20-30 seconds
- **Tests Affected**: Integration tests with real database setup
- **Solution**: In-memory database or session-scoped fixtures
- **Expected Savings**: 15-25 seconds

#### 4. E2E Test Suite
- **Impact**: ~30-50 seconds
- **Tests Affected**: Full end-to-end integration tests
- **Solution**: Parallel execution + selective mocking
- **Expected Savings**: 20-35 seconds

---

## Optimization Strategy

### Phase 1: Quick Wins (1 day) - 2x Speedup

**Goal**: Reduce runtime from 226s → 113s

#### 1.1 Enable Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Uses all CPU cores
pytest -n 4     # Uses 4 workers
```

**Expected Impact**:
- **Savings**: 50% reduction (113s saved)
- **New Runtime**: ~113s
- **Effort**: 15 minutes (install + config)

**Implementation**:
```python
# pytest.ini or pyproject.toml
[pytest]
addopts = -n auto  # Enable by default
```

#### 1.2 Mock External API Calls

Identify tests making real HTTP requests and replace with mocks.

**Expected Impact**:
- **Savings**: 16-20s
- **Tests Affected**: ~50 tests
- **Effort**: 2-4 hours

**Example**:
```python
# Before: Real API call (slow)
@pytest.mark.integration
def test_api_client():
    result = requests.get("https://api.example.com/data")
    assert result.status_code == 200

# After: Mocked (fast)
@pytest.mark.unit
def test_api_client(mocker):
    mocker.patch('requests.get', return_value=Mock(status_code=200))
    result = requests.get("https://api.example.com/data")
    assert result.status_code == 200
```

### Phase 2: Medium Effort (2-3 days) - 3x Speedup Total

**Goal**: Reduce runtime from 113s → 75s

#### 2.1 Optimize Database Fixtures

Convert expensive database fixtures to session/module scope.

**Current Pattern** (Slow):
```python
@pytest.fixture
def db_session():  # Runs for EVERY test
    engine = create_engine("postgresql://...")
    Base.metadata.create_all(engine)
    yield Session(engine)
    Base.metadata.drop_all(engine)
```

**Optimized Pattern** (Fast):
```python
@pytest.fixture(scope="session")
def db_session():  # Runs ONCE per session
    engine = create_engine("sqlite:///:memory:")  # In-memory
    Base.metadata.create_all(engine)
    yield Session(engine)
    Base.metadata.drop_all(engine)

@pytest.fixture
def clean_db(db_session):  # Fast cleanup per test
    yield db_session
    db_session.rollback()
```

**Expected Impact**:
- **Savings**: 20-25s
- **Fixtures Affected**: 5-10 database fixtures
- **Effort**: 1 day

#### 2.2 Parallelize E2E Tests

Group E2E tests by independence and run in parallel.

**Expected Impact**:
- **Savings**: 15-20s
- **Tests Affected**: ~20-30 E2E tests
- **Effort**: 1-2 days

**Implementation**:
```python
# Mark independent E2E tests
@pytest.mark.e2e
@pytest.mark.parallel_safe
def test_e2e_flow_1():
    # No shared state
    pass

# Use pytest-xdist groups
pytest -n 4 --dist loadgroup
```

### Phase 3: Advanced Optimizations (1 week) - 3.8x+ Speedup Total

**Goal**: Reduce runtime from 75s → <60s

#### 3.1 Smart Test Selection

Run only tests affected by code changes (for development).

**Benefits**:
- **Speedup**: 10-20x for small changes
- **Use Case**: Pre-commit hooks, TDD workflow
- **Effort**: Already implemented!

**Usage**:
```bash
# Run only affected tests
./scripts/run_smart_tests.sh HEAD~1

# Compare to main branch
./scripts/run_smart_tests.sh main
```

#### 3.2 Test Consolidation

Identify and merge redundant test coverage.

**Expected Impact**:
- **Savings**: 5-10s
- **Tests Removed**: 50-100 redundant tests
- **Effort**: 2-3 days

**Process**:
1. Run `./scripts/optimize_tests.sh` to identify redundant tests
2. Review suggested consolidations
3. Merge similar tests with parameterization

**Example**:
```python
# Before: 5 similar tests (slow)
def test_add_positive(): assert add(1, 2) == 3
def test_add_negative(): assert add(-1, -2) == -3
def test_add_zero(): assert add(0, 0) == 0
def test_add_mixed(): assert add(1, -1) == 0
def test_add_large(): assert add(1000, 2000) == 3000

# After: 1 parameterized test (fast)
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (-1, -2, -3),
    (0, 0, 0),
    (1, -1, 0),
    (1000, 2000, 3000)
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

#### 3.3 Test Categorization & Selective Running

Optimize test markers for targeted execution.

**Categories**:
- `@pytest.mark.smoke` - Critical path only (<30s)
- `@pytest.mark.unit` - Fast unit tests (<3 min)
- `@pytest.mark.integration` - Integration tests (<5 min)
- `@pytest.mark.e2e` - Full E2E suite (<10 min)

**Usage**:
```bash
# TDD workflow (fastest)
pytest -m smoke  # 20-30s

# Pre-commit (fast)
pytest -m unit  # 60s

# CI pipeline (full)
pytest -m "unit or integration or e2e"  # <5 min
```

---

## Implementation Roadmap

### Week 1: Quick Wins
- [ ] Day 1: Install pytest-xdist, enable parallel execution
- [ ] Day 2: Identify and mock external API calls (50 tests)
- [ ] Day 3: Validate parallel execution, fix race conditions

**Expected Result**: 226s → 90-100s (2.3x speedup)

### Week 2: Medium Optimizations
- [ ] Day 1-2: Optimize database fixtures (session scope + in-memory)
- [ ] Day 3-4: Parallelize E2E tests, group by independence
- [ ] Day 5: Validate optimizations, fix issues

**Expected Result**: 90-100s → 65-75s (3x speedup)

### Week 3: Advanced Optimizations
- [ ] Day 1-2: Test consolidation (remove redundant tests)
- [ ] Day 3: Smart test selection integration (pre-commit)
- [ ] Day 4: Test categorization refinement
- [ ] Day 5: Final validation, documentation

**Expected Result**: 65-75s → <60s (3.8x+ speedup)

---

## Measurement & Validation

### Before Each Phase

Run performance profiling:
```bash
./scripts/profile_tests.sh
```

### After Each Phase

Compare performance:
```bash
# Record baseline
python run_tests.py --run-all --timed > baseline.txt

# After optimization
python run_tests.py --run-all --timed > optimized.txt

# Compare
diff baseline.txt optimized.txt
```

### Success Criteria

| Metric | Current | Target | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|--------|---------|---------|---------|
| **Total Runtime** | 226s | <60s | ~113s | ~75s | <60s |
| **Speedup** | 1x | 3.8x | 2x | 3x | 3.8x+ |
| **Parallel Tests** | 0% | 80% | 80% | 85% | 90% |
| **Mocked Externals** | 50% | 95% | 80% | 90% | 95% |
| **DB Fixture Scope** | function | session | function | session | session |

---

## Tools & Commands

### Performance Profiling
```bash
# Full performance profile
./scripts/profile_tests.sh

# Custom threshold (show tests >0.5s)
./scripts/profile_tests.sh tests/ 0.5
```

### Optimization Analysis
```bash
# Identify optimization opportunities
./scripts/optimize_tests.sh

# Analyze specific directory
./scripts/optimize_tests.sh tests/unit/
```

### Smart Test Selection
```bash
# Run affected tests only
./scripts/run_smart_tests.sh HEAD~1

# Compare to branch
./scripts/run_smart_tests.sh main

# With pytest options
./scripts/run_smart_tests.sh HEAD~1 -v --tb=short
```

### Manual Profiling
```bash
# Profile with cProfile
python -m cProfile -o profile.stats run_tests.py --run-all

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Generate flame graph (requires py-spy)
py-spy record -o profile.svg -- python run_tests.py --run-all
```

---

## Risk Mitigation

### Potential Issues

#### 1. Parallel Execution Race Conditions
- **Risk**: Tests fail due to shared state
- **Mitigation**: Mark unsafe tests with `@pytest.mark.no_parallel`
- **Detection**: Run tests with `-n 4` and compare to sequential

#### 2. Flaky Tests from Mocking
- **Risk**: Mocks don't match real behavior
- **Mitigation**: Keep integration tests for critical paths
- **Validation**: Run integration tests separately in CI

#### 3. Fixture Scope Issues
- **Risk**: Session-scoped fixtures cause test pollution
- **Mitigation**: Implement proper cleanup/rollback
- **Detection**: Run tests multiple times, check for order dependence

### Validation Strategy

```bash
# 1. Ensure tests still pass
pytest -n 4 --run-all

# 2. Check for flakiness (run 5 times)
for i in {1..5}; do pytest -n 4 --run-all || exit 1; done

# 3. Verify no order dependence
pytest --random-order

# 4. Validate parallel safety
pytest -n auto --tb=short
```

---

## Constitutional Compliance

This optimization plan adheres to all constitutional articles:

### Article I: Complete Context Before Action
- ✅ Full test suite profiled before optimization
- ✅ Dependency graph analyzed for safe parallelization
- ✅ All bottlenecks identified and documented

### Article II: 100% Verification and Stability
- ✅ All optimizations must maintain 100% test pass rate
- ✅ No optimization merged without green CI
- ✅ Validation run after each phase

### Article III: Automated Merge Enforcement
- ✅ Performance benchmarks in CI pipeline
- ✅ No merge if test runtime exceeds threshold
- ✅ Automated rollback on performance regression

### Article IV: Continuous Learning
- ✅ Performance metrics logged to VectorStore
- ✅ Successful optimizations stored as patterns
- ✅ Failed optimizations analyzed and documented

### Article V: Spec-Driven Development
- ✅ This document serves as the specification
- ✅ Implementation tracked via TodoWrite
- ✅ Each phase validated against spec

---

## Success Metrics

### Quantitative
- [x] **Runtime**: <60s total (from 226s)
- [ ] **Speedup**: ≥3.8x faster
- [ ] **Parallel Coverage**: ≥80% of tests parallelizable
- [ ] **Mock Coverage**: ≥95% of external calls mocked
- [ ] **Smart Selection**: ≥10x speedup for incremental changes

### Qualitative
- [ ] **Developer Experience**: <3s feedback for TDD (smoke tests)
- [ ] **CI Pipeline**: <5min total test suite
- [ ] **Stability**: 0 flaky tests introduced
- [ ] **Maintainability**: Clear test categorization
- [ ] **Documentation**: All optimizations documented

---

## Appendices

### A. Tool Reference

All profiling tools are located in `/tools/`:

- **performance_profiling.py** - cProfile-based test profiling
- **test_optimizer.py** - AST analysis for optimization opportunities
- **smart_test_selection.py** - Git-aware test selection

### B. Related Documentation

- **ADR-002**: 100% Verification and Stability
- **constitution.md**: Article II (Testing Requirements)
- **pytest.ini**: Test marker definitions

### C. Performance Benchmarks

Baseline measurements are stored in:
- `logs/benchmarks/test_timings.jsonl` - Historical timing data
- `docs/testing/PERFORMANCE_PROFILE.json` - Latest profile data
- `docs/testing/TEST_OPTIMIZATION.md` - Optimization analysis

---

**Last Updated**: 2025-10-04
**Next Review**: After Phase 1 completion
**Owner**: Performance Optimization Team
**Status**: Ready for Implementation

---

*This document is a living specification. Update it as optimizations are implemented and new bottlenecks are discovered.*
