"""
Alex Preference Learner for Trinity Protocol.

Analyzes response history to learn Alex's preferences and generate recommendations.

Philosophy: Let the data guide us - optimize for Alex's subjective helpfulness.

Constitutional Compliance:
- Article IV: Continuous learning from all interactions
- Article I: Complete context before making recommendations
- Article II: Strict typing, no shortcuts
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from trinity_protocol.models.preferences import (
    AlexPreferences,
    ContextualPattern,
    DayOfWeekPreference,
    PreferenceRecommendation,
    QuestionPreference,
    ResponseRecord,
    ResponseType,
    TimingPreference,
    TopicPreference,
    calculate_confidence,
    classify_day_of_week,
    classify_time_of_day,
    DayOfWeek,
    QuestionType,
    TimeOfDay,
    TopicCategory,
)


class AlexPreferenceLearner:
    """
    Learns Alex's preferences from response history.

    Core algorithm:
    1. Aggregate responses by dimension (question type, timing, topic, context)
    2. Calculate acceptance rates with confidence scoring
    3. Identify trends and patterns
    4. Generate actionable recommendations for ARCHITECT

    Stateless: Each analysis run is independent, operating on provided responses.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.6,
        min_sample_size: int = 10,
        trend_window_days: int = 7
    ):
        """
        Initialize preference learner.

        Args:
            min_confidence_threshold: Minimum confidence for recommendations (0.0-1.0)
            min_sample_size: Minimum responses for reliable pattern
            trend_window_days: Days to analyze for trend detection
        """
        self.min_confidence_threshold = min_confidence_threshold
        self.min_sample_size = min_sample_size
        self.trend_window_days = trend_window_days

    def analyze_responses(self, responses: List[ResponseRecord]) -> AlexPreferences:
        """
        Analyze response history and generate preference model.

        Article I: Complete context - analyzes ALL provided responses.

        Args:
            responses: List of response records

        Returns:
            AlexPreferences model with all dimensions populated
        """
        if not responses:
            return AlexPreferences()

        # Calculate overall metrics
        total_responses = len(responses)
        yes_count = sum(1 for r in responses if r.response_type == ResponseType.YES)
        overall_acceptance_rate = yes_count / total_responses if total_responses > 0 else 0.0

        # Analyze each dimension
        question_prefs = self._analyze_question_types(responses)
        timing_prefs = self._analyze_timing(responses)
        day_prefs = self._analyze_days_of_week(responses)
        topic_prefs = self._analyze_topics(responses)
        contextual_patterns = self._analyze_context(responses)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            question_prefs,
            timing_prefs,
            day_prefs,
            topic_prefs,
            contextual_patterns
        )

        return AlexPreferences(
            last_updated=datetime.now(),
            total_responses=total_responses,
            overall_acceptance_rate=overall_acceptance_rate,
            question_preferences=question_prefs,
            timing_preferences=timing_prefs,
            day_preferences=day_prefs,
            topic_preferences=topic_prefs,
            contextual_patterns=contextual_patterns,
            recommendations=recommendations
        )

    def _analyze_question_types(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, QuestionPreference]:
        """
        Analyze preferences by question type.

        Args:
            responses: Response records

        Returns:
            Dict mapping question type to preference metrics
        """
        # Group by question type
        by_type: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            # Handle both enum and string values
            q_type = r.question_type if isinstance(r.question_type, str) else r.question_type.value
            by_type[q_type].append(r)

        prefs = {}
        for question_type_str, type_responses in by_type.items():
            total = len(type_responses)
            yes_count = sum(1 for r in type_responses if r.response_type == ResponseType.YES)
            no_count = sum(1 for r in type_responses if r.response_type == ResponseType.NO)
            later_count = sum(1 for r in type_responses if r.response_type == ResponseType.LATER)
            ignored_count = sum(1 for r in type_responses if r.response_type == ResponseType.IGNORED)

            # Calculate average response time (excluding ignored)
            response_times = [
                r.response_time_seconds
                for r in type_responses
                if r.response_time_seconds is not None
            ]
            avg_response_time = (
                sum(response_times) / len(response_times)
                if response_times else None
            )

            acceptance_rate = yes_count / total if total > 0 else 0.0
            confidence = calculate_confidence(total, self.min_sample_size)

            # Get QuestionType enum from string
            question_type_enum = QuestionType(question_type_str)

            prefs[question_type_str] = QuestionPreference(
                question_type=question_type_enum,
                total_asked=total,
                yes_count=yes_count,
                no_count=no_count,
                later_count=later_count,
                ignored_count=ignored_count,
                acceptance_rate=acceptance_rate,
                avg_response_time_seconds=avg_response_time,
                confidence=confidence,
                last_updated=datetime.now()
            )

        return prefs

    def _analyze_timing(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, TimingPreference]:
        """
        Analyze preferences by time of day.

        Args:
            responses: Response records

        Returns:
            Dict mapping time period to preference metrics
        """
        # Group by time of day
        by_time: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            # Handle both enum and string values
            time_str = r.time_of_day if isinstance(r.time_of_day, str) else r.time_of_day.value
            by_time[time_str].append(r)

        prefs = {}
        for time_period_str, time_responses in by_time.items():
            total = len(time_responses)
            yes_count = sum(1 for r in time_responses if r.response_type == ResponseType.YES)
            acceptance_rate = yes_count / total if total > 0 else 0.0
            confidence = calculate_confidence(total, self.min_sample_size)

            # Get TimeOfDay enum from string
            time_period_enum = TimeOfDay(time_period_str)

            prefs[time_period_str] = TimingPreference(
                time_of_day=time_period_enum,
                total_asked=total,
                yes_count=yes_count,
                acceptance_rate=acceptance_rate,
                confidence=confidence
            )

        return prefs

    def _analyze_days_of_week(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, DayOfWeekPreference]:
        """
        Analyze preferences by day of week.

        Args:
            responses: Response records

        Returns:
            Dict mapping day to preference metrics
        """
        # Group by day of week
        by_day: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            # Handle both enum and string values
            day_str = r.day_of_week if isinstance(r.day_of_week, str) else r.day_of_week.value
            by_day[day_str].append(r)

        prefs = {}
        for day_str, day_responses in by_day.items():
            total = len(day_responses)
            yes_count = sum(1 for r in day_responses if r.response_type == ResponseType.YES)
            acceptance_rate = yes_count / total if total > 0 else 0.0
            confidence = calculate_confidence(total, self.min_sample_size)

            # Get DayOfWeek enum from string
            day_enum = DayOfWeek(day_str)

            prefs[day_str] = DayOfWeekPreference(
                day_of_week=day_enum,
                total_asked=total,
                yes_count=yes_count,
                acceptance_rate=acceptance_rate,
                confidence=confidence
            )

        return prefs

    def _analyze_topics(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[str, TopicPreference]:
        """
        Analyze preferences by topic category.

        Args:
            responses: Response records

        Returns:
            Dict mapping topic to preference metrics
        """
        # Group by topic
        by_topic: Dict[str, List[ResponseRecord]] = defaultdict(list)
        for r in responses:
            # Handle both enum and string values
            topic_str = r.topic_category if isinstance(r.topic_category, str) else r.topic_category.value
            by_topic[topic_str].append(r)

        prefs = {}
        for topic_str, topic_responses in by_topic.items():
            total = len(topic_responses)
            yes_count = sum(1 for r in topic_responses if r.response_type == ResponseType.YES)
            no_count = sum(1 for r in topic_responses if r.response_type == ResponseType.NO)

            # Calculate average response time
            response_times = [
                r.response_time_seconds
                for r in topic_responses
                if r.response_time_seconds is not None
            ]
            avg_response_time = (
                sum(response_times) / len(response_times)
                if response_times else None
            )

            acceptance_rate = yes_count / total if total > 0 else 0.0
            confidence = calculate_confidence(total, self.min_sample_size)

            # Detect trend
            trend = self._detect_trend(topic_responses, self.trend_window_days)

            # Get TopicCategory enum from string
            topic_enum = TopicCategory(topic_str)

            prefs[topic_str] = TopicPreference(
                topic_category=topic_enum,
                total_asked=total,
                yes_count=yes_count,
                no_count=no_count,
                acceptance_rate=acceptance_rate,
                avg_response_time_seconds=avg_response_time,
                confidence=confidence,
                trend=trend
            )

        return prefs

    def _detect_trend(
        self,
        responses: List[ResponseRecord],
        window_days: int
    ) -> str:
        """
        Detect trend (increasing, stable, decreasing) over time window.

        Args:
            responses: Response records for a category
            window_days: Analysis window in days

        Returns:
            Trend classification
        """
        if len(responses) < 4:  # Need minimum data for trend
            return "stable"

        # Sort by timestamp
        sorted_responses = sorted(responses, key=lambda r: r.timestamp)

        # Split into two halves (earlier vs recent)
        cutoff = datetime.now() - timedelta(days=window_days)
        recent = [r for r in sorted_responses if r.timestamp >= cutoff]
        earlier = [r for r in sorted_responses if r.timestamp < cutoff]

        if not earlier or not recent:
            return "stable"

        # Calculate acceptance rates
        recent_yes = sum(1 for r in recent if r.response_type == ResponseType.YES)
        recent_rate = recent_yes / len(recent) if recent else 0.0

        earlier_yes = sum(1 for r in earlier if r.response_type == ResponseType.YES)
        earlier_rate = earlier_yes / len(earlier) if earlier else 0.0

        # Compare with 10% threshold
        diff = recent_rate - earlier_rate
        if diff > 0.1:
            return "increasing"
        elif diff < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _analyze_context(
        self,
        responses: List[ResponseRecord]
    ) -> List[ContextualPattern]:
        """
        Analyze contextual patterns that lead to YES responses.

        Args:
            responses: Response records

        Returns:
            List of contextual patterns
        """
        patterns = []

        # Pattern 1: Questions after specific context keywords
        context_keywords = self._extract_context_keywords(responses)
        for keywords, (occurrence, yes_count) in context_keywords.items():
            if occurrence < 3:  # Minimum 3 occurrences
                continue

            acceptance_rate = yes_count / occurrence if occurrence > 0 else 0.0
            confidence = calculate_confidence(occurrence, 3)

            if confidence >= self.min_confidence_threshold:
                pattern = ContextualPattern(
                    pattern_id=f"context_{uuid.uuid4().hex[:8]}",
                    pattern_description=f"Questions following: {', '.join(keywords)}",
                    context_keywords=list(keywords),
                    occurrence_count=occurrence,
                    yes_count=yes_count,
                    acceptance_rate=acceptance_rate,
                    confidence=confidence,
                    examples=[
                        r.question_text
                        for r in responses
                        if all(kw.lower() in r.context_before.lower() for kw in keywords)
                    ][:3]
                )
                patterns.append(pattern)

        return patterns

    def _extract_context_keywords(
        self,
        responses: List[ResponseRecord]
    ) -> Dict[Tuple[str, ...], Tuple[int, int]]:
        """
        Extract common context keyword patterns.

        Args:
            responses: Response records

        Returns:
            Dict mapping keyword tuples to (occurrence_count, yes_count)
        """
        # Simple keyword extraction (can be enhanced with NLP)
        common_keywords = [
            "book", "coaching", "client", "project", "sushi",
            "meeting", "call", "email", "code", "system"
        ]

        patterns: Dict[Tuple[str, ...], Tuple[int, int]] = defaultdict(lambda: (0, 0))

        for response in responses:
            context = response.context_before.lower()
            found_keywords = tuple(
                sorted([kw for kw in common_keywords if kw in context])
            )

            if found_keywords:
                occurrence, yes_count = patterns[found_keywords]
                patterns[found_keywords] = (
                    occurrence + 1,
                    yes_count + (1 if response.response_type == ResponseType.YES else 0)
                )

        return patterns

    def _generate_recommendations(
        self,
        question_prefs: Dict[str, QuestionPreference],
        timing_prefs: Dict[str, TimingPreference],
        day_prefs: Dict[str, DayOfWeekPreference],
        topic_prefs: Dict[str, TopicPreference],
        contextual_patterns: List[ContextualPattern]
    ) -> List[PreferenceRecommendation]:
        """
        Generate actionable recommendations for ARCHITECT.

        Args:
            question_prefs: Question type preferences
            timing_prefs: Timing preferences
            day_prefs: Day of week preferences
            topic_prefs: Topic preferences
            contextual_patterns: Contextual patterns

        Returns:
            List of recommendations
        """
        recommendations = []

        # Recommendation 1: High-acceptance question types
        for type_key, pref in question_prefs.items():
            if pref.confidence >= self.min_confidence_threshold:
                if pref.acceptance_rate >= 0.7:
                    recommendations.append(
                        PreferenceRecommendation(
                            recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                            recommendation_type="increase_frequency",
                            title=f"Increase {type_key} questions",
                            description=f"Alex accepts {pref.acceptance_rate:.0%} of {type_key} questions. Consider asking more.",
                            evidence=[
                                f"{pref.yes_count} YES out of {pref.total_asked} total",
                                f"Confidence: {pref.confidence:.0%}"
                            ],
                            confidence=pref.confidence,
                            priority="high" if pref.acceptance_rate >= 0.85 else "medium"
                        )
                    )
                elif pref.acceptance_rate <= 0.3 and pref.total_asked >= self.min_sample_size:
                    recommendations.append(
                        PreferenceRecommendation(
                            recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                            recommendation_type="decrease_frequency",
                            title=f"Reduce {type_key} questions",
                            description=f"Alex only accepts {pref.acceptance_rate:.0%} of {type_key} questions. Consider reducing or changing approach.",
                            evidence=[
                                f"{pref.yes_count} YES out of {pref.total_asked} total",
                                f"{pref.no_count} NO responses",
                                f"Confidence: {pref.confidence:.0%}"
                            ],
                            confidence=pref.confidence,
                            priority="medium"
                        )
                    )

        # Recommendation 2: Best timing
        best_time = max(
            timing_prefs.values(),
            key=lambda p: p.acceptance_rate,
            default=None
        )
        if best_time and best_time.confidence >= self.min_confidence_threshold:
            recommendations.append(
                PreferenceRecommendation(
                    recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                    recommendation_type="change_timing",
                    title=f"Best time to ask: {best_time.time_of_day}",
                    description=f"Alex accepts {best_time.acceptance_rate:.0%} of questions during {best_time.time_of_day}.",
                    evidence=[
                        f"{best_time.yes_count} YES out of {best_time.total_asked}",
                        f"Confidence: {best_time.confidence:.0%}"
                    ],
                    confidence=best_time.confidence,
                    priority="high" if best_time.acceptance_rate >= 0.7 else "medium"
                )
            )

        # Recommendation 3: High-value topics
        for topic_key, pref in topic_prefs.items():
            if pref.confidence >= self.min_confidence_threshold:
                if pref.acceptance_rate >= 0.75:
                    recommendations.append(
                        PreferenceRecommendation(
                            recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                            recommendation_type="new_opportunity",
                            title=f"High-value topic: {topic_key}",
                            description=f"Alex highly values {topic_key} suggestions ({pref.acceptance_rate:.0%} acceptance). Look for more opportunities.",
                            evidence=[
                                f"{pref.yes_count} YES out of {pref.total_asked}",
                                f"Trend: {pref.trend}",
                                f"Confidence: {pref.confidence:.0%}"
                            ],
                            confidence=pref.confidence,
                            priority="high"
                        )
                    )

        # Recommendation 4: Contextual patterns
        for pattern in contextual_patterns:
            if pattern.acceptance_rate >= 0.7:
                recommendations.append(
                    PreferenceRecommendation(
                        recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                        recommendation_type="new_opportunity",
                        title=f"Context pattern: {', '.join(pattern.context_keywords[:2])}",
                        description=pattern.pattern_description,
                        evidence=[
                            f"{pattern.yes_count} YES out of {pattern.occurrence_count}",
                            f"Acceptance rate: {pattern.acceptance_rate:.0%}",
                            f"Confidence: {pattern.confidence:.0%}"
                        ],
                        confidence=pattern.confidence,
                        priority="medium"
                    )
                )

        # Sort by priority and confidence
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda r: (priority_order[r.priority], -r.confidence)
        )

        return recommendations


def create_response_record(
    question_id: str,
    question_text: str,
    question_type: QuestionType,
    topic_category: TopicCategory,
    response_type: ResponseType,
    timestamp: datetime,
    response_time_seconds: Optional[float] = None,
    context_before: str = ""
) -> ResponseRecord:
    """
    Create a ResponseRecord with automatic time/day classification.

    Convenience function for creating properly formatted records.

    Args:
        question_id: Question identifier
        question_text: Question text
        question_type: Type of question
        topic_category: Topic category
        response_type: Alex's response
        timestamp: When question was asked
        response_time_seconds: Response time (None if ignored)
        context_before: Context before question

    Returns:
        ResponseRecord instance
    """
    return ResponseRecord(
        response_id=f"resp_{uuid.uuid4().hex[:8]}",
        question_id=question_id,
        question_text=question_text,
        question_type=question_type,
        topic_category=topic_category,
        response_type=response_type,
        timestamp=timestamp,
        response_time_seconds=response_time_seconds,
        context_before=context_before,
        day_of_week=classify_day_of_week(timestamp.weekday()),
        time_of_day=classify_time_of_day(timestamp.hour)
    )
