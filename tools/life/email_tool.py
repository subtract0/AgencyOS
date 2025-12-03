"""
Email Tool
==========

The "Messenger" for AgencyOS.
Allows the agent to draft and send emails.

Capabilities:
- draft_email: Create a draft for review.
- send_email: Send an email (Strict HITL).
- list_unread: See what's important.

Backends (via LIFE_EMAIL_BACKEND env var):
- "mock" (default): In-memory store for demos/testing
- "gmail": Gmail API (requires Google OAuth)
- "smtp": Any SMTP server (requires SMTP_* env vars)

Design:
- "Draft First" philosophy: Agents should default to drafting.
- Sending requires explicit user confirmation.
"""

from datetime import datetime
from typing import Any, Optional

from .backends import get_email_backend
from .backends.base import EmailBackend
from .base import LifeTool, ToolResult


class EmailTool(LifeTool):
    """Email management tool with pluggable backends."""

    def __init__(self, backend: Optional[EmailBackend] = None):
        """
        Initialize EmailTool.

        Args:
            backend: Optional backend override. If None, uses LIFE_EMAIL_BACKEND env var.
        """
        super().__init__(
            name="Email",
            description="Manage communication via email."
        )
        self._backend = backend or get_email_backend()
        self._backend.connect()

    @property
    def backend_name(self) -> str:
        """Return the active backend name."""
        return self._backend.name

    def get_capabilities(self) -> list[str]:
        return ["draft_email", "send_email", "list_unread"]

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "draft_email":
            return self.draft_email(**kwargs)
        elif action == "send_email":
            return self.send_email(**kwargs)
        elif action == "list_unread":
            return self.list_unread(**kwargs)
        else:
            return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")

    def draft_email(self, to: str, subject: str, body: str) -> ToolResult:
        """
        Create a draft email.

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Email body.
        """
        try:
            # Support both single address and list
            to_addresses = [to] if isinstance(to, str) else to

            draft = self._backend.create_draft(
                to_addresses=to_addresses,
                subject=subject,
                body=body,
            )

            return ToolResult(
                success=True,
                message=f"Draft created for {to}: '{subject}' (via {self._backend.name})",
                data={"draft_id": draft.id, "backend": self._backend.name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to create draft: {e}",
                error="DraftError"
            )

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        draft_id: Optional[str] = None,
    ) -> ToolResult:
        """
        Send an email (Requires Confirmation).

        Args:
            to: Recipient email address.
            subject: Email subject.
            body: Email body.
            draft_id: Optional draft ID to send instead of new email.
        """
        # Support both single address and list
        to_addresses = [to] if isinstance(to, str) else to

        # HITL Check - Email sending is a serious action
        details = f"To: {', '.join(to_addresses)}\nSubject: {subject}\nBody: {body[:100]}..."
        if not self._require_confirmation("send_email", f"Send email?\n{details}"):
            return ToolResult(success=False, message="User denied sending.", error="UserDenied")

        try:
            email = self._backend.send_email(
                to_addresses=to_addresses,
                subject=subject,
                body=body,
            )

            return ToolResult(
                success=True,
                message=f"Sent email to {', '.join(to_addresses)} (via {self._backend.name}).",
                data={"email_id": email.id, "sent_at": datetime.now().isoformat(), "backend": self._backend.name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to send email: {e}",
                error="SendError"
            )

    def list_unread(self, limit: int = 5) -> ToolResult:
        """
        List unread emails.

        Args:
            limit: Maximum number of emails to return.
        """
        try:
            emails = self._backend.list_unread(max_results=limit)

            if not emails:
                return ToolResult(
                    success=True,
                    message="Inbox Zero! No unread messages.",
                    data=[]
                )

            summary = "\n".join([
                f"- From {e.from_address}: {e.subject}"
                for e in emails
            ])

            return ToolResult(
                success=True,
                message=f"You have {len(emails)} unread emails:\n{summary}",
                data=[{
                    "id": e.id,
                    "from": e.from_address,
                    "subject": e.subject,
                    "body_preview": e.body[:200] if e.body else "",
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                } for e in emails]
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to list emails: {e}",
                error="ListError"
            )
