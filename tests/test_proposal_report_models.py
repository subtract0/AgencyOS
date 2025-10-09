"""
Test suite for ProposalReport models (EPIC 4.2 Component 4).

Constitutional Compliance:
- Law #1: TDD - tests written for schema validation
- Law #2: Strict typing - validates Pydantic model enforcement
- Law #3: Input validation - tests all validators
- Article II: 100% verification - comprehensive test coverage
"""

import json
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from shared.models.proposal_report import (
    AgentMetrics,
    ComparisonResult,
    EvidenceMetadata,
    ProposalReport,
    RecommendationType,
    StatisticalTestType,
)


class TestAgentMetrics:
    """Test AgentMetrics model validation and methods."""

    def test_valid_agent_metrics(self):
        """Test creation of valid AgentMetrics instance."""
        metrics = AgentMetrics(
            mean_score=0.85,
            std_dev=0.12,
            sample_size=10,
            min_score=0.65,
            max_score=0.95,
            median_score=0.87,
            p95_score=0.93,
            raw_scores=[0.65, 0.75, 0.8, 0.82, 0.85, 0.87, 0.88, 0.9, 0.92, 0.95],
        )

        assert metrics.mean_score == 0.85
        assert metrics.std_dev == 0.12
        assert metrics.sample_size == 10
        assert len(metrics.raw_scores) == 10

    def test_score_validation_out_of_range(self):
        """Test that scores outside [0.0, 1.0] are rejected."""
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            AgentMetrics(
                mean_score=1.5,  # Invalid: > 1.0
                std_dev=0.1,
                sample_size=5,
                min_score=0.5,
                max_score=1.0,
                median_score=0.8,
                p95_score=0.95,
                raw_scores=[0.5, 0.7, 0.8, 0.9, 1.0],
            )

    def test_raw_scores_validation_invalid_scores(self):
        """Test that raw_scores with invalid values are rejected."""
        with pytest.raises(ValidationError, match="outside valid range"):
            AgentMetrics(
                mean_score=0.85,
                std_dev=0.1,
                sample_size=5,
                min_score=0.5,
                max_score=1.0,
                median_score=0.8,
                p95_score=0.95,
                raw_scores=[0.5, 0.7, 1.5, 0.9, 1.0],  # 1.5 is invalid
            )

    def test_std_dev_validation_exceeds_limit(self):
        """Test that std_dev > 1.0 is rejected."""
        with pytest.raises(ValidationError, match="cannot exceed 1.0"):
            AgentMetrics(
                mean_score=0.5,
                std_dev=1.2,  # Invalid: > 1.0
                sample_size=5,
                min_score=0.0,
                max_score=1.0,
                median_score=0.5,
                p95_score=0.9,
                raw_scores=[0.1, 0.3, 0.5, 0.7, 0.9],
            )

    def test_coefficient_of_variation(self):
        """Test coefficient of variation calculation."""
        metrics = AgentMetrics(
            mean_score=0.8,
            std_dev=0.16,
            sample_size=10,
            min_score=0.5,
            max_score=1.0,
            median_score=0.8,
            p95_score=0.95,
            raw_scores=[0.5, 0.6, 0.7, 0.75, 0.8, 0.82, 0.85, 0.9, 0.95, 1.0],
        )

        cv = metrics.coefficient_of_variation()
        assert cv == pytest.approx(0.2, rel=1e-2)  # 0.16 / 0.8 = 0.2

    def test_coefficient_of_variation_zero_mean(self):
        """Test CV with zero mean score."""
        metrics = AgentMetrics(
            mean_score=0.0,
            std_dev=0.0,
            sample_size=5,
            min_score=0.0,
            max_score=0.0,
            median_score=0.0,
            p95_score=0.0,
            raw_scores=[0.0, 0.0, 0.0, 0.0, 0.0],
        )

        cv = metrics.coefficient_of_variation()
        assert cv == 0.0

    def test_standard_error(self):
        """Test standard error calculation."""
        metrics = AgentMetrics(
            mean_score=0.8,
            std_dev=0.3,
            sample_size=9,  # sqrt(9) = 3
            min_score=0.5,
            max_score=1.0,
            median_score=0.8,
            p95_score=0.95,
            raw_scores=[0.5, 0.6, 0.7, 0.75, 0.8, 0.82, 0.85, 0.9, 1.0],
        )

        se = metrics.standard_error()
        assert se == pytest.approx(0.1, rel=1e-2)  # 0.3 / 3 = 0.1


class TestComparisonResult:
    """Test ComparisonResult model validation and methods."""

    def test_valid_comparison_result(self):
        """Test creation of valid ComparisonResult instance."""
        comparison = ComparisonResult(
            test_type=StatisticalTestType.T_TEST,
            p_value=0.03,
            confidence_level=0.95,
            challenger_ci_lower=0.75,
            challenger_ci_upper=0.95,
            incumbent_ci_lower=0.60,
            incumbent_ci_upper=0.80,
            effect_size=0.65,
            is_significant=True,
            degrees_of_freedom=18,
            test_statistic=2.45,
        )

        assert comparison.test_type == StatisticalTestType.T_TEST
        assert comparison.p_value == 0.03
        assert comparison.is_significant is True

    def test_p_value_validation_out_of_range(self):
        """Test that p_value outside [0.0, 1.0] is rejected."""
        with pytest.raises(ValidationError, match="less than or equal to 1"):
            ComparisonResult(
                test_type=StatisticalTestType.T_TEST,
                p_value=1.5,  # Invalid: > 1.0
                challenger_ci_lower=0.75,
                challenger_ci_upper=0.95,
                incumbent_ci_lower=0.60,
                incumbent_ci_upper=0.80,
                effect_size=0.5,
                is_significant=True,
            )

    def test_ci_overlap_detection_overlapping(self):
        """Test CI overlap detection with overlapping intervals."""
        comparison = ComparisonResult(
            test_type=StatisticalTestType.T_TEST,
            p_value=0.15,
            challenger_ci_lower=0.70,
            challenger_ci_upper=0.90,
            incumbent_ci_lower=0.65,
            incumbent_ci_upper=0.85,  # Overlaps with challenger
            effect_size=0.2,
            is_significant=False,
        )

        assert comparison.is_ci_overlap() is True

    def test_ci_overlap_detection_non_overlapping(self):
        """Test CI overlap detection with non-overlapping intervals."""
        comparison = ComparisonResult(
            test_type=StatisticalTestType.T_TEST,
            p_value=0.01,
            challenger_ci_lower=0.85,
            challenger_ci_upper=0.95,
            incumbent_ci_lower=0.60,
            incumbent_ci_upper=0.75,  # Does not overlap
            effect_size=0.8,
            is_significant=True,
        )

        assert comparison.is_ci_overlap() is False


class TestEvidenceMetadata:
    """Test EvidenceMetadata model validation."""

    def test_valid_evidence_metadata(self):
        """Test creation of valid EvidenceMetadata instance."""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)

        evidence = EvidenceMetadata(
            task_ids=["task_1", "task_2", "task_3"],
            total_trials=30,
            duration_seconds=7200.0,
            total_cost_usd=1.25,
            results_file="benchmark_results/results_20250108.jsonl",
            timestamp_start=start_time,
            timestamp_end=end_time,
            data_quality_score=0.98,
            outliers_detected=2,
        )

        assert len(evidence.task_ids) == 3
        assert evidence.total_trials == 30
        assert evidence.data_quality_score == 0.98

    def test_timestamp_validation_end_before_start(self):
        """Test that end timestamp before start timestamp is rejected."""
        start_time = datetime.utcnow()
        end_time = start_time - timedelta(hours=1)  # Invalid: before start

        with pytest.raises(ValidationError, match="must be after"):
            EvidenceMetadata(
                task_ids=["task_1"],
                total_trials=10,
                duration_seconds=3600.0,
                total_cost_usd=0.5,
                timestamp_start=start_time,
                timestamp_end=end_time,  # Invalid
            )


class TestProposalReport:
    """Test ProposalReport model validation and decision logic."""

    @pytest.fixture
    def sample_challenger_metrics(self):
        """Sample challenger metrics (high performance)."""
        return AgentMetrics(
            mean_score=0.88,
            std_dev=0.08,
            sample_size=10,
            min_score=0.75,
            max_score=0.98,
            median_score=0.90,
            p95_score=0.96,
            raw_scores=[0.75, 0.80, 0.82, 0.85, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98],
        )

    @pytest.fixture
    def sample_incumbent_metrics(self):
        """Sample incumbent metrics (baseline performance)."""
        return AgentMetrics(
            mean_score=0.75,
            std_dev=0.10,
            sample_size=10,
            min_score=0.60,
            max_score=0.85,
            median_score=0.76,
            p95_score=0.83,
            raw_scores=[0.60, 0.65, 0.70, 0.72, 0.75, 0.76, 0.78, 0.80, 0.82, 0.85],
        )

    @pytest.fixture
    def sample_comparison(self):
        """Sample statistical comparison (significant improvement)."""
        return ComparisonResult(
            test_type=StatisticalTestType.T_TEST,
            p_value=0.012,
            confidence_level=0.95,
            challenger_ci_lower=0.82,
            challenger_ci_upper=0.94,
            incumbent_ci_lower=0.68,
            incumbent_ci_upper=0.82,
            effect_size=1.35,
            is_significant=True,
            degrees_of_freedom=18,
            test_statistic=3.25,
        )

    @pytest.fixture
    def sample_evidence(self):
        """Sample evidence metadata."""
        start_time = datetime.utcnow() - timedelta(hours=2)
        end_time = datetime.utcnow()

        return EvidenceMetadata(
            task_ids=["planner_jwt_auth", "planner_rate_limiting"],
            total_trials=20,
            duration_seconds=7200.0,
            total_cost_usd=2.50,
            results_file="benchmark_results/results_20250108.jsonl",
            timestamp_start=start_time,
            timestamp_end=end_time,
            data_quality_score=1.0,
            outliers_detected=0,
        )

    def test_valid_proposal_report_promote(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test creation of valid ProposalReport with PROMOTE recommendation."""
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.98,
            improvement_pct=17.3,  # (0.88 - 0.75) / 0.75 * 100
            p_value=0.012,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=5.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        assert report.recommendation == RecommendationType.PROMOTE
        assert report.confidence == 0.98
        assert report.improvement_pct == 17.3
        assert report.is_auto_promotable() is True

    def test_proposal_report_reject_regression(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test ProposalReport with REJECT recommendation (regression detected)."""
        # Modify challenger to perform worse
        poor_challenger = AgentMetrics(
            mean_score=0.65,  # Worse than incumbent (0.75)
            std_dev=0.12,
            sample_size=10,
            min_score=0.50,
            max_score=0.75,
            median_score=0.66,
            p95_score=0.73,
            raw_scores=[0.50, 0.55, 0.60, 0.62, 0.65, 0.66, 0.68, 0.70, 0.72, 0.75],
        )

        report = ProposalReport(
            winner_id="agent_v1_baseline",  # Incumbent wins
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.92,
            improvement_pct=-13.3,  # Negative = regression
            p_value=0.02,
            recommendation=RecommendationType.REJECT,
            challenger_metrics=poor_challenger,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=10.0,
            cost_per_trial_challenger=0.14,
            cost_per_trial_incumbent=0.12,
        )

        assert report.recommendation == RecommendationType.REJECT
        assert report.improvement_pct < 0
        assert report.is_auto_rejectable() is True

    def test_proposal_report_human_review_marginal(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test ProposalReport with HUMAN_REVIEW (marginal improvement)."""
        # Modify challenger to have marginal improvement
        marginal_challenger = AgentMetrics(
            mean_score=0.78,  # Slight improvement over 0.75
            std_dev=0.09,
            sample_size=10,
            min_score=0.65,
            max_score=0.88,
            median_score=0.79,
            p95_score=0.86,
            raw_scores=[0.65, 0.70, 0.73, 0.75, 0.78, 0.79, 0.81, 0.83, 0.85, 0.88],
        )

        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.75,
            improvement_pct=4.0,  # Marginal: < 5%
            p_value=0.08,  # Not significant: > 0.05
            recommendation=RecommendationType.HUMAN_REVIEW,
            challenger_metrics=marginal_challenger,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=8.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        assert report.recommendation == RecommendationType.HUMAN_REVIEW
        assert report.requires_human_review() is True
        assert report.is_auto_promotable() is False

    def test_winner_validation_invalid_winner(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test that winner_id must be either challenger or incumbent."""
        with pytest.raises(ValidationError, match="must be either challenger_id"):
            ProposalReport(
                winner_id="agent_v3_unknown",  # Invalid: not challenger or incumbent
                challenger_id="agent_v2_challenger",
                incumbent_id="agent_v1_baseline",
                confidence=0.95,
                improvement_pct=10.0,
                p_value=0.03,
                recommendation=RecommendationType.PROMOTE,
                challenger_metrics=sample_challenger_metrics,
                incumbent_metrics=sample_incumbent_metrics,
                comparison=sample_comparison,
                evidence=sample_evidence,
                cost_increase_pct=5.0,
                cost_per_trial_challenger=0.13,
                cost_per_trial_incumbent=0.12,
            )

    def test_auto_promotable_criteria(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test auto-promotion criteria enforcement."""
        # Valid PROMOTE case
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.97,
            improvement_pct=15.0,
            p_value=0.01,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=10.0,  # Within 20% threshold
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        assert report.is_auto_promotable() is True

        # Fail due to high cost increase
        report.cost_increase_pct = 25.0  # Exceeds 20% threshold
        assert report.is_auto_promotable() is False

    def test_get_promotion_summary(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test promotion summary generation."""
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.96,
            improvement_pct=12.5,
            p_value=0.02,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=8.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        summary = report.get_promotion_summary()

        assert summary["decision"] == "PROMOTE"
        assert summary["winner"] == "agent_v2_challenger"
        assert summary["improvement"] == "+12.5%"
        assert summary["confidence"] == "96.0%"
        assert summary["auto_promotable"] is True
        assert summary["requires_review"] is False

    def test_to_audit_log(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test audit log generation."""
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.96,
            improvement_pct=12.5,
            p_value=0.02,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=8.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
            notes="High confidence promotion with cost trade-off",
        )

        audit_log = report.to_audit_log()

        # Validate audit log structure
        assert "report_id" in audit_log
        assert audit_log["decision"] == "PROMOTE"
        assert audit_log["statistics"]["confidence"] == 0.96
        assert audit_log["statistics"]["improvement_pct"] == 12.5
        assert audit_log["challenger_metrics"]["mean"] == 0.88
        assert audit_log["incumbent_metrics"]["mean"] == 0.75
        assert audit_log["costs"]["increase_pct"] == 8.0
        assert audit_log["auto_actions"]["promotable"] is True
        assert audit_log["notes"] == "High confidence promotion with cost trade-off"

        # Validate JSON serialization
        json_str = json.dumps(audit_log, default=str)
        assert len(json_str) > 0

    def test_risk_factors_trigger_human_review(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test that risk factors force human review."""
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.96,
            improvement_pct=12.5,
            p_value=0.02,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=8.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
            risk_factors=["high_variance", "small_sample"],
        )

        # Risk factors present -> requires human review
        assert report.requires_human_review() is True

    def test_marginal_improvement_triggers_human_review(
        self,
        sample_challenger_metrics,
        sample_incumbent_metrics,
        sample_comparison,
        sample_evidence,
    ):
        """Test that marginal improvements (0-5%) trigger human review."""
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.90,
            improvement_pct=3.5,  # Marginal: 0-5%
            p_value=0.04,
            recommendation=RecommendationType.PROMOTE,
            challenger_metrics=sample_challenger_metrics,
            incumbent_metrics=sample_incumbent_metrics,
            comparison=sample_comparison,
            evidence=sample_evidence,
            cost_increase_pct=5.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        # Marginal improvement -> requires human review
        assert report.requires_human_review() is True


class TestRecommendationValidation:
    """Test recommendation validation logic."""

    @pytest.fixture
    def base_metrics_and_evidence(self):
        """Shared metrics and evidence for recommendation tests."""
        challenger = AgentMetrics(
            mean_score=0.88,
            std_dev=0.08,
            sample_size=10,
            min_score=0.75,
            max_score=0.98,
            median_score=0.90,
            p95_score=0.96,
            raw_scores=[0.75, 0.80, 0.82, 0.85, 0.88, 0.90, 0.92, 0.94, 0.96, 0.98],
        )

        incumbent = AgentMetrics(
            mean_score=0.75,
            std_dev=0.10,
            sample_size=10,
            min_score=0.60,
            max_score=0.85,
            median_score=0.76,
            p95_score=0.83,
            raw_scores=[0.60, 0.65, 0.70, 0.72, 0.75, 0.76, 0.78, 0.80, 0.82, 0.85],
        )

        comparison = ComparisonResult(
            test_type=StatisticalTestType.T_TEST,
            p_value=0.012,
            challenger_ci_lower=0.82,
            challenger_ci_upper=0.94,
            incumbent_ci_lower=0.68,
            incumbent_ci_upper=0.82,
            effect_size=1.35,
            is_significant=True,
        )

        start_time = datetime.utcnow() - timedelta(hours=2)
        evidence = EvidenceMetadata(
            task_ids=["task_1", "task_2"],
            total_trials=20,
            duration_seconds=7200.0,
            total_cost_usd=2.50,
            timestamp_start=start_time,
            timestamp_end=datetime.utcnow(),
        )

        return challenger, incumbent, comparison, evidence

    def test_recommendation_validation_warning_promote_weak_criteria(
        self, base_metrics_and_evidence, capsys
    ):
        """Test that PROMOTE with weak criteria logs warning."""
        challenger, incumbent, comparison, evidence = base_metrics_and_evidence

        # Create PROMOTE recommendation with weak criteria
        report = ProposalReport(
            winner_id="agent_v2_challenger",
            challenger_id="agent_v2_challenger",
            incumbent_id="agent_v1_baseline",
            confidence=0.85,  # Below 0.95 threshold
            improvement_pct=3.0,  # Below 5% threshold
            p_value=0.08,  # Above 0.05 threshold
            recommendation=RecommendationType.PROMOTE,  # Should trigger warning
            challenger_metrics=challenger,
            incumbent_metrics=incumbent,
            comparison=comparison,
            evidence=evidence,
            cost_increase_pct=5.0,
            cost_per_trial_challenger=0.13,
            cost_per_trial_incumbent=0.12,
        )

        # Check warning was printed
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "PROMOTE recommendation does not meet standard criteria" in captured.out

        # Report still created (soft validation)
        assert report.recommendation == RecommendationType.PROMOTE
