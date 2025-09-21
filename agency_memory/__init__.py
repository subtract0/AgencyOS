"""
Agency Memory Module

Lightweight memory system with in-memory store and Firestore fallback.
Provides store, search, and learning consolidation functionality.
"""

from .memory import Memory, MemoryStore, InMemoryStore, create_session_transcript

from .firestore_store import FirestoreStore, create_firestore_store

from .learning import consolidate_learnings, generate_learning_report

from .swarm_memory import SwarmMemory, SwarmMemoryStore, MemoryPriority

from .vector_store import VectorStore, SimilarityResult, EnhancedSwarmMemoryStore

__version__ = "1.0.0"

__all__ = [
    # Core classes
    "Memory",
    "MemoryStore",
    "InMemoryStore",
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
