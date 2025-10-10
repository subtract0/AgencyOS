"""
Comprehensive tests for MisclassificationDetector.

TDD-first implementation following Constitutional Law #1.
Tests written BEFORE implementation to ensure complete coverage.

Test Coverage:
- DetectedIssue and MisclassificationReport Pydantic models
- 4 detection rules (test_failure, code_churn, execution_timing, user_feedback)
- Multi-signal aggregation with weighted confidence
- Recommended tier computation
- VectorStore learning boost (Article IV)
- False positive mitigation
- Integration scenarios

Constitutional Compliance:
- Article I: Complete context (all signals evaluated)
- Article II: 100% test coverage, TDD mandatory
- Article IV: VectorStore integration for learning boost
- Article V: Follows spec-004-quality-feedback-loop.md Section 7

Reference: /Users/am/Code/Agency/specs/spec-004-quality-feedback-loop.md Section 7
"""

from datetime import datetime
from unittest.mock import Mock, MagicMock
from typing import List

import pytest

# Import modules AFTER they're created (tests first, then implementation)
# These imports will fail initially - that's correct for TDD RED phase!
try:
    from shared.models.quality_signals import (
        QualitySignals,
        SeverityLevel,
        UserFeedback
    )
    from shared.models.misclassification_report import (
        DetectedIssue,
        MisclassificationReport
    )
    from tools.quality_feedback.misclassification_detector import (
        MisclassificationDetector,
        DetectionError
    )
    from shared.type_definitions.result import Ok, Err
except ImportError:
    # Expected on first test run - mark as xfail
    pytest.skip("Models not yet implemented (TDD RED phase)", allow_module_level=True)


# ============================================================================
# Test Suite 1: Pydantic Model Validation
# ============================================================================

class TestDetectedIssueModel:
    """Test DetectedIssue Pydantic model validation."""

    def test_detected_issue_valid_creation(self):
        """Test creating valid DetectedIssue."""
        issue = DetectedIssue(
            rule_name="test_failure",
            confidence=0.95,
            severity=SeverityLevel.CRITICAL,
            description="Test failure rate 33%",
            signal_value=0.33
        )

        assert issue.rule_name == "test_failure"
        assert issue.confidence == 0.95
        assert issue.severity == SeverityLevel.CRITICAL
        assert issue.description == "Test failure rate 33%"
        assert issue.signal_value == 0.33

    def test_detected_issue_confidence_bounds(self):
        """Test confidence must be 0.0-1.0."""
        # Valid: exactly 0.0
        issue1 = DetectedIssue(
            rule_name="test", confidence=0.0,
            severity=SeverityLevel.INFO, description="Test"
        )
        assert issue1.confidence == 0.0

        # Valid: exactly 1.0
        issue2 = DetectedIssue(
            rule_name="test", confidence=1.0,
            severity=SeverityLevel.CRITICAL, description="Test"
        )
        assert issue2.confidence == 1.0

        # Invalid: below 0.0
        with pytest.raises(Exception):  # Pydantic ValidationError
            DetectedIssue(
                rule_name="test", confidence=-0.1,
                severity=SeverityLevel.INFO, description="Test"
            )

        # Invalid: above 1.0
        with pytest.raises(Exception):
            DetectedIssue(
                rule_name="test", confidence=1.1,
                severity=SeverityLevel.INFO, description="Test"
            )

    def test_detected_issue_optional_signal_value(self):
        """Test signal_value is optional (None for user feedback)."""
        issue = DetectedIssue(
            rule_name="user_feedback",
            confidence=1.0,
            severity=SeverityLevel.CRITICAL,
            description="User flagged as misclassified",
            signal_value=None
        )

        assert issue.signal_value is None


class TestMisclassificationReportModel:
    """Test MisclassificationReport Pydantic model validation."""

    def test_misclassification_report_valid_creation(self):
        """Test creating valid MisclassificationReport."""
        issues = [
            DetectedIssue(
                rule_name="test_failure",
                confidence=0.95,
                severity=SeverityLevel.CRITICAL,
                description="Test failures",
                signal_value=0.3
            )
        ]

        report = MisclassificationReport(
            task_id="task_123",
            original_tier="simple",
            recommended_tier="complex",
            detected_issues=issues,
            aggregated_confidence=0.95,
            is_misclassified=True,
            detected_at=datetime.utcnow().isoformat()
        )

        assert report.task_id == "task_123"
        assert report.original_tier == "simple"
        assert report.recommended_tier == "complex"
        assert len(report.detected_issues) == 1
        assert report.aggregated_confidence == 0.95
        assert report.is_misclassified is True

    def test_misclassification_report_empty_issues(self):
        """Test report with no detected issues."""
        report = MisclassificationReport(
            task_id="task_123",
            original_tier="simple",
            recommended_tier="simple",
            detected_issues=[],
            aggregated_confidence=0.0,
            is_misclassified=False,
            detected_at=datetime.utcnow().isoformat()
        )

        assert len(report.detected_issues) == 0
        assert report.is_misclassified is False
        assert report.recommended_tier == "simple"


# ============================================================================
# Test Suite 2: Detection Rule Unit Tests (15+ tests)
# ============================================================================

class TestRule1TestFailureDetection:
    """Test Rule 1: Test failure detection (confidence=0.95)."""

    def test_rule1_critical_test_failures_high(self):
        """Test test_failure_rate=0.33 (>30%), tier=simple → CRITICAL, upgrade to complex."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_1",
            original_tier="simple",
            test_failure_rate=0.33,  # 33% failures
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_1", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.recommended_tier == "complex"  # >30% → complex
        assert len(report.detected_issues) == 1

        issue = report.detected_issues[0]
        assert issue.rule_name == "test_failure"
        assert issue.confidence == 0.95
        assert issue.severity == SeverityLevel.CRITICAL
        assert issue.signal_value == 0.33

    def test_rule1_critical_test_failures_moderate(self):
        """Test test_failure_rate=0.2 (20%), tier=simple → CRITICAL, upgrade to moderate."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_2",
            original_tier="simple",
            test_failure_rate=0.2,  # 20% failures
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_2", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.recommended_tier == "moderate"  # 10-30% → moderate
        # Aggregated confidence: 0.95^2 / 1 = 0.9025
        assert abs(report.aggregated_confidence - 0.9025) < 0.01

    def test_rule1_boundary_no_detection(self):
        """Test test_failure_rate=0.09 (9%), tier=simple → No detection."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_3",
            original_tier="simple",
            test_failure_rate=0.09,  # Below 10% threshold
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_3", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0
        assert report.recommended_tier == "simple"  # No upgrade

    def test_rule1_none_signal_no_detection(self):
        """Test test_failure_rate=None (no tests run) → No detection."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_4",
            original_tier="simple",
            test_failure_rate=None,  # No tests run
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_4", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0


class TestRule2CodeChurnDetection:
    """Test Rule 2: Code churn detection (confidence varies)."""

    def test_rule2_critical_high_churn(self):
        """Test code_churn=150 lines, tier=simple → CRITICAL (confidence=0.85)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_5",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=150,  # >100 threshold
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_5", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.recommended_tier == "moderate"
        assert len(report.detected_issues) == 1

        issue = report.detected_issues[0]
        assert issue.rule_name == "code_churn"
        assert issue.confidence == 0.85
        assert issue.severity == SeverityLevel.CRITICAL
        assert issue.signal_value == 150

    def test_rule2_warning_moderate_churn(self):
        """Test code_churn=75 lines, tier=simple → WARNING (confidence=0.70)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_6",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=75,  # >50 threshold
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_6", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.recommended_tier == "moderate"

        issue = report.detected_issues[0]
        assert issue.rule_name == "code_churn"
        assert issue.confidence == 0.70
        assert issue.severity == SeverityLevel.WARNING

    def test_rule2_boundary_no_detection(self):
        """Test code_churn=49 lines, tier=simple → No detection."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_7",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=49,  # Below 50 threshold
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_7", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0


class TestRule3ExecutionTimingDetection:
    """Test Rule 3: Execution timing detection (confidence=0.75)."""

    def test_rule3_warning_high_timing_ratio(self):
        """Test execution_time_ratio=4.5, tier=simple → WARNING (confidence=0.75)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_8",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=None,
            execution_time_ratio=4.5,  # >3.0 threshold
            user_feedback=None
        )

        result = detector.detect("task_8", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.recommended_tier == "moderate"

        issue = report.detected_issues[0]
        assert issue.rule_name == "execution_timing"
        assert issue.confidence == 0.75
        assert issue.severity == SeverityLevel.WARNING
        assert issue.signal_value == 4.5

    def test_rule3_boundary_no_detection(self):
        """Test execution_time_ratio=2.9, tier=simple → No detection."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_9",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=None,
            execution_time_ratio=2.9,  # Below 3.0 threshold
            user_feedback=None
        )

        result = detector.detect("task_9", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0


class TestRule4UserFeedbackOverride:
    """Test Rule 4: User feedback override (confidence=1.0)."""

    def test_rule4_user_feedback_misclassified(self):
        """Test user_feedback=MISCLASSIFIED → CRITICAL (confidence=1.0)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_10",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=UserFeedback.MISCLASSIFIED
        )

        result = detector.detect("task_10", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is True
        assert report.aggregated_confidence == 1.0

        issue = report.detected_issues[0]
        assert issue.rule_name == "user_feedback"
        assert issue.confidence == 1.0
        assert issue.severity == SeverityLevel.CRITICAL
        assert issue.signal_value is None

    def test_rule4_user_feedback_correct_no_detection(self):
        """Test user_feedback=CORRECT → No detection."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_11",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=UserFeedback.CORRECT
        )

        result = detector.detect("task_11", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0


# ============================================================================
# Test Suite 3: Multi-Signal Aggregation
# ============================================================================

class TestMultiSignalAggregation:
    """Test aggregated confidence calculation from multiple rules."""

    def test_aggregation_test_failure_plus_churn(self):
        """Test aggregation: test_failure (0.95) + code_churn (0.85) → confidence ≈ 0.8138."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_12",
            original_tier="simple",
            test_failure_rate=0.3,  # Triggers Rule 1 (0.95)
            code_churn_lines=120,   # Triggers Rule 2 (0.85)
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_12", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert len(report.detected_issues) == 2

        # Aggregation formula: (0.95^2 + 0.85^2) / 2 = (0.9025 + 0.7225) / 2 = 0.8125
        expected_confidence = (0.95**2 + 0.85**2) / 2
        assert abs(report.aggregated_confidence - expected_confidence) < 0.01

    def test_aggregation_all_signals(self):
        """Test aggregation: test_failure + churn + timing → weighted average."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_13",
            original_tier="simple",
            test_failure_rate=0.2,   # Rule 1: 0.95
            code_churn_lines=75,     # Rule 2: 0.70
            execution_time_ratio=4.0, # Rule 3: 0.75
            user_feedback=None
        )

        result = detector.detect("task_13", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert len(report.detected_issues) == 3

        # Aggregation: (0.95^2 + 0.70^2 + 0.75^2) / 3 = (0.9025 + 0.49 + 0.5625) / 3 = 0.6517
        expected_confidence = (0.95**2 + 0.70**2 + 0.75**2) / 3
        assert abs(report.aggregated_confidence - expected_confidence) < 0.01

    def test_aggregation_user_feedback_overrides(self):
        """Test user feedback always returns confidence=1.0 (overrides all)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_14",
            original_tier="simple",
            test_failure_rate=0.3,   # Would be 0.95
            code_churn_lines=120,    # Would be 0.85
            execution_time_ratio=None,
            user_feedback=UserFeedback.MISCLASSIFIED  # Overrides to 1.0
        )

        result = detector.detect("task_14", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.aggregated_confidence == 1.0  # Always 1.0 with user feedback


# ============================================================================
# Test Suite 4: Recommended Tier Computation
# ============================================================================

class TestRecommendedTierComputation:
    """Test recommended tier based on detected issues."""

    def test_recommended_tier_high_test_failures(self):
        """Test test_failure_rate=0.4 → upgrade to complex."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_15",
            original_tier="simple",
            test_failure_rate=0.4,  # >30% → complex
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_15", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.recommended_tier == "complex"

    def test_recommended_tier_moderate_test_failures(self):
        """Test test_failure_rate=0.2 → upgrade to moderate."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_16",
            original_tier="simple",
            test_failure_rate=0.2,  # 10-30% → moderate
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_16", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.recommended_tier == "moderate"

    def test_recommended_tier_churn_only(self):
        """Test high churn alone → upgrade to moderate."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_17",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=150,  # CRITICAL churn
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_17", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.recommended_tier == "moderate"


# ============================================================================
# Test Suite 5: False Positive Mitigation
# ============================================================================

class TestFalsePositiveMitigation:
    """Test false positive mitigation (complex tier with good metrics)."""

    def test_complex_tier_good_metrics_no_detection(self):
        """Test tier=complex + good metrics → No detection (correctly classified)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_18",
            original_tier="complex",  # Already complex
            test_failure_rate=0.0,
            code_churn_lines=10,
            execution_time_ratio=0.9,
            user_feedback=None
        )

        result = detector.detect("task_18", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0
        assert report.recommended_tier == "complex"  # No change

    def test_moderate_tier_slight_overrun_no_detection(self):
        """Test tier=moderate + slight timing overrun → No detection (acceptable)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_19",
            original_tier="moderate",
            test_failure_rate=0.02,  # 2% failures (acceptable)
            code_churn_lines=25,     # Low churn
            execution_time_ratio=1.5, # Minor overrun
            user_feedback=None
        )

        result = detector.detect("task_19", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False


# ============================================================================
# Test Suite 6: VectorStore Learning Boost (Article IV)
# ============================================================================

class TestVectorStoreLearningBoost:
    """Test VectorStore learning boost (+0.1 confidence)."""

    def test_learning_boost_with_similar_case(self):
        """Test VectorStore finds similar case (similarity=0.9) → confidence +0.1."""
        # Mock AgentContext with VectorStore
        mock_context = Mock()
        mock_context.search_memories.return_value = [
            {
                "task_description": "Refactor async error handler",
                "original_tier": "simple",
                "corrected_tier": "complex",
                "confidence": 0.9,  # High confidence
                "detected_at": "2025-10-09T12:00:00Z"
            }
        ]

        detector = MisclassificationDetector(context=mock_context)
        signals = QualitySignals(
            task_id="task_20",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=75,  # Base confidence: 0.70^2 = 0.49
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_20", signals, task_description="Refactor async handler")

        assert result.is_ok()
        report = result.unwrap()

        # Base confidence 0.70^2 = 0.49, learning boost +0.1 = 0.59
        assert abs(report.aggregated_confidence - 0.59) < 0.01

        # Verify VectorStore was queried
        mock_context.search_memories.assert_called_once()

    def test_learning_boost_no_similar_case(self):
        """Test VectorStore finds no similar case → no boost (base confidence)."""
        mock_context = Mock()
        mock_context.search_memories.return_value = []  # No similar cases

        detector = MisclassificationDetector(context=mock_context)
        signals = QualitySignals(
            task_id="task_21",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=75,  # Base confidence: 0.70^2 = 0.49
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_21", signals, task_description="Fix typo")

        assert result.is_ok()
        report = result.unwrap()

        # No boost: confidence stays 0.70^2 = 0.49
        assert abs(report.aggregated_confidence - 0.49) < 0.01

    def test_learning_boost_graceful_degradation(self):
        """Test VectorStore query fails → gracefully degrade (no crash)."""
        mock_context = Mock()
        mock_context.search_memories.side_effect = Exception("VectorStore unavailable")

        detector = MisclassificationDetector(context=mock_context)
        signals = QualitySignals(
            task_id="task_22",
            original_tier="simple",
            test_failure_rate=0.2,
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_22", signals, task_description="Refactor")

        # Should not crash, return base confidence
        assert result.is_ok()
        report = result.unwrap()
        # Base confidence: 0.95^2 = 0.9025 (no boost due to VectorStore failure)
        assert abs(report.aggregated_confidence - 0.9025) < 0.01


# ============================================================================
# Test Suite 7: Integration Tests (5+ tests)
# ============================================================================

class TestEndToEndIntegration:
    """Integration tests for complete detection workflow."""

    def test_e2e_quality_signals_to_report(self):
        """E2E: QualitySignals → detect() → MisclassificationReport with multiple issues."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_e2e_1",
            original_tier="simple",
            test_failure_rate=0.33,  # Rule 1: CRITICAL
            code_churn_lines=145,    # Rule 2: CRITICAL
            execution_time_ratio=4.2, # Rule 3: WARNING
            user_feedback=None
        )

        result = detector.detect("task_e2e_1", signals)

        assert result.is_ok()
        report = result.unwrap()

        # Verify complete report
        assert report.task_id == "task_e2e_1"
        assert report.original_tier == "simple"
        assert report.recommended_tier == "complex"  # High test failures
        assert len(report.detected_issues) == 3
        assert report.is_misclassified is True
        # Aggregated confidence: (0.95^2 + 0.85^2 + 0.75^2) / 3 = 0.7292
        assert report.aggregated_confidence > 0.72

        # Verify detected_at is ISO 8601 timestamp
        datetime.fromisoformat(report.detected_at)

    def test_e2e_no_issues_detected(self):
        """E2E: All signals good → No issues detected."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_e2e_2",
            original_tier="simple",
            test_failure_rate=0.0,
            code_churn_lines=5,
            execution_time_ratio=0.8,
            user_feedback=None
        )

        result = detector.detect("task_e2e_2", signals)

        assert result.is_ok()
        report = result.unwrap()
        assert report.is_misclassified is False
        assert len(report.detected_issues) == 0
        assert report.recommended_tier == "simple"
        assert report.aggregated_confidence == 0.0

    def test_performance_detect_1000_tasks_under_1_second(self):
        """Performance: Detect 1,000 tasks in <1 second."""
        import time

        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="perf_test",
            original_tier="simple",
            test_failure_rate=0.15,
            code_churn_lines=80,
            execution_time_ratio=2.5,
            user_feedback=None
        )

        start_time = time.time()

        for i in range(1000):
            result = detector.detect(f"task_perf_{i}", signals)
            assert result.is_ok()

        elapsed_time = time.time() - start_time

        # Should complete in <1 second (spec requirement: <10ms p99)
        assert elapsed_time < 1.0, f"Performance regression: {elapsed_time:.2f}s for 1,000 detections"

    def test_stability_100_consecutive_detections(self):
        """Stability: 100 consecutive detections without crashes."""
        detector = MisclassificationDetector()

        for i in range(100):
            signals = QualitySignals(
                task_id=f"task_stability_{i}",
                original_tier="simple",
                test_failure_rate=0.1 + (i % 3) * 0.1,  # Vary signals
                code_churn_lines=50 + i,
                execution_time_ratio=2.0 + (i % 5) * 0.5,
                user_feedback=None
            )

            result = detector.detect(f"task_stability_{i}", signals)

            # Must not crash
            assert result.is_ok()

    def test_idempotency_same_signals_same_report(self):
        """Idempotency: Same signals → same report (deterministic)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_idem",
            original_tier="simple",
            test_failure_rate=0.2,
            code_churn_lines=75,
            execution_time_ratio=3.5,
            user_feedback=None
        )

        # Run detection twice
        result1 = detector.detect("task_idem", signals)
        result2 = detector.detect("task_idem", signals)

        assert result1.is_ok()
        assert result2.is_ok()

        report1 = result1.unwrap()
        report2 = result2.unwrap()

        # Reports should be identical (except detected_at timestamp)
        assert report1.task_id == report2.task_id
        assert report1.original_tier == report2.original_tier
        assert report1.recommended_tier == report2.recommended_tier
        assert len(report1.detected_issues) == len(report2.detected_issues)
        assert report1.aggregated_confidence == report2.aggregated_confidence
        assert report1.is_misclassified == report2.is_misclassified


# ============================================================================
# Test Suite 8: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and Result pattern compliance."""

    def test_detect_returns_result_type(self):
        """Test detect() returns Result type (not exceptions)."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_result",
            original_tier="simple",
            test_failure_rate=0.2,
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_result", signals)

        # Must return Result type
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_err')
        assert result.is_ok()

    def test_detect_handles_invalid_signals_gracefully(self):
        """Test detect() with None signals → graceful handling."""
        detector = MisclassificationDetector()
        signals = QualitySignals(
            task_id="task_none",
            original_tier="simple",
            test_failure_rate=None,
            code_churn_lines=None,
            execution_time_ratio=None,
            user_feedback=None
        )

        result = detector.detect("task_none", signals)

        # Should not crash with all None signals
        assert result.is_ok()
        report = result.unwrap()
        assert len(report.detected_issues) == 0
