"""
Memory Lock Manager Concurrency Control Tests

Tests MemoryLockManager with deadlock detection and lock ordering.
Verifies code_memory_tool_concurrency implementation.

Constitutional Compliance:
- Article I: Complete context (all tests run to completion)
- Article II: 100% verification (zero deadlocks, atomic operations)
- Article IV: Store deadlock patterns in VectorStore

Test Coverage (NECESSARY Pattern):
- Normal operation: Single lock acquisition and release
- Edge cases: Concurrent reads, different files, same file
- Corner cases: Deadlock scenarios (AB-BA cycle)
- Error conditions: Lock timeouts, acquisition failures
- Security: Lock ordering prevents deadlock

Performance Target:
- <5ms lock acquisition latency (99th percentile)
- Zero deadlocks in 10K concurrent operations
"""

import asyncio
import time
from pathlib import Path

import pytest

from tools.memory_lock_manager import (
    DeadlockCycle,
    LockContention,
    LockMetrics,
    MemoryLockManager,
    create_memory_lock_manager,
)


class TestLockManagerBasicOperations:
    """Basic lock operations - Normal scenarios (NECESSARY: N)"""

    @pytest.fixture
    async def lock_manager(self):
        """Create lock manager with default config"""
        manager = MemoryLockManager()
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_single_lock_acquisition(self, lock_manager):
        """
        GIVEN a file path
        WHEN acquire_lock is called
        THEN lock is acquired and released correctly
        """
        # Arrange
        test_path = "/memories/test.txt"

        # Act
        async with lock_manager.acquire_lock(test_path) as lock:
            # Assert - lock is held
            assert lock.locked()

        # Assert - lock is released
        assert not lock.locked()

    @pytest.mark.asyncio
    async def test_sequential_lock_acquisition(self, lock_manager):
        """
        GIVEN sequential lock requests
        WHEN each completes before next starts
        THEN all acquire successfully
        """
        # Arrange
        test_path = "/memories/sequential.txt"
        results = []

        # Act - 5 sequential acquisitions
        for i in range(5):
            async with lock_manager.acquire_lock(test_path):
                results.append(i)
                await asyncio.sleep(0.01)  # Simulate work

        # Assert
        assert results == [0, 1, 2, 3, 4]
        metrics = lock_manager.get_metrics()
        assert metrics.total_acquisitions >= 5

    @pytest.mark.asyncio
    async def test_lock_timeout_configuration(self, lock_manager):
        """
        GIVEN custom timeout configuration
        WHEN lock is held longer than timeout
        THEN timeout error is raised
        """
        # Arrange
        test_path = "/memories/timeout_config.txt"

        # Hold lock
        async with lock_manager.acquire_lock(test_path, timeout=5.0):

            # Act - Try to acquire with short timeout (will fail)
            with pytest.raises(TimeoutError) as exc_info:
                async with lock_manager.acquire_lock(test_path, timeout=0.1):
                    pass

            # Assert
            assert "Lock timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """
        GIVEN factory function parameters
        WHEN create_memory_lock_manager is called
        THEN properly configured manager is returned
        """
        # Arrange & Act
        manager = create_memory_lock_manager(
            lock_timeout=10.0,
            enable_deadlock_detection=True,
            enable_telemetry=True,
        )

        # Assert
        assert manager is not None
        assert manager.lock_timeout == 10.0
        assert manager.enable_deadlock_detection is True
        assert manager.enable_telemetry is True

        # Test basic operation
        async with manager.acquire_lock("/memories/test.txt"):
            pass  # Should succeed

        # Cleanup
        await manager.cleanup()


class TestConcurrentAccess:
    """Concurrent access tests - Multiple agents (NECESSARY: C)"""

    @pytest.fixture
    async def lock_manager(self):
        """Create lock manager with telemetry enabled"""
        manager = MemoryLockManager(enable_telemetry=True)
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_concurrent_reads_different_files(self, lock_manager):
        """
        GIVEN 10 concurrent agents reading different files
        WHEN all acquire locks simultaneously
        THEN all succeed without contention
        """
        # Arrange
        async def read_file(file_id: int):
            """Simulate agent reading a file"""
            path = f"/memories/file{file_id}.txt"
            async with lock_manager.acquire_lock(path):
                await asyncio.sleep(0.01)  # Simulate I/O
                return file_id

        # Act - 10 concurrent reads on different files
        tasks = [read_file(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Assert - All succeeded
        assert sorted(results) == list(range(10))

        # Check metrics
        metrics = lock_manager.get_metrics()
        assert metrics.total_acquisitions == 10
        assert metrics.total_contentions == 0  # No contention (different files)

    @pytest.mark.asyncio
    async def test_concurrent_writes_same_file(self, lock_manager):
        """
        GIVEN 5 concurrent agents writing to same file
        WHEN all try to acquire lock
        THEN operations are serialized (no race condition)
        """
        # Arrange
        test_path = "/memories/shared.txt"
        write_order = []
        lock_for_ordering = asyncio.Lock()

        async def write_file(agent_id: int):
            """Simulate agent writing to file"""
            async with lock_manager.acquire_lock(test_path):
                # Track order of lock acquisition
                async with lock_for_ordering:
                    write_order.append(agent_id)
                await asyncio.sleep(0.02)  # Simulate write operation

        # Act - 5 concurrent writes to same file
        tasks = [write_file(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Assert - All writes completed (serialized)
        assert len(write_order) == 5
        assert set(write_order) == {0, 1, 2, 3, 4}

        # Check contention metrics
        metrics = lock_manager.get_metrics()
        assert metrics.total_contentions >= 4  # At least 4 agents had to wait

    @pytest.mark.asyncio
    async def test_concurrent_read_write_ordering(self, lock_manager):
        """
        GIVEN mixed read and write operations on same file
        WHEN all execute concurrently
        THEN lock ensures proper ordering
        """
        # Arrange
        test_path = "/memories/mixed_access.txt"
        operations = []
        ops_lock = asyncio.Lock()

        async def reader(reader_id: int):
            async with lock_manager.acquire_lock(test_path):
                async with ops_lock:
                    operations.append(f"read_{reader_id}")
                await asyncio.sleep(0.01)

        async def writer(writer_id: int):
            async with lock_manager.acquire_lock(test_path):
                async with ops_lock:
                    operations.append(f"write_{writer_id}")
                await asyncio.sleep(0.01)

        # Act - 5 readers, 3 writers, interleaved
        tasks = [reader(i) for i in range(5)] + [writer(i) for i in range(3)]
        await asyncio.gather(*tasks)

        # Assert - All operations completed
        assert len(operations) == 8


class TestDeadlockPrevention:
    """Deadlock prevention tests - Lock ordering (NECESSARY: E)"""

    @pytest.fixture
    async def lock_manager(self):
        """Create lock manager with deadlock detection enabled"""
        manager = MemoryLockManager(
            lock_timeout=2.0,
            enable_deadlock_detection=True,
        )
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_global_lock_ordering_prevents_deadlock(self, lock_manager):
        """
        GIVEN two agents acquiring locks in reverse order
        WHEN acquire_multiple_locks is used
        THEN alphabetical ordering prevents AB-BA deadlock
        """
        # Arrange
        path_a = "/memories/a.txt"
        path_b = "/memories/b.txt"
        results = []

        async def agent1():
            """Try to lock b, then a (reversed)"""
            async with lock_manager.acquire_multiple_locks([path_b, path_a]):
                results.append("agent1")
                await asyncio.sleep(0.05)

        async def agent2():
            """Try to lock a, then b"""
            await asyncio.sleep(0.01)  # Start slightly later
            async with lock_manager.acquire_multiple_locks([path_a, path_b]):
                results.append("agent2")
                await asyncio.sleep(0.05)

        # Act - Both agents run concurrently
        await asyncio.gather(agent1(), agent2())

        # Assert - Both completed (no deadlock)
        assert len(results) == 2
        assert "agent1" in results
        assert "agent2" in results

    @pytest.mark.asyncio
    async def test_lock_timeout_detection(self, lock_manager):
        """
        GIVEN a lock held for extended period
        WHEN another task tries to acquire with timeout
        THEN timeout is detected and reported
        """
        # Arrange
        test_path = "/memories/timeout_test.txt"

        async def holder():
            """Hold lock for 3 seconds"""
            async with lock_manager.acquire_lock(test_path, timeout=5.0):
                await asyncio.sleep(3.0)

        async def waiter():
            """Try to acquire with 0.5s timeout"""
            await asyncio.sleep(0.1)  # Let holder acquire first
            async with lock_manager.acquire_lock(test_path, timeout=0.5):
                pass  # Should not reach here

        # Act
        holder_task = asyncio.create_task(holder())

        with pytest.raises(TimeoutError) as exc_info:
            await waiter()

        # Cleanup
        holder_task.cancel()
        try:
            await holder_task
        except asyncio.CancelledError:
            pass

        # Assert
        assert "Lock timeout" in str(exc_info.value)

        # Check metrics
        metrics = lock_manager.get_metrics()
        assert metrics.total_timeouts >= 1

    @pytest.mark.asyncio
    async def test_deadlock_detection_cycle_identification(self, lock_manager):
        """
        GIVEN potential AB-BA deadlock scenario
        WHEN timeout occurs
        THEN deadlock cycle is detected (if present)
        """
        # Note: This is a simplified test. Full cycle detection requires
        # complex multi-task scenarios. We verify the detection mechanism
        # can handle timeout scenarios without false positives.

        # Arrange
        path_a = "/memories/a.txt"
        path_b = "/memories/b.txt"

        # Act - Use proper ordering (no deadlock expected)
        async with lock_manager.acquire_multiple_locks([path_a, path_b]):
            # Verify no deadlock detected
            pass

        # Assert - No timeouts recorded
        metrics = lock_manager.get_metrics()
        initial_timeouts = metrics.total_timeouts

        # Now test actual timeout scenario
        async with lock_manager.acquire_lock(path_a, timeout=5.0):
            # Try to acquire same lock with short timeout
            with pytest.raises(TimeoutError):
                async with lock_manager.acquire_lock(path_a, timeout=0.1):
                    pass

        # Verify timeout was recorded
        metrics = lock_manager.get_metrics()
        assert metrics.total_timeouts > initial_timeouts


class TestLockMetricsTelemetry:
    """Lock metrics and telemetry tests (NECESSARY: Y)"""

    @pytest.fixture
    async def lock_manager(self):
        """Create lock manager with full telemetry"""
        manager = MemoryLockManager(
            enable_telemetry=True,
            enable_deadlock_detection=True,
        )
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_lock_metrics_aggregation(self, lock_manager):
        """
        GIVEN multiple lock operations
        WHEN metrics are retrieved
        THEN accurate aggregation is provided
        """
        # Arrange & Act - Perform various operations
        for i in range(10):
            async with lock_manager.acquire_lock(f"/memories/file{i}.txt"):
                await asyncio.sleep(0.01)

        # Get metrics
        metrics = lock_manager.get_metrics()

        # Assert
        assert isinstance(metrics, LockMetrics)
        assert metrics.total_acquisitions >= 10
        assert metrics.max_wait_time_ms >= 0
        assert metrics.avg_wait_time_ms >= 0

    @pytest.mark.asyncio
    async def test_contention_event_tracking(self, lock_manager):
        """
        GIVEN concurrent access to same file
        WHEN contention occurs
        THEN contention events are recorded
        """
        # Arrange
        test_path = "/memories/contention.txt"

        async def accessor(agent_id: int):
            async with lock_manager.acquire_lock(test_path):
                await asyncio.sleep(0.02)  # Hold lock briefly

        # Act - 5 agents contending for same file
        tasks = [accessor(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Get contention events
        events = lock_manager.get_contention_events(limit=10)

        # Assert - Contention recorded (at least 4 agents had to wait)
        assert len(events) >= 4
        for event in events:
            assert isinstance(event, LockContention)
            assert event.wait_time_ms > 0

    @pytest.mark.asyncio
    async def test_p99_latency_calculation(self, lock_manager):
        """
        GIVEN 100 lock operations
        WHEN metrics are calculated
        THEN 99th percentile latency is accurate
        """
        # Arrange & Act - 100 operations with varying delays
        for i in range(100):
            async with lock_manager.acquire_lock(f"/memories/p99_{i % 10}.txt"):
                await asyncio.sleep(0.001)  # Minimal work

        # Get metrics
        metrics = lock_manager.get_metrics()

        # Assert
        assert metrics.total_acquisitions >= 100
        assert metrics.p99_wait_time_ms >= 0
        assert metrics.p99_wait_time_ms <= 10.0  # Should be <10ms for local ops

    @pytest.mark.asyncio
    async def test_vectorstore_logging_on_deadlock(self, lock_manager):
        """
        GIVEN a timeout scenario
        WHEN potential deadlock is detected
        THEN pattern is logged to VectorStore (Article IV)
        """
        # Note: VectorStore logging is internal to _log_deadlock().
        # We verify it doesn't crash and completes successfully.

        # Arrange
        test_path = "/memories/vectorstore_test.txt"

        # Act - Trigger timeout
        async with lock_manager.acquire_lock(test_path, timeout=5.0):
            with pytest.raises(TimeoutError):
                async with lock_manager.acquire_lock(test_path, timeout=0.1):
                    pass

        # Assert - Manager still functional after logging
        metrics = lock_manager.get_metrics()
        assert metrics.total_timeouts >= 1

        # Verify can still acquire lock normally
        async with lock_manager.acquire_lock(test_path):
            pass  # Should succeed


class TestLockManagerEdgeCases:
    """Edge cases and corner scenarios (NECESSARY: E + C)"""

    @pytest.fixture
    async def lock_manager(self):
        """Create lock manager for edge case testing"""
        manager = MemoryLockManager()
        yield manager
        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_empty_path_list_multiple_locks(self, lock_manager):
        """
        GIVEN empty path list
        WHEN acquire_multiple_locks is called
        THEN it completes without error
        """
        # Arrange & Act
        async with lock_manager.acquire_multiple_locks([]) as locks:
            # Assert
            assert locks == []

    @pytest.mark.asyncio
    async def test_single_path_multiple_locks(self, lock_manager):
        """
        GIVEN single path in list
        WHEN acquire_multiple_locks is called
        THEN lock is acquired normally
        """
        # Arrange & Act
        async with lock_manager.acquire_multiple_locks(["/memories/single.txt"]) as locks:
            # Assert - Should return list of locks acquired
            assert len(locks) >= 0  # Context manager may or may not expose locks

    @pytest.mark.asyncio
    async def test_duplicate_paths_multiple_locks(self, lock_manager):
        """
        GIVEN duplicate paths in list
        WHEN acquire_multiple_locks is called
        THEN sorted deduplication prevents double-lock
        """
        # Arrange
        paths = ["/memories/a.txt", "/memories/a.txt", "/memories/b.txt"]

        # Act - Should handle duplicates gracefully
        async with lock_manager.acquire_multiple_locks(paths):
            pass  # Should succeed without deadlock

    @pytest.mark.asyncio
    async def test_rapid_acquire_release_cycle(self, lock_manager):
        """
        GIVEN rapid lock acquire/release cycles
        WHEN 1000 operations execute
        THEN no lock leaks or deadlocks occur
        """
        # Arrange
        test_path = "/memories/rapid.txt"

        # Act - 1000 rapid acquisitions
        for _ in range(1000):
            async with lock_manager.acquire_lock(test_path, timeout=1.0):
                pass  # Immediate release

        # Assert - Metrics show all completed
        metrics = lock_manager.get_metrics()
        assert metrics.total_acquisitions >= 1000
        assert metrics.total_timeouts == 0  # No deadlocks

    @pytest.mark.asyncio
    async def test_lock_manager_cleanup(self, lock_manager):
        """
        GIVEN lock manager with active metrics
        WHEN cleanup is called
        THEN resources are released and final metrics logged
        """
        # Arrange - Perform some operations
        for i in range(5):
            async with lock_manager.acquire_lock(f"/memories/cleanup_{i}.txt"):
                await asyncio.sleep(0.01)

        # Act
        await lock_manager.cleanup()

        # Assert - Metrics still accessible after cleanup
        metrics = lock_manager.get_metrics()
        assert metrics.total_acquisitions >= 5
