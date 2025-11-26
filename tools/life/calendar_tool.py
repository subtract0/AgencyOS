"""
Calendar Tool
=============

The "Timekeeper" for AgencyOS.
Allows the agent to view and manage the user's schedule.

Capabilities:
- schedule_event: Book a meeting or reminder.
- list_events: See what's coming up.
- find_free_slots: Proactively find time for deep work.

Design:
- Currently uses an IN-MEMORY store for safety/demo.
- Ready for Apple Calendar (EventKit) integration via `osascript`.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base import LifeTool, ToolResult
import uuid

class CalendarTool(LifeTool):
    def __init__(self):
        super().__init__(
            name="Calendar",
            description="Manage the user's schedule, appointments, and time."
        )
        # In-memory store for demo purposes
        self._events: Dict[str, Dict[str, Any]] = {}
        self._populate_demo_data()

    def _populate_demo_data(self):
        """Add some fake events to make the world feel alive."""
        now = datetime.now()
        
        # A meeting earlier today
        self._add_event_internal(
            title="Team Sync",
            start_time=now - timedelta(hours=4),
            end_time=now - timedelta(hours=3),
            description="Weekly sync with engineering."
        )
        
        # A meeting tomorrow
        self._add_event_internal(
            title="Dentist Appointment",
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=3),
            description="Routine checkup."
        )

    def _add_event_internal(self, title: str, start_time: datetime, end_time: datetime, description: str = "") -> str:
        event_id = str(uuid.uuid4())[:8]
        self._events[event_id] = {
            "id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description
        }
        return event_id

    def get_capabilities(self) -> List[str]:
        return ["schedule_event", "list_events", "check_availability"]

    def execute(self, action: str, **kwargs) -> ToolResult:
        if action == "schedule_event":
            return self.schedule_event(**kwargs)
        elif action == "list_events":
            return self.list_events(**kwargs)
        elif action == "check_availability":
            return self.check_availability(**kwargs)
        else:
            return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")

    def schedule_event(self, title: str, start_time: str, end_time: str, description: str = "") -> ToolResult:
        """
        Schedule a new event.
        Args:
            title: Event title.
            start_time: ISO format string.
            end_time: ISO format string.
            description: Optional details.
        """
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
        except ValueError:
            return ToolResult(success=False, message="Invalid date format. Use ISO 8601.", error="DateFormatError")

        # HITL Check
        if not self._require_confirmation("schedule_event", f"Book '{title}' from {start} to {end}?"):
            return ToolResult(success=False, message="User denied action.", error="UserDenied")

        event_id = self._add_event_internal(title, start, end, description)
        
        return ToolResult(
            success=True,
            message=f"Scheduled '{title}' for {start.strftime('%A, %b %d at %I:%M %p')}.",
            data={"event_id": event_id}
        )

    def list_events(self, days: int = 7) -> ToolResult:
        """List events for the next N days."""
        now = datetime.now()
        limit = now + timedelta(days=days)
        
        upcoming = []
        for event in self._events.values():
            if now <= event["start_time"] <= limit:
                upcoming.append(event)
        
        # Sort by time
        upcoming.sort(key=lambda x: x["start_time"])
        
        if not upcoming:
            return ToolResult(success=True, message="Calendar is clear for the next few days.", data=[])
            
        summary = "\n".join([
            f"- {e['start_time'].strftime('%a %I:%M %p')}: {e['title']}" 
            for e in upcoming
        ])
        
        return ToolResult(
            success=True,
            message=f"You have {len(upcoming)} upcoming events:\n{summary}",
            data=upcoming
        )

    def check_availability(self, start_time: str, end_time: str) -> ToolResult:
        """Check if a slot is free."""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
        except ValueError:
            return ToolResult(success=False, message="Invalid date format.", error="DateFormatError")

        conflicts = []
        for event in self._events.values():
            # Overlap logic: (StartA < EndB) and (EndA > StartB)
            if (start < event["end_time"]) and (end > event["start_time"]):
                conflicts.append(event)
        
        if conflicts:
            names = ", ".join([e["title"] for e in conflicts])
            return ToolResult(
                success=False, 
                message=f"Conflict detected with: {names}", 
                data={"conflicts": conflicts}
            )
            
        return ToolResult(success=True, message="Slot is free.", data={"available": True})
