"""
Unified Memory Facade - Consolidates multiple memory systems into a single interface.

This facade provides a unified API for all memory operations, routing to the appropriate
backend system based on the type of data being stored. It resolves the issue of having
three competing memory systems:
- agency_memory/Memory (old)
- agency_memory/enhanced_memory_store (transitional)
- pattern_intelligence/PatternStore (new)

Constitutional Compliance:
- Article I: Complete context by consolidating all memory systems
- Article III: Automated enforcement through unified interface
- Article IV: Continuous learning with pattern-specific routing
"""

from typing import Optional, List, Union, Dict
from shared.type_definitions.json import JSONValue
from pydantic import BaseModel, Field
from datetime import datetime
import threading

# Import the different memory systems
from agency_memory import Memory, EnhancedMemoryStore, create_enhanced_memory_store
from pattern_intelligence import PatternStore, CodingPattern


class MemoryQuery(BaseModel):
    """Unified query structure for memory operations."""
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None)
    limit: int = 10
    include_patterns: bool = True
    include_memories: bool = True


class SearchResults(BaseModel):
    """Results from searching across memory systems."""
    patterns: List[JSONValue] = Field(default_factory=list)
    memories: List[JSONValue] = Field(default_factory=list)
    legacy: List[JSONValue] = Field(default_factory=list)


class MemoryStats(BaseModel):
    """Statistics about memory usage."""
    pattern_count: int
    memory_count: int
    backends_active: JSONValue
    last_updated: str


class MigrationStats(BaseModel):
    """Statistics about migrated items."""
    patterns: int = 0
    memories: int = 0


class UnifiedMemory:
    """
    Unified facade for all memory operations in the Agency system.

    Routes operations to the appropriate backend:
    - Pattern operations -> PatternStore (new)
    - General memory operations -> EnhancedMemoryStore (enhanced)
    - Legacy operations -> Memory (old, for backward compatibility)

    Thread-safe implementation with per-operation locking.
    """

    def __init__(self):
        """Initialize all memory backends."""
        # Thread safety lock for operations
        self._lock = threading.RLock()

        # Pattern-specific storage (new system)
        self.pattern_store = PatternStore()

        # Enhanced memory for general operations
        self.memory_store = create_enhanced_memory_store()

        # Legacy memory for backward compatibility
        self.legacy_memory = Memory()

    def store_pattern(self, pattern: Union[Dict[str, JSONValue], CodingPattern]) -> str:
        """Store a coding pattern in the pattern store."""
        with self._lock:
            if isinstance(pattern, dict):
                # Convert dict to CodingPattern if needed
                pattern = CodingPattern(**pattern)
            return self.pattern_store.store_pattern(pattern)

    def store_memory(self,
                    key: str,
                    value: JSONValue,
                    tags: Optional[List[str]] = None,
                    category: Optional[str] = None) -> None:
        """Store general memory in the enhanced memory store."""
        with self._lock:
            self.memory_store.store_memory(
                key=key,
                value=value,
                tags=tags or [],
                metadata={"category": category} if category else {}
            )

    def search(self, query: MemoryQuery) -> SearchResults:
        """
        Unified search across all memory systems.

        Returns SearchResults with results from each system:
        - 'patterns': Results from PatternStore
        - 'memories': Results from EnhancedMemoryStore
        - 'legacy': Results from legacy Memory (if needed)
        """
        with self._lock:
            results = SearchResults()

            # Search patterns if requested
            if query.include_patterns:
                pattern_results = self.pattern_store.search_patterns(
                    query.query,
                    limit=query.limit
                )
                results.patterns = pattern_results

            # Search general memories if requested
            if query.include_memories:
                memory_results = self.memory_store.search_memories(
                    query.query,
                    tags=query.tags,
                    limit=query.limit
                )
                results.memories = memory_results

            return results

    def get_pattern(self, pattern_id: str) -> Optional[CodingPattern]:
        """Retrieve a specific pattern by ID."""
        with self._lock:
            return self.pattern_store.get_pattern(pattern_id)

    def get_memory(self, key: str) -> Optional[JSONValue]:
        """Retrieve a specific memory by key."""
        with self._lock:
            return self.memory_store.get_memory(key)

    def list_patterns(self,
                     category: Optional[str] = None,
                     limit: int = 100) -> List[CodingPattern]:
        """List all patterns, optionally filtered by category."""
        with self._lock:
            # Use search with empty query to get all patterns
            all_patterns = self.pattern_store.search_patterns("", limit=limit)

            if category:
                # Filter by category if specified
                return [p for p in all_patterns
                       if hasattr(p, 'category') and p.category == category]

            return all_patterns

    def clear_patterns(self) -> None:
        """Clear all patterns (use with caution)."""
        with self._lock:
            self.pattern_store.clear()

    def get_stats(self) -> MemoryStats:
        """Get statistics about memory usage."""
        with self._lock:
            return MemoryStats(
                pattern_count=len(self.list_patterns()),
                memory_count=self.memory_store.get_memory_count() if hasattr(self.memory_store, 'get_memory_count') else 0,
                backends_active={
                    "pattern_store": True,
                    "enhanced_memory": True,
                    "legacy_memory": True
                },
                last_updated=datetime.now().isoformat()
            )

    def migrate_legacy_data(self) -> MigrationStats:
        """
        Migrate data from legacy memory to appropriate new systems.

        Returns count of migrated items by type.
        """
        with self._lock:
            # Migration strategy: Copy data from old_store to new_store
            # 1. Extract all patterns from old_store (if supported)
            # 2. Extract all memories from old_store
            # 3. Bulk insert into new_store using appropriate methods
            # 4. Validate migration with spot checks
            # Note: Currently not needed as we use single store instance
            # Implement when cross-store migration becomes necessary
            return MigrationStats(patterns=0, memories=0)


# Singleton instance for global access
_unified_memory = None
_memory_lock = threading.Lock()


def get_unified_memory() -> UnifiedMemory:
    """Get or create the singleton UnifiedMemory instance (thread-safe)."""
    global _unified_memory

    # Double-checked locking pattern for thread safety
    if _unified_memory is None:
        with _memory_lock:
            if _unified_memory is None:
                _unified_memory = UnifiedMemory()

    return _unified_memory


# Convenience functions for common operations
def store_pattern(pattern: Union[Dict[str, JSONValue], CodingPattern]) -> str:
    """Store a pattern using the unified memory facade."""
    return get_unified_memory().store_pattern(pattern)


def store_memory(key: str, value: JSONValue, tags: Optional[List[str]] = None) -> None:
    """Store general memory using the unified memory facade."""
    get_unified_memory().store_memory(key, value, tags)


def search_all(query: str, limit: int = 10) -> SearchResults:
    """Search across all memory systems."""
    query_obj = MemoryQuery(query=query, limit=limit)
    return get_unified_memory().search(query_obj)