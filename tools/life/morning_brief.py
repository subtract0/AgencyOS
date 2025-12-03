"""
Morning Brief Generator
=======================

Generates a daily morning briefing with calendar, email, and task summaries.
Designed to run via Night Shift at a configured time (default: 6 AM).

The brief includes:
- Today's calendar events with prep notes
- Email triage (urgent, needs response, FYI)
- Suggested priorities for the day
- Weather and commute info (if configured)

Usage:
    # Generate brief manually
    python tools/life/morning_brief.py

    # Generate and save to file
    python tools/life/morning_brief.py --save

    # Night Shift integration (runs at scheduled time)
    Configured in Night Shift backlog with type: "morning_brief"

Configuration:
    MORNING_BRIEF_TIME: Time to generate (default: "06:00")
    MORNING_BRIEF_EMAIL: Email address to send brief (optional)
    MORNING_BRIEF_SAVE_PATH: Where to save briefs (default: ~/.agency/briefs/)
"""

import argparse
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.life.calendar_tool import CalendarTool
from tools.life.email_tool import EmailTool
from tools.life.base import ToolResult


@dataclass
class BriefSection:
    """A section of the morning brief."""
    title: str
    icon: str
    content: str
    priority: int = 0  # Higher = more important


@dataclass
class MorningBrief:
    """Complete morning brief."""
    date: datetime
    greeting: str
    sections: list[BriefSection] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """Render brief as markdown."""
        lines = [
            f"# Morning Brief - {self.date.strftime('%A, %B %d, %Y')}",
            "",
            f"> {self.greeting}",
            "",
            f"*Generated at {self.generated_at.strftime('%I:%M %p')}*",
            "",
            "---",
            "",
        ]

        # Sort sections by priority (highest first)
        sorted_sections = sorted(self.sections, key=lambda s: -s.priority)

        for section in sorted_sections:
            lines.append(f"## {section.icon} {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Have a productive day!*")

        return "\n".join(lines)


class MorningBriefGenerator:
    """
    Generates comprehensive morning briefings.

    Pulls data from:
    - Calendar (today's events, upcoming deadlines)
    - Email (unread count, urgent items)
    - Tasks (from backlog if available)
    """

    def __init__(
        self,
        calendar_tool: Optional[CalendarTool] = None,
        email_tool: Optional[EmailTool] = None,
    ):
        """
        Initialize the generator.

        Args:
            calendar_tool: Optional CalendarTool instance (creates one if not provided)
            email_tool: Optional EmailTool instance (creates one if not provided)
        """
        self._calendar = calendar_tool
        self._email = email_tool
        self._briefs_dir = Path.home() / ".agency" / "briefs"
        self._briefs_dir.mkdir(parents=True, exist_ok=True)

    def _get_calendar(self) -> CalendarTool:
        """Lazy-load calendar tool."""
        if self._calendar is None:
            self._calendar = CalendarTool()
        return self._calendar

    def _get_email(self) -> EmailTool:
        """Lazy-load email tool."""
        if self._email is None:
            self._email = EmailTool()
        return self._email

    def _get_greeting(self) -> str:
        """Generate a contextual greeting."""
        hour = datetime.now().hour
        day = datetime.now().strftime("%A")

        if hour < 12:
            time_greeting = "Good morning"
        elif hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"

        greetings = {
            "Monday": f"{time_greeting}! New week, fresh start.",
            "Tuesday": f"{time_greeting}! Let's build momentum.",
            "Wednesday": f"{time_greeting}! Halfway through the week.",
            "Thursday": f"{time_greeting}! Almost there.",
            "Friday": f"{time_greeting}! Finish strong, then rest.",
            "Saturday": f"{time_greeting}! Enjoy your weekend.",
            "Sunday": f"{time_greeting}! A day for rest and reflection.",
        }

        return greetings.get(day, f"{time_greeting}!")

    def _generate_calendar_section(self) -> BriefSection:
        """Generate calendar section of the brief."""
        try:
            calendar = self._get_calendar()
            result = calendar.list_events(days=1)

            if not result.success:
                return BriefSection(
                    title="TODAY'S SCHEDULE",
                    icon="📅",
                    content=f"*Could not load calendar: {result.message}*",
                    priority=10,
                )

            events = result.data or []

            if not events:
                content = "Your calendar is clear today. Time for deep work!"
            else:
                lines = []
                for event in events:
                    start = datetime.fromisoformat(event["start_time"])
                    title = event["title"]
                    lines.append(f"- **{start.strftime('%I:%M %p')}**: {title}")

                    # Add prep suggestion for meetings
                    if any(word in title.lower() for word in ["meeting", "call", "sync", "1:1"]):
                        lines.append(f"  - *Prep: Review notes and agenda*")

                content = "\n".join(lines)

            return BriefSection(
                title="TODAY'S SCHEDULE",
                icon="📅",
                content=content,
                priority=10,
            )

        except Exception as e:
            return BriefSection(
                title="TODAY'S SCHEDULE",
                icon="📅",
                content=f"*Calendar unavailable: {e}*",
                priority=10,
            )

    def _generate_email_section(self) -> BriefSection:
        """Generate email triage section of the brief."""
        try:
            email = self._get_email()
            result = email.list_unread(limit=10)

            if not result.success:
                return BriefSection(
                    title="EMAIL TRIAGE",
                    icon="📧",
                    content=f"*Could not load emails: {result.message}*",
                    priority=8,
                )

            emails = result.data or []

            if not emails:
                content = "**Inbox Zero!** No unread messages."
            else:
                # Categorize emails
                urgent = []
                needs_response = []
                fyi = []

                for email_item in emails:
                    subject = email_item.get("subject", "").lower()
                    sender = email_item.get("from", "")

                    # Simple heuristic categorization
                    if any(word in subject for word in ["urgent", "asap", "important", "action required"]):
                        urgent.append(email_item)
                    elif any(word in subject for word in ["re:", "reply", "question", "?"]):
                        needs_response.append(email_item)
                    else:
                        fyi.append(email_item)

                lines = []

                if urgent:
                    lines.append("### 🔴 Urgent")
                    for e in urgent[:3]:
                        lines.append(f"- **{e.get('from', 'Unknown')}**: {e.get('subject', 'No subject')}")

                if needs_response:
                    lines.append("")
                    lines.append("### 🟡 Needs Response")
                    for e in needs_response[:3]:
                        lines.append(f"- **{e.get('from', 'Unknown')}**: {e.get('subject', 'No subject')}")

                if fyi:
                    lines.append("")
                    lines.append(f"### 🟢 FYI ({len(fyi)} more)")
                    for e in fyi[:2]:
                        lines.append(f"- {e.get('from', 'Unknown')}: {e.get('subject', 'No subject')}")

                content = "\n".join(lines)

            return BriefSection(
                title="EMAIL TRIAGE",
                icon="📧",
                content=content,
                priority=8,
            )

        except Exception as e:
            return BriefSection(
                title="EMAIL TRIAGE",
                icon="📧",
                content=f"*Email unavailable: {e}*",
                priority=8,
            )

    def _generate_priorities_section(self, calendar_events: list) -> BriefSection:
        """Generate suggested priorities section."""
        suggestions = []

        # Time-based suggestions
        hour = datetime.now().hour
        if hour < 10:
            suggestions.append("Morning is best for deep work - tackle your hardest task first")

        # Calendar-based suggestions
        if calendar_events:
            first_event = calendar_events[0] if calendar_events else None
            if first_event:
                start = datetime.fromisoformat(first_event["start_time"])
                time_until = start - datetime.now()
                if time_until.total_seconds() > 3600:  # More than 1 hour
                    hours = int(time_until.total_seconds() // 3600)
                    suggestions.append(f"You have {hours} hour(s) of focus time before your first event")

        # Day-based suggestions
        day = datetime.now().strftime("%A")
        if day == "Friday":
            suggestions.append("Consider wrapping up loose ends before the weekend")
        elif day == "Monday":
            suggestions.append("Start with a quick planning session to set the week's priorities")

        if not suggestions:
            suggestions.append("No specific suggestions - trust your judgment today!")

        content = "\n".join([f"- {s}" for s in suggestions])

        return BriefSection(
            title="SUGGESTED PRIORITIES",
            icon="🎯",
            content=content,
            priority=5,
        )

    def _generate_focus_section(self) -> BriefSection:
        """Generate focus time analysis."""
        try:
            calendar = self._get_calendar()
            result = calendar.list_events(days=1)

            if not result.success or not result.data:
                return BriefSection(
                    title="FOCUS TIME",
                    icon="⏰",
                    content="Full day available for focus work!",
                    priority=3,
                )

            events = result.data
            # Calculate gaps between events
            now = datetime.now()
            work_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
            work_end = now.replace(hour=18, minute=0, second=0, microsecond=0)

            # Simple calculation: subtract meeting time from work day
            meeting_hours = 0
            for event in events:
                start = datetime.fromisoformat(event["start_time"])
                end = datetime.fromisoformat(event["end_time"])
                if start >= work_start and end <= work_end:
                    meeting_hours += (end - start).total_seconds() / 3600

            focus_hours = 8 - meeting_hours  # Assuming 8-hour workday

            if focus_hours >= 6:
                quality = "Excellent"
                emoji = "🟢"
            elif focus_hours >= 4:
                quality = "Good"
                emoji = "🟡"
            else:
                quality = "Limited"
                emoji = "🔴"

            content = f"{emoji} **{quality}**: ~{focus_hours:.1f} hours of potential focus time today"

            return BriefSection(
                title="FOCUS TIME",
                icon="⏰",
                content=content,
                priority=3,
            )

        except Exception:
            return BriefSection(
                title="FOCUS TIME",
                icon="⏰",
                content="Unable to calculate focus time",
                priority=3,
            )

    def generate(self) -> MorningBrief:
        """
        Generate a complete morning brief.

        Returns:
            MorningBrief object with all sections
        """
        brief = MorningBrief(
            date=datetime.now(),
            greeting=self._get_greeting(),
        )

        # Generate calendar section first (we'll use events for other sections)
        calendar_section = self._generate_calendar_section()
        brief.sections.append(calendar_section)

        # Get events for other sections
        try:
            calendar = self._get_calendar()
            events_result = calendar.list_events(days=1)
            events = events_result.data if events_result.success else []
        except Exception:
            events = []

        # Generate other sections
        brief.sections.append(self._generate_email_section())
        brief.sections.append(self._generate_priorities_section(events))
        brief.sections.append(self._generate_focus_section())

        return brief

    def save(self, brief: MorningBrief, path: Optional[Path] = None) -> Path:
        """
        Save brief to a markdown file.

        Args:
            brief: The brief to save
            path: Optional custom path (defaults to ~/.agency/briefs/YYYY-MM-DD.md)

        Returns:
            Path to the saved file
        """
        if path is None:
            filename = f"{brief.date.strftime('%Y-%m-%d')}.md"
            path = self._briefs_dir / filename

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(brief.to_markdown())

        return path

    def get_latest_brief(self) -> Optional[Path]:
        """Get path to the most recent brief."""
        briefs = sorted(self._briefs_dir.glob("*.md"), reverse=True)
        return briefs[0] if briefs else None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate morning brief"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save brief to file",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Custom output path",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Don't print to console",
    )

    args = parser.parse_args()

    # Generate brief
    generator = MorningBriefGenerator()
    brief = generator.generate()

    # Output
    if not args.quiet:
        print(brief.to_markdown())

    if args.save or args.output:
        output_path = Path(args.output) if args.output else None
        saved_path = generator.save(brief, output_path)
        if not args.quiet:
            print(f"\n📁 Saved to: {saved_path}")


if __name__ == "__main__":
    main()
