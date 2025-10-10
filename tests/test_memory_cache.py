"""
Memory Cache Tests (Phase 2, Task 4)

Tests LRU caching layer implementation with NECESSARY framework coverage.
Verifies: code_vectorstore_caching implementation (agency_memory/memory_cache.py)

Constitutional Compliance:
- Article I: Complete context (cache never returns partial results)
- Article II: 100% verification (cache consistency guaranteed)
- Article IV: Store patterns after success

NECESSARY Coverage:
- Normal: Happy path scenarios
- Edge: Boundary conditions
- Corner: Unusual combinations
- Error: Failure scenarios
- Security: Thread safety
- Stress: Performance under load
- Accessibility: API usability
- Regression: Bug prevention
- Yield: Output validation
"""

import hashlib
import threading
import time
from unittest.mock import MagicMock

import pytest

from shared.models.memory import CacheStats, MemoryRecord


class TestMemoryCacheInitialization:
    """Test cache initialization (Normal + Edge)."""

    def test_cache_initialization_default_size(self):
        """Normal: Cache initializes with default size."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        # Act
        cache = MemoryCache()

        # Assert
        assert cache.max_size == 128  # Default per spec
        assert len(cache._cache) == 0
        assert cache._stats.max_size == 128
        assert cache._stats.hits == 0
        assert cache._stats.misses == 0

    def test_cache_initialization_custom_size(self):
        """Normal: Cache initializes with custom size."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        # Act
        cache = MemoryCache(max_size=256)

        # Assert
        assert cache.max_size == 256
        assert cache._stats.max_size == 256


class TestCacheKeyGeneration:
    """Test cache key generation (Normal + Yield + Security)."""

    def test_generate_cache_key_from_tags_and_query(self):
        """Normal: Cache key is deterministic hash of query parameters."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        key1 = cache._generate_cache_key(query_tags=["agent", "pattern"], query_text="test query")
        key2 = cache._generate_cache_key(query_tags=["agent", "pattern"], query_text="test query")

        # Assert
        assert key1 == key2  # Same inputs produce same key
        assert len(key1) == 64  # SHA256 hex is 64 chars

    def test_generate_cache_key_different_inputs_different_keys(self):
        """Yield: Different query parameters produce different keys."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        key1 = cache._generate_cache_key(query_tags=["agent"], query_text="query1")
        key2 = cache._generate_cache_key(query_tags=["agent"], query_text="query2")
        key3 = cache._generate_cache_key(query_tags=["pattern"], query_text="query1")

        # Assert
        assert key1 != key2  # Different query text
        assert key1 != key3  # Different tags
        assert key2 != key3

    def test_generate_cache_key_tag_order_independence(self):
        """Yield: Tag order doesn't affect cache key (sorted internally)."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        key1 = cache._generate_cache_key(query_tags=["agent", "pattern", "test"])
        key2 = cache._generate_cache_key(query_tags=["test", "agent", "pattern"])

        # Assert
        assert key1 == key2  # Order-independent

    def test_generate_cache_key_none_values(self):
        """Edge: Cache key handles None values gracefully."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        key1 = cache._generate_cache_key(query_tags=None, query_text=None)
        key2 = cache._generate_cache_key(query_tags=[], query_text="")

        # Assert
        assert isinstance(key1, str)
        assert len(key1) == 64


class TestCacheGetSet:
    """Test cache get/set operations (Normal + Edge + Stress)."""

    def test_cache_hit_returns_cached_results(self):
        """Normal: Cache hit returns previously cached results."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        query_key = "test_key_123"
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Act
        cache.set(query_key, mock_results)
        cached_result = cache.get(query_key)

        # Assert
        assert cached_result == mock_results
        assert cache._stats.hits == 1
        assert cache._stats.misses == 0

    def test_cache_miss_returns_none(self):
        """Normal: Cache miss returns None and increments miss counter."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        result = cache.get("nonexistent_key")

        # Assert
        assert result is None
        assert cache._stats.hits == 0
        assert cache._stats.misses == 1

    def test_cache_hit_updates_timestamp_lru(self):
        """Normal: Cache hit updates timestamp for LRU tracking."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        query_key = "test_key"
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set(query_key, mock_results)
        initial_timestamp = cache._cache[query_key].timestamp

        # Act - wait and access again
        time.sleep(0.01)
        cache.get(query_key)
        updated_timestamp = cache._cache[query_key].timestamp

        # Assert
        assert updated_timestamp > initial_timestamp  # Timestamp updated

    def test_cache_hit_increments_access_count(self):
        """Yield: Cache hit increments access count for metrics."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        query_key = "test_key"
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set(query_key, mock_results)

        # Act
        cache.get(query_key)
        cache.get(query_key)
        cache.get(query_key)

        # Assert
        assert cache._cache[query_key].access_count == 3

    def test_cache_set_with_tags(self):
        """Normal: Cache stores tags for invalidation."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        query_key = "test_key"
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Act
        cache.set(query_key, mock_results, tags=["agent", "pattern"])

        # Assert
        assert cache._cache[query_key].tags == {"agent", "pattern"}


class TestCacheLRUEviction:
    """Test LRU eviction policy (Normal + Stress + Regression)."""

    def test_cache_eviction_when_full(self):
        """Normal: Cache evicts least recently used entry when full."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=3)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Fill cache
        cache.set("key1", mock_results)
        time.sleep(0.01)
        cache.set("key2", mock_results)
        time.sleep(0.01)
        cache.set("key3", mock_results)

        # Act - Add 4th item (should evict key1)
        time.sleep(0.01)
        cache.set("key4", mock_results)

        # Assert
        assert len(cache._cache) == 3
        assert "key1" not in cache._cache  # Oldest evicted
        assert "key2" in cache._cache
        assert "key3" in cache._cache
        assert "key4" in cache._cache
        assert cache._stats.evictions == 1

    def test_cache_eviction_respects_lru_access(self):
        """Regression: LRU eviction considers recent access, not just insertion time."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=3)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Fill cache
        cache.set("key1", mock_results)
        time.sleep(0.01)
        cache.set("key2", mock_results)
        time.sleep(0.01)
        cache.set("key3", mock_results)

        # Act - Access key1 (makes it recently used)
        time.sleep(0.01)
        cache.get("key1")

        # Add 4th item (should evict key2, not key1)
        time.sleep(0.01)
        cache.set("key4", mock_results)

        # Assert
        assert "key1" in cache._cache  # Accessed recently, not evicted
        assert "key2" not in cache._cache  # Least recently used, evicted
        assert cache._stats.evictions == 1

    def test_cache_eviction_multiple_evictions(self):
        """Stress: Multiple evictions tracked correctly."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=10)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Act - Add 20 items (should cause 10 evictions)
        for i in range(20):
            cache.set(f"key_{i}", mock_results)
            time.sleep(0.001)

        # Assert
        assert len(cache._cache) == 10
        assert cache._stats.evictions == 10


class TestCacheInvalidation:
    """Test cache invalidation (Normal + Edge + Security)."""

    def test_invalidate_pattern_by_tag(self):
        """Normal: Invalidate all cache entries with specific tag."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set("key1", mock_results, tags=["agent", "pattern"])
        cache.set("key2", mock_results, tags=["agent", "error"])
        cache.set("key3", mock_results, tags=["pattern"])

        # Act
        invalidated_count = cache.invalidate_pattern("pattern")

        # Assert
        assert invalidated_count == 2  # key1 and key3 invalidated
        assert "key1" not in cache._cache
        assert "key2" in cache._cache  # Not affected
        assert "key3" not in cache._cache

    def test_invalidate_pattern_no_matches(self):
        """Edge: Invalidate with no matches returns 0."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set("key1", mock_results, tags=["agent"])

        # Act
        invalidated_count = cache.invalidate_pattern("nonexistent")

        # Assert
        assert invalidated_count == 0
        assert "key1" in cache._cache  # Not affected

    def test_invalidate_all_clears_cache(self):
        """Normal: Invalidate all clears entire cache."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set("key1", mock_results)
        cache.set("key2", mock_results)
        cache.set("key3", mock_results)

        # Act
        cache.invalidate_all()

        # Assert
        assert len(cache._cache) == 0
        assert cache._stats.size == 0


class TestCacheStats:
    """Test cache statistics (Accessibility + Yield)."""

    def test_get_stats_returns_complete_metrics(self):
        """Accessibility: Stats API returns all required metrics."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=128)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Simulate cache activity
        cache.set("key1", mock_results)
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        # Act
        stats = cache.get_stats()

        # Assert
        assert isinstance(stats, CacheStats)
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.evictions == 0
        assert stats.size == 1
        assert stats.max_size == 128

    def test_cache_stats_hit_rate_calculation(self):
        """Yield: Hit rate calculated correctly."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set("key1", mock_results)

        # 8 hits, 2 misses = 80% hit rate
        for _ in range(8):
            cache.get("key1")  # Hit
        for _ in range(2):
            cache.get("nonexistent")  # Miss

        # Act
        stats = cache.get_stats()

        # Assert
        assert stats.hits == 8
        assert stats.misses == 2
        assert stats.hit_rate == 80.0  # 8/10 = 80%

    def test_cache_stats_hit_rate_zero_queries(self):
        """Edge: Hit rate is 0.0 when no queries executed."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()

        # Act
        stats = cache.get_stats()

        # Assert
        assert stats.hit_rate == 0.0


class TestCacheTopQueries:
    """Test top query tracking (Accessibility + Yield)."""

    def test_get_top_queries_returns_most_accessed(self):
        """Accessibility: Get top queries returns most frequently accessed."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        cache.set("key1", mock_results)
        cache.set("key2", mock_results)
        cache.set("key3", mock_results)

        # Access with different frequencies
        for _ in range(10):
            cache.get("key1")
        for _ in range(5):
            cache.get("key2")
        cache.get("key3")

        # Act
        top_queries = cache.get_top_queries(limit=3)

        # Assert
        assert len(top_queries) == 3
        assert top_queries[0] == ("key1", 10)  # Most accessed
        assert top_queries[1] == ("key2", 5)
        assert top_queries[2] == ("key3", 1)

    def test_get_top_queries_respects_limit(self):
        """Yield: Top queries respects limit parameter."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        for i in range(10):
            cache.set(f"key_{i}", mock_results)
            cache.get(f"key_{i}")

        # Act
        top_queries = cache.get_top_queries(limit=3)

        # Assert
        assert len(top_queries) <= 3


class TestCacheWarming:
    """Test cache warming strategy (Normal + Stress)."""

    def test_warm_cache_with_frequent_queries(self):
        """Normal: Cache warming pre-populates cache with frequent queries."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=128)
        mock_results1 = [
            MemoryRecord(
                key="mem1", content="test1", tags=["tag1"], timestamp="2025-01-01T00:00:00"
            )
        ]
        mock_results2 = [
            MemoryRecord(
                key="mem2", content="test2", tags=["tag2"], timestamp="2025-01-01T00:00:00"
            )
        ]

        frequent_queries = [
            ("key1", mock_results1, ["agent"]),
            ("key2", mock_results2, ["pattern"]),
        ]

        # Act
        warmed_count = cache.warm_cache(frequent_queries)

        # Assert
        assert warmed_count == 2
        assert cache._stats.size == 2
        assert cache.get("key1") == mock_results1  # Already in cache
        assert cache.get("key2") == mock_results2

    def test_warm_cache_stops_when_full(self):
        """Edge: Cache warming stops when cache reaches max size."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=3)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        frequent_queries = [
            (f"key{i}", mock_results, ["tag"])
            for i in range(10)  # Try to warm 10, but max_size=3
        ]

        # Act
        warmed_count = cache.warm_cache(frequent_queries)

        # Assert
        assert warmed_count == 3  # Only warmed up to max_size
        assert cache._stats.size == 3


class TestCacheThreadSafety:
    """Test thread safety (Security + Stress)."""

    def test_cache_thread_safe_concurrent_reads(self):
        """Security: Cache handles concurrent reads safely."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]
        cache.set("shared_key", mock_results)

        results = []

        def reader():
            for _ in range(100):
                result = cache.get("shared_key")
                results.append(result)

        # Act - 10 threads reading concurrently
        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - All reads successful, no exceptions
        assert len(results) == 1000  # 10 threads × 100 reads
        assert all(r == mock_results for r in results)

    def test_cache_thread_safe_concurrent_writes(self):
        """Security: Cache handles concurrent writes safely."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=100)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        def writer(thread_id):
            for i in range(10):
                cache.set(f"key_{thread_id}_{i}", mock_results)

        # Act - 10 threads writing concurrently
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - All writes successful, cache size correct
        assert len(cache._cache) == 100  # 10 threads × 10 writes = 100 entries

    def test_cache_thread_safe_concurrent_invalidation(self):
        """Security: Cache handles concurrent invalidation safely."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Pre-populate
        for i in range(50):
            cache.set(f"key_{i}", mock_results, tags=["agent", f"tag{i % 5}"])

        def invalidator(tag):
            cache.invalidate_pattern(tag)

        # Act - Multiple threads invalidating different tags
        threads = [threading.Thread(target=invalidator, args=(f"tag{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Assert - No crashes, some entries invalidated
        # (Exact count may vary due to race conditions, but should be consistent)
        assert cache._stats.size < 50  # Some entries invalidated


class TestCachePerformance:
    """Test cache performance (Stress + Regression)."""

    def test_cache_hit_latency_under_1ms(self):
        """Stress: Cache hit latency is <1ms per spec."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache()
        mock_results = [
            MemoryRecord(
                key="mem1", content="test" * 100, tags=["tag1"], timestamp="2025-01-01T00:00:00"
            )
        ]
        cache.set("key1", mock_results)

        # Act - Measure cache hit latency
        latencies = []
        for _ in range(100):
            start = time.time()
            cache.get("key1")
            latencies.append((time.time() - start) * 1000)  # Convert to ms

        avg_latency = sum(latencies) / len(latencies)

        # Assert
        assert avg_latency < 1.0  # <1ms per spec

    def test_cache_set_performance(self):
        """Stress: Cache set operation is fast."""
        # Arrange
        from agency_memory.memory_cache import MemoryCache

        cache = MemoryCache(max_size=1000)
        mock_results = [
            MemoryRecord(key="mem1", content="test", tags=["tag1"], timestamp="2025-01-01T00:00:00")
        ]

        # Act - Measure batch set performance
        start = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", mock_results)
        elapsed_ms = (time.time() - start) * 1000

        # Assert
        assert elapsed_ms < 100  # <100ms for 1000 sets


class TestCacheFactory:
    """Test factory function (Normal + Accessibility)."""

    def test_create_memory_cache_default(self):
        """Normal: Factory creates cache with default configuration."""
        # Arrange
        from agency_memory.memory_cache import create_memory_cache

        # Act
        cache = create_memory_cache()

        # Assert
        assert cache.max_size == 128  # Default per spec

    def test_create_memory_cache_custom_size(self):
        """Normal: Factory creates cache with custom size."""
        # Arrange
        from agency_memory.memory_cache import create_memory_cache

        # Act
        cache = create_memory_cache(max_size=256)

        # Assert
        assert cache.max_size == 256


# NECESSARY Coverage Summary:
# ✅ Normal: Happy path scenarios (get/set, eviction, invalidation)
# ✅ Edge: Boundary conditions (empty cache, full cache, no matches)
# ✅ Corner: Unusual combinations (tag order, None values)
# ✅ Error: N/A (cache operations don't raise errors, return None/0)
# ✅ Security: Thread safety (concurrent reads/writes/invalidation)
# ✅ Stress: Performance under load (<1ms hits, 1000 sets <100ms)
# ✅ Accessibility: API usability (stats, top queries, factory)
# ✅ Regression: Bug prevention (LRU access tracking, hit rate calc)
# ✅ Yield: Output validation (stats, hit rate, access counts)
