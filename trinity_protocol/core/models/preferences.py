"""
Preference Learning Models for Trinity Protocol.

Tracks Alex's response patterns to optimize proactive assistance.

Philosophy: Learn what Alex actually finds helpful, not what we think he should.

Constitutional Compliance:
- Article II: Strict typing with Pydantic (no Dict[Any, Any])
- Article IV: Continuous learning from all interactions
- Privacy: Secure storage of personal preferences
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ResponseType(str, Enum):
    """Alex's response types to Trinity questions."""

    YES = "YES"
    NO = "NO"
    LATER = "LATER"
    IGNORED = "IGNORED"  # No response within timeout


class QuestionType(str, Enum):
    """Types of questions Trinity asks."""

    LOW_STAKES = "low_stakes"  # "Want to grab sushi?"
    HIGH_VALUE = "high_value"  # "Work on coaching framework?"
    TASK_SUGGESTION = "task_suggestion"  # "Should I handle this?"
    CLARIFICATION = "clarification"  # "Did you mean X?"
    PROACTIVE_OFFER = "proactive_offer"  # "I noticed Y, want help?"


class TopicCategory(str, Enum):
    """Topic categories for preference tracking."""

    BOOK_PROJECT = "book_project"
    CLIENT_WORK = "client_work"
    COACHING = "coaching"
    PERSONAL = "personal"
    FOOD = "food"
    ENTERTAINMENT = "entertainment"
    TECHNICAL = "technical"
    SYSTEM_IMPROVEMENT = "system_improvement"
    OTHER = "other"


class DayOfWeek(str, Enum):
    """Days of the week."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeOfDay(str, Enum):
    """Time periods for timing analysis."""

    EARLY_MORNING = "early_morning"  # 5am-8am
    MORNING = "morning"  # 8am-12pm
    AFTERNOON = "afternoon"  # 12pm-5pm
    EVENING = "evening"  # 5pm-9pm
    NIGHT = "night"  # 9pm-12am
    LATE_NIGHT = "late_night"  # 12am-5am


class ResponseRecord(BaseModel):
    """
    Single response from Alex to a Trinity question.

    Atomic unit of preference learning.
    """

    response_id: str = Field(..., description="Unique response identifier")
    question_id: str = Field(..., description="ID of question asked")
    question_text: str = Field(..., description="Actual question text")
    question_type: QuestionType = Field(..., description="Type of question")
    topic_category: TopicCategory = Field(..., description="Topic category")
    response_type: ResponseType = Field(..., description="Alex's response")
    timestamp: datetime = Field(..., description="When question was asked")
    response_time_seconds: float | None = Field(
        default=None, description="Time taken to respond (None if IGNORED)"
    )
    context_before: str = Field(
        default="", max_length=500, description="What was happening before question"
    )
    day_of_week: DayOfWeek = Field(..., description="Day of week")
    time_of_day: TimeOfDay = Field(..., description="Time period")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        use_enum_values = True
        validate_assignment = True


class QuestionPreference(BaseModel):
    """
    Preference metrics for a specific question type.

    Tracks acceptance rates and patterns.
    """

    question_type: QuestionType = Field(..., description="Type of question")
    total_asked: int = Field(default=0, ge=0, description="Total questions asked")
    yes_count: int = Field(default=0, ge=0, description="YES responses")
    no_count: int = Field(default=0, ge=0, description="NO responses")
    later_count: int = Field(default=0, ge=0, description="LATER responses")
    ignored_count: int = Field(default=0, ge=0, description="Ignored questions")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="YES / total (0.0-1.0)")
    avg_response_time_seconds: float | None = Field(
        default=None, description="Average response time"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in pattern (based on sample size)"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    @property
    def rejection_rate(self) -> float:
        """Calculate rejection rate (NO / total)."""
        if self.total_asked == 0:
            return 0.0
        return self.no_count / self.total_asked

    @property
    def defer_rate(self) -> float:
        """Calculate defer rate (LATER / total)."""
        if self.total_asked == 0:
            return 0.0
        return self.later_count / self.total_asked

    class Config:
        """Pydantic config."""

        use_enum_values = True
        validate_assignment = True


class TimingPreference(BaseModel):
    """
    Preference metrics for timing patterns.

    When does Alex prefer to be asked questions?
    """

    time_of_day: TimeOfDay = Field(..., description="Time period")
    total_asked: int = Field(default=0, ge=0, description="Questions asked")
    yes_count: int = Field(default=0, ge=0, description="YES responses")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="YES / total")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in pattern")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class DayOfWeekPreference(BaseModel):
    """
    Preference metrics by day of week.

    Does Alex respond differently on Monday vs Friday?
    """

    day_of_week: DayOfWeek = Field(..., description="Day of week")
    total_asked: int = Field(default=0, ge=0, description="Questions asked")
    yes_count: int = Field(default=0, ge=0, description="YES responses")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="YES / total")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in pattern")

    class Config:
        """Pydantic config."""

        use_enum_values = True


class TopicPreference(BaseModel):
    """
    Preference metrics for topic categories.

    Which topics does Alex care about?
    """

    topic_category: TopicCategory = Field(..., description="Topic category")
    total_asked: int = Field(default=0, ge=0, description="Questions asked")
    yes_count: int = Field(default=0, ge=0, description="YES responses")
    no_count: int = Field(default=0, ge=0, description="NO responses")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="YES / total")
    avg_response_time_seconds: float | None = Field(
        default=None, description="Average response time"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in pattern")
    trend: Literal["increasing", "stable", "decreasing"] = Field(
        default="stable", description="Trend over time"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ContextualPattern(BaseModel):
    """
    Contextual patterns that lead to YES responses.

    What context increases acceptance?
    """

    pattern_id: str = Field(..., description="Pattern identifier")
    pattern_description: str = Field(..., max_length=200, description="Human-readable pattern")
    context_keywords: list[str] = Field(
        ..., min_items=1, description="Keywords that trigger pattern"
    )
    occurrence_count: int = Field(default=0, ge=0, description="Times pattern observed")
    yes_count: int = Field(default=0, ge=0, description="YES responses")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="YES / occurrence")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in pattern")
    examples: list[str] = Field(
        default_factory=list, max_items=3, description="Example questions (max 3)"
    )

    class Config:
        """Pydantic config."""

        validate_assignment = True


class PreferenceRecommendation(BaseModel):
    """
    Actionable recommendation for ARCHITECT.

    Based on learned preferences, what should we do?
    """

    recommendation_id: str = Field(..., description="Recommendation ID")
    recommendation_type: Literal[
        "increase_frequency",
        "decrease_frequency",
        "change_timing",
        "change_approach",
        "new_opportunity",
    ] = Field(..., description="Type of recommendation")
    title: str = Field(..., max_length=100, description="Recommendation title")
    description: str = Field(..., max_length=500, description="Detailed description")
    evidence: list[str] = Field(..., min_items=1, description="Evidence supporting recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Priority level"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    class Config:
        """Pydantic config."""

        frozen = True


class AlexPreferences(BaseModel):
    """
    Master preference model for Alex.

    Aggregates all preference dimensions for holistic understanding.
    """

    version: str = Field(default="1.0.0", description="Preference schema version")
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    total_responses: int = Field(default=0, ge=0, description="Total responses recorded")
    overall_acceptance_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall YES / total"
    )
    question_preferences: dict[str, QuestionPreference] = Field(
        default_factory=dict, description="Preferences by question type"
    )
    timing_preferences: dict[str, TimingPreference] = Field(
        default_factory=dict, description="Preferences by time of day"
    )
    day_preferences: dict[str, DayOfWeekPreference] = Field(
        default_factory=dict, description="Preferences by day of week"
    )
    topic_preferences: dict[str, TopicPreference] = Field(
        default_factory=dict, description="Preferences by topic category"
    )
    contextual_patterns: list[ContextualPattern] = Field(
        default_factory=list, description="Learned contextual patterns"
    )
    recommendations: list[PreferenceRecommendation] = Field(
        default_factory=list, description="Active recommendations"
    )
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        """Pydantic config."""

        validate_assignment = True


class PreferenceSnapshot(BaseModel):
    """
    Point-in-time snapshot of preferences.

    For version history and trend analysis.
    """

    snapshot_id: str = Field(..., description="Snapshot identifier")
    snapshot_date: datetime = Field(default_factory=datetime.now, description="Snapshot timestamp")
    preferences: AlexPreferences = Field(..., description="Preference state")
    snapshot_reason: str = Field(..., description="Why snapshot was taken")

    class Config:
        """Pydantic config."""

        frozen = True


# Utility functions


def classify_time_of_day(hour: int) -> TimeOfDay:
    """
    Classify hour into time of day period.

    Args:
        hour: Hour in 24-hour format (0-23)

    Returns:
        TimeOfDay enum
    """
    if 5 <= hour < 8:
        return TimeOfDay.EARLY_MORNING
    elif 8 <= hour < 12:
        return TimeOfDay.MORNING
    elif 12 <= hour < 17:
        return TimeOfDay.AFTERNOON
    elif 17 <= hour < 21:
        return TimeOfDay.EVENING
    elif 21 <= hour < 24:
        return TimeOfDay.NIGHT
    else:  # 0-5
        return TimeOfDay.LATE_NIGHT


def classify_day_of_week(weekday: int) -> DayOfWeek:
    """
    Classify weekday integer into DayOfWeek enum.

    Args:
        weekday: Weekday from datetime (0=Monday, 6=Sunday)

    Returns:
        DayOfWeek enum
    """
    days = [
        DayOfWeek.MONDAY,
        DayOfWeek.TUESDAY,
        DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY,
        DayOfWeek.FRIDAY,
        DayOfWeek.SATURDAY,
        DayOfWeek.SUNDAY,
    ]
    return days[weekday]


def calculate_confidence(sample_size: int, min_samples: int = 10) -> float:
    """
    Calculate confidence score based on sample size.

    Confidence approaches 1.0 as sample size increases beyond min_samples.

    Args:
        sample_size: Number of samples
        min_samples: Minimum samples for reliable pattern (default 10)

    Returns:
        Confidence score 0.0-1.0
    """
    if sample_size == 0:
        return 0.0
    if sample_size >= min_samples * 2:
        return 1.0
    # Linear interpolation from 0 to min_samples, then 0.5 to 1.0
    if sample_size < min_samples:
        return 0.5 * (sample_size / min_samples)
    else:
        # Between min_samples and 2*min_samples
        ratio = (sample_size - min_samples) / min_samples
        return 0.5 + (0.5 * ratio)
