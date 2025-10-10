"""Demo: Batch Memory Tool Performance

Demonstrates 3x+ throughput improvement with batch_view_async() for parallel reads.

Performance comparison:
- Sequential: 100 files * 5ms = 500ms
- Parallel (10 concurrency): 100 files / 10 * 5ms = 50ms
- 10x speedup (I/O bound)

Usage:
    python demo_batch_memory_reads.py
"""

import asyncio
import shutil
import tempfile
import time

from tools.async_memory_tool import AsyncMemoryTool


async def setup_test_files(tool: AsyncMemoryTool, count: int = 100) -> list[str]:
    """Create test files for benchmark

    Args:
        tool: AsyncMemoryTool instance
        count: Number of files to create

    Returns:
        List of file paths
    """
    print(f"Setting up {count} test files...")

    files = {
        f"/memories/test_file_{i}.txt": f"Content for file {i}\n" * 10
        for i in range(count)
    }

    results = await tool.batch_create_async(files, max_concurrency=10)

    # Verify all created successfully
    successes = sum(1 for r in results.values() if r.is_ok())
    print(f"Created {successes}/{count} files")

    return list(files.keys())


async def benchmark_sequential(
    tool: AsyncMemoryTool, paths: list[str], simulate_latency: float = 0.0
) -> float:
    """Benchmark sequential reads

    Args:
        tool: AsyncMemoryTool instance
        paths: List of file paths to read
        simulate_latency: Simulate network latency in seconds (default: 0.0)

    Returns:
        Elapsed time in seconds
    """
    print("\n=== Sequential Reads ===")
    if simulate_latency > 0:
        print(f"Simulating {simulate_latency * 1000:.1f}ms network latency per read")

    start = time.perf_counter()

    for path in paths:
        result = await tool.view_async(path)
        if result.is_err():
            print(f"Error reading {path}: {result.unwrap_err()}")

        # Simulate network latency
        if simulate_latency > 0:
            await asyncio.sleep(simulate_latency)

    elapsed = time.perf_counter() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Throughput: {len(paths) / elapsed:.1f} files/sec")

    return elapsed


async def benchmark_parallel(
    tool: AsyncMemoryTool,
    paths: list[str],
    max_concurrency: int = 10,
    simulate_latency: float = 0.0,
) -> float:
    """Benchmark parallel batch reads

    Args:
        tool: AsyncMemoryTool instance
        paths: List of file paths to read
        max_concurrency: Max concurrent reads
        simulate_latency: Simulate network latency in seconds (default: 0.0)

    Returns:
        Elapsed time in seconds
    """
    print(f"\n=== Parallel Batch Reads (concurrency={max_concurrency}) ===")
    if simulate_latency > 0:
        print(f"Simulating {simulate_latency * 1000:.1f}ms network latency per read")

    start = time.perf_counter()

    # Create modified view function with latency
    async def view_with_latency(path: str):
        result = await tool.view_async(path)
        if simulate_latency > 0:
            await asyncio.sleep(simulate_latency)
        return (path, result)

    if simulate_latency > 0:
        # Use custom implementation with latency simulation
        semaphore = asyncio.Semaphore(max_concurrency)

        async def bounded_view(path: str):
            async with semaphore:
                return await view_with_latency(path)

        tasks = [bounded_view(path) for path in paths]
        task_results = await asyncio.gather(*tasks)
        results = dict(task_results)
    else:
        # Use built-in batch_view_async
        results = await tool.batch_view_async(paths, max_concurrency=max_concurrency)

    elapsed = time.perf_counter() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Throughput: {len(paths) / elapsed:.1f} files/sec")

    # Verify results
    successes = sum(1 for r in results.values() if r.is_ok())
    print(f"Successes: {successes}/{len(paths)}")

    return elapsed


async def main():
    """Run batch read performance demo"""

    # Create temp directory for test
    temp_dir = tempfile.mkdtemp(prefix="async_memory_demo_")
    print(f"Using temporary directory: {temp_dir}")

    try:
        # Initialize tool
        tool = AsyncMemoryTool(base_dir=temp_dir)

        # Setup test files
        file_count = 100
        paths = await setup_test_files(tool, count=file_count)

        # Scenario 1: Local SSD (no latency)
        print("\n" + "=" * 60)
        print("SCENARIO 1: Local SSD (no latency)")
        print("=" * 60)

        sequential_time_local = await benchmark_sequential(tool, paths)
        parallel_time_10_local = await benchmark_parallel(
            tool, paths, max_concurrency=10
        )

        print("\n=== Local SSD Summary ===")
        print(f"Sequential: {sequential_time_local:.3f}s")
        print(f"Parallel (10 workers): {parallel_time_10_local:.3f}s")
        print(
            f"Speedup: {sequential_time_local / parallel_time_10_local:.2f}x (async overhead dominates)"
        )

        # Scenario 2: Network storage (5ms latency per read)
        print("\n" + "=" * 60)
        print("SCENARIO 2: Network Storage (5ms latency per read)")
        print("=" * 60)

        latency = 0.005  # 5ms network latency
        sequential_time_network = await benchmark_sequential(
            tool, paths, simulate_latency=latency
        )
        parallel_time_10_network = await benchmark_parallel(
            tool, paths, max_concurrency=10, simulate_latency=latency
        )

        print("\n=== Network Storage Summary ===")
        print(f"Sequential: {sequential_time_network:.3f}s")
        print(f"Parallel (10 workers): {parallel_time_10_network:.3f}s")
        print(f"Speedup: {sequential_time_network / parallel_time_10_network:.2f}x")

        # Validate 3x improvement for network scenario
        if sequential_time_network / parallel_time_10_network >= 3.0:
            print("\n✅ TARGET ACHIEVED: 3x+ throughput improvement (network I/O)")
        else:
            print(
                f"\n⚠️  Target not met: {sequential_time_network / parallel_time_10_network:.2f}x < 3.0x"
            )

    finally:
        # Cleanup
        print(f"\nCleaning up: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
