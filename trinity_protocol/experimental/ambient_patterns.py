"""Ambient Pattern Detection - EXPERIMENTAL

⚠️ **Status**: Experimental / Prototype
⚠️ **Production Readiness**: NOT READY

**Purpose**:
Pattern detection for ambient transcriptions (WITNESS agent).
Extends WITNESS with ambient-specific pattern detection:
- Recurring topics (mentioned N times)
- Project mentions
- Frustrations
- Action items

**Privacy Concerns**:
- Processes ambient conversation data (always-on listening)
- Pattern detection may capture sensitive topics
- No explicit user consent flow implemented
- Cross-session pattern storage (persistent tracking)

**External Dependencies**:
- Firestore (for persistent pattern storage)
- conversation_context module (experimental dependency)

**Known Issues**:
- Low test coverage (~20%)
- No error handling for pattern storage failures
- Privacy consent flow missing
- Topic extraction uses basic regex (low accuracy)
- No rate limiting on pattern publishing
- Cross-session learning lacks privacy controls

**To Upgrade to Production**:
See: docs/TRINITY_UPGRADE_CHECKLIST.md

Required steps:
- [ ] 100% test coverage (currently ~20%)
- [ ] Privacy consent flow implementation
- [ ] Error handling (Result<T,E> pattern throughout)
- [ ] Improved topic extraction (NLP-based)
- [ ] Rate limiting and deduplication
- [ ] Constitutional compliance (Articles I-V)
- [ ] Security review (pattern storage access controls)
- [ ] User control over pattern retention

**Constitutional Compliance (Partial)**:
- Article I: Complete context (full conversation window before detection)
- Article II: Strict typing (Pydantic models) ✅
- Article IV: Persist patterns to Firestore for learning ⚠️ (privacy concerns)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import re

from trinity_protocol.experimental.conversation_context import ConversationContext
from trinity_protocol.core.models.patterns import (
    DetectedPattern,
    PatternType,
    PatternContext,
    IntentClassification,
    RecurrenceMetrics
)
from shared.persistent_store import PersistentStore


class AmbientPatternDetector:
    """
    Ambient-specific pattern detection for WITNESS.

    Analyzes conversation context to detect:
    - Recurring topics (mentioned 3+ times)
    - Project mentions (actionable work)
    - Frustrations (user pain points)
    - Action items (explicit tasks)
    """

    def __init__(
        self,
        conversation_context: ConversationContext,
        pattern_store: PersistentStore,
        recurrence_threshold: int = 3,
        min_confidence: float = 0.7
    ):
        """
        Initialize ambient pattern detector.

        Args:
            conversation_context: Conversation context manager
            pattern_store: Persistent pattern storage
            recurrence_threshold: Minimum mentions for recurrence pattern
            min_confidence: Minimum confidence for pattern publishing
        """
        self.conversation_context = conversation_context
        self.pattern_store = pattern_store
        self.recurrence_threshold = recurrence_threshold
        self.min_confidence = min_confidence

        # Pattern keywords and weights
        self._init_pattern_keywords()

    def _init_pattern_keywords(self) -> None:
        """Initialize pattern detection keywords."""
        self.pattern_keywords = {
            PatternType.FRUSTRATION: {
                "keywords": [
                    "frustrat", "annoying", "taking forever", "not working",
                    "broken", "confusing", "waste of time", "stuck",
                    "why doesn't", "this should work", "unclear"
                ],
                "weight": 0.3
            },
            PatternType.ACTION_ITEM: {
                "keywords": [
                    "remind me", "need to", "have to", "must",
                    "todo", "task", "action item", "make sure",
                    "don't forget", "remember to"
                ],
                "weight": 0.35
            },
            PatternType.PROJECT_MENTION: {
                "keywords": [
                    "working on", "project", "building", "implementing",
                    "developing", "creating", "need to finish", "deadline",
                    "completing", "wrapping up"
                ],
                "weight": 0.3
            },
            PatternType.FEATURE_REQUEST: {
                "keywords": [
                    "i need", "can we add", "would be nice", "feature",
                    "please implement", "wish i could", "automate",
                    "make it easier", "improve"
                ],
                "weight": 0.35
            },
            PatternType.WORKFLOW_BOTTLENECK: {
                "keywords": [
                    "manually", "repetitive", "tedious", "time-consuming",
                    "slow process", "keeps happening", "every time",
                    "always have to", "inefficient"
                ],
                "weight": 0.3
            }
        }

    def detect_patterns(
        self,
        transcription_text: str,
        timestamp: datetime
    ) -> List[DetectedPattern]:
        """
        Detect patterns from new transcription.

        Analyzes both the new transcription and conversation context
        to identify meaningful patterns.

        Args:
            transcription_text: New transcription text
            timestamp: Transcription timestamp

        Returns:
            List of detected patterns above confidence threshold
        """
        detected_patterns: List[DetectedPattern] = []

        # Extract topics from transcription
        topics = self._extract_topics(transcription_text)

        # Track topic mentions in context
        for topic in topics:
            self.conversation_context.track_topic_mention(topic, timestamp)

        # Check for recurring topics
        recurring = self._detect_recurring_topics(topics, timestamp)
        detected_patterns.extend(recurring)

        # Check for specific pattern types
        for pattern_type in self.pattern_keywords:
            pattern = self._detect_pattern_type(
                pattern_type,
                transcription_text,
                timestamp
            )
            if pattern:
                detected_patterns.append(pattern)

        # Filter by confidence threshold
        return [
            p for p in detected_patterns
            if p.confidence >= self.min_confidence
        ]

    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract topics from transcription text.

        Uses simple noun phrase extraction and keyword matching.

        Args:
            text: Transcription text

        Returns:
            List of extracted topics
        """
        topics = []

        # Extract quoted phrases (often important topics)
        quoted_pattern = r'"([^"]+)"'
        quotes = re.findall(quoted_pattern, text)
        topics.extend(quotes)

        # Extract capitalized phrases (likely proper nouns/topics)
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        capitalized = re.findall(capitalized_pattern, text)
        topics.extend(capitalized)

        # Extract key noun phrases (simple pattern)
        # "the X", "my X", "our X"
        noun_phrase_pattern = r'\b(?:the|my|our|this|that)\s+([a-z]+(?:\s+[a-z]+){0,2})\b'
        noun_phrases = re.findall(noun_phrase_pattern, text.lower())
        topics.extend(noun_phrases)

        # Deduplicate and filter short topics
        unique_topics = list(set(
            topic.strip()
            for topic in topics
            if len(topic.strip()) > 3
        ))

        return unique_topics

    def _detect_recurring_topics(
        self,
        topics: List[str],
        timestamp: datetime
    ) -> List[DetectedPattern]:
        """
        Detect recurring topics (mentioned multiple times).

        Args:
            topics: Topics from current transcription
            timestamp: Current timestamp

        Returns:
            List of detected recurring topic patterns
        """
        patterns = []

        for topic in topics:
            mention_count = self.conversation_context.get_topic_mention_count(
                topic,
                time_window_minutes=self.conversation_context.window_minutes
            )

            # Check if meets recurrence threshold
            if mention_count >= self.recurrence_threshold:
                # Get topic cluster for details
                cluster = self.conversation_context.get_topic_cluster(
                    topic,
                    time_window_hours=24.0
                )

                if cluster:
                    # Calculate confidence based on recurrence
                    confidence = min(1.0, 0.6 + (mention_count / 10.0))

                    # Generate context summary
                    context_summary = self.conversation_context.get_context_summary(
                        max_length=500
                    )

                    pattern = DetectedPattern(
                        pattern_id=f"recurring_{topic}_{int(timestamp.timestamp())}",
                        pattern_type=PatternType.RECURRING_TOPIC,
                        topic=topic,
                        confidence=confidence,
                        mention_count=mention_count,
                        first_mention=cluster.mention_timestamps[0],
                        last_mention=timestamp,
                        context_summary=context_summary,
                        keywords=[topic],
                        urgency="MEDIUM" if mention_count >= 5 else "LOW"
                    )

                    patterns.append(pattern)

        return patterns

    def _detect_pattern_type(
        self,
        pattern_type: PatternType,
        text: str,
        timestamp: datetime
    ) -> Optional[DetectedPattern]:
        """
        Detect specific pattern type in transcription.

        Args:
            pattern_type: Pattern type to detect
            text: Transcription text
            timestamp: Transcription timestamp

        Returns:
            DetectedPattern if found, None otherwise
        """
        text_lower = text.lower()
        config = self.pattern_keywords[pattern_type]

        # Count keyword matches
        matched_keywords = []
        for keyword in config["keywords"]:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        # Calculate confidence
        if not matched_keywords:
            return None

        # Base confidence from keyword count
        # Single keyword match should reach threshold
        keyword_score = len(matched_keywords) * config["weight"]
        # Boost base score to make single matches detectable
        confidence = min(1.0, 0.6 + keyword_score)

        # Extract topic (use first matched keyword as proxy)
        topic = matched_keywords[0]

        # Determine urgency based on pattern type
        urgency = self._determine_urgency(pattern_type, matched_keywords)

        # Get context summary
        context_summary = self.conversation_context.get_context_summary(
            max_length=500
        )

        return DetectedPattern(
            pattern_id=f"{pattern_type.value}_{int(timestamp.timestamp())}",
            pattern_type=pattern_type,
            topic=topic,
            confidence=confidence,
            mention_count=1,  # Single mention for non-recurring patterns
            first_mention=timestamp,
            last_mention=timestamp,
            context_summary=context_summary,
            keywords=matched_keywords,
            sentiment=self._detect_sentiment(pattern_type),
            urgency=urgency
        )

    def _determine_urgency(
        self,
        pattern_type: PatternType,
        keywords: List[str]
    ) -> str:
        """
        Determine urgency level based on pattern type and keywords.

        Args:
            pattern_type: Pattern type
            keywords: Matched keywords

        Returns:
            Urgency level (LOW, MEDIUM, HIGH, CRITICAL)
        """
        # High urgency keywords
        high_urgency_keywords = ["critical", "urgent", "immediately", "asap", "now"]

        if any(kw in keywords for kw in high_urgency_keywords):
            return "HIGH"

        # Pattern-specific urgency
        urgency_map = {
            PatternType.FRUSTRATION: "MEDIUM",
            PatternType.ACTION_ITEM: "MEDIUM",
            PatternType.PROJECT_MENTION: "MEDIUM",
            PatternType.FEATURE_REQUEST: "LOW",
            PatternType.WORKFLOW_BOTTLENECK: "MEDIUM",
            PatternType.RECURRING_TOPIC: "LOW"
        }

        return urgency_map.get(pattern_type, "LOW")

    def _detect_sentiment(self, pattern_type: PatternType) -> str:
        """
        Detect sentiment based on pattern type.

        Args:
            pattern_type: Pattern type

        Returns:
            Sentiment (positive, negative, neutral)
        """
        sentiment_map = {
            PatternType.FRUSTRATION: "negative",
            PatternType.ACTION_ITEM: "neutral",
            PatternType.PROJECT_MENTION: "neutral",
            PatternType.FEATURE_REQUEST: "positive",
            PatternType.WORKFLOW_BOTTLENECK: "negative",
            PatternType.RECURRING_TOPIC: "neutral"
        }

        return sentiment_map.get(pattern_type, "neutral")

    def classify_intent(
        self,
        pattern: DetectedPattern
    ) -> IntentClassification:
        """
        Classify user intent from detected pattern.

        Args:
            pattern: Detected pattern

        Returns:
            IntentClassification for ARCHITECT
        """
        # Determine if action required
        action_required = pattern.pattern_type in [
            PatternType.ACTION_ITEM,
            PatternType.FRUSTRATION,
            PatternType.WORKFLOW_BOTTLENECK
        ] or pattern.mention_count >= 5

        # Map pattern type to intent type
        intent_type_map = {
            PatternType.RECURRING_TOPIC: "user_intent/recurring_topic",
            PatternType.PROJECT_MENTION: "user_intent/project",
            PatternType.FRUSTRATION: "user_intent/pain_point",
            PatternType.ACTION_ITEM: "user_intent/task",
            PatternType.FEATURE_REQUEST: "user_intent/feature_request",
            PatternType.WORKFLOW_BOTTLENECK: "user_intent/workflow_bottleneck"
        }

        intent_type = intent_type_map.get(
            pattern.pattern_type,
            "user_intent/unknown"
        )

        # Map urgency to priority
        priority_map = {
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "MEDIUM": "NORMAL",
            "LOW": "NORMAL"
        }
        priority = priority_map.get(pattern.urgency, "NORMAL")

        # Generate suggested action
        suggested_action = self._generate_suggested_action(pattern)

        # Generate rationale
        rationale = self._generate_rationale(pattern)

        return IntentClassification(
            intent_type=intent_type,
            confidence=pattern.confidence,
            action_required=action_required,
            priority=priority,
            suggested_action=suggested_action,
            rationale=rationale
        )

    def _generate_suggested_action(self, pattern: DetectedPattern) -> str:
        """Generate suggested action for ARCHITECT."""
        action_templates = {
            PatternType.RECURRING_TOPIC: f"Ask user about '{pattern.topic}' (mentioned {pattern.mention_count}x)",
            PatternType.PROJECT_MENTION: f"Offer help with project: {pattern.topic}",
            PatternType.FRUSTRATION: f"Address frustration: {pattern.topic}",
            PatternType.ACTION_ITEM: f"Create task: {pattern.topic}",
            PatternType.FEATURE_REQUEST: f"Implement feature: {pattern.topic}",
            PatternType.WORKFLOW_BOTTLENECK: f"Automate workflow: {pattern.topic}"
        }

        return action_templates.get(
            pattern.pattern_type,
            f"Investigate: {pattern.topic}"
        )

    def _generate_rationale(self, pattern: DetectedPattern) -> str:
        """Generate classification rationale."""
        # pattern_type is already a string due to use_enum_values=True
        pattern_type_str = pattern.pattern_type if isinstance(pattern.pattern_type, str) else pattern.pattern_type.value
        return (
            f"Detected {pattern_type_str} with {pattern.confidence:.2f} confidence. "
            f"Topic '{pattern.topic}' mentioned {pattern.mention_count} time(s). "
            f"Keywords: {', '.join(pattern.keywords[:3])}."
        )

    def persist_pattern(self, pattern: DetectedPattern) -> None:
        """
        Persist pattern to storage for cross-session learning.

        Args:
            pattern: Detected pattern to persist
        """
        # pattern_type is already a string due to use_enum_values=True
        pattern_type_str = pattern.pattern_type if isinstance(pattern.pattern_type, str) else pattern.pattern_type.value

        # Store using PersistentStore.store_pattern() method
        result = self.pattern_store.store_pattern(
            pattern_type=pattern_type_str,
            pattern_name=pattern.topic,
            content=pattern.context_summary,
            confidence=pattern.confidence,
            metadata={
                "pattern_id": pattern.pattern_id,
                "mention_count": pattern.mention_count,
                "first_mention": pattern.first_mention.isoformat(),
                "last_mention": pattern.last_mention.isoformat(),
                "keywords": pattern.keywords,
                "sentiment": pattern.sentiment,
                "urgency": pattern.urgency
            },
            evidence_count=pattern.mention_count
        )

        # Log if storage fails
        if result.is_err():
            error = result.unwrap_err()
            # Note: Using print instead of logger since logger might not be configured
            print(f"Warning: Failed to persist pattern: {error}")

    def get_recurrence_metrics(self, topic: str) -> Optional[RecurrenceMetrics]:
        """
        Get recurrence metrics for a topic.

        Args:
            topic: Topic to analyze

        Returns:
            RecurrenceMetrics if topic tracked, None otherwise
        """
        cluster = self.conversation_context.get_topic_cluster(
            topic,
            time_window_hours=168.0  # 7 days
        )

        if not cluster:
            return None

        # Calculate metrics
        total_mentions = cluster.mention_count
        unique_days = len(set(
            ts.date() for ts in cluster.mention_timestamps
        ))

        avg_mentions_per_day = total_mentions / max(1, unique_days)

        # Find peak mentions in single day
        mentions_by_day = {}
        for ts in cluster.mention_timestamps:
            day = ts.date()
            mentions_by_day[day] = mentions_by_day.get(day, 0) + 1

        peak_mentions = max(mentions_by_day.values()) if mentions_by_day else 0

        # Determine trend (simple: comparing first half vs second half)
        if len(cluster.mention_timestamps) >= 4:
            mid_point = len(cluster.mention_timestamps) // 2
            first_half_count = mid_point
            second_half_count = len(cluster.mention_timestamps) - mid_point

            if second_half_count > first_half_count * 1.2:
                trend = "increasing"
            elif second_half_count < first_half_count * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return RecurrenceMetrics(
            topic=topic,
            total_mentions=total_mentions,
            unique_days=unique_days,
            avg_mentions_per_day=avg_mentions_per_day,
            peak_mentions_in_day=peak_mentions,
            trend=trend,
            last_updated=datetime.now()
        )
