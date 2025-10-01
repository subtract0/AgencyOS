"""
Project Initializer for Trinity Protocol Phase 3.

Transforms YES responses into structured projects through conversational Q&A.
Orchestrates project creation from pattern detection to approved specification.

Constitutional Compliance:
- Article I: Complete context before action (all required questions answered)
- Article II: Strict typing with Result<T,E> pattern
- Article V: Spec-driven development (formal spec required)
- Article IV: Continuous learning from Q&A patterns

Flow:
1. Receive YES response from human_review_queue
2. Generate 5-10 contextual questions based on pattern type
3. Conduct Q&A session via HITL protocol
4. Validate completeness before spec generation
5. Trigger spec generation from conversation
6. Request user approval
7. Initialize project state in Firestore

Usage:
    initializer = ProjectInitializer(message_bus, llm_client, state_store)
    result = await initializer.initialize_project(pattern, user_id)
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.models.patterns import DetectedPattern
from trinity_protocol.models.project import (
    Project,
    ProjectState,
    ProjectMetadata,
    QAQuestion,
    QAAnswer,
    QASession,
    QuestionConfidence,
)
from shared.type_definitions.result import Result, Ok, Err


class InitializationError(Exception):
    """Project initialization error."""
    pass


class ProjectInitializer:
    """
    Orchestrates project initialization from YES response.

    Constitutional: Article I (complete context), Article V (spec-driven)
    """

    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        min_questions: int = 5,
        max_questions: int = 10
    ):
        """
        Initialize project initializer.

        Args:
            message_bus: Message bus for HITL communication
            llm_client: LLM for question generation
            min_questions: Minimum questions to ask (default: 5)
            max_questions: Maximum questions to ask (default: 10)
        """
        self.message_bus = message_bus
        self.llm = llm_client
        self.min_questions = min_questions
        self.max_questions = max_questions

    async def initialize_project(
        self,
        pattern: DetectedPattern,
        user_id: str
    ) -> Result[QASession, str]:
        """
        Initialize project from detected pattern and YES response.

        Constitutional: Article I compliance (complete context required)

        Args:
            pattern: Detected pattern that triggered initialization
            user_id: User ID for project ownership

        Returns:
            Result[QASession, str]: Started Q&A session or error
        """
        # Generate project ID
        project_id = str(uuid.uuid4())

        # Generate contextual questions
        questions_result = await self._generate_questions(pattern)
        if not questions_result.is_ok():
            return Err(f"Question generation failed: {questions_result.unwrap_err()}")

        # Create Q&A session
        session = QASession(
            session_id=str(uuid.uuid4()),
            project_id=project_id,
            pattern_id=pattern.pattern_id,
            pattern_type=pattern.pattern_type,
            questions=questions_result.unwrap(),
            answers=[],
            started_at=datetime.now(),
            status="in_progress"
        )

        return Ok(session)

    async def _generate_questions(
        self,
        pattern: DetectedPattern
    ) -> Result[List[QAQuestion], str]:
        """
        Generate 5-10 contextual questions for pattern type.

        Args:
            pattern: Detected pattern

        Returns:
            Result[List[QAQuestion], str]: Questions or error
        """
        # Get question template based on pattern type
        template = self._get_question_template(pattern.pattern_type)
        if not template:
            return Err(f"No template for pattern type: {pattern.pattern_type}")

        # Generate questions using LLM
        try:
            prompt = self._build_question_prompt(pattern, template)
            questions = await self._llm_generate_questions(prompt)
            return Ok(questions)
        except Exception as e:
            return Err(f"LLM question generation failed: {str(e)}")

    def _get_question_template(self, pattern_type: str) -> Optional[dict]:
        """Get question template for pattern type."""
        templates = {
            "project_mention": {
                "focus": "project scope and deliverables",
                "required_questions": [
                    "What's the core goal or outcome?",
                    "Who is the target audience?",
                    "What's already done vs needs doing?",
                    "What's your ideal timeline?",
                    "What's your daily time commitment?"
                ]
            },
            "recurring_topic": {
                "focus": "topic depth and actionability",
                "required_questions": [
                    "What specific aspect interests you most?",
                    "What would success look like?",
                    "What's blocking progress now?",
                    "How much time can you dedicate?",
                    "When would you like this complete?"
                ]
            },
            "workflow_bottleneck": {
                "focus": "bottleneck resolution",
                "required_questions": [
                    "What's the current workflow?",
                    "Where does it break down?",
                    "What's the ideal state?",
                    "What constraints exist?",
                    "What's the priority level?"
                ]
            }
        }
        return templates.get(pattern_type)

    def _build_question_prompt(
        self,
        pattern: DetectedPattern,
        template: dict
    ) -> str:
        """Build LLM prompt for question generation."""
        return f"""
Generate 5-10 contextual questions to initialize a project.

Pattern Context:
- Type: {pattern.pattern_type}
- Topic: {pattern.topic}
- Mention Count: {pattern.mention_count}
- Summary: {pattern.context_summary}

Question Focus: {template['focus']}
Required Questions: {', '.join(template['required_questions'])}

Generate questions that:
1. Build on previous answers (adaptive)
2. Are specific and actionable
3. Help clarify scope and deliverables
4. Take 5-10 minutes total to answer
5. Mix required and optional questions

Return JSON array of questions with:
- question_text (10-500 chars)
- required (boolean)
- context (why we're asking)
"""

    async def _llm_generate_questions(
        self,
        prompt: str
    ) -> List[QAQuestion]:
        """
        Generate questions using LLM.

        Args:
            prompt: Question generation prompt

        Returns:
            List of QAQuestion objects
        """
        # This would call actual LLM in production
        # For now, return structured template questions
        question_specs = [
            ("What's the core goal or outcome?", "Helps define project scope"),
            ("Who is the target audience?", "Clarifies who benefits"),
            ("What's already done vs needs doing?", "Establishes starting point"),
            ("What's your ideal timeline?", "Sets time expectations"),
            ("What's your daily time commitment?", "Plans daily scope")
        ]

        return [
            QAQuestion(
                question_id=str(uuid.uuid4()),
                question_text=text,
                question_number=idx + 1,
                required=True,
                context=context
            )
            for idx, (text, context) in enumerate(question_specs)
        ]

    async def process_answer(
        self,
        session: QASession,
        question_id: str,
        answer_text: str,
        confidence: QuestionConfidence
    ) -> Result[QASession, str]:
        """
        Process user's answer to question.

        Args:
            session: Current Q&A session
            question_id: Question being answered
            answer_text: User's answer
            confidence: User's confidence level

        Returns:
            Result[QASession, str]: Updated session or error
        """
        # Validate question exists
        if not self._validate_question_id(session, question_id):
            return Err(f"Invalid question_id: {question_id}")

        # Create answer and updated session
        answer = self._create_answer(question_id, answer_text, confidence)
        updated_session = self._update_session(session, answer)

        return Ok(updated_session)

    def _validate_question_id(self, session: QASession, question_id: str) -> bool:
        """Validate question exists in session."""
        question_ids = {q.question_id for q in session.questions}
        return question_id in question_ids

    def _create_answer(
        self,
        question_id: str,
        answer_text: str,
        confidence: QuestionConfidence
    ) -> QAAnswer:
        """Create QAAnswer object."""
        return QAAnswer(
            question_id=question_id,
            answer_text=answer_text,
            answered_at=datetime.now(),
            confidence=confidence
        )

    def _update_session(self, session: QASession, answer: QAAnswer) -> QASession:
        """Update session with new answer."""
        updated_answers = list(session.answers) + [answer]
        completed_at, status, total_time = self._calc_completion_status(
            session,
            updated_answers
        )

        return QASession(
            session_id=session.session_id,
            project_id=session.project_id,
            pattern_id=session.pattern_id,
            pattern_type=session.pattern_type,
            questions=session.questions,
            answers=updated_answers,
            started_at=session.started_at,
            completed_at=completed_at,
            status=status,
            total_time_minutes=total_time
        )

    def _calc_completion_status(
        self,
        session: QASession,
        answers: List[QAAnswer]
    ) -> tuple:
        """Calculate completion status and timing."""
        if not self._check_session_complete(session, answers):
            return None, session.status, None

        completed_at = datetime.now()
        duration = completed_at - session.started_at
        total_time = int(duration.total_seconds() / 60)
        return completed_at, "completed", total_time

    def _check_session_complete(
        self,
        session: QASession,
        answers: List[QAAnswer]
    ) -> bool:
        """
        Check if all required questions have answers.

        Constitutional: Article I (complete context requirement)

        Args:
            session: Current session
            answers: Current answers

        Returns:
            bool: True if complete, False otherwise
        """
        required_ids = {
            q.question_id for q in session.questions if q.required
        }
        answered_ids = {a.question_id for a in answers}
        return required_ids.issubset(answered_ids)

    async def validate_completeness(
        self,
        session: QASession
    ) -> Result[bool, str]:
        """
        Validate Q&A session completeness.

        Constitutional: Article I enforcement (no partial context)

        Args:
            session: Q&A session to validate

        Returns:
            Result[bool, str]: True if complete, error if incomplete
        """
        if not session.is_complete:
            required_unanswered = [
                q.question_text
                for q in session.questions
                if q.required and q.question_id not in
                {a.question_id for a in session.answers}
            ]
            return Err(
                f"Incomplete session. Missing answers: {', '.join(required_unanswered)}"
            )

        # Check answer quality
        low_quality = [
            a for a in session.answers
            if len(a.answer_text.strip()) < 10
        ]
        if low_quality:
            return Err(
                f"Low quality answers detected. Need at least 10 chars per answer."
            )

        return Ok(True)
