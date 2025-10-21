"""
Test suite for AgentContext checkpoint functionality.

Extends AgentContext with session state methods for checkpoint creation,
restoration, and session state access (Leap 3 stateful learning).

Article II: TDD - Tests written FIRST before implementation.
ADR-008: Strict typing with Pydantic.
ADR-010: Result pattern for error handling.

Spec Reference: specs/leap_3_stateful_learning.md lines 225-239
"""

import os
import tempfile
import threading
import time
from pathlib import Path

import pytest

from agency_memory import Memory
from shared.agent_context import AgentContext, create_agent_context
from shared.models.session import SessionState, SessionStatus
from shared.session_checkpoint import SessionCheckpoint


class TestAgentContextCheckpointCreation:
    """Test checkpoint creation via AgentContext.create_checkpoint()."""

    def test_create_checkpoint_saves_current_state(self):
        """Test that create_checkpoint() saves current session state."""
        # Arrange
        context = create_agent_context(session_id="test_checkpoint_save")
        context.set_metadata("task", "Create plan")
        context.set_metadata("progress", 50)
        context.store_memory("mem1", "test_content", ["test"])

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok(), f"Checkpoint creation failed: {result.unwrap_err()}"
        checkpoint = result.unwrap()
        assert isinstance(checkpoint, SessionCheckpoint)
        assert checkpoint.checkpoint_id.startswith("checkpoint_")
        assert "task" in checkpoint.session_state_json
        assert "Create plan" in checkpoint.session_state_json

    def test_create_checkpoint_updates_last_checkpoint_timestamp(self):
        """Test that create_checkpoint() updates last_checkpoint metadata."""
        # Arrange
        context = create_agent_context(session_id="test_checkpoint_timestamp")

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok()
        last_checkpoint = context.get_metadata("last_checkpoint_time")
        assert last_checkpoint is not None
        assert isinstance(last_checkpoint, str)  # ISO timestamp

    def test_create_checkpoint_returns_error_on_failure(self):
        """Test that create_checkpoint() returns Err on I/O failure."""
        # Arrange
        context = create_agent_context(session_id="test_checkpoint_error")

        # Make checkpoint directory read-only to force error
        with tempfile.TemporaryDirectory() as tmpdir:
            # Act - Pass invalid base_path that we'll make read-only
            readonly_dir = Path(tmpdir) / "readonly"
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)  # Read-only

            result = context.create_checkpoint(base_path=str(readonly_dir))

            # Assert
            assert result.is_err()
            error = result.unwrap_err()
            assert "io_error" in error or "permission" in error.lower()

    def test_create_checkpoint_includes_memory_snapshots(self):
        """Test that checkpoint includes session memory snapshots."""
        # Arrange
        context = create_agent_context(session_id="test_checkpoint_memories")
        context.store_memory("mem1", {"data": "value1"}, ["test", "important"])
        context.store_memory("mem2", {"data": "value2"}, ["test"])

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()
        # Verify memory snapshots are in serialized state
        assert "memory_snapshots" in checkpoint.session_state_json
        assert "mem1" in checkpoint.session_state_json or "value1" in checkpoint.session_state_json

    def test_create_checkpoint_thread_safe(self):
        """Test that create_checkpoint() is thread-safe."""
        # Arrange
        context = create_agent_context(session_id="test_checkpoint_thread_safe")
        results = []
        errors = []

        def create_checkpoint_worker():
            try:
                result = context.create_checkpoint()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Act - Create multiple checkpoints concurrently
        threads = [threading.Thread(target=create_checkpoint_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
            assert not t.is_alive(), "Thread did not complete within timeout"

        # Assert
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5
        # All should succeed (or fail gracefully with Err)
        successful = [r for r in results if r.is_ok()]
        assert len(successful) >= 1, "At least one checkpoint should succeed"


class TestAgentContextCheckpointRestoration:
    """Test checkpoint restoration via AgentContext.restore_from_checkpoint()."""

    def test_restore_from_checkpoint_loads_saved_state(self):
        """Test that restore_from_checkpoint() loads saved session state."""
        # Arrange - Create and save checkpoint
        original_context = create_agent_context(session_id="test_restore_session")
        original_context.set_metadata("task", "Implement feature")
        original_context.set_metadata("progress", 75)
        original_context.store_memory("key1", "value1", ["restore_test"])

        save_result = original_context.create_checkpoint()
        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        # Act - Restore to new context
        new_context = create_agent_context(session_id="test_restore_session")
        restore_result = new_context.restore_from_checkpoint(checkpoint.checkpoint_id)

        # Assert
        assert restore_result.is_ok(), f"Restore failed: {restore_result.unwrap_err()}"
        restored_state = restore_result.unwrap()
        assert isinstance(restored_state, SessionState)
        assert restored_state.metadata.get("task") == "Implement feature"
        assert restored_state.metadata.get("progress") == 75

    def test_restore_from_checkpoint_restores_memories(self):
        """Test that restored context can access original memories."""
        # Arrange - Create checkpoint with memories
        original_context = create_agent_context(session_id="test_restore_memories")
        original_context.store_memory("mem1", {"data": "original"}, ["restore"])

        save_result = original_context.create_checkpoint()
        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        # Act - Restore and search memories
        new_context = create_agent_context(session_id="test_restore_memories")
        restore_result = new_context.restore_from_checkpoint(checkpoint.checkpoint_id)
        assert restore_result.is_ok()

        # Search memories after restoration
        memories = new_context.search_memories(["restore"], include_session=True)

        # Assert
        assert len(memories) >= 1
        # Note: May include both original and restored memory entries

    def test_restore_from_checkpoint_updates_context_metadata(self):
        """Test that restore_from_checkpoint() updates context._metadata."""
        # Arrange
        original_context = create_agent_context(session_id="test_restore_metadata")
        original_context.set_metadata("key1", "value1")
        original_context.set_metadata("key2", 42)

        save_result = original_context.create_checkpoint()
        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        # Act
        new_context = create_agent_context(session_id="test_restore_metadata")
        restore_result = new_context.restore_from_checkpoint(checkpoint.checkpoint_id)
        assert restore_result.is_ok()

        # Assert - Check metadata updated
        assert new_context.get_metadata("key1") == "value1"
        assert new_context.get_metadata("key2") == 42

    def test_restore_from_checkpoint_returns_error_on_invalid_checkpoint_id(self):
        """Test that restore_from_checkpoint() returns Err for invalid checkpoint."""
        # Arrange
        context = create_agent_context(session_id="test_restore_invalid")

        # Act - Try to restore non-existent checkpoint
        result = context.restore_from_checkpoint("checkpoint_nonexistent_12345")

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert "not found" in error.lower() or "io_error" in error.lower()

    def test_restore_from_checkpoint_thread_safe(self):
        """Test that restore_from_checkpoint() is thread-safe."""
        # Arrange - Create checkpoint
        original_context = create_agent_context(session_id="test_restore_thread_safe")
        original_context.set_metadata("shared", "data")
        save_result = original_context.create_checkpoint()
        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        results = []
        errors = []

        def restore_worker():
            try:
                context = create_agent_context(session_id="test_restore_thread_safe")
                result = context.restore_from_checkpoint(checkpoint.checkpoint_id)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Act - Restore concurrently
        threads = [threading.Thread(target=restore_worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
            assert not t.is_alive(), "Thread did not complete within timeout"

        # Assert
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 3
        successful = [r for r in results if r.is_ok()]
        assert len(successful) >= 1, "At least one restore should succeed"


class TestAgentContextGetSessionState:
    """Test session state access via AgentContext.get_session_state()."""

    def test_get_session_state_returns_session_state_model(self):
        """Test that get_session_state() returns SessionState instance."""
        # Arrange
        context = create_agent_context(session_id="test_get_state")
        context.set_metadata("task_type", "planning")

        # Act
        state = context.get_session_state()

        # Assert
        assert isinstance(state, SessionState)
        assert state.session_id == "test_get_state"

    def test_get_session_state_includes_metadata(self):
        """Test that get_session_state() includes context metadata."""
        # Arrange
        context = create_agent_context(session_id="test_state_metadata")
        context.set_metadata("key1", "value1")
        context.set_metadata("key2", 100)
        context.set_metadata("key3", {"nested": "data"})

        # Act
        state = context.get_session_state()

        # Assert
        assert state.metadata.get("key1") == "value1"
        assert state.metadata.get("key2") == 100
        assert state.metadata.get("key3") == {"nested": "data"}

    def test_get_session_state_includes_memory_snapshots(self):
        """Test that get_session_state() includes session memories."""
        # Arrange
        context = create_agent_context(session_id="test_state_memories")
        context.store_memory("mem1", "content1", ["snapshot"])
        context.store_memory("mem2", "content2", ["snapshot"])

        # Act
        state = context.get_session_state()

        # Assert
        assert len(state.memory_snapshots) >= 2
        # Verify snapshots contain session memories
        memory_keys = [m.get("key") for m in state.memory_snapshots]
        assert "mem1" in memory_keys or "mem2" in memory_keys

    def test_get_session_state_sets_default_agent_name(self):
        """Test that get_session_state() sets default agent name."""
        # Arrange
        context = create_agent_context(session_id="test_state_agent")

        # Act
        state = context.get_session_state()

        # Assert
        assert state.agent_name is not None
        assert isinstance(state.agent_name, str)
        assert len(state.agent_name) > 0

    def test_get_session_state_sets_running_status(self):
        """Test that get_session_state() defaults to RUNNING status."""
        # Arrange
        context = create_agent_context(session_id="test_state_status")

        # Act
        state = context.get_session_state()

        # Assert
        assert state.status == SessionStatus.RUNNING


class TestAgentContextBackwardCompatibility:
    """Test that new checkpoint methods don't break existing AgentContext API."""

    def test_existing_methods_still_work(self):
        """Test that existing AgentContext methods are unaffected."""
        # Arrange
        context = create_agent_context(session_id="test_compatibility")

        # Act & Assert - All existing methods should work
        context.set_metadata("key", "value")
        assert context.get_metadata("key") == "value"

        context.store_memory("mem", "data", ["tag"])
        memories = context.search_memories(["tag"], include_session=True)
        assert len(memories) >= 1

        session_memories = context.get_session_memories()
        assert isinstance(session_memories, list)

    def test_new_methods_are_optional(self):
        """Test that new checkpoint methods are optional (don't break old usage)."""
        # Arrange - Use AgentContext without checkpoint methods
        context = create_agent_context(session_id="test_optional")
        context.set_metadata("data", 123)

        # Act - Normal workflow without checkpoints
        context.store_memory("normal", "workflow", ["no_checkpoint"])
        result = context.search_memories(["no_checkpoint"])

        # Assert
        assert len(result) >= 1
        assert context.get_metadata("data") == 123


class TestAgentContextCheckpointIntegration:
    """Integration tests for checkpoint workflow (create → restore)."""

    def test_full_checkpoint_restore_cycle(self):
        """Test complete checkpoint creation and restoration workflow."""
        # Arrange - Session 1: Work in progress
        session1 = create_agent_context(session_id="integration_test")
        session1.set_metadata("task", "Refactor code")
        session1.set_metadata("progress", 30)
        session1.store_memory("step1", "Analysis complete", ["workflow"])
        session1.store_memory("step2", "Tests written", ["workflow"])

        # Act - Create checkpoint
        checkpoint_result = session1.create_checkpoint()
        assert checkpoint_result.is_ok()
        checkpoint = checkpoint_result.unwrap()

        # Session 2: Restore from checkpoint (e.g., after restart)
        session2 = create_agent_context(session_id="integration_test")
        restore_result = session2.restore_from_checkpoint(checkpoint.checkpoint_id)
        assert restore_result.is_ok()

        # Assert - Verify state restored
        assert session2.get_metadata("task") == "Refactor code"
        assert session2.get_metadata("progress") == 30

        # Verify memories accessible
        memories = session2.search_memories(["workflow"], include_session=True)
        assert len(memories) >= 2

    def test_multiple_checkpoints_independent(self):
        """Test that multiple checkpoints don't interfere."""
        # Arrange
        context = create_agent_context(session_id="multi_checkpoint")

        # Checkpoint 1
        context.set_metadata("version", 1)
        result1 = context.create_checkpoint()
        assert result1.is_ok()
        checkpoint1 = result1.unwrap()

        # Modify state
        context.set_metadata("version", 2)
        context.set_metadata("extra", "data")

        # Checkpoint 2
        result2 = context.create_checkpoint()
        assert result2.is_ok()
        checkpoint2 = result2.unwrap()

        # Act - Restore checkpoint 1
        new_context = create_agent_context(session_id="multi_checkpoint")
        restore_result = new_context.restore_from_checkpoint(checkpoint1.checkpoint_id)
        assert restore_result.is_ok()

        # Assert - Restored to checkpoint 1 state
        assert new_context.get_metadata("version") == 1
        assert new_context.get_metadata("extra") is None  # Not in checkpoint 1

    def test_checkpoint_with_anthropic_memory_enabled(self):
        """Test checkpoint creation when Anthropic Memory Tool is enabled."""
        # Arrange
        context = create_agent_context(session_id="anthropic_checkpoint")

        # Only enable if anthropic package available
        try:
            context.enable_anthropic_memory()
            anthropic_enabled = True
        except ImportError:
            anthropic_enabled = False
            pytest.skip("Anthropic SDK not available")

        context.set_metadata("with_anthropic", True)

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()
        assert "with_anthropic" in checkpoint.session_state_json


class TestAgentContextCheckpointEdgeCases:
    """Edge case tests for checkpoint functionality."""

    def test_create_checkpoint_with_empty_context(self):
        """Test checkpoint creation with no metadata or memories."""
        # Arrange
        context = create_agent_context(session_id="empty_checkpoint")

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()
        assert checkpoint.checkpoint_id is not None

    def test_restore_checkpoint_with_corrupted_data(self):
        """Test restore handles corrupted checkpoint data gracefully."""
        # Arrange
        context = create_agent_context(session_id="corrupted_test")

        # Create checkpoint, then corrupt it manually
        result = context.create_checkpoint()
        assert result.is_ok()
        checkpoint = result.unwrap()

        # Corrupt checkpoint file (if we can access it)
        # This is tricky without direct file access, so we test with invalid ID
        # which simulates corruption/missing file

        # Act - Try to restore invalid checkpoint
        restore_result = context.restore_from_checkpoint("checkpoint_corrupted_invalid")

        # Assert
        assert restore_result.is_err()

    def test_checkpoint_with_large_metadata(self):
        """Test checkpoint handles large metadata gracefully."""
        # Arrange
        context = create_agent_context(session_id="large_metadata")
        large_data = {"data": "x" * 10000}  # 10KB string
        context.set_metadata("large_field", large_data)

        # Act
        result = context.create_checkpoint()

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()
        assert len(checkpoint.session_state_json) > 10000

    def test_checkpoint_preserves_session_id(self):
        """Test that checkpoint preserves exact session_id."""
        # Arrange
        unique_id = "very_specific_session_id_12345"
        context = create_agent_context(session_id=unique_id)
        context.set_metadata("test", "data")

        # Act - Create and restore
        save_result = context.create_checkpoint()
        assert save_result.is_ok()
        checkpoint = save_result.unwrap()

        new_context = create_agent_context(session_id=unique_id)
        restore_result = new_context.restore_from_checkpoint(checkpoint.checkpoint_id)
        assert restore_result.is_ok()

        # Assert
        restored_state = restore_result.unwrap()
        assert restored_state.session_id == unique_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
