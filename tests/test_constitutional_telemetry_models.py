"""
Test suite for constitutional telemetry Pydantic models.

Tests Article VII Phase 1 models following NECESSARY framework:
- Normal cases: Valid model creation
- Edge cases: Boundary values, optional fields
- Corner cases: Extreme scenarios
- Error cases: Invalid data, validation failures
"""

import json
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from shared.models.constitutional import (
    Article,
    ComplianceMetrics,
    ConstitutionalEvent,
    EnforcementAction,
    EnforcementOutcome,
)


class TestArticleEnum:
    """Test Article enum validation."""

    def test_valid_article_values(self):
        """NORMAL: Test all valid article enum values."""
        assert Article.ARTICLE_I == "I"
        assert Article.ARTICLE_II == "II"
        assert Article.ARTICLE_III == "III"
        assert Article.ARTICLE_IV == "IV"
        assert Article.ARTICLE_V == "V"
        assert Article.ARTICLE_VII == "VII"

    def test_article_enum_iteration(self):
        """NORMAL: Test iterating over article values."""
        articles = list(Article)
        assert len(articles) == 6
        assert Article.ARTICLE_I in articles

    def test_article_from_string(self):
        """NORMAL: Test creating article from string value."""
        article = Article("III")
        assert article == Article.ARTICLE_III


class TestEnforcementActionEnum:
    """Test EnforcementAction enum validation."""

    def test_valid_enforcement_actions(self):
        """NORMAL: Test all valid enforcement action values."""
        assert EnforcementAction.BLOCKED == "blocked"
        assert EnforcementAction.WARNING == "warning"
        assert EnforcementAction.AUTO_FIX == "auto_fix"
        assert EnforcementAction.PASSED == "passed"

    def test_enforcement_action_from_string(self):
        """NORMAL: Test creating enforcement action from string."""
        action = EnforcementAction("blocked")
        assert action == EnforcementAction.BLOCKED


class TestEnforcementOutcomeEnum:
    """Test EnforcementOutcome enum validation."""

    def test_valid_enforcement_outcomes(self):
        """NORMAL: Test all valid enforcement outcome values."""
        assert EnforcementOutcome.SUCCESS == "success"
        assert EnforcementOutcome.FALSE_POSITIVE == "false_positive"
        assert EnforcementOutcome.FRICTION == "friction"
        assert EnforcementOutcome.OVERRIDE == "override"

    def test_enforcement_outcome_from_string(self):
        """NORMAL: Test creating enforcement outcome from string."""
        outcome = EnforcementOutcome("false_positive")
        assert outcome == EnforcementOutcome.FALSE_POSITIVE


class TestConstitutionalEvent:
    """Test ConstitutionalEvent Pydantic model."""

    def test_create_minimal_valid_event(self):
        """NORMAL: Test creating event with minimal required fields."""
        event = ConstitutionalEvent(
            event_id="test-001",
            article=Article.ARTICLE_III,
            rule_description="No direct main commits",
            action=EnforcementAction.BLOCKED,
        )

        assert event.event_id == "test-001"
        assert event.article == Article.ARTICLE_III
        assert event.rule_description == "No direct main commits"
        assert event.action == EnforcementAction.BLOCKED
        assert event.outcome == EnforcementOutcome.SUCCESS  # Default
        assert event.section is None
        assert event.context == {}
        assert event.tags == []

    def test_create_full_event_with_all_fields(self):
        """NORMAL: Test creating event with all fields populated."""
        now = datetime.utcnow()
        event = ConstitutionalEvent(
            event_id="test-002",
            timestamp=now,
            article=Article.ARTICLE_III,
            section="2",
            rule_description="No direct main commits",
            context={
                "branch": "main",
                "commit_hash": "abc123",
                "agent_id": "planner",
                "operation": "commit",
            },
            action=EnforcementAction.BLOCKED,
            outcome=EnforcementOutcome.FALSE_POSITIVE,
            severity="error",
            error_message="Direct commit to main branch attempted",
            suggested_fix="Create a feature branch and PR",
            metadata={"retry_count": 0},
            tags=["constitutional", "article_iii"],
        )

        assert event.event_id == "test-002"
        assert event.timestamp == now
        assert event.article == Article.ARTICLE_III
        assert event.section == "2"
        assert event.action == EnforcementAction.BLOCKED
        assert event.outcome == EnforcementOutcome.FALSE_POSITIVE
        assert event.context["branch"] == "main"
        assert event.severity == "error"
        assert "Create a feature branch" in event.suggested_fix
        assert "constitutional" in event.tags

    def test_timestamp_defaults_to_utcnow(self):
        """NORMAL: Test that timestamp defaults to current UTC time."""
        before = datetime.utcnow()
        event = ConstitutionalEvent(
            event_id="test-003",
            article=Article.ARTICLE_I,
            rule_description="Complete context required",
            action=EnforcementAction.PASSED,
        )
        after = datetime.utcnow()

        assert before <= event.timestamp <= after

    def test_outcome_defaults_to_success(self):
        """NORMAL: Test that outcome defaults to SUCCESS."""
        event = ConstitutionalEvent(
            event_id="test-004",
            article=Article.ARTICLE_II,
            rule_description="100% test pass required",
            action=EnforcementAction.PASSED,
        )

        assert event.outcome == EnforcementOutcome.SUCCESS

    def test_severity_defaults_to_info(self):
        """NORMAL: Test that severity defaults to info."""
        event = ConstitutionalEvent(
            event_id="test-005",
            article=Article.ARTICLE_IV,
            rule_description="VectorStore integration required",
            action=EnforcementAction.WARNING,
        )

        assert event.severity == "info"

    def test_missing_required_field_raises_validation_error(self):
        """ERROR: Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ConstitutionalEvent(
                event_id="test-006",
                article=Article.ARTICLE_V,
                # Missing rule_description (required)
                action=EnforcementAction.PASSED,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("rule_description",) for e in errors)

    def test_invalid_article_type_raises_validation_error(self):
        """ERROR: Test that invalid article type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ConstitutionalEvent(
                event_id="test-007",
                article="INVALID_ARTICLE",  # Not a valid Article enum
                rule_description="Test rule",
                action=EnforcementAction.PASSED,
            )

        errors = exc_info.value.errors()
        assert any("article" in str(e["loc"]) for e in errors)

    def test_invalid_action_type_raises_validation_error(self):
        """ERROR: Test that invalid action type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ConstitutionalEvent(
                event_id="test-008",
                article=Article.ARTICLE_I,
                rule_description="Test rule",
                action="invalid_action",  # Not a valid EnforcementAction enum
            )

        errors = exc_info.value.errors()
        assert any("action" in str(e["loc"]) for e in errors)

    def test_invalid_outcome_type_raises_validation_error(self):
        """ERROR: Test that invalid outcome type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ConstitutionalEvent(
                event_id="test-009",
                article=Article.ARTICLE_I,
                rule_description="Test rule",
                action=EnforcementAction.PASSED,
                outcome="invalid_outcome",  # Not a valid EnforcementOutcome enum
            )

        errors = exc_info.value.errors()
        assert any("outcome" in str(e["loc"]) for e in errors)

    def test_extra_fields_forbidden(self):
        """ERROR: Test that extra fields are forbidden (ConfigDict extra=forbid)."""
        with pytest.raises(ValidationError) as exc_info:
            ConstitutionalEvent(
                event_id="test-010",
                article=Article.ARTICLE_I,
                rule_description="Test rule",
                action=EnforcementAction.PASSED,
                unknown_field="should fail",  # Extra field not in schema
            )

        errors = exc_info.value.errors()
        assert any("unknown_field" in str(e["loc"]) for e in errors)

    def test_to_jsonl_creates_valid_json(self):
        """NORMAL: Test to_jsonl() produces valid JSON string."""
        event = ConstitutionalEvent(
            event_id="test-011",
            article=Article.ARTICLE_III,
            rule_description="No main commits",
            action=EnforcementAction.BLOCKED,
            context={"branch": "main"},
        )

        jsonl = event.to_jsonl()
        assert isinstance(jsonl, str)

        # Should be valid JSON
        parsed = json.loads(jsonl)
        assert parsed["event_id"] == "test-011"
        assert parsed["article"] == "III"
        assert parsed["action"] == "blocked"

    def test_to_jsonl_serializes_datetime(self):
        """NORMAL: Test to_jsonl() serializes datetime properly."""
        now = datetime.utcnow()
        event = ConstitutionalEvent(
            event_id="test-012",
            timestamp=now,
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED,
        )

        jsonl = event.to_jsonl()
        parsed = json.loads(jsonl)

        # Datetime should be serialized as ISO string
        assert "timestamp" in parsed
        assert isinstance(parsed["timestamp"], str)

    def test_generate_tags_basic(self):
        """NORMAL: Test generate_tags() creates standard tags."""
        event = ConstitutionalEvent(
            event_id="test-013",
            article=Article.ARTICLE_III,
            rule_description="No main commits",
            action=EnforcementAction.BLOCKED,
            outcome=EnforcementOutcome.SUCCESS,
        )

        tags = event.generate_tags()

        assert "constitutional" in tags
        assert "article_iii" in tags
        assert "action_blocked" in tags
        assert "outcome_success" in tags

    def test_generate_tags_with_agent_context(self):
        """NORMAL: Test generate_tags() includes agent from context."""
        event = ConstitutionalEvent(
            event_id="test-014",
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED,
            context={"agent_id": "planner"},
        )

        tags = event.generate_tags()

        assert "agent:planner" in tags

    def test_generate_tags_with_operation_context(self):
        """NORMAL: Test generate_tags() includes operation from context."""
        event = ConstitutionalEvent(
            event_id="test-015",
            article=Article.ARTICLE_III,
            rule_description="No main commits",
            action=EnforcementAction.BLOCKED,
            context={"operation": "commit"},
        )

        tags = event.generate_tags()

        assert "operation:commit" in tags

    def test_generate_tags_merges_with_existing_tags(self):
        """NORMAL: Test generate_tags() merges with existing tags."""
        event = ConstitutionalEvent(
            event_id="test-016",
            article=Article.ARTICLE_II,
            rule_description="100% verification",
            action=EnforcementAction.PASSED,
            tags=["custom_tag", "test_tag"],
        )

        tags = event.generate_tags()

        assert "custom_tag" in tags
        assert "test_tag" in tags
        assert "constitutional" in tags

    def test_context_dict_with_nested_values(self):
        """EDGE: Test context dict with nested JSON values."""
        event = ConstitutionalEvent(
            event_id="test-017",
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED,
            context={
                "branch": "main",
                "files": ["file1.py", "file2.py"],
                "metadata": {"retry": 1, "timeout": 30},
            },
        )

        assert event.context["files"] == ["file1.py", "file2.py"]
        assert event.context["metadata"]["retry"] == 1

    def test_empty_context_dict(self):
        """EDGE: Test event with empty context dict."""
        event = ConstitutionalEvent(
            event_id="test-018",
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED,
            context={},
        )

        assert event.context == {}
        tags = event.generate_tags()
        assert "constitutional" in tags  # Should still generate base tags

    def test_empty_metadata_dict(self):
        """EDGE: Test event with empty metadata dict."""
        event = ConstitutionalEvent(
            event_id="test-019",
            article=Article.ARTICLE_I,
            rule_description="Complete context",
            action=EnforcementAction.PASSED,
            metadata={},
        )

        assert event.metadata == {}

    def test_long_rule_description(self):
        """EDGE: Test event with very long rule description."""
        long_description = "A" * 1000
        event = ConstitutionalEvent(
            event_id="test-020",
            article=Article.ARTICLE_V,
            rule_description=long_description,
            action=EnforcementAction.PASSED,
        )

        assert len(event.rule_description) == 1000

    def test_unicode_in_error_message(self):
        """EDGE: Test event with unicode characters in error message."""
        event = ConstitutionalEvent(
            event_id="test-021",
            article=Article.ARTICLE_III,
            rule_description="No main commits",
            action=EnforcementAction.BLOCKED,
            error_message="Блокировка коммита в main 中文测试 🚫",
        )

        assert "🚫" in event.error_message


class TestComplianceMetrics:
    """Test ComplianceMetrics Pydantic model."""

    def test_create_minimal_metrics(self):
        """NORMAL: Test creating metrics with minimal required fields."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(period_start=start, period_end=end)

        assert metrics.period_start == start
        assert metrics.period_end == end
        assert metrics.total_events == 0
        assert metrics.events_by_article == {}
        assert metrics.events_by_action == {}
        assert metrics.events_by_outcome == {}
        assert metrics.compliance_rate == 0.0
        assert metrics.false_positive_rate == 0.0

    def test_create_metrics_with_event_counts(self):
        """NORMAL: Test creating metrics with event counts."""
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start,
            period_end=end,
            total_events=100,
            events_by_article={"I": 20, "II": 30, "III": 50},
            events_by_action={"blocked": 10, "passed": 90},
            events_by_outcome={"success": 95, "false_positive": 5},
        )

        assert metrics.total_events == 100
        assert metrics.events_by_article["III"] == 50
        assert metrics.events_by_action["passed"] == 90

    def test_calculate_rates_with_zero_events(self):
        """EDGE: Test calculate_rates() with zero events."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start, period_end=end, total_events=0
        )

        metrics.calculate_rates()

        assert metrics.compliance_rate == 0.0
        assert metrics.false_positive_rate == 0.0

    def test_calculate_rates_with_all_success(self):
        """NORMAL: Test calculate_rates() with 100% success."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start,
            period_end=end,
            total_events=100,
            events_by_outcome={"success": 100},
        )

        metrics.calculate_rates()

        assert metrics.compliance_rate == 1.0
        assert metrics.false_positive_rate == 0.0

    def test_calculate_rates_with_mixed_outcomes(self):
        """NORMAL: Test calculate_rates() with mixed outcomes."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start,
            period_end=end,
            total_events=100,
            events_by_outcome={"success": 80, "false_positive": 10, "friction": 10},
        )

        metrics.calculate_rates()

        assert metrics.compliance_rate == 0.8
        assert metrics.false_positive_rate == 0.1

    def test_calculate_rates_with_all_false_positives(self):
        """EDGE: Test calculate_rates() with 100% false positives."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start,
            period_end=end,
            total_events=50,
            events_by_outcome={"false_positive": 50},
        )

        metrics.calculate_rates()

        assert metrics.compliance_rate == 0.0
        assert metrics.false_positive_rate == 1.0

    def test_compliance_rate_validation_range(self):
        """ERROR: Test that compliance_rate must be between 0.0 and 1.0."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        with pytest.raises(ValidationError) as exc_info:
            ComplianceMetrics(
                period_start=start, period_end=end, compliance_rate=1.5  # Invalid >1.0
            )

        errors = exc_info.value.errors()
        assert any("compliance_rate" in str(e["loc"]) for e in errors)

    def test_false_positive_rate_validation_range(self):
        """ERROR: Test that false_positive_rate must be between 0.0 and 1.0."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        with pytest.raises(ValidationError) as exc_info:
            ComplianceMetrics(
                period_start=start,
                period_end=end,
                false_positive_rate=-0.1,  # Invalid <0.0
            )

        errors = exc_info.value.errors()
        assert any("false_positive_rate" in str(e["loc"]) for e in errors)

    def test_extra_fields_forbidden_in_metrics(self):
        """ERROR: Test that extra fields are forbidden in ComplianceMetrics."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        with pytest.raises(ValidationError) as exc_info:
            ComplianceMetrics(
                period_start=start,
                period_end=end,
                unknown_metric="should fail",  # Extra field not in schema
            )

        errors = exc_info.value.errors()
        assert any("unknown_metric" in str(e["loc"]) for e in errors)

    def test_period_start_before_end(self):
        """NORMAL: Test that period_start can be before period_end."""
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(period_start=start, period_end=end)

        assert metrics.period_start < metrics.period_end

    def test_calculate_rates_idempotent(self):
        """EDGE: Test that calculate_rates() is idempotent."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        metrics = ComplianceMetrics(
            period_start=start,
            period_end=end,
            total_events=100,
            events_by_outcome={"success": 90, "false_positive": 10},
        )

        metrics.calculate_rates()
        first_compliance = metrics.compliance_rate
        first_fp_rate = metrics.false_positive_rate

        metrics.calculate_rates()
        second_compliance = metrics.compliance_rate
        second_fp_rate = metrics.false_positive_rate

        assert first_compliance == second_compliance
        assert first_fp_rate == second_fp_rate


class TestConstitutionalEventIntegration:
    """Integration tests for ConstitutionalEvent model."""

    def test_event_round_trip_jsonl(self):
        """INTEGRATION: Test serializing and deserializing event via JSONL."""
        original = ConstitutionalEvent(
            event_id="integration-001",
            article=Article.ARTICLE_III,
            section="2",
            rule_description="No direct main commits",
            context={
                "branch": "main",
                "agent_id": "autonomous",
                "operation": "commit",
            },
            action=EnforcementAction.BLOCKED,
            outcome=EnforcementOutcome.FALSE_POSITIVE,
            error_message="Direct commit blocked",
            tags=["test", "integration"],
        )

        # Serialize to JSONL
        jsonl = original.to_jsonl()

        # Deserialize back to dict then model
        event_dict = json.loads(jsonl)
        reconstructed = ConstitutionalEvent(**event_dict)

        # Verify key fields match
        assert reconstructed.event_id == original.event_id
        assert reconstructed.article == original.article
        assert reconstructed.action == original.action
        assert reconstructed.outcome == original.outcome
        assert reconstructed.context == original.context

    def test_event_batch_processing(self):
        """INTEGRATION: Test processing multiple events."""
        events = []

        for i in range(10):
            event = ConstitutionalEvent(
                event_id=f"batch-{i:03d}",
                article=Article.ARTICLE_II,
                rule_description=f"Test rule {i}",
                action=(
                    EnforcementAction.PASSED
                    if i % 2 == 0
                    else EnforcementAction.BLOCKED
                ),
                outcome=(
                    EnforcementOutcome.SUCCESS
                    if i % 3 == 0
                    else EnforcementOutcome.FRICTION
                ),
            )
            events.append(event)

        assert len(events) == 10

        # Verify all events are valid
        for event in events:
            assert event.article == Article.ARTICLE_II
            assert isinstance(event.timestamp, datetime)

    def test_metrics_aggregation_from_events(self):
        """INTEGRATION: Test building ComplianceMetrics from events."""
        start = datetime.utcnow() - timedelta(days=7)
        end = datetime.utcnow()

        # Create test events
        events = [
            ConstitutionalEvent(
                event_id=f"agg-{i:03d}",
                article=Article.ARTICLE_III,
                rule_description="Test",
                action=EnforcementAction.BLOCKED
                if i < 20
                else EnforcementAction.PASSED,
                outcome=EnforcementOutcome.SUCCESS
                if i < 90
                else EnforcementOutcome.FALSE_POSITIVE,
            )
            for i in range(100)
        ]

        # Build metrics
        metrics = ComplianceMetrics(
            period_start=start, period_end=end, total_events=len(events)
        )

        # Count outcomes
        for event in events:
            outcome_key = event.outcome.value
            metrics.events_by_outcome[outcome_key] = (
                metrics.events_by_outcome.get(outcome_key, 0) + 1
            )

        metrics.calculate_rates()

        assert metrics.total_events == 100
        assert metrics.compliance_rate == 0.9
        assert metrics.false_positive_rate == 0.1
