#!/usr/bin/env python3
"""
Performance benchmark for constitutional test fixtures.

Verifies initialization meets <200ms requirement for unit testing.
"""

import time
from statistics import mean, median, stdev


def benchmark_agent_creation(iterations: int = 10):
    """Benchmark create_constitutional_test_agent performance."""
    from tests.fixtures.constitutional_test_agents import create_constitutional_test_agent

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        agent = create_constitutional_test_agent(f"TestAgent{i}")
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms

    return {
        "mean": mean(times),
        "median": median(times),
        "min": min(times),
        "max": max(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "samples": len(times),
    }


def benchmark_context_creation(iterations: int = 10):
    """Benchmark create_test_agent_context performance."""
    from tests.fixtures.constitutional_test_agents import create_test_agent_context

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        context = create_test_agent_context(session_id=f"test_{i}")
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms

    return {
        "mean": mean(times),
        "median": median(times),
        "min": min(times),
        "max": max(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "samples": len(times),
    }


def benchmark_combined_creation(iterations: int = 10):
    """Benchmark combined agent + context creation."""
    from tests.fixtures.constitutional_test_agents import create_test_agent_with_context

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        agent, context = create_test_agent_with_context(f"TestAgent{i}")
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms

    return {
        "mean": mean(times),
        "median": median(times),
        "min": min(times),
        "max": max(times),
        "stdev": stdev(times) if len(times) > 1 else 0,
        "samples": len(times),
    }


def print_results(name: str, stats: dict, threshold_ms: float):
    """Print benchmark results with pass/fail status."""
    print(f"\n{name}:")
    print(f"  Mean:   {stats['mean']:6.2f}ms")
    print(f"  Median: {stats['median']:6.2f}ms")
    print(f"  Min:    {stats['min']:6.2f}ms")
    print(f"  Max:    {stats['max']:6.2f}ms")
    print(f"  StdDev: {stats['stdev']:6.2f}ms")
    print(f"  Samples: {stats['samples']}")

    status = "✅ PASS" if stats['mean'] < threshold_ms else "❌ FAIL"
    print(f"  Status: {status} (threshold: {threshold_ms}ms)")


def main():
    """Run all benchmarks and report results."""
    print("=" * 70)
    print("Constitutional Test Fixtures - Performance Benchmark")
    print("=" * 70)
    print("\nRequirement: <200ms for combined initialization")
    print("Constitutional compliance: Article I (Complete Context + Performance)\n")

    # Warmup
    print("Warming up...")
    from tests.fixtures.constitutional_test_agents import (
        create_constitutional_test_agent,
        create_test_agent_context,
    )

    _ = create_constitutional_test_agent("WarmupAgent")
    _ = create_test_agent_context()
    print("Warmup complete.\n")

    # Run benchmarks
    iterations = 10
    print(f"Running benchmarks ({iterations} iterations each)...")

    agent_stats = benchmark_agent_creation(iterations)
    context_stats = benchmark_context_creation(iterations)
    combined_stats = benchmark_combined_creation(iterations)

    # Print results
    print_results("Agent Creation", agent_stats, threshold_ms=100.0)
    print_results("Context Creation", context_stats, threshold_ms=50.0)
    print_results("Combined Creation", combined_stats, threshold_ms=200.0)

    # Overall assessment
    print("\n" + "=" * 70)
    all_pass = (
        agent_stats["mean"] < 100.0
        and context_stats["mean"] < 50.0
        and combined_stats["mean"] < 200.0
    )

    if all_pass:
        print("✅ ALL BENCHMARKS PASS - Constitutional compliance verified")
        print("   Fixtures are fast enough for unit testing")
    else:
        print("❌ SOME BENCHMARKS FAIL - Performance optimization needed")
        print("   Fixtures may be too slow for high-volume unit testing")

    print("=" * 70)

    # Memory operations benchmark
    print("\n\nMemory Operations Benchmark:")
    from tests.fixtures.constitutional_test_agents import create_test_agent_context

    context = create_test_agent_context()
    iterations = 100

    # Store benchmark
    start = time.perf_counter()
    for i in range(iterations):
        context.store_memory(f"key_{i}", f"value_{i}", tags=["test"])
    store_elapsed = (time.perf_counter() - start) * 1000 / iterations

    # Search benchmark
    start = time.perf_counter()
    for i in range(iterations):
        results = context.search_memories(["test"], include_session=True)
    search_elapsed = (time.perf_counter() - start) * 1000 / iterations

    print(f"  Store:  {store_elapsed:.3f}ms per operation")
    print(f"  Search: {search_elapsed:.3f}ms per operation")

    mem_pass = store_elapsed < 1.0 and search_elapsed < 1.0
    mem_status = "✅ PASS" if mem_pass else "❌ FAIL"
    print(f"  Status: {mem_status} (threshold: <1ms per operation)")

    return 0 if all_pass and mem_pass else 1


if __name__ == "__main__":
    exit(main())
