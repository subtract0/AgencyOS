"""
Agency Memory Module

Lightweight memory system with in-memory store and Firestore fallback.
Provides store, search, and learning consolidation functionality.
"""

from .memory import Memory, MemoryStore, InMemoryStore, create_session_transcript

from .firestore_store import FirestoreStore, create_firestore_store

from .learning import consolidate_learnings as _consolidate_learnings, generate_learning_report

def consolidate_learnings(source):
    """Consolidate learnings from various inputs.

    Accepts:
    - List[Dict]: direct list of memory records
    - Memory or MemoryStore instances (with get_all())
    - Bound get_all method (via __self__)
    - Memory wrapper objects exposing _store.get_all()
    """
    from .learning import consolidate_learnings as _consolidate

    # 1) Direct list/tuple of memory dicts
    if isinstance(source, (list, tuple)):
        return _consolidate(list(source))

    # 2) Objects exposing get_all()
    if hasattr(source, 'get_all'):
        try:
            memories = source.get_all()
            return _consolidate(memories)
        except Exception as e:
            # Silently continue to try next method
            import logging
            logging.debug(f"Method get_all() failed: {e}")

    # 3) Memory wrapper exposing _store.get_all()
    if hasattr(source, '_store') and hasattr(getattr(source, '_store'), 'get_all'):
        try:
            memories = source._store.get_all()  # type: ignore[attr-defined]
            return _consolidate(memories)
        except Exception as e:
            # Silently continue to try next method
            import logging
            logging.debug(f"Method get_all() failed: {e}")

    # 4) Bound method case (e.g., memory.get_all)
    if hasattr(source, '__self__'):
        store_obj = getattr(source, '__self__')
        if hasattr(store_obj, 'get_all'):
            try:
                memories = store_obj.get_all()
                return _consolidate(memories)
            except Exception:
                pass

    # Fallback to empty analysis
    return _consolidate([])

from .swarm_memory import SwarmMemory, SwarmMemoryStore, MemoryPriority

from .vector_store import VectorStore, SimilarityResult, EnhancedSwarmMemoryStore

from .enhanced_memory_store import EnhancedMemoryStore, create_enhanced_memory_store

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "Memory",
    "MemoryStore",
    "InMemoryStore",
    # Enhanced memory with VectorStore integration
    "EnhancedMemoryStore",
    "create_enhanced_memory_store",
    # Firestore backend
    "FirestoreStore",
    "create_firestore_store",
    # Learning and analysis
    "consolidate_learnings",
    "generate_learning_report",
    # Session management
    "create_session_transcript",
    # Swarm memory features
    "SwarmMemory",
    "SwarmMemoryStore",
    "MemoryPriority",
    # Vector similarity search
    "VectorStore",
    "SimilarityResult",
    "EnhancedSwarmMemoryStore",
]
