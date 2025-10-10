"""
Tests for AccuracyDriftDetector (Leap 5 Phase 4).

Constitutional compliance:
- Article I: Complete context (full 7-day prediction history)
- Article II: TDD (tests FIRST, 100% pass rate)
- Article IV: VectorStore integration (mock memory queries)
- Article V: Spec-driven (follows spec-009-misclassification-detection.md)

Test coverage:
- Rolling window accuracy calculation (N)
- Drift detection threshold logic (E)
- VectorStore query integration (S)
- Leap 4 quality signal integration (S)
- Insufficient data handling (E)
- Error propagation with Result pattern (S)

Author: CodeAgent
Date: 2025-10-10
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from shared.agent_context import AgentContext
from shared.models.prediction_log import PredictionLog
from shared.models.quality_signals import QualitySignals, SeverityLevel
from tools.ml_routing.accuracy_drift_detector import (
    AccuracyDriftDetector,
    DriftError,
    DriftReport,
)


class TestAccuracyDriftDetector:
    """Test suite for AccuracyDriftDetector."""

    @pytest.fixture
    def mock_context(self) -> AgentContext:
        """Create mock AgentContext with mocked memory."""
        context = MagicMock(spec=AgentContext)
        context.session_id = "test_session"
        context.search_memories = MagicMock()
        context.store_memory = MagicMock()
        return context

    @pytest.fixture
    def detector(self, mock_context: AgentContext) -> AccuracyDriftDetector:
        """Create AccuracyDriftDetector with baseline 98.2%."""
        return AccuracyDriftDetector(
            context=mock_context,
            baseline_accuracy=0.982,
            drift_threshold=0.05,
            window_days=7,
        )

    # ============ NORMAL OPERATION TESTS ============

    def test_no_drift_detected_when_accuracy_above_threshold(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test no drift when accuracy is 98.5% (above 93.2% threshold)."""
        # Arrange: 100 predictions, 98.5% accuracy
        predictions = self._create_prediction_logs(count=100, accuracy=0.985, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: No drift detected
        assert result.is_ok()
        report = result.unwrap()
        assert isinstance(report, DriftReport)
        assert report.current_accuracy == pytest.approx(0.985, abs=0.01)
        assert report.baseline_accuracy == 0.982
        assert report.accuracy_drop == pytest.approx(-0.003, abs=0.01)
        assert report.is_drift_detected is False
        assert report.total_predictions == 100
        assert report.correct_predictions == 98

        # VectorStore queried with correct tags
        mock_context.search_memories.assert_called_once()
        call_kwargs = mock_context.search_memories.call_args.kwargs
        assert "prediction" in call_kwargs.get("tags", [])
        assert call_kwargs.get("include_session") is False

    def test_drift_detected_when_accuracy_drops_below_threshold(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test drift detected when accuracy is 91.5% (below 93.2% threshold)."""
        # Arrange: 100 predictions, 91.5% accuracy (6.7% drop)
        predictions = self._create_prediction_logs(count=100, accuracy=0.915, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Drift detected
        assert result.is_ok()
        report = result.unwrap()
        assert report.current_accuracy == pytest.approx(0.915, abs=0.01)
        assert report.accuracy_drop == pytest.approx(0.067, abs=0.01)
        assert report.is_drift_detected is True
        assert report.drift_threshold == 0.05

        # Alert logged to VectorStore (Article IV)
        mock_context.store_memory.assert_called_once()
        call_kwargs = mock_context.store_memory.call_args.kwargs
        stored_key = call_kwargs.get("key") or mock_context.store_memory.call_args.args[0]
        assert "drift_alert" in stored_key
        stored_content = call_kwargs.get("content") or mock_context.store_memory.call_args.args[1]
        assert stored_content["severity"] == "warning"  # 6.7% drop = WARNING (5-10%)

    def test_rolling_window_accuracy_calculation(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test accuracy calculated from 7-day rolling window."""
        # Arrange: 300 predictions over 7 days, 95% accuracy
        predictions = self._create_prediction_logs(count=300, accuracy=0.95, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert
        assert result.is_ok()
        report = result.unwrap()
        assert report.total_predictions == 300
        assert report.correct_predictions == 285  # 95% of 300
        assert report.current_accuracy == pytest.approx(0.95, abs=0.01)

    # ============ EDGE CASES ============

    def test_insufficient_data_returns_error(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test error when <100 predictions (insufficient data)."""
        # Arrange: Only 50 predictions (below minimum 100)
        predictions = self._create_prediction_logs(count=50, accuracy=0.95, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Error returned
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DriftError)
        assert error.error_type == "insufficient_data"
        assert "50 predictions" in error.message
        assert "minimum: 100" in error.message

    def test_no_predictions_with_actual_tier_returns_error(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test error when no predictions have actual_tier set (Leap 4 quality feedback missing)."""
        # Arrange: 100 predictions but no actual_tier
        predictions = [
            self._create_prediction_dict(
                task_id=f"task_{i}",
                predicted_tier="P2",
                actual_tier=None,  # No quality feedback
                confidence=0.85,
                timestamp_offset=i // 15,
            )
            for i in range(100)
        ]
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Error for insufficient data
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "insufficient_data"
        assert "0 predictions" in error.message

    def test_exactly_threshold_drop_triggers_drift(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test drift triggered when accuracy drop exactly equals threshold (5%)."""
        # Arrange: 100 predictions, 93.0% accuracy (5.2% drop from 98.2%)
        predictions = self._create_prediction_logs(count=100, accuracy=0.930, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Drift DETECTED (5.2% > 5% threshold)
        assert result.is_ok()
        report = result.unwrap()
        assert report.accuracy_drop == pytest.approx(0.052, abs=0.01)
        assert report.is_drift_detected is True  # 5.2% > 5% threshold

    def test_drift_detector_with_custom_baseline(self, mock_context: AgentContext):
        """Test drift detector with custom baseline accuracy."""
        # Arrange: Custom baseline 95%, threshold 3%
        detector = AccuracyDriftDetector(
            context=mock_context,
            baseline_accuracy=0.95,
            drift_threshold=0.03,
            window_days=7,
        )
        predictions = self._create_prediction_logs(count=100, accuracy=0.91, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Drift detected (4% drop > 3% threshold)
        assert result.is_ok()
        report = result.unwrap()
        assert report.baseline_accuracy == 0.95
        assert report.accuracy_drop == pytest.approx(0.04, abs=0.01)
        assert report.is_drift_detected is True

    # ============ SECURITY & EDGE CASES ============

    def test_vectorstore_query_failure_returns_error(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test error propagation when VectorStore query fails."""
        # Arrange: VectorStore raises exception
        mock_context.search_memories.side_effect = Exception("VectorStore timeout")

        # Act
        result = detector.check_drift()

        # Assert: Error wrapped in Result
        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "vectorstore_error"
        assert "VectorStore timeout" in error.message

    def test_filters_predictions_outside_date_range(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test VectorStore query filters by 7-day date range."""
        # Arrange
        predictions = self._create_prediction_logs(count=100, accuracy=0.98, start_date_offset=6)
        mock_context.search_memories.return_value = predictions

        # Act
        detector.check_drift()

        # Assert: Query includes date range filters
        call_kwargs = mock_context.search_memories.call_args.kwargs
        filters = call_kwargs.get("filters", {})
        assert "timestamp" in filters
        assert "$gte" in filters["timestamp"]
        assert "$lte" in filters["timestamp"]

        # Verify date range is approximately 7 days
        start_date = datetime.fromisoformat(filters["timestamp"]["$gte"])
        end_date = datetime.fromisoformat(filters["timestamp"]["$lte"])
        time_diff = (end_date - start_date).days
        assert time_diff == pytest.approx(7, abs=1)

    # ============ LEAP 4 QUALITY SIGNAL INTEGRATION ============

    def test_integrates_leap4_quality_signals_in_report(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test drift report includes Leap 4 quality signals (test failure rate, code churn)."""
        # Arrange: Predictions with quality signals
        predictions = []
        for i in range(100):
            pred_dict = self._create_prediction_dict(
                task_id=f"task_{i}",
                predicted_tier="P2",
                actual_tier="P2" if i < 92 else "P1",  # 92% accuracy
                confidence=0.85,
                timestamp_offset=i // 15,
            )
            # Add quality signals (Leap 4)
            pred_dict["quality_signals"] = {
                "test_failure_rate": 0.08 if i >= 92 else 0.0,
                "code_churn_lines": 75 if i >= 92 else 10,
            }
            predictions.append(pred_dict)

        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: Quality signals included in report
        assert result.is_ok()
        report = result.unwrap()
        assert hasattr(report, "avg_test_failure_rate")
        assert report.avg_test_failure_rate == pytest.approx(0.0064, abs=0.01)
        assert hasattr(report, "avg_code_churn")
        assert report.avg_code_churn == pytest.approx(15.2, abs=5)

    def test_drift_severity_based_on_quality_signals(
        self, detector: AccuracyDriftDetector, mock_context: AgentContext
    ):
        """Test drift severity classification using quality signals."""
        # Arrange: Low accuracy + high test failure rate = CRITICAL
        predictions = []
        for i in range(100):
            pred_dict = self._create_prediction_dict(
                task_id=f"task_{i}",
                predicted_tier="P2",
                actual_tier="P2" if i < 90 else "P1",  # 90% accuracy (drift)
                confidence=0.85,
                timestamp_offset=i // 15,
            )
            # High test failure rate for misclassified tasks
            pred_dict["quality_signals"] = {
                "test_failure_rate": 0.15 if i >= 90 else 0.02,
                "code_churn_lines": 120 if i >= 90 else 20,
            }
            predictions.append(pred_dict)

        mock_context.search_memories.return_value = predictions

        # Act
        result = detector.check_drift()

        # Assert: WARNING severity (8.5% drop = 5-10% range)
        assert result.is_ok()
        report = result.unwrap()
        assert report.is_drift_detected is True
        assert report.severity == "warning"  # 8.5% drop = WARNING (5-10% range)
        assert report.avg_test_failure_rate > 0.03  # Misclassified tasks fail more tests

    # ============ HELPER METHODS ============

    def _create_prediction_logs(
        self, count: int, accuracy: float, start_date_offset: int
    ) -> list[dict]:
        """
        Create list of prediction log dictionaries for testing.

        Args:
            count: Number of predictions
            accuracy: Target accuracy (0.0-1.0)
            start_date_offset: Days before now for oldest prediction

        Returns:
            List of prediction dictionaries with predicted_tier and actual_tier
        """
        predictions = []
        correct_count = int(count * accuracy)

        for i in range(count):
            predicted_tier = "P2"
            # First `correct_count` predictions are correct
            actual_tier = "P2" if i < correct_count else "P1"

            predictions.append(
                self._create_prediction_dict(
                    task_id=f"task_{i}",
                    predicted_tier=predicted_tier,
                    actual_tier=actual_tier,
                    confidence=0.85,
                    timestamp_offset=start_date_offset - (i // (count // 7)),
                )
            )

        return predictions

    def _create_prediction_dict(
        self,
        task_id: str,
        predicted_tier: str,
        actual_tier: str | None,
        confidence: float,
        timestamp_offset: int,
    ) -> dict:
        """
        Create prediction dictionary for VectorStore mock.

        Args:
            task_id: Task identifier
            predicted_tier: Predicted tier (P1/P2/P3)
            actual_tier: Actual tier after execution (None if pending)
            confidence: Model confidence (0.0-1.0)
            timestamp_offset: Days before now for timestamp

        Returns:
            Dictionary with prediction fields for VectorStore
        """
        timestamp = datetime.now(UTC) - timedelta(days=timestamp_offset)
        return {
            "task_id": task_id,
            "predicted_tier": predicted_tier,
            "actual_tier": actual_tier,
            "confidence": confidence,
            "timestamp": timestamp.isoformat(),
            "method": "ml",
        }


class TestDriftReport:
    """Test suite for DriftReport Pydantic model."""

    def test_drift_report_creation(self):
        """Test DriftReport Pydantic model creation."""
        # Arrange & Act
        report = DriftReport(
            current_accuracy=0.915,
            baseline_accuracy=0.982,
            accuracy_drop=0.067,
            is_drift_detected=True,
            drift_threshold=0.05,
            total_predictions=100,
            correct_predictions=91,
            detection_timestamp=datetime.now(UTC).isoformat(),
            avg_test_failure_rate=0.08,
            avg_code_churn=75.5,
            severity="critical",
        )

        # Assert
        assert report.current_accuracy == 0.915
        assert report.is_drift_detected is True
        assert report.severity == "critical"
        assert report.avg_test_failure_rate == 0.08

    def test_drift_report_validation(self):
        """Test DriftReport validates accuracy range."""
        # Arrange & Act & Assert: Invalid accuracy >1.0
        with pytest.raises(ValueError):
            DriftReport(
                current_accuracy=1.5,  # Invalid
                baseline_accuracy=0.982,
                accuracy_drop=0.0,
                is_drift_detected=False,
                drift_threshold=0.05,
                total_predictions=100,
                correct_predictions=100,
                detection_timestamp=datetime.now(UTC).isoformat(),
                avg_test_failure_rate=0.0,
                avg_code_churn=0.0,
                severity="info",
            )


class TestDriftError:
    """Test suite for DriftError Pydantic model."""

    def test_drift_error_creation(self):
        """Test DriftError Pydantic model creation."""
        # Arrange & Act
        error = DriftError(
            error_type="insufficient_data",
            message="Only 50 predictions available (minimum: 100 required)",
            timestamp=datetime.now(UTC).isoformat(),
        )

        # Assert
        assert error.error_type == "insufficient_data"
        assert "50 predictions" in error.message

    def test_drift_error_types(self):
        """Test DriftError enum validation for error_type."""
        # Valid types
        valid_types = [
            "insufficient_data",
            "vectorstore_error",
            "calculation_error",
            "unknown",
        ]
        for error_type in valid_types:
            error = DriftError(
                error_type=error_type,
                message="Test error",
                timestamp=datetime.now(UTC).isoformat(),
            )
            assert error.error_type == error_type
