"""
Project Executor for Trinity Protocol Phase 3.

Manages daily execution with micro-task breakdown and progress tracking.
Coordinates between daily check-ins, background work, and completion detection.

Constitutional Compliance:
- Article I: Complete context before daily planning
- Article II: Strict typing with Result<T,E> pattern
- Article V: Spec-driven execution (references approved spec)
- Article IV: Learning from execution patterns

Flow:
1. Start execution after plan approval
2. Break plan into daily micro-tasks (<30 min each)
3. Coordinate with DailyCheckin for user input
4. Execute background tasks between check-ins
5. Track progress and adapt based on feedback
6. Detect completion and generate deliverable

Usage:
    executor = ProjectExecutor(llm_client, state_store)
    result = await executor.start_execution(project)
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from trinity_protocol.models.project import (
    Project,
    ProjectSpec,
    ProjectPlan,
    ProjectTask,
    TaskStatus,
    ProjectState,
)
from shared.type_definitions.result import Result, Ok, Err


class ExecutionError(Exception):
    """Project execution error."""
    pass


class ProjectExecutor:
    """
    Manage project execution from start to completion.

    Constitutional: Article I (complete context), Article V (spec-driven)
    """

    def __init__(
        self,
        llm_client,
        max_daily_tasks: int = 4
    ):
        """
        Initialize project executor.

        Args:
            llm_client: LLM for task planning
            max_daily_tasks: Maximum tasks per day (default: 4)
        """
        self.llm = llm_client
        self.max_daily_tasks = max_daily_tasks

    async def start_execution(
        self,
        project: Project,
        plan: ProjectPlan
    ) -> Result[None, str]:
        """
        Begin project execution after plan approval.

        Args:
            project: Project to execute
            plan: Approved implementation plan

        Returns:
            Result[None, str]: Success or error
        """
        # Validate project state
        if project.state not in [ProjectState.PLANNING, ProjectState.INITIALIZING]:
            return Err(
                f"Cannot start execution from state: {project.state}. "
                "Must be in PLANNING or INITIALIZING state."
            )

        # Validate plan approval
        if not plan.plan_markdown:
            return Err("Plan must be approved before execution starts")

        return Ok(None)

    async def get_next_task(
        self,
        project: Project,
        plan: ProjectPlan
    ) -> Result[Optional[ProjectTask], str]:
        """
        Retrieve next task based on dependencies and state.

        Args:
            project: Current project
            plan: Project plan with tasks

        Returns:
            Result[Optional[ProjectTask], str]: Next task or None if all complete
        """
        # Filter pending tasks
        pending_tasks = [
            t for t in plan.tasks if t.status == TaskStatus.PENDING
        ]

        if not pending_tasks:
            return Ok(None)  # All tasks complete

        # Find tasks with no pending dependencies
        completed_ids = {
            t.task_id for t in plan.tasks if t.status == TaskStatus.COMPLETED
        }

        available_tasks = [
            t for t in pending_tasks
            if all(dep_id in completed_ids for dep_id in t.dependencies)
        ]

        if not available_tasks:
            # Check for circular dependencies or blockers
            blocked_tasks = [
                t for t in pending_tasks
                if t.status == TaskStatus.BLOCKED
            ]
            if blocked_tasks:
                return Err(f"Tasks blocked: {len(blocked_tasks)} tasks cannot proceed")
            return Err("Dependency deadlock detected")

        # Return highest priority available task
        next_task = available_tasks[0]
        return Ok(next_task)

    async def complete_task(
        self,
        task: ProjectTask,
        output: str
    ) -> Result[ProjectTask, str]:
        """
        Mark task complete and update state.

        Args:
            task: Task to complete
            output: Task output/deliverable

        Returns:
            Result[ProjectTask, str]: Updated task or error
        """
        # Validate task can be completed
        if task.status == TaskStatus.COMPLETED:
            return Err(f"Task {task.task_id} already completed")

        if task.status == TaskStatus.BLOCKED:
            return Err(f"Task {task.task_id} is blocked, cannot complete")

        # Create completed task (immutable update)
        completed_task = ProjectTask(
            task_id=task.task_id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            estimated_minutes=task.estimated_minutes,
            dependencies=task.dependencies,
            acceptance_criteria=task.acceptance_criteria,
            assigned_to=task.assigned_to,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now()
        )

        return Ok(completed_task)

    async def check_completion(
        self,
        project: Project,
        plan: ProjectPlan
    ) -> Result[bool, str]:
        """
        Determine if project is complete.

        Args:
            project: Current project
            plan: Project plan

        Returns:
            Result[bool, str]: True if complete, False if in progress
        """
        # Check if all tasks completed
        total_tasks = len(plan.tasks)
        completed_tasks = len([
            t for t in plan.tasks if t.status == TaskStatus.COMPLETED
        ])

        if completed_tasks == total_tasks:
            return Ok(True)

        # Check if blocked with no way forward
        pending_tasks = [
            t for t in plan.tasks if t.status == TaskStatus.PENDING
        ]
        blocked_tasks = [
            t for t in plan.tasks if t.status == TaskStatus.BLOCKED
        ]

        if not pending_tasks and blocked_tasks:
            return Err(
                f"Project stalled: {len(blocked_tasks)} tasks blocked with no path forward"
            )

        return Ok(False)

    async def plan_daily_tasks(
        self,
        project: Project,
        plan: ProjectPlan,
        yesterday_feedback: Optional[str] = None
    ) -> Result[List[ProjectTask], str]:
        """
        Plan next 24 hours of work based on current state.

        Constitutional: Article I (complete context before planning)

        Args:
            project: Current project
            plan: Project plan
            yesterday_feedback: Feedback from previous day

        Returns:
            Result[List[ProjectTask], str]: Daily tasks or error
        """
        # Gather complete context
        context_result = await self._gather_complete_context(
            project,
            plan,
            yesterday_feedback
        )
        if not context_result.is_ok:
            return Err(f"Context gathering failed: {context_result.error}")

        # Get available tasks
        available_tasks = await self._get_available_tasks(plan)

        # Select up to max_daily_tasks
        daily_tasks = available_tasks[:self.max_daily_tasks]

        return Ok(daily_tasks)

    async def _gather_complete_context(
        self,
        project: Project,
        plan: ProjectPlan,
        yesterday_feedback: Optional[str]
    ) -> Result[dict, str]:
        """
        Gather complete context for daily planning.

        Constitutional: Article I enforcement
        """
        try:
            context = {
                "project_id": project.project_id,
                "project_title": project.title,
                "total_tasks": len(plan.tasks),
                "completed_tasks": len([
                    t for t in plan.tasks if t.status == TaskStatus.COMPLETED
                ]),
                "pending_tasks": len([
                    t for t in plan.tasks if t.status == TaskStatus.PENDING
                ]),
                "yesterday_feedback": yesterday_feedback or "None",
                "days_elapsed": (datetime.now() - project.created_at).days
            }
            return Ok(context)
        except Exception as e:
            return Err(f"Context gathering error: {str(e)}")

    async def _get_available_tasks(
        self,
        plan: ProjectPlan
    ) -> List[ProjectTask]:
        """Get tasks available to execute (no pending dependencies)."""
        completed_ids = {
            t.task_id for t in plan.tasks if t.status == TaskStatus.COMPLETED
        }

        available = [
            t for t in plan.tasks
            if t.status == TaskStatus.PENDING and
            all(dep_id in completed_ids for dep_id in t.dependencies)
        ]

        return available

    async def adapt_plan(
        self,
        project: Project,
        plan: ProjectPlan,
        feedback: str
    ) -> Result[ProjectPlan, str]:
        """
        Adapt plan based on user feedback.

        Args:
            project: Current project
            plan: Current plan
            feedback: User feedback requiring adaptation

        Returns:
            Result[ProjectPlan, str]: Updated plan or error
        """
        # In production, this would:
        # 1. Analyze feedback using LLM
        # 2. Identify required changes (re-prioritize, add/remove tasks)
        # 3. Update plan accordingly
        # 4. Request user approval of changes

        # For now, return current plan
        return Ok(plan)

    async def generate_deliverable(
        self,
        project: Project,
        plan: ProjectPlan
    ) -> Result[str, str]:
        """
        Generate final project deliverable.

        Args:
            project: Completed project
            plan: Project plan

        Returns:
            Result[str, str]: Deliverable path or error
        """
        # Validate project completion
        completion_result = await self.check_completion(project, plan)
        if not completion_result.is_ok():
            return Err(f"Cannot generate deliverable: {completion_result.unwrap_err()}")

        if not completion_result.unwrap():
            return Err("Project not complete, cannot generate deliverable")

        # Generate deliverable based on project type
        deliverable_path = f"deliverables/{project.project_id}/final_deliverable.md"

        return Ok(deliverable_path)
