"""
Safety Guard
============

A wrapper for Life Tools that enforces Human-in-the-Loop (HITL) safety.
It intercepts execution calls and requires explicit user confirmation for sensitive actions.

Usage:
    safe_tool = SafetyGuard(real_tool, sensitive_actions=["send_email", "schedule_event"])
    safe_tool.execute("send_email", ...) # Prompts user
"""

from typing import List, Any
from tools.life.base import LifeTool, ToolResult

class SafetyGuard:
    def __init__(self, tool: LifeTool, sensitive_actions: List[str] = None):
        self.tool = tool
        self.sensitive_actions = sensitive_actions or []

    def get_capabilities(self) -> List[str]:
        return self.tool.get_capabilities()

    def execute(self, action: str, **kwargs) -> ToolResult:
        if action in self.sensitive_actions:
            if not self._confirm_action(action, kwargs):
                return ToolResult(
                    success=False, 
                    message="Action blocked by SafetyGuard (User denied).", 
                    error="SecurityBlock"
                )
        
        return self.tool.execute(action, **kwargs)

    def _confirm_action(self, action: str, kwargs: Any) -> bool:
        """Prompt user for confirmation via CLI."""
        print(f"\n[SafetyGuard] 🛡️  INTERCEPTED: {self.tool.name}.{action}")
        print(f"Arguments: {kwargs}")
        
        while True:
            response = input("Allow this action? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            if response in ['n', 'no']:
                return False
