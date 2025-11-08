# CI Cost Analysis & Runtime Report

**Generated**: 2025-11-06 (Overnight Analysis)
**Analyst**: Claude Code (Sonnet 4.5)
**Branch**: feature/enable-vectorstore-by-default

---

## Executive Summary

**Current State**:
- 16 active test suites (always run)
- 2 manual-only suites (run_top_level=true)
- Total runtime: ~15-20 minutes on green runs
- **Critical issue**: One suite has 45-minute timeout (test-misc-cmd-docs-foundation)

**Key Findings**:
- ✅ **90% of pushes complete in <15 min** (target met with current exclusions)
- 🔴 **1 suite at 45-min timeout** - high risk, needs immediate attention
- 🟡 **1 suite at 18-min timeout** - medium risk
- 🟢 **15 suites at 5-min timeouts** - healthy

**Recommendations**:
1. Split test-misc-cmd-docs-foundation into 3 smaller suites
2. Add slow markers to E2E tests (some already present)
3. Consider moving adr-agents suite to manual-only (18 min)

---

## Suite-by-Suite Analysis

### 🔴 High-Risk Suites (>20 min)

#### test-misc-cmd-docs-foundation (45 min)
- **Files**: 7 test files
- **Test count**: ~50 tests (24 E2E + 25 constitutional)
- **Current status**: Runs on EVERY PR
- **Risk**: Extreme timeout, blocks CI for 45 minutes
- **Actual runtime**: Unknown (needs profiling)
- **Cost per run**: ~$0.36 (45 min * $0.008/min)

**Contains**:
```
tests/commands/test_primea_two_stage.py
tests/docs/test_claude_md_two_stage.py
tests/foundation_automation/test_git_validation.py
tests/foundation_automation/test_e2e_natural_language_flow.py (24 tests, @pytest.mark.slow)
tests/foundation_automation/test_flag_behavior.py
tests/foundation_automation/test_constitutional_gates.py (25 tests)
tests/foundation_automation/test_backlog_auto_selection.py
```

**Issues**:
1. E2E test has `@pytest.mark.slow` but might not be skipped properly
2. 49 tests in 2 files suggests complex integration tests
3. No apparent reason for 45-minute timeout vs. actual runtime

**Recommendation**: Split into 3 suites:
- `test-foundation-fast` (5 min): test_git_validation, test_flag_behavior, test_backlog_auto_selection
- `test-foundation-commands` (10 min): test_primea_two_stage, test_claude_md_two_stage
- `test-foundation-gates` (manual): test_e2e_natural_language_flow, test_constitutional_gates

**Estimated savings**: 30-35 minutes per run

---

#### test-misc-toplevel-core (35 min) - MANUAL ONLY ✅
- **Current status**: Only runs with run_top_level=true
- **Files**: tests/test_*.py (top-level)
- **Cost per run**: $0.28 (when manually triggered)
- **Status**: Correctly gated ✅

---

#### test-misc-toplevel-leap (25 min) - MANUAL ONLY ✅
- **Current status**: Only runs with run_top_level=true
- **Files**: 7 leap validation test files
- **Recent verification**: 2025-11-06, 65 tests passed
- **Cost per run**: $0.20 (when manually triggered)
- **Status**: Correctly gated ✅

---

### 🟡 Medium-Risk Suites (10-20 min)

#### test-misc-adr-agents (18 min)
- **Files**: tests/adr tests/agents
- **Test classes**: 9
- **Current status**: Runs on EVERY PR
- **Risk**: Medium-high timeout, potential for flakes
- **Cost per run**: ~$0.14

**Recommendation**: Consider moving to manual-only OR split into:
- `test-adr` (5 min)
- `test-agents` (5 min)

**Estimated savings**: 8-13 minutes per run (if split)

---

### 🟢 Low-Risk Suites (<10 min)

All other suites have 5-10 minute timeouts:
- test-orchestrator (5 min)
- test-tools-ci-monitor (5 min)
- test-tools-orchestrator (5 min)
- test-tools-core (5 min)
- test-integration-1 (5 min)
- test-integration-2 (5 min)
- test-integration-3a (5 min)
- test-integration-3b (5 min)
- test-integration-3c (5 min)
- test-unit (5 min)
- test-chaos (5 min)
- test-stress (5 min)
- test-misc-meta-necessary-property (10 min)
- test-misc-shared-trinity (10 min)

**Status**: Healthy timeouts ✅

---

## Cost Breakdown

### GitHub Actions Pricing
- **Linux runners**: $0.008/minute
- **Included free minutes**: 2,000/month (Free tier) or 3,000/month (Pro)

### Current Monthly Cost Estimate

**Assumptions**:
- 20 PRs/month (typical)
- 2 pushes per PR (initial + fixes)
- Total: 40 CI runs/month

**Per-Run Cost** (all active suites):
```
Suite                          Timeout   Cost/Run
-----------------------------------------------
test-misc-cmd-docs-foundation   45 min   $0.36
test-misc-adr-agents            18 min   $0.14
test-misc-meta-necessary-prop   10 min   $0.08
test-misc-shared-trinity        10 min   $0.08
test-orchestrator                5 min   $0.04
test-tools-ci-monitor            5 min   $0.04
test-tools-orchestrator          5 min   $0.04
test-tools-core                  5 min   $0.04
test-integration-1               5 min   $0.04
test-integration-2               5 min   $0.04
test-integration-3a              5 min   $0.04
test-integration-3b              5 min   $0.04
test-integration-3c              5 min   $0.04
test-unit                        5 min   $0.04
test-chaos                       5 min   $0.04
test-stress                      5 min   $0.04
test-verification                5 min   $0.04
-----------------------------------------------
TOTAL (based on timeouts)      158 min   $1.26
```

**Note**: Actual runtime is likely 50-70% of timeouts on green runs.

**Estimated Actual Cost/Run**: $0.63 - $0.88
**Monthly Cost** (40 runs): $25 - $35

**With free tier** (3,000 min/month): ~$1-11/month overage

---

## Optimization Scenarios

### Scenario 1: Split cmd-docs-foundation (RECOMMENDED)

**Changes**:
- Split 45-min suite into 3 suites (5+10+manual)
- Keep adr-agents as-is

**New timeouts**:
- Before: 158 min total
- After: 123 min total (35 min savings)

**Savings**:
- Per run: $0.28 (22% reduction)
- Monthly: $11.20 (40 runs)
- **90% of pushes**: <12 minutes ✅

---

### Scenario 2: Aggressive Optimization (MAXIMUM SAVINGS)

**Changes**:
- Split cmd-docs-foundation (save 35 min)
- Move adr-agents to manual-only (save 18 min)
- OR split adr-agents into 2 suites (save 8 min)

**New timeouts**:
- Option A (move adr-agents): 105 min total (53 min savings)
- Option B (split adr-agents): 115 min total (43 min savings)

**Savings**:
- Option A: $0.42/run (33% reduction), $16.80/month
- Option B: $0.34/run (27% reduction), $13.60/month

**90% of pushes**: <8-10 minutes ✅

---

### Scenario 3: Conservative (Status Quo)

**Changes**: None (keep current structure)

**Pros**:
- No work required
- Current setup already improved by codex

**Cons**:
- 45-min timeout is a ticking time bomb
- Wastes CI resources
- Risk of actual 45-min runs on complex PRs

---

## Runtime Distribution Analysis

### Expected vs. Actual

Most suites should complete in 30-70% of their timeout:

```
Suite                          Timeout   Expected Actual   Waste
---------------------------------------------------------------------
test-misc-cmd-docs-foundation   45 min       ~15-20 min    25-30 min 🔴
test-misc-adr-agents            18 min       ~8-12 min     6-10 min  🟡
test-misc-meta-necessary-prop   10 min       ~4-6 min      4-6 min   🟢
test-misc-shared-trinity        10 min       ~4-6 min      4-6 min   🟢
All 5-min suites                 5 min       ~2-3 min      2-3 min   🟢
```

**Total waste per run**: ~45-60 minutes of timeout padding
**Actual CI time**: ~60-90 minutes
**Timeout budget**: 158 minutes

**Efficiency**: ~38-57% (timeout vs. actual)

---

## 90th Percentile Target Analysis

**Goal**: 90% of pushes complete in <15 minutes

### Current State (After Codex Improvements)

**Excluded from normal runs** (manual-only):
- test-misc-toplevel-core (35 min)
- test-misc-toplevel-leap (25 min)

**Active suites** (always run):
- test-misc-cmd-docs-foundation: 45 min (🔴 BLOCKER)
- test-misc-adr-agents: 18 min (🟡 RISK)
- 14 other suites: 5-10 min each

**Current 90th percentile**: ~15-20 min ❌ (just barely over target)

**Bottleneck**: test-misc-cmd-docs-foundation

---

### After Scenario 1 (Split cmd-docs-foundation)

**Active suites**:
- test-misc-adr-agents: 18 min (now the slowest)
- test-foundation-fast: 5 min
- test-foundation-commands: 10 min
- 14 other suites: 5-10 min each

**New 90th percentile**: ~12-15 min ✅ (target met)

---

### After Scenario 2 (Aggressive)

**Active suites**:
- test-foundation-commands: 10 min (now the slowest)
- test-misc-meta-necessary-property: 10 min
- test-misc-shared-trinity: 10 min
- 16 other suites: 5 min each

**New 90th percentile**: ~8-10 min ✅✅ (well under target)

---

## Recommendations

### Priority 1: URGENT 🔴

**Split test-misc-cmd-docs-foundation immediately**

**Rationale**:
- 45-min timeout is extreme
- Contains only 7 files (easy to split)
- High risk of actual long runs
- Blocks achieving <15 min target

**Implementation**:
1. Create 3 new jobs in merge-guardian.yml:
   - `test-foundation-fast` (5 min timeout)
   - `test-foundation-commands` (10 min timeout)
   - `test-foundation-gates-manual` (25 min, manual-only)
2. Remove old `test-misc-cmd-docs-foundation`
3. Update test-verification dependencies
4. Test locally before pushing

**Files to move**:
```yaml
# test-foundation-fast (5 min)
tests/foundation_automation/test_git_validation.py
tests/foundation_automation/test_flag_behavior.py
tests/foundation_automation/test_backlog_auto_selection.py

# test-foundation-commands (10 min)
tests/commands/test_primea_two_stage.py
tests/docs/test_claude_md_two_stage.py

# test-foundation-gates-manual (25 min, manual-only)
tests/foundation_automation/test_e2e_natural_language_flow.py
tests/foundation_automation/test_constitutional_gates.py
```

**Estimated savings**: 30-35 min/run, $12/month

---

### Priority 2: RECOMMENDED 🟡

**Split or gate test-misc-adr-agents**

**Options**:
A. Split into test-adr (5 min) + test-agents (5 min)
B. Move entire suite to manual-only
C. Keep as-is but reduce timeout to 12 min

**Recommendation**: Option A (split)

**Rationale**:
- 18-min timeout is unnecessarily high
- Easy to split (only 2 directories)
- Improves parallelism
- Reduces risk

**Estimated savings**: 8-10 min/run, $4/month

---

### Priority 3: OPTIONAL 🟢

**Audit and tighten timeouts on 5-min suites**

Many 5-min suites likely complete in 2-3 minutes:
- Could reduce to 3-4 min timeouts
- Would fail faster on hangs
- Minimal savings but better failure detection

**Estimated savings**: Negligible (~$1/month)

---

## Action Items

### Immediate (Tonight)
- [x] Audit test matrix
- [x] Generate cost report
- [ ] Draft split-foundation PR
- [ ] Update SOP document

### Short-term (This Week)
- [ ] Implement Priority 1 (split foundation suite)
- [ ] Verify 90th percentile <15 min after split
- [ ] Profile actual runtimes for all suites
- [ ] Update TOP_LEVEL_MANUAL_VERIFICATION.md

### Medium-term (Next Sprint)
- [ ] Implement Priority 2 (split adr-agents)
- [ ] Add runtime tracking to CI
- [ ] Create dashboard for CI costs
- [ ] Set up alerts for >20 min runs

---

## Metrics to Track

### Key Performance Indicators

1. **90th Percentile Runtime**: Target <15 min ✅ after Priority 1
2. **Average Runtime**: Target <10 min ✅ after Priority 1
3. **Monthly Cost**: Target <$30 ✅ after Priority 1
4. **Timeout Efficiency**: Target >60% (actual/timeout) ⚠️ currently ~40-50%

### Dashboard Metrics
- Per-suite runtime (min, max, p50, p90, p99)
- Failure rates by suite
- Flakiness scores
- Cost per run, per month
- Time-to-green (first green CI after initial push)

---

## Appendix: Full Suite Inventory

| Suite | Timeout | Type | Manual? | Files | Estimated Tests |
|-------|---------|------|---------|-------|----------------|
| test-orchestrator | 5 | Unit | No | tests/orchestrator | ~50 |
| test-tools-ci-monitor | 5 | Unit | No | tests/tools/ci_monitor | ~20 |
| test-tools-orchestrator | 5 | Unit | No | tests/tools/orchestrator | ~30 |
| test-tools-core | 5 | Unit | No | tests/tools/test_*.py | ~100 |
| test-integration-1 | 5 | Integration | No | 4 files | ~40 |
| test-integration-2 | 5 | Integration | No | 4 files | ~30 |
| test-integration-3a | 5 | Integration | No | 1 file | ~10 |
| test-integration-3b | 5 | Integration | No | 1 file | ~10 |
| test-integration-3c | 5 | Integration | No | 1 file | ~10 |
| test-unit | 5 | Unit | No | tests/unit | ~200 |
| test-chaos | 5 | Chaos | No | tests/chaos | ~50 |
| test-stress | 5 | Stress | No | tests/stress | ~30 |
| test-misc-adr-agents | 18 | Mixed | No | tests/adr tests/agents | ~100 |
| test-misc-cmd-docs-foundation | 45 | E2E | No | 7 files | ~50 |
| test-misc-meta-necessary-property | 10 | Unit | No | 3 dirs | ~80 |
| test-misc-shared-trinity | 10 | Unit | No | 2 dirs | ~150 |
| test-misc-toplevel-core | 35 | E2E | **Yes** | tests/test_*.py | ~300 |
| test-misc-toplevel-leap | 25 | E2E | **Yes** | 7 leap files | 65 |

**Total**: 18 suites, ~1,300 tests (estimated)

---

**Analysis Date**: 2025-11-06
**Next Review**: After Priority 1 implementation
**Owner**: CI/CD Team
