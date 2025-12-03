"""
Life OS Tools - Ambient Life Assistant for AgencyOS

Steve Jobs-inspired tools for proactive life automation with HITL safety.

Tools:
- CalendarTool: Schedule management, availability checking
- EmailTool: Draft and send emails with human approval
- BrowserTool: Web research and automation

All tools implement HITL (Human-in-the-Loop) safety for actions that
affect real life (money, messages, reputation).
"""

from .base import LifeTool, ToolResult
from .calendar_tool import CalendarTool
from .email_tool import EmailTool
from .browser_tool import BrowserTool

__all__ = [
    "LifeTool",
    "ToolResult",
    "CalendarTool",
    "EmailTool",
    "BrowserTool",
]
