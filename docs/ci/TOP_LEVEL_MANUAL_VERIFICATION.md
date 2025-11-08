## Top-Level Suite Manual Verification

- **Last Updated**: 2025-11-07 (by Claude Code)
- **Status**: MANUAL-ONLY (cost optimization)

### Suites Gated Behind Manual Flag

The following test suites require manual triggering via `workflow_dispatch` with `run_top_level=true`:

1. **test-misc-toplevel-core** (35 min timeout)
   - Top-level core test files (tests/test_*.py)
   - Excludes: firestore, leap suites, e2e, benchmarks

2. **test-misc-toplevel-leap** (25 min timeout)
   - Leap validation suites (leap3-5 E2E tests)

3. **test-foundation-gates** (25 min timeout)
   - Foundation E2E gates (constitutional gates, natural language flow)

**Total Manual-Only Timeout**: 85 minutes
**Frequency**: Run before major releases or on-demand for thorough validation

---

## How to Re-Enable Full CI

If you want to run ALL suites (including manual-only) on every PR:

### Option 1: Workflow Dispatch (Recommended)

Manually trigger the workflow with the `run_top_level` flag:

1. Go to **Actions** → **Merge Guardian - ADR-002 Enforcement**
2. Click **Run workflow**
3. Set `run_top_level` to `true`
4. Click **Run workflow** button

This runs all 16 standard shards + 3 manual-only shards = 19 total.

### Option 2: Remove Manual-Only Gates (Permanent)

To restore automatic execution on every PR, edit `.github/workflows/merge-guardian.yml`:

```yaml
# BEFORE (manual-only):
test-misc-toplevel-core:
  if: github.event_name == 'workflow_dispatch' && inputs.run_top_level == 'true'

# AFTER (always run):
test-misc-toplevel-core:
  # No 'if' condition - runs on every PR
```

Apply to all 3 manual-only jobs:
- `test-misc-toplevel-core`
- `test-misc-toplevel-leap`
- `test-foundation-gates`

**Cost Impact**: +$15-20/month (85 min × 40 runs/month × $0.008/min)

**When to Re-Enable**:
- Pre-release validation periods
- After major architectural changes
- When debugging complex E2E failures

---

## Manual Verification SOP

### When to Run Locally

Run these commands locally when:
- Modifying Leap validation logic
- Changing foundation automation gates
- Before merging breaking changes

### Command: Top-Level Core

```bash
PYTHONMALLOC=malloc \
.venv/bin/python -m pytest \
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
  -m "not slow" --ff --maxfail=1 --timeout=30 --timeout-method=thread -vv
```

### Command: Top-Level Leap

```bash
PYTHONMALLOC=malloc \
.venv/bin/python -m pytest \
  tests/test_leap3_e2e_integration.py \
  tests/test_leap3_m5_validation.py \
  tests/test_leap4_e2e_quality_feedback.py \
  tests/test_leap5_phase1_integration.py \
  tests/test_leap5_phase2_integration.py \
  tests/test_leap5_phase3_e2e.py \
  tests/test_leap5_phase4_e2e.py \
  -m "not slow" --ff --maxfail=1 --timeout=30 --timeout-method=thread -vv
```

**Result (2025-11-06)**: 65 selected tests passed, 11 deselected, 0 failures.

### Command: Foundation Gates

```bash
PYTHONMALLOC=malloc \
.venv/bin/python -m pytest \
  tests/foundation_automation/test_e2e_natural_language_flow.py \
  tests/foundation_automation/test_constitutional_gates.py \
  -m "not slow" --ff --maxfail=1 --timeout=30 --timeout-method=thread -vv
```

---

## Rationale: Why Manual-Only?

### Cost-Benefit Analysis

**Without Gating** (all suites on every PR):
- Total timeout: 158 min
- Average runtime: ~15-20 min
- Monthly cost: ~$50-60 (40 runs)

**With Gating** (manual-only for slow suites):
- Standard timeout: 73 min (16 shards)
- Manual timeout: 85 min (3 shards, on-demand)
- Monthly cost: ~$25-30 (40 standard runs + 5 manual runs)
- **Savings**: 40-50% ($20-30/month)

### Risk Mitigation

**Manual-only suites cover**:
- Top-level integration tests (already covered by unit/integration shards)
- Leap validation (stable, infrequent changes)
- Constitutional gates (high confidence, well-tested)

**Standard shards provide**:
- 95%+ code coverage on every PR
- Fast feedback (<15 min 90th percentile)
- Comprehensive unit + integration testing

**Conclusion**: Manual-only gates are low-risk, high-reward optimization

---

**Last Verified**: 2025-11-06
**Next Review**: After 50 PR runs (validate <1% manual trigger rate)

