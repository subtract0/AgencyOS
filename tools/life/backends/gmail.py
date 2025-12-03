"""
Gmail Backend
=============

Real Gmail API integration.

Setup:
1. Create a project in Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Download credentials.json
5. Set GOOGLE_CREDENTIALS_PATH environment variable

First run will open a browser for OAuth authorization.
Token is cached in ~/.agency/gmail_token.json
"""

import base64
import os
import pickle
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from .base import BackendConfig, Email, EmailBackend

# Lazy import
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GmailBackend(EmailBackend):
    """Gmail API backend."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
    ]

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._service = None
        self._creds = None
        self._user_email = None

        # Get credentials path from config or environment
        self._credentials_path = (
            config.credentials_path if config else None
        ) or os.getenv("GOOGLE_CREDENTIALS_PATH")

        # Token storage location
        self._token_path = Path.home() / ".agency" / "gmail_token.json"
        self._token_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "gmail"

    def connect(self) -> bool:
        """Authenticate with Gmail API."""
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Gmail API dependencies not installed. "
                "Run: pip install google-auth-oauthlib google-api-python-client"
            )

        creds = None

        # Load existing token
        if self._token_path.exists():
            with open(self._token_path, "rb") as token:
                creds = pickle.load(token)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._credentials_path or not Path(self._credentials_path).exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self._credentials_path}. "
                        "Set GOOGLE_CREDENTIALS_PATH environment variable."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next time
            with open(self._token_path, "wb") as token:
                pickle.dump(creds, token)

        self._creds = creds
        self._service = build("gmail", "v1", credentials=creds)

        # Get user's email address
        profile = self._service.users().getProfile(userId="me").execute()
        self._user_email = profile.get("emailAddress", "me@gmail.com")

        self._connected = True
        return True

    def list_unread(self, max_results: int = 10) -> list[Email]:
        """List unread emails from Gmail."""
        if not self._connected:
            self.connect()

        results = (
            self._service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_results)
            .execute()
        )

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg_data = (
                self._service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="full")
                .execute()
            )

            headers = {
                h["name"]: h["value"] for h in msg_data["payload"]["headers"]
            }

            # Get body
            body = ""
            if "parts" in msg_data["payload"]:
                for part in msg_data["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        body = base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                        break
            elif "body" in msg_data["payload"] and "data" in msg_data["payload"]["body"]:
                body = base64.urlsafe_b64decode(
                    msg_data["payload"]["body"]["data"]
                ).decode("utf-8")

            emails.append(
                Email(
                    id=msg["id"],
                    from_address=headers.get("From", "unknown@unknown.com"),
                    to_addresses=[headers.get("To", "")],
                    subject=headers.get("Subject", "No Subject"),
                    body=body[:1000],  # Limit body length
                    is_read=False,
                    timestamp=datetime.fromtimestamp(
                        int(msg_data["internalDate"]) / 1000
                    ),
                )
            )

        return emails

    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
        attachments: list[str] = None,
    ) -> Email:
        """Send an email via Gmail."""
        if not self._connected:
            self.connect()

        message = MIMEMultipart()
        message["to"] = ", ".join(to_addresses)
        message["from"] = self._user_email
        message["subject"] = subject

        msg = MIMEText(body)
        message.attach(msg)

        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = (
            self._service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

        return Email(
            id=sent["id"],
            from_address=self._user_email,
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_read=True,
            timestamp=datetime.now(),
            attachments=attachments or [],
        )

    def create_draft(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
    ) -> Email:
        """Create a draft email in Gmail."""
        if not self._connected:
            self.connect()

        message = MIMEMultipart()
        message["to"] = ", ".join(to_addresses)
        message["from"] = self._user_email
        message["subject"] = subject

        msg = MIMEText(body)
        message.attach(msg)

        # Encode the message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        draft = (
            self._service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )

        return Email(
            id=draft["id"],
            from_address=self._user_email,
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_read=False,
            timestamp=datetime.now(),
        )
