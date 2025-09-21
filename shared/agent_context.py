"""
Agent Context Module

Provides lightweight context management for injecting shared services
like Memory without using global state.
"""

from typing import Optional, Any, Dict
from agency_memory import Memory
import logging

logger = logging.getLogger(__name__)


class AgentContext:
    """
    Lightweight context container for agent-level services.

    Allows injection of shared services like Memory without requiring
    global state. Each agent session can have its own context instance.
    """

    def __init__(self, memory: Optional[Memory] = None, session_id: Optional[str] = None):
        """
        Initialize agent context.

        Args:
            memory: Memory instance for this context (creates default if None)
            session_id: Unique identifier for this agent session
        """
        self.memory = memory or Memory()
        self.session_id = session_id or self._generate_session_id()
        self._metadata: Dict[str, Any] = {}

        logger.debug(f"AgentContext initialized with session_id: {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        from datetime import datetime
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata for this context."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from this context."""
        return self._metadata.get(key, default)

    def store_memory(self, key: str, content: Any, tags: list[str]) -> None:
        """
        Store a memory record with automatic session tagging.

        Args:
            key: Unique identifier for the memory
            content: Content to store
            tags: Tags for categorization (session tag added automatically)
        """
        # Always include session tag
        all_tags = tags + [f"session:{self.session_id}"]
        self.memory.store(key, content, all_tags)

    def search_memories(self, tags: list[str], include_session: bool = True) -> list[Dict[str, Any]]:
        """
        Search memories with optional session filtering.

        Args:
            tags: Tags to search for
            include_session: Whether to include session-specific tag in search

        Returns:
            List of matching memory records
        """
        search_tags = tags.copy()
        if include_session:
            search_tags.append(f"session:{self.session_id}")

        return self.memory.search(search_tags)

    def get_session_memories(self) -> list[Dict[str, Any]]:
        """Get all memories for this session."""
        return self.memory.search([f"session:{self.session_id}"])


def create_agent_context(memory: Optional[Memory] = None, session_id: Optional[str] = None) -> AgentContext:
    """
    Factory function to create an AgentContext instance.

    Args:
        memory: Optional Memory instance (creates default if None)
        session_id: Optional session identifier (generates if None)

    Returns:
        Configured AgentContext instance
    """
    return AgentContext(memory=memory, session_id=session_id)