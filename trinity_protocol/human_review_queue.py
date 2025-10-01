"""
Human Review Queue for Trinity Protocol HITL System

Manages the queue of questions awaiting human (Alex's) approval.
Integrates with MessageBus for persistence and async operations.

Constitutional Compliance:
- Article I: Complete context - questions persist across restarts
- Article IV: Continuous learning - track responses for pattern extraction
- Article II: Strict typing - Pydantic models, no Dict[Any, Any]
- Privacy: Respect focus time, question rate limits

Flow:
1. ARCHITECT detects pattern → Formulates question
2. Submit to human_review_queue (this module)
3. QuestionDelivery presents to Alex
4. ResponseHandler processes answer
5. YES → Route to EXECUTOR
   NO/LATER → Store for learning
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.models.hitl import HumanReviewRequest, HumanResponse


class HumanReviewQueue:
    """
    Persistent queue for human review requests.

    Stores questions in SQLite with metadata, publishes to MessageBus
    for async delivery, and tracks responses for learning.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        db_path: str = "trinity_hitl.db",
        queue_name: str = "human_review_queue"
    ):
        """
        Initialize human review queue.

        Args:
            message_bus: MessageBus instance for pub/sub
            db_path: Path to SQLite database for question metadata
            queue_name: Name of message queue (default: human_review_queue)
        """
        self.message_bus = message_bus
        self.db_path = Path(db_path)
        self.queue_name = queue_name
        self.conn: Optional[sqlite3.Connection] = None

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for question tracking."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                correlation_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                pattern_context TEXT NOT NULL,
                priority INTEGER NOT NULL,
                suggested_action TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                response_type TEXT,
                response_comment TEXT,
                answered_at TEXT,
                response_time_seconds REAL
            )
        """)

        # Indices for fast retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority
            ON questions(status, priority DESC, created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation
            ON questions(correlation_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires
            ON questions(expires_at)
        """)

        self.conn.commit()

    async def submit_question(self, request: HumanReviewRequest) -> int:
        """
        Submit a question to the review queue.

        Args:
            request: HumanReviewRequest to submit

        Returns:
            Question ID (SQLite row ID)
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        # Store in SQLite
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO questions (
                correlation_id, question_text, question_type,
                pattern_context, priority, suggested_action,
                created_at, expires_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            request.correlation_id,
            request.question_text,
            request.question_type,
            request.pattern_context.model_dump_json(),  # Serialize Pydantic model
            request.priority,
            request.suggested_action,
            request.created_at.isoformat(),
            request.expires_at.isoformat()
        ))

        question_id = cursor.lastrowid
        self.conn.commit()

        # Publish to message bus
        await self.message_bus.publish(
            queue_name=self.queue_name,
            message={
                "question_id": question_id,
                "correlation_id": request.correlation_id,
                "question_text": request.question_text,
                "question_type": request.question_type,
                "priority": request.priority,
                "expires_at": request.expires_at.isoformat()
            },
            priority=request.priority,
            correlation_id=request.correlation_id
        )

        return question_id

    async def get_pending_questions(self, limit: int = 10) -> List[HumanReviewRequest]:
        """
        Get pending questions from queue, excluding expired ones.

        Args:
            limit: Maximum number of questions to return

        Returns:
            List of HumanReviewRequest objects, ordered by priority
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM questions
            WHERE status = 'pending' AND expires_at > ?
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """, (now, limit))

        rows = cursor.fetchall()

        # Convert rows to HumanReviewRequest objects
        questions = []
        for row in rows:
            from trinity_protocol.models.patterns import DetectedPattern

            # Deserialize pattern context
            pattern_context = DetectedPattern.model_validate_json(row['pattern_context'])

            request = HumanReviewRequest(
                correlation_id=row['correlation_id'],
                question_text=row['question_text'],
                question_type=row['question_type'],
                pattern_context=pattern_context,
                priority=row['priority'],
                expires_at=datetime.fromisoformat(row['expires_at']),
                created_at=datetime.fromisoformat(row['created_at']),
                suggested_action=row['suggested_action']
            )
            questions.append(request)

        return questions

    async def get_question_by_correlation(
        self,
        correlation_id: str
    ) -> Optional[HumanReviewRequest]:
        """
        Get question by correlation ID.

        Args:
            correlation_id: Correlation ID to search for

        Returns:
            HumanReviewRequest if found, None otherwise
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT *
            FROM questions
            WHERE correlation_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (correlation_id,))

        row = cursor.fetchone()
        if not row:
            return None

        from trinity_protocol.models.patterns import DetectedPattern

        pattern_context = DetectedPattern.model_validate_json(row['pattern_context'])

        request = HumanReviewRequest(
            correlation_id=row['correlation_id'],
            question_text=row['question_text'],
            question_type=row['question_type'],
            pattern_context=pattern_context,
            priority=row['priority'],
            expires_at=datetime.fromisoformat(row['expires_at']),
            created_at=datetime.fromisoformat(row['created_at']),
            suggested_action=row['suggested_action']
        )

        return request

    async def mark_answered(
        self,
        question_id: int,
        response: HumanResponse
    ) -> None:
        """
        Mark question as answered with response.

        Args:
            question_id: Question ID to update
            response: HumanResponse with user's answer
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE questions
            SET status = 'answered',
                response_type = ?,
                response_comment = ?,
                answered_at = ?,
                response_time_seconds = ?
            WHERE id = ?
        """, (
            response.response_type,
            response.comment,
            response.responded_at.isoformat(),
            response.response_time_seconds,
            question_id
        ))

        self.conn.commit()

    async def expire_old_questions(self) -> int:
        """
        Mark expired questions as expired.

        Returns:
            Number of questions expired
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE questions
            SET status = 'expired'
            WHERE status = 'pending' AND expires_at <= ?
        """, (now,))

        expired_count = cursor.rowcount
        self.conn.commit()

        return expired_count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dict with total questions, by status, acceptance rate, etc.
        """
        if not self.conn:
            raise RuntimeError("Database not initialized")

        cursor = self.conn.cursor()

        # Total questions
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        total = cursor.fetchone()['count']

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM questions
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}

        # Response breakdown
        cursor.execute("""
            SELECT response_type, COUNT(*) as count
            FROM questions
            WHERE response_type IS NOT NULL
            GROUP BY response_type
        """)
        by_response = {row['response_type']: row['count'] for row in cursor.fetchall()}

        # Calculate acceptance rate
        yes_count = by_response.get('YES', 0)
        no_count = by_response.get('NO', 0)
        total_answered = yes_count + no_count
        acceptance_rate = yes_count / total_answered if total_answered > 0 else 0.0

        # Average response time
        cursor.execute("""
            SELECT AVG(response_time_seconds) as avg_time
            FROM questions
            WHERE response_time_seconds IS NOT NULL
        """)
        avg_response_time = cursor.fetchone()['avg_time'] or 0.0

        return {
            "total_questions": total,
            "by_status": by_status,
            "by_response": by_response,
            "acceptance_rate": round(acceptance_rate, 3),
            "avg_response_time_seconds": round(avg_response_time, 2)
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
