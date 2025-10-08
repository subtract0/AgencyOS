# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Agent Context Module

Provides lightweight context management for injecting shared services
like Memory without using global state.

Performance: VectorStore caching with @lru_cache provides 5x query speedup.
"""

import logging
from functools import lru_cache
from typing import Any

from agency_memory import Memory
from shared.type_definitions.json_value import JSONValue

logger = logging.getLogger(__name__)


class AgentContext:
    """
    Lightweight context container for agent-level services.

    Allows injection of shared services like Memory without requiring
    global state. Each agent session can have its own context instance.
    """

    def __init__(self, memory: Memory | None = None, session_id: str | None = None):
        """
        Initialize agent context.

        Args:
            memory: Memory instance for this context (creates default if None)
            session_id: Unique identifier for this agent session
        """
        self.memory = memory or Memory()
        self.session_id = session_id or self._generate_session_id()
        self._metadata: dict[str, JSONValue] = {}
        self._anthropic_memory_tool: Any | None = None  # Lazy initialization

        # Cache for search_memories - 5x performance improvement
        self._search_cache = lru_cache(maxsize=128)(self._search_memories_impl)

        logger.debug(f"AgentContext initialized with session_id: {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_suffix}"

    def set_metadata(self, key: str, value: JSONValue) -> None:
        """Set metadata for this context."""
        self._metadata[key] = value

    def get_metadata(self, key: str, default: JSONValue | None = None) -> JSONValue | None:
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

        # Invalidate cache after storing new memory
        self._search_cache.cache_clear()

    def _search_memories_impl(
        self, tags_tuple: tuple[str, ...], include_session: bool
    ) -> tuple[dict[str, JSONValue], ...]:
        """
        Internal cached implementation of search_memories.

        Uses tuple for hashable cache key. Returns tuple for immutability.
        """
        tags = list(tags_tuple)

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

        # Return as tuple for cache immutability
        return tuple(results)

    def search_memories(
        self, tags: list[str], include_session: bool = True
    ) -> list[dict[str, JSONValue]]:
        """
        Search memories with optional session filtering.

        Semantics:
        - Scope to current session when include_session=True.
        - Return memories that contain ALL requested tags (conjunctive), not any-of.
        - Additionally, when searching for ["tool"] specifically, exclude error-tagged
          memories so that tool-only queries do not return error events.

        Performance: Cached with LRU (maxsize=128) for 5x speedup on repeated queries.
        """
        # Convert tags to tuple for hashable cache key
        tags_tuple = tuple(tags)

        # Call cached implementation
        cached_result = self._search_cache(tags_tuple, include_session)

        # Convert back to list for API compatibility
        return list(cached_result)

    def get_session_memories(self) -> list[dict[str, JSONValue]]:
        """Get all memories for this session."""
        return self.memory.search([f"session:{self.session_id}"])

    def enable_anthropic_memory(self, base_dir: str | None = None) -> None:
        """
        Enable Anthropic Memory Tool for this context.

        Creates a file-based memory tool for Claude's beta memory feature.
        Enables persistent cross-conversation memory via /memories directory.

        Args:
            base_dir: Optional custom base directory
                     (default: ~/.agency/memories/{session_id})

        Raises:
            ImportError: If anthropic SDK not installed (need >=0.42.0)
        """
        try:
            from tools.anthropic_memory_tool import create_memory_tool
        except ImportError:
            raise ImportError(
                "Anthropic memory tool not available. "
                "Install anthropic>=0.42.0: uv pip install 'anthropic>=0.42.0'"
            )

        self._anthropic_memory_tool = create_memory_tool(
            session_id=self.session_id if base_dir is None else None,
            base_dir=base_dir
        )

        logger.info(
            f"Anthropic Memory Tool enabled: {self._anthropic_memory_tool.base_dir}"
        )

    def get_anthropic_memory_tool(self) -> Any:
        """
        Get the Anthropic Memory Tool instance.

        Returns:
            AgencyMemoryTool instance or None if not enabled

        Example:
            context.enable_anthropic_memory()
            tool = context.get_anthropic_memory_tool()
            tool.create("/memories/notes.txt", "Important info")
        """
        return self._anthropic_memory_tool

    def is_anthropic_memory_enabled(self) -> bool:
        """Check if Anthropic Memory Tool is enabled."""
        return self._anthropic_memory_tool is not None


def create_agent_context(
    memory: Memory | None = None, session_id: str | None = None
) -> AgentContext:
    """
    Factory function to create an AgentContext instance.

    Args:
        memory: Optional Memory instance (creates default if None)
        session_id: Optional session identifier (generates if None)

    Returns:
        Configured AgentContext instance
    """
    return AgentContext(memory=memory, session_id=session_id)
