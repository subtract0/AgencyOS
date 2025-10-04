"""
Pattern learning and extraction Pydantic models for Agency OS.
Replaces Dict[str, Any] in learning agent tools and self-healing systems.

NOTE: HealingPattern is being migrated to CodingPattern format.
New code should use pattern_intelligence.CodingPattern.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.type_definitions.json import JSONValue

logger = logging.getLogger(__name__)


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
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str
    category: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)
    actionable_insight: str | None = None

    model_config = ConfigDict(extra="forbid")


class HealingPattern(BaseModel):
    """
    Self-healing pattern definition.

    NOTE: This class is maintained for compatibility but new code
    should use pattern_intelligence.CodingPattern instead.
    """

    pattern_id: str
    pattern_type: PatternType
    trigger: str | None = None
    action: str | None = None
    context: str | None = None
    time_period: str | None = None
    sequence: str | None = None
    occurrences: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    effectiveness_score: float = Field(default=0.0, ge=0.0)
    description: str
    evidence: list[dict[str, JSONValue]] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.PENDING

    model_config = ConfigDict(extra="forbid")

    def to_coding_pattern(self):
        """
        Convert this HealingPattern to the unified CodingPattern format.

        Returns:
            CodingPattern: The converted pattern in the new format.
        """
        # Migration functionality removed - use pattern_intelligence.CodingPattern directly
        raise NotImplementedError(
            "Migration functionality removed - use pattern_intelligence.CodingPattern directly"
        )

    @classmethod
    def from_coding_pattern(cls, coding_pattern):
        """
        Create a HealingPattern from a CodingPattern for backward compatibility.

        Args:
            coding_pattern: A CodingPattern instance

        Returns:
            HealingPattern: Compatible representation
        """
        # Extract relevant fields from CodingPattern
        trigger = coding_pattern.context.symptoms[0] if coding_pattern.context.symptoms else None
        action = coding_pattern.solution.approach

        # Map pattern type from domain
        pattern_type_map = {
            "self_healing": PatternType.GENERAL,
            "trigger_action": PatternType.TRIGGER_ACTION,
            "context": PatternType.CONTEXT,
            "timing": PatternType.TIMING,
            "sequence": PatternType.SEQUENCE,
        }
        pattern_type = pattern_type_map.get(coding_pattern.context.domain, PatternType.GENERAL)

        # Map validation status
        validation_map = {
            "validated": ValidationStatus.VALIDATED,
            "unvalidated": ValidationStatus.PENDING,
            "deprecated": ValidationStatus.FAILED,
        }
        validation = validation_map.get(
            coding_pattern.metadata.validation_status, ValidationStatus.PENDING
        )

        return cls(
            pattern_id=coding_pattern.metadata.pattern_id,
            pattern_type=pattern_type,
            trigger=trigger,
            action=action,
            context=coding_pattern.context.description,
            time_period=coding_pattern.outcome.longevity,
            sequence=coding_pattern.solution.implementation,
            occurrences=coding_pattern.outcome.adoption_rate,
            success_rate=coding_pattern.outcome.success_rate,
            confidence=coding_pattern.outcome.confidence,
            overall_confidence=coding_pattern.outcome.confidence,
            effectiveness_score=coding_pattern.outcome.effectiveness_score(),
            description=coding_pattern.context.description,
            evidence=[],  # Evidence not directly mapped
            validation_status=validation,
        )


class CrossSessionData(BaseModel):
    """Cross-session learning data structure."""

    learnings: list[dict[str, JSONValue]] = Field(default_factory=list)
    total_learnings: int = Field(default=0, ge=0)
    sources: list[str] = Field(default_factory=list)

    @field_validator("total_learnings")
    def validate_total_learnings(cls, v: int, info) -> int:
        """Ensure total_learnings matches learnings list length."""
        learnings = info.data.get("learnings", [])
        if learnings and len(learnings) != v:
            return len(learnings)
        return v

    model_config = ConfigDict(extra="forbid")


class PatternExtraction(BaseModel):
    """Results from pattern extraction process."""

    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    time_window: str
    data_summary: dict[str, JSONValue]
    patterns_found: int = Field(default=0, ge=0)
    patterns: list[HealingPattern] = Field(default_factory=list)
    insights: list[dict[str, JSONValue]] = Field(default_factory=list)
    learning_objects: list[dict[str, JSONValue]] = Field(default_factory=list)
    recommendations: list[dict[str, JSONValue]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ToolExecutionResult(BaseModel):
    """Result from tool execution in learning context."""

    tool_name: str
    execution_timestamp: datetime = Field(default_factory=datetime.now)
    status: EventStatus
    result_data: dict[str, JSONValue] = Field(default_factory=dict)
    error_message: str | None = None
    execution_time: float | None = None
    context: dict[str, JSONValue] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ValidationOutcome(BaseModel):
    """Outcome from pattern or learning validation."""

    validation_id: str
    subject_id: str  # ID of what was validated (pattern_id, learning_id, etc.)
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    status: ValidationStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_criteria: list[str] = Field(default_factory=list)
    outcome_details: dict[str, JSONValue] = Field(default_factory=dict)
    next_review_date: datetime | None = None

    model_config = ConfigDict(extra="forbid")


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

    @field_validator("end_hour")
    def validate_hour_range(cls, v: int, info) -> int:
        """Ensure end_hour is after start_hour."""
        start_hour = info.data.get("start_hour", 0)
        if v <= start_hour:
            raise ValueError(f"end_hour ({v}) must be after start_hour ({start_hour})")
        return v

    model_config = ConfigDict(extra="forbid")


class ContextFeatures(BaseModel):
    """Extracted context features for pattern matching."""

    keywords: list[str] = Field(default_factory=list)
    context_type: str = "unknown"
    urgency: Literal["low", "normal", "high"] = "normal"
    domain: str = "general"
    agents_involved: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    error_types: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class PatternMatch(BaseModel):
    """Details about how a pattern matched to context."""

    pattern_id: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_reason: str
    matched_features: ContextFeatures
    pattern_type: PatternType

    model_config = ConfigDict(extra="forbid")


class LearningRecommendation(BaseModel):
    """Actionable recommendation from learning analysis."""

    recommendation_id: str
    type: Literal["pattern_group", "individual_pattern"] = "individual_pattern"
    pattern_type: PatternType | None = None
    pattern_id: str | None = None
    title: str
    description: str
    actionable_steps: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_patterns: int = Field(ge=0)
    evidence: list[dict[str, JSONValue]] = Field(default_factory=list)
    match_reason: str | None = None
    expected_benefit: str
    application_priority: ApplicationPriority

    model_config = ConfigDict(extra="forbid")


class ApplicationRecord(BaseModel):
    """Record of learning application for tracking effectiveness."""

    application_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    context_summary: str
    recommendations_count: int = Field(ge=0)
    recommendation_ids: list[str] = Field(default_factory=list)
    average_confidence: float = Field(ge=0.0, le=1.0)
    learning_types_applied: list[str] = Field(default_factory=list)
    status: Literal["applied", "pending", "failed"] = "applied"
    feedback_pending: bool = True

    model_config = ConfigDict(extra="forbid")


class LearningEffectiveness(BaseModel):
    """Metrics for learning system effectiveness."""

    total_applications: int = Field(default=0, ge=0)
    successful_applications: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    improvement_measured: bool = False
    last_effectiveness_update: datetime = Field(default_factory=datetime.now)
    trend_direction: Literal["improving", "stable", "declining", "unknown"] = "unknown"

    @field_validator("successful_applications")
    def validate_successful_count(cls, v: int, info) -> int:
        """Ensure successful applications don't exceed total."""
        total = info.data.get("total_applications", 0)
        if v > total:
            raise ValueError(
                f"successful_applications ({v}) cannot exceed total_applications ({total})"
            )
        return v

    @field_validator("success_rate")
    def calculate_success_rate(cls, v: float, info) -> float:
        """Calculate success rate from counts if not provided."""
        total = info.data.get("total_applications", 0)
        successful = info.data.get("successful_applications", 0)
        if total > 0:
            return successful / total
        return 0.0

    model_config = ConfigDict(extra="forbid")


class SelfHealingEvent(BaseModel):
    """Self-healing system event."""

    event_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str
    event_type: str
    status: EventStatus = EventStatus.PENDING
    trigger_name: str | None = None
    action_name: str | None = None
    trigger_type: str | None = None
    action_type: str | None = None
    content: str | None = None
    raw_line: str | None = None
    file: str | None = None
    component: str | None = None
    agent: str | None = None
    severity: str | None = None
    error_type: str | None = None
    line_number: int | None = None
    extracted_timestamp: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class DataCollectionSummary(BaseModel):
    """Summary of data collection for pattern extraction."""

    events: list[SelfHealingEvent] = Field(default_factory=list)
    sources_checked: list[str] = Field(default_factory=list)
    total_events: int = Field(default=0, ge=0)
    successful_events: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("total_events")
    def validate_total_events(cls, v: int, info) -> int:
        """Ensure total_events matches events list length."""
        events = info.data.get("events", [])
        if events and len(events) != v:
            return len(events)
        return v

    @field_validator("success_rate")
    def calculate_success_rate_from_events(cls, v: float, info) -> float:
        """Calculate success rate from event counts."""
        total = info.data.get("total_events", 0)
        successful = info.data.get("successful_events", 0)
        if total > 0:
            return successful / total
        return 0.0

    model_config = ConfigDict(extra="forbid")


class LearningObject(BaseModel):
    """Structured learning object for VectorStore storage."""

    learning_id: str
    type: str = "successful_pattern"
    category: str = "learning"
    title: str
    description: str
    actionable_insight: str
    confidence: float = Field(ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)
    patterns: dict[str, JSONValue] = Field(default_factory=dict)
    metadata: dict[str, JSONValue] = Field(default_factory=dict)
    application_criteria: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    created_timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")


class PatternMatchSummary(BaseModel):
    """Summary of pattern matching results."""

    total_matches: int = Field(default=0, ge=0)
    average_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    match_types: dict[str, int] = Field(default_factory=dict)
    top_matches: list[dict[str, JSONValue]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
