"""
Calendar Tool
=============

The "Timekeeper" for AgencyOS.
Allows the agent to view and manage the user's schedule.

Capabilities:
- schedule_event: Book a meeting or reminder.
- list_events: See what's coming up.
- find_free_slots: Proactively find time for deep work.

Backends (via LIFE_CALENDAR_BACKEND env var):
- "mock" (default): In-memory store for demos/testing
- "google": Google Calendar API
- "apple": macOS Calendar.app via AppleScript
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from .backends import get_calendar_backend
from .backends.base import CalendarBackend
from .base import LifeTool, ToolResult


class CalendarTool(LifeTool):
    """Calendar management tool with pluggable backends."""

    def __init__(self, backend: Optional[CalendarBackend] = None):
        """
        Initialize CalendarTool.

        Args:
            backend: Optional backend override. If None, uses LIFE_CALENDAR_BACKEND env var.
        """
        super().__init__(
            name="Calendar",
            description="Manage the user's schedule, appointments, and time."
        )
        self._backend = backend or get_calendar_backend()
        self._backend.connect()

    @property
    def backend_name(self) -> str:
        """Return the active backend name."""
        return self._backend.name

    def get_capabilities(self) -> list[str]:
        return ["schedule_event", "list_events", "check_availability"]

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "schedule_event":
            return self.schedule_event(**kwargs)
        elif action == "list_events":
            return self.list_events(**kwargs)
        elif action == "check_availability":
            return self.check_availability(**kwargs)
        else:
            return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")

    def schedule_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: list[str] = None,
    ) -> ToolResult:
        """
        Schedule a new event.

        Args:
            title: Event title.
            start_time: ISO format string.
            end_time: ISO format string.
            description: Optional details.
            location: Optional location.
            attendees: Optional list of email addresses.
        """
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
        except ValueError:
            return ToolResult(
                success=False,
                message="Invalid date format. Use ISO 8601 (e.g., 2024-01-15T14:00:00).",
                error="DateFormatError"
            )

        # HITL Check
        if not self._require_confirmation(
            "schedule_event",
            f"Book '{title}' from {start.strftime('%A, %b %d at %I:%M %p')} to {end.strftime('%I:%M %p')}?"
        ):
            return ToolResult(success=False, message="User denied action.", error="UserDenied")

        try:
            event = self._backend.create_event(
                title=title,
                start_time=start,
                end_time=end,
                description=description,
                location=location,
                attendees=attendees,
            )

            return ToolResult(
                success=True,
                message=f"Scheduled '{title}' for {start.strftime('%A, %b %d at %I:%M %p')} (via {self._backend.name}).",
                data={"event_id": event.id, "backend": self._backend.name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to schedule event: {e}",
                error="ScheduleError"
            )

    def list_events(self, days: int = 7) -> ToolResult:
        """List events for the next N days."""
        now = datetime.now()
        limit = now + timedelta(days=days)

        try:
            events = self._backend.list_events(now, limit)

            if not events:
                return ToolResult(
                    success=True,
                    message=f"Calendar is clear for the next {days} days.",
                    data=[]
                )

            summary = "\n".join([
                f"- {e.start_time.strftime('%a %I:%M %p')}: {e.title}"
                for e in events
            ])

            return ToolResult(
                success=True,
                message=f"You have {len(events)} upcoming events:\n{summary}",
                data=[{
                    "id": e.id,
                    "title": e.title,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "description": e.description,
                } for e in events]
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to list events: {e}",
                error="ListError"
            )

    def check_availability(self, start_time: str, end_time: str) -> ToolResult:
        """Check if a slot is free."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
        except ValueError:
            return ToolResult(
                success=False,
                message="Invalid date format. Use ISO 8601.",
                error="DateFormatError"
            )

        try:
            is_available, conflicts = self._backend.check_availability(start, end)

            if not is_available:
                names = ", ".join([e.title for e in conflicts])
                return ToolResult(
                    success=False,
                    message=f"Conflict detected with: {names}",
                    data={"conflicts": [{"id": e.id, "title": e.title} for e in conflicts]}
                )

            return ToolResult(
                success=True,
                message="Slot is free.",
                data={"available": True}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to check availability: {e}",
                error="AvailabilityError"
            )
