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
from .kanban import (
    CardStatus,
    CardType,
    KanbanCard,
    KanbanFeed,
)
from .learning import (
    ContentTypeBreakdown,
    LearningConsolidation,
    LearningInsight,
    LearningMetric,
    PatternAnalysis,
    TimeDistribution,
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
from .telemetry import (
    AgentMetrics,
    SystemHealth,
    TelemetryEvent,
    TelemetryMetrics,
)

__all__ = [
    # Memory models
    "MemoryRecord",
    "MemoryPriority",
    "MemoryMetadata",
    "MemorySearchResult",
    # Learning models
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
]
