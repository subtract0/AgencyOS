"""
FirestoreStore implementation with verbose fallback to InMemoryStore.
Only activates when FRESH_USE_FIRESTORE=true and gracefully degrades.
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, List
from shared.types.json import JSONValue

# Expose firestore at module scope for test patching
try:  # pragma: no cover
    from google.cloud import firestore as firestore  # type: ignore
except Exception:  # pragma: no cover
    firestore = None

from .memory import MemoryStore, InMemoryStore

logger = logging.getLogger(__name__)


class FirestoreStore(MemoryStore):
    """
    Firestore-backed memory store with graceful degradation.

    Behavior:
    1. Only activates if FRESH_USE_FIRESTORE=true
    2. Attempts to import google-cloud-firestore
    3. Falls back to InMemoryStore with verbose logging if unavailable
    4. Respects FIRESTORE_EMULATOR_HOST for local development
    """

    def __init__(self, collection_name: str = "agency_memories"):
        """
        Initialize FirestoreStore with fallback logic.

        Args:
            collection_name: Firestore collection name for memories
        """
        self.collection_name = collection_name
        self._fallback_store = None
        self._client = None
        self._collection = None

        # Check if Firestore should be used
        use_firestore = os.getenv("FRESH_USE_FIRESTORE", "").lower() == "true"

        if not use_firestore:
            logger.warning(
                "FirestoreStore: FRESH_USE_FIRESTORE not set to 'true', "
                "falling back to InMemoryStore"
            )
            self._initialize_fallback()
            return

        # Try to initialize Firestore
        if not self._initialize_firestore():
            self._initialize_fallback()

    def _initialize_firestore(self) -> bool:
        """
        Attempt to initialize Firestore client.

        Returns:
            True if successful, False if fallback needed
        """
        try:
            global firestore
            if firestore is None:
                from google.cloud import firestore as _fs  # type: ignore
                firestore = _fs

            # Check for emulator
            emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")
            if emulator_host:
                logger.info(f"FirestoreStore: Using emulator at {emulator_host}")
                # Set up emulator client
                os.environ["GOOGLE_CLOUD_PROJECT"] = "agency-dev"
                self._client = firestore.Client()
            else:
                logger.info("FirestoreStore: Connecting to production Firestore")
                self._client = firestore.Client()

            self._collection = self._client.collection(self.collection_name)

            # Test connection with a simple query
            try:
                # This will raise an exception if connection fails
                list(self._collection.limit(1).stream())
                logger.info(
                    f"FirestoreStore: Successfully connected to collection '{self.collection_name}'"
                )
                return True

            except Exception as e:
                logger.warning(
                    f"FirestoreStore: Connection test failed: {e}. "
                    "Falling back to InMemoryStore"
                )
                return False

        except ImportError:
            logger.warning(
                "FirestoreStore: google-cloud-firestore not available. "
                "Install with: pip install google-cloud-firestore. "
                "Falling back to InMemoryStore for this session."
            )
            return False

        except Exception as e:
            logger.warning(
                f"FirestoreStore: Initialization failed: {e}. "
                "Falling back to InMemoryStore"
            )
            return False

    def _initialize_fallback(self):
        """Initialize fallback InMemoryStore."""
        self._fallback_store = InMemoryStore()
        logger.info(
            "FirestoreStore: Using InMemoryStore fallback - "
            "data will not persist between sessions"
        )

    def store(self, key: str, content: Any, tags: List[str]) -> None:
        """Store content with timestamp and tags."""
        if self._fallback_store:
            return self._fallback_store.store(key, content, tags)

        memory_record = {
            "key": key,
            "content": content,
            "tags": tags,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Use key as document ID for easy retrieval
            self._collection.document(key).set(memory_record)
            logger.debug(f"FirestoreStore: Stored memory with key: {key}")

        except Exception as e:
            logger.error(f"FirestoreStore: Failed to store memory {key}: {e}")
            # Initialize fallback if Firestore fails during operation
            if not self._fallback_store:
                self._initialize_fallback()
            self._fallback_store.store(key, content, tags)

    def search(self, tags: List[str]) -> List[dict[str, JSONValue]]:
        """Search memories by tags using Firestore array-contains-any."""
        if self._fallback_store:
            return self._fallback_store.search(tags)

        if not tags:
            return []

        try:
            # Firestore query for documents where tags array contains any of the search tags
            query = self._collection.where("tags", "array_contains_any", tags)
            docs = query.stream()

            memories = []
            for doc in docs:
                memory = doc.to_dict()
                memories.append(memory)

            # Sort by timestamp (newest first)
            memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            logger.debug(
                f"FirestoreStore: Found {len(memories)} memories for tags: {tags}"
            )
            return memories

        except Exception as e:
            logger.error(f"FirestoreStore: Search failed for tags {tags}: {e}")
            # Fall back to empty result rather than crash
            return []

    def get_all(self) -> List[dict[str, JSONValue]]:
        """Get all memories from Firestore."""
        if self._fallback_store:
            return self._fallback_store.get_all()

        try:
            docs = self._collection.stream()
            memories = []

            for doc in docs:
                memory = doc.to_dict()
                memories.append(memory)

            # Sort by timestamp (newest first)
            memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            logger.debug(f"FirestoreStore: Retrieved {len(memories)} total memories")
            return memories

        except Exception as e:
            logger.error(f"FirestoreStore: Failed to retrieve all memories: {e}")
            return []


def create_firestore_store(collection_name: str = "agency_memories") -> FirestoreStore:
    """
    Factory function to create FirestoreStore with standard configuration.

    Args:
        collection_name: Firestore collection name

    Returns:
        FirestoreStore instance (may use InMemoryStore fallback)
    """
    return FirestoreStore(collection_name)
