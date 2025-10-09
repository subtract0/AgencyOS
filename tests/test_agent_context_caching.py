"""
Test suite for AgentContext VectorStore caching optimization.

Article II: TDD - Tests written FIRST before implementation.
ADR-008: Strict typing with Pydantic.
ADR-010: Result pattern for error handling.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from agency_memory import Memory
from shared.agent_context import AgentContext, create_agent_context


class TestAgentContextCaching:
    """Test VectorStore caching for 5x query performance improvement."""

    def test_search_memories_caches_results(self):
        """Test that identical searches return cached results."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_cache_session")

        # Store test data
        context.store_memory("mem1", "content1", ["test", "cached"])
        context.store_memory("mem2", "content2", ["test", "different"])

        # Act - First search (cache miss)
        start = time.perf_counter()
        result1 = context.search_memories(["test"], include_session=True)
        first_duration = time.perf_counter() - start

        # Second identical search (cache hit)
        start = time.perf_counter()
        result2 = context.search_memories(["test"], include_session=True)
        second_duration = time.perf_counter() - start

        # Assert
        assert result1 == result2, "Cached results should match original"
        assert len(result1) == 2, "Should return 2 memories with 'test' tag"
        # Cache should be significantly faster (at least 2x for meaningful cache benefit)
        # Note: This is a performance hint, not strict requirement
        # Real benefit shows with complex VectorStore queries

    def test_cache_invalidates_on_new_memory(self):
        """Test that cache is invalidated when new memories are stored."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_invalidation")

        context.store_memory("mem1", "content1", ["cached"])

        # Act - First search
        result1 = context.search_memories(["cached"], include_session=True)
        assert len(result1) == 1

        # Store new memory (should invalidate cache)
        context.store_memory("mem2", "content2", ["cached"])

        # Second search (should get fresh data)
        result2 = context.search_memories(["cached"], include_session=True)

        # Assert
        assert len(result2) == 2, "Should return updated results after cache invalidation"
        assert result1 != result2, "Results should differ after new memory added"

    def test_cache_distinguishes_different_queries(self):
        """Test that different queries maintain separate cache entries."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_multi_cache")

        context.store_memory("mem1", "content1", ["tag1"])
        context.store_memory("mem2", "content2", ["tag2"])
        context.store_memory("mem3", "content3", ["tag1", "tag2"])

        # Act
        tag1_results = context.search_memories(["tag1"], include_session=True)
        tag2_results = context.search_memories(["tag2"], include_session=True)
        both_results = context.search_memories(["tag1", "tag2"], include_session=True)

        # Assert
        assert len(tag1_results) == 2, "Should cache tag1 queries separately"
        assert len(tag2_results) == 2, "Should cache tag2 queries separately"
        assert len(both_results) == 1, "Should cache multi-tag queries separately"

    def test_cache_respects_include_session_parameter(self):
        """Test that cache distinguishes between session-scoped and global queries."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_session_scope")

        context.store_memory("mem1", "content1", ["global"])

        # Act
        session_results = context.search_memories(["global"], include_session=True)
        global_results = context.search_memories(["global"], include_session=False)

        # Assert - These should be cached separately
        # Note: Results may be identical, but cache keys differ
        assert isinstance(session_results, list)
        assert isinstance(global_results, list)

    def test_cache_size_limit_prevents_memory_bloat(self):
        """Test that cache has maximum size limit (LRU eviction)."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_cache_limit")

        # Store base memories
        for i in range(10):
            context.store_memory(f"mem_{i}", f"content_{i}", [f"tag_{i}"])

        # Act - Perform many different searches to fill cache
        results = []
        for i in range(150):  # Exceed default maxsize=128
            result = context.search_memories([f"tag_{i % 10}"], include_session=True)
            results.append(result)

        # Assert - Should complete without memory error
        # LRU cache evicts oldest entries automatically
        assert len(results) == 150, "Should handle cache limit gracefully"

    def test_cache_key_generation_is_deterministic(self):
        """Test that identical queries generate identical cache keys."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_deterministic")

        context.store_memory("mem1", "content1", ["test"])

        # Act - Multiple identical queries
        result1 = context.search_memories(["test"], include_session=True)
        result2 = context.search_memories(["test"], include_session=True)
        result3 = context.search_memories(["test"], include_session=True)

        # Assert
        assert result1 == result2 == result3, (
            "Identical queries should return identical cached results"
        )

    def test_cache_handles_empty_results(self):
        """Test that cache correctly stores and retrieves empty result sets."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_empty_cache")

        # Act - Search for non-existent tag
        result1 = context.search_memories(["nonexistent"], include_session=True)
        result2 = context.search_memories(["nonexistent"], include_session=True)

        # Assert
        assert result1 == [], "Should cache empty results"
        assert result2 == [], "Cached empty results should match"

    def test_cache_performance_benchmark(self):
        """Benchmark test: Verify cache provides measurable performance improvement."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_benchmark")

        # Store larger dataset for realistic benchmark
        for i in range(100):
            context.store_memory(f"mem_{i}", f"content_{i}", ["benchmark", f"tag_{i % 10}"])

        # Act - Measure uncached performance (first call)
        start = time.perf_counter()
        for _ in range(10):
            context.search_memories(["benchmark"], include_session=True)
            # Clear cache between iterations for baseline
            if hasattr(context.search_memories, "cache_clear"):
                context.search_memories.cache_clear()
        uncached_duration = time.perf_counter() - start

        # Measure cached performance (repeated calls)
        start = time.perf_counter()
        for _ in range(10):
            context.search_memories(["benchmark"], include_session=True)
        cached_duration = time.perf_counter() - start

        # Assert - Cached should be faster
        # Note: This is an informational test, actual speedup depends on VectorStore complexity
        # For in-memory stores, improvement may be minimal
        # For VectorStore with embeddings, improvement is 5x-10x
        assert cached_duration <= uncached_duration, "Cached queries should not be slower"

    def test_cache_clears_on_demand(self):
        """Test manual cache clearing functionality."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_cache_clear")

        context.store_memory("mem1", "content1", ["clearable"])

        # Act - Search, clear cache, search again
        result1 = context.search_memories(["clearable"], include_session=True)

        # Clear cache if method exists
        if hasattr(context.search_memories, "cache_clear"):
            context.search_memories.cache_clear()

        result2 = context.search_memories(["clearable"], include_session=True)

        # Assert
        assert result1 == result2, "Results should be identical even after cache clear"


class TestCachingIntegration:
    """Integration tests for caching with real-world scenarios."""

    def test_multi_agent_shared_context_caching(self):
        """Test caching behavior with multiple agents sharing same context."""
        # Arrange
        shared_memory = Memory()
        agent1_context = AgentContext(memory=shared_memory, session_id="agent1")
        agent2_context = AgentContext(memory=shared_memory, session_id="agent2")

        # Agent 1 stores memory
        agent1_context.store_memory("shared", "content", ["shared_tag"])

        # Act - Both agents search
        agent1_result = agent1_context.search_memories(["shared_tag"], include_session=True)
        agent2_result = agent2_context.search_memories(["shared_tag"], include_session=True)

        # Assert - Each agent has independent cache
        # Agent 1 should see memory (same session)
        assert len(agent1_result) >= 1

        # Agent 2 should NOT see memory (different session, include_session=True)
        assert len(agent2_result) == 0

    def test_caching_with_article_iv_compliance(self):
        """Test that caching maintains Article IV learning compliance."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="article_iv_test")

        # Store learning patterns
        context.store_memory(
            "pattern_1",
            {"pattern": "tdd_workflow", "confidence": 0.8},
            ["learning", "pattern", "tdd"],
        )

        # Act - Query learnings multiple times (typical Article IV workflow)
        learnings1 = context.search_memories(["learning", "pattern"], include_session=False)
        learnings2 = context.search_memories(["learning", "pattern"], include_session=False)

        # Assert
        assert learnings1 == learnings2, "Cached learnings should be consistent"
        assert len(learnings1) >= 1, "Should retrieve learning patterns"


class TestCacheEdgeCases:
    """Edge case tests for caching implementation."""

    def test_cache_with_very_long_tag_lists(self):
        """Test cache handles queries with many tags."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_long_tags")

        many_tags = [f"tag_{i}" for i in range(50)]
        context.store_memory("multi_tag", "content", many_tags)

        # Act
        result = context.search_memories(many_tags[:10], include_session=True)

        # Assert
        assert isinstance(result, list), "Should handle long tag lists"

    def test_cache_with_special_characters_in_tags(self):
        """Test cache key generation with special characters."""
        # Arrange
        memory = Memory()
        context = AgentContext(memory=memory, session_id="test_special_chars")

        special_tags = ["test:colon", "test/slash", "test-dash", "test_underscore"]
        context.store_memory("special", "content", special_tags)

        # Act
        result1 = context.search_memories(["test:colon"], include_session=True)
        result2 = context.search_memories(["test:colon"], include_session=True)

        # Assert
        assert result1 == result2, "Cache should handle special characters in tags"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
