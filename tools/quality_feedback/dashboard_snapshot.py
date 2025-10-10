"""Dashboard Snapshot Generator for Quality Feedback Loop Monitoring.

Generates periodic JSON snapshots of accuracy dashboard state for:
- Historical trend analysis
- Milestone tracking (first 100 tasks)
- Performance regression detection
- Constitutional Article IV learning extraction

Usage:
    python -m tools.quality_feedback.dashboard_snapshot

Output: logs/monitoring/snapshots/{timestamp}.json

Constitutional Compliance:
- Article I: Complete context (all dashboard data before snapshot)
- Article II: 100% verification (Pydantic validation)
- Article IV: Continuous learning (snapshots stored for analysis)
- Article V: Spec-004 traceability (monitoring requirements)
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

# Import dashboard if available, otherwise use mock data
try:
    from tools.quality_feedback.accuracy_dashboard import AccuracyDashboard, DashboardSnapshot

    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("Warning: AccuracyDashboard not available, using mock data", file=sys.stderr)


class SnapshotMetadata(BaseModel):
    """Metadata for dashboard snapshot."""

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 timestamp of snapshot generation (UTC)",
    )
    snapshot_version: str = Field(default="1.0", description="Snapshot schema version")
    dashboard_available: bool = Field(..., description="Whether real dashboard data was available")
    data_directory: str | None = Field(
        None, description="Path to dashboard data directory (if available)"
    )


class MockDashboardSnapshot(BaseModel):
    """Mock snapshot for when dashboard is unavailable."""

    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_tasks: int = Field(default=0)
    correct_classifications: int = Field(default=0)
    misclassifications: int = Field(default=0)
    accuracy_rate: float = Field(default=0.0)
    misclassifications_detected: int = Field(default=0)
    refinements_applied: int = Field(default=0)


class DashboardSnapshotGenerator:
    """Generates periodic JSON snapshots of dashboard state."""

    def __init__(self, data_dir: Path | None = None, output_dir: Path | None = None):
        """Initialize snapshot generator.

        Args:
            data_dir: Dashboard data directory (default: ~/.agency/dashboard/)
            output_dir: Snapshot output directory (default: logs/monitoring/snapshots/)
        """
        # Default directories
        if data_dir is None:
            data_dir = Path.home() / ".agency" / "dashboard"
        if output_dir is None:
            output_dir = Path("logs") / "monitoring" / "snapshots"

        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize dashboard if available
        self.dashboard: AccuracyDashboard | None = None
        if DASHBOARD_AVAILABLE and self.data_dir.exists():
            try:
                self.dashboard = AccuracyDashboard(data_dir=str(self.data_dir))
            except Exception as e:
                print(f"Warning: Failed to initialize dashboard: {e}", file=sys.stderr)

    def generate_snapshot(self, window_hours: int = 24) -> dict[str, Any]:
        """Generate dashboard snapshot.

        Args:
            window_hours: Time window for metrics (default: 24h)

        Returns:
            Dictionary containing snapshot data

        Constitutional Compliance:
            - Article I: Complete context (all dashboard data loaded)
            - Article II: Pydantic validation of snapshot structure
        """
        # Generate metadata
        metadata = SnapshotMetadata(
            dashboard_available=self.dashboard is not None,
            data_directory=str(self.data_dir) if self.data_dir.exists() else None,
        )

        # Generate dashboard snapshot
        if self.dashboard is not None:
            try:
                dashboard_snapshot = self.dashboard.generate_snapshot(window_hours=window_hours)
                snapshot_data = dashboard_snapshot.model_dump()
            except Exception as e:
                print(f"Warning: Failed to generate dashboard snapshot: {e}", file=sys.stderr)
                # Fallback to mock snapshot
                mock_snapshot = MockDashboardSnapshot()
                snapshot_data = mock_snapshot.model_dump()
        else:
            # Use mock snapshot when dashboard unavailable
            mock_snapshot = MockDashboardSnapshot()
            snapshot_data = mock_snapshot.model_dump()

        # Combine metadata and snapshot
        full_snapshot = {"metadata": metadata.model_dump(), "snapshot": snapshot_data}

        return full_snapshot

    def save_snapshot(self, snapshot: dict[str, Any], filename: str | None = None) -> Path:
        """Save snapshot to JSON file.

        Args:
            snapshot: Snapshot data dictionary
            filename: Optional custom filename (default: {timestamp}.json)

        Returns:
            Path to saved snapshot file

        Constitutional Compliance:
            - Article IV: Snapshots stored for continuous learning
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.json"

        # Save to file
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        return output_path

    def generate_and_save(self, window_hours: int = 24) -> Path:
        """Generate and save dashboard snapshot (convenience method).

        Args:
            window_hours: Time window for metrics (default: 24h)

        Returns:
            Path to saved snapshot file
        """
        snapshot = self.generate_snapshot(window_hours=window_hours)
        output_path = self.save_snapshot(snapshot)
        return output_path


def main():
    """CLI entry point for snapshot generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate dashboard snapshot for quality feedback monitoring"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Dashboard data directory (default: ~/.agency/dashboard/)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Snapshot output directory (default: logs/monitoring/snapshots/)",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=24,
        help="Time window for metrics in hours (default: 24)",
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    # Create generator
    generator = DashboardSnapshotGenerator(data_dir=args.data_dir, output_dir=args.output_dir)

    # Generate and save snapshot
    try:
        output_path = generator.generate_and_save(window_hours=args.window_hours)

        if args.verbose:
            print(f"✅ Snapshot generated: {output_path}")

            # Print snapshot summary
            with open(output_path) as f:
                snapshot = json.load(f)

            metadata = snapshot["metadata"]
            data = snapshot["snapshot"]

            print("\n📊 Snapshot Summary:")
            print(f"   Timestamp: {metadata['generated_at']}")
            print(f"   Dashboard Available: {metadata['dashboard_available']}")

            if "total_tasks" in data:
                print(f"   Total Tasks: {data['total_tasks']}")
                print(f"   Accuracy Rate: {data.get('accuracy_rate', 0.0):.2%}")
        else:
            # Quiet mode: just print path
            print(output_path)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
