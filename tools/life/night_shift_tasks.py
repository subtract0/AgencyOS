"""
Night Shift Life OS Task Handlers
=================================

Task handlers for Life OS features that run via Night Shift.

Task Types:
- morning_brief: Generate morning briefing at scheduled time
- email_triage: Auto-categorize and draft responses
- calendar_prep: Prepare for upcoming meetings

Usage:
    Add to Night Shift backlog:
    {
        "type": "morning_brief",
        "schedule": "06:00",
        "config": {"save": true, "email": "you@example.com"}
    }
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a Night Shift task execution."""
    success: bool
    message: str
    data: Optional[dict[str, Any]] = None
    artifacts: list[Path] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class LifeOSTaskHandler:
    """
    Handles Life OS tasks for Night Shift.

    Registers task types and executes them when scheduled.
    """

    def __init__(self):
        self._handlers = {
            "morning_brief": self._handle_morning_brief,
            "email_triage": self._handle_email_triage,
            "calendar_prep": self._handle_calendar_prep,
        }

    def can_handle(self, task_type: str) -> bool:
        """Check if this handler supports the task type."""
        return task_type in self._handlers

    def execute(self, task_type: str, config: dict[str, Any] = None) -> TaskResult:
        """
        Execute a Life OS task.

        Args:
            task_type: Type of task to execute
            config: Task-specific configuration

        Returns:
            TaskResult with success status and artifacts
        """
        if not self.can_handle(task_type):
            return TaskResult(
                success=False,
                message=f"Unknown task type: {task_type}",
            )

        handler = self._handlers[task_type]
        config = config or {}

        try:
            return handler(config)
        except Exception as e:
            logger.exception(f"Task {task_type} failed")
            return TaskResult(
                success=False,
                message=f"Task failed: {e}",
            )

    def _handle_morning_brief(self, config: dict[str, Any]) -> TaskResult:
        """Generate morning briefing."""
        from tools.life.morning_brief import MorningBriefGenerator

        generator = MorningBriefGenerator()
        brief = generator.generate()

        artifacts = []

        # Save to file
        if config.get("save", True):
            saved_path = generator.save(brief)
            artifacts.append(saved_path)
            logger.info(f"Morning brief saved to {saved_path}")

        # Send via email (if configured)
        if config.get("email"):
            try:
                from tools.life.email_tool import EmailTool

                email_tool = EmailTool()
                result = email_tool.send_email(
                    to=config["email"],
                    subject=f"Morning Brief - {brief.date.strftime('%B %d')}",
                    body=brief.to_markdown(),
                )
                if result.success:
                    logger.info(f"Morning brief emailed to {config['email']}")
                else:
                    logger.warning(f"Failed to email brief: {result.message}")
            except Exception as e:
                logger.warning(f"Could not email brief: {e}")

        return TaskResult(
            success=True,
            message=f"Morning brief generated for {brief.date.strftime('%Y-%m-%d')}",
            data={
                "date": brief.date.isoformat(),
                "sections": len(brief.sections),
                "greeting": brief.greeting,
            },
            artifacts=artifacts,
        )

    def _handle_email_triage(self, config: dict[str, Any]) -> TaskResult:
        """Triage emails and draft responses."""
        from tools.life.email_tool import EmailTool

        email_tool = EmailTool()
        result = email_tool.list_unread(limit=config.get("limit", 20))

        if not result.success:
            return TaskResult(
                success=False,
                message=f"Could not fetch emails: {result.message}",
            )

        emails = result.data or []

        # Categorize
        urgent = []
        needs_response = []
        fyi = []

        for email in emails:
            subject = email.get("subject", "").lower()
            if any(word in subject for word in ["urgent", "asap", "important"]):
                urgent.append(email)
            elif any(word in subject for word in ["re:", "?", "question"]):
                needs_response.append(email)
            else:
                fyi.append(email)

        return TaskResult(
            success=True,
            message=f"Triaged {len(emails)} emails: {len(urgent)} urgent, {len(needs_response)} need response",
            data={
                "total": len(emails),
                "urgent": len(urgent),
                "needs_response": len(needs_response),
                "fyi": len(fyi),
            },
        )

    def _handle_calendar_prep(self, config: dict[str, Any]) -> TaskResult:
        """Prepare for upcoming meetings."""
        from tools.life.calendar_tool import CalendarTool

        calendar_tool = CalendarTool()
        result = calendar_tool.list_events(days=1)

        if not result.success:
            return TaskResult(
                success=False,
                message=f"Could not fetch calendar: {result.message}",
            )

        events = result.data or []
        prep_notes = []

        for event in events:
            title = event.get("title", "Untitled")
            # Generate simple prep note
            prep_notes.append({
                "event": title,
                "prep": f"Review agenda and notes for: {title}",
            })

        return TaskResult(
            success=True,
            message=f"Prepared notes for {len(events)} events",
            data={
                "events": len(events),
                "prep_notes": prep_notes,
            },
        )


# Singleton instance for Night Shift integration
life_os_handler = LifeOSTaskHandler()
