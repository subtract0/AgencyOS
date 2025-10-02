"""
Tests for Trinity Protocol Human Review Queue

NECESSARY Pattern Compliance:
- Named: Clear test names describing HITL behavior
- Executable: Run independently with async support
- Comprehensive: Cover submission, retrieval, expiry, priority
- Error-validated: Test timeout and invalid input conditions
- State-verified: Assert queue states and message flow
- Side-effects controlled: Clean temp databases
- Assertions meaningful: Specific HITL checks
- Repeatable: Deterministic async results
- Yield fast: <1s per async test
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.human_review_queue import HumanReviewQueue
from trinity_protocol.core.models.hitl import HumanReviewRequest, HumanResponse
from trinity_protocol.core.models.patterns import DetectedPattern, PatternType


@pytest.fixture
def temp_db():
    """Provide temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_hitl.db"


@pytest.fixture
def temp_msg_bus_db():
    """Provide temporary message bus database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_msg_bus.db"


@pytest.fixture
async def message_bus(temp_msg_bus_db):
    """Provide message bus instance with isolated database."""
    bus = MessageBus(db_path=str(temp_msg_bus_db))
    yield bus
    bus.close()


@pytest.fixture
def sample_pattern():
    """Provide sample detected pattern."""
    return DetectedPattern(
        pattern_id="test-pattern-123",
        pattern_type=PatternType.RECURRING_TOPIC,
        topic="Trinity Protocol improvements",
        confidence=0.85,
        mention_count=3,
        first_mention=datetime.now() - timedelta(hours=2),
        last_mention=datetime.now(),
        context_summary="Alex mentioned improving HITL system multiple times",
        keywords=["hitl", "questions", "proactive"],
        sentiment="positive",
        urgency="medium"
    )


@pytest.fixture
def sample_review_request(sample_pattern):
    """Provide sample human review request."""
    return HumanReviewRequest(
        correlation_id="corr-test-456",
        question_text="Would you like me to implement the HITL question system?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=7,
        expires_at=datetime.now() + timedelta(hours=24),
        suggested_action="Implement question delivery and response capture"
    )


class TestHumanReviewQueueInitialization:
    """Test human review queue initialization."""

    @pytest.mark.asyncio
    async def test_initializes_with_message_bus(self, message_bus):
        """Queue initializes with message bus connection."""
        queue = HumanReviewQueue(message_bus=message_bus)

        assert queue.message_bus is message_bus
        assert queue.queue_name == "human_review_queue"

    @pytest.mark.asyncio
    async def test_creates_questions_table(self, message_bus, temp_db):
        """Queue creates SQLite table for question metadata."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        assert queue.conn is not None

        cursor = queue.conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='questions'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "questions"

        queue.close()


class TestQuestionSubmission:
    """Test submitting questions to review queue."""

    @pytest.mark.asyncio
    async def test_submits_question_to_queue(self, message_bus, sample_review_request):
        """Queue publishes question to message bus."""
        queue = HumanReviewQueue(message_bus=message_bus)

        question_id = await queue.submit_question(sample_review_request)

        assert isinstance(question_id, int)
        assert question_id > 0

        # Verify in message bus
        pending = await message_bus.get_pending_count("human_review_queue")
        assert pending == 1

        queue.close()

    @pytest.mark.asyncio
    async def test_stores_question_metadata_in_database(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue stores question metadata for tracking."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        question_id = await queue.submit_question(sample_review_request)

        # Verify in SQLite
        cursor = queue.conn.cursor()
        cursor.execute("""
            SELECT correlation_id, question_text, status, priority
            FROM questions WHERE id = ?
        """, (question_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row['correlation_id'] == "corr-test-456"
        assert "HITL question system" in row['question_text']
        assert row['status'] == "pending"
        assert row['priority'] == 7

        queue.close()

    @pytest.mark.asyncio
    async def test_respects_priority_ordering(self, message_bus, sample_pattern):
        """Queue submits high priority questions first."""
        queue = HumanReviewQueue(message_bus=message_bus)

        # Submit low priority
        low_priority = HumanReviewRequest(
            correlation_id="low",
            question_text="Low priority question?",
            question_type="low_stakes",
            pattern_context=sample_pattern,
            priority=2,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        await queue.submit_question(low_priority)

        # Submit high priority
        high_priority = HumanReviewRequest(
            correlation_id="high",
            question_text="High priority question?",
            question_type="high_value",
            pattern_context=sample_pattern,
            priority=9,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        await queue.submit_question(high_priority)

        # Retrieve should get high priority first
        questions = await queue.get_pending_questions(limit=2)

        assert len(questions) >= 1
        assert questions[0].priority == 9
        assert questions[0].correlation_id == "high"

        queue.close()

    @pytest.mark.asyncio
    async def test_sets_expiry_time_correctly(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue stores expiry time for timeout handling."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        question_id = await queue.submit_question(sample_review_request)

        cursor = queue.conn.cursor()
        cursor.execute("SELECT expires_at FROM questions WHERE id = ?", (question_id,))
        expires_at_str = cursor.fetchone()['expires_at']

        expires_at = datetime.fromisoformat(expires_at_str)
        time_diff = (expires_at - datetime.now()).total_seconds()

        # Should be approximately 24 hours (within 1 minute tolerance)
        assert 23.98 * 3600 <= time_diff <= 24.02 * 3600

        queue.close()


class TestQuestionRetrieval:
    """Test retrieving questions from queue."""

    @pytest.mark.asyncio
    async def test_retrieves_pending_questions(self, message_bus, temp_db, sample_review_request):
        """Queue returns pending questions in priority order."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        await queue.submit_question(sample_review_request)

        questions = await queue.get_pending_questions(limit=10)

        assert len(questions) == 1
        assert questions[0].correlation_id == "corr-test-456"
        assert questions[0].question_type == "high_value"

        queue.close()

    @pytest.mark.asyncio
    async def test_limits_results_correctly(self, message_bus, temp_db, sample_pattern):
        """Queue respects limit parameter."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        # Submit 5 questions (priority must be >= 1)
        for i in range(5):
            request = HumanReviewRequest(
                correlation_id=f"corr-{i}",
                question_text=f"Question {i}?",
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=i + 1,  # Priority 1-5
                expires_at=datetime.now() + timedelta(hours=24)
            )
            await queue.submit_question(request)

        # Get only 2
        questions = await queue.get_pending_questions(limit=2)

        assert len(questions) == 2

        queue.close()

    @pytest.mark.asyncio
    async def test_excludes_expired_questions(self, message_bus, temp_db, sample_pattern):
        """Queue does not return expired questions."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        # Submit expired question
        expired_request = HumanReviewRequest(
            correlation_id="expired",
            question_text="Expired question?",
            question_type="low_stakes",
            pattern_context=sample_pattern,
            priority=5,
            expires_at=datetime.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        await queue.submit_question(expired_request)

        # Submit valid question
        valid_request = HumanReviewRequest(
            correlation_id="valid",
            question_text="Valid question?",
            question_type="low_stakes",
            pattern_context=sample_pattern,
            priority=5,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        await queue.submit_question(valid_request)

        questions = await queue.get_pending_questions(limit=10)

        # Should only get valid question
        assert len(questions) == 1
        assert questions[0].correlation_id == "valid"

        queue.close()

    @pytest.mark.asyncio
    async def test_retrieves_question_by_correlation_id(
        self,
        message_bus,
        sample_review_request
    ):
        """Queue retrieves specific question by correlation ID."""
        queue = HumanReviewQueue(message_bus=message_bus)

        await queue.submit_question(sample_review_request)

        question = await queue.get_question_by_correlation("corr-test-456")

        assert question is not None
        assert question.correlation_id == "corr-test-456"
        assert question.priority == 7

        queue.close()

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_correlation(self, message_bus):
        """Queue returns None for non-existent correlation ID."""
        queue = HumanReviewQueue(message_bus=message_bus)

        question = await queue.get_question_by_correlation("nonexistent-123")

        assert question is None

        queue.close()


class TestQuestionStatusUpdates:
    """Test updating question status."""

    @pytest.mark.asyncio
    async def test_marks_question_as_answered(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue updates status to answered when response received."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="corr-test-456",
            response_type="YES",
            comment="Sounds great!",
            response_time_seconds=120.5
        )

        await queue.mark_answered(question_id, response)

        # Verify status updated
        cursor = queue.conn.cursor()
        cursor.execute("""
            SELECT status, response_type, answered_at
            FROM questions WHERE id = ?
        """, (question_id,))
        row = cursor.fetchone()

        assert row['status'] == "answered"
        assert row['response_type'] == "YES"
        assert row['answered_at'] is not None

        queue.close()

    @pytest.mark.asyncio
    async def test_marks_question_as_expired(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue marks expired questions automatically."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        question_id = await queue.submit_question(sample_review_request)

        # Manually set expiry to past
        cursor = queue.conn.cursor()
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            UPDATE questions SET expires_at = ? WHERE id = ?
        """, (past_time, question_id))
        queue.conn.commit()

        # Run expiry check
        expired_count = await queue.expire_old_questions()

        assert expired_count > 0

        # Verify status
        cursor.execute("SELECT status FROM questions WHERE id = ?", (question_id,))
        status = cursor.fetchone()['status']

        assert status == "expired"

        queue.close()

    @pytest.mark.asyncio
    async def test_does_not_expire_answered_questions(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue does not mark answered questions as expired."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        question_id = await queue.submit_question(sample_review_request)

        # Answer the question
        response = HumanResponse(
            correlation_id="corr-test-456",
            response_type="YES"
        )
        await queue.mark_answered(question_id, response)

        # Set expiry to past
        cursor = queue.conn.cursor()
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            UPDATE questions SET expires_at = ? WHERE id = ?
        """, (past_time, question_id))
        queue.conn.commit()

        # Run expiry check
        expired_count = await queue.expire_old_questions()

        # Should not expire answered questions
        cursor.execute("SELECT status FROM questions WHERE id = ?", (question_id,))
        status = cursor.fetchone()['status']

        assert status == "answered"  # Still answered, not expired

        queue.close()


class TestQueueStatistics:
    """Test queue statistics and monitoring."""

    @pytest.mark.asyncio
    async def test_returns_total_question_count(
        self,
        message_bus,
        temp_db,
        sample_pattern
    ):
        """Queue returns total number of questions."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        # Submit 3 questions
        for i in range(3):
            request = HumanReviewRequest(
                correlation_id=f"corr-{i}",
                question_text=f"Question {i}?",
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=5,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            await queue.submit_question(request)

        stats = queue.get_stats()

        assert stats['total_questions'] == 3

        queue.close()

    @pytest.mark.asyncio
    async def test_groups_questions_by_status(
        self,
        message_bus,
        sample_pattern
    ):
        """Queue groups questions by status."""
        queue = HumanReviewQueue(message_bus=message_bus)

        # Submit and answer one
        request1 = HumanReviewRequest(
            correlation_id="answered",
            question_text="Answered question?",
            question_type="low_stakes",
            pattern_context=sample_pattern,
            priority=5,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        q1_id = await queue.submit_question(request1)

        response = HumanResponse(correlation_id="answered", response_type="YES")
        await queue.mark_answered(q1_id, response)

        # Submit pending
        request2 = HumanReviewRequest(
            correlation_id="pending",
            question_text="Pending question?",
            question_type="low_stakes",
            pattern_context=sample_pattern,
            priority=5,
            expires_at=datetime.now() + timedelta(hours=24)
        )
        await queue.submit_question(request2)

        stats = queue.get_stats()

        assert 'by_status' in stats
        assert stats['by_status'].get('answered', 0) >= 1
        assert stats['by_status'].get('pending', 0) >= 1

        queue.close()

    @pytest.mark.asyncio
    async def test_calculates_acceptance_rate(
        self,
        message_bus,
        temp_db,
        sample_pattern
    ):
        """Queue calculates YES acceptance rate."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        # Submit 3 questions
        for i in range(3):
            request = HumanReviewRequest(
                correlation_id=f"q{i}",
                question_text=f"Question {i}?",
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=5,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            q_id = await queue.submit_question(request)

            # Answer: YES, NO, YES
            response_type = "YES" if i != 1 else "NO"
            response = HumanResponse(
                correlation_id=f"q{i}",
                response_type=response_type
            )
            await queue.mark_answered(q_id, response)

        stats = queue.get_stats()

        # 2 YES out of 3 answered = 66.7%
        assert 'acceptance_rate' in stats
        assert 0.66 <= stats['acceptance_rate'] <= 0.67

        queue.close()


class TestErrorHandling:
    """Test error conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_duplicate_correlation_ids(
        self,
        message_bus,
        temp_db,
        sample_review_request
    ):
        """Queue allows duplicate correlation IDs (resubmissions)."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        # Submit twice with same correlation ID
        id1 = await queue.submit_question(sample_review_request)
        id2 = await queue.submit_question(sample_review_request)

        # Both should succeed with different IDs
        assert id1 != id2

        questions = await queue.get_pending_questions(limit=10)
        assert len(questions) == 2

        queue.close()

    @pytest.mark.asyncio
    async def test_handles_empty_queue_gracefully(self, message_bus, temp_db):
        """Queue handles empty queue without errors."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_db))

        questions = await queue.get_pending_questions(limit=10)

        assert questions == []

        queue.close()

    @pytest.mark.asyncio
    async def test_validates_question_text_length(self, message_bus, sample_pattern):
        """Queue validates question text is not too short or long."""
        queue = HumanReviewQueue(message_bus=message_bus)

        # Too short (< 10 chars)
        with pytest.raises(ValueError):
            short_request = HumanReviewRequest(
                correlation_id="short",
                question_text="Short?",  # Only 6 chars
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=5,
                expires_at=datetime.now() + timedelta(hours=24)
            )

        # Too long (> 500 chars)
        with pytest.raises(ValueError):
            long_request = HumanReviewRequest(
                correlation_id="long",
                question_text="x" * 501,  # 501 chars
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=5,
                expires_at=datetime.now() + timedelta(hours=24)
            )

        queue.close()
