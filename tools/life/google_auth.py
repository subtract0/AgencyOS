
import os
from pathlib import Path
from typing import Iterable

# Permissions we need (Calendar + Gmail)
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

CONFIG_DIR = Path(
    os.path.expanduser(os.getenv("AGENCY_CONFIG_DIR", "~/.config/agencyos"))
)
GOOGLE_CONFIG_DIR = CONFIG_DIR / "google"
DEFAULT_CREDENTIALS = GOOGLE_CONFIG_DIR / "credentials.json"
DEFAULT_TOKEN = GOOGLE_CONFIG_DIR / "token.json"


def _candidate_paths(primary: Path, fallback: Path) -> Iterable[Path]:
    if primary:
        yield primary
    yield fallback


def _load_google_deps():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build, Resource
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Google API dependencies missing. Install with: "
            "pip install google-api-python-client google-auth-oauthlib"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, Resource


def get_credentials():
    """Gets valid user credentials from storage or triggers login flow."""
    Request, Credentials, InstalledAppFlow, _, _ = _load_google_deps()

    creds = None

    credentials_path = Path(
        os.path.expanduser(os.getenv("GOOGLE_OAUTH_CREDENTIALS", str(DEFAULT_CREDENTIALS)))
    )
    token_path = Path(
        os.path.expanduser(os.getenv("GOOGLE_OAUTH_TOKEN", str(DEFAULT_TOKEN)))
    )

    # The token file stores access + refresh tokens and is created after login.
    for candidate in _candidate_paths(token_path, Path("token.json")):
        if candidate.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(candidate), SCOPES)
                break
            except Exception:
                print(f"⚠️  Invalid {candidate}, skipping...")
                creds = None
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing Google Access Token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                # Token refresh failed - likely expired or revoked
                # Delete token and force re-auth
                print(f"⚠️  Token refresh failed: {e}")
                print("🔄 Deleting expired token and re-authenticating...")
                if token_path.exists():
                    token_path.unlink()
                creds = None  # Force new login flow below
        else:
            # OPTION A: Look for OAuth Client Secrets (for User Login)
            selected_credentials = None
            for candidate in _candidate_paths(credentials_path, Path("credentials.json")):
                if candidate.exists():
                    selected_credentials = candidate
                    break

            if selected_credentials:
                print("🌐 Initiating Google Login Flow (check your browser)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(selected_credentials), SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json(), encoding="utf-8")

            # OPTION B: Fallback to Environment Credentials (Service Account)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                print("🤖 Using Service Account from GOOGLE_APPLICATION_CREDENTIALS...")
                import google.auth
                creds, project_id = google.auth.default(scopes=SCOPES)
            
            else:
                raise FileNotFoundError(
                    f"⚠️  No credentials found!\n"
                    f"1. Put OAuth client JSON at {credentials_path}\n"
                    f"   (or set GOOGLE_OAUTH_CREDENTIALS to a custom path).\n"
                    f"2. OR set GOOGLE_APPLICATION_CREDENTIALS in .env for Service Account."
                )
            
    return creds


def get_service(api_name: str, api_version: str):
    """Builds and returns a Google API service."""
    _, _, _, build, _ = _load_google_deps()
    creds = get_credentials()
    return build(api_name, api_version, credentials=creds)
