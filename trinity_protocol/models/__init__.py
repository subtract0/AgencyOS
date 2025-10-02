"""
Trinity Protocol Models - Backward Compatibility Layer

⚠️ DEPRECATION WARNING ⚠️
Importing models from 'trinity_protocol.models' is deprecated.

**Deprecated Pattern:**
  from trinity_protocol.models import Project, PatternType, ...

**New Pattern (recommended):**
  from trinity_protocol.core.models import Project, PatternType, HumanReviewRequest, ...

This backward compatibility layer will be removed after 2025-11-02 (30 days).
See: trinity_protocol/README_REORGANIZATION.md for migration guide
"""

import warnings

warnings.warn(
    "\n⚠️ DEPRECATION WARNING ⚠️\n"
    "  Importing models from 'trinity_protocol.models' is deprecated.\n"
    "  Recommended: from trinity_protocol.core.models import Project, PatternType, ...\n"
    "  This backward compatibility will be removed after 2025-11-02 (30 days).\n"
    "  See: trinity_protocol/README_REORGANIZATION.md\n",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new locations for backward compatibility
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
