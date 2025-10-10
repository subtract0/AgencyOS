"""
Session checkpoint save/load for Leap 3 stateful learning.

Implements checkpoint persistence to ~/.agency/sessions/{session_id}/checkpoints/
with JSON serialization, atomic writes, and SHA256 integrity validation.

Constitutional Compliance:
- Article I: Complete context (read SessionState model before implementation)
- Article II: TDD required, Result pattern for all operations
- Article IV: Telemetry logging for checkpoint operations
- Article V: Follow spec (specs/leap_3_stateful_learning.md lines 728-874)

Specification: specs/leap_3_stateful_learning.md (Milestone M2)
Phase: Leap 3 - Checkpoint Persistence
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from shared.models.session import SessionState
from shared.type_definitions.result import Err, Ok, Result

logger = logging.getLogger(__name__)


class CheckpointError(BaseModel):
    """
    Checkpoint error information.

    Provides structured error details for checkpoint operations.

    Constitutional Compliance:
    - Article II (Law #2): Strict typing with Pydantic, no Dict[Any, Any]
    """

    error_type: str = Field(..., description="Error classification")
    message: str = Field(..., description="Human-readable error message")

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, v: str) -> str:
        """Ensure error_type is non-empty."""
        if not v or not v.strip():
            raise ValueError("error_type cannot be empty")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Ensure message is non-empty."""
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v


class SessionCheckpoint(BaseModel):
    """
    Session checkpoint metadata and data.

    Stores checkpoint ID, timestamp, serialized session state, and integrity checksum.

    Constitutional Compliance:
    - Article II (Law #2): Strict typing with Pydantic
    - Article II (Law #5): SHA256 checksum for integrity validation
    """

    checkpoint_id: str = Field(..., description="Unique checkpoint identifier")
    timestamp: datetime = Field(..., description="Checkpoint creation time")
    session_state_json: str = Field(..., description="Serialized SessionState JSON")
    checksum: str = Field(..., description="SHA256 hex digest of session_state_json")

    @field_validator("checkpoint_id")
    @classmethod
    def validate_checkpoint_id(cls, v: str) -> str:
        """Ensure checkpoint_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("checkpoint_id cannot be empty")
        return v

    @field_validator("checksum")
    @classmethod
    def validate_checksum_format(cls, v: str) -> str:
        """Ensure checksum is valid SHA256 hex (64 characters)."""
        if not v or len(v) != 64:
            raise ValueError("checksum must be 64-character SHA256 hex digest")
        if not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("checksum must be hexadecimal")
        return v.lower()


def save_checkpoint(
    session_state: SessionState, session_id: str, base_path: str = str(Path.home() / ".agency")
) -> Result[SessionCheckpoint, CheckpointError]:
    """
    Save session checkpoint to ~/.agency/sessions/{session_id}/checkpoints/.

    Uses atomic write pattern (write to .tmp, then rename) to prevent corruption.
    Calculates SHA256 checksum for integrity validation.

    Args:
        session_state: SessionState to checkpoint
        session_id: Session identifier for directory structure
        base_path: Base directory (default: ~/.agency)

    Returns:
        Result with SessionCheckpoint on success, CheckpointError on failure

    Constitutional Compliance:
    - Article I: Complete context (saves full SessionState)
    - Article II: Result pattern for error handling
    - Article IV: Telemetry logging for learning
    - Article V: Atomic writes prevent corruption

    Example:
        >>> from shared.models.session import SessionState, SessionStatus
        >>> session = SessionState(
        ...     session_id="test_session",
        ...     agent_name="planner",
        ...     status=SessionStatus.RUNNING
        ... )
        >>> result = save_checkpoint(session, "test_session")
        >>> if result.is_ok():
        ...     checkpoint = result.unwrap()
        ...     print(f"Saved: {checkpoint.checkpoint_id}")
    """
    try:
        # Validate session_id
        if not session_id or not session_id.strip():
            return Err(
                CheckpointError(
                    error_type="validation_error", message="session_id cannot be empty"
                )
            )

        # Create checkpoints directory
        checkpoints_dir = Path(base_path) / "sessions" / session_id / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Generate checkpoint ID with timestamp
        timestamp = datetime.now()
        checkpoint_id = f"checkpoint_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

        # Serialize SessionState to JSON
        session_state_json = session_state.model_dump_json(indent=2)

        # Calculate SHA256 checksum
        checksum = hashlib.sha256(session_state_json.encode("utf-8")).hexdigest()

        # Create SessionCheckpoint model
        checkpoint = SessionCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=timestamp,
            session_state_json=session_state_json,
            checksum=checksum,
        )

        # Atomic write: write to temp file, then rename
        checkpoint_file = checkpoints_dir / f"{checkpoint_id}.json"
        temp_file = checkpoints_dir / f"{checkpoint_id}.tmp"

        try:
            # Write checkpoint to temp file
            with open(temp_file, "w") as f:
                json.dump(checkpoint.model_dump(mode="json"), f, indent=2, default=str)

            # Atomic rename (POSIX guarantees atomicity)
            temp_file.rename(checkpoint_file)

            # Log telemetry for Article IV
            logger.info(
                f"Checkpoint saved: {checkpoint_id} "
                f"(session: {session_id}, "
                f"size: {len(session_state_json)} bytes, "
                f"checksum: {checksum[:8]}...)"
            )

            return Ok(checkpoint)

        finally:
            # Clean up temp file if it still exists
            if temp_file.exists():
                temp_file.unlink()

    except PermissionError as e:
        return Err(
            CheckpointError(
                error_type="io_error",
                message=f"Permission denied writing checkpoint: {str(e)}",
            )
        )
    except OSError as e:
        return Err(
            CheckpointError(
                error_type="io_error", message=f"Failed to write checkpoint: {str(e)}"
            )
        )
    except Exception as e:
        return Err(
            CheckpointError(
                error_type="unexpected_error",
                message=f"Checkpoint save failed: {str(e)}",
            )
        )


def load_checkpoint(
    checkpoint_id: str, session_id: str, base_path: str = str(Path.home() / ".agency")
) -> Result[SessionState, CheckpointError]:
    """
    Load session checkpoint from ~/.agency/sessions/{session_id}/checkpoints/.

    Validates SHA256 checksum to ensure data integrity.

    Args:
        checkpoint_id: Checkpoint identifier to load
        session_id: Session identifier for directory structure
        base_path: Base directory (default: ~/.agency)

    Returns:
        Result with SessionState on success, CheckpointError on failure

    Constitutional Compliance:
    - Article I: Complete context restoration
    - Article II: Checksum validation prevents corruption
    - Article II: Result pattern for error handling
    - Article IV: Telemetry logging for learning

    Example:
        >>> result = load_checkpoint("checkpoint_20251010_143022", "test_session")
        >>> if result.is_ok():
        ...     session = result.unwrap()
        ...     print(f"Loaded session: {session.session_id}")
        ... else:
        ...     error = result.unwrap_err()
        ...     print(f"Load failed: {error.message}")
    """
    try:
        # Validate inputs
        if not checkpoint_id or not checkpoint_id.strip():
            return Err(
                CheckpointError(
                    error_type="validation_error",
                    message="checkpoint_id cannot be empty",
                )
            )

        if not session_id or not session_id.strip():
            return Err(
                CheckpointError(
                    error_type="validation_error", message="session_id cannot be empty"
                )
            )

        # Construct checkpoint file path
        checkpoint_file = (
            Path(base_path)
            / "sessions"
            / session_id
            / "checkpoints"
            / f"{checkpoint_id}.json"
        )

        # Check file exists
        if not checkpoint_file.exists():
            return Err(
                CheckpointError(
                    error_type="io_error",
                    message=f"Checkpoint file not found: {checkpoint_file}",
                )
            )

        # Read checkpoint file
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)

        # Validate and parse checkpoint
        checkpoint = SessionCheckpoint(**checkpoint_data)

        # Verify SHA256 checksum
        calculated_checksum = hashlib.sha256(
            checkpoint.session_state_json.encode("utf-8")
        ).hexdigest()

        if calculated_checksum != checkpoint.checksum:
            return Err(
                CheckpointError(
                    error_type="checksum_mismatch",
                    message=f"Checksum mismatch: expected {checkpoint.checksum[:8]}..., "
                    f"got {calculated_checksum[:8]}...",
                )
            )

        # Deserialize SessionState
        session_state_dict = json.loads(checkpoint.session_state_json)
        session_state = SessionState(**session_state_dict)

        # Log telemetry for Article IV
        logger.info(
            f"Checkpoint loaded: {checkpoint_id} "
            f"(session: {session_id}, "
            f"checksum verified: {calculated_checksum[:8]}...)"
        )

        return Ok(session_state)

    except json.JSONDecodeError as e:
        return Err(
            CheckpointError(
                error_type="json_decode_error",
                message=f"Invalid JSON in checkpoint: {str(e)}",
            )
        )
    except PermissionError as e:
        return Err(
            CheckpointError(
                error_type="io_error",
                message=f"Permission denied reading checkpoint: {str(e)}",
            )
        )
    except OSError as e:
        return Err(
            CheckpointError(
                error_type="io_error", message=f"Failed to read checkpoint: {str(e)}"
            )
        )
    except ValueError as e:
        return Err(
            CheckpointError(
                error_type="validation_error",
                message=f"Invalid checkpoint data: {str(e)}",
            )
        )
    except Exception as e:
        return Err(
            CheckpointError(
                error_type="unexpected_error",
                message=f"Checkpoint load failed: {str(e)}",
            )
        )
