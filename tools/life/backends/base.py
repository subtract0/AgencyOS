"""
Backend Base Classes
====================

Abstract interfaces for Life Tool backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class BackendConfig:
    """Configuration for a backend."""
    credentials_path: Optional[str] = None
    api_key: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalendarEvent:
    """Standardized calendar event representation."""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: str = ""
    location: str = ""
    attendees: list[str] = field(default_factory=list)
    source: str = "unknown"  # Which backend created this


@dataclass
class Email:
    """Standardized email representation."""
    id: str
    from_address: str
    to_addresses: list[str]
    subject: str
    body: str
    is_read: bool = False
    timestamp: Optional[datetime] = None
    attachments: list[str] = field(default_factory=list)


class CalendarBackend(ABC):
    """Abstract interface for calendar backends."""

    def __init__(self, config: Optional[BackendConfig] = None):
        self.config = config or BackendConfig()
        self._connected = False

    @property
    def name(self) -> str:
        """Backend identifier."""
        return "abstract"

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the calendar service."""
        pass

    @abstractmethod
    def list_events(
        self,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 50
    ) -> list[CalendarEvent]:
        """List events in a date range."""
        pass

    @abstractmethod
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
        attendees: list[str] = None
    ) -> CalendarEvent:
        """Create a new calendar event."""
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        pass

    @abstractmethod
    def check_availability(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> tuple[bool, list[CalendarEvent]]:
        """Check if a time slot is free. Returns (is_available, conflicting_events)."""
        pass


class EmailBackend(ABC):
    """Abstract interface for email backends."""

    def __init__(self, config: Optional[BackendConfig] = None):
        self.config = config or BackendConfig()
        self._connected = False

    @property
    def name(self) -> str:
        """Backend identifier."""
        return "abstract"

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the email service."""
        pass

    @abstractmethod
    def list_unread(self, max_results: int = 10) -> list[Email]:
        """List unread emails."""
        pass

    @abstractmethod
    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
        attachments: list[str] = None
    ) -> Email:
        """Send an email."""
        pass

    @abstractmethod
    def create_draft(
        self,
        to_addresses: list[str],
        subject: str,
        body: str
    ) -> Email:
        """Create a draft email."""
        pass
