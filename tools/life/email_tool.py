"""
Email Tool
==========

The "Messenger" for AgencyOS.
Allows the agent to draft and send emails.

Capabilities:
- draft_email: Create a draft for review.
- send_email: Send an email (Strict HITL).
- list_unread: See what's important.

- "Draft First" philosophy: Default to drafting.
- Sending requires explicit user confirmation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
from email.mime.text import MIMEText
from .base import LifeTool, ToolResult
from .google_auth import get_service

class EmailTool(LifeTool):
    def __init__(self):
        super().__init__(
            name="Email",
            description="Manage communication via Gmail."
        )
        self._service = None

    @property
    def service(self):
        if not self._service:
            self._service = get_service('gmail', 'v1')
        return self._service

    def get_capabilities(self) -> List[str]:
        return ["draft_email", "send_email", "list_unread"]

    def execute(self, action: str, **kwargs) -> ToolResult:
        try:
            if action == "draft_email":
                return self.draft_email(**kwargs)
            elif action == "send_email":
                return self.send_email(**kwargs)
            elif action == "list_unread":
                return self.list_unread(**kwargs)
            elif action == "list_drafts":
                return self.list_drafts(**kwargs)
            elif action == "archive_threads":
                return self.archive_threads(**kwargs)
            elif action == "trash_threads":
                return self.trash_threads(**kwargs)
            elif action == "fetch_recent_threads":
                return self.fetch_recent_threads(**kwargs)
            else:
                return ToolResult(success=False, message=f"Unknown action: {action}", error="InvalidAction")
        except Exception as e:
            return ToolResult(success=False, message=f"Google API Error: {str(e)}", error="ApiError")

    def draft_email(self, to: str, subject: str, body: str) -> ToolResult:
        """Create a draft in Gmail."""
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_body = {'message': {'raw': raw_message}}
        
        draft = self.service.users().drafts().create(userId='me', body=create_body).execute()
        
        return ToolResult(
            success=True,
            message=f"Draft created for {to}: '{subject}'",
            data={"draft_id": draft['id']}
        )

    def send_email(self, to: str, subject: str, body: str, draft_id: Optional[str] = None) -> ToolResult:
        """Send an email via Gmail (Requires Confirmation)."""
        
        # HITL Check
        details = f"To: {to}\nSubject: {subject}\nBody: {body[:50]}..."
        if not self._require_confirmation("send_email", f"Send email?\n{details}"):
            return ToolResult(success=False, message="User denied sending.", error="UserDenied")

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_payload = {'raw': raw_message}

        sent_msg = self.service.users().messages().send(userId='me', body=body_payload).execute()
        
        return ToolResult(
            success=True,
            message=f"Sent email to {to}. ID: {sent_msg['id']}",
            data={"sent_at": datetime.now().isoformat(), "message_id": sent_msg['id']}
        )

    def list_unread(self, limit: int = 5) -> ToolResult:
        """List unread emails from Gmail."""
        return self.fetch_recent_threads(limit=limit, query='is:unread')
        
    def list_drafts(self, limit: int = 5) -> ToolResult:
        """List recent drafts from Gmail."""
        results = self.service.users().drafts().list(userId='me', maxResults=limit).execute()
        drafts = results.get('drafts', [])
        
        if not drafts:
            return ToolResult(success=True, message="No drafts found.", data=[])
            
        draft_details = []
        for d in drafts:
            draft_detail = self.service.users().drafts().get(userId='me', id=d['id']).execute()
            message = draft_detail['message']
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            draft_details.append(f"- ID {d['id']}: {subject}")

        summary = "\n".join(draft_details)
        
        return ToolResult(
            success=True,
            message=f"Found {len(draft_details)} recent drafts:\n{summary}",
            data=drafts
        )

    def fetch_recent_threads(self, limit: int = 20, query: str = 'in:inbox') -> ToolResult:
        """Fetch email threads for analysis."""
        try:
            results = self.service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return ToolResult(success=True, message="No emails found.", data=[])
                
            thread_summaries = []
            detailed_data = []
            
            # We need to fetch details to be useful
            for msg in messages:
                try:
                    msg_detail = self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                    payload = msg_detail.get('payload', {})
                    headers = payload.get('headers', [])
                    snippet = msg_detail.get('snippet', '')
                    
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
                    
                    thread_id = msg_detail.get('threadId')
                    
                    summary = f"Thread {thread_id} | From: {sender} | Sub: {subject} | Snippet: {snippet[:100]}"
                    thread_summaries.append(summary)
                    
                    detailed_data.append({
                        "id": msg['id'],
                        "threadId": thread_id,
                        "sender": sender,
                        "subject": subject,
                        "snippet": snippet
                    })
                except Exception as e:
                    print(f"Error fetching message {msg['id']}: {e}")

            return ToolResult(
                success=True,
                message=f"Fetched {len(detailed_data)} emails:\n" + "\n".join(thread_summaries),
                data=detailed_data
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Fetch failed: {e}", error=str(e))

    def _batch_modify(self, thread_ids: List[str], add_labels: List[str] = [], remove_labels: List[str] = []) -> ToolResult:
        """Helper for batch modification of threads."""
        if not thread_ids:
             return ToolResult(success=True, message="No threads selected.", data={})
             
        body = {
            "ids": thread_ids,
            "addLabelIds": add_labels,
            "removeLabelIds": remove_labels
        }
        
        try:
            self.service.users().threads().batchModify(userId='me', body=body).execute()
            return ToolResult(success=True, message=f"Modified {len(thread_ids)} threads.", data={"ids": thread_ids})
        except Exception as e:
            return ToolResult(success=False, message=f"Batch Modify Failed: {e}", error=str(e))

    def archive_threads(self, thread_ids: List[str]) -> ToolResult:
        """Archive threads (Remove 'INBOX' label)."""
        return self._batch_modify(thread_ids, remove_labels=['INBOX'])
        
    def trash_threads(self, thread_ids: List[str]) -> ToolResult:
        """Move threads to Trash."""
        return self._batch_modify(thread_ids, add_labels=['TRASH'])
    
    def _require_confirmation(self, action: str, details: str) -> bool:
        """Internal HITL check (placeholder until base class support)."""
        print(f"\n⚠️  CONFIRMATION REGUIRED: {action}")
        print(details)
        response = input("Proceed? (y/n): ")
        return response.lower().startswith('y')
