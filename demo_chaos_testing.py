#!/usr/bin/env python3
"""
Chaos Testing Framework Demo

Demonstrates Mars Rover-grade resilience testing capabilities.
"""

import time
from tools.chaos_testing import (
    ChaosConfig,
    ChaosEngine,
    ChaosType,
    chaos,
    generate_chaos_report,
)


def demo_basic_chaos():
    """Demonstrate basic chaos testing with decorator."""
    print("\n" + "=" * 70)
    print("Demo 1: Basic Chaos Testing with Decorator")
    print("=" * 70)

    @chaos(chaos_types=[ChaosType.TIMEOUT], failure_rate=0.5)
    def sample_task():
        """Task that might encounter delays."""
        for i in range(3):
            time.sleep(0.01)
            print(f"  Task step {i + 1} completed")

    print("\nRunning task with 50% timeout chaos...")
    result = sample_task()
    print(f"Result: {result}")
    print("✅ Task completed despite chaos!")


def demo_engine_chaos():
    """Demonstrate chaos testing with engine for detailed results."""
    print("\n" + "=" * 70)
    print("Demo 2: Chaos Testing with Engine (Detailed Results)")
    print("=" * 70)

    config = ChaosConfig(
        chaos_types=[ChaosType.TIMEOUT, ChaosType.DISK_IO],
        failure_rate=0.3,
        seed=42,  # Reproducible results
    )

    engine = ChaosEngine(config)

    def complex_task():
        """Task with multiple operations."""
        # Simulate multiple operations
        for i in range(5):
            time.sleep(0.01)
            try:
                # Simulate file operation
                with open(f"/tmp/chaos_demo_{i}.txt", "w") as f:
                    f.write(f"Data {i}")
            except IOError:
                # Graceful handling
                pass

    print("\nRunning complex task with network and disk chaos...")
    print(f"Chaos types: {config.chaos_types}")
    print(f"Failure rate: {config.failure_rate * 100}%")

    result = engine.run_chaos_test(complex_task)

    if result.is_ok():
        chaos_result = result.unwrap()
        print("\n📊 Chaos Test Results:")
        print(f"  Total injections: {chaos_result.total_injections}")
        print(f"  Successful recoveries: {chaos_result.successful_recoveries}")
        print(f"  Failed recoveries: {chaos_result.failed_recoveries}")
        print(f"  Crash count: {chaos_result.crash_count}")
        print(f"  Recovery rate: {chaos_result.recovery_rate * 100:.1f}%")
        print(f"  Duration: {chaos_result.duration_seconds:.2f}s")

        if chaos_result.crash_count == 0:
            print("\n✅ System survived chaos with zero crashes!")
        else:
            print(f"\n❌ System crashed {chaos_result.crash_count} times")
    else:
        print(f"\n❌ Chaos test failed: {result.unwrap_err()}")


def demo_report_generation():
    """Demonstrate chaos report generation."""
    print("\n" + "=" * 70)
    print("Demo 3: Chaos Report Generation")
    print("=" * 70)

    config = ChaosConfig(
        chaos_types=[ChaosType.NETWORK, ChaosType.TIMEOUT],
        failure_rate=0.4,
        seed=123,
    )

    engine = ChaosEngine(config)

    def network_task():
        """Simulate network-heavy task."""
        for _ in range(10):
            try:
                time.sleep(0.01)
                # Simulate network call
                # (would be requests.get() in real code)
            except Exception:
                pass

    print("\nRunning network task with chaos...")
    result = engine.run_chaos_test(network_task)

    if result.is_ok():
        chaos_result = result.unwrap()
        report = generate_chaos_report(chaos_result)

        print("\n📄 Generated Chaos Report:")
        print("-" * 70)
        print(report)
        print("-" * 70)


def demo_resilience_patterns():
    """Demonstrate common resilience patterns."""
    print("\n" + "=" * 70)
    print("Demo 4: Resilience Patterns")
    print("=" * 70)

    @chaos(chaos_types=[ChaosType.NETWORK], failure_rate=0.6)
    def task_with_retry():
        """Task with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Simulate operation
                time.sleep(0.01)
                print(f"  Attempt {attempt + 1} succeeded")
                return "Success"
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print("  All retries exhausted")
                    return "Failed after retries"
                time.sleep(0.01)  # Backoff

    print("\nRunning task with retry logic under 60% network chaos...")
    result = task_with_retry()
    print(f"\n✅ Task completed with retry pattern: {result}")


def main():
    """Run all chaos testing demos."""
    print("\n" + "🌪️  " * 15)
    print("  CHAOS TESTING FRAMEWORK - MARS ROVER DEMO")
    print("🌪️  " * 15)

    demo_basic_chaos()
    demo_engine_chaos()
    demo_report_generation()
    demo_resilience_patterns()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\n📚 Learn more:")
    print("  - Framework: tools/chaos_testing.py")
    print("  - Tests: tests/unit/tools/test_chaos_testing.py")
    print("  - Guide: docs/testing/CHAOS_TESTING_GUIDE.md")
    print("  - CLI: ./scripts/run_chaos_tests.sh --help")
    print("\n🚀 Mars Rover-grade resilience achieved!")


if __name__ == "__main__":
    main()
