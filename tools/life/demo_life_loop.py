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
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.life.calendar_tool import CalendarTool
from tools.life.browser_tool import BrowserTool

def print_step(step: str, content: str, delay: float = 1.5):
    """Print a step in the "Magic" loop with a delay for effect."""
    print(f"\n{step}")
    print(f"{content}")
    time.sleep(delay)

def main():
    print("\n" + "="*60)
    print("   A G E N C Y   O S   |   L I F E   E D I T I O N")
    print("="*60 + "\n")

    # Initialize Tools
    calendar = CalendarTool()
    browser = BrowserTool(mock_mode=True)

    # 1. AMBIENT INPUT
    # Simulated Whisper.cpp output
    user_voice = "Find a good Italian place nearby and book a table for two tonight at 7pm."
    
    print_step("👂 LISTENING (Ambient)", f'"{user_voice}"')

    # 2. INTENT PARSING (Simulated Trinity Brain)
    print_step("🧠 THINKING (Trinity)", "Analyzing intent...\n   -> Intent: Book Dinner\n   -> Cuisine: Italian\n   -> When: Tonight @ 7pm\n   -> Party: 2\n   -> Missing Info: Which restaurant?")

    # 3. RESEARCH (The New Capability)
    print_step("🌐 RESEARCHING", "Searching for 'best italian restaurant nearby'...")
    search_result = browser.search("best italian restaurant San Francisco") # Hardcoded location for demo
    
    if not search_result.success or not search_result.data:
        print("❌ Research failed.")
        return

    top_result = search_result.data[0]
    restaurant_name = top_result['title'].split("-")[0].strip() # Simple extraction
    print(f"   -> Found: {restaurant_name} ({top_result['url']})")

    # 4. PROACTIVE CHECK
    print_step("🔍 CHECKING", "Verifying availability...")
    
    # Calculate "Tonight at 7pm"
    today = datetime.now()
    start_time = today.replace(hour=19, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=2)
    
    availability = calendar.check_availability(start_time.isoformat(), end_time.isoformat())
    
    if not availability.success:
        print(f"❌ Conflict: {availability.message}")
        return

    print("   -> Slot is free.")

    # 5. EXECUTION (The Hands)
    print_step("⚡ ACTING", f"Booking table at {restaurant_name}...")
    
    result = calendar.schedule_event(
        title=f"Dinner at {restaurant_name}",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        description=f"Table for 2. Found via {top_result['url']}"
    )

    # 5. FEEDBACK (Delight)
    if result.success:
        print_step("✨ DONE", f"{result.message}")
    else:
        print_step("⚠️ FAILED", f"{result.message}")

    print("\n" + "="*60)
    print("   M A G I C   C O M P L E T E")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
