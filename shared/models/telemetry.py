"""
Telemetry and monitoring Pydantic models for Agency OS.
Replaces Dict[str, Any] in telemetry and metrics tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from shared.types.json import JSONValue
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EventType(str, Enum):
    """Types of telemetry events."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TOOL_INVOCATION = "tool_invocation"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HANDOFF = "handoff"
    LLM_CALL = "llm_call"
    MEMORY_OPERATION = "memory_operation"
    PATTERN_DETECTED = "pattern_detected"
    HEALING_TRIGGERED = "healing_triggered"


class EventSeverity(str, Enum):
    """Severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Individual telemetry event."""
    event_id: str
    event_type: EventType
    severity: EventSeverity = EventSeverity.INFO
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, JSONValue] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @field_validator('duration_ms')
    def validate_duration(cls, v: Optional[float]) -> Optional[float]:
        """Ensure duration is non-negative."""
        if v is not None and v < 0:
            raise ValueError('duration_ms must be non-negative')
        return v

    def is_error(self) -> bool:
        """Check if this is an error event."""
        return self.event_type == EventType.ERROR or self.severity in [EventSeverity.ERROR, EventSeverity.CRITICAL]

    def to_log_format(self) -> str:
        """Format event for logging."""
        return (
            f"[{self.timestamp.isoformat()}] {self.severity.upper()} "
            f"{self.event_type}: {self.metadata}"
        )


class AgentMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Metrics for a specific agent."""
    agent_id: str
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0
    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0
    error_rate: float = 0.0
    tools_used: Dict[str, int] = Field(default_factory=dict)
    memory_operations: int = 0
    handoffs_sent: int = 0
    handoffs_received: int = 0

    @field_validator('error_rate')
    def validate_error_rate(cls, v: float) -> float:
        """Ensure error rate is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('error_rate must be between 0 and 1')
        return v

    def calculate_success_rate(self) -> float:
        """Calculate success rate from invocations."""
        if self.total_invocations == 0:
            return 1.0
        return self.successful_invocations / self.total_invocations

    def update_from_event(self, event: TelemetryEvent) -> None:
        """Update metrics based on a telemetry event."""
        if event.agent_id != self.agent_id:
            return

        self.total_invocations += 1
        if event.success:
            self.successful_invocations += 1
        else:
            self.failed_invocations += 1

        if event.duration_ms:
            self.total_duration_ms += event.duration_ms
            self.average_duration_ms = self.total_duration_ms / self.total_invocations

        self.error_rate = self.failed_invocations / self.total_invocations if self.total_invocations > 0 else 0

        if event.tool_name:
            self.tools_used[event.tool_name] = self.tools_used.get(event.tool_name, 0) + 1


class SystemHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Overall system health metrics."""
    status: str = Field(default="healthy", pattern="^(healthy|degraded|critical)$")
    uptime_seconds: float = Field(0.0, ge=0.0)
    total_events: int = Field(0, ge=0)
    error_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)
    active_agents: List[str] = Field(default_factory=list)
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == "healthy"

    def update_status(self) -> None:
        """Update status based on error rates."""
        if self.total_events > 0:
            error_rate = self.error_count / self.total_events
            if error_rate > 0.1:
                self.status = "critical"
            elif error_rate > 0.05:
                self.status = "degraded"
            else:
                self.status = "healthy"


class TelemetryMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Aggregated telemetry metrics."""
    period_start: datetime
    period_end: datetime
    total_events: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_severity: Dict[str, int] = Field(default_factory=dict)
    agent_metrics: Dict[str, AgentMetrics] = Field(default_factory=dict)
    system_health: SystemHealth = Field(default_factory=SystemHealth)
    top_errors: List[str] = Field(default_factory=list)
    slowest_operations: List[Dict[str, JSONValue]] = Field(default_factory=list)

    def add_event(self, event: TelemetryEvent) -> None:
        """Add an event to the metrics."""
        self.total_events += 1

        # Update event type counts
        event_type_str = event.event_type.value
        self.events_by_type[event_type_str] = self.events_by_type.get(event_type_str, 0) + 1

        # Update severity counts
        severity_str = event.severity.value
        self.events_by_severity[severity_str] = self.events_by_severity.get(severity_str, 0) + 1

        # Update agent metrics
        if event.agent_id:
            if event.agent_id not in self.agent_metrics:
                self.agent_metrics[event.agent_id] = AgentMetrics(agent_id=event.agent_id)
            self.agent_metrics[event.agent_id].update_from_event(event)

        # Update system health
        self.system_health.total_events += 1
        if event.is_error():
            self.system_health.error_count += 1
            self.system_health.last_error = event.error_message
            self.system_health.last_error_time = event.timestamp
        elif event.severity == EventSeverity.WARNING:
            self.system_health.warning_count += 1

        self.system_health.update_status()

    def get_summary(self) -> Dict[str, JSONValue]:
        """Get a summary of the metrics."""
        return {
            "period": f"{self.period_start.isoformat()} to {self.period_end.isoformat()}",
            "total_events": self.total_events,
            "system_status": self.system_health.status,
            "active_agents": len(self.agent_metrics),
            "error_rate": self.system_health.error_count / self.total_events if self.total_events > 0 else 0
        }