"""
Session state management models for Agency OS.

Provides typed models for session state, compression metadata, checkpoint management,
and garbage collection. Implements TTL-based expiration and retention policies.

Constitutional Compliance:
- Article II (Law #2): Strict typing with Pydantic, no Dict[Any, Any]
- Article V: Follows spec: specs/leap_2_session_state_optimization.md
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.type_definitions.json_value import JSONValue

if TYPE_CHECKING:
    pass


class SessionStatus(str, Enum):
    """
    Session lifecycle states.

    PENDING: Created but not started
    RUNNING: Currently executing
    CHECKPOINTED: Paused with checkpoint saved
    COMPLETED: Successfully finished
    ABANDONED: Inactive for >7 days (not completed)
    EXPIRED: TTL exceeded
    """

    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class CompressionMetadata(BaseModel):
    """
    Compression statistics for session state.

    Tracks compression performance metrics for monitoring and optimization.
    """

    model_config = ConfigDict(extra="forbid")

    algorithm: str = Field(default="zlib", description="Compression algorithm")
    compression_level: int = Field(default=6, ge=1, le=9, description="zlib level (1-9)")
    original_size_bytes: int = Field(..., description="Uncompressed size")
    compressed_size_bytes: int = Field(..., description="Compressed size")
    compression_ratio: float = Field(..., ge=0, le=1, description="compressed/original")
    compression_time_ms: float = Field(..., description="Compression duration")

    @property
    def size_reduction_percent(self) -> float:
        """Calculate percentage size reduction."""
        return (1 - self.compression_ratio) * 100


class TaskProgress(BaseModel):
    """
    Summary of task progress metrics.

    Provides a read-only view of task progress state from SessionState.

    Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.4.1
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(default="", description="Task identifier")
    task_type: str = Field(default="", description="Task classification")
    progress_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Task completion percentage"
    )
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    total_steps: int = Field(default=0, ge=0)
    estimated_time_remaining_seconds: float | None = None
    started_at: datetime = Field(default_factory=datetime.now)
    estimated_completion_at: datetime | None = None


class TaskContext(BaseModel):
    """
    Task context for session resume.

    Provides all necessary context to resume a task from a checkpoint.

    Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
    """

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Session identifier")
    task_id: str = Field(default="", description="Task identifier")
    task_type: str = Field(default="", description="Task classification")
    progress_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Task completion percentage"
    )
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    active_memory_refs: list[str] = Field(default_factory=list)
    pinned_memories: list[str] = Field(default_factory=list)


class CheckpointMetadata(BaseModel):
    """
    Metadata for checkpoint/resume functionality.

    Supports multi-day task persistence with delta encoding and integrity validation.
    """

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(..., description="Unique checkpoint identifier")
    parent_checkpoint_id: str | None = Field(None, description="Previous checkpoint for delta")
    checkpoint_time: datetime = Field(default_factory=datetime.now)
    step_name: str = Field(..., description="Workflow step at checkpoint")
    completed_steps: list[str] = Field(default_factory=list)
    pending_steps: list[str] = Field(default_factory=list)
    delta_encoded: bool = Field(False, description="Whether delta encoding used")
    checksum: str = Field(..., description="SHA256 checksum for integrity")


class SessionState(BaseModel):
    """
    Optimized session state with compression and persistence support.

    Implements TTL-based expiration, compression metadata tracking,
    and checkpoint/resume capabilities for multi-day tasks.

    Example:
        >>> from datetime import datetime
        >>> session = SessionState(
        ...     session_id="session_20251010_123456",
        ...     agent_name="planner",
        ...     status=SessionStatus.RUNNING,
        ...     metadata={"task": "Create plan"}
        ... )
        >>> session.is_expired()
        False
        >>> session.mark_updated()
    """

    model_config = ConfigDict(extra="forbid")

    # Core session metadata
    session_id: str = Field(..., description="Unique session identifier")
    agent_name: str = Field(..., description="Agent owning this session")
    status: SessionStatus = Field(default=SessionStatus.PENDING)

    # Timestamps and TTL
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ttl_seconds: int = Field(default=2_592_000, description="30 days default")  # 30 * 24 * 60 * 60
    expires_at: datetime | None = Field(None, description="Calculated expiration time")

    # State content (compressed when serialized)
    metadata: dict[str, JSONValue] = Field(default_factory=dict)
    memory_snapshots: list[dict[str, JSONValue]] = Field(default_factory=list)
    tool_results: list[dict[str, JSONValue]] = Field(default_factory=list)

    # Compression and checkpoint metadata
    compression: CompressionMetadata | None = None
    checkpoint: CheckpointMetadata | None = None

    # NEW: Task Progress (Leap 3 - Spec Section 3.1)
    task_id: str | None = Field(None, description="Current task identifier")
    task_type: str | None = Field(None, description="Task classification")
    task_progress_percent: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Task completion percentage (0-100)",
    )
    completed_steps: list[str] = Field(default_factory=list, description="Workflow steps completed")
    pending_steps: list[str] = Field(default_factory=list, description="Workflow steps remaining")

    # NEW: Memory References (Leap 3 - Spec Section 3.1)
    active_memory_refs: list[str] = Field(
        default_factory=list, description="VectorStore memory keys currently in use"
    )
    pinned_memories: list[str] = Field(
        default_factory=list, description="Critical memories to retain (no GC)"
    )
    memory_snapshot_id: str | None = Field(None, description="Latest MemorySnapshot reference")

    # NEW: Agent States (Leap 3 - Spec Section 3.1)
    agent_states: dict[str, Any] = Field(
        default_factory=dict, description="Map of agent_id → AgentStateLearning"
    )

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Auto-calculate expires_at if not provided
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)

    def is_expired(self) -> bool:
        """
        Check if session has expired based on TTL.

        Returns:
            True if current time exceeds expires_at
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_completed(self) -> bool:
        """
        Check if session is in completed state.

        Returns:
            True if status is COMPLETED
        """
        return self.status == SessionStatus.COMPLETED

    def is_abandoned(self) -> bool:
        """
        Check if session is abandoned (not updated in 7 days).

        A session is considered abandoned if:
        - Not in COMPLETED status
        - No updates for >7 days

        Returns:
            True if session is abandoned
        """
        if self.status == SessionStatus.COMPLETED:
            return False
        idle_time = datetime.now() - self.updated_at
        return idle_time > timedelta(days=7)

    def mark_updated(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now()

    # NEW METHODS: Task Progress Tracking (Spec Section 3.1)

    def get_task_progress(self) -> TaskProgress:
        """
        Get current task progress summary.

        Returns:
            TaskProgress model with current state

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
        """
        total_steps = len(self.completed_steps) + len(self.pending_steps)

        return TaskProgress(
            task_id=self.task_id or "",
            task_type=self.task_type or "",
            progress_percent=self.task_progress_percent,
            completed_steps=self.completed_steps,
            pending_steps=self.pending_steps,
            total_steps=total_steps,
            started_at=self.created_at,
        )

    def update_task_progress(self, completed_step: str) -> None:
        """
        Mark a step as completed and auto-update progress percentage.

        Args:
            completed_step: Name of the step that was just completed

        Side Effects:
            - Adds step to completed_steps (idempotent)
            - Removes step from pending_steps if present
            - Recalculates task_progress_percent
            - Updates updated_at timestamp

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
        """
        # Add to completed_steps if not already there (idempotent)
        if completed_step not in self.completed_steps:
            self.completed_steps.append(completed_step)

        # Remove from pending_steps if present
        if completed_step in self.pending_steps:
            self.pending_steps.remove(completed_step)

        # Recalculate progress percentage
        total_steps = len(self.completed_steps) + len(self.pending_steps)
        if total_steps > 0:
            self.task_progress_percent = (len(self.completed_steps) / total_steps) * 100.0
        else:
            self.task_progress_percent = 0.0

        # Update timestamp
        self.mark_updated()

    def get_active_agent_states(self) -> dict[str, Any]:
        """
        Get all agent states with status != TERMINATED.

        Returns:
            Dictionary of agent_id → AgentStateLearning for active agents

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
        """
        return {
            agent_id: state
            for agent_id, state in self.agent_states.items()
            if not (hasattr(state, "status") and state.status == "terminated")
        }

    def add_memory_reference(self, memory_key: str, pinned: bool = False) -> None:
        """
        Add memory reference to active_memory_refs.

        Args:
            memory_key: VectorStore memory key to add
            pinned: If True, also add to pinned_memories (no GC)

        Side Effects:
            - Adds key to active_memory_refs (idempotent)
            - Optionally adds to pinned_memories if pinned=True
            - Updates updated_at timestamp

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
        """
        # Add to active refs (idempotent)
        if memory_key not in self.active_memory_refs:
            self.active_memory_refs.append(memory_key)

        # Add to pinned if requested
        if pinned and memory_key not in self.pinned_memories:
            self.pinned_memories.append(memory_key)

        # Update timestamp
        self.mark_updated()

    def resume_task_context(self) -> TaskContext:
        """
        Create TaskContext from current session state for task resume.

        Returns:
            TaskContext model with session and task state

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 3.1
        """
        return TaskContext(
            session_id=self.session_id,
            task_id=self.task_id or "",
            task_type=self.task_type or "",
            progress_percent=self.task_progress_percent,
            completed_steps=self.completed_steps,
            pending_steps=self.pending_steps,
            active_memory_refs=self.active_memory_refs,
            pinned_memories=self.pinned_memories,
        )

    # VALIDATORS: Field validation (Spec Section 6.1)

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """
        Ensure session_id is non-empty.

        Note: Spec recommends "session_" prefix, but validation is lenient
        for backward compatibility with existing tests.

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 6.1
        """
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v

    @field_validator("agent_states")
    @classmethod
    def validate_agent_states(cls, v: dict[str, Any]) -> dict[str, Any]:
        """
        Ensure all agent_states have valid agent_id keys.

        Spec Reference: specs/leap_3_session_state_models_spec.md Section 6.1
        """
        for agent_id, state in v.items():
            if not agent_id or not agent_id.strip():
                raise ValueError("agent_states keys cannot be empty")
            # Only validate agent_id match if state has agent_id attribute
            if hasattr(state, "agent_id") and state.agent_id != agent_id:
                raise ValueError(
                    f"agent_states key '{agent_id}' does not match "
                    f"state.agent_id '{state.agent_id}'"
                )
        return v


class GCResult(BaseModel):
    """
    Result of garbage collection run.

    Tracks metrics for monitoring and telemetry.
    """

    model_config = ConfigDict(extra="forbid")

    sessions_scanned: int = Field(0, description="Total sessions evaluated")
    sessions_deleted: int = Field(0, description="Sessions deleted")
    sessions_archived: int = Field(0, description="Sessions archived (completed)")
    disk_space_reclaimed_mb: float = Field(0.0, description="Disk space freed (megabytes)")
    collection_time_ms: float = Field(0.0, description="Total GC execution time")
    errors: list[str] = Field(default_factory=list, description="Error messages")


class RetentionPolicy(BaseModel):
    """
    Configurable retention policy for garbage collection.

    Defines how long different session types should be retained.
    """

    model_config = ConfigDict(extra="forbid")

    completed_retention_days: int = Field(90, description="Retention for completed sessions")
    abandoned_retention_days: int = Field(30, description="Retention for abandoned sessions")
    failed_retention_days: int = Field(7, description="Retention for failed sessions")
    respect_ttl: bool = Field(True, description="Honor session TTL regardless of status")
    archive_completed: bool = Field(
        True, description="Archive completed sessions instead of deleting"
    )
