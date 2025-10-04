"""
Tests for constitutional telemetry emission infrastructure.

Tests the dual-path event emission:
1. JSONL append to logs/constitutional_telemetry/
2. SimpleTelemetry integration

TDD-First: These tests are written BEFORE implementation.
"""

import json
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.models.constitutional import (
    Article,
    ConstitutionalEvent,
    EnforcementAction,
    EnforcementOutcome,
)


class TestConstitutionalEvent:
    """Test ConstitutionalEvent Pydantic model."""

    def test_constitutional_event_creation(self):
        """Test creating a valid ConstitutionalEvent."""
        event = ConstitutionalEvent(
            event_id="test-001",
            article=Article.ARTICLE_III,
            section="2",
            rule_description="No direct main commits",
            context={
                "branch": "main",
                "agent_id": "planner",
                "operation": "commit"
            },
            action=EnforcementAction.BLOCKED,
            outcome=EnforcementOutcome.SUCCESS
        )

        assert event.article == Article.ARTICLE_III
        assert event.section == "2"
        assert event.rule_description == "No direct main commits"
        assert event.action == EnforcementAction.BLOCKED
        assert event.outcome == EnforcementOutcome.SUCCESS
        assert event.context["branch"] == "main"

    def test_constitutional_event_validation_fails_on_invalid_article(self):
        """Test that invalid article enum raises validation error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ConstitutionalEvent(
                event_id="test-002",
                article="INVALID",  # Should fail
                rule_description="Test",
                action=EnforcementAction.PASSED
            )

    def test_constitutional_event_to_jsonl(self):
        """Test JSONL serialization."""
        event = ConstitutionalEvent(
            event_id="test-003",
            article=Article.ARTICLE_I,
            rule_description="Complete context check",
            action=EnforcementAction.PASSED,
            context={"agent_id": "planner"}
        )

        jsonl = event.to_jsonl()
        parsed = json.loads(jsonl)

        assert parsed["article"] == "I"
        assert parsed["event_id"] == "test-003"
        assert parsed["action"] == "passed"

    def test_generate_tags(self):
        """Test automatic tag generation."""
        event = ConstitutionalEvent(
            event_id="test-004",
            article=Article.ARTICLE_II,
            rule_description="100% verification",
            action=EnforcementAction.BLOCKED,
            outcome=EnforcementOutcome.FRICTION,
            context={
                "agent_id": "coder",
                "operation": "commit"
            }
        )

        tags = event.generate_tags()

        assert "constitutional" in tags
        assert "article_ii" in tags
        assert "action_blocked" in tags
        assert "outcome_friction" in tags
        assert "agent:coder" in tags
        assert "operation:commit" in tags


class TestConstitutionalTelemetry:
    """Test ConstitutionalTelemetry emission infrastructure."""

    def test_emit_event_creates_jsonl(self):
        """Test that emitting event creates JSONL file."""
        # Import at test time (implementation doesn't exist yet)
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            event = telemetry.emit_event(
                article=Article.ARTICLE_III,
                rule_description="No main commits",
                action=EnforcementAction.BLOCKED,
                context={"branch": "main"}
            )

            # Verify JSONL file created
            date_str = datetime.now(UTC).strftime("%Y%m%d")
            log_file = Path(tmpdir) / f"events_{date_str}.jsonl"
            assert log_file.exists()

            # Verify content
            with open(log_file) as f:
                line = f.readline()
                parsed = json.loads(line)
                assert parsed["article"] == "III"
                assert parsed["action"] == "blocked"
                assert parsed["rule_description"] == "No main commits"

    def test_emit_event_appends_to_existing_file(self):
        """Test that multiple events append to same daily file."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            # Emit multiple events
            telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Event 1",
                action=EnforcementAction.PASSED
            )

            telemetry.emit_event(
                article=Article.ARTICLE_II,
                rule_description="Event 2",
                action=EnforcementAction.WARNING
            )

            # Verify both events in same file
            date_str = datetime.now(UTC).strftime("%Y%m%d")
            log_file = Path(tmpdir) / f"events_{date_str}.jsonl"

            with open(log_file) as f:
                lines = f.readlines()
                assert len(lines) == 2

                event1 = json.loads(lines[0])
                event2 = json.loads(lines[1])

                assert event1["rule_description"] == "Event 1"
                assert event2["rule_description"] == "Event 2"

    def test_telemetry_failure_does_not_raise(self):
        """Test that telemetry failures are non-fatal."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        # Use invalid path that will fail on write
        telemetry = ConstitutionalTelemetry(log_dir=Path("/invalid/path/that/cannot/exist"))

        # Should not raise, just log warning
        event = telemetry.emit_event(
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED
        )

        # Event should still be created
        assert event is not None
        assert event.article == Article.ARTICLE_I

    def test_event_id_generation_unique(self):
        """Test that event IDs are unique."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            event1 = telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Test 1",
                action=EnforcementAction.PASSED
            )

            event2 = telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Test 2",
                action=EnforcementAction.PASSED
            )

            assert event1.event_id != event2.event_id

    @patch('tools.constitutional_telemetry.get_telemetry')
    def test_simple_telemetry_integration(self, mock_get_telemetry):
        """Test integration with SimpleTelemetry."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        # Mock SimpleTelemetry
        mock_telemetry = MagicMock()
        mock_get_telemetry.return_value = mock_telemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            telemetry.emit_event(
                article=Article.ARTICLE_III,
                rule_description="Test rule",
                action=EnforcementAction.BLOCKED,
                section="2",
                error_message="Blocked for testing"
            )

            # Verify SimpleTelemetry.log() was called
            mock_telemetry.log.assert_called_once()
            call_args = mock_telemetry.log.call_args

            assert call_args[1]["event"] == "constitutional_enforcement"
            assert call_args[1]["data"]["article"] == "III"
            assert call_args[1]["data"]["action"] == "blocked"
            assert call_args[1]["level"] == "error"  # BLOCKED maps to error

    def test_directory_creation(self):
        """Test that telemetry creates log directory if missing."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "constitutional_telemetry"

            # Directory doesn't exist yet
            assert not log_dir.exists()

            telemetry = ConstitutionalTelemetry(log_dir=log_dir)

            # Should be created during init
            assert log_dir.exists()

    def test_non_blocking_performance(self):
        """Test that event emission is <10ms (non-blocking requirement)."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            start = time.time()

            telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Performance test",
                action=EnforcementAction.PASSED
            )

            duration_ms = (time.time() - start) * 1000

            # Constitutional requirement: <10ms latency
            assert duration_ms < 10, f"Emission took {duration_ms:.2f}ms, exceeds 10ms limit"

    def test_bulk_emission_performance(self):
        """Test performance with 1000 events (avg <10ms per event)."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            start = time.time()

            for i in range(1000):
                telemetry.emit_event(
                    article=Article.ARTICLE_I,
                    rule_description=f"Event {i}",
                    action=EnforcementAction.PASSED
                )

            total_duration = time.time() - start
            avg_latency_ms = (total_duration / 1000) * 1000

            # Average should be well under 10ms
            assert avg_latency_ms < 10, f"Avg latency {avg_latency_ms:.2f}ms exceeds 10ms"

    def test_severity_mapping(self):
        """Test that enforcement actions map to correct severity levels."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        telemetry = ConstitutionalTelemetry()

        # Test mapping function
        assert telemetry._map_severity(EnforcementAction.BLOCKED) == "error"
        assert telemetry._map_severity(EnforcementAction.WARNING) == "warning"
        assert telemetry._map_severity(EnforcementAction.AUTO_FIX) == "info"
        assert telemetry._map_severity(EnforcementAction.PASSED) == "info"


class TestGlobalTelemetryFunctions:
    """Test module-level convenience functions."""

    def test_get_constitutional_telemetry_singleton(self):
        """Test that get_constitutional_telemetry returns singleton."""
        from tools.constitutional_telemetry import get_constitutional_telemetry

        instance1 = get_constitutional_telemetry()
        instance2 = get_constitutional_telemetry()

        # Should be same instance
        assert instance1 is instance2

    def test_emit_constitutional_event_convenience(self):
        """Test convenience function for emitting events."""
        from tools.constitutional_telemetry import emit_constitutional_event

        event = emit_constitutional_event(
            article=Article.ARTICLE_V,
            rule_description="Spec-driven development",
            action=EnforcementAction.PASSED,
            context={"spec_file": "feature.md"}
        )

        assert event is not None
        assert event.article == Article.ARTICLE_V
        assert event.context.get("spec_file") == "feature.md"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_permission_denied_handling(self):
        """Test graceful handling of permission errors."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        # Create directory with no write permissions
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "no_permissions"
            log_dir.mkdir()
            log_dir.chmod(0o444)  # Read-only

            telemetry = ConstitutionalTelemetry(log_dir=log_dir)

            # Should not raise
            event = telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Test",
                action=EnforcementAction.PASSED
            )

            assert event is not None

            # Cleanup: restore permissions
            log_dir.chmod(0o755)

    def test_disk_full_simulation(self):
        """Test behavior when disk is full (simulated)."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            # Mock the file write to raise OSError
            with patch('builtins.open', side_effect=OSError("No space left on device")):
                # Should not raise
                event = telemetry.emit_event(
                    article=Article.ARTICLE_I,
                    rule_description="Test",
                    action=EnforcementAction.PASSED
                )

                assert event is not None

    def test_invalid_enum_values_rejected(self):
        """Test that invalid enum values are rejected by Pydantic."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ConstitutionalEvent(
                event_id="test",
                article="INVALID_ARTICLE",
                rule_description="Test",
                action=EnforcementAction.PASSED
            )


class TestJSONLFormat:
    """Test JSONL file format compliance."""

    def test_jsonl_lines_are_valid_json(self):
        """Test that each line in JSONL file is valid JSON."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            # Emit multiple events
            for i in range(5):
                telemetry.emit_event(
                    article=Article.ARTICLE_I,
                    rule_description=f"Event {i}",
                    action=EnforcementAction.PASSED
                )

            # Read and validate each line
            date_str = datetime.now(UTC).strftime("%Y%m%d")
            log_file = Path(tmpdir) / f"events_{date_str}.jsonl"

            with open(log_file) as f:
                for line in f:
                    # Each line should be valid JSON
                    parsed = json.loads(line)
                    assert "event_id" in parsed
                    assert "article" in parsed
                    assert "action" in parsed

    def test_jsonl_timestamp_format(self):
        """Test that timestamps are ISO 8601 formatted."""
        from tools.constitutional_telemetry import ConstitutionalTelemetry

        with tempfile.TemporaryDirectory() as tmpdir:
            telemetry = ConstitutionalTelemetry(log_dir=Path(tmpdir))

            telemetry.emit_event(
                article=Article.ARTICLE_I,
                rule_description="Timestamp test",
                action=EnforcementAction.PASSED
            )

            date_str = datetime.now(UTC).strftime("%Y%m%d")
            log_file = Path(tmpdir) / f"events_{date_str}.jsonl"

            with open(log_file) as f:
                line = f.readline()
                parsed = json.loads(line)

                # Verify timestamp is ISO 8601
                timestamp_str = parsed["timestamp"]
                parsed_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                assert isinstance(parsed_timestamp, datetime)
