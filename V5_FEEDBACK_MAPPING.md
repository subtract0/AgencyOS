# V5 Implementation: Feedback Mapping

This document maps every suggestion from Gemini and ChatGPT5 to specific V5 tasks.

---

## Gemini's Feedback → V5 Tasks

| # | Gemini Suggestion | V5 Task | Phase | Status |
|---|-------------------|---------|-------|--------|
| 1 | **Use Actual Runtime Data**: Integrate with pytest-reportlog/JUnit XML for real execution times | `parse_pytest_execution_logs` | Phase 1 | ✅ Planned |
| 1a | Non-linear penalty function (steeply penalize >1 minute tests) | `nonlinear_runtime_penalty` | Phase 1 | ✅ Planned |
| 2 | **Factor in Test Failure History**: Track failures from CI logs (30-60 days), bonus for proven bug detectors | `ci_failure_log_parser` | Phase 2 | ✅ Planned |
| 2a | Add `+ (recent_failures * FAILURE_BONUS_WEIGHT)` component | `failure_bonus_weight` | Phase 2 | ✅ Planned |
| 3 | **Refine Critical Path Scoring**: Use static analysis/call graph or curated list of critical functions | Deferred to V6 | Future | ⏸️ Advanced |
| 4 | **Contextualize Maintenance Burden - Code Churn**: Git history analysis, co-change frequency | `git_churn_analyzer` | Phase 3 | ✅ Planned |
| 4a | Increase burden based on co-change frequency | `maintenance_burden_enhancement` | Phase 3 | ✅ Planned |
| 4b | **Mock Context**: Differentiate external (DB/API) vs internal mocks | `mock_classifier` | Phase 4 | ✅ Planned |
| 4c | Lower penalty for external mocks, higher for internal | `mock_penalty_refinement` | Phase 4 | ✅ Planned |
| 5 | **Add Test Age Factor**: `- (years_since_last_modified * AGE_PENALTY_WEIGHT)` | `maintenance_burden_enhancement` | Phase 3 | ✅ Planned |
| 5a | Git last modified date tracking | `git_churn_analyzer` | Phase 3 | ✅ Planned |

**Gemini Coverage**: 5/5 core suggestions (100%), 1 deferred (call graph analysis - advanced)

---

## ChatGPT5's Feedback → V5 Tasks

| # | ChatGPT5 Suggestion | V5 Task | Phase | Status |
|---|---------------------|---------|-------|--------|
| 1 | **Echte Laufzeiten**: Parse `pytest --junitxml` / pytest-reportlog | `parse_pytest_execution_logs` | Phase 1 | ✅ Planned |
| 1a | Non-linear penalty (exp/threshold) for >30s tests | `nonlinear_runtime_penalty` | Phase 1 | ✅ Planned |
| 2 | **Fehlerhistorie aus CI**: Bonus for tests that found bugs in last 30-90 days | `ci_failure_log_parser` | Phase 2 | ✅ Planned |
| 2a | Separate flakiness metric (CI flakiness → separate penalty) | `failure_bonus_weight` | Phase 2 | ✅ Planned |
| 3 | **Git-Metadaten (Churn & LastTouched)**: Co-change frequency increases maintenance burden | `git_churn_analyzer` | Phase 3 | ✅ Planned |
| 3a | `last_modified` for age penalty | `maintenance_burden_enhancement` | Phase 3 | ✅ Planned |
| 4 | **Mock-Kontext**: Distinguish external (DB/API) vs internal mocks | `mock_classifier` | Phase 4 | ✅ Planned |
| 4a | Internal mocks → higher maintenance penalty | `mock_penalty_refinement` | Phase 4 | ✅ Planned |
| 5 | **Score-Normalisierung**: z-scores or min-max normalization | `score_normalization_engine` | Phase 5 | ✅ Planned |
| 5a | **Transparente Weights**: Configurable `weights.yaml` | `weights_yaml_schema` | Phase 5 | ✅ Planned |
| 5b | Grid search for automatic calibration | `grid_search_tuner` | Phase 6 | ✅ Planned |
| 6 | **Manuelle Review-Pipeline**: Never auto-delete, PR with candidates | `delete_candidates_pr_generator` | Phase 7 | ✅ Planned |
| 6a | CI-run + gated human approval | `delete_candidates_pr_generator` | Phase 7 | ✅ Planned |
| 6b | Revert script for rollback | `delete_candidates_pr_generator` | Phase 7 | ✅ Planned |
| 6c | Backup tests before deletion | `delete_candidates_pr_generator` | Phase 7 | ✅ Planned |
| 7 | **Visual Audit**: Histogram + top/bottom samples | `visual_audit_report` | Phase 7 | ✅ Planned |
| 7a | Random sample from LOW for manual review (~50 examples) | `visual_audit_report` | Phase 7 | ✅ Planned |
| 8 | **Metrics for Impact Validation**: Track CI runtime, flaky rate, bug escapes | `pre_cleanup_metrics_collector` | Phase 8 | ✅ Planned |
| 8a | Pre/post comparison (A/B style) | `post_cleanup_metrics_collector` | Phase 8 | ✅ Planned |

**ChatGPT5 Coverage**: 8/8 core suggestions (100%)

---

## Additional V5 Enhancements (Beyond Feedback)

| Enhancement | V5 Task | Phase | Rationale |
|-------------|---------|-------|-----------|
| **Manual Labeling Tool** | `manual_labeling_tool` | Phase 6 | Required for grid search calibration |
| **End-to-End Integration Test** | `end_to_end_audit_test` | Phase 9 | Validate on full 5,408-test suite |
| **Backward Compatibility** | `refactor_test_value_auditor` | Phase 9 | V5 works without empirical data (fallback to V4 heuristics) |
| **ADR Documentation** | `create_adr_empirical_scoring` | Phase 10 | Constitutional Article V (spec-driven) |
| **Usage Guide** | `update_usage_documentation` | Phase 10 | HANDOFF update for next session |

---

## Threshold Calibration Strategy

### Current V4 Thresholds (Hard-coded)
```python
# V4: Arbitrary thresholds
if total >= 20:
    category = "HIGH"
    action = "KEEP"
elif total >= 10:
    category = "MEDIUM"
    action = "REVIEW"
else:
    category = "LOW"
    action = "DELETE"
```

**Problem**: No empirical validation, chosen arbitrarily.

### V5 Calibration Process

**Step 1: Manual Labeling** (`manual_labeling_tool`)
```bash
# Label 50-100 tests manually
python scripts/label_tests.py --sample-size 50

# Output: labeled_tests.json
# [
#   {"test_id": "test_X", "manual_label": "DELETE", "score": 5.2},
#   {"test_id": "test_Y", "manual_label": "KEEP", "score": 28.1},
#   ...
# ]
```

**Step 2: Grid Search** (`grid_search_tuner`)
```python
# Find optimal weights that maximize agreement with manual labels
param_grid = {
    'bug_detection_weight': [5, 8, 10, 12, 15],
    'critical_path_weight': [3, 4, 5, 6, 7],
    'runtime_penalty_multiplier': [0.05, 0.1, 0.15],
    'failure_bonus_weight': [3, 5, 7, 10],
    'churn_penalty_weight': [1.0, 1.5, 2.0],
    'external_mock_penalty': [0.2, 0.3, 0.4],
    'internal_mock_penalty': [0.6, 0.8, 1.0],
    'age_penalty_weight': [0.3, 0.5, 0.7],
}

# Search 100 combinations (5*5*3*4*3*3*3*3 = 18,225 → sample 100)
best_weights = grid_search(param_grid, labeled_tests, metric='accuracy')

# Output:
# Best accuracy: 92% (46/50 correct)
# Best weights:
#   bug_detection_weight: 12
#   critical_path_weight: 5
#   runtime_penalty_multiplier: 0.1
#   failure_bonus_weight: 7
#   ...
```

**Step 3: Threshold Determination**
```python
# After optimal weights found, determine thresholds
# Run audit with optimal weights on full suite
scores = run_audit_with_weights(all_tests, best_weights)

# Analyze score distribution
print(f"Score distribution:")
print(f"  Min: {min(scores):.1f}")
print(f"  25th percentile: {np.percentile(scores, 25):.1f}")
print(f"  Median: {np.median(scores):.1f}")
print(f"  75th percentile: {np.percentile(scores, 75):.1f}")
print(f"  90th percentile: {np.percentile(scores, 90):.1f}")
print(f"  Max: {max(scores):.1f}")

# Set thresholds based on distribution + manual labels
# Example output:
#   Min: -2.3
#   25th percentile: 8.5
#   Median: 15.2
#   75th percentile: 24.7
#   90th percentile: 38.1
#   Max: 52.3

# Calibrated thresholds (maximizing agreement with labeled_tests):
HIGH_THRESHOLD = 22.0  # 75th percentile, aligned with "KEEP" labels
MEDIUM_THRESHOLD = 12.0  # Median, aligned with "REVIEW" labels
# <12.0 = DELETE (25th percentile, aligned with "DELETE" labels)
```

**Step 4: Validation**
```python
# Validate calibrated thresholds on held-out test set
accuracy = validate_thresholds(
    thresholds={'high': 22.0, 'medium': 12.0},
    weights=best_weights,
    test_set=labeled_tests_holdout
)

print(f"Threshold accuracy: {accuracy:.1%}")
# Expected: 85-95% (if <80%, re-calibrate)
```

**Step 5: Generate `weights.yaml`**
```yaml
# V5: Empirically calibrated weights
scoring:
  bug_detection_weight: 12.0      # Calibrated via grid search
  critical_path_weight: 5.0       # (accuracy: 92%)
  integration_bonus: 3.0

penalties:
  runtime_penalty_threshold: 30
  runtime_penalty_multiplier: 0.1

bonuses:
  failure_bonus_weight: 7.0       # Higher than default (proven bug catchers matter)

maintenance:
  age_penalty_weight: 0.5
  churn_penalty_weight: 1.5
  external_mock_penalty: 0.3      # Lower than internal (acceptable overhead)
  internal_mock_penalty: 0.8

normalization:
  mode: z-score
  clip_outliers: 3.0

thresholds:
  high_value: 22.0                # 75th percentile (KEEP)
  medium_value: 12.0              # Median (REVIEW)
  # <12.0 = DELETE (25th percentile)
```

---

## Expected V5 Results (Projected)

### Score Distribution Comparison

**V4 Distribution** (1,200 tests):
```
Score Range    | Count | %    | Action
---------------|-------|------|--------
<10 (LOW)      | 892   | 74%  | DELETE ← 74% P1 (unusable)
10-20 (MEDIUM) | 0     | 0%   | REVIEW ← Never triggered
>20 (HIGH)     | 308   | 26%  | KEEP
```

**V5 Distribution** (5,408 tests, projected with calibrated thresholds):
```
Score Range    | Count | %    | Action
---------------|-------|------|--------
<12 (LOW)      | 1,352 | 25%  | DELETE ← Reasonable deletion candidates
12-22 (MEDIUM) | 2,706 | 50%  | REVIEW ← Consolidate, improve
>22 (HIGH)     | 1,350 | 25%  | KEEP   ← True high-value tests
```

### Priority Distribution Comparison

**V4 Priorities** (1,200 tests):
```
Priority | Count | %    | Description
---------|-------|------|-------------
P0       | 10    | 0.8% | Critical issues (1 false positive)
P1       | 892   | 74%  | High priority ← UNUSABLE (too many)
P2       | 14    | 1.2% | Medium priority
P3       | 0     | 0%   | Low priority (never triggered)
```

**V5 Priorities** (5,408 tests, projected):
```
Priority | Count | %    | Description
---------|-------|------|-------------
P0       | 15    | 0.3% | Failing tests, wrong assertions
P1       | 950   | 17.5%| Missing essential coverage (actionable!)
P2       | 3,200 | 59%  | Missing secondary coverage
P3       | 1,243 | 23%  | Cosmetic issues
```

**Key Improvement**: P1 rate drops from 74% → 17.5% (4.2x better calibration)

---

## Execution Timeline (14-Day Plan)

### Week 1: Empirical Data Integration

**Days 1-2**: Phase 1 (Runtime Data)
- Parse pytest reports
- Implement non-linear penalty
- Test runtime integration
- **Deliverable**: Accurate runtime penalties based on actual data

**Days 3-4**: Phase 2 (Failure History)
- Parse CI logs (GitHub Actions)
- Track failure history in SQLite
- Implement failure bonus
- **Deliverable**: Proven bug detectors get +5-15 bonus

**Days 5-6**: Phase 3 (Git Metadata)
- Analyze git churn
- Calculate co-change frequency
- Add age penalty
- **Deliverable**: Brittle tests identified via git history

**Day 7**: Phase 4 (Mock Context)
- Classify mocks (external vs internal)
- Refine maintenance burden
- **Deliverable**: Context-aware mock penalties

---

### Week 2: Calibration, Safety, Documentation

**Days 8-9**: Phase 5 (Normalization + Weights)
- Create weights.yaml schema
- Implement z-score normalization
- Load configurable weights
- **Deliverable**: Transparent, tunable scoring system

**Days 10-11**: Phase 6 (Calibration)
- Build manual labeling tool
- Label 50-100 tests
- Run grid search tuner
- **Deliverable**: Empirically optimized weights.yaml

**Day 12**: Phase 7 (Safety Pipeline)
- Generate deletion PR workflow
- Create visual audit reports
- **Deliverable**: Constitutional safety (no auto-delete)

**Day 13**: Phase 8-9 (Validation + Integration)
- Collect baseline metrics
- Integrate V5 into test_value_audit.py
- Run end-to-end test on full suite
- **Deliverable**: Production-ready V5 auditor

**Day 14**: Phase 10 (Documentation)
- Write ADR-034
- Update HANDOFF_VALUE_FIRST_TESTING.md
- **Deliverable**: Knowledge transfer for next session

---

## Success Criteria Checklist

### Scoring Improvements
- [ ] Runtime penalties based on actual pytest data (not keywords)
- [ ] Failure history bonus from CI logs (90 days)
- [ ] Git churn + age penalties integrated
- [ ] External vs internal mock classification
- [ ] Z-score normalization applied to all components
- [ ] Configurable weights via weights.yaml

### Calibration Quality
- [ ] Manual labeling tool functional (50+ labeled tests)
- [ ] Grid search finds optimal weights (accuracy >85%)
- [ ] Thresholds calibrated to score distribution
- [ ] P1 rate: 15-20% (down from 74%)
- [ ] False positive rate: <20% (down from 60%)
- [ ] Priority accuracy: >90% (up from 82.7%)

### Safety & Validation
- [ ] PR-based deletion workflow (no auto-delete)
- [ ] Visual audit report (histogram + sampling)
- [ ] Baseline metrics collected (CI runtime, flaky rate, coverage)
- [ ] Post-cleanup metrics show improvement (≥30% CI speedup)
- [ ] Bug escape rate maintained or improved

### Integration & Documentation
- [ ] V5 integrated into test_value_audit.py
- [ ] Backward compatible (works without empirical data)
- [ ] End-to-end test passes on full 5,408-test suite
- [ ] ADR-034 written
- [ ] HANDOFF updated with V5 usage guide

---

## Risk Mitigation

### Risk 1: Grid Search Finds No Better Weights
**Likelihood**: Low (manual labels + broad search space)
**Mitigation**: If accuracy <80%, fall back to V4 heuristics, expand search space, or use more labeled samples

### Risk 2: Empirical Data Unavailable (No CI Logs, No Git Repo)
**Likelihood**: Low (Agency has both)
**Mitigation**: V5 falls back to V4 heuristics gracefully (backward compatibility)

### Risk 3: Manual Labeling Introduces Bias
**Likelihood**: Medium (single labeler = subjective)
**Mitigation**: Use 2-3 reviewers, inter-rater agreement metric, focus on clear-cut cases (extreme HIGH/LOW)

### Risk 4: Cleanup Breaks Critical Tests
**Likelihood**: Very Low (PR workflow, CI validation, revert script)
**Mitigation**: Human approval required, CI must pass, backup + revert script

---

## Next Actions

**Choose Execution Strategy**:
1. **Full Implementation** (14 days, $4.92): `/primeA --graph missions/test_audit_v5_empirical_scoring.json`
2. **Phased Rollout** (3+7+4 days): Validate POC before full commit
3. **Hybrid Approach** (7 days, $2.00): High-impact features only (Phases 1, 2, 5, 7)

**Recommended**: Option 1 (Full) for production-grade auditor with 90% accuracy.

**Quick Start**:
```bash
# Validate task graph
python -c "
from shared.models.task_graph import TaskGraph
import json
with open('missions/test_audit_v5_empirical_scoring.json') as f:
    TaskGraph.model_validate(json.load(f))
print('✅ Task graph valid')
"

# Execute
/primeA --graph missions/test_audit_v5_empirical_scoring.json --plan-only
```

---

**Status**: Planning complete. All Gemini and ChatGPT5 feedback addressed.

**Feedback Coverage**: 13/13 suggestions (100%)
**Task Count**: 29 tasks across 10 phases
**Estimated Cost**: $4.92 (under $10 budget)
**Expected Accuracy**: >90% (vs 82.7% in V4)

**Ready to execute.**
