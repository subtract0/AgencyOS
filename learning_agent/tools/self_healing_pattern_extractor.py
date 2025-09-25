"""
Self-Healing Pattern Extraction Tool for LearningAgent.

Extracts successful patterns and strategies from self-healing system actions.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SelfHealingPatternExtractor(BaseTool):
    """
    Extracts patterns from self-healing system actions and outcomes.

    This tool analyzes self-healing system logs and telemetry to identify:
    - Successful intervention patterns
    - Trigger-action correlations that work well
    - Context patterns that lead to successful outcomes
    - Action sequences that resolve specific issues
    - Timing patterns for optimal interventions
    """

    data_sources: str = Field(
        default="all",
        description="Data sources to analyze: 'logs', 'telemetry', 'agent_memory', 'all'"
    )
    time_window: str = Field(
        default="7d",
        description="Time window for pattern extraction: '1d', '3d', '7d', '14d', '30d'"
    )
    success_threshold: float = Field(
        default=0.8,
        description="Minimum success rate to consider a pattern successful"
    )
    min_occurrences: int = Field(
        default=3,
        description="Minimum number of occurrences to establish a pattern"
    )
    pattern_confidence: float = Field(
        default=0.7,
        description="Minimum confidence score for extracted patterns"
    )

    def run(self) -> str:
        try:
            # Get time boundary
            time_boundary = datetime.now() - self._parse_time_window(self.time_window)

            # Collect data from various sources
            data_collection = self._collect_self_healing_data(time_boundary)

            if not data_collection['total_events']:
                return json.dumps({
                    "status": "no_data",
                    "message": "No self-healing events found in specified time window",
                    "time_window": self.time_window,
                    "sources_checked": data_collection['sources_checked']
                }, indent=2)

            # Extract patterns
            patterns = self._extract_successful_patterns(data_collection)

            # Score and validate patterns
            validated_patterns = self._validate_patterns(patterns, data_collection)

            # Generate actionable insights
            insights = self._generate_actionable_insights(validated_patterns)

            # Create learning objects
            learning_objects = self._create_learning_objects(validated_patterns, insights)

            result = {
                "extraction_timestamp": datetime.now().isoformat(),
                "time_window": self.time_window,
                "data_summary": {
                    "total_events": data_collection['total_events'],
                    "successful_events": data_collection['successful_events'],
                    "sources_analyzed": data_collection['sources_checked'],
                    "success_rate": data_collection['success_rate']
                },
                "patterns_found": len(validated_patterns),
                "patterns": validated_patterns,
                "insights": insights,
                "learning_objects": learning_objects,
                "recommendations": self._generate_recommendations(validated_patterns)
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Error in self-healing pattern extraction: {e}")
            return json.dumps({
                "error": f"Pattern extraction failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, indent=2)

    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string into timedelta."""
        if window.endswith('d'):
            days = int(window[:-1])
            return timedelta(days=days)
        elif window.endswith('h'):
            hours = int(window[:-1])
            return timedelta(hours=hours)
        else:
            return timedelta(days=7)  # Default to 7 days

    def _collect_self_healing_data(self, time_boundary: datetime) -> Dict[str, Any]:
        """Collect self-healing data from various sources."""
        data_collection = {
            'events': [],
            'sources_checked': [],
            'total_events': 0,
            'successful_events': 0,
            'success_rate': 0.0
        }

        if self.data_sources in ['all', 'logs']:
            log_data = self._collect_from_logs(time_boundary)
            data_collection['events'].extend(log_data)
            data_collection['sources_checked'].append('logs')

        if self.data_sources in ['all', 'telemetry']:
            telemetry_data = self._collect_from_telemetry(time_boundary)
            data_collection['events'].extend(telemetry_data)
            data_collection['sources_checked'].append('telemetry')

        if self.data_sources in ['all', 'agent_memory']:
            memory_data = self._collect_from_agent_memory(time_boundary)
            data_collection['events'].extend(memory_data)
            data_collection['sources_checked'].append('agent_memory')

        # Process collected data
        data_collection['total_events'] = len(data_collection['events'])
        successful_events = [e for e in data_collection['events'] if self._is_successful_event(e)]
        data_collection['successful_events'] = len(successful_events)

        if data_collection['total_events'] > 0:
            data_collection['success_rate'] = data_collection['successful_events'] / data_collection['total_events']

        return data_collection

    def _collect_from_logs(self, time_boundary: datetime) -> List[Dict[str, Any]]:
        """Collect self-healing events from log files."""
        events = []
        logs_dir = os.path.join(os.getcwd(), "logs", "self_healing")

        if not os.path.exists(logs_dir):
            return events

        try:
            for filename in os.listdir(logs_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(logs_dir, filename)

                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime >= time_boundary:
                        file_events = self._parse_log_file(filepath, time_boundary)
                        events.extend(file_events)

        except Exception as e:
            logger.warning(f"Error collecting from logs: {e}")

        return events

    def _collect_from_telemetry(self, time_boundary: datetime) -> List[Dict[str, Any]]:
        """Collect self-healing events from telemetry data."""
        events = []
        telemetry_dir = os.path.join(os.getcwd(), "logs", "telemetry")

        if not os.path.exists(telemetry_dir):
            return events

        try:
            for filename in os.listdir(telemetry_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(telemetry_dir, filename)

                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_mtime >= time_boundary:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                events.extend([e for e in data if self._is_self_healing_event(e, time_boundary)])
                            elif self._is_self_healing_event(data, time_boundary):
                                events.append(data)

        except Exception as e:
            logger.warning(f"Error collecting from telemetry: {e}")

        return events

    def _collect_from_agent_memory(self, time_boundary: datetime) -> List[Dict[str, Any]]:
        """Collect self-healing events from agent memory/context."""
        events = []

        try:
            # This would integrate with the actual agent context if available
            # For now, we'll look for memory dumps or session files
            sessions_dir = os.path.join(os.getcwd(), "logs", "sessions")

            if os.path.exists(sessions_dir):
                for filename in os.listdir(sessions_dir):
                    if filename.endswith('.md'):
                        filepath = os.path.join(sessions_dir, filename)
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

                        if file_mtime >= time_boundary:
                            session_events = self._extract_healing_from_session(filepath)
                            events.extend(session_events)

        except Exception as e:
            logger.warning(f"Error collecting from agent memory: {e}")

        return events

    def _parse_log_file(self, filepath: str, time_boundary: datetime) -> List[Dict[str, Any]]:
        """Parse log file for self-healing events."""
        events = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'self_healing' in line.lower() or 'trigger' in line.lower():
                        try:
                            # Try to parse as JSON
                            if '{' in line:
                                json_part = line[line.index('{'):]
                                event = json.loads(json_part)
                                if self._is_self_healing_event(event, time_boundary):
                                    events.append(event)
                        except:
                            # Parse as structured log
                            event = self._parse_structured_log_line(line, time_boundary)
                            if event:
                                events.append(event)

        except Exception as e:
            logger.warning(f"Error parsing log file {filepath}: {e}")

        return events

    def _parse_structured_log_line(self, line: str, time_boundary: datetime) -> Optional[Dict[str, Any]]:
        """Parse structured log line for self-healing information."""
        try:
            # Look for timestamp
            timestamp_str = None
            for part in line.split():
                if ':' in part and len(part) > 10:
                    try:
                        # Try to parse as timestamp
                        timestamp_str = part
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if timestamp < time_boundary:
                            return None
                        break
                    except:
                        continue

            # Extract key information
            event = {
                'timestamp': timestamp_str or datetime.now().isoformat(),
                'source': 'log_parsing',
                'raw_line': line
            }

            # Look for trigger information
            if 'trigger' in line.lower():
                event['event_type'] = 'trigger'
                # Extract trigger name
                trigger_idx = line.lower().index('trigger')
                remaining = line[trigger_idx:].split()
                if len(remaining) > 1:
                    event['trigger_name'] = remaining[1]

            # Look for action information
            if 'action' in line.lower():
                event['event_type'] = 'action'
                action_idx = line.lower().index('action')
                remaining = line[action_idx:].split()
                if len(remaining) > 1:
                    event['action_name'] = remaining[1]

            # Look for success/failure indicators
            if 'success' in line.lower():
                event['status'] = 'success'
            elif 'fail' in line.lower() or 'error' in line.lower():
                event['status'] = 'failed'

            return event

        except Exception:
            return None

    def _extract_healing_from_session(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract self-healing events from session transcript."""
        events = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for self-healing related content
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['self-healing', 'trigger', 'intelligent system', 'workflow']):
                    event = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'session_transcript',
                        'file': os.path.basename(filepath),
                        'content': line.strip(),
                        'event_type': 'session_mention'
                    }
                    events.append(event)

        except Exception as e:
            logger.warning(f"Error extracting from session {filepath}: {e}")

        return events

    def _is_self_healing_event(self, event: Dict[str, Any], time_boundary: datetime) -> bool:
        """Check if event is related to self-healing and within time window."""
        # Check timestamp
        timestamp_str = event.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp < time_boundary:
                    return False
            except:
                pass

        # Check if it's self-healing related
        text_content = str(event).lower()
        healing_keywords = ['self_healing', 'trigger', 'intelligent_system', 'workflow', 'dispatcher', 'pattern_analyzer']

        return any(keyword in text_content for keyword in healing_keywords)

    def _is_successful_event(self, event: Dict[str, Any]) -> bool:
        """Determine if an event represents a successful self-healing action."""
        status = event.get('status', '').lower()
        if status in ['success', 'successful', 'resolved', 'completed']:
            return True

        # Check for success indicators in content
        content = str(event.get('content', '') + event.get('raw_line', '')).lower()
        success_indicators = ['resolved', 'fixed', 'successful', 'completed', 'recovered']

        return any(indicator in content for indicator in success_indicators)

    def _extract_successful_patterns(self, data_collection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract patterns from successful self-healing events."""
        patterns = []
        events = data_collection['events']
        successful_events = [e for e in events if self._is_successful_event(e)]

        if len(successful_events) < self.min_occurrences:
            return patterns

        # Pattern 1: Trigger-Action Success Patterns
        trigger_action_patterns = self._extract_trigger_action_patterns(successful_events)
        patterns.extend(trigger_action_patterns)

        # Pattern 2: Context-Based Success Patterns
        context_patterns = self._extract_context_patterns(successful_events)
        patterns.extend(context_patterns)

        # Pattern 3: Timing Patterns
        timing_patterns = self._extract_timing_patterns(successful_events)
        patterns.extend(timing_patterns)

        # Pattern 4: Sequential Action Patterns
        sequence_patterns = self._extract_sequence_patterns(successful_events)
        patterns.extend(sequence_patterns)

        return patterns

    def _extract_trigger_action_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract trigger-action correlation patterns."""
        patterns = []

        # Group by trigger type and action type
        trigger_action_groups = defaultdict(list)

        for event in events:
            trigger = event.get('trigger_name') or event.get('trigger_type', 'unknown')
            action = event.get('action_name') or event.get('action_type', 'unknown')

            if trigger != 'unknown' and action != 'unknown':
                key = f"{trigger}::{action}"
                trigger_action_groups[key].append(event)

        # Find patterns with sufficient occurrences
        for combination, combo_events in trigger_action_groups.items():
            if len(combo_events) >= self.min_occurrences:
                trigger, action = combination.split('::')

                # Calculate success rate for this combination
                success_rate = len(combo_events) / len(events)  # Relative success

                if success_rate >= self.success_threshold:
                    patterns.append({
                        'pattern_id': f'trigger_action_{trigger}_{action}',
                        'pattern_type': 'trigger_action',
                        'trigger': trigger,
                        'action': action,
                        'occurrences': len(combo_events),
                        'success_rate': success_rate,
                        'confidence': min(0.9, len(combo_events) / 10),
                        'description': f'Trigger "{trigger}" successfully resolved by action "{action}"',
                        'evidence': combo_events[:3],  # Sample evidence
                        'effectiveness_score': success_rate * min(1.0, len(combo_events) / self.min_occurrences)
                    })

        return patterns

    def _extract_context_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract context-based success patterns."""
        patterns = []

        # Group by context characteristics
        context_groups = defaultdict(list)

        for event in events:
            context_keys = []

            # Extract context information
            if 'error_type' in event:
                context_keys.append(f"error:{event['error_type']}")
            if 'agent' in event:
                context_keys.append(f"agent:{event['agent']}")
            if 'component' in event:
                context_keys.append(f"component:{event['component']}")
            if 'severity' in event:
                context_keys.append(f"severity:{event['severity']}")

            # Group by context combinations
            for context_key in context_keys:
                context_groups[context_key].append(event)

        # Find patterns with sufficient occurrences
        for context, context_events in context_groups.items():
            if len(context_events) >= self.min_occurrences:
                success_rate = len(context_events) / len(events)

                if success_rate >= self.success_threshold:
                    patterns.append({
                        'pattern_id': f'context_{context.replace(":", "_")}',
                        'pattern_type': 'context',
                        'context': context,
                        'occurrences': len(context_events),
                        'success_rate': success_rate,
                        'confidence': min(0.8, len(context_events) / 8),
                        'description': f'Successful resolution in context: {context}',
                        'evidence': context_events[:2],
                        'effectiveness_score': success_rate * min(1.0, len(context_events) / self.min_occurrences)
                    })

        return patterns

    def _extract_timing_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract timing-based patterns."""
        patterns = []

        # Group by time of day
        time_groups = defaultdict(list)

        for event in events:
            timestamp_str = event.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    hour = timestamp.hour

                    # Group into time periods
                    if 6 <= hour < 12:
                        time_period = 'morning'
                    elif 12 <= hour < 18:
                        time_period = 'afternoon'
                    elif 18 <= hour < 24:
                        time_period = 'evening'
                    else:
                        time_period = 'night'

                    time_groups[time_period].append(event)
                except:
                    continue

        # Analyze time patterns
        for time_period, period_events in time_groups.items():
            if len(period_events) >= self.min_occurrences:
                success_rate = len(period_events) / len(events)

                patterns.append({
                    'pattern_id': f'timing_{time_period}',
                    'pattern_type': 'timing',
                    'time_period': time_period,
                    'occurrences': len(period_events),
                    'success_rate': success_rate,
                    'confidence': min(0.7, len(period_events) / 5),
                    'description': f'Higher success rate during {time_period}',
                    'evidence': period_events[:2],
                    'effectiveness_score': success_rate * min(1.0, len(period_events) / self.min_occurrences)
                })

        return patterns

    def _extract_sequence_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract sequential action patterns."""
        patterns = []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', ''))

        # Look for action sequences (events within short time windows)
        sequence_window = timedelta(minutes=30)  # 30-minute window for sequences
        sequences = []

        for i in range(len(sorted_events) - 1):
            try:
                current_time = datetime.fromisoformat(sorted_events[i].get('timestamp', '').replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(sorted_events[i+1].get('timestamp', '').replace('Z', '+00:00'))

                if next_time - current_time <= sequence_window:
                    current_action = sorted_events[i].get('action_name') or sorted_events[i].get('action_type', '')
                    next_action = sorted_events[i+1].get('action_name') or sorted_events[i+1].get('action_type', '')

                    if current_action and next_action:
                        sequence = f"{current_action} -> {next_action}"
                        sequences.append({
                            'sequence': sequence,
                            'events': [sorted_events[i], sorted_events[i+1]],
                            'time_gap': (next_time - current_time).total_seconds()
                        })
            except:
                continue

        # Find common sequences
        sequence_counts = defaultdict(list)
        for seq_data in sequences:
            sequence_counts[seq_data['sequence']].append(seq_data)

        for sequence, seq_instances in sequence_counts.items():
            if len(seq_instances) >= self.min_occurrences:
                avg_time_gap = sum(s['time_gap'] for s in seq_instances) / len(seq_instances)

                patterns.append({
                    'pattern_id': f'sequence_{sequence.replace(" -> ", "_to_")}',
                    'pattern_type': 'sequence',
                    'sequence': sequence,
                    'occurrences': len(seq_instances),
                    'average_time_gap': avg_time_gap,
                    'confidence': min(0.8, len(seq_instances) / 6),
                    'description': f'Successful action sequence: {sequence}',
                    'evidence': seq_instances[:2],
                    'effectiveness_score': len(seq_instances) / self.min_occurrences
                })

        return patterns

    def _validate_patterns(self, patterns: List[Dict[str, Any]], data_collection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and score patterns based on confidence and effectiveness."""
        validated_patterns = []

        for pattern in patterns:
            # Calculate overall confidence score
            base_confidence = pattern.get('confidence', 0)
            effectiveness = pattern.get('effectiveness_score', 0)
            occurrence_weight = min(1.0, pattern.get('occurrences', 0) / (self.min_occurrences * 2))

            # Combined confidence score
            overall_confidence = (base_confidence * 0.4 + effectiveness * 0.4 + occurrence_weight * 0.2)

            if overall_confidence >= self.pattern_confidence:
                pattern['overall_confidence'] = overall_confidence
                pattern['validation_status'] = 'validated'
                validated_patterns.append(pattern)
            else:
                pattern['overall_confidence'] = overall_confidence
                pattern['validation_status'] = 'insufficient_confidence'

        return validated_patterns

    def _generate_actionable_insights(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable insights from validated patterns."""
        insights = []

        # Group patterns by type
        pattern_types = defaultdict(list)
        for pattern in patterns:
            pattern_types[pattern['pattern_type']].append(pattern)

        # Generate insights for each pattern type
        for pattern_type, type_patterns in pattern_types.items():
            if pattern_type == 'trigger_action':
                insights.append({
                    'insight_type': 'trigger_action_optimization',
                    'title': 'Successful Trigger-Action Combinations',
                    'description': f'Found {len(type_patterns)} successful trigger-action patterns',
                    'actionable_recommendations': [
                        'Prioritize these trigger-action combinations in dispatch logic',
                        'Create automated workflows for these successful patterns',
                        'Document these patterns as best practices'
                    ],
                    'patterns': [p['pattern_id'] for p in type_patterns],
                    'confidence': sum(p['overall_confidence'] for p in type_patterns) / len(type_patterns)
                })

            elif pattern_type == 'context':
                insights.append({
                    'insight_type': 'context_optimization',
                    'title': 'Context-Specific Success Patterns',
                    'description': f'Identified {len(type_patterns)} context patterns with high success rates',
                    'actionable_recommendations': [
                        'Create context-aware trigger conditions',
                        'Implement context-specific action selection',
                        'Monitor context changes for proactive interventions'
                    ],
                    'patterns': [p['pattern_id'] for p in type_patterns],
                    'confidence': sum(p['overall_confidence'] for p in type_patterns) / len(type_patterns)
                })

            elif pattern_type == 'timing':
                insights.append({
                    'insight_type': 'timing_optimization',
                    'title': 'Temporal Success Patterns',
                    'description': f'Found {len(type_patterns)} timing patterns affecting success rates',
                    'actionable_recommendations': [
                        'Adjust monitoring frequency based on time patterns',
                        'Schedule maintenance during optimal time windows',
                        'Implement time-aware threshold adjustments'
                    ],
                    'patterns': [p['pattern_id'] for p in type_patterns],
                    'confidence': sum(p['overall_confidence'] for p in type_patterns) / len(type_patterns)
                })

            elif pattern_type == 'sequence':
                insights.append({
                    'insight_type': 'sequence_optimization',
                    'title': 'Successful Action Sequences',
                    'description': f'Discovered {len(type_patterns)} effective action sequences',
                    'actionable_recommendations': [
                        'Create workflow templates for successful sequences',
                        'Implement sequence-aware action scheduling',
                        'Monitor for sequence completion and optimization'
                    ],
                    'patterns': [p['pattern_id'] for p in type_patterns],
                    'confidence': sum(p['overall_confidence'] for p in type_patterns) / len(type_patterns)
                })

        return insights

    def _create_learning_objects(self, patterns: List[Dict[str, Any]], insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create structured learning objects for VectorStore storage."""
        learning_objects = []

        for pattern in patterns:
            learning_object = {
                'learning_id': f"self_healing_pattern_{pattern['pattern_id']}_{int(datetime.now().timestamp())}",
                'type': 'successful_pattern',
                'category': 'self_healing',
                'title': f"Self-Healing Pattern: {pattern['pattern_type'].title()}",
                'description': pattern['description'],
                'actionable_insight': self._create_actionable_insight_for_pattern(pattern),
                'confidence': pattern['overall_confidence'],
                'keywords': [
                    'self_healing',
                    pattern['pattern_type'],
                    'successful_pattern',
                    'automation'
                ],
                'patterns': {
                    'triggers': self._extract_pattern_triggers(pattern),
                    'actions': self._extract_pattern_actions(pattern),
                    'conditions': self._extract_pattern_conditions(pattern),
                    'outcomes': ['successful_resolution', 'pattern_validated']
                },
                'metadata': {
                    'created_timestamp': datetime.now().isoformat(),
                    'source_pattern_id': pattern['pattern_id'],
                    'pattern_data': pattern,
                    'extraction_method': 'self_healing_pattern_extractor',
                    'time_window': self.time_window,
                    'occurrences': pattern.get('occurrences', 0),
                    'effectiveness_score': pattern.get('effectiveness_score', 0)
                },
                'application_criteria': self._generate_application_criteria_for_pattern(pattern),
                'success_metrics': [
                    f"Pattern application success rate >= {pattern.get('success_rate', 0.8):.2f}",
                    "Resolution time improvement",
                    "Reduced manual intervention needed"
                ]
            }
            learning_objects.append(learning_object)

        return learning_objects

    def _create_actionable_insight_for_pattern(self, pattern: Dict[str, Any]) -> str:
        """Create actionable insight text for a pattern."""
        pattern_type = pattern['pattern_type']

        if pattern_type == 'trigger_action':
            return f"When trigger '{pattern['trigger']}' occurs, prioritize action '{pattern['action']}' for highest success rate ({pattern.get('success_rate', 0):.1%})"
        elif pattern_type == 'context':
            return f"In context '{pattern['context']}', current resolution approach shows {pattern.get('success_rate', 0):.1%} success rate - maintain and optimize this approach"
        elif pattern_type == 'timing':
            return f"Schedule self-healing actions during {pattern['time_period']} for optimal success rates"
        elif pattern_type == 'sequence':
            return f"Implement action sequence '{pattern['sequence']}' as a workflow template for consistent results"
        else:
            return f"Apply this {pattern_type} pattern when similar conditions are detected"

    def _extract_pattern_triggers(self, pattern: Dict[str, Any]) -> List[str]:
        """Extract trigger information from pattern."""
        triggers = []
        if 'trigger' in pattern:
            triggers.append(pattern['trigger'])
        if 'context' in pattern:
            triggers.append(f"context_match_{pattern['context']}")
        if 'time_period' in pattern:
            triggers.append(f"time_period_{pattern['time_period']}")
        return triggers or ['pattern_conditions_met']

    def _extract_pattern_actions(self, pattern: Dict[str, Any]) -> List[str]:
        """Extract action information from pattern."""
        actions = []
        if 'action' in pattern:
            actions.append(pattern['action'])
        if 'sequence' in pattern:
            actions.extend(pattern['sequence'].split(' -> '))
        return actions or ['apply_pattern']

    def _extract_pattern_conditions(self, pattern: Dict[str, Any]) -> List[str]:
        """Extract condition information from pattern."""
        conditions = []
        if 'success_rate' in pattern:
            conditions.append(f"success_rate >= {pattern['success_rate']:.2f}")
        if 'occurrences' in pattern:
            conditions.append(f"occurrences >= {pattern['occurrences']}")
        return conditions or ['pattern_validation_passed']

    def _generate_application_criteria_for_pattern(self, pattern: Dict[str, Any]) -> List[str]:
        """Generate application criteria for pattern."""
        criteria = [
            f"Pattern confidence >= {pattern['overall_confidence']:.2f}",
            "Similar context or trigger detected",
            "No conflicting patterns active"
        ]

        pattern_type = pattern['pattern_type']
        if pattern_type == 'trigger_action':
            criteria.append(f"Trigger type matches: {pattern['trigger']}")
        elif pattern_type == 'context':
            criteria.append(f"Context matches: {pattern['context']}")
        elif pattern_type == 'timing':
            criteria.append(f"Current time period: {pattern['time_period']}")

        return criteria

    def _generate_recommendations(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific recommendations based on patterns."""
        recommendations = []

        # High-confidence patterns get priority implementation
        high_confidence_patterns = [p for p in patterns if p['overall_confidence'] > 0.8]

        if high_confidence_patterns:
            recommendations.append({
                'priority': 'high',
                'category': 'pattern_implementation',
                'title': 'Implement High-Confidence Patterns',
                'description': f'Integrate {len(high_confidence_patterns)} high-confidence patterns into automated workflows',
                'specific_actions': [
                    'Create workflow templates for trigger-action patterns',
                    'Update dispatcher logic with context-aware selection',
                    'Implement timing-based optimization adjustments',
                    'Document patterns as institutional knowledge'
                ],
                'expected_benefits': [
                    'Increased automation success rate',
                    'Reduced manual intervention',
                    'Faster problem resolution',
                    'More consistent outcomes'
                ]
            })

        # Pattern monitoring and optimization
        recommendations.append({
            'priority': 'medium',
            'category': 'pattern_monitoring',
            'title': 'Enhance Pattern Monitoring',
            'description': 'Implement continuous monitoring and optimization of identified patterns',
            'specific_actions': [
                'Add pattern effectiveness tracking',
                'Create pattern performance dashboards',
                'Implement pattern degradation alerts',
                'Schedule regular pattern validation reviews'
            ],
            'expected_benefits': [
                'Early detection of pattern effectiveness changes',
                'Continuous improvement of automation',
                'Data-driven optimization decisions',
                'Proactive pattern maintenance'
            ]
        })

        return recommendations