"""
Comprehensive type safety test suite for PR #20.
Tests all Pydantic models and type guards introduced in the type safety sweep.
"""

import pytest
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import ValidationError

# Import all the new Pydantic models
from shared.models.telemetry import (
    TelemetryEvent,
    TelemetryMetrics,
    EventType,
    EventSeverity,
    SystemHealth,
    AgentMetrics
)
from shared.models.learning import (
    LearningInsight,
    LearningMetric,
    LearningConsolidation,
    PatternAnalysis,
    ContentTypeBreakdown,
    TimeDistribution
)
from shared.models.dashboard import (
    DashboardMetrics,
    DashboardSummary,
    SessionSummary,
    AgentActivity
)
from shared.models.memory import (
    MemoryPriority,
    MemoryMetadata,
    MemoryRecord,
    MemorySearchResult
)


class TestMemoryModels:
    """Test memory-related Pydantic models."""

    def test_memory_priority_enum(self):
        """Test MemoryPriority enum values."""
        assert MemoryPriority.LOW.value == "low"
        assert MemoryPriority.MEDIUM.value == "medium"
        assert MemoryPriority.HIGH.value == "high"
        assert MemoryPriority.CRITICAL.value == "critical"

    def test_memory_metadata_validation(self):
        """Test MemoryMetadata field validation."""
        # Valid metadata
        metadata = MemoryMetadata(
            agent_id="test_agent",
            session_id="session_123",
            success_rate=0.85
        )
        assert metadata.agent_id == "test_agent"
        assert metadata.success_rate == 0.85

        # Invalid success_rate should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(success_rate=1.5)  # > 1
        assert "success_rate must be between 0 and 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(success_rate=-0.1)  # < 0
        assert "success_rate must be between 0 and 1" in str(exc_info.value)

    def test_memory_record_validation(self):
        """Test MemoryRecord validation and methods."""
        # Valid record
        record = MemoryRecord(
            key="test_key",
            content="test content",
            tags=["tag1", "tag2", "tag1"],  # Duplicate tags
            priority=MemoryPriority.HIGH,
            ttl_seconds=3600
        )

        # Tags should be deduplicated
        assert record.tags == ["tag1", "tag2"]
        assert record.priority == MemoryPriority.HIGH

        # Test is_expired method
        assert not record.is_expired()

        # Test to_dict method
        record_dict = record.to_dict()
        assert isinstance(record_dict, dict)
        assert record_dict["key"] == "test_key"

        # Invalid TTL should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(
                key="test",
                content="test",
                ttl_seconds=-100
            )
        assert "ttl_seconds must be positive" in str(exc_info.value)

    def test_memory_search_result(self):
        """Test MemorySearchResult model."""
        record1 = MemoryRecord(key="key1", content="content1")
        record2 = MemoryRecord(key="key2", content="content2")

        result = MemorySearchResult(
            records=[record1, record2],
            total_count=2,
            search_query={"tags": ["test"]},
            execution_time_ms=15.5
        )

        assert result.total_count == 2
        assert len(result.records) == 2

        # Test get_by_key method
        found = result.get_by_key("key1")
        assert found is not None
        assert found.key == "key1"

        not_found = result.get_by_key("key3")
        assert not_found is None

        # Test filter_by_priority method
        high_priority = result.filter_by_priority(MemoryPriority.HIGH)
        assert isinstance(high_priority, list)


class TestTelemetryModels:
    """Test telemetry-related Pydantic models."""

    def test_telemetry_event_validation(self):
        """Test TelemetryEvent validation."""
        event = TelemetryEvent(
            event_id="evt_123",
            event_type=EventType.TOOL_USE,
            severity=EventSeverity.INFO,
            timestamp=datetime.now(),
            agent_id="agent_1",
            data={"tool": "search", "status": "success"}
        )

        assert event.event_type == EventType.TOOL_USE
        assert event.agent_id == "agent_1"
        assert event.severity == EventSeverity.INFO

    def test_telemetry_metrics_calculation(self):
        """Test TelemetryMetrics validation and calculations."""
        metrics = TelemetryMetrics(
            total_events=100,
            events_by_type={EventType.API_CALL: 50, EventType.TOOL_USE: 50},
            success_rate=0.85,
            error_rate=0.15,
            avg_response_time_ms=250.5
        )

        assert metrics.total_events == 100
        assert metrics.success_rate == 0.85

    def test_system_health_validation(self):
        """Test SystemHealth model."""
        health = SystemHealth(
            status="healthy",
            cpu_usage=45.2,
            memory_usage=2048,
            disk_usage=50.5,
            active_connections=10,
            uptime_seconds=3600
        )

        assert health.status == "healthy"
        assert health.memory_usage == 2048
        assert health.active_connections == 10

    def test_agent_metrics_validation(self):
        """Test AgentMetrics model."""
        metrics = AgentMetrics(
            agent_id="agent_1",
            tasks_completed=42,
            tasks_failed=3,
            average_task_time_ms=500.5,
            success_rate=0.93,
            last_activity=datetime.now()
        )

        assert metrics.agent_id == "agent_1"
        assert metrics.tasks_completed == 42
        assert metrics.success_rate == 0.93


class TestLearningModels:
    """Test learning-related Pydantic models."""

    def test_learning_insight_validation(self):
        """Test LearningInsight model."""
        insight = LearningInsight(
            insight_id="ins_123",
            category="optimization",
            description="Cache frequently accessed data",
            confidence=0.95,
            impact_score=8.5
        )

        assert insight.insight_id == "ins_123"
        assert insight.confidence == 0.95
        assert insight.impact_score == 8.5

    def test_learning_metric_validation(self):
        """Test LearningMetric model."""
        metric = LearningMetric(
            metric_name="accuracy",
            value=0.92,
            unit="percentage",
            timestamp=datetime.now(),
            trend="increasing"
        )

        assert metric.metric_name == "accuracy"
        assert metric.value == 0.92
        assert metric.trend == "increasing"

    def test_pattern_analysis_validation(self):
        """Test PatternAnalysis model."""
        analysis = PatternAnalysis(
            pattern_id="pat_456",
            pattern_type="error_recovery",
            occurrences=15,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            frequency=0.3
        )

        assert analysis.pattern_id == "pat_456"
        assert analysis.occurrences == 15
        assert analysis.frequency == 0.3

    def test_learning_consolidation(self):
        """Test LearningConsolidation model."""
        insights = [
            LearningInsight(
                insight_id=f"ins_{i}",
                category="performance",
                description=f"Insight {i}",
                confidence=0.8 + i * 0.05
            )
            for i in range(3)
        ]

        consolidation = LearningConsolidation(
            consolidation_id="con_789",
            timestamp=datetime.now(),
            insights=insights,
            total_patterns_analyzed=50,
            key_findings=["Finding 1", "Finding 2"]
        )

        assert consolidation.consolidation_id == "con_789"
        assert len(consolidation.insights) == 3
        assert consolidation.total_patterns_analyzed == 50


class TestDashboardModels:
    """Test dashboard-related Pydantic models."""

    def test_dashboard_metrics_validation(self):
        """Test DashboardMetrics model."""
        metrics = DashboardMetrics(
            timestamp=datetime.now(),
            active_agents=5,
            total_tasks=100,
            completed_tasks=85,
            failed_tasks=15,
            average_completion_time_ms=1500.5
        )

        assert metrics.active_agents == 5
        assert metrics.total_tasks == 100
        assert metrics.completed_tasks == 85

    def test_dashboard_summary_validation(self):
        """Test DashboardSummary model."""
        summary = DashboardSummary(
            summary_id="sum_123",
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_events=1000,
            unique_agents=10,
            top_performers=["agent_1", "agent_2", "agent_3"]
        )

        assert summary.summary_id == "sum_123"
        assert summary.total_events == 1000
        assert len(summary.top_performers) == 3

    def test_session_summary_validation(self):
        """Test SessionSummary model."""
        session = SessionSummary(
            session_id="sess_456",
            start_time=datetime.now(),
            duration_seconds=3600,
            tasks_completed=25,
            insights_generated=5,
            errors_encountered=2
        )

        assert session.session_id == "sess_456"
        assert session.duration_seconds == 3600
        assert session.tasks_completed == 25

    def test_agent_activity_validation(self):
        """Test AgentActivity model."""
        activity = AgentActivity(
            agent_id="agent_1",
            activity_type="task_execution",
            timestamp=datetime.now(),
            duration_ms=500,
            success=True,
            details={"task": "data_processing", "records": 100}
        )

        assert activity.agent_id == "agent_1"
        assert activity.activity_type == "task_execution"
        assert activity.success is True
        assert activity.details["records"] == 100


class TestTypeGuards:
    """Test type guard patterns used throughout the codebase."""

    def test_isinstance_guards_for_primitives(self):
        """Test isinstance() guards for primitive types."""
        # Test patterns from the codebase
        value: Any = 42
        if isinstance(value, (int, float)):
            # This should work without type errors
            result = value + 10
            assert result == 52

        value = "string"
        if isinstance(value, str):
            # This should work without type errors
            result = value.upper()
            assert result == "STRING"

        value = [1, 2, 3]
        if isinstance(value, list):
            # This should work without type errors
            result = len(value)
            assert result == 3

    def test_type_guard_for_optional_values(self):
        """Test type guards for Optional types."""
        optional_value: Optional[Dict[str, Any]] = {"key": "value"}

        if optional_value is not None:
            # After the guard, optional_value is Dict[str, Any]
            assert "key" in optional_value
            assert optional_value["key"] == "value"

        optional_value = None
        if optional_value is None:
            # Properly handle None case
            assert optional_value is None

    def test_complex_type_guards(self):
        """Test complex type guard patterns from the codebase."""
        # Pattern from swarm_memory.py
        tags_value: Any = ["tag1", "tag2"]
        if isinstance(tags_value, list):
            memory_tags = set(str(tag) for tag in tags_value if isinstance(tag, str))
            assert memory_tags == {"tag1", "tag2"}

        # Pattern for priority checking
        priority_val: Any = 3
        if isinstance(priority_val, (int, float)):
            priority_int = int(priority_val)
            assert priority_int == 3

    def test_model_validation_with_factory(self):
        """Test model creation with default factories."""
        # Test that default factories work correctly
        metadata = MemoryMetadata()  # Uses default_factory
        assert metadata.additional == {}

        record = MemoryRecord(
            key="test",
            content="content"
        )
        assert record.tags == []  # default_factory=list
        assert record.priority == MemoryPriority.MEDIUM  # default value


class TestBackwardCompatibility:
    """Test backward compatibility for Dict to Model conversions."""

    def test_dict_to_memory_record_conversion(self):
        """Test converting dict to MemoryRecord."""
        # Old dict format
        old_format = {
            "key": "test_key",
            "content": "test content",
            "tags": ["tag1", "tag2"],
            "timestamp": datetime.now().isoformat(),
            "priority": "high"
        }

        # Should be convertible to MemoryRecord
        record = MemoryRecord(
            key=old_format["key"],
            content=old_format["content"],
            tags=old_format["tags"],
            timestamp=datetime.fromisoformat(old_format["timestamp"]),
            priority=MemoryPriority(old_format["priority"])
        )

        assert record.key == "test_key"
        assert record.priority == MemoryPriority.HIGH

    def test_model_to_dict_conversion(self):
        """Test converting models back to dicts for compatibility."""
        record = MemoryRecord(
            key="test",
            content={"data": "value"},
            tags=["tag1"],
            priority=MemoryPriority.CRITICAL
        )

        # Convert to dict
        record_dict = record.to_dict()

        # Should be a proper dict with JSON-compatible values
        assert isinstance(record_dict, dict)
        assert record_dict["key"] == "test"
        assert record_dict["priority"] == "critical"
        assert isinstance(record_dict["timestamp"], str)  # ISO format string


class TestErrorHandling:
    """Test error handling and validation errors."""

    def test_strict_validation_no_extra_fields(self):
        """Test that models reject extra fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryMetadata(
                agent_id="test",
                unknown_field="should_fail"  # This should be rejected
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_required_field_validation(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(
                # Missing required 'key' field
                content="test"
            )
        assert "Field required" in str(exc_info.value)

    def test_type_validation(self):
        """Test that field types are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            MemoryRecord(
                key=123,  # Should be string
                content="test"
            )
        assert "Input should be a valid string" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])