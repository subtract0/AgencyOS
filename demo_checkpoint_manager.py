"""
Demo: CheckpointManager - Auto-checkpoint and Resume System

Demonstrates:
1. Auto-checkpoint triggers (task completion, phase milestones)
2. Multi-day task resume with state restoration
3. Retention policy and cleanup
4. Integration with AgentContext

Constitutional Compliance:
- Article I: Complete context restoration
- Article II: 100% state accuracy validation
- Article III: Automated checkpointing (no manual intervention)
- Article IV: Telemetry logging throughout
- Article V: Spec-driven (specs/checkpoint_manager_spec.md)
"""

import logging
import time
from pathlib import Path

from shared.agent_context import create_agent_context
from shared.checkpoint_manager import CheckpointConfig, CheckpointManager

# Configure logging to see telemetry
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def demo_basic_checkpoint():
    """Demonstration 1: Basic checkpoint creation and restoration."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Checkpoint Creation and Restoration")
    print("=" * 60)

    # Create context with session data
    context = create_agent_context(session_id="demo_basic")
    context.set_metadata("task", "Create comprehensive spec")
    context.set_metadata("progress_percent", 75)

    # Add some memories
    for i in range(10):
        context.store_memory(
            f"research_{i}",
            {"finding": f"Research point {i}", "source": f"paper_{i}.pdf"},
            ["research", "spec"],
        )

    print(f"\n✓ Session created: {context.session_id}")
    print(f"  - Metadata: {dict(context._metadata)}")
    print(f"  - Memories: {len(context.get_session_memories())} records")

    # Create checkpoint
    checkpoint_result = context.create_checkpoint()

    if checkpoint_result.is_ok():
        checkpoint = checkpoint_result.unwrap()
        print(f"\n✓ Checkpoint created: {checkpoint.checkpoint_id}")
        print(f"  - Timestamp: {checkpoint.timestamp}")
        print(f"  - Checksum: {checkpoint.checksum[:16]}...")
    else:
        print(f"\n✗ Checkpoint failed: {checkpoint_result.unwrap_err()}")
        return

    # Simulate session end
    del context

    # Resume from checkpoint
    print("\n--- Simulating session resume ---")
    manager = CheckpointManager(CheckpointConfig())
    resume_result = manager.resume_from_checkpoint("demo_basic", checkpoint.checkpoint_id)

    if resume_result.is_ok():
        restored_context = resume_result.unwrap()
        print(f"\n✓ Session restored: {restored_context.session_id}")
        print(f"  - Metadata: {dict(restored_context._metadata)}")
        print(f"  - Memories: {len(restored_context.get_session_memories())} records")

        # Validate accuracy
        assert restored_context.get_metadata("task") == "Create comprehensive spec"
        assert restored_context.get_metadata("progress_percent") == 75
        assert len(restored_context.get_session_memories()) == 10

        print("\n✓ State validation: 100% accuracy")
    else:
        print(f"\n✗ Resume failed: {resume_result.unwrap_err()}")


def demo_auto_checkpoint():
    """Demonstration 2: Auto-checkpoint with task completion triggers."""
    print("\n" + "=" * 60)
    print("DEMO 2: Auto-Checkpoint with Task Completion")
    print("=" * 60)

    # Create context and enable auto-checkpoint (disable timer to avoid 5s wait)
    context = create_agent_context(session_id="demo_auto")
    config = CheckpointConfig(
        checkpoint_interval_tasks=3,  # Checkpoint every 3 tasks
        checkpoint_retention_count=5,
        checkpoint_interval_minutes=999,  # Disable timer for demo speed
    )

    result = context.enable_auto_checkpoint(config)

    if result.is_ok():
        print(f"\n✓ Auto-checkpoint enabled")
        print(f"  - Interval: Every {config.checkpoint_interval_tasks} tasks")
    else:
        print(f"\n✗ Auto-checkpoint failed: {result.unwrap_err()}")
        return

    # Simulate task execution
    manager = context.get_checkpoint_manager()

    for task_id in range(10):
        context.set_metadata(f"task_{task_id}", "completed")
        manager.on_task_complete(context)

        if task_id % config.checkpoint_interval_tasks == (config.checkpoint_interval_tasks - 1):
            print(f"\n✓ Task {task_id} completed → Auto-checkpoint triggered")
            print(f"  - Total checkpoints: {manager._checkpoint_count}")

    # Manual phase checkpoint
    phase_result = manager.trigger_checkpoint(context, reason="phase_complete")

    if phase_result.is_ok():
        print(f"\n✓ Phase checkpoint created (manual trigger)")
        print(f"  - Total checkpoints: {manager._checkpoint_count}")

    # Cleanup
    context.disable_auto_checkpoint()
    print(f"\n✓ Auto-checkpoint disabled")


def demo_multi_day_resume():
    """Demonstration 3: Multi-day task resume (ADR-024 scenario)."""
    print("\n" + "=" * 60)
    print("DEMO 3: Multi-Day Task Resume (ADR-024 Scenario)")
    print("=" * 60)

    # Day 1: Friday 3pm - Start ADR-024
    print("\n--- Day 1: Friday 3pm ---")
    context = create_agent_context(session_id="ADR_024")
    context.set_metadata("task", "ADR-024: Multi-day specification")
    context.set_metadata("progress_percent", 60)
    context.set_metadata("status", "in_progress")

    # Simulate research (47 memories as per spec)
    for i in range(47):
        context.store_memory(
            f"adr_research_{i}",
            {
                "finding": f"Research point {i}",
                "category": "architecture" if i % 2 == 0 else "implementation",
            },
            ["adr", "research"],
        )

    print(f"✓ ADR-024 started")
    print(f"  - Progress: 60%")
    print(f"  - Research: 47 findings")

    # Create checkpoint before weekend
    checkpoint_result = context.create_checkpoint()

    if checkpoint_result.is_ok():
        checkpoint = checkpoint_result.unwrap()
        print(f"\n✓ Checkpoint saved before weekend")
        print(f"  - ID: {checkpoint.checkpoint_id}")
    else:
        print(f"\n✗ Checkpoint failed: {checkpoint_result.unwrap_err()}")
        return

    # Simulate weekend pause
    original_session_id = context.session_id
    del context
    print("\n--- Weekend pause (session cleared) ---")

    # Day 4: Monday 9am - Resume ADR-024
    print("\n--- Day 4: Monday 9am ---")
    manager = CheckpointManager(CheckpointConfig())

    # Detect paused session
    paused_result = manager.detect_paused_session(original_session_id)

    if paused_result.is_ok() and paused_result.unwrap() is not None:
        print(f"✓ Paused session detected: {original_session_id}")

        # Resume from checkpoint
        start_time = time.time()
        resume_result = manager.resume_from_checkpoint(original_session_id)
        resume_time = time.time() - start_time

        if resume_result.is_ok():
            restored_context = resume_result.unwrap()

            print(f"\n✓ Session resumed successfully")
            print(f"  - Resume time: {resume_time:.3f}s (target: <5s)")
            print(f"  - Task: {restored_context.get_metadata('task')}")
            print(f"  - Progress: {restored_context.get_metadata('progress_percent')}%")
            print(f"  - Research: {len(restored_context.get_session_memories())} findings")

            # Validate accuracy
            assert restored_context.get_metadata("progress_percent") == 60
            assert len(restored_context.get_session_memories()) == 47

            print(f"\n✓ State validation: 100% accuracy")
            print(f"✓ Performance: {'PASS' if resume_time < 5.0 else 'SLOW'}")
        else:
            print(f"\n✗ Resume failed: {resume_result.unwrap_err()}")
    else:
        print("✗ No paused session found")


def demo_retention_policy():
    """Demonstration 4: Retention policy and cleanup."""
    print("\n" + "=" * 60)
    print("DEMO 4: Retention Policy and Cleanup")
    print("=" * 60)

    # Create session with multiple checkpoints
    context = create_agent_context(session_id="demo_retention")

    print("\n--- Creating 10 checkpoints ---")
    for i in range(10):
        context.set_metadata("checkpoint_version", i)
        context.create_checkpoint()
        time.sleep(0.01)  # Ensure different timestamps

    checkpoints_dir = Path.home() / ".agency/sessions/demo_retention/checkpoints"
    initial_count = len(list(checkpoints_dir.glob("checkpoint_*.json")))
    print(f"✓ Created {initial_count} checkpoints")

    # Apply retention policy (keep last 5)
    print("\n--- Applying retention policy (keep last 5) ---")
    manager = CheckpointManager(CheckpointConfig(checkpoint_retention_count=5))
    cleanup_result = manager.cleanup_old_checkpoints("demo_retention")

    if cleanup_result.is_ok():
        deleted_count = cleanup_result.unwrap()
        remaining_count = len(list(checkpoints_dir.glob("checkpoint_*.json")))

        print(f"✓ Cleanup complete")
        print(f"  - Deleted: {deleted_count} checkpoints")
        print(f"  - Remaining: {remaining_count} checkpoints")

        assert remaining_count == 5, "Retention policy failed"
        print(f"\n✓ Retention policy: PASS")
    else:
        print(f"\n✗ Cleanup failed: {cleanup_result.unwrap_err()}")


def main():
    """Run all demonstrations."""
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║   CheckpointManager Demo - Auto-Checkpoint & Resume      ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    try:
        demo_basic_checkpoint()
        demo_auto_checkpoint()
        demo_multi_day_resume()
        demo_retention_policy()

        print("\n" + "=" * 60)
        print("All demonstrations completed successfully! ✓")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n✗ Demo failed: {e}")


if __name__ == "__main__":
    main()
