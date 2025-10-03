"""
Tests for Trinity Protocol Message Bus

NECESSARY Pattern Compliance:
- Named: Clear test names describing async behavior
- Executable: Run independently with async support
- Comprehensive: Cover pub/sub, persistence, correlation
- Error-validated: Test async error conditions
- State-verified: Assert message states
- Side-effects controlled: Clean temp files
- Assertions meaningful: Specific async checks
- Repeatable: Deterministic async results
- Yield fast: <1s per async test
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from shared.message_bus import MessageBus, async_message_bus


class TestMessageBusInitialization:
    """Test message bus initialization."""

    def test_creates_database_file_on_init(self):
        """Bus creates SQLite database file when initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            assert db_path.exists()
            assert db_path.stat().st_size > 0

            bus.close()

    def test_initializes_messages_table(self):
        """Bus creates messages table with correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            cursor = bus.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='messages'
            """)
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "messages"

            bus.close()

    def test_supports_context_manager(self):
        """Bus supports context manager protocol."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            with MessageBus(db_path=str(db_path)) as bus:
                assert bus.conn is not None

    @pytest.mark.asyncio
    async def test_supports_async_context_manager(self):
        """Bus supports async context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            async with async_message_bus(db_path=str(db_path)) as bus:
                assert bus.conn is not None


class TestMessagePublishing:
    """Test message publishing operations."""

    @pytest.mark.asyncio
    async def test_publishes_message_to_queue(self):
        """Bus persists published message to database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            message_id = await bus.publish(
                queue_name="test_queue",
                message={"data": "test_value"}
            )

            assert isinstance(message_id, int)
            assert message_id > 0

            # Verify in database
            cursor = bus.conn.cursor()
            cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()

            assert row is not None
            assert row['queue_name'] == "test_queue"
            assert '"data": "test_value"' in row['message_data']
            assert row['status'] == "pending"

            bus.close()

    @pytest.mark.asyncio
    async def test_stores_priority_correctly(self):
        """Bus stores message priority for ordering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            message_id = await bus.publish(
                queue_name="test_queue",
                message={"data": "urgent"},
                priority=10
            )

            cursor = bus.conn.cursor()
            cursor.execute("SELECT priority FROM messages WHERE id = ?", (message_id,))
            priority = cursor.fetchone()['priority']

            assert priority == 10

            bus.close()

    @pytest.mark.asyncio
    async def test_stores_correlation_id(self):
        """Bus stores correlation ID for message linking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            correlation_id = "test-correlation-123"
            message_id = await bus.publish(
                queue_name="test_queue",
                message={"data": "linked"},
                correlation_id=correlation_id
            )

            cursor = bus.conn.cursor()
            cursor.execute(
                "SELECT correlation_id FROM messages WHERE id = ?",
                (message_id,)
            )
            stored_corr_id = cursor.fetchone()['correlation_id']

            assert stored_corr_id == correlation_id

            bus.close()

    @pytest.mark.asyncio
    async def test_serializes_complex_message_data(self):
        """Bus serializes nested dicts and lists to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            complex_message = {
                "pattern": "failure",
                "data": {
                    "file": "test.py",
                    "keywords": ["error", "critical"]
                },
                "confidence": 0.85
            }

            message_id = await bus.publish(
                queue_name="test_queue",
                message=complex_message
            )

            cursor = bus.conn.cursor()
            cursor.execute(
                "SELECT message_data FROM messages WHERE id = ?",
                (message_id,)
            )
            stored_data = cursor.fetchone()['message_data']

            assert "pattern" in stored_data
            assert '"keywords": ["error", "critical"]' in stored_data or '"keywords":["error","critical"]' in stored_data

            bus.close()


class TestMessageSubscription:
    """Test message subscription and consumption."""

    @pytest.mark.asyncio
    async def test_subscribes_to_queue_and_receives_messages(self):
        """Subscriber receives messages published to queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            # Publish message first
            await bus.publish(
                queue_name="test_queue",
                message={"data": "test"}
            )

            # Subscribe and receive
            messages_received = []
            async def consume():
                async for message in bus.subscribe("test_queue"):
                    messages_received.append(message)
                    if len(messages_received) >= 1:
                        break

            # Run with timeout
            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(messages_received) == 1
            assert messages_received[0]['data'] == "test"

            bus.close()

    @pytest.mark.asyncio
    async def test_receives_existing_pending_messages_first(self):
        """Subscriber receives existing pending messages before new ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            # Publish 3 messages before subscribing
            await bus.publish("test_queue", {"order": 1})
            await bus.publish("test_queue", {"order": 2})
            await bus.publish("test_queue", {"order": 3})

            # Subscribe and receive
            messages_received = []
            async def consume():
                async for message in bus.subscribe("test_queue", batch_size=10):
                    messages_received.append(message)
                    if len(messages_received) >= 3:
                        break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(messages_received) == 3
            orders = [msg['order'] for msg in messages_received]
            assert orders == [1, 2, 3]

            bus.close()

    @pytest.mark.asyncio
    async def test_multiple_subscribers_receive_same_message(self):
        """Multiple subscribers all receive published messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            received_1 = []
            received_2 = []

            async def subscriber_1():
                async for msg in bus.subscribe("test_queue"):
                    received_1.append(msg)
                    if len(received_1) >= 1:
                        break

            async def subscriber_2():
                async for msg in bus.subscribe("test_queue"):
                    received_2.append(msg)
                    if len(received_2) >= 1:
                        break

            # Start subscribers
            task1 = asyncio.create_task(subscriber_1())
            task2 = asyncio.create_task(subscriber_2())

            # Give subscribers time to initialize
            await asyncio.sleep(0.1)

            # Publish message
            await bus.publish("test_queue", {"shared": "data"})

            # Wait for subscribers to receive
            try:
                await asyncio.wait_for(
                    asyncio.gather(task1, task2),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                pass

            # Both should have received the message
            assert len(received_1) >= 1
            assert len(received_2) >= 1
            assert received_1[0]['shared'] == "data"
            assert received_2[0]['shared'] == "data"

            bus.close()

    @pytest.mark.asyncio
    async def test_respects_priority_ordering(self):
        """Subscriber receives higher priority messages first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            # Publish messages with different priorities
            await bus.publish("test_queue", {"name": "low"}, priority=1)
            await bus.publish("test_queue", {"name": "high"}, priority=10)
            await bus.publish("test_queue", {"name": "medium"}, priority=5)

            # Subscribe and receive
            messages_received = []
            async def consume():
                async for message in bus.subscribe("test_queue", batch_size=10):
                    messages_received.append(message)
                    if len(messages_received) >= 3:
                        break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            # Should receive in priority order: high, medium, low
            names = [msg['name'] for msg in messages_received]
            assert names == ["high", "medium", "low"]

            bus.close()


class TestMessageAcknowledgment:
    """Test message acknowledgment and status tracking."""

    @pytest.mark.asyncio
    async def test_marks_message_as_processed(self):
        """Ack marks message status as processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            message_id = await bus.publish(
                "test_queue",
                {"data": "test"}
            )

            await bus.ack(message_id)

            cursor = bus.conn.cursor()
            cursor.execute(
                "SELECT status, processed_at FROM messages WHERE id = ?",
                (message_id,)
            )
            row = cursor.fetchone()

            assert row['status'] == "processed"
            assert row['processed_at'] is not None

            bus.close()

    @pytest.mark.asyncio
    async def test_processed_messages_not_returned_to_subscribers(self):
        """Processed messages don't appear in subscription feed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            # Publish and immediately acknowledge
            msg_id = await bus.publish("test_queue", {"data": "processed"})
            await bus.ack(msg_id)

            # Publish unprocessed message
            await bus.publish("test_queue", {"data": "pending"})

            # Subscribe should only get pending
            messages_received = []
            async def consume():
                async for message in bus.subscribe("test_queue", batch_size=10):
                    messages_received.append(message)
                    if len(messages_received) >= 1:
                        break

            try:
                await asyncio.wait_for(consume(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            assert len(messages_received) == 1
            assert messages_received[0]['data'] == "pending"

            bus.close()


class TestCorrelationTracking:
    """Test correlation ID tracking for related messages."""

    @pytest.mark.asyncio
    async def test_retrieves_messages_by_correlation_id(self):
        """Bus returns all messages with given correlation ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            corr_id = "test-correlation-123"

            # Publish related messages
            await bus.publish("queue1", {"step": 1}, correlation_id=corr_id)
            await bus.publish("queue2", {"step": 2}, correlation_id=corr_id)
            await bus.publish("queue3", {"step": 3}, correlation_id=corr_id)

            # Publish unrelated message
            await bus.publish("queue1", {"step": "unrelated"})

            # Get by correlation
            related = await bus.get_by_correlation(corr_id)

            assert len(related) == 3
            steps = [msg['message_data']['step'] for msg in related]
            assert steps == [1, 2, 3]

            bus.close()

    @pytest.mark.asyncio
    async def test_correlation_messages_ordered_by_time(self):
        """Correlated messages returned in chronological order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            corr_id = "time-test"

            # Publish in specific order
            await bus.publish("q1", {"order": "first"}, correlation_id=corr_id)
            await asyncio.sleep(0.01)  # Ensure different timestamps
            await bus.publish("q2", {"order": "second"}, correlation_id=corr_id)
            await asyncio.sleep(0.01)
            await bus.publish("q3", {"order": "third"}, correlation_id=corr_id)

            related = await bus.get_by_correlation(corr_id)

            orders = [msg['message_data']['order'] for msg in related]
            assert orders == ["first", "second", "third"]

            bus.close()


class TestStatistics:
    """Test message bus statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_returns_total_message_count(self):
        """Stats include total number of messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            await bus.publish("q1", {"data": 1})
            await bus.publish("q2", {"data": 2})
            await bus.publish("q3", {"data": 3})

            stats = bus.get_stats()

            assert stats['total_messages'] == 3

            bus.close()

    @pytest.mark.asyncio
    async def test_groups_messages_by_status(self):
        """Stats include breakdown by message status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            msg1 = await bus.publish("q1", {"data": 1})
            await bus.publish("q1", {"data": 2})
            await bus.ack(msg1)  # One processed, one pending

            stats = bus.get_stats()

            assert 'by_status' in stats
            assert stats['by_status'].get('processed', 0) == 1
            assert stats['by_status'].get('pending', 0) == 1

            bus.close()

    @pytest.mark.asyncio
    async def test_groups_messages_by_queue(self):
        """Stats include breakdown by queue name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            await bus.publish("improvement_queue", {"data": 1})
            await bus.publish("improvement_queue", {"data": 2})
            await bus.publish("execution_queue", {"data": 3})

            stats = bus.get_stats()

            assert 'by_queue' in stats
            assert 'improvement_queue' in stats['by_queue']
            assert 'execution_queue' in stats['by_queue']

            bus.close()

    @pytest.mark.asyncio
    async def test_tracks_active_subscribers(self):
        """Stats include count of active subscribers per queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            # Create subscriber tasks (but don't await them)
            async def dummy_subscriber(queue):
                async for _ in bus.subscribe(queue):
                    pass

            task1 = asyncio.create_task(dummy_subscriber("q1"))
            task2 = asyncio.create_task(dummy_subscriber("q1"))
            task3 = asyncio.create_task(dummy_subscriber("q2"))

            # Give subscribers time to register
            await asyncio.sleep(0.1)

            stats = bus.get_stats()

            assert 'active_subscribers' in stats
            assert stats['active_subscribers'].get('q1', 0) == 2
            assert stats['active_subscribers'].get('q2', 0) == 1

            # Cleanup
            task1.cancel()
            task2.cancel()
            task3.cancel()
            try:
                await asyncio.gather(task1, task2, task3)
            except asyncio.CancelledError:
                pass

            bus.close()

    @pytest.mark.asyncio
    async def test_returns_pending_count_for_queue(self):
        """Bus returns count of pending messages in specific queue."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            await bus.publish("q1", {"data": 1})
            await bus.publish("q1", {"data": 2})
            msg3 = await bus.publish("q1", {"data": 3})
            await bus.ack(msg3)  # One processed

            await bus.publish("q2", {"data": 4})

            q1_pending = await bus.get_pending_count("q1")
            q2_pending = await bus.get_pending_count("q2")

            assert q1_pending == 2  # 2 pending in q1
            assert q2_pending == 1  # 1 pending in q2

            bus.close()


class TestErrorHandling:
    """Test error conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_raises_error_when_publishing_without_init(self):
        """Bus raises RuntimeError if used before initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))
            bus.close()
            bus.conn = None

            with pytest.raises(RuntimeError, match="Message bus not initialized"):
                await bus.publish("test_queue", {"data": "test"})

    @pytest.mark.asyncio
    async def test_handles_empty_queue_gracefully(self):
        """Bus handles subscription to empty queue without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            bus = MessageBus(db_path=str(db_path))

            messages_received = []

            async def consume_with_timeout():
                async for message in bus.subscribe("empty_queue"):
                    messages_received.append(message)
                    break

            try:
                await asyncio.wait_for(consume_with_timeout(), timeout=0.5)
            except asyncio.TimeoutError:
                pass  # Expected - no messages available

            # Should not have raised any exceptions
            assert len(messages_received) == 0

            bus.close()
