"""
Google Calendar Backend
=======================

Real Google Calendar API integration.

Setup:
1. Create a project in Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download credentials.json
5. Set GOOGLE_CREDENTIALS_PATH environment variable

First run will open a browser for OAuth authorization.
Token is cached in ~/.agency/google_token.json
"""

import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import BackendConfig, CalendarBackend, CalendarEvent

# Lazy import - only load when actually used
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleCalendarBackend(CalendarBackend):
    """Google Calendar API backend."""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._service = None
        self._creds = None

        # Get credentials path from config or environment
        self._credentials_path = (
            config.credentials_path if config else None
        ) or os.getenv("GOOGLE_CREDENTIALS_PATH")

        # Token storage location
        self._token_path = Path.home() / ".agency" / "google_token.json"
        self._token_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "google"

    def connect(self) -> bool:
        """Authenticate with Google Calendar API."""
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Calendar API dependencies not installed. "
                "Run: pip install google-auth-oauthlib google-api-python-client"
            )

        creds = None

        # Load existing token
        if self._token_path.exists():
            with open(self._token_path, "rb") as token:
                creds = pickle.load(token)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._credentials_path or not Path(self._credentials_path).exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self._credentials_path}. "
                        "Set GOOGLE_CREDENTIALS_PATH environment variable."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next time
            with open(self._token_path, "wb") as token:
                pickle.dump(creds, token)

        self._creds = creds
        self._service = build("calendar", "v3", credentials=creds)
        self._connected = True
        return True

    def list_events(
        self,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """List events from Google Calendar."""
        if not self._connected:
            self.connect()

        events_result = (
            self._service.events()
            .list(
                calendarId="primary",
                timeMin=start_date.isoformat() + "Z",
                timeMax=end_date.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for item in events_result.get("items", []):
            start = item["start"].get("dateTime", item["start"].get("date"))
            end = item["end"].get("dateTime", item["end"].get("date"))

            events.append(
                CalendarEvent(
                    id=item["id"],
                    title=item.get("summary", "Untitled"),
                    start_time=datetime.fromisoformat(start.replace("Z", "+00:00")),
                    end_time=datetime.fromisoformat(end.replace("Z", "+00:00")),
                    description=item.get("description", ""),
                    location=item.get("location", ""),
                    attendees=[
                        a.get("email", "") for a in item.get("attendees", [])
                    ],
                    source="google",
                )
            )

        return events

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: list[str] = None,
    ) -> CalendarEvent:
        """Create a new Google Calendar event."""
        if not self._connected:
            self.connect()

        event_body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        created = (
            self._service.events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )

        return CalendarEvent(
            id=created["id"],
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees or [],
            source="google",
        )

    def delete_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event."""
        if not self._connected:
            self.connect()

        try:
            self._service.events().delete(
                calendarId="primary", eventId=event_id
            ).execute()
            return True
        except Exception:
            return False

    def check_availability(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[bool, list[CalendarEvent]]:
        """Check availability using Google Calendar's freebusy API."""
        if not self._connected:
            self.connect()

        # Get events in the time range
        events = self.list_events(start_time, end_time, max_results=10)

        conflicts = []
        for event in events:
            # Check for overlap
            if (start_time < event.end_time) and (end_time > event.start_time):
                conflicts.append(event)

        return (len(conflicts) == 0, conflicts)
