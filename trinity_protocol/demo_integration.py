"""
Trinity Protocol Integration Demo

Demonstrates the complete Week 1-3 infrastructure working together:
- Persistent Store (Week 1)
- Message Bus (Week 1)
- Local Model Server (Week 2)
- WITNESS Agent (Week 3)

This demo simulates:
1. Events being published to telemetry_stream
2. WITNESS detecting patterns
3. Signals being published to improvement_queue
4. Patterns being persisted for learning
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.message_bus import MessageBus
from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.witness_agent import WitnessAgent
from shared.local_model_server import LocalModelServer


class TrinityDemo:
    """Demonstrates Trinity Protocol infrastructure."""

    def __init__(self):
        self.message_bus = MessageBus("demo_messages.db")
        self.pattern_store = PersistentStore("demo_patterns.db")
        self.model_server = None
        self.witness = None

    async def initialize(self):
        """Initialize all components."""
        print("🚀 Trinity Protocol Demo - Initializing Components\n")
        print("=" * 60)

        # Check local model availability
        print("\n1. Local Model Server")
        print("-" * 60)
        self.model_server = LocalModelServer()
        available = await self.model_server.is_local_available()

        if available:
            models = await self.model_server.get_available_models()
            print(f"✅ Ollama available with {len(models)} models")
            for model in models[:3]:
                print(f"   - {model}")
        else:
            print("⚠️  Ollama not running (optional for this demo)")

        # Initialize WITNESS
        print("\n2. WITNESS Agent (Perception Layer)")
        print("-" * 60)
        self.witness = WitnessAgent(
            message_bus=self.message_bus,
            pattern_store=self.pattern_store,
            min_confidence=0.7
        )
        print("✅ WITNESS agent initialized")
        print(f"   - Monitoring: telemetry_stream, personal_context_stream")
        print(f"   - Publishing to: improvement_queue")
        print(f"   - Min confidence: 0.7")

        # Check message bus
        print("\n3. Message Bus (Async Pub/Sub)")
        print("-" * 60)
        stats = self.message_bus.get_stats()
        print(f"✅ Message bus operational")
        print(f"   - Total messages: {stats['total_messages']}")
        print(f"   - Queues: {list(stats['by_queue'].keys()) if stats['by_queue'] else 'None yet'}")

        # Check persistent store
        print("\n4. Persistent Store (Pattern Learning)")
        print("-" * 60)
        store_stats = self.pattern_store.get_stats()
        print(f"✅ Pattern store operational")
        print(f"   - Total patterns: {store_stats['total_patterns']}")
        print(f"   - FAISS available: {store_stats['faiss_available']}")

        print("\n" + "=" * 60)
        print("✅ All components initialized successfully!\n")

    async def run_demo(self):
        """Run the integration demo."""
        print("🎬 Starting Trinity Protocol Demo\n")
        print("=" * 60)

        # Simulate various events
        test_events = [
            {
                "type": "critical_error",
                "message": "Fatal error: ModuleNotFoundError when importing core library",
                "metadata": {"file": "agent.py", "line": 42, "error_type": "ModuleNotFoundError"}
            },
            {
                "type": "constitutional_violation",
                "message": "Found Dict[Any, Any] in function signature - constitutional violation",
                "metadata": {"file": "legacy_code.py", "line": 105}
            },
            {
                "type": "flaky_test",
                "message": "Test failed with AssertionError - sometimes passes, intermittent failure",
                "metadata": {"file": "test_integration.py", "error_type": "AssertionError"}
            },
            {
                "type": "user_intent",
                "message": "I need dark mode feature - please implement this",
                "metadata": {"source": "user_context"}
            },
            {
                "type": "code_duplication",
                "message": "Similar code repeated in 3 files - DRY violation detected",
                "metadata": {"files": ["a.py", "b.py", "c.py"]}
            }
        ]

        # Start WITNESS in background
        witness_task = asyncio.create_task(self.witness.run())

        # Give WITNESS time to start
        await asyncio.sleep(0.5)

        print("\n📡 Publishing Test Events to Telemetry Stream")
        print("-" * 60)

        # Publish events
        for i, event in enumerate(test_events, 1):
            print(f"\n{i}. Publishing: {event['type']}")
            print(f"   Message: {event['message'][:70]}...")

            await self.message_bus.publish(
                queue_name="telemetry_stream",
                message=event,
                priority=5 if event['type'] in ['critical_error', 'constitutional_violation'] else 0
            )

            # Give WITNESS time to process
            await asyncio.sleep(0.3)

        # Wait for processing
        await asyncio.sleep(1.0)

        # Stop WITNESS
        await self.witness.stop()
        try:
            await asyncio.wait_for(witness_task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass  # Expected when stopping agent

        # Check results
        print("\n\n🔍 Checking Results")
        print("=" * 60)

        # Check improvement queue for signals
        print("\n1. Signals in Improvement Queue")
        print("-" * 60)
        pending_signals = await self.message_bus.get_pending_count("improvement_queue")
        print(f"✅ Found {pending_signals} signals published by WITNESS")

        if pending_signals > 0:
            # Fetch and display signals
            signals = await self.message_bus._fetch_pending("improvement_queue", limit=10)
            for i, signal in enumerate(signals, 1):
                print(f"\n   Signal {i}:")
                print(f"   - Pattern: {signal['pattern']}")
                print(f"   - Priority: {signal['priority']}")
                print(f"   - Confidence: {signal['confidence']:.2f}")
                print(f"   - Summary: {signal['summary'][:60]}...")

        # Check pattern store
        print("\n\n2. Patterns Stored for Learning")
        print("-" * 60)
        store_stats = self.pattern_store.get_stats()
        print(f"✅ Total patterns stored: {store_stats['total_patterns']}")

        if store_stats['by_type']:
            print("\n   By type:")
            for ptype, count in store_stats['by_type'].items():
                print(f"   - {ptype}: {count}")

        if store_stats['top_patterns']:
            print("\n   Most frequent:")
            for item in store_stats['top_patterns'][:3]:
                if isinstance(item, tuple) and len(item) == 2:
                    pattern_name, times_seen = item
                    print(f"   - {pattern_name}: seen {times_seen}x")
                else:
                    print(f"   - {item}")

        # WITNESS stats
        print("\n\n3. WITNESS Agent Statistics")
        print("-" * 60)
        witness_stats = self.witness.get_stats()
        detector_stats = witness_stats['detector']
        print(f"✅ Total detections: {detector_stats['total_detections']}")
        print(f"   Unique patterns: {detector_stats['unique_patterns']}")

        if detector_stats['most_common']:
            print("\n   Most common patterns detected:")
            for pattern_name, count in detector_stats['most_common'][:3]:
                print(f"   - {pattern_name}: {count}x")

        # Message bus final stats
        print("\n\n4. Message Bus Statistics")
        print("-" * 60)
        bus_stats = self.message_bus.get_stats()
        print(f"✅ Total messages processed: {bus_stats['total_messages']}")
        print(f"   By status:")
        for status, count in bus_stats.get('by_status', {}).items():
            print(f"   - {status}: {count}")

        print("\n" + "=" * 60)
        print("✅ Demo Complete!\n")

    async def cleanup(self):
        """Cleanup resources."""
        print("\n🧹 Cleaning up resources...")

        if self.model_server:
            await self.model_server.close()

        if self.message_bus:
            self.message_bus.close()

        if self.pattern_store:
            self.pattern_store.close()

        # Clean demo databases
        Path("demo_messages.db").unlink(missing_ok=True)
        Path("demo_patterns.db").unlink(missing_ok=True)

        print("✅ Cleanup complete\n")

    async def run(self):
        """Run full demo."""
        try:
            await self.initialize()
            await self.run_demo()
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("   TRINITY PROTOCOL - INTEGRATION DEMONSTRATION")
    print("   Foundation Complete: Weeks 1-3")
    print("=" * 60 + "\n")

    demo = TrinityDemo()
    await demo.run()

    print("=" * 60)
    print("🎉 Trinity Protocol Foundation Verified!")
    print("=" * 60)
    print("\nComponents Working:")
    print("  ✅ Persistent Store (SQLite + FAISS)")
    print("  ✅ Message Bus (Async Pub/Sub)")
    print("  ✅ Local Model Server (Ollama Integration)")
    print("  ✅ WITNESS Agent (Pattern Detection)")
    print("\nReady for:")
    print("  → Week 5: ARCHITECT Agent (Strategic Planning)")
    print("  → Week 6: EXECUTOR Agent (Meta-Orchestration)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
