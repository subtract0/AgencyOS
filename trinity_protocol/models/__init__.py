"""
Trinity Protocol data models.

Exports all Pydantic models for ambient intelligence system.
"""

from trinity_protocol.experimental.models.audio import (
    AudioFormat,
    AudioConfig,
    AudioSegment,
    WhisperConfig,
    TranscriptionSegment,
    TranscriptionResult,
    VADResult,
    AudioCaptureStats,
)

from trinity_protocol.core.models.patterns import (
    PatternType,
    DetectedPattern,
    PatternContext,
    AmbientEvent,
    TopicCluster,
    IntentClassification,
    RecurrenceMetrics,
)

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

__all__ = [
    # Audio models
    "AudioFormat",
    "AudioConfig",
    "AudioSegment",
    "WhisperConfig",
    "TranscriptionSegment",
    "TranscriptionResult",
    "VADResult",
    "AudioCaptureStats",
    # Pattern models
    "PatternType",
    "DetectedPattern",
    "PatternContext",
    "AmbientEvent",
    "TopicCluster",
    "IntentClassification",
    "RecurrenceMetrics",
    # Project models (Phase 3)
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
]
