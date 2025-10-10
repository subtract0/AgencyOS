"""
LRU caching layer for frequently accessed memories.

Implements thread-safe LRU cache with:
- Configurable size (default 128 entries per spec)
- Cache warming on startup from top 100 accessed patterns
- Eviction metrics logging (hit/miss ratio)
- Tag-aware invalidation for write operations

Constitutional Compliance:
- Article I: Complete context before action (cache never returns partial results)
- Article II: 100% verification (cache consistency guaranteed)
- Article IV: Continuous learning (cache metrics feed into optimization)

Performance Targets (spec):
- 80%+ cache hit rate
- <100MB memory footprint
- <1ms cache hit latency
- Thread-safe for concurrent agent access
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from shared.models.memory import CacheStats
from shared.type_definitions.json import JSONValue

if TYPE_CHECKING:
    from shared.models.memory import MemoryRecord

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry with result and metadata.

    Attributes:
        results: Cached list of MemoryRecord objects
        timestamp: Unix timestamp when cached
        access_count: Number of times this entry was accessed
        tags: Tags associated with this query (for invalidation)
    """

    results: list["MemoryRecord"]
    timestamp: float
    access_count: int = 0
    tags: set[str] | None = None


class MemoryCache:
    """
    Thread-safe LRU cache for memory search results.

    Features:
    - LRU eviction when cache is full
    - Tag-aware invalidation (invalidate queries affected by tag changes)
    - Thread-safe operations using RLock
    - Performance metrics tracking

    Design:
    - Cache key: hash(query_tags + query_text + search_params)
    - Eviction: Least Recently Used (LRU)
    - Invalidation: Tag-based (when new memory stored with overlapping tags)
    - Concurrency: threading.RLock for thread safety
    """

    def __init__(self, max_size: int = 128):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of cached entries (default 128 per spec)
        """
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)

        logger.info(f"MemoryCache initialized with max_size={max_size}")

    def _generate_cache_key(
        self, query_tags: list[str] | None = None, query_text: str | None = None, **params: JSONValue
    ) -> str:
        """
        Generate deterministic cache key from query parameters.

        Uses SHA256 hash of stable representation to ensure:
        - Same queries always generate same key
        - Different queries generate different keys
        - Keys are fixed-length (64 chars)

        Args:
            query_tags: Tags to filter by
            query_text: Semantic search query text
            **params: Additional search parameters (top_k, min_similarity, etc.)

        Returns:
            64-character hex string (SHA256 hash)
        """
        # Sort tags for stability
        tags_str = str(sorted(query_tags or []))
        text_str = query_text or ""
        params_str = str(sorted(params.items()))

        key_str = f"{tags_str}|{text_str}|{params_str}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, query_key: str) -> list["MemoryRecord"] | None:
        """
        Get cached results if present.

        Thread-safe operation. Updates access_count and timestamp for LRU tracking.

        Args:
            query_key: Cache key from _generate_cache_key()

        Returns:
            Cached list of MemoryRecord objects, or None if not in cache
        """
        with self._lock:
            if query_key not in self._cache:
                self._stats.misses += 1
                return None

            # Cache hit - update access tracking
            entry = self._cache[query_key]
            entry.access_count += 1
            entry.timestamp = time.time()  # Update for LRU

            self._stats.hits += 1
            self._stats.size = len(self._cache)

            logger.debug(
                f"Cache HIT: key={query_key[:16]}... "
                f"(hit_rate={self._stats.hit_rate:.1f}%, access_count={entry.access_count})"
            )

            return entry.results

    def set(
        self, query_key: str, results: list["MemoryRecord"], tags: list[str] | None = None
    ) -> None:
        """
        Cache search results.

        Implements LRU eviction: if cache is full, removes least recently used entry
        before adding new one.

        Thread-safe operation.

        Args:
            query_key: Cache key from _generate_cache_key()
            results: List of MemoryRecord objects to cache
            tags: Optional tags for this query (used for invalidation)
        """
        with self._lock:
            # LRU eviction if cache full
            if len(self._cache) >= self.max_size:
                # Find entry with oldest timestamp (least recently used)
                oldest_key = min(self._cache, key=lambda k: self._cache[k].timestamp)
                del self._cache[oldest_key]
                self._stats.evictions += 1
                logger.debug(f"Cache EVICTION: key={oldest_key[:16]}... (LRU policy)")

            # Add new entry
            self._cache[query_key] = CacheEntry(
                results=results, timestamp=time.time(), tags=set(tags or [])
            )

            self._stats.size = len(self._cache)

            logger.debug(
                f"Cache SET: key={query_key[:16]}... "
                f"(size={len(self._cache)}/{self.max_size}, results={len(results)})"
            )

    def invalidate_pattern(self, tag: str) -> int:
        """
        Invalidate all cache entries affected by a tag.

        Use case: New memory stored with tag "pattern" -> invalidate all queries
        that search for "pattern" to ensure fresh results.

        Thread-safe operation.

        Args:
            tag: Tag that was added/modified

        Returns:
            Number of cache entries invalidated
        """
        with self._lock:
            keys_to_delete = []

            for key, entry in self._cache.items():
                # Invalidate if query included this tag
                if entry.tags and tag in entry.tags:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]

            if keys_to_delete:
                logger.debug(
                    f"Cache INVALIDATION: tag={tag} affected {len(keys_to_delete)} entries"
                )

            self._stats.size = len(self._cache)
            return len(keys_to_delete)

    def invalidate_all(self) -> None:
        """
        Clear entire cache.

        Use case: Write operation that affects many memories (batch insert, etc.)
        Safer to clear all than try to selectively invalidate.

        Thread-safe operation.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.size = 0

            if count > 0:
                logger.debug(f"Cache CLEAR: invalidated {count} entries")

    def get_stats(self) -> CacheStats:
        """
        Get cache performance statistics.

        Thread-safe operation.

        Returns:
            CacheStats object with hit/miss/eviction counts and rates
        """
        with self._lock:
            # Return copy to avoid external mutation
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=self._stats.size,
                max_size=self._stats.max_size,
            )

    def get_top_queries(self, limit: int = 10) -> list[tuple[str, int]]:
        """
        Get most frequently accessed queries.

        Used for cache warming strategy - identify hot queries to pre-populate.

        Thread-safe operation.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of (query_key, access_count) tuples, sorted by access_count descending
        """
        with self._lock:
            sorted_entries = sorted(
                [(k, v.access_count) for k, v in self._cache.items()],
                key=lambda x: x[1],
                reverse=True,
            )
            return sorted_entries[:limit]

    def warm_cache(
        self,
        frequent_queries: list[tuple[str, list["MemoryRecord"], list[str] | None]],
    ) -> int:
        """
        Pre-populate cache with frequent queries.

        Strategy: Load top N queries from metrics/telemetry and cache them
        to improve initial hit rate after startup.

        Thread-safe operation.

        Args:
            frequent_queries: List of (query_key, results, tags) tuples to warm

        Returns:
            Number of entries warmed
        """
        warmed_count = 0

        with self._lock:
            for query_key, results, tags in frequent_queries:
                if len(self._cache) >= self.max_size:
                    break  # Cache full, stop warming

                self._cache[query_key] = CacheEntry(
                    results=results, timestamp=time.time(), tags=set(tags or [])
                )
                warmed_count += 1

            self._stats.size = len(self._cache)

        logger.info(f"Cache warming: loaded {warmed_count} frequent queries")
        return warmed_count


def create_memory_cache(max_size: int = 128) -> MemoryCache:
    """
    Factory function to create a MemoryCache instance.

    Args:
        max_size: Maximum cache size (default 128 per spec)

    Returns:
        Configured MemoryCache instance
    """
    return MemoryCache(max_size=max_size)
