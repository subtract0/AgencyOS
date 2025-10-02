"""
Preference Learning for Trinity Protocol HITL System

Analyzes response patterns to learn when Alex says YES and optimize
question asking strategy.

Constitutional Compliance:
- Article IV: Continuous learning from all interactions
- Article II: Strict typing with Pydantic models
- Privacy: Learn from patterns, not individual content

Learning Goals:
1. Acceptance rate by question type
2. Best time of day to ask
3. Context patterns that correlate with YES
4. Response time patterns
5. Question priority sweet spot

Future Implementation:
- Firestore integration for cross-session persistence
- ML model for question acceptance prediction
- Adaptive rate limiting based on acceptance patterns
- Context-aware question prioritization
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.core.models.hitl import PreferencePattern, QuestionStats


class PreferenceLearning:
    """
    Learns Alex's preferences from HITL responses.

    Analyzes telemetry data to optimize question asking strategy.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        min_sample_size: int = 10,
        min_confidence: float = 0.7
    ):
        """
        Initialize preference learning system.

        Args:
            message_bus: MessageBus for consuming telemetry
            min_sample_size: Minimum samples before creating preference pattern
            min_confidence: Minimum confidence threshold for patterns
        """
        self.message_bus = message_bus
        self.min_sample_size = min_sample_size
        self.min_confidence = min_confidence

        # In-memory stats (would be Firestore in full implementation)
        self.stats = QuestionStats()
        self._response_history: List[Dict[str, Any]] = []

    async def run(self) -> None:
        """
        Main loop: subscribe to telemetry_stream and analyze responses.

        Builds preference patterns from YES/NO/LATER decisions.
        """
        async for message in self.message_bus.subscribe("telemetry_stream"):
            event_type = message.get("event_type")

            if event_type in ["response_yes", "response_no", "response_later"]:
                await self._process_response_event(message)

            # Acknowledge message
            await self.message_bus.ack(message["_message_id"])

    async def _process_response_event(self, event: Dict[str, Any]) -> None:
        """
        Process a response event and update statistics.

        Args:
            event: Telemetry event with response data
        """
        response_type = event.get("response_type")
        response_time = event.get("response_time_seconds", 0.0)

        # Update stats
        self.stats.total_questions_asked += 1

        if response_type == "YES":
            self.stats.yes_responses += 1
        elif response_type == "NO":
            self.stats.no_responses += 1
        elif response_type == "LATER":
            self.stats.later_responses += 1

        # Update average response time
        total_responses = (
            self.stats.yes_responses +
            self.stats.no_responses +
            self.stats.later_responses
        )
        if total_responses > 0:
            current_avg = self.stats.avg_response_time_seconds
            self.stats.avg_response_time_seconds = (
                (current_avg * (total_responses - 1) + response_time) / total_responses
            )

        # Store in history for pattern analysis
        self._response_history.append(event)

        # Analyze patterns when we have enough data
        if len(self._response_history) >= self.min_sample_size:
            await self._analyze_patterns()

    async def _analyze_patterns(self) -> None:
        """
        Analyze response history to extract preference patterns.

        Identifies:
        - Question types with high acceptance
        - Best times of day
        - Context keywords correlated with YES
        """
        # Group by question type
        by_type: Dict[str, List[str]] = {}
        for event in self._response_history:
            q_type = event.get("question_type", "unknown")
            r_type = event.get("response_type")

            if q_type not in by_type:
                by_type[q_type] = []
            by_type[q_type].append(r_type)

        # Calculate acceptance rates
        patterns: List[PreferencePattern] = []

        for q_type, responses in by_type.items():
            yes_count = responses.count("YES")
            no_count = responses.count("NO")
            total = yes_count + no_count

            if total >= self.min_sample_size:
                acceptance_rate = yes_count / total
                confidence = min(1.0, total / (self.min_sample_size * 2))

                if confidence >= self.min_confidence:
                    pattern = PreferencePattern(
                        pattern_id=f"pref_{q_type}_{datetime.now().timestamp()}",
                        question_type=q_type,
                        pattern_topic=q_type,
                        acceptance_rate=acceptance_rate,
                        sample_size=total,
                        confidence=confidence,
                        context_keywords=[],  # TODO: Extract from events
                        preferred_time_of_day=None  # TODO: Analyze timestamps
                    )
                    patterns.append(pattern)

        # Store patterns (would be Firestore in full implementation)
        # For now, just print summary
        if patterns:
            self._print_learning_summary(patterns)

    def _print_learning_summary(self, patterns: List[PreferencePattern]) -> None:
        """
        Print learning summary to console.

        Args:
            patterns: List of discovered preference patterns
        """
        print("\n" + "=" * 70)
        print("TRINITY PROTOCOL: Preference Learning Update")
        print("=" * 70)
        print(f"\nTotal Questions Asked: {self.stats.total_questions_asked}")
        print(f"Acceptance Rate: {self.stats.acceptance_rate:.1%}")
        print(f"Response Rate: {self.stats.response_rate:.1%}")
        print(f"Avg Response Time: {self.stats.avg_response_time_seconds:.1f}s")

        if patterns:
            print("\nLearned Preferences:")
            for pattern in patterns:
                print(f"\n  {pattern.question_type}:")
                print(f"    Acceptance: {pattern.acceptance_rate:.1%}")
                print(f"    Confidence: {pattern.confidence:.2f}")
                print(f"    Sample Size: {pattern.sample_size}")

        print("\n" + "=" * 70 + "\n")

    def get_stats(self) -> QuestionStats:
        """
        Get current question statistics.

        Returns:
            QuestionStats with current metrics
        """
        return self.stats

    def get_recommendation(self, question_type: str) -> Dict[str, Any]:
        """
        Get recommendation for asking a question.

        Args:
            question_type: Type of question to ask

        Returns:
            Dict with recommendation (should_ask, best_time, confidence)
        """
        # Analyze history for this question type
        type_responses = [
            e for e in self._response_history
            if e.get("question_type") == question_type
        ]

        if len(type_responses) < self.min_sample_size:
            # Not enough data, default to neutral recommendation
            return {
                "should_ask": True,
                "confidence": 0.5,
                "reason": "Insufficient data for this question type",
                "sample_size": len(type_responses)
            }

        # Calculate acceptance rate
        yes_count = sum(1 for e in type_responses if e.get("response_type") == "YES")
        total = len(type_responses)
        acceptance_rate = yes_count / total if total > 0 else 0.0

        # Recommend if acceptance rate is above threshold
        should_ask = acceptance_rate >= 0.5

        return {
            "should_ask": should_ask,
            "confidence": min(1.0, total / (self.min_sample_size * 2)),
            "acceptance_rate": acceptance_rate,
            "sample_size": total,
            "reason": f"Based on {total} samples, {acceptance_rate:.1%} acceptance rate"
        }


class FirestorePreferenceLearning(PreferenceLearning):
    """
    Future: Firestore-backed preference learning for persistence.

    Extension point for storing patterns in Firestore for
    cross-session learning and agent coordination.
    """

    def __init__(self, *args, firestore_client=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.firestore = firestore_client
        # Future: Initialize Firestore collections
        raise NotImplementedError("Firestore integration not yet implemented")
