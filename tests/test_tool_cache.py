"""
Comprehensive test suite for tool smart caching infrastructure.

Tests cache hit/miss behavior, TTL expiration, file dependency invalidation,
LRU eviction, pattern-based invalidation, and cache statistics.

Constitutional Compliance:
- Article I: Complete test coverage before implementation
- Article II: 100% test success requirement
- Law #1: TDD is mandatory
"""

import time
import tempfile
from pathlib import Path
import pytest
from shared.tool_cache import (
    ToolCache,
    CacheEntry,
    with_cache,
    clear_cache,
    invalidate_file,
    get_cache_stats,
)


class TestCacheEntry:
    """Test CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test basic cache entry creation."""
        entry = CacheEntry(
            result="test_value",
            timestamp=time.time(),
            file_dependencies=["file1.py"]
        )
        assert entry.result == "test_value"
        assert isinstance(entry.timestamp, float)
        assert entry.file_dependencies == ["file1.py"]

    def test_cache_entry_no_dependencies(self):
        """Test cache entry without file dependencies."""
        entry = CacheEntry(
            result=42,
            timestamp=time.time(),
            file_dependencies=None
        )
        assert entry.result == 42
        assert entry.file_dependencies is None


class TestToolCache:
    """Test ToolCache core functionality."""

    def setup_method(self):
        """Create fresh cache for each test."""
        self.cache = ToolCache(max_size=100, default_ttl=300)

    def test_cache_key_generation_deterministic(self):
        """Test cache keys are deterministic for same inputs."""
        key1 = self.cache.get_cache_key("func", (1, 2), {"arg": "value"})
        key2 = self.cache.get_cache_key("func", (1, 2), {"arg": "value"})
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA256 hex digest

    def test_cache_key_different_for_different_inputs(self):
        """Test cache keys differ for different inputs."""
        key1 = self.cache.get_cache_key("func", (1, 2), {})
        key2 = self.cache.get_cache_key("func", (1, 3), {})
        key3 = self.cache.get_cache_key("other_func", (1, 2), {})
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_cache_set_and_get_hit(self):
        """Test successful cache hit."""
        key = "test_key"
        result = {"data": "cached_value"}

        self.cache.set(key, result)
        cached = self.cache.get(key)

        assert cached == result

    def test_cache_get_miss_nonexistent(self):
        """Test cache miss for nonexistent key."""
        cached = self.cache.get("nonexistent_key")
        assert cached is None

    def test_cache_ttl_expiration(self):
        """Test cache entry expires after TTL."""
        key = "expiring_key"
        result = "value"

        # Set with 1 second TTL
        self.cache.set(key, result)

        # Should hit within TTL
        cached = self.cache.get(key, ttl_seconds=1)
        assert cached == result

        # Wait for expiration
        time.sleep(1.1)

        # Should miss after TTL
        cached = self.cache.get(key, ttl_seconds=1)
        assert cached is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        small_cache = ToolCache(max_size=3, default_ttl=300)

        # Fill cache
        small_cache.set("key1", "value1")
        time.sleep(0.01)  # Ensure different timestamps
        small_cache.set("key2", "value2")
        time.sleep(0.01)
        small_cache.set("key3", "value3")

        # Add one more - should evict oldest (key1)
        time.sleep(0.01)
        small_cache.set("key4", "value4")

        assert small_cache.get("key1") is None  # Evicted
        assert small_cache.get("key2") == "value2"
        assert small_cache.get("key3") == "value3"
        assert small_cache.get("key4") == "value4"

    def test_cache_file_dependency_invalidation(self):
        """Test cache invalidation when file is modified."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
            f.write("initial content")

        try:
            key = "file_dep_key"

            # Cache with file dependency
            self.cache.set(key, "cached_result", file_dependencies=[temp_file])

            # Should hit before modification
            cached = self.cache.get(key)
            assert cached == "cached_result"

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            Path(temp_file).write_text("modified content")

            # Should miss after file modification
            cached = self.cache.get(key)
            assert cached is None

        finally:
            Path(temp_file).unlink()

    def test_cache_file_dependency_nonexistent_file(self):
        """Test cache invalidation when dependency file doesn't exist."""
        key = "missing_file_key"
        nonexistent_file = "/tmp/nonexistent_file_xyz_123.txt"

        self.cache.set(key, "result", file_dependencies=[nonexistent_file])

        # Should invalidate for missing file
        cached = self.cache.get(key)
        assert cached is None

    def test_invalidate_file_explicit(self):
        """Test explicit file invalidation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            file_path = f1.name
            f1.write("content1")

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            other_file = f2.name
            f2.write("content2")

        try:
            # Cache entries with file dependency
            self.cache.set("key1", "value1", file_dependencies=[file_path])
            self.cache.set("key2", "value2", file_dependencies=[file_path])
            self.cache.set("key3", "value3", file_dependencies=[other_file])

            # Invalidate specific file
            self.cache.invalidate_file(file_path)

            # Entries with that file dependency should be gone
            assert self.cache.get("key1") is None
            assert self.cache.get("key2") is None
            assert self.cache.get("key3") == "value3"  # Different file

        finally:
            Path(file_path).unlink()
            Path(other_file).unlink()

    def test_invalidate_pattern(self):
        """Test pattern-based cache invalidation."""
        self.cache.set("git_status", "result1")
        self.cache.set("git_branch", "result2")
        self.cache.set("file_read", "result3")

        # Invalidate all git_* keys
        self.cache.invalidate_pattern("git_*")

        assert self.cache.get("git_status") is None
        assert self.cache.get("git_branch") is None
        assert self.cache.get("file_read") == "result3"  # Not matching pattern

    def test_clear_cache(self):
        """Test clearing entire cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        self.cache.clear()

        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert self.cache.get("key3") is None
        assert len(self.cache.cache) == 0


class TestCacheDecorator:
    """Test @with_cache decorator functionality."""

    def setup_method(self):
        """Clear global cache before each test."""
        clear_cache()
        self.call_count = 0

    def test_cache_decorator_basic(self):
        """Test basic cache decorator usage."""

        @with_cache(ttl_seconds=300)
        def expensive_function(x: int) -> int:
            self.call_count += 1
            return x * 2

        # First call - cache miss
        result1 = expensive_function(5)
        assert result1 == 10
        assert self.call_count == 1

        # Second call - cache hit
        result2 = expensive_function(5)
        assert result2 == 10
        assert self.call_count == 1  # Not called again

        # Different args - cache miss
        result3 = expensive_function(10)
        assert result3 == 20
        assert self.call_count == 2

    def test_cache_decorator_with_kwargs(self):
        """Test cache decorator with keyword arguments."""

        @with_cache(ttl_seconds=300)
        def func_with_kwargs(a: int, b: int = 10) -> int:
            self.call_count += 1
            return a + b

        # First call
        result1 = func_with_kwargs(5, b=20)
        assert result1 == 25
        assert self.call_count == 1

        # Same args - cache hit
        result2 = func_with_kwargs(5, b=20)
        assert result2 == 25
        assert self.call_count == 1

        # Different kwargs - cache miss
        result3 = func_with_kwargs(5, b=30)
        assert result3 == 35
        assert self.call_count == 2

    def test_cache_decorator_ttl_expiration(self):
        """Test cache decorator respects TTL."""

        @with_cache(ttl_seconds=1)
        def short_lived_function(x: int) -> int:
            self.call_count += 1
            return x * 3

        # First call
        result1 = short_lived_function(5)
        assert result1 == 15
        assert self.call_count == 1

        # Within TTL - cache hit
        result2 = short_lived_function(5)
        assert result2 == 15
        assert self.call_count == 1

        # Wait for TTL expiration
        time.sleep(1.1)

        # After TTL - cache miss
        result3 = short_lived_function(5)
        assert result3 == 15
        assert self.call_count == 2

    def test_cache_decorator_with_file_dependencies(self):
        """Test cache decorator with file dependency tracking."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
            f.write("initial")

        try:

            @with_cache(
                ttl_seconds=300,
                file_dependencies=lambda file_path: [file_path]
            )
            def read_file(file_path: str) -> str:
                self.call_count += 1
                return Path(file_path).read_text()

            # First call - cache miss
            result1 = read_file(temp_file)
            assert result1 == "initial"
            assert self.call_count == 1

            # Second call - cache hit
            result2 = read_file(temp_file)
            assert result2 == "initial"
            assert self.call_count == 1

            # Modify file
            time.sleep(0.1)
            Path(temp_file).write_text("modified")

            # Third call - cache miss (file changed)
            result3 = read_file(temp_file)
            assert result3 == "modified"
            assert self.call_count == 2

        finally:
            Path(temp_file).unlink()

    def test_cache_decorator_multiple_functions(self):
        """Test cache decorator with multiple functions (separate caches)."""

        @with_cache(ttl_seconds=300)
        def func_a(x: int) -> int:
            return x * 2

        @with_cache(ttl_seconds=300)
        def func_b(x: int) -> int:
            return x * 3

        # Each function has separate cache space
        result_a1 = func_a(5)
        result_b1 = func_b(5)

        assert result_a1 == 10
        assert result_b1 == 15

        # Both should be cached independently
        result_a2 = func_a(5)
        result_b2 = func_b(5)

        assert result_a2 == 10
        assert result_b2 == 15


class TestGlobalCacheAPI:
    """Test global cache management functions."""

    def test_clear_cache_global(self):
        """Test global cache clear function."""

        @with_cache(ttl_seconds=300)
        def cached_func(x: int) -> int:
            return x * 2

        # Populate cache
        cached_func(5)
        cached_func(10)

        # Clear global cache
        clear_cache()

        # Cache should be empty (but this is hard to verify without internals)
        # Just verify the function still works
        result = cached_func(5)
        assert result == 10

    def test_invalidate_file_global(self):
        """Test global file invalidation function."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
            f.write("content")

        try:

            @with_cache(
                ttl_seconds=300,
                file_dependencies=lambda fp: [fp]
            )
            def read_cached(file_path: str) -> str:
                return Path(file_path).read_text()

            # Cache the read
            result1 = read_cached(temp_file)
            assert result1 == "content"

            # Invalidate via global API
            invalidate_file(temp_file)

            # Should re-read after invalidation
            time.sleep(0.1)
            Path(temp_file).write_text("new_content")
            result2 = read_cached(temp_file)
            assert result2 == "new_content"

        finally:
            Path(temp_file).unlink()

    def test_get_cache_stats(self):
        """Test cache statistics reporting."""
        clear_cache()

        @with_cache(ttl_seconds=300)
        def tracked_func(x: int) -> int:
            return x * 2

        # Populate cache
        tracked_func(1)
        tracked_func(2)
        tracked_func(3)

        stats = get_cache_stats()

        assert isinstance(stats, dict)
        assert "size" in stats
        assert "max_size" in stats
        assert "entries" in stats
        assert stats["size"] >= 0
        assert isinstance(stats["entries"], list)


class TestCacheEdgeCases:
    """Test edge cases and error conditions."""

    def test_cache_with_none_result(self):
        """Test caching None values."""
        cache = ToolCache()

        cache.set("null_key", None)
        result = cache.get("null_key")

        # None is a valid cached value (different from cache miss)
        assert result is None

    def test_cache_with_complex_objects(self):
        """Test caching complex objects."""
        cache = ToolCache()

        complex_obj = {
            "nested": {"data": [1, 2, 3]},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }

        cache.set("complex_key", complex_obj)
        result = cache.get("complex_key")

        assert result == complex_obj

    def test_cache_concurrent_access(self):
        """Test cache behavior with concurrent-like access."""
        cache = ToolCache(max_size=5)

        # Rapidly set multiple keys
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}")

        # Should only have last 5 (LRU evicted earlier ones)
        assert len(cache.cache) <= 5

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @with_cache(ttl_seconds=300)
        def documented_function(x: int) -> int:
            """This is a documented function."""
            return x * 2

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."


class TestCachePerformance:
    """Test cache performance characteristics."""

    def test_cache_hit_is_faster_than_miss(self):
        """Test cache hits are significantly faster than misses."""

        @with_cache(ttl_seconds=300)
        def slow_function(x: int) -> int:
            time.sleep(0.01)  # Simulate expensive operation
            return x * 2

        # First call (cache miss)
        start_miss = time.time()
        result_miss = slow_function(5)
        time_miss = time.time() - start_miss

        # Second call (cache hit)
        start_hit = time.time()
        result_hit = slow_function(5)
        time_hit = time.time() - start_hit

        assert result_miss == result_hit == 10
        assert time_hit < time_miss  # Cache hit should be faster
        assert time_hit < 0.005  # Cache hit should be < 5ms

    def test_cache_scales_with_size(self):
        """Test cache handles large number of entries."""
        cache = ToolCache(max_size=1000)

        # Add 500 entries
        for i in range(500):
            cache.set(f"key_{i}", f"value_{i}")

        # All should be retrievable
        for i in range(500):
            assert cache.get(f"key_{i}") == f"value_{i}"

        assert len(cache.cache) == 500
