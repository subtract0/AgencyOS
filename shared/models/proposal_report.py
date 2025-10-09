"""
ProposalReport Models for EPIC 4.2 Component 4: Automated Agent Promotion

Comprehensive schema for statistical A/B test analysis and promotion decisions.

CONSTITUTIONAL COMPLIANCE:
- Article I: Complete context - full statistical validation before decisions
- Article II: 100% verification - rigorous statistical significance testing
- Article III: Automated merge enforcement - promotion gates are absolute
- Article IV: Continuous learning - decisions feed back into benchmarks
- Article V: Spec-driven - implements EPIC 4.2 formal specification

DESIGN PRINCIPLES:
- Strict typing (Constitutional Law #2): No Dict[Any, Any]
- Result pattern (Constitutional Law #5): Statistical outcomes as Result types
- TDD-first (Constitutional Law #1): Testable, verifiable metrics
- Input validation (Constitutional Law #3): All thresholds validated
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from shared.type_definitions.json import JSONValue


class RecommendationType(str, Enum):
    """
    Promotion recommendation types based on statistical analysis.

    Constitutional enforcement levels:
    - PROMOTE: Auto-promotion (Article III - automated merge)
    - REJECT: Auto-rejection (statistical evidence of regression)
    - HUMAN_REVIEW: Manual review required (insufficient confidence)
    """

    PROMOTE = "PROMOTE"
    REJECT = "REJECT"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class StatisticalTestType(str, Enum):
    """Types of statistical tests used for validation."""

    T_TEST = "t_test"  # Student's t-test (parametric)
    MANN_WHITNEY = "mann_whitney"  # Mann-Whitney U test (non-parametric)
    BOOTSTRAP = "bootstrap"  # Bootstrap confidence intervals
    BAYESIAN = "bayesian"  # Bayesian A/B test


class AgentMetrics(BaseModel):
    """
    Statistical metrics for a single agent variant.

    Contains:
    - Central tendency: mean score
    - Dispersion: standard deviation
    - Sample size: number of benchmark runs
    - Raw data: all individual scores for further analysis

    Constitutional Compliance:
    - Article II: 100% verification - all scores recorded
    - Article I: Complete context - raw data preserved
    """

    model_config = ConfigDict(extra="forbid")

    mean_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mean aggregate score (0.0-1.0 range)"
    )
    std_dev: float = Field(..., ge=0.0, description="Standard deviation of scores")
    sample_size: int = Field(..., ge=1, description="Number of benchmark trials")
    min_score: float = Field(..., ge=0.0, le=1.0, description="Minimum score observed")
    max_score: float = Field(..., ge=0.0, le=1.0, description="Maximum score observed")
    median_score: float = Field(..., ge=0.0, le=1.0, description="Median score (P50)")
    p95_score: float = Field(..., ge=0.0, le=1.0, description="95th percentile score")
    raw_scores: list[float] = Field(
        ..., min_length=1, description="All individual scores for statistical tests"
    )

    @field_validator("raw_scores")
    def validate_raw_scores(cls, v: list[float]) -> list[float]:
        """Ensure all scores are in valid range [0.0, 1.0]."""
        for score in v:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Score {score} outside valid range [0.0, 1.0]")
        return v

    @field_validator("std_dev")
    def validate_std_dev(cls, v: float) -> float:
        """Standard deviation cannot exceed 1.0 for normalized scores."""
        if v > 1.0:
            raise ValueError("Standard deviation cannot exceed 1.0 for normalized scores")
        return v

    def coefficient_of_variation(self) -> float:
        """
        Calculate coefficient of variation (CV).

        CV = std_dev / mean (if mean > 0)
        Measures relative variability (lower is more stable).
        """
        if self.mean_score == 0:
            return 0.0
        return self.std_dev / self.mean_score

    def standard_error(self) -> float:
        """
        Calculate standard error of the mean.

        SE = std_dev / sqrt(sample_size)
        Used for confidence interval calculations.
        """
        import math

        return self.std_dev / math.sqrt(self.sample_size)


class ComparisonResult(BaseModel):
    """
    Statistical comparison between two agent variants.

    Contains:
    - Test type used (t-test, Mann-Whitney, etc.)
    - P-value (probability of observing difference by chance)
    - Confidence intervals for both variants
    - Effect size (magnitude of difference)
    - Statistical significance flag

    Constitutional Compliance:
    - Article II: 100% verification - rigorous statistical validation
    - Article I: Complete context - full test results preserved
    """

    model_config = ConfigDict(extra="forbid")

    test_type: StatisticalTestType = Field(..., description="Statistical test used for comparison")
    p_value: float = Field(
        ..., ge=0.0, le=1.0, description="P-value from statistical test (0.0-1.0)"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Confidence level for intervals (default 0.95)"
    )
    challenger_ci_lower: float = Field(
        ..., description="Challenger 95% confidence interval lower bound"
    )
    challenger_ci_upper: float = Field(
        ..., description="Challenger 95% confidence interval upper bound"
    )
    incumbent_ci_lower: float = Field(
        ..., description="Incumbent 95% confidence interval lower bound"
    )
    incumbent_ci_upper: float = Field(
        ..., description="Incumbent 95% confidence interval upper bound"
    )
    effect_size: float = Field(
        ..., description="Cohen's d or similar effect size metric (standardized difference)"
    )
    is_significant: bool = Field(
        ..., description="True if p_value < alpha threshold (typically 0.05)"
    )
    degrees_of_freedom: int | None = Field(
        None, description="Degrees of freedom for t-test (None for non-parametric)"
    )
    test_statistic: float | None = Field(
        None, description="Test statistic value (t-statistic, U-statistic, etc.)"
    )

    @field_validator("p_value")
    def validate_p_value(cls, v: float) -> float:
        """P-value must be in [0.0, 1.0] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"P-value {v} outside valid range [0.0, 1.0]")
        return v

    def is_ci_overlap(self) -> bool:
        """
        Check if confidence intervals overlap.

        Non-overlapping CIs suggest significant difference.
        Conservative indicator of statistical significance.
        """
        # Check if challenger CI overlaps with incumbent CI
        return not (
            self.challenger_ci_upper < self.incumbent_ci_lower
            or self.challenger_ci_lower > self.incumbent_ci_upper
        )


class EvidenceMetadata(BaseModel):
    """
    Metadata about benchmark evidence used in promotion decision.

    Contains:
    - Task IDs benchmarked
    - Duration of testing period
    - Cost tracking
    - Data quality indicators

    Constitutional Compliance:
    - Article I: Complete context - full evidence trail
    - Article IV: Continuous learning - evidence feeds learning system
    """

    model_config = ConfigDict(extra="forbid")

    task_ids: list[str] = Field(..., min_length=1, description="Benchmark task IDs executed")
    total_trials: int = Field(..., ge=1, description="Total number of trials across all tasks")
    duration_seconds: float = Field(..., ge=0.0, description="Total duration of A/B test")
    total_cost_usd: float = Field(..., ge=0.0, description="Total cost of benchmark runs")
    results_file: str | None = Field(None, description="Path to JSONL results file for audit trail")
    timestamp_start: datetime = Field(..., description="A/B test start timestamp")
    timestamp_end: datetime = Field(..., description="A/B test end timestamp")
    data_quality_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Data quality indicator (1.0 = perfect, <1.0 = issues detected)",
    )
    outliers_detected: int = Field(
        default=0, ge=0, description="Number of outlier trials detected and excluded"
    )

    @field_validator("timestamp_end")
    def validate_timestamps(cls, v: datetime, info) -> datetime:
        """Ensure end timestamp is after start timestamp."""
        if "timestamp_start" in info.data and v < info.data["timestamp_start"]:
            raise ValueError("timestamp_end must be after timestamp_start")
        return v


class ProposalReport(BaseModel):
    """
    Comprehensive A/B test report for automated agent promotion decisions.

    This is the PRIMARY output of EPIC 4.2 Component 4 (Statistical Validation).
    Used by Component 5 (Automated Promotion) to make promotion decisions.

    PROMOTION DECISION RULES (Constitutional Enforcement):

    1. PROMOTE (Auto-Merge):
       - confidence >= 0.95
       - improvement_pct >= 5.0%
       - p_value < 0.05
       - sample_size >= min_samples threshold
       - no cost regression > 20%

    2. REJECT (Auto-Reject):
       - confidence < 0.5 OR
       - improvement_pct < 0% (regression) OR
       - cost_increase_pct > 50% with improvement < 10%

    3. HUMAN_REVIEW (Manual Review):
       - All other cases
       - Marginal improvements (0-5%)
       - High variance in results
       - Insufficient statistical power

    Constitutional Compliance:
    - Article I: Complete context - full statistical validation
    - Article II: 100% verification - rigorous significance testing
    - Article III: Automated merge - PROMOTE triggers auto-promotion
    - Article IV: Learning - results stored in VectorStore
    - Article V: Spec-driven - implements EPIC 4.2 specification

    Constitutional Laws Enforced:
    - Law #2: Strict typing (no Dict[Any, Any])
    - Law #3: Input validation (Pydantic validators)
    - Law #5: No exceptions (recommendation always present)
    """

    model_config = ConfigDict(extra="forbid")

    # Agent identifiers
    winner_id: str = Field(..., description="Agent variant that performed best")
    challenger_id: str = Field(..., description="New agent variant being tested")
    incumbent_id: str = Field(..., description="Current production agent variant")

    # Statistical metrics
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Statistical confidence in result (0.0-1.0)"
    )
    improvement_pct: float = Field(
        ..., description="Percentage improvement of winner over incumbent (can be negative)"
    )
    p_value: float = Field(
        ..., ge=0.0, le=1.0, description="P-value from statistical significance test"
    )

    # Promotion decision
    recommendation: RecommendationType = Field(
        ..., description="Automated promotion recommendation"
    )

    # Detailed metrics
    challenger_metrics: AgentMetrics = Field(
        ..., description="Statistical metrics for challenger variant"
    )
    incumbent_metrics: AgentMetrics = Field(
        ..., description="Statistical metrics for incumbent variant"
    )
    comparison: ComparisonResult = Field(
        ..., description="Statistical comparison between challenger and incumbent"
    )

    # Evidence and audit trail
    evidence: EvidenceMetadata = Field(
        ..., description="Metadata about benchmark evidence and data quality"
    )

    # Cost analysis
    cost_increase_pct: float = Field(
        ..., description="Percentage increase in cost per trial (negative = cost savings)"
    )
    cost_per_trial_challenger: float = Field(
        ..., ge=0.0, description="Average cost per trial for challenger"
    )
    cost_per_trial_incumbent: float = Field(
        ..., ge=0.0, description="Average cost per trial for incumbent"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report creation timestamp"
    )

    # Additional context
    notes: str | None = Field(
        None, description="Optional notes about edge cases or manual overrides"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Identified risk factors (e.g., 'high_variance', 'small_sample')",
    )

    @model_validator(mode="after")
    def validate_winner_is_challenger_or_incumbent(self) -> ProposalReport:
        """Winner must be either challenger or incumbent."""
        if self.winner_id not in [self.challenger_id, self.incumbent_id]:
            raise ValueError(
                f"winner_id '{self.winner_id}' must be either challenger_id "
                f"'{self.challenger_id}' or incumbent_id '{self.incumbent_id}'"
            )
        return self

    @field_validator("recommendation")
    def validate_recommendation_logic(cls, v: RecommendationType, info) -> RecommendationType:
        """
        Validate recommendation follows constitutional decision rules.

        This is a SOFT validation (warning, not error) to allow flexibility
        for manual overrides while preserving audit trail.
        """
        # Skip validation if not all fields present
        required_fields = ["confidence", "improvement_pct", "p_value"]
        if not all(field in info.data for field in required_fields):
            return v

        confidence = info.data["confidence"]
        improvement = info.data["improvement_pct"]
        p_value = info.data["p_value"]

        # PROMOTE criteria
        if v == RecommendationType.PROMOTE:
            if not (confidence >= 0.95 and improvement >= 5.0 and p_value < 0.05):
                # Log warning but allow (manual override case)
                print(
                    f"WARNING: PROMOTE recommendation does not meet standard criteria "
                    f"(confidence={confidence:.2f}, improvement={improvement:.1f}%, "
                    f"p_value={p_value:.4f})"
                )

        # REJECT criteria
        elif v == RecommendationType.REJECT:
            if not (confidence < 0.5 or improvement < 0):
                # Log warning but allow
                print(
                    f"WARNING: REJECT recommendation does not meet standard criteria "
                    f"(confidence={confidence:.2f}, improvement={improvement:.1f}%)"
                )

        return v

    def is_auto_promotable(self) -> bool:
        """
        Check if report meets criteria for automated promotion.

        Returns:
            True if PROMOTE recommendation with all criteria met

        Constitutional Enforcement:
        - Article III: Automated merge enforcement
        - No bypass authority - criteria are absolute
        """
        if self.recommendation != RecommendationType.PROMOTE:
            return False

        # Strict promotion criteria
        return (
            self.confidence >= 0.95
            and self.improvement_pct >= 5.0
            and self.p_value < 0.05
            and self.challenger_metrics.sample_size >= 3  # Minimum trials
            and self.cost_increase_pct <= 20.0  # Max 20% cost increase
        )

    def is_auto_rejectable(self) -> bool:
        """
        Check if report meets criteria for automated rejection.

        Returns:
            True if REJECT recommendation with clear regression

        Constitutional Enforcement:
        - Article III: Automated quality gates
        """
        if self.recommendation != RecommendationType.REJECT:
            return False

        # Auto-reject on regression or very low confidence
        return self.improvement_pct < 0 or self.confidence < 0.5

    def requires_human_review(self) -> bool:
        """
        Check if report requires manual human review.

        Returns:
            True if HUMAN_REVIEW recommendation or edge cases detected
        """
        if self.recommendation == RecommendationType.HUMAN_REVIEW:
            return True

        # Force human review on risk factors
        if self.risk_factors:
            return True

        # Force human review on marginal improvements
        if 0 <= self.improvement_pct < 5.0:
            return True

        return False

    def get_promotion_summary(self) -> dict[str, JSONValue]:
        """
        Generate human-readable promotion summary.

        Returns:
            Dictionary with key metrics and decision rationale

        Used for:
        - Logging promotion decisions
        - Notifications to developers
        - Audit trail documentation
        """
        return {
            "decision": self.recommendation.value,
            "winner": self.winner_id,
            "challenger": self.challenger_id,
            "incumbent": self.incumbent_id,
            "improvement": f"{self.improvement_pct:+.1f}%",
            "confidence": f"{self.confidence:.1%}",
            "p_value": f"{self.p_value:.4f}",
            "sample_size_challenger": self.challenger_metrics.sample_size,
            "sample_size_incumbent": self.incumbent_metrics.sample_size,
            "cost_impact": f"{self.cost_increase_pct:+.1f}%",
            "auto_promotable": self.is_auto_promotable(),
            "requires_review": self.requires_human_review(),
            "risk_factors": self.risk_factors,
            "timestamp": self.created_at.isoformat(),
        }

    def to_audit_log(self) -> dict[str, JSONValue]:
        """
        Generate comprehensive audit log entry.

        Returns:
            Full serialization for persistent audit trail

        Constitutional Compliance:
        - Article I: Complete context for audit
        - Article IV: Learning from promotion decisions
        """
        return {
            "report_id": f"proposal_{self.created_at.strftime('%Y%m%d_%H%M%S')}",
            "decision": self.recommendation.value,
            "agents": {
                "winner": self.winner_id,
                "challenger": self.challenger_id,
                "incumbent": self.incumbent_id,
            },
            "statistics": {
                "confidence": self.confidence,
                "improvement_pct": self.improvement_pct,
                "p_value": self.p_value,
                "effect_size": self.comparison.effect_size,
                "test_type": self.comparison.test_type.value,
            },
            "challenger_metrics": {
                "mean": self.challenger_metrics.mean_score,
                "std_dev": self.challenger_metrics.std_dev,
                "sample_size": self.challenger_metrics.sample_size,
                "cv": self.challenger_metrics.coefficient_of_variation(),
            },
            "incumbent_metrics": {
                "mean": self.incumbent_metrics.mean_score,
                "std_dev": self.incumbent_metrics.std_dev,
                "sample_size": self.incumbent_metrics.sample_size,
                "cv": self.incumbent_metrics.coefficient_of_variation(),
            },
            "costs": {
                "challenger_per_trial": self.cost_per_trial_challenger,
                "incumbent_per_trial": self.cost_per_trial_incumbent,
                "increase_pct": self.cost_increase_pct,
            },
            "evidence": {
                "task_ids": self.evidence.task_ids,
                "total_trials": self.evidence.total_trials,
                "duration_seconds": self.evidence.duration_seconds,
                "total_cost_usd": self.evidence.total_cost_usd,
                "data_quality": self.evidence.data_quality_score,
            },
            "risk_factors": self.risk_factors,
            "auto_actions": {
                "promotable": self.is_auto_promotable(),
                "rejectable": self.is_auto_rejectable(),
                "requires_review": self.requires_human_review(),
            },
            "timestamp": self.created_at.isoformat(),
            "notes": self.notes,
        }


__all__ = [
    "RecommendationType",
    "StatisticalTestType",
    "AgentMetrics",
    "ComparisonResult",
    "EvidenceMetadata",
    "ProposalReport",
]
