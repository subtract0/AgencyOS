"""
SMTP Email Backend
==================

Send emails via SMTP (works with any email provider).

Configuration via environment variables:
- SMTP_HOST: SMTP server hostname (e.g., smtp.gmail.com)
- SMTP_PORT: SMTP port (default: 587 for TLS)
- SMTP_USER: Username/email for authentication
- SMTP_PASSWORD: Password or app-specific password
- SMTP_FROM_EMAIL: From email address (defaults to SMTP_USER)
"""

import os
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .base import BackendConfig, Email, EmailBackend


class SmtpBackend(EmailBackend):
    """SMTP email backend."""

    def __init__(self, config: Optional[BackendConfig] = None):
        super().__init__(config)
        self._smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self._smtp_user = os.getenv("SMTP_USER", "")
        self._smtp_password = os.getenv("SMTP_PASSWORD", "")
        self._from_email = os.getenv("SMTP_FROM_EMAIL", self._smtp_user)
        self._drafts: dict[str, Email] = {}

    @property
    def name(self) -> str:
        return "smtp"

    def connect(self) -> bool:
        """Verify SMTP credentials by attempting a connection."""
        if not self._smtp_user or not self._smtp_password:
            raise ValueError(
                "SMTP credentials not configured. "
                "Set SMTP_USER and SMTP_PASSWORD environment variables."
            )

        try:
            server = smtplib.SMTP(self._smtp_host, self._smtp_port)
            server.starttls()
            server.login(self._smtp_user, self._smtp_password)
            server.quit()
            self._connected = True
            return True
        except Exception as e:
            raise ConnectionError(f"SMTP connection failed: {e}")

    def list_unread(self, max_results: int = 10) -> list[Email]:
        """SMTP doesn't support reading emails - return empty list."""
        # SMTP is send-only. For reading, use IMAP or Gmail backend.
        return []

    def send_email(
        self,
        to_addresses: list[str],
        subject: str,
        body: str,
        attachments: list[str] = None,
    ) -> Email:
        """Send an email via SMTP."""
        if not self._smtp_user or not self._smtp_password:
            raise ValueError("SMTP credentials not configured.")

        message = MIMEMultipart()
        message["From"] = self._from_email
        message["To"] = ", ".join(to_addresses)
        message["Subject"] = subject

        msg = MIMEText(body)
        message.attach(msg)

        # Connect and send
        server = smtplib.SMTP(self._smtp_host, self._smtp_port)
        server.starttls()
        server.login(self._smtp_user, self._smtp_password)
        server.sendmail(self._from_email, to_addresses, message.as_string())
        server.quit()

        email_id = str(uuid.uuid4())[:8]
        return Email(
            id=email_id,
            from_address=self._from_email,
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
        """Create a local draft (SMTP doesn't have server-side drafts)."""
        draft_id = str(uuid.uuid4())[:8]
        draft = Email(
            id=draft_id,
            from_address=self._from_email,
            to_addresses=to_addresses,
            subject=subject,
            body=body,
            is_read=False,
            timestamp=datetime.now(),
        )
        self._drafts[draft_id] = draft
        return draft
