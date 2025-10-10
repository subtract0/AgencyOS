"""
Tests for session checkpoint save/load functionality (Leap 3).

Constitutional Compliance:
- Article II: TDD approach - tests written FIRST (retroactive for existing impl)
- Article II (Law #2): Strict typing with Pydantic models
- Article V: Follows spec: specs/leap_3_stateful_learning.md lines 728-874

Test Coverage:
- save_checkpoint() with atomic writes and checksums
- load_checkpoint() with validation
- Error handling via Result pattern
- Auto-directory creation
- Checkpoint versioning with timestamps

Acceptance Criteria Validation:
- AC-1: save_checkpoint() writes JSON to ~/.agency/sessions/{session_id}/checkpoints/
- AC-2: load_checkpoint() reads and validates checkpoint data
- AC-3: Atomic writes using temp file + rename pattern
- AC-4: Result<SessionCheckpoint, CheckpointError> return types
- AC-5: Auto-create session directories if missing
- AC-6: Checkpoint versioning with timestamp
"""

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from shared.models.session import SessionState, SessionStatus
from shared.session_checkpoint import (
    CheckpointError,
    SessionCheckpoint,
    load_checkpoint,
    save_checkpoint,
)
from shared.type_definitions.result import Err, Ok


@pytest.fixture
def temp_session_dir():
    """Create temporary session directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session_id = "test_session_123"
        yield session_id, tmpdir


@pytest.fixture
def sample_session_state():
    """Create sample SessionState for testing."""
    return SessionState(
        session_id="test_session_123",
        agent_name="test_agent",
        status=SessionStatus.RUNNING,
        metadata={"task": "test_task", "priority": "high"},
        task_id="task_001",
        task_type="implementation",
        task_progress_percent=45.0,
        completed_steps=["step1", "step2"],
        pending_steps=["step3", "step4"],
        active_memory_refs=["mem_001", "mem_002"],
        pinned_memories=["mem_001"],
    )


class TestSaveCheckpoint:
    """Test save_checkpoint() functionality."""

    def test_save_checkpoint_creates_directory_if_missing(
        self, temp_session_dir, sample_session_state
    ):
        """AC-5: Test auto-creation of checkpoint directory."""
        session_id, base_path = temp_session_dir

        # Directory should not exist yet
        checkpoints_dir = Path(base_path) / "sessions" / session_id / "checkpoints"
        assert not checkpoints_dir.exists()

        # Save checkpoint
        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        # Should succeed
        assert result.is_ok()

        # Directory should now exist
        assert checkpoints_dir.exists()
        assert checkpoints_dir.is_dir()

    def test_save_checkpoint_writes_to_correct_location(
        self, temp_session_dir, sample_session_state
    ):
        """AC-1: Test checkpoint writes to ~/.agency/sessions/{session_id}/checkpoints/."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_ok()
        checkpoint = result.unwrap()

        # Verify file exists in correct location
        expected_path = (
            Path(base_path)
            / "sessions"
            / session_id
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )
        assert expected_path.exists()

    def test_save_checkpoint_writes_json_file(
        self, temp_session_dir, sample_session_state
    ):
        """AC-1: Test checkpoint writes valid JSON file."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_ok()
        checkpoint = result.unwrap()

        # Verify checkpoint file exists
        checkpoint_file = (
            Path(base_path)
            / "sessions"
            / session_id
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )
        assert checkpoint_file.exists()

        # Verify valid JSON
        with open(checkpoint_file, "r") as f:
            data = json.load(f)

        assert "checkpoint_id" in data
        assert "timestamp" in data
        assert "session_state_json" in data
        assert "checksum" in data

    def test_save_checkpoint_includes_correct_data(
        self, temp_session_dir, sample_session_state
    ):
        """Test checkpoint contains correct session state data."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        checkpoint = result.unwrap()

        # Verify session_state_json contains original data
        state_dict = json.loads(checkpoint.session_state_json)
        assert state_dict["session_id"] == "test_session_123"
        assert state_dict["agent_name"] == "test_agent"
        assert state_dict["task_id"] == "task_001"
        assert state_dict["task_progress_percent"] == 45.0
        assert state_dict["completed_steps"] == ["step1", "step2"]

    def test_save_checkpoint_generates_valid_sha256_checksum(
        self, temp_session_dir, sample_session_state
    ):
        """Test checkpoint SHA256 checksum validation."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        checkpoint = result.unwrap()

        # Calculate expected checksum
        expected_checksum = hashlib.sha256(
            checkpoint.session_state_json.encode("utf-8")
        ).hexdigest()

        assert checkpoint.checksum == expected_checksum
        assert len(checkpoint.checksum) == 64  # SHA256 hex length

    def test_save_checkpoint_uses_atomic_write(
        self, temp_session_dir, sample_session_state
    ):
        """AC-3: Test atomic write pattern (temp file + rename)."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_ok()

        # No .tmp files should remain after successful write
        checkpoints_dir = Path(base_path) / "sessions" / session_id / "checkpoints"
        tmp_files = list(checkpoints_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_save_checkpoint_generates_unique_checkpoint_ids(
        self, temp_session_dir, sample_session_state
    ):
        """AC-6: Test checkpoint_id uniqueness with timestamps."""
        session_id, base_path = temp_session_dir

        # Save first checkpoint
        result1 = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        # Small delay to ensure different timestamp
        time.sleep(0.001)

        # Save second checkpoint (with slight modification)
        sample_session_state.task_progress_percent = 50.0
        result2 = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert result1.is_ok()
        assert result2.is_ok()

        checkpoint1 = result1.unwrap()
        checkpoint2 = result2.unwrap()

        # Checkpoint IDs should be different
        assert checkpoint1.checkpoint_id != checkpoint2.checkpoint_id

    def test_save_checkpoint_returns_session_checkpoint_model(
        self, temp_session_dir, sample_session_state
    ):
        """AC-4: Test return type is Result[SessionCheckpoint, CheckpointError]."""
        session_id, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_ok()
        checkpoint = result.unwrap()

        # Verify type
        assert isinstance(checkpoint, SessionCheckpoint)

        # Verify required fields
        assert checkpoint.checkpoint_id
        assert isinstance(checkpoint.timestamp, datetime)
        assert checkpoint.session_state_json
        assert checkpoint.checksum

    def test_save_checkpoint_handles_invalid_session_id(
        self, temp_session_dir, sample_session_state
    ):
        """AC-4: Test error handling returns CheckpointError."""
        _, base_path = temp_session_dir

        result = save_checkpoint(
            session_state=sample_session_state,
            session_id="",  # Invalid: empty session_id
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert error.error_type == "validation_error"
        assert "session_id" in error.message.lower()


class TestLoadCheckpoint:
    """Test load_checkpoint() functionality."""

    def test_load_checkpoint_restores_session_state(
        self, temp_session_dir, sample_session_state
    ):
        """AC-2: Test checkpoint restore returns original SessionState."""
        session_id, base_path = temp_session_dir

        # Save checkpoint
        save_result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        checkpoint = save_result.unwrap()

        # Load checkpoint
        load_result = load_checkpoint(
            checkpoint_id=checkpoint.checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert load_result.is_ok()
        restored_state = load_result.unwrap()

        # Verify restored state matches original
        assert restored_state.session_id == sample_session_state.session_id
        assert restored_state.agent_name == sample_session_state.agent_name
        assert restored_state.task_id == sample_session_state.task_id
        assert (
            restored_state.task_progress_percent
            == sample_session_state.task_progress_percent
        )
        assert restored_state.completed_steps == sample_session_state.completed_steps
        assert restored_state.pending_steps == sample_session_state.pending_steps

    def test_load_checkpoint_validates_sha256_checksum(
        self, temp_session_dir, sample_session_state
    ):
        """AC-2: Test checksum validation detects corruption."""
        session_id, base_path = temp_session_dir

        # Save checkpoint
        save_result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        checkpoint = save_result.unwrap()

        # Corrupt the checkpoint file
        checkpoint_file = (
            Path(base_path)
            / "sessions"
            / session_id
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )

        with open(checkpoint_file, "r") as f:
            data = json.load(f)

        # Modify session_state_json without updating checksum
        data["session_state_json"] = json.dumps({"corrupted": True})

        with open(checkpoint_file, "w") as f:
            json.dump(data, f)

        # Load checkpoint - should fail checksum validation
        load_result = load_checkpoint(
            checkpoint_id=checkpoint.checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert load_result.is_err()
        error = load_result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert error.error_type == "checksum_mismatch"
        assert "checksum" in error.message.lower()

    def test_load_checkpoint_handles_missing_file(self, temp_session_dir):
        """AC-4: Test error handling for non-existent checkpoint."""
        session_id, base_path = temp_session_dir

        result = load_checkpoint(
            checkpoint_id="nonexistent_checkpoint",
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert error.error_type == "io_error"
        assert "not found" in error.message.lower()

    def test_load_checkpoint_handles_invalid_json(
        self, temp_session_dir, sample_session_state
    ):
        """Test error handling for corrupted JSON."""
        session_id, base_path = temp_session_dir

        # Create checkpoint directory
        checkpoints_dir = Path(base_path) / "sessions" / session_id / "checkpoints"
        checkpoints_dir.mkdir(parents=True)

        # Write invalid JSON
        checkpoint_id = "corrupt_checkpoint"
        checkpoint_file = checkpoints_dir / f"{checkpoint_id}.json"

        with open(checkpoint_file, "w") as f:
            f.write("{ invalid json }")

        # Load checkpoint - should fail
        result = load_checkpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert error.error_type == "json_decode_error"

    def test_load_checkpoint_handles_invalid_session_state(self, temp_session_dir):
        """Test error handling for invalid SessionState data."""
        session_id, base_path = temp_session_dir

        # Create checkpoint directory
        checkpoints_dir = Path(base_path) / "sessions" / session_id / "checkpoints"
        checkpoints_dir.mkdir(parents=True)

        # Create checkpoint with invalid SessionState
        checkpoint_id = "invalid_state_checkpoint"
        checkpoint_file = checkpoints_dir / f"{checkpoint_id}.json"

        invalid_state_json = json.dumps({"invalid": "state"})
        checksum = hashlib.sha256(invalid_state_json.encode("utf-8")).hexdigest()

        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "session_state_json": invalid_state_json,
            "checksum": checksum,
        }

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f)

        # Load checkpoint - should fail validation
        result = load_checkpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert error.error_type == "validation_error"

    def test_load_checkpoint_validates_empty_checkpoint_id(self, temp_session_dir):
        """Test validation of empty checkpoint_id."""
        session_id, base_path = temp_session_dir

        result = load_checkpoint(
            checkpoint_id="",
            session_id=session_id,
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "validation_error"
        assert "checkpoint_id" in error.message.lower()

    def test_load_checkpoint_validates_empty_session_id(self, temp_session_dir):
        """Test validation of empty session_id."""
        _, base_path = temp_session_dir

        result = load_checkpoint(
            checkpoint_id="some_checkpoint",
            session_id="",
            base_path=base_path,
        )

        assert result.is_err()
        error = result.unwrap_err()
        assert error.error_type == "validation_error"
        assert "session_id" in error.message.lower()


class TestCheckpointErrorModel:
    """Test CheckpointError Pydantic model."""

    def test_checkpoint_error_has_required_fields(self):
        """Test CheckpointError model structure."""
        error = CheckpointError(
            error_type="validation_error", message="Invalid checkpoint data"
        )

        assert error.error_type == "validation_error"
        assert error.message == "Invalid checkpoint data"

    def test_checkpoint_error_validates_error_type(self):
        """Test error_type validation."""
        # Empty error_type should fail
        with pytest.raises(ValueError, match="error_type cannot be empty"):
            CheckpointError(error_type="", message="Test")

    def test_checkpoint_error_validates_message(self):
        """Test message validation."""
        # Empty message should fail
        with pytest.raises(ValueError, match="message cannot be empty"):
            CheckpointError(error_type="test_error", message="")


class TestSessionCheckpointModel:
    """Test SessionCheckpoint Pydantic model."""

    def test_session_checkpoint_has_required_fields(self):
        """Test SessionCheckpoint model structure."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="ckpt_123",
            timestamp=datetime.now(),
            session_state_json='{"test": "data"}',
            checksum="a" * 64,  # Valid SHA256 hex
        )

        assert checkpoint.checkpoint_id == "ckpt_123"
        assert isinstance(checkpoint.timestamp, datetime)
        assert checkpoint.session_state_json == '{"test": "data"}'
        assert checkpoint.checksum == "a" * 64

    def test_session_checkpoint_validates_checkpoint_id(self):
        """Test checkpoint_id validation."""
        # Empty checkpoint_id should fail
        with pytest.raises(ValueError, match="checkpoint_id cannot be empty"):
            SessionCheckpoint(
                checkpoint_id="",
                timestamp=datetime.now(),
                session_state_json='{"test": "data"}',
                checksum="a" * 64,
            )

    def test_session_checkpoint_validates_checksum_length(self):
        """Test checksum format validation (SHA256 = 64 chars)."""
        # Invalid length should fail
        with pytest.raises(ValueError, match="64-character SHA256"):
            SessionCheckpoint(
                checkpoint_id="ckpt_123",
                timestamp=datetime.now(),
                session_state_json='{"test": "data"}',
                checksum="abc123",  # Too short
            )

    def test_session_checkpoint_validates_checksum_format(self):
        """Test checksum must be hexadecimal."""
        # Non-hex characters should fail
        with pytest.raises(ValueError, match="hexadecimal"):
            SessionCheckpoint(
                checkpoint_id="ckpt_123",
                timestamp=datetime.now(),
                session_state_json='{"test": "data"}',
                checksum="g" * 64,  # 'g' is not hex
            )

    def test_session_checkpoint_normalizes_checksum_to_lowercase(self):
        """Test checksum is normalized to lowercase."""
        checkpoint = SessionCheckpoint(
            checkpoint_id="ckpt_123",
            timestamp=datetime.now(),
            session_state_json='{"test": "data"}',
            checksum="A" * 64,  # Uppercase
        )

        assert checkpoint.checksum == "a" * 64  # Should be lowercase


class TestCheckpointIntegration:
    """Integration tests for save/load roundtrip."""

    def test_save_load_roundtrip_preserves_all_data(
        self, temp_session_dir, sample_session_state
    ):
        """Test full save/load cycle preserves all SessionState fields."""
        session_id, base_path = temp_session_dir

        # Save checkpoint
        save_result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        # Load checkpoint
        load_result = load_checkpoint(
            checkpoint_id=checkpoint.checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert load_result.is_ok()
        restored_state = load_result.unwrap()

        # Verify ALL fields match
        assert restored_state.session_id == sample_session_state.session_id
        assert restored_state.agent_name == sample_session_state.agent_name
        assert restored_state.status == sample_session_state.status
        assert restored_state.metadata == sample_session_state.metadata
        assert restored_state.task_id == sample_session_state.task_id
        assert restored_state.task_type == sample_session_state.task_type
        assert (
            restored_state.task_progress_percent
            == sample_session_state.task_progress_percent
        )
        assert restored_state.completed_steps == sample_session_state.completed_steps
        assert restored_state.pending_steps == sample_session_state.pending_steps
        assert (
            restored_state.active_memory_refs == sample_session_state.active_memory_refs
        )
        assert restored_state.pinned_memories == sample_session_state.pinned_memories

    def test_multiple_checkpoints_in_same_session(
        self, temp_session_dir, sample_session_state
    ):
        """Test creating multiple checkpoints for same session."""
        session_id, base_path = temp_session_dir

        # Save checkpoint 1
        result1 = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        # Update state
        sample_session_state.task_progress_percent = 75.0
        sample_session_state.completed_steps.append("step3")

        # Small delay for unique timestamp
        time.sleep(0.001)

        # Save checkpoint 2
        result2 = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )

        # Both should succeed
        assert result1.is_ok()
        assert result2.is_ok()

        # Load both checkpoints
        checkpoint1 = result1.unwrap()
        checkpoint2 = result2.unwrap()

        load_result1 = load_checkpoint(
            checkpoint_id=checkpoint1.checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        load_result2 = load_checkpoint(
            checkpoint_id=checkpoint2.checkpoint_id,
            session_id=session_id,
            base_path=base_path,
        )

        assert load_result1.is_ok()
        assert load_result2.is_ok()

        # Verify different progress states
        state1 = load_result1.unwrap()
        state2 = load_result2.unwrap()

        assert state1.task_progress_percent == 45.0
        assert state2.task_progress_percent == 75.0
        assert len(state1.completed_steps) == 2
        assert len(state2.completed_steps) == 3

    def test_checkpoints_isolated_per_session(
        self, temp_session_dir, sample_session_state
    ):
        """Test checkpoints are isolated by session_id."""
        session_id_1, base_path = temp_session_dir
        session_id_2 = "test_session_456"

        # Create second session
        session_state_2 = SessionState(
            session_id=session_id_2,
            agent_name="other_agent",
            status=SessionStatus.PENDING,
        )

        # Save checkpoints for both sessions
        result1 = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id_1,
            base_path=base_path,
        )

        result2 = save_checkpoint(
            session_state=session_state_2,
            session_id=session_id_2,
            base_path=base_path,
        )

        assert result1.is_ok()
        assert result2.is_ok()

        # Verify separate directories
        dir1 = Path(base_path) / "sessions" / session_id_1 / "checkpoints"
        dir2 = Path(base_path) / "sessions" / session_id_2 / "checkpoints"

        assert dir1.exists()
        assert dir2.exists()
        assert dir1 != dir2

    def test_checkpoint_timestamp_accuracy(
        self, temp_session_dir, sample_session_state
    ):
        """Test checkpoint timestamp is accurate."""
        session_id, base_path = temp_session_dir

        before_save = datetime.now()
        result = save_checkpoint(
            session_state=sample_session_state,
            session_id=session_id,
            base_path=base_path,
        )
        after_save = datetime.now()

        assert result.is_ok()
        checkpoint = result.unwrap()

        # Timestamp should be within the save window
        assert before_save <= checkpoint.timestamp <= after_save
