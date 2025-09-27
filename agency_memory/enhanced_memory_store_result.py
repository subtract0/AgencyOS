# mypy: disable-error-code="misc,assignment,arg-type,attr-defined,index,return-value,union-attr,dict-item,operator"
"""
Enhanced Memory Store with Result Pattern for Error Handling.

This is a demonstration implementation showing how the Result<T, E> pattern
can improve error handling in the agency_memory module by replacing
try/catch blocks with explicit error types.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
from shared.type_definitions.json import JSONValue
from shared.type_definitions.result import Result, Ok, Err, ResultStr
from .memory import MemoryStore
from shared.models.memory import MemorySearchResult, MemoryRecord, MemoryPriority, MemoryMetadata
from .vector_store import VectorStore, SimilarityResult
from .type_conversion_utils import MemoryConverter, create_memory_converter
import json

logger = logging.getLogger(__name__)


class MemoryStoreError:
    """Error types for memory store operations."""

    VECTOR_STORE_FAILED = "vector_store_operation_failed"
    INVALID_KEY = "invalid_key"
    INVALID_CONTENT = "invalid_content"
    SEARCH_FAILED = "search_operation_failed"
    SERIALIZATION_FAILED = "serialization_failed"
    CONVERSION_FAILED = "memory_conversion_failed"


class EnhancedMemoryStoreResult(MemoryStore):
    """
    Enhanced memory store demonstrating Result pattern for error handling.

    This implementation shows how to replace traditional try/catch blocks
    with the Result<T, E> pattern for more explicit and type-safe error handling.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None, embedding_provider: str = "sentence-transformers"):
        """
        Initialize enhanced memory store.

        Args:
            vector_store: Optional VectorStore instance
            embedding_provider: Embedding provider for semantic search
        """
        self._memories: Dict[str, Dict[str, JSONValue]] = {}
        self.vector_store = vector_store or VectorStore(embedding_provider=embedding_provider)
        self._learning_triggers: List[str] = []
        self.memory_converter = create_memory_converter()

        logger.info(f"EnhancedMemoryStoreResult initialized with embedding provider: {embedding_provider}")

    def store_result(self, key: str, content: Any, tags: List[str]) -> ResultStr[None]:
        """
        Store content with Result pattern error handling.

        Args:
            key: Unique memory key
            content: Content to store
            tags: Associated tags

        Returns:
            Result[None, str]: Ok(None) if successful, Err(error_message) if failed
        """
        # Validate inputs
        if not key or not isinstance(key, str):
            return Err(f"{MemoryStoreError.INVALID_KEY}: Key must be a non-empty string")

        if content is None:
            return Err(f"{MemoryStoreError.INVALID_CONTENT}: Content cannot be None")

        # Convert content to memory record
        conversion_result = self._convert_to_memory_record(key, content, tags)
        if conversion_result.is_err():
            return conversion_result.map_err(lambda e: f"{MemoryStoreError.CONVERSION_FAILED}: {e}")

        memory_record = conversion_result.unwrap()

        # Store in traditional memory
        self._memories[key] = memory_record

        # Add to vector store with error handling
        vector_result = self._add_to_vector_store(key, memory_record)
        if vector_result.is_err():
            # Log warning but don't fail the entire operation
            logger.warning(f"Vector store operation failed: {vector_result.unwrap_err()}")

        # Check for learning triggers
        self._check_learning_triggers(memory_record)

        logger.debug(f"Successfully stored memory with key: {key}, tags: {tags}")
        return Ok(None)

    def search_result(self, tags: List[str]) -> Result[MemorySearchResult, str]:
        """
        Search memories with Result pattern error handling.

        Args:
            tags: List of tags to search for

        Returns:
            Result[MemorySearchResult, str]: Ok(search_results) if successful, Err(error_message) if failed
        """
        if not tags:
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: Tags list cannot be empty")

        try:
            filtered_memories = self._filter_memories_by_tags(tags)
            # Convert dict records to MemoryRecord objects
            memory_records = []
            for mem_dict in filtered_memories:
                try:
                    record = MemoryRecord.model_validate(mem_dict)
                    memory_records.append(record)
                except Exception:
                    # Skip invalid records
                    continue

            search_result = MemorySearchResult(
                records=memory_records,
                total_count=len(memory_records),
                search_query={"tags": tags},
                execution_time_ms=0.0
            )
            return Ok(search_result)
        except Exception as e:
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: {str(e)}")

    def semantic_search_result(self, query: str, top_k: int = 10, min_similarity: float = 0.5) -> Result[List[Dict[str, JSONValue]], str]:
        """
        Perform semantic search with Result pattern error handling.

        Args:
            query: Search query
            top_k: Maximum number of results
            min_similarity: Minimum similarity threshold

        Returns:
            Result[List[Dict], str]: Ok(search_results) if successful, Err(error_message) if failed
        """
        if not query or not isinstance(query, str):
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: Query must be a non-empty string")

        if top_k <= 0:
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: top_k must be positive")

        if not (0.0 <= min_similarity <= 1.0):
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: min_similarity must be between 0.0 and 1.0")

        # Get all memories for search
        all_memories = list(self._memories.values())
        if not all_memories:
            return Ok([])

        # Perform semantic search with error handling
        search_result = self._perform_vector_search(query, all_memories, top_k, min_similarity)
        if search_result.is_err():
            return search_result

        results = search_result.unwrap()
        logger.debug(f"Semantic search for '{query}' returned {len(results)} results")
        return Ok(results)

    def combined_search_result(self, tags: Optional[List[str]] = None, query: Optional[str] = None, top_k: int = 10) -> Result[List[Dict[str, JSONValue]], str]:
        """
        Combined tag-based and semantic search with Result pattern.

        Args:
            tags: Optional tags to filter by
            query: Optional semantic search query
            top_k: Maximum number of results

        Returns:
            Result[List[Dict], str]: Ok(search_results) if successful, Err(error_message) if failed
        """
        if not tags and not query:
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: Either tags or query must be provided")

        if top_k <= 0:
            return Err(f"{MemoryStoreError.SEARCH_FAILED}: top_k must be positive")

        # Handle tag-only search
        if tags and not query:
            return self.search_result(tags).map(lambda result: [rec.to_dict() for rec in result.records[:top_k]])

        # Handle semantic-only search
        if query and not tags:
            return self.semantic_search_result(query, top_k)

        # Handle combined search
        if tags and query:
            # First filter by tags
            tag_search_result = self.search_result(tags)
            if tag_search_result.is_err():
                return Ok([])  # Graceful degradation

            tag_filtered_memories = [rec.to_dict() for rec in tag_search_result.unwrap().records]

            if not tag_filtered_memories:
                return Ok([])

            # Then perform semantic search on filtered results
            return self._perform_vector_search_on_subset(query, tag_filtered_memories, top_k)

        return Err(f"{MemoryStoreError.SEARCH_FAILED}: Unexpected search parameters")

    # Legacy interface methods for compatibility
    def store(self, key: str, content: Any, tags: List[str]) -> None:
        """Legacy store method - logs errors instead of raising exceptions."""
        result = self.store_result(key, content, tags)
        if result.is_err():
            logger.error(f"Store operation failed: {result.unwrap_err()}")

    def search(self, tags: List[str]) -> MemorySearchResult:
        """Legacy search method - returns empty result on error."""
        result = self.search_result(tags)
        if result.is_err():
            logger.error(f"Search operation failed: {result.unwrap_err()}")
            return MemorySearchResult(records=[], total_count=0, search_query={"tags": tags}, execution_time_ms=0.0)
        return result.unwrap()

    def semantic_search(self, query: str, top_k: int = 10, min_similarity: float = 0.5) -> List[Dict[str, JSONValue]]:
        """Legacy semantic search method - returns empty list on error."""
        result = self.semantic_search_result(query, top_k, min_similarity)
        return result.unwrap_or([])

    def get_all(self) -> MemorySearchResult:
        """Get all stored memories."""
        all_memories = list(self._memories.values())
        # Convert dict records to MemoryRecord objects
        memory_records = []
        for mem_dict in all_memories:
            try:
                record = MemoryRecord.model_validate(mem_dict)
                memory_records.append(record)
            except Exception:
                # Skip invalid records
                continue

        return MemorySearchResult(
            records=memory_records,
            total_count=len(memory_records),
            search_query={},
            execution_time_ms=0.0
        )

    # Private helper methods

    def _convert_to_memory_record(self, key: str, content: Any, tags: List[str]) -> ResultStr[Dict[str, JSONValue]]:
        """Convert content to memory record format."""
        try:
            metadata = MemoryMetadata(
                additional={"source": "enhanced_memory_store"}
            )

            memory_record = MemoryRecord(
                key=key,
                content=content,
                tags=tags,
                priority=MemoryPriority.MEDIUM,
                metadata=metadata,
                timestamp=datetime.now(),
                ttl_seconds=None,
                embedding=None
            )

            converted = self.memory_converter.record_to_dict(memory_record)
            return Ok(converted)
        except Exception as e:
            return Err(str(e))

    def _add_to_vector_store(self, key: str, memory_record: Dict[str, JSONValue]) -> ResultStr[None]:
        """Add memory to vector store with error handling."""
        try:
            self.vector_store.add_memory(key, memory_record)
            logger.debug(f"Added memory to VectorStore: {key}")
            return Ok(None)
        except Exception as e:
            return Err(f"Vector store operation failed: {str(e)}")

    def _perform_vector_search(self, query: str, memories: List[Dict[str, JSONValue]], top_k: int, min_similarity: float) -> Result[List[Dict[str, JSONValue]], str]:
        """Perform vector search with error handling."""
        try:
            results = self.vector_store.hybrid_search(query, memories, top_k)

            # Filter by minimum similarity and convert to memory format
            filtered_results = []
            for result in results:
                if result.similarity_score >= min_similarity:
                    memory_with_score = result.memory.copy()
                    memory_with_score['relevance_score'] = result.similarity_score
                    memory_with_score['search_type'] = result.search_type
                    filtered_results.append(memory_with_score)

            return Ok(filtered_results)
        except Exception as e:
            return Err(f"Vector search failed: {str(e)}")

    def _perform_vector_search_on_subset(self, query: str, memories: List[Dict[str, JSONValue]], top_k: int) -> Result[List[Dict[str, JSONValue]], str]:
        """Perform vector search on a subset of memories."""
        return self._perform_vector_search(query, memories, top_k, 0.0)

    def _filter_memories_by_tags(self, tags: List[str]) -> List[Dict[str, JSONValue]]:
        """Filter memories by tags."""
        filtered_memories = []
        for memory in self._memories.values():
            # Tags can be stored directly in the memory record or in metadata
            memory_tags = memory.get('tags', [])
            if not memory_tags:
                memory_tags = memory.get('metadata', {}).get('tags', [])

            if isinstance(memory_tags, list) and any(tag in memory_tags for tag in tags):
                filtered_memories.append(memory)
        return filtered_memories

    def _check_learning_triggers(self, memory_record: Dict[str, JSONValue]) -> None:
        """Check for learning trigger conditions."""
        # Simplified learning trigger logic
        pass


def create_enhanced_memory_store_result(embedding_provider: str = "sentence-transformers") -> EnhancedMemoryStoreResult:
    """
    Factory function to create an EnhancedMemoryStoreResult instance.

    Args:
        embedding_provider: Embedding provider for semantic search

    Returns:
        EnhancedMemoryStoreResult: Configured memory store instance
    """
    return EnhancedMemoryStoreResult(embedding_provider=embedding_provider)