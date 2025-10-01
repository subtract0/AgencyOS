"""
Real-Time Pattern Detection Dashboard

Monitors Trinity Protocol pattern detection with 1-minute refresh:
- Events processed vs expected
- Detection rate and accuracy
- Pattern type distribution
- Confidence trends
- Learning statistics

Usage:
    python trinity_protocol/pattern_dashboard.py --live
    python trinity_protocol/pattern_dashboard.py --once
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from trinity_protocol.persistent_store import PersistentStore
from trinity_protocol.message_bus import MessageBus


class PatternDashboard:
    """Real-time pattern detection monitoring dashboard."""

    def __init__(
        self,
        pattern_store: PersistentStore,
        message_bus: MessageBus,
        expected_events: Optional[int] = None
    ):
        """
        Initialize pattern dashboard.

        Args:
            pattern_store: Pattern storage for statistics
            message_bus: Message bus for queue monitoring
            expected_events: Expected total events (for progress tracking)
        """
        self.pattern_store = pattern_store
        self.message_bus = message_bus
        self.expected_events = expected_events

    async def render(self, clear_screen: bool = True) -> None:
        """
        Render dashboard to console.

        Args:
            clear_screen: Whether to clear screen before rendering
        """
        if clear_screen:
            print("\033[2J\033[H")  # Clear screen and move cursor to top

        pattern_stats = self.pattern_store.get_stats()

        # Queue statistics
        telemetry_count = await self.message_bus.get_pending_count("telemetry_stream")
        improvement_count = await self.message_bus.get_pending_count("improvement_queue")
        execution_count = await self.message_bus.get_pending_count("execution_queue")

        print("=" * 80)
        print(" " * 20 + "TRINITY PROTOCOL - PATTERN DETECTION")
        print("=" * 80)

        # Event progress
        if self.expected_events:
            processed = pattern_stats["total_patterns"]
            progress = (processed / self.expected_events * 100) if self.expected_events > 0 else 0

            bar_width = 50
            filled = int((progress / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(f"\n📊 EVENT PROGRESS:")
            print(f"   {bar} {progress:.1f}%")
            print(f"   {processed} / {self.expected_events} events processed")

        # Pattern detection
        print(f"\n🔍 PATTERN DETECTION:")
        print(f"   Total patterns: {pattern_stats['total_patterns']}")
        print(f"   Average confidence: {pattern_stats['average_confidence']:.3f}")
        print(f"   FAISS available: {'✓' if pattern_stats['faiss_available'] else '✗'}")
        if pattern_stats['faiss_available']:
            print(f"   Embedding index size: {pattern_stats['index_size']}")

        # By pattern type
        if pattern_stats["by_type"]:
            print(f"\n📋 BY PATTERN TYPE:")
            sorted_types = sorted(
                pattern_stats["by_type"].items(),
                key=lambda x: -x[1]
            )
            for pattern_type, count in sorted_types:
                percent = (count / pattern_stats["total_patterns"] * 100) if pattern_stats["total_patterns"] > 0 else 0
                bar_width = 30
                filled = int((percent / 100) * bar_width)
                bar = "▓" * filled + "░" * (bar_width - filled)
                print(f"   {pattern_type:25s} {bar} {count:4d} ({percent:.1f}%)")

        # Top patterns
        if pattern_stats["top_patterns"]:
            print(f"\n🏆 TOP PATTERNS (by frequency):")
            for i, pattern in enumerate(pattern_stats["top_patterns"][:5], 1):
                success_rate = pattern.get("success_rate", 0)
                success_indicator = "✓" if success_rate > 0.8 else "⚠"
                print(f"   {i}. {pattern['pattern_name']:30s} "
                      f"seen {pattern['times_seen']:3d}x "
                      f"{success_indicator} {success_rate*100:.0f}% success")

        # Queue health
        print(f"\n📬 MESSAGE QUEUES:")
        print(f"   telemetry_stream    {telemetry_count:4d} pending")
        print(f"   improvement_queue   {improvement_count:4d} pending")
        print(f"   execution_queue     {execution_count:4d} pending")

        # Queue health indicator
        max_backlog = max(telemetry_count, improvement_count, execution_count)
        if max_backlog > 50:
            print(f"\n   ⚠️  WARNING: Queue backlog detected ({max_backlog} messages)")
        elif max_backlog > 20:
            print(f"\n   ⚡ Processing load: {max_backlog} messages")
        else:
            print(f"\n   ✓ All queues healthy")

        print("\n" + "=" * 80)
        print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    async def run_live(self, refresh_seconds: int = 60) -> None:
        """
        Run dashboard in live mode with auto-refresh.

        Args:
            refresh_seconds: Seconds between refreshes
        """
        import asyncio

        print("Starting live pattern dashboard (Ctrl+C to exit)...")
        try:
            while True:
                await self.render(clear_screen=True)
                await asyncio.sleep(refresh_seconds)
        except KeyboardInterrupt:
            print("\n\nDashboard stopped.")

    async def run_once(self) -> None:
        """Render dashboard once."""
        await self.render(clear_screen=False)


async def main():
    """Main entry point."""
    import asyncio

    parser = argparse.ArgumentParser(description="Trinity Protocol Pattern Dashboard")
    parser.add_argument("--pattern-db", default="trinity_patterns.db", help="Pattern database path")
    parser.add_argument("--message-db", default="trinity_messages.db", help="Message database path")
    parser.add_argument("--expected-events", type=int, help="Expected total events")
    parser.add_argument("--live", action="store_true", help="Run in live mode (auto-refresh)")
    parser.add_argument("--refresh", type=int, default=60, help="Refresh interval in seconds")
    parser.add_argument("--once", action="store_true", help="Render once and exit")

    args = parser.parse_args()

    # Initialize stores
    pattern_store = PersistentStore(args.pattern_db)
    message_bus = MessageBus(args.message_db)

    try:
        dashboard = PatternDashboard(
            pattern_store=pattern_store,
            message_bus=message_bus,
            expected_events=args.expected_events
        )

        if args.once:
            await dashboard.run_once()
        else:
            await dashboard.run_live(refresh_seconds=args.refresh)
    finally:
        pattern_store.close()
        message_bus.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
