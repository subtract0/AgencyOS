"""
Test suite for session checkpoint save/load functionality.

Constitutional Compliance:
- Article II: TDD - tests written FIRST
- Article II (Law #2): Strict typing, no Dict[Any, Any]
- Article V: Follows spec: specs/leap_3_stateful_learning.md:728-874

Tests cover:
1. save_checkpoint() - Success case with atomic writes
2. load_checkpoint() - Success case with SHA256 validation
3. Checkpoint not found error handling
4. Checksum validation failure
5. Atomic write on failure (temp file cleanup)
6. Auto-create directories if missing
7. Result<T,E> pattern validation

Specification: specs/leap_3_stateful_learning.md (Milestone M2)
Verification Target: checkpoint_persistence_leap3
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from shared.models.session import SessionState, SessionStatus
from shared.session_checkpoint import (
    CheckpointError,
    SessionCheckpoint,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create temporary checkpoint directory for tests."""
    checkpoint_dir = tmp_path / "sessions" / "test_session_123" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir


@pytest.fixture
def sample_session_state():
    """Create sample SessionState for testing."""
    return SessionState(
        session_id="test_session_123",
        agent_name="test_agent",
        status=SessionStatus.RUNNING,
        task_id="task_001",
        task_type="implementation",
        task_progress_percent=45.5,
        completed_steps=["step1", "step2"],
        pending_steps=["step3", "step4"],
        active_memory_refs=["mem_001", "mem_002"],
        pinned_memories=["mem_001"],
        metadata={"project": "Agency", "priority": "high"},
    )


class TestSaveCheckpoint:
    """Test save_checkpoint() functionality."""

    def test_save_checkpoint_success(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN a valid SessionState
        WHEN save_checkpoint() is called
        THEN it should create checkpoint file with SHA256 checksum
        AND return Ok(SessionCheckpoint)
        """
        # Set checkpoint directory
        base_path = str(temp_checkpoint_dir.parent.parent.parent)
        result = save_checkpoint(sample_session_state, "test_session_123", base_path)

        # Assert: Result is Ok
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err().message if result.is_err() else ''}"

        checkpoint = result.unwrap()

        # Verify checkpoint model
        assert isinstance(checkpoint, SessionCheckpoint)
        assert checkpoint.checksum != ""
        assert len(checkpoint.checksum) == 64  # SHA256 hex digest length

        # Verify checkpoint file exists
        checkpoint_file = (
            temp_checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        )
        assert checkpoint_file.exists(), f"Checkpoint file not found: {checkpoint_file}"

        # Verify file contains valid JSON
        with open(checkpoint_file) as f:
            data = json.load(f)
            assert "checkpoint_id" in data
            assert "checksum" in data
            assert "session_state_json" in data

    def test_save_checkpoint_auto_creates_directories(self, tmp_path, sample_session_state):
        """
        GIVEN a non-existent checkpoint directory
        WHEN save_checkpoint() is called
        THEN it should auto-create the directory structure
        AND save checkpoint successfully
        """
        # Use a fresh directory that doesn't exist yet
        non_existent_dir = tmp_path / "new_sessions"

        result = save_checkpoint(sample_session_state, "test_session_123", str(non_existent_dir))

        # Assert: Success with auto-created directories
        assert result.is_ok(), f"Expected Ok, got Err: {result.unwrap_err().message if result.is_err() else ''}"

        checkpoint = result.unwrap()
        checkpoint_file = (
            non_existent_dir
            / "sessions"
            / "test_session_123"
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )

        assert checkpoint_file.exists(), "Checkpoint file not created despite auto-create"

    def test_save_checkpoint_atomic_write(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN save_checkpoint() execution
        WHEN checkpoint is saved
        THEN no temp files should be left behind
        AND no partial checkpoint files should exist
        """
        base_path = str(temp_checkpoint_dir.parent.parent.parent)

        # Save a valid checkpoint
        result = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert result.is_ok()

        # Verify no .tmp files left behind
        tmp_files = list(temp_checkpoint_dir.glob("*.tmp"))
        assert len(tmp_files) == 0, f"Found temp files: {tmp_files}"

    def test_save_checkpoint_validates_session_id(self, sample_session_state):
        """
        GIVEN an empty session_id
        WHEN save_checkpoint() is called
        THEN it should return Err with validation error
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            result = save_checkpoint(sample_session_state, "", tmpdir)

        # Assert: Err with validation message
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "session_id cannot be empty" in error.message.lower()

    def test_save_checkpoint_handles_serialization_error(self, sample_session_state):
        """
        GIVEN a SessionState with non-serializable data
        WHEN save_checkpoint() is called
        THEN it should return Err with serialization error
        """
        # Mock model_dump_json to raise error
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                SessionState, "model_dump_json", side_effect=ValueError("Serialization failed")
            ):
                result = save_checkpoint(sample_session_state, "test_session_123", tmpdir)

        # Assert: Err with serialization error
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "failed" in error.message.lower()


class TestLoadCheckpoint:
    """Test load_checkpoint() functionality."""

    def test_load_checkpoint_success(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN a valid checkpoint file
        WHEN load_checkpoint() is called
        THEN it should return Ok(SessionState) with validated data
        """
        # Save checkpoint first
        base_path = str(temp_checkpoint_dir.parent.parent.parent)
        save_result = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert save_result.is_ok()

        checkpoint = save_result.unwrap()

        # Load checkpoint
        load_result = load_checkpoint(checkpoint.checkpoint_id, "test_session_123", base_path)

        # Assert: Ok with SessionState
        assert load_result.is_ok(), f"Expected Ok, got Err: {load_result.unwrap_err().message if load_result.is_err() else ''}"

        loaded_state = load_result.unwrap()

        # Verify loaded state matches original
        assert isinstance(loaded_state, SessionState)
        assert loaded_state.session_id == sample_session_state.session_id
        assert loaded_state.agent_name == sample_session_state.agent_name
        assert loaded_state.task_id == sample_session_state.task_id
        assert loaded_state.task_progress_percent == sample_session_state.task_progress_percent
        assert loaded_state.completed_steps == sample_session_state.completed_steps
        assert loaded_state.pending_steps == sample_session_state.pending_steps

    def test_load_checkpoint_not_found(self):
        """
        GIVEN a non-existent checkpoint_id
        WHEN load_checkpoint() is called
        THEN it should return Err with "not found" message
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_checkpoint("nonexistent_checkpoint", "test_session_123", tmpdir)

        # Assert: Err with not found message
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "not found" in error.message.lower()

    def test_load_checkpoint_checksum_validation_failure(
        self, temp_checkpoint_dir, sample_session_state
    ):
        """
        GIVEN a checkpoint file with corrupted checksum
        WHEN load_checkpoint() is called
        THEN it should return Err with checksum validation error
        """
        # Save checkpoint first
        base_path = str(temp_checkpoint_dir.parent.parent.parent)
        save_result = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert save_result.is_ok()

        checkpoint = save_result.unwrap()
        checkpoint_file = temp_checkpoint_dir / f"{checkpoint.checkpoint_id}.json"

        # Corrupt the checksum in the file
        with open(checkpoint_file, "r") as f:
            data = json.load(f)

        data["checksum"] = "0" * 64  # Invalid checksum

        with open(checkpoint_file, "w") as f:
            json.dump(data, f)

        # Attempt to load corrupted checkpoint
        load_result = load_checkpoint(checkpoint.checkpoint_id, "test_session_123", base_path)

        # Assert: Err with checksum validation error
        assert load_result.is_err()
        error = load_result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "checksum" in error.message.lower()

    def test_load_checkpoint_validates_session_id(self):
        """
        GIVEN an empty session_id
        WHEN load_checkpoint() is called
        THEN it should return Err with validation error
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_checkpoint("checkpoint_123", "", tmpdir)

        # Assert: Err with validation message
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "session_id cannot be empty" in error.message.lower()

    def test_load_checkpoint_handles_invalid_json(self, temp_checkpoint_dir):
        """
        GIVEN a checkpoint file with invalid JSON
        WHEN load_checkpoint() is called
        THEN it should return Err with parse error
        """
        checkpoint_id = "invalid_checkpoint"

        base_path = str(temp_checkpoint_dir.parent.parent.parent)
        checkpoint_file = temp_checkpoint_dir / f"{checkpoint_id}.json"

        # Write invalid JSON
        with open(checkpoint_file, "w") as f:
            f.write("{invalid json content")

        # Attempt to load
        load_result = load_checkpoint(checkpoint_id, "test_session_123", base_path)

        # Assert: Err with parse error
        assert load_result.is_err()
        error = load_result.unwrap_err()
        assert isinstance(error, CheckpointError)
        assert "json" in error.message.lower() or "decode" in error.message.lower()


class TestCheckpointVersioning:
    """Test checkpoint versioning with timestamps."""

    def test_checkpoint_timestamp_ordering(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN multiple checkpoints saved sequentially
        WHEN loading checkpoints
        THEN timestamps should reflect creation order
        """
        base_path = str(temp_checkpoint_dir.parent.parent.parent)

        # Save first checkpoint
        result1 = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert result1.is_ok()
        checkpoint1 = result1.unwrap()

        # Modify state and save second checkpoint
        sample_session_state.task_progress_percent = 75.0
        result2 = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert result2.is_ok()
        checkpoint2 = result2.unwrap()

        # Assert: Timestamps are ordered
        assert checkpoint2.timestamp >= checkpoint1.timestamp
        assert checkpoint2.checkpoint_id != checkpoint1.checkpoint_id

    def test_checkpoint_id_uniqueness(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN multiple checkpoints for same session
        WHEN saving checkpoints
        THEN each checkpoint_id should be unique
        """
        checkpoint_ids = set()

        base_path = str(temp_checkpoint_dir.parent.parent.parent)

        for i in range(5):
            result = save_checkpoint(sample_session_state, "test_session_123", base_path)
            assert result.is_ok()
            checkpoint = result.unwrap()
            checkpoint_ids.add(checkpoint.checkpoint_id)

        # Assert: All checkpoint IDs are unique
        assert len(checkpoint_ids) == 5, "Checkpoint IDs should be unique"


class TestCheckpointModel:
    """Test SessionCheckpoint Pydantic model."""

    def test_checkpoint_model_validation(self):
        """
        GIVEN valid checkpoint data
        WHEN creating SessionCheckpoint model
        THEN it should validate and construct successfully
        """
        checkpoint_data = {
            "checkpoint_id": "checkpoint_20251010_123456",
            "timestamp": datetime.now(),
            "session_state_json": '{"session_id": "session_123"}',
            "checksum": "a" * 64,
        }

        checkpoint = SessionCheckpoint(**checkpoint_data)

        assert checkpoint.checkpoint_id == checkpoint_data["checkpoint_id"]
        assert len(checkpoint.checksum) == 64

    def test_checkpoint_model_requires_all_fields(self):
        """
        GIVEN incomplete checkpoint data
        WHEN creating SessionCheckpoint model
        THEN it should raise validation error
        """
        incomplete_data = {
            "checkpoint_id": "checkpoint_123",
            # Missing required fields
        }

        with pytest.raises(ValueError):
            SessionCheckpoint(**incomplete_data)

    def test_checkpoint_model_validates_checksum_length(self):
        """
        GIVEN checkpoint data with invalid checksum length
        WHEN creating SessionCheckpoint model
        THEN it should raise validation error
        """
        invalid_data = {
            "checkpoint_id": "checkpoint_123",
            "timestamp": datetime.now(),
            "session_state_json": '{}',
            "checksum": "abc123",  # Too short
        }

        with pytest.raises(ValueError, match="checksum must be 64-character"):
            SessionCheckpoint(**invalid_data)


class TestCheckpointError:
    """Test CheckpointError error model."""

    def test_checkpoint_error_creation(self):
        """
        GIVEN error message and error_type
        WHEN creating CheckpointError
        THEN it should store error details
        """
        error = CheckpointError(message="Checkpoint not found", error_type="NOT_FOUND")

        assert error.message == "Checkpoint not found"
        assert error.error_type == "NOT_FOUND"

    def test_checkpoint_error_requires_non_empty_fields(self):
        """
        GIVEN empty error_type or message
        WHEN creating CheckpointError
        THEN it should raise validation error
        """
        with pytest.raises(ValueError, match="error_type cannot be empty"):
            CheckpointError(message="Test", error_type="")

        with pytest.raises(ValueError, match="message cannot be empty"):
            CheckpointError(message="", error_type="TEST")


class TestCheckpointIntegration:
    """Integration tests combining checkpoint features."""

    def test_full_checkpoint_lifecycle(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN a complete checkpoint lifecycle
        WHEN saving and loading checkpoint
        THEN all data should round-trip correctly
        """
        base_path = str(temp_checkpoint_dir.parent.parent.parent)

        # Save checkpoint
        save_result = save_checkpoint(sample_session_state, "test_session_123", base_path)
        assert save_result.is_ok()

        checkpoint = save_result.unwrap()

        # Load checkpoint
        load_result = load_checkpoint(checkpoint.checkpoint_id, "test_session_123", base_path)
        assert load_result.is_ok()

        loaded_state = load_result.unwrap()

        # Verify all fields match
        assert loaded_state.session_id == sample_session_state.session_id
        assert loaded_state.agent_name == sample_session_state.agent_name
        assert loaded_state.status == sample_session_state.status
        assert loaded_state.task_id == sample_session_state.task_id
        assert loaded_state.task_type == sample_session_state.task_type
        assert loaded_state.task_progress_percent == sample_session_state.task_progress_percent
        assert loaded_state.completed_steps == sample_session_state.completed_steps
        assert loaded_state.pending_steps == sample_session_state.pending_steps
        assert loaded_state.active_memory_refs == sample_session_state.active_memory_refs
        assert loaded_state.pinned_memories == sample_session_state.pinned_memories
        assert loaded_state.metadata == sample_session_state.metadata

    def test_multiple_checkpoints_same_session(self, temp_checkpoint_dir, sample_session_state):
        """
        GIVEN multiple checkpoints for the same session
        WHEN loading each checkpoint
        THEN each should restore correct state
        """
        base_path = str(temp_checkpoint_dir.parent.parent.parent)
        checkpoints = []

        # Save 3 checkpoints with different progress
        for i, progress in enumerate([25.0, 50.0, 75.0]):
            sample_session_state.task_progress_percent = progress
            sample_session_state.completed_steps = [f"step{j}" for j in range(1, i+2)]

            result = save_checkpoint(sample_session_state, "test_session_123", base_path)
            assert result.is_ok()
            checkpoints.append(result.unwrap())

        # Load and verify each checkpoint
        for i, checkpoint in enumerate(checkpoints):
            expected_progress = [25.0, 50.0, 75.0][i]

            load_result = load_checkpoint(checkpoint.checkpoint_id, "test_session_123", base_path)
            assert load_result.is_ok()

            loaded = load_result.unwrap()
            assert loaded.task_progress_percent == expected_progress
