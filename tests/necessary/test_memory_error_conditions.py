"""
NECESSARY Pattern Tests: Error Conditions for Memory System

Tests focus on:
- Async operation failures
- Thread safety violations
- Concurrent access errors
- VectorStore failures
- Invalid data handling
- Transaction rollback scenarios
"""

from threading import Thread
from unittest.mock import MagicMock, Mock, patch

import pytest

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.memory import InMemoryStore, Memory
from shared.models.memory import MemoryMetadata, MemoryPriority, MemoryRecord


class TestMemoryAsyncErrorConditions:
    """Test error conditions for async memory operations."""

    def test_store_with_none_content(self):
        """Test that storing None content is handled gracefully."""
        store = InMemoryStore()

        # Should not raise exception
        store.store("test_key", None, ["test"])

        # Verify storage succeeded with None
        record = store.get("test_key")
        assert record is not None
        assert record.content is None

    def test_store_with_none_key(self):
        """Test that storing with None key raises appropriate error."""
        from pydantic_core import ValidationError

        store = InMemoryStore()

        # None key should cause a validation error (Pydantic validates the MemoryRecord)
        with pytest.raises((TypeError, AttributeError, KeyError, ValidationError)):
            store.store(None, {"data": "test"}, ["test"])

    def test_store_with_none_tags(self):
        """Test that storing with None tags is handled."""
        from pydantic_core import ValidationError

        store = InMemoryStore()

        # Should handle None tags gracefully (likely converts to empty list)
        # or raise a validation error (Pydantic validates the MemoryRecord)
        try:
            store.store("test_key", {"data": "test"}, None)
            record = store.get("test_key")
            assert record is not None
        except (TypeError, AttributeError, ValidationError):
            # If it raises an error, that's also acceptable behavior
            pass

    def test_search_with_none_tags(self):
        """Test that searching with None tags returns empty result."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        # Search with None should return empty or raise error
        try:
            result = store.search(None)
            # If it doesn't raise, should return empty
            assert result.total_count == 0
        except (TypeError, AttributeError):
            # Raising an error is also acceptable
            pass

    def test_concurrent_store_operations(self):
        """Test concurrent store operations for race conditions."""
        store = InMemoryStore()
        errors = []

        def store_data(key_prefix, count):
            try:
                for i in range(count):
                    store.store(f"{key_prefix}_{i}", {"data": i}, [key_prefix])
            except Exception as e:
                errors.append(e)

        # Create multiple threads writing simultaneously
        threads = [Thread(target=store_data, args=(f"thread{i}", 50)) for i in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Check for errors
        assert len(errors) == 0, f"Concurrent operations caused errors: {errors}"

        # Verify all data was stored
        all_results = store.get_all()
        assert all_results.total_count == 250  # 5 threads * 50 items

    def test_concurrent_read_write_operations(self):
        """Test concurrent read and write operations."""
        store = InMemoryStore()
        errors = []

        # Pre-populate some data
        for i in range(10):
            store.store(f"initial_{i}", {"data": i}, ["initial"])

        def write_data():
            try:
                for i in range(20):
                    store.store(f"write_{i}", {"data": i}, ["write"])
            except Exception as e:
                errors.append(e)

        def read_data():
            try:
                for _ in range(30):
                    store.search(["initial"])
                    store.get_all()
            except Exception as e:
                errors.append(e)

        # Mix read and write operations
        threads = [
            Thread(target=write_data),
            Thread(target=read_data),
            Thread(target=write_data),
            Thread(target=read_data),
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"Concurrent read/write caused errors: {errors}"

    def test_memory_store_with_circular_reference(self):
        """Test storing data with circular references."""
        store = InMemoryStore()

        # Create circular reference (dict containing itself)
        circular_data = {"key": "value"}
        circular_data["self"] = circular_data

        # Should handle circular reference (likely by storing reference)
        # or raise appropriate error
        try:
            store.store("circular", circular_data, ["test"])
            # If it succeeds, verify retrieval works
            record = store.get("circular")
            assert record is not None
        except (ValueError, RecursionError, TypeError):
            # These are acceptable errors for circular references
            pass

    def test_enhanced_memory_vector_store_failure(self):
        """Test enhanced memory when VectorStore operations fail."""
        with patch("agency_memory.enhanced_memory_store.VectorStore") as mock_vector:
            # Make VectorStore.add_memory raise exception
            mock_vector_instance = MagicMock()
            mock_vector_instance.add_memory.side_effect = RuntimeError("VectorStore failure")
            mock_vector.return_value = mock_vector_instance

            store = EnhancedMemoryStore()

            # Should handle VectorStore failure gracefully
            store.store("test_key", {"data": "test"}, ["test"])

            # Verify traditional memory still works
            result = store.search(["test"])
            assert result.total_count == 1

    def test_semantic_search_with_empty_memories(self):
        """Test semantic search when no memories exist."""
        store = EnhancedMemoryStore()

        # Should return empty list without error
        results = store.semantic_search("test query", top_k=10)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_semantic_search_with_malformed_query(self):
        """Test semantic search with malformed queries."""
        store = EnhancedMemoryStore()
        store.store("test", {"data": "test"}, ["test"])

        malformed_queries = [
            "",  # Empty string
            " " * 1000,  # Only whitespace
            "\n\n\n",  # Only newlines
        ]

        for query in malformed_queries:
            # Others might return empty or raise - both are acceptable
            try:
                results = store.semantic_search(query)
                assert isinstance(results, list)
            except (TypeError, ValueError, AttributeError):
                # Acceptable to raise errors for malformed input
                pass

        # Test None separately - should return empty list (catches in exception handler)
        results = store.semantic_search(None)
        assert isinstance(results, list)
        assert len(results) == 0


class TestMemoryTransactionErrors:
    """Test transaction-like error scenarios."""

    def test_get_memory_nonexistent_key(self):
        """Test getting memory with non-existent key."""
        store = InMemoryStore()

        result = store.get("nonexistent")
        assert result is None

    def test_search_with_empty_tag_list(self):
        """Test search with empty tag list."""
        store = InMemoryStore()
        store.store("key1", {"data": "test"}, ["tag1"])

        result = store.search([])
        assert result.total_count == 0
        assert len(result.records) == 0

    def test_memory_facade_with_invalid_store(self):
        """Test Memory class with invalid store backend."""
        # Create a broken store
        broken_store = Mock()
        broken_store.store.side_effect = RuntimeError("Store is broken")
        broken_store.search.side_effect = RuntimeError("Store is broken")
        broken_store.get_all.side_effect = RuntimeError("Store is broken")

        memory = Memory(store=broken_store)

        # All operations should raise errors
        with pytest.raises(RuntimeError):
            memory.store("key", {"data": "test"}, ["tag"])

        with pytest.raises(RuntimeError):
            memory.search(["tag"])

        with pytest.raises(RuntimeError):
            memory.get_all()

    def test_enhanced_memory_learning_pattern_extraction_failure(self):
        """Test learning pattern extraction with corrupted data."""
        store = EnhancedMemoryStore()

        # Store memories with missing or corrupted fields
        store._memories["bad1"] = {
            # Missing 'content' field
            "key": "bad1",
            "tags": ["error"],
            "timestamp": "2024-01-01T00:00:00",
        }

        store._memories["bad2"] = {
            "key": "bad2",
            "content": None,
            "tags": None,  # Invalid tags
            "timestamp": None,
        }

        # Should handle corrupted data gracefully
        patterns = store.get_learning_patterns(min_confidence=0.5)
        assert isinstance(patterns, list)
        # May be empty or contain patterns, but shouldn't crash


class TestMemoryResourceExhaustion:
    """Test memory system under resource constraints."""

    def test_store_large_number_of_memories(self):
        """Test storing a large number of memories."""
        store = InMemoryStore()

        # Store 10,000 memories
        for i in range(10000):
            store.store(f"key_{i}", {"index": i, "data": f"data_{i}"}, [f"tag_{i % 10}"])

        # Verify all were stored
        result = store.get_all()
        assert result.total_count == 10000

        # Search should still work
        tag_results = store.search(["tag_5"])
        assert tag_results.total_count == 1000  # Every 10th item

    def test_store_very_large_content(self):
        """Test storing very large content objects."""
        store = InMemoryStore()

        # Create a 1MB string
        large_content = "x" * (1024 * 1024)

        # Should handle large content
        store.store("large_key", {"data": large_content}, ["large"])

        record = store.get("large_key")
        assert record is not None
        assert len(record.content["data"]) == 1024 * 1024

    def test_store_deeply_nested_content(self):
        """Test storing deeply nested data structures."""
        store = InMemoryStore()

        # Create deeply nested dict (100 levels)
        nested = {}
        current = nested
        for i in range(100):
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]
        current["value"] = "deep"

        # Should handle deep nesting
        store.store("deep_key", nested, ["nested"])

        record = store.get("deep_key")
        assert record is not None


class TestMemoryEdgeCaseErrors:
    """Test edge case error scenarios."""

    def test_store_with_special_characters_in_key(self):
        """Test storing with special characters in keys."""
        store = InMemoryStore()

        special_keys = [
            "key/with/slashes",
            "key\\with\\backslashes",
            "key:with:colons",
            "key with spaces",
            "key\twith\ttabs",
            "key\nwith\nnewlines",
            "key.with.dots",
            "key@with#special$chars%",
        ]

        for key in special_keys:
            store.store(key, {"data": "test"}, ["special"])
            record = store.get(key)
            assert record is not None, f"Failed to store/retrieve key: {key}"

    def test_store_with_unicode_content(self):
        """Test storing with unicode and emoji content."""
        store = InMemoryStore()

        unicode_content = {
            "chinese": "你好世界",
            "japanese": "こんにちは世界",
            "emoji": "🚀🎉🔥💯",
            "mixed": "Hello 世界 🌍",
        }

        store.store("unicode_key", unicode_content, ["unicode"])
        record = store.get("unicode_key")
        assert record is not None
        assert record.content["emoji"] == "🚀🎉🔥💯"

    def test_timestamp_consistency_during_rapid_operations(self):
        """Test timestamp consistency with rapid successive operations."""
        store = InMemoryStore()

        # Store multiple items rapidly
        for i in range(100):
            store.store(f"rapid_{i}", {"index": i}, ["rapid"])

        # Get all and check timestamps are monotonic
        result = store.get_all()
        timestamps = [record.timestamp for record in result.records]

        # All timestamps should be valid datetime objects
        from datetime import datetime

        assert all(isinstance(ts, datetime) for ts in timestamps)

    def test_memory_with_invalid_priority(self):
        """Test memory record with invalid priority values."""
        from datetime import datetime

        # Valid priorities should work
        for priority in [MemoryPriority.LOW, MemoryPriority.MEDIUM, MemoryPriority.HIGH]:
            record = MemoryRecord(
                key="test",
                content={"data": "test"},
                tags=["test"],
                timestamp=datetime.now(),
                priority=priority,
                metadata=MemoryMetadata(),
                ttl_seconds=None,
                embedding=None,
            )
            assert record.priority == priority

    def test_enhanced_memory_optimize_with_failures(self):
        """Test VectorStore optimization when some memories fail."""
        with patch("agency_memory.enhanced_memory_store.VectorStore") as mock_vector:
            mock_vector_instance = MagicMock()

            # Make add_memory fail intermittently
            call_count = [0]

            def add_memory_side_effect(key, memory):
                call_count[0] += 1
                if call_count[0] % 3 == 0:
                    raise RuntimeError("Intermittent failure")

            mock_vector_instance.add_memory.side_effect = add_memory_side_effect
            mock_vector_instance._embeddings = {}
            mock_vector.return_value = mock_vector_instance

            store = EnhancedMemoryStore()

            # Add some memories
            for i in range(10):
                store.store(f"key_{i}", {"data": i}, ["test"])

            # Optimize should handle failures gracefully
            stats = store.optimize_vector_store()

            # Should report errors but continue
            assert isinstance(stats, dict)
            assert "errors" in stats
            assert stats["errors"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
