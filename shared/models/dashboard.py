"""
Dashboard and summary Pydantic models for Agency OS.
Replaces Dict[str, Any] in dashboard and reporting functions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from shared.type_definitions.json import JSONValue
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SessionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Summary of a single session."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_memories: int = 0
    total_events: int = 0
    agents_involved: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    errors_encountered: int = 0
    success_rate: float = Field(1.0, ge=0.0, le=1.0)
    key_achievements: List[str] = Field(default_factory=list)

    @field_validator('duration_seconds')
    def validate_duration(cls, v: Optional[float]) -> Optional[float]:
        """Ensure duration is positive if set."""
        if v is not None and v < 0:
            raise ValueError('duration_seconds must be non-negative')
        return v

    def calculate_duration(self) -> None:
        """Calculate duration from start and end times."""
        if self.start_time and self.end_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()

    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.end_time is None


class AgentActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Activity summary for a specific agent."""
    agent_id: str
    agent_type: str
    invocation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_response_time_ms: float = 0.0
    tools_used: Dict[str, int] = Field(default_factory=dict)
    handoffs_sent: int = 0
    handoffs_received: int = 0
    memory_operations: int = 0
    last_active: Optional[datetime] = None
    status: str = Field(default="idle", pattern="^(idle|active|error|disabled)$")

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.invocation_count == 0:
            return 1.0
        return self.success_count / self.invocation_count

    def update_status(self) -> None:
        """Update status based on recent activity."""
        if self.last_active:
            time_since_active = (datetime.now() - self.last_active).total_seconds()
            if time_since_active < 60:
                self.status = "active"
            elif self.failure_count > self.success_count:
                self.status = "error"
            else:
                self.status = "idle"


class DashboardMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Core metrics for dashboard display."""
    sessions_analyzed: int = 0
    total_memories: int = 0
    total_events: int = 0
    avg_memories_per_session: float = 0.0
    avg_events_per_session: float = 0.0
    total_agents: int = 0
    active_agents: int = 0
    total_tools: int = 0
    system_uptime_hours: float = 0.0
    error_rate: float = Field(0.0, ge=0.0, le=1.0)
    success_rate: float = Field(1.0, ge=0.0, le=1.0)
    healing_triggers: int = 0
    patterns_detected: int = 0

    def calculate_averages(self) -> None:
        """Calculate average metrics."""
        if self.sessions_analyzed > 0:
            self.avg_memories_per_session = self.total_memories / self.sessions_analyzed
            self.avg_events_per_session = self.total_events / self.sessions_analyzed


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """
    Complete dashboard summary.
    Replaces Dict[str, Any] returned from dashboard functions.
    """
    metrics: DashboardMetrics = Field(default_factory=DashboardMetrics)
    active_sessions: List[SessionSummary] = Field(default_factory=list)
    agent_activities: Dict[str, AgentActivity] = Field(default_factory=dict)
    recent_errors: List[Dict[str, JSONValue]] = Field(default_factory=list)
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    alerts: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    def add_session(self, session: SessionSummary) -> None:
        """Add a session to the dashboard."""
        self.active_sessions.append(session)
        self.metrics.sessions_analyzed += 1
        self.metrics.total_memories += session.total_memories
        self.metrics.total_events += session.total_events
        self.metrics.calculate_averages()

    def add_agent_activity(self, activity: AgentActivity) -> None:
        """Add agent activity to the dashboard."""
        self.agent_activities[activity.agent_id] = activity
        self.metrics.total_agents = len(self.agent_activities)
        self.metrics.active_agents = sum(
            1 for a in self.agent_activities.values()
            if a.status == "active"
        )

    def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs."""
        return [
            agent_id for agent_id, activity in self.agent_activities.items()
            if activity.status == "active"
        ]

    def has_alerts(self) -> bool:
        """Check if there are any alerts."""
        return len(self.alerts) > 0

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode='json')

    def generate_summary_text(self) -> str:
        """Generate a human-readable summary."""
        return (
            f"Dashboard Summary (Generated: {self.generated_at.isoformat()})\n"
            f"Sessions: {self.metrics.sessions_analyzed}\n"
            f"Total Memories: {self.metrics.total_memories}\n"
            f"Active Agents: {self.metrics.active_agents}/{self.metrics.total_agents}\n"
            f"Success Rate: {self.metrics.success_rate:.2%}\n"
            f"Alerts: {len(self.alerts)}"
        )