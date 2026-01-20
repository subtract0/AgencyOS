#!/usr/bin/env python3
"""Second Brain Digest Generator.

Produces daily/weekly summaries (tap on the shoulder).

Usage:
    python digest.py daily    # Daily digest
    python digest.py weekly   # Weekly review
    python digest.py status   # Quick status
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.brain import SecondBrain


def main():
    brain = SecondBrain()

    if len(sys.argv) < 2:
        print("🧠 Second Brain Digest")
        print("\nUsage:")
        print("  python digest.py daily   - Get your daily digest")
        print("  python digest.py weekly  - Get your weekly review")
        print("  python digest.py status  - Quick brain status")
        return

    command = sys.argv[1].lower()

    if command == "daily":
        print(brain.daily_digest())

    elif command == "weekly":
        print(brain.weekly_review())

    elif command == "status":
        status = brain.get_status()
        print("🧠 Second Brain Status")
        print("=" * 40)
        print(f"📊 Stats:")
        for key, value in status['stats'].items():
            print(f"   {key}: {value}")
        print(f"\n⚙️ Settings:")
        print(f"   Confidence threshold: {status['confidence_threshold']}")
        print(f"\n📥 Needs review: {status['needs_review']} items")
        print(f"🚀 Active projects: {status['active_projects']}")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python digest.py search 'query'")
            return
        query = " ".join(sys.argv[2:])
        results = brain.search(query)
        print(f"🔍 Search results for '{query}':")
        for r in results:
            print(f"   [{r['type']}] {r['name']}: {r['preview'][:60]}...")

    else:
        print(f"Unknown command: {command}")
        print("Available: daily, weekly, status, search")


if __name__ == "__main__":
    main()
