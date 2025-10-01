"""
Tests for Trinity Protocol Response Handler

Handles user responses (YES/NO/LATER) and routes them appropriately.

NECESSARY Pattern Compliance:
- Named: Clear test names describing response routing
- Executable: Run independently with async support
- Comprehensive: Cover all response types, routing logic, learning updates
- Error-validated: Test invalid responses and edge cases
- State-verified: Assert routing decisions and state changes
- Side-effects controlled: Clean temp databases
- Assertions meaningful: Specific routing checks
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
from trinity_protocol.response_handler import ResponseHandler
from trinity_protocol.models.hitl import HumanReviewRequest, HumanResponse
from trinity_protocol.models.patterns import DetectedPattern, PatternType


@pytest.fixture
def temp_msg_bus_db():
    """Provide temporary message bus database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_msg_bus.db"


@pytest.fixture
def temp_queue_db():
    """Provide temporary queue database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_queue.db"


@pytest.fixture
async def message_bus(temp_msg_bus_db):
    """Provide message bus instance."""
    bus = MessageBus(db_path=str(temp_msg_bus_db))
    yield bus
    bus.close()


@pytest.fixture
def sample_pattern():
    """Provide sample detected pattern."""
    return DetectedPattern(
        pattern_id="test-pattern-123",
        pattern_type=PatternType.RECURRING_TOPIC,
        topic="HITL improvements",
        confidence=0.85,
        mention_count=3,
        first_mention=datetime.now() - timedelta(hours=2),
        last_mention=datetime.now(),
        context_summary="User wants better question handling",
        keywords=["hitl", "questions"],
        sentiment="positive",
        urgency="medium"
    )


@pytest.fixture
def sample_review_request(sample_pattern):
    """Provide sample review request."""
    return HumanReviewRequest(
        correlation_id="test-corr-456",
        question_text="Should I implement the HITL response handler?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=7,
        expires_at=datetime.now() + timedelta(hours=24),
        suggested_action="Build response routing system"
    )


class TestResponseHandlerInitialization:
    """Test response handler initialization."""

    @pytest.mark.asyncio
    async def test_initializes_with_dependencies(self, message_bus, temp_queue_db):
        """Handler initializes with message bus and queue."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(
            message_bus=message_bus,
            review_queue=queue
        )

        assert handler.message_bus is message_bus
        assert handler.review_queue is queue
        assert handler.execution_queue_name == "execution_queue"

        queue.close()


class TestYESResponseRouting:
    """Test YES response routing to EXECUTOR."""

    @pytest.mark.asyncio
    async def test_routes_yes_to_execution_queue(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """YES responses publish task to execution_queue."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        # Submit question
        question_id = await queue.submit_question(sample_review_request)

        # Respond YES
        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="YES",
            comment="Sounds great!"
        )

        await handler.process_response(question_id, response)

        # Verify task in execution_queue
        pending = await message_bus.get_pending_count("execution_queue")
        assert pending == 1

        # Verify question marked as answered
        stats = queue.get_stats()
        assert stats['by_response'].get('YES', 0) == 1

        queue.close()

    @pytest.mark.asyncio
    async def test_yes_response_includes_context(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """YES responses include pattern context for EXECUTOR."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="YES"
        )

        await handler.process_response(question_id, response)

        # Get published task from execution_queue
        async for msg in message_bus.subscribe("execution_queue"):
            # Verify it has pattern context
            assert 'pattern_context' in msg
            assert msg['correlation_id'] == "test-corr-456"
            assert msg['approved'] is True
            break

        queue.close()

    @pytest.mark.asyncio
    async def test_yes_response_calculates_time(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """YES responses calculate response time for learning."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        # Simulate user took 60 seconds to respond
        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="YES",
            response_time_seconds=60.0
        )

        await handler.process_response(question_id, response)

        # Verify response time stored
        stats = queue.get_stats()
        assert stats['avg_response_time_seconds'] == 60.0

        queue.close()


class TestNOResponseHandling:
    """Test NO response handling (no execution, store for learning)."""

    @pytest.mark.asyncio
    async def test_no_response_does_not_execute(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """NO responses do NOT publish to execution_queue."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="NO",
            comment="Not now, too busy"
        )

        await handler.process_response(question_id, response)

        # Verify NO task in execution_queue
        pending = await message_bus.get_pending_count("execution_queue")
        assert pending == 0

        # Verify question marked as answered with NO
        stats = queue.get_stats()
        assert stats['by_response'].get('NO', 0) == 1

        queue.close()

    @pytest.mark.asyncio
    async def test_no_response_stores_for_learning(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """NO responses publish to learning telemetry."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="NO",
            comment="Wrong timing"
        )

        await handler.process_response(question_id, response)

        # Verify learning signal published
        pending = await message_bus.get_pending_count("telemetry_stream")
        assert pending == 1

        queue.close()


class TestLATERResponseHandling:
    """Test LATER response handling (remind me)."""

    @pytest.mark.asyncio
    async def test_later_response_does_not_execute_immediately(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """LATER responses do NOT execute immediately."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="LATER",
            comment="Ask me tomorrow"
        )

        await handler.process_response(question_id, response)

        # No execution
        pending = await message_bus.get_pending_count("execution_queue")
        assert pending == 0

        # Marked as LATER
        stats = queue.get_stats()
        assert stats['by_response'].get('LATER', 0) == 1

        queue.close()

    @pytest.mark.asyncio
    async def test_later_response_schedules_reminder(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """LATER responses schedule question resubmission."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(
            message_bus=message_bus,
            review_queue=queue,
            later_delay_hours=4  # Configurable delay
        )

        question_id = await queue.submit_question(sample_review_request)

        response = HumanResponse(
            correlation_id="test-corr-456",
            response_type="LATER"
        )

        await handler.process_response(question_id, response)

        # Verify reminder scheduled (would check a reminders queue in full implementation)
        # For now, verify telemetry event
        pending = await message_bus.get_pending_count("telemetry_stream")
        assert pending >= 1

        queue.close()


class TestErrorHandling:
    """Test error conditions and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_nonexistent_question_id(
        self,
        message_bus,
        temp_queue_db
    ):
        """Handler raises error for non-existent question ID."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        response = HumanResponse(
            correlation_id="nonexistent",
            response_type="YES"
        )

        with pytest.raises(ValueError, match="Question.*not found"):
            await handler.process_response(99999, response)

        queue.close()

    @pytest.mark.asyncio
    async def test_handles_mismatched_correlation_id(
        self,
        message_bus,
        temp_queue_db,
        sample_review_request
    ):
        """Handler validates correlation ID matches question."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        question_id = await queue.submit_question(sample_review_request)

        # Response with wrong correlation ID
        response = HumanResponse(
            correlation_id="wrong-correlation",
            response_type="YES"
        )

        with pytest.raises(ValueError, match="Correlation ID mismatch"):
            await handler.process_response(question_id, response)

        queue.close()


class TestResponseStatistics:
    """Test response tracking and statistics."""

    @pytest.mark.asyncio
    async def test_tracks_response_time_distribution(
        self,
        message_bus,
        temp_queue_db,
        sample_pattern
    ):
        """Handler tracks response time distribution."""
        queue = HumanReviewQueue(message_bus=message_bus, db_path=str(temp_queue_db))
        handler = ResponseHandler(message_bus=message_bus, review_queue=queue)

        # Submit and answer multiple questions
        response_times = [10.0, 30.0, 60.0]
        for i, rt in enumerate(response_times):
            request = HumanReviewRequest(
                correlation_id=f"q{i}",
                question_text=f"Question {i}?",
                question_type="low_stakes",
                pattern_context=sample_pattern,
                priority=5,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            q_id = await queue.submit_question(request)

            response = HumanResponse(
                correlation_id=f"q{i}",
                response_type="YES",
                response_time_seconds=rt
            )
            await handler.process_response(q_id, response)

        stats = queue.get_stats()

        # Average should be (10 + 30 + 60) / 3 = 33.33
        assert 33.0 <= stats['avg_response_time_seconds'] <= 34.0

        queue.close()
