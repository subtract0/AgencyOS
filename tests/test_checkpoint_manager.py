"""
Tests for CheckpointManager - Auto-checkpoint and resume system.

Constitutional Compliance:
- Article I: Complete context (test all checkpoint scenarios)
- Article II: TDD mandatory - tests written BEFORE implementation
- Article II: 100% test coverage required
- Article IV: Test telemetry logging and learning
- Article V: Tests map to spec requirements (specs/checkpoint_manager_spec.md)

Test Coverage:
- CheckpointManager initialization and configuration
- Auto-checkpoint triggers (interval, task, interrupt, phase)
- Resume logic with fallback on corruption
- Retention policy and cleanup
- Integration with AgentContext
- Error recovery strategies
- Thread safety and signal handling
- Performance benchmarks (<5s resume, <1s save)
"""

import hashlib
import json
import signal
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.agent_context import create_agent_context
from shared.checkpoint_manager import CheckpointConfig, CheckpointManager
from shared.models.session import SessionState, SessionStatus
from shared.session_checkpoint import load_checkpoint, save_checkpoint


class TestCheckpointManagerInit:
    """Test CheckpointManager initialization and configuration."""

    def test_checkpoint_manager_default_config(self):
        """Test CheckpointManager with default configuration."""
        # Arrange
        config = CheckpointConfig()

        # Act
        manager = CheckpointManager(config)

        # Assert
        assert manager.config.auto_checkpoint_enabled is True
        assert manager.config.checkpoint_interval_tasks == 5
        assert manager.config.checkpoint_interval_minutes == 30
        assert manager.config.checkpoint_on_interrupt is True
        assert manager.config.checkpoint_retention_count == 5
        assert manager.config.checkpoint_retention_days == 7
        assert manager._checkpoint_count == 0
        assert manager._checkpoint_failures == 0
        assert manager._resume_count == 0

    def test_checkpoint_manager_custom_config(self):
        """Test CheckpointManager with custom configuration."""
        # Arrange
        config = CheckpointConfig(
            checkpoint_interval_minutes=15,
            checkpoint_interval_tasks=3,
            checkpoint_retention_count=10,
            checkpoint_on_interrupt=False,
        )

        # Act
        manager = CheckpointManager(config)

        # Assert
        assert manager.config.checkpoint_interval_minutes == 15
        assert manager.config.checkpoint_interval_tasks == 3
        assert manager.config.checkpoint_retention_count == 10
        assert manager.config.checkpoint_on_interrupt is False

    def test_checkpoint_config_validation(self):
        """Test CheckpointConfig validates field constraints."""
        # Test valid config
        config = CheckpointConfig(
            checkpoint_interval_tasks=1,
            checkpoint_retention_count=-1,  # Keep all (debug mode)
        )
        assert config.checkpoint_interval_tasks == 1
        assert config.checkpoint_retention_count == -1

        # Test invalid values caught by Pydantic
        with pytest.raises(ValueError):
            CheckpointConfig(checkpoint_interval_tasks=0)  # Must be >= 1


class TestCheckpointTrigger:
    """Test manual checkpoint trigger functionality."""

    def test_trigger_checkpoint_success(self, tmp_path):
        """Test manual checkpoint trigger creates valid checkpoint."""
        # Arrange
        context = create_agent_context(session_id="test_trigger")
        context.set_metadata("task", "Create plan")
        context.store_memory("mem1", {"data": "test"}, ["test"])

        config = CheckpointConfig(base_path=str(tmp_path))
        manager = CheckpointManager(config)

        # Act
        result = manager.trigger_checkpoint(context, reason="manual")

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()
        assert checkpoint.checkpoint_id.startswith("checkpoint_")
        assert manager._checkpoint_count == 1

        # Verify checkpoint file exists
        checkpoint_file = (
            tmp_path
            / "sessions"
            / context.session_id
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )
        assert checkpoint_file.exists()

    def test_trigger_checkpoint_with_telemetry(self, tmp_path, caplog):
        """Test checkpoint trigger logs telemetry (Article IV)."""
        # Arrange
        context = create_agent_context(session_id="test_telemetry")
        context.set_metadata("progress", 50)

        config = CheckpointConfig(base_path=str(tmp_path))
        manager = CheckpointManager(config)

        # Act
        with caplog.at_level("INFO"):
            result = manager.trigger_checkpoint(context, reason="test_reason")

        # Assert
        assert result.is_ok()
        checkpoint = result.unwrap()

        # Verify telemetry logging
        assert any("Checkpoint triggered" in record.message for record in caplog.records)
        assert any(
            f"checkpoint_id={checkpoint.checkpoint_id}" in record.message
            for record in caplog.records
        )
        assert any("reason=test_reason" in record.message for record in caplog.records)

    def test_trigger_checkpoint_thread_safe(self, tmp_path):
        """Test checkpoint trigger is thread-safe."""
        # Arrange
        context = create_agent_context(session_id="test_thread_safe")
        config = CheckpointConfig(base_path=str(tmp_path))
        manager = CheckpointManager(config)

        results = []

        def trigger_worker():
            result = manager.trigger_checkpoint(context, reason="concurrent")
            results.append(result)

        # Act - trigger 10 concurrent checkpoints
        threads = [threading.Thread(target=trigger_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - all succeeded, no corruption
        assert all(r.is_ok() for r in results)
        assert manager._checkpoint_count == 10


class TestAutoCheckpointStart:
    """Test auto-checkpoint system startup."""

    def test_start_auto_checkpoint_success(self, tmp_path):
        """Test starting auto-checkpoint system."""
        # Arrange
        context = create_agent_context(session_id="test_start")
        config = CheckpointConfig(base_path=str(tmp_path), checkpoint_interval_minutes=60)
        manager = CheckpointManager(config)

        # Act
        result = manager.start_auto_checkpoint(context, task_id="test_task")

        # Assert
        assert result.is_ok()
        assert manager._context is context
        assert manager._task_count == 0

        # Cleanup
        manager.stop_auto_checkpoint()

    def test_start_auto_checkpoint_disabled(self, tmp_path):
        """Test start_auto_checkpoint when disabled."""
        # Arrange
        context = create_agent_context(session_id="test_disabled")
        config = CheckpointConfig(auto_checkpoint_enabled=False, base_path=str(tmp_path))
        manager = CheckpointManager(config)

        # Act
        result = manager.start_auto_checkpoint(context, task_id="test_task")

        # Assert
        assert result.is_ok()
        assert manager._context is None  # Not initialized when disabled

    def test_stop_auto_checkpoint(self, tmp_path):
        """Test stopping auto-checkpoint system."""
        # Arrange
        context = create_agent_context(session_id="test_stop")
        config = CheckpointConfig(base_path=str(tmp_path), checkpoint_interval_minutes=60)
        manager = CheckpointManager(config)

        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act
        result = manager.stop_auto_checkpoint()

        # Assert
        assert result.is_ok()
        assert manager._context is None
        assert manager._timer_thread is None or not manager._timer_thread.is_alive()


class TestTaskCompletionCheckpoint:
    """Test task completion checkpoint trigger."""

    def test_on_task_complete_triggers_after_interval(self, tmp_path):
        """Test on_task_complete triggers checkpoint every N tasks."""
        # Arrange
        context = create_agent_context(session_id="test_task_complete")
        config = CheckpointConfig(checkpoint_interval_tasks=3, base_path=str(tmp_path))
        manager = CheckpointManager(config)

        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - complete 6 tasks
        for i in range(6):
            context.set_metadata(f"task_{i}", "completed")
            result = manager.on_task_complete(context)
            assert result.is_ok()

        # Assert - should have 2 checkpoints (tasks 2 and 5, 0-indexed)
        assert manager._checkpoint_count == 2

        # Cleanup
        manager.stop_auto_checkpoint()

    def test_on_task_complete_no_checkpoint_before_interval(self, tmp_path):
        """Test on_task_complete does not trigger before interval."""
        # Arrange
        context = create_agent_context(session_id="test_no_trigger")
        config = CheckpointConfig(checkpoint_interval_tasks=5, base_path=str(tmp_path))
        manager = CheckpointManager(config)

        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - complete 4 tasks (less than interval)
        for i in range(4):
            result = manager.on_task_complete(context)
            assert result.is_ok()

        # Assert - no checkpoints created
        assert manager._checkpoint_count == 0

        # Cleanup
        manager.stop_auto_checkpoint()


class TestResumeFromCheckpoint:
    """Test checkpoint resume logic with integrity validation."""

    def test_resume_from_checkpoint_success(self, tmp_path):
        """Test resume from valid checkpoint restores full state."""
        # Arrange - Create checkpoint
        context = create_agent_context(session_id="test_resume")
        context.set_metadata("progress", 60)
        context.set_metadata("task", "ADR-024")

        for i in range(10):
            context.store_memory(f"memory_{i}", {"data": f"content_{i}"}, ["test"])

        checkpoint_result = context.create_checkpoint(base_path=str(tmp_path))
        assert checkpoint_result.is_ok()
        checkpoint = checkpoint_result.unwrap()

        # Act - Resume from checkpoint
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        resume_result = manager.resume_from_checkpoint(context.session_id, checkpoint.checkpoint_id)

        # Assert - Full state restored
        assert resume_result.is_ok()
        restored_context = resume_result.unwrap()

        assert restored_context.session_id == context.session_id
        assert restored_context.get_metadata("progress") == 60
        assert restored_context.get_metadata("task") == "ADR-024"

        restored_memories = restored_context.get_session_memories()
        assert len(restored_memories) == 10

        # Verify telemetry
        assert manager._resume_count == 1

    def test_resume_from_checkpoint_latest_auto_detect(self, tmp_path):
        """Test resume automatically uses latest checkpoint when ID is None."""
        # Arrange - Create multiple checkpoints
        context = create_agent_context(session_id="test_auto_detect")

        for i in range(3):
            context.set_metadata("version", i)
            context.create_checkpoint(base_path=str(tmp_path))
            time.sleep(0.01)  # Ensure different timestamps

        # Act - Resume without specifying checkpoint_id
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        resume_result = manager.resume_from_checkpoint(context.session_id, checkpoint_id=None)

        # Assert - Latest checkpoint restored (version 2)
        assert resume_result.is_ok()
        restored_context = resume_result.unwrap()
        assert restored_context.get_metadata("version") == 2

    def test_resume_fallback_on_corruption(self, tmp_path):
        """Test resume falls back to previous checkpoint on corruption."""
        # Arrange - Create 3 checkpoints
        context = create_agent_context(session_id="test_fallback")

        for i in range(3):
            context.set_metadata("version", i)
            context.create_checkpoint(base_path=str(tmp_path))
            time.sleep(0.01)

        # Corrupt latest checkpoint
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        checkpoint_files = sorted(
            checkpoints_dir.glob("checkpoint_*.json"), key=lambda p: p.stat().st_mtime
        )
        latest_checkpoint = checkpoint_files[-1]

        # Corrupt file by modifying bytes
        with open(latest_checkpoint, "rb") as f:
            data = bytearray(f.read())

        data[-10] = (data[-10] + 1) % 256  # Corrupt last bytes

        with open(latest_checkpoint, "wb") as f:
            f.write(data)

        # Act - Resume should fallback to 2nd checkpoint
        manager = CheckpointManager(
            CheckpointConfig(checkpoint_max_retries=3, base_path=str(tmp_path))
        )
        resume_result = manager.resume_from_checkpoint(context.session_id)

        # Assert - 2nd checkpoint restored (version 1)
        assert resume_result.is_ok()
        restored_context = resume_result.unwrap()
        assert restored_context.get_metadata("version") == 1

    def test_resume_fails_when_all_corrupted(self, tmp_path):
        """Test resume fails when all checkpoints are corrupted."""
        # Arrange - Create checkpoint
        context = create_agent_context(session_id="test_all_corrupted")
        context.set_metadata("data", "test")
        context.create_checkpoint(base_path=str(tmp_path))

        # Corrupt the checkpoint
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        checkpoint_file = list(checkpoints_dir.glob("checkpoint_*.json"))[0]

        with open(checkpoint_file, "rb") as f:
            data = bytearray(f.read())

        data[-10] = (data[-10] + 1) % 256

        with open(checkpoint_file, "wb") as f:
            f.write(data)

        # Act - Resume should fail
        manager = CheckpointManager(
            CheckpointConfig(checkpoint_max_retries=3, base_path=str(tmp_path))
        )
        resume_result = manager.resume_from_checkpoint(context.session_id)

        # Assert - All checkpoints corrupted error
        assert resume_result.is_err()
        error = resume_result.unwrap_err()
        assert "all_checkpoints_corrupted" in error

    def test_resume_performance_under_5_seconds(self, tmp_path):
        """Test resume completes in <5 seconds (performance requirement)."""
        # Arrange - Create checkpoint with realistic data (50 memories)
        context = create_agent_context(session_id="test_performance")
        context.set_metadata("task", "ADR-024: Multi-day specification")
        context.set_metadata("progress_percent", 60)

        for i in range(50):
            context.store_memory(
                f"adr_research_{i}",
                {"finding": f"Research point {i}", "data": "x" * 100},
                ["adr", "research"],
            )

        checkpoint_result = context.create_checkpoint(base_path=str(tmp_path))
        assert checkpoint_result.is_ok()
        checkpoint = checkpoint_result.unwrap()

        # Act - Measure resume time
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        start_time = time.time()
        resume_result = manager.resume_from_checkpoint(context.session_id, checkpoint.checkpoint_id)
        resume_time = time.time() - start_time

        # Assert - Performance target met
        assert resume_result.is_ok()
        assert resume_time < 5.0, f"Resume took {resume_time:.2f}s (target: <5s)"

        # Verify state accuracy
        restored_context = resume_result.unwrap()
        assert restored_context.get_metadata("progress_percent") == 60
        assert len(restored_context.get_session_memories()) == 50


class TestDetectPausedSession:
    """Test paused session detection."""

    def test_detect_paused_session_with_checkpoints(self, tmp_path):
        """Test detect_paused_session finds latest checkpoint."""
        # Arrange
        context = create_agent_context(session_id="test_detect")
        context.set_metadata("task", "Resume test")
        context.create_checkpoint(base_path=str(tmp_path))

        # Act
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        result = manager.detect_paused_session(context.session_id)

        # Assert
        assert result.is_ok()
        checkpoint_meta = result.unwrap()
        assert checkpoint_meta is not None
        assert checkpoint_meta.checkpoint_id.startswith("checkpoint_")

    def test_detect_paused_session_no_checkpoints(self, tmp_path):
        """Test detect_paused_session returns None when no checkpoints."""
        # Arrange - No checkpoints created
        session_id = "test_no_checkpoints"

        # Act
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        result = manager.detect_paused_session(session_id)

        # Assert
        assert result.is_ok()
        checkpoint_meta = result.unwrap()
        assert checkpoint_meta is None


class TestRetentionPolicy:
    """Test checkpoint retention policy and cleanup."""

    def test_cleanup_keeps_last_n_checkpoints(self, tmp_path):
        """Test cleanup retains last N checkpoints."""
        # Arrange - Create 10 checkpoints
        context = create_agent_context(session_id="test_cleanup")

        for i in range(10):
            context.set_metadata("checkpoint", i)
            context.create_checkpoint(base_path=str(tmp_path))
            time.sleep(0.01)

        # Act - Cleanup (keep last 5)
        manager = CheckpointManager(
            CheckpointConfig(checkpoint_retention_count=5, base_path=str(tmp_path))
        )
        result = manager.cleanup_old_checkpoints(context.session_id)

        # Assert
        assert result.is_ok()
        deleted_count = result.unwrap()
        assert deleted_count == 5

        # Verify only 5 checkpoints remain
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        remaining = list(checkpoints_dir.glob("checkpoint_*.json"))
        assert len(remaining) == 5

    def test_cleanup_deletes_old_checkpoints(self, tmp_path):
        """Test cleanup deletes checkpoints older than retention days."""
        # Arrange - Create checkpoint and manually set old mtime
        context = create_agent_context(session_id="test_old_cleanup")
        checkpoint_result = context.create_checkpoint(base_path=str(tmp_path))
        assert checkpoint_result.is_ok()
        checkpoint = checkpoint_result.unwrap()

        # Set mtime to 10 days ago
        checkpoint_file = (
            tmp_path
            / "sessions"
            / context.session_id
            / "checkpoints"
            / f"{checkpoint.checkpoint_id}.json"
        )
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        checkpoint_file.touch()
        import os

        os.utime(checkpoint_file, (old_time, old_time))

        # Act - Cleanup (retention 7 days)
        manager = CheckpointManager(
            CheckpointConfig(checkpoint_retention_days=7, base_path=str(tmp_path))
        )
        result = manager.cleanup_old_checkpoints(context.session_id)

        # Assert - Old checkpoint deleted
        assert result.is_ok()
        deleted_count = result.unwrap()
        assert deleted_count == 1
        assert not checkpoint_file.exists()

    def test_cleanup_keep_all_mode(self, tmp_path):
        """Test cleanup with retention_count=-1 keeps all checkpoints."""
        # Arrange - Create 10 checkpoints
        context = create_agent_context(session_id="test_keep_all")

        for i in range(10):
            context.set_metadata("checkpoint", i)
            context.create_checkpoint(base_path=str(tmp_path))
            time.sleep(0.01)

        # Act - Cleanup with keep all mode
        manager = CheckpointManager(
            CheckpointConfig(checkpoint_retention_count=-1, base_path=str(tmp_path))
        )
        result = manager.cleanup_old_checkpoints(context.session_id)

        # Assert - No checkpoints deleted
        assert result.is_ok()
        deleted_count = result.unwrap()
        assert deleted_count == 0

        # Verify all 10 checkpoints remain
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        remaining = list(checkpoints_dir.glob("checkpoint_*.json"))
        assert len(remaining) == 10


class TestIntervalTimer:
    """Test interval-based auto-checkpoint trigger."""

    @pytest.mark.skip(reason="Slow test (61s), enable for full validation")
    def test_interval_timer_triggers_checkpoint(self, tmp_path):
        """Test interval timer creates checkpoint after timeout."""
        # Arrange
        context = create_agent_context(session_id="test_interval")
        config = CheckpointConfig(
            checkpoint_interval_minutes=1,  # 1 minute for test
            base_path=str(tmp_path),
        )

        manager = CheckpointManager(config)
        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - Wait for interval (61 seconds)
        time.sleep(61)

        # Assert - At least 1 checkpoint created
        assert manager._checkpoint_count >= 1

        # Cleanup
        manager.stop_auto_checkpoint()

    @pytest.mark.skip(reason="Slow test, enable for full validation")
    def test_interval_timer_multiple_triggers(self, tmp_path):
        """Test interval timer creates multiple checkpoints."""
        # Arrange
        context = create_agent_context(session_id="test_multi_interval")
        config = CheckpointConfig(
            checkpoint_interval_minutes=1,  # 1 minute
            base_path=str(tmp_path),
        )

        manager = CheckpointManager(config)
        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - Wait for 2 intervals (125 seconds)
        time.sleep(125)

        # Assert - At least 2 checkpoints created
        assert manager._checkpoint_count >= 2

        # Cleanup
        manager.stop_auto_checkpoint()

    def test_interval_timer_stops_cleanly(self, tmp_path):
        """Test interval timer thread stops cleanly."""
        # Arrange
        context = create_agent_context(session_id="test_timer_stop")
        config = CheckpointConfig(checkpoint_interval_minutes=60, base_path=str(tmp_path))

        manager = CheckpointManager(config)
        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - Stop after 1 second
        time.sleep(1)
        result = manager.stop_auto_checkpoint()

        # Assert - Thread stopped
        assert result.is_ok()
        assert manager._timer_thread is None or not manager._timer_thread.is_alive()


class TestInterruptCheckpoint:
    """Test interrupt signal handler checkpoint."""

    @pytest.mark.skip(reason="Signal handling test requires careful isolation")
    def test_interrupt_checkpoint_on_sigint(self, tmp_path):
        """Test interrupt signal triggers emergency checkpoint."""
        # Arrange
        context = create_agent_context(session_id="test_interrupt")
        config = CheckpointConfig(checkpoint_on_interrupt=True, base_path=str(tmp_path))

        manager = CheckpointManager(config)
        manager.start_auto_checkpoint(context, task_id="test_task")

        # Act - Simulate interrupt signal
        import os
        import signal

        os.kill(os.getpid(), signal.SIGINT)

        # Wait for handler to execute
        time.sleep(0.5)

        # Assert - Emergency checkpoint created
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        checkpoints = list(checkpoints_dir.glob("checkpoint_*.json"))

        assert len(checkpoints) >= 1

        # Cleanup
        manager.stop_auto_checkpoint()

    def test_interrupt_handler_installation(self, tmp_path):
        """Test interrupt handler is installed correctly."""
        # Arrange
        context = create_agent_context(session_id="test_handler_install")
        config = CheckpointConfig(checkpoint_on_interrupt=True, base_path=str(tmp_path))

        manager = CheckpointManager(config)

        # Get original handler
        original_handler = signal.getsignal(signal.SIGINT)

        # Act - Start auto-checkpoint
        manager.start_auto_checkpoint(context, task_id="test_task")

        # Assert - Handler changed
        current_handler = signal.getsignal(signal.SIGINT)
        assert current_handler != original_handler

        # Cleanup - Restore original handler
        manager.stop_auto_checkpoint()

        # Verify handler restored
        restored_handler = signal.getsignal(signal.SIGINT)
        assert restored_handler == original_handler


class TestAgentContextIntegration:
    """Test CheckpointManager integration with AgentContext."""

    def test_agent_context_enable_auto_checkpoint(self, tmp_path):
        """Test AgentContext.enable_auto_checkpoint() creates CheckpointManager."""
        # Arrange
        context = create_agent_context(session_id="test_enable")
        config = CheckpointConfig(base_path=str(tmp_path), checkpoint_interval_minutes=60)

        # Act
        result = context.enable_auto_checkpoint(config)

        # Assert
        assert result.is_ok()
        manager = context.get_checkpoint_manager()
        assert manager is not None
        assert isinstance(manager, CheckpointManager)

        # Cleanup
        context.disable_auto_checkpoint()

    def test_agent_context_disable_auto_checkpoint(self, tmp_path):
        """Test AgentContext.disable_auto_checkpoint() cleans up resources."""
        # Arrange
        context = create_agent_context(session_id="test_disable")
        config = CheckpointConfig(base_path=str(tmp_path), checkpoint_interval_minutes=60)

        context.enable_auto_checkpoint(config)

        # Act
        result = context.disable_auto_checkpoint()

        # Assert
        assert result.is_ok()
        manager = context.get_checkpoint_manager()
        assert manager is None

    def test_agent_context_get_checkpoint_manager(self, tmp_path):
        """Test AgentContext.get_checkpoint_manager() returns manager instance."""
        # Arrange
        context = create_agent_context(session_id="test_get_manager")
        config = CheckpointConfig(base_path=str(tmp_path))

        # Act - Before enabling
        manager_before = context.get_checkpoint_manager()

        # Enable auto-checkpoint
        context.enable_auto_checkpoint(config)
        manager_after = context.get_checkpoint_manager()

        # Assert
        assert manager_before is None
        assert manager_after is not None
        assert isinstance(manager_after, CheckpointManager)

        # Cleanup
        context.disable_auto_checkpoint()


class TestErrorRecovery:
    """Test error recovery strategies."""

    def test_checkpoint_failure_increments_counter(self, tmp_path):
        """Test failed checkpoint increments failure counter."""
        # Arrange - Make directory read-only to force failure
        context = create_agent_context(session_id="test_failure")
        config = CheckpointConfig(base_path=str(tmp_path))
        manager = CheckpointManager(config)

        # Create checkpoint directory and make it read-only
        checkpoints_dir = tmp_path / "sessions" / context.session_id / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        checkpoints_dir.chmod(0o444)  # Read-only

        # Act
        result = manager.trigger_checkpoint(context, reason="test_failure")

        # Assert - Checkpoint failed
        assert result.is_err()
        assert manager._checkpoint_failures >= 1

        # Cleanup - Restore permissions
        checkpoints_dir.chmod(0o755)

    def test_missing_checkpoint_file_error(self, tmp_path):
        """Test resume handles missing checkpoint file gracefully."""
        # Arrange
        session_id = "test_missing"
        checkpoint_id = "checkpoint_nonexistent"

        # Act
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        result = manager.resume_from_checkpoint(session_id, checkpoint_id)

        # Assert - Error returned
        assert result.is_err()
        error = result.unwrap_err()
        assert "io_error" in error or "all_checkpoints_corrupted" in error


class TestCheckpointPerformance:
    """Test checkpoint performance benchmarks."""

    def test_checkpoint_save_under_1_second(self, tmp_path):
        """Test checkpoint save completes in <1 second."""
        # Arrange - Realistic state (50 memories, 10KB metadata)
        context = create_agent_context(session_id="test_save_perf")

        for i in range(50):
            context.store_memory(f"memory_{i}", {"data": "x" * 100}, ["test"])

        context.set_metadata("large_field", {"data": "x" * 5000})

        # Act - Measure save time
        start = time.time()
        result = context.create_checkpoint(base_path=str(tmp_path))
        save_time = time.time() - start

        # Assert
        assert result.is_ok()
        assert save_time < 1.0, f"Checkpoint save took {save_time:.3f}s (target: <1s)"

    def test_checkpoint_load_under_5_seconds(self, tmp_path):
        """Test checkpoint load completes in <5 seconds."""
        # Arrange - Create checkpoint with 100 memories
        context = create_agent_context(session_id="test_load_perf")

        for i in range(100):
            context.store_memory(f"memory_{i}", {"data": "x" * 200}, ["test"])

        checkpoint_result = context.create_checkpoint(base_path=str(tmp_path))
        assert checkpoint_result.is_ok()
        checkpoint = checkpoint_result.unwrap()

        # Act - Measure load time
        manager = CheckpointManager(CheckpointConfig(base_path=str(tmp_path)))
        start = time.time()
        resume_result = manager.resume_from_checkpoint(context.session_id, checkpoint.checkpoint_id)
        load_time = time.time() - start

        # Assert
        assert resume_result.is_ok()
        assert load_time < 5.0, f"Checkpoint load took {load_time:.3f}s (target: <5s)"


class TestOrchestratorIntegration:
    """Test CheckpointManager integration with orchestrator workflows."""

    def test_orchestrator_workflow_simulation(self, tmp_path):
        """Test checkpoint integration with orchestrator task workflow."""
        # Arrange - Simulate orchestrator workflow
        context = create_agent_context(session_id="test_orchestrator")

        config = CheckpointConfig(
            checkpoint_interval_tasks=5,
            checkpoint_on_phase_complete=True,
            base_path=str(tmp_path),
        )

        context.enable_auto_checkpoint(config)
        manager = context.get_checkpoint_manager()

        # Act - Execute 10 tasks
        for task_id in range(10):
            context.set_metadata(f"task_{task_id}", "completed")
            manager.on_task_complete(context)

        # Assert - 2 checkpoints created (tasks 4 and 9, 0-indexed)
        assert manager._checkpoint_count == 2

        # Act - Phase completion checkpoint
        phase_result = manager.trigger_checkpoint(context, reason="phase_complete")

        # Assert - 3rd checkpoint created
        assert phase_result.is_ok()
        assert manager._checkpoint_count == 3

        # Cleanup
        context.disable_auto_checkpoint()

    def test_multi_day_adr_resume_simulation(self, tmp_path):
        """
        Simulate multi-day ADR development with checkpoint resume.

        Journey from spec: ChiefArchitect ADR-024 over weekend.
        """
        # Day 1: Friday 3pm - Start ADR-024
        context = create_agent_context(session_id="ADR_024")
        context.set_metadata("task", "ADR-024: Multi-day specification")
        context.set_metadata("progress_percent", 60)

        # Add 47 memory records (simulate ADR research)
        for i in range(47):
            context.store_memory(
                key=f"adr_research_{i}",
                content={"finding": f"Research point {i}"},
                tags=["adr", "research"],
            )

        # Enable auto-checkpoint
        config = CheckpointConfig(checkpoint_interval_minutes=30, base_path=str(tmp_path))
        context.enable_auto_checkpoint(config)

        # Create checkpoint
        checkpoint_manager = context.get_checkpoint_manager()
        checkpoint_result = checkpoint_manager.trigger_checkpoint(context, reason="manual_save")
        assert checkpoint_result.is_ok()

        # Simulate weekend pause
        context.disable_auto_checkpoint()
        original_session_id = context.session_id
        del context

        # Day 4: Monday 9am - Resume ADR-024
        manager = CheckpointManager(config)

        # Detect paused session
        paused_result = manager.detect_paused_session(original_session_id)
        assert paused_result.is_ok()
        assert paused_result.unwrap() is not None

        # Resume from checkpoint (<5 seconds target)
        start_time = time.time()
        resume_result = manager.resume_from_checkpoint(original_session_id)
        resume_time = time.time() - start_time

        # Assert - State restored
        assert resume_result.is_ok()
        restored_context = resume_result.unwrap()

        # Validate state restoration (100% accuracy)
        assert restored_context.get_metadata("task") == "ADR-024: Multi-day specification"
        assert restored_context.get_metadata("progress_percent") == 60

        restored_memories = restored_context.get_session_memories()
        assert len(restored_memories) == 47

        # Validate performance (<5 seconds)
        assert resume_time < 5.0, f"Resume took {resume_time:.2f}s (target: <5s)"


# Fixtures for temporary directories
@pytest.fixture
def tmp_path(tmpdir):
    """Create temporary directory for test checkpoints."""
    return Path(tmpdir)
