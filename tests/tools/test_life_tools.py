"""
Tests for Life OS Tools (Browser, Calendar, Email)

NECESSARY Pattern Coverage:
- N: Normal operation (all basic capabilities)
- E: Edge cases (empty inputs, boundary values)
- C: Corner cases (special characters, mock mode)
- E: Error conditions (invalid actions, date formats)
- S: Security (HITL confirmation)
- S: Stress (multiple operations)
- A: Accessibility (clear error messages)
- R: Regression (consistent return types)
- Y: Yield tests (ToolResult pattern)

Constitutional compliance:
- Article I: Complete context (tools return full data)
- Article II: TDD (tests written first)
- Article III: Local enforcement (no external deps required)
- Article V: Human-in-the-loop for sensitive actions
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest


# =============================================================================
# Base Tool Tests
# =============================================================================

class TestToolResult:
    """Test ToolResult dataclass."""

    def test_tool_result_success(self):
        """
        Test AC-1.1: ToolResult with success=True.

        NECESSARY: N (Normal operation)
        """
        from tools.life.base import ToolResult

        result = ToolResult(success=True, message="Action completed")

        assert result.success is True
        assert result.message == "Action completed"
        assert result.data is None
        assert result.error is None

    def test_tool_result_failure(self):
        """
        Test AC-1.2: ToolResult with success=False.

        NECESSARY: E (Error condition)
        """
        from tools.life.base import ToolResult

        result = ToolResult(
            success=False,
            message="Action failed",
            error="SomeError"
        )

        assert result.success is False
        assert result.error == "SomeError"

    def test_tool_result_with_data(self):
        """
        Test AC-1.3: ToolResult with data payload.

        NECESSARY: N (Normal operation)
        """
        from tools.life.base import ToolResult

        result = ToolResult(
            success=True,
            message="Data retrieved",
            data={"key": "value", "count": 42}
        )

        assert result.data is not None
        assert result.data["key"] == "value"
        assert result.data["count"] == 42


# =============================================================================
# Browser Tool Tests
# =============================================================================

class TestBrowserTool:
    """Test BrowserTool functionality."""

    def test_browser_init(self):
        """
        Test AC-2.1: BrowserTool initializes correctly.

        NECESSARY: N (Normal operation)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool()

        assert browser.name == "Browser"
        assert "search" in browser.get_capabilities()
        assert "visit" in browser.get_capabilities()

    def test_browser_mock_mode_search(self):
        """
        Test AC-2.2: BrowserTool search in mock mode.

        NECESSARY: N (Normal operation - mock mode)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool(mock_mode=True)

        result = browser.search("Italian restaurant SF")

        assert result.success is True
        assert "mock result" in result.message.lower() or "found" in result.message.lower()
        assert result.data is not None

    def test_browser_execute_search(self):
        """
        Test AC-2.3: BrowserTool execute with search action.

        NECESSARY: N (Normal operation)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool(mock_mode=True)

        result = browser.execute("search", query="test query")

        assert result.success is True

    def test_browser_execute_unknown_action(self):
        """
        Test AC-2.4: BrowserTool execute with unknown action.

        NECESSARY: E (Error condition)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool(mock_mode=True)

        result = browser.execute("unknown_action")

        assert result.success is False
        assert result.error == "InvalidAction"

    def test_browser_visit_failure(self):
        """
        Test AC-2.5: BrowserTool visit with invalid URL.

        NECESSARY: E (Error condition)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool()

        result = browser.visit("http://invalid-url-that-does-not-exist-12345.com")

        assert result.success is False
        assert result.error == "VisitError"

    def test_browser_search_with_num_results(self):
        """
        Test AC-2.6: BrowserTool search with custom num_results.

        NECESSARY: E (Edge case - parameter variation)
        """
        from tools.life.browser_tool import BrowserTool

        browser = BrowserTool(mock_mode=True)

        result = browser.search("test", num_results=3)

        assert result.success is True


# =============================================================================
# Calendar Tool Tests
# =============================================================================

class TestCalendarTool:
    """Test CalendarTool functionality."""

    def test_calendar_init(self):
        """
        Test AC-3.1: CalendarTool initializes with demo data.

        NECESSARY: N (Normal operation)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        assert calendar.name == "Calendar"
        assert "schedule_event" in calendar.get_capabilities()
        assert "list_events" in calendar.get_capabilities()
        assert "check_availability" in calendar.get_capabilities()
        # Should have demo events
        assert len(calendar._events) > 0

    def test_calendar_list_events(self):
        """
        Test AC-3.2: CalendarTool list events.

        NECESSARY: N (Normal operation)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        result = calendar.list_events(days=30)

        assert result.success is True
        # Should have at least one upcoming event from demo data
        assert result.data is not None

    def test_calendar_schedule_event(self):
        """
        Test AC-3.3: CalendarTool schedule new event.

        NECESSARY: N (Normal operation)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        tomorrow = datetime.now() + timedelta(days=1)
        start = tomorrow.replace(hour=14, minute=0).isoformat()
        end = tomorrow.replace(hour=15, minute=0).isoformat()

        result = calendar.schedule_event(
            title="Test Meeting",
            start_time=start,
            end_time=end,
            description="A test meeting"
        )

        assert result.success is True
        assert "Test Meeting" in result.message
        assert result.data["event_id"] is not None

    def test_calendar_schedule_invalid_date(self):
        """
        Test AC-3.4: CalendarTool schedule with invalid date format.

        NECESSARY: E (Error condition)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        result = calendar.schedule_event(
            title="Test",
            start_time="not-a-date",
            end_time="also-not-a-date"
        )

        assert result.success is False
        assert result.error == "DateFormatError"

    def test_calendar_check_availability_free(self):
        """
        Test AC-3.5: CalendarTool check availability - slot is free.

        NECESSARY: N (Normal operation)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        # Check a far future slot that's definitely free
        future = datetime.now() + timedelta(days=30)
        start = future.replace(hour=10, minute=0).isoformat()
        end = future.replace(hour=11, minute=0).isoformat()

        result = calendar.check_availability(start_time=start, end_time=end)

        assert result.success is True
        assert "free" in result.message.lower()

    def test_calendar_execute_unknown_action(self):
        """
        Test AC-3.6: CalendarTool execute with unknown action.

        NECESSARY: E (Error condition)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        result = calendar.execute("unknown_action")

        assert result.success is False
        assert result.error == "InvalidAction"

    def test_calendar_list_events_empty(self):
        """
        Test AC-3.7: CalendarTool list events when calendar is empty.

        NECESSARY: E (Edge case - empty calendar)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()
        # Clear demo events
        calendar._events = {}

        result = calendar.list_events(days=7)

        assert result.success is True
        assert "clear" in result.message.lower()


# =============================================================================
# Email Tool Tests
# =============================================================================

class TestEmailTool:
    """Test EmailTool functionality."""

    def test_email_init(self):
        """
        Test AC-4.1: EmailTool initializes with demo inbox.

        NECESSARY: N (Normal operation)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        assert email.name == "Email"
        assert "draft_email" in email.get_capabilities()
        assert "send_email" in email.get_capabilities()
        assert "list_unread" in email.get_capabilities()
        # Should have demo inbox
        assert len(email._inbox) > 0

    def test_email_draft(self):
        """
        Test AC-4.2: EmailTool create draft.

        NECESSARY: N (Normal operation)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        result = email.draft_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test body content"
        )

        assert result.success is True
        assert result.data["draft_id"] is not None
        assert "Draft created" in result.message

    def test_email_send(self):
        """
        Test AC-4.3: EmailTool send email (with HITL auto-approved).

        NECESSARY: N (Normal operation)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        result = email.send_email(
            to="recipient@example.com",
            subject="Test",
            body="Test content"
        )

        assert result.success is True
        assert "Sent" in result.message

    def test_email_send_from_draft(self):
        """
        Test AC-4.4: EmailTool send from existing draft.

        NECESSARY: N (Normal operation)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        # Create draft first
        draft_result = email.draft_email(
            to="test@example.com",
            subject="Draft Subject",
            body="Draft body"
        )
        draft_id = draft_result.data["draft_id"]

        # Send from draft
        send_result = email.send_email(
            to="test@example.com",
            subject="Draft Subject",
            body="Draft body",
            draft_id=draft_id
        )

        assert send_result.success is True
        # Draft should be deleted after sending
        assert draft_id not in email._drafts

    def test_email_list_unread(self):
        """
        Test AC-4.5: EmailTool list unread emails.

        NECESSARY: N (Normal operation)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        result = email.list_unread()

        assert result.success is True
        # Demo inbox has at least one unread
        assert len(result.data) >= 1

    def test_email_list_unread_with_limit(self):
        """
        Test AC-4.6: EmailTool list unread with limit.

        NECESSARY: E (Edge case - limit parameter)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        result = email.list_unread(limit=1)

        assert result.success is True
        assert len(result.data) <= 1

    def test_email_execute_unknown_action(self):
        """
        Test AC-4.7: EmailTool execute with unknown action.

        NECESSARY: E (Error condition)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        result = email.execute("unknown_action")

        assert result.success is False
        assert result.error == "InvalidAction"

    def test_email_inbox_zero(self):
        """
        Test AC-4.8: EmailTool list unread when inbox is empty.

        NECESSARY: E (Edge case - inbox zero)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()
        # Mark all as read
        for msg in email._inbox:
            msg["read"] = True

        result = email.list_unread()

        assert result.success is True
        assert "Inbox Zero" in result.message or len(result.data) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestLifeToolsIntegration:
    """Integration tests for Life Tools."""

    def test_all_tools_have_capabilities(self):
        """
        Test AC-5.1: All Life Tools implement get_capabilities.

        NECESSARY: N (Normal - interface compliance)
        """
        from tools.life.browser_tool import BrowserTool
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        tools = [BrowserTool(mock_mode=True), CalendarTool(), EmailTool()]

        for tool in tools:
            caps = tool.get_capabilities()
            assert isinstance(caps, list)
            assert len(caps) > 0
            assert all(isinstance(c, str) for c in caps)

    def test_all_tools_return_tool_result(self):
        """
        Test AC-5.2: All Life Tools return ToolResult from execute.

        NECESSARY: R (Regression - consistent return type)
        """
        from tools.life.base import ToolResult
        from tools.life.browser_tool import BrowserTool
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        browser = BrowserTool(mock_mode=True)
        calendar = CalendarTool()
        email = EmailTool()

        # Execute actions
        results = [
            browser.execute("search", query="test"),
            calendar.execute("list_events", days=7),
            email.execute("list_unread"),
        ]

        for result in results:
            assert isinstance(result, ToolResult)
            assert isinstance(result.success, bool)
            assert isinstance(result.message, str)

    def test_workflow_search_and_schedule(self):
        """
        Test AC-5.3: Workflow - search for restaurant, schedule dinner.

        NECESSARY: N (Normal - multi-tool workflow)
        """
        from tools.life.browser_tool import BrowserTool
        from tools.life.calendar_tool import CalendarTool

        browser = BrowserTool(mock_mode=True)
        calendar = CalendarTool()

        # Search for restaurant
        search_result = browser.search("Italian restaurant SF")
        assert search_result.success is True

        # Schedule dinner
        tomorrow = datetime.now() + timedelta(days=1)
        start = tomorrow.replace(hour=19, minute=0).isoformat()
        end = tomorrow.replace(hour=21, minute=0).isoformat()

        schedule_result = calendar.schedule_event(
            title="Dinner at Luigi's",
            start_time=start,
            end_time=end,
            description="Found via browser search"
        )
        assert schedule_result.success is True

    def test_workflow_draft_and_send_email(self):
        """
        Test AC-5.4: Workflow - draft email, then send.

        NECESSARY: N (Normal - multi-step workflow)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        # Create draft
        draft_result = email.draft_email(
            to="friend@example.com",
            subject="Dinner Plans",
            body="Let's meet at 7pm!"
        )
        assert draft_result.success is True
        draft_id = draft_result.data["draft_id"]

        # Verify draft exists
        assert draft_id in email._drafts

        # Send from draft
        send_result = email.send_email(
            to="friend@example.com",
            subject="Dinner Plans",
            body="Let's meet at 7pm!",
            draft_id=draft_id
        )
        assert send_result.success is True

        # Draft should be removed
        assert draft_id not in email._drafts


# =============================================================================
# Security Tests
# =============================================================================

class TestLifeToolsSecurity:
    """Security tests for Life Tools (HITL confirmation)."""

    def test_calendar_requires_confirmation(self):
        """
        Test AC-6.1: CalendarTool schedule requires HITL confirmation.

        NECESSARY: S (Security - HITL)
        """
        from tools.life.calendar_tool import CalendarTool

        calendar = CalendarTool()

        # Mock _require_confirmation to deny
        original_confirm = calendar._require_confirmation
        calendar._require_confirmation = lambda action, details: False

        tomorrow = datetime.now() + timedelta(days=1)
        result = calendar.schedule_event(
            title="Test",
            start_time=tomorrow.isoformat(),
            end_time=(tomorrow + timedelta(hours=1)).isoformat()
        )

        assert result.success is False
        assert result.error == "UserDenied"

        # Restore
        calendar._require_confirmation = original_confirm

    def test_email_send_requires_confirmation(self):
        """
        Test AC-6.2: EmailTool send requires HITL confirmation.

        NECESSARY: S (Security - HITL)
        """
        from tools.life.email_tool import EmailTool

        email = EmailTool()

        # Mock _require_confirmation to deny
        original_confirm = email._require_confirmation
        email._require_confirmation = lambda action, details: False

        result = email.send_email(
            to="test@example.com",
            subject="Test",
            body="Test"
        )

        assert result.success is False
        assert result.error == "UserDenied"

        # Restore
        email._require_confirmation = original_confirm


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
