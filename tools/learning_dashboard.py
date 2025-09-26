"""
Learning Observability Dashboard.

Provides comprehensive metrics and visualization for learning system effectiveness.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from shared.type_definitions.json import JSONValue
from collections import defaultdict, Counter
from dataclasses import dataclass

from agency_memory import VectorStore
from shared.agent_context import AgentContext

logger = logging.getLogger(__name__)


@dataclass
class LearningMetric:
    """Learning system metric."""
    name: str
    value: float
    unit: str
    trend: str  # 'up', 'down', 'stable'
    description: str
    timestamp: str


@dataclass
class LearningAlert:
    """Learning system alert."""
    level: str  # 'info', 'warning', 'error'
    message: str
    metric: str
    threshold: float
    current_value: float
    timestamp: str


class LearningDashboard:
    """
    Comprehensive learning observability dashboard.

    Tracks and visualizes:
    - Learning pattern accumulation rates
    - Pattern application success rates
    - VectorStore performance metrics
    - Cross-session learning effectiveness
    - Learning system health indicators
    """

    def __init__(self, agent_context: AgentContext, vector_store: Optional[VectorStore] = None):
        """
        Initialize learning dashboard.

        Args:
            agent_context: Agent context for memory access
            vector_store: Optional VectorStore for pattern analysis
        """
        self.agent_context = agent_context
        self.vector_store = vector_store or VectorStore()
        self.metrics_history = []
        self.alerts = []

        logger.info("LearningDashboard initialized")

    def generate_comprehensive_report(self) -> Dict[str, JSONValue]:
        """Generate comprehensive learning system report."""
        try:
            # Collect all metrics
            metrics = self._collect_all_metrics()

            # Generate alerts
            alerts = self._check_learning_alerts(metrics)

            # Calculate trends
            trends = self._calculate_trends(metrics)

            # Generate insights
            insights = self._generate_learning_insights(metrics, trends)

            # Create health score
            health_score = self._calculate_system_health(metrics, alerts)

            report = {
                "report_timestamp": datetime.now().isoformat(),
                "health_score": health_score,
                "metrics": metrics,
                "trends": trends,
                "alerts": [alert.__dict__ for alert in alerts],
                "insights": insights,
                "recommendations": self._generate_improvement_recommendations(metrics, alerts),
                "summary": self._create_executive_summary(health_score, metrics, alerts)
            }

            logger.info(f"Generated comprehensive learning report with {len(metrics)} metrics and {len(alerts)} alerts")
            return report

        except Exception as e:
            logger.error(f"Error generating learning report: {e}")
            return {
                "error": f"Failed to generate learning report: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _collect_all_metrics(self) -> Dict[str, LearningMetric]:
        """Collect all learning system metrics."""
        metrics = {}

        try:
            # VectorStore metrics
            vector_metrics = self._collect_vector_store_metrics()
            metrics.update(vector_metrics)

            # Pattern application metrics
            application_metrics = self._collect_pattern_application_metrics()
            metrics.update(application_metrics)

            # Learning progression metrics
            progression_metrics = self._collect_learning_progression_metrics()
            metrics.update(progression_metrics)

            # Cross-session effectiveness metrics
            cross_session_metrics = self._collect_cross_session_metrics()
            metrics.update(cross_session_metrics)

            # System performance metrics
            performance_metrics = self._collect_performance_metrics()
            metrics.update(performance_metrics)

        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")

        return metrics

    def _collect_vector_store_metrics(self) -> Dict[str, LearningMetric]:
        """Collect VectorStore performance metrics."""
        metrics = {}

        try:
            # Get VectorStore stats
            vector_stats = self.vector_store.get_stats()

            # Total memories metric
            metrics['total_memories'] = LearningMetric(
                name="Total Memories",
                value=vector_stats.get('total_memories', 0),
                unit="count",
                trend=self._calculate_metric_trend('total_memories', vector_stats.get('total_memories', 0)),
                description="Total number of memories stored in VectorStore",
                timestamp=datetime.now().isoformat()
            )

            # Memories with embeddings metric
            metrics['memories_with_embeddings'] = LearningMetric(
                name="Memories with Embeddings",
                value=vector_stats.get('memories_with_embeddings', 0),
                unit="count",
                trend=self._calculate_metric_trend('memories_with_embeddings', vector_stats.get('memories_with_embeddings', 0)),
                description="Number of memories with semantic embeddings",
                timestamp=datetime.now().isoformat()
            )

            # Embedding coverage rate
            total = vector_stats.get('total_memories', 0)
            with_embeddings = vector_stats.get('memories_with_embeddings', 0)
            coverage_rate = (with_embeddings / total * 100) if total > 0 else 0

            metrics['embedding_coverage'] = LearningMetric(
                name="Embedding Coverage",
                value=coverage_rate,
                unit="percent",
                trend=self._calculate_metric_trend('embedding_coverage', coverage_rate),
                description="Percentage of memories with semantic embeddings",
                timestamp=datetime.now().isoformat()
            )

            # Embedding provider status
            embedding_available = vector_stats.get('embedding_available', False)
            metrics['embedding_status'] = LearningMetric(
                name="Embedding System Status",
                value=1.0 if embedding_available else 0.0,
                unit="boolean",
                trend="stable",
                description="Status of embedding generation system",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error collecting VectorStore metrics: {e}")

        return metrics

    def _collect_pattern_application_metrics(self) -> Dict[str, LearningMetric]:
        """Collect pattern application effectiveness metrics."""
        metrics = {}

        try:
            # Search for pattern application records
            application_memories = self.agent_context.search_memories(
                tags=["pattern_application", "learning_applied"], include_session=False
            )

            # Calculate application rate
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_applications = [
                m for m in application_memories
                if self._is_recent_memory(m, recent_cutoff)
            ]

            metrics['pattern_application_rate'] = LearningMetric(
                name="Pattern Application Rate",
                value=len(recent_applications),
                unit="per_week",
                trend=self._calculate_metric_trend('pattern_application_rate', len(recent_applications)),
                description="Number of patterns applied per week",
                timestamp=datetime.now().isoformat()
            )

            # Calculate success rate
            successful_applications = [
                m for m in recent_applications
                if self._is_successful_application(m)
            ]

            success_rate = (len(successful_applications) / len(recent_applications) * 100) if recent_applications else 0

            metrics['pattern_success_rate'] = LearningMetric(
                name="Pattern Success Rate",
                value=success_rate,
                unit="percent",
                trend=self._calculate_metric_trend('pattern_success_rate', success_rate),
                description="Success rate of applied patterns",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error collecting pattern application metrics: {e}")

        return metrics

    def _collect_learning_progression_metrics(self) -> Dict[str, LearningMetric]:
        """Collect learning progression and accumulation metrics."""
        metrics = {}

        try:
            # Search for learning objects
            learning_memories = self.agent_context.search_memories(
                tags=["learning", "pattern", "insight"], include_session=False
            )

            # Calculate learning accumulation rate
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_learnings = [
                m for m in learning_memories
                if self._is_recent_memory(m, recent_cutoff)
            ]

            metrics['learning_accumulation_rate'] = LearningMetric(
                name="Learning Accumulation Rate",
                value=len(recent_learnings),
                unit="per_month",
                trend=self._calculate_metric_trend('learning_accumulation_rate', len(recent_learnings)),
                description="New learnings acquired per month",
                timestamp=datetime.now().isoformat()
            )

            # Calculate learning diversity
            learning_types = self._extract_learning_types(learning_memories)
            diversity_score = len(learning_types)

            metrics['learning_diversity'] = LearningMetric(
                name="Learning Diversity",
                value=diversity_score,
                unit="types",
                trend=self._calculate_metric_trend('learning_diversity', diversity_score),
                description="Number of different learning types accumulated",
                timestamp=datetime.now().isoformat()
            )

            # Calculate average learning confidence
            confidences = self._extract_learning_confidences(learning_memories)
            avg_confidence = sum(confidences) / len(confidences) * 100 if confidences else 0

            metrics['average_learning_confidence'] = LearningMetric(
                name="Average Learning Confidence",
                value=avg_confidence,
                unit="percent",
                trend=self._calculate_metric_trend('average_learning_confidence', avg_confidence),
                description="Average confidence score of stored learnings",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error collecting learning progression metrics: {e}")

        return metrics

    def _collect_cross_session_metrics(self) -> Dict[str, LearningMetric]:
        """Collect cross-session learning effectiveness metrics."""
        metrics = {}

        try:
            # Search for cross-session application records
            cross_session_memories = self.agent_context.search_memories(
                tags=["cross_session", "historical_pattern"], include_session=False
            )

            # Calculate cross-session application rate
            recent_cutoff = datetime.now() - timedelta(days=14)
            recent_cross_sessions = [
                m for m in cross_session_memories
                if self._is_recent_memory(m, recent_cutoff)
            ]

            metrics['cross_session_application_rate'] = LearningMetric(
                name="Cross-Session Application Rate",
                value=len(recent_cross_sessions),
                unit="per_two_weeks",
                trend=self._calculate_metric_trend('cross_session_application_rate', len(recent_cross_sessions)),
                description="Cross-session pattern applications per two weeks",
                timestamp=datetime.now().isoformat()
            )

            # Calculate knowledge retention score
            # This would measure how well patterns persist and remain useful
            retention_score = self._calculate_knowledge_retention(cross_session_memories)

            metrics['knowledge_retention'] = LearningMetric(
                name="Knowledge Retention Score",
                value=retention_score,
                unit="score",
                trend=self._calculate_metric_trend('knowledge_retention', retention_score),
                description="How well knowledge persists across sessions",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error collecting cross-session metrics: {e}")

        return metrics

    def _collect_performance_metrics(self) -> Dict[str, LearningMetric]:
        """Collect learning system performance metrics."""
        metrics = {}

        try:
            # Memory utilization (simplified)
            total_memories = len(self.agent_context.get_session_memories())

            metrics['memory_utilization'] = LearningMetric(
                name="Memory Utilization",
                value=total_memories,
                unit="count",
                trend=self._calculate_metric_trend('memory_utilization', total_memories),
                description="Total memories in current session",
                timestamp=datetime.now().isoformat()
            )

            # Learning trigger frequency
            learning_triggers = self._count_learning_triggers()

            metrics['learning_trigger_frequency'] = LearningMetric(
                name="Learning Trigger Frequency",
                value=learning_triggers,
                unit="per_day",
                trend=self._calculate_metric_trend('learning_trigger_frequency', learning_triggers),
                description="Frequency of automatic learning triggers",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.warning(f"Error collecting performance metrics: {e}")

        return metrics

    def _calculate_metric_trend(self, metric_name: str, current_value: float) -> str:
        """Calculate trend for a metric based on history."""
        try:
            # Look for historical values of this metric
            historical_values = []
            for record in self.metrics_history[-10:]:  # Last 10 records
                if metric_name in record and 'value' in record[metric_name]:
                    historical_values.append(record[metric_name]['value'])

            if len(historical_values) < 2:
                return "stable"

            # Simple trend calculation
            recent_avg = sum(historical_values[-3:]) / min(3, len(historical_values))
            if current_value > recent_avg * 1.1:
                return "up"
            elif current_value < recent_avg * 0.9:
                return "down"
            else:
                return "stable"

        except Exception:
            return "stable"

    def _is_recent_memory(self, memory: Dict[str, JSONValue], cutoff_time: datetime) -> bool:
        """Check if memory is recent based on timestamp."""
        try:
            timestamp_str = memory.get('timestamp', '')
            if timestamp_str:
                memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return memory_time >= cutoff_time
        except Exception:
            pass
        return False

    def _is_successful_application(self, memory: Dict[str, JSONValue]) -> bool:
        """Check if pattern application was successful."""
        content = str(memory.get('content', '')).lower()
        success_indicators = ['success', 'resolved', 'improved', 'effective', 'working']
        return any(indicator in content for indicator in success_indicators)

    def _extract_learning_types(self, learning_memories: List[dict[str, JSONValue]]) -> List[str]:
        """Extract unique learning types from memories."""
        types = set()
        for memory in learning_memories:
            content = memory.get('content', {})
            if isinstance(content, dict):
                learning_type = content.get('type', content.get('learning_type', 'unknown'))
                types.add(learning_type)
            else:
                # Try to extract type from text content
                content_str = str(content).lower()
                if 'error' in content_str:
                    types.add('error_resolution')
                elif 'optimization' in content_str:
                    types.add('optimization')
                elif 'pattern' in content_str:
                    types.add('pattern')
        return list(types)

    def _extract_learning_confidences(self, learning_memories: List[dict[str, JSONValue]]) -> List[float]:
        """Extract confidence scores from learning memories."""
        confidences = []
        for memory in learning_memories:
            content = memory.get('content', {})
            if isinstance(content, dict):
                confidence = content.get('confidence', content.get('overall_confidence', 0.5))
                if isinstance(confidence, (int, float)):
                    confidences.append(float(confidence))
        return confidences

    def _calculate_knowledge_retention(self, cross_session_memories: List[dict[str, JSONValue]]) -> float:
        """Calculate knowledge retention score."""
        try:
            if not cross_session_memories:
                return 0.0

            # Simple retention calculation based on successful applications over time
            successful_applications = [
                m for m in cross_session_memories
                if self._is_successful_application(m)
            ]

            retention_score = len(successful_applications) / len(cross_session_memories) * 100
            return min(100.0, retention_score)

        except Exception:
            return 0.0

    def _count_learning_triggers(self) -> int:
        """Count learning triggers in recent period."""
        try:
            trigger_memories = self.agent_context.search_memories(
                tags=["learning_trigger", "automatic_learning"], include_session=False
            )

            # Count triggers in last day
            recent_cutoff = datetime.now() - timedelta(days=1)
            recent_triggers = [
                m for m in trigger_memories
                if self._is_recent_memory(m, recent_cutoff)
            ]

            return len(recent_triggers)

        except Exception:
            return 0

    def _check_learning_alerts(self, metrics: Dict[str, LearningMetric]) -> List[LearningAlert]:
        """Check for learning system alerts based on metrics."""
        alerts = []

        try:
            # Check embedding coverage
            if 'embedding_coverage' in metrics:
                coverage = metrics['embedding_coverage'].value
                if coverage < 50:
                    alerts.append(LearningAlert(
                        level="warning",
                        message="Low embedding coverage may reduce learning effectiveness",
                        metric="embedding_coverage",
                        threshold=50.0,
                        current_value=coverage,
                        timestamp=datetime.now().isoformat()
                    ))

            # Check pattern success rate
            if 'pattern_success_rate' in metrics:
                success_rate = metrics['pattern_success_rate'].value
                if success_rate < 60:
                    alerts.append(LearningAlert(
                        level="warning",
                        message="Pattern application success rate is below optimal",
                        metric="pattern_success_rate",
                        threshold=60.0,
                        current_value=success_rate,
                        timestamp=datetime.now().isoformat()
                    ))

            # Check learning accumulation
            if 'learning_accumulation_rate' in metrics:
                accumulation = metrics['learning_accumulation_rate'].value
                if accumulation < 5:
                    alerts.append(LearningAlert(
                        level="info",
                        message="Learning accumulation rate is low - consider more active learning",
                        metric="learning_accumulation_rate",
                        threshold=5.0,
                        current_value=accumulation,
                        timestamp=datetime.now().isoformat()
                    ))

            # Check embedding system status
            if 'embedding_status' in metrics:
                status = metrics['embedding_status'].value
                if status < 1.0:
                    alerts.append(LearningAlert(
                        level="error",
                        message="Embedding system is not available - semantic search disabled",
                        metric="embedding_status",
                        threshold=1.0,
                        current_value=status,
                        timestamp=datetime.now().isoformat()
                    ))

        except Exception as e:
            logger.warning(f"Error checking learning alerts: {e}")

        return alerts

    def _calculate_trends(self, metrics: Dict[str, LearningMetric]) -> Dict[str, str]:
        """Calculate overall trends for metric categories."""
        trends = {}

        try:
            # VectorStore trends
            vector_trends = [metrics[key].trend for key in metrics if key.startswith('embedding') or 'memories' in key]
            trends['vector_store'] = self._aggregate_trends(vector_trends)

            # Pattern application trends
            pattern_trends = [metrics[key].trend for key in metrics if 'pattern' in key]
            trends['pattern_application'] = self._aggregate_trends(pattern_trends)

            # Learning progression trends
            learning_trends = [metrics[key].trend for key in metrics if 'learning' in key]
            trends['learning_progression'] = self._aggregate_trends(learning_trends)

        except Exception as e:
            logger.warning(f"Error calculating trends: {e}")

        return trends

    def _aggregate_trends(self, trend_list: List[str]) -> str:
        """Aggregate individual trends into overall trend."""
        if not trend_list:
            return "stable"

        trend_counts = Counter(trend_list)

        if trend_counts['up'] > trend_counts['down']:
            return "improving"
        elif trend_counts['down'] > trend_counts['up']:
            return "declining"
        else:
            return "stable"

    def _generate_learning_insights(self, metrics: Dict[str, LearningMetric], trends: Dict[str, str]) -> List[Dict[str, JSONValue]]:
        """Generate insights based on metrics and trends."""
        insights = []

        try:
            # VectorStore insights
            if 'embedding_coverage' in metrics:
                coverage = metrics['embedding_coverage'].value
                if coverage > 80:
                    insights.append({
                        'category': 'vector_store',
                        'type': 'positive',
                        'message': f'Excellent embedding coverage ({coverage:.1f}%) enables effective semantic search',
                        'recommendation': 'Continue maintaining high embedding coverage'
                    })
                elif coverage < 50:
                    insights.append({
                        'category': 'vector_store',
                        'type': 'improvement',
                        'message': f'Low embedding coverage ({coverage:.1f}%) limits learning effectiveness',
                        'recommendation': 'Focus on improving embedding generation and storage'
                    })

            # Pattern application insights
            if 'pattern_success_rate' in metrics and 'pattern_application_rate' in metrics:
                success_rate = metrics['pattern_success_rate'].value
                application_rate = metrics['pattern_application_rate'].value

                if success_rate > 80 and application_rate > 5:
                    insights.append({
                        'category': 'pattern_application',
                        'type': 'positive',
                        'message': f'High pattern success rate ({success_rate:.1f}%) with good application frequency',
                        'recommendation': 'Learning system is performing well - maintain current approach'
                    })

            # Learning progression insights
            if 'learning_diversity' in metrics:
                diversity = metrics['learning_diversity'].value
                if diversity > 5:
                    insights.append({
                        'category': 'learning_progression',
                        'type': 'positive',
                        'message': f'Good learning diversity ({diversity} types) indicates comprehensive learning',
                        'recommendation': 'Continue exploring diverse learning opportunities'
                    })

            # Trend-based insights
            for category, trend in trends.items():
                if trend == "improving":
                    insights.append({
                        'category': category,
                        'type': 'positive',
                        'message': f'{category.replace("_", " ").title()} metrics are improving',
                        'recommendation': 'Current strategies are effective - continue and possibly expand'
                    })
                elif trend == "declining":
                    insights.append({
                        'category': category,
                        'type': 'concern',
                        'message': f'{category.replace("_", " ").title()} metrics are declining',
                        'recommendation': 'Review and adjust strategies for this area'
                    })

        except Exception as e:
            logger.warning(f"Error generating insights: {e}")

        return insights

    def _calculate_system_health(self, metrics: Dict[str, LearningMetric], alerts: List[LearningAlert]) -> Dict[str, JSONValue]:
        """Calculate overall learning system health score."""
        try:
            # Base health score calculation
            health_factors = []

            # VectorStore health
            if 'embedding_coverage' in metrics:
                coverage = metrics['embedding_coverage'].value
                health_factors.append(min(100, coverage))

            # Pattern effectiveness health
            if 'pattern_success_rate' in metrics:
                success_rate = metrics['pattern_success_rate'].value
                health_factors.append(success_rate)

            # Learning progression health
            if 'learning_accumulation_rate' in metrics:
                accumulation = metrics['learning_accumulation_rate'].value
                # Normalize to 0-100 scale
                health_factors.append(min(100, accumulation * 10))

            # Alert penalty
            error_alerts = len([a for a in alerts if a.level == 'error'])
            warning_alerts = len([a for a in alerts if a.level == 'warning'])
            alert_penalty = error_alerts * 20 + warning_alerts * 10

            # Calculate overall score
            if health_factors:
                base_score = sum(health_factors) / len(health_factors)
                final_score = max(0, base_score - alert_penalty)
            else:
                final_score = 50  # Neutral score if no metrics

            # Determine status
            if final_score >= 80:
                status = "excellent"
            elif final_score >= 60:
                status = "good"
            elif final_score >= 40:
                status = "fair"
            else:
                status = "poor"

            return {
                'score': final_score,
                'status': status,
                'components': {
                    'base_score': sum(health_factors) / len(health_factors) if health_factors else 50,
                    'alert_penalty': alert_penalty,
                    'factor_count': len(health_factors)
                },
                'calculation_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating system health: {e}")
            return {
                'score': 0,
                'status': 'unknown',
                'error': str(e),
                'calculation_timestamp': datetime.now().isoformat()
            }

    def _generate_improvement_recommendations(self, metrics: Dict[str, LearningMetric], alerts: List[LearningAlert]) -> List[Dict[str, JSONValue]]:
        """Generate specific recommendations for improving learning system."""
        recommendations = []

        try:
            # Address critical alerts first
            error_alerts = [a for a in alerts if a.level == 'error']
            for alert in error_alerts:
                recommendations.append({
                    'priority': 'high',
                    'category': 'alert_resolution',
                    'title': f'Resolve {alert.metric} Issue',
                    'description': alert.message,
                    'specific_actions': self._get_alert_resolution_actions(alert)
                })

            # Metric-based improvements
            if 'embedding_coverage' in metrics and metrics['embedding_coverage'].value < 70:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'vector_store',
                    'title': 'Improve Embedding Coverage',
                    'description': 'Increase percentage of memories with semantic embeddings',
                    'specific_actions': [
                        'Run VectorStore optimization process',
                        'Check embedding provider configuration',
                        'Implement automatic embedding generation for new memories'
                    ]
                })

            if 'pattern_application_rate' in metrics and metrics['pattern_application_rate'].value < 3:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'pattern_application',
                    'title': 'Increase Pattern Application',
                    'description': 'Apply learned patterns more frequently',
                    'specific_actions': [
                        'Review pattern matching thresholds',
                        'Implement proactive pattern suggestion',
                        'Add automatic pattern application triggers'
                    ]
                })

            # General improvements
            recommendations.append({
                'priority': 'low',
                'category': 'monitoring',
                'title': 'Enhance Learning Monitoring',
                'description': 'Improve observability and tracking of learning effectiveness',
                'specific_actions': [
                    'Implement learning effectiveness feedback loops',
                    'Add more granular metrics collection',
                    'Create automated learning reports'
                ]
            })

        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")

        return recommendations

    def _get_alert_resolution_actions(self, alert: LearningAlert) -> List[str]:
        """Get specific actions to resolve an alert."""
        if alert.metric == 'embedding_status':
            return [
                'Check embedding provider availability',
                'Verify API keys and configuration',
                'Restart embedding service if needed',
                'Consider alternative embedding providers'
            ]
        elif alert.metric == 'pattern_success_rate':
            return [
                'Review failed pattern applications',
                'Improve pattern matching algorithms',
                'Update pattern confidence thresholds',
                'Retrain pattern selection models'
            ]
        else:
            return [
                f'Investigate {alert.metric} metric',
                'Check system logs for related issues',
                'Review configuration settings',
                'Consider metric threshold adjustments'
            ]

    def _create_executive_summary(self, health_score: Dict[str, JSONValue], metrics: Dict[str, LearningMetric], alerts: List[LearningAlert]) -> Dict[str, JSONValue]:
        """Create executive summary of learning system status."""
        try:
            # Key statistics
            total_metrics = len(metrics)
            positive_trends = len([m for m in metrics.values() if m.trend == 'up'])
            negative_trends = len([m for m in metrics.values() if m.trend == 'down'])

            # Alert summary
            critical_issues = len([a for a in alerts if a.level == 'error'])
            warnings = len([a for a in alerts if a.level == 'warning'])

            # Key highlights
            highlights = []
            if health_score['score'] >= 80:
                highlights.append("Learning system is performing excellently")
            elif health_score['score'] >= 60:
                highlights.append("Learning system is performing well with room for improvement")
            else:
                highlights.append("Learning system needs attention and optimization")

            if positive_trends > negative_trends:
                highlights.append(f"Positive trends in {positive_trends} metrics")
            elif negative_trends > positive_trends:
                highlights.append(f"Concerning trends in {negative_trends} metrics")

            if critical_issues == 0:
                highlights.append("No critical issues detected")
            else:
                highlights.append(f"{critical_issues} critical issue(s) require immediate attention")

            return {
                'health_status': health_score['status'],
                'health_score': health_score['score'],
                'metrics_tracked': total_metrics,
                'positive_trends': positive_trends,
                'negative_trends': negative_trends,
                'critical_issues': critical_issues,
                'warnings': warnings,
                'key_highlights': highlights,
                'overall_assessment': self._get_overall_assessment(health_score['score'], critical_issues),
                'summary_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating executive summary: {e}")
            return {
                'error': str(e),
                'summary_timestamp': datetime.now().isoformat()
            }

    def _get_overall_assessment(self, health_score: float, critical_issues: int) -> str:
        """Get overall assessment based on health score and issues."""
        if critical_issues > 0:
            return "Requires immediate attention due to critical issues"
        elif health_score >= 80:
            return "Learning system is healthy and performing optimally"
        elif health_score >= 60:
            return "Learning system is stable with opportunities for optimization"
        elif health_score >= 40:
            return "Learning system needs improvement to reach optimal performance"
        else:
            return "Learning system requires significant optimization and attention"

    def save_metrics_snapshot(self) -> str:
        """Save current metrics as historical snapshot."""
        try:
            # Collect current metrics
            current_metrics = self._collect_all_metrics()

            # Convert to serializable format
            metrics_snapshot = {}
            for name, metric in current_metrics.items():
                metrics_snapshot[name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'trend': metric.trend,
                    'timestamp': metric.timestamp
                }

            # Add to history
            self.metrics_history.append({
                'snapshot_timestamp': datetime.now().isoformat(),
                'metrics': metrics_snapshot
            })

            # Keep only recent history (last 100 snapshots)
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]

            logger.info(f"Saved metrics snapshot with {len(current_metrics)} metrics")
            return f"Metrics snapshot saved with {len(current_metrics)} metrics"

        except Exception as e:
            logger.error(f"Error saving metrics snapshot: {e}")
            return f"Failed to save metrics snapshot: {str(e)}"


def create_learning_dashboard(agent_context: AgentContext, vector_store: Optional[VectorStore] = None) -> LearningDashboard:
    """
    Factory function to create a LearningDashboard.

    Args:
        agent_context: Agent context for memory access
        vector_store: Optional VectorStore for pattern analysis

    Returns:
        Configured LearningDashboard instance
    """
    return LearningDashboard(agent_context, vector_store)