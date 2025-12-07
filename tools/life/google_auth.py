
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# Permissions we need (Calendar + Gmail)
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

CREDENTIALS_FILE = 'credentials.json'  # User must provide this
TOKEN_FILE = 'token.json'              # We generate this

def get_credentials() -> Credentials:
    """Gets valid user credentials from storage or triggers login flow."""
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            print(f"⚠️  Invalid {TOKEN_FILE}, skipping...")
            creds = None
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing Google Access Token...")
            creds.refresh(Request())
        else:
            # OPTION A: Look for OAuth Client Secrets (for User Login)
            if os.path.exists(CREDENTIALS_FILE):
                print("🌐 Initiating Google Login Flow (check your browser)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())

            # OPTION B: Fallback to Environment Credentials (Service Account)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                print("🤖 Using Service Account from GOOGLE_APPLICATION_CREDENTIALS...")
                import google.auth
                creds, project_id = google.auth.default(scopes=SCOPES)
            
            else:
                raise FileNotFoundError(
                    f"⚠️  No credentials found!\n"
                    f"1. Put 'credentials.json' (OAuth Client) in this folder for User Login.\n"
                    f"2. OR set GOOGLE_APPLICATION_CREDENTIALS in .env for Service Account."
                )
            
    return creds

def get_service(api_name: str, api_version: str) -> Resource:
    """Builds and returns a Google API service."""
    creds = get_credentials()
    return build(api_name, api_version, credentials=creds)
