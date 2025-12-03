"""
Mock Backends
=============

In-memory mock implementations for development and testing.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from .base import (
    BackendConfig,
    CalendarBackend,
    CalendarEvent,
    Email,
    EmailBackend,
)


class MockCalendarBackend(CalendarBackend):
    """In-memory mock calendar backend for testing."""

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._events: dict[str, CalendarEvent] = {}
        self._populate_demo_data()

    @property
    def name(self) -> str:
        return "mock"

    def _populate_demo_data(self) -> None:
        """Add demo events."""
        now = datetime.now()

        # A meeting earlier today
        self._create_event_internal(
            title="Team Sync",
            start_time=now - timedelta(hours=4),
            end_time=now - timedelta(hours=3),
            description="Weekly sync with engineering.",
        )

        # A meeting tomorrow
        self._create_event_internal(
            title="Dentist Appointment",
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=3),
            description="Routine checkup.",
        )

    def _create_event_internal(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: list[str] = None,
    ) -> CalendarEvent:
        event_id = str(uuid.uuid4())[:8]
        event = CalendarEvent(
            id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees or [],
            source="mock",
        )
        self._events[event_id] = event
        return event

    def connect(self) -> bool:
        self._connected = True
        return True

    def list_events(
        self,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        events = [
            e
            for e in self._events.values()
            if start_date <= e.start_time <= end_date
        ]
        events.sort(key=lambda x: x.start_time)
        return events[:max_results]

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: list[str] = None,
    ) -> CalendarEvent:
        return self._create_event_internal(
            title, start_time, end_time, description, location, attendees
        )

    def delete_event(self, event_id: str) -> bool:
        if event_id in self._events:
            del self._events[event_id]
            return True
        return False

    def check_availability(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[bool, list[CalendarEvent]]:
        conflicts = []
        for event in self._events.values():
            # Overlap: (StartA < EndB) and (EndA > StartB)
            if (start_time < event.end_time) and (end_time > event.start_time):
                conflicts.append(event)
        return (len(conflicts) == 0, conflicts)


class MockEmailBackend(EmailBackend):
    """In-memory mock email backend for testing."""

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._drafts: dict[str, Email] = {}
        self._sent: list[Email] = []
        self._inbox: list[Email] = []
        self._populate_demo_data()

    @property
    def name(self) -> str:
        return "mock"

    def _populate_demo_data(self) -> None:
        """Add demo emails."""
        self._inbox = [
            Email(
                id="1",
                from_address="sarah@example.com",
                to_addresses=["me@example.com"],
                subject="Re: Roadmap",
                body="Can we move the meeting to Thursday?",
                is_read=False,
                timestamp=datetime.now() - timedelta(hours=2),
            ),
            Email(
                id="2",
                from_address="newsletter@tech.com",
                to_addresses=["me@example.com"],
                subject="Weekly Tech Update",
                body="This week in tech...",
                is_read=True,
                timestamp=datetime.now() - timedelta(days=1),
            ),
        ]

    def connect(self) -> bool:
        self._connected = True
        return True

    def list_unread(self, max_results: int = 10) -> list[Email]:
        unread = [e for e in self._inbox if not e.is_read]
        return unread[:max_results]

    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
        attachments: list[str] = None,
    ) -> Email:
        email_id = str(uuid.uuid4())[:8]
        email = Email(
            id=email_id,
            from_address="me@example.com",
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_read=True,
            timestamp=datetime.now(),
            attachments=attachments or [],
        )
        self._sent.append(email)
        return email

    def create_draft(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
    ) -> Email:
        draft_id = str(uuid.uuid4())[:8]
        draft = Email(
            id=draft_id,
            from_address="me@example.com",
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_read=False,
            timestamp=datetime.now(),
        )
        self._drafts[draft_id] = draft
        return draft
