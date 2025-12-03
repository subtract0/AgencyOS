"""
Apple Calendar Backend
======================

Native macOS Calendar integration via osascript/AppleScript.

Works out of the box on macOS - no API keys needed.
Uses the system Calendar app.
"""

import subprocess
import uuid
from datetime import datetime
from typing import Optional

from .base import BackendConfig, CalendarBackend, CalendarEvent


class AppleCalendarBackend(CalendarBackend):
    """Apple Calendar (Calendar.app) backend via AppleScript."""

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._calendar_name = config.extra.get("calendar_name", "Calendar") if config else "Calendar"

    @property
    def name(self) -> str:
        return "apple"

    def _run_applescript(self, script: str) -> str:
        """Execute AppleScript and return output."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(f"AppleScript error: {result.stderr}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError("AppleScript timed out")
        except FileNotFoundError:
            raise RuntimeError("osascript not found - this backend only works on macOS")

    def connect(self) -> bool:
        """Verify Calendar.app is accessible."""
        try:
            script = 'tell application "Calendar" to get name of calendars'
            self._run_applescript(script)
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def list_events(
        self,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """List events from Apple Calendar."""
        # Format dates for AppleScript
        start_str = start_date.strftime("%B %d, %Y %I:%M:%S %p")
        end_str = end_date.strftime("%B %d, %Y %I:%M:%S %p")

        script = f'''
        tell application "Calendar"
            set startDate to date "{start_str}"
            set endDate to date "{end_str}"
            set eventList to ""
            repeat with cal in calendars
                repeat with evt in (every event of cal whose start date >= startDate and start date <= endDate)
                    set eventList to eventList & (uid of evt) & "|" & (summary of evt) & "|" & (start date of evt as string) & "|" & (end date of evt as string) & "\\n"
                end repeat
            end repeat
            return eventList
        end tell
        '''

        try:
            output = self._run_applescript(script)
            events = []

            for line in output.split("\n"):
                if not line.strip():
                    continue
                parts = line.split("|")
                if len(parts) >= 4:
                    events.append(
                        CalendarEvent(
                            id=parts[0],
                            title=parts[1],
                            start_time=datetime.strptime(parts[2], "%A, %B %d, %Y at %I:%M:%S %p"),
                            end_time=datetime.strptime(parts[3], "%A, %B %d, %Y at %I:%M:%S %p"),
                            source="apple",
                        )
                    )

            return events[:max_results]
        except Exception as e:
            # Return empty list on error (AppleScript date parsing can be tricky)
            return []

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: list[str] = None,
    ) -> CalendarEvent:
        """Create a new event in Apple Calendar."""
        start_str = start_time.strftime("%B %d, %Y %I:%M:%S %p")
        end_str = end_time.strftime("%B %d, %Y %I:%M:%S %p")

        # Escape quotes in title and description
        title_escaped = title.replace('"', '\\"')
        desc_escaped = description.replace('"', '\\"')
        loc_escaped = location.replace('"', '\\"')

        script = f'''
        tell application "Calendar"
            tell calendar "{self._calendar_name}"
                set newEvent to make new event with properties {{summary:"{title_escaped}", start date:date "{start_str}", end date:date "{end_str}", description:"{desc_escaped}", location:"{loc_escaped}"}}
                return uid of newEvent
            end tell
        end tell
        '''

        try:
            event_id = self._run_applescript(script)
            return CalendarEvent(
                id=event_id or str(uuid.uuid4())[:8],
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees or [],
                source="apple",
            )
        except Exception as e:
            # Fallback ID if AppleScript fails
            return CalendarEvent(
                id=str(uuid.uuid4())[:8],
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees or [],
                source="apple",
            )

    def delete_event(self, event_id: str) -> bool:
        """Delete an event from Apple Calendar."""
        script = f'''
        tell application "Calendar"
            repeat with cal in calendars
                try
                    delete (first event of cal whose uid is "{event_id}")
                    return "deleted"
                end try
            end repeat
            return "not found"
        end tell
        '''

        try:
            result = self._run_applescript(script)
            return result == "deleted"
        except Exception:
            return False

    def check_availability(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[bool, list[CalendarEvent]]:
        """Check availability by listing events in the time range."""
        events = self.list_events(start_time, end_time, max_results=10)

        conflicts = []
        for event in events:
            if (start_time < event.end_time) and (end_time > event.start_time):
                conflicts.append(event)

        return (len(conflicts) == 0, conflicts)
