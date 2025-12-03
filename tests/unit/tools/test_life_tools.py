"""
Tests for Life OS Tools
=======================

Unit tests for CalendarTool, EmailTool, and BrowserTool with mock backends.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import backends directly to avoid loading full tools package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestMockCalendarBackend:
    """Tests for MockCalendarBackend."""

    def test_connect(self):
        """Test backend connection."""
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        assert backend.connect() is True
        assert backend._connected is True

    def test_list_events_returns_demo_data(self):
        """Test listing events returns demo data."""
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        backend.connect()

        now = datetime.now()
        events = backend.list_events(
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=7)
        )

        # Should have demo events
        assert len(events) > 0
        assert all(hasattr(e, 'title') for e in events)

    def test_create_event(self):
        """Test creating a new event."""
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        backend.connect()

        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        event = backend.create_event(
            title="Test Meeting",
            start_time=start,
            end_time=end,
            description="A test event"
        )

        assert event.title == "Test Meeting"
        assert event.id is not None
        assert event.source == "mock"

    def test_check_availability_free_slot(self):
        """Test availability check for free slot."""
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        backend.connect()

        # Check a far future slot (should be free)
        start = datetime.now() + timedelta(days=30)
        end = start + timedelta(hours=1)

        is_available, conflicts = backend.check_availability(start, end)

        assert is_available is True
        assert len(conflicts) == 0

    def test_delete_event(self):
        """Test deleting an event."""
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        backend.connect()

        # Create an event first
        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)
        event = backend.create_event(
            title="To Delete",
            start_time=start,
            end_time=end
        )

        # Delete it
        result = backend.delete_event(event.id)
        assert result is True

        # Try to delete non-existent
        result = backend.delete_event("nonexistent")
        assert result is False


class TestMockEmailBackend:
    """Tests for MockEmailBackend."""

    def test_connect(self):
        """Test backend connection."""
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        assert backend.connect() is True

    def test_list_unread_returns_demo_data(self):
        """Test listing unread emails returns demo data."""
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        backend.connect()

        emails = backend.list_unread()

        # Should have at least one unread demo email
        assert len(emails) >= 1
        assert all(hasattr(e, 'subject') for e in emails)

    def test_create_draft(self):
        """Test creating a draft email."""
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        backend.connect()

        draft = backend.create_draft(
            to_addresses=["test@example.com"],
            subject="Test Subject",
            body="Test body"
        )

        assert draft.subject == "Test Subject"
        assert draft.id is not None

    def test_send_email(self):
        """Test sending an email."""
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        backend.connect()

        email = backend.send_email(
            to_addresses=["test@example.com"],
            subject="Test Email",
            body="Hello!"
        )

        assert email.subject == "Test Email"
        assert email.is_read is True  # Sent emails are marked as read


class TestCalendarTool:
    """Tests for CalendarTool with mock backend."""

    def test_schedule_event(self):
        """Test scheduling an event via CalendarTool."""
        from tools.life.calendar_tool import CalendarTool
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        tool = CalendarTool(backend=backend)

        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=2)

        # Mock HITL confirmation
        with patch.object(tool, '_require_confirmation', return_value=True):
            result = tool.schedule_event(
                title="Test Event",
                start_time=start.isoformat(),
                end_time=end.isoformat(),
                description="A test"
            )

        assert result.success is True
        assert "Test Event" in result.message
        assert "mock" in result.message  # Shows backend

    def test_list_events(self):
        """Test listing events via CalendarTool."""
        from tools.life.calendar_tool import CalendarTool
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        tool = CalendarTool(backend=backend)

        result = tool.list_events(days=30)

        assert result.success is True
        # Should have some events from demo data or be empty with a message
        assert isinstance(result.data, list)

    def test_check_availability(self):
        """Test checking availability via CalendarTool."""
        from tools.life.calendar_tool import CalendarTool
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        tool = CalendarTool(backend=backend)

        start = datetime.now() + timedelta(days=30)
        end = start + timedelta(hours=1)

        result = tool.check_availability(
            start_time=start.isoformat(),
            end_time=end.isoformat()
        )

        assert result.success is True
        assert result.data.get("available") is True

    def test_invalid_date_format(self):
        """Test error handling for invalid date format."""
        from tools.life.calendar_tool import CalendarTool
        from tools.life.backends.mock_backend import MockCalendarBackend

        backend = MockCalendarBackend()
        tool = CalendarTool(backend=backend)

        result = tool.schedule_event(
            title="Test",
            start_time="invalid-date",
            end_time="also-invalid"
        )

        assert result.success is False
        assert result.error == "DateFormatError"


class TestEmailTool:
    """Tests for EmailTool with mock backend."""

    def test_draft_email(self):
        """Test drafting an email via EmailTool."""
        from tools.life.email_tool import EmailTool
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        tool = EmailTool(backend=backend)

        result = tool.draft_email(
            to="test@example.com",
            subject="Test Draft",
            body="Hello!"
        )

        assert result.success is True
        assert "Draft created" in result.message
        assert "mock" in result.message

    def test_send_email_with_confirmation(self):
        """Test sending email with HITL confirmation."""
        from tools.life.email_tool import EmailTool
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        tool = EmailTool(backend=backend)

        # Mock HITL confirmation
        with patch.object(tool, '_require_confirmation', return_value=True):
            result = tool.send_email(
                to="test@example.com",
                subject="Test Send",
                body="Hello!"
            )

        assert result.success is True
        assert "Sent email" in result.message

    def test_send_email_denied(self):
        """Test sending email when user denies confirmation."""
        from tools.life.email_tool import EmailTool
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        tool = EmailTool(backend=backend)

        # Mock HITL denial
        with patch.object(tool, '_require_confirmation', return_value=False):
            result = tool.send_email(
                to="test@example.com",
                subject="Test Send",
                body="Hello!"
            )

        assert result.success is False
        assert result.error == "UserDenied"

    def test_list_unread(self):
        """Test listing unread emails via EmailTool."""
        from tools.life.email_tool import EmailTool
        from tools.life.backends.mock_backend import MockEmailBackend

        backend = MockEmailBackend()
        tool = EmailTool(backend=backend)

        result = tool.list_unread(limit=5)

        assert result.success is True
        assert isinstance(result.data, list)


class TestBackendSelection:
    """Tests for backend auto-selection."""

    def test_calendar_defaults_to_mock(self):
        """Test that calendar defaults to mock backend."""
        from tools.life.backends import get_calendar_backend

        # Without env var, should return mock
        backend = get_calendar_backend()
        assert backend.name == "mock"

    def test_email_defaults_to_mock(self):
        """Test that email defaults to mock backend."""
        from tools.life.backends import get_email_backend

        # Without env var, should return mock
        backend = get_email_backend()
        assert backend.name == "mock"

    @patch.dict('os.environ', {'LIFE_CALENDAR_BACKEND': 'mock'})
    def test_calendar_mock_explicit(self):
        """Test explicit mock backend selection."""
        from tools.life.backends import get_calendar_backend

        backend = get_calendar_backend()
        assert backend.name == "mock"

    @patch.dict('os.environ', {'LIFE_EMAIL_BACKEND': 'mock'})
    def test_email_mock_explicit(self):
        """Test explicit mock backend selection."""
        from tools.life.backends import get_email_backend

        backend = get_email_backend()
        assert backend.name == "mock"
