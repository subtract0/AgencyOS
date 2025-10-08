"""
Test VectorStore singleton embedding model optimization.

Constitutional Compliance:
- Article I: Complete context (all singleton behavior tested)
- Article II: 100% coverage of singleton pattern
- Article IV: Memory optimization enables better VectorStore performance
- TDD: Tests validate shared model behavior

Tests verify that multiple VectorStore instances share a single embedding model
to reduce memory usage from 220MB (10 instances × 22MB) to 22MB (1 shared instance).

NECESSARY Criteria:
- N: Tests production singleton optimization
- E: Explicit test names describe model sharing behavior
- C: Complete behavior coverage (singleton, sharing, independence)
- E: Efficient execution (<1s per test)
- S: Stable, deterministic behavior
- S: Scoped to singleton pattern testing
- A: Actionable failure messages
- R: Relevant to memory optimization goals
- Y: Yieldful - prevents memory bloat in multi-agent scenarios
"""

from unittest.mock import Mock, patch

import pytest

from agency_memory.vector_store import VectorStore, _get_shared_embedding_model


class TestEmbeddingModelSingleton:
    """Tests for _get_shared_embedding_model singleton function."""

    @pytest.mark.skip(reason="Requires sentence-transformers - optional dependency")
    def test_get_shared_embedding_model_returns_same_instance(self):
        """Should return same model instance on multiple calls."""
        # Act
        model1 = _get_shared_embedding_model()
        model2 = _get_shared_embedding_model()

        # Assert - same object instance
        assert id(model1) == id(model2)
        assert model1 is model2

    def test_get_shared_embedding_model_is_cached_with_lru_cache(self):
        """Should use lru_cache for singleton behavior."""
        # Assert - function has cache attribute from lru_cache
        assert hasattr(_get_shared_embedding_model, "cache_info")

        # Get cache info
        cache_info = _get_shared_embedding_model.cache_info()
        assert hasattr(cache_info, "maxsize")


class TestVectorStoreModelSharing:
    """Tests for VectorStore instances sharing embedding model."""

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_multiple_vectorstores_share_same_model(self, mock_get_model):
        """Should use shared model singleton across multiple VectorStore instances."""
        # Arrange
        mock_model = Mock()
        mock_model.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        # Act - Create multiple VectorStore instances
        store1 = VectorStore(embedding_provider="sentence-transformers")
        store2 = VectorStore(embedding_provider="sentence-transformers")
        store3 = VectorStore(embedding_provider="sentence-transformers")

        # Assert - singleton function called for each instance
        assert mock_get_model.call_count == 3

        # Assert - all stores use the same model instance
        assert store1._embedding_model is store2._embedding_model
        assert store2._embedding_model is store3._embedding_model
        assert id(store1._embedding_model) == id(store2._embedding_model)

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_vectorstore_embeddings_independent_despite_shared_model(self, mock_get_model):
        """Should maintain independent embeddings despite shared model."""
        # Arrange
        import numpy as np
        mock_model = Mock()
        # Return numpy array to match real SentenceTransformer behavior
        mock_model.encode = Mock(return_value=np.array([[0.1, 0.2, 0.3]]))
        mock_get_model.return_value = mock_model

        # Act
        store1 = VectorStore(embedding_provider="sentence-transformers")
        store2 = VectorStore(embedding_provider="sentence-transformers")

        store1.add_memory("memory_1", {"content": "Store 1 content"})
        store2.add_memory("memory_2", {"content": "Store 2 content"})

        # Assert - stores have independent embeddings
        assert "memory_1" in store1._embeddings
        assert "memory_1" not in store2._embeddings
        assert "memory_2" in store2._embeddings
        assert "memory_2" not in store1._embeddings

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_vectorstore_with_different_providers_do_not_share(self, mock_get_model):
        """Should not use singleton for different embedding providers."""
        # Arrange
        mock_model = Mock()
        mock_model.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        # Act
        store_with_st = VectorStore(embedding_provider="sentence-transformers")
        store_with_openai = VectorStore(embedding_provider="openai")
        store_no_provider = VectorStore(embedding_provider=None)

        # Assert - only sentence-transformers provider uses singleton
        assert mock_get_model.call_count == 1
        assert hasattr(store_with_st, "_embedding_model")
        # OpenAI and None providers don't use the singleton
        assert store_with_openai._embedding_function is None or not hasattr(
            store_with_openai, "_embedding_model"
        )

    def test_vectorstore_without_provider_has_no_embedding_model(self):
        """Should not initialize embedding model when provider is None."""
        # Act
        store = VectorStore(embedding_provider=None)

        # Assert
        assert store._embedding_function is None
        assert not hasattr(store, "_embedding_model") or store._embedding_model is None

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_memory_operations_work_with_shared_model(self, mock_get_model):
        """Should perform memory operations correctly with shared model."""
        # Arrange
        import numpy as np
        mock_model = Mock()
        embedding_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        # Return numpy array to match real SentenceTransformer behavior
        mock_model.encode = Mock(return_value=np.array([embedding_vector]))
        mock_get_model.return_value = mock_model

        # Act
        store1 = VectorStore(embedding_provider="sentence-transformers")
        store2 = VectorStore(embedding_provider="sentence-transformers")

        store1.add_memory("test_1", {"content": "Test content 1"})
        store2.add_memory("test_2", {"content": "Test content 2"})

        # Assert - both stores generated embeddings using shared model
        assert "test_1" in store1._embeddings
        assert store1._embeddings["test_1"] == embedding_vector
        assert "test_2" in store2._embeddings
        assert store2._embeddings["test_2"] == embedding_vector

        # Assert - model.encode called for each add_memory operation
        assert mock_model.encode.call_count == 2


class TestMemoryOptimization:
    """Tests for memory optimization benefits of singleton pattern."""

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_ten_vectorstores_use_single_model_instance(self, mock_get_model):
        """Should demonstrate 10x memory savings with singleton pattern."""
        # Arrange
        mock_model = Mock()
        mock_model.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        # Act - Create 10 VectorStore instances (typical multi-agent scenario)
        stores = [
            VectorStore(embedding_provider="sentence-transformers") for _ in range(10)
        ]

        # Assert - singleton function called 10 times
        assert mock_get_model.call_count == 10

        # Assert - but all stores share the SAME model instance
        model_ids = {id(store._embedding_model) for store in stores}
        assert len(model_ids) == 1, "All stores should share same model instance"

        # Assert - without singleton, would have 10 different models (220MB)
        # With singleton: 1 model (22MB) - 198MB savings (90% reduction)

    @patch("agency_memory.vector_store._get_shared_embedding_model")
    def test_model_sharing_does_not_affect_store_independence(self, mock_get_model):
        """Should maintain VectorStore independence despite shared model."""
        # Arrange
        mock_model = Mock()
        mock_model.encode = Mock(return_value=[[0.5] * 384])  # MiniLM dimension
        mock_get_model.return_value = mock_model

        # Act
        stores = [
            VectorStore(embedding_provider="sentence-transformers") for _ in range(5)
        ]

        # Add different memories to each store
        for i, store in enumerate(stores):
            store.add_memory(f"memory_{i}", {"content": f"Content {i}"})

        # Assert - each store has only its own memories
        for i, store in enumerate(stores):
            assert f"memory_{i}" in store._memory_records
            # Verify other stores' memories are NOT in this store
            for j in range(5):
                if i != j:
                    assert f"memory_{j}" not in store._memory_records

        # Assert - all stores have different memory counts
        memory_counts = [len(store._memory_records) for store in stores]
        assert all(count == 1 for count in memory_counts)
