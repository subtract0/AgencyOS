"""
Comprehensive tests for QualitySignalCollector.

TDD-first implementation following Constitutional Law #1.
Tests written BEFORE implementation to ensure complete coverage.

Test Coverage:
- QualitySignals Pydantic model validation
- Severity computation logic (all thresholds)
- QualitySignalCollector signal collection methods
- Error handling and graceful degradation
- Integration scenarios

Constitutional Compliance:
- Article I: Complete context (all signals collected)
- Article II: 100% test coverage, strict typing
- Article IV: VectorStore pattern extraction
- Article V: Follows spec-004-quality-feedback-loop.md
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
from typing import Optional

import pytest

# Import modules AFTER they're created (tests first, then implementation)
# These imports will fail initially - that's correct for TDD!
try:
    from shared.models.quality_signals import (
        QualitySignals,
        SeverityLevel,
        UserFeedback
    )
    from tools.quality_feedback.signal_collector import (
        QualitySignalCollector,
        SignalCollectionError
    )
except ImportError:
    # Expected on first test run - mark as xfail
    pytest.skip("Models not yet implemented (TDD RED phase)", allow_module_level=True)


# ============================================================================
# Test Suite 1: QualitySignals Pydantic Model
# ============================================================================

class TestQualitySignalsPydanticModel:
    """Test Pydantic model validation and severity computation."""

    def test_valid_quality_signals_all_fields_populated(self):
        """Test valid QualitySignals with all fields."""
        # Arrange
        signals = QualitySignals(
            task_id="task_123",
            original_tier="simple",
            test_failure_rate=0.15,
            code_churn_lines=120,
            execution_time_ratio=4.2,
            user_feedback=UserFeedback.MISCLASSIFIED
        )

        # Assert
        assert signals.task_id == "task_123"
        assert signals.original_tier == "simple"
        assert signals.test_failure_rate == 0.15
        assert signals.code_churn_lines == 120
        assert signals.execution_time_ratio == 4.2
        assert signals.user_feedback == UserFeedback.MISCLASSIFIED
        assert signals.severity == SeverityLevel.CRITICAL
        assert signals.detected_at is not None

    def test_valid_quality_signals_minimal_fields(self):
        """Test QualitySignals with only required fields."""
        # Arrange
        signals = QualitySignals(
            task_id="task_456",
            original_tier="moderate"
        )

        # Assert
        assert signals.task_id == "task_456"
        assert signals.original_tier == "moderate"
        assert signals.test_failure_rate is None
        assert signals.code_churn_lines is None
        assert signals.execution_time_ratio is None
        assert signals.user_feedback is None
        assert signals.severity == SeverityLevel.INFO  # Default when no signals

    def test_invalid_test_failure_rate_below_zero(self):
        """Test validation rejects test_failure_rate < 0.0."""
        # Act & Assert
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            QualitySignals(
                task_id="task_789",
                original_tier="simple",
                test_failure_rate=-0.5
            )

    def test_invalid_test_failure_rate_above_one(self):
        """Test validation rejects test_failure_rate > 1.0."""
        # Act & Assert
        with pytest.raises(ValueError, match="less than or equal to 1"):
            QualitySignals(
                task_id="task_789",
                original_tier="simple",
                test_failure_rate=1.5
            )

    def test_invalid_code_churn_negative(self):
        """Test validation rejects negative code_churn_lines."""
        # Act & Assert
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            QualitySignals(
                task_id="task_789",
                original_tier="simple",
                code_churn_lines=-10
            )

    def test_invalid_execution_time_ratio_negative(self):
        """Test validation rejects negative execution_time_ratio."""
        # Act & Assert
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            QualitySignals(
                task_id="task_789",
                original_tier="simple",
                execution_time_ratio=-1.5
            )

    def test_invalid_original_tier(self):
        """Test validation rejects invalid tier values."""
        # Act & Assert
        with pytest.raises(ValueError, match="String should match pattern"):
            QualitySignals(
                task_id="task_789",
                original_tier="invalid_tier"
            )


# ============================================================================
# Test Suite 2: Severity Computation Logic
# ============================================================================

class TestSeverityComputation:
    """Test severity level computation from quality signals."""

    def test_severity_critical_from_user_feedback_misclassified(self):
        """Test CRITICAL severity from user_feedback=misclassified."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_001",
            original_tier="simple",
            user_feedback=UserFeedback.MISCLASSIFIED
        )

        # Assert
        assert signals.severity == SeverityLevel.CRITICAL

    def test_severity_critical_from_test_failure_rate_above_threshold(self):
        """Test CRITICAL severity from test_failure_rate > 0.1."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_002",
            original_tier="simple",
            test_failure_rate=0.3  # 30% failures
        )

        # Assert
        assert signals.severity == SeverityLevel.CRITICAL

    def test_severity_critical_from_code_churn_above_100(self):
        """Test CRITICAL severity from code_churn_lines > 100."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_003",
            original_tier="moderate",
            code_churn_lines=168  # 168 lines changed
        )

        # Assert
        assert signals.severity == SeverityLevel.CRITICAL

    def test_severity_warning_from_code_churn_above_50(self):
        """Test WARNING severity from code_churn_lines > 50 but <= 100."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_004",
            original_tier="simple",
            code_churn_lines=75  # Between 50 and 100
        )

        # Assert
        assert signals.severity == SeverityLevel.WARNING

    def test_severity_warning_from_execution_time_ratio_above_3(self):
        """Test WARNING severity from execution_time_ratio > 3.0."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_005",
            original_tier="moderate",
            execution_time_ratio=4.5  # Took 4.5x longer
        )

        # Assert
        assert signals.severity == SeverityLevel.WARNING

    def test_severity_info_when_all_signals_none(self):
        """Test INFO severity when all signals are None."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_006",
            original_tier="complex"
        )

        # Assert
        assert signals.severity == SeverityLevel.INFO

    def test_severity_info_when_all_signals_below_thresholds(self):
        """Test INFO severity when all signals below thresholds."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_007",
            original_tier="simple",
            test_failure_rate=0.05,  # 5% failures (below 10%)
            code_churn_lines=30,  # Below 50
            execution_time_ratio=1.2,  # Below 3.0
            user_feedback=UserFeedback.CORRECT
        )

        # Assert
        assert signals.severity == SeverityLevel.INFO

    def test_severity_priority_user_feedback_overrides_all(self):
        """Test user_feedback has highest priority over all other signals."""
        # Arrange & Act
        signals = QualitySignals(
            task_id="task_008",
            original_tier="simple",
            test_failure_rate=0.0,  # No failures
            code_churn_lines=10,  # Low churn
            execution_time_ratio=1.0,  # Perfect timing
            user_feedback=UserFeedback.MISCLASSIFIED  # User says it's wrong
        )

        # Assert - user feedback overrides all other positive signals
        assert signals.severity == SeverityLevel.CRITICAL


# ============================================================================
# Test Suite 3: QualitySignalCollector - Test Failure Collection
# ============================================================================

class TestCollectTestFailures:
    """Test pytest JSON report parsing for test failure rate."""

    @pytest.fixture
    def mock_pytest_report(self):
        """Fixture providing sample pytest JSON report."""
        return {
            "summary": {
                "total": 10,
                "passed": 7,
                "failed": 3
            }
        }

    def test_collect_test_failure_rate_from_valid_report(self, tmp_path, mock_pytest_report):
        """Test collecting test_failure_rate from valid pytest JSON report."""
        # Arrange
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps(mock_pytest_report))

        collector = QualitySignalCollector(
            pytest_report_path=str(report_path)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_test_001",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.test_failure_rate == 0.3  # 3 failed / 10 total

    def test_collect_test_failure_rate_zero_failures(self, tmp_path):
        """Test test_failure_rate=0.0 when all tests pass."""
        # Arrange
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({
            "summary": {"total": 15, "passed": 15, "failed": 0}
        }))

        collector = QualitySignalCollector(
            pytest_report_path=str(report_path)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_test_002",
            original_tier="moderate"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.test_failure_rate == 0.0

    def test_collect_test_failure_rate_report_missing(self, tmp_path):
        """Test test_failure_rate=None when pytest report missing."""
        # Arrange
        report_path = tmp_path / "nonexistent.json"

        collector = QualitySignalCollector(
            pytest_report_path=str(report_path)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_test_003",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.test_failure_rate is None  # Graceful degradation

    def test_collect_test_failure_rate_malformed_json(self, tmp_path):
        """Test test_failure_rate=None when JSON is malformed."""
        # Arrange
        report_path = tmp_path / "malformed.json"
        report_path.write_text("{ invalid json }")

        collector = QualitySignalCollector(
            pytest_report_path=str(report_path)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_test_004",
            original_tier="simple"
        )

        # Assert - should not crash, return None for test_failure_rate
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.test_failure_rate is None


# ============================================================================
# Test Suite 4: QualitySignalCollector - Code Churn Collection
# ============================================================================

class TestCollectCodeChurn:
    """Test git diff parsing for code churn measurement."""

    @patch('subprocess.run')
    def test_collect_code_churn_from_git_diff(self, mock_run):
        """Test collecting code_churn_lines from git diff --stat."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0,
            stdout="5 files changed, 145 insertions(+), 23 deletions(-)\n"
        )

        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_churn_001",
            original_tier="moderate"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.code_churn_lines == 168  # 145 + 23

    @patch('subprocess.run')
    def test_collect_code_churn_insertions_only(self, mock_run):
        """Test code churn with only insertions (no deletions)."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0,
            stdout="3 files changed, 50 insertions(+)\n"
        )

        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_churn_002",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.code_churn_lines == 50

    @patch('subprocess.run')
    def test_collect_code_churn_deletions_only(self, mock_run):
        """Test code churn with only deletions (no insertions)."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0,
            stdout="2 files changed, 30 deletions(-)\n"
        )

        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_churn_003",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.code_churn_lines == 30

    @patch('subprocess.run')
    def test_collect_code_churn_git_command_failure(self, mock_run):
        """Test code_churn_lines=None when git command fails."""
        # Arrange
        mock_run.return_value = Mock(returncode=1)

        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_churn_004",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.code_churn_lines is None  # Graceful degradation

    @patch('subprocess.run')
    def test_collect_code_churn_git_timeout(self, mock_run):
        """Test code_churn_lines=None when git command times out."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)

        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_churn_005",
            original_tier="simple"
        )

        # Assert - should not crash
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.code_churn_lines is None


# ============================================================================
# Test Suite 5: QualitySignalCollector - Execution Timing
# ============================================================================

class TestCollectExecutionTiming:
    """Test execution time ratio calculation."""

    def test_execution_time_ratio_perfect_estimate(self):
        """Test execution_time_ratio=1.0 when actual matches estimated."""
        # Arrange
        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_timing_001",
            original_tier="simple",
            estimated_time_seconds=200.0,
            actual_time_seconds=200.0
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.execution_time_ratio == 1.0

    def test_execution_time_ratio_underestimated(self):
        """Test execution_time_ratio > 1.0 when task took longer."""
        # Arrange
        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_timing_002",
            original_tier="simple",
            estimated_time_seconds=200.0,
            actual_time_seconds=600.0  # Took 3x longer
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.execution_time_ratio == 3.0

    def test_execution_time_ratio_overestimated(self):
        """Test execution_time_ratio < 1.0 when task finished early."""
        # Arrange
        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_timing_003",
            original_tier="moderate",
            estimated_time_seconds=400.0,
            actual_time_seconds=200.0  # Finished in half the time
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.execution_time_ratio == 0.5

    def test_execution_time_ratio_missing_estimate(self):
        """Test execution_time_ratio=None when estimated_time not provided."""
        # Arrange
        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_timing_004",
            original_tier="simple",
            actual_time_seconds=300.0
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.execution_time_ratio is None

    def test_execution_time_ratio_missing_actual(self):
        """Test execution_time_ratio=None when actual_time not provided."""
        # Arrange
        collector = QualitySignalCollector()

        # Act
        result = collector.collect_signals(
            task_id="task_timing_005",
            original_tier="simple",
            estimated_time_seconds=200.0
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.execution_time_ratio is None


# ============================================================================
# Test Suite 6: QualitySignalCollector - User Feedback
# ============================================================================

class TestCollectUserFeedback:
    """Test user feedback collection from file store."""

    def test_collect_user_feedback_misclassified(self, tmp_path):
        """Test collecting user_feedback=misclassified from file."""
        # Arrange
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()
        feedback_file = feedback_dir / "task_feedback_001.json"
        feedback_file.write_text(json.dumps({"feedback": "misclassified"}))

        collector = QualitySignalCollector(
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_feedback_001",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.user_feedback == UserFeedback.MISCLASSIFIED

    def test_collect_user_feedback_correct(self, tmp_path):
        """Test collecting user_feedback=correct from file."""
        # Arrange
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()
        feedback_file = feedback_dir / "task_feedback_002.json"
        feedback_file.write_text(json.dumps({"feedback": "correct"}))

        collector = QualitySignalCollector(
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_feedback_002",
            original_tier="moderate"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.user_feedback == UserFeedback.CORRECT

    def test_collect_user_feedback_unsure(self, tmp_path):
        """Test collecting user_feedback=unsure from file."""
        # Arrange
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()
        feedback_file = feedback_dir / "task_feedback_003.json"
        feedback_file.write_text(json.dumps({"feedback": "unsure"}))

        collector = QualitySignalCollector(
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_feedback_003",
            original_tier="complex"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.user_feedback == UserFeedback.UNSURE

    def test_collect_user_feedback_missing_file(self, tmp_path):
        """Test user_feedback=None when feedback file missing."""
        # Arrange
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()

        collector = QualitySignalCollector(
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_feedback_999",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.user_feedback is None

    def test_collect_user_feedback_invalid_json(self, tmp_path):
        """Test user_feedback=None when JSON is invalid."""
        # Arrange
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()
        feedback_file = feedback_dir / "task_feedback_004.json"
        feedback_file.write_text("{ invalid json }")

        collector = QualitySignalCollector(
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_feedback_004",
            original_tier="simple"
        )

        # Assert - should not crash
        assert result.is_ok()
        signals = result.unwrap()
        assert signals.user_feedback is None


# ============================================================================
# Test Suite 7: Full Integration Tests
# ============================================================================

class TestQualitySignalCollectorIntegration:
    """End-to-end integration tests with all signals."""

    @patch('subprocess.run')
    def test_full_integration_all_signals_collected(self, mock_run, tmp_path):
        """Test full collection with all four signals present."""
        # Arrange - pytest report
        report_path = tmp_path / "report.json"
        report_path.write_text(json.dumps({
            "summary": {"total": 10, "failed": 3}
        }))

        # Arrange - git diff
        mock_run.return_value = Mock(
            returncode=0,
            stdout="5 files changed, 145 insertions(+), 23 deletions(-)\n"
        )

        # Arrange - user feedback
        feedback_dir = tmp_path / "feedback"
        feedback_dir.mkdir()
        feedback_file = feedback_dir / "task_integration_001.json"
        feedback_file.write_text(json.dumps({"feedback": "misclassified"}))

        collector = QualitySignalCollector(
            pytest_report_path=str(report_path),
            user_feedback_dir=str(feedback_dir)
        )

        # Act
        result = collector.collect_signals(
            task_id="task_integration_001",
            original_tier="simple",
            estimated_time_seconds=200.0,
            actual_time_seconds=600.0
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()

        # All signals collected
        assert signals.test_failure_rate == 0.3
        assert signals.code_churn_lines == 168
        assert signals.execution_time_ratio == 3.0
        assert signals.user_feedback == UserFeedback.MISCLASSIFIED

        # Severity is CRITICAL (user feedback overrides all)
        assert signals.severity == SeverityLevel.CRITICAL

    @patch('subprocess.run')
    def test_full_integration_partial_signals_graceful(self, mock_run, tmp_path):
        """Test graceful handling when some signals unavailable."""
        # Arrange - only git diff succeeds, others fail
        mock_run.return_value = Mock(
            returncode=0,
            stdout="3 files changed, 85 insertions(+)\n"
        )

        collector = QualitySignalCollector(
            pytest_report_path="/nonexistent/report.json",
            user_feedback_dir="/nonexistent/feedback"
        )

        # Act
        result = collector.collect_signals(
            task_id="task_integration_002",
            original_tier="moderate"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()

        # Available signals
        assert signals.code_churn_lines == 85

        # Unavailable signals are None
        assert signals.test_failure_rate is None
        assert signals.execution_time_ratio is None
        assert signals.user_feedback is None

        # Severity based on available signals
        assert signals.severity == SeverityLevel.WARNING  # churn > 50

    @patch('subprocess.run')
    def test_full_integration_all_signals_missing(self, mock_run):
        """Test handling when all signals unavailable."""
        # Arrange - all collection methods fail
        mock_run.return_value = Mock(returncode=1)

        collector = QualitySignalCollector(
            pytest_report_path="/nonexistent/report.json",
            user_feedback_dir="/nonexistent/feedback"
        )

        # Act
        result = collector.collect_signals(
            task_id="task_integration_003",
            original_tier="simple"
        )

        # Assert
        assert result.is_ok()
        signals = result.unwrap()

        # All signals None
        assert signals.test_failure_rate is None
        assert signals.code_churn_lines is None
        assert signals.execution_time_ratio is None
        assert signals.user_feedback is None

        # Default severity
        assert signals.severity == SeverityLevel.INFO


# ============================================================================
# Test Suite 8: Constitutional Compliance
# ============================================================================

class TestConstitutionalCompliance:
    """Test constitutional compliance requirements."""

    def test_article_i_complete_context_all_signals_attempted(self):
        """Article I: All four signal types attempted before severity computation."""
        # This is tested by integration tests verifying all collection methods called
        pass  # Covered by test_full_integration_all_signals_collected

    def test_article_ii_strict_typing_no_dict_any_any(self):
        """Article II: QualitySignals uses strict typing (no Dict[Any, Any])."""
        from shared.models.quality_signals import QualitySignals
        import inspect

        # Get type annotations
        annotations = QualitySignals.__annotations__

        # Verify no 'Any' in type definitions
        for field_name, field_type in annotations.items():
            assert "Any" not in str(field_type), \
                f"Field '{field_name}' uses Any type (violation)"

    def test_article_ii_result_pattern_used(self):
        """Article II: QualitySignalCollector returns Result<T, E>."""
        from tools.quality_feedback.signal_collector import QualitySignalCollector
        from shared.type_definitions.result import Result
        import inspect

        # Verify collect_signals returns Result
        sig = inspect.signature(QualitySignalCollector.collect_signals)
        return_annotation = sig.return_annotation

        # Should be Result type
        assert "Result" in str(return_annotation)

    def test_article_v_follows_specification(self):
        """Article V: Implementation follows spec-004-quality-feedback-loop.md."""
        # Verify enum values match spec
        assert SeverityLevel.CRITICAL.value == "critical"
        assert SeverityLevel.WARNING.value == "warning"
        assert SeverityLevel.INFO.value == "info"

        assert UserFeedback.CORRECT.value == "correct"
        assert UserFeedback.MISCLASSIFIED.value == "misclassified"
        assert UserFeedback.UNSURE.value == "unsure"
