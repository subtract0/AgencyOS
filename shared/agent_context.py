"""
Agent Context Module

Provides lightweight context management for injecting shared services
like Memory without using global state.
"""

from typing import Optional, Any, Dict
from shared.types.json import JSONValue
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
        self._metadata: Dict[str, JSONValue] = {}

        logger.debug(f"AgentContext initialized with session_id: {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        from datetime import datetime
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def set_metadata(self, key: str, value: JSONValue) -> None:
        """Set metadata for this context."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Optional[JSONValue] = None) -> Optional[JSONValue]:
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

    def search_memories(self, tags: list[str], include_session: bool = True) -> list[dict[str, JSONValue]]:
        """
        Search memories with optional session filtering.

        Semantics:
        - Scope to current session when include_session=True.
        - Return memories that contain ALL requested tags (conjunctive), not any-of.
        - Additionally, when searching for ["tool"] specifically, exclude error-tagged
          memories so that tool-only queries do not return error events.
        """
        # Gather candidate set (session-scoped)
        session_tag = f"session:{self.session_id}"
        candidates = self.memory.search([session_tag]) if include_session else self.memory.get_all()

        req = set(tags or [])
        results: list[dict[str, JSONValue]] = []
        for mem in candidates:
            mem_tags = set(mem.get("tags", []))
            if req.issubset(mem_tags):
                results.append(mem)

        # Exclude error-tagged entries for tool-only queries
        if req == {"tool"}:
            results = [m for m in results if "error" not in m.get("tags", [])]

        # Keep newest first (they already come roughly sorted, but ensure)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results

    def get_session_memories(self) -> list[dict[str, JSONValue]]:
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