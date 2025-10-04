"""
Tests for the refactored enhanced_memory_store.py.

Ensures that the refactored code maintains all existing functionality
while providing improved performance and maintainability.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from agency_memory.enhanced_memory_store import EnhancedMemoryStore
from agency_memory.type_conversion_utils import (
    MemoryConverter,
    TypeConversionCache,
    create_memory_converter,
)
from shared.models.memory import MemoryMetadata, MemoryPriority, MemoryRecord


class TestTypeConversionCache:
    """Test the type conversion cache functionality."""

    def test_cache_initialization(self):
        """Test that cache initializes correctly."""
        cache = TypeConversionCache()
        assert cache._type_cache == {}

    def test_is_list_caching(self):
        """Test that list type checks are cached."""
        cache = TypeConversionCache()
        test_list = [1, 2, 3]

        # First call should cache the result
        result1 = cache.is_list(test_list)
        assert result1 is True
        assert id(test_list) in cache._type_cache

        # Second call should use cached result
        result2 = cache.is_list(test_list)
        assert result2 is True
        assert result1 == result2

    def test_is_string_caching(self):
        """Test that string type checks are cached."""
        cache = TypeConversionCache()
        test_string = "hello"

        result1 = cache.is_string(test_string)
        assert result1 is True
        assert id(test_string) in cache._type_cache

        result2 = cache.is_string(test_string)
        assert result2 is True

    def test_is_number_caching(self):
        """Test that number type checks are cached."""
        cache = TypeConversionCache()
        test_int = 42
        test_float = 3.14

        assert cache.is_number(test_int) is True
        assert cache.is_number(test_float) is True
        assert cache.is_number("not a number") is False

    def test_cache_clear(self):
        """Test that cache can be cleared."""
        cache = TypeConversionCache()
        test_list = [1, 2, 3]

        cache.is_list(test_list)
        assert len(cache._type_cache) > 0

        cache.clear()
        assert cache._type_cache == {}


class TestMemoryConverter:
    """Test the memory converter functionality."""

    def test_extract_tags_list_valid_list(self):
        """Test extracting tags from valid list."""
        converter = MemoryConverter()
        tags = ["tag1", "tag2", "tag3"]

        result = converter.extract_tags_list(tags)
        assert result == ["tag1", "tag2", "tag3"]

    def test_extract_tags_list_mixed_types(self):
        """Test extracting tags from list with mixed types."""
        converter = MemoryConverter()
        tags = ["tag1", 123, "tag2", None, "tag3"]

        result = converter.extract_tags_list(tags)
        assert result == ["tag1", "tag2", "tag3"]

    def test_extract_tags_list_invalid_input(self):
        """Test extracting tags from invalid input."""
        converter = MemoryConverter()

        assert converter.extract_tags_list("not a list") == []
        assert converter.extract_tags_list(None) == []
        assert converter.extract_tags_list(123) == []

    def test_safe_string_conversion(self):
        """Test safe string conversion."""
        converter = MemoryConverter()

        assert converter.safe_string_conversion("hello") == "hello"
        assert converter.safe_string_conversion(123) == "123"
        assert converter.safe_string_conversion(None) == ""
        assert converter.safe_string_conversion(None, "default") == "default"

    def test_safe_timestamp_conversion_valid(self):
        """Test safe timestamp conversion with valid input."""
        converter = MemoryConverter()
        iso_string = "2024-01-01T12:00:00"

        result = converter.safe_timestamp_conversion(iso_string)
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_safe_timestamp_conversion_invalid(self):
        """Test safe timestamp conversion with invalid input."""
        converter = MemoryConverter()

        # Should return current time for invalid inputs
        result1 = converter.safe_timestamp_conversion("invalid")
        result2 = converter.safe_timestamp_conversion(None)
        result3 = converter.safe_timestamp_conversion(123)

        assert isinstance(result1, datetime)
        assert isinstance(result2, datetime)
        assert isinstance(result3, datetime)

    def test_memory_dict_to_record_valid(self):
        """Test converting valid memory dict to record."""
        converter = MemoryConverter()
        memory_dict = {
            "key": "test_key",
            "content": "test content",
            "tags": ["tag1", "tag2"],
            "timestamp": "2024-01-01T12:00:00",
        }

        record = converter.memory_dict_to_record(memory_dict)
        assert record is not None
        assert record.key == "test_key"
        assert record.content == "test content"
        assert record.tags == ["tag1", "tag2"]
        assert record.timestamp.year == 2024

    def test_memory_dict_to_record_invalid(self):
        """Test converting invalid memory dict to record."""
        converter = MemoryConverter()

        # Missing required fields should still work with defaults
        memory_dict = {}
        record = converter.memory_dict_to_record(memory_dict)
        assert record is not None
        assert record.key == ""
        assert record.tags == []

    def test_record_to_dict(self):
        """Test converting memory record to dict."""
        converter = MemoryConverter()
        record = MemoryRecord(
            key="test_key",
            content="test content",
            tags=["tag1", "tag2"],
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            priority=MemoryPriority.LOW,
            metadata=MemoryMetadata(),
            ttl_seconds=None,
            embedding=None,
        )

        result = converter.record_to_dict(record)
        assert result["key"] == "test_key"
        assert result["content"] == "test content"
        assert result["tags"] == ["tag1", "tag2"]
        assert result["timestamp"] == "2024-01-01T12:00:00"
        assert result["priority"] == "low"

    def test_add_relevance_score(self):
        """Test adding relevance score to memory dict."""
        converter = MemoryConverter()
        memory_dict = {"key": "test", "content": "content"}

        enhanced = converter.add_relevance_score(memory_dict, 0.85, "semantic")
        assert enhanced["relevance_score"] == 0.85
        assert enhanced["search_type"] == "semantic"
        assert enhanced["key"] == "test"  # Original data preserved


class TestEnhancedMemoryStoreRefactor:
    """Test the refactored EnhancedMemoryStore functionality."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store."""
        vector_store = Mock()
        vector_store.add_memory = Mock()
        vector_store.hybrid_search = Mock()
        vector_store.get_stats = Mock(return_value={"total_embeddings": 0})
        return vector_store

    @pytest.fixture
    def enhanced_store(self, mock_vector_store):
        """Create an enhanced memory store with mocked vector store."""
        return EnhancedMemoryStore(vector_store=mock_vector_store)

    def test_initialization_with_converter(self, enhanced_store):
        """Test that store initializes with memory converter."""
        assert hasattr(enhanced_store, "memory_converter")
        assert isinstance(enhanced_store.memory_converter, MemoryConverter)

    def test_filter_memories_by_tags(self, enhanced_store):
        """Test the tag filtering helper method."""
        # Store some test data
        enhanced_store.store("key1", "content1", ["tag1", "common"])
        enhanced_store.store("key2", "content2", ["tag2", "common"])
        enhanced_store.store("key3", "content3", ["tag3"])

        # Test filtering
        result = enhanced_store._filter_memories_by_tags(["common"])
        assert len(result) == 2

        keys = [r["key"] for r in result]
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" not in keys

    def test_perform_semantic_search_on_memories(self, enhanced_store, mock_vector_store):
        """Test the semantic search helper method."""
        # Mock vector store response
        mock_result = Mock()
        mock_result.memory = {"key": "test", "content": "content"}
        mock_result.similarity_score = 0.85
        mock_result.search_type = "semantic"
        mock_vector_store.hybrid_search.return_value = [mock_result]

        memories = [{"key": "test", "content": "content"}]
        result = enhanced_store._perform_semantic_search_on_memories("query", memories, 10)

        assert len(result) == 1
        assert result[0]["relevance_score"] == 0.85
        assert result[0]["search_type"] == "semantic"

    def test_perform_semantic_search_empty_memories(self, enhanced_store):
        """Test semantic search with empty memories list."""
        result = enhanced_store._perform_semantic_search_on_memories("query", [], 10)
        assert result == []

    def test_format_tag_only_results(self, enhanced_store):
        """Test the tag-only results formatting."""
        memories = [
            {"key": "key1", "content": "content1"},
            {"key": "key2", "content": "content2"},
            {"key": "key3", "content": "content3"},
        ]

        result = enhanced_store._format_tag_only_results(memories, 2)
        assert len(result) == 2
        assert result[0]["key"] == "key1"
        assert result[1]["key"] == "key2"

    def test_format_all_memories_results(self, enhanced_store):
        """Test the all memories results formatting."""
        enhanced_store.store("key1", "content1", ["tag1"])
        enhanced_store.store("key2", "content2", ["tag2"])

        result = enhanced_store._format_all_memories_results(10)
        assert len(result) == 2
        assert all("key" in r for r in result)
        assert all("content" in r for r in result)

    def test_combined_search_refactored_tags_and_query(self, enhanced_store, mock_vector_store):
        """Test refactored combined_search with both tags and query."""
        # Setup
        enhanced_store.store("key1", "content1", ["tag1"])
        enhanced_store.store("key2", "content2", ["tag1"])

        mock_result = Mock()
        mock_result.memory = {"key": "key1", "content": "content1"}
        mock_result.similarity_score = 0.85
        mock_result.search_type = "semantic"
        mock_vector_store.hybrid_search.return_value = [mock_result]

        # Test
        result = enhanced_store.combined_search(tags=["tag1"], query="test query", top_k=10)

        assert len(result) == 1
        assert result[0]["key"] == "key1"
        assert "relevance_score" in result[0]

    def test_combined_search_refactored_tags_only(self, enhanced_store):
        """Test refactored combined_search with tags only."""
        enhanced_store.store("key1", "content1", ["tag1"])
        enhanced_store.store("key2", "content2", ["tag2"])

        result = enhanced_store.combined_search(tags=["tag1"], top_k=10)

        assert len(result) == 1
        assert result[0]["key"] == "key1"

    def test_combined_search_refactored_query_only(self, enhanced_store):
        """Test refactored combined_search with query only."""
        enhanced_store.store("key1", "content1", ["tag1"])

        with patch.object(enhanced_store, "semantic_search") as mock_semantic:
            mock_semantic.return_value = [{"key": "key1", "content": "content1"}]

            result = enhanced_store.combined_search(query="test query", top_k=10)

            mock_semantic.assert_called_once_with("test query", 10)
            assert len(result) == 1

    def test_combined_search_refactored_no_params(self, enhanced_store):
        """Test refactored combined_search with no parameters."""
        enhanced_store.store("key1", "content1", ["tag1"])
        enhanced_store.store("key2", "content2", ["tag2"])

        result = enhanced_store.combined_search(top_k=10)

        assert len(result) == 2
        assert all("key" in r for r in result)

    def test_combined_search_function_length(self):
        """Test that combined_search function is under 50 lines."""
        import inspect

        source_lines = inspect.getsource(EnhancedMemoryStore.combined_search)
        line_count = len(
            [
                line
                for line in source_lines.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
        )
        assert line_count <= 50, f"combined_search has {line_count} lines, should be <= 50"

    def test_optimized_search_performance(self, enhanced_store):
        """Test that optimized search performs better with type caching."""
        # Store test data with various tag types
        test_data = [
            ("key1", "content1", ["tag1", "common"]),
            ("key2", "content2", ["tag2", "common"]),
            ("key3", "content3", ["tag3"]),
        ]

        for key, content, tags in test_data:
            enhanced_store.store(key, content, tags)

        # Clear the type cache to test caching behavior
        enhanced_store.memory_converter.type_cache.clear()

        # Perform search - this should populate the cache
        result1 = enhanced_store.search(["common"])
        assert len(result1.records) == 2

        # Check that type cache has entries
        assert len(enhanced_store.memory_converter.type_cache._type_cache) > 0

        # Perform another search - should use cached results
        result2 = enhanced_store.search(["common"])
        assert len(result2.records) == 2

    def test_memory_conversion_integration(self, enhanced_store):
        """Test that memory conversion works correctly in real usage."""
        enhanced_store.store("test_key", "test content", ["tag1", "tag2"])

        # Test search conversion
        search_result = enhanced_store.search(["tag1"])
        assert len(search_result.records) == 1
        record = search_result.records[0]
        assert record.key == "test_key"
        assert record.content == "test content"
        assert record.tags == ["tag1", "tag2"]

        # Test get_all conversion
        all_result = enhanced_store.get_all()
        assert len(all_result.records) == 1
        assert all_result.records[0].key == "test_key"


def test_create_memory_converter_factory():
    """Test the factory function for creating memory converters."""
    converter = create_memory_converter()
    assert isinstance(converter, MemoryConverter)
    assert isinstance(converter.type_cache, TypeConversionCache)


class TestRegressionPrevention:
    """Test to ensure no regression in existing functionality."""

    @pytest.fixture
    def enhanced_store(self):
        """Create enhanced store for regression testing."""
        with patch("agency_memory.enhanced_memory_store.VectorStore"):
            return EnhancedMemoryStore()

    def test_store_functionality_unchanged(self, enhanced_store):
        """Test that store functionality remains unchanged."""
        enhanced_store.store("key1", "content1", ["tag1", "tag2"])

        # Check internal storage
        assert "key1" in enhanced_store._memories
        memory = enhanced_store._memories["key1"]
        assert memory["content"] == "content1"
        assert memory["tags"] == ["tag1", "tag2"]

    def test_search_functionality_unchanged(self, enhanced_store):
        """Test that search functionality remains unchanged."""
        enhanced_store.store("key1", "content1", ["tag1", "common"])
        enhanced_store.store("key2", "content2", ["tag2", "common"])
        enhanced_store.store("key3", "content3", ["tag3"])

        result = enhanced_store.search(["common"])
        assert len(result.records) == 2
        keys = [r.key for r in result.records]
        assert "key1" in keys
        assert "key2" in keys

    def test_get_all_functionality_unchanged(self, enhanced_store):
        """Test that get_all functionality remains unchanged."""
        enhanced_store.store("key1", "content1", ["tag1"])
        enhanced_store.store("key2", "content2", ["tag2"])

        result = enhanced_store.get_all()
        assert len(result.records) == 2
        assert result.total_count == 2

    def test_learning_patterns_functionality_unchanged(self, enhanced_store):
        """Test that learning patterns functionality remains unchanged."""
        # Store some memories with learning-related tags
        enhanced_store.store("key1", "successful tool usage", ["tool", "success"])
        enhanced_store.store("key2", "error occurred", ["error"])
        enhanced_store.store("key3", "agent handoff", ["handoff", "agent"])

        patterns = enhanced_store.get_learning_patterns()
        assert isinstance(patterns, list)
        # Should return empty list due to insufficient data, but function should work
