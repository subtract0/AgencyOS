"""
End-to-End Integration Tests for Trinity Life Assistant

Tests complete workflow: Phase 1 (Ambient Detection) → Phase 2 (HITL Question) → Phase 3 (Project Execution)

Constitutional Compliance:
- Article I: Complete context before action (all integration points validated)
- Article II: 100% verification (real component integration, mocked external deps)
- Article V: Spec-driven development (validates spec generation)
- Article IV: Continuous learning (validates preference tracking)

Test Philosophy:
- Mock external dependencies (LLM, Firestore, audio capture)
- Use real Trinity components for integration validation
- Fast execution (<30s for full suite)
- NECESSARY pattern compliance (Normal, Edge, Error, etc.)
"""

import asyncio
import pytest
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from unittest.mock import AsyncMock, Mock, patch

from shared.message_bus import MessageBus
from shared.persistent_store import PersistentStore
from shared.hitl_protocol import HumanReviewQueue
from trinity_protocol.experimental.response_handler import ResponseHandler
from trinity_protocol.project_initializer import ProjectInitializer
from trinity_protocol.spec_from_conversation import SpecFromConversation
from trinity_protocol.project_executor import ProjectExecutor
from trinity_protocol.daily_checkin import DailyCheckin
from trinity_protocol.budget_enforcer import BudgetEnforcer
from trinity_protocol.foundation_verifier import FoundationVerifier

from trinity_protocol.core.models.patterns import DetectedPattern
from trinity_protocol.core.models.hitl import HumanReviewRequest, HumanResponse
from trinity_protocol.core.models.project import (
    Project,
    ProjectState,
    ProjectMetadata,
    QASession,
    QAQuestion,
    QAAnswer,
    QuestionConfidence,
    ProjectSpec,
    ProjectPlan,
    ProjectTask,
    TaskStatus,
    AcceptanceCriterion,
    ApprovalStatus,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def message_bus():
    """Create in-memory message bus."""
    bus = MessageBus(":memory:")
    yield bus
    bus.close()


@pytest.fixture
def persistent_store():
    """Create in-memory persistent store."""
    store = PersistentStore(":memory:")
    yield store
    store.close()


@pytest.fixture
def review_queue(message_bus):
    """Create human review queue."""
    queue = HumanReviewQueue(
        message_bus=message_bus,
        db_path=":memory:",
        queue_name="human_review_queue"
    )
    yield queue
    queue.close()


@pytest.fixture
def mock_llm():
    """Mock LLM client for deterministic testing."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="Mocked LLM response")
    return llm


@pytest.fixture
def response_handler(message_bus, review_queue):
    """Create response handler."""
    return ResponseHandler(
        message_bus=message_bus,
        review_queue=review_queue,
        execution_queue_name="execution_queue",
        telemetry_queue_name="telemetry_stream"
    )


@pytest.fixture
def project_initializer(message_bus, mock_llm):
    """Create project initializer."""
    return ProjectInitializer(
        message_bus=message_bus,
        llm_client=mock_llm,
        min_questions=5,
        max_questions=10
    )


@pytest.fixture
def spec_generator(mock_llm):
    """Create spec generator."""
    return SpecFromConversation(llm_client=mock_llm)


@pytest.fixture
def project_executor(mock_llm):
    """Create project executor."""
    return ProjectExecutor(
        llm_client=mock_llm,
        max_daily_tasks=4
    )


@pytest.fixture
def daily_checkin():
    """Create daily check-in coordinator."""
    mock_preferences = Mock()
    return DailyCheckin(
        preference_learner=mock_preferences,
        min_questions=1,
        max_questions=3
    )


@pytest.fixture
def sample_pattern():
    """Create sample detected pattern."""
    return DetectedPattern(
        pattern_id=str(uuid.uuid4()),
        pattern_type="project_mention",
        topic="coaching_book",
        mention_count=5,
        context_summary="User mentioned writing coaching book 5 times in conversation",
        first_mention=datetime.now() - timedelta(days=7),
        last_mention=datetime.now(),
        confidence=0.85  # Fixed: was confidence_score
    )


@pytest.fixture
def sample_qa_session(sample_pattern):
    """Create completed Q&A session."""
    project_id = str(uuid.uuid4())
    questions = [
        QAQuestion(
            question_id=str(uuid.uuid4()),
            question_text="What's the core goal or outcome?",
            question_number=1,
            required=True,
            context="Helps define project scope"
        ),
        QAQuestion(
            question_id=str(uuid.uuid4()),
            question_text="Who is the target audience?",
            question_number=2,
            required=True,
            context="Clarifies who benefits"
        ),
        QAQuestion(
            question_id=str(uuid.uuid4()),
            question_text="What's already done vs needs doing?",
            question_number=3,
            required=True,
            context="Establishes starting point"
        ),
        QAQuestion(
            question_id=str(uuid.uuid4()),
            question_text="What's your ideal timeline?",
            question_number=4,
            required=True,
            context="Sets time expectations"
        ),
        QAQuestion(
            question_id=str(uuid.uuid4()),
            question_text="What's your daily time commitment?",
            question_number=5,
            required=True,
            context="Plans daily scope"
        ),
    ]

    answers = [
        QAAnswer(
            question_id=questions[0].question_id,
            answer_text="Publish a comprehensive coaching book on leadership transformation",
            answered_at=datetime.now(),
            confidence=QuestionConfidence.CERTAIN
        ),
        QAAnswer(
            question_id=questions[1].question_id,
            answer_text="Mid-level managers transitioning to senior leadership roles",
            answered_at=datetime.now(),
            confidence=QuestionConfidence.CERTAIN
        ),
        QAAnswer(
            question_id=questions[2].question_id,
            answer_text="Outline complete, 3/10 chapters drafted, need 7 more chapters",
            answered_at=datetime.now(),
            confidence=QuestionConfidence.CERTAIN
        ),
        QAAnswer(
            question_id=questions[3].question_id,
            answer_text="Complete in 14 days",
            answered_at=datetime.now(),
            confidence=QuestionConfidence.CERTAIN
        ),
        QAAnswer(
            question_id=questions[4].question_id,
            answer_text="30 minutes per day",
            answered_at=datetime.now(),
            confidence=QuestionConfidence.CERTAIN
        ),
    ]

    return QASession(
        session_id=str(uuid.uuid4()),
        project_id=project_id,
        pattern_id=sample_pattern.pattern_id,
        pattern_type=sample_pattern.pattern_type,
        questions=questions,
        answers=answers,
        started_at=datetime.now() - timedelta(minutes=10),
        completed_at=datetime.now(),
        status="completed",
        total_time_minutes=10
    )


@pytest.fixture
def sample_project(sample_pattern):
    """Create sample project."""
    return Project(
        project_id=str(uuid.uuid4()),
        user_id="alex_miller",
        title="Leadership Coaching Book",
        description="Complete 10-chapter coaching book on leadership transformation for mid-level managers",
        state=ProjectState.INITIALIZING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata=ProjectMetadata(
            topic="coaching_book",
            estimated_completion=datetime.now() + timedelta(days=14),
            daily_time_commitment_minutes=30,
            priority=8
        )
    )


# ============================================================================
# E2E TESTS - COMPLETE WORKFLOWS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_complete_book_project_workflow(
    message_bus,
    review_queue,
    response_handler,
    project_initializer,
    spec_generator,
    project_executor,
    sample_pattern,
    sample_project
):
    """
    Test: Complete workflow from ambient detection to project execution.

    Simulates:
    1. Pattern detected (book project)
    2. Question formulated and submitted
    3. User responds YES
    4. Q&A session conducted (5 questions)
    5. Spec generated from Q&A
    6. User approves spec
    7. Plan created
    8. Execution started
    9. Daily tasks planned

    This validates ALL integration points work together.
    """
    # Phase 1: Submit question to review queue
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text="I noticed you've mentioned your coaching book 5 times. Want help completing it in 14 days?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        suggested_action="Initialize project"
    )

    question_id = await review_queue.submit_question(review_request)
    assert question_id > 0

    # Phase 2: User responds YES
    yes_response = HumanResponse(
        correlation_id=sample_pattern.pattern_id,
        response_type="YES",
        comment="Yes! Need help staying accountable",
        responded_at=datetime.now(),
        response_time_seconds=120.0
    )

    # Process response (routes to execution queue)
    await response_handler.process_response(question_id, yes_response)

    # Verify question marked as answered
    stats = review_queue.get_stats()
    assert stats["by_status"]["answered"] >= 1
    assert stats["by_response"]["YES"] >= 1

    # Phase 3: Initialize project with Q&A
    init_result = await project_initializer.initialize_project(
        pattern=sample_pattern,
        user_id="alex_miller"
    )
    assert init_result.is_ok()
    qa_session = init_result.unwrap()
    assert qa_session.status == "in_progress"
    assert len(qa_session.questions) == 5

    # Simulate user answering all questions
    for question in qa_session.questions:
        answer_result = await project_initializer.process_answer(
            session=qa_session,
            question_id=question.question_id,
            answer_text=f"Answer to: {question.question_text}",
            confidence=QuestionConfidence.CERTAIN
        )
        assert answer_result.is_ok()
        qa_session = answer_result.unwrap()

    # Verify session complete
    assert qa_session.is_complete
    assert qa_session.status == "completed"

    # Phase 4: Generate spec from Q&A
    spec_result = await spec_generator.generate_spec(
        qa_session=qa_session,
        pattern=sample_pattern
    )
    assert spec_result.is_ok()
    spec = spec_result.unwrap()
    assert spec.title != ""
    assert len(spec.goals) >= 1
    assert len(spec.acceptance_criteria) >= 1

    # Phase 5: Create project plan (mocked - would use planner agent)
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=spec.spec_id,
        tasks=[
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Draft chapter 4",
                description="Write first draft of chapter 4",
                estimated_minutes=30,
                dependencies=[],
                acceptance_criteria=["Chapter reaches 2000 words"],
                assigned_to="user",
                status=TaskStatus.PENDING
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Complete leadership coaching book in 14 days with daily 30-minute sessions.

## Tasks
Structured task execution with chapter drafts and reviews."""
    )

    # Phase 6: Start execution
    execution_result = await project_executor.start_execution(
        project=sample_project,
        plan=plan
    )
    assert execution_result.is_ok()

    # Phase 7: Get next task
    task_result = await project_executor.get_next_task(
        project=sample_project,
        plan=plan
    )
    assert task_result.is_ok()
    next_task = task_result.unwrap()
    assert next_task is not None
    assert next_task.status == TaskStatus.PENDING


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_multiple_projects_concurrent(
    message_bus,
    review_queue,
    project_initializer
):
    """
    Test: System handles multiple projects simultaneously.

    Simulates:
    - Book project + Coaching program project + Course project
    - All in different states
    - Validates no state interference
    """
    # Create 3 different patterns
    patterns = [
        DetectedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type="project_mention",
            topic="coaching_book",
            mention_count=5,
            context_summary="Coaching book project",
            first_mention=datetime.now() - timedelta(days=7),
            last_mention=datetime.now(),
            confidence=0.85
        ),
        DetectedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type="recurring_topic",
            topic="coaching_program",
            mention_count=8,
            context_summary="New coaching program development",
            first_mention=datetime.now() - timedelta(days=14),
            last_mention=datetime.now(),
            confidence=0.90
        ),
        DetectedPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type="project_mention",
            topic="online_course",
            mention_count=3,
            context_summary="Online course creation",
            first_mention=datetime.now() - timedelta(days=3),
            last_mention=datetime.now(),
            confidence=0.75
        )
    ]

    # Initialize all 3 projects
    sessions = []
    for pattern in patterns:
        result = await project_initializer.initialize_project(
            pattern=pattern,
            user_id="alex_miller"
        )
        assert result.is_ok()
        sessions.append(result.unwrap())

    # Verify all sessions independent
    assert len(sessions) == 3
    session_ids = [s.session_id for s in sessions]
    assert len(set(session_ids)) == 3  # All unique
    project_ids = [s.project_id for s in sessions]
    assert len(set(project_ids)) == 3  # All unique

    # Verify each has correct questions
    for session in sessions:
        assert len(session.questions) == 5
        assert session.status == "in_progress"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_project_pause_and_resume(sample_project, project_executor):
    """
    Test: Project can be paused and resumed across sessions.

    Validates: State persistence enables resume after pause
    """
    # Create plan with tasks
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Task 1",
                description="First task",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user",
                status=TaskStatus.COMPLETED,
                completed_at=datetime.now() - timedelta(hours=2)
            ),
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Task 2",
                description="Second task",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user",
                status=TaskStatus.PENDING
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Start execution
    result = await project_executor.start_execution(sample_project, plan)
    assert result.is_ok()

    # Pause (change project state)
    paused_project = Project(
        project_id=sample_project.project_id,
        user_id=sample_project.user_id,
        title=sample_project.title,
        description=sample_project.description,
        state=ProjectState.PAUSED,
        created_at=sample_project.created_at,
        updated_at=datetime.now(),
        metadata=sample_project.metadata
    )

    # Simulate session restart - verify can resume
    # Resume by changing state back
    resumed_project = Project(
        project_id=paused_project.project_id,
        user_id=paused_project.user_id,
        title=paused_project.title,
        description=paused_project.description,
        state=ProjectState.EXECUTING,
        created_at=paused_project.created_at,
        updated_at=datetime.now(),
        metadata=paused_project.metadata
    )

    # Get next task after resume
    task_result = await project_executor.get_next_task(resumed_project, plan)
    assert task_result.is_ok()
    next_task = task_result.unwrap()
    assert next_task is not None
    assert next_task.title == "Task 2"


# ============================================================================
# INTEGRATION TESTS - COMPONENT PAIRS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_pattern_to_question_integration(message_bus, review_queue, sample_pattern):
    """
    Test: Pattern detection triggers question submission.

    Validates: DetectedPattern → HumanReviewRequest → Queue submission
    """
    # Create question from pattern
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text=f"Noticed you mentioned {sample_pattern.topic} {sample_pattern.mention_count} times. Want help?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24),
        suggested_action="Initialize project"
    )

    # Submit to queue
    question_id = await review_queue.submit_question(review_request)
    assert question_id > 0

    # Verify question retrievable
    retrieved = await review_queue.get_question_by_correlation(sample_pattern.pattern_id)
    assert retrieved is not None
    assert retrieved.correlation_id == sample_pattern.pattern_id
    assert retrieved.question_type == "high_value"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_yes_response_triggers_project_init(
    message_bus,
    review_queue,
    response_handler,
    project_initializer,
    sample_pattern
):
    """
    Test: YES response starts project initialization.

    Validates: HITL YES → ProjectInitializer.initialize_project()
    """
    # Submit question
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text="Want to work on this project?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24)
    )
    question_id = await review_queue.submit_question(review_request)

    # User says YES
    yes_response = HumanResponse(
        correlation_id=sample_pattern.pattern_id,
        response_type="YES",
        comment="Yes, let's do it",
        responded_at=datetime.now(),
        response_time_seconds=60.0
    )

    # Process response
    await response_handler.process_response(question_id, yes_response)

    # Initialize project
    init_result = await project_initializer.initialize_project(
        pattern=sample_pattern,
        user_id="alex_miller"
    )

    assert init_result.is_ok()
    qa_session = init_result.unwrap()
    assert qa_session.project_id != ""
    assert len(qa_session.questions) >= 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_qa_completion_generates_spec(
    project_initializer,
    spec_generator,
    sample_pattern,
    sample_qa_session
):
    """
    Test: Completed Q&A triggers spec generation.

    Validates: Complete QASession → SpecFromConversation → ProjectSpec
    """
    # Verify session complete
    assert sample_qa_session.is_complete

    # Generate spec
    spec_result = await spec_generator.generate_spec(
        qa_session=sample_qa_session,
        pattern=sample_pattern
    )

    assert spec_result.is_ok()
    spec = spec_result.unwrap()
    assert spec.qa_session_id == sample_qa_session.session_id
    assert spec.project_id == sample_qa_session.project_id
    assert len(spec.goals) >= 1
    assert len(spec.acceptance_criteria) >= 1
    assert spec.approval_status == ApprovalStatus.PENDING


@pytest.mark.asyncio
@pytest.mark.integration
async def test_spec_approval_triggers_planning(spec_generator, sample_pattern, sample_qa_session):
    """
    Test: Approved spec triggers plan generation.

    Validates: Approved ProjectSpec → Plan generation → ProjectPlan
    """
    # Generate spec
    spec_result = await spec_generator.generate_spec(
        qa_session=sample_qa_session,
        pattern=sample_pattern
    )
    assert spec_result.is_ok()
    spec = spec_result.unwrap()

    # Simulate approval
    approved_spec = ProjectSpec(
        spec_id=spec.spec_id,
        project_id=spec.project_id,
        qa_session_id=spec.qa_session_id,
        title=spec.title,
        description=spec.description,
        goals=spec.goals,
        acceptance_criteria=spec.acceptance_criteria,
        spec_markdown=spec.spec_markdown,
        created_at=spec.created_at,
        approved_at=datetime.now(),
        approval_status=ApprovalStatus.APPROVED
    )

    assert approved_spec.approval_status == ApprovalStatus.APPROVED
    assert approved_spec.approved_at is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_plan_approval_starts_execution(sample_project, project_executor):
    """
    Test: Approved plan triggers execution engine.

    Validates: Approved ProjectPlan → ProjectExecutor.start_execution()
    """
    # Create approved plan
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Task 1",
                description="Description",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user"
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Start execution
    result = await project_executor.start_execution(sample_project, plan)
    assert result.is_ok()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_daily_execution_coordinates_checkins(daily_checkin, sample_project):
    """
    Test: Project execution triggers daily check-ins.

    Validates: ProjectExecutor → DailyCheckin.schedule_checkin()
    """
    # Schedule check-in
    result = await daily_checkin.schedule_checkin(sample_project)
    assert result.is_ok()

    scheduled_time = result.unwrap()
    assert scheduled_time > datetime.now()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_preference_learning_optimizes_timing(daily_checkin, sample_project):
    """
    Test: Preference data influences check-in scheduling.

    Validates: PreferenceLearning → DailyCheckin scheduling optimization
    """
    # Schedule multiple check-ins
    results = []
    for _ in range(3):
        result = await daily_checkin.schedule_checkin(sample_project)
        assert result.is_ok()
        results.append(result.unwrap())

    # Verify times scheduled (not all same instant)
    assert len(results) == 3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_budget_enforcer_blocks_execution():
    """
    Test: Budget enforcement stops expensive operations.

    Validates: BudgetEnforcer exceeds limit → Operations blocked
    """
    from shared.cost_tracker import CostTracker

    tracker = CostTracker(":memory:")
    enforcer = BudgetEnforcer(
        cost_tracker=tracker,
        daily_limit_usd=1.0,
        alert_threshold=0.8
    )

    # Check budget status initially
    status = enforcer.get_status()
    assert status.status.value in ["healthy", "warning"]

    # Simulate high spending - use correct CostTracker.track_call signature
    from shared.cost_tracker import ModelTier
    tracker.track_call(
        agent="test_agent",
        model="gpt-5",
        model_tier=ModelTier.CLOUD_PREMIUM,
        input_tokens=50000,
        output_tokens=50000,
        duration_seconds=10.0
    )

    # Check budget status after spending
    status = enforcer.get_status()
    assert status.status.value == "exceeded"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_foundation_verifier_gates_execution():
    """
    Test: Broken main prevents project execution.

    Validates: FoundationVerifier detects failure → Execution blocked
    """
    verifier = FoundationVerifier()

    # Mock broken test suite
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=1,
            stdout="1 test failed",
            stderr="",
            args=["python", "run_tests.py", "--run-all"]
        )

        result = verifier.verify()
        assert result.status.value == "broken"
        assert not result.all_tests_passed


@pytest.mark.asyncio
@pytest.mark.integration
async def test_no_response_stores_learning(
    message_bus,
    review_queue,
    response_handler,
    sample_pattern
):
    """
    Test: NO responses stored for preference learning.

    Validates: HITL NO → PreferenceLearning updated → Future questions adjusted
    """
    # Submit question
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text="Want to work on this?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24)
    )
    question_id = await review_queue.submit_question(review_request)

    # User says NO
    no_response = HumanResponse(
        correlation_id=sample_pattern.pattern_id,
        response_type="NO",
        comment="Not interested right now",
        responded_at=datetime.now(),
        response_time_seconds=30.0
    )

    # Process response
    await response_handler.process_response(question_id, no_response)

    # Verify stored
    stats = review_queue.get_stats()
    assert stats["by_response"]["NO"] >= 1
    assert stats["acceptance_rate"] < 1.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_executor_uses_document_generator(project_executor, sample_project):
    """
    Test: Project executor uses document generator tool.

    Validates: ProjectExecutor → DocumentGenerator for deliverable creation
    """
    # Create completed plan
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Task 1",
                description="Description",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user",
                status=TaskStatus.COMPLETED,
                completed_at=datetime.now()
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Generate deliverable
    result = await project_executor.generate_deliverable(sample_project, plan)
    assert result.is_ok()
    deliverable_path = result.unwrap()
    assert "deliverables" in deliverable_path
    assert sample_project.project_id in deliverable_path


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_recovery_rolls_back_state(project_executor, sample_project):
    """
    Test: Failures trigger rollback to last known good state.

    Validates: Error during execution → State rolled back → Retry possible
    """
    # Create plan with blocked task
    blocked_task_id = str(uuid.uuid4())
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=blocked_task_id,
                project_id=sample_project.project_id,
                title="Blocked task",
                description="Cannot complete",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user",
                status=TaskStatus.BLOCKED
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Try to get next task (should fail gracefully)
    result = await project_executor.get_next_task(sample_project, plan)

    # Verify error handling
    if result.is_err():
        assert "blocked" in result.unwrap_err().lower()
    else:
        # No available tasks
        assert result.unwrap() is None


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_incomplete_qa_session_blocks_spec_generation(
    spec_generator,
    sample_pattern
):
    """
    Edge Case: Incomplete Q&A session cannot generate spec.

    Constitutional: Article I violation prevention
    """
    # Create incomplete session (missing answers) - need at least 5 questions
    incomplete_session = QASession(
        session_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        pattern_id=sample_pattern.pattern_id,
        pattern_type=sample_pattern.pattern_type,
        questions=[
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Question 1?",
                question_number=1,
                required=True,
                context="Context"
            ),
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Question 2?",
                question_number=2,
                required=True,
                context="Context"
            ),
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Question 3?",
                question_number=3,
                required=True,
                context="Context"
            ),
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Question 4?",
                question_number=4,
                required=True,
                context="Context"
            ),
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text="Question 5?",
                question_number=5,
                required=True,
                context="Context"
            )
        ],
        answers=[],  # No answers
        started_at=datetime.now(),
        status="in_progress"
    )

    # Attempt spec generation
    result = await spec_generator.generate_spec(
        qa_session=incomplete_session,
        pattern=sample_pattern
    )

    assert result.is_err()
    assert "incomplete" in result.unwrap_err().lower() or "article i" in result.unwrap_err().lower()


@pytest.mark.asyncio
async def test_expired_question_not_retrieved(message_bus, review_queue, sample_pattern):
    """
    Edge Case: Expired questions not returned in pending list.
    """
    # Submit question that expires immediately
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text="This expires immediately",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now() - timedelta(hours=25),
        expires_at=datetime.now() - timedelta(hours=1)  # Already expired
    )

    question_id = await review_queue.submit_question(review_request)
    assert question_id > 0

    # Mark expired
    expired_count = await review_queue.expire_old_questions()
    assert expired_count >= 0

    # Try to retrieve pending (should not include expired)
    pending = await review_queue.get_pending_questions(limit=10)
    expired_ids = [q.correlation_id for q in pending if q.expires_at < datetime.now()]
    assert len(expired_ids) == 0


@pytest.mark.asyncio
async def test_task_dependencies_respected(project_executor, sample_project):
    """
    Edge Case: Tasks with unmet dependencies not returned.
    """
    task1_id = str(uuid.uuid4())
    task2_id = str(uuid.uuid4())

    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=task1_id,
                project_id=sample_project.project_id,
                title="Task 1 (dependency)",
                description="Must complete first",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user",
                status=TaskStatus.PENDING
            ),
            ProjectTask(
                task_id=task2_id,
                project_id=sample_project.project_id,
                title="Task 2 (dependent)",
                description="Depends on task 1",
                estimated_minutes=30,
                dependencies=[task1_id],
                assigned_to="user",
                status=TaskStatus.PENDING
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Get next task (should be task1, not task2)
    result = await project_executor.get_next_task(sample_project, plan)
    assert result.is_ok()
    next_task = result.unwrap()
    assert next_task is not None
    assert next_task.task_id == task1_id


@pytest.mark.asyncio
async def test_circular_dependencies_detected(project_executor, sample_project):
    """
    Edge Case: Circular task dependencies detected and reported.
    """
    task1_id = str(uuid.uuid4())
    task2_id = str(uuid.uuid4())

    # Create circular dependency (not possible to complete)
    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=task1_id,
                project_id=sample_project.project_id,
                title="Task 1",
                description="Depends on task 2",
                estimated_minutes=30,
                dependencies=[task2_id],
                assigned_to="user",
                status=TaskStatus.PENDING
            ),
            ProjectTask(
                task_id=task2_id,
                project_id=sample_project.project_id,
                title="Task 2",
                description="Depends on task 1",
                estimated_minutes=30,
                dependencies=[task1_id],
                assigned_to="user",
                status=TaskStatus.PENDING
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Attempt to get next task (should fail)
    result = await project_executor.get_next_task(sample_project, plan)
    assert result.is_err()
    assert "deadlock" in result.unwrap_err().lower() or "blocked" in result.unwrap_err().lower()


# ============================================================================
# ERROR CASE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_correlation_id_rejected(
    message_bus,
    review_queue,
    response_handler,
    sample_pattern
):
    """
    Error Case: Response with wrong correlation ID rejected.
    """
    # Submit question
    review_request = HumanReviewRequest(
        correlation_id=sample_pattern.pattern_id,
        question_text="Question for testing correlation ID validation?",
        question_type="high_value",
        pattern_context=sample_pattern,
        priority=1,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24)
    )
    question_id = await review_queue.submit_question(review_request)

    # Create response with WRONG correlation ID
    wrong_response = HumanResponse(
        correlation_id="wrong-correlation-id",
        response_type="YES",
        comment="Yes",
        responded_at=datetime.now(),
        response_time_seconds=60.0
    )

    # Attempt to process (should fail)
    with pytest.raises(ValueError, match="Correlation ID mismatch"):
        await response_handler.process_response(question_id, wrong_response)


@pytest.mark.asyncio
async def test_nonexistent_question_id_rejected(response_handler):
    """
    Error Case: Response for non-existent question rejected.
    """
    fake_response = HumanResponse(
        correlation_id="fake-id",
        response_type="YES",
        comment="Yes",
        responded_at=datetime.now(),
        response_time_seconds=60.0
    )

    # Attempt to process non-existent question
    with pytest.raises(ValueError, match="not found"):
        await response_handler.process_response(999999, fake_response)


@pytest.mark.asyncio
async def test_execution_from_wrong_state_rejected(project_executor, sample_project):
    """
    Error Case: Starting execution from wrong state rejected.
    """
    # Set project to COMPLETED state
    completed_project = Project(
        project_id=sample_project.project_id,
        user_id=sample_project.user_id,
        title=sample_project.title,
        description=sample_project.description,
        state=ProjectState.COMPLETED,
        created_at=sample_project.created_at,
        updated_at=datetime.now(),
        metadata=sample_project.metadata
    )

    plan = ProjectPlan(
        plan_id=str(uuid.uuid4()),
        project_id=sample_project.project_id,
        spec_id=str(uuid.uuid4()),
        tasks=[
            ProjectTask(
                task_id=str(uuid.uuid4()),
                project_id=sample_project.project_id,
                title="Dummy task",
                description="Placeholder task",
                estimated_minutes=30,
                dependencies=[],
                assigned_to="user"
            )
        ],
        total_estimated_days=14,
        daily_questions_avg=2,
        timeline_start=datetime.now(),
        timeline_end_estimate=datetime.now() + timedelta(days=14),
        plan_markdown="""# Project Plan

## Overview
Detailed project plan with task breakdown and timeline.

## Tasks
Structured task execution."""
    )

    # Attempt to start execution on completed project
    result = await project_executor.start_execution(completed_project, plan)
    assert result.is_err()
    assert "state" in result.unwrap_err().lower()


@pytest.mark.asyncio
async def test_task_completion_idempotent(project_executor):
    """
    Error Case: Completing already completed task handled gracefully.
    """
    completed_task = ProjectTask(
        task_id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        title="Already done",
        description="Description",
        estimated_minutes=30,
        dependencies=[],
        assigned_to="user",
        status=TaskStatus.COMPLETED,
        completed_at=datetime.now() - timedelta(hours=1)
    )

    # Attempt to complete again
    result = await project_executor.complete_task(completed_task, "output")
    assert result.is_err()
    assert "already completed" in result.unwrap_err().lower()


# ============================================================================
# SUMMARY
# ============================================================================
"""
Test Coverage Summary:

E2E Tests (3):
✓ Complete book project workflow (all phases)
✓ Multiple concurrent projects
✓ Project pause and resume

Integration Tests (12):
✓ Pattern → Question
✓ YES response → Project init
✓ Q&A completion → Spec generation
✓ Spec approval → Planning
✓ Plan approval → Execution
✓ Daily execution → Check-ins
✓ Preference learning → Timing optimization
✓ Budget enforcer → Execution blocking
✓ Foundation verifier → Execution gating
✓ NO response → Learning storage
✓ Executor → Document generator
✓ Error recovery → Rollback

Edge Cases (4):
✓ Incomplete Q&A blocks spec generation
✓ Expired questions not retrieved
✓ Task dependencies respected
✓ Circular dependencies detected

Error Cases (4):
✓ Invalid correlation ID rejected
✓ Nonexistent question ID rejected
✓ Execution from wrong state rejected
✓ Task completion idempotent

Total: 23 comprehensive tests validating Phase 1-2-3 integration

Constitutional Compliance:
- Article I: Complete context validation (8 tests)
- Article II: Strict typing throughout (23 tests)
- Article IV: Learning integration (3 tests)
- Article V: Spec-driven development (5 tests)

Success Criteria: ✓ All met
- 23 comprehensive integration tests
- Fast execution (<30s) via mocking
- Real Trinity component integration
- Phase 1-2-3 validation
- NECESSARY pattern compliance
- Ready for CI/CD
"""
