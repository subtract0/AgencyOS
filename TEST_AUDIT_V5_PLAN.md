# Test Value Auditor V5: Empirical Data-Driven Scoring System

**Date**: 2025-10-23
**Status**: Planning Complete - Ready for Implementation
**Mission**: `/primeA --graph missions/test_audit_v5_empirical_scoring.json`

---

## Executive Summary

Based on comprehensive feedback from Gemini, ChatGPT5, and analysis of V4 audit results, this plan implements a **production-grade empirical test value scoring system** that addresses all identified limitations.

### Key Improvements

**From Gemini's Feedback**:
1. ✅ Actual runtime data (pytest reports, not keyword heuristics)
2. ✅ CI failure history tracking (proven bug detectors)
3. ✅ Git metadata integration (churn, last modified)
4. ✅ Mock context classification (external vs internal)
5. ✅ Test age factor (obsolescence detection)

**From ChatGPT5's Feedback**:
1. ✅ Real runtime parsing (`junitxml`, `pytest-reportlog`)
2. ✅ Non-linear runtime penalty (exponential for >30s tests)
3. ✅ Git churn + co-change frequency
4. ✅ Configurable `weights.yaml` with transparent defaults
5. ✅ Score normalization (z-score, min-max)
6. ✅ Grid search tuner for automatic calibration
7. ✅ Manual review pipeline (PR-based, never auto-delete)
8. ✅ Visual audit reports (histogram + sampling)
9. ✅ Impact validation metrics (pre/post cleanup A/B comparison)

### Expected Outcomes

| Metric | V4 (Heuristic) | V5 (Empirical) | Improvement |
|--------|----------------|----------------|-------------|
| **P1 Rate** | 74% (892/1,200) | **15-20%** | **4x better calibration** |
| **False Positive Rate** | 60% (Accessibility, Year-round) | **<20%** | **3x more accurate** |
| **Priority Accuracy** | 82.7% (75-test validation) | **>90%** | +8% improvement |
| **Actionability Score** | 3/10 (too many P1s) | **8/10** | Usable roadmap |
| **Calibration Method** | Manual thresholds | **Grid search on labeled data** | Automated tuning |
| **Runtime Penalty** | Keyword-based (inaccurate) | **Actual pytest duration** | Precise penalties |
| **Maintenance Burden** | Mock count only | **Churn + age + mock context** | Multi-factor accuracy |
| **Cost** | $0 (local qwen3-coder) | **$0** | Still free |

---

## The Problem: V4 Audit Limitations

### 1. Over-Classification (74% P1 Rate)

**V4 Result**: 892/1,200 tests (74%) marked P1 "High Priority"
**Issue**: Dilutes urgency, roadmap becomes unusable
**Root Cause**: Any NECESSARY gap → P1 (no calibration)

**Example**:
```python
# V4 marks this as P1 (missing 7/9 NECESSARY categories)
def test_default_ref_is_head():
    tool = Git(cmd="status")
    assert tool.ref == "HEAD"

# Reality: This is a focused unit test BY DESIGN
# Missing Accessibility, Year-round, Cascading = NOT APPLICABLE
```

### 2. False Gap Reporting (60% False Positive Rate)

| Category | Gap Count | False Positive Rate | Issue |
|----------|-----------|---------------------|-------|
| Accessibility | 460/500 (92%) | **~95%** | Not applicable to backend tests |
| Year-round | 457/500 (91%) | **~90%** | Not applicable to stateless tests |
| Cascading | 425/500 (85%) | **~70%** | Unit tests don't test error propagation |
| Security | 432/500 (86%) | **~50%** | Too broad interpretation |

**Problem**: LLM applies ALL 9 NECESSARY categories to EVERY test, regardless of test type.

### 3. Heuristic-Based Scoring (Inaccurate Penalties)

**Runtime Penalty** (Current):
```python
# V4 guesses runtime from keywords
if 'sleep' in code:
    penalty += 5.0
if 'docker' in code:
    penalty += 3.0

# Problem: Inaccurate! A test with 'sleep(0.001)' gets same penalty as 'sleep(60)'
```

**Maintenance Burden** (Current):
```python
# V4 counts all mocks equally
burden = mock_count * 0.5

# Problem: Mocking external DB (acceptable) penalized same as mocking internal classes (code smell)
```

### 4. No Threshold Calibration

**V4 Thresholds** (Hard-coded):
- P1: ≥7 NECESSARY gaps → 74% of tests
- P2: 4-6 gaps → 15%
- P3: Never triggered → 0%

**Problem**: No empirical validation. Thresholds chosen arbitrarily.

---

## The Solution: V5 Empirical Scoring System

### 10-Phase Implementation Plan

#### **Phase 1: Actual Runtime Data Integration** (3 tasks)

**Problem Solved**: Keyword-based runtime estimation is inaccurate.

**Solution**:
1. **Parse pytest execution logs** (`junitxml`, `pytest-reportlog`)
   - Extract actual `duration_seconds` per test
   - Handle missing/incomplete reports gracefully

2. **Non-linear runtime penalty function**:
   ```python
   # V5: Exponential penalty for slow tests
   def calculate_runtime_penalty(runtime_sec):
       if runtime_sec < 10:
           return runtime_sec * 0.05  # Minimal penalty
       elif runtime_sec < 30:
           return 0.5 + (runtime_sec - 10) * 0.1  # Moderate
       else:
           # Steep penalty for >30s tests
           return 2.5 + (runtime_sec - 30) * 0.5 + exp((runtime_sec - 30) / 10)

   # Examples:
   # 5s test: 0.25 penalty
   # 20s test: 1.5 penalty
   # 45s test: 12.0 penalty (steeply penalized)
   # 60s test: 25.0 penalty (extreme)
   ```

**Impact**: Accurate runtime penalties → Better cost/benefit analysis

---

#### **Phase 2: CI Failure History Tracking** (3 tasks)

**Problem Solved**: Heuristic bug detection (keywords like "regression", "bug") doesn't capture actual bug-catching ability.

**Solution**:
1. **Parse CI logs** (GitHub Actions, CircleCI, Jenkins)
   - Track test failures last 30-90 days
   - Store in SQLite: `test_id, failure_date, failure_reason, fixed_date`

2. **Failure history bonus**:
   ```python
   # V5: Proven bug detectors get bonus
   def calculate_failure_bonus(test_id, failure_db):
       recent_failures = failure_db.get_fixed_failures(test_id, days=90)
       flaky_failures = failure_db.get_unfixed_failures(test_id, days=90)

       if len(recent_failures) == 0:
           return 0  # No bonus
       elif len(recent_failures) <= 2:
           return 5 * len(recent_failures)  # +5-10 bonus (proven bug detector)
       elif len(recent_failures) <= 5:
           return 15  # +15 bonus (critical regression test)
       elif len(flaky_failures) > 10:
           return -5  # Flaky test penalty (unreliable)
       else:
           return 10  # Multiple proven bugs caught

   # Examples:
   # Test caught 2 bugs (fixed): +10 bonus
   # Test caught 5 bugs (fixed): +15 bonus
   # Test failed 12 times (never fixed): -5 penalty (flaky)
   ```

**Impact**: Prioritize tests that actually catch bugs in production/staging

---

#### **Phase 3: Git Churn and Age Analysis** (3 tasks)

**Problem Solved**: Maintenance burden doesn't account for test brittleness (frequent breakage on refactors).

**Solution**:
1. **Git churn analyzer**:
   ```bash
   # Track test file modifications
   git log --numstat --follow tests/test_example.py --since="90 days ago"

   # Calculate:
   # - commits_last_90_days (how often test changes)
   # - co_change_count (test + production file in same commit)
   # - last_modified_date (for age penalty)
   ```

2. **Enhanced maintenance burden**:
   ```python
   # V5: Churn + age factors
   def calculate_maintenance_burden(test_file, git_data):
       base_burden = len(test_code.split('\n')) / 10  # Line count

       # Churn penalty (brittle tests)
       co_change_count = git_data.get_co_changes(test_file, days=90)
       churn_penalty = co_change_count * 1.5  # High co-change = breaks on refactor

       # Age penalty (obsolete tests)
       years_since_modified = git_data.get_age_years(test_file)
       age_penalty = years_since_modified * 0.5  # Old tests may be obsolete

       return base_burden + churn_penalty + age_penalty

   # Examples:
   # Test modified 5 times with production code: +7.5 churn penalty
   # Test last modified 3 years ago: +1.5 age penalty
   # New test (0 commits): 0 churn penalty
   ```

**Impact**: Identify brittle tests that break on every refactor

---

#### **Phase 4: Mock Context Classification** (3 tasks)

**Problem Solved**: All mocks penalized equally, but external mocks (DB, API) are acceptable overhead.

**Solution**:
1. **Mock classifier** (AST-based):
   ```python
   # V5: Distinguish external vs internal mocks
   def classify_mocks(test_code):
       external_patterns = ['requests', 'psycopg2', 'Path', 'open', 'firestore']
       internal_patterns = [
           'AgentContext', 'MemoryStore', 'Planner', 'Coder',
           'from agency', 'from shared', 'from tools'
       ]

       mocks = extract_mocks_ast(test_code)  # Parse with AST

       external_mocks = [m for m in mocks if any(p in m.target for p in external_patterns)]
       internal_mocks = [m for m in mocks if any(p in m.target for p in internal_patterns)]

       return len(external_mocks), len(internal_mocks)
   ```

2. **Refined mock penalty**:
   ```python
   # V5: Context-aware penalties
   external_mocks, internal_mocks = classify_mocks(test_code)

   burden = (external_mocks * 0.3) + (internal_mocks * 0.8)

   # Examples:
   # 5 external mocks (DB): +1.5 penalty (acceptable)
   # 5 internal mocks (classes): +4.0 penalty (code smell)
   # Mixed (3 external + 2 internal): 0.9 + 1.6 = 2.5 penalty
   ```

**Impact**: Accurately penalize implementation detail testing, not infrastructure mocking

---

#### **Phase 5: Score Normalization & Configurable Weights** (4 tasks)

**Problem Solved**: Score components have different scales (runtime: 0-60s, mock count: 0-20), making weighted sum unreliable.

**Solution**:
1. **weights.yaml schema**:
   ```yaml
   # V5: Transparent, configurable weights
   scoring:
     bug_detection_weight: 10.0      # Multiply normalized bug score
     critical_path_weight: 5.0       # Multiply normalized path score
     integration_bonus: 3.0          # Integration tests get bonus

   penalties:
     runtime_penalty_threshold: 30   # Non-linear penalty above 30s
     runtime_penalty_multiplier: 0.1

   bonuses:
     failure_bonus_weight: 5.0       # Per proven bug caught

   maintenance:
     age_penalty_weight: 0.5         # Per year since last modified
     churn_penalty_weight: 1.5       # Per co-change commit
     external_mock_penalty: 0.3      # Per external mock
     internal_mock_penalty: 0.8      # Per internal mock

   normalization:
     mode: z-score                    # Options: none, z-score, min-max
     clip_outliers: 3.0              # Clip z-scores beyond ±3σ

   thresholds:
     high_value: 20                  # KEEP threshold
     medium_value: 10                # REVIEW threshold
     # <10 = DELETE
   ```

2. **Z-score normalization**:
   ```python
   # V5: Normalize components before weighted sum
   def normalize_scores(all_tests):
       bug_scores = [t.bug_detection_score for t in all_tests]
       runtime_scores = [t.runtime_penalty for t in all_tests]
       # ... other components

       bug_mean, bug_std = mean(bug_scores), std(bug_scores)
       runtime_mean, runtime_std = mean(runtime_scores), std(runtime_scores)

       for test in all_tests:
           test.bug_detection_normalized = (test.bug_detection_score - bug_mean) / bug_std
           test.runtime_normalized = (test.runtime_penalty - runtime_mean) / runtime_std
           # Clip outliers to ±3σ
           test.bug_detection_normalized = clip(test.bug_detection_normalized, -3, 3)

           # Weighted sum with normalized values
           test.total_score = (
               test.bug_detection_normalized * weights.bug_detection_weight +
               test.critical_path_normalized * weights.critical_path_weight -
               test.runtime_normalized * weights.runtime_penalty_multiplier -
               test.maintenance_normalized * weights.maintenance_weight +
               test.failure_bonus  # Already in points
           )
   ```

**Impact**: Components are comparable, weights are transparent, tuning is systematic

---

#### **Phase 6: Grid Search Tuner for Weight Calibration** (3 tasks)

**Problem Solved**: V4 thresholds (P1 > 20, P2 10-20, P3 <10) are arbitrary, not calibrated to actual test quality.

**Solution**:
1. **Manual labeling tool**:
   ```bash
   # V5: CLI tool for manual test labeling
   python scripts/label_tests.py --sample-size 50

   # Shows:
   # Test: test_agent_context_creation
   # File: tests/test_agent_context.py:42
   # Code: [syntax highlighted test code]
   # Current Score: 5.2 (LOW)
   #
   # Your label: [K]eep / [R]eview / [D]elete / [C]onsolidate? D
   # Reason (optional): Mocking hell, tests nothing

   # Saves to: labeled_tests.json
   ```

2. **Grid search optimization**:
   ```python
   # V5: Find optimal weights that maximize agreement with manual labels
   from sklearn.model_selection import GridSearchCV

   param_grid = {
       'bug_detection_weight': [5, 8, 10, 12, 15],
       'critical_path_weight': [3, 4, 5, 6, 7],
       'runtime_penalty_multiplier': [0.05, 0.1, 0.15],
       'failure_bonus_weight': [3, 5, 7, 10],
       'churn_penalty_weight': [1.0, 1.5, 2.0],
       # ... other weights
   }

   # Metric: Accuracy (predicted action matches manual label)
   def score_weights(weights_candidate, labeled_tests):
       predicted_actions = []
       for test in labeled_tests:
           score = calculate_total_score(test, weights_candidate)
           predicted_action = classify_action(score)  # KEEP/REVIEW/DELETE
           predicted_actions.append(predicted_action)

       actual_actions = [t.manual_label for t in labeled_tests]
       accuracy = sum(p == a for p, a in zip(predicted_actions, actual_actions)) / len(labeled_tests)
       return accuracy

   # Search grid (100 combinations)
   best_weights, best_accuracy = grid_search(param_grid, labeled_tests, score_fn=score_weights)

   # Output:
   # Best accuracy: 92% (46/50 correct)
   # Best weights:
   #   bug_detection_weight: 12
   #   critical_path_weight: 5
   #   runtime_penalty_multiplier: 0.1
   #   failure_bonus_weight: 7
   #   churn_penalty_weight: 1.5

   # Save to: weights_optimized.yaml
   ```

**Impact**: Automated calibration based on human judgment, not guesswork

---

#### **Phase 7: Manual Review Pipeline & Safety** (3 tasks)

**Problem Solved**: V4 roadmap suggests mass deletion, but no safety mechanisms to prevent mistakes.

**Solution**:
1. **PR-based deletion workflow**:
   ```bash
   # V5: NEVER auto-delete, always human approval
   python scripts/generate_deletion_pr.py --threshold 10

   # Creates:
   # 1. candidates_to_delete.txt (452 tests, score <10)
   # 2. backup/ directory (copies of all test files)
   # 3. revert.sh script (restore deleted tests)
   # 4. GitHub PR with detailed description

   # PR description includes:
   # - Test count: 452 candidates
   # - Score distribution histogram
   # - Top 10 examples with justification
   # - Risk assessment: LOW (no integration tests in list)
   # - Revert instructions

   # PR requires:
   # - Manual review + approval
   # - CI pass (remaining tests must pass)
   # - No auto-merge
   ```

2. **Visual audit report**:
   ```bash
   # V5: HTML report for human review
   python scripts/generate_visual_report.py

   # Generates: audit_report.html
   # - Score distribution histogram (matplotlib)
   # - Top 10 highest-value tests (integration, critical path)
   # - Bottom 10 lowest-value tests (mocking hell)
   # - Random sample of 50 LOW tests for spot-checking
   # - Summary stats: avg score, median, std dev, quartiles
   ```

**Impact**: Safe deletion workflow with human oversight, no accidental losses

---

#### **Phase 8: Impact Validation Metrics** (3 tasks)

**Problem Solved**: V4 doesn't measure impact of cleanup. Are we actually improving test suite health?

**Solution**:
1. **Pre-cleanup baseline**:
   ```bash
   # V5: Measure before cleanup
   python scripts/collect_baseline_metrics.py

   # Measures:
   # 1. CI runtime: pytest --durations=0 (avg of 10 runs)
   # 2. Flaky test rate: run 10x, count intermittent failures
   # 3. Test suite size: test count, total LOC
   # 4. Code coverage: pytest-cov percentage

   # Saves: metrics_baseline.json
   # {
   #   "ci_runtime_avg_sec": 1847,
   #   "ci_runtime_std_dev": 23,
   #   "flaky_test_count": 14,
   #   "test_count": 5408,
   #   "test_loc": 162000,
   #   "coverage_pct": 87.3
   # }
   ```

2. **Post-cleanup comparison**:
   ```bash
   # V5: Measure after cleanup, validate improvements
   python scripts/collect_post_metrics.py --baseline metrics_baseline.json

   # Generates: metrics_comparison_report.md
   #
   # ## CI Runtime
   # Before: 1847s (30.8 min)
   # After: 1123s (18.7 min)
   # Improvement: -39% ✅ (Target: ≥30%)
   #
   # ## Flaky Tests
   # Before: 14 flaky tests
   # After: 5 flaky tests
   # Improvement: -64% ✅ (Target: ≥50%)
   #
   # ## Test Suite Size
   # Before: 5,408 tests (162K LOC)
   # After: 2,521 tests (71K LOC)
   # Reduction: -53% tests, -56% LOC
   #
   # ## Code Coverage
   # Before: 87.3%
   # After: 88.1%
   # Change: +0.8% ✅ (Maintained/improved)
   #
   # ## Bug Escape Rate (Manual)
   # Bugs found in production (30 days post-cleanup): 2
   # Baseline (30 days pre-cleanup): 3
   # Change: -33% ✅ (Fewer bugs escaped)
   ```

**Impact**: A/B validation of cleanup effectiveness, not guesswork

---

#### **Phase 9: Integration with Existing Auditor** (2 tasks)

**Problem Solved**: V4 and V5 should share codebase, not duplicate logic.

**Solution**:
1. **Refactor test_value_audit.py**:
   ```python
   # V5: Backward-compatible integration
   class TestValueAuditor:
       def __init__(self, config_path='weights.yaml'):
           self.weights = load_weights(config_path)  # V5: configurable

           # V5: Optional empirical data sources
           self.runtime_parser = RuntimeParser() if pytest_log_exists() else None
           self.failure_db = FailureDatabase() if ci_logs_exist() else None
           self.git_analyzer = GitChurnAnalyzer() if is_git_repo() else None

       def score_test(self, test):
           # V5: Use empirical data if available, fallback to heuristics

           # Bug detection (V4 heuristics + V5 failure history)
           bug_score = self._score_bug_detection_heuristic(test)
           if self.failure_db:
               bug_score += self.failure_db.get_failure_bonus(test.id)

           # Runtime (V5 actual data + V4 heuristic fallback)
           if self.runtime_parser:
               runtime = self.runtime_parser.get_runtime(test.id)
               runtime_penalty = self._nonlinear_runtime_penalty(runtime)
           else:
               runtime_penalty = self._estimate_runtime_penalty_heuristic(test)

           # Maintenance burden (V5 churn + age + V4 mock count)
           burden = self._score_maintenance_burden_heuristic(test)
           if self.git_analyzer:
               burden += self.git_analyzer.get_churn_penalty(test.file)
               burden += self.git_analyzer.get_age_penalty(test.file)

           # Weighted sum with normalization (V5)
           if self.weights.normalization.mode != 'none':
               bug_score = normalize(bug_score, self.all_bug_scores, mode=self.weights.normalization.mode)
               # ... other components

           total = (
               bug_score * self.weights.bug_detection_weight +
               # ... other components
           )

           return total
   ```

**Impact**: Graceful migration from V4 to V5, no breaking changes

---

#### **Phase 10: Documentation & ADR** (2 tasks)

**Solution**:
1. **ADR-034: Empirical Test Value Scoring**
   - Context: V4 limitations (74% P1, 60% false gaps)
   - Decision: 8 empirical enhancements
   - Consequences: 30-40% better calibration, actionable roadmap
   - Alternatives: Keep heuristics (rejected), Use ML model (future work)

2. **Usage guide updates**:
   - HANDOFF_VALUE_FIRST_TESTING.md: V5 instructions
   - weights.yaml configuration examples
   - Grid search tuner workflow
   - PR safety pipeline usage

---

## Comparison: V4 vs V5

| Feature | V4 (Heuristic) | V5 (Empirical) | Improvement |
|---------|----------------|----------------|-------------|
| **Runtime Penalty** | Keyword-based (`sleep`, `docker`) | **Actual pytest duration** | Precise, non-linear |
| **Bug Detection** | Name heuristics (`regression`, `bug`) | **CI failure history (90 days)** | Proven bug catchers |
| **Maintenance Burden** | Mock count only | **Churn + age + mock context** | Multi-factor accuracy |
| **Mock Classification** | All mocks equal | **External (0.3x) vs internal (0.8x)** | Context-aware |
| **Score Normalization** | None (different scales) | **Z-score or min-max** | Comparable components |
| **Weight Tuning** | Hard-coded | **Grid search on labeled data** | Automated calibration |
| **Threshold Calibration** | Arbitrary (P1 >20, P2 10-20) | **Optimized for 90% accuracy** | Data-driven |
| **Safety Pipeline** | Roadmap suggests mass deletion | **PR-based, human approval** | Constitutional safety |
| **Impact Validation** | None | **Pre/post A/B comparison** | Measurable improvement |
| **Visual Reporting** | Text-only | **Histogram + sampling** | Human-friendly review |
| **P1 Rate** | 74% (unusable) | **15-20% (actionable)** | 4x better calibration |
| **False Positive Rate** | 60% | **<20%** | 3x more accurate |
| **Actionability Score** | 3/10 | **8/10** | Execution-ready roadmap |

---

## Expected V5 Audit Results

### Score Distribution (Projected)

**V4 Distribution** (1,200 tests):
```
HIGH (>20):    308 (26%)  ← Mixed quality (integration + false positives)
MEDIUM (10-20): 0 (0%)    ← Never triggered
LOW (<10):     892 (74%)  ← Massive over-reporting
```

**V5 Distribution** (5,408 tests, projected):
```
HIGH (>20):   1,350 (25%)  ← True high-value (integration, critical path, regression)
MEDIUM (10-20): 3,000 (55%)  ← Review candidates (complex algorithms, edge cases)
LOW (<10):    1,058 (20%)  ← Delete candidates (mocking hell, redundant)
```

### Priority Distribution (Projected)

**V4 Priorities** (1,200 tests):
```
P0 (Critical):      10 (0.8%)  ← 1 false positive
P1 (High):         892 (74.3%) ← Massive over-classification
P2 (Medium):        14 (1.2%)  ← Under-utilized
P3 (Low):            0 (0%)    ← Never triggered
```

**V5 Priorities** (5,408 tests, projected):
```
P0 (Critical):      15 (0.3%)  ← Failing tests, wrong assertions (validated)
P1 (High):         950 (17.5%) ← Missing essential coverage (Normal, Edge, Essential, Spec)
P2 (Medium):     3,200 (59%)   ← Missing secondary coverage (Resilience, Security where applicable)
P3 (Low):        1,243 (23%)   ← Cosmetic issues (naming, formatting)
```

### Actionable Healing Roadmap

**V5 Roadmap Structure**:
```markdown
## Phase 1: P0 Critical Fixes (15 tests, 2 hours)
- [ ] Fix test_X: Assertion checks wrong value (CRITICAL)
- [ ] Fix test_Y: Logic error in test setup (CRITICAL)
[Specific, actionable fixes with code examples]

## Phase 2: P1 High Priority (950 tests, 80 hours)
### Missing Normal Coverage (380 tests)
- [ ] Add happy path test for feature_X
- [ ] Add standard usage test for component_Y
[Grouped by NECESSARY category, specific examples]

### Missing Edge Coverage (570 tests)
- [ ] Add boundary test: min_value=0, max_value=100
- [ ] Add empty input test for list_processor
[Concrete edge cases, not vague "add edge tests"]

## Phase 3: P2 Medium Priority (3,200 tests, 200 hours)
[Optional: Fill secondary gaps after P0/P1 complete]

## Phase 4: P3 Low Priority (1,243 tests, 40 hours)
[Cosmetic fixes: Rename misleading tests, fix docstrings]
```

---

## Recommended Execution Strategy

### Option 1: Full Implementation (14 days, $4.92)

```bash
# Run complete V5 implementation
/primeA --graph missions/test_audit_v5_empirical_scoring.json
```

**Timeline**:
- Week 1: Phases 1-5 (empirical data integration)
- Week 2: Phases 6-10 (calibration, safety, documentation)

**Outcome**: Production-grade test value auditor, 90% accuracy, actionable roadmap

---

### Option 2: Phased Rollout (Validate Before Full Commit)

**Phase 1: Proof of Concept** (3 days, $1.50)
```bash
# Implement only runtime data + failure history (Phases 1-2)
/primeA --graph missions/test_audit_v5_poc.json --plan-only

# Validate on 100-test sample
# If accuracy >85%, proceed to Phase 2
```

**Phase 2: Full Empirical Scoring** (7 days, $2.50)
```bash
# Add git churn, mock classification, normalization (Phases 3-5)
/primeA --graph missions/test_audit_v5_empirical_scoring.json --phase-limit 5
```

**Phase 3: Calibration & Safety** (4 days, $1.00)
```bash
# Complete implementation (Phases 6-10)
/primeA --graph missions/test_audit_v5_empirical_scoring.json --phase-start 6
```

---

### Option 3: Hybrid Approach (Gemini + ChatGPT5 Essentials)

**Focus on highest-impact improvements**:
1. ✅ Actual runtime data (Phase 1) - **Eliminates most inaccurate penalties**
2. ✅ Failure history bonus (Phase 2) - **Prioritizes proven bug detectors**
3. ✅ Configurable weights (Phase 5) - **Enables manual tuning without code changes**
4. ✅ Visual reporting (Phase 7) - **Human-friendly review workflow**
5. ✅ PR safety pipeline (Phase 7) - **Constitutional compliance**

**Skip** (lower priority):
- Git churn analysis (Phase 3) - Nice-to-have, not critical
- Mock classification (Phase 4) - Refinement, not essential
- Grid search tuner (Phase 6) - Manual calibration sufficient initially

**Timeline**: 7 days, $2.00
**Outcome**: 80% of benefits with 50% of effort

---

## Next Steps

### Immediate (5 minutes)
```bash
# Review task graph
cat missions/test_audit_v5_empirical_scoring.json | jq '.phases[].title'

# Validate task graph structure
python -c "
from shared.models.task_graph import TaskGraph
import json
with open('missions/test_audit_v5_empirical_scoring.json') as f:
    graph = TaskGraph.model_validate(json.load(f))
print(f'✅ Task graph validated: {len(graph.phases)} phases, {len(graph.all_tasks())} tasks')
"
```

### Short-term (Today)
```bash
# Option A: Full implementation
/primeA --graph missions/test_audit_v5_empirical_scoring.json

# Option B: Plan-only review
/primeA --graph missions/test_audit_v5_empirical_scoring.json --plan-only

# Option C: Phased rollout (POC first)
/primeA --graph missions/test_audit_v5_poc.json  # Create POC subset
```

### Long-term (2 weeks)
1. **Complete V5 implementation** (10 phases)
2. **Run full audit on 5,408 tests** (6 hours)
3. **Manual labeling** (50 tests, 2 hours)
4. **Grid search calibration** (automated, 10 minutes)
5. **Generate deletion PR** (human approval)
6. **Execute cleanup** (CI validation)
7. **Measure impact** (A/B comparison)
8. **Document learnings** (ADR-034)

---

## Success Criteria

**V5 Audit Passes If**:
1. ✅ P1 rate: 15-20% (down from 74%)
2. ✅ False positive rate: <20% (down from 60%)
3. ✅ Priority accuracy: >90% (up from 82.7%)
4. ✅ Actionability score: ≥8/10 (up from 3/10)
5. ✅ Runtime penalties: Based on actual pytest data
6. ✅ Failure history: Integrated from CI logs (90 days)
7. ✅ Git churn: Reflected in maintenance burden
8. ✅ Mock context: External vs internal classification
9. ✅ Weights: Calibrated via grid search on labeled data
10. ✅ Safety: PR-based deletion workflow (no auto-delete)

**Metrics Validation** (Post-cleanup):
1. ✅ CI runtime: Reduced by ≥30%
2. ✅ Flaky tests: Reduced by ≥50%
3. ✅ Coverage: Maintained or improved
4. ✅ Bug escape rate: Same or lower (30-day comparison)

---

## Files Generated

1. **Task Graph**: `missions/test_audit_v5_empirical_scoring.json` (10 phases, 29 tasks)
2. **This Plan**: `TEST_AUDIT_V5_PLAN.md` (comprehensive overview)
3. **Future Outputs** (after execution):
   - `scripts/parse_pytest_logs.py` (runtime parser)
   - `scripts/ci_failure_tracker.py` (failure history DB)
   - `scripts/git_churn_analyzer.py` (churn + age)
   - `scripts/mock_classifier.py` (external vs internal)
   - `weights.yaml` (configurable scoring)
   - `scripts/grid_search_tuner.py` (weight optimization)
   - `scripts/label_tests.py` (manual labeling tool)
   - `scripts/generate_deletion_pr.py` (PR safety pipeline)
   - `scripts/generate_visual_report.py` (histogram + sampling)
   - `scripts/collect_baseline_metrics.py` (pre-cleanup A/B)
   - `scripts/collect_post_metrics.py` (post-cleanup validation)
   - `docs/adr/ADR-034-empirical-test-value-scoring.md` (architecture decision)

---

## Constitutional Compliance

**Article I: Complete Context**
- ✅ All 8 Gemini suggestions addressed
- ✅ All 8 ChatGPT5 suggestions addressed
- ✅ V4 audit analysis integrated

**Article II: 100% Verification**
- ✅ Every Code task has Test dependency
- ✅ 29 tasks, all with acceptance criteria
- ✅ Integration tests for each phase

**Article III: Automated Enforcement**
- ✅ PR-based deletion workflow (no manual bypass)
- ✅ CI validation required before merge
- ✅ Revert script for rollback safety

**Article IV: Continuous Learning**
- ✅ Grid search calibration stores optimal weights
- ✅ Manual labels stored for future training
- ✅ Audit results queryable via VectorStore

**Article V: Spec-Driven Development**
- ✅ Task graph is the specification
- ✅ Traceability: Gemini feedback → tasks → code
- ✅ ADR documents architectural decision

---

**Ready to execute. Choose your strategy and run `/primeA`.**

**Recommended**: Option 1 (Full implementation, 14 days, $4.92) for production-grade auditor.
**Fastest**: Option 3 (Hybrid, 7 days, $2.00) for 80% benefits with 50% effort.
**Safest**: Option 2 (Phased, 3+7+4 days) for validation checkpoints.

---

**The goal is not perfect thresholds. The goal is systematic calibration based on empirical data and human judgment.**

**Quality > Quantity. Empirical > Heuristic. Data-driven > Guesswork. Always.**
