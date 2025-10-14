"""Tests for real-time accuracy dashboard.

Validates dashboard metrics calculation, snapshot generation,
and HTML rendering functionality.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from shared.models.misclassification_report import MisclassificationReport
from shared.models.quality_signals import QualitySignals
from shared.models.refinement_result import RefinementResult
from tools.quality_feedback.accuracy_dashboard import (
    AccuracyDashboard,
    AccuracyMetrics,
    DashboardSnapshot,
)


class TestAccuracyDashboard:
    """Test suite for AccuracyDashboard."""

    @pytest.fixture
    def temp_dashboard(self) -> AccuracyDashboard:
        """Create dashboard with temporary data directory."""
        with TemporaryDirectory() as tmpdir:
            dashboard = AccuracyDashboard(data_dir=tmpdir)
            yield dashboard

    def test_initialization(self, temp_dashboard: AccuracyDashboard):
        """Test dashboard initializes with correct structure."""
        # Arrange/Act: Done in fixture

        # Assert
        assert temp_dashboard.data_dir.exists()
        assert temp_dashboard.tasks_file == temp_dashboard.data_dir / "task_records.jsonl"
        assert temp_dashboard.metrics_file == temp_dashboard.data_dir / "hourly_metrics.jsonl"

    def test_record_task_basic(self, temp_dashboard: AccuracyDashboard):
        """Test recording basic task execution."""
        # Arrange
        quality_signals = [
            QualitySignals(
                task_id="task_1",
                original_tier="moderate",
                execution_time_ratio=2.5,  # Took 2.5x longer than estimated
            )
        ]

        # Act
        temp_dashboard.record_task(
            task_id="task_1", actual_tier="P2", predicted_tier="P2", quality_signals=quality_signals
        )

        # Assert
        assert temp_dashboard.tasks_file.exists()
        with open(temp_dashboard.tasks_file) as f:
            record = json.loads(f.readline())

        assert record["task_id"] == "task_1"
        assert record["actual_tier"] == "P2"
        assert record["predicted_tier"] == "P2"
        assert record["is_correct"] is True
        assert len(record["quality_signals"]) == 1

    def test_record_task_with_misclassification(self, temp_dashboard: AccuracyDashboard):
        """Test recording task with misclassification report."""
        # Arrange
        quality_signals = [
            QualitySignals(
                task_id="task_2",
                original_tier="simple",
                test_failure_rate=0.3,  # 30% tests failed (CRITICAL severity)
            )
        ]

        from shared.models.misclassification_report import DetectedIssue

        detected_issue = DetectedIssue(
            rule_name="test_failure",
            confidence=0.95,
            severity="critical",
            description="Test failure rate 30%",
            signal_value=0.3,
        )

        misclassification = MisclassificationReport(
            task_id="task_2",
            original_tier="simple",
            recommended_tier="complex",
            detected_issues=[detected_issue],
            aggregated_confidence=0.95,
            is_misclassified=True,
            detected_at=datetime.now().isoformat(),
        )

        # Act
        temp_dashboard.record_task(
            task_id="task_2",
            actual_tier="P1",
            predicted_tier="P3",
            quality_signals=quality_signals,
            misclassification=misclassification,
        )

        # Assert
        with open(temp_dashboard.tasks_file) as f:
            record = json.loads(f.readline())

        assert record["is_correct"] is False
        assert record["misclassification"] is not None
        assert record["misclassification"]["is_misclassified"] is True

    def test_calculate_metrics_empty(self, temp_dashboard: AccuracyDashboard):
        """Test metrics calculation with no data."""
        # Arrange/Act
        metrics = temp_dashboard.calculate_metrics()

        # Assert
        assert metrics.total_tasks == 0
        assert metrics.accuracy_rate == 0.0
        assert metrics.detection_rate == 0.0

    def test_calculate_metrics_basic(self, temp_dashboard: AccuracyDashboard):
        """Test metrics calculation with basic task data."""
        # Arrange
        # Record 10 tasks: 8 correct, 2 incorrect
        for i in range(10):
            predicted = "P1" if i < 8 else "P2"
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="complex",
                code_churn_lines=25,  # Minor churn (INFO severity)
            )
            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier="P1",
                predicted_tier=predicted,
                quality_signals=[signal],
            )

        # Act
        metrics = temp_dashboard.calculate_metrics()

        # Assert
        assert metrics.total_tasks == 10
        assert metrics.correct_classifications == 8
        assert metrics.misclassifications == 2
        assert metrics.accuracy_rate == 0.8

    def test_calculate_metrics_per_tier(self, temp_dashboard: AccuracyDashboard):
        """Test per-tier accuracy calculation."""
        # Arrange
        tasks = [
            ("P1", "P1"),  # Correct
            ("P1", "P1"),  # Correct
            ("P1", "P2"),  # Incorrect
            ("P2", "P2"),  # Correct
            ("P2", "P3"),  # Incorrect
            ("P3", "P3"),  # Correct
        ]

        for i, (actual, predicted) in enumerate(tasks):
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="moderate",
                execution_time_ratio=1.5,  # Minor timing deviation (INFO severity)
            )
            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier=actual,
                predicted_tier=predicted,
                quality_signals=[signal],
            )

        # Act
        metrics = temp_dashboard.calculate_metrics()

        # Assert
        assert metrics.p1_accuracy == pytest.approx(2 / 3)  # 2 correct out of 3
        assert metrics.p2_accuracy == pytest.approx(1 / 2)  # 1 correct out of 2
        assert metrics.p3_accuracy == pytest.approx(1.0)  # 1 correct out of 1

    def test_calculate_metrics_with_detection(self, temp_dashboard: AccuracyDashboard):
        """Test detection rate calculation."""
        # Arrange
        # 10 tasks: 8 correct, 2 incorrect (1 detected)
        for i in range(10):
            predicted = "P1" if i < 8 else "P2"
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="simple",
                code_churn_lines=30,  # Minor churn (INFO severity)
            )
            misclassification = None

            if i == 9:  # Detect second misclassification
                from shared.models.misclassification_report import DetectedIssue

                detected_issue = DetectedIssue(
                    rule_name="code_churn",
                    confidence=0.8,
                    severity="warning",
                    description="Code churn 60 lines",
                    signal_value=60,
                )
                misclassification = MisclassificationReport(
                    task_id=f"task_{i}",
                    original_tier="simple",
                    recommended_tier="moderate",
                    detected_issues=[detected_issue],
                    aggregated_confidence=0.8,
                    is_misclassified=True,
                    detected_at=datetime.now().isoformat(),
                )

            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier="P1",
                predicted_tier=predicted,
                quality_signals=[signal],
                misclassification=misclassification,
            )

        # Act
        metrics = temp_dashboard.calculate_metrics()

        # Assert
        assert metrics.misclassifications_detected == 1
        assert metrics.detection_rate == 0.5  # 1 detected out of 2 misclassifications

    def test_get_snapshot(self, temp_dashboard: AccuracyDashboard):
        """Test complete dashboard snapshot generation."""
        # Arrange
        # Record some tasks
        for i in range(10):
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="complex",
                execution_time_ratio=1.2,  # Minor timing deviation
            )
            temp_dashboard.record_task(
                task_id=f"task_{i}", actual_tier="P1", predicted_tier="P1", quality_signals=[signal]
            )

        # Act
        snapshot = temp_dashboard.get_snapshot()

        # Assert
        assert isinstance(snapshot, DashboardSnapshot)
        assert snapshot.total_tasks_processed == 10
        assert snapshot.cumulative_accuracy == 1.0
        assert snapshot.current_metrics.total_tasks == 10
        assert len(snapshot.hourly_metrics) > 0

    def test_render_html(self, temp_dashboard: AccuracyDashboard):
        """Test HTML rendering."""
        # Arrange
        signal = QualitySignals(
            task_id="task_1",
            original_tier="moderate",
            code_churn_lines=15,  # Minor churn
        )

        temp_dashboard.record_task(
            task_id="task_1", actual_tier="P1", predicted_tier="P1", quality_signals=[signal]
        )

        # Act
        html = temp_dashboard.render_html()

        # Assert
        assert "Quality Feedback Loop - Accuracy Dashboard" in html
        assert "Current Accuracy" in html
        assert "chart.js" in html  # Chart library included (lowercase in CDN URL)
        assert "accuracyChart" in html  # Chart canvas present

    def test_recent_misclassifications(self, temp_dashboard: AccuracyDashboard):
        """Test retrieval of recent misclassifications."""
        # Arrange
        # Create 15 misclassifications
        for i in range(15):
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="simple",
                test_failure_rate=0.2,  # CRITICAL severity
            )

            from shared.models.misclassification_report import DetectedIssue

            detected_issue = DetectedIssue(
                rule_name="test_failure",
                confidence=0.9,
                severity="critical",
                description="Test failure rate 20%",
                signal_value=0.2,
            )
            misclassification = MisclassificationReport(
                task_id=f"task_{i}",
                original_tier="simple",
                recommended_tier="moderate",
                detected_issues=[detected_issue],
                aggregated_confidence=0.9,
                is_misclassified=True,
                detected_at=datetime.now().isoformat(),
            )

            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier="P1",
                predicted_tier="P2",
                quality_signals=[signal],
                misclassification=misclassification,
            )

        # Act
        recent = temp_dashboard._get_recent_misclassifications(limit=10)

        # Assert
        assert len(recent) == 10  # Limited to 10
        assert all(isinstance(r, MisclassificationReport) for r in recent)

    def test_recent_refinements(self, temp_dashboard: AccuracyDashboard):
        """Test retrieval of recent refinements."""
        # Arrange
        # Create 5 refinements
        for i in range(5):
            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="moderate",
                execution_time_ratio=2.0,  # Minor timing deviation
            )
            refinement = RefinementResult(
                task_id=f"task_{i}",
                patterns_updated=1,
                confidence_before=0.7,
                confidence_after=0.8,
                threshold_adjustments=[],
                iteration_count=1,
                convergence_achieved=False,
                accuracy_estimate=None,
                refined_at=datetime.now().isoformat(),
            )

            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier="P1",
                predicted_tier="P1",
                quality_signals=[signal],
                refinement=refinement,
            )

        # Act
        recent = temp_dashboard._get_recent_refinements(limit=10)

        # Assert
        assert len(recent) == 5
        assert all(isinstance(r, RefinementResult) for r in recent)

    def test_accuracy_improvement_detection(self, temp_dashboard: AccuracyDashboard):
        """Test detection of accuracy improvement trend.

        Note: is_improving requires comparing metrics from different time windows.
        When all tasks are in the same hour, no improvement can be detected.
        This test verifies the correct behavior when tasks are in a single window.
        """
        # Arrange
        # Record 100 tasks in current time window (all in same hour)
        for i in range(100):
            # Accuracy improves from 80% to 95%
            accuracy = 0.80 + (i / 100) * 0.15
            predicted = "P1" if (i % 100) / 100 < accuracy else "P2"

            signal = QualitySignals(
                task_id=f"task_{i}",
                original_tier="complex",
                code_churn_lines=20,  # Minor churn
            )
            temp_dashboard.record_task(
                task_id=f"task_{i}",
                actual_tier="P1",
                predicted_tier=predicted,
                quality_signals=[signal],
            )

        # Act
        snapshot = temp_dashboard.get_snapshot()

        # Assert
        # When all tasks are in same hour window, no time-based improvement can be detected
        # This is correct behavior - is_improving requires multiple time windows
        assert snapshot.is_improving is False
        assert snapshot.cumulative_accuracy >= 0.90  # But overall accuracy is high

    def test_time_window_filtering(self, temp_dashboard: AccuracyDashboard):
        """Test metrics calculation respects time windows."""
        # Arrange
        signal = QualitySignals(
            task_id="task_recent",
            original_tier="simple",
            execution_time_ratio=1.0,
        )

        # Record task within 1-hour window
        temp_dashboard.record_task(
            task_id="task_recent", actual_tier="P1", predicted_tier="P1", quality_signals=[signal]
        )

        # Manually add old task (>1 hour ago) to JSONL
        old_signal = QualitySignals(
            task_id="task_old",
            original_tier="simple",
            code_churn_lines=10,
        )
        old_record = {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "task_id": "task_old",
            "actual_tier": "P1",
            "predicted_tier": "P2",
            "is_correct": False,
            "quality_signals": [old_signal.model_dump()],
            "misclassification": None,
            "refinement": None,
        }

        with open(temp_dashboard.tasks_file, "a") as f:
            f.write(json.dumps(old_record) + "\n")

        # Act
        metrics_1h = temp_dashboard.calculate_metrics(window_hours=1)
        metrics_3h = temp_dashboard.calculate_metrics(window_hours=3)

        # Assert
        assert metrics_1h.total_tasks == 1  # Only recent task
        assert metrics_3h.total_tasks == 2  # Both tasks


class TestAccuracyMetrics:
    """Test suite for AccuracyMetrics model."""

    def test_validation_accuracy_rate(self):
        """Test accuracy rate validation (0.0-1.0)."""
        # Valid range
        metrics = AccuracyMetrics(
            timestamp=datetime.now(),
            total_tasks=10,
            correct_classifications=8,
            misclassifications=2,
            accuracy_rate=0.8,
        )
        assert metrics.accuracy_rate == 0.8

        # Invalid: >1.0
        with pytest.raises(ValueError):
            AccuracyMetrics(
                timestamp=datetime.now(),
                total_tasks=10,
                correct_classifications=8,
                misclassifications=2,
                accuracy_rate=1.5,
            )

        # Invalid: <0.0
        with pytest.raises(ValueError):
            AccuracyMetrics(
                timestamp=datetime.now(),
                total_tasks=10,
                correct_classifications=8,
                misclassifications=2,
                accuracy_rate=-0.1,
            )

    def test_validation_counts(self):
        """Test count validation (non-negative)."""
        # Valid
        metrics = AccuracyMetrics(
            timestamp=datetime.now(),
            total_tasks=0,
            correct_classifications=0,
            misclassifications=0,
            accuracy_rate=0.0,
        )
        assert metrics.total_tasks == 0

        # Invalid: negative total
        with pytest.raises(ValueError):
            AccuracyMetrics(
                timestamp=datetime.now(),
                total_tasks=-1,
                correct_classifications=0,
                misclassifications=0,
                accuracy_rate=0.0,
            )


class TestDashboardSnapshot:
    """Test suite for DashboardSnapshot model."""

    def test_complete_snapshot(self):
        """Test complete snapshot structure."""
        # Arrange
        current_metrics = AccuracyMetrics(
            timestamp=datetime.now(),
            total_tasks=10,
            correct_classifications=9,
            misclassifications=1,
            accuracy_rate=0.9,
        )

        # Act
        snapshot = DashboardSnapshot(
            generated_at=datetime.now(),
            current_metrics=current_metrics,
            hourly_metrics=[current_metrics],
            total_tasks_processed=100,
            cumulative_accuracy=0.88,
            total_refinements=5,
            recent_misclassifications=[],
            recent_refinements=[],
            is_improving=True,
            refinement_effectiveness=0.8,
            vectorstore_utilization=1.0,
        )

        # Assert
        assert snapshot.current_metrics.accuracy_rate == 0.9
        assert snapshot.cumulative_accuracy == 0.88
        assert snapshot.is_improving is True
        assert snapshot.refinement_effectiveness == 0.8
