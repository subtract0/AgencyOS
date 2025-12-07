
from tools.life.calendar_tool import CalendarTool
from tools.life.email_tool import EmailTool
import json

def test_google_tools():
    print("🤖 Testing Google Tools Integration...\n")

    # 1. Test Calendar
    print("📅 Testing CalendarTool...")
    cal = CalendarTool()
    try:
        # List events (read-only safe test)
        result = cal.list_events(days=3)
        if result.success:
            print(f"✅ Calendar Success: {result.message.splitlines()[0]}")
            # print(json.dumps(result.data, indent=2)) 
        else:
            print(f"❌ Calendar Failed: {result.message}")
            print(f"   Error: {result.error}")
    except Exception as e:
        print(f"❌ Calendar Exception: {e}")

    print("-" * 30)

    # 2. Test Gmail
    print("📧 Testing EmailTool...")
    email = EmailTool()
    try:
        # List unread (read-only safe test)
        result = email.list_unread(limit=3)
        if result.success:
            print(f"✅ Email Success: {result.message.splitlines()[0]}")
        else:
            print(f"❌ Email Failed: {result.message}")
            print(f"   Error: {result.error}")
    except Exception as e:
        print(f"❌ Email Exception: {e}")

    print("\n🎉 Verification Complete!")

if __name__ == "__main__":
    test_google_tools()
