"""
Shared Pydantic Models for Agency OS
Constitutional Law #2: Strict typing enforcement
"""

from .context import (
    AgentContextData,
    AgentState,
    SessionMetadata,
)
from .dashboard import (
    AgentActivity,
    DashboardSummary,
    SessionSummary,
)
from .ensemble_model import EnsembleModel
from .extracted_metadata_features import ExtractedMetadataFeatures
from .kanban import (
    CardStatus,
    CardType,
    KanbanCard,
    KanbanFeed,
)
from .quality_feedback_sample import QualityFeedbackSample
from .learning import (
    AgentStateLearning,
    ContentTypeBreakdown,
    LearningConsolidation,
    LearningInsight,
    LearningMetric,
    PatternAnalysis,
    TimeDistribution,
)
from .lock_metadata import (
    LockError,
    LockHandle,
    LockMetadata,
)
from .memory import (
    MemoryMetadata,
    MemoryPriority,
    MemoryRecord,
    MemorySearchResult,
)
from .message import MessageEnvelope
from .orchestrator import (
    BackoffType,
    CancellationType,
    ExecutionMetrics,
    FairnessType,
    OrchestrationResultModel,
    TaskResultModel,
)
from .patterns import (
    ApplicationPriority,
    ApplicationRecord,
    ContextFeatures,
    CrossSessionData,
    DataCollectionSummary,
    EventStatus,
    HealingPattern,
    LearningEffectiveness,
    LearningObject,
    LearningRecommendation,
    PatternExtraction,
    PatternMatch,
    PatternMatchSummary,
    PatternType,
    SelfHealingEvent,
    SessionInsight,
    TemporalPattern,
    ToolExecutionResult,
    ValidationOutcome,
    ValidationStatus,
)
from .priority_task import (
    BacklogError,
    PriorityTask,
)
from .session import (
    CheckpointMetadata,
    CompressionMetadata,
    GCResult,
    RetentionPolicy,
    SessionState,
    SessionStatus,
    TaskContext,
    TaskProgress,
)
from .task_feature_vector import TaskFeatureVector
from .task_metadata import TaskMetadata
from .telemetry import (
    AgentMetrics,
    SystemHealth,
    TelemetryEvent,
    TelemetryMetrics,
)
from .training_dataset import TrainingDataset

__all__ = [
    # Lock models
    "LockMetadata",
    "LockHandle",
    "LockError",
    # Priority task models
    "PriorityTask",
    "BacklogError",
    # Memory models
    "MemoryRecord",
    "MemoryPriority",
    "MemoryMetadata",
    "MemorySearchResult",
    # Learning models
    "AgentStateLearning",
    "LearningConsolidation",
    "LearningInsight",
    "LearningMetric",
    "PatternAnalysis",
    "ContentTypeBreakdown",
    "TimeDistribution",
    # Telemetry models
    "TelemetryEvent",
    "TelemetryMetrics",
    "AgentMetrics",
    "SystemHealth",
    # Dashboard models
    "DashboardSummary",
    "SessionSummary",
    "AgentActivity",
    # Context models
    "AgentContextData",
    "SessionMetadata",
    "AgentState",
    # Pattern models
    "SessionInsight",
    "HealingPattern",
    "CrossSessionData",
    "PatternExtraction",
    "ToolExecutionResult",
    "ValidationOutcome",
    "TemporalPattern",
    "ContextFeatures",
    "PatternMatch",
    "LearningRecommendation",
    "ApplicationRecord",
    "LearningEffectiveness",
    "SelfHealingEvent",
    "DataCollectionSummary",
    "LearningObject",
    "PatternMatchSummary",
    "PatternType",
    "ValidationStatus",
    "ApplicationPriority",
    "EventStatus",
    # Messaging
    "MessageEnvelope",
    # Orchestrator models
    "ExecutionMetrics",
    "TaskResultModel",
    "OrchestrationResultModel",
    "BackoffType",
    "FairnessType",
    "CancellationType",
    # Kanban models
    "KanbanCard",
    "KanbanFeed",
    "CardType",
    "CardStatus",
    # Session models
    "SessionState",
    "SessionStatus",
    "TaskProgress",
    "TaskContext",
    "CompressionMetadata",
    "CheckpointMetadata",
    "GCResult",
    "RetentionPolicy",
    # ML Routing models (Leap 5)
    "EnsembleModel",
    "ExtractedMetadataFeatures",
    "QualityFeedbackSample",
    "TaskFeatureVector",
    "TaskMetadata",
    "TrainingDataset",
]
