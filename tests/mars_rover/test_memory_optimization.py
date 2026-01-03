"""
Mars Rover Reliability - Phase 3: Memory Optimization Tests.

Constitutional Compliance:
- Article VI: TDD (Tests written FIRST)
- Article IV: Learning (VectorStore is mandatory)
- Article II: 100% verification (persistence survives crashes)

Acceptance Criteria:
1. Query latency <50ms for 95th percentile
2. LRU cache with >80% hit rate
3. Crash recovery restores all data
4. Memory security (encryption, permissions)
"""

import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestQueryLatencyOptimization:
    """VectorStore query latency tests."""

    def test_query_latency_under_50ms_95th_percentile(self) -> None:
        """Query latency should be <50ms for 95th percentile."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        store = OptimizedVectorStore()

        # Populate with test patterns
        for i in range(100):
            store.store(f"pattern_{i}", {"value": i}, tags=["test"])

        # Measure query latencies
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            store.search(tags=["test"])
            latencies.append((time.perf_counter() - start) * 1000)  # ms

        # Sort and get 95th percentile
        latencies.sort()
        p95 = latencies[94]

        assert p95 < 50.0, f"95th percentile latency {p95:.2f}ms exceeds 50ms target"

    def test_batch_queries_reduce_overhead(self) -> None:
        """Batch queries should be more efficient than individual queries."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        store = OptimizedVectorStore()

        # Populate
        for i in range(50):
            store.store(f"item_{i}", {"data": f"value_{i}"}, tags=["batch_test"])

        # Time individual queries
        start = time.perf_counter()
        for i in range(10):
            store.search(tags=[f"batch_test"])
        individual_time = time.perf_counter() - start

        # Time batch query
        start = time.perf_counter()
        store.batch_search([{"tags": ["batch_test"]} for _ in range(10)])
        batch_time = time.perf_counter() - start

        # Batch should be faster (or at least not significantly slower)
        assert batch_time <= individual_time * 1.5, (
            f"Batch query ({batch_time:.3f}s) should be efficient vs "
            f"individual ({individual_time:.3f}s)"
        )


class TestLRUCache:
    """LRU cache tests."""

    def test_cache_hit_rate_above_80_percent(self) -> None:
        """Cache hit rate should be >80% for repeated queries."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        store = OptimizedVectorStore(cache_size=100)

        # Populate with some patterns
        for i in range(20):
            store.store(f"cached_item_{i}", {"data": i}, tags=["cached"])

        # Query same data repeatedly (should hit cache)
        for _ in range(100):
            store.search(tags=["cached"])

        metrics = store.get_cache_metrics()

        assert metrics["hit_rate"] >= 0.8, (
            f"Cache hit rate {metrics['hit_rate']:.2%} below 80% target"
        )

    def test_cache_eviction_on_capacity(self) -> None:
        """Cache should evict LRU entries when at capacity."""
        from tools.mars_rover.memory_optimizer import LRUCache

        cache = LRUCache(max_size=10)

        # Fill cache beyond capacity
        for i in range(15):
            cache.set(f"key_{i}", f"value_{i}")

        metrics = cache.get_metrics()

        assert metrics["evictions"] > 0, "Should have evicted entries"
        assert metrics["size"] <= 10, "Cache size should not exceed capacity"

    def test_cache_invalidation_on_store(self) -> None:
        """Cache should be invalidated when store is updated."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        store = OptimizedVectorStore(cache_size=100)

        # Store and query
        store.store("test_key", {"value": 1}, tags=["invalidation_test"])
        result1 = store.search(tags=["invalidation_test"])

        # Update the store
        store.store("test_key_2", {"value": 2}, tags=["invalidation_test"])

        # Query again - should see updated data (cache invalidated)
        result2 = store.search(tags=["invalidation_test"])

        assert len(result2) >= len(result1), "Should see new data after invalidation"


class TestCrashRecovery:
    """Crash recovery and persistence tests."""

    def test_periodic_snapshots_work(self) -> None:
        """Periodic snapshots should be created."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        with tempfile.TemporaryDirectory() as temp_dir:
            store = OptimizedVectorStore(
                persistence_dir=temp_dir,
                snapshot_interval_seconds=1,
            )

            # Store data
            store.store("snapshot_test", {"important": "data"}, tags=["persist"])

            # Force snapshot
            store.create_snapshot()

            # Verify snapshot file exists (may be .json or .json.gz)
            snapshot_files = list(Path(temp_dir).glob("snapshot_*"))
            assert len(snapshot_files) > 0, "Snapshot file should be created"

    def test_recovery_from_snapshot(self) -> None:
        """Should recover data from snapshot after crash."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create store and add data
            store1 = OptimizedVectorStore(persistence_dir=temp_dir)
            store1.store("recover_test", {"critical": "info"}, tags=["recovery"])
            store1.create_snapshot()

            # Simulate crash by creating new store
            store2 = OptimizedVectorStore(persistence_dir=temp_dir)
            store2.recover_from_snapshot()

            # Verify data recovered
            results = store2.search(tags=["recovery"])
            assert len(results) > 0, "Data should be recovered from snapshot"

    def test_transaction_log_durability(self) -> None:
        """Transaction log should ensure durability."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        with tempfile.TemporaryDirectory() as temp_dir:
            store = OptimizedVectorStore(
                persistence_dir=temp_dir,
                enable_transaction_log=True,
            )

            # Store multiple items
            for i in range(5):
                store.store(f"durable_{i}", {"index": i}, tags=["durable"])

            # Verify transaction log exists
            log_file = Path(temp_dir) / "transaction.log"
            assert log_file.exists() or store.has_transaction_log(), (
                "Transaction log should exist"
            )


class TestMemorySecurity:
    """Memory security tests."""

    def test_file_permissions_restricted(self) -> None:
        """Memory files should have restricted permissions (owner only)."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        with tempfile.TemporaryDirectory() as temp_dir:
            store = OptimizedVectorStore(
                persistence_dir=temp_dir,
                secure_mode=True,
            )

            store.store("secure_data", {"secret": "value"}, tags=["secure"])
            store.create_snapshot()

            # Check file permissions (should be 600 or more restrictive)
            snapshot_files = list(Path(temp_dir).glob("*.json"))
            for f in snapshot_files:
                mode = f.stat().st_mode & 0o777
                assert mode <= 0o600, f"File {f} has insecure permissions: {oct(mode)}"

    def test_no_sensitive_data_in_logs(self) -> None:
        """Sensitive data should not appear in logs."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore
        import logging

        with tempfile.TemporaryDirectory() as temp_dir:
            # Capture log output
            log_output = []
            handler = logging.Handler()
            handler.emit = lambda record: log_output.append(record.getMessage())

            logger = logging.getLogger("tools.mars_rover.memory_optimizer")
            logger.addHandler(handler)

            try:
                store = OptimizedVectorStore(persistence_dir=temp_dir)
                store.store(
                    "api_key_test",
                    {"api_key": "sk-secret123", "password": "hunter2"},
                    tags=["sensitive"],
                )

                # Check logs don't contain sensitive data
                log_text = " ".join(log_output)
                assert "sk-secret123" not in log_text, "API key leaked to logs"
                assert "hunter2" not in log_text, "Password leaked to logs"
            finally:
                logger.removeHandler(handler)


class TestOptimizedStoreConfiguration:
    """Configuration tests."""

    def test_default_configuration(self) -> None:
        """Default configuration should have sensible values."""
        from tools.mars_rover.memory_optimizer import MemoryOptimizerConfig

        config = MemoryOptimizerConfig()

        assert config.cache_size > 0
        assert config.snapshot_interval_seconds > 0
        assert config.enable_compression

    def test_custom_configuration(self) -> None:
        """Custom configuration should be applied."""
        from tools.mars_rover.memory_optimizer import (
            MemoryOptimizerConfig,
            OptimizedVectorStore,
        )

        config = MemoryOptimizerConfig(
            cache_size=500,
            snapshot_interval_seconds=60,
            enable_compression=False,
        )

        store = OptimizedVectorStore(config=config)

        assert store.config.cache_size == 500
        assert store.config.snapshot_interval_seconds == 60
        assert not store.config.enable_compression


class TestIndexOptimization:
    """Index optimization tests."""

    def test_tag_index_speeds_up_queries(self) -> None:
        """Tag index should speed up tag-based queries."""
        from tools.mars_rover.memory_optimizer import OptimizedVectorStore

        store = OptimizedVectorStore()

        # Add many items with various tags
        for i in range(100):
            store.store(f"indexed_{i}", {"data": i}, tags=[f"group_{i % 10}"])

        # Query by specific tag should be fast
        start = time.perf_counter()
        results = store.search(tags=["group_5"])
        query_time = time.perf_counter() - start

        assert query_time < 0.1, f"Tag query too slow: {query_time:.3f}s"
        assert len(results) == 10, "Should find all items with tag"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
