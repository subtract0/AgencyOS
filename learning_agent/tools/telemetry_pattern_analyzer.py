# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Telemetry Pattern Analysis Tool for LearningAgent.

Analyzes telemetry data to extract patterns for learning and optimization.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from shared.type_definitions.json import JSONValue
import logging
from learning_agent.json_utils import (
    is_dict, is_list, is_str, is_int, is_float, is_number, is_none,
    safe_get, safe_get_dict, safe_get_list, safe_get_str, safe_get_int, safe_get_float,
    ensure_dict, ensure_list, ensure_str
)

logger = logging.getLogger(__name__)


class TelemetryPatternAnalyzer(BaseTool):  # mypy: disable-error-code="misc"
    """
    Analyzes telemetry data to extract learning patterns.

    This tool processes telemetry logs to identify:
    - Performance patterns and bottlenecks
    - Error correlation patterns
    - Resource usage trends
    - Agent interaction patterns
    - Success/failure patterns in self-healing actions
    """

    telemetry_dir: str = Field(
        default="",
        description="Directory containing telemetry data (defaults to logs/telemetry)"
    )
    analysis_window: str = Field(
        default="24h",
        description="Time window for analysis: '1h', '6h', '24h', '7d'"
    )
    pattern_types: str = Field(
        default="all",
        description="Types to analyze: 'performance', 'errors', 'self_healing', 'agents', 'all'"
    )
    min_confidence: float = Field(
        default=0.6,
        description="Minimum confidence threshold for pattern extraction"
    )

    def run(self) -> str:
        try:
            # Determine telemetry directory
            telemetry_dir = self.telemetry_dir or os.path.join(os.getcwd(), "logs", "telemetry")

            if not os.path.exists(telemetry_dir):
                return json.dumps({
                    "error": f"Telemetry directory not found: {telemetry_dir}",
                    "suggestion": "Ensure telemetry logging is enabled and directory exists"
                }, indent=2)

            # Parse analysis window
            time_delta = self._parse_time_window(self.analysis_window)
            cutoff_time = datetime.now() - time_delta

            # Load and filter telemetry data
            telemetry_data = self._load_telemetry_data(telemetry_dir, cutoff_time)

            if not telemetry_data:
                return json.dumps({
                    "warning": "No telemetry data found in specified time window",
                    "time_window": self.analysis_window,
                    "telemetry_dir": telemetry_dir
                }, indent=2)

            # Extract patterns based on requested types
            patterns = self._extract_patterns(telemetry_data)

            # Calculate confidence scores and filter
            filtered_patterns = self._filter_by_confidence(patterns)

            # Generate insights
            insights = self._generate_insights(filtered_patterns, telemetry_data)

            result = {
                "analysis_timestamp": datetime.now().isoformat(),
                "time_window": self.analysis_window,
                "data_points_analyzed": len(telemetry_data),
                "patterns_found": len(filtered_patterns),
                "patterns": filtered_patterns,
                "insights": insights,
                "recommendations": self._generate_recommendations(filtered_patterns)
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in telemetry pattern analysis: {e}")
            return json.dumps({
                "error": f"Telemetry analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2)

    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string into timedelta."""
        if window.endswith('h'):
            hours = int(window[:-1])
            return timedelta(hours=hours)
        elif window.endswith('d'):
            days = int(window[:-1])
            return timedelta(days=days)
        elif window.endswith('m'):
            minutes = int(window[:-1])
            return timedelta(minutes=minutes)
        else:
            # Default to 24 hours
            return timedelta(hours=24)

    def _load_telemetry_data(self, telemetry_dir: str, cutoff_time: datetime) -> List[Dict[str, JSONValue]]:
        """Load telemetry data from files within time window."""
        telemetry_data = []

        try:
            # Look for telemetry files
            for root, dirs, files in os.walk(telemetry_dir):
                for file in files:
                    if file.endswith('.json') or file.endswith('.log'):
                        filepath = os.path.join(root, file)

                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if file_mtime >= cutoff_time:
                            data = self._parse_telemetry_file(filepath)
                            if data:
                                telemetry_data.extend(data)

        except Exception as e:
            logger.warning(f"Error loading telemetry data: {e}")

        return telemetry_data

    def _parse_telemetry_file(self, filepath: str) -> List[Dict[str, JSONValue]]:
        """Parse individual telemetry file."""
        data = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.json'):
                    # JSON format
                    parsed_content = json.load(f)
                    if isinstance(parsed_content, list):
                        for item in parsed_content:
                            data.append(ensure_dict(item))
                    else:
                        data.append(ensure_dict(parsed_content))
                else:
                    # Log format - try to parse JSON lines
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('{'):
                            try:
                                parsed_entry = json.loads(line)
                                entry = ensure_dict(parsed_entry)
                                data.append(entry)
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.warning(f"Error parsing telemetry file {filepath}: {e}")

        return data

    def _extract_patterns(self, telemetry_data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Extract patterns from telemetry data."""
        patterns = []

        # Group by pattern types
        if self.pattern_types in ['all', 'performance']:
            patterns.extend(self._extract_performance_patterns(telemetry_data))

        if self.pattern_types in ['all', 'errors']:
            patterns.extend(self._extract_error_patterns(telemetry_data))

        if self.pattern_types in ['all', 'self_healing']:
            patterns.extend(self._extract_self_healing_patterns(telemetry_data))

        if self.pattern_types in ['all', 'agents']:
            patterns.extend(self._extract_agent_patterns(telemetry_data))

        return patterns

    def _extract_performance_patterns(self, data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Extract performance-related patterns."""
        patterns = []

        # Response time patterns
        response_times: List[Dict[str, JSONValue]] = []
        for entry in data:
            if 'response_time' in entry or 'duration' in entry:
                time_val = safe_get(entry, 'response_time') or safe_get(entry, 'duration', 0)
                if is_number(time_val):
                    response_times.append({
                        'time': time_val,
                        'timestamp': safe_get(entry, 'timestamp'),
                        'operation': safe_get_str(entry, 'operation', 'unknown')
                    })

        if response_times:
            total_time = sum(safe_get_float(r, 'time', 0) for r in response_times)
            avg_time = total_time / len(response_times)
            slow_ops = [r for r in response_times if safe_get_float(r, 'time', 0) > avg_time * 2]

            if slow_ops:
                pattern: Dict[str, JSONValue] = {
                    'pattern_id': 'performance_slow_operations',
                    'type': 'performance',
                    'title': 'Slow Operation Pattern Detected',
                    'description': f'Found {len(slow_ops)} operations slower than 2x average',
                    'confidence': min(0.9, len(slow_ops) / len(response_times) * 2),
                    'data': {
                        'avg_response_time': avg_time,
                        'slow_operations': slow_ops[:5],  # Top 5
                        'total_slow_count': len(slow_ops)
                    },
                    'severity': 'high' if len(slow_ops) > len(response_times) * 0.2 else 'medium'
                }
                patterns.append(pattern)

        # Resource usage patterns
        memory_usage = [e for e in data if 'memory_usage' in e]
        if memory_usage:
            high_memory = [e for e in memory_usage if safe_get_float(e, 'memory_usage', 0) > 80]
            if high_memory:
                peak_usage = max(safe_get_float(e, 'memory_usage', 0) for e in high_memory)
                memory_pattern: Dict[str, JSONValue] = {
                    'pattern_id': 'performance_high_memory',
                    'type': 'performance',
                    'title': 'High Memory Usage Pattern',
                    'description': f'Memory usage exceeded 80% in {len(high_memory)} instances',
                    'confidence': min(0.8, len(high_memory) / len(memory_usage)),
                    'data': {
                        'high_memory_events': len(high_memory),
                        'peak_usage': peak_usage
                    },
                    'severity': 'critical' if len(high_memory) > 10 else 'high'
                }
                patterns.append(memory_pattern)

        return patterns

    def _extract_error_patterns(self, data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Extract error-related patterns."""
        patterns = []

        # Error frequency patterns
        errors = [e for e in data if safe_get_str(e, 'level') == 'ERROR' or 'error' in e]
        if errors:
            # Group by error type
            error_types: Dict[str, List[Dict[str, JSONValue]]] = {}
            for error in errors:
                error_type = safe_get_str(error, 'error_type') or safe_get_str(error, 'type', 'unknown')
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(error)

            # Find recurring error patterns
            for error_type, occurrences in error_types.items():
                if len(occurrences) >= 3:  # At least 3 occurrences
                    error_pattern: Dict[str, JSONValue] = {
                        'pattern_id': f'error_recurring_{error_type}',
                        'type': 'error',
                        'title': f'Recurring Error Pattern: {error_type}',
                        'description': f'Error type "{error_type}" occurred {len(occurrences)} times',
                        'confidence': min(0.9, len(occurrences) / 10),
                        'data': {
                            'error_type': error_type,
                            'occurrence_count': len(occurrences),
                            'recent_occurrences': occurrences[-3:],  # Last 3
                            'time_pattern': self._analyze_time_pattern(occurrences)
                        },
                        'severity': 'critical' if len(occurrences) > 10 else 'high'
                    }
                    patterns.append(error_pattern)

        return patterns

    def _extract_self_healing_patterns(self, data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Extract self-healing action patterns."""
        patterns = []

        # Self-healing action data
        healing_actions = [e for e in data if 'self_healing' in e or 'trigger' in e]
        if healing_actions:
            # Success/failure patterns
            successful = [a for a in healing_actions if safe_get_str(a, 'status') == 'success']
            failed = [a for a in healing_actions if safe_get_str(a, 'status') == 'failed']

            if successful:
                # Analyze successful patterns
                success_rate = len(successful) / len(healing_actions)
                success_pattern: Dict[str, JSONValue] = {
                    'pattern_id': 'self_healing_success_pattern',
                    'type': 'self_healing',
                    'title': 'Self-Healing Success Pattern',
                    'description': f'Self-healing actions have {success_rate:.1%} success rate',
                    'confidence': min(0.9, success_rate),
                    'data': {
                        'total_actions': len(healing_actions),
                        'successful_actions': len(successful),
                        'success_rate': success_rate,
                        'common_triggers': self._extract_common_triggers(successful),
                        'effective_actions': self._extract_effective_actions(successful)
                    },
                    'severity': 'low' if success_rate > 0.8 else 'medium'
                }
                patterns.append(success_pattern)

            if failed and len(failed) / len(healing_actions) > 0.3:
                # High failure rate pattern
                failure_pattern: Dict[str, JSONValue] = {
                    'pattern_id': 'self_healing_failure_pattern',
                    'type': 'self_healing',
                    'title': 'Self-Healing Failure Pattern',
                    'description': f'High failure rate in self-healing: {len(failed)} failures',
                    'confidence': len(failed) / len(healing_actions),
                    'data': {
                        'failed_actions': len(failed),
                        'failure_rate': len(failed) / len(healing_actions),
                        'common_failure_causes': self._extract_failure_causes(failed)
                    },
                    'severity': 'critical'
                }
                patterns.append(failure_pattern)

        return patterns

    def _extract_agent_patterns(self, data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Extract agent interaction patterns."""
        patterns = []

        # Agent communication patterns
        agent_data = [e for e in data if 'agent' in e or 'handoff' in e]
        if agent_data:
            # Handoff patterns
            handoffs = [e for e in agent_data if 'handoff' in e]
            if handoffs:
                # Analyze handoff success
                successful_handoffs = [h for h in handoffs if safe_get_str(h, 'status') == 'success']
                if successful_handoffs:
                    success_rate = len(successful_handoffs) / len(handoffs)
                    handoff_pattern: Dict[str, JSONValue] = {
                        'pattern_id': 'agent_handoff_pattern',
                        'type': 'agent',
                        'title': 'Agent Handoff Pattern',
                        'description': f'Agent handoffs have {success_rate:.1%} success rate',
                        'confidence': min(0.8, success_rate),
                        'data': {
                            'total_handoffs': len(handoffs),
                            'successful_handoffs': len(successful_handoffs),
                            'success_rate': success_rate,
                            'common_handoff_pairs': self._extract_handoff_pairs(successful_handoffs)
                        },
                        'severity': 'low' if success_rate > 0.9 else 'medium'
                    }
                    patterns.append(handoff_pattern)

        return patterns

    def _analyze_time_pattern(self, events: List[Dict[str, JSONValue]]) -> Dict[str, JSONValue]:
        """Analyze temporal patterns in events."""
        timestamps = [safe_get(e, 'timestamp') for e in events if safe_get(e, 'timestamp')]
        if not timestamps:
            return {}

        # Convert to datetime objects
        datetimes: List[datetime] = []
        for ts in timestamps:
            try:
                if is_str(ts):
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    datetimes.append(dt)
            except (ValueError, TypeError) as e:
                continue

        if len(datetimes) < 2:
            return {}

        # Calculate intervals
        intervals = []
        for i in range(1, len(datetimes)):
            interval = (datetimes[i] - datetimes[i-1]).total_seconds()
            intervals.append(interval)

        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        return {
            'event_count': len(datetimes),
            'time_span_hours': (datetimes[-1] - datetimes[0]).total_seconds() / 3600,
            'average_interval_seconds': avg_interval,
            'pattern': 'frequent' if avg_interval < 300 else 'periodic' if avg_interval < 3600 else 'sparse'
        }

    def _extract_common_triggers(self, successful_actions: List[Dict[str, JSONValue]]) -> List[str]:
        """Extract common triggers from successful actions."""
        triggers: Dict[str, int] = {}
        for action in successful_actions:
            trigger = safe_get_str(action, 'trigger') or safe_get_str(action, 'trigger_type', 'unknown')
            triggers[trigger] = triggers.get(trigger, 0) + 1

        # Return top 3 triggers
        sorted_triggers = sorted(triggers.items(), key=lambda x: x[1], reverse=True)
        return [trigger for trigger, count in sorted_triggers[:3]]

    def _extract_effective_actions(self, successful_actions: List[Dict[str, JSONValue]]) -> List[str]:
        """Extract effective action types."""
        actions: Dict[str, int] = {}
        for action in successful_actions:
            action_type = safe_get_str(action, 'action') or safe_get_str(action, 'action_type', 'unknown')
            actions[action_type] = actions.get(action_type, 0) + 1

        # Return top 3 actions
        sorted_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)
        return [action for action, count in sorted_actions[:3]]

    def _extract_failure_causes(self, failed_actions: List[Dict[str, JSONValue]]) -> List[str]:
        """Extract common failure causes."""
        causes: Dict[str, int] = {}
        for action in failed_actions:
            cause_raw = safe_get(action, 'failure_reason') or safe_get(action, 'error', 'unknown')
            cause = ensure_str(cause_raw)
            causes[cause] = causes.get(cause, 0) + 1

        # Return top 3 causes
        sorted_causes = sorted(causes.items(), key=lambda x: x[1], reverse=True)
        return [cause for cause, count in sorted_causes[:3]]

    def _extract_handoff_pairs(self, handoffs: List[Dict[str, JSONValue]]) -> List[str]:
        """Extract common agent handoff pairs."""
        pairs: Dict[str, int] = {}
        for handoff in handoffs:
            from_agent = safe_get_str(handoff, 'from_agent', 'unknown')
            to_agent = safe_get_str(handoff, 'to_agent', 'unknown')
            pair = f"{from_agent} -> {to_agent}"
            pairs[pair] = pairs.get(pair, 0) + 1

        # Return top 3 pairs
        sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
        return [pair for pair, count in sorted_pairs[:3]]

    def _filter_by_confidence(self, patterns: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Filter patterns by minimum confidence threshold."""
        return [p for p in patterns if safe_get_float(p, 'confidence', 0) >= self.min_confidence]

    def _generate_insights(self, patterns: List[Dict[str, JSONValue]], data: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Generate actionable insights from patterns."""
        insights = []

        # Performance insights
        performance_patterns = [p for p in patterns if safe_get_str(p, 'type') == 'performance']
        if performance_patterns:
            has_critical = any(safe_get_str(p, 'severity') == 'critical' for p in performance_patterns)
            performance_insight: Dict[str, JSONValue] = {
                'category': 'performance',
                'insight': f'Found {len(performance_patterns)} performance patterns',
                'recommendation': 'Consider optimizing slow operations and monitoring resource usage',
                'priority': 'high' if has_critical else 'medium'
            }
            insights.append(performance_insight)

        # Error insights
        error_patterns = [p for p in patterns if safe_get_str(p, 'type') == 'error']
        if error_patterns:
            error_insight: Dict[str, JSONValue] = {
                'category': 'error_handling',
                'insight': f'Detected {len(error_patterns)} recurring error patterns',
                'recommendation': 'Implement proactive error prevention for recurring issues',
                'priority': 'critical' if len(error_patterns) > 5 else 'high'
            }
            insights.append(error_insight)

        # Self-healing insights
        healing_patterns = [p for p in patterns if safe_get_str(p, 'type') == 'self_healing']
        if healing_patterns:
            success_patterns = [p for p in healing_patterns if 'success' in safe_get_str(p, 'pattern_id')]
            if success_patterns:
                healing_insight: Dict[str, JSONValue] = {
                    'category': 'self_healing',
                    'insight': 'Self-healing system showing good performance',
                    'recommendation': 'Document and replicate successful healing patterns',
                    'priority': 'medium'
                }
                insights.append(healing_insight)

        return insights

    def _generate_recommendations(self, patterns: List[Dict[str, JSONValue]]) -> List[Dict[str, JSONValue]]:
        """Generate specific recommendations based on patterns."""
        recommendations = []

        # Critical patterns get immediate recommendations
        critical_patterns = [p for p in patterns if safe_get_str(p, 'severity') == 'critical']
        for pattern in critical_patterns:
            critical_rec: Dict[str, JSONValue] = {
                'pattern_id': safe_get_str(pattern, 'pattern_id'),
                'priority': 'immediate',
                'action': f'Address critical pattern: {safe_get_str(pattern, "title")}',
                'description': safe_get_str(pattern, 'description'),
                'suggested_steps': self._get_pattern_specific_steps(pattern)
            }
            recommendations.append(critical_rec)

        # Performance optimization recommendations
        performance_patterns = [p for p in patterns if safe_get_str(p, 'type') == 'performance']
        if performance_patterns:
            perf_rec: Dict[str, JSONValue] = {
                'pattern_id': 'performance_optimization',
                'priority': 'high',
                'action': 'Implement performance monitoring and optimization',
                'description': 'Multiple performance patterns detected',
                'suggested_steps': [
                    'Add performance metrics collection',
                    'Implement caching for slow operations',
                    'Add resource usage monitoring',
                    'Set up performance alerts'
                ]
            }
            recommendations.append(perf_rec)

        return recommendations

    def _get_pattern_specific_steps(self, pattern: Dict[str, JSONValue]) -> List[str]:
        """Get specific steps for addressing a pattern."""
        pattern_type = safe_get_str(pattern, 'type')
        pattern_id = safe_get_str(pattern, 'pattern_id')

        if 'error_recurring' in pattern_id:
            return [
                'Analyze root cause of recurring error',
                'Implement specific error prevention',
                'Add enhanced logging for this error type',
                'Create automated recovery procedure'
            ]
        elif 'performance_slow' in pattern_id:
            return [
                'Profile slow operations to identify bottlenecks',
                'Implement caching or optimization',
                'Add performance monitoring',
                'Set performance thresholds and alerts'
            ]
        elif 'self_healing_failure' in pattern_id:
            return [
                'Review failed self-healing actions',
                'Improve action reliability',
                'Add fallback procedures',
                'Enhance failure detection and reporting'
            ]
        else:
            return [
                'Investigate pattern cause',
                'Implement monitoring',
                'Develop mitigation strategy',
                'Document findings'
            ]