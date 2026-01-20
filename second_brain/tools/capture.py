#!/usr/bin/env python3
"""Second Brain Capture Tool.

The ONE frictionless action: dump a thought and move on.

Usage:
    # Capture a thought
    python capture.py "Need to call Sarah about the project deadline"

    # Capture from stdin (for piping)
    echo "Remember to review quarterly goals" | python capture.py

    # Interactive mode
    python capture.py --interactive
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.brain import SecondBrain


def main():
    brain = SecondBrain()

    # Interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("🧠 Second Brain Capture (type 'quit' to exit)")
        print("   Just dump your thoughts, one per line.\n")

        while True:
            try:
                thought = input("💭 > ").strip()
                if thought.lower() in ("quit", "exit", "q"):
                    print("👋 Goodbye!")
                    break
                if not thought:
                    continue

                result = brain.capture(thought)
                print(f"   ✅ {result['message']}\n")

            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                break

    # Stdin mode
    elif not sys.stdin.isatty():
        for line in sys.stdin:
            thought = line.strip()
            if thought:
                result = brain.capture(thought)
                print(f"✅ {result['message']}")

    # Single thought from args
    elif len(sys.argv) > 1:
        thought = " ".join(sys.argv[1:])
        result = brain.capture(thought)
        print(f"✅ {result['message']}")

        # Show extracted data if filed successfully
        if result['status'] == 'filed' and result.get('extracted'):
            print("\n📝 Extracted:")
            for key, value in result['extracted'].items():
                if value:
                    print(f"   {key}: {value}")

    else:
        print("🧠 Second Brain Capture")
        print("\nUsage:")
        print("  python capture.py 'Your thought here'")
        print("  python capture.py --interactive")
        print("  echo 'thought' | python capture.py")
        print("\nExamples:")
        print("  python capture.py 'Call mom on Sunday'")
        print("  python capture.py 'Sarah mentioned she likes hiking - follow up'")
        print("  python capture.py 'Idea: What if we automated the weekly report?'")


if __name__ == "__main__":
    main()
