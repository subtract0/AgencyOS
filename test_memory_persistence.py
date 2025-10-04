#!/usr/bin/env python3
"""
Test Firestore Cross-Session Persistence for Agency Memory

This script tests that memories persist across different Python sessions.
"""

import sys
from datetime import datetime

from agency_memory import create_firestore_store

# Unique test ID for this run
TEST_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")


def test_store_memories():
    """Phase 1: Store test memories"""
    print("=" * 60)
    print("PHASE 1: Storing test memories to Firestore")
    print("=" * 60)

    try:
        store = create_firestore_store(collection_name="agency_persistence_test")
        print("✅ Created FirestoreStore")

        # Store multiple test memories
        test_data = [
            {
                "key": f"persistence_test_1_{TEST_SESSION_ID}",
                "content": {
                    "type": "pattern",
                    "description": "Successful TDD implementation pattern",
                    "context": "Test-first development approach",
                },
                "tags": ["pattern", "tdd", "success", TEST_SESSION_ID],
            },
            {
                "key": f"persistence_test_2_{TEST_SESSION_ID}",
                "content": {
                    "type": "learning",
                    "description": "VectorStore semantic search improves pattern matching",
                    "context": "Enhanced memory retrieval",
                },
                "tags": ["learning", "vectorstore", "semantic_search", TEST_SESSION_ID],
            },
            {
                "key": f"persistence_test_3_{TEST_SESSION_ID}",
                "content": {
                    "type": "error_resolution",
                    "description": "Fixed NoneType error with proper type guards",
                    "context": "Autonomous healing success",
                },
                "tags": ["error_resolution", "healing", "success", TEST_SESSION_ID],
            },
        ]

        stored_keys = []
        for data in test_data:
            store.store(data["key"], data["content"], data["tags"])
            stored_keys.append(data["key"])
            print(f"📝 Stored: {data['key']}")

        print(f"\n✅ Successfully stored {len(stored_keys)} memories")
        print(f"   Test Session ID: {TEST_SESSION_ID}")

        # Verify immediate retrieval
        print("\n🔍 Verifying immediate retrieval...")
        result = store.search([TEST_SESSION_ID])
        print(f"   Found {result.total_count} records with session tag")

        print("\n🎉 PHASE 1 COMPLETE: All memories stored successfully")
        print("\n   To test persistence, run this command in a new terminal:")
        print(f"   python test_memory_persistence.py retrieve {TEST_SESSION_ID}")
        print("=" * 60)

        return stored_keys

    except Exception as e:
        print(f"\n❌ ERROR in Phase 1: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def test_retrieve_memories(session_id):
    """Phase 2: Retrieve memories (simulating fresh session)"""
    print("=" * 60)
    print("PHASE 2: Retrieving memories (fresh session)")
    print("=" * 60)

    try:
        # Create a new store instance (simulates fresh session)
        store = create_firestore_store(collection_name="agency_persistence_test")
        print("✅ Created new FirestoreStore instance")

        # Retrieve memories by session ID
        print(f"\n🔍 Retrieving memories with session tag: {session_id}")
        session_memories = store.search([session_id])

        if session_memories.total_count == 0:
            print(f"❌ ERROR: No memories found for session {session_id}!")
            print("   Persistence may have failed, or session ID is incorrect.")
            sys.exit(1)

        print(f"✅ Retrieved {session_memories.total_count} memories from session {session_id}")

        # Display retrieved memories
        print("\n📋 Retrieved memories:")
        for i, record in enumerate(session_memories.records, 1):
            print(f"\n   {i}. Key: {record.key}")
            print(f"      Tags: {', '.join(record.tags)}")
            print(f"      Timestamp: {record.timestamp}")
            content = record.content
            if isinstance(content, dict):
                print(f"      Type: {content.get('type', 'N/A')}")
                print(f"      Description: {content.get('description', 'N/A')}")

        print("\n🎉 PHASE 2 COMPLETE: Cross-session persistence verified!")
        print("=" * 60)

        return session_memories.total_count

    except Exception as e:
        print(f"\n❌ ERROR in Phase 2: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "retrieve":
        if len(sys.argv) < 3:
            print("Usage: python test_memory_persistence.py retrieve <session_id>")
            sys.exit(1)
        session_id = sys.argv[2]
        test_retrieve_memories(session_id)
    else:
        test_store_memories()

    print("\n✅ Firestore persistence test completed successfully!\n")
