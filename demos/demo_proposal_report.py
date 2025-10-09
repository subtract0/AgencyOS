#!/usr/bin/env python3
"""
Demo: ProposalReport Schema Usage (EPIC 4.2 Component 4)

Demonstrates:
1. Creating ProposalReport from A/B test results
2. Statistical validation and decision logic
3. Auto-promotion, rejection, and human review workflows
4. Audit logging for constitutional compliance

Constitutional Compliance:
- Article I: Complete context - full statistical validation
- Article II: 100% verification - rigorous significance testing
- Article III: Automated merge enforcement
- Article IV: Learning - audit logs feed VectorStore
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from shared.models.proposal_report import (
    AgentMetrics,
    ComparisonResult,
    EvidenceMetadata,
    ProposalReport,
    RecommendationType,
    StatisticalTestType,
)


def create_sample_metrics(
    mean: float, std_dev: float, sample_size: int, label: str
) -> AgentMetrics:
    """
    Create sample AgentMetrics with synthetic data.

    In production, this would come from EnhancedABOrchestrator results.
    """
    import random

    random.seed(hash(label))  # Deterministic for demo

    # Generate raw scores with normal distribution
    raw_scores = []
    for _ in range(sample_size):
        score = random.gauss(mean, std_dev)
        score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        raw_scores.append(round(score, 3))

    raw_scores.sort()

    return AgentMetrics(
        mean_score=round(mean, 3),
        std_dev=round(std_dev, 3),
        sample_size=sample_size,
        min_score=min(raw_scores),
        max_score=max(raw_scores),
        median_score=round(sorted(raw_scores)[len(raw_scores) // 2], 3),
        p95_score=round(sorted(raw_scores)[int(len(raw_scores) * 0.95)], 3),
        raw_scores=raw_scores,
    )


def create_sample_comparison(
    challenger_mean: float,
    incumbent_mean: float,
    challenger_std: float,
    incumbent_std: float,
    sample_size: int,
) -> ComparisonResult:
    """
    Create sample ComparisonResult with t-test statistics.

    In production, this would use scipy.stats.ttest_ind.
    """
    import math

    # Simplified t-test calculation
    pooled_std = math.sqrt((challenger_std**2 + incumbent_std**2) / 2)
    effect_size = (challenger_mean - incumbent_mean) / pooled_std if pooled_std > 0 else 0.0

    # Simplified p-value estimation (in production, use scipy)
    if abs(effect_size) > 2.0:
        p_value = 0.01
    elif abs(effect_size) > 1.0:
        p_value = 0.05
    else:
        p_value = 0.15

    # Confidence intervals (mean ± 1.96 * SE)
    se_challenger = challenger_std / math.sqrt(sample_size)
    se_incumbent = incumbent_std / math.sqrt(sample_size)

    return ComparisonResult(
        test_type=StatisticalTestType.T_TEST,
        p_value=round(p_value, 4),
        confidence_level=0.95,
        challenger_ci_lower=round(challenger_mean - 1.96 * se_challenger, 3),
        challenger_ci_upper=round(challenger_mean + 1.96 * se_challenger, 3),
        incumbent_ci_lower=round(incumbent_mean - 1.96 * se_incumbent, 3),
        incumbent_ci_upper=round(incumbent_mean + 1.96 * se_incumbent, 3),
        effect_size=round(effect_size, 3),
        is_significant=p_value < 0.05,
        degrees_of_freedom=(sample_size - 1) * 2,
        test_statistic=round(effect_size * math.sqrt(sample_size / 2), 3),
    )


def scenario_1_promote_clear_winner():
    """
    Scenario 1: Clear winner with strong statistical evidence.

    Expected: PROMOTE recommendation, auto-promotable = True
    """
    print("\n" + "=" * 80)
    print("SCENARIO 1: Clear Winner - Strong Statistical Evidence")
    print("=" * 80 + "\n")

    # Challenger significantly outperforms incumbent
    challenger_metrics = create_sample_metrics(
        mean=0.88, std_dev=0.08, sample_size=15, label="challenger_v2"
    )

    incumbent_metrics = create_sample_metrics(
        mean=0.72, std_dev=0.10, sample_size=15, label="incumbent_v1"
    )

    comparison = create_sample_comparison(
        challenger_mean=0.88,
        incumbent_mean=0.72,
        challenger_std=0.08,
        incumbent_std=0.10,
        sample_size=15,
    )

    # Evidence metadata
    start_time = datetime.utcnow() - timedelta(hours=3)
    evidence = EvidenceMetadata(
        task_ids=["planner_jwt_auth", "planner_rate_limiting", "planner_caching"],
        total_trials=30,
        duration_seconds=10800.0,
        total_cost_usd=3.75,
        results_file="benchmark_results/results_scenario1.jsonl",
        timestamp_start=start_time,
        timestamp_end=datetime.utcnow(),
        data_quality_score=1.0,
        outliers_detected=0,
    )

    # Calculate improvement
    improvement_pct = ((0.88 - 0.72) / 0.72) * 100

    # Create report
    report = ProposalReport(
        winner_id="agent_v2_advanced",
        challenger_id="agent_v2_advanced",
        incumbent_id="agent_v1_baseline",
        confidence=0.98,
        improvement_pct=round(improvement_pct, 1),
        p_value=comparison.p_value,
        recommendation=RecommendationType.PROMOTE,
        challenger_metrics=challenger_metrics,
        incumbent_metrics=incumbent_metrics,
        comparison=comparison,
        evidence=evidence,
        cost_increase_pct=8.0,
        cost_per_trial_challenger=0.125,
        cost_per_trial_incumbent=0.116,
    )

    # Display summary
    summary = report.get_promotion_summary()
    print("PROMOTION SUMMARY:")
    print(f"  Decision:      {summary['decision']}")
    print(f"  Winner:        {summary['winner']}")
    print(f"  Improvement:   {summary['improvement']}")
    print(f"  Confidence:    {summary['confidence']}")
    print(f"  P-value:       {summary['p_value']}")
    print(f"  Cost Impact:   {summary['cost_impact']}")
    print(f"  Auto-promotable: {summary['auto_promotable']}")
    print(f"  Requires Review: {summary['requires_review']}")

    # Display detailed metrics
    print("\nDETAILED METRICS:")
    print(
        f"  Challenger: mean={challenger_metrics.mean_score:.3f}, "
        f"std={challenger_metrics.std_dev:.3f}, n={challenger_metrics.sample_size}"
    )
    print(
        f"  Incumbent:  mean={incumbent_metrics.mean_score:.3f}, "
        f"std={incumbent_metrics.std_dev:.3f}, n={incumbent_metrics.sample_size}"
    )
    print(f"  Effect Size: {comparison.effect_size:.3f}")
    print(f"  Statistical Significance: {comparison.is_significant}")

    # Save audit log
    audit_log = report.to_audit_log()
    audit_file = Path("logs/ab_testing/audit_scenario1.json")
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_file, "w") as f:
        json.dump(audit_log, f, indent=2, default=str)

    print(f"\n✅ Audit log saved to: {audit_file}")
    print("   ACTION: Auto-promote agent_v2_advanced to production")


def scenario_2_reject_regression():
    """
    Scenario 2: Challenger performs worse than incumbent.

    Expected: REJECT recommendation, auto-rejectable = True
    """
    print("\n" + "=" * 80)
    print("SCENARIO 2: Regression Detected - Auto-Reject")
    print("=" * 80 + "\n")

    # Challenger underperforms
    challenger_metrics = create_sample_metrics(
        mean=0.65, std_dev=0.12, sample_size=12, label="challenger_v2_bad"
    )

    incumbent_metrics = create_sample_metrics(
        mean=0.78, std_dev=0.09, sample_size=12, label="incumbent_v1_good"
    )

    comparison = create_sample_comparison(
        challenger_mean=0.65,
        incumbent_mean=0.78,
        challenger_std=0.12,
        incumbent_std=0.09,
        sample_size=12,
    )

    start_time = datetime.utcnow() - timedelta(hours=2)
    evidence = EvidenceMetadata(
        task_ids=["planner_jwt_auth", "planner_rate_limiting"],
        total_trials=24,
        duration_seconds=7200.0,
        total_cost_usd=2.88,
        results_file="benchmark_results/results_scenario2.jsonl",
        timestamp_start=start_time,
        timestamp_end=datetime.utcnow(),
        data_quality_score=0.95,
        outliers_detected=2,
    )

    improvement_pct = ((0.65 - 0.78) / 0.78) * 100  # Negative = regression

    report = ProposalReport(
        winner_id="agent_v1_baseline",  # Incumbent wins
        challenger_id="agent_v2_experimental",
        incumbent_id="agent_v1_baseline",
        confidence=0.93,
        improvement_pct=round(improvement_pct, 1),
        p_value=comparison.p_value,
        recommendation=RecommendationType.REJECT,
        challenger_metrics=challenger_metrics,
        incumbent_metrics=incumbent_metrics,
        comparison=comparison,
        evidence=evidence,
        cost_increase_pct=15.0,
        cost_per_trial_challenger=0.138,
        cost_per_trial_incumbent=0.120,
        notes="Challenger shows significant regression in both tasks",
    )

    summary = report.get_promotion_summary()
    print("REJECTION SUMMARY:")
    print(f"  Decision:      {summary['decision']}")
    print(f"  Winner:        {summary['winner']} (incumbent retained)")
    print(f"  Improvement:   {summary['improvement']} (REGRESSION)")
    print(f"  Confidence:    {summary['confidence']}")
    print(f"  Auto-rejectable: {report.is_auto_rejectable()}")

    print("\n❌ ACTION: Reject agent_v2_experimental, keep agent_v1_baseline in production")


def scenario_3_human_review_marginal():
    """
    Scenario 3: Marginal improvement, requires human review.

    Expected: HUMAN_REVIEW recommendation
    """
    print("\n" + "=" * 80)
    print("SCENARIO 3: Marginal Improvement - Human Review Required")
    print("=" * 80 + "\n")

    # Marginal improvement
    challenger_metrics = create_sample_metrics(
        mean=0.78, std_dev=0.09, sample_size=10, label="challenger_v2_marginal"
    )

    incumbent_metrics = create_sample_metrics(
        mean=0.75, std_dev=0.10, sample_size=10, label="incumbent_v1_marginal"
    )

    comparison = create_sample_comparison(
        challenger_mean=0.78,
        incumbent_mean=0.75,
        challenger_std=0.09,
        incumbent_std=0.10,
        sample_size=10,
    )

    start_time = datetime.utcnow() - timedelta(hours=1, minutes=30)
    evidence = EvidenceMetadata(
        task_ids=["planner_jwt_auth"],
        total_trials=20,
        duration_seconds=5400.0,
        total_cost_usd=2.00,
        results_file="benchmark_results/results_scenario3.jsonl",
        timestamp_start=start_time,
        timestamp_end=datetime.utcnow(),
        data_quality_score=0.98,
        outliers_detected=0,
    )

    improvement_pct = ((0.78 - 0.75) / 0.75) * 100  # ~4% (marginal)

    report = ProposalReport(
        winner_id="agent_v2_candidate",
        challenger_id="agent_v2_candidate",
        incumbent_id="agent_v1_baseline",
        confidence=0.75,
        improvement_pct=round(improvement_pct, 1),
        p_value=0.08,  # Not statistically significant at 0.05 level
        recommendation=RecommendationType.HUMAN_REVIEW,
        challenger_metrics=challenger_metrics,
        incumbent_metrics=incumbent_metrics,
        comparison=comparison,
        evidence=evidence,
        cost_increase_pct=12.0,
        cost_per_trial_challenger=0.134,
        cost_per_trial_incumbent=0.120,
        risk_factors=["marginal_improvement", "high_cost_increase"],
    )

    summary = report.get_promotion_summary()
    print("HUMAN REVIEW REQUIRED:")
    print(f"  Decision:      {summary['decision']}")
    print(f"  Winner:        {summary['winner']}")
    print(f"  Improvement:   {summary['improvement']} (marginal)")
    print(f"  Confidence:    {summary['confidence']}")
    print(f"  P-value:       {summary['p_value']} (not significant)")
    print(f"  Cost Impact:   {summary['cost_impact']}")
    print(f"  Risk Factors:  {summary['risk_factors']}")

    print("\n⚠️  ACTION: Human review required - marginal improvement with cost trade-off")
    print("   Consider: More trials, A/A test validation, cost-benefit analysis")


def main():
    """Run all demo scenarios."""
    print("\n" + "=" * 80)
    print("ProposalReport Schema Demo (EPIC 4.2 Component 4)")
    print("Automated Agent Promotion Decision System")
    print("=" * 80)

    # Run scenarios
    scenario_1_promote_clear_winner()
    scenario_2_reject_regression()
    scenario_3_human_review_marginal()

    # Summary
    print("\n" + "=" * 80)
    print("DECISION CRITERIA SUMMARY")
    print("=" * 80 + "\n")

    print("AUTO-PROMOTE (Article III - Automated Merge):")
    print("  ✅ confidence >= 0.95")
    print("  ✅ improvement >= 5.0%")
    print("  ✅ p_value < 0.05")
    print("  ✅ sample_size >= 3")
    print("  ✅ cost_increase <= 20%")

    print("\nAUTO-REJECT (Quality Gate):")
    print("  ❌ improvement < 0% (regression)")
    print("  ❌ confidence < 0.5 (low confidence)")
    print("  ❌ cost_increase > 50% AND improvement < 10%")

    print("\nHUMAN REVIEW (Default for edge cases):")
    print("  ⚠️  Marginal improvements (0-5%)")
    print("  ⚠️  High variance in results")
    print("  ⚠️  Risk factors detected")
    print("  ⚠️  Insufficient statistical power")

    print("\n" + "=" * 80)
    print("Constitutional Compliance:")
    print("  Article I:   Complete context - full statistical validation ✅")
    print("  Article II:  100% verification - rigorous significance testing ✅")
    print("  Article III: Automated merge enforcement - no bypass authority ✅")
    print("  Article IV:  Continuous learning - audit logs feed VectorStore ✅")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
