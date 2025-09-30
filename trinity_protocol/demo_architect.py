"""
ARCHITECT Agent Integration Demo

Demonstrates the complete WITNESS → ARCHITECT → EXECUTOR pipeline.

This demo shows:
1. WITNESS detects patterns and publishes signals to improvement_queue
2. ARCHITECT processes signals and generates task graphs
3. Task graphs published to execution_queue (EXECUTOR would pick up from here)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.witness_agent import WitnessAgent
from trinity_protocol.architect_agent import ArchitectAgent


class ArchitectDemo:
    """Integration demo for ARCHITECT agent."""

    def __init__(self):
        # Infrastructure (in-memory databases for demo)
        self.message_bus = MessageBus(":memory:")
        self.pattern_store = PersistentStore(":memory:")

        # Agents
        self.witness = WitnessAgent(
            message_bus=self.message_bus,
            pattern_store=self.pattern_store,
            min_confidence=0.6
        )

        self.architect = ArchitectAgent(
            message_bus=self.message_bus,
            pattern_store=self.pattern_store,
            min_complexity=0.7
        )

    async def run_demo(self):
        """
        Run complete demo showing Trinity Protocol pipeline.

        Flow:
        1. Start WITNESS and ARCHITECT agents
        2. Publish test events to telemetry_stream
        3. WITNESS detects patterns → improvement_queue
        4. ARCHITECT processes signals → execution_queue
        5. Verify task graphs generated correctly
        """
        print("\n" + "=" * 60)
        print("TRINITY PROTOCOL - ARCHITECT AGENT DEMO")
        print("=" * 60)

        # Start agents in background
        print("\n[1] Starting WITNESS and ARCHITECT agents...")
        witness_task = asyncio.create_task(self.witness.run())
        architect_task = asyncio.create_task(self.architect.run())

        # Wait for agents to initialize
        await asyncio.sleep(0.5)

        # Publish test events
        print("\n[2] Publishing test events to telemetry_stream...")
        await self._publish_test_events()

        # Wait for processing
        print("\n[3] Waiting for WITNESS → ARCHITECT pipeline...")
        await asyncio.sleep(2.0)

        # Check results
        print("\n[4] Checking results...")
        await self._verify_results()

        # Stop agents
        print("\n[5] Stopping agents...")
        await self.witness.stop()
        await self.architect.stop()

        try:
            await asyncio.wait_for(witness_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass

        try:
            await asyncio.wait_for(architect_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass

        # Summary
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)

        self._print_summary()

        # Cleanup
        self.message_bus.close()
        self.pattern_store.close()

    async def _publish_test_events(self):
        """Publish diverse test events representing real-world scenarios."""

        test_events = [
            # Event 1: Simple bug fix (low complexity)
            {
                "message": "NoneType error in user authentication module",
                "severity": "high",
                "file": "auth/login.py",
                "error_type": "AttributeError"
            },

            # Event 2: Code duplication (moderate complexity)
            {
                "message": "Duplicate validation logic found in 3 controllers",
                "files": ["api/users.py", "api/posts.py", "api/comments.py"],
                "pattern": "code_duplication"
            },

            # Event 3: Constitutional violation (high complexity, architectural)
            {
                "message": "Dict[Any, Any] usage detected in core models - violates Article II type safety",
                "file": "models/user.py",
                "severity": "critical",
                "keywords": ["architecture", "constitutional_violation"]
            },

            # Event 4: User feature request (high complexity)
            {
                "message": "User requests: Dark mode support across entire application",
                "scope": "multi-file",
                "keywords": ["ui", "system-wide", "refactor"]
            },

            # Event 5: Flaky test (low complexity)
            {
                "message": "Test test_concurrent_updates fails intermittently (race condition)",
                "test_file": "tests/test_database.py",
                "failure_rate": "30%"
            }
        ]

        for i, event in enumerate(test_events, 1):
            await self.message_bus.publish("telemetry_stream", event)
            print(f"   ✓ Event {i}: {event.get('message', 'Unknown')[:60]}...")

        print(f"\n   Published {len(test_events)} events")

    async def _verify_results(self):
        """Verify that pipeline produced expected results."""

        # Check WITNESS stats
        witness_stats = self.witness.get_stats()
        print(f"\n   WITNESS Stats:")
        detector_stats = witness_stats.get('detector', {})
        print(f"   - Patterns detected: {detector_stats.get('total_detections', 0)}")

        # Check improvement_queue (signals from WITNESS)
        improvement_count = await self.message_bus.get_pending_count("improvement_queue")
        print(f"\n   Improvement Queue:")
        print(f"   - Pending signals: {improvement_count}")

        # Check ARCHITECT stats
        architect_stats = self.architect.get_stats()
        print(f"\n   ARCHITECT Stats:")
        print(f"   - Signals processed: {architect_stats['signals_processed']}")
        print(f"   - Specs generated: {architect_stats['specs_generated']}")
        print(f"   - ADRs generated: {architect_stats['adrs_generated']}")
        print(f"   - Tasks created: {architect_stats['tasks_created']}")
        print(f"   - Escalations (cloud): {architect_stats['escalations']}")

        # Check execution_queue (tasks from ARCHITECT)
        execution_count = await self.message_bus.get_pending_count("execution_queue")
        print(f"\n   Execution Queue:")
        print(f"   - Pending tasks: {execution_count}")

        # Sample some tasks
        if execution_count > 0:
            print(f"\n   Sample Tasks Generated:")
            sample_count = min(3, execution_count)

            async for i, message in self._async_enumerate(
                self.message_bus.subscribe("execution_queue", batch_size=sample_count)
            ):
                if i >= sample_count:
                    break

                task = message
                print(f"   - Task {i+1}:")
                print(f"     Type: {task.get('task_type')}")
                print(f"     Sub-Agent: {task.get('sub_agent')}")
                print(f"     Priority: {task.get('priority')}")
                print(f"     Dependencies: {task.get('dependencies', [])}")

    def _print_summary(self):
        """Print final summary statistics."""
        witness_stats = self.witness.get_stats()
        architect_stats = self.architect.get_stats()

        print("\n📊 FINAL STATISTICS")
        print("-" * 60)

        print("\nWITNESS Agent (Perception Layer):")
        detector_stats = witness_stats.get('detector', {})
        print(f"  ✓ Patterns detected: {detector_stats.get('total_detections', 0)}")

        print("\nARCHITECT Agent (Cognition Layer):")
        print(f"  ✓ Signals processed: {architect_stats['signals_processed']}")
        print(f"  ✓ Tasks created: {architect_stats['tasks_created']}")
        print(f"  ✓ Specs generated: {architect_stats['specs_generated']}")
        print(f"  ✓ ADRs generated: {architect_stats['adrs_generated']}")
        print(f"  ✓ Cloud escalations: {architect_stats['escalations']}")

        # Calculate efficiency metrics
        signals_count = architect_stats['signals_processed']
        if signals_count > 0:
            tasks_per_signal = architect_stats['tasks_created'] / signals_count
            print(f"\nEfficiency:")
            print(f"  ✓ Avg tasks per signal: {tasks_per_signal:.1f}")

        print("\n" + "=" * 60)
        print("Trinity Protocol Weeks 1-3 + Week 5 operational!")
        print("Next: Week 6 (EXECUTOR agent)")
        print("=" * 60 + "\n")

    async def _async_enumerate(self, async_iter):
        """Async enumerate helper."""
        i = 0
        async for item in async_iter:
            yield i, item
            i += 1


async def main():
    """Run demo."""
    demo = ArchitectDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
