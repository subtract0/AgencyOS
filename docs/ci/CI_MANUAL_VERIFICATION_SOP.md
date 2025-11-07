# CI Manual Verification Standard Operating Procedure (SOP)

**Version**: 1.0
**Last Updated**: 2025-11-06
**Owner**: CI/CD Team
**Status**: Active

---

## Purpose

This SOP defines when and how to run expensive top-level test suites that are excluded from normal CI runs to maintain <15-minute build times for 90% of pushes.

---

## When to Run Top-Level Suites

### ✅ MUST Run (Before Merge)

Run top-level suites when changes affect:

1. **Core orchestration logic**
   - Files: `agency.py`, `shared/agent_context.py`, `shared/model_policy.py`
   - Reason: Top-level tests exercise full orchestrator workflows

2. **Constitutional enforcement**
   - Files: `constitution.md`, any constitutional gate logic
   - Reason: Must verify Articles I-V compliance

3. **Leap validation logic**
   - Files: Any leap-related code (leap 3-7 implementations)
   - Reason: Leap suites test end-to-end workflows

4. **Major refactors**
   - Changes: >500 lines modified, architectural changes
   - Reason: High risk of breaking integration points

5. **Before release to main**
   - Trigger: Final approval of feature branches
   - Reason: Extra verification before production merge

---

### ⚠️ SHOULD Run (Recommended)

Run top-level suites for:

1. **Agent modifications**
   - Files: `*_agent/` directories
   - Reason: Agents interact in complex ways tested by top-level suites

2. **Memory system changes**
   - Files: `agency_memory/`, VectorStore logic
   - Reason: Memory integration tested in leap suites

3. **Tool additions/changes**
   - Files: `tools/` with significant changes
   - Reason: Tool usage tested in E2E workflows

4. **Large PR reviews**
   - Trigger: PR with >10 file changes
   - Reason: Higher chance of unexpected interactions

---

### ℹ️ OPTIONAL (Low Risk)

Top-level suites can be skipped for:

1. **Documentation-only changes**
   - Files: `*.md`, `docs/` (non-CI)
   - Reason: No code execution affected

2. **Test-only changes**
   - Files: `tests/` with no implementation changes
   - Reason: Test matrix already covers this

3. **Configuration tweaks**
   - Files: `.env.example`, `pytest.ini`, minor config
   - Reason: Low impact, fast suites already validate

4. **Minor bug fixes**
   - Changes: <50 lines, isolated scope
   - Reason: Fast suites provide sufficient coverage

---

## How to Run Top-Level Suites

### Method 1: GitHub Actions (Recommended)

1. **Navigate to Actions tab**
   - Go to: https://github.com/[org]/AgencyOS/actions/workflows/merge-guardian.yml

2. **Click "Run workflow"**
   - Select branch: `feature/your-branch-name`
   - Set `run_top_level`: `true`
   - Add reason: "Pre-merge verification for [feature]"

3. **Monitor execution**
   - Suites will run in parallel
   - Expected runtime: 35-45 minutes total
   - Check for green checkmarks

4. **Verify results**
   - Both top-level suites must pass:
     - ✅ test-misc-toplevel-core (35 min)
     - ✅ test-misc-toplevel-leap (25 min)

**Cost**: ~$0.50/run (60 min * $0.008/min)

---

### Method 2: Local Verification (Alternative)

#### Prerequisites
```bash
# Ensure dependencies installed
pip install -r requirements.txt
pip install git+https://github.com/openai/openai-agents-python.git@main
pip install pytest-timeout

# Set environment
export PYTHONPATH=$PWD
export USE_ENHANCED_MEMORY=true
export AGENCY_TEST_TIMEOUT_OVERRIDE=300
export OPENAI_API_KEY=test-key-12345
```

#### Run Top-Level Core Suite

```bash
PYTHONMALLOC=malloc python -m pytest \
  tests/test_*.py \
  --ignore=tests/test_firestore_learning_persistence.py \
  --ignore=tests/test_firestore_mock_integration.py \
  --ignore=tests/test_leap3_e2e_integration.py \
  --ignore=tests/test_leap3_m5_validation.py \
  --ignore=tests/test_leap4_e2e_quality_feedback.py \
  --ignore=tests/test_leap5_phase1_integration.py \
  --ignore=tests/test_leap5_phase2_integration.py \
  --ignore=tests/test_leap5_phase3_e2e.py \
  --ignore=tests/test_leap5_phase4_e2e.py \
  --ignore=tests/e2e \
  --ignore=tests/benchmarks \
  -m "not slow" --ff --maxfail=1 \
  --timeout=30 --timeout-method=thread -vv
```

**Expected**:
- Runtime: ~15-25 minutes (faster than CI due to local resources)
- Output: Detailed test results with `-vv` verbosity

---

#### Run Top-Level Leap Suite

```bash
PYTHONMALLOC=malloc python -m pytest \
  tests/test_leap3_e2e_integration.py \
  tests/test_leap3_m5_validation.py \
  tests/test_leap4_e2e_quality_feedback.py \
  tests/test_leap5_phase1_integration.py \
  tests/test_leap5_phase2_integration.py \
  tests/test_leap5_phase3_e2e.py \
  tests/test_leap5_phase4_e2e.py \
  -m "not slow" --ff --maxfail=1 \
  --timeout=30 --timeout-method=thread -vv
```

**Expected**:
- Runtime: ~10-15 minutes
- Tests: 65 selected (as of 2025-11-06)
- Output: Leap validation results

---

### Method 3: Quick Smoke Test (Fast)

For rapid validation without full suite:

```bash
# Run a representative sample of top-level tests
pytest tests/test_agency_orchestrator.py tests/test_leap3_e2e_integration.py::test_leap3_basic_workflow -vv --maxfail=1
```

**Expected**:
- Runtime: ~2-5 minutes
- Coverage: Basic orchestration + one leap test
- Use case: Quick sanity check before full run

---

## Updating Manual Verification Documentation

### When to Update TOP_LEVEL_MANUAL_VERIFICATION.md

Update `docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md` after:

1. **Every manual run** (if new issues found)
2. **After leap suite changes** (test count changes)
3. **After fixing top-level test failures**
4. **Before major releases** (capture latest validation)

---

### How to Update

1. **Run the suites locally** (see commands above)

2. **Capture key metrics**:
   ```bash
   # Count tests
   pytest tests/test_leap*.py --collect-only -q | grep "test session starts"

   # Measure runtime
   time pytest tests/test_leap*.py -m "not slow" ...
   ```

3. **Update the document**:
   ```markdown
   ## Top-Level Suite Manual Verification

   - **Date**: [YYYY-MM-DD]
   - **Command**: [exact pytest command used]
   - **Result**: [N selected tests passed, M deselected, 0 failures]
   - **Runtime**: [actual time in minutes]
   - **Notes**: [any issues, warnings, or observations]
   ```

4. **Commit the update**:
   ```bash
   git add docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md
   git commit -m "docs(ci): update manual verification results [YYYY-MM-DD]"
   ```

---

## Interpreting Results

### ✅ All Green (Pass)

**Criteria**:
- All tests passed
- No warnings about skipped mandatory tests
- No timeout failures

**Action**: Proceed with merge

---

### ⚠️ Partial Pass (Investigate)

**Scenarios**:
- Some tests skipped due to missing dependencies
- Warnings about flaky tests
- Timeouts on non-critical tests

**Action**:
1. Review warnings/skips
2. Determine if issues are environmental or code-related
3. Re-run if environmental
4. Fix if code-related

---

### ❌ Failures (Block)

**Criteria**:
- Any test failure
- Assertion errors
- Uncaught exceptions

**Action**:
1. **DO NOT MERGE**
2. Investigate failure root cause
3. Fix the code or test
4. Re-run verification
5. Only merge after ✅ All Green

---

## Troubleshooting Guide

### Issue: "ModuleNotFoundError: dotenv"

**Cause**: Missing dependencies

**Fix**:
```bash
pip install python-dotenv
# OR
pip install -r requirements.txt
```

---

### Issue: "Timeout after 30 seconds"

**Cause**: Test taking too long (network, API, complexity)

**Fix**:
1. Check if marked `@pytest.mark.slow` (should be skipped with `-m "not slow"`)
2. Increase timeout: `--timeout=60`
3. Investigate why test is slow (use profiler)

---

### Issue: "ImportError: cannot import PrimeAResult"

**Cause**: Circular imports or missing implementation

**Fix**:
1. Check `PYTHONPATH` is set to repo root
2. Verify imports in test file
3. Check if implementation exists

---

### Issue: Tests pass locally but fail in CI

**Common causes**:
1. **Environment differences**:
   - Local: macOS, CI: Ubuntu
   - Local: Python 3.13, CI: Mismatch
   - Local: Different package versions

2. **Timing issues**:
   - CI runners are slower
   - Race conditions in async tests
   - Timeout values too tight

3. **Resource constraints**:
   - CI: Limited memory (7GB vs. local 128GB)
   - CI: Limited CPU cores
   - CI: Slower I/O

**Fix**:
- Add debugging output (`-vv`)
- Check GitHub Actions logs
- Increase timeouts if needed
- Use `PYTHONMALLOC=malloc` (same as CI)

---

## Cost Management

### Current Costs

**Normal CI run** (16 active suites):
- Timeout-based: 158 min = $1.26
- Actual: ~60-90 min = $0.48-$0.72

**With top-level suites** (run_top_level=true):
- Additional: 60 min = $0.48
- Total: ~$1.00-$1.20/run

**Monthly estimate** (40 runs):
- Normal: $20-30/month
- With 10% top-level runs: $25-35/month

---

### Free Tier Limits

**GitHub Free Tier**: 2,000 minutes/month
**GitHub Pro**: 3,000 minutes/month

**Current usage** (40 runs/month):
- Normal runs: 2,400-3,600 minutes
- Result: **May exceed free tier**

**Recommendation**: Monitor usage, consider GitHub Pro if consistently over 2,000 min/month

---

## Best Practices

### 1. Run Top-Level Locally First

Before triggering expensive CI runs:
```bash
# Quick check
pytest tests/test_agency_orchestrator.py -vv

# If passes, run full suites locally
# (saves CI minutes)
```

---

### 2. Use --maxfail=1 for Fast Feedback

Stop on first failure to save time:
```bash
pytest ... --maxfail=1
```

---

### 3. Use --ff (Failed-First) for Debugging

Re-run failed tests first:
```bash
pytest ... --ff
```

---

### 4. Profile Slow Tests

Identify bottlenecks:
```bash
pytest --durations=10 ...
```

---

### 5. Check for Flaky Tests

If tests fail intermittently:
```bash
# Run 10 times
for i in {1..10}; do pytest tests/test_flaky.py || break; done
```

---

## Decision Tree

```
┌─────────────────────────────────────────┐
│ PR ready for merge?                     │
└───────────┬─────────────────────────────┘
            │
            ├─ All fast suites ✅?
            │  │
            │  ├─ No → Fix failures first
            │  │
            │  └─ Yes → Continue
            │            │
            │            ├─ Changes affect core/orchestration/leaps?
            │            │  │
            │            │  ├─ No → Merge without top-level
            │            │  │
            │            │  └─ Yes → Run top-level suites
            │            │           │
            │            │           ├─ All pass ✅?
            │            │           │  │
            │            │           │  ├─ No → Fix and re-run
            │            │           │  │
            │            │           │  └─ Yes → ✅ MERGE
```

---

## Appendix: Suite Contents

### test-misc-toplevel-core
**Files**: All `tests/test_*.py` in root
**Excludes**: Leap suites, firestore, e2e, benchmarks
**Examples**:
- test_agency_orchestrator.py
- test_agent_context.py
- test_memory_api.py
- test_tool_integration.py
- (300+ tests total)

---

### test-misc-toplevel-leap
**Files**:
- tests/test_leap3_e2e_integration.py
- tests/test_leap3_m5_validation.py
- tests/test_leap4_e2e_quality_feedback.py
- tests/test_leap5_phase1_integration.py
- tests/test_leap5_phase2_integration.py
- tests/test_leap5_phase3_e2e.py
- tests/test_leap5_phase4_e2e.py

**Tests**: 65 (as of 2025-11-06)

---

## Quick Reference

**Run top-level in CI**:
```
Actions → Merge Guardian → Run workflow → run_top_level=true
```

**Run top-level locally** (core):
```bash
PYTHONMALLOC=malloc python -m pytest tests/test_*.py \
  --ignore=tests/test_leap*.py --ignore=tests/test_firestore*.py \
  -m "not slow" --maxfail=1 --timeout=30 -vv
```

**Run top-level locally** (leap):
```bash
PYTHONMALLOC=malloc python -m pytest tests/test_leap*.py \
  -m "not slow" --maxfail=1 --timeout=30 -vv
```

**Update verification doc**:
```bash
# Run suite, capture output
pytest ... | tee verification_output.txt

# Update TOP_LEVEL_MANUAL_VERIFICATION.md with:
# - Date
# - Command used
# - Results (passed/failed/skipped)
# - Runtime

git add docs/ci/TOP_LEVEL_MANUAL_VERIFICATION.md
git commit -m "docs(ci): update manual verification YYYY-MM-DD"
```

---

**SOP Version**: 1.0
**Effective Date**: 2025-11-06
**Review Schedule**: Quarterly or after major CI changes
**Owner**: CI/CD Team
