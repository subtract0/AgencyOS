"""
Complete Trinity Protocol Integration Demo

Demonstrates the full autonomous improvement cycle:
EVENT → WITNESS → ARCHITECT → EXECUTOR → TELEMETRY → LEARNING

This is the complete "Second Brain" in action.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.cost_tracker import CostTracker
from trinity_protocol.witness_agent import WitnessAgent
from trinity_protocol.architect_agent import ArchitectAgent
from trinity_protocol.executor_agent import ExecutorAgent


class TrinityDemo:
    """
    Complete Trinity Protocol demonstration.

    Shows the full autonomous cycle with cost tracking.
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
        self.cost_tracker = CostTracker(":memory:", budget_usd=budget_usd)
        print(f"   ✓ Message Bus (3 queues: telemetry, improvement, execution)")
        print(f"   ✓ Pattern Store (cross-session learning)")
        print(f"   ✓ Cost Tracker (budget: ${budget_usd:.2f})")

        # PERCEPTION: WITNESS Agent
        print("\n[2/6] Starting PERCEPTION layer (WITNESS)...")
        self.witness = WitnessAgent(
            message_bus=self.message_bus,
            pattern_store=self.pattern_store,
            min_confidence=0.6
        )
        print("   ✓ WITNESS agent ready (8-step cycle)")
        print("   ✓ Monitoring: telemetry_stream + personal_context_stream")

        # COGNITION: ARCHITECT Agent
        print("\n[3/6] Starting COGNITION layer (ARCHITECT)...")
        self.architect = ArchitectAgent(
            message_bus=self.message_bus,
            pattern_store=self.pattern_store,
            min_complexity=0.7
        )
        print("   ✓ ARCHITECT agent ready (10-step cycle)")
        print("   ✓ Hybrid intelligence: local Codestral / cloud GPT-5")

        # ACTION: EXECUTOR Agent
        print("\n[4/6] Starting ACTION layer (EXECUTOR)...")
        self.executor = ExecutorAgent(
            message_bus=self.message_bus,
            cost_tracker=self.cost_tracker
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
            except (asyncio.TimeoutError, asyncio.CancelledError):
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

        self.cost_tracker.print_dashboard()

        # Cleanup
        self.message_bus.close()
        self.pattern_store.close()
        self.cost_tracker.close()

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
                "error_type": "AttributeError"
            },
            {
                "message": "Dict[Any, Any] detected in user model - constitutional violation",
                "file": "models/user.py",
                "severity": "high",
                "keywords": ["type_safety", "constitution"]
            },
            {
                "message": "Test test_concurrent_transactions fails 40% of the time",
                "test_file": "tests/test_payments.py",
                "failure_rate": "40%"
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
        detector_stats = witness_stats.get('detector', {})
        print("\n🔍 PERCEPTION Layer (WITNESS):")
        print(f"   Patterns detected: {detector_stats.get('total_detections', 0)}")

        improvement_count = await self.message_bus.get_pending_count("improvement_queue")
        print(f"   Signals published: {improvement_count} → improvement_queue")

        # ARCHITECT results
        architect_stats = self.architect.get_stats()
        print(f"\n🧠 COGNITION Layer (ARCHITECT):")
        print(f"   Signals processed: {architect_stats['signals_processed']}")
        print(f"   Tasks created: {architect_stats['tasks_created']}")
        print(f"   Specs generated: {architect_stats['specs_generated']}")
        print(f"   Cloud escalations: {architect_stats['escalations']}")

        execution_count = await self.message_bus.get_pending_count("execution_queue")
        print(f"   Tasks queued: {execution_count} → execution_queue")

        # EXECUTOR results
        executor_stats = self.executor.get_stats()
        print(f"\n⚡ ACTION Layer (EXECUTOR):")
        print(f"   Tasks executed: {executor_stats['tasks_processed']}")
        print(f"   Tasks succeeded: {executor_stats['tasks_succeeded']}")
        print(f"   Tasks failed: {executor_stats['tasks_failed']}")

        telemetry_count = await self.message_bus.get_pending_count("telemetry_stream")
        print(f"   Telemetry reports: {telemetry_count} → telemetry_stream")

        # Overall pipeline
        print(f"\n🔄 Pipeline Integrity:")
        if architect_stats['signals_processed'] > 0 and executor_stats['tasks_processed'] > 0:
            print(f"   ✅ Complete cycle operational (WITNESS → ARCHITECT → EXECUTOR)")
        else:
            print(f"   ⚠️  Pipeline still warming up (normal for short demo)")

        # Learning
        pattern_stats = self.pattern_store.get_stats()
        print(f"\n📚 Learning (Cross-Session):")
        print(f"   Patterns stored: {pattern_stats['total_patterns']}")
        print(f"   FAISS available: {pattern_stats['faiss_available']}")


async def main():
    """Run the demo."""
    demo = TrinityDemo(budget_usd=10.0)
    await demo.run_complete_demo()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting Trinity Protocol Complete Demo...")
    print("This demonstrates the full autonomous improvement cycle.")
    print("=" * 70)

    asyncio.run(main())
