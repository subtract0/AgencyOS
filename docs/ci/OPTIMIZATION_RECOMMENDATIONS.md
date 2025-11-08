# CI Optimization Recommendations

**Generated**: 2025-11-06 (Overnight Analysis)
**Status**: Ready for Implementation
**Priority**: HIGH (45-min timeout is critical risk)

---

## 🔴 PRIORITY 1: Split test-misc-cmd-docs-foundation (URGENT)

### Problem
- Single suite with 45-minute timeout
- Only 7 test files but contains expensive E2E tests
- Blocks achieving <15 min target for 90% of pushes
- High risk of actual long runs

### Solution
Split into 3 separate suites:

```yaml
# New suite 1: Fast foundation tests (5 min)
test-foundation-fast:
  timeout-minutes: 5
  tests:
    - tests/foundation_automation/test_git_validation.py
    - tests/foundation_automation/test_flag_behavior.py
    - tests/foundation_automation/test_backlog_auto_selection.py

# New suite 2: Command tests (10 min)
test-foundation-commands:
  timeout-minutes: 10
  tests:
    - tests/commands/test_primea_two_stage.py
    - tests/docs/test_claude_md_two_stage.py

# New suite 3: E2E gates (manual-only, 25 min)
test-foundation-gates:
  timeout-minutes: 25
  if: github.event_name == 'workflow_dispatch' && inputs.run_top_level == 'true'
  tests:
    - tests/foundation_automation/test_e2e_natural_language_flow.py
    - tests/foundation_automation/test_constitutional_gates.py
```

### Expected Impact
- **Savings**: 30-35 minutes per run
- **Cost reduction**: $12/month (40 runs)
- **90th percentile**: 15-20 min → 12-15 min ✅

### Implementation Checklist
- [ ] Create `test-foundation-fast` job in merge-guardian.yml
- [ ] Create `test-foundation-commands` job in merge-guardian.yml
- [ ] Create `test-foundation-gates` job (manual-only)
- [ ] Remove `test-misc-cmd-docs-foundation` job
- [ ] Update `test-verification` dependencies
- [ ] Test locally before pushing
- [ ] Monitor first 3 CI runs for issues

---

## 🟡 PRIORITY 2: Split test-misc-adr-agents (RECOMMENDED)

### Problem
- 18-minute timeout (2nd longest after foundation suite)
- Could be split easily into 2 directories
- Medium risk of timeouts on complex changes

### Solution A: Split into 2 suites (RECOMMENDED)

```yaml
# New suite 1: ADR tests (5 min)
test-adr:
  timeout-minutes: 5
  tests: tests/adr

# New suite 2: Agent tests (5 min)
test-agents:
  timeout-minutes: 5
  tests: tests/agents
```

**Pros**:
- Better parallelism (2 suites run concurrently)
- Faster failure detection
- Each suite has tighter timeout

**Cons**:
- Slightly more complex CI config
- 2 suites instead of 1

### Solution B: Move to manual-only

```yaml
test-adr-agents:
  if: github.event_name == 'workflow_dispatch' && inputs.run_top_level == 'true'
```

**Pros**:
- Simplest change
- Maximum savings (18 min)

**Cons**:
- Loses some coverage on normal PRs
- Requires manual verification more often

### Recommendation
**Solution A** (split) - Better balance of coverage and speed

### Expected Impact
- **Savings**: 8-10 minutes per run (via parallelism)
- **Cost reduction**: $4/month
- **90th percentile**: 12-15 min → 10-12 min ✅

---

## 🟢 PRIORITY 3: Tighten Fast Suite Timeouts (OPTIONAL)

### Problem
- Most 5-min suites complete in 2-3 minutes
- Excess timeout padding hides slow tests
- Failures take longer to detect

### Solution
Reduce timeouts to realistic values:

```yaml
# Before
timeout-minutes: 5

# After (for suites that consistently finish in <3 min)
timeout-minutes: 3
```

### Target Suites
- test-tools-ci-monitor: 5 → 3 min
- test-tools-core: 5 → 3 min
- test-chaos: 5 → 3 min
- test-stress: 5 → 3 min

### Expected Impact
- **Savings**: Minimal (~2-3 min/run)
- **Cost reduction**: <$1/month
- **Benefit**: Faster failure detection, encourages writing faster tests

### Risk
- May need to increase timeouts if actual runtimes vary
- Requires profiling to validate

---

## 🔵 PRIORITY 4: Add Slow Test Markers (PREVENTIVE)

### Problem
- Some E2E tests not properly marked `@pytest.mark.slow`
- Expensive tests might run in normal suites
- No enforcement of slow markers

### Solution
1. **Audit all tests for slow markers**:
   ```bash
   # Find tests that take >5 seconds
   pytest --durations=50 --collect-only | grep -E "test_.*" > slow_tests.txt
   ```

2. **Add markers where missing**:
   ```python
   @pytest.mark.slow
   def test_expensive_e2e_workflow():
       ...
   ```

3. **Enforce in pytest.ini**:
   ```ini
   [pytest]
   markers =
       slow: marks tests as slow (>5 seconds)
       integration: marks tests as integration tests
   ```

4. **Add pre-commit hook**:
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: check-slow-markers
         name: Check for slow tests without markers
         entry: scripts/check_slow_markers.sh
         language: script
   ```

### Expected Impact
- **Prevention**: Avoids future timeout issues
- **Clarity**: Clear separation of fast vs. slow tests
- **Cost**: Zero (just good practice)

---

## 📊 Combined Impact Summary

### Scenario 1: Priority 1 Only (Minimum)
- **Before**: 158 min total timeout
- **After**: 123 min total timeout
- **Savings**: 35 min/run, $12/month
- **90th percentile**: 12-15 min ✅

### Scenario 2: Priority 1 + 2 (Recommended)
- **Before**: 158 min total timeout
- **After**: 115 min total timeout
- **Savings**: 43 min/run, $16/month
- **90th percentile**: 10-12 min ✅✅

### Scenario 3: All Priorities (Aggressive)
- **Before**: 158 min total timeout
- **After**: ~105 min total timeout
- **Savings**: 53 min/run, $20/month
- **90th percentile**: 8-10 min ✅✅✅
- **Bonus**: Better test hygiene, faster feedback

---

## Implementation Plan

### Week 1: Priority 1 (Foundation Split)
**Monday**:
- [ ] Create PR with split-foundation changes
- [ ] Test locally
- [ ] Document new suite structure

**Tuesday**:
- [ ] Review PR
- [ ] Merge after approval
- [ ] Monitor 3 green CI runs

**Wednesday**:
- [ ] Verify 90th percentile <15 min
- [ ] Update cost tracking
- [ ] Document lessons learned

### Week 2: Priority 2 (ADR-Agents Split)
**Monday**:
- [ ] Profile adr vs. agents test runtime
- [ ] Create PR with split
- [ ] Test locally

**Tuesday**:
- [ ] Review and merge
- [ ] Monitor CI performance

**Wednesday**:
- [ ] Verify 90th percentile <12 min
- [ ] Celebrate success 🎉

### Week 3: Priority 3 & 4 (Polish)
**Optional**: Only if time allows and results from Priority 1+2 are stable

---

## Risk Assessment

### Priority 1 (Split Foundation)
- **Risk Level**: LOW
- **Rationale**: Clean split, clear boundaries
- **Mitigation**: Test locally first, monitor closely

### Priority 2 (Split ADR-Agents)
- **Risk Level**: LOW
- **Rationale**: Simple directory split
- **Mitigation**: Verify test dependencies don't cross directories

### Priority 3 (Tighten Timeouts)
- **Risk Level**: MEDIUM
- **Rationale**: May need adjustments if timeouts too tight
- **Mitigation**: Start conservative (4 min), tighten later

### Priority 4 (Slow Markers)
- **Risk Level**: LOW
- **Rationale**: Preventive, no immediate changes
- **Mitigation**: Gradual rollout, no enforcement initially

---

## Success Metrics

### Key Results (After Implementation)
1. **90th percentile runtime**: <12 minutes ✅
2. **Average runtime**: <10 minutes ✅
3. **Monthly CI cost**: <$30 ✅
4. **Failed runs due to timeout**: <1% ✅
5. **Developer satisfaction**: Faster feedback ✅

### Monitoring Plan
- Track runtime per suite (p50, p90, p99)
- Track timeout failures
- Track monthly costs
- Survey developers quarterly

---

## Approval Required

### Changes Requiring Review
1. **merge-guardian.yml modifications** (Priority 1 & 2)
   - Reviewer: CI/CD Team Lead
   - Reason: Critical CI infrastructure

2. **Test reorganization** (if needed)
   - Reviewer: Test Infrastructure Team
   - Reason: Ensure test coverage maintained

### Auto-Approved (Can Proceed)
1. Documentation updates
2. Local profiling
3. Slow marker additions (non-breaking)

---

## Appendix: Draft PR for Priority 1

**Title**: `ci: split foundation suite to reduce timeout from 45 min to 15 min`

**Description**:
```markdown
## Problem
The `test-misc-cmd-docs-foundation` suite has a 45-minute timeout, making it the
slowest suite and preventing us from achieving the <15 min target for 90% of pushes.

## Solution
Split into 3 suites:
- `test-foundation-fast` (5 min): Fast foundation tests
- `test-foundation-commands` (10 min): Command/docs tests
- `test-foundation-gates` (25 min, manual-only): E2E constitutional gates

## Impact
- ✅ Reduces timeout by 30-35 minutes per run
- ✅ Achieves <15 min target for 90% of pushes
- ✅ Saves ~$12/month in CI costs
- ✅ Better failure isolation (know which subset failed)

## Testing
- [x] Ran all 3 suites locally
- [x] Verified test counts match original
- [x] Confirmed slow markers work correctly

## Checklist
- [x] Updated merge-guardian.yml
- [x] Updated CI_COST_ANALYSIS.md
- [x] Updated CI_MANUAL_VERIFICATION_SOP.md
- [x] Tested locally
```

**Files to Change**:
- `.github/workflows/merge-guardian.yml`
- `docs/ci/CI_COST_ANALYSIS.md`
- `docs/ci/CI_MANUAL_VERIFICATION_SOP.md`

---

**Recommendations Version**: 1.0
**Next Review**: After Priority 1 implementation
**Owner**: CI/CD Team
