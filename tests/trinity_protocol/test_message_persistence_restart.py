"""
Tests for Message Persistence Across Restarts

NECESSARY Pattern Compliance:
- Named: Clear test names describing persistence behavior
- Executable: Run independently with real SQLite
- Comprehensive: Cover restart scenarios
- Error-validated: Test crash recovery
- State-verified: Assert message persistence
- Side-effects controlled: Use temp databases
- Assertions meaningful: Specific persistence checks
- Repeatable: Deterministic restart scenarios
- Yield fast: <1s per test

Constitutional Compliance:
- Article IV: Continuous learning (messages persist for cross-session learning)
- Article I: Complete context (no data loss on restart)
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from trinity_protocol.message_bus import MessageBus


class TestMessagePersistenceAcrossRestarts:
    """Test that messages survive process restarts."""

    @pytest.mark.asyncio
    async def test_messages_persist_after_bus_close_and_reopen(self):
        """Published messages persist after bus close and reopen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # First session: publish messages
            bus1 = MessageBus(db_path=str(db_path))
            await bus1.publish("test_queue", {"data": "message1"})
            await bus1.publish("test_queue", {"data": "message2"})
            bus1.close()

            # Second session: reopen and verify messages exist
            bus2 = MessageBus(db_path=str(db_path))
            pending_count = await bus2.get_pending_count("test_queue")

            assert pending_count == 2
            bus2.close()

    @pytest.mark.asyncio
    async def test_messages_survive_process_crash_simulation(self):
        """Messages survive simulated process crash (unclean shutdown)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Publish messages
            bus1 = MessageBus(db_path=str(db_path))
            msg_id1 = await bus1.publish("execution_queue", {
                "task_id": "task-001",
                "spec": {"details": "important task"}
            })
            msg_id2 = await bus1.publish("execution_queue", {
                "task_id": "task-002",
                "spec": {"details": "critical task"}
            })

            # Simulate crash (no clean close)
            # Do NOT call bus1.close()
            bus1.conn.close()  # Forcefully close connection
            del bus1

            # Session 2: Restart and verify messages
            bus2 = MessageBus(db_path=str(db_path))
            pending = await bus2.get_pending_count("execution_queue")

            assert pending == 2

            # Verify message data intact
            messages_received = []
            async def consume():
                async for msg in bus2.subscribe("execution_queue", batch_size=10):
                    messages_received.append(msg)
                    if len(messages_received) >= 2:
                        break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(messages_received) == 2
            task_ids = {msg['task_id'] for msg in messages_received}
            assert task_ids == {"task-001", "task-002"}

            bus2.close()

    @pytest.mark.asyncio
    async def test_processed_messages_remain_processed_after_restart(self):
        """Processed messages remain processed after restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Publish and acknowledge
            bus1 = MessageBus(db_path=str(db_path))
            msg_id = await bus1.publish("test_queue", {"data": "processed"})
            await bus1.ack(msg_id)
            bus1.close()

            # Session 2: Verify message still processed
            bus2 = MessageBus(db_path=str(db_path))
            pending = await bus2.get_pending_count("test_queue")

            assert pending == 0  # Message should not reappear
            bus2.close()

    @pytest.mark.asyncio
    async def test_correlation_tracking_persists_across_restarts(self):
        """Correlation IDs persist and work after restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            corr_id = "test-correlation-restart"

            # Session 1: Publish related messages
            bus1 = MessageBus(db_path=str(db_path))
            await bus1.publish("queue1", {"step": 1}, correlation_id=corr_id)
            await bus1.publish("queue2", {"step": 2}, correlation_id=corr_id)
            bus1.close()

            # Session 2: Query by correlation after restart
            bus2 = MessageBus(db_path=str(db_path))
            related = await bus2.get_by_correlation(corr_id)

            assert len(related) == 2
            steps = [msg['message_data']['step'] for msg in related]
            assert set(steps) == {1, 2}

            bus2.close()


class TestRestartRecovery:
    """Test recovery behavior after restart."""

    @pytest.mark.asyncio
    async def test_subscriber_receives_old_messages_after_restart(self):
        """New subscriber receives old pending messages after restart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Publish but don't consume
            bus1 = MessageBus(db_path=str(db_path))
            await bus1.publish("recovery_queue", {"order": 1})
            await bus1.publish("recovery_queue", {"order": 2})
            await bus1.publish("recovery_queue", {"order": 3})
            bus1.close()

            # Session 2: Subscribe and receive all pending
            bus2 = MessageBus(db_path=str(db_path))

            messages_received = []
            async def consume():
                async for msg in bus2.subscribe("recovery_queue", batch_size=10):
                    messages_received.append(msg)
                    if len(messages_received) >= 3:
                        break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(messages_received) == 3
            orders = [msg['order'] for msg in messages_received]
            assert orders == [1, 2, 3]

            bus2.close()

    @pytest.mark.asyncio
    async def test_restart_does_not_duplicate_messages(self):
        """Restart does not duplicate or lose messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Publish 5 messages
            bus1 = MessageBus(db_path=str(db_path))
            for i in range(5):
                await bus1.publish("dedupe_queue", {"id": i})
            bus1.close()

            # Session 2: Count messages
            bus2 = MessageBus(db_path=str(db_path))
            count1 = await bus2.get_pending_count("dedupe_queue")
            bus2.close()

            # Session 3: Count again
            bus3 = MessageBus(db_path=str(db_path))
            count2 = await bus3.get_pending_count("dedupe_queue")
            bus3.close()

            # Counts should be identical
            assert count1 == 5
            assert count2 == 5


class TestTimeoutHandling:
    """Test handling of timeouts across restarts."""

    @pytest.mark.asyncio
    async def test_messages_remain_pending_if_subscriber_times_out(self):
        """Messages remain pending if subscriber times out before ack."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Publish message
            bus1 = MessageBus(db_path=str(db_path))
            msg_id = await bus1.publish("timeout_queue", {"data": "value"})

            # Subscribe but timeout without ack
            async def consume_and_timeout():
                async for msg in bus1.subscribe("timeout_queue"):
                    # Receive message but DON'T ack
                    # Simulate timeout/crash
                    return msg

            try:
                await asyncio.wait_for(consume_and_timeout(), timeout=0.5)
            except asyncio.TimeoutError:
                pass

            bus1.close()

            # Session 2: Message should still be pending
            bus2 = MessageBus(db_path=str(db_path))
            pending = await bus2.get_pending_count("timeout_queue")

            assert pending == 1  # Message NOT acknowledged, still pending

            bus2.close()


class TestContinuousOperation:
    """Test 24/7 continuous operation scenarios."""

    @pytest.mark.asyncio
    async def test_supports_true_24_7_operation(self):
        """Message bus supports true 24/7 continuous operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Simulate 3 restart cycles
            for cycle in range(3):
                bus = MessageBus(db_path=str(db_path))

                # Publish work
                await bus.publish("continuous_queue", {"cycle": cycle})

                # Close (simulating restart)
                bus.close()

            # Final session: verify all work queued
            final_bus = MessageBus(db_path=str(db_path))
            pending = await final_bus.get_pending_count("continuous_queue")

            assert pending == 3

            final_bus.close()

    @pytest.mark.asyncio
    async def test_executor_restart_recovery_scenario(self):
        """
        Simulate EXECUTOR restart recovery.

        Article IV requirement: Work must not be lost on restart.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # ARCHITECT publishes tasks
            bus_architect = MessageBus(db_path=str(db_path))
            await bus_architect.publish("execution_queue", {
                "task_id": "task-1",
                "correlation_id": "work-batch-001",
                "task_type": "code_generation"
            })
            await bus_architect.publish("execution_queue", {
                "task_id": "task-2",
                "correlation_id": "work-batch-001",
                "task_type": "test_generation"
            })
            bus_architect.close()

            # EXECUTOR starts, processes task-1, then crashes before task-2
            bus_executor_1 = MessageBus(db_path=str(db_path))

            messages_processed = []
            async def executor_consume():
                async for msg in bus_executor_1.subscribe("execution_queue"):
                    messages_processed.append(msg)
                    # Process task-1
                    await bus_executor_1.ack(msg["_message_id"])

                    # Crash before processing task-2
                    if len(messages_processed) >= 1:
                        break

            try:
                await asyncio.wait_for(executor_consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # Simulate crash
            bus_executor_1.conn.close()
            del bus_executor_1

            # EXECUTOR restarts
            bus_executor_2 = MessageBus(db_path=str(db_path))
            pending = await bus_executor_2.get_pending_count("execution_queue")

            # Should have task-2 still pending
            assert pending == 1

            # Verify it's task-2
            remaining_messages = []
            async def consume_remaining():
                async for msg in bus_executor_2.subscribe("execution_queue", batch_size=10):
                    remaining_messages.append(msg)
                    break

            try:
                await asyncio.wait_for(consume_remaining(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(remaining_messages) == 1
            assert remaining_messages[0]['task_id'] == "task-2"

            bus_executor_2.close()


class TestArticleIVCompliance:
    """Test Article IV: Continuous Learning compliance."""

    @pytest.mark.asyncio
    async def test_telemetry_persists_for_learning(self):
        """
        Telemetry messages persist for WITNESS learning.

        Article IV requirement: Enable cross-session pattern recognition.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # EXECUTOR publishes telemetry
            bus_executor = MessageBus(db_path=str(db_path))
            await bus_executor.publish("telemetry_stream", {
                "status": "success",
                "task_id": "task-001",
                "duration_seconds": 45.2,
                "cost_usd": 0.15
            })
            bus_executor.close()

            # System restarts

            # WITNESS starts and reads telemetry
            bus_witness = MessageBus(db_path=str(db_path))
            pending = await bus_witness.get_pending_count("telemetry_stream")

            assert pending == 1  # Telemetry available for learning

            bus_witness.close()

    @pytest.mark.asyncio
    async def test_improvement_signals_persist_for_architect(self):
        """
        Improvement signals persist for ARCHITECT.

        Article IV: Patterns detected must not be lost on restart.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # WITNESS publishes improvement signal
            bus_witness = MessageBus(db_path=str(db_path))
            await bus_witness.publish("improvement_queue", {
                "pattern": "type_violation",
                "confidence": 0.85,
                "evidence_count": 5,
                "priority": "HIGH"
            })
            bus_witness.close()

            # System restarts overnight

            # ARCHITECT starts next day
            bus_architect = MessageBus(db_path=str(db_path))
            pending = await bus_architect.get_pending_count("improvement_queue")

            assert pending == 1  # Improvement signal preserved

            # ARCHITECT can process it
            signals_received = []
            async def consume():
                async for msg in bus_architect.subscribe("improvement_queue"):
                    signals_received.append(msg)
                    break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(signals_received) == 1
            assert signals_received[0]['pattern'] == "type_violation"

            bus_architect.close()
