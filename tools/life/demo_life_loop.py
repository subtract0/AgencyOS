"""
Life OS: The "Magic" Loop Demo
==============================

Demonstrates the "Steve Jobs" vision of AgencyOS.
No complex commands. Just natural language and proactive help.

Scenario:
1.  User is speaking (Ambient Input).
2.  System detects an intent ("Meeting with Sarah").
3.  System proactively checks calendar and books it.
4.  System confirms with a delightful notification.

Backends:
Set LIFE_CALENDAR_BACKEND and LIFE_EMAIL_BACKEND to switch between:
- "mock" (default): In-memory for demos
- "google": Google Calendar/Gmail API
- "apple": macOS Calendar.app

Usage:
    # Demo with mock backend (default)
    python tools/life/demo_life_loop.py

    # Demo with Google Calendar
    LIFE_CALENDAR_BACKEND=google python tools/life/demo_life_loop.py

    # Demo with Apple Calendar (macOS only)
    LIFE_CALENDAR_BACKEND=apple python tools/life/demo_life_loop.py
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Direct imports from life module (avoids loading full tools package)
from tools.life.calendar_tool import CalendarTool
from tools.life.email_tool import EmailTool
from tools.life.browser_tool import BrowserTool


def print_step(step: str, content: str, delay: float = 1.5):
    """Print a step in the "Magic" loop with a delay for effect."""
    print(f"\n{step}")
    print(f"{content}")
    time.sleep(delay)


def main():
    print("\n" + "=" * 60)
    print("   A G E N C Y   O S   |   L I F E   E D I T I O N")
    print("=" * 60)

    # Show backend configuration
    calendar_backend = os.getenv("LIFE_CALENDAR_BACKEND", "mock")
    email_backend = os.getenv("LIFE_EMAIL_BACKEND", "mock")
    print(f"\n📱 Backends: Calendar={calendar_backend}, Email={email_backend}")
    print("-" * 60)

    # Initialize Tools with configured backends
    try:
        calendar = CalendarTool()
        print(f"   ✅ Calendar connected ({calendar.backend_name})")
    except Exception as e:
        print(f"   ❌ Calendar failed: {e}")
        return

    try:
        email = EmailTool()
        print(f"   ✅ Email connected ({email.backend_name})")
    except Exception as e:
        print(f"   ⚠️  Email failed (continuing without): {e}")
        email = None

    try:
        browser = BrowserTool(mock_mode=(calendar_backend == "mock"))
        print(f"   ✅ Browser ready")
    except Exception as e:
        print(f"   ⚠️  Browser failed: {e}")
        browser = None

    print("-" * 60)

    # 1. AMBIENT INPUT (Simulated Whisper.cpp output)
    user_voice = "Find a good Italian place nearby and book a table for two tonight at 7pm."
    print_step("👂 LISTENING (Ambient)", f'"{user_voice}"')

    # 2. INTENT PARSING (Simulated Trinity Brain)
    print_step(
        "🧠 THINKING (Trinity)",
        "Analyzing intent...\n"
        "   -> Intent: Book Dinner\n"
        "   -> Cuisine: Italian\n"
        "   -> When: Tonight @ 7pm\n"
        "   -> Party: 2\n"
        "   -> Missing Info: Which restaurant?"
    )

    # 3. RESEARCH (The New Capability)
    if browser:
        print_step("🌐 RESEARCHING", "Searching for 'best italian restaurant nearby'...")
        search_result = browser.search("best italian restaurant San Francisco")

        if not search_result.success or not search_result.data:
            print("   ⚠️  Research failed, using default.")
            restaurant_name = "Italian Kitchen"
            restaurant_url = "https://example.com"
        else:
            top_result = search_result.data[0]
            restaurant_name = top_result['title'].split("-")[0].strip()
            restaurant_url = top_result['url']
            print(f"   -> Found: {restaurant_name} ({restaurant_url})")
    else:
        restaurant_name = "Italian Kitchen"
        restaurant_url = "https://example.com"

    # 4. PROACTIVE CHECK
    print_step("🔍 CHECKING", "Verifying availability...")

    # Calculate "Tonight at 7pm"
    today = datetime.now()
    start_time = today.replace(hour=19, minute=0, second=0, microsecond=0)
    if start_time < today:
        start_time = start_time + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)

    availability = calendar.check_availability(start_time.isoformat(), end_time.isoformat())

    if not availability.success:
        print(f"   ❌ Conflict: {availability.message}")
        print("\n   Would you like me to suggest alternative times?")
        return

    print("   -> Slot is free.")

    # 5. EXECUTION (The Hands)
    print_step("⚡ ACTING", f"Booking table at {restaurant_name}...")

    result = calendar.schedule_event(
        title=f"Dinner at {restaurant_name}",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        description=f"Table for 2. Found via {restaurant_url}",
        location=restaurant_name,
    )

    # 6. FEEDBACK (Delight)
    if result.success:
        print_step("✨ DONE", f"{result.message}")

        # Bonus: Draft confirmation email
        if email:
            print_step("📧 BONUS", "Drafting confirmation email...")
            draft_result = email.draft_email(
                to="partner@example.com",
                subject=f"Dinner tonight at {restaurant_name}!",
                body=f"Hi!\n\nI've booked us a table at {restaurant_name} tonight at 7pm.\n\nSee you there!"
            )
            if draft_result.success:
                print(f"   -> {draft_result.message}")
    else:
        print_step("⚠️ FAILED", f"{result.message}")

    print("\n" + "=" * 60)
    print("   M A G I C   C O M P L E T E")
    print(f"   Backend: {calendar.backend_name}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
