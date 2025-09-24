"""
Memory interface with in-memory default implementation.
Provides store, search, and retrieval functionality with timestamps.

Implements MCP-compatible patterns for standardized memory integration.
See MCP_INTEGRATION_STANDARDS.md for detailed specifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import os
import logging

logger = logging.getLogger(__name__)


class MemoryStore(ABC):
    """Abstract interface for memory storage backends.

    Follows MCP resource pattern for standardized memory access.
    Compatible with MCP server implementations for cross-system integration.
    See MCP_INTEGRATION_STANDARDS.md for implementation guidelines.
    """

    @abstractmethod
    def store(self, key: str, content: Any, tags: List[str]) -> None:
        """Store content with key, tags, and automatic timestamp.

        Implements MCP tool pattern for memory operations.
        Supports structured data storage compatible with MCP servers.
        """
        pass

    @abstractmethod
    def search(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Retrieve memories matching any of the provided tags.

        Implements semantic search pattern recommended in MCP standards.
        Returns structured data compatible with MCP resource access.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all stored memories."""
        pass


class InMemoryStore(MemoryStore):
    """In-memory implementation of MemoryStore using dict.

    Provides working memory layer as recommended in MCP integration standards.
    Suitable for session-specific, temporary memory storage.
    See MCP_INTEGRATION_STANDARDS.md for persistent memory alternatives.
    """

    def __init__(self):
        self._memories: Dict[str, Dict[str, Any]] = {}
        logger.info(
            "InMemoryStore initialized - data will not persist between sessions"
        )

    def store(self, key: str, content: Any, tags: List[str]) -> None:
        """Store content with timestamp and tags.

        Implements MCP-compatible memory storage with structured metadata.
        Automatically adds timestamps for memory lifecycle management.
        """
        memory_record = {
            "key": key,
            "content": content,
            "tags": tags,
            "timestamp": datetime.now().isoformat(),
        }
        self._memories[key] = memory_record
        logger.debug(f"Stored memory with key: {key}, tags: {tags}")

    def search(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Return memories that have any of the specified tags.

        Implements tag-based retrieval pattern from MCP standards.
        Returns sorted results with newest memories first for optimal context.
        """
        if not tags:
            return []

        matches = []
        tag_set = set(tags)

        for memory in self._memories.values():
            memory_tags = set(memory.get("tags", []))
            if tag_set.intersection(memory_tags):
                matches.append(memory)

        # Sort by timestamp (newest first)
        matches.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.debug(f"Found {len(matches)} memories matching tags: {tags}")
        return matches

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by key."""
        return self._memories.get(key)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all memories sorted by timestamp (newest first)."""
        all_memories = list(self._memories.values())
        all_memories.sort(key=lambda x: x["timestamp"], reverse=True)
        logger.debug(f"Retrieved all {len(all_memories)} memories")
        return all_memories


class Memory:
    """Main Memory class that uses injectable store backend.

    Implements MCP client pattern with pluggable memory stores.
    Supports dependency injection for different storage backends.
    Compatible with MCP server resources and tools.
    """

    def __init__(self, store: Optional[MemoryStore] = None):
        """Initialize with store backend. Defaults to InMemoryStore."""
        self._store = store or InMemoryStore()

    def store(self, key: str, content: Any, tags: List[str] = None) -> None:
        """Store content with key and optional tags."""
        tags = tags or []  # Default to empty list if not provided
        self._store.store(key, content, tags)

    def search(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        return self._store.search(tags)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by key."""
        if hasattr(self._store, 'get'):
            return self._store.get(key)
        # Fallback: search all and find by key
        all_memories = self.get_all()
        for memory in all_memories:
            if memory.get('key') == key:
                return memory
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all memories."""
        return self._store.get_all()


def create_session_transcript(memories: List[Dict[str, Any]], session_id: str) -> str:
    """
    Create a markdown session transcript from memories.

    Args:
        memories: List of memory records
        session_id: Unique session identifier

    Returns:
        Path to created transcript file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{session_id}.md"
    filepath = os.path.join("/Users/am/Code/Agency/logs/sessions", filename)
    # Ensure filepath is a concrete string even if os.path.join is monkey-patched
    if not isinstance(filepath, str):
        base = os.getenv("TMPDIR", "/tmp")
        if not isinstance(base, str):
            base = "/tmp"
        if not base.endswith("/"):
            base += "/"
        filepath = base + filename

    # Create transcript content
    content = f"# Session Transcript: {session_id}\n\n"
    content += f"**Generated:** {datetime.now().isoformat()}\n"
    content += f"**Total Memories:** {len(memories)}\n\n"

    if not memories:
        content += "No memories recorded for this session.\n"
    else:
        content += "## Memory Records\n\n"

        for i, memory in enumerate(memories, 1):
            content += f"### {i}. {memory.get('key', 'Unnamed')}\n\n"
            content += f"**Timestamp:** {memory.get('timestamp', 'Unknown')}\n"
            content += f"**Tags:** {', '.join(memory.get('tags', []))}\n\n"

            # Format content
            memory_content = memory.get("content", "")
            if isinstance(memory_content, str):
                content += f"**Content:**\n```\n{memory_content}\n```\n\n"
            else:
                content += f"**Content:** {str(memory_content)}\n\n"

            content += "---\n\n"

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Write transcript with fallback if permission is denied
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except PermissionError:
        fallback_path = f"/tmp/{filename}"
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(content)
        filepath = fallback_path

    logger.info(f"Session transcript created: {filepath}")
    return filepath
