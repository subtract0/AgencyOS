"""Real-Time Accuracy Dashboard for Quality Feedback Loop.

Provides live monitoring of routing accuracy, misclassification detection,
and VectorStore refinement effectiveness across task executions.

Constitutional Compliance:
- Article IV: Continuous learning visualization
- Article V: Spec-004 traceability (monitoring requirements)
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from pydantic import BaseModel, Field

from shared.models.quality_signals import QualitySignals
from shared.models.misclassification_report import MisclassificationReport
from shared.models.refinement_result import RefinementResult


class AccuracyMetrics(BaseModel):
    """Accuracy metrics over time window."""

    timestamp: datetime
    total_tasks: int = Field(ge=0)
    correct_classifications: int = Field(ge=0)
    misclassifications: int = Field(ge=0)
    accuracy_rate: float = Field(ge=0.0, le=1.0)

    # Breakdown by tier
    p1_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    p2_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    p3_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Detection metrics
    misclassifications_detected: int = Field(0, ge=0)
    detection_rate: float = Field(0.0, ge=0.0, le=1.0)

    # Refinement metrics
    refinements_applied: int = Field(0, ge=0)
    avg_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class DashboardSnapshot(BaseModel):
    """Complete dashboard state at point in time."""

    generated_at: datetime

    # Current window metrics (last hour)
    current_metrics: AccuracyMetrics

    # Historical trend (last 24 hours)
    hourly_metrics: List[AccuracyMetrics]

    # Cumulative stats (all time)
    total_tasks_processed: int = Field(ge=0)
    cumulative_accuracy: float = Field(ge=0.0, le=1.0)
    total_refinements: int = Field(ge=0)

    # Recent misclassifications (last 10)
    recent_misclassifications: List[MisclassificationReport]

    # Recent refinements (last 10)
    recent_refinements: List[RefinementResult]

    # Health indicators
    is_improving: bool  # Accuracy trending up
    refinement_effectiveness: float = Field(ge=0.0, le=1.0)  # % of refinements that improve accuracy
    vectorstore_utilization: float = Field(ge=0.0, le=1.0)  # % of tasks querying learnings


class AccuracyDashboard:
    """Real-time accuracy monitoring dashboard.

    Tracks routing accuracy, misclassification detection, and refinement
    effectiveness over time. Provides live metrics for quality feedback loop.

    Usage:
        dashboard = AccuracyDashboard(data_dir="~/.agency/quality_feedback")

        # Record task execution
        dashboard.record_task(
            task_id="task_1",
            actual_tier="P1",
            predicted_tier="P1",
            quality_signals=[...]
        )

        # Get current snapshot
        snapshot = dashboard.get_snapshot()
        print(f"Current accuracy: {snapshot.current_metrics.accuracy_rate:.1%}")

        # Generate HTML report
        html = dashboard.render_html()
        Path("dashboard.html").write_text(html)
    """

    def __init__(self, data_dir: str = "~/.agency/quality_feedback"):
        """Initialize dashboard with data directory.

        Args:
            data_dir: Directory to store metrics and task records
        """
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.data_dir / "task_records.jsonl"
        self.metrics_file = self.data_dir / "hourly_metrics.jsonl"

    def record_task(
        self,
        task_id: str,
        actual_tier: str,
        predicted_tier: str,
        quality_signals: List[QualitySignals],
        misclassification: Optional[MisclassificationReport] = None,
        refinement: Optional[RefinementResult] = None
    ) -> None:
        """Record task execution and outcomes.

        Args:
            task_id: Unique task identifier
            actual_tier: Ground truth tier (P1/P2/P3)
            predicted_tier: Model-predicted tier
            quality_signals: Quality signals from execution
            misclassification: If detected, the misclassification report
            refinement: If applied, the refinement result
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "actual_tier": actual_tier,
            "predicted_tier": predicted_tier,
            "is_correct": actual_tier == predicted_tier,
            "quality_signals": [s.dict() for s in quality_signals],
            "misclassification": misclassification.dict() if misclassification else None,
            "refinement": refinement.dict() if refinement else None
        }

        # Append to JSONL file
        with open(self.tasks_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    def calculate_metrics(self, window_hours: int = 1) -> AccuracyMetrics:
        """Calculate accuracy metrics for time window.

        Args:
            window_hours: Hours to look back (default: 1)

        Returns:
            AccuracyMetrics for the specified window
        """
        if not self.tasks_file.exists():
            return AccuracyMetrics(
                timestamp=datetime.now(),
                total_tasks=0,
                correct_classifications=0,
                misclassifications=0,
                accuracy_rate=0.0
            )

        cutoff = datetime.now() - timedelta(hours=window_hours)

        # Load task records within window
        records = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record["timestamp"])

                if record_time >= cutoff:
                    records.append(record)

        if not records:
            return AccuracyMetrics(
                timestamp=datetime.now(),
                total_tasks=0,
                correct_classifications=0,
                misclassifications=0,
                accuracy_rate=0.0
            )

        # Calculate overall accuracy
        total_tasks = len(records)
        correct = sum(1 for r in records if r["is_correct"])
        misclassifications = total_tasks - correct
        accuracy_rate = correct / total_tasks

        # Calculate per-tier accuracy
        tier_stats = {"P1": {"correct": 0, "total": 0},
                      "P2": {"correct": 0, "total": 0},
                      "P3": {"correct": 0, "total": 0}}

        for record in records:
            tier = record["actual_tier"]
            tier_stats[tier]["total"] += 1
            if record["is_correct"]:
                tier_stats[tier]["correct"] += 1

        p1_accuracy = (tier_stats["P1"]["correct"] / tier_stats["P1"]["total"]
                      if tier_stats["P1"]["total"] > 0 else None)
        p2_accuracy = (tier_stats["P2"]["correct"] / tier_stats["P2"]["total"]
                      if tier_stats["P2"]["total"] > 0 else None)
        p3_accuracy = (tier_stats["P3"]["correct"] / tier_stats["P3"]["total"]
                      if tier_stats["P3"]["total"] > 0 else None)

        # Calculate detection metrics
        detected = sum(1 for r in records if r["misclassification"] is not None)
        detection_rate = detected / misclassifications if misclassifications > 0 else 0.0

        # Calculate refinement metrics
        refinements = sum(1 for r in records if r["refinement"] is not None)
        confidences = [r["refinement"]["confidence"] for r in records
                      if r["refinement"] is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        return AccuracyMetrics(
            timestamp=datetime.now(),
            total_tasks=total_tasks,
            correct_classifications=correct,
            misclassifications=misclassifications,
            accuracy_rate=accuracy_rate,
            p1_accuracy=p1_accuracy,
            p2_accuracy=p2_accuracy,
            p3_accuracy=p3_accuracy,
            misclassifications_detected=detected,
            detection_rate=detection_rate,
            refinements_applied=refinements,
            avg_confidence=avg_confidence
        )

    def get_snapshot(self) -> DashboardSnapshot:
        """Get complete dashboard snapshot.

        Returns:
            DashboardSnapshot with current and historical metrics
        """
        # Current metrics (last hour)
        current_metrics = self.calculate_metrics(window_hours=1)

        # Hourly metrics (last 24 hours)
        hourly_metrics = []
        for hour in range(24, 0, -1):
            metrics = self.calculate_metrics(window_hours=hour)
            hourly_metrics.append(metrics)

        # Cumulative stats (all time)
        all_time_metrics = self.calculate_metrics(window_hours=24*365)  # 1 year max

        # Recent misclassifications and refinements
        recent_misclassifications = self._get_recent_misclassifications(limit=10)
        recent_refinements = self._get_recent_refinements(limit=10)

        # Health indicators
        is_improving = self._is_accuracy_improving(hourly_metrics)
        refinement_effectiveness = self._calculate_refinement_effectiveness()
        vectorstore_utilization = self._calculate_vectorstore_utilization()

        return DashboardSnapshot(
            generated_at=datetime.now(),
            current_metrics=current_metrics,
            hourly_metrics=hourly_metrics,
            total_tasks_processed=all_time_metrics.total_tasks,
            cumulative_accuracy=all_time_metrics.accuracy_rate,
            total_refinements=all_time_metrics.refinements_applied,
            recent_misclassifications=recent_misclassifications,
            recent_refinements=recent_refinements,
            is_improving=is_improving,
            refinement_effectiveness=refinement_effectiveness,
            vectorstore_utilization=vectorstore_utilization
        )

    def _get_recent_misclassifications(self, limit: int = 10) -> List[MisclassificationReport]:
        """Get most recent misclassification reports."""
        if not self.tasks_file.exists():
            return []

        reports = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                if record["misclassification"]:
                    reports.append(MisclassificationReport(**record["misclassification"]))

        return reports[-limit:]

    def _get_recent_refinements(self, limit: int = 10) -> List[RefinementResult]:
        """Get most recent refinement results."""
        if not self.tasks_file.exists():
            return []

        refinements = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                if record["refinement"]:
                    refinements.append(RefinementResult(**record["refinement"]))

        return refinements[-limit:]

    def _is_accuracy_improving(self, hourly_metrics: List[AccuracyMetrics]) -> bool:
        """Check if accuracy is trending upward."""
        if len(hourly_metrics) < 2:
            return False

        # Compare recent 6 hours vs previous 6 hours
        recent_avg = sum(m.accuracy_rate for m in hourly_metrics[:6]) / 6
        previous_avg = sum(m.accuracy_rate for m in hourly_metrics[6:12]) / 6 if len(hourly_metrics) >= 12 else recent_avg

        return recent_avg > previous_avg

    def _calculate_refinement_effectiveness(self) -> float:
        """Calculate % of refinements that improved accuracy."""
        if not self.tasks_file.exists():
            return 0.0

        # Find tasks with refinements and check if accuracy improved after
        refinement_tasks = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                if record["refinement"]:
                    refinement_tasks.append(record)

        if not refinement_tasks:
            return 0.0

        # For each refinement, check if subsequent tasks had better accuracy
        improvements = 0
        for i, task in enumerate(refinement_tasks):
            refinement_time = datetime.fromisoformat(task["timestamp"])

            # Get accuracy before and after refinement (10 tasks window)
            before_accuracy = self._get_accuracy_before(refinement_time, window_tasks=10)
            after_accuracy = self._get_accuracy_after(refinement_time, window_tasks=10)

            if after_accuracy > before_accuracy:
                improvements += 1

        return improvements / len(refinement_tasks)

    def _get_accuracy_before(self, timestamp: datetime, window_tasks: int = 10) -> float:
        """Get accuracy for N tasks before timestamp."""
        if not self.tasks_file.exists():
            return 0.0

        before_tasks = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record["timestamp"])

                if record_time < timestamp:
                    before_tasks.append(record)

        recent_before = before_tasks[-window_tasks:]
        if not recent_before:
            return 0.0

        correct = sum(1 for r in recent_before if r["is_correct"])
        return correct / len(recent_before)

    def _get_accuracy_after(self, timestamp: datetime, window_tasks: int = 10) -> float:
        """Get accuracy for N tasks after timestamp."""
        if not self.tasks_file.exists():
            return 0.0

        after_tasks = []
        with open(self.tasks_file) as f:
            for line in f:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record["timestamp"])

                if record_time > timestamp:
                    after_tasks.append(record)

        recent_after = after_tasks[:window_tasks]
        if not recent_after:
            return 0.0

        correct = sum(1 for r in recent_after if r["is_correct"])
        return correct / len(recent_after)

    def _calculate_vectorstore_utilization(self) -> float:
        """Calculate % of tasks that queried VectorStore learnings."""
        # Placeholder - would need to track VectorStore queries
        # For now, assume all tasks query learnings (Article IV mandate)
        return 1.0

    def render_html(self) -> str:
        """Render dashboard as HTML.

        Returns:
            HTML string with live dashboard
        """
        snapshot = self.get_snapshot()

        # Generate accuracy trend chart data
        trend_data = [(m.timestamp.strftime("%H:%M"), m.accuracy_rate * 100)
                     for m in snapshot.hourly_metrics]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quality Feedback Loop - Accuracy Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-good {{ background: #10b981; }}
        .status-warning {{ background: #f59e0b; }}
        .status-error {{ background: #ef4444; }}
        .chart {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .recent-list {{
            background: white;
            padding: 20px;
            border-radius: 8px;
        }}
        .recent-item {{
            border-bottom: 1px solid #eee;
            padding: 10px 0;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>Quality Feedback Loop - Accuracy Dashboard</h1>
        <p>Generated at: {snapshot.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{snapshot.current_metrics.accuracy_rate:.1%}</div>
            <div class="metric-label">
                <span class="status-indicator {'status-good' if snapshot.current_metrics.accuracy_rate >= 0.9 else 'status-warning' if snapshot.current_metrics.accuracy_rate >= 0.8 else 'status-error'}"></span>
                Current Accuracy (1h)
            </div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{snapshot.cumulative_accuracy:.1%}</div>
            <div class="metric-label">
                <span class="status-indicator {'status-good' if snapshot.is_improving else 'status-warning'}"></span>
                Cumulative Accuracy {'↑' if snapshot.is_improving else '→'}
            </div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{snapshot.current_metrics.detection_rate:.1%}</div>
            <div class="metric-label">
                <span class="status-indicator status-good"></span>
                Detection Rate
            </div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{snapshot.refinement_effectiveness:.1%}</div>
            <div class="metric-label">
                <span class="status-indicator status-good"></span>
                Refinement Effectiveness
            </div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{snapshot.total_tasks_processed}</div>
            <div class="metric-label">Total Tasks Processed</div>
        </div>

        <div class="metric-card">
            <div class="metric-value">{snapshot.total_refinements}</div>
            <div class="metric-label">Total Refinements Applied</div>
        </div>
    </div>

    <div class="chart">
        <h2>Accuracy Trend (24h)</h2>
        <canvas id="accuracyChart"></canvas>
    </div>

    <div class="metrics-grid">
        <div class="recent-list">
            <h3>Recent Misclassifications</h3>
            {self._render_misclassifications_html(snapshot.recent_misclassifications)}
        </div>

        <div class="recent-list">
            <h3>Recent Refinements</h3>
            {self._render_refinements_html(snapshot.recent_refinements)}
        </div>
    </div>

    <script>
        const ctx = document.getElementById('accuracyChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {[t for t, _ in trend_data]},
                datasets: [{{
                    label: 'Accuracy %',
                    data: {[a for _, a in trend_data]},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: false,
                        min: 70,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html

    def _render_misclassifications_html(self, reports: List[MisclassificationReport]) -> str:
        """Render misclassification reports as HTML."""
        if not reports:
            return "<p>No recent misclassifications detected.</p>"

        items = []
        for report in reports:
            items.append(f"""
                <div class="recent-item">
                    <strong>{report.task_id}</strong><br>
                    {report.predicted_tier} → {report.actual_tier}
                    (Severity: {report.severity})<br>
                    <span class="timestamp">{report.detection_timestamp.strftime("%Y-%m-%d %H:%M")}</span>
                </div>
            """)

        return "\n".join(items)

    def _render_refinements_html(self, refinements: List[RefinementResult]) -> str:
        """Render refinement results as HTML."""
        if not refinements:
            return "<p>No recent refinements applied.</p>"

        items = []
        for refinement in refinements:
            items.append(f"""
                <div class="recent-item">
                    <strong>Pattern: {refinement.pattern_name}</strong><br>
                    Confidence: {refinement.confidence:.1%}<br>
                    <span class="timestamp">{refinement.refinement_timestamp.strftime("%Y-%m-%d %H:%M")}</span>
                </div>
            """)

        return "\n".join(items)


def main() -> None:
    """Demo: Generate sample dashboard."""
    dashboard = AccuracyDashboard()

    # Generate sample data
    from datetime import timedelta
    import random

    tiers = ["P1", "P2", "P3"]
    base_time = datetime.now() - timedelta(hours=24)

    for i in range(100):
        task_time = base_time + timedelta(minutes=i*14.4)  # ~100 tasks in 24h

        actual_tier = random.choice(tiers)
        # Simulate 85% accuracy initially, improving to 90%
        accuracy = 0.85 + (i / 100) * 0.05
        predicted_tier = actual_tier if random.random() < accuracy else random.choice(tiers)

        quality_signals = [
            QualitySignal(
                signal_type="execution_time",
                value=random.uniform(0.5, 5.0),
                expected_range=(0.0, 10.0),
                confidence=random.uniform(0.7, 0.95)
            )
        ]

        # Simulate misclassification detection (33% of misclassifications)
        misclassification = None
        if actual_tier != predicted_tier and random.random() < 0.33:
            misclassification = MisclassificationReport(
                task_id=f"task_{i}",
                predicted_tier=predicted_tier,
                actual_tier=actual_tier,
                evidence_signals=quality_signals,
                severity="high" if abs(int(predicted_tier[1]) - int(actual_tier[1])) > 1 else "medium",
                confidence=random.uniform(0.7, 0.95),
                detection_timestamp=task_time
            )

        dashboard.record_task(
            task_id=f"task_{i}",
            actual_tier=actual_tier,
            predicted_tier=predicted_tier,
            quality_signals=quality_signals,
            misclassification=misclassification
        )

    # Generate HTML
    html = dashboard.render_html()
    output_path = Path("/tmp/accuracy_dashboard.html")
    output_path.write_text(html)

    print(f"✅ Dashboard generated: {output_path}")
    print(f"   Open in browser: file://{output_path.absolute()}")

    # Print snapshot
    snapshot = dashboard.get_snapshot()
    print(f"\n📊 Current Metrics:")
    print(f"   Accuracy: {snapshot.current_metrics.accuracy_rate:.1%}")
    print(f"   Detection Rate: {snapshot.current_metrics.detection_rate:.1%}")
    print(f"   Refinement Effectiveness: {snapshot.refinement_effectiveness:.1%}")
    print(f"   Total Tasks: {snapshot.total_tasks_processed}")


if __name__ == "__main__":
    main()
