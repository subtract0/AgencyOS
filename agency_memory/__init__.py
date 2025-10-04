# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Agency Memory Module

Consolidated memory system with enhanced memory store as the primary implementation.
Provides comprehensive memory functionality with vector search, learning consolidation,
and multiple backend options.
"""

from .firestore_store import FirestoreStore, create_firestore_store
from .learning import consolidate_learnings as _consolidate_learnings
from .learning import generate_learning_report
from .memory import InMemoryStore, Memory, MemoryStore, create_session_transcript


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
    if hasattr(source, "get_all"):
        try:
            memories = source.get_all()
            return _consolidate(memories)
        except Exception as e:
            # Silently continue to try next method
            import logging

            logging.debug(f"Method get_all() failed: {e}")

    # 3) Memory wrapper exposing _store.get_all()
    if hasattr(source, "_store") and hasattr(getattr(source, "_store"), "get_all"):
        try:
            memories = source._store.get_all()  # mypy: disable-error-code="attr-defined"
            return _consolidate(memories)
        except Exception as e:
            # Silently continue to try next method
            import logging

            logging.debug(f"Method get_all() failed: {e}")

    # 4) Bound method case (e.g., memory.get_all)
    if hasattr(source, "__self__"):
        store_obj = getattr(source, "__self__")
        if hasattr(store_obj, "get_all"):
            try:
                memories = store_obj.get_all()
                return _consolidate(memories)
            except AttributeError as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Memory store missing get_all method: {e}")
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Failed to retrieve memories from store: {e}")

    # Fallback to empty analysis
    return _consolidate([])


from .enhanced_memory_store import EnhancedMemoryStore, create_enhanced_memory_store
from .swarm_memory import MemoryPriority, SwarmMemory, SwarmMemoryStore
from .vector_store import EnhancedSwarmMemoryStore, SimilarityResult, VectorStore

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
