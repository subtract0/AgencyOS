# ProposalReport Schema Quick Reference

**EPIC 4.2 Component 4: Statistical Validation for Agent Promotion**

## Quick Import

```python
from shared.models import (
    ProposalReport,
    ProposalAgentMetrics,
    ComparisonResult,
    EvidenceMetadata,
    RecommendationType,
    StatisticalTestType,
)
```

## Core Models (4)

### 1. ProposalAgentMetrics
Statistical metrics for one agent variant (challenger or incumbent).

```python
metrics = ProposalAgentMetrics(
    mean_score=0.85,        # Mean score (0.0-1.0)
    std_dev=0.12,           # Standard deviation
    sample_size=10,         # Number of trials
    min_score=0.65,         # Min observed
    max_score=0.95,         # Max observed
    median_score=0.87,      # P50
    p95_score=0.93,         # P95
    raw_scores=[...]        # All scores for statistical tests
)
```

### 2. ComparisonResult
Statistical comparison between challenger and incumbent.

```python
comparison = ComparisonResult(
    test_type=StatisticalTestType.T_TEST,
    p_value=0.012,                  # Significance level
    challenger_ci_lower=0.82,       # 95% CI bounds
    challenger_ci_upper=0.94,
    incumbent_ci_lower=0.68,
    incumbent_ci_upper=0.82,
    effect_size=1.35,               # Cohen's d
    is_significant=True,            # p < 0.05
)
```

### 3. EvidenceMetadata
Benchmark evidence and data quality tracking.

```python
evidence = EvidenceMetadata(
    task_ids=["task_1", "task_2"],
    total_trials=30,
    duration_seconds=7200.0,
    total_cost_usd=2.50,
    timestamp_start=start_time,
    timestamp_end=end_time,
)
```

### 4. ProposalReport (Primary)
Comprehensive A/B test report for promotion decisions.

```python
report = ProposalReport(
    winner_id="agent_v2_challenger",
    challenger_id="agent_v2_challenger",
    incumbent_id="agent_v1_baseline",
    confidence=0.98,
    improvement_pct=17.3,
    p_value=0.012,
    recommendation=RecommendationType.PROMOTE,
    challenger_metrics=challenger_metrics,
    incumbent_metrics=incumbent_metrics,
    comparison=comparison,
    evidence=evidence,
    cost_increase_pct=8.0,
)
```

## Decision Criteria (Constitutional Enforcement)

### AUTO-PROMOTE ✅
```python
if report.is_auto_promotable():  # ALL must be true:
    # confidence >= 0.95
    # improvement_pct >= 5.0%
    # p_value < 0.05
    # sample_size >= 3
    # cost_increase_pct <= 20%
    deploy_to_production(report.challenger_id)
```

### AUTO-REJECT ❌
```python
if report.is_auto_rejectable():  # ANY can be true:
    # improvement_pct < 0% (regression)
    # confidence < 0.5
    # cost_increase > 50% AND improvement < 10%
    keep_incumbent(report.incumbent_id)
```

### HUMAN REVIEW ⚠️
```python
if report.requires_human_review():
    # Marginal improvement (0-5%)
    # Risk factors detected
    # Neither promotable nor rejectable
    notify_reviewers(report)
```

## Key Methods

```python
# Human-readable summary
summary = report.get_promotion_summary()
# {
#     "decision": "PROMOTE",
#     "improvement": "+17.3%",
#     "confidence": "98.0%",
#     "auto_promotable": True,
#     ...
# }

# Comprehensive audit log (Article IV)
audit_log = report.to_audit_log()
context.store_memory(
    key=f"promotion_{timestamp}",
    content=audit_log,
    tags=["proposal_report", "promotion"]
)
```

## Enums

```python
class RecommendationType(str, Enum):
    PROMOTE = "PROMOTE"          # Auto-promotion
    REJECT = "REJECT"            # Auto-rejection
    HUMAN_REVIEW = "HUMAN_REVIEW"  # Manual review

class StatisticalTestType(str, Enum):
    T_TEST = "t_test"            # Student's t-test
    MANN_WHITNEY = "mann_whitney"  # Non-parametric
    BOOTSTRAP = "bootstrap"      # Bootstrap CI
    BAYESIAN = "bayesian"        # Bayesian A/B
```

## Constitutional Compliance

- **Article I**: Complete context - full statistical validation
- **Article II**: 100% verification - rigorous significance testing
- **Article III**: Automated merge - no bypass authority
- **Article IV**: Learning - audit logs to VectorStore
- **Law #2**: Strict typing (no Dict[Any, Any])
- **Law #3**: Input validation (Pydantic)

## Files

- **Model**: `shared/models/proposal_report.py`
- **Tests**: `tests/test_proposal_report_models.py` (23 tests, 100% pass)
- **Demo**: `demos/demo_proposal_report.py`
- **Docs**: `docs/PROPOSAL_REPORT_SCHEMA.md`

## Usage Pattern

```python
# 1. Run A/B orchestrator
orchestrator = EnhancedABOrchestrator(agent_ids=[...], ...)
results_path = orchestrator.run()

# 2. Calculate statistics (scipy.stats.ttest_ind)
t_stat, p_value = stats.ttest_ind(challenger_scores, incumbent_scores)

# 3. Create ProposalReport
report = ProposalReport(...)

# 4. Make decision
if report.is_auto_promotable():
    promote_agent(report.challenger_id)
elif report.is_auto_rejectable():
    reject_agent(report.challenger_id)
else:
    notify_human_reviewers(report)

# 5. Log to VectorStore (Article IV)
context.store_memory("promotion_decision", report.to_audit_log())
```

---

**Version**: 1.0.0 | **Status**: Production Ready ✅ | **EPIC**: 4.2.4
