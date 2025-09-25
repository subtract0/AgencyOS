"""Enhanced telemetry aggregator with time-series analysis capabilities.

This module extends the basic telemetry aggregator with:
- Time-series analysis for trend detection
- Correlation analysis between different metrics
- Predictive indicators for proactive responses
- Historical data comparison and anomaly detection
"""

from __future__ import annotations

import json
import numpy as np
import os
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from scipy import stats
from sklearn.linear_model import LinearRegression

from tools.telemetry.aggregator import aggregate, list_events, _parse_since, _iso_now, _telemetry_dir


@dataclass
class TimeSeriesPoint:
    """A single point in a time series."""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Results of trend analysis for a metric."""
    metric_name: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable', 'volatile'
    slope: float  # Rate of change
    r_squared: float  # Correlation coefficient
    confidence: float  # Statistical confidence (0.0 to 1.0)
    volatility: float  # Standard deviation of changes
    prediction_24h: Optional[float]  # Predicted value in 24 hours
    significance: str  # 'low', 'medium', 'high'


@dataclass
class CorrelationResult:
    """Results of correlation analysis between metrics."""
    metric1: str
    metric2: str
    correlation: float  # Pearson correlation coefficient
    p_value: float  # Statistical significance
    lag: int  # Time lag in minutes where correlation is strongest
    strength: str  # 'weak', 'moderate', 'strong'
    interpretation: str  # Human-readable interpretation


@dataclass
class AnomalyDetection:
    """Results of anomaly detection analysis."""
    metric_name: str
    current_value: float
    expected_value: float
    deviation_score: float  # Standard deviations from expected
    is_anomaly: bool
    severity: str  # 'low', 'medium', 'high'
    historical_context: Dict[str, Any]


class EnhancedTelemetryAggregator:
    """Enhanced telemetry aggregator with time-series analysis."""

    def __init__(self, telemetry_dir: Optional[str] = None, history_retention_hours: int = 168):
        """Initialize the enhanced aggregator.

        Args:
            telemetry_dir: Optional custom telemetry directory
            history_retention_hours: Hours of historical data to retain (default: 7 days)
        """
        self.telemetry_dir = telemetry_dir
        self.history_retention_hours = history_retention_hours

        # Time series storage
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.correlation_cache: Dict[Tuple[str, str], CorrelationResult] = {}
        self.trend_cache: Dict[str, TrendAnalysis] = {}

        # Configuration
        self.trend_confidence_threshold = 0.7
        self.anomaly_threshold = 2.0  # Standard deviations
        self.correlation_threshold = 0.5

        # Initialize with historical data
        self._load_historical_data()

    def _load_historical_data(self) -> None:
        """Load historical telemetry data to build time series."""
        try:
            # Load data from the last retention period
            since = f"{self.history_retention_hours}h"
            events = list_events(since=since, telemetry_dir=self.telemetry_dir, limit=10000)

            # Build time series from events
            for event in events:
                self._process_event_for_timeseries(event)

        except Exception as e:
            # Log error but continue - aggregator should work without historical data
            pass

    def _process_event_for_timeseries(self, event: Dict[str, Any]) -> None:
        """Process a single event to extract time series data."""
        try:
            # Parse timestamp
            ts_str = event.get('ts', '')
            if not ts_str:
                return

            # Handle different timestamp formats
            if ts_str.endswith('Z'):
                ts_str = ts_str[:-1] + '+00:00'
            timestamp = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)

            # Extract metrics based on event type
            event_type = event.get('type', '')

            if event_type == 'task_finished':
                # Extract task duration, cost, and usage metrics
                usage = event.get('usage', {})
                if usage:
                    tokens = usage.get('total_tokens', 0)
                    if tokens > 0:
                        self.metric_history['total_tokens'].append(
                            TimeSeriesPoint(timestamp, float(tokens), {'event_id': event.get('id')})
                        )

                # Extract cost if available
                model = event.get('model', '')
                if model and usage:
                    # Simplified cost estimation
                    cost = self._estimate_event_cost(usage, model)
                    if cost > 0:
                        self.metric_history['cost_per_task'].append(
                            TimeSeriesPoint(timestamp, cost, {'model': model})
                        )

                # Extract duration
                duration = event.get('duration_s')
                if duration is not None:
                    self.metric_history['task_duration'].append(
                        TimeSeriesPoint(timestamp, float(duration), {'agent': event.get('agent')})
                    )

                # Extract status for error rate calculation
                status = event.get('status', '').lower()
                error_value = 1.0 if status == 'failed' else 0.0
                self.metric_history['error_indicator'].append(
                    TimeSeriesPoint(timestamp, error_value, {'status': status})
                )

            elif event_type == 'heartbeat':
                # Extract system utilization metrics if available
                # This would depend on what heartbeat events contain
                pass

        except Exception as e:
            # Skip invalid events
            pass

    def _estimate_event_cost(self, usage: Dict[str, Any], model: str) -> float:
        """Estimate cost for a single event."""
        # Simple cost estimation - this could be enhanced with real pricing data
        tokens = usage.get('total_tokens', 0)
        if 'gpt-4' in model.lower():
            return tokens * 0.00006  # Rough estimate
        elif 'gpt-3.5' in model.lower():
            return tokens * 0.000002
        elif 'claude' in model.lower():
            return tokens * 0.000008
        return tokens * 0.00001  # Default rate

    def enhanced_aggregate(self, since: str = "1h", include_timeseries: bool = True) -> Dict[str, Any]:
        """Enhanced aggregation with time-series analysis.

        Args:
            since: Time window for analysis
            include_timeseries: Whether to include detailed time-series analysis

        Returns:
            Enhanced aggregation results with time-series insights
        """
        # Get base aggregation
        base_result = aggregate(since=since, telemetry_dir=self.telemetry_dir)

        if not include_timeseries:
            return base_result

        # Add time-series analysis
        since_dt = _parse_since(since)
        current_time = _iso_now()

        # Update time series with current telemetry data
        self._update_timeseries_from_aggregation(base_result, current_time)

        # Perform time-series analysis
        trends = self._analyze_trends(since_dt, current_time)
        correlations = self._analyze_correlations(since_dt, current_time)
        anomalies = self._detect_anomalies(since_dt, current_time)
        predictions = self._generate_predictions()

        # Enhance base result
        enhanced_result = base_result.copy()
        enhanced_result.update({
            'timeseries_analysis': {
                'trends': [self._trend_to_dict(trend) for trend in trends],
                'correlations': [self._correlation_to_dict(corr) for corr in correlations],
                'anomalies': [self._anomaly_to_dict(anomaly) for anomaly in anomalies],
                'predictions': predictions,
                'data_quality': self._assess_data_quality(),
                'analysis_timestamp': current_time.isoformat()
            }
        })

        return enhanced_result

    def _update_timeseries_from_aggregation(self, aggregation: Dict[str, Any], timestamp: datetime) -> None:
        """Update time series with current aggregation data."""
        try:
            # Extract key metrics from current aggregation
            resources = aggregation.get('resources', {})
            costs = aggregation.get('costs', {})
            bottlenecks = aggregation.get('bottlenecks', {})
            results = aggregation.get('recent_results', {})

            # Update resource utilization metrics
            if 'utilization' in resources and resources['utilization'] is not None:
                self.metric_history['utilization'].append(
                    TimeSeriesPoint(timestamp, float(resources['utilization']))
                )

            # Update running tasks count
            running_count = resources.get('running', 0)
            self.metric_history['running_tasks'].append(
                TimeSeriesPoint(timestamp, float(running_count))
            )

            # Update cost metrics
            total_cost = costs.get('total_usd', 0)
            if total_cost > 0:
                self.metric_history['total_cost'].append(
                    TimeSeriesPoint(timestamp, float(total_cost))
                )

            # Update error rate
            error_rate = bottlenecks.get('error_rate', 0)
            self.metric_history['error_rate'].append(
                TimeSeriesPoint(timestamp, float(error_rate))
            )

            # Update task completion metrics
            total_tasks = sum(results.values())
            if total_tasks > 0:
                success_rate = results.get('success', 0) / total_tasks
                self.metric_history['success_rate'].append(
                    TimeSeriesPoint(timestamp, float(success_rate))
                )

        except Exception as e:
            # Continue without time-series update if there's an error
            pass

    def _analyze_trends(self, since_dt: datetime, current_time: datetime) -> List[TrendAnalysis]:
        """Analyze trends in time series data."""
        trends = []

        for metric_name, points in self.metric_history.items():
            if len(points) < 5:  # Need minimum data points for trend analysis
                continue

            try:
                # Filter points to the analysis window
                filtered_points = [
                    p for p in points
                    if isinstance(p, TimeSeriesPoint) and since_dt <= p.timestamp <= current_time
                ]

                if len(filtered_points) < 3:
                    continue

                # Prepare data for regression
                timestamps = [(p.timestamp - since_dt).total_seconds() for p in filtered_points]
                values = [p.value for p in filtered_points]

                if not timestamps or not values or len(set(values)) == 1:
                    continue

                # Perform linear regression
                X = np.array(timestamps).reshape(-1, 1)
                y = np.array(values)

                model = LinearRegression()
                model.fit(X, y)

                slope = model.coef_[0]
                r_squared = model.score(X, y)

                # Calculate volatility
                if len(values) > 1:
                    volatility = np.std(np.diff(values))
                else:
                    volatility = 0.0

                # Determine trend direction
                slope_threshold = np.std(values) * 0.01  # 1% of standard deviation
                if abs(slope) < slope_threshold:
                    direction = 'stable'
                elif slope > 0:
                    direction = 'increasing'
                else:
                    direction = 'decreasing'

                # Determine significance
                if r_squared > 0.8 and abs(slope) > slope_threshold:
                    significance = 'high'
                elif r_squared > 0.5:
                    significance = 'medium'
                else:
                    significance = 'low'

                # Predict 24h ahead
                prediction_24h = None
                if r_squared > 0.5:  # Only predict if trend is reliable
                    future_seconds = 24 * 3600  # 24 hours
                    last_timestamp = timestamps[-1]
                    prediction_24h = model.predict([[last_timestamp + future_seconds]])[0]

                trend = TrendAnalysis(
                    metric_name=metric_name,
                    trend_direction=direction,
                    slope=slope,
                    r_squared=r_squared,
                    confidence=min(r_squared, 1.0),
                    volatility=volatility,
                    prediction_24h=prediction_24h,
                    significance=significance
                )

                trends.append(trend)

            except Exception as e:
                # Skip this metric if analysis fails
                continue

        return trends

    def _analyze_correlations(self, since_dt: datetime, current_time: datetime) -> List[CorrelationResult]:
        """Analyze correlations between different metrics."""
        correlations = []
        metric_names = list(self.metric_history.keys())

        # Only analyze correlations if we have multiple metrics
        if len(metric_names) < 2:
            return correlations

        for i, metric1 in enumerate(metric_names):
            for metric2 in metric_names[i+1:]:
                try:
                    correlation = self._calculate_correlation(metric1, metric2, since_dt, current_time)
                    if correlation and abs(correlation.correlation) > self.correlation_threshold:
                        correlations.append(correlation)
                except Exception:
                    continue

        return correlations

    def _calculate_correlation(self, metric1: str, metric2: str, since_dt: datetime, current_time: datetime) -> Optional[CorrelationResult]:
        """Calculate correlation between two metrics."""
        try:
            # Get time series for both metrics
            series1 = [p for p in self.metric_history[metric1] if isinstance(p, TimeSeriesPoint) and since_dt <= p.timestamp <= current_time]
            series2 = [p for p in self.metric_history[metric2] if isinstance(p, TimeSeriesPoint) and since_dt <= p.timestamp <= current_time]

            if len(series1) < 5 or len(series2) < 5:
                return None

            # Align time series by timestamp (simple approach - could be improved)
            values1, values2 = self._align_timeseries(series1, series2)

            if len(values1) < 3 or len(values2) < 3:
                return None

            # Calculate Pearson correlation
            correlation, p_value = stats.pearsonr(values1, values2)

            # Determine strength
            abs_corr = abs(correlation)
            if abs_corr > 0.8:
                strength = 'strong'
            elif abs_corr > 0.5:
                strength = 'moderate'
            else:
                strength = 'weak'

            # Generate interpretation
            if correlation > 0.7:
                interpretation = f"{metric1} and {metric2} increase together strongly"
            elif correlation < -0.7:
                interpretation = f"When {metric1} increases, {metric2} tends to decrease"
            elif abs_corr > 0.3:
                interpretation = f"{metric1} and {metric2} show moderate correlation"
            else:
                interpretation = f"{metric1} and {metric2} show weak correlation"

            return CorrelationResult(
                metric1=metric1,
                metric2=metric2,
                correlation=correlation,
                p_value=p_value,
                lag=0,  # Simplified - could implement lag analysis
                strength=strength,
                interpretation=interpretation
            )

        except Exception:
            return None

    def _align_timeseries(self, series1: List[TimeSeriesPoint], series2: List[TimeSeriesPoint]) -> Tuple[List[float], List[float]]:
        """Align two time series by finding overlapping time periods."""
        # Simple alignment - find overlapping timestamps within a tolerance
        tolerance = timedelta(minutes=5)  # 5-minute tolerance

        values1, values2 = [], []

        for point1 in series1:
            # Find closest point in series2
            closest_point = None
            min_diff = float('inf')

            for point2 in series2:
                diff = abs((point1.timestamp - point2.timestamp).total_seconds())
                if diff < min_diff and diff <= tolerance.total_seconds():
                    min_diff = diff
                    closest_point = point2

            if closest_point:
                values1.append(point1.value)
                values2.append(closest_point.value)

        return values1, values2

    def _detect_anomalies(self, since_dt: datetime, current_time: datetime) -> List[AnomalyDetection]:
        """Detect anomalies in current metric values."""
        anomalies = []

        for metric_name, points in self.metric_history.items():
            try:
                # Filter points to analysis window
                filtered_points = [
                    p for p in points
                    if isinstance(p, TimeSeriesPoint) and since_dt <= p.timestamp <= current_time
                ]

                if len(filtered_points) < 10:  # Need sufficient history
                    continue

                # Get current and historical values
                current_point = filtered_points[-1]
                historical_values = [p.value for p in filtered_points[:-5]]  # Exclude recent values

                if len(historical_values) < 5:
                    continue

                # Calculate expected value and deviation
                expected_value = np.mean(historical_values)
                std_dev = np.std(historical_values)

                if std_dev == 0:  # No variation in historical data
                    continue

                # Calculate deviation score
                deviation_score = abs(current_point.value - expected_value) / std_dev

                # Determine if anomalous
                is_anomaly = deviation_score > self.anomaly_threshold

                if is_anomaly:
                    # Determine severity
                    if deviation_score > 4.0:
                        severity = 'high'
                    elif deviation_score > 3.0:
                        severity = 'medium'
                    else:
                        severity = 'low'

                    anomaly = AnomalyDetection(
                        metric_name=metric_name,
                        current_value=current_point.value,
                        expected_value=expected_value,
                        deviation_score=deviation_score,
                        is_anomaly=is_anomaly,
                        severity=severity,
                        historical_context={
                            'mean': expected_value,
                            'std_dev': std_dev,
                            'historical_count': len(historical_values),
                            'min_historical': min(historical_values),
                            'max_historical': max(historical_values)
                        }
                    )

                    anomalies.append(anomaly)

            except Exception:
                continue

        return anomalies

    def _generate_predictions(self) -> Dict[str, Any]:
        """Generate predictions for key metrics."""
        predictions = {}

        # Get trend analyses for prediction
        current_time = _iso_now()
        since_dt = current_time - timedelta(hours=4)  # Use 4 hours of data for prediction
        trends = self._analyze_trends(since_dt, current_time)

        for trend in trends:
            if trend.confidence > 0.6 and trend.prediction_24h is not None:
                predictions[trend.metric_name] = {
                    'predicted_value_24h': trend.prediction_24h,
                    'confidence': trend.confidence,
                    'trend_direction': trend.trend_direction,
                    'current_slope': trend.slope
                }

        return predictions

    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess the quality of time series data."""
        quality = {
            'metrics_available': len(self.metric_history),
            'total_data_points': sum(len(points) for points in self.metric_history.values()),
            'data_freshness': {},
            'data_completeness': {},
            'overall_score': 0.0
        }

        current_time = _iso_now()
        scores = []

        for metric_name, points in self.metric_history.items():
            if not points:
                continue

            # Check data freshness
            latest_point = max(points, key=lambda p: p.timestamp if isinstance(p, TimeSeriesPoint) else datetime.min.replace(tzinfo=timezone.utc))
            if isinstance(latest_point, TimeSeriesPoint):
                freshness_hours = (current_time - latest_point.timestamp).total_seconds() / 3600
                quality['data_freshness'][metric_name] = freshness_hours

                # Score freshness (0-1, where 1 is very fresh)
                if freshness_hours < 1:
                    freshness_score = 1.0
                elif freshness_hours < 6:
                    freshness_score = 0.8
                elif freshness_hours < 24:
                    freshness_score = 0.5
                else:
                    freshness_score = 0.2

                scores.append(freshness_score)

            # Check data completeness (number of points vs expected)
            expected_points = min(1000, 24 * 4)  # Expect up to 4 points per hour for 24 hours
            completeness = min(1.0, len(points) / expected_points)
            quality['data_completeness'][metric_name] = completeness
            scores.append(completeness)

        # Calculate overall quality score
        if scores:
            quality['overall_score'] = np.mean(scores)

        return quality

    def get_metric_summary(self, metric_name: str, since: str = "24h") -> Optional[Dict[str, Any]]:
        """Get detailed summary for a specific metric."""
        if metric_name not in self.metric_history:
            return None

        since_dt = _parse_since(since)
        current_time = _iso_now()

        # Filter points
        points = [
            p for p in self.metric_history[metric_name]
            if isinstance(p, TimeSeriesPoint) and since_dt <= p.timestamp <= current_time
        ]

        if not points:
            return None

        values = [p.value for p in points]

        return {
            'metric_name': metric_name,
            'time_window': since,
            'data_points': len(points),
            'statistics': {
                'current': values[-1],
                'mean': np.mean(values),
                'median': np.median(values),
                'std_dev': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'percentile_25': np.percentile(values, 25),
                'percentile_75': np.percentile(values, 75)
            },
            'trend': self._get_metric_trend(metric_name, since_dt, current_time),
            'recent_changes': self._get_recent_changes(points),
            'timestamps': {
                'first': points[0].timestamp.isoformat(),
                'last': points[-1].timestamp.isoformat()
            }
        }

    def _get_metric_trend(self, metric_name: str, since_dt: datetime, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Get trend information for a specific metric."""
        trends = self._analyze_trends(since_dt, current_time)
        metric_trend = next((t for t in trends if t.metric_name == metric_name), None)

        if metric_trend:
            return self._trend_to_dict(metric_trend)
        return None

    def _get_recent_changes(self, points: List[TimeSeriesPoint]) -> Dict[str, Any]:
        """Analyze recent changes in a metric."""
        if len(points) < 2:
            return {}

        recent_values = [p.value for p in points[-10:]]  # Last 10 points

        if len(recent_values) < 2:
            return {}

        # Calculate recent change rate
        first_recent = recent_values[0]
        last_recent = recent_values[-1]
        change_percent = ((last_recent - first_recent) / abs(first_recent)) * 100 if first_recent != 0 else 0

        return {
            'change_percent': change_percent,
            'direction': 'increasing' if change_percent > 1 else 'decreasing' if change_percent < -1 else 'stable',
            'volatility': np.std(recent_values) if len(recent_values) > 1 else 0,
            'acceleration': self._calculate_acceleration(recent_values)
        }

    def _calculate_acceleration(self, values: List[float]) -> float:
        """Calculate acceleration (second derivative) of values."""
        if len(values) < 3:
            return 0.0

        # Calculate first derivatives (velocity)
        velocities = [values[i+1] - values[i] for i in range(len(values)-1)]

        if len(velocities) < 2:
            return 0.0

        # Calculate second derivatives (acceleration)
        accelerations = [velocities[i+1] - velocities[i] for i in range(len(velocities)-1)]

        return np.mean(accelerations) if accelerations else 0.0

    def _trend_to_dict(self, trend: TrendAnalysis) -> Dict[str, Any]:
        """Convert TrendAnalysis to dictionary."""
        return {
            'metric_name': trend.metric_name,
            'trend_direction': trend.trend_direction,
            'slope': trend.slope,
            'r_squared': trend.r_squared,
            'confidence': trend.confidence,
            'volatility': trend.volatility,
            'prediction_24h': trend.prediction_24h,
            'significance': trend.significance
        }

    def _correlation_to_dict(self, correlation: CorrelationResult) -> Dict[str, Any]:
        """Convert CorrelationResult to dictionary."""
        return {
            'metric1': correlation.metric1,
            'metric2': correlation.metric2,
            'correlation': correlation.correlation,
            'p_value': correlation.p_value,
            'lag': correlation.lag,
            'strength': correlation.strength,
            'interpretation': correlation.interpretation
        }

    def _anomaly_to_dict(self, anomaly: AnomalyDetection) -> Dict[str, Any]:
        """Convert AnomalyDetection to dictionary."""
        return {
            'metric_name': anomaly.metric_name,
            'current_value': anomaly.current_value,
            'expected_value': anomaly.expected_value,
            'deviation_score': anomaly.deviation_score,
            'is_anomaly': anomaly.is_anomaly,
            'severity': anomaly.severity,
            'historical_context': anomaly.historical_context
        }


def create_enhanced_aggregator(telemetry_dir: Optional[str] = None, history_retention_hours: int = 168) -> EnhancedTelemetryAggregator:
    """Factory function to create an EnhancedTelemetryAggregator instance."""
    return EnhancedTelemetryAggregator(telemetry_dir=telemetry_dir, history_retention_hours=history_retention_hours)


def enhanced_aggregate(since: str = "1h", telemetry_dir: Optional[str] = None, include_timeseries: bool = True) -> Dict[str, Any]:
    """Convenience function for enhanced aggregation."""
    aggregator = create_enhanced_aggregator(telemetry_dir=telemetry_dir)
    return aggregator.enhanced_aggregate(since=since, include_timeseries=include_timeseries)