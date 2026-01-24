#!/usr/bin/env python3
"""
Operator - Your 24/7 AI Assistant
=================================

Text-based interface for testing without voice.
Voice mode available via voice_loop.py.

Usage:
    python operator.py              # Interactive text mode
    python operator.py "check email" # Single command
    python operator.py --setup      # Setup Google OAuth
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.env_loader import load_agency_env
load_agency_env()

from tools.life.clock_tool import ClockTool
from tools.life.base import ToolResult

# Try to import Second Brain
try:
    from second_brain.lib.brain import SecondBrain
    BRAIN_AVAILABLE = True
except Exception:
    BRAIN_AVAILABLE = False

# Try to import Google tools (may fail if not configured)
try:
    from tools.life.email_tool import EmailTool
    from tools.life.calendar_tool import CalendarTool
    GOOGLE_AVAILABLE = True
except Exception as e:
    GOOGLE_AVAILABLE = False
    GOOGLE_ERROR = str(e)


class Operator:
    """Text-based Operator interface."""

    def __init__(self):
        self.tools = {
            "clock": ClockTool(),
        }

        if GOOGLE_AVAILABLE:
            try:
                self.tools["email"] = EmailTool()
                self.tools["calendar"] = CalendarTool()
            except Exception as e:
                print(f"⚠️  Google tools not available: {e}")

        # Second Brain
        if BRAIN_AVAILABLE:
            self.brain = SecondBrain()
        else:
            self.brain = None

    def process(self, command: str) -> str:
        """Process a natural language command."""
        cmd_lower = command.lower()

        # Time/Clock
        if any(w in cmd_lower for w in ["time", "uhr", "zeit", "clock"]):
            result = self.tools["clock"].execute("get_current_time")
            return result.message

        # Date
        if any(w in cmd_lower for w in ["date", "datum", "today", "heute"]):
            result = self.tools["clock"].execute("get_current_time")
            return result.message

        # Email
        if any(w in cmd_lower for w in ["email", "mail", "inbox", "unread"]):
            if "email" not in self.tools:
                return self._google_setup_hint("email")
            try:
                result = self.tools["email"].execute("list_unread")
                if result.success:
                    emails = result.data.get("emails", [])
                    if not emails:
                        return "📭 No unread emails."
                    response = f"📬 {len(emails)} unread email(s):\n"
                    for e in emails[:5]:
                        response += f"  • {e.get('from', 'Unknown')}: {e.get('subject', 'No subject')}\n"
                    return response
                else:
                    if "invalid_grant" in result.message:
                        return self._google_reauth_hint()
                    return f"❌ {result.message}"
            except Exception as e:
                if "invalid_grant" in str(e):
                    return self._google_reauth_hint()
                return f"❌ Email error: {e}"

        # Calendar
        if any(w in cmd_lower for w in ["calendar", "kalender", "termine", "events", "schedule", "meeting"]):
            if "calendar" not in self.tools:
                return self._google_setup_hint("calendar")
            try:
                result = self.tools["calendar"].execute("list_events")
                if result.success:
                    events = result.data.get("events", [])
                    if not events:
                        return "📅 No upcoming events."
                    response = f"📅 {len(events)} upcoming event(s):\n"
                    for e in events[:5]:
                        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                        response += f"  • {e.get('summary', 'No title')} - {start}\n"
                    return response
                else:
                    if "invalid_grant" in result.message:
                        return self._google_reauth_hint()
                    return f"❌ {result.message}"
            except Exception as e:
                if "invalid_grant" in str(e):
                    return self._google_reauth_hint()
                return f"❌ Calendar error: {e}"

        # Second Brain - Capture
        if any(w in cmd_lower for w in ["capture", "remember", "note", "brain", "merke", "notiz"]):
            if not self.brain:
                return "❌ Second Brain not available."
            # Extract the thought (after the keyword)
            thought = command
            for keyword in ["capture:", "remember:", "note:", "brain:", "merke:", "notiz:"]:
                if keyword in cmd_lower:
                    thought = command.split(keyword, 1)[-1].strip()
                    break
            result = self.brain.capture(thought)
            return f"🧠 {result['message']}"

        # Second Brain - Daily Digest
        if any(w in cmd_lower for w in ["daily", "digest", "today", "priorities"]):
            if not self.brain:
                return "❌ Second Brain not available."
            return self.brain.daily_digest()

        # Second Brain - Status
        if "brain status" in cmd_lower:
            if not self.brain:
                return "❌ Second Brain not available."
            status = self.brain.get_status()
            return f"🧠 Second Brain: {status['stats']['projects']} projects, {status['stats']['ideas']} ideas, {status['needs_review']} need review"

        # Help
        if any(w in cmd_lower for w in ["help", "hilfe", "commands", "befehle"]):
            return self._help()

        # Status
        if any(w in cmd_lower for w in ["status", "health"]):
            return self._status()

        # Unknown
        return f"🤔 I don't understand '{command}'. Try 'help' for available commands."

    def _google_setup_hint(self, service: str) -> str:
        return f"""❌ {service.title()} not configured.

Run this to set up Google:
    python tools/life/operator.py --setup
"""

    def _google_reauth_hint(self) -> str:
        return """🔐 Google token expired. Re-authenticate:

    rm ~/.config/agencyos/google/token.json
    python tools/life/operator.py --setup
"""

    def _help(self) -> str:
        return """🤖 Operator Commands:

Time & Date:
  "what time is it" / "wie spät ist es"
  "what's the date" / "welches datum"

Second Brain:
  "capture: <thought>" / "remember: <thought>"
  "daily" / "digest" - Daily priorities
  "brain status" - Second Brain stats

Email (requires Google setup):
  "check my email" / "ungelesene mails"

Calendar (requires Google setup):
  "my calendar" / "meine termine"

System:
  "status" - Show system status
  "help" - Show this help
"""

    def _status(self) -> str:
        status = "🤖 Operator Status\n" + "=" * 30 + "\n"

        # Clock (always works)
        status += "✅ Clock: Working\n"

        # Google tools
        if "email" in self.tools:
            try:
                self.tools["email"].service
                status += "✅ Email: Connected\n"
            except:
                status += "⚠️  Email: Token expired\n"
        else:
            status += "❌ Email: Not configured\n"

        if "calendar" in self.tools:
            try:
                self.tools["calendar"].service
                status += "✅ Calendar: Connected\n"
            except:
                status += "⚠️  Calendar: Token expired\n"
        else:
            status += "❌ Calendar: Not configured\n"

        status += "\nRun 'python operator.py --setup' to configure Google."
        return status


def setup_google():
    """Interactive Google OAuth setup."""
    print("""
🔧 Google OAuth Setup
=====================

This will connect Operator to your Gmail and Google Calendar.

Step 1: Get credentials from Google Cloud Console
-------------------------------------------------
1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable APIs:
   - Gmail API
   - Google Calendar API
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download the JSON file

Step 2: Place the credentials file
----------------------------------
""")

    creds_dir = os.path.expanduser("~/.config/agencyos/google")
    creds_file = os.path.join(creds_dir, "credentials.json")

    print(f"Save the downloaded JSON as:\n  {creds_file}\n")

    if os.path.exists(creds_file):
        print("✅ credentials.json found!")

        # Check if token exists and is valid
        token_file = os.path.join(creds_dir, "token.json")
        if os.path.exists(token_file):
            print("⚠️  Existing token found. Delete it to re-authenticate:")
            print(f"    rm {token_file}")

            response = input("\nDelete and re-authenticate? [y/N]: ").strip().lower()
            if response == 'y':
                os.remove(token_file)
                print("✅ Token deleted. Authenticating...")
            else:
                print("Keeping existing token.")
                return

        # Try to authenticate
        print("\n🔐 Opening browser for Google login...")
        try:
            from tools.life.google_auth import get_service
            service = get_service('gmail', 'v1')
            print("✅ Gmail connected!")

            service = get_service('calendar', 'v3')
            print("✅ Calendar connected!")

            print("\n🎉 Setup complete! Try:")
            print("    python operator.py 'check my email'")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
    else:
        print("❌ credentials.json not found.")
        print("\nAfter downloading from Google Cloud Console, run this again.")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            setup_google()
            return
        elif sys.argv[1] == "--help":
            print(__doc__)
            return
        else:
            # Single command mode
            operator = Operator()
            command = " ".join(sys.argv[1:])
            print(operator.process(command))
            return

    # Interactive mode
    operator = Operator()
    print("🤖 Operator Ready (type 'quit' to exit, 'help' for commands)\n")

    while True:
        try:
            command = input("You: ").strip()
            if not command:
                continue
            if command.lower() in ("quit", "exit", "q"):
                print("👋 Goodbye!")
                break

            response = operator.process(command)
            print(f"\n🤖 Operator: {response}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
