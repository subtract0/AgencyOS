"""
Tests for the Enhanced Memory Store with Result pattern implementation.

Tests error propagation, type safety, and improved error handling
in the agency_memory module.
"""

from unittest.mock import Mock, patch

import pytest

from agency_memory.enhanced_memory_store_result import (
    EnhancedMemoryStoreResult,
    MemoryStoreError,
    create_enhanced_memory_store_result,
)
from shared.models.memory import MemorySearchResult
from shared.type_definitions.result import Err, Ok


class TestEnhancedMemoryStoreResultBasics:
    """Test basic functionality of EnhancedMemoryStoreResult."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()

    def test_initialization(self):
        """Test store initialization."""
        assert self.store is not None
        assert hasattr(self.store, "_memories")
        assert hasattr(self.store, "vector_store")

    def test_factory_function(self):
        """Test factory function."""
        store = create_enhanced_memory_store_result("test-provider")
        assert isinstance(store, EnhancedMemoryStoreResult)


class TestStoreResultMethod:
    """Test store_result method with Result pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()

    def test_store_result_success(self):
        """Test successful store operation."""
        result = self.store.store_result("test_key", "test content", ["tag1", "tag2"])
        assert result.is_ok()
        assert result.unwrap() is None
        assert "test_key" in self.store._memories

    def test_store_result_invalid_key_empty(self):
        """Test store with empty key."""
        result = self.store.store_result("", "content", ["tag1"])
        assert result.is_err()
        assert MemoryStoreError.INVALID_KEY in result.unwrap_err()

    def test_store_result_invalid_key_none(self):
        """Test store with None key."""
        result = self.store.store_result(None, "content", ["tag1"])
        assert result.is_err()
        assert MemoryStoreError.INVALID_KEY in result.unwrap_err()

    def test_store_result_invalid_key_wrong_type(self):
        """Test store with wrong key type."""
        result = self.store.store_result(123, "content", ["tag1"])
        assert result.is_err()
        assert MemoryStoreError.INVALID_KEY in result.unwrap_err()

    def test_store_result_invalid_content_none(self):
        """Test store with None content."""
        result = self.store.store_result("test_key", None, ["tag1"])
        assert result.is_err()
        assert MemoryStoreError.INVALID_CONTENT in result.unwrap_err()

    @patch("agency_memory.enhanced_memory_store_result.logger")
    def test_store_result_vector_store_failure_logs_warning(self, mock_logger):
        """Test that vector store failures are logged but don't fail the operation."""
        # Mock vector store to raise exception
        self.store.vector_store = Mock()
        self.store.vector_store.add_memory.side_effect = Exception("Vector store error")

        result = self.store.store_result("test_key", "content", ["tag1"])

        # Operation should still succeed
        assert result.is_ok()
        assert "test_key" in self.store._memories

        # Warning should be logged
        mock_logger.warning.assert_called_once()
        assert "Vector store operation failed" in str(mock_logger.warning.call_args)


class TestSearchResultMethod:
    """Test search_result method with Result pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()
        # Add some test data
        self.store.store_result("key1", "content1", ["tag1", "tag2"])
        self.store.store_result("key2", "content2", ["tag2", "tag3"])
        self.store.store_result("key3", "content3", ["tag3", "tag4"])

    def test_search_result_success(self):
        """Test successful search operation."""
        result = self.store.search_result(["tag1"])
        assert result.is_ok()

        search_result = result.unwrap()
        assert isinstance(search_result, MemorySearchResult)
        assert search_result.total_count == 1
        assert search_result.search_query == {"tags": ["tag1"]}

    def test_search_result_multiple_tags(self):
        """Test search with multiple tags."""
        result = self.store.search_result(["tag2", "tag3"])
        assert result.is_ok()

        search_result = result.unwrap()
        assert search_result.total_count == 3  # All memories have tag2 or tag3

    def test_search_result_no_matches(self):
        """Test search with no matching tags."""
        result = self.store.search_result(["nonexistent_tag"])
        assert result.is_ok()

        search_result = result.unwrap()
        assert search_result.total_count == 0

    def test_search_result_empty_tags(self):
        """Test search with empty tags list."""
        result = self.store.search_result([])
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()


class TestSemanticSearchResultMethod:
    """Test semantic_search_result method with Result pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()
        # Add some test data
        self.store.store_result("key1", "test content about cats", ["animal"])
        self.store.store_result("key2", "test content about dogs", ["animal"])

    def test_semantic_search_result_success(self):
        """Test successful semantic search."""
        with patch.object(self.store, "_perform_vector_search") as mock_search:
            mock_search.return_value = Ok([{"key": "key1", "content": "cats"}])

            result = self.store.semantic_search_result("pets", top_k=5)
            assert result.is_ok()
            assert len(result.unwrap()) == 1

    def test_semantic_search_result_invalid_query_empty(self):
        """Test semantic search with empty query."""
        result = self.store.semantic_search_result("", top_k=5)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_invalid_query_none(self):
        """Test semantic search with None query."""
        result = self.store.semantic_search_result(None, top_k=5)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_invalid_top_k_zero(self):
        """Test semantic search with zero top_k."""
        result = self.store.semantic_search_result("test", top_k=0)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_invalid_top_k_negative(self):
        """Test semantic search with negative top_k."""
        result = self.store.semantic_search_result("test", top_k=-1)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_invalid_similarity_low(self):
        """Test semantic search with similarity below 0."""
        result = self.store.semantic_search_result("test", min_similarity=-0.1)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_invalid_similarity_high(self):
        """Test semantic search with similarity above 1."""
        result = self.store.semantic_search_result("test", min_similarity=1.1)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_semantic_search_result_empty_store(self):
        """Test semantic search on empty store."""
        empty_store = EnhancedMemoryStoreResult()
        result = empty_store.semantic_search_result("test")
        assert result.is_ok()
        assert result.unwrap() == []

    def test_semantic_search_result_vector_search_failure(self):
        """Test semantic search when vector search fails."""
        with patch.object(self.store, "_perform_vector_search") as mock_search:
            mock_search.return_value = Err("Vector search failed")

            result = self.store.semantic_search_result("test")
            assert result.is_err()
            assert "Vector search failed" in result.unwrap_err()


class TestCombinedSearchResultMethod:
    """Test combined_search_result method with Result pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()
        self.store.store_result("key1", "content about cats", ["animal", "pet"])
        self.store.store_result("key2", "content about dogs", ["animal", "pet"])
        self.store.store_result("key3", "content about cars", ["vehicle"])

    def test_combined_search_result_no_parameters(self):
        """Test combined search with no parameters."""
        result = self.store.combined_search_result()
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_combined_search_result_invalid_top_k(self):
        """Test combined search with invalid top_k."""
        result = self.store.combined_search_result(tags=["animal"], top_k=0)
        assert result.is_err()
        assert MemoryStoreError.SEARCH_FAILED in result.unwrap_err()

    def test_combined_search_result_tags_only(self):
        """Test combined search with tags only."""
        result = self.store.combined_search_result(tags=["animal"])
        assert result.is_ok()
        memories = result.unwrap()
        assert len(memories) == 2  # Both cat and dog memories

    def test_combined_search_result_query_only(self):
        """Test combined search with query only."""
        with patch.object(self.store, "semantic_search_result") as mock_search:
            mock_search.return_value = Ok([{"key": "key1"}])

            result = self.store.combined_search_result(query="pets")
            assert result.is_ok()
            mock_search.assert_called_once_with("pets", 10)

    def test_combined_search_result_tags_and_query(self):
        """Test combined search with both tags and query."""
        with patch.object(self.store, "_perform_vector_search_on_subset") as mock_search:
            mock_search.return_value = Ok([{"key": "key1"}])

            result = self.store.combined_search_result(tags=["animal"], query="cats")
            assert result.is_ok()
            mock_search.assert_called_once()

    def test_combined_search_result_tags_search_failure(self):
        """Test combined search when tag search fails."""
        with patch.object(self.store, "search_result") as mock_search:
            mock_search.return_value = Err("Tag search failed")

            result = self.store.combined_search_result(tags=["animal"], query="cats")
            assert result.is_ok()
            assert result.unwrap() == []  # Graceful degradation


class TestLegacyInterfaceCompatibility:
    """Test legacy interface methods for backward compatibility."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()

    @patch("agency_memory.enhanced_memory_store_result.logger")
    def test_legacy_store_success(self, mock_logger):
        """Test legacy store method with success."""
        self.store.store("test_key", "content", ["tag1"])
        assert "test_key" in self.store._memories
        mock_logger.error.assert_not_called()

    @patch("agency_memory.enhanced_memory_store_result.logger")
    def test_legacy_store_failure(self, mock_logger):
        """Test legacy store method with failure."""
        self.store.store("", "content", ["tag1"])  # Invalid key
        mock_logger.error.assert_called_once()
        assert "Store operation failed" in str(mock_logger.error.call_args)

    @patch("agency_memory.enhanced_memory_store_result.logger")
    def test_legacy_search_success(self, mock_logger):
        """Test legacy search method with success."""
        self.store.store("key1", "content", ["tag1"])
        result = self.store.search(["tag1"])
        assert isinstance(result, MemorySearchResult)
        assert result.total_count == 1
        mock_logger.error.assert_not_called()

    @patch("agency_memory.enhanced_memory_store_result.logger")
    def test_legacy_search_failure(self, mock_logger):
        """Test legacy search method with failure."""
        result = self.store.search([])  # Empty tags
        assert isinstance(result, MemorySearchResult)
        assert result.total_count == 0
        mock_logger.error.assert_called_once()

    def test_legacy_semantic_search_success(self):
        """Test legacy semantic search method with success."""
        with patch.object(self.store, "semantic_search_result") as mock_search:
            mock_search.return_value = Ok([{"key": "key1"}])

            result = self.store.semantic_search("test")
            assert result == [{"key": "key1"}]

    def test_legacy_semantic_search_failure(self):
        """Test legacy semantic search method with failure."""
        with patch.object(self.store, "semantic_search_result") as mock_search:
            mock_search.return_value = Err("Search failed")

            result = self.store.semantic_search("test")
            assert result == []  # Returns empty list on error


class TestPrivateHelperMethods:
    """Test private helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = EnhancedMemoryStoreResult()

    def test_convert_to_memory_record_success(self):
        """Test successful memory record conversion."""
        result = self.store._convert_to_memory_record("key", "content", ["tag1"])
        assert result.is_ok()

        memory_record = result.unwrap()
        assert memory_record["key"] == "key"
        assert memory_record["content"] == "content"

    def test_add_to_vector_store_success(self):
        """Test successful vector store addition."""
        memory_record = {"key": "test", "content": "test"}

        with patch.object(self.store.vector_store, "add_memory") as mock_add:
            result = self.store._add_to_vector_store("key", memory_record)
            assert result.is_ok()
            mock_add.assert_called_once_with("key", memory_record)

    def test_add_to_vector_store_failure(self):
        """Test vector store addition failure."""
        memory_record = {"key": "test", "content": "test"}

        with patch.object(self.store.vector_store, "add_memory") as mock_add:
            mock_add.side_effect = Exception("Vector store error")

            result = self.store._add_to_vector_store("key", memory_record)
            assert result.is_err()
            assert "Vector store operation failed" in result.unwrap_err()

    def test_filter_memories_by_tags(self):
        """Test memory filtering by tags."""
        # Add test memories
        self.store.store_result("key1", "content1", ["tag1", "tag2"])
        self.store.store_result("key2", "content2", ["tag3"])

        filtered = self.store._filter_memories_by_tags(["tag1"])
        assert len(filtered) == 1

        filtered = self.store._filter_memories_by_tags(["tag1", "tag3"])
        assert len(filtered) == 2

        filtered = self.store._filter_memories_by_tags(["nonexistent"])
        assert len(filtered) == 0


if __name__ == "__main__":
    pytest.main([__file__])
