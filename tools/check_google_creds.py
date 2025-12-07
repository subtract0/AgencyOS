
from tools.life.google_auth import get_credentials
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🕵️ Checking Google Credentials...")
    
    # Check for credentials.json
    if os.path.exists('credentials.json'):
        print("✅ Found 'credentials.json' file.")
    else:
        print("ℹ️  'credentials.json' not found in root (Flow will fail if no other auth method exists).")
        
    try:
        print("→ Attempting to load credentials...")
        creds = get_credentials()
        if creds and creds.valid:
            print("✅ Successfully authenticated!")
            print(f"   Scopes: {creds.scopes}")
        else:
            print("❌ Authentication failed (Popup might have been needed but cancelled?)")
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        print("\n💡 TIP: You need a 'credentials.json' file (OAuth Client Secret) in this folder.")
        print("   Download it from Google Cloud Console: 'Download JSON'")

if __name__ == "__main__":
    main()
