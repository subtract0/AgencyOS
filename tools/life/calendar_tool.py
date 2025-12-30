"""
Calendar Tool
=============

The "Timekeeper" for AgencyOS.
Allows the agent to view and manage the user's schedule.

Capabilities:
- schedule_event: Book a meeting or reminder.
- list_events: See what's coming up.
- find_free_slots: Proactively find time for deep work.

- Ready for Google Calendar integration.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import LifeTool, ToolResult
from .google_auth import get_service

class CalendarTool(LifeTool):
    def __init__(self):
        super().__init__(
            name="Calendar",
            description="Manage the user's Google Calendar."
        )
        # Service initialized lazily on first use to avoid blocking init
        self._service = None

    @property
    def service(self):
        if not self._service:
            self._service = get_service('calendar', 'v3')
        return self._service

    def get_capabilities(self) -> List[str]:
        return ["schedule_event", "list_events", "check_availability"]

    def execute(self, action: str, **kwargs) -> ToolResult:
        try:
            if action == "schedule_event":
                return self.schedule_event(**kwargs)
            elif action == "list_events":
                return self.list_events(**kwargs)
            elif action == "check_availability":
                return self.check_availability(**kwargs)
            else:
                return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")
        except Exception as e:
            return ToolResult(success=False, message=f"Google API Error: {str(e)}", error="ApiError")

    def schedule_event(self, title: str, start_time: str, end_time: str, description: str = "") -> ToolResult:
        """
        Schedule a new event on Google Calendar.
        Args:
            title: Event title.
            start_time: ISO format string.
            end_time: ISO format string.
            description: Optional details.
        """
        # HITL Check
        if not self._require_confirmation("schedule_event", f"Book '{title}' from {start_time} to {end_time}?"):
            return ToolResult(success=False, message="User denied action.", error="UserDenied")

        event_body = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'UTC'}, # Assuming UTC or offset included
            'end': {'dateTime': end_time, 'timeZone': 'UTC'},
        }

        event = self.service.events().insert(calendarId='primary', body=event_body).execute()
        
        return ToolResult(
            success=True,
            message=f"Scheduled '{title}'. Link: {event.get('htmlLink')}",
            data={"event_id": event.get('id'), "link": event.get('htmlLink')}
        )

    def list_events(self, days: int = 7) -> ToolResult:
        """List upcoming events from 'primary' calendar."""
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10 * days, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            return ToolResult(success=True, message="No upcoming events found.", data=[])

        summary_lines = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary_lines.append(f"- {start}: {event['summary']}")
            
        return ToolResult(
            success=True,
            message=f"Found {len(events)} upcoming events:\n" + "\n".join(summary_lines),
            data=events
        )

    def check_availability(self, start_time: str, end_time: str) -> ToolResult:
        """Check availability via FreeBusy API."""
        body = {
            "timeMin": start_time,
            "timeMax": end_time,
            "items": [{"id": "primary"}]
        }
        
        events_result = self.service.freebusy().query(body=body).execute()
        busy_slots = events_result['calendars']['primary']['busy']
        
        if busy_slots:
             return ToolResult(
                success=False, 
                message=f"Busy during this time. {len(busy_slots)} conflicting slots.", 
                data={"conflicts": busy_slots}
            )
            
        return ToolResult(success=True, message="Slot is free.", data={"available": True})
    
    def _require_confirmation(self, action: str, details: str) -> bool:
        """Internal HITL check (placeholder until base class support)."""
        print(f"\n⚠️  CONFIRMATION REGUIRED: {action}")
        print(details)
        response = input("Proceed? (y/n): ")
        return response.lower().startswith('y')
