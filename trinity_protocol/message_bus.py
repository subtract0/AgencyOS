"""
Message Bus for Trinity Protocol

Provides persistent, async message queue for agent communication.
Messages persist across restarts, enabling true continuous operation.

Architecture:
- SQLite: Persistent message storage
- Asyncio: Non-blocking queue operations
- Pub/Sub: Multiple subscribers per queue

Queues:
- improvement_queue: WITNESS → ARCHITECT (patterns detected)
- execution_queue: ARCHITECT → EXECUTOR (tasks to execute)
- telemetry_stream: EXECUTOR → WITNESS (outcomes, loop closure)
- personal_context_stream: User → WITNESS (user intent signals)

Constitutional Compliance:
- Article I: Complete context - messages persist until processed
- Article IV: Continuous learning - telemetry enables cross-session learning
"""

import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, AsyncIterator
import json
from contextlib import asynccontextmanager


class MessageBus:
    """
    Persistent async message bus for Trinity Protocol.

    Supports multiple queues with pub/sub pattern. Messages persist
    across restarts for true 24/7 autonomous operation.
    """

    def __init__(self, db_path: str = "trinity_messages.db"):
        """
        Initialize message bus.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with message schema."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queue_name TEXT NOT NULL,
                message_data TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                correlation_id TEXT,
                created_at TEXT NOT NULL,
                processed_at TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)

        # Indices for fast retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_status
            ON messages(queue_name, status, priority DESC, created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation
            ON messages(correlation_id)
        """)

        self.conn.commit()

    async def publish(
        self,
        queue_name: str,
        message: Dict[str, Any],
        priority: int = 0,
        correlation_id: Optional[str] = None
    ) -> int:
        """
        Publish message to queue.

        Args:
            queue_name: Target queue name
            message: Message data as dict
            priority: Priority (higher = more urgent)
            correlation_id: Optional ID linking related messages

        Returns:
            Message ID
        """
        if not self.conn:
            raise RuntimeError("Message bus not initialized")

        message_json = json.dumps(message)
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO messages (
                queue_name, message_data, priority, correlation_id,
                created_at, status
            )
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (queue_name, message_json, priority, correlation_id, now))

        message_id = cursor.lastrowid
        self.conn.commit()

        # Notify subscribers
        await self._notify_subscribers(queue_name, message_id, message)

        return message_id

    async def subscribe(
        self,
        queue_name: str,
        batch_size: int = 1
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to queue and yield messages as they arrive.

        Args:
            queue_name: Queue name to subscribe to
            batch_size: Number of messages to fetch per batch

        Yields:
            Message dicts from queue
        """
        # Create subscriber queue
        subscriber_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        if queue_name not in self.subscribers:
            self.subscribers[queue_name] = []
        self.subscribers[queue_name].append(subscriber_queue)

        try:
            # First, yield any existing pending messages
            existing = await self._fetch_pending(queue_name, batch_size)
            for msg in existing:
                yield msg

            # Then yield new messages as they arrive
            while True:
                message = await subscriber_queue.get()
                yield message

        finally:
            # Cleanup subscriber
            if queue_name in self.subscribers:
                self.subscribers[queue_name].remove(subscriber_queue)

    async def _notify_subscribers(
        self,
        queue_name: str,
        message_id: int,
        message: Dict[str, Any]
    ) -> None:
        """Notify all subscribers of new message."""
        if queue_name in self.subscribers:
            for subscriber_queue in self.subscribers[queue_name]:
                try:
                    # Add message ID to message data
                    full_message = {"_message_id": message_id, **message}
                    await subscriber_queue.put(full_message)
                except asyncio.QueueFull:
                    # Skip if subscriber queue is full
                    pass

    async def _fetch_pending(
        self,
        queue_name: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch pending messages from database."""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, message_data
            FROM messages
            WHERE queue_name = ? AND status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """, (queue_name, limit))

        rows = cursor.fetchall()
        messages = []

        for row in rows:
            message_data = json.loads(row['message_data'])
            message_data['_message_id'] = row['id']
            messages.append(message_data)

        return messages

    async def ack(self, message_id: int) -> None:
        """
        Acknowledge message as processed.

        Args:
            message_id: Message ID to acknowledge
        """
        if not self.conn:
            raise RuntimeError("Message bus not initialized")

        now = datetime.now().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE messages
            SET status = 'processed', processed_at = ?
            WHERE id = ?
        """, (now, message_id))

        self.conn.commit()

    async def get_pending_count(self, queue_name: str) -> int:
        """
        Get count of pending messages in queue.

        Args:
            queue_name: Queue name

        Returns:
            Number of pending messages
        """
        if not self.conn:
            raise RuntimeError("Message bus not initialized")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE queue_name = ? AND status = 'pending'
        """, (queue_name,))

        return cursor.fetchone()['count']

    async def get_by_correlation(
        self,
        correlation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all messages with given correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of related messages
        """
        if not self.conn:
            raise RuntimeError("Message bus not initialized")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, queue_name, message_data, status, created_at, processed_at
            FROM messages
            WHERE correlation_id = ?
            ORDER BY created_at ASC
        """, (correlation_id,))

        rows = cursor.fetchall()
        messages = []

        for row in rows:
            msg = dict(row)
            msg['message_data'] = json.loads(msg['message_data'])
            messages.append(msg)

        return messages

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dict with queue stats, throughput, etc.
        """
        if not self.conn:
            raise RuntimeError("Message bus not initialized")

        cursor = self.conn.cursor()

        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        total = cursor.fetchone()['count']

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM messages
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}

        # By queue
        cursor.execute("""
            SELECT queue_name, COUNT(*) as count, status
            FROM messages
            GROUP BY queue_name, status
        """)
        by_queue: Dict[str, Dict[str, int]] = {}
        for row in cursor.fetchall():
            queue = row['queue_name']
            if queue not in by_queue:
                by_queue[queue] = {}
            by_queue[queue][row['status']] = row['count']

        # Active subscribers
        active_subscribers = {
            queue: len(subs)
            for queue, subs in self.subscribers.items()
        }

        return {
            "total_messages": total,
            "by_status": by_status,
            "by_queue": by_queue,
            "active_subscribers": active_subscribers
        }

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


@asynccontextmanager
async def async_message_bus(db_path: str = "trinity_messages.db"):
    """
    Async context manager for message bus.

    Usage:
        async with async_message_bus() as bus:
            await bus.publish("test_queue", {"data": "value"})
    """
    bus = MessageBus(db_path)
    try:
        yield bus
    finally:
        bus.close()
