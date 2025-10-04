# Performance Profiling - Quick Start Guide

**Goal**: Speed up test suite from 226s to <60s

---

## 🚀 TL;DR - Run This Now

```bash
# 1. Install parallel execution
pip install pytest-xdist

# 2. Run tests 2-4x faster immediately
pytest -n auto

# 3. For development: run only affected tests (200x faster!)
./scripts/run_smart_tests.sh
```

---

## 📊 Available Tools

### 1. Smart Test Selection (Use Daily)

**Run only tests affected by your changes** - 200x speedup!

```bash
# Compare to last commit
./scripts/run_smart_tests.sh

# Compare to main branch
./scripts/run_smart_tests.sh main

# Compare to 5 commits ago
./scripts/run_smart_tests.sh HEAD~5
```

**Real Results**:
- Changed 17 files → Run only 12 tests (0.5% of suite)
- Time: 1.8s instead of 226s
- **203x faster**

### 2. Performance Profiling

**Find slow tests and bottlenecks**:

```bash
# Profile full test suite
./scripts/profile_tests.sh

# Show tests slower than 0.5s
./scripts/profile_tests.sh tests/ 0.5
```

**Output**:
- `docs/testing/PERFORMANCE_PROFILE.md` - Slowest tests, bottlenecks
- `docs/testing/PERFORMANCE_PROFILE.json` - Raw data

### 3. Optimization Analysis

**Identify what to fix**:

```bash
# Analyze full suite
./scripts/optimize_tests.sh

# Analyze specific directory
./scripts/optimize_tests.sh tests/unit/
```

**Output**:
- `docs/testing/TEST_OPTIMIZATION.md` - Action plan

**Real Results**:
- 1,340 tests can run in parallel
- 141 tests need mocks
- 137.5s savings identified

---

## ⚡ Quick Wins (Do These First)

### 1. Enable Parallel Execution (5 minutes)

```bash
# Install
pip install pytest-xdist

# Run with auto-detection
pytest -n auto

# Or specify workers
pytest -n 4
```

**Impact**: 2-4x speedup immediately

### 2. Use Smart Selection in Pre-Commit (10 minutes)

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
./scripts/run_smart_tests.sh --since HEAD
```

**Impact**: 100-200x speedup for typical changes

### 3. Add Mocks to Top 10 Slowest Tests (1 hour)

```bash
# Find slow tests
./scripts/profile_tests.sh

# Review PERFORMANCE_PROFILE.md
# Add mocks to database/network calls
```

**Impact**: 10-20s savings

---

## 📈 Optimization Roadmap

### Phase 1: Quick Wins (1 day) → 226s to ~100s

- [x] Profiling tools created
- [ ] Install pytest-xdist
- [ ] Enable parallel execution
- [ ] Mock external API calls (141 tests identified)

### Phase 2: Medium Effort (3 days) → 100s to ~70s

- [ ] Optimize database fixtures (session scope)
- [ ] Parallelize E2E tests
- [ ] Add smart selection to CI

### Phase 3: Advanced (1 week) → 70s to <60s

- [ ] Test consolidation
- [ ] Remove redundant coverage
- [ ] Fine-tune parallel groups

---

## 📝 Common Commands

### Development Workflow

```bash
# 1. Make changes
git add .

# 2. Run affected tests only
./scripts/run_smart_tests.sh

# 3. Before commit, run full suite
python run_tests.py --run-all
```

### Profiling Workflow

```bash
# 1. Profile performance
./scripts/profile_tests.sh

# 2. Analyze optimizations
./scripts/optimize_tests.sh

# 3. Review reports
cat docs/testing/PERFORMANCE_PROFILE.md
cat docs/testing/TEST_OPTIMIZATION.md
```

### CI/CD Integration

```bash
# Run only affected tests in PR
python -m tools.smart_test_selection \
  --since origin/main \
  --output selected_tests.txt

pytest $(cat selected_tests.txt)
```

---

## 🎯 Success Metrics

### Current State
- Runtime: 226s
- Tests: 2,438
- Average: 0.09s/test

### Target State
- Runtime: <60s ✅ Achievable
- Speedup: 3.8x
- Parallel: 80%+ of tests

### Already Achieved
- Smart selection: **203x speedup** for incremental changes
- Identified: 1,340 parallelizable tests
- Found: 141 tests needing mocks
- Estimated: 137.5s savings potential

---

## 🔍 Detailed Documentation

- **Full Plan**: `docs/testing/PERFORMANCE_OPTIMIZATION.md`
- **Tool Summary**: `docs/testing/PROFILING_TOOLS_SUMMARY.md`
- **This Guide**: `docs/testing/QUICK_START_PROFILING.md`

---

## 💡 Tips

1. **TDD Workflow**: Use `./scripts/run_smart_tests.sh` for instant feedback
2. **Before Commit**: Always run full suite with `python run_tests.py --run-all`
3. **CI Optimization**: Use smart selection for PR checks, full suite for main
4. **Monitor Performance**: Re-run profiling after changes to track progress

---

**Remember**: Smart test selection gives you **200x speedup** right now, no code changes needed!

```bash
./scripts/run_smart_tests.sh
```

🚀 Start here, optimize from there.
