"""
Budget Guard Integration Example for primeA Orchestrator

Demonstrates how to integrate budget guard with task graph execution.

Usage:
    python tools/orchestrator/budget_guard_example.py
"""

from tools.orchestrator.budget_guard import BudgetGuard, BudgetLimits


def example_basic_usage() -> None:
    """Basic usage: check budget before executing task graph."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Budget Check")
    print("=" * 60)

    guard = BudgetGuard()
    limits = BudgetLimits(daily_usd=100.0, per_mission_usd=10.0)

    # Estimate cost for 5 tasks, 10K tokens each
    estimate = guard.estimate_cost(total_tokens=50000, tasks_count=5, cost_per_1k=0.0025)

    print(f"Estimated cost: ${estimate.total_usd:.4f}")
    print(f"Daily limit: ${limits.daily_usd:.2f}")
    print(f"Per-mission limit: ${limits.per_mission_usd:.2f}")

    result = guard.check_budget(estimate, limits, force=False)

    if result.is_ok():
        print("✅ Budget check PASSED - proceed with execution")
    else:
        error = result.unwrap_err()
        print(f"❌ Budget check FAILED: {error}")


def example_budget_exceeded() -> None:
    """Example: budget exceeded, requires --force override."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Budget Exceeded (Requires --force)")
    print("=" * 60)

    guard = BudgetGuard()
    limits = BudgetLimits(daily_usd=10.0, per_mission_usd=1.0)

    # Expensive task: 1M tokens = $2.50 > $1.00 per-mission limit
    expensive_estimate = guard.estimate_cost(
        total_tokens=1_000_000, tasks_count=10, cost_per_1k=0.0025
    )

    print(f"Estimated cost: ${expensive_estimate.total_usd:.4f}")
    print(f"Per-mission limit: ${limits.per_mission_usd:.2f}")

    # First attempt: blocked
    result = guard.check_budget(expensive_estimate, limits, force=False)

    if result.is_err():
        error = result.unwrap_err()
        print(f"\n❌ BLOCKED: {error.message}")
        print(f"   Estimated: ${error.estimated_cost_usd:.4f}")
        print(f"   Limit: ${error.per_mission_limit_usd:.2f}")

        # Second attempt: override with --force
        print("\nRetrying with --force flag...")
        override_result = guard.check_budget(expensive_estimate, limits, force=True)

        if override_result.is_ok():
            print("✅ Budget OVERRIDDEN - execution allowed")
            print(f"   (Logged to audit trail: {guard.audit_log_path})")


def example_daily_tracking() -> None:
    """Example: tracking daily spend across multiple missions."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Daily Spend Tracking")
    print("=" * 60)

    guard = BudgetGuard()
    limits = BudgetLimits(daily_usd=10.0, per_mission_usd=5.0)

    # Execute 3 missions
    missions = [
        (20000, 3, "Mission 1: Small tasks"),
        (100000, 5, "Mission 2: Medium tasks"),
        (50000, 4, "Mission 3: Regular tasks"),
    ]

    for tokens, tasks, description in missions:
        estimate = guard.estimate_cost(total_tokens=tokens, tasks_count=tasks)
        daily_spend = guard.get_daily_spend()

        print(f"\n{description}")
        print(f"  Tokens: {tokens:,} | Tasks: {tasks}")
        print(f"  Cost: ${estimate.total_usd:.4f}")
        print(f"  Daily spend so far: ${daily_spend:.4f}/${limits.daily_usd:.2f}")

        result = guard.check_budget(estimate, limits, force=False)

        if result.is_ok():
            print(f"  ✅ Executed (new total: ${daily_spend + estimate.total_usd:.4f})")
        else:
            error = result.unwrap_err()
            print(f"  ❌ Blocked: {error.message}")


def example_primeA_integration() -> None:
    """Example: How to integrate with primeA orchestrator."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: primeA Integration Pattern")
    print("=" * 60)

    code = '''
# In tools/orchestrator/api.py or primeA command:

from tools.orchestrator.budget_guard import BudgetGuard, BudgetLimits

def execute_task_graph(graph: TaskGraph, force: bool = False):
    """Execute task graph with budget governance."""

    # 1. Initialize budget guard
    guard = BudgetGuard()
    limits = BudgetLimits(
        daily_usd=float(os.getenv("DAILY_BUDGET_USD", "100.0")),
        per_mission_usd=float(os.getenv("PER_MISSION_BUDGET_USD", "10.0"))
    )

    # 2. Estimate total cost from graph
    total_tokens = sum(task.estimated_tokens for task in graph.nodes.values())
    estimate = guard.estimate_cost(
        total_tokens=total_tokens,
        tasks_count=len(graph.nodes),
        cost_per_1k=0.0025  # Or get from model pricing
    )

    # 3. Check budget before execution
    result = guard.check_budget(estimate, limits, force=force)

    if result.is_err():
        error = result.unwrap_err()
        raise RuntimeError(
            f"Budget exceeded: {error.message}\\n"
            f"Use --force to override (will be logged to audit trail)"
        )

    # 4. Execute graph (budget approved)
    return await run_graph(ctx, graph, policy)
'''

    print(code)
    print("\nEnvironment variables:")
    print("  export DAILY_BUDGET_USD=100.0")
    print("  export PER_MISSION_BUDGET_USD=10.0")
    print("\nCommand usage:")
    print("  primeA graph.json                    # Enforces budget")
    print("  primeA graph.json --force            # Overrides budget (logged)")


if __name__ == "__main__":
    example_basic_usage()
    example_budget_exceeded()
    example_daily_tracking()
    example_primeA_integration()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
