# ProposalReport Schema Documentation

**EPIC 4.2 Component 4: Statistical Validation & Promotion Decisions**

## Overview

The `ProposalReport` schema provides comprehensive statistical validation for automated agent promotion decisions based on A/B testing results. This is the PRIMARY output of the statistical validation component and the PRIMARY input to the automated promotion component.

## Constitutional Compliance

### Article I: Complete Context Before Action
- **Full Statistical Validation**: All reports include complete statistical analysis (t-tests, confidence intervals, effect sizes)
- **Evidence Preservation**: Raw scores, trial counts, task IDs, and timestamps preserved for audit
- **No Partial Results**: Reports require minimum sample sizes and data quality checks

### Article II: 100% Verification and Stability
- **Rigorous Significance Testing**: P-values, confidence intervals, and effect sizes calculated
- **Quality Gates**: Strict promotion criteria (confidence ≥ 0.95, improvement ≥ 5%, p < 0.05)
- **Verifiable Decisions**: All recommendations backed by statistical evidence

### Article III: Automated Merge Enforcement
- **Auto-Promotion**: `is_auto_promotable()` enforces strict criteria with zero manual overrides
- **Auto-Rejection**: `is_auto_rejectable()` rejects regressions automatically
- **No Bypass Authority**: Promotion gates are absolute barriers

### Article IV: Continuous Learning and Improvement
- **Audit Logging**: `to_audit_log()` creates comprehensive records for VectorStore
- **Pattern Storage**: Successful promotion patterns feed learning system
- **Cross-Session Learning**: Historical decisions inform future thresholds

### Article V: Spec-Driven Development
- **Implements EPIC 4.2**: Formal specification for statistical validation
- **Testable Requirements**: All criteria verifiable via unit tests
- **Living Documentation**: Schema evolves with benchmark infrastructure

## Core Models

### 1. AgentMetrics

Statistical metrics for a single agent variant (challenger or incumbent).

```python
from shared.models.proposal_report import AgentMetrics

metrics = AgentMetrics(
    mean_score=0.85,           # Mean aggregate score (0.0-1.0)
    std_dev=0.12,              # Standard deviation
    sample_size=10,            # Number of benchmark trials
    min_score=0.65,            # Minimum score observed
    max_score=0.95,            # Maximum score observed
    median_score=0.87,         # Median score (P50)
    p95_score=0.93,            # 95th percentile score
    raw_scores=[...]           # All individual scores
)

# Derived metrics
cv = metrics.coefficient_of_variation()  # Relative variability
se = metrics.standard_error()            # Standard error of mean
```

**Key Methods:**
- `coefficient_of_variation()`: Measures relative variability (lower = more stable)
- `standard_error()`: Used for confidence interval calculations

**Validation Rules:**
- All scores must be in [0.0, 1.0] range
- `std_dev` cannot exceed 1.0 for normalized scores
- `raw_scores` must contain at least 1 value

---

### 2. ComparisonResult

Statistical comparison between challenger and incumbent variants.

```python
from shared.models.proposal_report import ComparisonResult, StatisticalTestType

comparison = ComparisonResult(
    test_type=StatisticalTestType.T_TEST,
    p_value=0.012,                  # Probability of observing difference by chance
    confidence_level=0.95,          # Confidence level for intervals
    challenger_ci_lower=0.82,       # Challenger 95% CI lower bound
    challenger_ci_upper=0.94,       # Challenger 95% CI upper bound
    incumbent_ci_lower=0.68,        # Incumbent 95% CI lower bound
    incumbent_ci_upper=0.82,        # Incumbent 95% CI upper bound
    effect_size=1.35,               # Cohen's d (standardized difference)
    is_significant=True,            # True if p_value < 0.05
    degrees_of_freedom=18,          # For t-test
    test_statistic=3.25             # T-statistic value
)

# Check for confidence interval overlap
overlap = comparison.is_ci_overlap()  # False = significant difference
```

**Statistical Test Types:**
- `T_TEST`: Student's t-test (parametric, assumes normality)
- `MANN_WHITNEY`: Mann-Whitney U test (non-parametric)
- `BOOTSTRAP`: Bootstrap confidence intervals
- `BAYESIAN`: Bayesian A/B testing

**Key Methods:**
- `is_ci_overlap()`: Conservative indicator of statistical significance

---

### 3. EvidenceMetadata

Metadata about benchmark evidence and data quality.

```python
from shared.models.proposal_report import EvidenceMetadata
from datetime import datetime, timedelta

start_time = datetime.utcnow() - timedelta(hours=2)
evidence = EvidenceMetadata(
    task_ids=["planner_jwt_auth", "planner_rate_limiting"],
    total_trials=30,
    duration_seconds=7200.0,
    total_cost_usd=2.50,
    results_file="benchmark_results/results_20250108.jsonl",
    timestamp_start=start_time,
    timestamp_end=datetime.utcnow(),
    data_quality_score=1.0,      # 1.0 = perfect, <1.0 = issues detected
    outliers_detected=0          # Number of outlier trials excluded
)
```

**Validation Rules:**
- `timestamp_end` must be after `timestamp_start`
- `task_ids` must contain at least 1 task
- `data_quality_score` in [0.0, 1.0] range

---

### 4. ProposalReport (Primary Model)

Comprehensive A/B test report for automated agent promotion decisions.

```python
from shared.models.proposal_report import ProposalReport, RecommendationType

report = ProposalReport(
    # Agent identifiers
    winner_id="agent_v2_challenger",
    challenger_id="agent_v2_challenger",
    incumbent_id="agent_v1_baseline",

    # Statistical metrics
    confidence=0.98,
    improvement_pct=17.3,          # (challenger_mean - incumbent_mean) / incumbent_mean * 100
    p_value=0.012,

    # Promotion decision
    recommendation=RecommendationType.PROMOTE,

    # Detailed metrics
    challenger_metrics=challenger_metrics,
    incumbent_metrics=incumbent_metrics,
    comparison=comparison,

    # Evidence and audit trail
    evidence=evidence,

    # Cost analysis
    cost_increase_pct=8.0,
    cost_per_trial_challenger=0.13,
    cost_per_trial_incumbent=0.12,

    # Optional context
    notes="High confidence promotion with acceptable cost trade-off",
    risk_factors=[]
)
```

**Recommendation Types:**
- `PROMOTE`: Auto-promotion to production
- `REJECT`: Auto-rejection (regression detected)
- `HUMAN_REVIEW`: Manual review required

---

## Decision Criteria

### AUTO-PROMOTE (Article III Enforcement)

```python
report.is_auto_promotable()  # Returns True if ALL criteria met
```

**Criteria:**
1. ✅ `confidence >= 0.95` (95% statistical confidence)
2. ✅ `improvement_pct >= 5.0` (minimum 5% improvement)
3. ✅ `p_value < 0.05` (statistically significant at α=0.05)
4. ✅ `challenger_metrics.sample_size >= 3` (minimum 3 trials)
5. ✅ `cost_increase_pct <= 20.0` (maximum 20% cost increase)

**Example:**
```python
if report.is_auto_promotable():
    print(f"✅ Auto-promoting {report.challenger_id} to production")
    # Trigger automated deployment pipeline
    deploy_to_production(report.challenger_id)
```

---

### AUTO-REJECT (Quality Gate)

```python
report.is_auto_rejectable()  # Returns True if ANY criterion met
```

**Criteria:**
1. ❌ `improvement_pct < 0` (regression detected)
2. ❌ `confidence < 0.5` (insufficient statistical confidence)
3. ❌ `cost_increase_pct > 50% AND improvement_pct < 10%` (unacceptable cost trade-off)

**Example:**
```python
if report.is_auto_rejectable():
    print(f"❌ Auto-rejecting {report.challenger_id}, keeping {report.incumbent_id}")
    # Log rejection reason
    log_rejection(report)
```

---

### HUMAN REVIEW (Default for Edge Cases)

```python
report.requires_human_review()  # Returns True if review needed
```

**Triggers:**
1. ⚠️ Marginal improvements (0% ≤ improvement < 5%)
2. ⚠️ Risk factors detected (e.g., `["high_variance", "small_sample"]`)
3. ⚠️ Explicit `HUMAN_REVIEW` recommendation
4. ⚠️ Neither auto-promotable nor auto-rejectable

**Example:**
```python
if report.requires_human_review():
    print(f"⚠️  Human review required for {report.challenger_id}")
    # Notify human reviewers
    send_notification_to_reviewers(report)
```

---

## Key Methods

### `get_promotion_summary() -> dict`

Generate human-readable promotion summary.

```python
summary = report.get_promotion_summary()
print(summary)
# {
#     "decision": "PROMOTE",
#     "winner": "agent_v2_challenger",
#     "challenger": "agent_v2_challenger",
#     "incumbent": "agent_v1_baseline",
#     "improvement": "+17.3%",
#     "confidence": "98.0%",
#     "p_value": "0.0120",
#     "sample_size_challenger": 15,
#     "sample_size_incumbent": 15,
#     "cost_impact": "+8.0%",
#     "auto_promotable": True,
#     "requires_review": False,
#     "risk_factors": [],
#     "timestamp": "2025-01-08T12:34:56"
# }
```

**Use Cases:**
- Logging promotion decisions
- Notifications to developers
- Dashboard displays

---

### `to_audit_log() -> dict`

Generate comprehensive audit log entry.

```python
audit_log = report.to_audit_log()

# Save to VectorStore for Article IV compliance
context.store_memory(
    key=f"promotion_decision_{report.created_at.strftime('%Y%m%d_%H%M%S')}",
    content=audit_log,
    tags=["proposal_report", "promotion", report.recommendation.value]
)
```

**Audit Log Structure:**
```json
{
  "report_id": "proposal_20250108_123456",
  "decision": "PROMOTE",
  "agents": {
    "winner": "agent_v2_challenger",
    "challenger": "agent_v2_challenger",
    "incumbent": "agent_v1_baseline"
  },
  "statistics": {
    "confidence": 0.98,
    "improvement_pct": 17.3,
    "p_value": 0.012,
    "effect_size": 1.35,
    "test_type": "t_test"
  },
  "challenger_metrics": { ... },
  "incumbent_metrics": { ... },
  "costs": { ... },
  "evidence": { ... },
  "risk_factors": [],
  "auto_actions": {
    "promotable": true,
    "rejectable": false,
    "requires_review": false
  },
  "timestamp": "2025-01-08T12:34:56",
  "notes": "High confidence promotion..."
}
```

---

## Integration with A/B Testing Infrastructure

### Phase 1: EnhancedABOrchestrator Integration

```python
from dspy_agents.ab_testing import EnhancedABOrchestrator
from shared.models.proposal_report import ProposalReport, AgentMetrics, ComparisonResult, EvidenceMetadata

# Step 1: Run A/B orchestrator
orchestrator = EnhancedABOrchestrator(
    agent_ids=["agent_v1_baseline", "agent_v2_challenger"],
    task_ids=["planner_jwt_auth", "planner_rate_limiting"],
    repeats=10,
    budget_limit=5.0
)

results_path = orchestrator.run()

# Step 2: Load results and calculate statistics
with open(results_path) as f:
    results = [json.loads(line) for line in f]

# Separate by agent
challenger_results = [r for r in results if r["agent_id"] == "agent_v2_challenger"]
incumbent_results = [r for r in results if r["agent_id"] == "agent_v1_baseline"]

# Step 3: Calculate metrics
challenger_scores = [r["scores"]["aggregate"] for r in challenger_results]
incumbent_scores = [r["scores"]["aggregate"] for r in incumbent_results]

challenger_metrics = AgentMetrics(
    mean_score=np.mean(challenger_scores),
    std_dev=np.std(challenger_scores),
    sample_size=len(challenger_scores),
    min_score=min(challenger_scores),
    max_score=max(challenger_scores),
    median_score=np.median(challenger_scores),
    p95_score=np.percentile(challenger_scores, 95),
    raw_scores=challenger_scores
)

# Similar for incumbent_metrics...

# Step 4: Run statistical test (scipy.stats.ttest_ind)
from scipy import stats

t_stat, p_value = stats.ttest_ind(challenger_scores, incumbent_scores)
effect_size = (np.mean(challenger_scores) - np.mean(incumbent_scores)) / np.sqrt(
    (np.var(challenger_scores) + np.var(incumbent_scores)) / 2
)

comparison = ComparisonResult(
    test_type=StatisticalTestType.T_TEST,
    p_value=p_value,
    # ... calculate confidence intervals
    effect_size=effect_size,
    is_significant=p_value < 0.05,
    test_statistic=t_stat
)

# Step 5: Create ProposalReport
report = ProposalReport(
    winner_id="agent_v2_challenger" if np.mean(challenger_scores) > np.mean(incumbent_scores) else "agent_v1_baseline",
    challenger_id="agent_v2_challenger",
    incumbent_id="agent_v1_baseline",
    confidence=1.0 - p_value,
    improvement_pct=((np.mean(challenger_scores) - np.mean(incumbent_scores)) / np.mean(incumbent_scores)) * 100,
    p_value=p_value,
    recommendation=determine_recommendation(confidence, improvement_pct, p_value),
    challenger_metrics=challenger_metrics,
    incumbent_metrics=incumbent_metrics,
    comparison=comparison,
    evidence=evidence,
    cost_increase_pct=calculate_cost_increase(challenger_results, incumbent_results),
    cost_per_trial_challenger=orchestrator.total_cost / len(challenger_results),
    cost_per_trial_incumbent=orchestrator.total_cost / len(incumbent_results)
)

# Step 6: Make promotion decision
if report.is_auto_promotable():
    promote_agent(report.challenger_id)
elif report.is_auto_rejectable():
    reject_agent(report.challenger_id)
else:
    notify_human_reviewers(report)
```

---

## Testing

### Unit Tests

Run comprehensive test suite:

```bash
python -m pytest tests/test_proposal_report_models.py -v
```

**Test Coverage (23 tests, 100% passing):**
- ✅ AgentMetrics validation and methods (7 tests)
- ✅ ComparisonResult validation and CI overlap detection (3 tests)
- ✅ EvidenceMetadata timestamp validation (2 tests)
- ✅ ProposalReport validation and decision logic (11 tests)

**Key Test Scenarios:**
1. Valid model creation with correct data
2. Field validation (score ranges, p-values, timestamps)
3. Auto-promotion criteria enforcement
4. Auto-rejection criteria enforcement
5. Human review triggers (marginal improvements, risk factors)
6. Winner validation (must be challenger or incumbent)
7. Audit log generation and JSON serialization

---

## Demo Script

Run interactive demo:

```bash
python demos/demo_proposal_report.py
```

**Demo Scenarios:**
1. **Clear Winner**: Strong statistical evidence → PROMOTE
2. **Regression**: Challenger underperforms → REJECT
3. **Marginal Improvement**: Borderline case → HUMAN_REVIEW

---

## Constitutional Laws Enforced

### Law #2: Strict Typing Always
- ✅ No `Dict[Any, Any]` - all fields explicitly typed
- ✅ Pydantic models with strict validation
- ✅ `ConfigDict(extra="forbid")` prevents unexpected fields

### Law #3: Validate All Inputs
- ✅ Score range validation [0.0, 1.0]
- ✅ P-value validation [0.0, 1.0]
- ✅ Timestamp ordering validation
- ✅ Winner must be challenger or incumbent

### Law #5: Embrace Functional Error Handling
- ✅ No exceptions for control flow
- ✅ Recommendation always present (PROMOTE/REJECT/HUMAN_REVIEW)
- ✅ Boolean methods for decision logic (`is_auto_promotable()`)

### Law #9: Document Public APIs
- ✅ Comprehensive docstrings for all models and methods
- ✅ Field descriptions in Pydantic models
- ✅ Usage examples in this documentation

---

## Future Enhancements

### Phase 2: Advanced Statistical Tests
- **Bayesian A/B Testing**: Calculate probability that challenger is better
- **Sequential Analysis**: Early stopping for clear winners
- **Multi-Armed Bandit**: Dynamic traffic allocation

### Phase 3: Cost-Quality Trade-off Analysis
- **Pareto Frontier**: Visualize cost vs. quality trade-offs
- **Cost-Adjusted Metrics**: Normalize scores by cost
- **Budget Optimization**: Recommend optimal agent mix for budget

### Phase 4: Continuous Monitoring
- **Post-Promotion Validation**: Monitor promoted agents in production
- **Regression Detection**: Automated rollback on performance degradation
- **A/A Testing**: Validate statistical test calibration

---

## References

- **EPIC 4.2 Specification**: Self-Evolution Architecture
- **Component 4**: Statistical Validation & Promotion Decisions
- **ADR-007**: Spec-Driven Development
- **ADR-008**: Strict Typing (no Dict[Any, Any])
- **Constitution**: Articles I-V, Laws 1-10

---

**Version**: 1.0.0
**Last Updated**: 2025-01-08
**Owner**: EPIC 4.2 Implementation Team
**Status**: Production Ready ✅
