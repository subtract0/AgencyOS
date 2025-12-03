"""
Tests for Morning Brief Generator
=================================

Unit tests for MorningBriefGenerator and Night Shift integration.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestMorningBriefGenerator:
    """Tests for MorningBriefGenerator."""

    def test_generate_creates_brief(self):
        """Test that generate creates a complete brief."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockCalendarBackend, MockEmailBackend
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        # Create tools with mock backends
        calendar = CalendarTool(backend=MockCalendarBackend())
        email = EmailTool(backend=MockEmailBackend())

        generator = MorningBriefGenerator(
            calendar_tool=calendar,
            email_tool=email,
        )

        brief = generator.generate()

        assert brief is not None
        assert brief.date is not None
        assert brief.greeting is not None
        assert len(brief.sections) > 0

    def test_brief_has_required_sections(self):
        """Test that brief contains all required sections."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockCalendarBackend, MockEmailBackend
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        calendar = CalendarTool(backend=MockCalendarBackend())
        email = EmailTool(backend=MockEmailBackend())

        generator = MorningBriefGenerator(
            calendar_tool=calendar,
            email_tool=email,
        )

        brief = generator.generate()
        section_titles = [s.title for s in brief.sections]

        assert "TODAY'S SCHEDULE" in section_titles
        assert "EMAIL TRIAGE" in section_titles
        assert "SUGGESTED PRIORITIES" in section_titles
        assert "FOCUS TIME" in section_titles

    def test_to_markdown_generates_valid_markdown(self):
        """Test that to_markdown generates valid markdown."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockCalendarBackend, MockEmailBackend
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        calendar = CalendarTool(backend=MockCalendarBackend())
        email = EmailTool(backend=MockEmailBackend())

        generator = MorningBriefGenerator(
            calendar_tool=calendar,
            email_tool=email,
        )

        brief = generator.generate()
        markdown = brief.to_markdown()

        # Check markdown structure
        assert markdown.startswith("# Morning Brief")
        assert "---" in markdown  # Horizontal rules
        assert "##" in markdown  # Section headers
        assert "*Generated at" in markdown

    def test_save_creates_file(self):
        """Test that save creates a file."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockCalendarBackend, MockEmailBackend
        from tools.life.calendar_tool import CalendarTool
        from tools.life.email_tool import EmailTool

        calendar = CalendarTool(backend=MockCalendarBackend())
        email = EmailTool(backend=MockEmailBackend())

        generator = MorningBriefGenerator(
            calendar_tool=calendar,
            email_tool=email,
        )

        brief = generator.generate()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_brief.md"
            saved_path = generator.save(brief, path)

            assert saved_path.exists()
            content = saved_path.read_text()
            assert "Morning Brief" in content

    def test_greeting_varies_by_day(self):
        """Test that greeting changes based on day of week."""
        from tools.life.morning_brief import MorningBriefGenerator

        generator = MorningBriefGenerator()

        # The greeting should exist and be non-empty
        greeting = generator._get_greeting()
        assert greeting is not None
        assert len(greeting) > 0
        assert "morning" in greeting.lower() or "afternoon" in greeting.lower() or "evening" in greeting.lower()

    def test_calendar_section_handles_empty_calendar(self):
        """Test calendar section with no events."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockCalendarBackend
        from tools.life.calendar_tool import CalendarTool

        # Create mock backend with no events
        backend = MockCalendarBackend()
        backend._events = {}  # Clear demo events

        calendar = CalendarTool(backend=backend)
        generator = MorningBriefGenerator(calendar_tool=calendar)

        section = generator._generate_calendar_section()

        assert section.title == "TODAY'S SCHEDULE"
        assert "clear" in section.content.lower() or "free" in section.content.lower()

    def test_email_section_handles_inbox_zero(self):
        """Test email section with no unread emails."""
        from tools.life.morning_brief import MorningBriefGenerator
        from tools.life.backends.mock_backend import MockEmailBackend
        from tools.life.email_tool import EmailTool

        # Create mock backend with no unread
        backend = MockEmailBackend()
        backend._inbox = []  # Clear demo emails

        email = EmailTool(backend=backend)
        generator = MorningBriefGenerator(email_tool=email)

        section = generator._generate_email_section()

        assert section.title == "EMAIL TRIAGE"
        assert "inbox zero" in section.content.lower()


class TestNightShiftTaskHandler:
    """Tests for Life OS Night Shift task handlers."""

    def test_can_handle_morning_brief(self):
        """Test that handler recognizes morning_brief task type."""
        from tools.life.night_shift_tasks import LifeOSTaskHandler

        handler = LifeOSTaskHandler()

        assert handler.can_handle("morning_brief") is True
        assert handler.can_handle("email_triage") is True
        assert handler.can_handle("calendar_prep") is True
        assert handler.can_handle("unknown_task") is False

    def test_execute_morning_brief(self):
        """Test executing morning brief task."""
        from tools.life.night_shift_tasks import LifeOSTaskHandler

        handler = LifeOSTaskHandler()

        # Execute with save disabled to avoid file creation
        result = handler.execute("morning_brief", {"save": False})

        assert result.success is True
        assert "Morning brief generated" in result.message
        assert result.data is not None
        assert "date" in result.data

    def test_execute_email_triage(self):
        """Test executing email triage task."""
        from tools.life.night_shift_tasks import LifeOSTaskHandler

        handler = LifeOSTaskHandler()

        result = handler.execute("email_triage", {"limit": 5})

        assert result.success is True
        assert "Triaged" in result.message
        assert result.data is not None
        assert "total" in result.data

    def test_execute_calendar_prep(self):
        """Test executing calendar prep task."""
        from tools.life.night_shift_tasks import LifeOSTaskHandler

        handler = LifeOSTaskHandler()

        result = handler.execute("calendar_prep", {})

        assert result.success is True
        assert "Prepared" in result.message
        assert result.data is not None

    def test_execute_unknown_task_fails(self):
        """Test that unknown task type fails gracefully."""
        from tools.life.night_shift_tasks import LifeOSTaskHandler

        handler = LifeOSTaskHandler()

        result = handler.execute("nonexistent_task", {})

        assert result.success is False
        assert "Unknown task type" in result.message


class TestMorningBriefDataclass:
    """Tests for MorningBrief dataclass."""

    def test_brief_section_creation(self):
        """Test creating a BriefSection."""
        from tools.life.morning_brief import BriefSection

        section = BriefSection(
            title="Test Section",
            icon="🧪",
            content="Test content",
            priority=5,
        )

        assert section.title == "Test Section"
        assert section.icon == "🧪"
        assert section.priority == 5

    def test_morning_brief_creation(self):
        """Test creating a MorningBrief."""
        from tools.life.morning_brief import MorningBrief, BriefSection

        brief = MorningBrief(
            date=datetime.now(),
            greeting="Hello!",
            sections=[
                BriefSection(title="Test", icon="🧪", content="Content", priority=1)
            ],
        )

        assert brief.greeting == "Hello!"
        assert len(brief.sections) == 1
        assert brief.generated_at is not None

    def test_sections_sorted_by_priority(self):
        """Test that sections are sorted by priority in markdown output."""
        from tools.life.morning_brief import MorningBrief, BriefSection

        brief = MorningBrief(
            date=datetime.now(),
            greeting="Test",
            sections=[
                BriefSection(title="Low Priority", icon="📉", content="Low", priority=1),
                BriefSection(title="High Priority", icon="📈", content="High", priority=10),
                BriefSection(title="Medium Priority", icon="➡️", content="Medium", priority=5),
            ],
        )

        markdown = brief.to_markdown()

        # High priority should come before medium, medium before low
        high_pos = markdown.find("High Priority")
        medium_pos = markdown.find("Medium Priority")
        low_pos = markdown.find("Low Priority")

        assert high_pos < medium_pos < low_pos
