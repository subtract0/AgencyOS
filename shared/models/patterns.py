"""
Pattern learning and extraction Pydantic models for Agency OS.
Replaces Dict[str, Any] in learning agent tools and self-healing systems.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal, Union
from shared.types.json import JSONValue
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PatternType(str, Enum):
    """Types of patterns that can be extracted."""
    TRIGGER_ACTION = "trigger_action"
    CONTEXT = "context"
    TIMING = "timing"
    SEQUENCE = "sequence"
    GENERAL = "general"
    SESSION_LEARNING = "session_learning"


class ValidationStatus(str, Enum):
    """Pattern validation status."""
    VALIDATED = "validated"
    PENDING = "pending"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"
    FAILED = "failed"


class ApplicationPriority(str, Enum):
    """Application priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventStatus(str, Enum):
    """Self-healing event status."""
    SUCCESS = "success"
    SUCCESSFUL = "successful"
    RESOLVED = "resolved"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"
    PENDING = "pending"


class SessionInsight(BaseModel):
    """Session-level insights for cross-session learning."""
    insight_id: str
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str
    category: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    actionable_insight: Optional[str] = None

    class Config:
        extra = "forbid"


class HealingPattern(BaseModel):
    """Self-healing pattern definition."""
    pattern_id: str
    pattern_type: PatternType
    trigger: Optional[str] = None
    action: Optional[str] = None
    context: Optional[str] = None
    time_period: Optional[str] = None
    sequence: Optional[str] = None
    occurrences: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    effectiveness_score: float = Field(default=0.0, ge=0.0)
    description: str
    evidence: List[Dict[str, JSONValue]] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.PENDING

    class Config:
        extra = "forbid"


class CrossSessionData(BaseModel):
    """Cross-session learning data structure."""
    learnings: List[Dict[str, JSONValue]] = Field(default_factory=list)
    total_learnings: int = Field(default=0, ge=0)
    sources: List[str] = Field(default_factory=list)

    @field_validator('total_learnings')
    def validate_total_learnings(cls, v: int, info) -> int:
        """Ensure total_learnings matches learnings list length."""
        learnings = info.data.get('learnings', [])
        if learnings and len(learnings) != v:
            return len(learnings)
        return v

    class Config:
        extra = "forbid"


class PatternExtraction(BaseModel):
    """Results from pattern extraction process."""
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    time_window: str
    data_summary: Dict[str, JSONValue]
    patterns_found: int = Field(default=0, ge=0)
    patterns: List[HealingPattern] = Field(default_factory=list)
    insights: List[Dict[str, JSONValue]] = Field(default_factory=list)
    learning_objects: List[Dict[str, JSONValue]] = Field(default_factory=list)
    recommendations: List[Dict[str, JSONValue]] = Field(default_factory=list)

    class Config:
        extra = "forbid"


class ToolExecutionResult(BaseModel):
    """Result from tool execution in learning context."""
    tool_name: str
    execution_timestamp: datetime = Field(default_factory=datetime.now)
    status: EventStatus
    result_data: Dict[str, JSONValue] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    context: Dict[str, JSONValue] = Field(default_factory=dict)

    class Config:
        extra = "forbid"


class ValidationOutcome(BaseModel):
    """Outcome from pattern or learning validation."""
    validation_id: str
    subject_id: str  # ID of what was validated (pattern_id, learning_id, etc.)
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    status: ValidationStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_criteria: List[str] = Field(default_factory=list)
    outcome_details: Dict[str, JSONValue] = Field(default_factory=dict)
    next_review_date: Optional[datetime] = None

    class Config:
        extra = "forbid"


class TemporalPattern(BaseModel):
    """Time-based patterns for learning effectiveness."""
    pattern_id: str
    time_period: str  # e.g., "morning", "afternoon", "evening", "night"
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=0, le=23)
    success_rate: float = Field(ge=0.0, le=1.0)
    occurrences: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    description: str

    @field_validator('end_hour')
    def validate_hour_range(cls, v: int, info) -> int:
        """Ensure end_hour is after start_hour."""
        start_hour = info.data.get('start_hour', 0)
        if v <= start_hour:
            raise ValueError(f'end_hour ({v}) must be after start_hour ({start_hour})')
        return v

    class Config:
        extra = "forbid"


class ContextFeatures(BaseModel):
    """Extracted context features for pattern matching."""
    keywords: List[str] = Field(default_factory=list)
    context_type: str = "unknown"
    urgency: Literal["low", "normal", "high"] = "normal"
    domain: str = "general"
    agents_involved: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    error_types: List[str] = Field(default_factory=list)

    class Config:
        extra = "forbid"


class PatternMatch(BaseModel):
    """Details about how a pattern matched to context."""
    pattern_id: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reason: str
    matched_features: ContextFeatures
    pattern_type: PatternType

    class Config:
        extra = "forbid"


class LearningRecommendation(BaseModel):
    """Actionable recommendation from learning analysis."""
    recommendation_id: str
    type: Literal["pattern_group", "individual_pattern"] = "individual_pattern"
    pattern_type: Optional[PatternType] = None
    pattern_id: Optional[str] = None
    title: str
    description: str
    actionable_steps: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_patterns: int = Field(ge=0)
    evidence: List[Dict[str, JSONValue]] = Field(default_factory=list)
    match_reason: Optional[str] = None
    expected_benefit: str
    application_priority: ApplicationPriority

    class Config:
        extra = "forbid"


class ApplicationRecord(BaseModel):
    """Record of learning application for tracking effectiveness."""
    application_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    context_summary: str
    recommendations_count: int = Field(ge=0)
    recommendation_ids: List[str] = Field(default_factory=list)
    average_confidence: float = Field(ge=0.0, le=1.0)
    learning_types_applied: List[str] = Field(default_factory=list)
    status: Literal["applied", "pending", "failed"] = "applied"
    feedback_pending: bool = True

    class Config:
        extra = "forbid"


class LearningEffectiveness(BaseModel):
    """Metrics for learning system effectiveness."""
    total_applications: int = Field(default=0, ge=0)
    successful_applications: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    improvement_measured: bool = False
    last_effectiveness_update: datetime = Field(default_factory=datetime.now)
    trend_direction: Literal["improving", "stable", "declining", "unknown"] = "unknown"

    @field_validator('successful_applications')
    def validate_successful_count(cls, v: int, info) -> int:
        """Ensure successful applications don't exceed total."""
        total = info.data.get('total_applications', 0)
        if v > total:
            raise ValueError(f'successful_applications ({v}) cannot exceed total_applications ({total})')
        return v

    @field_validator('success_rate')
    def calculate_success_rate(cls, v: float, info) -> float:
        """Calculate success rate from counts if not provided."""
        total = info.data.get('total_applications', 0)
        successful = info.data.get('successful_applications', 0)
        if total > 0:
            return successful / total
        return 0.0

    class Config:
        extra = "forbid"


class SelfHealingEvent(BaseModel):
    """Self-healing system event."""
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    event_type: str
    status: EventStatus = EventStatus.PENDING
    trigger_name: Optional[str] = None
    action_name: Optional[str] = None
    trigger_type: Optional[str] = None
    action_type: Optional[str] = None
    content: Optional[str] = None
    raw_line: Optional[str] = None
    file: Optional[str] = None
    component: Optional[str] = None
    agent: Optional[str] = None
    severity: Optional[str] = None
    error_type: Optional[str] = None
    line_number: Optional[int] = None
    extracted_timestamp: Optional[datetime] = None

    class Config:
        extra = "forbid"


class DataCollectionSummary(BaseModel):
    """Summary of data collection for pattern extraction."""
    events: List[SelfHealingEvent] = Field(default_factory=list)
    sources_checked: List[str] = Field(default_factory=list)
    total_events: int = Field(default=0, ge=0)
    successful_events: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('total_events')
    def validate_total_events(cls, v: int, info) -> int:
        """Ensure total_events matches events list length."""
        events = info.data.get('events', [])
        if events and len(events) != v:
            return len(events)
        return v

    @field_validator('success_rate')
    def calculate_success_rate_from_events(cls, v: float, info) -> float:
        """Calculate success rate from event counts."""
        total = info.data.get('total_events', 0)
        successful = info.data.get('successful_events', 0)
        if total > 0:
            return successful / total
        return 0.0

    class Config:
        extra = "forbid"


class LearningObject(BaseModel):
    """Structured learning object for VectorStore storage."""
    learning_id: str
    type: str = "successful_pattern"
    category: str = "learning"
    title: str
    description: str
    actionable_insight: str
    confidence: float = Field(ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    patterns: Dict[str, JSONValue] = Field(default_factory=dict)
    metadata: Dict[str, JSONValue] = Field(default_factory=dict)
    application_criteria: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    created_timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        extra = "forbid"


class PatternMatchSummary(BaseModel):
    """Summary of pattern matching results."""
    total_matches: int = Field(default=0, ge=0)
    average_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    match_types: Dict[str, int] = Field(default_factory=dict)
    top_matches: List[Dict[str, JSONValue]] = Field(default_factory=list)

    class Config:
        extra = "forbid"