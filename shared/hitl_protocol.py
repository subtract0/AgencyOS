"""
Generic Human-in-the-Loop (HITL) Protocol

Provides persistent, async question-answer system for agent-human interaction.
Consolidates functionality from trinity_protocol/human_review_queue.py and
trinity_protocol/question_delivery.py into a generic, reusable protocol.

Features:
- Asynchronous question asking (ask_async)
- Response waiting with timeout (wait_response)
- Approval workflow (approve)
- Queue management (get_pending, expire_old_questions)
- Statistics tracking (get_stats)
- Message bus integration for pub/sub
- SQLite persistence for reliability

Constitutional Compliance:
- Article I: Complete context - questions persist across restarts
- Article II: Strict typing - Pydantic models, no Dict[Any, Any]
- Article IV: Continuous learning - track responses for pattern extraction
- Article V: TDD - comprehensive tests written first

Usage:
    # Async context manager
    async with HITLProtocol(message_bus) as hitl:
        question_id = await hitl.ask_async("Proceed?", {"file": "test.py"})
        response = await hitl.wait_response(question_id, timeout=300)
        if response.is_ok():
            print(f"User said: {response.value.answer}")

    # Approval workflow
    async with HITLProtocol(message_bus) as hitl:
        approved = await hitl.approve(
            action="Refactor test.py",
            details={"lines": 100}
        )
        if approved.is_ok() and approved.value:
            print("Approved!")
"""

import sqlite3
import asyncio
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field, field_validator

from shared.type_definitions.result import Result, Ok, Err
from shared.type_definitions.json_value import JSONValue
from shared.message_bus import MessageBus


class HITLError(Exception):
    """Base exception for HITL protocol errors."""
    pass


class HITLTimeoutError(HITLError):
    """Exception for timeout errors."""
    pass


class HITLQuestion(BaseModel):
    """
    Question submitted to HITL queue.

    Fields:
        question_id: Unique question identifier
        question: Question text to display to user
        context: Additional context as key-value pairs
        options: List of valid response options (empty = free-form)
        timeout_seconds: Timeout in seconds before question expires
        created_at: When question was created
    """

    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., min_length=1, description="Question text")
    context: Dict[str, str] = Field(
        default_factory=dict, description="Additional context"
    )
    options: List[str] = Field(
        default_factory=list, description="Valid response options"
    )
    timeout_seconds: int = Field(
        default=300, ge=1, description="Timeout in seconds"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    @field_validator("question_id")
    @classmethod
    def validate_question_id(cls, v: str) -> str:
        """Validate question_id is not empty."""
        if not v or not v.strip():
            raise ValueError("question_id cannot be empty")
        return v

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question is not empty."""
        if not v or not v.strip():
            raise ValueError("question cannot be empty")
        return v


class HITLResponse(BaseModel):
    """
    Response to a HITL question.

    Fields:
        question_id: Question being answered
        answer: User's answer text
        timestamp: When response was submitted
    """

    question_id: str = Field(..., description="Question being answered")
    answer: str = Field(..., description="User's answer")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class HITLConfig(BaseModel):
    """
    Configuration for HITL protocol.

    Fields:
        queue_name: Message bus queue name
        default_timeout_seconds: Default timeout for questions
        max_questions_per_hour: Rate limit for questions
        quiet_hours_start: Hour to stop asking (0-23, None = no quiet hours)
        quiet_hours_end: Hour to resume asking (0-23)
    """

    queue_name: str = Field(
        default="hitl_questions", description="Message bus queue name"
    )
    default_timeout_seconds: int = Field(
        default=300, ge=1, description="Default timeout"
    )
    max_questions_per_hour: int = Field(
        default=10, ge=1, description="Max questions per hour"
    )
    quiet_hours_start: Optional[int] = Field(
        default=None, ge=0, le=23, description="Quiet hours start (24h)"
    )
    quiet_hours_end: Optional[int] = Field(
        default=None, ge=0, le=23, description="Quiet hours end (24h)"
    )


class HITLProtocol:
    """
    Generic human-in-the-loop protocol.

    Manages question queue, response collection, and approval workflows.
    Uses MessageBus for pub/sub and SQLite for persistence.
    """

    def __init__(
        self,
        message_bus: MessageBus,
        config: Optional[HITLConfig] = None,
        db_path: str = "hitl_protocol.db",
    ):
        """
        Initialize HITL protocol.

        Args:
            message_bus: MessageBus for pub/sub
            config: Configuration (uses defaults if None)
            db_path: Path to SQLite database
        """
        self.message_bus = message_bus
        self.config = config or HITLConfig()
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._response_waiters: Dict[str, asyncio.Future] = {}

        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        self.conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hitl_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL UNIQUE,
                question_text TEXT NOT NULL,
                context TEXT NOT NULL,
                options TEXT NOT NULL,
                timeout_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                response TEXT,
                answered_at TEXT
            )
        """)

        # Indices for fast retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON hitl_questions(status, created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_question_id
            ON hitl_questions(question_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires
            ON hitl_questions(expires_at)
        """)

        self.conn.commit()

    def ask(
        self,
        question: str,
        context: Optional[Dict[str, str]] = None,
        options: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Result[str, str]:
        """
        Ask synchronous question (blocking).

        NOT IMPLEMENTED in MVP - use ask_async() instead.

        Args:
            question: Question text
            context: Additional context
            options: Valid response options
            timeout_seconds: Timeout in seconds

        Returns:
            Result with answer on success, error on failure
        """
        return Err(
            "Synchronous ask() not implemented - use ask_async() instead"
        )

    async def ask_async(
        self,
        question: str,
        context: Optional[Dict[str, str]] = None,
        options: Optional[List[str]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Result[str, str]:
        """
        Ask asynchronous question (returns question_id immediately).

        Creates question, stores in database, publishes to message bus.
        Use wait_response() to wait for user response.

        Args:
            question: Question text
            context: Additional context
            options: Valid response options
            timeout_seconds: Timeout in seconds (uses default if None)

        Returns:
            Result with question_id on success, error on failure

        Example:
            result = await hitl.ask_async("Proceed?", {"file": "test.py"})
            if result.is_ok():
                question_id = result.value
                response = await hitl.wait_response(question_id, timeout=300)
        """
        if not question or not question.strip():
            return Err("Question cannot be empty")

        try:
            # Create question model
            question_id = str(uuid.uuid4())
            timeout = timeout_seconds or self.config.default_timeout_seconds
            now = datetime.now()
            expires_at = now + timedelta(seconds=timeout)

            hitl_question = HITLQuestion(
                question_id=question_id,
                question=question,
                context=context or {},
                options=options or [],
                timeout_seconds=timeout,
                created_at=now,
            )

            # Store in database
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO hitl_questions (
                    question_id, question_text, context, options,
                    timeout_seconds, created_at, expires_at, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
                (
                    question_id,
                    question,
                    json.dumps(context or {}),
                    json.dumps(options or []),
                    timeout,
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )
            self.conn.commit()

            # Publish to message bus
            await self.message_bus.publish(
                queue_name=self.config.queue_name,
                message={
                    "question_id": question_id,
                    "question": question,
                    "context": context or {},
                    "options": options or [],
                    "expires_at": expires_at.isoformat(),
                },
                priority=5,
            )

            return Ok(question_id)

        except Exception as e:
            return Err(f"Failed to create question: {str(e)}")

    async def wait_response(
        self, question_id: str, timeout: int
    ) -> Result[HITLResponse, str]:
        """
        Wait for response to a question.

        Blocks until response is submitted or timeout expires.

        Args:
            question_id: Question ID to wait for
            timeout: Timeout in seconds

        Returns:
            Result with HITLResponse on success, error on timeout/failure

        Example:
            question_id = (await hitl.ask_async("Proceed?", {})).value
            result = await hitl.wait_response(question_id, timeout=300)
            if result.is_ok():
                print(f"User said: {result.value.answer}")
        """
        # Check if question exists
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        if not row:
            return Err(f"Question '{question_id}' not found")

        # Check if already answered
        if row["status"] == "answered":
            return Ok(
                HITLResponse(
                    question_id=question_id,
                    answer=row["response"],
                    timestamp=datetime.fromisoformat(row["answered_at"]),
                )
            )

        # Create future for this question
        future: asyncio.Future = asyncio.Future()
        self._response_waiters[question_id] = future

        try:
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return Ok(response)

        except asyncio.TimeoutError:
            return Err(f"Timeout waiting for response to '{question_id}'")

        finally:
            # Cleanup waiter
            if question_id in self._response_waiters:
                del self._response_waiters[question_id]

    async def approve(
        self,
        action: str,
        details: Optional[JSONValue] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Result[bool, str]:
        """
        Request approval for an action.

        Convenience method that creates approval question and waits for response.
        Returns True if approved (user responds 'yes'), False if rejected.

        Args:
            action: Action description
            details: Additional details
            timeout_seconds: Timeout in seconds

        Returns:
            Result with True/False on success, error on timeout/failure

        Example:
            result = await hitl.approve(
                action="Refactor test.py",
                details={"lines": 100}
            )
            if result.is_ok() and result.value:
                print("Approved - proceeding with refactor")
        """
        # Create approval question
        question = f"Approve: {action}?"
        context_dict = {
            "action": action,
            **(details or {}),
        }

        # Convert all values to strings
        context = {
            k: str(v) for k, v in context_dict.items()
        }

        result = await self.ask_async(
            question=question,
            context=context,
            options=["yes", "no"],
            timeout_seconds=timeout_seconds,
        )

        if result.is_err():
            return Err(result.unwrap_err())

        question_id = result.unwrap()
        timeout = timeout_seconds or self.config.default_timeout_seconds

        # Wait for response
        response_result = await self.wait_response(
            question_id, timeout=timeout
        )

        if response_result.is_err():
            return Err(response_result.unwrap_err())

        response = response_result.unwrap()
        approved = response.answer.lower() in ["yes", "y", "true", "1"]

        return Ok(approved)

    async def get_pending(
        self, limit: int = 100
    ) -> Result[List[HITLQuestion], str]:
        """
        Get pending questions from queue.

        Returns questions that are pending (not answered or expired).

        Args:
            limit: Maximum number of questions to return

        Returns:
            Result with list of HITLQuestion on success, error on failure

        Example:
            result = await hitl.get_pending()
            if result.is_ok():
                for question in result.value:
                    print(f"Pending: {question.question}")
        """
        try:
            now = datetime.now().isoformat()

            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM hitl_questions
                WHERE status = 'pending' AND expires_at > ?
                ORDER BY created_at ASC
                LIMIT ?
            """,
                (now, limit),
            )

            rows = cursor.fetchall()

            questions = []
            for row in rows:
                question = HITLQuestion(
                    question_id=row["question_id"],
                    question=row["question_text"],
                    context=json.loads(row["context"]),
                    options=json.loads(row["options"]),
                    timeout_seconds=row["timeout_seconds"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                questions.append(question)

            return Ok(questions)

        except Exception as e:
            return Err(f"Failed to get pending questions: {str(e)}")

    async def submit_response(
        self, question_id: str, answer: str
    ) -> Result[None, str]:
        """
        Submit response to a question.

        Marks question as answered, stores response, and notifies waiters.

        Args:
            question_id: Question ID to answer
            answer: User's answer

        Returns:
            Result with None on success, error on failure

        Example:
            await hitl.submit_response("q123", "yes")
        """
        if not answer or not answer.strip():
            return Err("Answer cannot be empty")

        try:
            # Check if question exists
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM hitl_questions WHERE question_id = ?",
                (question_id,),
            )
            row = cursor.fetchone()

            if not row:
                return Err(f"Question '{question_id}' not found")

            now = datetime.now()

            # Update database
            cursor.execute(
                """
                UPDATE hitl_questions
                SET status = 'answered',
                    response = ?,
                    answered_at = ?
                WHERE question_id = ?
            """,
                (answer, now.isoformat(), question_id),
            )
            self.conn.commit()

            # Notify waiters
            if question_id in self._response_waiters:
                future = self._response_waiters[question_id]
                if not future.done():
                    response = HITLResponse(
                        question_id=question_id,
                        answer=answer,
                        timestamp=now,
                    )
                    future.set_result(response)

            return Ok(None)

        except Exception as e:
            return Err(f"Failed to submit response: {str(e)}")

    async def expire_old_questions(self) -> Result[int, str]:
        """
        Mark expired questions as expired.

        Updates status of questions past their expiration time.

        Returns:
            Result with count of expired questions on success, error on failure

        Example:
            result = await hitl.expire_old_questions()
            if result.is_ok():
                print(f"Expired {result.value} questions")
        """
        try:
            now = datetime.now().isoformat()

            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE hitl_questions
                SET status = 'expired'
                WHERE status = 'pending' AND expires_at <= ?
            """,
                (now,),
            )

            expired_count = cursor.rowcount
            self.conn.commit()

            return Ok(expired_count)

        except Exception as e:
            return Err(f"Failed to expire questions: {str(e)}")

    def get_stats(self) -> JSONValue:
        """
        Get HITL statistics.

        Returns:
            Dict with total questions, by status, acceptance rate, etc.

        Example:
            stats = hitl.get_stats()
            print(f"Total questions: {stats['total_questions']}")
            print(f"Acceptance rate: {stats['acceptance_rate']:.1%}")
        """
        if not self.conn:
            return {
                "total_questions": 0,
                "by_status": {},
                "acceptance_rate": 0.0,
            }

        cursor = self.conn.cursor()

        # Total questions
        cursor.execute("SELECT COUNT(*) as count FROM hitl_questions")
        total = cursor.fetchone()["count"]

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM hitl_questions
            GROUP BY status
        """)
        by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Calculate acceptance rate
        cursor.execute("""
            SELECT response, COUNT(*) as count
            FROM hitl_questions
            WHERE status = 'answered'
            GROUP BY response
        """)
        responses = {row["response"]: row["count"] for row in cursor.fetchall()}

        yes_count = sum(
            count
            for answer, count in responses.items()
            if answer.lower() in ["yes", "y", "true", "1"]
        )
        total_answered = sum(responses.values())
        acceptance_rate = (
            yes_count / total_answered if total_answered > 0 else 0.0
        )

        return {
            "total_questions": total,
            "by_status": by_status,
            "acceptance_rate": round(acceptance_rate, 3),
        }

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        # Cancel all pending waiters
        for future in self._response_waiters.values():
            if not future.done():
                future.cancel()
        self._response_waiters.clear()

        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Synchronous context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous context manager exit."""
        self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
