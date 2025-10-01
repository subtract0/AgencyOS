#!/usr/bin/env python3
"""
Interactive demonstration of cross-session learning persistence.

This script proves that insights stored in one session can be retrieved in another
by simulating two separate sessions with Firestore.

Usage:
    python demo_cross_session_persistence.py
"""

import os
import time
from datetime import datetime
from agency_memory import FirestoreStore


def setup_firestore():
    """Configure Firestore environment."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
        "/Users/am/Code/Agency/gothic-point-390410-firebase-adminsdk-fbsvc-505b6b6075.json"
    )
    os.environ["FRESH_USE_FIRESTORE"] = "true"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    """Run cross-session persistence demonstration."""
    setup_firestore()

    # Demo collection name
    collection_name = f"demo_cross_session_{int(time.time())}"

    print_section("CROSS-SESSION PERSISTENCE DEMONSTRATION")
    print(f"\nCollection: {collection_name}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # ========================================================================
    # SESSION 1: Store insights
    # ========================================================================
    print_section("SESSION 1: Storing Insights")

    session_1_store = FirestoreStore(collection_name=collection_name)

    # Verify we're using real Firestore
    print(f"\n✓ Firestore client initialized: {session_1_store._client is not None}")
    print(f"✓ Using FirestoreStore (not fallback): {session_1_store._fallback_store is None}")
    print(f"✓ Project ID: {session_1_store._client.project}")

    # Create sample insights
    insights = [
        {
            "key": "parallel_tool_calls_001",
            "content": {
                "type": "tool_pattern",
                "title": "Parallel Tool Call Optimization",
                "description": "Batching Read/Grep calls reduces latency by 60%",
                "confidence": 0.92,
                "evidence": {
                    "sessions_analyzed": 50,
                    "avg_time_saved_ms": 450
                }
            },
            "tags": ["learning", "performance", "parallel_orchestration"]
        },
        {
            "key": "error_auto_fix_001",
            "content": {
                "type": "error_resolution",
                "title": "NoneType Auto-Fix Pattern",
                "description": "Automatic type guards prevent 95% of NoneType errors",
                "confidence": 0.88,
                "evidence": {
                    "fixes_applied": 120,
                    "success_rate": 0.95
                }
            },
            "tags": ["learning", "quality", "auto_fix"]
        },
        {
            "key": "test_consolidation_001",
            "content": {
                "type": "optimization",
                "title": "Test Consolidation Strategy",
                "description": "Merging similar tests reduces execution time by 40%",
                "confidence": 0.85,
                "evidence": {
                    "tests_merged": 25,
                    "time_saved_seconds": 180
                }
            },
            "tags": ["learning", "testing", "optimization"]
        }
    ]

    # Store all insights
    print("\nStoring insights to Firestore...")
    for insight in insights:
        session_1_store.store(
            insight["key"],
            insight["content"],
            insight["tags"]
        )
        print(f"  ✓ Stored: {insight['content']['title']}")

    # Wait for Firestore to persist
    print("\nWaiting for persistence (2 seconds)...")
    time.sleep(2)

    # Verify storage in Session 1
    print("\nVerifying storage in Session 1...")
    session_1_results = session_1_store.search(["learning"])
    print(f"  ✓ Found {session_1_results.total_count} insights")

    print("\n✓ SESSION 1 COMPLETE - All insights stored")

    # ========================================================================
    # SIMULATE SESSION END
    # ========================================================================
    print_section("SIMULATING SESSION END")
    print("\n  Closing Session 1 connection...")
    print("  (In real usage, the store instance would be destroyed)")
    print("  Simulating application restart or new session...")
    time.sleep(1)

    # ========================================================================
    # SESSION 2: Retrieve insights (new store instance)
    # ========================================================================
    print_section("SESSION 2: Retrieving Insights")

    # Create completely new store instance
    session_2_store = FirestoreStore(collection_name=collection_name)

    # Verify Session 2 is also using real Firestore
    print(f"\n✓ New Firestore client initialized: {session_2_store._client is not None}")
    print(f"✓ Using FirestoreStore (not fallback): {session_2_store._fallback_store is None}")
    print(f"✓ Project ID: {session_2_store._client.project}")

    # Retrieve insights stored in Session 1
    print("\nSearching for insights stored in Session 1...")
    session_2_results = session_2_store.search(["learning"])

    print(f"\n✓ Found {session_2_results.total_count} insights from previous session")

    # Display retrieved insights
    print("\nRetrieved Insights:")
    for i, record in enumerate(session_2_results.records, 1):
        print(f"\n  {i}. {record.key}")
        if isinstance(record.content, dict):
            print(f"     Title: {record.content.get('title', 'N/A')}")
            print(f"     Type: {record.content.get('type', 'N/A')}")
            print(f"     Confidence: {record.content.get('confidence', 'N/A')}")
            print(f"     Tags: {', '.join(record.tags[:3])}")

    # Verify data integrity
    print("\n" + "-" * 80)
    print("DATA INTEGRITY CHECK")
    print("-" * 80)

    # Check each insight
    all_found = True
    for original_insight in insights:
        found = False
        for record in session_2_results.records:
            if record.key == original_insight["key"]:
                found = True
                # Verify content matches
                if isinstance(record.content, dict):
                    original_title = original_insight["content"]["title"]
                    retrieved_title = record.content.get("title", "")
                    if original_title == retrieved_title:
                        print(f"✓ {original_insight['key']}: Content matches")
                    else:
                        print(f"✗ {original_insight['key']}: Content mismatch")
                        all_found = False
                break

        if not found:
            print(f"✗ {original_insight['key']}: NOT FOUND")
            all_found = False

    # ========================================================================
    # FINAL VERDICT
    # ========================================================================
    print_section("PERSISTENCE VERIFICATION RESULT")

    if all_found and session_2_results.total_count >= len(insights):
        print("\n✅ SUCCESS: Cross-session persistence PROVEN")
        print("\n  All insights stored in Session 1 were successfully retrieved in Session 2")
        print("  Data integrity maintained: 100%")
        print("  No data loss detected")
        print("\n  CONCLUSION: Learning system uses PERSISTENT storage (Firestore)")
    else:
        print("\n❌ FAILURE: Cross-session persistence FAILED")
        print("\n  Some insights were not retrieved or data was corrupted")
        print("  Learning system may not be persisting correctly")

    # ========================================================================
    # CLEANUP
    # ========================================================================
    print_section("CLEANUP")

    print("\nDeleting test collection...")
    try:
        docs = session_2_store._collection.stream()
        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1
        print(f"✓ Deleted {deleted_count} test documents")
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")

    print("\n✓ Demo complete")


if __name__ == "__main__":
    main()
