"""
Daily Check-in Coordinator for Trinity Protocol Phase 3.

Coordinates 1-3 questions per day to move projects forward.
Integrates with preference learning for optimal timing.

Constitutional Compliance:
- Article IV: Preference learning integration (optimal timing)
- Article II: Strict typing with Result<T,E> pattern
- Article I: Complete context before question generation
- User respect: Maximum 3 questions per day, batched delivery

Flow:
1. Schedule check-in based on preference learning
2. Generate 1-3 questions for current project phase
3. Batch questions together (not separate interruptions)
4. Deliver via HITL protocol at optimal time
5. Process responses and update project state
6. Schedule next check-in

Usage:
    coordinator = DailyCheckin(preference_learner, response_handler)
    result = await coordinator.schedule_checkin(project, plan)
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from trinity_protocol.core.models.project import (
    Project,
    ProjectPlan,
    ProjectTask,
    CheckinQuestion,
    CheckinResponse,
    DailyCheckin as DailyCheckinModel,
)
from shared.type_definitions.result import Result, Ok, Err


class CheckinError(Exception):
    """Daily check-in error."""
    pass


class DailyCheckin:
    """
    Coordinate daily user interactions (1-3 questions).

    Constitutional: Article IV (preference learning integration)
    """

    def __init__(
        self,
        preference_learner,
        min_questions: int = 1,
        max_questions: int = 3
    ):
        """
        Initialize daily check-in coordinator.

        Args:
            preference_learner: Preference learning system
            min_questions: Minimum questions per check-in (default: 1)
            max_questions: Maximum questions per check-in (default: 3)
        """
        self.preferences = preference_learner
        self.min_questions = min_questions
        self.max_questions = max_questions

    async def schedule_checkin(
        self,
        project: Project
    ) -> Result[datetime, str]:
        """
        Schedule next check-in based on preference learning.

        Constitutional: Article IV (apply learned preferences)

        Args:
            project: Project to schedule check-in for

        Returns:
            Result[datetime, str]: Scheduled time or error
        """
        # Get optimal time from preference learner
        try:
            optimal_time = await self._get_optimal_time(project)
            return Ok(optimal_time)
        except Exception as e:
            return Err(f"Scheduling failed: {str(e)}")

    async def _get_optimal_time(self, project: Project) -> datetime:
        """
        Get optimal check-in time from preference learning.

        In production, this would:
        1. Query PreferenceLearning for user's best response times
        2. Respect quiet hours (22:00-08:00)
        3. Avoid focus blocks
        4. Consider project priority
        """
        # For now, schedule for 09:00 next day
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

    async def generate_checkin_questions(
        self,
        project: Project,
        plan: ProjectPlan,
        current_phase: str = "execution"
    ) -> Result[List[CheckinQuestion], str]:
        """
        Generate 1-3 questions for current project phase.

        Constitutional: Article I (complete context before generation)

        Args:
            project: Current project
            plan: Project plan
            current_phase: Current project phase

        Returns:
            Result[List[CheckinQuestion], str]: Questions or error
        """
        # Gather context
        context_result = await self._gather_checkin_context(project, plan)
        if not context_result.is_ok:
            return Err(f"Context gathering failed: {context_result.error}")

        # Generate questions based on phase
        questions = await self._generate_phase_questions(
            project,
            plan,
            current_phase
        )

        # Limit to max_questions
        limited_questions = questions[:self.max_questions]

        if len(limited_questions) < self.min_questions:
            return Err(
                f"Insufficient questions generated: {len(limited_questions)} < {self.min_questions}"
            )

        return Ok(limited_questions)

    async def _gather_checkin_context(
        self,
        project: Project,
        plan: ProjectPlan
    ) -> Result[dict, str]:
        """
        Gather complete context for check-in question generation.

        Constitutional: Article I enforcement
        """
        try:
            # Calculate progress
            total_tasks = len(plan.tasks)
            completed_tasks = len([
                t for t in plan.tasks if t.status == "completed"
            ])
            progress_pct = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

            context = {
                "project_id": project.project_id,
                "project_title": project.title,
                "progress_percentage": progress_pct,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "days_active": (datetime.now() - project.created_at).days
            }
            return Ok(context)
        except Exception as e:
            return Err(f"Context error: {str(e)}")

    async def _generate_phase_questions(
        self,
        project: Project,
        plan: ProjectPlan,
        phase: str
    ) -> List[CheckinQuestion]:
        """Generate questions for current phase."""
        checkin_id = str(uuid.uuid4())
        next_task = self._get_next_task(plan)

        # Generate task-specific and general questions
        task_questions = self._gen_task_questions(
            checkin_id,
            project,
            next_task,
            phase
        )
        general_question = self._gen_general_question(checkin_id, project)

        return task_questions + [general_question]

    def _gen_task_questions(
        self,
        checkin_id: str,
        project: Project,
        task: Optional[ProjectTask],
        phase: str
    ) -> List[CheckinQuestion]:
        """Generate task-specific questions."""
        if phase != "execution" or not task:
            return []

        questions = [
            CheckinQuestion(
                question_id=str(uuid.uuid4()),
                checkin_id=checkin_id,
                project_id=project.project_id,
                task_id=task.task_id,
                question_text=f"Ready to work on: {task.title}? Any concerns?",
                question_type="progress",
                asked_at=datetime.now()
            )
        ]

        if task.description:
            questions.append(
                CheckinQuestion(
                    question_id=str(uuid.uuid4()),
                    checkin_id=checkin_id,
                    project_id=project.project_id,
                    task_id=task.task_id,
                    question_text=f"Any specific approach you prefer for: {task.title}?",
                    question_type="clarification",
                    asked_at=datetime.now()
                )
            )

        return questions

    def _gen_general_question(self, checkin_id: str, project: Project) -> CheckinQuestion:
        """Generate general progress question."""
        return CheckinQuestion(
            question_id=str(uuid.uuid4()),
            checkin_id=checkin_id,
            project_id=project.project_id,
            task_id=None,
            question_text="How's the project going overall? Any blockers?",
            question_type="feedback",
            asked_at=datetime.now()
        )

    def _get_next_task(self, plan: ProjectPlan) -> Optional[ProjectTask]:
        """Get next pending task from plan."""
        pending_tasks = [
            t for t in plan.tasks if t.status == "pending"
        ]
        return pending_tasks[0] if pending_tasks else None

    async def process_checkin_response(
        self,
        checkin: DailyCheckinModel,
        responses: List[CheckinResponse]
    ) -> Result[None, str]:
        """
        Process check-in responses and update project state.

        Args:
            checkin: Daily check-in
            responses: User responses

        Returns:
            Result[None, str]: Success or error
        """
        # Validate all questions answered
        question_ids = {q.question_id for q in checkin.questions}
        response_ids = {r.question_id for r in responses}

        if not question_ids.issubset(response_ids):
            missing = question_ids - response_ids
            return Err(f"Missing responses for questions: {missing}")

        # Analyze responses
        analysis = self._analyze_responses(responses)

        # Check for blockers
        if analysis["has_blockers"]:
            return Err(f"Blocker detected: {analysis['blocker_description']}")

        # Update project state would happen here
        # (integrate with ProjectExecutor)

        return Ok(None)

    def _analyze_responses(self, responses: List[CheckinResponse]) -> dict:
        """Analyze responses for blockers and sentiment."""
        # Simple sentiment analysis
        negative_count = len([
            r for r in responses if r.sentiment == "negative"
        ])

        # Check for blocker keywords
        blocker_keywords = ["blocked", "stuck", "can't", "won't", "impossible"]
        has_blockers = any(
            any(keyword in r.response_text.lower() for keyword in blocker_keywords)
            for r in responses
        )

        blocker_text = ""
        if has_blockers:
            blocker_responses = [
                r for r in responses
                if any(keyword in r.response_text.lower() for keyword in blocker_keywords)
            ]
            blocker_text = blocker_responses[0].response_text if blocker_responses else ""

        return {
            "has_blockers": has_blockers,
            "blocker_description": blocker_text,
            "negative_sentiment_count": negative_count,
            "total_responses": len(responses)
        }

    async def create_checkin(
        self,
        project: Project,
        questions: List[CheckinQuestion]
    ) -> Result[DailyCheckinModel, str]:
        """
        Create daily check-in object.

        Args:
            project: Project
            questions: Check-in questions

        Returns:
            Result[DailyCheckinModel, str]: Check-in or error
        """
        if not questions:
            return Err("Cannot create check-in without questions")

        if len(questions) > self.max_questions:
            return Err(f"Too many questions: {len(questions)} > {self.max_questions}")

        checkin = DailyCheckinModel(
            checkin_id=str(uuid.uuid4()),
            project_id=project.project_id,
            checkin_date=datetime.now(),
            questions=questions,
            responses=[],
            total_time_minutes=0,
            next_steps="Awaiting user responses",
            status="pending"
        )

        return Ok(checkin)
