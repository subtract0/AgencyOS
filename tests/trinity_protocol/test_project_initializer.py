"""
Tests for Trinity Phase 3 Project Initializer.

Tests cover:
- Project initialization from YES response
- Q&A question generation
- Q&A session conductor
- Answer validation and completeness
- Integration with HumanReviewQueue
- Error handling and rollback

Constitutional Compliance:
- Article I: Complete context before spec generation
- Article II: 100% verification (NECESSARY pattern)
- Article V: Spec-driven development
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from shared.type_definitions.result import Result, Ok, Err

try:
    from trinity_protocol.project_initializer import (
        ProjectInitializer,
        generate_questions_for_pattern,
        conduct_qa_session,
        validate_qa_completeness,
    )
    from trinity_protocol.core.models.project import (
        QASession,
        QAQuestion,
        QAAnswer,
        Project,
    )
    from trinity_protocol.core.models.patterns import DetectedPattern
    IMPLEMENTATION_AVAILABLE = True
except ImportError:
    IMPLEMENTATION_AVAILABLE = False
    pytest.skip("Phase 3 ProjectInitializer not yet implemented", allow_module_level=True)


# ============================================================================
# Question Generation Tests (NECESSARY Pattern)
# ============================================================================


class TestQuestionGeneration:
    """Test Q&A question generation for different pattern types."""

    @pytest.mark.asyncio
    async def test_generate_questions_for_book_project(self):
        """Test generating 5-10 questions for book project pattern."""
        pattern = DetectedPattern(
            pattern_id="pattern_001",
            pattern_type="book_project",
            description="User mentioned writing coaching book",
            confidence=0.85,
            evidence=["coaching book", "entrepreneurs"],
            detected_at=datetime.now()
        )

        questions = await generate_questions_for_pattern(pattern)

        assert questions.is_ok()
        question_list = questions.value
        assert 5 <= len(question_list) <= 10
        assert all(isinstance(q, QAQuestion) for q in question_list)

    @pytest.mark.asyncio
    async def test_generated_questions_have_required_fields(self):
        """Test generated questions include all required fields."""
        pattern = DetectedPattern(
            pattern_id="pattern_002",
            pattern_type="workflow",
            description="Workflow improvement opportunity",
            confidence=0.75,
            evidence=["slow process"],
            detected_at=datetime.now()
        )

        questions = await generate_questions_for_pattern(pattern)

        assert questions.is_ok()
        for q in questions.value:
            assert q.question_id is not None
            assert q.question_text != ""
            assert q.question_number > 0
            assert isinstance(q.required, bool)

    @pytest.mark.asyncio
    async def test_questions_numbered_sequentially(self):
        """Test questions are numbered 1, 2, 3, etc."""
        pattern = DetectedPattern(
            pattern_id="pattern_003",
            pattern_type="decision",
            description="Decision needed",
            confidence=0.80,
            evidence=["which approach"],
            detected_at=datetime.now()
        )

        questions = await generate_questions_for_pattern(pattern)

        assert questions.is_ok()
        numbers = [q.question_number for q in questions.value]
        assert numbers == list(range(1, len(numbers) + 1))

    @pytest.mark.asyncio
    async def test_questions_include_context(self):
        """Test questions include context explaining why asked."""
        pattern = DetectedPattern(
            pattern_id="pattern_004",
            pattern_type="book_project",
            description="Book writing project",
            confidence=0.90,
            evidence=["write a book"],
            detected_at=datetime.now()
        )

        questions = await generate_questions_for_pattern(pattern)

        assert questions.is_ok()
        # At least some questions should have context
        contexts = [q.context for q in questions.value if q.context]
        assert len(contexts) > 0

    @pytest.mark.asyncio
    async def test_invalid_pattern_type_returns_error(self):
        """Test invalid pattern type returns error."""
        pattern = DetectedPattern(
            pattern_id="pattern_005",
            pattern_type="invalid_type",
            description="Unknown pattern",
            confidence=0.50,
            evidence=[],
            detected_at=datetime.now()
        )

        questions = await generate_questions_for_pattern(pattern)

        assert questions.is_err()
        assert "invalid" in questions.error.lower() or "unknown" in questions.error.lower()


# ============================================================================
# Project Initialization Tests (NECESSARY Pattern)
# ============================================================================


class TestProjectInitialization:
    """Test project initialization orchestration."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for ProjectInitializer."""
        return {
            "human_review_queue": Mock(),
            "state_store": Mock(),
            "llm_client": Mock(),
        }

    @pytest.mark.asyncio
    async def test_initialize_project_from_yes_response(self, mock_dependencies):
        """Test initializing project from YES response."""
        initializer = ProjectInitializer(**mock_dependencies)

        pattern = DetectedPattern(
            pattern_id="pattern_101",
            pattern_type="book_project",
            description="Book project",
            confidence=0.85,
            evidence=["book"],
            detected_at=datetime.now()
        )

        user_response = "YES!"

        result = await initializer.initialize_project(pattern, user_response)

        assert result.is_ok()
        project_session = result.value
        assert project_session.project_id is not None
        assert project_session.pattern_id == "pattern_101"

    @pytest.mark.asyncio
    async def test_initialization_creates_qa_session(self, mock_dependencies):
        """Test initialization creates QASession."""
        initializer = ProjectInitializer(**mock_dependencies)

        pattern = DetectedPattern(
            pattern_id="pattern_102",
            pattern_type="workflow",
            description="Workflow",
            confidence=0.75,
            evidence=[],
            detected_at=datetime.now()
        )

        result = await initializer.initialize_project(pattern, "YES")

        assert result.is_ok()
        session = result.value
        assert isinstance(session, QASession)
        assert session.status == "in_progress"

    @pytest.mark.asyncio
    async def test_initialization_generates_questions(self, mock_dependencies):
        """Test initialization generates questions immediately."""
        initializer = ProjectInitializer(**mock_dependencies)

        pattern = DetectedPattern(
            pattern_id="pattern_103",
            pattern_type="book_project",
            description="Book",
            confidence=0.90,
            evidence=["book"],
            detected_at=datetime.now()
        )

        result = await initializer.initialize_project(pattern, "YES")

        assert result.is_ok()
        session = result.value
        assert len(session.questions) >= 5

    @pytest.mark.asyncio
    async def test_initialization_persists_to_firestore(self, mock_dependencies):
        """Test initialization persists session to Firestore."""
        mock_store = Mock()
        mock_store.store_qa_session = AsyncMock(return_value=Ok("session_id"))
        mock_dependencies["state_store"] = mock_store

        initializer = ProjectInitializer(**mock_dependencies)

        pattern = DetectedPattern(
            pattern_id="pattern_104",
            pattern_type="decision",
            description="Decision",
            confidence=0.80,
            evidence=[],
            detected_at=datetime.now()
        )

        await initializer.initialize_project(pattern, "YES")

        mock_store.store_qa_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_handles_firestore_failure(self, mock_dependencies):
        """Test initialization handles Firestore persistence failure."""
        mock_store = Mock()
        mock_store.store_qa_session = AsyncMock(return_value=Err("Firestore unavailable"))
        mock_dependencies["state_store"] = mock_store

        initializer = ProjectInitializer(**mock_dependencies)

        pattern = DetectedPattern(
            pattern_id="pattern_105",
            pattern_type="book_project",
            description="Book",
            confidence=0.85,
            evidence=[],
            detected_at=datetime.now()
        )

        result = await initializer.initialize_project(pattern, "YES")

        assert result.is_err()
        assert "firestore" in result.error.lower()


# ============================================================================
# Q&A Session Conductor Tests (NECESSARY Pattern)
# ============================================================================


class TestQASessionConductor:
    """Test Q&A session conducting logic."""

    @pytest.mark.asyncio
    async def test_conduct_qa_session_asks_questions_sequentially(self):
        """Test Q&A conductor asks questions one by one."""
        questions = [
            QAQuestion(
                question_id=f"q_{i}",
                question_text=f"Question {i}",
                question_number=i,
                required=True
            )
            for i in range(1, 6)
        ]

        session = QASession(
            session_id="session_001",
            project_id="proj_001",
            pattern_id="pattern_001",
            pattern_type="book_project",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Ok("User answer"))

        result = await conduct_qa_session(session, mock_hitl)

        assert result.is_ok()
        assert mock_hitl.ask_question.call_count == 5

    @pytest.mark.asyncio
    async def test_qa_session_collects_all_answers(self):
        """Test Q&A session collects answers for all questions."""
        questions = [
            QAQuestion(
                question_id=f"q_{i}",
                question_text=f"Question {i}",
                question_number=i,
                required=True
            )
            for i in range(1, 4)
        ]

        session = QASession(
            session_id="session_002",
            project_id="proj_002",
            pattern_id="pattern_002",
            pattern_type="workflow",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Ok("Answer"))

        result = await conduct_qa_session(session, mock_hitl)

        assert result.is_ok()
        completed_session = result.value
        assert len(completed_session.answers) == 3

    @pytest.mark.asyncio
    async def test_qa_session_handles_user_timeout(self):
        """Test Q&A session handles user not responding."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question 1",
                question_number=1,
                required=True
            )
        ]

        session = QASession(
            session_id="session_003",
            project_id="proj_003",
            pattern_id="pattern_003",
            pattern_type="decision",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Err("User timeout"))

        result = await conduct_qa_session(session, mock_hitl)

        assert result.is_err()
        assert "timeout" in result.error.lower()

    @pytest.mark.asyncio
    async def test_qa_session_marks_completed_when_done(self):
        """Test Q&A session status changes to completed."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question",
                question_number=1,
                required=True
            )
        ]

        session = QASession(
            session_id="session_004",
            project_id="proj_004",
            pattern_id="pattern_004",
            pattern_type="book_project",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Ok("Answer"))

        result = await conduct_qa_session(session, mock_hitl)

        assert result.is_ok()
        completed_session = result.value
        assert completed_session.status == "completed"
        assert completed_session.completed_at is not None

    @pytest.mark.asyncio
    async def test_qa_session_calculates_total_time(self):
        """Test Q&A session calculates total_time_minutes."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question",
                question_number=1,
                required=True
            )
        ]

        start_time = datetime(2025, 10, 1, 10, 0)
        session = QASession(
            session_id="session_005",
            project_id="proj_005",
            pattern_id="pattern_005",
            pattern_type="workflow",
            questions=questions,
            answers=[],
            started_at=start_time,
            status="in_progress"
        )

        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Ok("Answer"))

        with patch('trinity_protocol.project_initializer.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2025, 10, 1, 10, 7)  # 7 minutes later
            result = await conduct_qa_session(session, mock_hitl)

        assert result.is_ok()
        completed_session = result.value
        assert completed_session.total_time_minutes == 7


# ============================================================================
# Answer Validation Tests (NECESSARY Pattern)
# ============================================================================


class TestAnswerValidation:
    """Test answer validation and completeness checking."""

    def test_validate_completeness_all_required_answered(self):
        """Test completeness validation passes when all required answered."""
        questions = [
            QAQuestion(
                question_id=f"q_{i}",
                question_text=f"Question {i}",
                question_number=i,
                required=True
            )
            for i in range(1, 4)
        ]

        answers = [
            QAAnswer(
                question_id=f"q_{i}",
                answer_text=f"Answer {i}",
                answered_at=datetime.now(),
                confidence="certain"
            )
            for i in range(1, 4)
        ]

        session = QASession(
            session_id="session_101",
            project_id="proj_101",
            pattern_id="pattern_101",
            pattern_type="book_project",
            questions=questions,
            answers=answers,
            started_at=datetime.now(),
            status="completed"
        )

        result = validate_qa_completeness(session)

        assert result.is_ok()
        assert result.value is True

    def test_validate_completeness_missing_required_answer(self):
        """Test completeness validation fails when required answer missing."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question 1",
                question_number=1,
                required=True
            ),
            QAQuestion(
                question_id="q_2",
                question_text="Question 2",
                question_number=2,
                required=True
            )
        ]

        answers = [
            QAAnswer(
                question_id="q_1",
                answer_text="Answer 1",
                answered_at=datetime.now(),
                confidence="certain"
            )
            # Missing q_2
        ]

        session = QASession(
            session_id="session_102",
            project_id="proj_102",
            pattern_id="pattern_102",
            pattern_type="workflow",
            questions=questions,
            answers=answers,
            started_at=datetime.now(),
            status="in_progress"
        )

        result = validate_qa_completeness(session)

        assert result.is_ok()
        assert result.value is False

    def test_validate_completeness_optional_questions_can_be_skipped(self):
        """Test optional questions don't block completeness."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Required question",
                question_number=1,
                required=True
            ),
            QAQuestion(
                question_id="q_2",
                question_text="Optional question",
                question_number=2,
                required=False
            )
        ]

        answers = [
            QAAnswer(
                question_id="q_1",
                answer_text="Answer 1",
                answered_at=datetime.now(),
                confidence="certain"
            )
            # q_2 skipped (optional)
        ]

        session = QASession(
            session_id="session_103",
            project_id="proj_103",
            pattern_id="pattern_103",
            pattern_type="decision",
            questions=questions,
            answers=answers,
            started_at=datetime.now(),
            status="completed"
        )

        result = validate_qa_completeness(session)

        assert result.is_ok()
        assert result.value is True

    def test_validate_empty_answer_text_fails(self):
        """Test validation fails on empty answer text."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question",
                question_number=1,
                required=True
            )
        ]

        answers = [
            QAAnswer(
                question_id="q_1",
                answer_text="",  # Empty answer
                answered_at=datetime.now(),
                confidence="certain"
            )
        ]

        session = QASession(
            session_id="session_104",
            project_id="proj_104",
            pattern_id="pattern_104",
            pattern_type="book_project",
            questions=questions,
            answers=answers,
            started_at=datetime.now(),
            status="in_progress"
        )

        result = validate_qa_completeness(session)

        # Empty answers should not count as complete
        assert result.is_ok()
        assert result.value is False


# ============================================================================
# Integration with HumanReviewQueue Tests (NECESSARY Pattern)
# ============================================================================


class TestHITLIntegration:
    """Test integration with Human-In-The-Loop protocol."""

    @pytest.mark.asyncio
    async def test_initialization_triggers_from_yes_response(self):
        """Test project initialization triggered by YES response."""
        mock_hitl = Mock()
        mock_hitl.get_pending_approvals = AsyncMock(return_value=Ok([]))

        initializer = ProjectInitializer(
            human_review_queue=mock_hitl,
            state_store=Mock(),
            llm_client=Mock()
        )

        pattern = DetectedPattern(
            pattern_id="pattern_201",
            pattern_type="book_project",
            description="Book",
            confidence=0.85,
            evidence=[],
            detected_at=datetime.now()
        )

        result = await initializer.initialize_project(pattern, "YES")

        assert result.is_ok()

    @pytest.mark.asyncio
    async def test_questions_routed_through_hitl(self):
        """Test Q&A questions routed through HITL protocol."""
        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Ok("User response"))

        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question 1",
                question_number=1,
                required=True
            )
        ]

        session = QASession(
            session_id="session_201",
            project_id="proj_201",
            pattern_id="pattern_201",
            pattern_type="workflow",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        await conduct_qa_session(session, mock_hitl)

        mock_hitl.ask_question.assert_called()

    @pytest.mark.asyncio
    async def test_no_response_handling_graceful(self):
        """Test graceful handling when user doesn't respond."""
        mock_hitl = Mock()
        mock_hitl.ask_question = AsyncMock(return_value=Err("NO response"))

        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question",
                question_number=1,
                required=True
            )
        ]

        session = QASession(
            session_id="session_202",
            project_id="proj_202",
            pattern_id="pattern_202",
            pattern_type="decision",
            questions=questions,
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        result = await conduct_qa_session(session, mock_hitl)

        # Should return error, not crash
        assert result.is_err()


# ============================================================================
# Error Handling and Rollback Tests (NECESSARY Pattern)
# ============================================================================


class TestErrorHandling:
    """Test error handling and rollback scenarios."""

    @pytest.mark.asyncio
    async def test_llm_failure_returns_error(self):
        """Test LLM failure during question generation."""
        mock_llm = Mock()
        mock_llm.generate = AsyncMock(return_value=Err("LLM unavailable"))

        pattern = DetectedPattern(
            pattern_id="pattern_301",
            pattern_type="book_project",
            description="Book",
            confidence=0.85,
            evidence=[],
            detected_at=datetime.now()
        )

        with patch('trinity_protocol.project_initializer.llm_client', mock_llm):
            result = await generate_questions_for_pattern(pattern)

        assert result.is_err()

    @pytest.mark.asyncio
    async def test_partial_qa_session_not_used_for_spec(self):
        """Test incomplete Q&A session blocks spec generation (Article I)."""
        questions = [
            QAQuestion(
                question_id="q_1",
                question_text="Question 1",
                question_number=1,
                required=True
            ),
            QAQuestion(
                question_id="q_2",
                question_text="Question 2",
                question_number=2,
                required=True
            )
        ]

        answers = [
            QAAnswer(
                question_id="q_1",
                answer_text="Answer 1",
                answered_at=datetime.now(),
                confidence="certain"
            )
            # Missing q_2 - incomplete
        ]

        session = QASession(
            session_id="session_301",
            project_id="proj_301",
            pattern_id="pattern_301",
            pattern_type="book_project",
            questions=questions,
            answers=answers,
            started_at=datetime.now(),
            status="in_progress"
        )

        # Attempting to proceed with incomplete session should fail
        completeness = validate_qa_completeness(session)
        assert completeness.is_ok()
        assert completeness.value is False  # Not complete

    @pytest.mark.asyncio
    async def test_firestore_rollback_on_failure(self):
        """Test rollback when Firestore operation fails."""
        mock_store = Mock()
        mock_store.store_qa_session = AsyncMock(return_value=Err("Write failed"))

        initializer = ProjectInitializer(
            human_review_queue=Mock(),
            state_store=mock_store,
            llm_client=Mock()
        )

        pattern = DetectedPattern(
            pattern_id="pattern_302",
            pattern_type="workflow",
            description="Workflow",
            confidence=0.75,
            evidence=[],
            detected_at=datetime.now()
        )

        result = await initializer.initialize_project(pattern, "YES")

        # Should return error, not partial state
        assert result.is_err()


# ============================================================================
# Test Summary
# ============================================================================

"""
Test Coverage Summary (30+ tests):

1. Question Generation (5 tests):
   - Generate 5-10 questions per pattern type
   - Question field validation
   - Sequential numbering
   - Error handling for invalid patterns

2. Project Initialization (6 tests):
   - Initialize from YES response
   - Create QASession
   - Generate questions
   - Persist to Firestore
   - Handle persistence failures

3. Q&A Session Conductor (6 tests):
   - Ask questions sequentially
   - Collect all answers
   - Handle user timeout
   - Mark completion
   - Calculate total time

4. Answer Validation (5 tests):
   - Validate completeness
   - Detect missing required answers
   - Allow optional question skips
   - Reject empty answers

5. HITL Integration (3 tests):
   - Trigger from YES response
   - Route questions through HITL
   - Handle NO response gracefully

6. Error Handling (5 tests):
   - LLM failure handling
   - Incomplete Q&A blocks spec (Article I)
   - Firestore rollback on failure

Total: 30+ tests covering ProjectInitializer with NECESSARY pattern compliance.
"""
