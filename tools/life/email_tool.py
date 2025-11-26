"""
Email Tool
==========

The "Messenger" for AgencyOS.
Allows the agent to draft and send emails.

Capabilities:
- draft_email: Create a draft for review.
- send_email: Send an email (Strict HITL).
- list_unread: See what's important.

Design:
- "Draft First" philosophy: Agents should default to drafting.
- Sending requires explicit user confirmation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import LifeTool, ToolResult
import uuid

class EmailTool(LifeTool):
    def __init__(self):
        super().__init__(
            name="Email",
            description="Manage communication via email."
        )
        # In-memory store for demo
        self._drafts: Dict[str, Dict[str, Any]] = {}
        self._inbox: List[Dict[str, Any]] = [
            {"id": "1", "from": "sarah@example.com", "subject": "Re: Roadmap", "body": "Can we move the meeting?", "read": False},
            {"id": "2", "from": "newsletter@tech.com", "subject": "Weekly Update", "body": "...", "read": True}
        ]

    def get_capabilities(self) -> List[str]:
        return ["draft_email", "send_email", "list_unread"]

    def execute(self, action: str, **kwargs) -> ToolResult:
        if action == "draft_email":
            return self.draft_email(**kwargs)
        elif action == "send_email":
            return self.send_email(**kwargs)
        elif action == "list_unread":
            return self.list_unread(**kwargs)
        else:
            return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")

    def draft_email(self, to: str, subject: str, body: str) -> ToolResult:
        """Create a draft email."""
        draft_id = str(uuid.uuid4())[:8]
        self._drafts[draft_id] = {
            "id": draft_id,
            "to": to,
            "subject": subject,
            "body": body,
            "created_at": datetime.now()
        }
        
        return ToolResult(
            success=True,
            message=f"Draft created for {to}: '{subject}'",
            data={"draft_id": draft_id}
        )

    def send_email(self, to: str, subject: str, body: str, draft_id: Optional[str] = None) -> ToolResult:
        """Send an email (Requires Confirmation)."""
        
        # HITL Check
        details = f"To: {to}\nSubject: {subject}\nBody: {body[:50]}..."
        if not self._require_confirmation("send_email", f"Send email?\n{details}"):
            return ToolResult(success=False, message="User denied sending.", error="UserDenied")

        # In production, use SMTP or Gmail API
        if draft_id and draft_id in self._drafts:
            del self._drafts[draft_id]
            
        return ToolResult(
            success=True,
            message=f"Sent email to {to}.",
            data={"sent_at": datetime.now().isoformat()}
        )

    def list_unread(self, limit: int = 5) -> ToolResult:
        """List unread emails."""
        unread = [e for e in self._inbox if not e["read"]][:limit]
        
        if not unread:
            return ToolResult(success=True, message="Inbox Zero! No unread messages.", data=[])
            
        summary = "\n".join([f"- From {e['from']}: {e['subject']}" for e in unread])
        
        return ToolResult(
            success=True,
            message=f"You have {len(unread)} unread emails:\n{summary}",
            data=unread
        )
