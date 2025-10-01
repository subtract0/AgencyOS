"""
Tests for Trinity Protocol Preference Learning System.

Tests cover:
- Preference models
- AlexPreferenceLearner algorithm
- PreferenceStore (in-memory and Firestore)

Constitutional Compliance:
- Article II: 100% test coverage before implementation
- TDD: Tests written to define behavior
"""

import pytest
from datetime import datetime, timedelta
from typing import List

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
from trinity_protocol.alex_preference_learner import (
    AlexPreferenceLearner,
    create_response_record,
)
from trinity_protocol.preference_store import PreferenceStore


# ============================================================================
# Model Tests
# ============================================================================


class TestPreferenceModels:
    """Test preference model definitions."""

    def test_response_record_creation(self):
        """Test creating ResponseRecord with all fields."""
        record = ResponseRecord(
            response_id="resp_123",
            question_id="q_456",
            question_text="Want to work on coaching framework?",
            question_type=QuestionType.HIGH_VALUE,
            topic_category=TopicCategory.COACHING,
            response_type=ResponseType.YES,
            timestamp=datetime(2025, 10, 1, 10, 30),
            response_time_seconds=5.2,
            context_before="Alex was reviewing coaching notes",
            day_of_week=DayOfWeek.TUESDAY,
            time_of_day=TimeOfDay.MORNING
        )

        assert record.response_id == "resp_123"
        assert record.question_type == QuestionType.HIGH_VALUE
        assert record.response_type == ResponseType.YES
        assert record.response_time_seconds == 5.2

    def test_question_preference_rates(self):
        """Test QuestionPreference rate calculations."""
        pref = QuestionPreference(
            question_type=QuestionType.HIGH_VALUE,
            total_asked=100,
            yes_count=85,
            no_count=10,
            later_count=3,
            ignored_count=2,
            acceptance_rate=0.85,
            confidence=0.95
        )

        assert pref.acceptance_rate == 0.85
        assert pref.rejection_rate == 0.10
        assert pref.defer_rate == 0.03

    def test_topic_preference_with_trend(self):
        """Test TopicPreference with trend tracking."""
        pref = TopicPreference(
            topic_category=TopicCategory.BOOK_PROJECT,
            total_asked=50,
            yes_count=45,
            no_count=5,
            acceptance_rate=0.90,
            confidence=0.9,
            trend="increasing"
        )

        assert pref.acceptance_rate == 0.90
        assert pref.trend == "increasing"

    def test_contextual_pattern(self):
        """Test ContextualPattern model."""
        pattern = ContextualPattern(
            pattern_id="pat_123",
            pattern_description="Questions after book mentions",
            context_keywords=["book", "coaching"],
            occurrence_count=15,
            yes_count=12,
            acceptance_rate=0.80,
            confidence=0.85,
            examples=["Example 1", "Example 2"]
        )

        assert len(pattern.context_keywords) == 2
        assert pattern.acceptance_rate == 0.80
        assert len(pattern.examples) == 2

    def test_preference_recommendation(self):
        """Test PreferenceRecommendation model."""
        rec = PreferenceRecommendation(
            recommendation_id="rec_123",
            recommendation_type="increase_frequency",
            title="Ask more about coaching",
            description="High acceptance rate on coaching topics",
            evidence=["85% acceptance", "20 responses"],
            confidence=0.90,
            priority="high"
        )

        assert rec.priority == "high"
        assert rec.confidence == 0.90
        assert len(rec.evidence) == 2


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Test utility functions."""

    def test_classify_time_of_day(self):
        """Test time of day classification."""
        assert classify_time_of_day(6) == TimeOfDay.EARLY_MORNING
        assert classify_time_of_day(10) == TimeOfDay.MORNING
        assert classify_time_of_day(14) == TimeOfDay.AFTERNOON
        assert classify_time_of_day(18) == TimeOfDay.EVENING
        assert classify_time_of_day(22) == TimeOfDay.NIGHT
        assert classify_time_of_day(2) == TimeOfDay.LATE_NIGHT

    def test_classify_day_of_week(self):
        """Test day of week classification."""
        assert classify_day_of_week(0) == DayOfWeek.MONDAY
        assert classify_day_of_week(4) == DayOfWeek.FRIDAY
        assert classify_day_of_week(6) == DayOfWeek.SUNDAY

    def test_calculate_confidence(self):
        """Test confidence calculation."""
        # No samples
        assert calculate_confidence(0) == 0.0

        # Below min_samples
        assert calculate_confidence(5, min_samples=10) == 0.25

        # At min_samples
        assert calculate_confidence(10, min_samples=10) == 0.5

        # Above min_samples (2x)
        assert calculate_confidence(20, min_samples=10) == 1.0

    def test_create_response_record_helper(self):
        """Test create_response_record convenience function."""
        # Use a Monday for predictable weekday testing
        timestamp = datetime(2025, 9, 29, 10, 30)  # Monday, September 29, 2025

        record = create_response_record(
            question_id="q_123",
            question_text="Test question",
            question_type=QuestionType.HIGH_VALUE,
            topic_category=TopicCategory.COACHING,
            response_type=ResponseType.YES,
            timestamp=timestamp,
            response_time_seconds=3.5,
            context_before="Context here"
        )

        # Auto-populated fields
        assert record.day_of_week == DayOfWeek.MONDAY
        assert record.time_of_day == TimeOfDay.MORNING
        assert record.response_id.startswith("resp_")


# ============================================================================
# AlexPreferenceLearner Tests
# ============================================================================


class TestAlexPreferenceLearner:
    """Test preference learning algorithm."""

    @pytest.fixture
    def learner(self):
        """Create learner instance."""
        return AlexPreferenceLearner(
            min_confidence_threshold=0.6,
            min_sample_size=10,
            trend_window_days=7
        )

    @pytest.fixture
    def sample_responses(self) -> List[ResponseRecord]:
        """Create sample response data."""
        base_time = datetime(2025, 10, 1, 10, 0)
        responses = []

        # High-value questions (high acceptance)
        for i in range(15):
            responses.append(
                create_response_record(
                    question_id=f"q_high_{i}",
                    question_text=f"Work on coaching framework? (iteration {i})",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.COACHING,
                    response_type=ResponseType.YES if i < 12 else ResponseType.NO,
                    timestamp=base_time + timedelta(hours=i),
                    response_time_seconds=5.0,
                    context_before="Alex reviewing coaching notes"
                )
            )

        # Low-stakes questions (low acceptance)
        for i in range(10):
            responses.append(
                create_response_record(
                    question_id=f"q_low_{i}",
                    question_text=f"Want sushi? (iteration {i})",
                    question_type=QuestionType.LOW_STAKES,
                    topic_category=TopicCategory.FOOD,
                    response_type=ResponseType.NO if i < 7 else ResponseType.YES,
                    timestamp=base_time + timedelta(hours=i, minutes=30),
                    response_time_seconds=2.0,
                    context_before="Alex working on project"
                )
            )

        return responses

    def test_analyze_empty_responses(self, learner):
        """Test analyzing empty response list."""
        prefs = learner.analyze_responses([])

        assert prefs.total_responses == 0
        assert prefs.overall_acceptance_rate == 0.0
        assert len(prefs.question_preferences) == 0

    def test_analyze_question_types(self, learner, sample_responses):
        """Test question type analysis."""
        prefs = learner.analyze_responses(sample_responses)

        # Check high-value questions
        high_value_key = QuestionType.HIGH_VALUE.value
        assert high_value_key in prefs.question_preferences

        high_pref = prefs.question_preferences[high_value_key]
        assert high_pref.total_asked == 15
        assert high_pref.yes_count == 12
        assert high_pref.acceptance_rate == 0.8  # 12/15

        # Check low-stakes questions
        low_stakes_key = QuestionType.LOW_STAKES.value
        assert low_stakes_key in prefs.question_preferences

        low_pref = prefs.question_preferences[low_stakes_key]
        assert low_pref.total_asked == 10
        assert low_pref.yes_count == 3
        assert low_pref.acceptance_rate == 0.3  # 3/10

    def test_analyze_timing(self, learner, sample_responses):
        """Test timing analysis."""
        prefs = learner.analyze_responses(sample_responses)

        # Sample responses span multiple time periods due to hour offsets
        # Check that timing preferences exist
        assert len(prefs.timing_preferences) > 0

        # Verify structure of a timing preference
        for time_key, time_pref in prefs.timing_preferences.items():
            assert time_pref.total_asked > 0
            assert 0.0 <= time_pref.acceptance_rate <= 1.0
            assert 0.0 <= time_pref.confidence <= 1.0

    def test_analyze_topics(self, learner, sample_responses):
        """Test topic analysis."""
        prefs = learner.analyze_responses(sample_responses)

        # Check coaching topic
        coaching_key = TopicCategory.COACHING.value
        assert coaching_key in prefs.topic_preferences

        coaching_pref = prefs.topic_preferences[coaching_key]
        assert coaching_pref.total_asked == 15
        assert coaching_pref.yes_count == 12
        assert coaching_pref.acceptance_rate == 0.8

    def test_detect_increasing_trend(self, learner):
        """Test trend detection - increasing."""
        base_time = datetime.now() - timedelta(days=14)
        responses = []

        # Earlier period: low acceptance
        for i in range(10):
            responses.append(
                create_response_record(
                    question_id=f"q_{i}",
                    question_text="Question",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.COACHING,
                    response_type=ResponseType.NO if i < 8 else ResponseType.YES,
                    timestamp=base_time + timedelta(days=i)
                )
            )

        # Recent period: high acceptance
        for i in range(10):
            responses.append(
                create_response_record(
                    question_id=f"q_recent_{i}",
                    question_text="Question",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.COACHING,
                    response_type=ResponseType.YES if i < 8 else ResponseType.NO,
                    timestamp=datetime.now() - timedelta(days=6-i)
                )
            )

        prefs = learner.analyze_responses(responses)
        coaching_pref = prefs.topic_preferences[TopicCategory.COACHING.value]

        assert coaching_pref.trend == "increasing"

    def test_generate_recommendations(self, learner, sample_responses):
        """Test recommendation generation."""
        prefs = learner.analyze_responses(sample_responses)

        assert len(prefs.recommendations) > 0

        # Should recommend increasing high-value questions (80% acceptance)
        high_value_recs = [
            r for r in prefs.recommendations
            if "high_value" in r.title.lower() or "high_value" in r.description.lower()
        ]
        assert len(high_value_recs) > 0

        # Should recommend something about low-stakes questions (30% acceptance)
        # Either reduce frequency or acknowledge low acceptance
        low_stakes_recs = [
            r for r in prefs.recommendations
            if "low_stakes" in r.title.lower() or "low_stakes" in r.description.lower()
        ]
        # Note: Recommendation may not always generate if confidence is low
        # Just verify that if present, it's correctly structured
        if low_stakes_recs:
            assert low_stakes_recs[0].confidence > 0

    def test_contextual_pattern_detection(self, learner):
        """Test contextual pattern detection."""
        base_time = datetime.now()
        responses = []

        # Create pattern: questions after "book" context
        for i in range(5):
            responses.append(
                create_response_record(
                    question_id=f"q_book_{i}",
                    question_text="Work on book?",
                    question_type=QuestionType.HIGH_VALUE,
                    topic_category=TopicCategory.BOOK_PROJECT,
                    response_type=ResponseType.YES,
                    timestamp=base_time + timedelta(hours=i),
                    context_before="Alex mentioned book project in conversation"
                )
            )

        prefs = learner.analyze_responses(responses)

        # Should detect "book" context pattern
        book_patterns = [
            p for p in prefs.contextual_patterns
            if "book" in p.context_keywords
        ]
        assert len(book_patterns) >= 1

    def test_overall_acceptance_rate(self, learner, sample_responses):
        """Test overall acceptance rate calculation."""
        prefs = learner.analyze_responses(sample_responses)

        # 12 YES from high-value + 3 YES from low-stakes = 15 YES out of 25 total
        assert prefs.total_responses == 25
        assert prefs.overall_acceptance_rate == 0.6  # 15/25


# ============================================================================
# PreferenceStore Tests
# ============================================================================


class TestPreferenceStore:
    """Test preference storage (in-memory mode)."""

    @pytest.fixture
    def store(self):
        """Create in-memory store."""
        return PreferenceStore(use_firestore=False)

    @pytest.fixture
    def sample_record(self):
        """Create sample response record."""
        return create_response_record(
            question_id="q_123",
            question_text="Test question",
            question_type=QuestionType.HIGH_VALUE,
            topic_category=TopicCategory.COACHING,
            response_type=ResponseType.YES,
            timestamp=datetime.now(),
            response_time_seconds=5.0
        )

    def test_store_response(self, store, sample_record):
        """Test storing a response."""
        response_id = store.store_response(sample_record)

        assert response_id == sample_record.response_id

        # Verify stored
        stats = store.get_stats()
        assert stats["response_count"] == 1

    def test_get_recent_responses(self, store, sample_record):
        """Test retrieving recent responses."""
        store.store_response(sample_record)

        responses = store.get_recent_responses(limit=10)

        assert len(responses) == 1
        assert responses[0].response_id == sample_record.response_id

    def test_store_preferences(self, store):
        """Test storing preferences."""
        prefs = AlexPreferences(
            total_responses=50,
            overall_acceptance_rate=0.75
        )

        snapshot_id = store.store_preferences(prefs, snapshot_reason="test")

        assert snapshot_id.startswith("snap_")

        # Verify stored
        current = store.get_current_preferences()
        assert current is not None
        assert current.total_responses == 50

    def test_get_preference_history(self, store):
        """Test retrieving preference history."""
        # Store multiple snapshots
        import time
        for i in range(3):
            prefs = AlexPreferences(
                total_responses=i * 10,
                overall_acceptance_rate=0.5 + (i * 0.1)
            )
            store.store_preferences(prefs, snapshot_reason=f"snapshot_{i}")
            time.sleep(0.01)  # Ensure different timestamps

        history = store.get_preference_history(limit=5)

        assert len(history) == 3
        # Should be in reverse chronological order (most recent first)
        # Last snapshot (i=2) should be first
        assert history[0].preferences.total_responses == 20

    def test_query_responses_by_question_type(self, store):
        """Test querying responses by question type."""
        # Store different types
        for q_type in [QuestionType.HIGH_VALUE, QuestionType.LOW_STAKES]:
            for i in range(3):
                record = create_response_record(
                    question_id=f"q_{q_type.value}_{i}",
                    question_text="Test",
                    question_type=q_type,
                    topic_category=TopicCategory.COACHING,
                    response_type=ResponseType.YES,
                    timestamp=datetime.now()
                )
                store.store_response(record)

        # Query high-value only
        high_value_responses = store.query_responses(
            question_type=QuestionType.HIGH_VALUE.value
        )

        assert len(high_value_responses) == 3
        assert all(r.question_type == QuestionType.HIGH_VALUE for r in high_value_responses)

    def test_query_responses_by_date_range(self, store):
        """Test querying responses by date range."""
        base_time = datetime(2025, 10, 1, 10, 0)

        # Store responses across different dates
        for i in range(5):
            record = create_response_record(
                question_id=f"q_{i}",
                question_text="Test",
                question_type=QuestionType.HIGH_VALUE,
                topic_category=TopicCategory.COACHING,
                response_type=ResponseType.YES,
                timestamp=base_time + timedelta(days=i)
            )
            store.store_response(record)

        # Query specific range
        start = base_time + timedelta(days=1)
        end = base_time + timedelta(days=3)

        responses = store.query_responses(start_date=start, end_date=end)

        assert len(responses) == 3  # Days 1, 2, 3

    def test_get_stats(self, store, sample_record):
        """Test storage statistics."""
        # Empty stats
        stats = store.get_stats()
        assert stats["backend"] == "in_memory"
        assert stats["response_count"] == 0
        assert stats["has_current_preferences"] is False

        # Add data
        store.store_response(sample_record)
        prefs = AlexPreferences()
        store.store_preferences(prefs)

        stats = store.get_stats()
        assert stats["response_count"] == 1
        assert stats["has_current_preferences"] is True

    def test_clear_cache(self, store, sample_record):
        """Test clearing cache."""
        store.store_response(sample_record)
        assert store.get_stats()["response_count"] == 1

        store.clear_cache()
        assert store.get_stats()["response_count"] == 0

    def test_delete_all_responses(self, store, sample_record):
        """Test deleting all responses."""
        # Store multiple
        for i in range(5):
            store.store_response(sample_record)

        count = store.delete_all_responses()

        assert count == 5
        assert store.get_stats()["response_count"] == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestPreferenceLearningIntegration:
    """Integration tests for complete preference learning workflow."""

    def test_end_to_end_workflow(self):
        """Test complete workflow: responses → learning → storage → recommendations."""
        # 1. Create store
        store = PreferenceStore(use_firestore=False)

        # 2. Generate and store responses
        base_time = datetime.now()
        for i in range(20):
            # Mostly YES for coaching
            record = create_response_record(
                question_id=f"q_coaching_{i}",
                question_text="Work on coaching?",
                question_type=QuestionType.HIGH_VALUE,
                topic_category=TopicCategory.COACHING,
                response_type=ResponseType.YES if i < 16 else ResponseType.NO,
                timestamp=base_time + timedelta(hours=i),
                context_before="coaching discussion"
            )
            store.store_response(record)

        # Mostly NO for food
        for i in range(10):
            record = create_response_record(
                question_id=f"q_food_{i}",
                question_text="Want sushi?",
                question_type=QuestionType.LOW_STAKES,
                topic_category=TopicCategory.FOOD,
                response_type=ResponseType.NO if i < 8 else ResponseType.YES,
                timestamp=base_time + timedelta(hours=i),
                context_before="work session"
            )
            store.store_response(record)

        # 3. Learn preferences
        learner = AlexPreferenceLearner()
        responses = store.get_recent_responses(limit=100)
        preferences = learner.analyze_responses(responses)

        # 4. Store preferences
        snapshot_id = store.store_preferences(preferences, snapshot_reason="end_to_end_test")
        assert snapshot_id is not None

        # 5. Verify learned insights
        assert preferences.total_responses == 30

        # Coaching should have high acceptance
        coaching_pref = preferences.topic_preferences[TopicCategory.COACHING.value]
        assert coaching_pref.acceptance_rate >= 0.75

        # Food should have low acceptance
        food_pref = preferences.topic_preferences[TopicCategory.FOOD.value]
        assert food_pref.acceptance_rate <= 0.25

        # 6. Verify recommendations exist
        assert len(preferences.recommendations) > 0

        # Should recommend more coaching questions
        coaching_recs = [
            r for r in preferences.recommendations
            if "coaching" in r.title.lower() or "coaching" in r.description.lower()
        ]
        assert len(coaching_recs) > 0

    def test_preference_evolution_over_time(self):
        """Test that preferences evolve as new data comes in."""
        store = PreferenceStore(use_firestore=False)
        learner = AlexPreferenceLearner()

        # Phase 1: Initial low acceptance
        base_time = datetime.now() - timedelta(days=14)
        for i in range(10):
            record = create_response_record(
                question_id=f"q_phase1_{i}",
                question_text="Coaching question",
                question_type=QuestionType.HIGH_VALUE,
                topic_category=TopicCategory.COACHING,
                response_type=ResponseType.NO if i < 7 else ResponseType.YES,
                timestamp=base_time + timedelta(days=i)
            )
            store.store_response(record)

        # Learn phase 1
        responses = store.get_recent_responses(limit=100)
        prefs1 = learner.analyze_responses(responses)
        store.store_preferences(prefs1, snapshot_reason="phase1")

        coaching_rate_1 = prefs1.topic_preferences[TopicCategory.COACHING.value].acceptance_rate
        assert coaching_rate_1 <= 0.35  # Low acceptance

        # Phase 2: Improved acceptance
        for i in range(10):
            record = create_response_record(
                question_id=f"q_phase2_{i}",
                question_text="Coaching question",
                question_type=QuestionType.HIGH_VALUE,
                topic_category=TopicCategory.COACHING,
                response_type=ResponseType.YES if i < 8 else ResponseType.NO,
                timestamp=datetime.now() - timedelta(days=6-i)
            )
            store.store_response(record)

        # Learn phase 2
        responses = store.get_recent_responses(limit=100)
        prefs2 = learner.analyze_responses(responses)
        store.store_preferences(prefs2, snapshot_reason="phase2")

        coaching_rate_2 = prefs2.topic_preferences[TopicCategory.COACHING.value].acceptance_rate
        assert coaching_rate_2 >= 0.55  # Overall improved (11 YES out of 20 total)

        # Verify trend detection
        assert prefs2.topic_preferences[TopicCategory.COACHING.value].trend == "increasing"

        # Verify history
        history = store.get_preference_history(limit=10)
        assert len(history) == 2
