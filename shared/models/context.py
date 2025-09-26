"""
Agent context and state Pydantic models for Agency OS.
Replaces Dict[str, Any] in agent context management.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from shared.types.json import JSONValue
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AgentStatus(str, Enum):
    """Status of an agent."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Metadata for an agent session."""
    session_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    parent_session_id: Optional[str] = None
    user_id: Optional[str] = None
    environment: str = Field(default="production")
    tags: List[str] = Field(default_factory=list)
    custom_data: Dict[str, JSONValue] = Field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.end_time is None

    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def end_session(self) -> None:
        """Mark session as ended."""
        self.end_time = datetime.now()


class TaskContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Context for a specific task."""
    task_id: str
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, JSONValue] = Field(default_factory=dict)
    output_data: Dict[str, JSONValue] = Field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = Field(default_factory=list)

    @field_validator('retry_count')
    def validate_retry_count(cls, v: int, values: Dict[str, object]) -> int:
        """Ensure retry count doesn't exceed max."""
        max_retries = values.get('max_retries', 3)
        if v > max_retries:
            raise ValueError(f'retry_count {v} exceeds max_retries {max_retries}')
        return v

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries

    def mark_started(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def mark_completed(self, output: Dict[str, JSONValue]) -> None:
        """Mark task as completed with output."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.output_data = output

    def mark_failed(self, error: str) -> None:
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error


class AgentState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """Current state of an agent."""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.INITIALIZING
    current_task: Optional[TaskContext] = None
    task_queue: List[TaskContext] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    resource_usage: Dict[str, float] = Field(default_factory=dict)
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    error_count: int = 0
    success_count: int = 0

    def is_available(self) -> bool:
        """Check if agent is available for new tasks."""
        return self.status in [AgentStatus.READY, AgentStatus.WAITING]

    def has_capacity(self, max_queue_size: int = 10) -> bool:
        """Check if agent can accept more tasks."""
        return len(self.task_queue) < max_queue_size

    def add_task(self, task: TaskContext) -> None:
        """Add task to queue."""
        self.task_queue.append(task)

    def get_next_task(self) -> Optional[TaskContext]:
        """Get next task from queue."""
        if self.task_queue:
            task = self.task_queue.pop(0)
            self.current_task = task
            self.status = AgentStatus.RUNNING
            return task
        return None

    def complete_current_task(self) -> None:
        """Mark current task as completed."""
        if self.current_task:
            self.completed_tasks.append(self.current_task.task_id)
            self.success_count += 1
            self.current_task = None
            self.status = AgentStatus.READY

    def update_heartbeat(self) -> None:
        """Update last heartbeat time."""
        self.last_heartbeat = datetime.now()

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total


class AgentContextData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """
    Complete agent context data.
    Replaces Dict[str, Any] for agent context management.
    """
    session: SessionMetadata
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    shared_memory: Dict[str, JSONValue] = Field(default_factory=dict)
    global_config: Dict[str, JSONValue] = Field(default_factory=dict)
    active_handoffs: List[Dict[str, str]] = Field(default_factory=list)
    message_queue: List[Dict[str, JSONValue]] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)

    def add_agent(self, agent: AgentState) -> None:
        """Add or update agent state."""
        self.agent_states[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID."""
        return self.agent_states.get(agent_id)

    def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs."""
        return [
            agent_id for agent_id, state in self.agent_states.items()
            if state.status not in [AgentStatus.TERMINATED, AgentStatus.ERROR]
        ]

    def has_active_tasks(self) -> bool:
        """Check if any agents have active tasks."""
        return any(
            state.current_task is not None
            for state in self.agent_states.values()
        )

    def get_total_queued_tasks(self) -> int:
        """Get total number of queued tasks across all agents."""
        return sum(
            len(state.task_queue)
            for state in self.agent_states.values()
        )

    def broadcast_message(self, message: Dict[str, JSONValue]) -> None:
        """Add message to broadcast queue."""
        message['timestamp'] = datetime.now().isoformat()
        self.message_queue.append(message)

    def to_dict(self) -> Dict[str, JSONValue]:
        """Convert to dictionary for backward compatibility."""
        return self.model_dump(mode='json')