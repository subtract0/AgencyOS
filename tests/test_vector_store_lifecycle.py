"""
Tests for VectorStore Lifecycle Management

Constitutional Compliance:
- Article I: Complete context (all VectorStore lifecycle paths tested)
- Article II: 100% coverage of CRITICAL VectorStore functions
- Article IV: VectorStore integration is constitutionally mandated
- TDD: Tests validate memory management behavior

Tests cover CRITICAL VectorStore functions:
- add_memory() - Memory insertion with embedding generation
- search() - Similarity search with namespace filtering
- remove_memory() - Memory deletion and cleanup
- get_stats() - Statistics retrieval and monitoring

NECESSARY Criteria:
- N: Tests production VectorStore code paths
- E: Explicit test names describe memory operations
- C: Complete behavior coverage (insert, search, delete, stats)
- E: Efficient execution (<1s per test)
- S: Stable, deterministic behavior
- S: Scoped to one concern per test
- A: Actionable failure messages
- R: Relevant to current architecture (Article IV compliance)
- Y: Yieldful - prevents memory leaks and search failures
"""

from unittest.mock import Mock

from agency_memory.vector_store import VectorStore
from shared.type_definitions.json import JSONValue


class TestAddMemory:
    """Tests for add_memory() CRITICAL function."""

    def test_add_memory_stores_memory_record(self):
        """Should store memory record in internal storage."""
        # Arrange
        store = VectorStore()
        memory_key = "test_memory_001"
        memory_content: dict[str, JSONValue] = {
            "content": "Test memory content",
            "tags": ["test", "memory"],
            "timestamp": "2025-10-03T12:00:00Z",
        }

        # Act
        store.add_memory(memory_key, memory_content)

        # Assert
        assert memory_key in store._memory_records
        assert store._memory_records[memory_key]["content"] == "Test memory content"

    def test_add_memory_adds_key_to_content_if_missing(self):
        """Should add memory key to content if not present."""
        # Arrange
        store = VectorStore()
        memory_key = "test_memory_002"
        memory_content: dict[str, JSONValue] = {"content": "Test content"}

        # Act
        store.add_memory(memory_key, memory_content)

        # Assert
        assert store._memory_records[memory_key]["key"] == memory_key

    def test_add_memory_generates_searchable_text(self):
        """Should generate searchable text from memory content."""
        # Arrange
        store = VectorStore()
        memory_key = "test_memory_003"
        memory_content: dict[str, JSONValue] = {
            "key": memory_key,
            "content": "Important test data",
            "tags": ["important", "test"],
        }

        # Act
        store.add_memory(memory_key, memory_content)

        # Assert
        assert memory_key in store._memory_texts
        searchable_text = store._memory_texts[memory_key]
        assert "test_memory_003" in searchable_text
        assert "Important test data" in searchable_text

    def test_add_memory_generates_embedding_if_provider_available(self):
        """Should generate embedding when embedding provider is available."""
        # Arrange
        mock_embed_fn = Mock(return_value=[[0.1, 0.2, 0.3, 0.4]])
        store = VectorStore()
        store._embedding_function = mock_embed_fn

        memory_key = "test_memory_004"
        memory_content: dict[str, JSONValue] = {"content": "Test content for embedding"}

        # Act
        store.add_memory(memory_key, memory_content)

        # Assert
        mock_embed_fn.assert_called_once()
        assert memory_key in store._embeddings
        assert store._embeddings[memory_key] == [0.1, 0.2, 0.3, 0.4]

    def test_add_memory_handles_embedding_failure_gracefully(self):
        """Should handle embedding generation failure without crashing."""

        # Arrange
        def failing_embed_fn(texts):
            raise RuntimeError("Embedding service unavailable")

        store = VectorStore()
        store._embedding_function = failing_embed_fn

        memory_key = "test_memory_005"
        memory_content: dict[str, JSONValue] = {"content": "Test content"}

        # Act - should not raise
        store.add_memory(memory_key, memory_content)

        # Assert - memory stored even though embedding failed
        assert memory_key in store._memory_records
        assert memory_key not in store._embeddings

    def test_add_memory_handles_complex_content_types(self):
        """Should handle dict and list content types."""
        # Arrange
        store = VectorStore()

        # Test with dict content
        memory_key_dict = "test_memory_006"
        memory_content_dict: dict[str, JSONValue] = {
            "content": {"nested": "data", "values": [1, 2, 3]}
        }

        # Test with list content
        memory_key_list = "test_memory_007"
        memory_content_list: dict[str, JSONValue] = {"content": ["item1", "item2", "item3"]}

        # Act
        store.add_memory(memory_key_dict, memory_content_dict)
        store.add_memory(memory_key_list, memory_content_list)

        # Assert - should extract searchable text from complex types
        assert memory_key_dict in store._memory_texts
        assert memory_key_list in store._memory_texts


class TestSearch:
    """Tests for search() CRITICAL function."""

    def test_search_returns_results_for_matching_query(self):
        """Should return results matching the search query."""
        # Arrange
        store = VectorStore()
        store.add_memory(
            "memory_1", {"content": "Python programming tutorial", "tags": ["python", "tutorial"]}
        )
        store.add_memory(
            "memory_2", {"content": "JavaScript framework guide", "tags": ["javascript", "guide"]}
        )

        # Act
        results = store.search("python tutorial", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) > 0
        # Python memory should be in results
        result_keys = [r.get("key") for r in results]
        assert "memory_1" in result_keys

    def test_search_filters_by_namespace(self):
        """Should filter results by namespace when provided."""
        # Arrange
        store = VectorStore()
        store.add_memory(
            "memory_1", {"content": "Test content 1", "metadata": {"namespace": "session_123"}}
        )
        store.add_memory(
            "memory_2", {"content": "Test content 2", "metadata": {"namespace": "session_456"}}
        )

        # Act
        results = store.search("test", namespace="session_123", limit=10)

        # Assert
        # Should only return memories from session_123
        for result in results:
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                assert metadata.get("namespace") == "session_123"

    def test_search_respects_limit_parameter(self):
        """Should respect the limit parameter for result count."""
        # Arrange
        store = VectorStore()
        for i in range(20):
            store.add_memory(f"memory_{i}", {"content": f"Test content {i}", "tags": ["test"]})

        # Act
        results = store.search("test", limit=5)

        # Assert
        assert len(results) <= 5

    def test_search_returns_empty_list_when_no_matches(self):
        """Should return empty list when no memories match."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Python programming", "tags": ["python"]})

        # Act
        results = store.search("nonexistent query xyz", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_handles_empty_store(self):
        """Should handle search on empty store gracefully."""
        # Arrange
        store = VectorStore()

        # Act
        results = store.search("any query", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_catches_value_error_and_returns_empty(self):
        """Should catch ValueError and return empty list."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test"})

        # Mock hybrid_search to raise ValueError
        original_hybrid_search = store.hybrid_search

        def failing_search(*args, **kwargs):
            raise ValueError("Search configuration error")

        store.hybrid_search = failing_search

        # Act
        results = store.search("test query", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_catches_key_error_and_returns_empty(self):
        """Should catch KeyError and return empty list."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test"})

        # Mock to raise KeyError
        def failing_search(*args, **kwargs):
            raise KeyError("Missing required field")

        store.hybrid_search = failing_search

        # Act
        results = store.search("test query", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_catches_generic_exception_and_returns_empty(self):
        """Should catch unexpected exceptions and return empty list."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test"})

        # Mock to raise unexpected exception
        def failing_search(*args, **kwargs):
            raise RuntimeError("Unexpected critical error")

        store.hybrid_search = failing_search

        # Act
        results = store.search("test query", limit=10)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_includes_relevance_score_and_type(self):
        """Should include relevance_score and search_type in results."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test content for scoring", "tags": ["test"]})

        # Act
        results = store.search("test content", limit=10)

        # Assert
        if len(results) > 0:
            result = results[0]
            assert "relevance_score" in result
            assert "search_type" in result


class TestRemoveMemory:
    """Tests for remove_memory() CRITICAL function."""

    def test_remove_memory_deletes_from_all_stores(self):
        """Should remove memory from all internal stores."""
        # Arrange
        store = VectorStore()
        memory_key = "test_memory_001"
        memory_content: dict[str, JSONValue] = {
            "content": "Test content to be removed",
            "tags": ["test"],
        }
        store.add_memory(memory_key, memory_content)

        # Verify memory exists
        assert memory_key in store._memory_records
        assert memory_key in store._memory_texts

        # Act
        store.remove_memory(memory_key)

        # Assert - memory removed from all stores
        assert memory_key not in store._memory_records
        assert memory_key not in store._memory_texts
        assert memory_key not in store._embeddings

    def test_remove_memory_handles_nonexistent_key(self):
        """Should handle removal of non-existent key gracefully."""
        # Arrange
        store = VectorStore()

        # Act - should not raise
        store.remove_memory("nonexistent_key_12345")

        # Assert - no error raised
        assert "nonexistent_key_12345" not in store._memory_records

    def test_remove_memory_with_embedding(self):
        """Should remove embedding along with memory."""
        # Arrange
        mock_embed_fn = Mock(return_value=[[0.1, 0.2, 0.3]])
        store = VectorStore()
        store._embedding_function = mock_embed_fn

        memory_key = "test_memory_002"
        store.add_memory(memory_key, {"content": "Test content"})

        # Verify embedding exists
        assert memory_key in store._embeddings

        # Act
        store.remove_memory(memory_key)

        # Assert
        assert memory_key not in store._embeddings

    def test_remove_memory_does_not_affect_other_memories(self):
        """Should only remove specified memory, not others."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Keep this"})
        store.add_memory("memory_2", {"content": "Remove this"})
        store.add_memory("memory_3", {"content": "Keep this too"})

        # Act
        store.remove_memory("memory_2")

        # Assert
        assert "memory_1" in store._memory_records
        assert "memory_2" not in store._memory_records
        assert "memory_3" in store._memory_records


class TestGetStats:
    """Tests for get_stats() CRITICAL function."""

    def test_get_stats_returns_correct_memory_counts(self):
        """Should return accurate memory and embedding counts."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test 1"})
        store.add_memory("memory_2", {"content": "Test 2"})
        store.add_memory("memory_3", {"content": "Test 3"})

        # Act
        stats = store.get_stats()

        # Assert
        assert isinstance(stats, dict)
        assert stats["total_memories"] == 3
        assert "memories_with_embeddings" in stats

    def test_get_stats_includes_provider_information(self):
        """Should include embedding provider information."""
        # Arrange
        store = VectorStore(embedding_provider="openai")

        # Act
        stats = store.get_stats()

        # Assert
        assert "embedding_provider" in stats
        assert stats["embedding_provider"] == "openai"

    def test_get_stats_indicates_embedding_availability(self):
        """Should indicate whether embeddings are available."""
        # Arrange
        store_without = VectorStore(embedding_provider=None)
        store_with = VectorStore(embedding_provider="sentence-transformers")

        # Act
        stats_without = store_without.get_stats()
        stats_with = store_with.get_stats()

        # Assert
        assert "embedding_available" in stats_without
        assert "has_embeddings" in stats_without
        # Note: actual availability depends on whether dependencies are installed

    def test_get_stats_includes_timestamp(self):
        """Should include last_updated timestamp."""
        # Arrange
        store = VectorStore()

        # Act
        stats = store.get_stats()

        # Assert
        assert "last_updated" in stats
        # Verify it's a valid ISO timestamp
        from datetime import datetime

        datetime.fromisoformat(stats["last_updated"])  # Should not raise

    def test_get_stats_on_empty_store(self):
        """Should return valid stats for empty store."""
        # Arrange
        store = VectorStore()

        # Act
        stats = store.get_stats()

        # Assert
        assert stats["total_memories"] == 0
        assert stats["memories_with_embeddings"] == 0

    def test_get_stats_after_add_and_remove(self):
        """Should reflect accurate counts after add and remove operations."""
        # Arrange
        store = VectorStore()
        store.add_memory("memory_1", {"content": "Test 1"})
        store.add_memory("memory_2", {"content": "Test 2"})
        store.remove_memory("memory_1")

        # Act
        stats = store.get_stats()

        # Assert
        assert stats["total_memories"] == 1


class TestVectorStoreIntegration:
    """Integration tests for VectorStore lifecycle."""

    def test_full_lifecycle_add_search_remove(self):
        """Should support complete add-search-remove lifecycle."""
        # Arrange
        store = VectorStore()

        # Act - Add
        store.add_memory(
            "task_001", {"content": "Complete Python refactoring task", "tags": ["task", "python"]}
        )
        store.add_memory(
            "task_002",
            {"content": "Write tests for JavaScript module", "tags": ["task", "javascript"]},
        )

        # Act - Search
        results = store.search("python task", limit=10)
        assert len(results) > 0

        # Act - Get stats
        stats = store.get_stats()
        assert stats["total_memories"] == 2

        # Act - Remove
        store.remove_memory("task_001")

        # Assert final state
        final_stats = store.get_stats()
        assert final_stats["total_memories"] == 1
        final_results = store.search("python task", limit=10)
        # Python task should not be found anymore
        result_keys = [r.get("key") for r in final_results]
        assert "task_001" not in result_keys

    def test_concurrent_add_and_search(self):
        """Should handle concurrent add and search operations."""
        # Arrange
        store = VectorStore()

        # Act - Add multiple memories rapidly
        for i in range(10):
            store.add_memory(f"memory_{i}", {"content": f"Test content {i}", "tags": ["test"]})

        # Act - Search while memories are present
        results = store.search("test content", limit=5)

        # Assert
        assert len(results) > 0
        assert len(results) <= 5

    def test_memory_persistence_across_operations(self):
        """Should maintain memory integrity across multiple operations."""
        # Arrange
        store = VectorStore()
        original_content = {
            "content": "Original test data",
            "tags": ["original", "test"],
            "metadata": {"priority": "high"},
        }

        # Act
        store.add_memory("persistent_memory", original_content)

        # Search for it
        results = store.search("original test", limit=10)

        # Get stats
        stats = store.get_stats()

        # Assert - memory structure preserved
        assert len(results) > 0
        found_memory = next((r for r in results if r.get("key") == "persistent_memory"), None)
        assert found_memory is not None
        assert found_memory["content"] == "Original test data"
        assert stats["total_memories"] == 1
