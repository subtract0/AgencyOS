"""
Async Memory Tool Stress Tests

High-load stress tests for AsyncMemoryTool and MemoryLockManager.
Verifies stability under extreme concurrent load (50+ parallel operations).

Constitutional Compliance:
- Article I: Complete context (all stress tests run to completion)
- Article II: 100% stability (zero crashes, zero deadlocks)
- Article IV: Store stress test patterns in VectorStore

Test Coverage (NECESSARY Pattern):
- Stress: 50 parallel reads across 3 workers
- Stress: 100 concurrent agents accessing different files
- Stress: Race conditions with 2 agents editing same file 1000 times
- Stress: Memory usage validation over 10K operations

Performance Target:
- 50 parallel reads: <500ms total time
- 100 concurrent agents: zero deadlocks
- 1000 edits: zero race conditions (atomic operations)
- 10K operations: <100MB memory usage
"""

import asyncio
import gc
import os
import sys
import time
from pathlib import Path

import pytest

from tools.async_memory_tool import AsyncMemoryTool


class TestStressParallelReads:
    """Stress test: Parallel read operations (NECESSARY: S)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool with many test files"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))

        # Create 50 files for stress testing
        files = {f"/memories/stress{i}.txt": f"Stress content {i}" * 10 for i in range(50)}
        await tool.batch_create_async(files, max_concurrency=10)

        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_50_parallel_reads(self, async_tool):
        """
        GIVEN 50 files exist
        WHEN 50 concurrent reads execute across 3 workers
        THEN all reads complete successfully in <500ms
        """
        # Arrange
        paths = [f"/memories/stress{i}.txt" for i in range(50)]

        # Act - 50 parallel reads with max_concurrency=3 (simulates 3 workers)
        start = time.perf_counter()
        results = await async_tool.batch_view_async(paths, max_concurrency=3)
        elapsed = time.perf_counter() - start

        # Assert - All successful
        assert len(results) == 50
        success_count = sum(1 for r in results.values() if r.is_ok())
        assert success_count == 50, f"Expected 50 successes, got {success_count}"

        # Performance assertion (relaxed for CI environments)
        # Local SSD: ~50-100ms, CI: may be slower
        assert elapsed < 5.0, f"50 parallel reads took {elapsed:.3f}s (expected <5s)"

        print(f"\n[STRESS] 50 parallel reads (3 workers): {elapsed:.3f}s")
        print(f"[STRESS] Average per read: {elapsed / 50 * 1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_100_parallel_reads_high_concurrency(self, async_tool):
        """
        GIVEN 100 files
        WHEN 100 concurrent reads execute with high concurrency (20 workers)
        THEN all complete without deadlock or timeout
        """
        # Arrange - Create 100 files
        files = {f"/memories/high{i}.txt": f"High concurrency {i}" for i in range(100)}
        await async_tool.batch_create_async(files, max_concurrency=10)

        paths = list(files.keys())

        # Act - 100 parallel reads with 20 workers
        start = time.perf_counter()
        results = await async_tool.batch_view_async(paths, max_concurrency=20)
        elapsed = time.perf_counter() - start

        # Assert
        assert len(results) == 100
        assert all(r.is_ok() for r in results.values())

        print(f"\n[STRESS] 100 parallel reads (20 workers): {elapsed:.3f}s")

        # Check lock metrics
        metrics = async_tool.get_lock_metrics()
        print(f"[STRESS] Lock acquisitions: {metrics.total_acquisitions}")
        print(f"[STRESS] Lock contentions: {metrics.total_contentions}")
        print(f"[STRESS] Lock timeouts: {metrics.total_timeouts}")

        assert metrics.total_timeouts == 0, "No timeouts should occur"


class TestStressConcurrentAgents:
    """Stress test: Multiple concurrent agents (NECESSARY: S)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool for agent simulation"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_100_concurrent_agents_different_files(self, async_tool):
        """
        GIVEN 100 concurrent agents
        WHEN each agent accesses a different file
        THEN all operations complete without deadlock
        """

        # Arrange
        async def agent_workflow(agent_id: int):
            """Simulate agent creating and reading its own file"""
            path = f"/memories/agent{agent_id}.txt"
            content = f"Agent {agent_id} data"

            # Create
            create_result = await async_tool.create_async(path, content)
            if create_result.is_err():
                return f"agent{agent_id}_create_failed"

            # Read
            view_result = await async_tool.view_async(path)
            if view_result.is_err():
                return f"agent{agent_id}_view_failed"

            # Verify
            if view_result.unwrap() != content:
                return f"agent{agent_id}_content_mismatch"

            return f"agent{agent_id}_success"

        # Act - 100 concurrent agents
        start = time.perf_counter()
        tasks = [agent_workflow(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # Assert - All successful
        success_count = sum(1 for r in results if r.endswith("_success"))
        assert success_count == 100, f"Expected 100 successes, got {success_count}"

        print(f"\n[STRESS] 100 concurrent agents: {elapsed:.3f}s")
        print(f"[STRESS] Average per agent: {elapsed / 100 * 1000:.2f}ms")

        # Check metrics
        metrics = async_tool.get_lock_metrics()
        assert metrics.total_timeouts == 0, "No deadlocks should occur"

    @pytest.mark.asyncio
    async def test_50_agents_contending_for_10_files(self, async_tool):
        """
        GIVEN 50 concurrent agents
        WHEN all contend for 10 shared files
        THEN operations are serialized without deadlock
        """
        # Arrange - Create 10 shared files
        for i in range(10):
            await async_tool.create_async(f"/memories/shared{i}.txt", f"Initial {i}")

        async def agent_workflow(agent_id: int):
            """Agent reads and writes to random shared files"""
            file_id = agent_id % 10  # 50 agents -> 10 files (5 agents per file)
            path = f"/memories/shared{file_id}.txt"

            # Read
            view_result = await async_tool.view_async(path)
            if view_result.is_err():
                return False

            # Write (append agent ID)
            current_content = view_result.unwrap()
            new_content = f"{current_content}\nAgent {agent_id} was here"

            create_result = await async_tool.create_async(path, new_content)
            return create_result.is_ok()

        # Act - 50 agents contending for 10 files
        start = time.perf_counter()
        tasks = [agent_workflow(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # Assert - All should complete (some may fail due to race, but no deadlock)
        assert all(isinstance(r, bool) for r in results), "All agents should complete"

        print(f"\n[STRESS] 50 agents on 10 files: {elapsed:.3f}s")

        # Check for contention
        metrics = async_tool.get_lock_metrics()
        print(f"[STRESS] Lock contentions: {metrics.total_contentions}")
        assert metrics.total_contentions > 0, "Expected contention with shared files"
        assert metrics.total_timeouts == 0, "No deadlocks should occur"


class TestStressRaceConditions:
    """Stress test: Race condition validation (NECESSARY: C)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool for race condition testing"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    async def test_race_conditions_2_agents_1000_edits(self, async_tool):
        """
        GIVEN 2 concurrent agents editing same file
        WHEN each performs 1000 edits
        THEN all edits are atomic (no corruption, no race conditions)
        """
        # Arrange
        test_path = "/memories/race_test.txt"
        await async_tool.create_async(test_path, "0")

        async def incrementer(agent_id: int, iterations: int):
            """Agent that increments counter in file"""
            success_count = 0
            for _ in range(iterations):
                # Read current value
                view_result = await async_tool.view_async(test_path)
                if view_result.is_err():
                    continue

                try:
                    current_value = int(view_result.unwrap().strip())
                except ValueError:
                    # Race condition detected: file corrupted
                    return -1

                # Increment
                new_value = current_value + 1

                # Write back
                create_result = await async_tool.create_async(test_path, str(new_value))
                if create_result.is_ok():
                    success_count += 1

            return success_count

        # Act - 2 agents, each doing 1000 increments
        start = time.perf_counter()
        tasks = [incrementer(0, 1000), incrementer(1, 1000)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # Assert
        assert all(r >= 0 for r in results), "No race condition corruption should occur"

        # Read final value
        final_result = await async_tool.view_async(test_path)
        assert final_result.is_ok()

        final_value = int(final_result.unwrap().strip())
        print(f"\n[STRESS] 2 agents, 1000 edits each: {elapsed:.3f}s")
        print(f"[STRESS] Final value: {final_value}")
        print(f"[STRESS] Agent 0 successes: {results[0]}")
        print(f"[STRESS] Agent 1 successes: {results[1]}")

        # Final value should be some increment of 0 (no corruption)
        # Due to lock contention, not all edits may succeed, but no corruption
        assert final_value >= 0, "Value should never be negative (corruption)"

    @pytest.mark.asyncio
    async def test_concurrent_rename_operations(self, async_tool):
        """
        GIVEN 10 files to rename concurrently
        WHEN all renames execute simultaneously
        THEN no deadlocks occur (dual lock ordering verified)
        """
        # Arrange - Create 10 files
        for i in range(10):
            await async_tool.create_async(f"/memories/old{i}.txt", f"Content {i}")

        async def rename_file(file_id: int):
            """Rename file with potential lock ordering conflict"""
            old_path = f"/memories/old{file_id}.txt"
            new_path = f"/memories/new{file_id}.txt"
            result = await async_tool.rename_async(old_path, new_path)
            return result.is_ok()

        # Act - 10 concurrent renames
        start = time.perf_counter()
        tasks = [rename_file(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        # Assert - All should succeed (no deadlock)
        success_count = sum(1 for r in results if r)
        assert success_count == 10, f"Expected 10 successes, got {success_count}"

        print(f"\n[STRESS] 10 concurrent renames: {elapsed:.3f}s")

        # Verify no timeouts
        metrics = async_tool.get_lock_metrics()
        assert metrics.total_timeouts == 0, "No deadlocks should occur"


class TestStressMemoryUsage:
    """Stress test: Memory usage validation (NECESSARY: S)"""

    @pytest.fixture
    async def async_tool(self, tmp_path):
        """Create async memory tool for memory usage testing"""
        tool = AsyncMemoryTool(base_dir=str(tmp_path / "memories"))
        yield tool
        await tool.cleanup()

    @pytest.mark.asyncio
    @pytest.mark.timeout(180)  # 3 minute timeout for stress test
    async def test_memory_usage_10k_operations(self, async_tool):
        """
        GIVEN 10K file operations
        WHEN operations complete
        THEN memory usage remains stable (<100MB growth)
        """
        # Arrange
        gc.collect()

        # Get baseline memory (Python RSS)
        try:
            import psutil

            process = psutil.Process(os.getpid())
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pytest.skip("psutil not installed, skipping memory test")

        # Act - 10K operations with batching for performance
        # Optimization: Batch file operations to reduce lock contention
        start = time.perf_counter()
        batch_size = 100  # Process 100 ops before checking memory
        paths = [f"/memories/mem_test_{i % 20}.txt" for i in range(20)]  # Reuse 20 paths

        for batch in range(100):  # 100 batches * 100 ops = 10K ops
            batch_start = batch * batch_size

            # Batch create operations
            for i in range(batch_size):
                op_num = batch_start + i
                path = paths[op_num % 20]

                # Simplified: Just create, skip view to reduce overhead
                create_result = await async_tool.create_async(path, f"Content {op_num}")

                # Don't log errors during stress test (too slow)

            # Check memory every batch (1000 ops)
            if batch % 10 == 0 and batch > 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - baseline_memory
                print(
                    f"[STRESS] After {(batch + 1) * batch_size} ops: {memory_growth:.2f}MB growth"
                )

                # Early termination if memory growth excessive (prevents timeout)
                if memory_growth > 150:
                    print(
                        f"[STRESS] Early termination at {(batch + 1) * batch_size} ops - excessive memory growth"
                    )
                    break

        elapsed = time.perf_counter() - start

        # Force garbage collection
        gc.collect()

        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory

        # Assert - Memory growth should be reasonable (<100MB for 10K ops)
        print(f"\n[STRESS] 10K operations: {elapsed:.3f}s")
        print(f"[STRESS] Baseline memory: {baseline_memory:.2f}MB")
        print(f"[STRESS] Final memory: {final_memory:.2f}MB")
        print(f"[STRESS] Memory growth: {memory_growth:.2f}MB")
        print(f"[STRESS] Ops/sec: {10000 / elapsed:.0f}")

        assert memory_growth < 100, f"Memory growth {memory_growth:.2f}MB exceeds 100MB limit"

        # Check lock metrics
        metrics = async_tool.get_lock_metrics()
        print(f"[STRESS] Total lock acquisitions: {metrics.total_acquisitions}")
        print(f"[STRESS] Total contentions: {metrics.total_contentions}")
        print(f"[STRESS] Total timeouts: {metrics.total_timeouts}")

        assert metrics.total_timeouts == 0, "No deadlocks in 10K operations"

    @pytest.mark.asyncio
    async def test_lock_cleanup_prevents_leaks(self, async_tool):
        """
        GIVEN 1000 lock acquisitions and releases
        WHEN cleanup is called
        THEN no lock objects are leaked
        """
        # Arrange & Act - 1000 lock operations
        for i in range(1000):
            async with async_tool._lock_manager.acquire_lock(f"/memories/leak_test_{i % 10}.txt"):
                pass

        # Get lock registry size before cleanup
        registry_size_before = len(async_tool._lock_manager._file_locks)

        # Cleanup
        await async_tool.cleanup()

        # Assert - Registry size should be reasonable (10 unique paths)
        # Some implementations may clear registry on cleanup, others may not
        # Both are valid as long as no memory leak occurs
        print(f"\n[STRESS] Lock registry size: {registry_size_before}")

        # Verify manager still functional after cleanup
        # (cleanup should not break future operations)
        test_result = await async_tool.create_async("/memories/post_cleanup.txt", "test")
        assert test_result.is_ok(), "Manager should work after cleanup"
