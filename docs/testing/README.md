# Testing Documentation Index

**Quick access to all test-related documentation and tools**

---

## 🚀 Quick Start

**Want to speed up tests immediately?**

```bash
# 1. Install parallel execution (5 min)
pip install pytest-xdist
pytest -n auto  # 2-4x faster

# 2. Use smart test selection (200x faster for dev!)
./scripts/run_smart_tests.sh
```

→ **[Quick Start Guide](QUICK_START_PROFILING.md)**

---

## 📚 Documentation

### Performance Optimization

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[Quick Start Guide](QUICK_START_PROFILING.md)** | TL;DR commands and quick wins | Start here! |
| **[Optimization Plan](PERFORMANCE_OPTIMIZATION.md)** | 3-phase roadmap to <60s | Planning optimizations |
| **[Tools Summary](PROFILING_TOOLS_SUMMARY.md)** | Complete implementation details | Understanding the tools |

### Testing Strategy

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[Constitution](../../constitution.md)** | TDD requirements, Article II | Before writing tests |
| **[pytest.ini](../../pytest.ini)** | Test configuration and markers | Configuring test runs |
| **[Run Tests Guide](../../run_tests.py)** | Test runner documentation | Running test suites |

---

## 🔧 Available Tools

### Python Modules (`/tools/`)

#### 1. Performance Profiler
**File**: `tools/performance_profiling.py`

**Purpose**: Profile test suite and identify bottlenecks

```bash
# Profile full suite
python -m tools.performance_profiling

# With custom settings
python -m tools.performance_profiling \
  --test-path tests/ \
  --output docs/testing/PERFORMANCE_PROFILE.md \
  --threshold 1.0
```

**Output**:
- `PERFORMANCE_PROFILE.md` - Slowest tests, bottlenecks
- `PERFORMANCE_PROFILE.json` - Raw profiling data

#### 2. Test Optimizer
**File**: `tools/test_optimizer.py`

**Purpose**: Analyze test suite for optimization opportunities

```bash
# Analyze full suite
python -m tools.test_optimizer \
  --test-dir tests/ \
  --output docs/testing/TEST_OPTIMIZATION.md
```

**Output**:
- `TEST_OPTIMIZATION.md` - Parallelization, mocking, consolidation opportunities

**Real Results**:
- 1,340 parallelizable tests
- 141 tests needing mocks
- 137.5s potential savings

#### 3. Smart Test Selector
**File**: `tools/smart_test_selection.py`

**Purpose**: Run only tests affected by code changes

```bash
# Compare to last commit
python -m tools.smart_test_selection \
  --since HEAD~1 \
  --output selected_tests.txt \
  --report docs/testing/SMART_SELECTION.md

# Run selected tests
pytest $(cat selected_tests.txt)
```

**Output**:
- `selected_tests.txt` - List of affected tests
- `SMART_SELECTION.md` - Selection report

**Real Results**:
- 17 files changed → 12 tests (0.5% of suite)
- **203x speedup** for incremental development

### Shell Scripts (`/scripts/`)

#### 1. Profile Tests
**File**: `scripts/profile_tests.sh`

```bash
# Profile full suite
./scripts/profile_tests.sh

# With custom threshold
./scripts/profile_tests.sh tests/ 0.5
```

#### 2. Run Smart Tests
**File**: `scripts/run_smart_tests.sh`

```bash
# Compare to last commit
./scripts/run_smart_tests.sh

# Compare to main branch
./scripts/run_smart_tests.sh main

# With pytest options
./scripts/run_smart_tests.sh HEAD~1 -v --tb=short
```

#### 3. Optimize Tests
**File**: `scripts/optimize_tests.sh`

```bash
# Analyze full suite
./scripts/optimize_tests.sh

# Analyze specific directory
./scripts/optimize_tests.sh tests/unit/
```

---

## 📊 Performance Metrics

### Current Baseline
- **Runtime**: 226 seconds
- **Test Count**: 2,438 tests
- **Average**: 0.09s per test

### Optimization Potential

| Phase | Duration | Actions | Runtime | Speedup |
|-------|----------|---------|---------|---------|
| Current | - | Baseline | 226s | 1.0x |
| Phase 1 | 1 day | Parallel + mocks | ~100s | 2.3x |
| Phase 2 | 3 days | Fixtures + E2E | ~70s | 3.2x |
| Phase 3 | 1 week | Consolidation | <60s | **3.8x** ✅ |

### Already Achieved
- ✅ Smart selection: **203x speedup**
- ✅ 1,340 parallelizable tests identified
- ✅ 141 mocking opportunities found
- ✅ 137.5s savings potential

---

## 🎯 Common Workflows

### Development Workflow

```bash
# 1. Make code changes
vim agency_code_agent/coder.py

# 2. Run affected tests only (fast!)
./scripts/run_smart_tests.sh

# 3. Before commit: full validation
python run_tests.py --run-all
```

### Profiling Workflow

```bash
# 1. Identify bottlenecks
./scripts/profile_tests.sh

# 2. Analyze optimizations
./scripts/optimize_tests.sh

# 3. Review reports
cat docs/testing/PERFORMANCE_PROFILE.md
cat docs/testing/TEST_OPTIMIZATION.md

# 4. Implement fixes and re-profile
./scripts/profile_tests.sh
```

---

**Start Here**: [Quick Start Guide](QUICK_START_PROFILING.md) 🚀

---

## Phase 2A: Test Bloat Removal

**Status**: READY FOR EXECUTION
**Goal**: Remove 731 experimental tests (24.7% reduction) to achieve Mars-ready efficiency

### Quick Access

- **Executive Summary**: [PHASE_2A_EXECUTIVE_SUMMARY.md](PHASE_2A_EXECUTIVE_SUMMARY.md) - Start here (5 min read)
- **Quick Reference**: [PHASE_2A_QUICK_REFERENCE.md](PHASE_2A_QUICK_REFERENCE.md) - Fast lookup table
- **Full Analysis**: [PHASE_2A_BLOAT_ANALYSIS.md](PHASE_2A_BLOAT_ANALYSIS.md) - Complete report
- **Data (JSON)**: [phase_2a_bloat_detailed.json](phase_2a_bloat_detailed.json) - Machine-readable
- **Execution Script**: [../scripts/phase_2a_delete_bloat.sh](../../scripts/phase_2a_delete_bloat.sh)

### Analysis Results

```
Current State:  2,965 tests, 153 files, ~296s runtime
After Phase 2A: 2,234 tests, 118 files, ~223s runtime
Impact:         -731 tests (-24.7%), 1.33x faster
```

### Bloat Breakdown

| Category | Files | Tests | Lines | Action |
|----------|-------|-------|-------|--------|
| Trinity Protocol | 19 | 139 | 9,364 | DELETE |
| DSPy A/B Testing | 6 | 248 | 6,469 | DELETE |
| Archived Legacy | 7 | 24 | 4,514 | DELETE |
| Other Experimental | 3 | 320 | 2,500 | DELETE |
| **Total** | **35** | **731** | **22,847** | **REMOVE** |

### Execute Now

```bash
cd /Users/am/Code/Agency
bash scripts/phase_2a_delete_bloat.sh
```

### NECESSARY Framework

Tests scored 0-9 on these criteria:
1. **N**ecessary - Tests production code (not experimental)
2. **E**xplicit - Clear what's being tested
3. **C**omplete - Tests full behavior
4. **E**fficient - Fast execution (<1s ideal)
5. **S**table - No flaky/timing dependencies
6. **S**coped - One concern per test
7. **A**ctionable - Clear failure messages
8. **R**elevant - Tests current architecture
9. **Y**ieldful - Catches real bugs

**Threshold**: Tests scoring <4 are bloat. However, experimental tests are removed regardless of score.

### Next Phases

- **Phase 2A.2**: Consolidate 10 duplicate test groups (~100 tests)
- **Phase 2B**: Optimize slow/complex tests
- **Phase 2C**: Mars-ready parallelization and caching

---

*Generated by Auditor Agent - 2025-10-03*
