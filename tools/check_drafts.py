
from tools.life.email_tool import EmailTool
import json

def check_drafts():
    print("📧 Checking latest drafts...")
    email = EmailTool()
    
    result = email.list_drafts(limit=5)
    if result.success:
        print(f"✅ Success: {result.message}")
    else:
        print(f"❌ Failed: {result.message}")
        if result.error:
            print(f"   Error: {result.error}")

if __name__ == "__main__":
    check_drafts()
