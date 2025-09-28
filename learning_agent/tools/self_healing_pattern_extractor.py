# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item"
"""
Self-Healing Pattern Extraction Tool for LearningAgent.

Extracts successful patterns and strategies from self-healing system actions.
Now outputs unified CodingPattern format for the Infinite Intelligence Amplifier.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from shared.type_definitions.json import JSONValue
import logging
from collections import defaultdict
from learning_agent.json_utils import (
    is_dict, is_list, is_str, is_int, is_float, is_number, is_none,
    safe_get, safe_get_dict, safe_get_list, safe_get_str, safe_get_int, safe_get_float,
    ensure_dict, ensure_list, ensure_str
)
from shared.models.patterns import (
    HealingPattern,
    PatternExtraction,
    DataCollectionSummary,
    SelfHealingEvent,
    LearningObject,
    PatternType,
    ValidationStatus,
    EventStatus
)
# Import the unified CodingPattern format
from pattern_intelligence.coding_pattern import (
    CodingPattern,
    ProblemContext,
    SolutionApproach,
    EffectivenessMetric,
    PatternMetadata
)

logger = logging.getLogger(__name__)


class SelfHealingPatternExtractor(BaseTool):  # mypy: disable-error-code="misc"
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

            if not data_collection.total_events:
                return json.dumps({
                    "status": "no_data",
                    "message": "No self-healing events found in specified time window",
                    "time_window": self.time_window,
                    "sources_checked": data_collection.sources_checked
                }, indent=2)

            # Extract patterns (now returns CodingPattern objects)
            patterns = self._extract_successful_patterns(data_collection)

            # Score and validate patterns
            validated_patterns = self._validate_patterns(patterns, data_collection)

            # Generate actionable insights
            insights = self._generate_actionable_insights(validated_patterns)

            # Create learning objects
            learning_objects = self._create_learning_objects(validated_patterns, insights)

            # Support both formats during transition
            legacy_patterns = []
            coding_patterns = []
            for p in validated_patterns:
                if isinstance(p, CodingPattern):
                    coding_patterns.append(p.to_dict())
                    # Also create legacy format for backward compatibility
                    legacy_patterns.append(HealingPattern.from_coding_pattern(p).model_dump())
                elif isinstance(p, HealingPattern):
                    legacy_patterns.append(p.model_dump())
                    # Convert to new format
                    coding_patterns.append(p.to_coding_pattern().to_dict())

            result = {
                "extraction_timestamp": datetime.now().isoformat(),
                "time_window": self.time_window,
                "data_summary": {
                    "total_events": data_collection.total_events,
                    "successful_events": data_collection.successful_events,
                    "sources_analyzed": data_collection.sources_checked,
                    "success_rate": data_collection.success_rate
                },
                "patterns_found": len(validated_patterns),
                "patterns": legacy_patterns,  # Legacy format for compatibility
                "coding_patterns": coding_patterns,  # New unified format
                "insights": insights,
                "learning_objects": [lo.model_dump() for lo in learning_objects],
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

    def _collect_self_healing_data(self, time_boundary: datetime) -> DataCollectionSummary:
        """Collect self-healing data from various sources."""
        events_list = []
        sources_checked = []

        if self.data_sources in ['all', 'logs']:
            log_data = self._collect_from_logs(time_boundary)
            events_list.extend(log_data)
            sources_checked.append('logs')

        if self.data_sources in ['all', 'telemetry']:
            telemetry_data = self._collect_from_telemetry(time_boundary)
            events_list.extend(telemetry_data)
            sources_checked.append('telemetry')

        if self.data_sources in ['all', 'agent_memory']:
            memory_data = self._collect_from_agent_memory(time_boundary)
            events_list.extend(memory_data)
            sources_checked.append('agent_memory')

        # Process collected data and create structured events
        structured_events = []
        for event_data in events_list:
            try:
                structured_event = self._create_structured_event(event_data)
                structured_events.append(structured_event)
            except Exception as e:
                logger.warning(f"Error structuring event: {e}")
                continue

        # Count successful events
        successful_events = [e for e in structured_events if self._is_successful_structured_event(e)]

        return DataCollectionSummary(
            events=structured_events,
            sources_checked=sources_checked,
            total_events=len(structured_events),
            successful_events=len(successful_events)
        )

    def _create_structured_event(self, event_data: Dict[str, JSONValue]) -> SelfHealingEvent:
        """Create a structured SelfHealingEvent from raw event data."""
        # Extract timestamp
        timestamp_value = safe_get(event_data, 'timestamp')
        if timestamp_value:
            try:
                if is_str(timestamp_value):
                    timestamp = datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                else:
                    timestamp = timestamp_value if isinstance(timestamp_value, datetime) else datetime.now()
            except (ValueError, TypeError) as e:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Map status from string to EventStatus enum
        status_str = safe_get_str(event_data, 'status', 'pending').lower()
        if status_str in ['success', 'successful']:
            status = EventStatus.SUCCESS
        elif status_str in ['resolved', 'completed']:
            status = EventStatus.RESOLVED
        elif status_str in ['failed', 'error']:
            status = EventStatus.FAILED
        else:
            status = EventStatus.PENDING

        return SelfHealingEvent(
            event_id=safe_get_str(event_data, 'event_id', f"event_{int(timestamp.timestamp())}"),
            timestamp=timestamp,
            source=safe_get_str(event_data, 'source', 'unknown'),
            event_type=safe_get_str(event_data, 'event_type', 'unknown'),
            status=status,
            trigger_name=safe_get_str(event_data, 'trigger_name') if safe_get(event_data, 'trigger_name') else None,
            action_name=safe_get_str(event_data, 'action_name') if safe_get(event_data, 'action_name') else None,
            trigger_type=safe_get_str(event_data, 'trigger_type') if safe_get(event_data, 'trigger_type') else None,
            action_type=safe_get_str(event_data, 'action_type') if safe_get(event_data, 'action_type') else None,
            content=safe_get_str(event_data, 'content') if safe_get(event_data, 'content') else None,
            raw_line=safe_get_str(event_data, 'raw_line') if safe_get(event_data, 'raw_line') else None,
            file=safe_get_str(event_data, 'file') if safe_get(event_data, 'file') else None,
            component=safe_get_str(event_data, 'component') if safe_get(event_data, 'component') else None,
            agent=safe_get_str(event_data, 'agent') if safe_get(event_data, 'agent') else None,
            severity=safe_get_str(event_data, 'severity') if safe_get(event_data, 'severity') else None,
            error_type=safe_get_str(event_data, 'error_type') if safe_get(event_data, 'error_type') else None,
            line_number=safe_get_int(event_data, 'line_number') if safe_get(event_data, 'line_number') else None,
            extracted_timestamp=safe_get_str(event_data, 'extracted_timestamp') if safe_get(event_data, 'extracted_timestamp') else None
        )

    def _is_successful_structured_event(self, event: SelfHealingEvent) -> bool:
        """Check if structured event represents success."""
        return event.status in [EventStatus.SUCCESS, EventStatus.SUCCESSFUL, EventStatus.RESOLVED, EventStatus.COMPLETED]

    def _collect_from_logs(self, time_boundary: datetime) -> List[Dict[str, JSONValue]]:
        """Collect self-healing events from log files."""
        events: List[Dict[str, JSONValue]] = []
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

    def _collect_from_telemetry(self, time_boundary: datetime) -> List[Dict[str, JSONValue]]:
        """Collect self-healing events from telemetry data."""
        events: List[Dict[str, JSONValue]] = []
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
                            parsed_data = json.load(f)
                            data = ensure_dict(parsed_data) if not isinstance(parsed_data, list) else parsed_data

                            if isinstance(data, list):
                                for item in data:
                                    item_dict = ensure_dict(item)
                                    if self._is_self_healing_event(item_dict, time_boundary):
                                        events.append(item_dict)
                            elif self._is_self_healing_event(data, time_boundary):
                                events.append(data)

        except Exception as e:
            logger.warning(f"Error collecting from telemetry: {e}")

        return events

    def _collect_from_agent_memory(self, time_boundary: datetime) -> List[Dict[str, JSONValue]]:
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

    def _parse_log_file(self, filepath: str, time_boundary: datetime) -> List[Dict[str, JSONValue]]:
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
                                parsed_event = json.loads(json_part)
                                event = ensure_dict(parsed_event)
                                if self._is_self_healing_event(event, time_boundary):
                                    events.append(event)
                        except (json.JSONDecodeError, ValueError, KeyError) as e:
                            # Parse as structured log
                            event = self._parse_structured_log_line(line, time_boundary)
                            if event:
                                events.append(event)

        except Exception as e:
            logger.warning(f"Error parsing log file {filepath}: {e}")

        return events

    def _parse_structured_log_line(self, line: str, time_boundary: datetime) -> Optional[Dict[str, JSONValue]]:
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
                    except (ValueError, TypeError) as e:
                        continue

            # Extract key information
            event: Dict[str, JSONValue] = {
                'event_id': f"log_{int(datetime.now().timestamp())}",
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

        except (AttributeError, IndexError, ValueError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to parse self-healing event from line: {e}")
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error parsing self-healing event: {e}")
            return None

    def _extract_healing_from_session(self, filepath: str) -> List[Dict[str, JSONValue]]:
        """Extract self-healing events from session transcript."""
        events = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for self-healing related content
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['self-healing', 'trigger', 'intelligent system', 'workflow']):
                    event: Dict[str, JSONValue] = {
                        'event_id': f"session_{int(datetime.now().timestamp())}",
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

    def _is_self_healing_event(self, event: Dict[str, JSONValue], time_boundary: datetime) -> bool:
        """Check if event is related to self-healing and within time window."""
        # Check timestamp
        timestamp_value = safe_get(event, 'timestamp')
        if timestamp_value:
            try:
                timestamp_str = ensure_str(timestamp_value)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                if timestamp < time_boundary:
                    return False
            except (ValueError, TypeError) as e:
                pass

        # Check if it's self-healing related
        text_content = str(event).lower()
        healing_keywords = ['self_healing', 'trigger', 'intelligent_system', 'workflow', 'dispatcher', 'pattern_analyzer']

        return any(keyword in text_content for keyword in healing_keywords)

    def _is_successful_event(self, event: Dict[str, JSONValue]) -> bool:
        """Determine if an event represents a successful self-healing action."""
        status = safe_get_str(event, 'status').lower()
        if status in ['success', 'successful', 'resolved', 'completed']:
            return True

        # Check for success indicators in content
        content_val = safe_get_str(event, 'content')
        raw_line_val = safe_get_str(event, 'raw_line')
        content = (content_val + raw_line_val).lower()
        success_indicators = ['resolved', 'fixed', 'successful', 'completed', 'recovered']

        return any(indicator in content for indicator in success_indicators)

    def _extract_successful_patterns(self, data_collection: DataCollectionSummary) -> List[CodingPattern]:
        """Extract patterns from successful self-healing events - now returns CodingPattern objects."""
        patterns: List[CodingPattern] = []
        events = data_collection.events
        successful_events = [e for e in events if self._is_successful_structured_event(e)]

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

    def _extract_trigger_action_patterns(self, events: List[SelfHealingEvent]) -> List[CodingPattern]:
        """Extract trigger-action correlation patterns - now returns CodingPattern."""
        patterns = []

        # Group by trigger type and action type
        trigger_action_groups = defaultdict(list)

        for event in events:
            trigger = event.trigger_name or event.trigger_type or 'unknown'
            action = event.action_name or event.action_type or 'unknown'

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
                    # Create CodingPattern instead of HealingPattern
                    context = ProblemContext(
                        description=f"Self-healing trigger '{trigger}' detected",
                        domain="self_healing",
                        constraints=[],
                        symptoms=[trigger],
                        scale=f"{len(combo_events)} occurrences",
                        urgency="high" if success_rate > 0.9 else "medium"
                    )

                    solution = SolutionApproach(
                        approach=f"Execute action '{action}' in response to trigger",
                        implementation=f"When '{trigger}' is detected, automatically execute '{action}'",
                        tools=["self_healing_system"],
                        reasoning=f"This trigger-action pair has {success_rate:.1%} success rate",
                        code_examples=[],
                        dependencies=[],
                        alternatives=[]
                    )

                    outcome = EffectivenessMetric(
                        success_rate=success_rate,
                        performance_impact=None,
                        maintainability_impact="Reduces manual intervention",
                        user_impact="Automatic issue resolution",
                        technical_debt=None,
                        adoption_rate=len(combo_events),
                        longevity=None,
                        confidence=self.pattern_confidence
                    )

                    metadata = PatternMetadata(
                        pattern_id=f'trigger_action_{trigger}_{action}',
                        discovered_timestamp=datetime.now().isoformat(),
                        source="self_healing:trigger_action",
                        discoverer="self_healing_pattern_extractor",
                        last_applied=None,
                        application_count=len(combo_events),
                        validation_status="validated" if success_rate > 0.8 else "unvalidated",
                        tags=["trigger_action", "self_healing", trigger, action],
                        related_patterns=[]
                    )

                    patterns.append(CodingPattern(
                        context=context,
                        solution=solution,
                        outcome=outcome,
                        metadata=metadata
                    ))

        return patterns

    def _extract_context_patterns(self, events: List[SelfHealingEvent]) -> List[CodingPattern]:
        """Extract context-based success patterns."""
        patterns = []

        # Group by context characteristics
        context_groups = defaultdict(list)

        for event in events:
            context_keys = []

            # Extract context information
            if event.error_type:
                context_keys.append(f"error:{event.error_type}")
            if event.agent:
                context_keys.append(f"agent:{event.agent}")
            if event.component:
                context_keys.append(f"component:{event.component}")
            if event.severity:
                context_keys.append(f"severity:{event.severity}")

            # Group by context combinations
            for context_key in context_keys:
                context_groups[context_key].append(event)

        # Find patterns with sufficient occurrences
        for context, context_events in context_groups.items():
            if len(context_events) >= self.min_occurrences:
                success_rate = len(context_events) / len(events)

                if success_rate >= self.success_threshold:
                    # Create CodingPattern for context pattern
                    problem_context = ProblemContext(
                        description=f"Issues in context: {context}",
                        domain="self_healing_context",
                        constraints=[],
                        symptoms=[context],
                        scale=f"{len(context_events)} occurrences",
                        urgency="medium"
                    )

                    solution = SolutionApproach(
                        approach=f"Context-aware resolution for {context}",
                        implementation=f"Apply context-specific handling when in {context}",
                        tools=["self_healing_system"],
                        reasoning=f"This context has {success_rate:.1%} success rate",
                        code_examples=[],
                        dependencies=[],
                        alternatives=[]
                    )

                    outcome = EffectivenessMetric(
                        success_rate=success_rate,
                        performance_impact=None,
                        maintainability_impact="Context-aware issue resolution",
                        user_impact=None,
                        technical_debt=None,
                        adoption_rate=len(context_events),
                        longevity=None,
                        confidence=min(0.8, len(context_events) / 8)
                    )

                    metadata = PatternMetadata(
                        pattern_id=f'context_{context.replace(":", "_")}',
                        discovered_timestamp=datetime.now().isoformat(),
                        source="self_healing:context",
                        discoverer="self_healing_pattern_extractor",
                        last_applied=None,
                        application_count=len(context_events),
                        validation_status="validated" if success_rate > 0.8 else "unvalidated",
                        tags=["context_pattern", "self_healing", context],
                        related_patterns=[]
                    )

                    patterns.append(CodingPattern(
                        context=problem_context,
                        solution=solution,
                        outcome=outcome,
                        metadata=metadata
                    ))

        return patterns

    def _extract_timing_patterns(self, events: List[SelfHealingEvent]) -> List[CodingPattern]:
        """Extract timing-based patterns."""
        patterns = []

        # Group by time of day
        time_groups = defaultdict(list)

        for event in events:
            try:
                timestamp = event.timestamp
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
            except (AttributeError, TypeError) as e:
                continue

        # Analyze time patterns
        for time_period, period_events in time_groups.items():
            if len(period_events) >= self.min_occurrences:
                success_rate = len(period_events) / len(events)

                patterns.append(HealingPattern(
                    pattern_id=f'timing_{time_period}',
                    pattern_type=PatternType.TIMING,
                    time_period=time_period,
                    occurrences=len(period_events),
                    success_rate=success_rate,
                    confidence=min(0.7, len(period_events) / 5),
                    description=f'Higher success rate during {time_period}',
                    evidence=[e.model_dump() for e in period_events[:2]],
                    effectiveness_score=success_rate * min(1.0, len(period_events) / self.min_occurrences),
                    validation_status=ValidationStatus.PENDING
                ))

        return patterns

    def _extract_sequence_patterns(self, events: List[SelfHealingEvent]) -> List[CodingPattern]:
        """Extract sequential action patterns."""
        patterns = []

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Look for action sequences (events within short time windows)
        sequence_window = timedelta(minutes=30)  # 30-minute window for sequences
        sequences = []

        for i in range(len(sorted_events) - 1):
            try:
                current_time = sorted_events[i].timestamp
                next_time = sorted_events[i+1].timestamp

                if next_time - current_time <= sequence_window:
                    current_action = sorted_events[i].action_name or sorted_events[i].action_type or ''
                    next_action = sorted_events[i+1].action_name or sorted_events[i+1].action_type or ''

                    if current_action and next_action:
                        sequence = f"{current_action} -> {next_action}"
                        sequences.append({
                            'sequence': sequence,
                            'events': [sorted_events[i], sorted_events[i+1]],
                            'time_gap': (next_time - current_time).total_seconds()
                        })
            except (AttributeError, TypeError, IndexError) as e:
                continue

        # Find common sequences
        sequence_counts = defaultdict(list)
        for seq_data in sequences:
            sequence_counts[seq_data['sequence']].append(seq_data)

        for sequence, seq_instances in sequence_counts.items():
            if len(seq_instances) >= self.min_occurrences:
                avg_time_gap = sum(s['time_gap'] for s in seq_instances) / len(seq_instances)

                patterns.append(HealingPattern(
                    pattern_id=f'sequence_{sequence.replace(" -> ", "_to_")}',
                    pattern_type=PatternType.SEQUENCE,
                    sequence=sequence,
                    occurrences=len(seq_instances),
                    confidence=min(0.8, len(seq_instances) / 6),
                    description=f'Successful action sequence: {sequence}',
                    evidence=seq_instances[:2],
                    effectiveness_score=len(seq_instances) / self.min_occurrences,
                    validation_status=ValidationStatus.PENDING,
                    success_rate=1.0  # Sequences from successful events
                ))

        return patterns

    def _validate_patterns(self, patterns: List[CodingPattern], data_collection: DataCollectionSummary) -> List[CodingPattern]:
        """Validate and score patterns based on confidence and effectiveness."""
        validated_patterns = []

        for pattern in patterns:
            # Calculate overall confidence score
            base_confidence = pattern.confidence
            effectiveness = pattern.effectiveness_score
            occurrence_weight = min(1.0, pattern.occurrences / (self.min_occurrences * 2))

            # Combined confidence score
            overall_confidence = (base_confidence * 0.4 + effectiveness * 0.4 + occurrence_weight * 0.2)

            # Update the pattern with overall confidence
            pattern.overall_confidence = overall_confidence

            if overall_confidence >= self.pattern_confidence:
                pattern.validation_status = ValidationStatus.VALIDATED
                validated_patterns.append(pattern)
            else:
                pattern.validation_status = ValidationStatus.INSUFFICIENT_CONFIDENCE

        return validated_patterns

    def _generate_actionable_insights(self, patterns: List[CodingPattern]) -> List[Dict[str, JSONValue]]:
        """Generate actionable insights from validated patterns."""
        insights = []

        # Group patterns by type
        pattern_types: Dict[str, List[HealingPattern]] = defaultdict(list)
        for pattern in patterns:
            pattern_types[pattern.pattern_type.value].append(pattern)

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
                    'patterns': [p.pattern_id for p in type_patterns],
                    'confidence': sum(p.overall_confidence for p in type_patterns) / len(type_patterns)
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
                    'patterns': [p.pattern_id for p in type_patterns],
                    'confidence': sum(p.overall_confidence for p in type_patterns) / len(type_patterns)
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
                    'patterns': [p.pattern_id for p in type_patterns],
                    'confidence': sum(p.overall_confidence for p in type_patterns) / len(type_patterns)
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
                    'patterns': [p.pattern_id for p in type_patterns],
                    'confidence': sum(p.overall_confidence for p in type_patterns) / len(type_patterns)
                })

        return insights

    def _create_learning_objects(self, patterns: List[CodingPattern], insights: List[Dict[str, JSONValue]]) -> List[LearningObject]:
        """Create structured learning objects for VectorStore storage."""
        learning_objects = []

        for pattern in patterns:
            learning_object = LearningObject(
                learning_id=f"self_healing_pattern_{pattern.pattern_id}_{int(datetime.now().timestamp())}",
                type='successful_pattern',
                category='self_healing',
                title=f"Self-Healing Pattern: {pattern.pattern_type.value.title()}",
                description=pattern.description,
                actionable_insight=self._create_actionable_insight_for_pattern(pattern),
                confidence=pattern.overall_confidence,
                keywords=[
                    'self_healing',
                    pattern.pattern_type.value,
                    'successful_pattern',
                    'automation'
                ],
                patterns={
                    'triggers': self._extract_pattern_triggers(pattern),
                    'actions': self._extract_pattern_actions(pattern),
                    'conditions': self._extract_pattern_conditions(pattern),
                    'outcomes': ['successful_resolution', 'pattern_validated']
                },
                metadata={
                    'created_timestamp': datetime.now().isoformat(),
                    'source_pattern_id': pattern.pattern_id,
                    'pattern_data': pattern.model_dump(),
                    'extraction_method': 'self_healing_pattern_extractor',
                    'time_window': self.time_window,
                    'occurrences': pattern.occurrences,
                    'effectiveness_score': pattern.effectiveness_score
                },
                application_criteria=self._generate_application_criteria_for_pattern(pattern),
                success_metrics=[
                    f"Pattern application success rate >= {pattern.success_rate:.2f}",
                    "Resolution time improvement",
                    "Reduced manual intervention needed"
                ]
            )
            learning_objects.append(learning_object)

        return learning_objects

    def _create_actionable_insight_for_pattern(self, pattern: HealingPattern) -> str:
        """Create actionable insight text for a pattern."""
        pattern_type = pattern.pattern_type

        if pattern_type == PatternType.TRIGGER_ACTION:
            return f"When trigger '{pattern.trigger}' occurs, prioritize action '{pattern.action}' for highest success rate ({pattern.success_rate:.1%})"
        elif pattern_type == PatternType.CONTEXT:
            return f"In context '{pattern.context}', current resolution approach shows {pattern.success_rate:.1%} success rate - maintain and optimize this approach"
        elif pattern_type == PatternType.TIMING:
            return f"Schedule self-healing actions during {pattern.time_period} for optimal success rates"
        elif pattern_type == PatternType.SEQUENCE:
            return f"Implement action sequence '{pattern.sequence}' as a workflow template for consistent results"
        else:
            return f"Apply this {pattern_type.value} pattern when similar conditions are detected"

    def _extract_pattern_triggers(self, pattern: HealingPattern) -> List[str]:
        """Extract trigger information from pattern."""
        triggers = []
        if pattern.trigger:
            triggers.append(pattern.trigger)
        if pattern.context:
            triggers.append(f"context_match_{pattern.context}")
        if pattern.time_period:
            triggers.append(f"time_period_{pattern.time_period}")
        return triggers or ['pattern_conditions_met']

    def _extract_pattern_actions(self, pattern: HealingPattern) -> List[str]:
        """Extract action information from pattern."""
        actions = []
        if pattern.action:
            actions.append(pattern.action)
        if pattern.sequence:
            actions.extend(pattern.sequence.split(' -> '))
        return actions or ['apply_pattern']

    def _extract_pattern_conditions(self, pattern: HealingPattern) -> List[str]:
        """Extract condition information from pattern."""
        conditions = []
        conditions.append(f"success_rate >= {pattern.success_rate:.2f}")
        conditions.append(f"occurrences >= {pattern.occurrences}")
        return conditions or ['pattern_validation_passed']

    def _generate_application_criteria_for_pattern(self, pattern: HealingPattern) -> List[str]:
        """Generate application criteria for pattern."""
        criteria = [
            f"Pattern confidence >= {pattern.overall_confidence:.2f}",
            "Similar context or trigger detected",
            "No conflicting patterns active"
        ]

        pattern_type = pattern.pattern_type
        if pattern_type == PatternType.TRIGGER_ACTION:
            criteria.append(f"Trigger type matches: {pattern.trigger}")
        elif pattern_type == PatternType.CONTEXT:
            criteria.append(f"Context matches: {pattern.context}")
        elif pattern_type == PatternType.TIMING:
            criteria.append(f"Current time period: {pattern.time_period}")

        return criteria

    def _generate_recommendations(self, patterns: List[CodingPattern]) -> List[Dict[str, JSONValue]]:
        """Generate specific recommendations based on patterns."""
        recommendations = []

        # High-confidence patterns get priority implementation
        high_confidence_patterns = [p for p in patterns if p.overall_confidence > 0.8]

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