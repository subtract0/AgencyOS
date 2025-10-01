"""
Pattern Detection Models for WITNESS Ambient Mode.

Defines Pydantic models for detected patterns, pattern types, contexts,
and ambient events for proactive assistance.

Constitutional Compliance:
- Article II: Strict typing with Pydantic (no Dict[Any, Any])
- Article IV: Continuous learning with pattern persistence
- Article VII: Clear, descriptive naming
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class PatternType(str, Enum):
    """Types of patterns detected from ambient transcriptions."""
    RECURRING_TOPIC = "recurring_topic"
    PROJECT_MENTION = "project_mention"
    FRUSTRATION = "frustration"
    ACTION_ITEM = "action_item"
    FEATURE_REQUEST = "feature_request"
    WORKFLOW_BOTTLENECK = "workflow_bottleneck"
    OPPORTUNITY = "opportunity"


class DetectedPattern(BaseModel):
    """
    Pattern detected from ambient transcriptions.

    Represents a meaningful insight extracted from conversation
    that may warrant proactive assistance.
    """
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: PatternType = Field(..., description="Type of pattern detected")
    topic: str = Field(..., min_length=1, description="Main topic or theme")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score"
    )
    mention_count: int = Field(
        ...,
        ge=1,
        description="Number of times topic mentioned"
    )
    first_mention: datetime = Field(
        ...,
        description="Timestamp of first mention"
    )
    last_mention: datetime = Field(
        ...,
        description="Timestamp of most recent mention"
    )
    context_summary: str = Field(
        ...,
        max_length=500,
        description="Summary of context around mentions"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords associated with pattern"
    )
    sentiment: Optional[str] = Field(
        default=None,
        description="Detected sentiment (positive, negative, neutral)"
    )
    urgency: Optional[str] = Field(
        default=None,
        description="Urgency level (low, medium, high, critical)"
    )

    class Config:
        """Pydantic config."""
        use_enum_values = True


class PatternContext(BaseModel):
    """
    Contextual information about pattern detection.

    Provides additional metadata for ARCHITECT to formulate
    better questions and suggestions.
    """
    conversation_id: str = Field(
        ...,
        description="ID of conversation where pattern detected"
    )
    speaker_count: int = Field(
        default=1,
        ge=1,
        description="Number of distinct speakers"
    )
    duration_minutes: float = Field(
        ...,
        gt=0.0,
        description="Duration of conversation in minutes"
    )
    related_patterns: List[str] = Field(
        default_factory=list,
        description="IDs of related patterns"
    )
    transcript_excerpts: List[str] = Field(
        default_factory=list,
        max_items=5,
        description="Key transcript excerpts (max 5)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True


class AmbientEvent(BaseModel):
    """
    Event published to personal_context_stream from ambient listener.

    Represents a transcription with metadata for WITNESS consumption.
    """
    event_type: str = Field(
        default="ambient_transcription",
        description="Event type identifier"
    )
    source: Literal["ambient_listener"] = Field(
        default="ambient_listener",
        description="Event source"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Transcribed text"
    )
    timestamp: str = Field(
        ...,
        description="ISO8601 timestamp"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Whisper transcription confidence"
    )
    session_id: str = Field(
        ...,
        description="Ambient listening session ID"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation segment ID"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        """Pydantic config."""
        frozen = True


class TopicCluster(BaseModel):
    """
    Cluster of related topics detected over time.

    Used for recurrence detection and pattern analysis.
    """
    cluster_id: str = Field(..., description="Cluster identifier")
    central_topic: str = Field(..., description="Central theme of cluster")
    related_keywords: List[str] = Field(
        ...,
        min_items=1,
        description="Keywords in cluster"
    )
    mention_timestamps: List[datetime] = Field(
        ...,
        min_items=1,
        description="Timestamps of all mentions"
    )
    recurrence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score indicating recurrence strength"
    )
    time_window_hours: float = Field(
        ...,
        gt=0.0,
        description="Time window for recurrence calculation"
    )

    @property
    def mention_count(self) -> int:
        """Get total mention count."""
        return len(self.mention_timestamps)

    @property
    def avg_time_between_mentions(self) -> float:
        """Calculate average time between mentions in hours."""
        if len(self.mention_timestamps) < 2:
            return 0.0

        sorted_timestamps = sorted(self.mention_timestamps)
        total_hours = 0.0

        for i in range(1, len(sorted_timestamps)):
            delta = sorted_timestamps[i] - sorted_timestamps[i - 1]
            total_hours += delta.total_seconds() / 3600

        return total_hours / (len(sorted_timestamps) - 1)

    class Config:
        """Pydantic config."""
        validate_assignment = True


class IntentClassification(BaseModel):
    """
    Classification of user intent from ambient transcription.

    Used by WITNESS to determine if pattern warrants ARCHITECT attention.
    """
    intent_type: str = Field(..., description="Type of intent detected")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence"
    )
    action_required: bool = Field(
        ...,
        description="Whether action is required"
    )
    priority: str = Field(
        ...,
        description="Priority level (LOW, NORMAL, HIGH, CRITICAL)"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description="Suggested action for ARCHITECT"
    )
    rationale: str = Field(
        ...,
        max_length=500,
        description="Explanation of classification"
    )

    class Config:
        """Pydantic config."""
        frozen = True


class RecurrenceMetrics(BaseModel):
    """
    Metrics for topic recurrence analysis.

    Tracks frequency, timing, and patterns of topic mentions.
    """
    topic: str = Field(..., description="Topic being tracked")
    total_mentions: int = Field(..., ge=0, description="Total mention count")
    unique_days: int = Field(..., ge=0, description="Days with mentions")
    avg_mentions_per_day: float = Field(
        ...,
        ge=0.0,
        description="Average mentions per day"
    )
    peak_mentions_in_day: int = Field(
        ...,
        ge=0,
        description="Highest mentions in single day"
    )
    trend: str = Field(
        ...,
        description="Trend direction (increasing, stable, decreasing)"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last metrics update"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True
