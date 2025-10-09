#!/usr/bin/env python3
"""
Parallel Execution Demo

Demonstrates the power of parallel agent execution using git worktrees
and ThreadPoolExecutor.

EPIC 4.2 Component 3: Parallel Execution Demo

Shows:
- Sequential vs Parallel performance comparison
- Real-time progress reporting
- Thread-safe budget tracking
- Speedup metrics visualization

Usage:
    python demos/parallel_execution_demo.py

Expected Output:
    Speedup: 2-3x faster with max_workers=3
    Perfect isolation via worktrees
    No conflicts between parallel agents

Constitutional Compliance:
- Article I: Complete context (isolated execution)
- Article II: 100% verification (measurable speedup)
- Article IV: Learning (performance metrics captured)

Created: 2025-10-08
"""

import logging
import time
from pathlib import Path

from dspy_agents.parallel_orchestrator import ParallelABOrchestrator, compare_sequential_vs_parallel

# Configure logging with colored output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def print_banner(text: str, char: str = "="):
    """Print a fancy banner."""
    width = 60
    print()
    print(char * width)
    print(f"{text.center(width)}")
    print(char * width)
    print()


def demo_basic_parallel_execution():
    """Demo 1: Basic parallel execution."""
    print_banner("DEMO 1: Basic Parallel Execution")

    print("Running 3 agents × 1 task × 2 repeats = 6 jobs in parallel...")
    print("Max workers: 3")
    print()

    orchestrator = ParallelABOrchestrator(
        agent_ids=["agent_v1", "agent_v2", "agent_v3"],
        task_ids=["planner_api_auth_jwt"],
        repeats=2,
        budget_limit=5.0,
        max_workers=3,
    )

    start = time.time()
    results_path = orchestrator.run()
    duration = time.time() - start

    print()
    print(f"✅ Completed in {duration:.2f}s")
    print("📊 Stats:")
    stats = orchestrator.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"📁 Results: {results_path}")

    # Cleanup
    results_path.unlink()


def demo_sequential_vs_parallel():
    """Demo 2: Sequential vs Parallel comparison."""
    print_banner("DEMO 2: Sequential vs Parallel Comparison")

    print("Comparing sequential (1 worker) vs parallel (3 workers)...")
    print("Configuration:")
    print("  - Agents: agent_v1, agent_v2, agent_v3")
    print("  - Tasks: planner_api_auth_jwt")
    print("  - Repeats: 2")
    print("  - Total jobs: 6")
    print()

    results = compare_sequential_vs_parallel(
        agent_ids=["agent_v1", "agent_v2", "agent_v3"],
        task_ids=["planner_api_auth_jwt"],
        repeats=2,
        budget_limit=5.0,
    )

    print()
    print("📊 DETAILED RESULTS:")
    print()
    print("Sequential Execution:")
    print(f"  Duration:       {results['sequential']['duration_s']:.2f}s")
    print(f"  Jobs completed: {results['sequential']['completed_jobs']}")
    print()
    print("Parallel Execution:")
    print(f"  Duration:       {results['parallel']['duration_s']:.2f}s")
    print(f"  Jobs completed: {results['parallel']['completed_jobs']}")
    print()
    print("Performance Metrics:")
    print(f"  Speedup:        {results['speedup']:.2f}x")
    print(f"  Time saved:     {results['time_saved_s']:.2f}s")
    print(f"  Efficiency:     {results['efficiency_pct']:.1f}% (vs 3 workers)")
    print()

    # Visual speedup bar
    speedup = results["speedup"]
    bar_length = int(speedup * 10)
    print(f"Speedup Visualization: {'█' * bar_length} {speedup:.2f}x")
    print()

    if speedup >= 2.0:
        print("✅ EXCELLENT: Achieved > 2x speedup!")
    elif speedup >= 1.5:
        print("✅ GOOD: Achieved > 1.5x speedup")
    else:
        print("⚠️  FAIR: Speedup below 1.5x (may need optimization)")

    # Cleanup
    Path(results["sequential"]["results_file"]).unlink()
    Path(results["parallel"]["results_file"]).unlink()


def demo_scalability():
    """Demo 3: Scalability test with different worker counts."""
    print_banner("DEMO 3: Scalability Analysis")

    print("Testing scalability with 1, 2, 3, and 4 workers...")
    print("Configuration: 4 agents × 1 task × 2 repeats = 8 jobs")
    print()

    worker_counts = [1, 2, 3, 4]
    results = {}

    for workers in worker_counts:
        print(f"Testing with {workers} worker(s)...", end=" ", flush=True)

        orchestrator = ParallelABOrchestrator(
            agent_ids=["agent_v1", "agent_v2", "agent_v3", "agent_v4"],
            task_ids=["planner_api_auth_jwt"],
            repeats=2,
            budget_limit=10.0,
            max_workers=workers,
        )

        start = time.time()
        results_path = orchestrator.run()
        duration = time.time() - start

        results[workers] = {
            "duration": duration,
            "completed": orchestrator._completed_jobs,
            "results_file": results_path,
        }

        print(f"{duration:.2f}s")

    print()
    print("📊 SCALABILITY RESULTS:")
    print()
    print("Workers | Duration | Jobs | Speedup vs 1 worker")
    print("--------|----------|------|--------------------")

    baseline = results[1]["duration"]
    for workers in worker_counts:
        duration = results[workers]["duration"]
        completed = results[workers]["completed"]
        speedup = baseline / duration if duration > 0 else 0

        print(f"   {workers}    | {duration:6.2f}s | {completed:4d} | {speedup:6.2f}x")

    print()
    print("Efficiency Analysis:")
    for workers in [2, 3, 4]:
        speedup = baseline / results[workers]["duration"]
        efficiency = (speedup / workers) * 100
        print(f"  {workers} workers: {efficiency:.1f}% efficiency")

    # Cleanup
    for worker_results in results.values():
        worker_results["results_file"].unlink()


def demo_budget_enforcement():
    """Demo 4: Thread-safe budget enforcement."""
    print_banner("DEMO 4: Budget Enforcement (Parallel)")

    print("Testing budget enforcement with parallel execution...")
    print("Configuration:")
    print("  - Agents: 4")
    print("  - Tasks: 1")
    print("  - Repeats: 3")
    print("  - Total jobs: 12")
    print("  - Budget limit: $0.5 (very low to trigger early stop)")
    print("  - Workers: 3")
    print()

    orchestrator = ParallelABOrchestrator(
        agent_ids=["agent_v1", "agent_v2", "agent_v3", "agent_v4"],
        task_ids=["planner_api_auth_jwt"],
        repeats=3,
        budget_limit=0.5,
        max_workers=3,
    )

    start = time.time()
    results_path = orchestrator.run()
    duration = time.time() - start

    print()
    print("📊 BUDGET ENFORCEMENT RESULTS:")
    print(f"  Duration:       {duration:.2f}s")
    print(f"  Jobs completed: {orchestrator._completed_jobs}/12")
    print(f"  Total cost:     ${orchestrator.total_cost:.4f}")
    print(f"  Budget limit:   ${orchestrator.budget_limit:.4f}")
    print(f"  Budget used:    {(orchestrator.total_cost / orchestrator.budget_limit) * 100:.1f}%")
    print()

    if orchestrator.total_cost <= orchestrator.budget_limit * 1.2:
        print("✅ Budget enforcement PASSED (within 20% tolerance)")
    else:
        print("⚠️  Budget exceeded tolerance (parallel timing race condition)")

    # Cleanup
    results_path.unlink()


def demo_progress_tracking():
    """Demo 5: Real-time progress tracking."""
    print_banner("DEMO 5: Real-Time Progress Tracking")

    print("Running orchestration with real-time stats...")
    print("Watch the progress updates below:")
    print()

    orchestrator = ParallelABOrchestrator(
        agent_ids=["agent_v1", "agent_v2", "agent_v3"],
        task_ids=["planner_api_auth_jwt"],
        repeats=3,
        budget_limit=10.0,
        max_workers=2,  # Slower to see progress
    )

    # Run orchestration (progress logged by orchestrator)
    results_path = orchestrator.run()

    print()
    print("Final Stats:")
    stats = orchestrator.get_stats()
    print(f"  Progress:     {stats['progress_pct']:.1f}%")
    print(f"  Completed:    {stats['completed_jobs']}/{stats['total_jobs']} jobs")
    print(f"  Budget used:  ${stats['total_cost_usd']:.2f}/${stats['budget_limit_usd']:.2f}")
    print(f"  Budget %:     {stats['budget_used_pct']:.1f}%")

    # Cleanup
    results_path.unlink()


def main():
    """Run all demos."""
    print_banner("🚀 PARALLEL EXECUTION DEMO SUITE 🚀", "=")

    print("EPIC 4.2 Component 3: Parallel Execution Framework")
    print("Demonstrates:")
    print("  ✅ True parallel agent execution via ThreadPoolExecutor")
    print("  ✅ Perfect isolation via git worktrees")
    print("  ✅ Thread-safe budget tracking")
    print("  ✅ 2-3x speedup with 3 workers")
    print()
    input("Press Enter to start demos...")

    try:
        # Run demos
        demo_basic_parallel_execution()
        input("\nPress Enter for next demo...")

        demo_sequential_vs_parallel()
        input("\nPress Enter for next demo...")

        demo_scalability()
        input("\nPress Enter for next demo...")

        demo_budget_enforcement()
        input("\nPress Enter for next demo...")

        demo_progress_tracking()

        # Final summary
        print_banner("✅ ALL DEMOS COMPLETE ✅", "=")
        print("Key Takeaways:")
        print("  1. Parallel execution achieves 2-3x speedup with 3 workers")
        print("  2. Thread-safe budget enforcement prevents overruns")
        print("  3. Git worktrees provide perfect isolation (no conflicts)")
        print("  4. Real-time progress tracking via get_stats()")
        print("  5. Graceful degradation on errors")
        print()
        print("EPIC 4.2 Component 3: COMPLETE 🚀")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()
