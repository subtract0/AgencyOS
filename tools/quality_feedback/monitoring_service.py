"""
Monitoring Service for Quality Feedback Loop.

Tracks first 100 tasks processed through the Quality Feedback Loop
and generates milestone reports at 25/50/75/100 task intervals.

Constitutional Compliance:
- Article I: Complete context (all task data before milestone)
- Article II: 100% verification (Pydantic validation)
- Article IV: Milestone data stored for learning
- Article V: Spec-004 traceability

Usage:
    service = MonitoringService(data_dir="~/.agency/quality_feedback")

    # Record task execution
    service.record_task(task_id="task_1", predicted_tier="P2", actual_tier="P2")

    # Check for milestone
    milestone = service.check_milestone()
    if milestone:
        print(f"🎯 Milestone {milestone.milestone_number} reached!")
        print(f"   Accuracy: {milestone.metrics.overall_accuracy:.1%}")

    # Generate manual milestone report
    report = service.generate_milestone_report(force=True)

    # Get monitoring history
    history = service.get_history()
    print(f"Completed: {history.is_complete}")

Reference: specs/spec-004-quality-feedback-loop.md
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from shared.models.misclassification_report import MisclassificationReport
from shared.models.monitoring_milestone import (
    MilestoneHistory,
    MilestoneMetrics,
    MonitoringMilestone,
)
from shared.models.quality_signals import QualitySignals
from shared.models.refinement_result import RefinementResult
from tools.quality_feedback.accuracy_dashboard import AccuracyDashboard


class TaskCounter(BaseModel):
    """Thread-safe task counter with persistence."""

    model_config = ConfigDict(
        # Pydantic V2 uses model serializers instead of json_encoders
        arbitrary_types_allowed=True
    )

    count: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=datetime.now)
    last_milestone: int = Field(default=0, ge=0)
    session_id: str = Field(default_factory=lambda: f"monitoring_{int(datetime.now().timestamp())}")


class MonitoringService:
    """
    Service for monitoring first 100 tasks through Quality Feedback Loop.

    Automatically generates milestone reports at 25/50/75/100 task thresholds
    and integrates with AccuracyDashboard for comprehensive metrics.

    Thread-safe implementation with file-based persistence.

    Example:
        >>> service = MonitoringService()
        >>> service.record_task("task_1", "P2", "P2")
        >>> milestone = service.check_milestone()
        >>> if milestone:
        ...     print(f"Milestone {milestone.milestone_number} reached!")
    """

    # Milestone thresholds
    MILESTONES = [25, 50, 75, 100]

    def __init__(self, data_dir: str = "~/.agency/quality_feedback"):
        """
        Initialize monitoring service.

        Args:
            data_dir: Directory to store counter and milestone data
        """
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.counter_file = self.data_dir / "task_counter.json"
        self.milestones_dir = Path("logs/monitoring/milestones")
        self.milestones_dir.mkdir(parents=True, exist_ok=True)

        # Thread lock for counter operations
        self._lock = threading.Lock()

        # Initialize or load counter
        self._counter = self._load_counter()

        # Initialize dashboard for metrics
        self.dashboard = AccuracyDashboard(data_dir=str(self.data_dir))

    def _load_counter(self) -> TaskCounter:
        """
        Load task counter from persistence file.

        Returns:
            TaskCounter with current state or new counter if file doesn't exist
        """
        if self.counter_file.exists():
            try:
                data = json.loads(self.counter_file.read_text())
                # Convert ISO strings back to datetime
                if "started_at" in data:
                    data["started_at"] = datetime.fromisoformat(data["started_at"])
                return TaskCounter(**data)
            except Exception as e:
                print(f"⚠️  Failed to load counter: {e}, creating new counter")

        return TaskCounter()

    def _save_counter(self) -> None:
        """Save task counter to persistence file (thread-safe)."""
        with self._lock:
            # Convert datetime to ISO string for JSON serialization
            data = self._counter.dict()
            data["started_at"] = self._counter.started_at.isoformat()
            self.counter_file.write_text(json.dumps(data, indent=2))

    def record_task(
        self,
        task_id: str,
        predicted_tier: str,
        actual_tier: str,
        quality_signals: list[QualitySignals] | None = None,
        misclassification: MisclassificationReport | None = None,
        refinement: RefinementResult | None = None,
    ) -> None:
        """
        Record task execution and increment counter.

        Args:
            task_id: Unique task identifier
            predicted_tier: Model-predicted tier (P1/P2/P3)
            actual_tier: Ground truth tier
            quality_signals: Quality signals from execution
            misclassification: If detected, the misclassification report
            refinement: If applied, the refinement result
        """
        # Record in dashboard for metrics
        self.dashboard.record_task(
            task_id=task_id,
            actual_tier=actual_tier,
            predicted_tier=predicted_tier,
            quality_signals=quality_signals or [],
            misclassification=misclassification,
            refinement=refinement,
        )

        # Increment counter (thread-safe)
        with self._lock:
            self._counter.count += 1
            self._save_counter()

    def get_current_count(self) -> int:
        """
        Get current task count (thread-safe).

        Returns:
            Number of tasks processed since monitoring start
        """
        with self._lock:
            return self._counter.count

    def check_milestone(self) -> MonitoringMilestone | None:
        """
        Check if milestone threshold reached and generate report.

        Automatically generates milestone report when crossing 25/50/75/100
        task thresholds. Only generates each milestone once.

        Returns:
            MonitoringMilestone if threshold crossed, None otherwise
        """
        current_count = self.get_current_count()

        # Find next milestone threshold
        next_milestone = None
        for threshold in self.MILESTONES:
            if current_count >= threshold > self._counter.last_milestone:
                next_milestone = threshold
                break

        if next_milestone is None:
            return None

        # Generate milestone report
        milestone = self.generate_milestone_report(milestone_threshold=next_milestone)

        # Update last milestone (thread-safe)
        with self._lock:
            self._counter.last_milestone = next_milestone
            self._save_counter()

        return milestone

    def generate_milestone_report(
        self, milestone_threshold: int | None = None, force: bool = False
    ) -> MonitoringMilestone | None:
        """
        Generate milestone report with comprehensive metrics.

        Args:
            milestone_threshold: Specific milestone to generate (25/50/75/100).
                                If None, uses current count to determine milestone.
            force: If True, generate report even if already generated

        Returns:
            MonitoringMilestone with metrics snapshot, or None if criteria not met
        """
        current_count = self.get_current_count()

        # Determine milestone number and threshold
        if milestone_threshold is None:
            # Find current milestone based on count
            milestone_threshold = None
            for threshold in self.MILESTONES:
                if current_count >= threshold:
                    milestone_threshold = threshold

            if milestone_threshold is None:
                return None  # Haven't reached first milestone yet

        # Check if already generated (unless forced)
        if not force and milestone_threshold <= self._counter.last_milestone:
            return None  # Already generated this milestone

        milestone_number = self.MILESTONES.index(milestone_threshold) + 1

        # Get dashboard snapshot for metrics
        snapshot = self.dashboard.get_snapshot()

        # Calculate interval metrics (since last milestone)
        last_milestone_count = self._counter.last_milestone
        interval_metrics = self._calculate_interval_metrics(last_milestone_count, current_count)

        # Build milestone metrics
        metrics = MilestoneMetrics(
            total_tasks=current_count,
            tasks_since_last_milestone=current_count - last_milestone_count,
            overall_accuracy=snapshot.cumulative_accuracy,
            interval_accuracy=interval_metrics["accuracy"],
            misclassifications_detected=len(snapshot.recent_misclassifications),
            detection_rate=interval_metrics["detection_rate"],
            refinements_applied=snapshot.total_refinements,
            refinement_effectiveness=snapshot.refinement_effectiveness,
            avg_refinement_confidence=snapshot.current_metrics.avg_confidence,
            p1_accuracy=snapshot.current_metrics.p1_accuracy,
            p2_accuracy=snapshot.current_metrics.p2_accuracy,
            p3_accuracy=snapshot.current_metrics.p3_accuracy,
            avg_test_failure_rate=interval_metrics.get("avg_test_failure_rate"),
            avg_code_churn=interval_metrics.get("avg_code_churn"),
            avg_execution_time_ratio=interval_metrics.get("avg_execution_time_ratio"),
        )

        # Calculate improvement indicators
        is_improving = snapshot.is_improving
        accuracy_delta = self._calculate_accuracy_delta(milestone_number)

        # Generate dashboard snapshot HTML
        dashboard_html = self.dashboard.render_html()
        snapshot_path = self.milestones_dir / f"milestone_{milestone_threshold}.html"
        snapshot_path.write_text(dashboard_html)

        # Analyze misclassification patterns
        top_patterns = self._extract_top_patterns(snapshot.recent_misclassifications)
        recommended_actions = self._generate_recommendations(metrics, top_patterns, is_improving)

        # Create milestone
        time_since_start = (datetime.now() - self._counter.started_at).total_seconds()

        milestone = MonitoringMilestone(
            milestone_number=milestone_number,
            task_threshold=milestone_threshold,
            reached_at=datetime.now(),
            time_since_start=time_since_start,
            tasks_processed=current_count,
            metrics=metrics,
            is_improving=is_improving,
            accuracy_delta=accuracy_delta,
            dashboard_snapshot_path=str(snapshot_path.absolute()),
            top_misclassification_patterns=top_patterns,
            recommended_actions=recommended_actions,
        )

        # Save milestone report
        self._save_milestone(milestone)

        return milestone

    def _calculate_interval_metrics(self, start_count: int, end_count: int) -> dict[str, float]:
        """
        Calculate metrics for task interval (since last milestone).

        Args:
            start_count: Starting task count (last milestone)
            end_count: Ending task count (current)

        Returns:
            Dictionary with interval-specific metrics
        """
        # Read task records in interval
        if not self.dashboard.tasks_file.exists():
            return {"accuracy": 0.0, "detection_rate": 0.0}

        interval_records = []
        with open(self.dashboard.tasks_file) as f:
            for i, line in enumerate(f):
                if start_count <= i < end_count:
                    interval_records.append(json.loads(line))

        if not interval_records:
            return {"accuracy": 0.0, "detection_rate": 0.0}

        # Calculate interval accuracy
        correct = sum(1 for r in interval_records if r["is_correct"])
        accuracy = correct / len(interval_records)

        # Calculate detection rate
        detected = sum(1 for r in interval_records if r["misclassification"] is not None)
        detection_rate = detected / len(interval_records)

        # Calculate average quality signals
        test_failures = [
            r["quality_signals"][0].get("test_failure_rate")
            for r in interval_records
            if r["quality_signals"] and r["quality_signals"][0].get("test_failure_rate") is not None
        ]
        avg_test_failure_rate = sum(test_failures) / len(test_failures) if test_failures else None

        churns = [
            r["quality_signals"][0].get("code_churn_lines")
            for r in interval_records
            if r["quality_signals"] and r["quality_signals"][0].get("code_churn_lines") is not None
        ]
        avg_code_churn = sum(churns) / len(churns) if churns else None

        timings = [
            r["quality_signals"][0].get("execution_time_ratio")
            for r in interval_records
            if r["quality_signals"]
            and r["quality_signals"][0].get("execution_time_ratio") is not None
        ]
        avg_execution_time_ratio = sum(timings) / len(timings) if timings else None

        return {
            "accuracy": accuracy,
            "detection_rate": detection_rate,
            "avg_test_failure_rate": avg_test_failure_rate,
            "avg_code_churn": avg_code_churn,
            "avg_execution_time_ratio": avg_execution_time_ratio,
        }

    def _calculate_accuracy_delta(self, milestone_number: int) -> float | None:
        """
        Calculate accuracy change since previous milestone.

        Args:
            milestone_number: Current milestone number (1-4)

        Returns:
            Accuracy delta in percentage points, or None if first milestone
        """
        if milestone_number == 1:
            return None  # No previous milestone to compare

        # Load previous milestone
        prev_milestone_path = (
            self.milestones_dir / f"milestone_{self.MILESTONES[milestone_number - 2]}.json"
        )

        if not prev_milestone_path.exists():
            return None

        try:
            prev_data = json.loads(prev_milestone_path.read_text())
            prev_accuracy = prev_data["metrics"]["overall_accuracy"]

            current_snapshot = self.dashboard.get_snapshot()
            current_accuracy = current_snapshot.cumulative_accuracy

            return current_accuracy - prev_accuracy

        except Exception as e:
            print(f"⚠️  Failed to calculate accuracy delta: {e}")
            return None

    def _extract_top_patterns(
        self, misclassifications: list[MisclassificationReport], top_n: int = 3
    ) -> list[str]:
        """
        Extract most common misclassification patterns.

        Args:
            misclassifications: Recent misclassification reports
            top_n: Number of top patterns to return

        Returns:
            List of pattern descriptions (e.g., "simple → complex (test failures)")
        """
        if not misclassifications:
            return []

        # Count pattern occurrences
        pattern_counts: dict[str, int] = {}

        for report in misclassifications:
            pattern = f"{report.predicted_tier} → {report.actual_tier}"

            # Add primary detection signal
            if report.severity == "critical":
                # Find CRITICAL signal
                for signal in report.evidence_signals:
                    if signal.test_failure_rate and signal.test_failure_rate > 0.1:
                        pattern += " (test failures)"
                        break
                    elif signal.code_churn_lines and signal.code_churn_lines > 100:
                        pattern += " (high churn)"
                        break

            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Sort by frequency
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

        return [pattern for pattern, _ in sorted_patterns[:top_n]]

    def _generate_recommendations(
        self, metrics: MilestoneMetrics, top_patterns: list[str], is_improving: bool
    ) -> list[str]:
        """
        Generate actionable recommendations based on metrics.

        Args:
            metrics: Milestone metrics
            top_patterns: Top misclassification patterns
            is_improving: Whether accuracy is improving

        Returns:
            List of recommended actions
        """
        recommendations = []

        # Accuracy recommendations
        if metrics.overall_accuracy < 0.90:
            recommendations.append("⚠️  Accuracy below 90% - Continue VectorStore refinement")
        elif metrics.overall_accuracy >= 0.98:
            recommendations.append("✅ Target accuracy achieved (>98%) - Monitor for stability")

        # Improvement trend
        if not is_improving and metrics.total_tasks > 25:
            recommendations.append("⚠️  Accuracy plateaued - Review threshold tuning")

        # Detection rate
        if metrics.detection_rate > 0.15:
            recommendations.append(
                f"⚠️  High detection rate ({metrics.detection_rate:.1%}) - "
                "Consider lowering classification thresholds"
            )

        # Refinement effectiveness
        if metrics.refinement_effectiveness < 0.70 and metrics.refinements_applied > 5:
            recommendations.append(
                "⚠️  Low refinement effectiveness (<70%) - "
                "Review pattern quality and confidence scores"
            )

        # Pattern-specific recommendations
        if "test failures" in " ".join(top_patterns):
            recommendations.append(
                "💡 Test failure pattern detected - Lower test_failure_rate threshold to 0.09"
            )

        if "high churn" in " ".join(top_patterns):
            recommendations.append(
                "💡 High churn pattern detected - Lower code_churn threshold to 90 lines"
            )

        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("✅ System performing well - Continue monitoring")

        return recommendations

    def _save_milestone(self, milestone: MonitoringMilestone) -> None:
        """
        Save milestone report to JSON file.

        Args:
            milestone: Milestone to save
        """
        filename = f"milestone_{milestone.task_threshold}.json"
        filepath = self.milestones_dir / filename

        # Convert to dict for JSON serialization
        data = milestone.dict()
        data["reached_at"] = milestone.reached_at.isoformat()

        filepath.write_text(json.dumps(data, indent=2))

        print(f"💾 Milestone {milestone.milestone_number} saved: {filepath}")

    def get_history(self) -> MilestoneHistory:
        """
        Get complete milestone history.

        Returns:
            MilestoneHistory with all reached milestones
        """
        milestones = []

        # Load all milestone files
        for i, threshold in enumerate(self.MILESTONES):
            filepath = self.milestones_dir / f"milestone_{threshold}.json"

            if filepath.exists():
                try:
                    data = json.loads(filepath.read_text())
                    # Convert ISO strings back to datetime
                    data["reached_at"] = datetime.fromisoformat(data["reached_at"])
                    milestone = MonitoringMilestone(**data)
                    milestones.append(milestone)
                except Exception as e:
                    print(f"⚠️  Failed to load milestone {threshold}: {e}")

        # Determine completion status
        is_complete = len(milestones) >= 4

        final_accuracy = None
        accuracy_improvement = None

        if is_complete:
            final_accuracy = milestones[-1].metrics.overall_accuracy
            if len(milestones) > 1:
                accuracy_improvement = (
                    milestones[-1].metrics.overall_accuracy - milestones[0].metrics.overall_accuracy
                )

        return MilestoneHistory(
            monitoring_session_id=self._counter.session_id,
            started_at=self._counter.started_at,
            milestones=milestones,
            is_complete=is_complete,
            final_accuracy=final_accuracy,
            accuracy_improvement=accuracy_improvement,
        )

    def reset(self) -> None:
        """
        Reset monitoring counter and clear milestones.

        WARNING: This will delete all milestone data and start fresh.
        Use with caution.
        """
        with self._lock:
            self._counter = TaskCounter()
            self._save_counter()

        # Clear milestone files
        for filepath in self.milestones_dir.glob("milestone_*.json"):
            filepath.unlink()

        for filepath in self.milestones_dir.glob("milestone_*.html"):
            filepath.unlink()

        print("🔄 Monitoring service reset - all milestones cleared")


def main() -> None:
    """Demo: Monitor first 100 tasks with milestone reports."""
    import random

    from shared.models.quality_signals import QualitySignals

    service = MonitoringService()

    print("🎯 Monitoring Service Demo")
    print(f"   Session: {service._counter.session_id}")
    print(f"   Current count: {service.get_current_count()}")
    print()

    # Simulate 100 tasks with improving accuracy
    print("📊 Simulating 100 tasks...")

    tiers = ["P1", "P2", "P3"]

    for i in range(1, 101):
        # Simulate improving accuracy (85% → 98%)
        base_accuracy = 0.85 + (i / 100) * 0.13
        actual_tier = random.choice(tiers)
        predicted_tier = actual_tier if random.random() < base_accuracy else random.choice(tiers)

        # Create sample quality signals
        signals = [
            QualitySignals(
                task_id=f"task_{i}",
                original_tier=predicted_tier.lower()
                .replace("p1", "complex")
                .replace("p2", "moderate")
                .replace("p3", "simple"),
                test_failure_rate=random.uniform(0.0, 0.2),
                code_churn_lines=random.randint(10, 150),
                execution_time_ratio=random.uniform(0.5, 4.0),
            )
        ]

        service.record_task(
            task_id=f"task_{i}",
            predicted_tier=actual_tier,
            actual_tier=actual_tier if random.random() < base_accuracy else random.choice(tiers),
            quality_signals=signals,
        )

        # Check for milestone
        milestone = service.check_milestone()
        if milestone:
            print(f"\n🎯 Milestone {milestone.milestone_number} Reached!")
            print(f"   Tasks: {milestone.tasks_processed}/{milestone.task_threshold}")
            print(f"   Overall Accuracy: {milestone.metrics.overall_accuracy:.1%}")
            print(f"   Interval Accuracy: {milestone.metrics.interval_accuracy:.1%}")
            print(f"   Improving: {'✅' if milestone.is_improving else '⚠️'}")
            print(f"   Snapshot: {milestone.dashboard_snapshot_path}")
            print("\n   Top Patterns:")
            for pattern in milestone.top_misclassification_patterns:
                print(f"      - {pattern}")
            print("\n   Recommendations:")
            for action in milestone.recommended_actions:
                print(f"      {action}")
            print()

    # Show final history
    print("\n📈 Monitoring History:")
    history = service.get_history()
    print(f"   Complete: {history.is_complete}")
    print(f"   Milestones: {len(history.milestones)}/4")
    if history.final_accuracy:
        print(f"   Final Accuracy: {history.final_accuracy:.1%}")
    if history.accuracy_improvement:
        print(f"   Improvement: +{history.accuracy_improvement:.1%}")

    if history.milestones:
        progression = history.calculate_progression_rate()
        if progression:
            print(f"   Avg Improvement/Milestone: +{progression:.1%}")


if __name__ == "__main__":
    main()
