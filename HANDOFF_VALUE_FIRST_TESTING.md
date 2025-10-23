# Handoff: Value-First Testing Revolution

**Date**: 2025-10-23
**Session**: Value-First Testing made Constitutional Law
**Status**: Audit running, ready for next steps

---

## What Was Accomplished

### ✅ Constitutional Amendment
- **Article VII added**: Value-First Testing Philosophy
- **Principle**: Quality > Quantity. Delete score <10, Keep score >20. Let QUALITY determine count.
- **No arbitrary targets**: Removed "2,000-3,000 tests", "70/30 ratio" - these come from ACTUAL audit results

### ✅ Tools Built
- `scripts/test_value_audit.py` - Scores all 5,408 tests by VALUE
- **V5 Upgrade**: Empirical scoring with actual runtime data, CI failure history, git churn analysis
- **Scoring**: bug_detection * 10 + critical_path * 5 + integration * 3 - runtime * 0.1 - maintenance * 2

### ✅ Documentation
- ADR-033: Value-First Testing Philosophy
- ADR-034: Empirical Test Value Scoring (V5)
- TEST_PRUNING_PROPOSAL.md: Detailed examples
- VALUE_FIRST_REVOLUTION_COMPLETE.md: Full summary

---

## V5 Empirical Scoring Quick Start

### What's New in V5
V5 replaces keyword-based heuristics with **real empirical data**:
- ✅ **Actual runtime data** from pytest JSON reports (not sleep pattern guesses)
- ✅ **CI failure history** from `.audit/failure_history.sqlite` (proven bug detectors)
- ✅ **Git churn analysis** from repository history (maintenance burden)
- ✅ **Configurable weights** via `weights.yaml` (tune for your domain)
- ✅ **100% backward compatible** (V4 fallback if empirical data unavailable)

### Prerequisites
- `weights.yaml` in root directory (already configured)
- **Optional**: `.audit/runtime_cache.json` for actual test runtimes
- **Optional**: `.git/` for churn analysis (auto-detected)
- **Optional**: `.audit/failure_history.sqlite` for CI failure bonuses

### Basic Usage
```bash
# Run V5 audit (auto-detects empirical data sources)
python scripts/test_value_audit.py

# Force V4 fallback (disable V5)
AUDIT_USE_V5=false python scripts/test_value_audit.py

# V5 with verbose logging
python scripts/test_value_audit.py --log-level=DEBUG
```

### Scoring Modes
V5 automatically adapts to available data:

- **V5_FULL**: All empirical data available (runtime + CI + git + weights)
- **V5_PARTIAL**: Some empirical data available (e.g., git + weights only)
- **V4_FALLBACK**: No empirical data (uses heuristics)

Check audit output metadata to see which mode was active:
```json
{
  "metadata": {
    "scoring_version": "V5_PARTIAL",
    "v5_enabled": true,
    "data_sources": {
      "weights": true,
      "runtime": false,
      "git_churn": true,
      "ci_failures": false
    }
  }
}
```

### Configuring Scoring Weights

The `weights.yaml` file controls V5 scoring behavior. Edit to tune for your codebase:

```yaml
# Bug Detection (0-10 scale)
bug_detection_weight: 10.0  # Higher = prioritize bug catchers

# Critical Path (0-10 scale)
critical_path_weight: 5.0   # Higher = prioritize core logic tests

# Integration Bonus (0-10 scale)
integration_bonus_weight: 3.0  # Higher = favor integration tests

# Runtime Penalty (non-linear)
runtime_penalty:
  fast_threshold: 10.0        # Tests <10s: minimal penalty
  moderate_threshold: 30.0    # Tests 10-30s: moderate penalty
  slow_threshold: 30.0        # Tests >30s: exponential penalty
  base_weight: 0.1

# Maintenance Burden
maintenance_burden_weight: 2.0

# Mock Penalties
mock_penalties:
  external_mock_weight: 0.3   # DB/API mocks (acceptable)
  internal_mock_weight: 0.8   # Class mocks (code smell)

# Git Churn
git_churn:
  churn_weight: 1.5           # Co-change frequency penalty
  age_penalty_weight: 0.5     # Old test penalty

# Failure History
failure_history:
  failure_bonus_weight: 5.0   # Per bug caught
  flaky_penalty: -5.0         # Unreliable tests
```

**Pro Tip**: Use `scripts/grid_search_tuner.py` to auto-optimize weights based on manual labels.

### Empirical Data Sources

V5 uses real data when available:

#### 1. Actual Runtime Data
**Source**: `.audit/runtime_cache.json`
**How to Generate**:
```bash
# Run tests with timing data
pytest tests/ --json-report --json-report-file=.audit/runtime_cache.json
```

**Fallback**: Heuristic estimation (sleep patterns, docker keywords)

#### 2. CI Failure History
**Source**: `.audit/failure_history.sqlite`
**How to Generate**:
```bash
python scripts/ci_failure_parser.py --days=90
```

**Fallback**: failure_bonus = 0

#### 3. Git Churn Analysis
**Source**: `.git/` repository
**How to Use**: Automatically detected if repository initialized

**Fallback**: churn_penalty = 0, age_penalty = 0

**Best Practice**: Run all three for highest scoring accuracy!

### Understanding V5 Scores

V5 scores differ from V4 due to empirical data:

| Score Range | Category | Action | V5 Indicators |
|-------------|----------|--------|---------------|
| **≥20** | HIGH | KEEP | Integration tests, proven bug catchers (CI failures), recent tests |
| **10-20** | MEDIUM | REVIEW | Complex algorithms, moderate runtime, some mocks |
| **<10** | LOW | DELETE | Mocking hell (10+ mocks), slow (>60s), brittle (high churn) |

**Example V5 Score Breakdown**:
```json
{
  "name": "test_agent_memory_integration",
  "total_score": 28.5,
  "category": "HIGH",
  "action": "KEEP",
  "reason": "Integration test with proven bug detection",

  "actual_runtime_seconds": 2.3,
  "runtime_source": "pytest_json",
  "failure_bonus": 10.0,
  "churn_burden": 0.5,
  "git_commits": 3,
  "git_age_years": 0.5
}
```

### V4 → V5 Migration

**Backward Compatible**: Existing workflows unchanged!

**What Changed**:
- ✅ Scores more accurate (empirical data vs keywords)
- ✅ Proven bug detectors identified (CI history)
- ✅ Slow tests heavily penalized (exponential, not linear)
- ✅ Configurable weights (weights.yaml)

**What Stayed Same**:
- ✅ CLI interface identical
- ✅ Output format compatible
- ✅ Categories unchanged (HIGH/MEDIUM/LOW)
- ✅ Actions unchanged (KEEP/REVIEW/DELETE/CONSOLIDATE)

**Recommended**: Review weights.yaml and tune for your domain!

---

## Current State

**Test Value Audit**:
- **Status**: Running (PID 21540)
- **Progress**: Scoring 5,408 tests
- **Output**: Will generate deletion candidates, consolidation opportunities, high-value list

**Check progress**:
```bash
tail -f audit_value_final_*.log
ps -p 21540  # Check if still running
```

---

## What Comes From Audit (Data-Driven, Not Prescribed)

The audit will generate based on ACTUAL scores:
1. **candidates_to_delete.txt** - Tests with score <10 (mocking hell, implementation details)
2. **candidates_to_consolidate.txt** - Redundant tests (parameterize)
3. **high_value_tests.txt** - Tests with score >20 (integration, critical path, security)

**Final test count = Whatever QUALITY dictates** (not 2,000-3,000)

---

## Next Steps Options

### Option A: Wait for Audit, Manual Review
```bash
# When audit completes:
cat audit_reports/candidates_to_delete_*.txt | head -100
# Review top candidates manually
# Create approved_deletions.txt (human judgment)
# Run batch delete script
```

### Option B: Autonomous Pruning with /primeA
```bash
/primeA "Review test value audit results and autonomously prune low-value tests (<10 score), consolidate redundant tests, verify test suite still passes after deletions"
```

### Option C: Targeted Improvement (No Deletion)
```bash
/primeA "Use test value audit to identify top 10 files with most low-value tests, refactor them to be integration tests instead of mocking hell"
```

---

## Key Principle (Corrected)

**WRONG** (what I initially said):
- Target 2,000-3,000 tests
- Target 70% integration, 30% unit
- Target <15 min CI/CD

**RIGHT** (corrected based on your feedback):
- Delete tests with score <10 (quality threshold)
- Keep tests with score >20 (quality threshold)
- Let ACTUAL QUALITY determine final count
- Measure improvement (faster CI/CD, fewer breakages) vs prescribe numbers

**The audit TELLS US the answer, we don't prescribe it upfront.**

---

## Files Modified

1. `constitution.md` - Article VII (removed arbitrary targets)
2. `docs/adr/ADR-033-value-first-testing-philosophy.md` - Created
3. `scripts/test_value_audit.py` - Created (505 lines)
4. Various summary docs

---

## Recommended Next Action

**Let audit complete** (~2 min), then:

```bash
/primeA "Execute Article VII: Review test value audit results, delete tests with score <10 (after top-100 manual verification), consolidate redundant tests, measure improvement in CI/CD time and test suite health. Final test count determined by QUALITY, not targets."
```

**Key**: /primeA will use Article VII as constitutional guidance, but rely on AUDIT DATA for decisions, not prescribed numbers.

---

## Context for Next Session

- **Problem identified**: 6,554 tests, many low-value (mocking hell, implementation details)
- **Solution**: Made Value-First Testing constitutional law (Article VII)
- **Audit running**: Will identify actual deletion/consolidation candidates
- **No prescriptive targets**: Quality determines count, not arbitrary goals
- **Next**: Execute pruning based on audit results (score thresholds)

---

**Files to check when ready**:
- `audit_value_final_*.log` - Audit progress/results
- `audit_reports/test_value_audit_*.json` - Full scored results
- `audit_reports/candidates_to_delete_*.txt` - Actual deletion list

**The quality bar is set (score <10 = DELETE, score >20 = KEEP). The audit tells us WHO meets it.**
