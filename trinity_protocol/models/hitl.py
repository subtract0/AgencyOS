"""
Human-in-the-Loop (HITL) Models for Trinity Protocol.

Defines Pydantic models for the question-answer system that enables
Trinity to ask Alex questions and capture responses (YES/NO/LATER).

Constitutional Compliance:
- Article II: Strict typing with Pydantic (no Dict[Any, Any])
- Article IV: Continuous learning from responses
- Article VII: Clear, descriptive naming
- Privacy: Respect user focus time
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

from trinity_protocol.models.patterns import DetectedPattern


class HumanReviewRequest(BaseModel):
    """
    Question submitted to human review queue.

    Represents a question formulated by ARCHITECT that needs
    Alex's approval before EXECUTOR takes action.
    """

    correlation_id: str = Field(
        ...,
        description="Unique ID linking this question to pattern and potential tasks"
    )
    question_text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Clear, concise question for Alex (10-500 chars)"
    )
    question_type: Literal["low_stakes", "high_value"] = Field(
        ...,
        description="Stakes level: low_stakes = quick wins, high_value = major impact"
    )
    pattern_context: DetectedPattern = Field(
        ...,
        description="Pattern that triggered this question"
    )
    priority: int = Field(
        ...,
        ge=1,
        le=10,
        description="Priority level (1-10, higher = more urgent)"
    )
    expires_at: datetime = Field(
        ...,
        description="Question expires after this time (defaults to 24h)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When question was created"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Brief description of what would happen if YES"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True
        frozen = False  # Allow updates during lifecycle


class HumanResponse(BaseModel):
    """
    User's response to a question from the review queue.

    Captures YES (proceed), NO (don't do this), or LATER (ask again).
    """

    correlation_id: str = Field(
        ...,
        description="Links response to original question"
    )
    response_type: Literal["YES", "NO", "LATER"] = Field(
        ...,
        description="User decision: YES (execute), NO (don't execute), LATER (remind me)"
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional user comment explaining the decision"
    )
    responded_at: datetime = Field(
        default_factory=datetime.now,
        description="When user responded"
    )
    response_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Time from question creation to response (for learning)"
    )

    class Config:
        """Pydantic config."""
        frozen = True  # Responses are immutable once created


class QuestionStats(BaseModel):
    """
    Statistics about question asking and response patterns.

    Used by PreferenceLearning to optimize when/what to ask.
    """

    total_questions_asked: int = Field(
        default=0,
        ge=0,
        description="Total questions asked"
    )
    yes_responses: int = Field(
        default=0,
        ge=0,
        description="Number of YES responses"
    )
    no_responses: int = Field(
        default=0,
        ge=0,
        description="Number of NO responses"
    )
    later_responses: int = Field(
        default=0,
        ge=0,
        description="Number of LATER responses"
    )
    expired_questions: int = Field(
        default=0,
        ge=0,
        description="Questions that expired without response"
    )
    avg_response_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Average response time"
    )

    @property
    def acceptance_rate(self) -> float:
        """Calculate acceptance rate (YES / total answered)."""
        total_answered = self.yes_responses + self.no_responses
        if total_answered == 0:
            return 0.0
        return self.yes_responses / total_answered

    @property
    def response_rate(self) -> float:
        """Calculate response rate (answered / total asked)."""
        if self.total_questions_asked == 0:
            return 0.0
        total_answered = self.yes_responses + self.no_responses + self.later_responses
        return total_answered / self.total_questions_asked

    class Config:
        """Pydantic config."""
        validate_assignment = True


class PreferencePattern(BaseModel):
    """
    Learned pattern about when Alex says YES.

    Stored in Firestore for cross-session learning.
    """

    pattern_id: str = Field(..., description="Unique pattern identifier")
    question_type: str = Field(..., description="Type of question")
    pattern_topic: str = Field(..., description="Topic/theme of questions")
    acceptance_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of YES responses for this pattern"
    )
    sample_size: int = Field(
        ...,
        ge=1,
        description="Number of questions in this pattern"
    )
    preferred_time_of_day: Optional[str] = Field(
        default=None,
        description="Best time to ask (e.g., 'morning', 'afternoon', 'evening')"
    )
    context_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords associated with YES responses"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in this preference pattern"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last time pattern was updated"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True


class QuestionDeliveryConfig(BaseModel):
    """
    Configuration for question delivery system.

    Controls how and when questions are presented to Alex.
    """

    delivery_method: Literal["terminal", "web", "voice"] = Field(
        default="terminal",
        description="How to deliver questions (terminal for MVP)"
    )
    max_questions_per_hour: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Rate limit: max questions per hour"
    )
    quiet_hours_start: Optional[int] = Field(
        default=22,
        ge=0,
        le=23,
        description="Hour to stop asking questions (24h format)"
    )
    quiet_hours_end: Optional[int] = Field(
        default=8,
        ge=0,
        le=23,
        description="Hour to resume asking questions (24h format)"
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require explicit confirmation before executing"
    )
    default_expiry_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Default question expiry time in hours (1-168)"
    )

    class Config:
        """Pydantic config."""
        validate_assignment = True
