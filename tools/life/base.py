"""
Life Tool Base Class
====================

The foundation for all "Life Tools" in AgencyOS.
Designed with the "Steve Jobs" philosophy: Simple, Intuitive, Human-Centric.

Each tool must be:
1.  **Self-Describing**: Agents must instantly understand how to use it.
2.  **Safe**: Actions affecting real life (money, messages, reputation) require HITL (Human-in-the-Loop).
3.  **Delightful**: Feedback should be clear and conversational.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class ToolResult:
    """Standardized result from a Life Tool action."""
    success: bool
    message: str  # Human-readable feedback ("Scheduled meeting with Sarah.")
    data: Optional[Dict[str, Any]] = None  # Machine-readable data ({event_id: "123"})
    error: Optional[str] = None

class LifeTool(ABC):
    """Abstract base class for all Life Tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"life_tool.{name}")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return a list of capabilities (e.g., ['schedule_event', 'list_events'])."""
        pass

    @abstractmethod
    def execute(self, action: str, **kwargs) -> ToolResult:
        """
        Execute a specific action.
        
        Args:
            action: The name of the capability to execute.
            **kwargs: Arguments for the action.
            
        Returns:
            ToolResult: The outcome of the action.
        """
        pass

    def _require_confirmation(self, action: str, details: str) -> bool:
        """
        Simulate Human-in-the-Loop (HITL) confirmation.
        In production, this would trigger a UI prompt or notification.
        """
        # For now, we log and auto-approve in "Safe Mode" or prompt in CLI
        print(f"\n[LifeOS Security] 🔒 Confirmation Required")
        print(f"Action: {self.name}.{action}")
        print(f"Details: {details}")
        # In a real agent loop, this would pause execution.
        # For this prototype, we assume 'True' if it's a safe action.
        return True
