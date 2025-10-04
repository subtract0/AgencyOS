"""
Unit tests for shared HITL Protocol.

Tests the generic human-in-the-loop protocol extracted from Trinity.
Tests all core functionality: asking questions, capturing responses,
approval workflows, queue management, and timeout handling.

Constitutional Compliance:
- Article I: Complete context - tests verify persistence
- Article II: Strict typing - Pydantic models validated
- Article V: TDD - tests written before implementation
"""

import asyncio
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from shared.hitl_protocol import (
    HITLConfig,
    HITLProtocol,
    HITLQuestion,
    HITLResponse,
)
from shared.message_bus import MessageBus


class TestHITLQuestion:
    """Test HITLQuestion model validation."""

    def test_creates_valid_question(self):
        """Should create valid question with all fields."""
        question = HITLQuestion(
            question_id="q1",
            question="Proceed with refactor?",
            context={"file": "test.py", "lines": "100"},
            options=["yes", "no", "later"],
            timeout_seconds=300,
        )

        assert question.question_id == "q1"
        assert question.question == "Proceed with refactor?"
        assert question.context == {"file": "test.py", "lines": "100"}
        assert question.options == ["yes", "no", "later"]
        assert question.timeout_seconds == 300

    def test_creates_question_with_defaults(self):
        """Should create question with default options and timeout."""
        question = HITLQuestion(
            question_id="q1",
            question="Proceed?",
            context={},
        )

        assert question.options == []
        assert question.timeout_seconds == 300  # Default 5 minutes

    def test_validates_question_id(self):
        """Should validate question_id is not empty."""
        with pytest.raises(ValueError):
            HITLQuestion(
                question_id="",
                question="Test?",
                context={},
            )

    def test_validates_question_text(self):
        """Should validate question text is not empty."""
        with pytest.raises(ValueError):
            HITLQuestion(
                question_id="q1",
                question="",
                context={},
            )


class TestHITLResponse:
    """Test HITLResponse model validation."""

    def test_creates_valid_response(self):
        """Should create valid response with all fields."""
        now = datetime.now()
        response = HITLResponse(
            question_id="q1",
            answer="yes",
            timestamp=now,
        )

        assert response.question_id == "q1"
        assert response.answer == "yes"
        assert response.timestamp == now

    def test_creates_response_with_default_timestamp(self):
        """Should create response with current timestamp by default."""
        response = HITLResponse(
            question_id="q1",
            answer="no",
        )

        assert response.question_id == "q1"
        assert response.answer == "no"
        assert isinstance(response.timestamp, datetime)


class TestHITLConfig:
    """Test HITLConfig model validation."""

    def test_creates_config_with_defaults(self):
        """Should create config with sensible defaults."""
        config = HITLConfig()

        assert config.queue_name == "hitl_questions"
        assert config.default_timeout_seconds == 300
        assert config.max_questions_per_hour == 10
        assert config.quiet_hours_start is None
        assert config.quiet_hours_end is None

    def test_creates_config_with_custom_values(self):
        """Should create config with custom values."""
        config = HITLConfig(
            queue_name="custom_queue",
            default_timeout_seconds=600,
            max_questions_per_hour=5,
            quiet_hours_start=22,
            quiet_hours_end=8,
        )

        assert config.queue_name == "custom_queue"
        assert config.default_timeout_seconds == 600
        assert config.max_questions_per_hour == 5
        assert config.quiet_hours_start == 22
        assert config.quiet_hours_end == 8


@pytest.fixture
def temp_db():
    """Temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_hitl_db():
    """Temporary HITL database for testing."""
    with tempfile.NamedTemporaryFile(suffix="_hitl.db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def message_bus(temp_db):
    """Message bus instance for testing."""
    bus = MessageBus(db_path=temp_db)
    yield bus
    bus.close()


@pytest.fixture
async def hitl_protocol(message_bus, temp_hitl_db):
    """HITLProtocol instance for testing."""
    protocol = HITLProtocol(message_bus=message_bus, db_path=temp_hitl_db)
    yield protocol
    protocol.close()


class TestHITLProtocolInitialization:
    """Test HITLProtocol initialization."""

    @pytest.mark.asyncio
    async def test_initializes_with_message_bus(self, message_bus):
        """Should initialize with message bus."""
        protocol = HITLProtocol(message_bus=message_bus)

        assert protocol.message_bus == message_bus
        assert protocol.config.queue_name == "hitl_questions"

        protocol.close()

    @pytest.mark.asyncio
    async def test_initializes_with_custom_config(self, message_bus):
        """Should initialize with custom config."""
        config = HITLConfig(queue_name="custom_queue")
        protocol = HITLProtocol(message_bus=message_bus, config=config)

        assert protocol.config.queue_name == "custom_queue"

        protocol.close()

    @pytest.mark.asyncio
    async def test_initializes_database_schema(self, message_bus):
        """Should initialize database schema on creation."""
        protocol = HITLProtocol(message_bus=message_bus)

        # Verify table exists
        cursor = protocol.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='hitl_questions'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "hitl_questions"

        protocol.close()


class TestHITLProtocolAsk:
    """Test synchronous ask() method."""

    @pytest.mark.asyncio
    async def test_ask_returns_error_not_implemented(self, hitl_protocol):
        """Should return error for synchronous ask (not implemented in MVP)."""
        result = hitl_protocol.ask(
            question="Proceed with refactor?",
            context={"file": "test.py"},
            options=["yes", "no"],
        )

        assert result.is_err()
        assert "not implemented" in str(result.unwrap_err()).lower()


class TestHITLProtocolAskAsync:
    """Test asynchronous ask_async() method."""

    @pytest.mark.asyncio
    async def test_ask_async_creates_question(self, hitl_protocol):
        """Should create question and return question_id."""
        result = await hitl_protocol.ask_async(
            question="Proceed with refactor?",
            context={"file": "test.py"},
            options=["yes", "no"],
        )

        assert result.is_ok()
        question_id = result.unwrap()
        assert isinstance(question_id, str)
        assert len(question_id) > 0

    @pytest.mark.asyncio
    async def test_ask_async_stores_in_database(self, hitl_protocol):
        """Should store question in database."""
        result = await hitl_protocol.ask_async(
            question="Proceed with refactor?",
            context={"file": "test.py"},
        )

        assert result.is_ok()
        question_id = result.unwrap()

        # Verify in database
        cursor = hitl_protocol.conn.cursor()
        cursor.execute(
            "SELECT * FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row is not None
        assert row["question_text"] == "Proceed with refactor?"
        assert row["status"] == "pending"

    @pytest.mark.asyncio
    async def test_ask_async_publishes_to_message_bus(self, hitl_protocol):
        """Should publish question to message bus."""
        result = await hitl_protocol.ask_async(
            question="Proceed with refactor?",
            context={"file": "test.py"},
        )

        assert result.is_ok()

        # Check message bus
        pending_count = await hitl_protocol.message_bus.get_pending_count("hitl_questions")
        assert pending_count == 1

    @pytest.mark.asyncio
    async def test_ask_async_uses_custom_timeout(self, hitl_protocol):
        """Should use custom timeout when provided."""
        result = await hitl_protocol.ask_async(
            question="Proceed?",
            context={},
            timeout_seconds=600,
        )

        assert result.is_ok()
        question_id = result.unwrap()

        # Verify timeout in database
        cursor = hitl_protocol.conn.cursor()
        cursor.execute(
            "SELECT timeout_seconds FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row["timeout_seconds"] == 600

    @pytest.mark.asyncio
    async def test_ask_async_validates_question_text(self, hitl_protocol):
        """Should validate question text is not empty."""
        result = await hitl_protocol.ask_async(
            question="",
            context={},
        )

        assert result.is_err()
        assert "question" in str(result.unwrap_err()).lower()


class TestHITLProtocolWaitResponse:
    """Test wait_response() method."""

    @pytest.mark.asyncio
    async def test_wait_response_returns_submitted_response(self, hitl_protocol):
        """Should return response after it's submitted."""
        # Create question
        result = await hitl_protocol.ask_async(
            question="Proceed?",
            context={},
        )
        question_id = result.unwrap()

        # Submit response in background
        async def submit_after_delay():
            await asyncio.sleep(0.1)
            await hitl_protocol.submit_response(question_id, "yes")

        asyncio.create_task(submit_after_delay())

        # Wait for response
        result = await hitl_protocol.wait_response(question_id, timeout=2)

        assert result.is_ok()
        response = result.unwrap()
        assert response.question_id == question_id
        assert response.answer == "yes"

    @pytest.mark.asyncio
    async def test_wait_response_returns_error_on_timeout(self, hitl_protocol):
        """Should return error if timeout expires."""
        # Create question
        result = await hitl_protocol.ask_async(
            question="Proceed?",
            context={},
        )
        question_id = result.unwrap()

        # Wait for response with short timeout
        result = await hitl_protocol.wait_response(question_id, timeout=0.1)

        assert result.is_err()
        assert "timeout" in str(result.unwrap_err()).lower()

    @pytest.mark.asyncio
    async def test_wait_response_returns_error_for_invalid_question_id(self, hitl_protocol):
        """Should return error for invalid question_id."""
        result = await hitl_protocol.wait_response("invalid_id", timeout=1)

        assert result.is_err()
        assert "not found" in str(result.unwrap_err()).lower()


class TestHITLProtocolApprove:
    """Test approve() method (convenience wrapper)."""

    @pytest.mark.asyncio
    async def test_approve_creates_approval_question(self, hitl_protocol):
        """Should create approval question and wait for response."""

        # Submit response in background
        async def submit_approval():
            await asyncio.sleep(0.1)
            # Get pending questions
            pending = await hitl_protocol.get_pending()
            assert pending.is_ok()
            questions = pending.unwrap()
            if questions:
                await hitl_protocol.submit_response(questions[0].question_id, "yes")

        asyncio.create_task(submit_approval())

        # Request approval
        result = await hitl_protocol.approve(
            action="Refactor test.py",
            details={"file": "test.py", "lines": 100},
            timeout_seconds=2,
        )

        assert result.is_ok()
        assert result.unwrap() is True

    @pytest.mark.asyncio
    async def test_approve_returns_false_for_no_response(self, hitl_protocol):
        """Should return False if user responds with 'no'."""

        # Submit rejection in background
        async def submit_rejection():
            await asyncio.sleep(0.1)
            pending = await hitl_protocol.get_pending()
            questions = pending.unwrap()
            if questions:
                await hitl_protocol.submit_response(questions[0].question_id, "no")

        asyncio.create_task(submit_rejection())

        # Request approval
        result = await hitl_protocol.approve(
            action="Refactor test.py",
            details={"file": "test.py"},
            timeout_seconds=2,
        )

        assert result.is_ok()
        assert result.unwrap() is False

    @pytest.mark.asyncio
    async def test_approve_returns_error_on_timeout(self, hitl_protocol):
        """Should return error if approval times out."""
        result = await hitl_protocol.approve(
            action="Refactor test.py",
            details={"file": "test.py"},
            timeout_seconds=0.1,
        )

        assert result.is_err()
        assert "timeout" in str(result.unwrap_err()).lower()


class TestHITLProtocolGetPending:
    """Test get_pending() method."""

    @pytest.mark.asyncio
    async def test_get_pending_returns_empty_list_initially(self, hitl_protocol):
        """Should return empty list when no questions pending."""
        result = await hitl_protocol.get_pending()

        assert result.is_ok()
        assert result.unwrap() == []

    @pytest.mark.asyncio
    async def test_get_pending_returns_pending_questions(self, hitl_protocol):
        """Should return list of pending questions."""
        # Create multiple questions
        await hitl_protocol.ask_async("Question 1?", {})
        await hitl_protocol.ask_async("Question 2?", {})
        await hitl_protocol.ask_async("Question 3?", {})

        result = await hitl_protocol.get_pending()

        assert result.is_ok()
        questions = result.unwrap()
        assert len(questions) == 3
        assert all(isinstance(q, HITLQuestion) for q in questions)

    @pytest.mark.asyncio
    async def test_get_pending_excludes_answered_questions(self, hitl_protocol):
        """Should exclude answered questions from pending list."""
        # Create questions
        result1 = await hitl_protocol.ask_async("Question 1?", {})
        result2 = await hitl_protocol.ask_async("Question 2?", {})

        # Answer first question
        await hitl_protocol.submit_response(result1.unwrap(), "yes")

        # Get pending
        result = await hitl_protocol.get_pending()

        assert result.is_ok()
        questions = result.unwrap()
        assert len(questions) == 1
        assert questions[0].question == "Question 2?"

    @pytest.mark.asyncio
    async def test_get_pending_respects_limit(self, hitl_protocol):
        """Should respect limit parameter."""
        # Create multiple questions
        for i in range(5):
            await hitl_protocol.ask_async(f"Question {i}?", {})

        result = await hitl_protocol.get_pending(limit=2)

        assert result.is_ok()
        questions = result.unwrap()
        assert len(questions) == 2


class TestHITLProtocolSubmitResponse:
    """Test submit_response() method."""

    @pytest.mark.asyncio
    async def test_submit_response_marks_question_answered(self, hitl_protocol):
        """Should mark question as answered in database."""
        # Create question
        result = await hitl_protocol.ask_async("Proceed?", {})
        question_id = result.unwrap()

        # Submit response
        result = await hitl_protocol.submit_response(question_id, "yes")

        assert result.is_ok()

        # Verify in database
        cursor = hitl_protocol.conn.cursor()
        cursor.execute(
            "SELECT status, response FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row["status"] == "answered"
        assert row["response"] == "yes"

    @pytest.mark.asyncio
    async def test_submit_response_returns_error_for_invalid_question_id(self, hitl_protocol):
        """Should return error for invalid question_id."""
        result = await hitl_protocol.submit_response("invalid_id", "yes")

        assert result.is_err()
        assert "not found" in str(result.unwrap_err()).lower()

    @pytest.mark.asyncio
    async def test_submit_response_validates_answer(self, hitl_protocol):
        """Should validate answer is not empty."""
        # Create question
        result = await hitl_protocol.ask_async("Proceed?", {})
        question_id = result.unwrap()

        # Submit empty answer
        result = await hitl_protocol.submit_response(question_id, "")

        assert result.is_err()
        assert "answer" in str(result.unwrap_err()).lower()


class TestHITLProtocolExpireOld:
    """Test expire_old_questions() method."""

    @pytest.mark.asyncio
    async def test_expire_old_marks_expired_questions(self, hitl_protocol):
        """Should mark expired questions as expired."""
        # Manually insert question with past expiration time
        # (can't use asyncio.sleep as pytest-asyncio doesn't actually sleep)
        import json
        import uuid
        from datetime import datetime

        question_id = str(uuid.uuid4())
        now = datetime.now()
        past_time = now - timedelta(hours=1)  # Expired 1 hour ago

        cursor = hitl_protocol.conn.cursor()
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
                "Old question?",
                json.dumps({}),
                json.dumps([]),
                3600,
                past_time.isoformat(),
                past_time.isoformat(),  # Already expired
            ),
        )
        hitl_protocol.conn.commit()

        # Verify question was created
        cursor.execute(
            "SELECT question_id, status, expires_at FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()
        assert row is not None, "Question was not created in database"
        assert row["status"] == "pending"

        # Expire old questions
        result = await hitl_protocol.expire_old_questions()

        assert result.is_ok()
        expired_count = result.unwrap()
        assert expired_count >= 1, f"Expected at least 1 expired question, got {expired_count}"

        # Verify in database
        cursor.execute(
            "SELECT status FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row["status"] == "expired"

    @pytest.mark.asyncio
    async def test_expire_old_does_not_affect_valid_questions(self, hitl_protocol):
        """Should not expire questions within timeout window."""
        # Create question with long timeout
        result = await hitl_protocol.ask_async(
            question="Proceed?",
            context={},
            timeout_seconds=3600,  # 1 hour
        )
        question_id = result.unwrap()

        # Expire old questions
        await hitl_protocol.expire_old_questions()

        # Verify still pending
        cursor = hitl_protocol.conn.cursor()
        cursor.execute(
            "SELECT status FROM hitl_questions WHERE question_id = ?",
            (question_id,),
        )
        row = cursor.fetchone()

        assert row["status"] == "pending"


class TestHITLProtocolGetStats:
    """Test get_stats() method."""

    @pytest.mark.asyncio
    async def test_get_stats_returns_empty_stats_initially(self, hitl_protocol):
        """Should return empty stats when no questions."""
        stats = hitl_protocol.get_stats()

        assert stats["total_questions"] == 0
        assert stats["by_status"] == {}

    @pytest.mark.asyncio
    async def test_get_stats_returns_question_counts(self, hitl_protocol):
        """Should return question counts by status."""
        # Create questions
        r1 = await hitl_protocol.ask_async("Q1?", {})
        r2 = await hitl_protocol.ask_async("Q2?", {})
        r3 = await hitl_protocol.ask_async("Q3?", {})

        # Answer some
        await hitl_protocol.submit_response(r1.unwrap(), "yes")
        await hitl_protocol.submit_response(r2.unwrap(), "no")

        stats = hitl_protocol.get_stats()

        assert stats["total_questions"] == 3
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["answered"] == 2

    @pytest.mark.asyncio
    async def test_get_stats_calculates_acceptance_rate(self, hitl_protocol):
        """Should calculate acceptance rate from responses."""
        # Create and answer questions
        r1 = await hitl_protocol.ask_async("Q1?", {})
        r2 = await hitl_protocol.ask_async("Q2?", {})
        r3 = await hitl_protocol.ask_async("Q3?", {})

        await hitl_protocol.submit_response(r1.unwrap(), "yes")
        await hitl_protocol.submit_response(r2.unwrap(), "yes")
        await hitl_protocol.submit_response(r3.unwrap(), "no")

        stats = hitl_protocol.get_stats()

        # 2 yes out of 3 = 66.67%
        assert "acceptance_rate" in stats
        assert 0.6 <= stats["acceptance_rate"] <= 0.7


class TestHITLProtocolContextManager:
    """Test context manager protocol."""

    @pytest.mark.asyncio
    async def test_context_manager_closes_resources(self, message_bus):
        """Should close resources when exiting context."""
        with HITLProtocol(message_bus=message_bus) as protocol:
            assert protocol.conn is not None

        # After exiting, connection should be closed
        assert protocol.conn is None

    @pytest.mark.asyncio
    async def test_async_context_manager_closes_resources(self, message_bus):
        """Should close resources when exiting async context."""
        async with HITLProtocol(message_bus=message_bus) as protocol:
            assert protocol.conn is not None

        # After exiting, connection should be closed
        assert protocol.conn is None
