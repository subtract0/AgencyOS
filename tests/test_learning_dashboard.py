"""
Comprehensive test coverage for tools.learning_dashboard module.
Tests dashboard generation, metric calculations, and data visualization logic.
"""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

import pytest

from tools.learning_dashboard import (
    LearningMetric,
    LearningAlert,
    LearningDashboard,
    create_learning_dashboard
)
from shared.type_definitions.json import JSONValue


class TestLearningMetric:
    """Test LearningMetric dataclass."""

    def test_learning_metric_creation(self):
        """Test LearningMetric creation with valid data."""
        timestamp = datetime.now().isoformat()
        metric = LearningMetric(
            name="Test Metric",
            value=75.5,
            unit="percent",
            trend="up",
            description="Test metric description",
            timestamp=timestamp
        )

        assert metric.name == "Test Metric"
        assert metric.value == 75.5
        assert metric.unit == "percent"
        assert metric.trend == "up"
        assert metric.description == "Test metric description"
        assert metric.timestamp == timestamp

    def test_learning_metric_various_trends(self):
        """Test LearningMetric with various trend values."""
        trends = ["up", "down", "stable"]
        timestamp = datetime.now().isoformat()

        for trend in trends:
            metric = LearningMetric(
                name="Trend Test",
                value=50.0,
                unit="count",
                trend=trend,
                description="Testing trends",
                timestamp=timestamp
            )
            assert metric.trend == trend

    def test_learning_metric_various_units(self):
        """Test LearningMetric with various unit types."""
        units = ["percent", "count", "per_week", "score", "boolean"]
        timestamp = datetime.now().isoformat()

        for unit in units:
            metric = LearningMetric(
                name="Unit Test",
                value=100.0,
                unit=unit,
                trend="stable",
                description="Testing units",
                timestamp=timestamp
            )
            assert metric.unit == unit


class TestLearningAlert:
    """Test LearningAlert dataclass."""

    def test_learning_alert_creation(self):
        """Test LearningAlert creation with valid data."""
        timestamp = datetime.now().isoformat()
        alert = LearningAlert(
            level="warning",
            message="Test alert message",
            metric="test_metric",
            threshold=50.0,
            current_value=25.0,
            timestamp=timestamp
        )

        assert alert.level == "warning"
        assert alert.message == "Test alert message"
        assert alert.metric == "test_metric"
        assert alert.threshold == 50.0
        assert alert.current_value == 25.0
        assert alert.timestamp == timestamp

    def test_learning_alert_levels(self):
        """Test LearningAlert with different alert levels."""
        levels = ["info", "warning", "error"]
        timestamp = datetime.now().isoformat()

        for level in levels:
            alert = LearningAlert(
                level=level,
                message=f"Alert level {level}",
                metric="test_metric",
                threshold=100.0,
                current_value=50.0,
                timestamp=timestamp
            )
            assert alert.level == level

    def test_learning_alert_threshold_comparison(self):
        """Test LearningAlert with various threshold scenarios."""
        timestamp = datetime.now().isoformat()

        # Current value below threshold
        below_alert = LearningAlert(
            level="warning",
            message="Below threshold",
            metric="test_metric",
            threshold=100.0,
            current_value=50.0,
            timestamp=timestamp
        )
        assert below_alert.current_value < below_alert.threshold

        # Current value above threshold
        above_alert = LearningAlert(
            level="warning",
            message="Above threshold",
            metric="test_metric",
            threshold=50.0,
            current_value=100.0,
            timestamp=timestamp
        )
        assert above_alert.current_value > above_alert.threshold


class TestLearningDashboard:
    """Test LearningDashboard main functionality."""

    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock AgentContext for testing."""
        mock_context = Mock()
        mock_context.search_memories.return_value = []
        mock_context.get_session_memories.return_value = []
        return mock_context

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStore for testing."""
        mock_store = Mock()
        mock_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 80,
            'embedding_available': True
        }
        return mock_store

    @pytest.fixture
    def learning_dashboard(self, mock_agent_context, mock_vector_store):
        """Create a LearningDashboard instance for testing."""
        return LearningDashboard(mock_agent_context, mock_vector_store)

    def test_dashboard_initialization(self, mock_agent_context, mock_vector_store):
        """Test LearningDashboard initialization."""
        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)

        assert dashboard.agent_context == mock_agent_context
        assert dashboard.vector_store == mock_vector_store
        assert dashboard.metrics_history == []
        assert dashboard.alerts == []

    def test_dashboard_initialization_default_vector_store(self, mock_agent_context):
        """Test LearningDashboard initialization with default VectorStore."""
        with patch('tools.learning_dashboard.VectorStore') as mock_vector_store_class:
            mock_instance = Mock()
            mock_vector_store_class.return_value = mock_instance

            dashboard = LearningDashboard(mock_agent_context)

            assert dashboard.agent_context == mock_agent_context
            assert dashboard.vector_store == mock_instance

    def test_generate_comprehensive_report_basic(self, learning_dashboard):
        """Test basic comprehensive report generation."""
        with patch.object(learning_dashboard, '_collect_all_metrics') as mock_collect:
            mock_collect.return_value = {
                'test_metric': LearningMetric(
                    name="Test",
                    value=75.0,
                    unit="percent",
                    trend="up",
                    description="Test metric",
                    timestamp=datetime.now().isoformat()
                )
            }

            with patch.object(learning_dashboard, '_check_learning_alerts') as mock_alerts:
                mock_alerts.return_value = []

                with patch.object(learning_dashboard, '_calculate_trends') as mock_trends:
                    mock_trends.return_value = {"test_category": "stable"}

                    result = learning_dashboard.generate_comprehensive_report()

                    assert isinstance(result, dict)
                    assert "report_timestamp" in result
                    assert "health_score" in result
                    assert "metrics" in result
                    assert "trends" in result
                    assert "alerts" in result
                    assert "insights" in result
                    assert "recommendations" in result
                    assert "summary" in result

    def test_generate_comprehensive_report_with_error(self, learning_dashboard):
        """Test comprehensive report generation with error handling."""
        with patch.object(learning_dashboard, '_collect_all_metrics', side_effect=Exception("Test error")):
            result = learning_dashboard.generate_comprehensive_report()

            assert isinstance(result, dict)
            assert "error" in result
            assert "Test error" in result["error"]
            assert "timestamp" in result

    def test_collect_vector_store_metrics(self, learning_dashboard):
        """Test VectorStore metrics collection."""
        learning_dashboard.vector_store.get_stats.return_value = {
            'total_memories': 150,
            'memories_with_embeddings': 120,
            'embedding_available': True
        }

        metrics = learning_dashboard._collect_vector_store_metrics()

        assert 'total_memories' in metrics
        assert 'memories_with_embeddings' in metrics
        assert 'embedding_coverage' in metrics
        assert 'embedding_status' in metrics

        assert metrics['total_memories'].value == 150.0
        assert metrics['memories_with_embeddings'].value == 120.0
        assert metrics['embedding_coverage'].value == 80.0  # 120/150 * 100
        assert metrics['embedding_status'].value == 1.0

    def test_collect_vector_store_metrics_no_embeddings(self, learning_dashboard):
        """Test VectorStore metrics with no embedding system."""
        learning_dashboard.vector_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 0,
            'embedding_available': False
        }

        metrics = learning_dashboard._collect_vector_store_metrics()

        assert metrics['embedding_coverage'].value == 0.0
        assert metrics['embedding_status'].value == 0.0

    def test_collect_vector_store_metrics_with_error(self, learning_dashboard):
        """Test VectorStore metrics collection with error."""
        learning_dashboard.vector_store.get_stats.side_effect = Exception("VectorStore error")

        metrics = learning_dashboard._collect_vector_store_metrics()

        # Should return empty dict on error
        assert isinstance(metrics, dict)
        assert len(metrics) == 0

    def test_collect_pattern_application_metrics(self, learning_dashboard):
        """Test pattern application metrics collection."""
        # Mock recent pattern applications
        recent_time = datetime.now().isoformat()
        mock_memories = [
            {'content': 'pattern applied successfully', 'timestamp': recent_time},
            {'content': 'pattern resolved issue', 'timestamp': recent_time},
            {'content': 'pattern failed to work', 'timestamp': recent_time}
        ]

        learning_dashboard.agent_context.search_memories.return_value = mock_memories

        metrics = learning_dashboard._collect_pattern_application_metrics()

        assert 'pattern_application_rate' in metrics
        assert 'pattern_success_rate' in metrics

        assert metrics['pattern_application_rate'].value == 3  # 3 recent applications
        # Should calculate success rate based on success indicators

    def test_collect_learning_progression_metrics(self, learning_dashboard):
        """Test learning progression metrics collection."""
        recent_time = datetime.now().isoformat()
        mock_memories = [
            {
                'content': {'type': 'error_resolution', 'confidence': 0.8},
                'timestamp': recent_time
            },
            {
                'content': {'type': 'optimization', 'confidence': 0.9},
                'timestamp': recent_time
            },
            {
                'content': 'pattern learning applied',
                'timestamp': recent_time
            }
        ]

        learning_dashboard.agent_context.search_memories.return_value = mock_memories

        metrics = learning_dashboard._collect_learning_progression_metrics()

        assert 'learning_accumulation_rate' in metrics
        assert 'learning_diversity' in metrics
        assert 'average_learning_confidence' in metrics

        assert metrics['learning_accumulation_rate'].value == 3
        assert metrics['learning_diversity'].value >= 2  # At least 2 types

    def test_collect_cross_session_metrics(self, learning_dashboard):
        """Test cross-session metrics collection."""
        recent_time = datetime.now().isoformat()
        mock_memories = [
            {'content': 'cross-session pattern applied successfully', 'timestamp': recent_time},
            {'content': 'historical pattern effective', 'timestamp': recent_time}
        ]

        learning_dashboard.agent_context.search_memories.return_value = mock_memories

        metrics = learning_dashboard._collect_cross_session_metrics()

        assert 'cross_session_application_rate' in metrics
        assert 'knowledge_retention' in metrics

        assert metrics['cross_session_application_rate'].value == 2

    def test_collect_performance_metrics(self, learning_dashboard):
        """Test performance metrics collection."""
        learning_dashboard.agent_context.get_session_memories.return_value = ['mem1', 'mem2', 'mem3']

        with patch.object(learning_dashboard, '_count_learning_triggers', return_value=5):
            metrics = learning_dashboard._collect_performance_metrics()

            assert 'memory_utilization' in metrics
            assert 'learning_trigger_frequency' in metrics

            assert metrics['memory_utilization'].value == 3
            assert metrics['learning_trigger_frequency'].value == 5

    def test_calculate_metric_trend_no_history(self, learning_dashboard):
        """Test metric trend calculation with no history."""
        trend = learning_dashboard._calculate_metric_trend('new_metric', 100.0)
        assert trend == "stable"

    def test_calculate_metric_trend_with_history(self, learning_dashboard):
        """Test metric trend calculation with history."""
        # Setup metric history
        learning_dashboard.metrics_history = [
            {
                'metrics': {
                    'test_metric': {'value': 80.0}
                }
            },
            {
                'metrics': {
                    'test_metric': {'value': 85.0}
                }
            },
            {
                'metrics': {
                    'test_metric': {'value': 90.0}
                }
            }
        ]

        # Test upward trend
        trend_up = learning_dashboard._calculate_metric_trend('test_metric', 100.0)
        assert trend_up == "up"

        # Test downward trend
        trend_down = learning_dashboard._calculate_metric_trend('test_metric', 70.0)
        assert trend_down == "down"

        # Test stable trend
        trend_stable = learning_dashboard._calculate_metric_trend('test_metric', 87.0)
        assert trend_stable == "stable"

    def test_is_recent_memory(self, learning_dashboard):
        """Test recent memory identification."""
        cutoff_time = datetime.now() - timedelta(hours=1)

        # Recent memory
        recent_memory = {
            'timestamp': datetime.now().isoformat()
        }
        assert learning_dashboard._is_recent_memory(recent_memory, cutoff_time) is True

        # Old memory
        old_memory = {
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
        }
        assert learning_dashboard._is_recent_memory(old_memory, cutoff_time) is False

        # Memory without timestamp
        no_timestamp_memory = {}
        assert learning_dashboard._is_recent_memory(no_timestamp_memory, cutoff_time) is False

        # Memory with invalid timestamp
        invalid_timestamp_memory = {
            'timestamp': 'invalid-timestamp'
        }
        assert learning_dashboard._is_recent_memory(invalid_timestamp_memory, cutoff_time) is False

    def test_is_successful_application(self, learning_dashboard):
        """Test successful application identification."""
        success_cases = [
            {'content': 'pattern applied with success'},
            {'content': 'issue resolved effectively'},
            {'content': 'improvement working well'},
            {'content': 'effective solution implemented'}
        ]

        for case in success_cases:
            assert learning_dashboard._is_successful_application(case) is True

        failure_cases = [
            {'content': 'pattern failed to work'},
            {'content': 'no improvement seen'},
            {'content': 'approach did not help'}
        ]

        for case in failure_cases:
            assert learning_dashboard._is_successful_application(case) is False

    def test_extract_learning_types(self, learning_dashboard):
        """Test learning type extraction from memories."""
        memories = [
            {'content': {'type': 'error_resolution'}},
            {'content': {'learning_type': 'optimization'}},
            {'content': 'error handling pattern'},
            {'content': 'optimization technique'},
            {'content': 'pattern application'},
            {'content': {'type': 'error_resolution'}}  # Duplicate
        ]

        types = learning_dashboard._extract_learning_types(memories)

        assert 'error_resolution' in types
        assert 'optimization' in types
        assert 'pattern' in types
        # Should not have duplicates
        assert len([t for t in types if t == 'error_resolution']) == 1

    def test_extract_learning_confidences(self, learning_dashboard):
        """Test confidence extraction from learning memories."""
        memories = [
            {'content': {'confidence': 0.8}},
            {'content': {'overall_confidence': 0.9}},
            {'content': {'confidence': 0.7}},
            {'content': 'no confidence specified'}
        ]

        confidences = learning_dashboard._extract_learning_confidences(memories)

        assert len(confidences) == 3
        assert 0.8 in confidences
        assert 0.9 in confidences
        assert 0.7 in confidences

    def test_calculate_knowledge_retention(self, learning_dashboard):
        """Test knowledge retention calculation."""
        # All successful applications
        successful_memories = [
            {'content': 'pattern success'},
            {'content': 'resolved issue'},
            {'content': 'effective solution'}
        ]

        retention_perfect = learning_dashboard._calculate_knowledge_retention(successful_memories)
        assert retention_perfect == 100.0

        # Mixed success/failure
        mixed_memories = [
            {'content': 'pattern success'},
            {'content': 'failed to resolve'},
            {'content': 'effective solution'},
            {'content': 'no improvement'}
        ]

        retention_mixed = learning_dashboard._calculate_knowledge_retention(mixed_memories)
        assert retention_mixed == 50.0  # 2 out of 4 successful

        # No memories
        retention_empty = learning_dashboard._calculate_knowledge_retention([])
        assert retention_empty == 0.0

    def test_count_learning_triggers(self, learning_dashboard):
        """Test learning trigger counting."""
        recent_time = datetime.now().isoformat()
        old_time = (datetime.now() - timedelta(days=2)).isoformat()

        mock_triggers = [
            {'timestamp': recent_time},
            {'timestamp': recent_time},
            {'timestamp': old_time}  # Should not be counted
        ]

        learning_dashboard.agent_context.search_memories.return_value = mock_triggers

        count = learning_dashboard._count_learning_triggers()
        assert count == 2  # Only recent triggers

    def test_check_learning_alerts(self, learning_dashboard):
        """Test learning alert generation."""
        metrics = {
            'embedding_coverage': LearningMetric(
                name="Embedding Coverage",
                value=30.0,  # Below 50% threshold
                unit="percent",
                trend="down",
                description="Low coverage",
                timestamp=datetime.now().isoformat()
            ),
            'pattern_success_rate': LearningMetric(
                name="Pattern Success Rate",
                value=40.0,  # Below 60% threshold
                unit="percent",
                trend="down",
                description="Low success rate",
                timestamp=datetime.now().isoformat()
            ),
            'embedding_status': LearningMetric(
                name="Embedding Status",
                value=0.0,  # Embedding system down
                unit="boolean",
                trend="stable",
                description="Embedding system status",
                timestamp=datetime.now().isoformat()
            )
        }

        alerts = learning_dashboard._check_learning_alerts(metrics)

        assert len(alerts) == 3
        alert_levels = [alert.level for alert in alerts]
        assert "warning" in alert_levels
        assert "error" in alert_levels

    def test_calculate_trends(self, learning_dashboard):
        """Test trend calculation for metric categories."""
        metrics = {
            'embedding_coverage': LearningMetric("Coverage", 80.0, "percent", "up", "desc", "timestamp"),
            'total_memories': LearningMetric("Memories", 100.0, "count", "up", "desc", "timestamp"),
            'pattern_success_rate': LearningMetric("Success", 75.0, "percent", "down", "desc", "timestamp"),
            'pattern_application_rate': LearningMetric("Apps", 5.0, "per_week", "stable", "desc", "timestamp"),
            'learning_accumulation_rate': LearningMetric("Learning", 10.0, "per_month", "up", "desc", "timestamp")
        }

        trends = learning_dashboard._calculate_trends(metrics)

        assert 'vector_store' in trends
        assert 'pattern_application' in trends
        assert 'learning_progression' in trends

    def test_aggregate_trends(self, learning_dashboard):
        """Test trend aggregation logic."""
        # More up trends
        trends_up = ['up', 'up', 'down']
        result_up = learning_dashboard._aggregate_trends(trends_up)
        assert result_up == "improving"

        # More down trends
        trends_down = ['down', 'down', 'up']
        result_down = learning_dashboard._aggregate_trends(trends_down)
        assert result_down == "declining"

        # Equal or stable
        trends_stable = ['up', 'down', 'stable']
        result_stable = learning_dashboard._aggregate_trends(trends_stable)
        assert result_stable == "stable"

        # Empty list
        trends_empty = []
        result_empty = learning_dashboard._aggregate_trends(trends_empty)
        assert result_empty == "stable"

    def test_generate_learning_insights(self, learning_dashboard):
        """Test learning insights generation."""
        metrics = {
            'embedding_coverage': LearningMetric("Coverage", 85.0, "percent", "up", "desc", "timestamp"),
            'pattern_success_rate': LearningMetric("Success", 90.0, "percent", "up", "desc", "timestamp"),
            'pattern_application_rate': LearningMetric("Apps", 10.0, "per_week", "up", "desc", "timestamp"),
            'learning_diversity': LearningMetric("Diversity", 8.0, "types", "up", "desc", "timestamp")
        }

        trends = {
            'vector_store': 'improving',
            'pattern_application': 'stable'
        }

        insights = learning_dashboard._generate_learning_insights(metrics, trends)

        assert isinstance(insights, list)
        assert len(insights) > 0

        # Check insight structure
        for insight in insights:
            assert 'category' in insight
            assert 'type' in insight
            assert 'message' in insight
            assert 'recommendation' in insight

    def test_calculate_system_health(self, learning_dashboard):
        """Test system health score calculation."""
        metrics = {
            'embedding_coverage': LearningMetric("Coverage", 80.0, "percent", "up", "desc", "timestamp"),
            'pattern_success_rate': LearningMetric("Success", 85.0, "percent", "up", "desc", "timestamp"),
            'learning_accumulation_rate': LearningMetric("Learning", 5.0, "per_month", "up", "desc", "timestamp")
        }

        alerts = [
            LearningAlert("warning", "Test warning", "test_metric", 50.0, 40.0, "timestamp")
        ]

        health = learning_dashboard._calculate_system_health(metrics, alerts)

        assert isinstance(health, dict)
        assert 'score' in health
        assert 'status' in health
        assert 'components' in health
        assert 'calculation_timestamp' in health

        assert isinstance(health['score'], (int, float))
        assert health['status'] in ['excellent', 'good', 'fair', 'poor']

    def test_generate_improvement_recommendations(self, learning_dashboard):
        """Test improvement recommendations generation."""
        metrics = {
            'embedding_coverage': LearningMetric("Coverage", 30.0, "percent", "down", "desc", "timestamp"),
            'pattern_application_rate': LearningMetric("Apps", 1.0, "per_week", "down", "desc", "timestamp")
        }

        alerts = [
            LearningAlert("error", "Critical issue", "embedding_status", 1.0, 0.0, "timestamp")
        ]

        recommendations = learning_dashboard._generate_improvement_recommendations(metrics, alerts)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check recommendation structure
        for rec in recommendations:
            assert 'priority' in rec
            assert 'category' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'specific_actions' in rec

    def test_get_alert_resolution_actions(self, learning_dashboard):
        """Test alert resolution action generation."""
        embedding_alert = LearningAlert("error", "Embedding down", "embedding_status", 1.0, 0.0, "timestamp")
        pattern_alert = LearningAlert("warning", "Low success", "pattern_success_rate", 60.0, 40.0, "timestamp")
        other_alert = LearningAlert("info", "Other issue", "other_metric", 100.0, 50.0, "timestamp")

        embedding_actions = learning_dashboard._get_alert_resolution_actions(embedding_alert)
        pattern_actions = learning_dashboard._get_alert_resolution_actions(pattern_alert)
        other_actions = learning_dashboard._get_alert_resolution_actions(other_alert)

        assert isinstance(embedding_actions, list)
        assert len(embedding_actions) > 0
        assert any("embedding" in action.lower() for action in embedding_actions)

        assert isinstance(pattern_actions, list)
        assert len(pattern_actions) > 0
        assert any("pattern" in action.lower() for action in pattern_actions)

        assert isinstance(other_actions, list)
        assert len(other_actions) > 0

    def test_create_executive_summary(self, learning_dashboard):
        """Test executive summary creation."""
        health_score = {
            'score': 75.0,
            'status': 'good'
        }

        metrics = {
            'metric1': LearningMetric("Metric1", 80.0, "percent", "up", "desc", "timestamp"),
            'metric2': LearningMetric("Metric2", 60.0, "percent", "down", "desc", "timestamp")
        }

        alerts = [
            LearningAlert("warning", "Test warning", "test_metric", 50.0, 40.0, "timestamp")
        ]

        summary = learning_dashboard._create_executive_summary(health_score, metrics, alerts)

        assert isinstance(summary, dict)
        assert 'health_status' in summary
        assert 'health_score' in summary
        assert 'metrics_tracked' in summary
        assert 'positive_trends' in summary
        assert 'negative_trends' in summary
        assert 'critical_issues' in summary
        assert 'warnings' in summary
        assert 'key_highlights' in summary
        assert 'overall_assessment' in summary
        assert 'summary_timestamp' in summary

    def test_get_overall_assessment(self, learning_dashboard):
        """Test overall assessment generation."""
        # Excellent health, no issues
        assessment_excellent = learning_dashboard._get_overall_assessment(85.0, 0)
        assert "optimally" in assessment_excellent

        # Good health, no critical issues
        assessment_good = learning_dashboard._get_overall_assessment(70.0, 0)
        assert "stable" in assessment_good

        # Fair health
        assessment_fair = learning_dashboard._get_overall_assessment(50.0, 0)
        assert "improvement" in assessment_fair

        # Poor health
        assessment_poor = learning_dashboard._get_overall_assessment(30.0, 0)
        assert "significant" in assessment_poor

        # Critical issues override score
        assessment_critical = learning_dashboard._get_overall_assessment(90.0, 2)
        assert "immediate attention" in assessment_critical

    def test_save_metrics_snapshot(self, learning_dashboard):
        """Test metrics snapshot saving."""
        # Mock metrics collection
        mock_metrics = {
            'test_metric': LearningMetric(
                name="Test",
                value=75.0,
                unit="percent",
                trend="up",
                description="Test metric",
                timestamp=datetime.now().isoformat()
            )
        }

        with patch.object(learning_dashboard, '_collect_all_metrics', return_value=mock_metrics):
            result = learning_dashboard.save_metrics_snapshot()

            assert "snapshot saved" in result.lower()
            assert len(learning_dashboard.metrics_history) == 1

            # Check snapshot structure
            snapshot = learning_dashboard.metrics_history[0]
            assert 'snapshot_timestamp' in snapshot
            assert 'metrics' in snapshot
            assert 'test_metric' in snapshot['metrics']

    def test_save_metrics_snapshot_history_limit(self, learning_dashboard):
        """Test metrics snapshot history limit."""
        # Fill history beyond limit
        for i in range(105):
            learning_dashboard.metrics_history.append({
                'snapshot_timestamp': datetime.now().isoformat(),
                'metrics': {'test': {'value': i}}
            })

        mock_metrics = {
            'new_metric': LearningMetric("New", 100.0, "count", "stable", "desc", "timestamp")
        }

        with patch.object(learning_dashboard, '_collect_all_metrics', return_value=mock_metrics):
            learning_dashboard.save_metrics_snapshot()

            # Should maintain limit of 100
            assert len(learning_dashboard.metrics_history) == 100

    def test_save_metrics_snapshot_error(self, learning_dashboard):
        """Test metrics snapshot saving with error."""
        with patch.object(learning_dashboard, '_collect_all_metrics', side_effect=Exception("Snapshot error")):
            result = learning_dashboard.save_metrics_snapshot()

            assert "Failed to save" in result
            assert "Snapshot error" in result


class TestCreateLearningDashboard:
    """Test the create_learning_dashboard factory function."""

    def test_create_learning_dashboard_with_vector_store(self):
        """Test factory function with provided VectorStore."""
        mock_context = Mock()
        mock_vector_store = Mock()

        dashboard = create_learning_dashboard(mock_context, mock_vector_store)

        assert isinstance(dashboard, LearningDashboard)
        assert dashboard.agent_context == mock_context
        assert dashboard.vector_store == mock_vector_store

    def test_create_learning_dashboard_without_vector_store(self):
        """Test factory function without VectorStore (should create default)."""
        mock_context = Mock()

        with patch('tools.learning_dashboard.VectorStore') as mock_vector_store_class:
            mock_instance = Mock()
            mock_vector_store_class.return_value = mock_instance

            dashboard = create_learning_dashboard(mock_context)

            assert isinstance(dashboard, LearningDashboard)
            assert dashboard.agent_context == mock_context
            assert dashboard.vector_store == mock_instance


class TestLearningDashboardIntegration:
    """Test integration scenarios for LearningDashboard."""

    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock AgentContext for testing."""
        mock_context = Mock()
        mock_context.search_memories.return_value = []
        mock_context.get_session_memories.return_value = []
        return mock_context

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStore for testing."""
        mock_store = Mock()
        mock_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 80,
            'embedding_available': True
        }
        return mock_store

    @pytest.fixture
    def comprehensive_mock_data(self):
        """Create comprehensive mock data for integration testing."""
        return {
            'vector_stats': {
                'total_memories': 500,
                'memories_with_embeddings': 400,
                'embedding_available': True
            },
            'pattern_memories': [
                {'content': 'pattern applied successfully', 'timestamp': datetime.now().isoformat()},
                {'content': 'pattern resolved issue effectively', 'timestamp': datetime.now().isoformat()},
                {'content': 'pattern failed to work properly', 'timestamp': datetime.now().isoformat()},
            ],
            'learning_memories': [
                {'content': {'type': 'error_resolution', 'confidence': 0.9}, 'timestamp': datetime.now().isoformat()},
                {'content': {'type': 'optimization', 'confidence': 0.8}, 'timestamp': datetime.now().isoformat()},
                {'content': {'learning_type': 'pattern', 'confidence': 0.7}, 'timestamp': datetime.now().isoformat()},
            ],
            'cross_session_memories': [
                {'content': 'cross-session pattern successful', 'timestamp': datetime.now().isoformat()},
                {'content': 'historical pattern effective', 'timestamp': datetime.now().isoformat()},
            ],
            'trigger_memories': [
                {'timestamp': datetime.now().isoformat()},
                {'timestamp': datetime.now().isoformat()},
            ],
            'session_memories': ['mem1', 'mem2', 'mem3', 'mem4', 'mem5']
        }

    def test_full_report_generation_integration(self, mock_agent_context, mock_vector_store, comprehensive_mock_data):
        """Test full report generation with comprehensive data."""
        # Setup mocks
        mock_vector_store.get_stats.return_value = comprehensive_mock_data['vector_stats']

        def mock_search_memories(tags=None, **kwargs):
            if 'pattern_application' in tags:
                return comprehensive_mock_data['pattern_memories']
            elif 'learning' in tags:
                return comprehensive_mock_data['learning_memories']
            elif 'cross_session' in tags:
                return comprehensive_mock_data['cross_session_memories']
            elif 'learning_trigger' in tags:
                return comprehensive_mock_data['trigger_memories']
            return []

        mock_agent_context.search_memories.side_effect = mock_search_memories
        mock_agent_context.get_session_memories.return_value = comprehensive_mock_data['session_memories']

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)
        report = dashboard.generate_comprehensive_report()

        # Verify comprehensive report structure
        assert isinstance(report, dict)
        assert 'report_timestamp' in report
        assert 'health_score' in report
        assert 'metrics' in report
        assert 'trends' in report
        assert 'alerts' in report
        assert 'insights' in report
        assert 'recommendations' in report
        assert 'summary' in report

        # Verify metrics are calculated
        metrics = report['metrics']
        assert len(metrics) > 5  # Should have multiple metric categories

        # Verify health score calculation
        health_score = report['health_score']
        assert isinstance(health_score, dict)
        assert 'score' in health_score
        assert 'status' in health_score

        # Verify summary contains key information
        summary = report['summary']
        assert isinstance(summary, dict)
        assert 'health_status' in summary
        assert 'metrics_tracked' in summary

    def test_dashboard_with_poor_metrics(self, mock_agent_context, mock_vector_store):
        """Test dashboard behavior with poor performance metrics."""
        # Setup poor performance data
        mock_vector_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 10,  # Very low coverage
            'embedding_available': False      # System down
        }

        mock_agent_context.search_memories.return_value = []  # No learning activity
        mock_agent_context.get_session_memories.return_value = []

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)
        report = dashboard.generate_comprehensive_report()

        # Should generate alerts for poor performance
        alerts = report['alerts']
        assert len(alerts) > 0

        # Health score should be low
        health_score = report['health_score']
        assert health_score['score'] < 50

        # Should have improvement recommendations
        recommendations = report['recommendations']
        assert len(recommendations) > 0

    def test_dashboard_with_excellent_metrics(self, mock_agent_context, mock_vector_store):
        """Test dashboard behavior with excellent performance metrics."""
        # Setup excellent performance data
        mock_vector_store.get_stats.return_value = {
            'total_memories': 1000,
            'memories_with_embeddings': 950,  # Excellent coverage
            'embedding_available': True
        }

        # Mock high activity and success
        excellent_time = datetime.now().isoformat()
        mock_agent_context.search_memories.return_value = [
            {'content': 'pattern applied successfully', 'timestamp': excellent_time},
            {'content': 'pattern resolved effectively', 'timestamp': excellent_time},
            {'content': 'pattern improved performance', 'timestamp': excellent_time},
        ] * 10  # Lots of successful activity

        mock_agent_context.get_session_memories.return_value = ['mem'] * 20

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)
        report = dashboard.generate_comprehensive_report()

        # Should have few or no alerts
        alerts = report['alerts']
        error_alerts = [a for a in alerts if a['level'] == 'error']
        assert len(error_alerts) == 0

        # Health score should be high
        health_score = report['health_score']
        assert health_score['score'] > 70

        # Should have positive insights
        insights = report['insights']
        positive_insights = [i for i in insights if i['type'] == 'positive']
        assert len(positive_insights) > 0


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock AgentContext for testing."""
        mock_context = Mock()
        mock_context.search_memories.return_value = []
        mock_context.get_session_memories.return_value = []
        return mock_context

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStore for testing."""
        mock_store = Mock()
        mock_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 80,
            'embedding_available': True
        }
        return mock_store

    def test_dashboard_with_malformed_memory_data(self, mock_agent_context, mock_vector_store):
        """Test dashboard handling of malformed memory data."""
        # Setup malformed data
        malformed_memories = [
            {'content': None, 'timestamp': 'invalid'},
            {'invalid_structure': True},
            {'content': {'malformed': 'data'}, 'timestamp': None},
            # Valid memory mixed in
            {'content': 'valid pattern success', 'timestamp': datetime.now().isoformat()}
        ]

        mock_agent_context.search_memories.return_value = malformed_memories
        mock_agent_context.get_session_memories.return_value = []

        mock_vector_store.get_stats.return_value = {
            'total_memories': 100,
            'memories_with_embeddings': 80,
            'embedding_available': True
        }

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)

        # Should not crash with malformed data
        report = dashboard.generate_comprehensive_report()
        assert isinstance(report, dict)
        assert 'error' not in report  # Should handle gracefully

    def test_dashboard_with_empty_data(self, mock_agent_context, mock_vector_store):
        """Test dashboard with completely empty data."""
        mock_agent_context.search_memories.return_value = []
        mock_agent_context.get_session_memories.return_value = []

        mock_vector_store.get_stats.return_value = {
            'total_memories': 0,
            'memories_with_embeddings': 0,
            'embedding_available': False
        }

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)
        report = dashboard.generate_comprehensive_report()

        # Should handle empty data gracefully
        assert isinstance(report, dict)
        assert 'metrics' in report
        assert 'health_score' in report

        # Health score should reflect lack of data
        health_score = report['health_score']
        assert health_score['score'] <= 50

    def test_dashboard_logging(self, mock_agent_context, mock_vector_store, caplog):
        """Test dashboard logging functionality."""
        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)

        with caplog.at_level(logging.INFO):
            dashboard.generate_comprehensive_report()

        # Should have logged initialization and report generation
        log_messages = [record.message for record in caplog.records]
        assert any("LearningDashboard initialized" in msg for msg in log_messages)

    def test_dashboard_with_vector_store_error(self, mock_agent_context):
        """Test dashboard when VectorStore operations fail."""
        mock_vector_store = Mock()
        mock_vector_store.get_stats.side_effect = Exception("VectorStore connection failed")

        dashboard = LearningDashboard(mock_agent_context, mock_vector_store)

        # Should handle VectorStore errors gracefully
        report = dashboard.generate_comprehensive_report()
        assert isinstance(report, dict)
        # Should still generate report despite VectorStore errors