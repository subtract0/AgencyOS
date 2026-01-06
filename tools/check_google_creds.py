
from tools.life.google_auth import DEFAULT_CREDENTIALS, get_credentials
import os
from shared.env_loader import load_agency_env

load_agency_env()

def main():
    print("🕵️ Checking Google Credentials...")
    
    primary_path = os.path.expanduser(str(DEFAULT_CREDENTIALS))
    root_path = "credentials.json"
    if os.path.exists(primary_path):
        print(f"✅ Found OAuth credentials at {primary_path}.")
    elif os.path.exists(root_path):
        print("✅ Found 'credentials.json' in repo root (legacy location).")
    else:
        print("ℹ️  OAuth credentials not found in default locations.")
        
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
        print("\n💡 TIP: Place OAuth client JSON at:")
        print(f"   {primary_path}")
        print("   (or set GOOGLE_OAUTH_CREDENTIALS to a custom path)")

if __name__ == "__main__":
    main()
