"""
Lock metadata models for multi-agent coordination.

Constitutional compliance:
- ADR-008: Strict typing enforcement (no Dict[Any, Any])
- ADR-010: Result pattern for error handling
- Constitutional Law #2: Explicit types always
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LockMetadata(BaseModel):
    """
    Enhanced lock file metadata for multi-agent coordination.

    Used to store rich metadata in lock files for visibility and debugging.
    """

    session_id: str = Field(..., description="Unique session identifier")
    timestamp: datetime = Field(..., description="Lock acquisition time (ISO 8601)")
    heartbeat: datetime = Field(..., description="Last heartbeat update time (ISO 8601)")
    terminal: str = Field(..., description="Terminal identifier (e.g., terminal_1)")
    user: str = Field(..., description="System user who owns the lock")
    task_description: str = Field(
        ..., description="Human-readable task name (e.g., Priority #1: Task Name)"
    )

    model_config = ConfigDict(extra="forbid")


class LockHandle(BaseModel):
    """
    Handle returned after successful lock acquisition.

    Contains references needed for lock release and heartbeat management.
    """

    task_id: str = Field(..., description="Task identifier")
    session_id: str = Field(..., description="Session that owns the lock")
    lock_file_path: str = Field(..., description="Path to lock file")
    heartbeat_thread_id: str | None = Field(
        default=None, description="Heartbeat thread identifier (if active)"
    )

    model_config = ConfigDict(extra="forbid")


class LockError(BaseModel):
    """
    Error information for lock operations.

    Used with Result[T, LockError] pattern for functional error handling.
    """

    error_type: str = Field(
        ...,
        description="Error type: AlreadyLocked, NotOwned, NotFound, IOError, InvalidSession",
    )
    message: str = Field(..., description="Human-readable error message")
    task_id: str | None = Field(default=None, description="Task that caused the error")
    session_id: str | None = Field(default=None, description="Session involved in error")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def already_locked(cls, task_id: str, holder_session: str) -> "LockError":
        """Create AlreadyLocked error."""
        return cls(
            error_type="AlreadyLocked",
            message=f"Task '{task_id}' is locked by session '{holder_session}'",
            task_id=task_id,
            session_id=holder_session,
        )

    @classmethod
    def not_owned(cls, task_id: str, session_id: str) -> "LockError":
        """Create NotOwned error."""
        return cls(
            error_type="NotOwned",
            message=f"Session '{session_id}' does not own lock for task '{task_id}'",
            task_id=task_id,
            session_id=session_id,
        )

    @classmethod
    def not_found(cls, task_id: str) -> "LockError":
        """Create NotFound error."""
        return cls(
            error_type="NotFound",
            message=f"No lock found for task '{task_id}'",
            task_id=task_id,
        )

    @classmethod
    def io_error(cls, message: str, task_id: str | None = None) -> "LockError":
        """Create IOError."""
        return cls(
            error_type="IOError",
            message=f"Filesystem error: {message}",
            task_id=task_id,
        )

    @classmethod
    def invalid_session(cls, session_id: str) -> "LockError":
        """Create InvalidSession error."""
        return cls(
            error_type="InvalidSession",
            message=f"Invalid session ID format: '{session_id}'",
            session_id=session_id,
        )
