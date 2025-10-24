#!/usr/bin/env python3
"""
VectorStore Inspection Script

Inspect all stored memories to understand what's actually in VectorStore.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.agent_context import create_agent_context


def main():
    """Inspect VectorStore contents."""
    print("=" * 80)
    print("VectorStore Inspection")
    print("=" * 80)
    print()

    context = create_agent_context(
        session_id=f"vectorstore_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # Try different query strategies
    queries = [
        {"tags": ["pattern"], "desc": "All patterns"},
        {"tags": ["test_recovery"], "desc": "Test recovery only"},
        {"tags": ["test"], "desc": "Any test-related"},
        {"tags": ["coder"], "desc": "Coder agent patterns"},
        {"tags": ["success"], "desc": "Successful patterns"},
    ]

    for query_info in queries:
        tags = query_info["tags"]
        desc = query_info["desc"]

        print(f"Query: {desc}")
        print(f"Tags: {tags}")

        try:
            results = context.search_memories(tags=tags, include_session=False)
            print(f"Results: {len(results)} patterns found")

            if results:
                print("\nSample patterns:")
                for idx, result in enumerate(results[:3], 1):
                    content = result.get("content", {})
                    result_tags = result.get("tags", [])
                    metadata = result.get("metadata", {})

                    print(f"\n  Pattern {idx}:")
                    print(f"    Tags: {result_tags}")
                    print(f"    Confidence: {metadata.get('confidence', 'N/A')}")
                    print(f"    Content keys: {list(content.keys())}")

        except Exception as e:
            print(f"Error: {e}")

        print("-" * 80)
        print()

    # Check if VectorStore is enabled
    print("VectorStore Configuration:")
    print(f"  Enhanced memory enabled: {context._use_enhanced_memory}")
    print(f"  Memory store type: {type(context._memory_store).__name__}")
    print()


if __name__ == "__main__":
    main()
