"""
Project Models for Trinity Protocol Phase 3.

Defines Pydantic models for project initialization, execution, and tracking.
Supports conversational project creation with formal specification generation.

Constitutional Compliance:
- Article II: Strict typing with Pydantic (zero Dict[Any, Any])
- Article V: Spec-driven development (formal specifications required)
- Article I: Complete context before action (all required fields validated)
- Privacy: User project data encrypted, full control over deletion
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class ProjectState(str, Enum):
    """Project lifecycle states."""
    INITIALIZING = "initializing"
    SPEC_REVIEW = "spec_review"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Individual task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class QuestionConfidence(str, Enum):
    """User confidence in Q&A answers."""
    CERTAIN = "certain"
    UNCERTAIN = "uncertain"
    NOT_SURE = "not_sure"


class ApprovalStatus(str, Enum):
    """Specification approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class QAQuestion(BaseModel):
    """
    Single question in project initialization Q&A session.

    Constitutional: Article I compliance (complete context via required field)
    """
    question_id: str = Field(
        ...,
        description="Unique identifier for this question"
    )
    question_text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Question text (10-500 chars)"
    )
    question_number: int = Field(
        ...,
        ge=1,
        le=10,
        description="Question number in sequence (1-10)"
    )
    required: bool = Field(
        ...,
        description="Is answer required before proceeding?"
    )
    context: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Why we're asking this question"
    )

    class Config:
        """Pydantic configuration."""
        frozen = True


class QAAnswer(BaseModel):
    """
    User's answer to Q&A question.

    Constitutional: Strict typing (no Any types)
    """
    question_id: str = Field(
        ...,
        description="Links answer to question"
    )
    answer_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's answer (1-2000 chars)"
    )
    answered_at: datetime = Field(
        default_factory=datetime.now,
        description="When user answered"
    )
    confidence: QuestionConfidence = Field(
        ...,
        description="User's confidence in answer"
    )

    class Config:
        """Pydantic configuration."""
        frozen = True


class QASession(BaseModel):
    """
    Complete Q&A session for project initialization.

    Constitutional: Article I (complete context - all required questions answered)
    """
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    project_id: str = Field(
        ...,
        description="Associated project ID"
    )
    pattern_id: str = Field(
        ...,
        description="Pattern that triggered initialization"
    )
    pattern_type: str = Field(
        ...,
        description="Type of pattern (book_project, workflow, etc.)"
    )
    questions: List[QAQuestion] = Field(
        ...,
        min_items=5,
        max_items=10,
        description="5-10 initialization questions"
    )
    answers: List[QAAnswer] = Field(
        default_factory=list,
        description="User's answers"
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="Session start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Session completion time"
    )
    status: Literal["in_progress", "completed", "abandoned"] = Field(
        default="in_progress",
        description="Session status"
    )
    total_time_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total time spent in session"
    )

    @property
    def is_complete(self) -> bool:
        """Check if all required questions have answers."""
        required_ids = {q.question_id for q in self.questions if q.required}
        answered_ids = {a.question_id for a in self.answers}
        return required_ids.issubset(answered_ids)

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class AcceptanceCriterion(BaseModel):
    """Single acceptance criterion for project success."""
    criterion_id: str = Field(..., description="Unique criterion ID")
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Verifiable criterion"
    )
    verification_method: str = Field(
        ...,
        max_length=200,
        description="How to verify completion"
    )
    met: bool = Field(default=False, description="Has criterion been met?")

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectSpec(BaseModel):
    """
    Formal project specification.

    Constitutional: Article V (spec-driven development requirement)
    """
    spec_id: str = Field(..., description="Unique specification ID")
    project_id: str = Field(..., description="Associated project ID")
    qa_session_id: str = Field(..., description="Source Q&A session")
    title: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Project title"
    )
    description: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Project description"
    )
    goals: List[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Project goals (1-10)"
    )
    non_goals: List[str] = Field(
        default_factory=list,
        max_items=10,
        description="Explicit non-goals"
    )
    user_personas: List[str] = Field(
        default_factory=list,
        max_items=5,
        description="User personas"
    )
    acceptance_criteria: List[AcceptanceCriterion] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="Success criteria (1-20)"
    )
    constraints: List[str] = Field(
        default_factory=list,
        max_items=10,
        description="Constraints and limitations"
    )
    spec_markdown: str = Field(
        ...,
        min_length=100,
        description="Full spec.md content"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Spec creation time"
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="Approval timestamp"
    )
    approval_status: ApprovalStatus = Field(
        default=ApprovalStatus.PENDING,
        description="Approval status"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True


class ProjectTask(BaseModel):
    """
    Single micro-task in project plan.

    Constitutional: Clear boundaries (<30 min estimated duration)
    """
    task_id: str = Field(..., description="Unique task ID")
    project_id: str = Field(..., description="Associated project")
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Task title"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Task description"
    )
    estimated_minutes: int = Field(
        ...,
        ge=1,
        le=60,
        description="Estimated duration (1-60 min)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Task IDs that must complete first"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        max_items=5,
        description="Task completion criteria"
    )
    assigned_to: Literal["user", "system"] = Field(
        ...,
        description="Who executes this task"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current status"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion timestamp"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True


class ProjectPlan(BaseModel):
    """
    Implementation plan with task breakdown.

    Constitutional: Article V (spec-driven planning)
    """
    plan_id: str = Field(..., description="Unique plan ID")
    project_id: str = Field(..., description="Associated project")
    spec_id: str = Field(..., description="Source specification")
    tasks: List[ProjectTask] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Project tasks (1-100)"
    )
    total_estimated_days: int = Field(
        ...,
        ge=1,
        le=60,
        description="Estimated duration in days"
    )
    daily_questions_avg: int = Field(
        ...,
        ge=1,
        le=3,
        description="Average questions per day"
    )
    timeline_start: datetime = Field(
        default_factory=datetime.now,
        description="Plan start date"
    )
    timeline_end_estimate: datetime = Field(
        ...,
        description="Estimated completion date"
    )
    plan_markdown: str = Field(
        ...,
        min_length=100,
        description="Full plan.md content"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Plan creation time"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class CheckinQuestion(BaseModel):
    """Question asked during daily check-in."""
    question_id: str = Field(..., description="Unique question ID")
    checkin_id: str = Field(..., description="Associated check-in")
    project_id: str = Field(..., description="Associated project")
    task_id: Optional[str] = Field(
        default=None,
        description="Related task if applicable"
    )
    question_text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Question text"
    )
    question_type: Literal["clarification", "decision", "feedback", "progress"] = Field(
        ...,
        description="Type of question"
    )
    asked_at: datetime = Field(
        default_factory=datetime.now,
        description="When asked"
    )

    class Config:
        """Pydantic configuration."""
        frozen = True


class CheckinResponse(BaseModel):
    """User's response to check-in question."""
    response_id: str = Field(..., description="Unique response ID")
    question_id: str = Field(..., description="Associated question")
    response_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's response"
    )
    responded_at: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        ...,
        description="Detected sentiment"
    )
    action_needed: bool = Field(
        default=False,
        description="Does response require action?"
    )

    class Config:
        """Pydantic configuration."""
        frozen = True


class DailyCheckin(BaseModel):
    """Complete daily check-in interaction."""
    checkin_id: str = Field(..., description="Unique check-in ID")
    project_id: str = Field(..., description="Associated project")
    checkin_date: datetime = Field(
        default_factory=datetime.now,
        description="Check-in date"
    )
    questions: List[CheckinQuestion] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Check-in questions (1-3)"
    )
    responses: List[CheckinResponse] = Field(
        default_factory=list,
        description="User responses"
    )
    total_time_minutes: int = Field(
        default=0,
        ge=0,
        le=30,
        description="Time spent (0-30 min)"
    )
    next_steps: str = Field(
        default="",
        max_length=500,
        description="What system will do next"
    )
    status: Literal["pending", "completed", "skipped"] = Field(
        default="pending",
        description="Check-in status"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ProjectMetadata(BaseModel):
    """Project metadata and settings."""
    topic: str = Field(..., description="Primary topic/category")
    estimated_completion: datetime = Field(
        ...,
        description="Estimated completion date"
    )
    daily_time_commitment_minutes: int = Field(
        ...,
        ge=5,
        le=60,
        description="Daily time commitment (5-60 min)"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Project priority (1-10)"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class Project(BaseModel):
    """
    Complete project entity.

    Constitutional: All articles compliance
    - Article I: Complete context (all required fields)
    - Article II: Strict typing (zero Dict[Any])
    - Article V: Spec-driven (spec required)
    """
    project_id: str = Field(..., description="Unique project ID")
    user_id: str = Field(..., description="Owner user ID")
    title: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Project title"
    )
    description: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Project description"
    )
    state: ProjectState = Field(
        default=ProjectState.INITIALIZING,
        description="Current project state"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    completion_date: Optional[datetime] = Field(
        default=None,
        description="Completion date if done"
    )
    metadata: ProjectMetadata = Field(
        ...,
        description="Project metadata"
    )

    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True


class ProjectOutcome(BaseModel):
    """
    Final project outcome for learning.

    Constitutional: Article IV (continuous learning)
    """
    project_id: str = Field(..., description="Associated project")
    completed: bool = Field(..., description="Successfully completed?")
    completion_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Completion percentage (0.0-1.0)"
    )
    total_time_minutes: int = Field(
        ...,
        ge=0,
        description="Total time invested"
    )
    total_checkins: int = Field(
        ...,
        ge=0,
        description="Number of check-ins conducted"
    )
    user_satisfaction: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="User satisfaction rating (1-5)"
    )
    deliverable_quality: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Deliverable quality rating (1-5)"
    )
    blockers_encountered: List[str] = Field(
        default_factory=list,
        max_items=20,
        description="Blockers encountered"
    )
    learnings: List[str] = Field(
        default_factory=list,
        max_items=20,
        description="Lessons learned"
    )
    would_recommend: Optional[bool] = Field(
        default=None,
        description="Would user recommend Trinity?"
    )

    class Config:
        """Pydantic configuration."""
        frozen = True
