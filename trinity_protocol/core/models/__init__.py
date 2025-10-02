"""
Trinity Protocol Core Models - Production-Ready Data Structures

All models in this directory meet production criteria:
- Strict Pydantic typing (no Dict[Any, Any])
- Comprehensive validation
- Documentation with examples
- Used by production agents

Constitutional Compliance:
- Article II: 100% strict typing with Pydantic
- Article IV: Models support learning and preference tracking
- Article V: Formal specifications via ProjectSpec
"""

# Project models (Phase 3)
from trinity_protocol.core.models.project import (
    ProjectState,
    TaskStatus,
    QuestionConfidence,
    ApprovalStatus,
    QAQuestion,
    QAAnswer,
    QASession,
    AcceptanceCriterion,
    ProjectSpec,
    ProjectTask,
    ProjectPlan,
    CheckinQuestion,
    CheckinResponse,
    DailyCheckin,
    ProjectMetadata,
    Project,
    ProjectOutcome,
)

# Pattern detection models
from trinity_protocol.core.models.patterns import (
    PatternType,
    DetectedPattern,
    PatternContext,
    AmbientEvent,
    TopicCluster,
    IntentClassification,
    RecurrenceMetrics,
)

# Human-in-the-loop models
from trinity_protocol.core.models.hitl import (
    HumanReviewRequest,
    HumanResponse,
    QuestionStats,
    PreferencePattern,
    QuestionDeliveryConfig,
)

# Preference learning models
from trinity_protocol.core.models.preferences import (
    ResponseType,
    QuestionType,
    TopicCategory,
    DayOfWeek,
    TimeOfDay,
    ResponseRecord,
    QuestionPreference,
    TimingPreference,
    DayOfWeekPreference,
    TopicPreference,
    ContextualPattern,
    PreferenceRecommendation,
    AlexPreferences,
    PreferenceSnapshot,
)

__all__ = [
    # Project models
    "ProjectState",
    "TaskStatus",
    "QuestionConfidence",
    "ApprovalStatus",
    "QAQuestion",
    "QAAnswer",
    "QASession",
    "AcceptanceCriterion",
    "ProjectSpec",
    "ProjectTask",
    "ProjectPlan",
    "CheckinQuestion",
    "CheckinResponse",
    "DailyCheckin",
    "ProjectMetadata",
    "Project",
    "ProjectOutcome",
    # Pattern models
    "PatternType",
    "DetectedPattern",
    "PatternContext",
    "AmbientEvent",
    "TopicCluster",
    "IntentClassification",
    "RecurrenceMetrics",
    # HITL models
    "HumanReviewRequest",
    "HumanResponse",
    "QuestionStats",
    "PreferencePattern",
    "QuestionDeliveryConfig",
    # Preference models
    "ResponseType",
    "QuestionType",
    "TopicCategory",
    "DayOfWeek",
    "TimeOfDay",
    "ResponseRecord",
    "QuestionPreference",
    "TimingPreference",
    "DayOfWeekPreference",
    "TopicPreference",
    "ContextualPattern",
    "PreferenceRecommendation",
    "AlexPreferences",
    "PreferenceSnapshot",
]
