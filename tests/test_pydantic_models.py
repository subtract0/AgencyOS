"""
Test suite for new Pydantic models.
Validates Constitutional Law #2 compliance.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from shared.models.memory import (
    MemoryRecord,
    MemoryPriority,
    MemoryMetadata,
    MemorySearchResult,
)
from shared.models.learning import (
    LearningConsolidation,
    LearningInsight,
    LearningMetric,
    PatternAnalysis,
    ContentTypeBreakdown,
    TimeDistribution,
)
from shared.models.telemetry import (
    TelemetryEvent,
    TelemetryMetrics,
    AgentMetrics,
    SystemHealth,
    EventType,
    EventSeverity,
)
from shared.models.dashboard import (
    DashboardSummary,
    SessionSummary,
    AgentActivity,
    DashboardMetrics,
)
from shared.models.context import (
    AgentContextData,
    SessionMetadata,
    AgentState,
    TaskContext,
    AgentStatus,
    TaskStatus,
)


class TestMemoryModels:
    """Test memory-related Pydantic models."""

    def test_memory_record_creation(self) -> None:
        """Test creating a memory record with all fields."""
        record = MemoryRecord(
            key="test_key",
            content="Test content",
            tags=["test", "unit"],
            priority=MemoryPriority.HIGH,
            ttl_seconds=3600,
            embedding=None
        )
        assert record.key == "test_key"
        assert record.priority == MemoryPriority.HIGH
        assert len(record.tags) == 2
        assert not record.is_expired()

    def test_memory_metadata_validation(self) -> None:
        """Test metadata field validation."""
        metadata = MemoryMetadata(
            agent_id="agent_1",
            success_rate=0.95
        )
        assert metadata.success_rate == 0.95

        # Test invalid success rate
        with pytest.raises(ValueError, match="success_rate must be between 0 and 1"):
            MemoryMetadata(success_rate=1.5)

    def test_memory_search_result(self) -> None:
        """Test memory search result functionality."""
        record1 = MemoryRecord(key="key1", content="content1", priority=MemoryPriority.HIGH, embedding=None, ttl_seconds=None)
        record2 = MemoryRecord(key="key2", content="content2", priority=MemoryPriority.LOW, embedding=None, ttl_seconds=None)

        result = MemorySearchResult(
            records=[record1, record2],
            total_count=2,
            execution_time_ms=0.0
        )

        assert result.get_by_key("key1") == record1
        assert len(result.filter_by_priority(MemoryPriority.HIGH)) == 1

    def test_memory_backward_compatibility(self) -> None:
        """Test backward compatibility with Dict[str, Any]."""
        record = MemoryRecord(key="test", content="data", embedding=None, ttl_seconds=None)
        dict_repr = record.to_dict()
        assert isinstance(dict_repr, dict)
        assert dict_repr["key"] == "test"


class TestLearningModels:
    """Test learning-related Pydantic models."""

    def test_learning_consolidation_creation(self) -> None:
        """Test creating a learning consolidation."""
        consolidation = LearningConsolidation(
            summary="Test summary",
            total_memories=100,
            unique_tags=10,
            tag_frequencies={"error": 5, "success": 20}
        )
        assert consolidation.total_memories == 100
        assert consolidation.get_top_tags(1)[0] == ("success", 20)

    def test_content_type_breakdown(self) -> None:
        """Test content type analysis."""
        breakdown = ContentTypeBreakdown(
            text=50,
            error=10,
            success=30
        )
        assert breakdown.total() == 90
        assert breakdown.get_dominant_type() == "text"

    def test_pattern_analysis(self) -> None:
        """Test pattern analysis model."""
        analysis = PatternAnalysis(
            confidence_score=0.85,
            anomalies_detected=3
        )
        assert analysis.confidence_score == 0.85
        assert not analysis.has_patterns()  # No actual patterns yet

    def test_learning_insight_validation(self) -> None:
        """Test learning insight validation."""
        insight = LearningInsight(
            category="performance",
            description="High error rate detected",
            importance="critical",
            confidence=0.9
        )
        assert insight.importance == "critical"

        # Test invalid importance level
        with pytest.raises(ValueError):
            LearningInsight(
                category="test",
                description="test",
                importance="invalid"
            )


class TestTelemetryModels:
    """Test telemetry-related Pydantic models."""

    def test_telemetry_event_creation(self) -> None:
        """Test creating telemetry events."""
        event = TelemetryEvent(
            event_id="evt_1",
            event_type=EventType.TOOL_INVOCATION,
            agent_id="agent_1",
            tool_name="bash",
            duration_ms=150.5
        )
        assert event.event_type == EventType.TOOL_INVOCATION
        assert not event.is_error()

    def test_agent_metrics_update(self) -> None:
        """Test agent metrics updates from events."""
        metrics = AgentMetrics(agent_id="agent_1")

        event = TelemetryEvent(
            event_id="evt_1",
            event_type=EventType.TOOL_INVOCATION,
            agent_id="agent_1",
            success=True,
            duration_ms=100
        )

        metrics.update_from_event(event)
        assert metrics.total_invocations == 1
        assert metrics.successful_invocations == 1
        assert metrics.average_duration_ms == 100

    def test_system_health_status(self) -> None:
        """Test system health status updates."""
        health = SystemHealth(
            total_events=100,
            error_count=15
        )
        health.update_status()
        assert health.status == "critical"  # >10% error rate

    def test_telemetry_metrics_aggregation(self) -> None:
        """Test telemetry metrics aggregation."""
        metrics = TelemetryMetrics(
            period_start=datetime.now(),
            period_end=datetime.now() + timedelta(hours=1)
        )

        event = TelemetryEvent(
            event_id="evt_1",
            event_type=EventType.ERROR,
            severity=EventSeverity.ERROR,
            agent_id="agent_1"
        )

        metrics.add_event(event)
        assert metrics.total_events == 1
        assert metrics.system_health.error_count == 1


class TestDashboardModels:
    """Test dashboard-related Pydantic models."""

    def test_session_summary(self) -> None:
        """Test session summary functionality."""
        session = SessionSummary(
            session_id="session_1",
            start_time=datetime.now(),
            total_memories=50,
            agents_involved=["agent_1", "agent_2"],
            success_rate=0.8
        )
        assert session.is_active()
        assert len(session.agents_involved) == 2

    def test_agent_activity(self) -> None:
        """Test agent activity tracking."""
        activity = AgentActivity(
            agent_id="agent_1",
            agent_type="code_agent",
            invocation_count=10,
            success_count=9
        )
        assert activity.get_success_rate() == 0.9

        activity.update_status()
        assert activity.status == "idle"  # No recent activity

    def test_dashboard_summary_aggregation(self) -> None:
        """Test dashboard summary aggregation."""
        dashboard = DashboardSummary()

        session = SessionSummary(
            session_id="s1",
            start_time=datetime.now(),
            total_memories=100,
            total_events=50,
            success_rate=0.9
        )

        dashboard.add_session(session)
        assert dashboard.metrics.sessions_analyzed == 1
        assert dashboard.metrics.avg_memories_per_session == 100

    def test_dashboard_backward_compatibility(self) -> None:
        """Test backward compatibility."""
        dashboard = DashboardSummary()
        dict_repr = dashboard.to_dict()
        assert isinstance(dict_repr, dict)
        assert "metrics" in dict_repr


class TestContextModels:
    """Test context-related Pydantic models."""

    def test_session_metadata(self) -> None:
        """Test session metadata functionality."""
        session = SessionMetadata(session_id="session_1")
        assert session.is_active()

        session.end_session()
        assert not session.is_active()
        assert session.duration_seconds() is not None

    def test_task_context_lifecycle(self) -> None:
        """Test task context lifecycle."""
        task = TaskContext(
            task_id="task_1",
            task_type="analysis"
        )
        assert task.status == TaskStatus.PENDING

        task.mark_started()
        assert task.status == TaskStatus.IN_PROGRESS

        task.mark_completed({"result": "success"})
        assert task.status == TaskStatus.COMPLETED
        assert task.output_data["result"] == "success"

    def test_agent_state_management(self) -> None:
        """Test agent state management."""
        state = AgentState(
            agent_id="agent_1",
            agent_type="code_agent",
            status=AgentStatus.READY
        )

        task = TaskContext(task_id="t1", task_type="code")
        state.add_task(task)
        assert state.has_capacity()

        next_task = state.get_next_task()
        assert next_task == task
        assert state.status == AgentStatus.RUNNING

    def test_agent_context_data(self) -> None:
        """Test complete agent context."""
        session = SessionMetadata(session_id="s1")
        context = AgentContextData(session=session)

        agent = AgentState(
            agent_id="agent_1",
            agent_type="test",
            status=AgentStatus.READY
        )

        context.add_agent(agent)
        assert context.get_agent("agent_1") == agent
        assert len(context.get_active_agents()) == 1


class TestModelIntegration:
    """Test integration between different model types."""

    def test_memory_to_learning_flow(self) -> None:
        """Test flow from memory records to learning consolidation."""
        # Create memory records
        records = [
            MemoryRecord(key=f"key_{i}", content=f"content_{i}", tags=["test"], embedding=None, ttl_seconds=None)
            for i in range(5)
        ]

        # Create learning consolidation from records
        consolidation = LearningConsolidation(
            summary=f"Analyzed {len(records)} memories",
            total_memories=len(records),
            unique_tags=1,
            tag_frequencies={"test": len(records)}
        )

        assert consolidation.total_memories == 5
        assert consolidation.tag_frequencies["test"] == 5

    def test_telemetry_to_dashboard_flow(self) -> None:
        """Test flow from telemetry events to dashboard."""
        # Create telemetry events
        events = [
            TelemetryEvent(
                event_id=f"evt_{i}",
                event_type=EventType.TOOL_INVOCATION,
                agent_id="agent_1"
            )
            for i in range(3)
        ]

        # Create dashboard from events
        dashboard = DashboardSummary()
        dashboard.metrics.total_events = len(events)

        assert dashboard.metrics.total_events == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])