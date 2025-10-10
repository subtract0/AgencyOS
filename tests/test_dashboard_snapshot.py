"""Tests for dashboard snapshot generator.

Validates snapshot generation, JSON structure, and file I/O.
"""

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tools.quality_feedback.dashboard_snapshot import (
    DashboardSnapshotGenerator,
    MockDashboardSnapshot,
    SnapshotMetadata,
)


class TestSnapshotMetadata:
    """Test suite for SnapshotMetadata model."""

    def test_metadata_creation(self):
        """Test metadata creation with defaults."""
        metadata = SnapshotMetadata(dashboard_available=True)

        assert metadata.dashboard_available is True
        assert metadata.snapshot_version == "1.0"
        assert isinstance(metadata.generated_at, str)
        # Verify ISO 8601 format
        datetime.fromisoformat(metadata.generated_at.replace("Z", "+00:00"))

    def test_metadata_with_custom_data_dir(self):
        """Test metadata with custom data directory."""
        metadata = SnapshotMetadata(dashboard_available=True, data_directory="/custom/path")

        assert metadata.data_directory == "/custom/path"

    def test_metadata_serialization(self):
        """Test metadata JSON serialization."""
        metadata = SnapshotMetadata(dashboard_available=False)
        data = metadata.model_dump()

        assert "generated_at" in data
        assert "snapshot_version" in data
        assert "dashboard_available" in data
        assert data["dashboard_available"] is False


class TestMockDashboardSnapshot:
    """Test suite for MockDashboardSnapshot model."""

    def test_mock_snapshot_defaults(self):
        """Test mock snapshot with default values."""
        snapshot = MockDashboardSnapshot()

        assert snapshot.total_tasks == 0
        assert snapshot.correct_classifications == 0
        assert snapshot.misclassifications == 0
        assert snapshot.accuracy_rate == 0.0
        assert snapshot.misclassifications_detected == 0
        assert snapshot.refinements_applied == 0
        assert isinstance(snapshot.timestamp, str)

    def test_mock_snapshot_with_data(self):
        """Test mock snapshot with custom data."""
        snapshot = MockDashboardSnapshot(
            total_tasks=50, correct_classifications=42, misclassifications=8, accuracy_rate=0.84
        )

        assert snapshot.total_tasks == 50
        assert snapshot.correct_classifications == 42
        assert snapshot.misclassifications == 8
        assert snapshot.accuracy_rate == 0.84

    def test_mock_snapshot_serialization(self):
        """Test mock snapshot JSON serialization."""
        snapshot = MockDashboardSnapshot(total_tasks=10)
        data = snapshot.model_dump()

        assert data["total_tasks"] == 10
        assert "timestamp" in data
        assert "accuracy_rate" in data


class TestDashboardSnapshotGenerator:
    """Test suite for DashboardSnapshotGenerator."""

    @pytest.fixture
    def temp_generator(self) -> DashboardSnapshotGenerator:
        """Create generator with temporary directories."""
        with TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "dashboard"
            output_dir = Path(tmpdir) / "snapshots"

            data_dir.mkdir(parents=True, exist_ok=True)

            generator = DashboardSnapshotGenerator(data_dir=data_dir, output_dir=output_dir)
            yield generator

    def test_generator_initialization(self, temp_generator):
        """Test generator initialization."""
        assert temp_generator.data_dir.exists()
        assert temp_generator.output_dir.exists()

    def test_generate_snapshot_without_dashboard(self, temp_generator):
        """Test snapshot generation when dashboard unavailable."""
        snapshot = temp_generator.generate_snapshot()

        # Verify structure
        assert "metadata" in snapshot
        assert "snapshot" in snapshot

        # Verify metadata
        metadata = snapshot["metadata"]
        assert "generated_at" in metadata
        assert "dashboard_available" in metadata
        assert metadata["dashboard_available"] is False

        # Verify mock snapshot data
        data = snapshot["snapshot"]
        assert "total_tasks" in data
        assert "accuracy_rate" in data
        assert data["total_tasks"] == 0

    def test_generate_snapshot_with_window(self, temp_generator):
        """Test snapshot generation with custom time window."""
        snapshot = temp_generator.generate_snapshot(window_hours=48)

        assert "snapshot" in snapshot
        # Verify snapshot was generated (even if mock)
        assert snapshot["snapshot"]["total_tasks"] >= 0

    def test_save_snapshot(self, temp_generator):
        """Test snapshot saving to file."""
        snapshot = temp_generator.generate_snapshot()
        output_path = temp_generator.save_snapshot(snapshot)

        # Verify file exists
        assert output_path.exists()
        assert output_path.suffix == ".json"

        # Verify file contents
        with open(output_path) as f:
            loaded = json.load(f)

        assert "metadata" in loaded
        assert "snapshot" in loaded

    def test_save_snapshot_with_custom_filename(self, temp_generator):
        """Test snapshot saving with custom filename."""
        snapshot = temp_generator.generate_snapshot()
        custom_name = "test_snapshot.json"
        output_path = temp_generator.save_snapshot(snapshot, filename=custom_name)

        assert output_path.name == custom_name
        assert output_path.exists()

    def test_generate_and_save(self, temp_generator):
        """Test convenience method for generate + save."""
        output_path = temp_generator.generate_and_save(window_hours=12)

        # Verify file exists
        assert output_path.exists()

        # Verify contents
        with open(output_path) as f:
            snapshot = json.load(f)

        assert "metadata" in snapshot
        assert "snapshot" in snapshot

    def test_multiple_snapshots(self, temp_generator):
        """Test generating multiple snapshots."""
        # Generate 3 snapshots
        paths = []
        for _ in range(3):
            path = temp_generator.generate_and_save()
            paths.append(path)

        # Verify all files exist
        for path in paths:
            assert path.exists()

        # Verify unique filenames (timestamp-based)
        assert len(set(p.name for p in paths)) == 3

    def test_snapshot_json_structure(self, temp_generator):
        """Test snapshot JSON structure matches expected format."""
        output_path = temp_generator.generate_and_save()

        with open(output_path) as f:
            snapshot = json.load(f)

        # Verify top-level structure
        assert isinstance(snapshot, dict)
        assert "metadata" in snapshot
        assert "snapshot" in snapshot

        # Verify metadata structure
        metadata = snapshot["metadata"]
        assert "generated_at" in metadata
        assert "snapshot_version" in metadata
        assert "dashboard_available" in metadata

        # Verify snapshot data structure
        data = snapshot["snapshot"]
        assert "total_tasks" in data
        assert "correct_classifications" in data
        assert "misclassifications" in data
        assert "accuracy_rate" in data

    def test_snapshot_timestamp_format(self, temp_generator):
        """Test snapshot timestamp is valid ISO 8601."""
        snapshot = temp_generator.generate_snapshot()
        timestamp = snapshot["metadata"]["generated_at"]

        # Verify ISO 8601 format
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_output_directory_creation(self):
        """Test automatic creation of output directory."""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new" / "snapshots"

            # Directory doesn't exist yet
            assert not output_dir.exists()

            # Create generator
            generator = DashboardSnapshotGenerator(output_dir=output_dir)

            # Directory should now exist
            assert output_dir.exists()

    def test_graceful_handling_of_missing_dashboard_data(self, temp_generator):
        """Test graceful handling when dashboard data missing."""
        # data_dir exists but is empty
        snapshot = temp_generator.generate_snapshot()

        # Should use mock data, not crash
        assert snapshot["metadata"]["dashboard_available"] is False
        assert snapshot["snapshot"]["total_tasks"] == 0


class TestCLIIntegration:
    """Test CLI functionality."""

    def test_cli_main_execution(self):
        """Test CLI main() function runs without error."""
        import sys
        from io import StringIO

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "snapshots"

            # Mock sys.argv
            original_argv = sys.argv
            sys.argv = [
                "dashboard_snapshot.py",
                "--output-dir",
                str(output_dir),
                "--window-hours",
                "12",
            ]

            try:
                from tools.quality_feedback.dashboard_snapshot import main

                # Capture stdout
                captured_output = StringIO()
                sys.stdout = captured_output

                # Run main
                main()

                # Verify output contains path
                output = captured_output.getvalue()
                assert "snapshots" in output

            finally:
                # Restore sys.argv and stdout
                sys.argv = original_argv
                sys.stdout = sys.__stdout__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
