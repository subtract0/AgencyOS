"""
Shared Pydantic Models for Agency OS
Constitutional Law #2: Strict typing enforcement
"""

from .memory import (
    MemoryRecord,
    MemoryPriority,
    MemoryMetadata,
    MemorySearchResult,
)
from .learning import (
    LearningConsolidation,
    LearningInsight,
    LearningMetric,
    PatternAnalysis,
    ContentTypeBreakdown,
    TimeDistribution,
)
from .telemetry import (
    TelemetryEvent,
    TelemetryMetrics,
    AgentMetrics,
    SystemHealth,
)
from .dashboard import (
    DashboardSummary,
    SessionSummary,
    AgentActivity,
)
from .context import (
    AgentContextData,
    SessionMetadata,
    AgentState,
)
from .patterns import (
    SessionInsight,
    HealingPattern,
    CrossSessionData,
    PatternExtraction,
    ToolExecutionResult,
    ValidationOutcome,
    TemporalPattern,
    ContextFeatures,
    PatternMatch,
    LearningRecommendation,
    ApplicationRecord,
    LearningEffectiveness,
    SelfHealingEvent,
    DataCollectionSummary,
    LearningObject,
    PatternMatchSummary,
    PatternType,
    ValidationStatus,
    ApplicationPriority,
    EventStatus,
)
from .message import MessageEnvelope
from .orchestrator import (
    ExecutionMetrics,
    TaskResultModel,
    OrchestrationResultModel,
    BackoffType,
    FairnessType,
    CancellationType,
)
from .kanban import (
    KanbanCard,
    KanbanFeed,
    CardType,
    CardStatus,
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