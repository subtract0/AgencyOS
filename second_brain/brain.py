#!/usr/bin/env python3
"""Second Brain CLI.

Your cognitive extension - capture thoughts, let AI route them,
get daily digests that actually matter.

Usage:
    python brain.py capture "Your thought here"
    python brain.py capture --interactive
    python brain.py daily
    python brain.py weekly
    python brain.py status
    python brain.py search "query"
    python brain.py fix entry_id category
    python brain.py review  # Show items needing review
"""

import sys
import os
import argparse

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.brain import SecondBrain
from lib.storage import SecondBrainStorage


def main():
    parser = argparse.ArgumentParser(
        description="🧠 Second Brain - Your cognitive extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  brain.py capture "Call Sarah about the project"
  brain.py capture -i              # Interactive mode
  brain.py daily                   # Daily digest
  brain.py weekly                  # Weekly review
  brain.py status                  # Quick status
  brain.py search "project name"   # Search
  brain.py fix abc123 projects     # Fix misclassified item
  brain.py review                  # Show items needing review
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Capture
    capture_parser = subparsers.add_parser("capture", aliases=["c"], help="Capture a thought")
    capture_parser.add_argument("thought", nargs="*", help="The thought to capture")
    capture_parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")

    # Daily digest
    subparsers.add_parser("daily", aliases=["d"], help="Get daily digest")

    # Weekly review
    subparsers.add_parser("weekly", aliases=["w"], help="Get weekly review")

    # Status
    subparsers.add_parser("status", aliases=["s"], help="Show brain status")

    # Search
    search_parser = subparsers.add_parser("search", help="Search your brain")
    search_parser.add_argument("query", nargs="+", help="Search query")

    # Fix
    fix_parser = subparsers.add_parser("fix", help="Fix a misclassified item")
    fix_parser.add_argument("entry_id", help="Entry ID to fix")
    fix_parser.add_argument("category", choices=["people", "projects", "ideas", "admin"], help="Correct category")

    # Review
    subparsers.add_parser("review", aliases=["r"], help="Show items needing review")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    brain = SecondBrain()

    # CAPTURE
    if args.command in ("capture", "c"):
        if args.interactive:
            print("🧠 Second Brain Capture")
            print("   Type your thoughts. One per line. 'quit' to exit.\n")
            while True:
                try:
                    thought = input("💭 > ").strip()
                    if thought.lower() in ("quit", "exit", "q"):
                        break
                    if thought:
                        result = brain.capture(thought)
                        print(f"   ✅ {result['message']}\n")
                except (KeyboardInterrupt, EOFError):
                    break
            print("👋 Done!")
        elif args.thought:
            thought = " ".join(args.thought)
            result = brain.capture(thought)
            print(f"✅ {result['message']}")
            if result['status'] == 'filed' and result.get('extracted'):
                print("\n📝 Extracted:")
                for k, v in result['extracted'].items():
                    if v:
                        print(f"   {k}: {v}")
        else:
            # Read from stdin
            for line in sys.stdin:
                if line.strip():
                    result = brain.capture(line.strip())
                    print(f"✅ {result['message']}")

    # DAILY
    elif args.command in ("daily", "d"):
        print(brain.daily_digest())

    # WEEKLY
    elif args.command in ("weekly", "w"):
        print(brain.weekly_review())

    # STATUS
    elif args.command in ("status", "s"):
        status = brain.get_status()
        print("🧠 Second Brain Status")
        print("=" * 40)
        for k, v in status['stats'].items():
            print(f"   {k}: {v}")
        print(f"\n   Needs review: {status['needs_review']}")
        print(f"   Active projects: {status['active_projects']}")

    # SEARCH
    elif args.command == "search":
        query = " ".join(args.query)
        results = brain.search(query)
        if results:
            print(f"🔍 Found {len(results)} results for '{query}':\n")
            for r in results:
                print(f"   [{r['type']}] {r['name']}")
                print(f"       {r['preview'][:80]}")
        else:
            print(f"No results for '{query}'")

    # FIX
    elif args.command == "fix":
        result = brain.fix(args.entry_id, args.category)
        print(f"{'✅' if result['status'] == 'fixed' else '❌'} {result['message']}")

    # REVIEW
    elif args.command in ("review", "r"):
        needs_review = brain.storage.get_needs_review()
        if not needs_review:
            print("✨ Nothing needs review!")
        else:
            print(f"📥 {len(needs_review)} items need review:\n")
            for entry in needs_review:
                print(f"   ID: {entry.id}")
                print(f"   Text: {entry.raw_text[:80]}...")
                print(f"   Suggested: {entry.filed_to} ({int(entry.confidence * 100)}%)")
                print(f"   Fix: brain.py fix {entry.id} <category>")
                print()


if __name__ == "__main__":
    main()
