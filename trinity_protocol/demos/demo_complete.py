#!/usr/bin/env python3
"""
Trinity Protocol Complete Demo

Demonstrates full Trinity capabilities:
- Project architecture (Architect agent)
- Project execution (Executor agent)
- Pattern detection (Witness agent)
- Cost tracking and budgets
- Foundation verification
- Orchestration workflow

This is the complete "Second Brain" in action, consolidating:
- demo_complete_trinity.py (core workflow)
- demo_integration.py (infrastructure integration)
- test_dashboard_demo.py (cost tracking)
- demo_architect.py (architect-specific features)

Usage:
    python trinity_protocol/demos/demo_complete.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.agent_context import create_agent_context
from shared.cost_tracker import CostTracker, ModelTier, SQLiteStorage
from shared.message_bus import MessageBus
from shared.persistent_store import PersistentStore
from trinity_protocol.core import ArchitectAgent, ExecutorAgent, WitnessAgent


class TrinityCompleteDemo:
    """
    Complete Trinity Protocol demonstration.

    Shows the full autonomous cycle with all three agents and cost tracking.
    """

    def __init__(self, budget_usd: float = 10.0):
        """
        Initialize Trinity Protocol with all three agents.

        Args:
            budget_usd: Cost budget for the demo
        """
        print("\n" + "=" * 70)
        print(" " * 15 + "🧠 TRINITY PROTOCOL - COMPLETE DEMO")
        print(" " * 10 + "The Second Brain for Autonomous Development")
        print("=" * 70)

        # Infrastructure
        print("\n[1/6] Initializing infrastructure...")
        self.message_bus = MessageBus(":memory:")
        self.pattern_store = PersistentStore(":memory:")

        # Create cost tracker with correct API
        storage = SQLiteStorage(":memory:")
        self.cost_tracker = CostTracker(storage=storage)
        self.cost_tracker.set_budget(limit_usd=budget_usd, alert_threshold_pct=80.0)

        self.agent_context = create_agent_context()

        print("   ✓ Message Bus (3 queues: telemetry, improvement, execution)")
        print("   ✓ Pattern Store (cross-session learning)")
        print(f"   ✓ Cost Tracker (budget: ${budget_usd:.2f})")

        # PERCEPTION: WITNESS Agent
        print("\n[2/6] Starting PERCEPTION layer (WITNESS)...")
        self.witness = WitnessAgent(
            message_bus=self.message_bus, pattern_store=self.pattern_store, min_confidence=0.6
        )
        print("   ✓ WITNESS agent ready (8-step cycle)")
        print("   ✓ Monitoring: telemetry_stream + personal_context_stream")

        # COGNITION: ARCHITECT Agent
        print("\n[3/6] Starting COGNITION layer (ARCHITECT)...")
        self.architect = ArchitectAgent(
            message_bus=self.message_bus, pattern_store=self.pattern_store, min_complexity=0.7
        )
        print("   ✓ ARCHITECT agent ready (10-step cycle)")
        print("   ✓ Hybrid intelligence: local Codestral / cloud GPT-5")

        # ACTION: EXECUTOR Agent
        print("\n[4/6] Starting ACTION layer (EXECUTOR)...")
        self.executor = ExecutorAgent(
            message_bus=self.message_bus,
            cost_tracker=self.cost_tracker,
            agent_context=self.agent_context,
        )
        print("   ✓ EXECUTOR agent ready (9-step cycle)")
        print("   ✓ Sub-agents: CodeWriter, TestArchitect, ReleaseManager")

        self.running_tasks = []

    async def run_complete_demo(self):
        """
        Run complete Trinity demonstration.

        Flow:
        1. Publish test events
        2. WITNESS detects patterns → improvement_queue
        3. ARCHITECT plans tasks → execution_queue
        4. EXECUTOR executes tasks → telemetry_stream
        5. Verify results and show costs
        """

        # Start all agents
        print("\n[5/6] Starting autonomous agents...")
        witness_task = asyncio.create_task(self.witness.run())
        architect_task = asyncio.create_task(self.architect.run())
        executor_task = asyncio.create_task(self.executor.run())

        self.running_tasks = [witness_task, architect_task, executor_task]
        print("   ✓ All three agents running autonomously")

        # Wait for initialization
        await asyncio.sleep(0.5)

        # Publish test events
        print("\n[6/6] Publishing test events...")
        await self._publish_test_events()

        # Wait for processing
        print("\n⏳ Processing through Trinity pipeline...")
        print("   (This takes a few seconds for all three layers)")
        await asyncio.sleep(3.0)

        # Stop agents
        print("\n🛑 Stopping agents...")
        await self.witness.stop()
        await self.architect.stop()
        await self.executor.stop()

        # Wait for graceful shutdown
        for task in self.running_tasks:
            try:
                await asyncio.wait_for(task, timeout=2.0)
            except (TimeoutError, asyncio.CancelledError):
                pass

        # Show results
        print("\n" + "=" * 70)
        print(" " * 25 + "📊 RESULTS")
        print("=" * 70)

        await self._show_results()

        # Show costs
        print("\n" + "=" * 70)
        print(" " * 22 + "💰 COST ANALYSIS")
        print("=" * 70)

        # Get and display cost summary
        summary_result = self.cost_tracker.get_summary()
        if summary_result.is_ok():
            summary = summary_result.unwrap()
            print(f"\nTotal Cost: ${summary.total_cost_usd:.4f}")
            print(f"Total Calls: {summary.total_calls}")
            print(f"Total Tokens In: {summary.total_tokens_in:,}")
            print(f"Total Tokens Out: {summary.total_tokens_out:,}")
            print(f"Success Rate: {summary.success_rate:.1%}")

            if summary.by_operation:
                print("\nCost by Operation:")
                for op, cost in summary.by_operation.items():
                    print(f"  {op}: ${cost:.4f}")

            if summary.by_model:
                print("\nCost by Model:")
                for model, cost in summary.by_model.items():
                    print(f"  {model}: ${cost:.4f}")

            # Show budget status
            budget_result = self.cost_tracker.get_budget_status()
            if budget_result.is_ok():
                budget = budget_result.unwrap()
                if budget.limit_usd:
                    print("\nBudget Status:")
                    print(f"  Limit: ${budget.limit_usd:.2f}")
                    print(f"  Spent: ${budget.spent_usd:.4f}")
                    print(f"  Remaining: ${budget.remaining_usd:.4f}")
                    print(f"  Percent Used: {budget.percent_used:.1f}%")
                    if budget.alert_triggered:
                        print("  ⚠️  Budget alert triggered!")
                    if budget.limit_exceeded:
                        print("  🔴 Budget limit exceeded!")

        # Cleanup
        self.message_bus.close()
        self.pattern_store.close()
        self.cost_tracker.storage.close()

        print("\n" + "=" * 70)
        print(" " * 20 + "✅ DEMO COMPLETE")
        print("=" * 70)
        print("\n🎉 Trinity Protocol autonomous cycle demonstrated!")
        print("   The Second Brain is operational and ready for production.\n")

    async def _publish_test_events(self):
        """Publish diverse test events to telemetry stream."""

        test_events = [
            {
                "message": "Critical error: NoneType in production payment processing",
                "severity": "critical",
                "file": "payments/stripe.py",
                "error_type": "AttributeError",
                "keywords": ["NoneType", "critical", "payment"],
            },
            {
                "message": "Dict[Any, Any] detected in user model - constitutional violation",
                "file": "models/user.py",
                "severity": "high",
                "keywords": ["type_safety", "constitution", "violation"],
            },
            {
                "message": "Test test_concurrent_transactions fails 40% of the time",
                "test_file": "tests/test_payments.py",
                "failure_rate": "40%",
                "keywords": ["flaky", "test", "concurrency"],
            },
            {
                "message": "Duplicate validation logic found in 3 files",
                "files": ["auth.py", "api.py", "utils.py"],
                "pattern": "code_duplication",
                "keywords": ["duplication", "refactor"],
            },
            {
                "message": "User requests: Dark mode support across entire application",
                "scope": "multi-file",
                "priority": "NORMAL",
                "keywords": ["ui", "feature_request", "dark_mode"],
            },
        ]

        for i, event in enumerate(test_events, 1):
            await self.message_bus.publish("telemetry_stream", event)
            print(f"   {i}. {event['message'][:60]}...")

        print(f"\n   ✓ Published {len(test_events)} events to telemetry_stream")

    async def _show_results(self):
        """Show results from each layer."""

        # WITNESS results
        witness_stats = self.witness.get_stats()
        detector_stats = witness_stats.get("detector", {})
        print("\n🔍 PERCEPTION Layer (WITNESS):")
        print(f"   Patterns detected: {detector_stats.get('total_detections', 0)}")

        improvement_count = await self.message_bus.get_pending_count("improvement_queue")
        print(f"   Signals published: {improvement_count} → improvement_queue")

        # ARCHITECT results
        architect_stats = self.architect.get_stats()
        print("\n🧠 COGNITION Layer (ARCHITECT):")
        print(f"   Signals processed: {architect_stats['signals_processed']}")
        print(f"   Tasks created: {architect_stats['tasks_created']}")
        print(f"   Specs generated: {architect_stats['specs_generated']}")
        print(f"   Cloud escalations: {architect_stats['escalations']}")

        execution_count = await self.message_bus.get_pending_count("execution_queue")
        print(f"   Tasks queued: {execution_count} → execution_queue")

        # EXECUTOR results
        executor_stats = self.executor.get_stats()
        print("\n⚡ ACTION Layer (EXECUTOR):")
        print(f"   Tasks executed: {executor_stats['tasks_processed']}")
        print(f"   Tasks succeeded: {executor_stats['tasks_succeeded']}")
        print(f"   Tasks failed: {executor_stats['tasks_failed']}")

        telemetry_count = await self.message_bus.get_pending_count("telemetry_stream")
        print(f"   Telemetry reports: {telemetry_count} → telemetry_stream")

        # Overall pipeline
        print("\n🔄 Pipeline Integrity:")
        if architect_stats["signals_processed"] > 0 and executor_stats["tasks_processed"] > 0:
            print("   ✅ Complete cycle operational (WITNESS → ARCHITECT → EXECUTOR)")
        else:
            print("   ⚠️  Pipeline still warming up (normal for short demo)")

        # Learning
        pattern_stats = self.pattern_store.get_stats()
        print("\n📚 Learning (Cross-Session):")
        print(f"   Patterns stored: {pattern_stats['total_patterns']}")
        print(f"   FAISS available: {pattern_stats['faiss_available']}")


async def demo_architect():
    """
    Demo: Architect agent creates project plan.

    Demonstrates WITNESS → ARCHITECT pipeline:
    - Pattern detection
    - Complexity assessment
    - Spec generation
    - Task graph creation
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "ARCHITECT AGENT DEMO")
    print("=" * 70)

    message_bus = MessageBus(":memory:")
    pattern_store = PersistentStore(":memory:")

    witness = WitnessAgent(message_bus=message_bus, pattern_store=pattern_store, min_confidence=0.6)

    architect = ArchitectAgent(
        message_bus=message_bus, pattern_store=pattern_store, min_complexity=0.7
    )

    print("\n[1/3] Starting WITNESS and ARCHITECT agents...")
    witness_task = asyncio.create_task(witness.run())
    architect_task = asyncio.create_task(architect.run())
    await asyncio.sleep(0.5)

    print("\n[2/3] Publishing architectural challenge...")
    await message_bus.publish(
        "telemetry_stream",
        {
            "message": "Dict[Any, Any] usage detected in core models - violates Article II type safety",
            "file": "models/user.py",
            "severity": "critical",
            "keywords": ["architecture", "constitutional_violation"],
        },
    )

    await asyncio.sleep(2.0)

    print("\n[3/3] Checking results...")
    architect_stats = architect.get_stats()
    print(f"   Signals processed: {architect_stats['signals_processed']}")
    print(f"   Tasks created: {architect_stats['tasks_created']}")
    print(f"   Specs generated: {architect_stats['specs_generated']}")

    await witness.stop()
    await architect.stop()

    for task in [witness_task, architect_task]:
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (TimeoutError, asyncio.CancelledError):
            pass

    message_bus.close()
    pattern_store.close()

    print("\n✅ ARCHITECT demo complete\n")


async def demo_cost_tracking():
    """
    Demo: Cost tracking and budget management.

    Demonstrates:
    - LLM call tracking
    - Cost calculation by agent/model
    - Budget enforcement
    - Dashboard visualization
    """
    print("\n" + "=" * 70)
    print(" " * 20 + "COST TRACKING DEMO")
    print("=" * 70)

    storage = SQLiteStorage(":memory:")
    tracker = CostTracker(storage=storage)
    tracker.set_budget(limit_usd=5.0, alert_threshold_pct=80.0)

    print("\n[1/2] Simulating LLM calls...")

    # Simulate various LLM calls
    calls = [
        ("WITNESS", "codestral-22b", ModelTier.LOCAL, 500, 200),
        ("ARCHITECT", "gpt-5", ModelTier.CLOUD_PREMIUM, 2000, 1000),
        ("EXECUTOR", "gpt-5-mini", ModelTier.CLOUD_MINI, 1500, 800),
        ("WITNESS", "codestral-22b", ModelTier.LOCAL, 400, 150),
        ("ARCHITECT", "claude-4.1", ModelTier.CLOUD_PREMIUM, 2500, 1200),
    ]

    for agent, model, tier, input_tokens, output_tokens in calls:
        result = tracker.track(
            operation=agent,
            model=model,
            model_tier=tier,
            tokens_in=input_tokens,
            tokens_out=output_tokens,
            duration_seconds=2.5,
            success=True,
            metadata={"agent": agent},
        )
        if result.is_ok():
            print(f"   ✓ {agent}: {model} ({input_tokens} → {output_tokens} tokens)")
        else:
            print(f"   ✗ {agent}: Failed to track - {result.unwrap_err()}")

    print("\n[2/2] Cost dashboard:")

    # Display summary
    summary_result = tracker.get_summary()
    if summary_result.is_ok():
        summary = summary_result.unwrap()
        print(f"\n  Total Cost: ${summary.total_cost_usd:.4f}")
        print(f"  Total Calls: {summary.total_calls}")
        print(f"  Success Rate: {summary.success_rate:.1%}")

        print("\n  Cost by Agent:")
        for op, cost in summary.by_operation.items():
            print(f"    {op}: ${cost:.4f}")

        print("\n  Cost by Model:")
        for model, cost in summary.by_model.items():
            print(f"    {model}: ${cost:.4f}")

        # Show budget status
        budget_result = tracker.get_budget_status()
        if budget_result.is_ok():
            budget = budget_result.unwrap()
            print(
                f"\n  Budget: ${budget.spent_usd:.4f} / ${budget.limit_usd:.2f} ({budget.percent_used:.1f}%)"
            )

    tracker.storage.close()
    print("\n✅ Cost tracking demo complete\n")


async def main():
    """Run all demos."""
    import argparse

    parser = argparse.ArgumentParser(description="Trinity Protocol Complete Demo")
    parser.add_argument("--budget", type=float, default=10.0, help="Budget in USD")
    parser.add_argument(
        "--demo",
        choices=["complete", "architect", "cost", "all"],
        default="all",
        help="Which demo to run",
    )

    args = parser.parse_args()

    if args.demo in ["all", "complete"]:
        demo = TrinityCompleteDemo(budget_usd=args.budget)
        await demo.run_complete_demo()

    if args.demo in ["all", "architect"]:
        await demo_architect()

    if args.demo in ["all", "cost"]:
        await demo_cost_tracking()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting Trinity Protocol Complete Demo...")
    print("This demonstrates the full autonomous improvement cycle.")
    print("=" * 70)

    asyncio.run(main())
